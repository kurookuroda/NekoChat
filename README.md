# NekoChat v2.8.15

A clean, harmless CLI chat client for several LLM services.

NekoChat (the script is still `pollenchat.py`) is a lightweight terminal chat application. It talks to OpenAI-compatible services — [PollinationsAI](https://pollinations.ai/), NVIDIA, Mistral and Cloudflare Workers AI are built in, and you can add your own in `config.json`. It also supports image generation (PollinationsAI), multi-session management, code extraction, and more. It runs on plain CPython, including Termux.

## Features

- **Multiple services** — Switch service with `[service]` and model with `[model]`; add your own OpenAI-compatible service in `config.json`
- **API keys kept out of the way** — Set keys with `[key]`; they are stored only in `keys.json` (owner-only, git-ignored), never in configs, sessions or exports
- **Streaming & batch modes** — Toggle live token-by-token output or wait-for-complete display
- **Plugins** — Reusable prompts saved as text files and attached to a session or to every session with `[plugin]`, optionally with their own temperature / max_tokens / model
- **System prompt layers** — A global prompt with `[system]` and an optional prompt for just the current session with `[system session]`
- **Temperature / max_tokens control** — Fine-tune generation parameters with `[config]`
- **Image generation** — Generate images from text prompts inside `[image]` mode, with configurable size and seed
- **Multiline input** — Paste or type long messages with `[long]` (type `[end]` on its own line to finish; blank lines are preserved)
- **File import** — Load `.md` or `.txt` files and send them as user messages with `[import]`
- **Conversation search** — Find past messages with `[search]`
- **Markdown rendering** — Re-display the last response with formatted Markdown via `[render]`
- **Code extraction** — Save code blocks from the last response with `[savecode]`
- **Session export** — Export conversations to Markdown files with `[export]`
- **Undo** — Remove the last user-assistant exchange with `[undo]`
- **Token estimate** — Rough token count estimation for the current context with `[token]`
- **Multi-session management** — Manage multiple parallel conversations with `[sessions]`, `[switch]`, `[new]`, `[rename]`, `[delete]`
- **Auto-save / auto-load** — Every session is saved atomically after each exchange (and on `[undo]`/`[clear]`), plus once more on exit; all sessions are restored on startup

## Installation

```bash
# Clone or download pollenchat.py
git clone https://github.com/kurookuroda/NekoChat.git
cd NekoChat

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
python pollenchat.py
```

On first launch you will be asked for your name. After that, just type normally to chat. Use `[help]` to see all available commands.

## Services and API Keys

Type `[service]` to see the services, pick one, enter its API key if it needs one, and choose a model. The service only changes once a model has been chosen.

| Service | Key | Notes |
|---------|-----|-------|
| `pollinations` | none | Anonymous legacy endpoint (`text.pollinations.ai`). It may be down or no longer free (HTTP 500 / 402) — switch service if so |
| `pollinations-key` | `POLLINATIONS_API_KEY` | `gen.pollinations.ai`; get a key at enter.pollinations.ai |
| `nvidia` | `NVIDIA_API_KEY` | Key from build.nvidia.com. Model IDs include the organisation, e.g. `meta/llama-...` |
| `mistral` | `MISTRAL_API_KEY` | Key from console.mistral.ai |
| `cloudflare` | `CLOUDFLARE_API_TOKEN` | Also needs your account ID (`CLOUDFLARE_ACCOUNT_ID`); `[service]` asks for it and keeps it in `config.json`. No model list — type a model ID such as `@cf/...` |

Free-tier limits differ per service and change over time; check each service's own documentation.

### Where the key comes from

NekoChat looks for a service's key in this order:

1. The key you entered with `[key]` in this session
2. The environment variable above (e.g. `export NVIDIA_API_KEY=...`, which also works from `~/.bashrc` in Termux)
3. `keys.json`

`[key]` shows which source is in use (only the last 4 characters of a key are displayed), reads the key with hidden input, and asks whether to save it to `keys.json`. Enter `delete` at the key prompt to remove a stored key. `keys.json` is created with owner-only permissions and is listed in `.gitignore`. If you ever committed a real key, revoke it — Git history keeps it.

### Model names

Models are stored as `service/model-id` (e.g. `nvidia/meta/llama-3.1-70b-instruct`). A name without a service prefix, such as `openai`, means PollinationsAI, so older `config.json` and session files keep working. Model lists are fetched from the service when you open `[service]` / `[model]` (cached for 10 minutes); long lists can be filtered by substring, and if a service has no list you type the model ID.

### Adding or overriding services (`config.json`)

An optional `providers` block defines your own OpenAI-compatible services or overrides built-in ones:

```json
{
  "providers": {
    "groq": {
      "chat_url": "https://api.groq.com/openai/v1/chat/completions",
      "models_url": "https://api.groq.com/openai/v1/models",
      "key_env": "GROQ_API_KEY",
      "label": "Groq"
    },
    "ollama": {
      "chat_url": "http://localhost:11434/v1/chat/completions"
    },
    "cloudflare": {
      "vars": {"CLOUDFLARE_ACCOUNT_ID": "your-account-id"}
    }
  }
}
```

- Fields: `chat_url`, `models_url` (`null` = no list), `key_env` (`null` = no key), `label`, `rate_hint`, `fail_hint`, `vars`.
- `${VAR}` in a URL is filled from the environment first, then from the service's `vars`.
- Only `https://` URLs are accepted (plain `http://` only for `localhost`). Service names use `a-z`, `0-9` and `-`.
- Keys are **not** read from this block — use `[key]`, `keys.json` or environment variables. Invalid entries are skipped with a warning at startup.
- Sessions remember the model as `service/model-id`; if you move sessions to another machine, bring the `providers` block along too.

## Commands

### Chat & Settings

| Command | Description |
|---------|-------------|
| `[service]` | Switch service (PollinationsAI, NVIDIA, Mistral, Cloudflare, your own) and pick its model |
| `[model]` | Select a model of the current service |
| `[key]` | Set or remove API keys (hidden input; optionally saved to `keys.json`) |
| `[system]` | Set the **global** system prompt, shared by every session (multi-line, `[end]` to finish, `[reset]` for default) |
| `[system session]` | Set a system prompt for the **current session only**; it is added after the global one (`[reset]` removes it) |
| `[plugin]` | Reusable prompts: `[plugin]` lists, `[plugin show NAME]`, `[plugin on NAME [global]]`, `[plugin off NAME]`, `[plugin new NAME]` |
| `[config]` | Set `temperature` / `max_tokens` |
| `[stream]` | Toggle streaming / batch display mode |

### Input

| Command | Description |
|---------|-------------|
| `[long]` | Enter multiline input mode |
| `[import]` | Import a `.md` / `.txt` file and send as user message |

### Output & History

| Command | Description |
|---------|-------------|
| `[search]` | Search conversation history |
| `[render]` | Re-display last response with Markdown formatting |
| `[savecode]` | Extract and save code blocks from last response |
| `[export]` | Export conversation to Markdown file |
| `[undo]` | Remove the last user-assistant exchange |
| `[token]` | Show rough token estimate for current context |

### Image Generation

| Command | Description |
|---------|-------------|
| `[image]` | Enter image generation mode |

Inside image mode:
- Type a prompt to generate an image
- `[size]` — change width/height (default 1024x1024, range 64–4096)
- `[seed]` — set/clear a fixed seed for reproducible images
- `exit` — return to chat mode

### Session Management

| Command | Description |
|---------|-------------|
| `[sessions]` | List all sessions |
| `[switch]` | Switch to another session |
| `[new]` | Create a new empty session |
| `[rename]` | Rename the current session |
| `[delete]` | Delete a session (cannot delete current) |
| `[save]` | Save current session manually (legacy) |
| `[load]` | Load a session from file manually (legacy) |
| `[clear]` | Clear current session history |
| `[history]` | Show current session history |

### Other

| Command | Description |
|---------|-------------|
| `[help]` | Show help |
| `[exit]` | Quit NekoChat (auto-saves all sessions) |

## Directories

NekoChat creates the following files and directories in its working folder:

- `sessions/` — Saved session JSON files
- `pollen_images/` — Generated images
- `pollen_codes/` — Extracted code blocks
- `pollen_exports/` — Exported Markdown conversations
- `config.json` — User preferences (model, system prompt, username, optional `providers` and `plugins`, etc.)
- `plugins/` — Plugin files (`NAME.txt`)
- `keys.json` — API keys saved with `[key]` (owner-only; never commit it)

## Session Management Details

NekoChat supports multiple parallel conversation sessions. Each session is an independent conversation history.

- **Auto-load**: On startup, all `.json` files in `sessions/` are automatically loaded as sessions.
- **Auto-save**: On exit (`[exit]` or Ctrl+D), all sessions are automatically saved back to `sessions/`.
- **Current session indicator**: The prompt shows the active session name: `User[work] :`
- **Session-agnostic config**: `model` (including its service), the global `system_prompt`, `temperature`, and `max_tokens` are global settings shared across all sessions. The one per-session setting is the session system prompt (see below).

## System Prompts

There are two layers:

| Layer | Command | Stored in | Applies to |
|-------|---------|-----------|------------|
| Global | `[system]` | `config.json` | every session |
| Session | `[system session]` | the session's file in `sessions/` | the current session only |

What is sent to the AI is the global prompt, a blank line, then the session prompt, as **one** system message. `[system]` and `[system session]` first show both layers and how many characters are sent. `[sessions]` marks sessions that have a session prompt (`[+prompt]`). `[new]` starts without one, `[rename]` / `[delete]` / `[save]` carry it along, and `[export]` / `[token]` use what is actually sent. A change takes effect from the next message; earlier replies stay in the history, so for a clean break start a new session.

`[load]` (legacy) restores a session's own prompt but no longer overwrites the global one.

## Plugins

A plugin is a named, reusable prompt kept as a plain text file in `plugins/NAME.txt`. Plugins are **data only**: no code and no URLs, so a plugin can add text to the system prompt and tweak a few settings, but it cannot change where your messages are sent.

```
description: Reviews code and lists problems by priority
temperature: 0.2
max_tokens: 1200
model: some-model-id
---
You are an experienced code reviewer.
List the problems you find, most important first.
```

- The header is flat `key: value` lines, ended by a `---` line. Keys: `description` (one line, shown in lists), `temperature` (0.0-2.0), `max_tokens`, `model`. All are optional; unknown keys are an error. A file without a header is simply the prompt text.
- Names use `a-z`, `0-9`, `-` and `_` (up to 40 characters); the prompt text is limited to 20,000 characters.
- `description` is for people only; it is never sent to the AI. Only the prompt text is.

| Command | What it does |
|---------|--------------|
| `[plugin]` | List plugins (`[S]` attached to this session, `[G]` attached to every session) |
| `[plugin show NAME]` | Show the header, settings and text |
| `[plugin on NAME]` | Attach to the current session |
| `[plugin on NAME global]` | Attach to every session |
| `[plugin off NAME]` | Detach (the file stays in `plugins/`) |
| `[plugin new NAME]` | Create a plugin (description, optional settings, then the text; finish with `[end]`) |

**Attaching asks every time.** The screen shows the text length and a preview, and the settings the plugin would change (`temperature : 0.7 -> 0.2`, and which plugin it replaces). NekoChat remembers the file's SHA-256. If the file is edited later — or is missing or invalid — it is **not used** (one notice is shown) until you approve it again with `[plugin on NAME]`. Only names and hashes are stored: `plugins` in `config.json` for global ones, and in the session file for session ones.

**What is sent to the AI** is one system message: the global prompt, the global plugins, the session prompt, then the session plugins (in the order they were attached), separated by blank lines.

**Settings are applied on top, not saved.** While a plugin is attached, its `temperature`, `max_tokens` and `model` are used for requests; `config.json` is never rewritten, and detaching a plugin brings the old values back. Session plugins win over global ones, and later ones over earlier ones. `[config]`, `[model]`, `[system]` and the reply label show what is in effect. A plugin's `model` is a model ID of the **current service** only. When the service's model list is known and does not contain it, the override is ignored with a notice; if the list cannot be checked, it is applied.

Plugin files are plain text, so you can copy them between machines. Treat a file you did not write like any other prompt: its text is sent to the AI service you use.

### Typing and pasting multi-line text

`[system]`, `[system session]`, `[plugin new]` and `[long]` read lines until `[end]` on its own line.

- **Pasted text is read as a whole before it is judged.** `[end]` ends the input only as the last line of a paste (or when typed alone). `[reset]` counts only when it is alone on its line. If either appears elsewhere inside pasted text it is kept as ordinary text and a notice is shown; type `[end]` yourself afterwards.
- Lines that arrive within 0.3 s after `[end]` are discarded and reported, never sent to the AI. A paste that reaches the terminal in pieces more than 0.3 s apart (for example over a slow SSH link) can still leak.
- `[system]` and `[system session]` show a preview (line and character counts, first lines) and ask `Apply? (Y/n)`; the first line's indentation is kept. Ctrl+D cancels instead of applying half-typed text (also when it is typed right after a line); Ctrl+C cancels as before.
- The lines typed here are removed from the up-arrow history.
- Paste detection relies on timing and works on POSIX terminals (Linux, macOS, Termux). On Windows lines are read one at a time, as before.
- `[system <something else>]` prints the usage instead of being sent to the AI.

## Image Generation

Inside `[image]` mode you can:

- Type a prompt to generate an image
- Use `[size]` to change width/height (default 1024x1024, range 64–4096)
- Use `[seed]` to fix a random seed for reproducible images
- Type `exit` to return to chat mode

## Importing Files

`[import]` reads `.md` or `.txt` files and sends them as a user message. You can optionally append a question after the file content. Files larger than 200 KB trigger a confirmation prompt to avoid accidentally sending huge payloads.

## Token Estimate

`[token]` provides a rough token count based on character counts:

- ASCII characters: ~4 chars per token
- Non-ASCII characters: ~1.5 chars per token

This is only an approximation. Actual token counts depend on the model's tokenizer.

## Notes

- Every service has rate limits. If you see HTTP 429, wait a moment and retry; the message names the service.
- Image generation (`[image]`) always uses PollinationsAI's image endpoint, whichever chat service is selected, and may be affected by the same availability issues.
- The `max_tokens` parameter is optional; if unset, the server default is used.
- Image generation parameters (width, height, seed) are session-only and not persisted to `config.json`.
- Session files store model, username, temperature, max_tokens, conversation history, the session's own system prompt (`session_prompt`, only if set) and its attached plugins (`plugins`: names and hashes, only if any). The global system prompt lives in `config.json`; older session files may still contain a `system_prompt` field, which is ignored.

## License

MIT License — feel free to use, modify, and distribute.
