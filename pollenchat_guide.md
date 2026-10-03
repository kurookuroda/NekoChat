# NekoChat 使い方ガイド（v2.8.16）

NekoChat（スクリプト名は `pollenchat.py` のまま）は、複数の LLM サービスにつながるクリーンな CLI チャットクライアントです。PollinationsAI・NVIDIA・Mistral・Cloudflare Workers AI を内蔵し、`config.json` で自分のサービスも追加できます。

## 起動

```bash
python pollenchat.py
```

初回起動時に名前を聞かれます。Enter で環境変数のデフォルト値が使われます。

```
[+] Your name (Enter for 'user'): Taro
[OK] Welcome, Taro! Type [help] for commands.

Taro[default] :
```

プロンプトの `[default]` は現在のセッシン名です。

---

## 基本的なチャット

コマンド以外をそのまま入力すると、AI と会話できます。

```
Taro[default] : PythonでFizzBuzzを書いて

NekoChat (openai): もちろんです。以下にPythonコードを示します。
```python
for i in range(1, 101):
    if i % 15 == 0:
        print("FizzBuzz")
    ...
```
```

ストリーミングモードでは、AI の応答が1文字ずつリアルタイムに表示されます。

---

## サービスとモデルの切り替え

`[service]` でサービスを選ぶと、必要ならそのまま API キーを入力し、続けてモデルを選べます。**モデルを選ぶまでサービスは切り替わりません**（途中でキャンセルすると元のままです）。

```
Taro[default] : [service]

Services:
  [*] 1. pollinations      no key needed
  [ ] 2. pollinations-key  key not set
  [ ] 3. nvidia            key not set
  [ ] 4. mistral           key not set
  [ ] 5. cloudflare        key not set

[+] Select service (number or name, Enter=cancel): 4
[~] Mistral needs an API key.
MISTRAL_API_KEY (input hidden, Enter=cancel, 'delete'=remove saved key):
[OK] Key for mistral set for this session (...a1b2).
[+] Save to keys.json? (y/N): y
[OK] Saved to keys.json (owner-only permissions).

Available models (Mistral):
  [ ] 1. codestral-latest
  [ ] 2. mistral-small-latest
  ...
[+] Select model (number or name, Enter=cancel): 2
[OK] Service: mistral  Model: mistral/mistral-small-latest
```

- モデル一覧は選んだ時点でそのサービスから取得します（10分間キャッシュ）。25件を超えると、先に絞り込み（部分一致）を聞かれます。
- 一覧が取れないサービス（Cloudflare など）では、モデル ID を直接入力します。
- 保存される形式は `サービス/モデルID` です。接頭辞のない名前（`openai` など）は PollinationsAI のモデルとして扱われます。

`[model]` は、**今のサービスの中だけ**でモデルを選び直します。

```
Taro[default] : [model]

Available models (Mistral):
  [*] 1. mistral-small-latest
  ...
[+] Select model (number or name, Enter=cancel): 1
[OK] Model set to: mistral/mistral-small-latest
```

---

## APIキーの管理

`[key]` でキーの設定・削除ができます（入力は画面に出ません）。

```
Taro[default] : [key]

Services that need an API key:
  1. pollinations-key  POLLINATIONS_API_KEY     [not set]
  2. nvidia            NVIDIA_API_KEY           [set: keys.json ...x9Qa]
  3. mistral           MISTRAL_API_KEY          [not set]
  4. cloudflare        CLOUDFLARE_API_TOKEN     [not set]
```

キーは次の順で探されます。

1. `[key]` でこのセッション中に入力した値
2. 環境変数（例: `export NVIDIA_API_KEY=...`。Termux なら `~/.bashrc` に書けます）
3. `keys.json`

`keys.json` は所有者だけが読める権限で作られ、`.gitignore` に入っています。キーは `config.json`・セッション・エクスポートには書かれません。誤ってコミットした場合は、キー自体を無効にして作り直してください。

