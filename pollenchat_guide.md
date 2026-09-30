# NekoChat 使い方ガイド（v2.8.13）

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

```
Taro[default] : [system]

Current system prompt:
  You are a helpful assistant.

[+] Enter new prompt (empty line = keep, [reset] = default):
あなたは優秀なPythonプログラマーです。簡潔に回答してください。

[OK] System prompt updated.
```

`[reset]` と入力するとデフォトに戻ります。

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
| `[system]` | システムプロンプトを設定 |
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