| サービス | 環境変数 | 補足 |
|----------|----------|------|
| pollinations | なし | 匿名の旧端点。停止・有料化している可能性あり（HTTP 500 / 402） |
| pollinations-key | `POLLINATIONS_API_KEY` | `enter.pollinations.ai` でキーを取得 |
| nvidia | `NVIDIA_API_KEY` | `build.nvidia.com`。モデルIDは `meta/llama-...` のように組織名付き |
| mistral | `MISTRAL_API_KEY` | `console.mistral.ai` |
| cloudflare | `CLOUDFLARE_API_TOKEN` | アカウントID（`CLOUDFLARE_ACCOUNT_ID`）も必要。`[service]` が聞いて `config.json` に保存します |

無料枠の上限はサービスごとに違い、変わることもあります。各サービスの公式情報を確認してください。

### 自分のサービスを追加する

`config.json` の `providers` に書くと、OpenAI 互換のサービスを追加（または内蔵のものを上書き）できます。

```json
{
  "providers": {
    "groq": {
      "chat_url": "https://api.groq.com/openai/v1/chat/completions",
      "models_url": "https://api.groq.com/openai/v1/models",
      "key_env": "GROQ_API_KEY",
      "label": "Groq"
    },
    "ollama": {"chat_url": "http://localhost:11434/v1/chat/completions"}
  }
}
```

- 使える項目: `chat_url` / `models_url`（`null` で一覧なし）/ `key_env`（`null` でキー不要）/ `label` / `rate_hint` / `fail_hint` / `vars`
- URL の `${VAR}` は、環境変数、サービスの `vars` の順で埋められます。
- `https://` のみ（`localhost` に限り `http://` も可）。キーをここに書いても読まれません。
- セッションは `サービス/モデルID` を覚えているので、別のマシンに移すときは `providers` も一緒に移してください。

---

## システムプロンプト

システムプロンプトは**2つの層**に分かれています。

| 層 | コマンド | 保存先 | 効く範囲 |
|----|----------|--------|----------|
| 全体 | `[system]` | `config.json` | すべてのセッション |
| セッション | `[system session]` | そのセッションのファイル | 今のセッションだけ |

AI に送られるのは、**全体のプロンプト、空行、セッションのプロンプト**の順に連結した、1つの system メッセージです。

```
Taro[default] : [system session]

System prompt layers:
  Global:             You are a helpful assistant.
  Session [default]:  (none)
  Sent to the AI:     28 characters

Enter the prompt for session 'default'. Type [end] to finish, [reset] to remove it:
このセッションでは、コードレビューだけを行う。
[end]

Received 1 line(s), 23 characters:
  このセッションでは、コードレビューだけを行う。
[+] Apply to session 'default'? (Y/n):
[OK] Session prompt set for 'default'.
```

- `[system]` も同じ形式で、**全体の層**を変更します（`[reset]` で初期の文言に戻ります）。
- `[system session]` の `[reset]` は、**セッションの層を消して**、全体の層だけに戻します。
- どちらも、確定の前にプレビューを表示して `Apply? (Y/n)` と聞きます。Enter だけなら確定、`n` で取り消しです。Ctrl+D や Ctrl+C でも、変更せずに取り消せます。
- 変更は**次の送信から**効きます。過去の応答は履歴に残るので、前の指示の口調が残ることがあります。きっぱり切り替えたいときは、`[new]` で新しいセッションを作ってください。
- `[sessions]` の一覧では、セッションのプロンプトがあるセッションに `[+prompt]` が付きます。
- `[new]` で作ったセッションは、セッションのプロンプトなしで始まります。`[rename]`・`[delete]`・`[save]` では、セッションのプロンプトも一緒に動きます。`[export]` と `[token]` は、実際に送られる内容で計算します。
- 旧式の `[load]` は、ファイルにあるセッションのプロンプトを戻しますが、全体のプロンプトは書き換えません。

### 複数行の入力と貼り付け

`[system]`、`[system session]`、`[plugin new]`、`[long]` は、単独の行の `[end]` まで、複数行を読みます。

- **貼り付けは、まとまり全体を読んでから判断します。** `[end]` が終了の合図になるのは、貼り付けの**最後の行**にあるとき（または手で単独で打ったとき）だけです。`[reset]` は、それだけの行のときだけ有効です。貼り付けの途中にあるときは、**ふつうの文章として残し**、その旨を表示します。そのあとで、`[end]` を自分で入力してください。
- `[end]` のあと0.3秒以内に届いた行は、AI へは送らず、捨てて報告します。ただし、0.3秒を超える間隔で、細切れに届く貼り付け（遅い SSH など）では、漏れることがあります。
- 入力した行は、上矢印の履歴には残りません。
- 貼り付けの検出は、時間に頼っていて、POSIX の端末（Linux、macOS、Termux）で働きます。Windows では、これまでどおり1行ずつ読みます。
- `[system ほかの文字]` と入力すると、使い方が表示されます（AI には送られません）。

---

## プラグイン（定型プロンプト）

プラグインは、**名前を付けて保存しておく定型のプロンプト**です。`plugins/名前.txt` という、ふつうのテキストファイルで、必要なときに、**今のセッション**または**全セッション**へ付け外しできます。プラグインは**データだけ**で、コードも URL も含められません。プロンプトの文章を足して、いくつかの設定を調整するだけで、メッセージの送り先は変えられません。

```
description: コードをレビューして、問題を優先度順に挙げる
temperature: 0.2
max_tokens: 1200
model: モデルのID
---
あなたは経験豊富なコードレビュアーです。
見つけた問題を、重要なものから順に挙げてください。
```

- 先頭の「ヘッダ」は、`キー: 値` の行だけで、`---` の行で終わります。使えるキーは、`description`（1行の説明）、`temperature`（0.0〜2.0）、`max_tokens`、`model` で、**すべて省略できます**。知らないキーはエラーです。ヘッダのないファイルは、そのまま本文になります。
- 名前は、`a-z`、`0-9`、`-`、`_` が使えます（40文字まで）。本文は、20,000文字までです。
- `description` は**人が見るための説明**で、AI には送られません。送られるのは、本文だけです。

| コマンド | 内容 |
|----------|------|
| `[plugin]` | 一覧（`[S]` はこのセッションに付いている、`[G]` は全セッションに付いている） |
| `[plugin show 名前]` | ヘッダ、設定、本文を表示 |
| `[plugin on 名前]` | 今のセッションに付ける |
| `[plugin on 名前 global]` | 全セッションに付ける |
| `[plugin off 名前]` | 外す（ファイルは `plugins/` に残ります） |
| `[plugin new 名前]` | 作る（説明、任意の設定、本文の順に聞かれます。本文は `[end]` で終えます） |

```
Taro[default] : [plugin on code-review]

Plugin 'code-review' -> session 'default'
  Description : コードをレビューして、問題を優先度順に挙げる
  Prompt text : 46 characters
    あなたは経験豊富なコードレビュアーです。
    見つけた問題を、重要なものから順に挙げてください。
  Settings it changes while attached (config.json is not modified):
    temperature : 0.7 -> 0.2
    max_tokens  : (server default) -> 1200
[+] Attach? (Y/n):
[OK] Plugin 'code-review' attached to session 'default'.
```

**付けるときは、毎回確認します。** 文章の長さ、プレビュー、変わる設定（どのプラグインの設定を置き換えるか）が表示されます。このとき、ファイルの SHA-256（内容の指紋）を覚えておきます。**あとでファイルが書き換えられたり、消えたり、壊れたりすると、そのプラグインは使われません**（お知らせを1回表示します）。もう一度 `[plugin on 名前]` で承認すれば、使えるようになります。保存されるのは、名前と指紋だけです（全体は `config.json` の `plugins`、セッションはそのセッションのファイル）。

**AI に送られるもの**は、1つの system メッセージです。全体のプロンプト、全体のプラグイン、セッションのプロンプト、セッションのプラグイン（付けた順）の順に、空行でつなぎます。

**設定は、上から重ねるだけで、保存されません。** 付けている間だけ、`temperature`・`max_tokens`・`model` が、送信に使われます。`config.json` は書き換えられず、外せば元の値に戻ります。セッションのプラグインは全体のプラグインより、あとのものは前のものより、優先されます。`[config]`、`[model]`、`[system]`、返信のラベルに、今効いている内容が表示されます。`model` は、**今のサービスの中のモデル ID** だけを指定できます。サービスのモデル一覧が分かっていて、そこにないときは、お知らせを出して無視します（一覧を確認できないときは、そのまま使います）。

プラグインのファイルは、ふつうのテキストなので、別のマシンへコピーできます。自分で書いていないファイルは、ほかのプロンプトと同じように扱ってください。中の文章は、使っている AI サービスに送られます。

---

## temperature / max_tokens

```
Taro[default] : [config]

Current configuration:
  temperature : 0.7
  max_tokens  : (unset / server default)

[+] temperature (current: 0.7, Enter=keep, 0.0-2.0): 1.2
[OK] temperature set to 1.2

[+] max_tokens (current: (unset), Enter=keep, 'none'=unset): 2048
[OK] max_tokens set to 2048
```

- `temperature`: 0.0（決定的）〜 2.0（創造的）
- `max_tokens`: `none` で未設定に戻せます

---

## ストリーミングモードの切り替え

```
Taro[default] : [stream]
[OK] Streaming mode: OFF (batch)
```

バッチモードでは、APIから全文が返ってきてから一括表示されます。

---

## 画像生成

```
Taro[default] : [image]

Image Generation Mode
  Current: 1024x1024, seed=random

[image] Taro: a cat wearing a space suit
[~] Generating image... prompt: a cat wearing a space suit... | size: 1024x1024 | seed: 48291
[OK] Image saved: pollen_images/img_20260929_143052_a_cat_wearing_a_space_s.png
```

画像モード内で使えるサブコマンド:

```
[image] Taro: [size]
[+] width (current: 1024): 768
[+] height (current: 1024): 768
[OK] Size set to 768x768

[image] Taro: [seed]
[+] seed (current: random, 'none'=random): 42
[OK] Seed fixed to 42
```

シードを固定すると、同じプロンプトで同じ画像を再現できます。

---

## マルチライン入力

```
Taro[default] : [long]
[+] Multiline mode. Enter text, then a blank line to finish:
def hello():
    print("Hello, world!")

[Input preview]:
def hello():
    print("Hello, world!")
```

---

## ファイルのインポート

```
Taro[default] : [import]
[+] File path: notes.md
[OK] Loaded 12,340 characters.
[Preview]: # プロジェクト仕様書 ...

[+] Question about this file (Enter to send file content only): 要約して
```

> 200KB を超えるファイルは確認プロンプトが表示されます。

---

## 会話履歴の検索

```
Taro[default] : [search]
[+] Search keyword: Python

3 match(es):
  [1]Taro: PythonでFizzBuzz書いて
  [5]AI: Pythonのリスト内包表記は...
  [8]Taro: Pythonのデコータって何？
```

---

## Markdown の再表示とコード保存

```
Taro[default] : [render]
--- Rendered (Markdown) ---
▶ python
for i in range(1, 101): ...
◀
---------------------------

Taro[default] : [savecode]
Code blocks found: 1
  1. [python] 5 lines — for i in range...

[+] Select block number (Enter = 1, [all] = save each): 1
[+] Filename (Enter for 'snippet.py'): fizzbuzz.py
[OK] Code saved: pollen_codes/fizzbuzz.py
```

---

## セッションのエクスポート

```
Taro[default] : [export]
[+] Export filename (Enter for auto): project_discussion
[+] Include system prompt in export? y/N: n
[OK] Exported to: pollen_exports/project_discussion.md
```

---

## Discord への配信

`[discord ...]` は、今のセッションのやり取りを、Discord の **Webhook** へ送ります。選び方とフラグは、`[export]` と同じです。

```
[discord]                          登録済みの Webhook（URL は伏せて表示）と使い方
[discord add webhook [ラベル]]     Webhook を登録（URL は非表示で入力）
[discord rm ラベル]                登録を消す
[discord list]                     [export list] と同じ番号つきの一覧
[discord -1]                       最新のやり取りを送る
[discord 2:5 rev bare full]        番号・範囲・フラグは [export] と同じ（bare = 回答のみ）
[discord -3: to main backup]       送信先をラベルで指定（省略時は、登録した全部）
[discord -3: to webhook]           種類で指定（全部の Webhook）
```

番号か範囲の指定は、必須です（`:` は「すべて」）。Webhook は、Discord のチャンネルの設定（連携サービス → ウェブフック）で作ります。既存のスレッドへ送るときは、URL の末尾に `?thread_id=スレッドのID` を付けます。

**URL の置き場所。** Webhook の URL には、秘密のトークンが含まれていて、知っている人は誰でも、そのチャンネルに投稿できます。NekoChat は、`discord_webhooks.txt`（所有者だけが読める権限で作られ、`.gitignore` に入っています）と、環境変数 `DISCORD_WEBHOOK_URL`（ラベルは `env`）に保存します。`config.json`、セッション、エクスポートには書かれず、画面にもエラー文にも、表示されません。ファイルは、1行に1つ、`URL` か `ラベル URL` の形で、`#` はコメントです（JSON の配列やオブジェクトも読めますが、その場合は手で編集します）。ラベルのない行は、ファイルの順に `webhook1`、`webhook2`… という名前になるので、名前を固定したいときは、ラベルを付けてください。ラベルには、`a-z`、`0-9`、`-`、`_`（32文字まで）が使えますが、`webhook`、`bot`、`all`、`to`、`list`、`add`、`rm`、`env` は使えません。受け付ける URL は、`https://discord.com/api/webhooks/ID/トークン`（`discordapp.com`、`canary.`、`ptb.` も可）だけです。本物の URL を、公開の場所に貼ってしまったときは、Discord でその Webhook を削除して、作り直してください。

**送るときの動き**
- まず、送信先、メッセージ数と投稿数、文字数、所要時間の目安、最初のメッセージのプレビューを表示して、`Send? (Y/n)` と聞きます。
- 1つのやり取りは、1つ以上のメッセージになります。見出し `**#12** : Neko : 2026-10-03 18:40`、質問の引用（長いと短縮。`full` で全文。`bare` では省略）、回答の順です。システムプロンプトとプラグインの本文は、送りません。
- Discord の2000文字の上限を超えるときは、行の境目で分割します（数え方は UTF-16 なので、絵文字は2文字分です）。コードブロックは閉じて開き直し、最後以外の末尾に `(続く...)` が付きます。1つの Webhook あたり100メッセージを超える送信は、断ります。送るやり取りを減らしてください。
- 本文中の `@everyone` やロールのメンションでは、通知が飛びません（`allowed_mentions` を空にしています）。
- **同じ Webhook（同じ Webhook ID）への2つの投稿は、前の投稿が終わってから3秒以上**あけます。別の Webhook へは、続けて送ります。このため、長い送信は、（メッセージ数 − 1）× 3秒に、通信の時間を足した程度かかります。
- HTTP 429 のときは、`retry_after`（最大60秒）だけ待って、最大5回まで再送します。失敗した Webhook への送信は、そこで止めて、ほかの Webhook には続けます。結果は、Webhook ごとに報告されます（`main: 8/8 sent`、または止まった場所と理由）。Ctrl+C で、安全に止まり、どこまで送ったかを報告します。自動の再送は、しません。

いまは、Webhook だけに対応しています。Bot トークンでスレッドを作る方式は、`[discord add bot]` として、あとで追加する予定です。

---

## Undo とトークン概算

```
Taro[default] : [undo]
[OK] Undid last exchange (2 message(s)). History now: 5 messages.

Taro[default] : [token]
Token estimate (default):
  Approximate tokens : 1,234
  Total characters   : 5,678
  ASCII chars        : 3,456
  Non-ASCII chars    : 2,222
  ※ This is a rough estimate. Actual tokenizer counts may differ.
```

---

## 複数セッョン管理

### 新規セッション作成

```
Taro[default] : [new]
[+] New session name: work
[OK] Created and switched to 'work'

Taro[work] : プロジェクトAの要件を整理して
```

### セッション切り替え

```
Taro[work] : [switch]

Sessions:
  [*] 1. default (3 messages)
  [ ] 2. work (2 messages)

[+] Switch to (number or name): default
[OK] Switched to 'default' (3 messages)

Taro[default] :
```

### セッションのリネーム

```
Taro[default] : [rename]
[+] Rename 'default' to: hobby
[OK] Renamed 'default' → 'hobby'
```

### セッションの削除

```
Taro[hobby] : [delete]
[+] Delete session (name, Enter=cancel): work
[!] Really delete 'work'? type 'yes': yes
[OK] Deleted 'work'
```

> 現在アクティブなセッションは削除できません。削除前に `[switch]` で別のセッションに移ってください。

### 自動保存・自動読込

終了時に全セッションが自動保存され、次回起動時に自動で復元されます。

```
Taro[hobby] : [exit]
Bye bye, Taro!
[OK] All sessions saved.
```

---

## 便利なワークフロー例

### 仕事と趣味を分ける

```
[ new ] → work
[ system ] → あなたは優秀な技術顧問です。
（仕事の相談）
[ switch ] → default
[ rename ] → hobby
（趣味の雑談）
```

### 長文ドキュメントを読み込んで質問

```
[ import ] → spec.md → 「この仕様書に不足している項目は？」
```

### コード生成 → 保存 → エクスポート

```
「FastAPIのCRUDサンプルを書いて」
[ savecode ] → 1 → crud.py
[ export ] → fastapi_chat.md → n
```

---

## コマンド早見表

| コマンド | 用途 |
|---------|------|
| `[service]` | サービスを切り替え（キー入力→モデル選択まで） |
| `[model]` | 今のサービスのモデルを切り替え |
| `[key]` | APIキーの設定・削除 |
| `[system]` | 全体のシステムプロンプトを設定（全セッション共通） |
| `[system session]` | 今のセッションだけのシステムプロンプトを設定 |
| `[discord]` | 選んだやり取りを Discord の Webhook へ送る |
| `[plugin]` | 定型プロンプト（プラグイン）の一覧・表示・付け外し・作成 |
| `[config]` | temperature / max_tokens を調整 |
| `[stream]` | ストリーミング ON/OFF 切り替え |
| `[image]` | 画像生成モード |
| `[long]` | マルチライン入力 |
| `[import]` | .md / .txt ファイルを読込んで送信 |
| `[search]` | 会話履歴を検索 |
| `[render]` | 直前の応答をMarkdown再表示 |
| `[savecode]` | コードブロックをファイル保存 |
| `[export]` | 会話をMarkdownファイルにエクスポート |
| `[undo]` | 直前のやり取りを削除 |
| `[token]` | 概算トークン数を表示 |
| `[sessions]` | セッション一覧 |
| `[switch]` | セッション切り替え |
| `[new]` | 新規セッション作成 |
| `[rename]` | セッション名変更 |
| `[delete]` | セッション削除 |
| `[clear]` | 現在のセッション履歴をクリア |
| `[history]` | 現在のセッション履歴を表示 |
| `[help]` | ヘルプ表示 |
| `[exit]` | 終了（自動保存あり） |

---

## トラブルシューティング

### HTTP 429 (Rate Limited)

どのサービスにもレート制限があります。数秒〜数十秒待ってから再試行してください。メッセージにサービス名が出ます。

### HTTP 500 / 402（PollinationsAI の匿名端点）

旧端点が停止している、または無料でなくなっている可能性があります。`[service]` で別のサービスに切り替えるか、`POLLINATIONS_API_KEY` を設定して `pollinations-key` を使ってください。

### 認証エラー（HTTP 401 / 403）

キーが違う、または期限切れです。`[key]` で入れ直してください（環境変数が優先されていないかも確認を。`[key]` の一覧に取得元が出ます）。

### モデルが応答しない

`[model]` で別のモデルに切り替えるか、`[service]` で別のサービスを試してください。モデルの可用性はサービスごとに変動します。

### セッショが復元されない

`sessions/` ディレクトリ内の `.json` ファイルを確認してください。手動でファイルを移動した場合は、起動時に自動読込されます。

### 巨大なファイルの送信を防ぎたい

`[import]` は 200KB を超えるファイルで確認プロンプトを表示します。それ以上のサイズ制限を設けたい場合は、スクリプト内の `IMPORT_MAX_BYTES` を変更してください。
