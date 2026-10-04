#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NekoChat v2.8.17 — Clean CLI chat client for several LLM services
(the file is still named pollenchat.py)

Changes in v2.8.17:
  - Discord auto mode: [discord auto on -3:] posts the newest exchanges by itself
    each time 3 new ones are pending; -1: (the default) after every reply. The
    window is written like a Python slice counted from the end (-3: = the last
    three); only -N: (N = 1..20) is accepted. Flags and "to" work as in the
    manual command: [discord auto on -3: bare to main]. [discord auto off],
    [discord auto flush] (send what is pending now), [discord auto] (status).
    It is per session, kept in memory only (off at start-up), counts only
    exchanges made after it was switched on, and shows (discord 2/3) in the
    prompt. Leaving the session ([switch], [new], [load]) or quitting turns it
    off after asking "Send N pending exchange(s) now? (Y/n)". [undo] / [clear]
    / [load] never leave removed exchanges counted as sent (posted messages
    cannot be unsent). A batch needing more than 30 messages is held back with
    the manual command to send it; a webhook that fails is paused for the
    session (resend command shown); Ctrl+C turns the mode off.
  - Posts to the same webhook stay 3 s apart across consecutive sends (also a
    manual send right after an automatic one). Known secrets (API keys, webhook
    URLs/tokens) found in the text are replaced by [redacted] in every Discord
    send.
  - pollinations-key: the model list can be read without a key (the catalogue is
    public); key errors point to https://enter.pollinations.ai/keys (and to the
    NVIDIA / Mistral key pages).

Changes in v2.8.16:
  - [discord ...] posts chosen exchanges to Discord through webhooks. The
    selection and flags are the same as [export]:
      [discord]                         registered webhooks (URL hidden) + usage
      [discord add webhook [LABEL]]     register one (the URL is typed hidden)
      [discord rm LABEL]                remove one
      [discord list]                    the same numbered list as [export list]
      [discord -1] / [discord 2:5 rev bare full] [to LABEL... | webhook | all]
    Webhook URLs hold a secret token, so they live in discord_webhooks.txt
    (owner-only, git-ignored; "URL" or "LABEL URL" per line, '#' comments, or a
    JSON array/object) and/or DISCORD_WEBHOOK_URL (label "env"), never in
    config.json, and are never printed (errors are scrubbed too). Only
    https://discord.com/api/webhooks/ID/TOKEN (optionally ?thread_id=ID) is
    accepted. With no "to", every registered webhook receives the message.
  - Every send shows the destinations, message/post counts, characters, the
    estimated time and a preview, and asks first. Long answers are cut at line
    boundaries (code fences closed and reopened, length counted in UTF-16,
    "(続く...)" on all but the last part). @everyone/role pings are disabled.
    Posts to the SAME webhook (by ID) are 3 s apart; different webhooks follow
    each other at once. HTTP 429 waits retry_after (at most 5 times, 60 s each).
    A webhook that fails stops receiving; the others carry on; Ctrl+C stops
    cleanly; the result is reported per webhook.

Changes in v2.8.15:
  - Plugins: named, reusable prompts kept as plain text in plugins/NAME.txt
    (flat "key: value" header with description / temperature / max_tokens /
    model, a "---" line, then the prompt text; a file without a header is just
    the text). Plugins are DATA ONLY - no code, no URLs.
      [plugin]                  list ([S] = this session, [G] = every session)
      [plugin show NAME]        header, settings and text
      [plugin on NAME [global]] attach to this session / to every session
      [plugin off NAME]         detach (the file is kept)
      [plugin new NAME]         create one (description, optional settings, text)
    Attaching shows what it adds and changes and asks for confirmation every
    time. The file's SHA-256 is remembered (only names + hashes are stored:
    "plugins" in config.json / in the session file); a plugin that was edited
    since, or is missing or invalid, is NOT used (one notice) until it is
    approved again with [plugin on NAME]. What is sent: global text, global
    plugins, session text, session plugins (attach order), one system message.
  - A plugin's temperature / max_tokens / model apply only while it is attached,
    on top of config.json, which is never rewritten (session plugins beat global
    ones, later beat earlier). "model" is an ID of the CURRENT service; if the
    service's model list is known and lacks it, it is ignored with a notice.
    [config], [model], [system] and the reply label show what is in effect.
  - Fix: Ctrl+D typed right after a line in [system], [system session],
    [plugin new] or [long] could hang the input (the terminal's EOF state was
    lost when readline switched modes while checking for pasted lines).

Changes in v2.8.14:
  - System prompt layers. [system] sets the GLOBAL prompt (as before, shared by
    every session). New [system session] sets a prompt for the CURRENT session
    only. What is sent is the global prompt, a blank line, then the session
    prompt, as ONE system message. The session prompt is stored in the session
    file ("session_prompt") and follows [rename], [delete] and [save]; [new]
    starts without one. [sessions] marks sessions that have one. [export] and
    [token] use what is actually sent.
  - The "system_prompt" field that used to be copied into every session file
    was only a snapshot of the global setting and is no longer written or
    read. [load] no longer overwrites the global system prompt with it (the
    same rule as the user name since v2.8.12); it restores the session prompt.
  - [system], [system session] and [long] share one block reader:
      * a pasted burst is read whole before it is judged: [end] ends the block
        only as the last line of a burst (or typed alone) and [reset] only when
        it is alone; elsewhere they stay ordinary text, with a notice. The rest
        of a paste is no longer sent to the AI as a chat message;
      * lines arriving within 0.3s after [end] are dropped and reported;
      * lines typed in the block are removed from the readline history;
      * Ctrl+D cancels instead of applying half-typed text; [system] and
        [system session] show a preview and ask "Apply? (Y/n)" first, and the
        first line's indentation is kept.
    Pastes that arrive in pieces more than 0.3s apart can still leak.
  - [system <anything else>] prints the usage instead of going to the AI.

Changes in v2.8.13:
  - Works with more than PollinationsAI. Built in: PollinationsAI (anonymous
    legacy endpoint), PollinationsAI with an API key, NVIDIA, Mistral and
    Cloudflare Workers AI - all OpenAI-compatible. The stored model string is
    "service/model-id"; a bare name (e.g. "openai") still means PollinationsAI,
    so old config.json and session files keep working.
  - New [service]: pick a service, enter its API key if needed, then pick a
    model. The service only changes once a model has been chosen.
    [model] now chooses within the current service. Model lists are fetched
    from the service on demand (cached for 10 minutes; filter when long; type
    a model ID by hand when a service has no list). Nothing is fetched at start.
  - New [key]: set or remove API keys (hidden input). Lookup order: key entered
    this session > environment variable > keys.json. keys.json is written with
    owner-only permissions and listed in .gitignore. Keys are never written to
    config.json, session files or exports.
  - Optional "providers" block in config.json: override a built-in service or
    add your own OpenAI-compatible one (chat_url, models_url, key_env, label,
    vars ...). ${VAR} in URLs is expanded from the environment, then from
    "vars" (Cloudflare's account ID is asked for by [service] and kept there).
    https only (plain http only for localhost). No keys in this block.
  - Errors name the service. 401/403 point at the key, 429 shows the service's
    own hint, and 402/5xx on the anonymous PollinationsAI endpoint suggest
    switching service.
  - Banner, prompt, exports and User-Agent now say NekoChat.

Fixes in v2.8.12:
  - New [name] command to change your display name (it used to be asked only
    once, at first start). Names are NFC-normalised, limited to 24 display
    columns (CJK and emoji count as 2) and must not contain control,
    zero-width or combining characters (they break readline's cursor math).
  - Each user message now stores the name it was sent under (a "name" field
    in the session file). Older logs are filled from the "username" saved in
    the session file. [history], [search], [sessions] and [export] show these
    names, so a rename does not rewrite the past. [sessions] lists the name
    flow, e.g. "A → B". The "name" field is never sent to the API.
  - [load] no longer overwrites the current name with the one stored in the
    session file (the name is a user setting, not session data).
  - The first-start name prompt uses the same validation.

Fixes in v2.8.11:
  - [export] by exchange (question + answer): [export list], [export -1],
    [export -3:], [export 2:5], [export ::-1] with rev / bare / full flags.
    Indexes and slices follow Python (0 = oldest, -1 = latest, stop excluded).
    Long questions are shortened to head + tail with a note.
  - send_chat: HTTP errors now show the server's reason. New helper
    _server_error_text() reads the JSON "error" field (or the response body).
    5xx are reported as server-side problems, 429 keeps its rate-limit
    message, and other codes (402, 404, ...) get the reason appended.
  - Input prompt: the "user[session] :" prompt is now passed to input() via
    _read_input(prompt) so readline knows about it. It used to be printed
    separately, and line editing (Backspace to line start, Home, history
    redraw) erased it. On GNU readline the colour codes are marked as
    zero-width with 0x01/0x02 (_rl_safe) so long lines keep the correct
    cursor position. _ask() prompts ([model], [import], ...) go through
    _rl_safe() as well. Paste merging in _pending_lines() is unchanged.

Fixes in v2.8.10:
  - _truncate_at_turn now requires 2+ turn markers (outside ``` blocks)
    before truncating. This reduces false positives: a single role label
    like "AI:" or "User:" in definitions / examples / translation tables
    is no longer cut.  Note that text with 2+ labels (e.g. a translation
    table with both "User:" and "AI:") is still truncated — use batch mode
    or turn guard OFF for such content.
  - stream_response: when exactly one marker is seen during streaming,
    display is held back from that point onward until either (a) a second
    marker confirms a fake turn (truncate) or (b) the stream ends with only
    one marker (legitimate content — flush the held-back tail). This prevents
    the first fake "User:" line from appearing on screen before truncation.
  - Fixed: _find_turn_markers() now checks _turn_guard_enabled so guard OFF
    no longer truncates or holds back display in stream mode.
  - Turn guard now also ignores markers inside ``` code blocks.
  - Improved [guard] help text and toggle message to warn about false
    positives.

Fixes in v2.8.9:
  - Added _read_input() with multi-line paste detection (POSIX only).
    Pasted text with newlines is merged into a single message instead of
    being processed line-by-line, which caused unstoppable AI response loops.
  - Pasted multi-line text is never interpreted as commands (prevents pasted
    text containing bracketed words like [exit] from triggering commands).

Fixes in v2.8.8:
  - Default _stream_mode changed to False (batch) to avoid phantom input loops
    on browser-based terminals (Colab xterm.js, etc.)
  - Added sys.stdout.flush() guards around stream output and prompt input
  - HELP_TEXT warns that streaming may misbehave on web terminals

Fixes in v2.8.7:
  - Turn guard: truncate AI responses at fake User:/Assistant:/AI: markers
    to prevent free-tier models from generating phantom conversation turns
  - [guard] command to toggle turn guard (default: ON)

Fixes in v2.8.6:
  - Removed \001/\002 ANSI wrapping in _rl_prompt() to prevent readline/libedit
    from mis-handling prompts and causing phantom auto-input on some terminals

Fixes in v2.8.5:
  - [save]: assign _sessions[name] BEFORE _save_session_atomic() so the new file
    is no longer written with an empty (or stale) history
  - main prompt now goes through _ask() like every other prompt

Fixes in v2.8.4:
  - _rl_prompt() is now conditional: only wraps ANSI codes when readline is present
  - All colored input() prompts go through _rl_prompt() for consistent readline safety
  - [size] validates dimensions before assigning to _img_width/_img_height
  - [rename] skips os.remove() when old and new resolve to the same file
  - _sanitize_session_name strips trailing .json so keys stay consistent
  - [save] now uses _save_session_atomic() for crash-safe writes
  - stream_response hardened against non-list choices / non-dict delta

Fixes in v2.8.3:
  - _auto_load_all_sessions() moved after banner so broken-JSON warnings are visible
  - rename_session: save new session before removing old file (crash safety)
  - undo_last / clear_history: auto-save current session immediately
  - readline-safe ANSI prompt wrapper to prevent display glitches
  - stream_response: guard against non-dict JSON payloads
  - [save]: sanitize session name with _sanitize_session_name
  - [system]: empty-input guard with .strip()
  - [size]: validate dimensions at input time
  - HELP_TEXT: add missing em-dash for [model]

Fixes in v2.8.2:
  - [long] / [system] now use [end] terminator (empty lines are preserved)
  - [save] copy-on-write to avoid shared list references
  - [clear] resets _last_assistant_text so [render]/[savecode] don't see stale data
  - generate_image: quote(prompt, safe="") to handle slashes in prompts
  - Atomic per-session auto-save after every successful chat_once
  - _auto_load_all_sessions warns about broken JSON instead of silently skipping
  - batch_response / stream_response guard against malformed choices
  - Image size validation (64–4096)
  - Seed=0 is now handled correctly (0 is falsy but valid)
  - import_file: expand ~ and strip surrounding quotes from path
  - readline support on Unix for arrow-key editing
  - rename_session early-return when name is unchanged
  - estimate_tokens notes MAX_HISTORY limit
  - _prompt_float unused "current" argument removed

New features in v2.8:
  - Multi-session management: [sessions] [switch] [new] [rename] [delete]
  - Auto-load all sessions on startup, auto-save all on exit
  - Session name shown in the prompt

API Docs: https://github.com/pollinations/pollinations/blob/master/APIDOCS.md
"""

from __future__ import annotations

import os
import sys
import json
import getpass
import copy
import hashlib
import time
import re
import random
import unicodedata
import datetime
import requests
from typing import Any, Optional
from urllib.parse import quote

from colorama import init, Fore, Style

init(autoreset=True)

# Enable line editing / history on Unix terminals
# (no effect on Windows without pyreadline, but harmless)
try:
    import readline  # noqa: F401
    # libedit (macOS) treats prompt markers differently: only GNU readline gets them
    _READLINE_GNU = "libedit" not in (readline.__doc__ or "")
except ImportError:
    _READLINE_GNU = False

# ============ CONFIG ============
API_BASE = "https://text.pollinations.ai/openai"
IMAGE_BASE = "https://image.pollinations.ai/prompt"
MODELS_URL = "https://text.pollinations.ai/models"

# ============ PROVIDERS ============
# Registry of OpenAI-compatible chat services. Keep only slow-changing facts here
# (URLs, key env var names); model lists are fetched from the service at runtime.
#   chat_url  : full chat-completions endpoint (${VAR} is expanded from the environment,
#               then from the service's "vars" in config.json)
#   models_url: model list endpoint, or None if unavailable (manual model ID entry)
#   key_env   : environment variable holding the API key, or None (no key needed)
#   rate_hint : shown on HTTP 429
PROVIDERS: dict[str, dict[str, Any]] = {
    "pollinations": {
        "label": "PollinationsAI",
        "chat_url": API_BASE,
        "models_url": MODELS_URL,
        "key_env": None,
        "rate_hint": "PollinationsAI free tier has limits. Wait a moment and retry.",
        "fail_hint": (
            "The anonymous legacy endpoint may be down or no longer free. Switch with [service], or set "
            "POLLINATIONS_API_KEY and use the pollinations-key service."
        ),
    },
    "pollinations-key": {
        "label": "PollinationsAI (API key)",
        "chat_url": "https://gen.pollinations.ai/v1/chat/completions",
        "models_url": "https://gen.pollinations.ai/v1/models",
        "models_public": True,   # the catalogue can be read without a key
        "key_env": "POLLINATIONS_API_KEY",
        "key_url": "https://enter.pollinations.ai/keys",
        "rate_hint": "PollinationsAI rate limit or Pollen balance reached. Wait a moment and retry.",
    },
    "nvidia": {
        "label": "NVIDIA",
        "chat_url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "models_url": "https://integrate.api.nvidia.com/v1/models",
        "key_env": "NVIDIA_API_KEY",
        "key_url": "https://build.nvidia.com",
        "rate_hint": "NVIDIA rate limit reached. Wait a moment and retry.",
    },
    "mistral": {
        "label": "Mistral",
        "chat_url": "https://api.mistral.ai/v1/chat/completions",
        "models_url": "https://api.mistral.ai/v1/models",
        "key_env": "MISTRAL_API_KEY",
        "key_url": "https://console.mistral.ai",
        "rate_hint": "Mistral free-tier rate limit reached. Wait a moment and retry.",
    },
    "cloudflare": {
        "label": "Cloudflare Workers AI",
        "chat_url": "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/ai/v1/chat/completions",
        "models_url": None,
        "key_env": "CLOUDFLARE_API_TOKEN",
        "rate_hint": "Cloudflare daily free allocation may be used up (resets 00:00 UTC). Retry later.",
    },
}
DEFAULT_PROVIDER = "pollinations"
_BUILTIN_PROVIDERS = copy.deepcopy(PROVIDERS)

# ---- user-defined / overridden services (the optional "providers" block of config.json) ----
# {"providers": {"cloudflare": {"vars": {"CLOUDFLARE_ACCOUNT_ID": "..."}},
#                "groq": {"chat_url": "https://api.groq.com/openai/v1/chat/completions",
#                         "models_url": "https://api.groq.com/openai/v1/models",
#                         "key_env": "GROQ_API_KEY"}}}
# API keys never go here (use [key] / keys.json / environment variables).
_providers_cfg: dict[str, dict[str, Any]] = {}
_config_warnings: list[str] = []
_PROVIDER_STR_FIELDS = ("label", "chat_url", "models_url", "key_env", "rate_hint", "fail_hint")
_NULLABLE_FIELDS = ("models_url", "key_env")
_LOCAL_HTTP = re.compile(r"^http://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?(/|$)")

def _url_ok(url: str) -> bool:
    """https only; plain http is accepted for a local server (e.g. Ollama)."""
    return url.startswith("https://") or bool(_LOCAL_HTTP.match(url))

def apply_providers_config(block: object) -> None:
    """Rebuild PROVIDERS from the built-ins plus the config.json block. Bad entries are
    skipped with a warning (shown after the banner)."""
    global _providers_cfg
    PROVIDERS.clear()
    PROVIDERS.update(copy.deepcopy(_BUILTIN_PROVIDERS))
    _providers_cfg = {}
    if block is None:
        return
    if not isinstance(block, dict):
        _config_warnings.append("config.json: 'providers' must be an object; ignored.")
        return
    for name, ov in block.items():
        where = f"config.json providers.{name}"
        if not isinstance(name, str) or not isinstance(ov, dict):
            _config_warnings.append(f"{where}: must be an object; ignored.")
            continue
        is_new = name not in PROVIDERS
        if is_new and not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
            _config_warnings.append(f"{where}: service names use a-z, 0-9 and '-' only; ignored.")
            continue
        clean: dict[str, Any] = {}
        for k, v in ov.items():
            if k in _PROVIDER_STR_FIELDS:
                if v is None and k in _NULLABLE_FIELDS:
                    clean[k] = None
                elif isinstance(v, str) and v.strip():
                    clean[k] = v.strip()
                else:
                    _config_warnings.append(f"{where}.{k}: must be a non-empty string; ignored.")
            elif k == "vars":
                if isinstance(v, dict) and all(isinstance(a, str) and isinstance(b, str) for a, b in v.items()):
                    clean["vars"] = dict(v)
                else:
                    _config_warnings.append(f"{where}.vars: must be an object of strings; ignored.")
            elif k.lower().replace("_", "") in ("apikey", "key", "token"):
                _config_warnings.append(f"{where}.{k}: keys are not read from config.json; use [key].")
            else:
                _config_warnings.append(f"{where}.{k}: unknown field; ignored.")
        for k in ("chat_url", "models_url"):
            if clean.get(k) and not _url_ok(clean[k]):
                _config_warnings.append(f"{where}.{k}: only https:// (or http://localhost) is allowed; ignored.")
                clean.pop(k)
        if is_new and not clean.get("chat_url"):
            _config_warnings.append(f"{where}: a new service needs a valid chat_url; ignored.")
            continue
        if not clean:
            continue
        if is_new:
            PROVIDERS[name] = {
                "label": name, "chat_url": None, "models_url": None, "key_env": None,
                "rate_hint": f"{name}: rate limit reached. Wait a moment and retry.",
            }
        PROVIDERS[name].update(clean)
        _providers_cfg[name] = clean

def _flush_config_warnings() -> None:
    for w in _config_warnings:
        print(f"{Fore.YELLOW}[!] {w}{Style.RESET_ALL}")
    _config_warnings.clear()

def split_model(full: str) -> tuple[str, str]:
    """'nvidia/meta/llama-3.1-70b-instruct' -> ('nvidia', 'meta/llama-3.1-70b-instruct').

    Only a registered first segment counts as a provider; anything else
    (e.g. a bare 'openai') is a PollinationsAI model name, so old configs keep working.
    """
    head, sep, rest = full.partition("/")
    if sep and rest and head in PROVIDERS:
        return head, rest
    return DEFAULT_PROVIDER, full

# ============ API KEYS ============
# Lookup order: [key] entered this session > environment variable > keys.json.
# Keys never go into config.json, session files or exports.
KEYS_FILE = "keys.json"
_session_keys: dict[str, str] = {}

def load_keys() -> dict[str, str]:
    """Read keys.json ({service: key}). Missing or broken file -> {}."""
    try:
        with open(KEYS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {k: v.strip() for k, v in data.items()
            if isinstance(k, str) and isinstance(v, str) and v.strip()}

def save_keys(keys: dict[str, str]) -> bool:
    """Write keys.json readable by the owner only (chmod 600)."""
    try:
        fd = os.open(KEYS_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(keys, f, ensure_ascii=False, indent=2)
        try:
            os.chmod(KEYS_FILE, 0o600)  # also tighten a pre-existing file
        except OSError:
            pass
        return True
    except OSError as e:
        print(f"{Fore.RED}[!] Could not save {KEYS_FILE}: {e}{Style.RESET_ALL}")
        return False

def get_api_key(provider: str) -> Optional[str]:
    env = PROVIDERS[provider].get("key_env")
    if not env:
        return None
    if _session_keys.get(provider):
        return _session_keys[provider]
    val = (os.environ.get(env) or "").strip()
    if val:
        return val
    return load_keys().get(provider) or None

def key_source(provider: str) -> Optional[str]:
    """Where the key currently in use comes from: 'session', 'env', 'keys.json' or None."""
    env = PROVIDERS[provider].get("key_env")
    if not env:
        return None
    if _session_keys.get(provider):
        return "session"
    if (os.environ.get(env) or "").strip():
        return "env"
    if load_keys().get(provider):
        return "keys.json"
    return None

def _mask_key(key: str) -> str:
    return "..." + key[-4:] if len(key) >= 12 else "****"

def _expand_env(text: str, extra: Optional[dict[str, str]] = None) -> tuple[str, list[str]]:
    """Expand ${VAR} from the environment, then from `extra` (a service's "vars").
    Returns (text, names of missing variables)."""
    missing: list[str] = []
    def repl(m: re.Match) -> str:
        val = os.environ.get(m.group(1)) or (extra or {}).get(m.group(1))
        if not val:
            missing.append(m.group(1))
            return ""
        return val
    return re.sub(r"\$\{([A-Za-z0-9_]+)\}", repl, text), missing

def _key_hint(spec: dict) -> str:
    return f"; get one at {spec['key_url']}" if spec.get("key_url") else ""


def resolve_request(full_model: str) -> Optional[tuple[str, str, dict[str, str]]]:
    """Return (url, model_id, extra_headers) for the model, or None after printing why not."""
    provider, model_id = split_model(full_model)
    spec = PROVIDERS[provider]
    url, missing = _expand_env(str(spec["chat_url"]), spec.get("vars"))
    if missing:
        print(f"{Fore.RED}[!] {spec['label']}: not set: {', '.join(missing)} "
              f"(environment variable, or providers.{provider}.vars in config.json){Style.RESET_ALL}")
        return None
    headers: dict[str, str] = {}
    if spec.get("key_env"):
        key = get_api_key(provider)
        if not key:
            print(f"{Fore.RED}[!] {spec['label']}: API key not set "
                  f"(use [key] or set {spec['key_env']}{_key_hint(spec)}){Style.RESET_ALL}")
            return None
        headers["Authorization"] = f"Bearer {key}"
    return url, model_id, headers

SESSION_DIR = "sessions"
IMAGE_DIR = "pollen_images"
CODE_DIR = "pollen_codes"
EXPORT_DIR = "pollen_exports"
PLUGIN_DIR = "plugins"
CONFIG_FILE = "config.json"
MAX_HISTORY = 20
IMPORT_MAX_BYTES = 200_000

# Extension map for code block languages
LANG_EXT = {
    "python": ".py", "py": ".py",
    "javascript": ".js", "js": ".js",
    "typescript": ".ts", "ts": ".ts",
    "jsx": ".jsx", "tsx": ".tsx",
    "html": ".html", "css": ".css", "json": ".json",
    "bash": ".sh", "sh": ".sh", "shell": ".sh", "zsh": ".zsh",
    "cpp": ".cpp", "c++": ".cpp", "c": ".c",
    "go": ".go", "rust": ".rs", "rs": ".rs",
    "java": ".java", "kotlin": ".kt", "swift": ".swift",
    "ruby": ".rb", "rb": ".rb", "php": ".php",
    "sql": ".sql", "yaml": ".yaml", "yml": ".yml",
    "toml": ".toml", "xml": ".xml",
    "dockerfile": ".dockerfile", "docker": ".dockerfile",
    "makefile": ".mk", "cmake": ".cmake",
    "lua": ".lua", "r": ".r",
    "perl": ".pl", "pl": ".pl",
    "haskell": ".hs", "hs": ".hs",
    "scala": ".scala", "dart": ".dart",
    "julia": ".jl", "matlab": ".m",
    "vim": ".vim", "ini": ".ini", "cfg": ".cfg",
    "csv": ".csv", "markdown": ".md", "md": ".md",
    "tex": ".tex", "latex": ".tex",
}

# ============ BANNER ============
BANNER = r"""
    _   __     __            ________          __
   / | / /__  / /______     / ____/ /_  ____ _/ /_
  /  |/ / _ \/ //_/ __ \   / /   / __ \/ __ `/ __/
 / /|  /  __/ ,< / /_/ /  / /___/ / / / /_/ / /_
/_/ |_/\___/_/|_|\____/   \____/_/ /_/\__,_/\__/
                                          v2.8.17
        Clean & Harmless — Multi-service LLM chat
"""

# ============ STATE ============
_sessions: dict[str, list[dict[str, str]]] = {"default": []}
_current_session: str = "default"
_session_last_text: dict[str, str] = {}
_session_prompts: dict[str, str] = {}   # per-session layer, added after the global one
_plugins_global: list[dict[str, str]] = []              # [{"name", "sha256"}] used by every session
_session_plugins: dict[str, list[dict[str, str]]] = {}  # same, per session
_warned: set[str] = set()

current_model: str = "openai"
DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."
_system_prompt: str = DEFAULT_SYSTEM_PROMPT   # global layer
_temperature: float = 0.7
_max_tokens: Optional[int] = None
_stream_mode: bool = False  # default batch mode: safer on browser terminals
_last_assistant_text: str = ""
_turn_guard_enabled: bool = False  # opt-in: stops AI from generating fake user/assistant turns

# Image mode defaults (not persisted in config)
_img_width: int = 1024
_img_height: int = 1024
_img_seed: Optional[int] = None

username: str = "User"

# ============ UTILS ============
def clear() -> None:
    os.system("clear" if os.name == "posix" else "cls")

def ensure_dirs() -> None:
    os.makedirs(SESSION_DIR, exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)
    os.makedirs(CODE_DIR, exist_ok=True)
    os.makedirs(EXPORT_DIR, exist_ok=True)
    os.makedirs(PLUGIN_DIR, exist_ok=True)

def _safe_session_name(name: str) -> str:
    name = os.path.basename(name.strip())
    if not name:
        name = "session"
    return name if name.endswith(".json") else name + ".json"

def _safe_filename(name: str) -> str:
    name = os.path.basename(name.strip())
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    return name or "snippet"

def _sanitize_session_name(name: str) -> str:
    name = name.strip()
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    # Strip trailing .json so "foo.json" becomes "foo" and stays consistent
    if name.lower().endswith(".json"):
        name = name[:-5]
    return name or "untitled"

# Turn guard (opt-in via [guard]): some free-tier models keep generating fake
# User:/Assistant: turns. We truncate the response at the first marker when
# *two or more* such markers are found outside ``` code blocks. A single
# marker is treated as legitimate content (definitions, examples, etc.).
_TURN_RE = re.compile(
    r"\n[ \t]*(?:User|Assistant|AI)[ \t]*[:：]",
    re.IGNORECASE,
)
_TURN_WORDS = ("user", "assistant", "ai")


def _truncate_at_turn(text: str) -> str:
    """Truncate text at the first turn-marker if turn guard is enabled.

    To reduce false positives (e.g. definitions like "AI: artificial
    intelligence" or "User: 利用者"), we only truncate when *two or more*
    turn markers are found outside ``` code blocks. A single marker is
    treated as intentional content (definitions, examples, etc.).
    """
    if not _turn_guard_enabled:
        return text

    # Collect markers that are NOT inside ``` code blocks
    matches = []
    for m in _TURN_RE.finditer(text):
        backticks_before = text[: m.start()].count("```")
        if backticks_before % 2 == 0:  # outside code block
            matches.append(m)

    # Need 2+ markers to be confident it is a fake conversation turn sequence.
    # A lone marker is usually a definition, translation table, or example.
    if len(matches) < 2:
        return text

    first = matches[0]
    return text[: first.start()]


def _find_turn_markers(text: str) -> list[int]:
    """Return start positions of turn markers that are outside ``` blocks."""
    if not _turn_guard_enabled:
        return []
    positions = []
    for m in _TURN_RE.finditer(text):
        if text[: m.start()].count("```") % 2 == 0:
            positions.append(m.start())
    return positions


def _held_back_len(text: str) -> int:
    """Length of the tail that may be the start of a turn marker split across
    stream chunks (e.g. "\nUs" + "er:"). Streaming holds these back until the
    next chunk shows whether they really are a marker."""
    if not _turn_guard_enabled:
        return 0
    nl = text.rfind("\n")
    if nl == -1:
        return 0
    tail = text[nl + 1:].lstrip(" \t").lower()
    word = tail.rstrip(" \t")
    if word == "" or any(w.startswith(word) for w in _TURN_WORDS):
        return len(text) - nl
    return 0


def _stdin_at_eof() -> bool:
    """True if stdin is readable only because of an end-of-input condition (no bytes queued).

    A Ctrl+D typed right after a line leaves the terminal in canonical mode with an
    "EOF pending" state: select() reports it readable, but readline's raw-mode input()
    would block forever because switching modes drops that state. The state is consumed
    here so it does not linger either."""
    try:
        import fcntl
        import struct
        import termios
        fd = sys.stdin.fileno()
        queued = struct.unpack("i", fcntl.ioctl(fd, termios.FIONREAD, struct.pack("i", 0)))[0]
        if queued == 0:
            os.read(fd, 1)
            return True
    except Exception:
        pass
    return False

def _pending_lines(wait: float = 0.1, eof_out: Optional[list] = None) -> list[str]:
    """Return extra lines already waiting on stdin (i.e. pasted text).

    Terminal paste is far faster than typing, so if more input arrives within
    0.1s of the previous line it is treated as part of the same paste.
    POSIX only: Windows select() does not support stdin, so nothing is
    detected there (Windows paste behaviour is less prone to this issue).
    If stdin hits EOF while draining, True is appended to `eof_out` (when given) so
    the caller can tell Ctrl+D apart from "no more lines".
    """
    extra: list[str] = []
    if os.name != "posix":
        return extra
    import select
    try:
        while True:
            readable, _, _ = select.select([sys.stdin], [], [], wait)
            if sys.stdin not in readable:
                break
            if _stdin_at_eof():
                if eof_out is not None:
                    eof_out.append(True)
                break
            try:
                extra.append(input())
            except EOFError:
                if eof_out is not None:
                    eof_out.append(True)
                break
    except (OSError, ValueError):
        pass
    return extra


def _history_len() -> int:
    try:
        import readline
        return readline.get_current_history_length()
    except Exception:
        return 0

def _prune_history(start: int) -> None:
    """Drop readline history entries added since `start` (lines typed into a block
    must not come back with the up-arrow at the chat prompt)."""
    try:
        import readline
        for i in range(readline.get_current_history_length(), start, -1):
            readline.remove_history_item(i - 1)
    except Exception:
        pass

LATE_LINES_WAIT = 0.3  # seconds to wait for stragglers after [end]

def read_block(allow_reset: bool = False) -> tuple[list[str], str, int]:
    """Read lines until [end] (used by [system], [system session] and [long]).

    Returns (lines, status, literal) where status is "end", "reset" or "eof" and
    `literal` counts [end]/[reset] lines that were kept as text.

    Pasted text arrives as a burst of lines. A whole burst is read before it is
    judged, so a command word inside pasted text is not acted on half-way (the
    rest of the paste would otherwise leak into the chat as a message):
      - [end] ends the block only as the LAST line of a burst (or typed alone);
      - [reset] (when allowed) counts only when it is the only line of a burst;
      - anywhere else they are kept as ordinary text and reported.
    Lines arriving shortly after the end are dropped, never sent to the AI.
    Lines typed here are removed from the readline history.
    """
    specials = {"[end]"} | ({"[reset]"} if allow_reset else set())
    start = _history_len()
    lines: list[str] = []
    literal = 0
    status = "eof"
    late: list[str] = []
    try:
        while True:
            try:
                first = input()
            except EOFError:
                status = "eof"
                break
            eof_hit: list[bool] = []
            burst = [first] + _pending_lines(eof_out=eof_hit)
            if eof_hit:  # Ctrl+D arrived right behind the line
                lines.extend(burst)
                status = "eof"
                break
            tail = burst[-1].strip()
            if tail == "[end]":
                content, status = burst[:-1], "end"
            elif allow_reset and len(burst) == 1 and tail == "[reset]":
                content, status = [], "reset"
            else:
                content, status = burst, ""
            kept = sum(1 for ln in content if ln.strip() in specials)
            if kept:  # tell the user right away, while they can still type [end]
                print(
                    f"{Fore.YELLOW}[~] {kept} line(s) of [end]/[reset] inside pasted text were "
                    f"kept as text. To finish, type [end] on its own line.{Style.RESET_ALL}"
                )
            literal += kept
            lines.extend(content)
            if status:
                break
        if status in ("end", "reset"):
            late = _pending_lines(LATE_LINES_WAIT)
    finally:
        _prune_history(start)
    if late:
        print(
            f"{Fore.YELLOW}[~] Discarded {len(late)} line(s) that arrived after [end] "
            f"(first: {late[0][:40]!r}).{Style.RESET_ALL}"
        )
    return lines, status, literal

def _join_block(lines: list[str]) -> str:
    """Join lines; drop blank lines at both ends but keep the first line's indentation."""
    i, j = 0, len(lines)
    while i < j and not lines[i].strip():
        i += 1
    while j > i and not lines[j - 1].strip():
        j -= 1
    return "\n".join(lines[i:j]).rstrip()

def _confirm_block(text: str, target: str) -> bool:
    """Show a short preview of `text` and ask before applying it."""
    n_lines = text.count("\n") + 1
    print(f"\n{Fore.YELLOW}Received {n_lines} line(s), {len(text):,} characters:{Style.RESET_ALL}")
    for ln in text.split("\n")[:3]:
        print(f"  {ln[:80]}{'…' if len(ln) > 80 else ''}")
    if n_lines > 3:
        print(f"  … ({n_lines - 3} more line(s))")
    answer = _ask(f"{Fore.CYAN}[+] Apply to {target}? (Y/n): {Style.RESET_ALL}").lower()
    return answer in ("", "y", "yes")

def _ask(prompt_text: str, multiline: bool = False) -> str:
    """Wrapper around input().

    Extra pasted lines are not left in the buffer (they would otherwise leak
    into the next prompt and be sent to the AI as separate messages). With
    multiline=True they are joined into the answer; otherwise they are
    discarded with a notice.
    """
    first = input(_rl_safe(prompt_text))
    extra = _pending_lines()
    if extra:
        if multiline:
            return "\n".join([first] + extra).strip()
        print(
            f"{Fore.YELLOW}[~] Ignored {len(extra)} extra pasted line(s); "
            f"only the first line was used.{Style.RESET_ALL}"
        )
    return first.strip()


def _rl_safe(prompt: str) -> str:
    """Mark ANSI colour codes in a prompt as zero-width for GNU readline.

    Without the 0x01 ... 0x02 markers readline counts the escape bytes as
    visible columns and mis-places the cursor on long lines.
    """
    if not _READLINE_GNU:
        return prompt
    return re.sub(r"(\x1b\[[0-9;]*m)", "\x01\\1\x02", prompt)


def _read_input(prompt: str = "") -> tuple[str, bool]:
    """Read input, detecting multi-line paste and merging into a single message.

    The prompt is passed to input() so that readline manages it (redraws keep it).

    When a user pastes multi-line text into a terminal, each line is fed to
    stdin separately. We detect this by checking if more lines arrive within a
    short timeout (0.1s) after the first line. Human typing is too slow to
    trigger this; only pasted text does.

    Returns:
        (text, is_paste): text is the merged input, is_paste is True if
        multiple lines were detected and merged.
    """
    lines = [input(prompt)] + _pending_lines()

    is_paste = len(lines) > 1
    if is_paste:
        print(
            f"{Fore.CYAN}[~] Detected {len(lines)} pasted lines; "
            f"merged into one message.{Style.RESET_ALL}"
        )

    return "\n".join(lines), is_paste

# ============ CONFIG ============
def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}

def save_config(cfg: dict) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"{Fore.RED}[!] Config save failed: {e}{Style.RESET_ALL}")

def apply_config(cfg: dict) -> None:
    global current_model, _system_prompt, username, _stream_mode, _temperature, _max_tokens
    if "model" in cfg and isinstance(cfg["model"], str):
        current_model = cfg["model"]
    if "providers" in cfg:
        apply_providers_config(cfg["providers"])
    if "plugins" in cfg:
        cleaned = _clean_plugin_entries(cfg["plugins"])
        if not isinstance(cfg["plugins"], list) or len(cleaned) != len(cfg["plugins"]):
            _config_warnings.append("config.json: some 'plugins' entries were invalid and ignored.")
        _plugins_global[:] = cleaned
    if "system_prompt" in cfg and isinstance(cfg["system_prompt"], str):
        _system_prompt = cfg["system_prompt"]
    if "username" in cfg and isinstance(cfg["username"], str):
        username = cfg["username"]
    if "stream_mode" in cfg and isinstance(cfg["stream_mode"], bool):
        _stream_mode = cfg["stream_mode"]
    if "temperature" in cfg and isinstance(cfg["temperature"], (int, float)):
        _temperature = float(cfg["temperature"])
    if "max_tokens" in cfg:
        if cfg["max_tokens"] is None:
            _max_tokens = None
        elif isinstance(cfg["max_tokens"], int) and not isinstance(cfg["max_tokens"], bool):
            _max_tokens = cfg["max_tokens"]

def build_config() -> dict:
    cfg: dict[str, Any] = {
        "model": current_model,
        "system_prompt": _system_prompt,
        "username": username,
        "stream_mode": _stream_mode,
        "temperature": _temperature,
        "max_tokens": _max_tokens,
    }
    if _providers_cfg:  # only written when the user has customised services
        cfg["providers"] = _providers_cfg
    if _plugins_global:
        cfg["plugins"] = _plugins_global
    return cfg

# ============ MARKDOWN RENDERER ============
def render_markdown(text: str) -> str:
    result = []
    in_code_block = False

    for raw_line in text.splitlines(keepends=True):
        line = raw_line.rstrip("\n\r")

        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            if in_code_block:
                lang = line.strip()[3:].strip()
                result.append(f"{Fore.CYAN}▶ {lang if lang else 'code'}{Style.RESET_ALL}\n")
            else:
                result.append(f"{Fore.CYAN}◀{Style.RESET_ALL}\n")
            continue

        if in_code_block:
            result.append(f"{Fore.LIGHTBLACK_EX}{line}{Style.RESET_ALL}\n")
            continue

        header_match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if header_match:
            level = len(header_match.group(1))
            colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.MAGENTA, Fore.WHITE]
            color = colors[level - 1] if level <= len(colors) else Fore.WHITE
            result.append(f"{color}{Style.BRIGHT}{line}{Style.RESET_ALL}\n")
            continue

        formatted = line
        formatted = re.sub(
            r"\*\*(.+?)\*\*",
            lambda m: f"{Style.BRIGHT}{Fore.WHITE}{m.group(1)}{Style.RESET_ALL}",
            formatted,
        )
        formatted = re.sub(
            r"`([^`]+)`",
            lambda m: f"{Fore.LIGHTBLACK_EX}{m.group(1)}{Style.RESET_ALL}",
            formatted,
        )
        result.append(f"{formatted}\n")

    return "".join(result).rstrip("\n")

# ============ MODELS ============
def _extract_model_name(item: str | dict) -> Optional[str]:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        for key in ("name", "id", "model"):
            val = item.get(key)
            if isinstance(val, str):
                return val
    return None

MODELS_CACHE_TTL = 600  # seconds
_models_cache: dict[str, tuple[float, list[str]]] = {}
_DEFAULT_MODELS = ["openai", "mistral", "llama", "claude", "gemini", "deepseek", "qwen"]

def _parse_model_list(data: object) -> list[str]:
    """Accepts a bare list or an OpenAI-style {"data": [...]} object."""
    if isinstance(data, dict):
        for k in ("data", "models", "result"):
            if isinstance(data.get(k), list):
                data = data[k]
                break
    if not isinstance(data, list):
        return []
    ids: list[str] = []
    for item in data:
        name = _extract_model_name(item)
        if name and name not in ids:
            ids.append(name)
    return ids

def fetch_models_for(provider: str, force: bool = False) -> Optional[list[str]]:
    """Model IDs offered by a service, or None if they can't be listed (enter an ID by hand)."""
    spec = PROVIDERS[provider]
    url = spec.get("models_url")
    if not url:
        return None
    url, missing = _expand_env(str(url), spec.get("vars"))
    if missing:
        print(f"{Fore.RED}[!] {spec['label']}: not set: {', '.join(missing)}{Style.RESET_ALL}")
        return None
    cached = _models_cache.get(provider)
    if cached and not force and time.time() - cached[0] < MODELS_CACHE_TTL:
        return cached[1]
    headers = {"User-Agent": "NekoChat/2.8.17"}
    if spec.get("key_env"):
        key = get_api_key(provider)
        if key:
            headers["Authorization"] = f"Bearer {key}"
        elif not spec.get("models_public"):
            print(f"{Fore.RED}[!] {spec['label']}: API key not set "
                  f"(use [key] or set {spec['key_env']}{_key_hint(spec)}){Style.RESET_ALL}")
            return None
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        ids = _parse_model_list(r.json())
    except Exception as e:
        print(f"{Fore.YELLOW}[!] Could not fetch models from {spec['label']} ({e}){Style.RESET_ALL}")
        return None
    if not ids:
        return None
    if provider != DEFAULT_PROVIDER:
        ids.sort(key=str.lower)
    _models_cache[provider] = (time.time(), ids)
    return ids

def make_model_string(provider: str, model_id: str) -> str:
    """Stored form: 'service/model-id'. Plain PollinationsAI names stay bare (old configs)."""
    if provider == DEFAULT_PROVIDER and split_model(model_id) == (DEFAULT_PROVIDER, model_id):
        return model_id
    return f"{provider}/{model_id}"

def _model_from_text(text: str, provider: str, ids: Optional[list[str]]) -> str:
    """Typed model -> stored string. An exact ID from the service's own list always wins
    (so 'nvidia/llama-...' typed under the nvidia service is not misread as a service prefix);
    otherwise a registered 'service/...' prefix switches service."""
    if ids and text in ids:
        return make_model_string(provider, text)
    head, sep, rest = text.partition("/")
    if sep and rest and head in PROVIDERS:
        return text
    return make_model_string(provider, text)

def _pick_model(provider: str) -> Optional[str]:
    """Let the user choose a model of one service. Returns the stored string or None (cancelled)."""
    spec = PROVIDERS[provider]
    ids = fetch_models_for(provider)
    if ids is None and provider == DEFAULT_PROVIDER:
        print(f"{Fore.YELLOW}[~] Using the built-in model list.{Style.RESET_ALL}")
        ids = list(_DEFAULT_MODELS)

    if ids:
        shown = ids
        if len(ids) > 25:
            flt = _ask(
                f"\n{Fore.CYAN}[+] {len(ids)} models. Filter (substring, Enter=show all): {Style.RESET_ALL}"
            ).lower()
            if flt:
                shown = [m for m in ids if flt in m.lower()]
                if not shown:
                    print(f"{Fore.RED}[!] No model matches '{flt}'.{Style.RESET_ALL}")
                    return None
        print(f"\n{Fore.YELLOW}Available models ({spec['label']}):{Style.RESET_ALL}")
        for i, m in enumerate(shown, 1):
            marker = f"{Fore.GREEN}*{Style.RESET_ALL}" if make_model_string(provider, m) == current_model else " "
            print(f"  [{marker}] {i}. {m}")
        choice = _ask(
            f"\n{Fore.CYAN}[+] Select model (number or name, Enter=cancel): {Style.RESET_ALL}"
        )
    else:
        print(f"{Fore.YELLOW}[~] No model list for {spec['label']}; enter a model ID.{Style.RESET_ALL}")
        choice = _ask(f"{Fore.CYAN}[+] Model ID (Enter=cancel): {Style.RESET_ALL}")
    if not choice:
        return None

    if ids and choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(shown):
            return make_model_string(provider, shown[idx])
        print(f"{Fore.RED}[!] Invalid number.{Style.RESET_ALL}")
        return None
    return _model_from_text(choice, provider, ids)

def select_model() -> None:
    """[model]: choose a model within the current service."""
    global current_model
    eff = _effective_settings()
    if "model" in eff["source"]:
        print(f"{Fore.YELLOW}[~] Plugin '{eff['source']['model']}' sets the model to {eff['model']} while "
              f"attached. The model you pick here is used when no plugin overrides it.{Style.RESET_ALL}")
    provider, _ = split_model(current_model)
    model = _pick_model(provider)
    if model is None:
        return
    current_model = model
    print(f"{Fore.GREEN}[OK] Model set to: {current_model}{Style.RESET_ALL}")
    save_config(build_config())

# ============ PLUGIN COMMANDS ============
PLUGIN_USAGE = (
    "Usage: [plugin] | [plugin show NAME] | [plugin on NAME [global]] | "
    "[plugin off NAME] | [plugin new NAME]"
)

def _fmt_setting(key: str, value: Any) -> str:
    if key == "max_tokens" and value is None:
        return "(server default)"
    return str(value)

def _attached_scope(name: str) -> Optional[str]:
    if any(e["name"] == name for e in _session_plugins.get(_current_session, [])):
        return "session"
    if any(e["name"] == name for e in _plugins_global):
        return "global"
    return None

def _plugin_entries(scope: str, create: bool = False) -> list[dict[str, str]]:
    """The attached-plugin list of a level. Only `create=True` may add an empty session entry."""
    if scope == "global":
        return _plugins_global
    if create:
        return _session_plugins.setdefault(_current_session, [])
    return _session_plugins.get(_current_session, [])

def _plugin_save(scope: str) -> None:
    if scope == "global":
        save_config(build_config())
    else:
        if not _session_plugins.get(_current_session):
            _session_plugins.pop(_current_session, None)
        _save_session_atomic(_current_session)

def _verify_plugin_model(model_id: str) -> str:
    ids = fetch_models_for(split_model(current_model)[0])
    if ids is None:
        return "could not be checked against the service's model list"
    if model_id in ids:
        return "found in the service's model list"
    return "NOT in the service's model list - it will be ignored while attached"

def plugin_list() -> None:
    names = list_plugin_names()
    sess = {e["name"] for e in _session_plugins.get(_current_session, [])}
    glob = {e["name"] for e in _plugins_global}
    _, problems = _active_plugins()
    bad = {(sc, n): why for sc, n, why in problems}
    print(f"\n{Fore.YELLOW}Plugins ({PLUGIN_DIR}/):{Style.RESET_ALL}")
    if not names and not sess and not glob:
        print("  (none yet - create one with [plugin new NAME])")
    for n in names:
        mark = "S" if n in sess else ("G" if n in glob else " ")
        try:
            desc = load_plugin(n)["meta"].get("description", "")
        except PluginError as ex:
            desc = f"{Fore.RED}(invalid: {ex}){Style.RESET_ALL}"
        scope = "session" if n in sess else ("global" if n in glob else "")
        why = bad.get((scope, n))
        warn = f"  {Fore.RED}NOT used: {why}{Style.RESET_ALL}" if why and "unusable" not in why else ""
        print(f"  [{mark}] {n:<20} {desc}{warn}")
    for scope, n, why in problems:
        if n not in names:
            print(f"  [{'S' if scope == 'session' else 'G'}] {n:<20} {Fore.RED}NOT used: {why}{Style.RESET_ALL}")
    print(f"  [S] attached to session '{_current_session}'   [G] attached to every session\n")

def plugin_show(name: str) -> None:
    try:
        p = load_plugin(name)
    except PluginError as ex:
        print(f"{Fore.RED}[!] Plugin '{name}': {ex}{Style.RESET_ALL}")
        return
    m = p["meta"]
    scope = _attached_scope(name)
    entry = next((e for e in _plugin_entries(scope) if e["name"] == name), None) if scope else None
    if scope is None:
        state = "not attached"
    elif entry and entry["sha256"] != p["sha256"]:
        state = f"attached to {scope}, but NOT used: the file changed since you approved it"
    else:
        state = f"attached to {scope}"
    print(f"\n{Fore.YELLOW}Plugin '{name}'{Style.RESET_ALL}  ({state})")
    print(f"  Description : {m.get('description', '(none)')}")
    for key in ("temperature", "max_tokens", "model"):
        if key in m:
            print(f"  {key:<12}: {m[key]}")
    print(f"  File        : {_plugin_path(name)}  ({len(p['body']):,} characters of prompt)\n")
    body = p["body"]
    print(body[:3000] + (f"\n… ({len(body) - 3000:,} more characters)" if len(body) > 3000 else ""))
    print()

def plugin_on(name: str, scope: str) -> None:
    try:
        p = load_plugin(name)
    except PluginError as ex:
        print(f"{Fore.RED}[!] Plugin '{name}': {ex}{Style.RESET_ALL}")
        return
    other = "global" if scope == "session" else "session"
    if any(e["name"] == name for e in
           (_plugins_global if other == "global" else _session_plugins.get(_current_session, []))):
        print(f"{Fore.YELLOW}[~] '{name}' is already attached to the {other} level; "
              f"remove it first with [plugin off {name}].{Style.RESET_ALL}")
        return
    entries = _plugin_entries(scope)
    mine = next((e for e in entries if e["name"] == name), None)
    if mine and mine["sha256"] == p["sha256"]:
        print(f"{Fore.YELLOW}[~] '{name}' is already attached ({scope}).{Style.RESET_ALL}")
        return

    m = p["meta"]
    target = "every session" if scope == "global" else f"session '{_current_session}'"
    before = _effective_settings()
    after = _effective_settings(extra={**p, "scope": scope})
    print(f"\n{Fore.YELLOW}Plugin '{name}' -> {target}{Style.RESET_ALL}")
    if m.get("description"):
        print(f"  Description : {m['description']}")
    print(f"  Prompt text : {len(p['body']):,} characters")
    for ln in p["body"].split("\n")[:3]:
        print(f"    {ln[:80]}{'…' if len(ln) > 80 else ''}")
    rows: list[str] = []
    for key in ("temperature", "max_tokens"):
        if key in m:
            src = before["source"].get(key)
            rows.append(f"    {key:<12}: {_fmt_setting(key, before[key])} -> {_fmt_setting(key, m[key])}"
                        + (f"   (replaces plugin '{src}')" if src else ""))
    if "model" in m:
        new_model = make_model_string(split_model(current_model)[0], m["model"])
        src = before["source"].get("model")
        rows.append(f"    {'model':<12}: {before['model']} -> {new_model}   [{_verify_plugin_model(m['model'])}]"
                    + (f"   (replaces plugin '{src}')" if src else ""))
    if rows:
        print("  Settings it changes while attached (config.json is not modified):")
        for r in rows:
            print(r)
    else:
        print("  Settings    : none (prompt text only)")
    if mine:
        print(f"  {Fore.YELLOW}The file changed since you approved it.{Style.RESET_ALL}")
    if _ask(f"{Fore.CYAN}[+] Attach? (Y/n): {Style.RESET_ALL}").lower() not in ("", "y", "yes"):
        print(f"{Fore.YELLOW}[~] Cancelled; nothing attached.{Style.RESET_ALL}")
        return
    if mine:
        mine["sha256"] = p["sha256"]
    else:
        _plugin_entries(scope, create=True).append({"name": name, "sha256": p["sha256"]})
    _plugin_save(scope)
    print(f"{Fore.GREEN}[OK] Plugin '{name}' attached to {target}.{Style.RESET_ALL}")
    _show_prompt_layers()

def plugin_off(name: str) -> None:
    scope = _attached_scope(name)
    if scope is None:
        print(f"{Fore.YELLOW}[~] '{name}' is not attached.{Style.RESET_ALL}")
        return
    entries = _plugin_entries(scope)
    entries[:] = [e for e in entries if e["name"] != name]
    _plugin_save(scope)
    print(f"{Fore.GREEN}[OK] Plugin '{name}' removed from the {scope} level "
          f"(the file in {PLUGIN_DIR}/ is kept).{Style.RESET_ALL}")

def plugin_new(name: str) -> None:
    if not PLUGIN_NAME_RE.fullmatch(name):
        print(f"{Fore.RED}[!] Invalid name. Use a-z, 0-9, '-' and '_' (at most 40 characters).{Style.RESET_ALL}")
        return
    path = _plugin_path(name)
    if os.path.exists(path):
        print(f"{Fore.RED}[!] {path} already exists.{Style.RESET_ALL}")
        return
    desc = _ask(f"{Fore.CYAN}[+] Description (one line, Enter=none): {Style.RESET_ALL}")
    if len(desc) > 200:
        print(f"{Fore.RED}[!] The description must be at most 200 characters.{Style.RESET_ALL}")
        return
    temperature = _prompt_float(
        f"{Fore.CYAN}[+] temperature (Enter=skip, 0.0-2.0): {Style.RESET_ALL}", 0.0, 2.0)
    max_tokens = _prompt_optional_int(f"{Fore.CYAN}[+] max_tokens (Enter=skip): {Style.RESET_ALL}")
    model = _ask(f"{Fore.CYAN}[+] model (an ID of the current service, Enter=skip): {Style.RESET_ALL}")
    if model and not re.fullmatch(r"\S{1,200}", model):
        print(f"{Fore.RED}[!] A model ID has no spaces.{Style.RESET_ALL}")
        return
    print(f"{Fore.CYAN}Enter the prompt text. Type [end] to finish:{Style.RESET_ALL}")
    lines, status, _ = read_block(allow_reset=False)
    if status == "eof":
        print(f"{Fore.YELLOW}[~] Input ended (Ctrl+D); nothing created.{Style.RESET_ALL}")
        return
    body = _join_block(lines)
    if not body:
        print(f"{Fore.YELLOW}[~] No text; nothing created.{Style.RESET_ALL}")
        return
    if len(body) > MAX_PLUGIN_BODY:
        print(f"{Fore.RED}[!] The text is longer than {MAX_PLUGIN_BODY:,} characters.{Style.RESET_ALL}")
        return
    head = [f"name: {name}"]
    if desc:
        head.append(f"description: {desc}")
    if temperature is not None:
        head.append(f"temperature: {round(temperature, 2)}")
    if max_tokens is not None and max_tokens != -1:
        head.append(f"max_tokens: {max_tokens}")
    if model:
        head.append(f"model: {model}")
    text = "\n".join(head) + "\n---\n" + body + "\n"
    try:  # validate exactly what would be written
        parse_plugin(text, name)
    except PluginError as ex:
        print(f"{Fore.RED}[!] {ex}{Style.RESET_ALL}")
        return
    if not _confirm_block(body, f"the new plugin file {path}"):
        print(f"{Fore.YELLOW}[~] Cancelled; nothing created.{Style.RESET_ALL}")
        return
    try:
        with open(path, "x", encoding="utf-8", newline="\n") as f:
            f.write(text)
    except OSError as e:
        print(f"{Fore.RED}[!] Could not create {path}: {e}{Style.RESET_ALL}")
        return
    print(f"{Fore.GREEN}[OK] Created {path}. Attach it with [plugin on {name}].{Style.RESET_ALL}")

def plugin_command(norm: str) -> None:
    """Dispatch '[plugin ...]' (norm is the lower-cased, whitespace-normalised command)."""
    if not norm.endswith("]"):
        print(f"{Fore.YELLOW}[~] {PLUGIN_USAGE}{Style.RESET_ALL}")
        return
    args = norm[1:-1].split()[1:]
    if not args or args == ["list"]:
        plugin_list()
    elif args[0] == "show" and len(args) == 2:
        plugin_show(args[1])
    elif args[0] == "on" and len(args) == 2:
        plugin_on(args[1], "session")
    elif args[0] == "on" and len(args) == 3 and args[2] == "global":
        plugin_on(args[1], "global")
    elif args[0] == "off" and len(args) == 2:
        plugin_off(args[1])
    elif args[0] == "new" and len(args) == 2:
        plugin_new(args[1])
    else:
        print(f"{Fore.YELLOW}[~] {PLUGIN_USAGE}{Style.RESET_ALL}")

# ============ API KEY COMMAND ============
def set_key() -> None:
    names = [n for n, sp in PROVIDERS.items() if sp.get("key_env")]
    print(f"\n{Fore.YELLOW}Services that need an API key:{Style.RESET_ALL}")
    for i, n in enumerate(names, 1):
        src = key_source(n)
        if src:
            status = f"{Fore.GREEN}[set: {src} {_mask_key(get_api_key(n) or '')}]{Style.RESET_ALL}"
        else:
            status = f"{Fore.RED}[not set]{Style.RESET_ALL}"
        print(f"  {i}. {n:<17} {PROVIDERS[n]['key_env']:<24} {status}")

    choice = _ask(f"\n{Fore.CYAN}[+] Select service (number or name, Enter=cancel): {Style.RESET_ALL}")
    if not choice:
        return
    if choice.isdigit() and 1 <= int(choice) <= len(names):
        name = names[int(choice) - 1]
    elif choice in names:
        name = choice
    else:
        print(f"{Fore.RED}[!] Unknown service.{Style.RESET_ALL}")
        return

    _enter_key(name)

def _enter_key(name: str, note: bool = True) -> bool:
    """Ask for the key of a service (hidden input). True if a key is now set for this session."""
    env = PROVIDERS[name]["key_env"]
    try:
        value = getpass.getpass(
            f"{env} (input hidden, Enter=cancel, 'delete'=remove saved key): "
        ).strip()
    except (EOFError, KeyboardInterrupt):
        print(f"\n{Fore.YELLOW}[~] Cancelled.{Style.RESET_ALL}")
        return False
    if not value:
        return False

    if value == "delete":
        _session_keys.pop(name, None)
        keys = load_keys()
        if name in keys:
            del keys[name]
            if not save_keys(keys):
                return False
        print(f"{Fore.GREEN}[OK] Removed the stored key for {name}.{Style.RESET_ALL}")
        if (os.environ.get(env) or "").strip():
            print(f"{Fore.YELLOW}[~] {env} is still set in the environment.{Style.RESET_ALL}")
        return False

    if any(c.isspace() for c in value):
        print(f"{Fore.RED}[!] A key must not contain spaces or line breaks.{Style.RESET_ALL}")
        return False

    _session_keys[name] = value
    print(f"{Fore.GREEN}[OK] Key for {name} set for this session ({_mask_key(value)}).{Style.RESET_ALL}")

    if _ask(f"{Fore.CYAN}[+] Save to {KEYS_FILE}? (y/N): {Style.RESET_ALL}").lower() in ("y", "yes"):
        keys = load_keys()
        keys[name] = value
        if save_keys(keys):
            print(f"{Fore.GREEN}[OK] Saved to {KEYS_FILE} (owner-only permissions).{Style.RESET_ALL}")

    if note:
        missing = _missing_vars(name)
        if missing:
            print(f"{Fore.YELLOW}[~] {PROVIDERS[name]['label']} also needs: {', '.join(missing)} "
                  f"([service] will ask for it).{Style.RESET_ALL}")
    return True

def _missing_vars(name: str) -> list[str]:
    """${VAR} names in the service's chat URL that have no value yet."""
    spec = PROVIDERS[name]
    return list(dict.fromkeys(_expand_env(str(spec["chat_url"]), spec.get("vars"))[1]))

def _ensure_url_vars(name: str) -> bool:
    """Ask for any missing ${VAR} of the chat URL (e.g. the Cloudflare account ID, which is
    not a secret) and keep it in config.json. False if the user skipped."""
    missing = _missing_vars(name)
    for var in missing:
        val = _ask(f"{Fore.CYAN}[+] {var} (Enter=skip): {Style.RESET_ALL}")
        if not val or any(c.isspace() for c in val):
            print(f"{Fore.YELLOW}[~] {var} is required for {PROVIDERS[name]['label']}.{Style.RESET_ALL}")
            return False
        PROVIDERS[name].setdefault("vars", {})[var] = val
        _providers_cfg.setdefault(name, {}).setdefault("vars", {})[var] = val
    if missing:
        save_config(build_config())
        print(f"{Fore.GREEN}[OK] Saved to config.json (this value is not secret).{Style.RESET_ALL}")
    return True

# ============ SERVICE COMMAND ============
def select_service() -> None:
    """[service]: pick a service, enter its key if needed, then pick a model.
    The service only changes once a model has been chosen."""
    global current_model
    names = list(PROVIDERS)
    cur = split_model(current_model)[0]
    print(f"\n{Fore.YELLOW}Services:{Style.RESET_ALL}")
    for i, n in enumerate(names, 1):
        sp = PROVIDERS[n]
        if not sp.get("key_env"):
            status = "no key needed"
        elif key_source(n):
            status = f"{Fore.GREEN}key: {key_source(n)}{Style.RESET_ALL}"
        else:
            status = f"{Fore.RED}key not set{Style.RESET_ALL}"
        marker = f"{Fore.GREEN}*{Style.RESET_ALL}" if n == cur else " "
        print(f"  [{marker}] {i}. {n:<17} {status}")

    choice = _ask(f"\n{Fore.CYAN}[+] Select service (number or name, Enter=cancel): {Style.RESET_ALL}")
    if not choice:
        return
    if choice.isdigit() and 1 <= int(choice) <= len(names):
        name = names[int(choice) - 1]
    elif choice in names:
        name = choice
    else:
        print(f"{Fore.RED}[!] Unknown service.{Style.RESET_ALL}")
        return

    if PROVIDERS[name].get("key_env") and not get_api_key(name):
        print(f"{Fore.YELLOW}[~] {PROVIDERS[name]['label']} needs an API key.{Style.RESET_ALL}")
        if not _enter_key(name, note=False):
            print(f"{Fore.YELLOW}[~] Service not changed.{Style.RESET_ALL}")
            return
    if not _ensure_url_vars(name):
        print(f"{Fore.YELLOW}[~] Service not changed.{Style.RESET_ALL}")
        return

    model = _pick_model(name)
    if model is None:
        print(f"{Fore.YELLOW}[~] Service not changed.{Style.RESET_ALL}")
        return
    current_model = model
    print(f"{Fore.GREEN}[OK] Service: {name}  Model: {current_model}{Style.RESET_ALL}")
    save_config(build_config())

# ============ SYSTEM PROMPT ============
# ============ PLUGINS ============
# A plugin is a named, reusable prompt kept in plugins/NAME.txt:
#     description: one line            (header: flat "key: value" lines)
#     temperature: 0.2
#     max_tokens: 1200
#     model: some-model-id             (a model of the CURRENT service only)
#     ---
#     the prompt text ...
# Plugins are data only. The text joins the system prompt; the optional settings are applied
# at send time on top of config.json, which is never rewritten. Attaching asks for confirmation
# and remembers the file's SHA-256; a file that changed since then is ignored until re-approved.
PLUGIN_NAME_RE = re.compile(r"[a-z0-9][a-z0-9_-]{0,39}")
PLUGIN_KEYS = ("name", "description", "temperature", "max_tokens", "model")
MAX_PLUGIN_BODY = 20000

class PluginError(Exception):
    pass

def _plugin_path(name: str) -> str:
    return os.path.join(PLUGIN_DIR, f"{name}.txt")

def _norm_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")

def parse_plugin(text: str, stem: str) -> tuple[dict[str, Any], str]:
    """Parse plugin text -> (meta, body). Strict: unknown keys and bad values are errors."""
    lines = _norm_text(text).split("\n")
    raw: dict[str, str] = {}
    body_lines = lines
    first = next((ln for ln in lines if ln.strip()), "")
    if re.match(r"^[A-Za-z_]+\s*:", first) and any(ln.strip() == "---" for ln in lines):
        end = next(i for i, ln in enumerate(lines) if ln.strip() == "---")
        for ln in lines[:end]:
            if not ln.strip():
                continue
            key, sep, val = ln.partition(":")
            key = key.strip().lower()
            if not sep or not re.fullmatch(r"[a-z_]+", key):
                raise PluginError(f"bad header line {ln[:40]!r}")
            if key not in PLUGIN_KEYS:
                raise PluginError(f"unknown header key '{key}' (allowed: {', '.join(PLUGIN_KEYS)})")
            if key in raw:
                raise PluginError(f"duplicate header key '{key}'")
            raw[key] = val.strip()
        body_lines = lines[end + 1:]
    if "name" in raw and raw["name"] != stem:
        raise PluginError(f"header name '{raw['name']}' differs from the file name '{stem}'")
    meta: dict[str, Any] = {"name": stem}
    desc = raw.get("description", "")
    if len(desc) > 200:
        raise PluginError("description is longer than 200 characters")
    if desc:
        meta["description"] = desc
    for key in ("temperature", "max_tokens", "model"):
        if key in raw and not raw[key]:
            raise PluginError(f"'{key}' has no value")
    if "temperature" in raw:
        try:
            t = float(raw["temperature"])
        except ValueError:
            raise PluginError("temperature must be a number") from None
        if not (0.0 <= t <= 2.0):
            raise PluginError("temperature must be between 0.0 and 2.0")
        meta["temperature"] = t
    if "max_tokens" in raw:
        try:
            m = int(raw["max_tokens"])
        except ValueError:
            raise PluginError("max_tokens must be a whole number") from None
        if not (1 <= m <= 1_000_000):
            raise PluginError("max_tokens must be between 1 and 1000000")
        meta["max_tokens"] = m
    if "model" in raw:
        if not re.fullmatch(r"\S{1,200}", raw["model"]):
            raise PluginError("model must be a single model ID without spaces")
        meta["model"] = raw["model"]
    body = _join_block(body_lines)
    if not body:
        raise PluginError("there is no prompt text")
    if len(body) > MAX_PLUGIN_BODY:
        raise PluginError(f"the prompt text is longer than {MAX_PLUGIN_BODY:,} characters")
    return meta, body

def load_plugin(name: str) -> dict[str, Any]:
    if not PLUGIN_NAME_RE.fullmatch(name):
        raise PluginError("invalid plugin name (use a-z, 0-9, '-' and '_'; at most 40 characters)")
    try:
        with open(_plugin_path(name), "r", encoding="utf-8") as f:
            raw = f.read()
    except FileNotFoundError:
        raise PluginError("file not found") from None
    except (OSError, UnicodeDecodeError) as e:
        raise PluginError(f"cannot read the file ({e})") from None
    text = _norm_text(raw)
    meta, body = parse_plugin(text, name)
    return {"name": name, "meta": meta, "body": body,
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}

def list_plugin_names() -> list[str]:
    try:
        files = os.listdir(PLUGIN_DIR)
    except OSError:
        return []
    return sorted(f[:-4] for f in files if f.endswith(".txt") and PLUGIN_NAME_RE.fullmatch(f[:-4]))

def _clean_plugin_entries(raw: object) -> list[dict[str, str]]:
    """Validate the attached-plugin list read from config.json / a session file."""
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    if not isinstance(raw, list):
        return out
    for e in raw:
        if (isinstance(e, dict) and isinstance(e.get("name"), str) and isinstance(e.get("sha256"), str)
                and PLUGIN_NAME_RE.fullmatch(e["name"]) and re.fullmatch(r"[0-9a-f]{64}", e["sha256"])
                and e["name"] not in seen):
            seen.add(e["name"])
            out.append({"name": e["name"], "sha256": e["sha256"]})
    return out

def _active_plugins(
    session: Optional[str] = None, extra: Optional[dict[str, Any]] = None
) -> tuple[list[dict[str, Any]], list[tuple[str, str, str]]]:
    """Plugins that are in use now, in application order (global ones, then the session's).

    Returns (active, problems); problems are (scope, name, reason) for attached plugins that
    are missing, invalid, or changed since they were approved. `extra` (an already loaded
    plugin plus "scope") is added as if attached - used to preview a change.
    """
    sname = session if session is not None else _current_session
    active: list[dict[str, Any]] = []
    problems: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for scope, entries in (("global", _plugins_global), ("session", _session_plugins.get(sname, []))):
        for e in entries:
            if e["name"] in seen or (extra is not None and e["name"] == extra["name"]):
                continue
            seen.add(e["name"])
            try:
                p = load_plugin(e["name"])
            except PluginError as ex:
                problems.append((scope, e["name"], f"unusable ({ex})"))
                continue
            if p["sha256"] != e["sha256"]:
                problems.append((scope, e["name"],
                                 f"changed since you approved it; re-approve with [plugin on {e['name']}]"))
                continue
            active.append({**p, "scope": scope})
        if extra is not None and extra["scope"] == scope and extra["name"] not in seen:
            seen.add(extra["name"])
            active.append(extra)
    return active, problems

def _effective_settings(
    session: Optional[str] = None, extra: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """Settings used for a request: config.json values with plugin overrides on top.
    Later plugins win (the session's after the global ones). Nothing here is saved."""
    active, _ = _active_plugins(session, extra)
    provider = split_model(current_model)[0]
    cached = _models_cache.get(provider)
    st: dict[str, Any] = {"temperature": _temperature, "max_tokens": _max_tokens, "model": current_model}
    source: dict[str, str] = {}
    skipped: list[tuple[str, str]] = []
    for p in active:
        m = p["meta"]
        if "temperature" in m:
            st["temperature"], source["temperature"] = m["temperature"], p["name"]
        if "max_tokens" in m:
            st["max_tokens"], source["max_tokens"] = m["max_tokens"], p["name"]
        if "model" in m:
            if cached and m["model"] not in cached[1]:   # known not to exist in this service
                skipped.append((p["name"], m["model"]))
                continue
            st["model"], source["model"] = make_model_string(provider, m["model"]), p["name"]
    st["source"] = source
    st["skipped_models"] = skipped
    return st

def _warn_once(key: str, msg: str) -> None:
    if key not in _warned:
        _warned.add(key)
        print(f"{Fore.YELLOW}[~] {msg}{Style.RESET_ALL}")

def _effective_system_prompt(session: Optional[str] = None) -> str:
    """What is actually sent, as one message: global text, global plugins, session text,
    session plugins - separated by blank lines."""
    name = session if session is not None else _current_session
    active, _ = _active_plugins(name)
    parts = [_system_prompt]
    parts += [p["body"] for p in active if p["scope"] == "global"]
    parts.append(_session_prompts.get(name, ""))
    parts += [p["body"] for p in active if p["scope"] == "session"]
    return "\n\n".join(x for x in parts if x and x.strip())

def _clip(text: str, limit: int = 200) -> str:
    one = text.replace("\n", " ⏎ ")
    return one if len(one) <= limit else one[:limit] + "…"

def _show_prompt_layers() -> None:
    sess = _session_prompts.get(_current_session, "")
    active, problems = _active_plugins()

    def plugin_names(scope: str) -> str:
        used = [p["name"] for p in active if p["scope"] == scope]
        bad = [f"{n} (NOT used)" for sc, n, _ in problems if sc == scope]
        return ", ".join(used + bad)

    rows = [("Global:", _clip(_system_prompt) if _system_prompt else "(none)")]
    if plugin_names("global"):
        rows.append(("Global plugins:", plugin_names("global")))
    rows.append((f"Session [{_current_session}]:", _clip(sess) if sess else "(none)"))
    if plugin_names("session"):
        rows.append(("Session plugins:", plugin_names("session")))
    rows.append(("Sent to the AI:", f"{len(_effective_system_prompt()):,} characters"))
    w = max(len(label) for label, _ in rows) + 2
    print(f"\n{Fore.YELLOW}System prompt layers:{Style.RESET_ALL}")
    for label, value in rows:
        print(f"  {label:<{w}}{value}")
    print()

def set_system_prompt() -> None:
    """[system]: the GLOBAL layer (shared by every session)."""
    global _system_prompt
    _show_prompt_layers()
    print(
        f"{Fore.CYAN}Enter the new GLOBAL prompt. "
        f"Type [end] to finish, [reset] for the default:{Style.RESET_ALL}"
    )
    lines, status, _ = read_block(allow_reset=True)
    if status == "reset":
        _system_prompt = DEFAULT_SYSTEM_PROMPT
        print(f"{Fore.GREEN}[OK] Global system prompt reset to default.{Style.RESET_ALL}")
        save_config(build_config())
        return
    if status == "eof":
        print(f"{Fore.YELLOW}[~] Input ended (Ctrl+D); nothing changed.{Style.RESET_ALL}")
        return
    text = _join_block(lines)
    if not text:
        print(f"{Fore.YELLOW}[~] Kept current prompt.{Style.RESET_ALL}")
        return
    if not _confirm_block(text, "the global system prompt"):
        print(f"{Fore.YELLOW}[~] Cancelled; nothing changed.{Style.RESET_ALL}")
        return
    _system_prompt = text
    save_config(build_config())
    print(f"{Fore.GREEN}[OK] Global system prompt updated.{Style.RESET_ALL}")
    _show_prompt_layers()

def set_session_prompt() -> None:
    """[system session]: a layer for the CURRENT session only, added after the global one."""
    name = _current_session
    _show_prompt_layers()
    print(
        f"{Fore.CYAN}Enter the prompt for session '{name}'. "
        f"Type [end] to finish, [reset] to remove it:{Style.RESET_ALL}"
    )
    lines, status, _ = read_block(allow_reset=True)
    if status == "reset":
        if _session_prompts.pop(name, None) is not None:
            _save_session_atomic(name)
        print(
            f"{Fore.GREEN}[OK] Session prompt removed; only the global prompt "
            f"applies to '{name}'.{Style.RESET_ALL}"
        )
        return
    if status == "eof":
        print(f"{Fore.YELLOW}[~] Input ended (Ctrl+D); nothing changed.{Style.RESET_ALL}")
        return
    text = _join_block(lines)
    if not text:
        print(f"{Fore.YELLOW}[~] Kept current session prompt.{Style.RESET_ALL}")
        return
    if not _confirm_block(text, f"session '{name}'"):
        print(f"{Fore.YELLOW}[~] Cancelled; nothing changed.{Style.RESET_ALL}")
        return
    _session_prompts[name] = text
    _save_session_atomic(name)
    print(f"{Fore.GREEN}[OK] Session prompt set for '{name}'.{Style.RESET_ALL}")
    _show_prompt_layers()

# ============ CONFIG (temperature / max_tokens) ============
def _prompt_float(prompt_text: str, min_val: float, max_val: float) -> Optional[float]:
    while True:
        raw = _ask(prompt_text)
        if raw == "":
            return None
        try:
            val = float(raw)
        except ValueError:
            print(f"{Fore.RED}[!] Please enter a number.{Style.RESET_ALL}")
            continue
        if not (min_val <= val <= max_val):
            print(f"{Fore.RED}[!] Value must be between {min_val} and {max_val}.{Style.RESET_ALL}")
            continue
        return val

def _prompt_optional_int(prompt_text: str) -> Optional[int]:
    while True:
        raw = _ask(prompt_text).lower()
        if raw == "":
            return None
        if raw == "none":
            return -1
        try:
            val = int(raw)
        except ValueError:
            print(f"{Fore.RED}[!] Please enter a positive integer or 'none'.{Style.RESET_ALL}")
            continue
        if val < 1:
            print(f"{Fore.RED}[!] Must be at least 1.{Style.RESET_ALL}")
            continue
        return val

def edit_config() -> None:
    global _temperature, _max_tokens
    print(f"\n{Fore.YELLOW}Current configuration:{Style.RESET_ALL}")
    print(f"  temperature : {_temperature}")
    mt = str(_max_tokens) if _max_tokens is not None else "(unset / server default)"
    print(f"  max_tokens  : {mt}\n")
    eff = _effective_settings()
    if eff["source"]:
        print(f"{Fore.MAGENTA}  Plugins currently override these while attached (not saved to config.json):{Style.RESET_ALL}")
        for key in ("temperature", "max_tokens", "model"):
            if key in eff["source"]:
                print(f"    {key:<12}: {_fmt_setting(key, eff[key])}   (plugin '{eff['source'][key]}')")
        print()

    new_temp = _prompt_float(
        f"{Fore.CYAN}[+] temperature (current: {_temperature}, Enter=keep, 0.0-2.0): {Style.RESET_ALL}",
        0.0, 2.0,
    )
    if new_temp is not None:
        _temperature = round(new_temp, 2)
        print(f"{Fore.GREEN}[OK] temperature set to {_temperature}{Style.RESET_ALL}")

    new_mt = _prompt_optional_int(
        f"{Fore.CYAN}[+] max_tokens (current: {mt}, Enter=keep, 'none'=unset): {Style.RESET_ALL}"
    )
    if new_mt == -1:
        _max_tokens = None
        print(f"{Fore.GREEN}[OK] max_tokens unset (server default){Style.RESET_ALL}")
    elif new_mt is not None:
        _max_tokens = new_mt
        print(f"{Fore.GREEN}[OK] max_tokens set to {_max_tokens}{Style.RESET_ALL}")

    save_config(build_config())

# ============ STREAM / TURN GUARD TOGGLE ============
def toggle_stream() -> None:
    global _stream_mode
    _stream_mode = not _stream_mode
    status = "ON (streaming)" if _stream_mode else "OFF (batch)"
    print(f"{Fore.GREEN}[OK] Streaming mode: {status}{Style.RESET_ALL}")
    save_config(build_config())


def toggle_turn_guard() -> None:
    global _turn_guard_enabled
    _turn_guard_enabled = not _turn_guard_enabled
    status = "ON" if _turn_guard_enabled else "OFF"
    print(f"{Fore.GREEN}[OK] Turn guard: {status}{Style.RESET_ALL}")
    if _turn_guard_enabled:
        print(
            f"{Fore.YELLOW}    Note: May still cut legitimate text that contains "
            f"multiple User:/Assistant:/AI: labels (e.g. definitions, "
            f"translation tables). Use with care.{Style.RESET_ALL}"
        )

# ============ USER NAME ============
NAME_MAX_WIDTH = 24  # display columns (CJK and emoji count as 2)


def _display_width(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


def _validate_username(raw: str) -> tuple[Optional[str], Optional[str]]:
    """Normalise and check a display name. Returns (name, error)."""
    name = " ".join(unicodedata.normalize("NFC", raw).split())
    if not name:
        return None, "Name cannot be empty."
    for ch in name:
        cat = unicodedata.category(ch)
        if cat[0] == "C" or cat in ("Mn", "Me"):
            return None, (
                f"Unsupported character U+{ord(ch):04X} "
                "(control, zero-width and combining characters are not allowed)."
            )
    if _display_width(name) > NAME_MAX_WIDTH:
        return None, (
            f"Name is too long (max {NAME_MAX_WIDTH} columns; CJK and emoji count as 2)."
        )
    return name, None


def _msg_name(msg: dict) -> str:
    """Name a user message was sent under (falls back to the current name)."""
    n = msg.get("name")
    return n if isinstance(n, str) and n else username


def _stamp_names(history: list[dict], fallback: object) -> None:
    """Give user messages without a stored name the name saved in the session file."""
    fb = fallback if isinstance(fallback, str) and fallback else ""
    for msg in history:
        if msg["role"] != "user":
            continue
        n = msg.get("name")
        if isinstance(n, str) and n:
            continue
        if fb:
            msg["name"] = fb
        else:
            msg.pop("name", None)


def _name_flow(history: list[dict]) -> list[str]:
    """Names used by user messages in order, consecutive duplicates merged."""
    flow: list[str] = []
    for msg in history:
        if msg["role"] == "user":
            n = _msg_name(msg)
            if not flow or flow[-1] != n:
                flow.append(n)
    return flow


def _past_names() -> list[str]:
    seen: list[str] = []
    for sname in sorted(_sessions):
        for n in _name_flow(_sessions[sname]):
            if n not in seen:
                seen.append(n)
    return seen


def set_username() -> None:
    global username
    print(f"\n{Fore.YELLOW}Current name:{Style.RESET_ALL} {username}")
    others = [n for n in _past_names() if n != username]
    if others:
        print(f"{Fore.YELLOW}Also found in saved logs:{Style.RESET_ALL} {', '.join(others)}")
    print("  (Past messages keep the name they were sent with.)")
    raw = _ask(f"{Fore.CYAN}[+] New name (Enter to keep '{username}'): {Style.RESET_ALL}")
    if not raw:
        print(f"{Fore.YELLOW}[~] Kept current name.{Style.RESET_ALL}")
        return
    name, err = _validate_username(raw)
    if err or name is None:
        print(f"{Fore.RED}[!] {err}{Style.RESET_ALL}")
        return
    if name == username:
        print(f"{Fore.YELLOW}[~] Same name. No change.{Style.RESET_ALL}")
        return
    old, username = username, name
    save_config(build_config())
    print(f"{Fore.GREEN}[OK] Name changed: '{old}' → '{name}'{Style.RESET_ALL}")

# ============ SESSION MANAGEMENT (multi-session) ============
def _valid_history(history: object) -> bool:
    if not isinstance(history, list):
        return False
    for msg in history:
        if not isinstance(msg, dict):
            return False
        if msg.get("role") not in ("user", "assistant"):
            return False
        if not isinstance(msg.get("content"), str):
            return False
    return True

def _save_session_atomic(name: str) -> None:
    """Save a single session atomically (write to temp, then rename)."""
    history = _sessions.get(name, [])
    fname = _safe_session_name(name)
    tmp_path = os.path.join(SESSION_DIR, f".{fname}.tmp")
    path = os.path.join(SESSION_DIR, fname)
    data = {
        "model": current_model,
        "username": username,
        "temperature": _temperature,
        "max_tokens": _max_tokens,
        "history": history,
        "saved_at": datetime.datetime.now().isoformat(),
    }
    if _session_prompts.get(name):
        data["session_prompt"] = _session_prompts[name]
    if _session_plugins.get(name):
        data["plugins"] = _session_plugins[name]
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except OSError as e:
        print(f"{Fore.RED}[!] Failed to save '{name}': {e}{Style.RESET_ALL}")

def _auto_load_all_sessions() -> None:
    global _sessions, _current_session
    _sessions = {}
    _session_prompts.clear()
    _session_plugins.clear()
    files = sorted(f for f in os.listdir(SESSION_DIR) if f.endswith(".json"))
    loaded_any = False
    for fname in files:
        path = os.path.join(SESSION_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            history = data.get("history", []) if isinstance(data, dict) else []
            if _valid_history(history):
                _stamp_names(history, data.get("username") if isinstance(data, dict) else None)
                name = fname[:-5]
                _sessions[name] = history
                sp = data.get("session_prompt") if isinstance(data, dict) else None
                if isinstance(sp, str) and sp.strip():
                    _session_prompts[name] = sp
                pl = _clean_plugin_entries(data.get("plugins")) if isinstance(data, dict) else []
                if pl:
                    _session_plugins[name] = pl
                loaded_any = True
            else:
                print(
                    f"{Fore.YELLOW}[!] Skipped '{fname}': invalid history format.{Style.RESET_ALL}"
                )
        except json.JSONDecodeError as e:
            print(
                f"{Fore.YELLOW}[!] Skipped '{fname}': JSON error ({e}).{Style.RESET_ALL}"
            )
        except Exception as e:
            print(f"{Fore.YELLOW}[!] Skipped '{fname}': {e}.{Style.RESET_ALL}")
    if not loaded_any:
        _sessions = {"default": []}
        _current_session = "default"
    else:
        if "default" in _sessions:
            _current_session = "default"
        else:
            _current_session = sorted(_sessions.keys())[0]

def _auto_save_all_sessions() -> None:
    for name in _sessions:
        _save_session_atomic(name)

def list_sessions() -> None:
    print(f"\n{Fore.YELLOW}Sessions:{Style.RESET_ALL}")
    for i, name in enumerate(sorted(_sessions.keys()), 1):
        marker = f"{Fore.GREEN}*{Style.RESET_ALL}" if name == _current_session else " "
        count = len(_sessions[name])
        flow = _name_flow(_sessions[name])
        if len(flow) > 4:
            flow = ["…"] + flow[-4:]
        who = f"  {Fore.CYAN}{' → '.join(flow)}{Style.RESET_ALL}" if flow else ""
        has_sp = f"  {Fore.MAGENTA}[+prompt]{Style.RESET_ALL}" if _session_prompts.get(name) else ""
        print(f"  [{marker}] {i}. {name} ({count} messages){has_sp}{who}")
    print()

def switch_session() -> None:
    global _current_session, _last_assistant_text
    list_sessions()
    choice = _ask(f"{Fore.CYAN}[+] Switch to (number or name): {Style.RESET_ALL}")
    if not choice:
        return
    names = sorted(_sessions.keys())
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(names):
            name = names[idx]
        else:
            print(f"{Fore.RED}[!] Invalid number.{Style.RESET_ALL}")
            return
    else:
        if choice not in _sessions:
            print(
                f"{Fore.RED}[!] Session '{choice}' not found. Use [new] to create.{Style.RESET_ALL}"
            )
            return
        name = choice

    if name != _current_session:
        _discord_auto_leave(_current_session)
    _current_session = name
    _last_assistant_text = _session_last_text.get(name, "")
    print(
        f"{Fore.GREEN}[OK] Switched to '{_current_session}' "
        f"({len(_sessions[_current_session])} messages){Style.RESET_ALL}"
    )

def new_session() -> None:
    global _current_session, _last_assistant_text
    name = _ask(f"{Fore.CYAN}[+] New session name: {Style.RESET_ALL}")
    if not name:
        print(f"{Fore.RED}[!] Name cannot be empty.{Style.RESET_ALL}")
        return
    name = _sanitize_session_name(name)
    if name in _sessions:
        print(
            f"{Fore.YELLOW}[!] Session '{name}' already exists. Switched to it.{Style.RESET_ALL}"
        )
        if name != _current_session:
            _discord_auto_leave(_current_session)
        _current_session = name
        _last_assistant_text = _session_last_text.get(name, "")
        return
    _sessions[name] = []
    _discord_auto_leave(_current_session)
    _current_session = name
    _last_assistant_text = ""
    print(f"{Fore.GREEN}[OK] Created and switched to '{name}'{Style.RESET_ALL}")

def rename_session() -> None:
    global _current_session
    old = _current_session
    new = _ask(f"{Fore.CYAN}[+] Rename '{old}' to: {Style.RESET_ALL}")
    if not new:
        return
    new = _sanitize_session_name(new)
    if new == old:
        print(f"{Fore.YELLOW}[~] Same name. No change.{Style.RESET_ALL}")
        return
    if new in _sessions:
        print(f"{Fore.RED}[!] Name '{new}' already exists.{Style.RESET_ALL}")
        return
    _sessions[new] = _sessions.pop(old)
    _session_last_text[new] = _session_last_text.pop(old, "")
    if old in _session_prompts:
        _session_prompts[new] = _session_prompts.pop(old)
    if old in _session_plugins:
        _session_plugins[new] = _session_plugins.pop(old)
    if old in _discord_auto:
        _discord_auto[new] = _discord_auto.pop(old)
    _current_session = new

    # Save new session BEFORE removing old file so a crash won't lose data
    _save_session_atomic(new)

    # Remove old session file to avoid orphan files
    old_path = os.path.join(SESSION_DIR, _safe_session_name(old))
    new_path = os.path.join(SESSION_DIR, _safe_session_name(new))
    try:
        if os.path.exists(old_path):
            # On case-insensitive filesystems (Windows/macOS) renaming "work" → "Work"
            # resolves to the same physical file.  Skip deletion so we don't nuke the
            # newly-written session.
            try:
                same = os.path.samefile(old_path, new_path)
            except (OSError, ValueError):
                same = False
            if not same:
                os.remove(old_path)
    except OSError as e:
        print(f"{Fore.YELLOW}[!] Could not remove old file: {e}{Style.RESET_ALL}")

    print(f"{Fore.GREEN}[OK] Renamed '{old}' → '{new}'{Style.RESET_ALL}")

def delete_session() -> None:
    name = _ask(f"{Fore.CYAN}[+] Delete session (name, Enter=cancel): {Style.RESET_ALL}")
    if not name or name not in _sessions:
        print(f"{Fore.YELLOW}[~] Cancelled or not found.{Style.RESET_ALL}")
        return
    if name == _current_session:
        print(f"{Fore.RED}[!] Cannot delete the current session.{Style.RESET_ALL}")
        return
    confirm = _ask(f"{Fore.RED}[!] Really delete '{name}'? type 'yes': {Style.RESET_ALL}")
    if confirm != "yes":
        print(f"{Fore.YELLOW}[~] Cancelled.{Style.RESET_ALL}")
        return
    del _sessions[name]
    _session_last_text.pop(name, None)
    _session_prompts.pop(name, None)
    _session_plugins.pop(name, None)
    _discord_auto.pop(name, None)
    # Also delete the file
    fname = _safe_session_name(name)
    path = os.path.join(SESSION_DIR, fname)
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError as e:
        print(f"{Fore.YELLOW}[!] Could not remove file: {e}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}[OK] Deleted '{name}'{Style.RESET_ALL}")

# ============ CHAT ============
def _server_error_text(resp: Optional[requests.Response]) -> str:
    """Short reason taken from an error response body (JSON "error" field if present)."""
    if resp is None:
        return ""
    try:
        data = resp.json()
        if isinstance(data, dict) and data.get("error"):
            err = data["error"]
            if isinstance(err, dict):  # e.g. {"error": {"message": "...", "code": "UNAUTHORIZED"}}
                err = err.get("message") or err.get("code") or err
            return str(err)[:200]
    except ValueError:
        pass
    text = (resp.text or "").strip()
    return "" if text in ("", "{}") else text[:200]

def send_chat(
    messages: list[dict[str, str]], stream: bool = True
) -> Optional[requests.Response]:
    for scope, pname, reason in _active_plugins()[1]:
        _warn_once(f"plugin:{scope}:{pname}:{reason}", f"Plugin '{pname}' ({scope}) is not used: {reason}.")
    eff = _effective_settings()
    for pname, mid in eff["skipped_models"]:
        _warn_once(f"model:{pname}:{mid}:{current_model}",
                   f"Plugin '{pname}' asks for model '{mid}', which this service does not list; "
                   f"using {current_model}.")
    resolved = resolve_request(eff["model"])
    if resolved is None:
        return None
    url, model_id, auth_headers = resolved
    provider, _ = split_model(eff["model"])
    spec = PROVIDERS[provider]

    payload: dict[str, object] = {
        "model": model_id,
        "messages": messages,
        "stream": stream,
        "temperature": eff["temperature"],
    }
    if eff["max_tokens"] is not None:
        payload["max_tokens"] = eff["max_tokens"]

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "NekoChat/2.8.17",
        **auth_headers,
    }

    try:
        response = requests.post(
            url, headers=headers, json=payload, stream=stream,
            timeout=(10, 60) if stream else (10, 180),  # (connect, read)
        )
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response is not None else None
        reason = _server_error_text(e.response)
        if code == 429:
            print(
                f"{Fore.RED}[!] Rate limited (429). "
                f"{spec['rate_hint']}{Style.RESET_ALL}"
            )
        elif code in (401, 403) and spec.get("key_env"):
            detail = f" — {reason}" if reason else ""
            print(
                f"{Fore.RED}[!] {spec['label']}: authentication failed (HTTP {code}){detail}. "
                f"Check {spec['key_env']}{_key_hint(spec)}.{Style.RESET_ALL}"
            )
        elif code is not None and code >= 500:
            print(f"{Fore.RED}[!] HTTP {code} from server: {reason or '(no details)'}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}    Server-side problem, not a NekoChat bug. Retry later.{Style.RESET_ALL}")
            if spec.get("fail_hint"):
                print(f"{Fore.YELLOW}    {spec['fail_hint']}{Style.RESET_ALL}")
        else:
            detail = f" — {reason}" if reason else ""
            print(f"{Fore.RED}[!] HTTP Error: {e}{detail}{Style.RESET_ALL}")
            if code == 402 and spec.get("fail_hint"):
                print(f"{Fore.YELLOW}    {spec['fail_hint']}{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"{Fore.RED}[!] Request failed: {e}{Style.RESET_ALL}")
        return None

def stream_response(response: requests.Response) -> tuple[str, bool]:
    full_text = ""   # accepted text (after turn-guard truncation)
    shown = 0        # how many chars of full_text are already on screen
    completed = False
    stopped = False
    finished = False  # saw [DONE] or a finish_reason

    def _emit(s: str) -> None:
        if s:
            sys.stdout.write(Fore.MAGENTA + s + Style.RESET_ALL)
            sys.stdout.flush()

    try:
        for line in response.iter_lines(decode_unicode=False):
            if not line:
                continue
            text_line = line.decode("utf-8", errors="replace").strip()
            if not text_line.startswith("data:"):
                continue
            data_str = text_line[5:].strip()
            if data_str == "[DONE]":
                finished = True
                break
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                continue
            if not isinstance(data, dict):
                continue
            choices = data.get("choices")
            if not isinstance(choices, list) or not choices:
                continue
            first = choices[0]
            if not isinstance(first, dict):
                continue
            if first.get("finish_reason"):
                finished = True
            delta = first.get("delta")
            if not isinstance(delta, dict):
                continue
            content = delta.get("content") or ""
            if not content:
                continue

            candidate = full_text + content
            marker_positions = _find_turn_markers(candidate)

            if len(marker_positions) >= 2:
                # Two or more markers: definitely a fake turn sequence.
                # Truncate at the first marker and stop reading.
                full_text = candidate[: marker_positions[0]]
                stopped = True
                _emit(full_text[shown:])
                shown = len(full_text)
                break
            elif len(marker_positions) == 1:
                # Exactly one marker: hold back everything from the marker onward.
                # If a second marker arrives later we will truncate here;
                # if the stream ends with only one marker it was legitimate content
                # (definition, example, etc.) and we flush the held-back tail at the end.
                full_text = candidate
                pos = marker_positions[0]
                if pos > shown:
                    _emit(full_text[shown:pos])
                    shown = pos
            else:
                # No markers yet: normal streaming with held-back tail
                full_text = candidate
                safe = len(full_text) - _held_back_len(full_text)
                if safe > shown:
                    _emit(full_text[shown:safe])
                    shown = safe

        if not stopped:
            _emit(full_text[shown:])  # flush any held-back tail
        completed = True
        print()
        if stopped:
            print(f"{Fore.YELLOW}[~] Turn guard stopped fake turn generation.{Style.RESET_ALL}")
        elif not finished:
            print(
                f"{Fore.YELLOW}[~] Stream ended without [DONE]; "
                f"the response may be cut off.{Style.RESET_ALL}"
            )
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Interrupted by user.{Style.RESET_ALL}")
    except requests.exceptions.RequestException as e:
        print(f"\n{Fore.RED}[!] Stream error: {e}{Style.RESET_ALL}")
    finally:
        response.close()
        # Defensive flush: on some terminal emulators (e.g. Colab xterm.js)
        # streamed output can leak into the next input() buffer.
        sys.stdout.flush()
    return full_text, completed

def batch_response(response: requests.Response) -> tuple[str, bool]:
    try:
        data = response.json()
        choices = data.get("choices") or []
        if choices and isinstance(choices[0], dict):
            message = choices[0].get("message") or {}
            if isinstance(message, dict):
                content = message.get("content", "")
                if content:
                    truncated = _truncate_at_turn(content)
                    if truncated != content:
                        print(
                            f"\n{Fore.YELLOW}[~] Turn guard stopped fake turn generation.{Style.RESET_ALL}"
                        )
                    print(Fore.MAGENTA + truncated + Style.RESET_ALL)
                    return truncated, True
        return "", True
    except (json.JSONDecodeError, KeyError, AttributeError, requests.exceptions.RequestException) as e:
        print(f"{Fore.RED}[!] Batch response error: {e}{Style.RESET_ALL}")
        return "", False

def _trim_history(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    system_msgs = [m for m in messages if m.get("role") == "system"]
    rest = [m for m in messages if m.get("role") != "system"]

    trimmed = rest[-MAX_HISTORY:] if len(rest) > MAX_HISTORY else rest[:]
    while trimmed and trimmed[0].get("role") != "user":
        trimmed = trimmed[1:]

    return system_msgs + trimmed

def _build_messages_for_api(user_input: str) -> list[dict[str, str]]:
    msgs: list[dict[str, str]] = []
    effective = _effective_system_prompt()
    if effective:
        msgs.append({"role": "system", "content": effective})
    # Only role/content go to the API; the local "name" field stays in the log
    msgs.extend(
        {"role": m["role"], "content": m["content"]} for m in _sessions[_current_session]
    )
    msgs.append({"role": "user", "content": user_input})
    return _trim_history(msgs)

def chat_once(user_input: str) -> bool:
    global _last_assistant_text

    api_messages = _build_messages_for_api(user_input)
    response = send_chat(api_messages, stream=_stream_mode)
    if not response:
        return False

    _sessions[_current_session].append(
        {"role": "user", "content": user_input, "name": username}
    )

    print(f"\n{Fore.YELLOW}NekoChat ({_effective_settings()['model']}):{Style.RESET_ALL} ", end="", flush=True)

    if _stream_mode:
        assistant_text, completed = stream_response(response)
    else:
        assistant_text, completed = batch_response(response)

    if not completed or not assistant_text:
        _sessions[_current_session].pop()
        print(f"{Fore.YELLOW}[~] この応答は履歴に追加しませんでした。{Style.RESET_ALL}")
        _last_assistant_text = ""
        _session_last_text[_current_session] = ""
        return False

    _sessions[_current_session].append({"role": "assistant", "content": assistant_text})
    _last_assistant_text = assistant_text
    _session_last_text[_current_session] = assistant_text
    _save_session_atomic(_current_session)  # auto-save after every exchange
    try:
        _discord_auto_after_reply()
    except Exception as e:  # a delivery problem must never break the chat itself
        print(f"{Fore.YELLOW}[~] discord auto mode: {type(e).__name__}; this exchange may not have "
              f"been sent.{Style.RESET_ALL}")
    return True

# ============ RENDER LAST RESPONSE ============
def render_last() -> None:
    if not _last_assistant_text:
        print(f"{Fore.YELLOW}[~] No assistant response to render yet.{Style.RESET_ALL}")
        return
    print(f"\n{Fore.YELLOW}--- Rendered (Markdown) ---{Style.RESET_ALL}\n")
    print(render_markdown(_last_assistant_text))
    print(f"\n{Fore.YELLOW}---------------------------{Style.RESET_ALL}\n")

# ============ SAVE CODE ============
def _extract_code_blocks(text: str) -> list[tuple[str, str]]:
    pattern = r"```([\w+\-#]*)\n(.*?)\n```"
    return re.findall(pattern, text, re.DOTALL)

def _guess_extension(lang: str) -> str:
    return LANG_EXT.get(lang.lower(), ".txt")

def save_code() -> None:
    if not _last_assistant_text:
        print(f"{Fore.YELLOW}[~] No assistant response to extract code from.{Style.RESET_ALL}")
        return

    blocks = _extract_code_blocks(_last_assistant_text)
    if not blocks:
        print(
            f"{Fore.YELLOW}[~] No code blocks (```...```) found in last response.{Style.RESET_ALL}"
        )
        return

    print(f"\n{Fore.YELLOW}Code blocks found: {len(blocks)}{Style.RESET_ALL}")
    for i, (lang, code_text) in enumerate(blocks, 1):
        lang_display = lang if lang else "(no language)"
        line_count = code_text.count("\n") + 1
        preview = code_text[:80].replace("\n", " ")
        suffix = "..." if len(code_text) > 80 else ""
        print(f"  {i}. [{lang_display}] {line_count} lines — {preview}{suffix}")

    choice = _ask(
        f"\n{Fore.CYAN}[+] Select block number (Enter = 1, [all] = save each): {Style.RESET_ALL}"
    )

    if choice.lower() == "all":
        saved = []
        for idx, (lang, code_text) in enumerate(blocks, 1):
            ext = _guess_extension(lang)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = os.path.join(CODE_DIR, f"snippet_{ts}_{idx}{ext}")
            with open(fname, "w", encoding="utf-8") as f:
                f.write(code_text)
            saved.append(fname)
        print(f"{Fore.GREEN}[OK] Saved {len(saved)} file(s) to {CODE_DIR}/{Style.RESET_ALL}")
        for s in saved:
            print(f"  - {os.path.basename(s)}")
        return

    if not choice:
        choice = "1"
    if not choice.isdigit():
        print(f"{Fore.RED}[!] Invalid selection.{Style.RESET_ALL}")
        return

    idx = int(choice) - 1
    if not (0 <= idx < len(blocks)):
        print(f"{Fore.RED}[!] Invalid selection.{Style.RESET_ALL}")
        return

    lang, code_text = blocks[idx]
    ext = _guess_extension(lang)
    default_name = f"snippet{ext}"
    raw_name = _ask(f"{Fore.CYAN}[+] Filename (Enter for '{default_name}'): {Style.RESET_ALL}")
    fname = _safe_filename(raw_name) if raw_name else default_name
    if not os.path.splitext(fname)[1]:
        fname += ext

    path = os.path.join(CODE_DIR, fname)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(code_text)
        print(f"{Fore.GREEN}[OK] Code saved: {path}{Style.RESET_ALL}")
    except OSError as e:
        print(f"{Fore.RED}[!] Save failed: {e}{Style.RESET_ALL}")

# ============ EXPORT ============
def export_session() -> None:
    if not _sessions[_current_session]:
        print(f"{Fore.YELLOW}[~] No conversation to export.{Style.RESET_ALL}")
        return

    raw = _ask(f"{Fore.CYAN}[+] Export filename (Enter for auto): {Style.RESET_ALL}")
    if raw:
        fname = _safe_filename(raw)
        if not fname.endswith(".md"):
            fname += ".md"
    else:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"export_{ts}.md"

    include_system = False
    if _effective_system_prompt():
        sp_choice = _ask(
            f"{Fore.CYAN}[+] Include system prompt in export? y/N: {Style.RESET_ALL}"
        ).lower()
        include_system = sp_choice == "y"

    lines = []
    lines.append("# NekoChat Session Export\n")
    lines.append(f"- **Model:** {_effective_settings()['model']}\n")
    lines.append(f"- **Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    if include_system:
        lines.append(f"- **System Prompt:** {_effective_system_prompt()}\n")
    lines.append("\n---\n")

    for msg in _sessions[_current_session]:
        role = f"User ({_msg_name(msg)})" if msg["role"] == "user" else "Assistant"
        lines.append(f"\n## {role}\n\n{msg['content']}\n")

    lines.append("\n---\n\n*Exported by NekoChat*\n")

    path = os.path.join(EXPORT_DIR, fname)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("".join(lines))
        print(f"{Fore.GREEN}[OK] Exported to: {path}{Style.RESET_ALL}")
    except OSError as e:
        print(f"{Fore.RED}[!] Export failed: {e}{Style.RESET_ALL}")

# ============ EXPORT (exchange range) ============
# One "exchange" = an assistant message plus the user message right before it.
# Indexes follow Python lists: 0 = oldest, -1 = latest. Ranges are slices
# (start:stop:step, stop excluded), e.g. [export -3:] [export 2:5] [export ::-1].
EXPORT_Q_LIMIT = 500   # longer questions are shortened unless "full" is given
EXPORT_Q_HEAD = 350
EXPORT_Q_TAIL = 150

_EXPORT_CMD_RE = re.compile(r"^\[export\s+(.*?)\s*\]$", re.IGNORECASE)
_EXPORT_INDEX_RE = re.compile(r"^-?\d+$")
_EXPORT_SLICE_RE = re.compile(r"^(-?\d*):(-?\d*)(?::(-?\d*))?$")
_EXPORT_FLAGS = ("rev", "bare", "full")

EXPORT_USAGE = (
    "Usage: [export] | [export list] | [export <index|slice> [rev] [bare] [full]]\n"
    "  index : 0 = oldest, -1 = latest          e.g. [export -1]\n"
    "  slice : start:stop:step (stop excluded)  e.g. [export -3:]  [export 2:5]  [export ::-1]\n"
    "  rev   : reverse the selected order       bare : answers only\n"
    "  full  : do not shorten long questions"
)


def _exchanges(session: Optional[str] = None) -> list[tuple[str, str, str]]:
    """(question, answer, asker name) of a session (default: the current one), oldest first."""
    history = _sessions.get(session if session is not None else _current_session, [])
    result: list[tuple[str, str, str]] = []
    for i, msg in enumerate(history):
        if msg["role"] != "assistant":
            continue
        question = ""
        asker = ""
        if i > 0 and history[i - 1]["role"] == "user":
            question = history[i - 1]["content"]
            asker = _msg_name(history[i - 1])
        result.append((question, msg["content"], asker))
    return result


def _parse_export_args(raw: str, n: int) -> tuple[Optional[dict], Optional[str]]:
    """Parse the text inside [export ...]. Returns (parsed, error)."""
    tokens = raw.lower().split()
    if "list" in tokens:
        if len(tokens) > 1:
            return None, "'list' cannot be combined with other arguments."
        return {"list": True}, None

    flags: set[str] = set()
    sel: Optional[str] = None
    for tok in tokens:
        if tok in _EXPORT_FLAGS:
            flags.add(tok)
        elif _EXPORT_INDEX_RE.match(tok) or _EXPORT_SLICE_RE.match(tok):
            if sel is not None:
                return None, "Only one index or slice is allowed."
            sel = tok
        else:
            return None, f"Unknown argument: {tok}"

    if sel is None:
        picked = list(range(n))
        sel_text = ":"
    elif _EXPORT_INDEX_RE.match(sel):
        k = int(sel)
        if not (-n <= k < n):
            return None, f"Index {k} out of range (valid: {-n} to {n - 1})."
        picked = [k % n]
        sel_text = sel
    else:
        parts = [int(x) if x else None for x in _EXPORT_SLICE_RE.match(sel).groups()]
        if parts[2] == 0:
            return None, "Slice step cannot be zero."
        picked = list(range(n))[slice(*parts)]
        sel_text = sel

    if "rev" in flags:
        picked.reverse()
    return {"picked": picked, "flags": flags, "sel": sel_text}, None


def _balance_fences(text: str, inside: bool = False) -> str:
    """Make sure ``` fences in a cut-out piece are paired."""
    if inside:
        text = "```\n" + text
    if text.count("```") % 2 == 1:
        text += "\n```"
    return text


def _shorten_question(q: str) -> str:
    """Keep head + tail of a long question (imported files put the real
    question at the END of the message)."""
    if len(q) <= EXPORT_Q_LIMIT:
        return q
    head = q[:EXPORT_Q_HEAD]
    tail = q[-EXPORT_Q_TAIL:]
    tail_inside = q[: len(q) - EXPORT_Q_TAIL].count("```") % 2 == 1
    note = (
        f"…（全 {len(q):,} 文字のうち先頭 {EXPORT_Q_HEAD} 文字と"
        f"末尾 {EXPORT_Q_TAIL} 文字を表示）…"
    )
    short = f"{_balance_fences(head)}\n\n{note}\n\n{_balance_fences(tail, tail_inside)}"
    return short if len(short) < len(q) else q  # never make it longer


def _quote(text: str) -> str:
    lines = text.splitlines() or [""]
    return "\n".join(f"> {ln}" if ln else ">" for ln in lines)


def _build_exchange_md(
    exs: list[tuple[str, str, str]], picked: list[int], flags: set[str], sel_text: str
) -> str:
    n = len(exs)

    def heading(i: int) -> str:
        return f"## #{i} ({i - n})"

    if "bare" in flags:
        if len(picked) == 1:
            return exs[picked[0]][1].rstrip("\n") + "\n"
        blocks = [f"{heading(i)}\n\n{exs[i][1].rstrip()}" for i in picked]
        return "\n\n---\n\n".join(blocks) + "\n"

    if len(picked) == 1:
        order = "1 exchange"
    else:
        if picked == sorted(picked):
            how = "oldest first"
        elif picked == sorted(picked, reverse=True):
            how = "newest first"
        else:
            how = "custom order"
        order = f"{len(picked)} exchanges, {how}"

    lines = [
        "# NekoChat Export\n",
        f"- **Session:** {_current_session}\n",
        f"- **Selection:** {sel_text} ({order})\n",
        f"- **Model:** {_effective_settings()['model']} (at export)\n",
        f"- **Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        "\n---\n",
    ]
    for i in picked:
        question, answer, asker = exs[i]
        lines.append(f"\n{heading(i)}\n")
        if question:
            q = question if "full" in flags else _shorten_question(question)
            label = f"User ({asker})" if asker else "User"
            lines.append(f"\n### {label}\n\n{_quote(q)}\n")
        lines.append(f"\n### Assistant\n\n{answer.rstrip()}\n")
        lines.append("\n---\n")
    lines.append("\n*Exported by NekoChat*\n")
    return "".join(lines)


def _export_filename(picked: list[int], flags: set[str]) -> str:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    lo, hi = min(picked), max(picked)
    span = f"{lo:04d}" if lo == hi else f"{lo:04d}-{hi:04d}"
    if len(picked) > 1 and sorted(picked) != list(range(lo, hi + 1)):
        span += "_sparse"
    suffix = "".join(f"_{f}" for f in _EXPORT_FLAGS if f in flags)
    base = f"export_{ts}_{_safe_filename(_current_session)}_{span}{suffix}"
    name = f"{base}.md"
    k = 2
    while os.path.exists(os.path.join(EXPORT_DIR, name)):
        name = f"{base}_{k}.md"
        k += 1
    return name


def _one_line(text: str, limit: int) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= limit else flat[:limit] + "…"


def _print_exchange_list(exs: list[tuple[str, str, str]]) -> None:
    n = len(exs)
    w = len(str(n - 1))
    print(
        f"\n{Fore.YELLOW}Exchanges in '{_current_session}' "
        f"(oldest first, {n} total):{Style.RESET_ALL}"
    )
    for i, (q, a, who) in enumerate(exs):
        print(
            f"  [{i:>{w}}] ({i - n:>{w + 1}}) "
            f"{who or 'Q'}: {_one_line(q, 40) or '-'} | A: {_one_line(a, 40)}"
        )
    print()


def export_exchanges(raw: str) -> None:
    """[export <index|slice> [rev] [bare] [full]] and [export list]."""
    exs = _exchanges()
    if not exs:
        print(f"{Fore.YELLOW}[~] No conversation to export.{Style.RESET_ALL}")
        return

    parsed, err = _parse_export_args(raw, len(exs))
    if err or parsed is None:
        print(f"{Fore.RED}[!] {err}{Style.RESET_ALL}\n{EXPORT_USAGE}")
        return
    if parsed.get("list"):
        _print_exchange_list(exs)
        return

    picked = parsed["picked"]
    if not picked:
        print(f"{Fore.YELLOW}[~] Nothing matches that selection.{Style.RESET_ALL}")
        return

    md = _build_exchange_md(exs, picked, parsed["flags"], parsed["sel"])
    path = os.path.join(EXPORT_DIR, _export_filename(picked, parsed["flags"]))
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
        print(
            f"{Fore.GREEN}[OK] Exported {len(picked)} exchange(s) to: {path}{Style.RESET_ALL}"
        )
    except OSError as e:
        print(f"{Fore.RED}[!] Export failed: {e}{Style.RESET_ALL}")

# ============ DISCORD ============
# [discord ...] posts chosen exchanges to Discord channels through webhooks (a simple path:
# no bot token, no thread creation). Selection syntax and flags are the same as [export].
# A webhook URL contains a secret token: it is kept in discord_webhooks.txt (owner-only,
# git-ignored) or DISCORD_WEBHOOK_URL, entered with hidden input, and never printed.
DISCORD_FILE = "discord_webhooks.txt"
DISCORD_ENV = "DISCORD_WEBHOOK_URL"
DISCORD_MESSAGE_INTERVAL = 3.0   # seconds between two posts to the SAME webhook (by webhook ID)
DISCORD_LIMIT = 2000             # Discord's per-message limit (counted in UTF-16 code units)
DISCORD_CHUNK = 1900             # target size when a message has to be split
DISCORD_CONT = "\n(続く...)"
DISCORD_RETRY_MAX = 5            # re-sends after HTTP 429
DISCORD_RETRY_WAIT_MAX = 60.0    # longest single wait for a 429
DISCORD_MAX_MESSAGES = 100       # refuse sends needing more messages than this
DISCORD_RESERVED = frozenset({"webhook", "bot", "all", "to", "list", "add", "rm", "env", "auto", "on", "off"})
DISCORD_LABEL_RE = re.compile(r"[a-z0-9][a-z0-9_-]{0,31}")
_DISCORD_URL_RE = re.compile(
    r"https://(?:(?:canary|ptb)\.)?discord(?:app)?\.com/api(?:/v\d+)?/webhooks/"
    r"(\d{5,25})/([A-Za-z0-9_-]{10,200})(?:\?thread_id=(\d{5,25}))?"
)
DISCORD_USAGE = (
    "Usage: [discord] | [discord list] | [discord add webhook [LABEL]] | [discord rm LABEL]\n"
    "       [discord <index|slice> [rev] [bare] [full] [to LABEL... | webhook | all]]\n"
    "  index : 0 = oldest, -1 = latest   e.g. [discord -1]  [discord 2:5]  [discord -3: to main]\n"
    "  rev   : reverse the order         bare : answers only      full : do not shorten long questions\n"
    "  to    : destinations (default: every registered webhook)\n"
    "  auto  : [discord auto on -3: [bare] [full] [to LABEL...]]  post by itself whenever 3 new exchanges\n"
    "          are pending (-1: = after every reply) | [discord auto off] | [discord auto flush] | [discord auto]"
)


class DiscordError(Exception):
    pass


def _u16len(text: str) -> int:
    """Length in UTF-16 code units - how Discord counts its 2000-character limit."""
    return len(text.encode("utf-16-le", "surrogatepass")) // 2


def _discord_hook(label: str, url: str, source: str, line: Optional[int]) -> Optional[dict]:
    m = _DISCORD_URL_RE.fullmatch(url)
    if not m:
        return None
    return {"label": label, "url": url, "id": m.group(1), "token": m.group(2),
            "thread_id": m.group(3) or "", "source": source, "line": line}


def load_discord_hooks() -> tuple[list[dict], list[str], str]:
    """Registered webhooks -> (hooks, warnings, file format: "none" | "text" | "json").

    discord_webhooks.txt: one webhook per line, "URL" or "LABEL URL", '#' starts a comment;
    or a JSON array of URLs / object {label: URL}. DISCORD_WEBHOOK_URL adds one more ("env").
    Warnings never include the text of a bad line (it may be a secret)."""
    warns: list[str] = []
    entries: list[tuple[Optional[str], str, Optional[int]]] = []  # (label, url, line number)
    fmt = "none"
    raw: Optional[str] = None
    try:
        with open(DISCORD_FILE, "r", encoding="utf-8") as f:
            raw = f.read()
    except FileNotFoundError:
        pass
    except (OSError, UnicodeDecodeError) as e:
        warns.append(f"{DISCORD_FILE} could not be read ({type(e).__name__}).")
    if raw is not None and raw.strip():
        text = raw.lstrip("\ufeff").strip()
        data: Any = None
        if text[:1] in "[{":
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = None
        if isinstance(data, (list, dict)):
            fmt = "json"
            items = list(data.items()) if isinstance(data, dict) else [(None, u) for u in data]
            for k, (label, u) in enumerate(items, 1):
                if isinstance(u, str) and (label is None or isinstance(label, str)):
                    entries.append((label, u.strip(), k))
                else:
                    warns.append(f"{DISCORD_FILE}: item {k} is not a text URL (ignored).")
        else:
            fmt = "text"
            for no, line in enumerate(raw.lstrip("\ufeff").splitlines(), 1):
                st = line.strip()
                if not st or st.startswith("#"):
                    continue
                parts = st.split()
                if len(parts) == 1:
                    entries.append((None, parts[0], no))
                elif len(parts) == 2:
                    entries.append((parts[0], parts[1], no))
                else:
                    warns.append(f"{DISCORD_FILE} line {no}: expected 'URL' or 'LABEL URL' (ignored).")
    hooks: list[dict] = []
    used: set[str] = set()
    seen: dict[tuple[str, str], str] = {}
    pending: list[tuple[dict, int]] = []
    for label, url, no in entries:
        where = f"{DISCORD_FILE} {'item' if fmt == 'json' else 'line'} {no}"
        if label is not None and (not DISCORD_LABEL_RE.fullmatch(label) or label in DISCORD_RESERVED):
            warns.append(f"{where}: the label is not allowed (use a-z, 0-9, '-' and '_'; "
                         f"not {', '.join(sorted(DISCORD_RESERVED))}) (ignored).")
            continue
        if label is not None and label in used:
            warns.append(f"{where}: the label '{label}' is already used (ignored).")
            continue
        h = _discord_hook(label or "", url, "file", no)
        if h is None:
            warns.append(f"{where}: not a Discord webhook URL (ignored).")
            continue
        key = (h["id"], h["thread_id"])
        if key in seen:
            warns.append(f"{where}: the same webhook as '{seen[key]}' (ignored).")
            continue
        if label is not None:
            used.add(label)
            seen[key] = label
            hooks.append(h)
        else:
            pending.append((h, len(hooks)))
            seen[key] = "(unlabeled)"
            hooks.append(h)
    n = 0
    for h, _ in pending:  # unlabeled entries get webhook1, webhook2, ... in file order
        n += 1
        while f"webhook{n}" in used:
            n += 1
        h["label"] = f"webhook{n}"
        used.add(h["label"])
    env_url = (os.environ.get(DISCORD_ENV) or "").strip()
    if env_url:
        h = _discord_hook("env", env_url, "env", None)
        if h is None:
            warns.append(f"{DISCORD_ENV} is not a Discord webhook URL (ignored).")
        elif (h["id"], h["thread_id"]) not in seen:
            hooks.append(h)
    if hooks and fmt != "none" and os.name == "posix":
        try:
            if os.stat(DISCORD_FILE).st_mode & 0o077:
                warns.append(f"{DISCORD_FILE} can be read by other users; run: chmod 600 {DISCORD_FILE}")
        except OSError:
            pass
    return hooks, warns, fmt


def _discord_write(lines: list[str]) -> None:
    """Rewrite discord_webhooks.txt atomically with owner-only permissions."""
    tmp = DISCORD_FILE + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(ln if ln.endswith("\n") else ln + "\n" for ln in lines))
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, DISCORD_FILE)


def _discord_read_lines() -> list[str]:
    try:
        with open(DISCORD_FILE, "r", encoding="utf-8") as f:
            return f.read().splitlines(keepends=True)
    except FileNotFoundError:
        return []


def _hook_desc(h: dict) -> str:
    where = f"thread {h['thread_id']}" if h["thread_id"] else "channel"
    return f"{h['label']:<12} ...{h['token'][-4:]}   {where}"


def discord_status() -> None:
    hooks, warns, fmt = load_discord_hooks()
    print(f"\n{Fore.YELLOW}Discord webhooks ({DISCORD_FILE}):{Style.RESET_ALL}")
    if not hooks:
        print("  (none yet - add one with [discord add webhook])")
    for h in hooks:
        note = f"   (from {DISCORD_ENV})" if h["source"] == "env" else ""
        print(f"  [webhook] {_hook_desc(h)}{note}")
    for w in warns:
        print(f"{Fore.YELLOW}[~] {w}{Style.RESET_ALL}")
    print(f"\n{DISCORD_USAGE}\n")


def discord_add_webhook(label: Optional[str]) -> None:
    hooks, _, fmt = load_discord_hooks()
    if fmt == "json":
        print(f"{Fore.YELLOW}[~] {DISCORD_FILE} is in JSON format; edit it by hand "
              f"(or use the 'LABEL URL' line format).{Style.RESET_ALL}")
        return
    labels = {h["label"] for h in hooks}
    if label is None:
        n = 1
        while f"webhook{n}" in labels:
            n += 1
        label = f"webhook{n}"
    elif not DISCORD_LABEL_RE.fullmatch(label) or label in DISCORD_RESERVED:
        print(f"{Fore.RED}[!] Invalid label. Use a-z, 0-9, '-' and '_' (up to 32 characters); "
              f"not {', '.join(sorted(DISCORD_RESERVED))}.{Style.RESET_ALL}")
        return
    elif label in labels:
        print(f"{Fore.RED}[!] The label '{label}' already exists.{Style.RESET_ALL}")
        return
    try:
        url = getpass.getpass(
            f"Webhook URL for '{label}' (input hidden, Enter=cancel): "
        ).strip()
    except (EOFError, KeyboardInterrupt):
        print(f"\n{Fore.YELLOW}[~] Cancelled.{Style.RESET_ALL}")
        return
    if not url:
        return
    h = _discord_hook(label, url, "file", None)
    if h is None:
        print(f"{Fore.RED}[!] That is not a Discord webhook URL "
              f"(https://discord.com/api/webhooks/ID/TOKEN, optionally ?thread_id=ID).{Style.RESET_ALL}")
        return
    for other in hooks:
        if (other["id"], other["thread_id"]) == (h["id"], h["thread_id"]):
            print(f"{Fore.RED}[!] That webhook is already registered as '{other['label']}'.{Style.RESET_ALL}")
            return
    lines = _discord_read_lines()
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    lines.append(f"{label} {url}\n")
    try:
        _discord_write(lines)
    except OSError as e:
        print(f"{Fore.RED}[!] Could not write {DISCORD_FILE}: {type(e).__name__}.{Style.RESET_ALL}")
        return
    print(f"{Fore.GREEN}[OK] Webhook '{label}' added (...{h['token'][-4:]}). "
          f"The file is owner-only; never commit it.{Style.RESET_ALL}")


def discord_remove(label: str) -> None:
    hooks, _, fmt = load_discord_hooks()
    h = next((x for x in hooks if x["label"] == label), None)
    if h is None:
        print(f"{Fore.YELLOW}[~] No webhook is registered as '{label}'.{Style.RESET_ALL}")
        return
    if h["source"] == "env":
        print(f"{Fore.YELLOW}[~] '{label}' comes from the environment variable {DISCORD_ENV}; "
              f"unset it instead.{Style.RESET_ALL}")
        return
    if fmt == "json":
        print(f"{Fore.YELLOW}[~] {DISCORD_FILE} is in JSON format; edit it by hand.{Style.RESET_ALL}")
        return
    if _ask(f"{Fore.CYAN}[+] Remove '{label}' (...{h['token'][-4:]})? (y/N): {Style.RESET_ALL}").lower() \
            not in ("y", "yes"):
        print(f"{Fore.YELLOW}[~] Cancelled.{Style.RESET_ALL}")
        return
    lines = _discord_read_lines()
    idx = (h["line"] or 0) - 1
    if not (0 <= idx < len(lines)):
        print(f"{Fore.RED}[!] The file changed; try again.{Style.RESET_ALL}")
        return
    del lines[idx]
    try:
        _discord_write(lines)
    except OSError as e:
        print(f"{Fore.RED}[!] Could not write {DISCORD_FILE}: {type(e).__name__}.{Style.RESET_ALL}")
        return
    print(f"{Fore.GREEN}[OK] Webhook '{label}' removed.{Style.RESET_ALL}")


def _discord_split(text: str, budget: int = DISCORD_CHUNK) -> list[str]:
    """Cut text into messages Discord accepts: at line boundaries when possible, code fences
    closed and reopened across the cut, UTF-16 length counted, continuation marker added."""
    if _u16len(text) <= DISCORD_LIMIT:
        return [text]
    chunks: list[str] = []
    cur: list[str] = []
    cur_len = 0

    def flush() -> None:
        nonlocal cur, cur_len
        if cur:
            chunks.append("\n".join(cur))
        cur, cur_len = [], 0

    for line in text.split("\n"):
        ll = _u16len(line)
        if ll > budget:  # a single very long line: cut it by characters
            flush()
            piece, pl = "", 0
            for ch in line:
                cl = _u16len(ch)
                if pl + cl > budget:
                    chunks.append(piece)
                    piece, pl = "", 0
                piece += ch
                pl += cl
            if piece:
                cur, cur_len = [piece], pl
            continue
        add = ll + (1 if cur else 0)
        if cur_len + add > budget:
            flush()
            cur, cur_len = [line], ll
        else:
            cur.append(line)
            cur_len += add
    flush()
    chunks = [c.strip("\n") for c in chunks if c.strip()]
    out: list[str] = []
    inside = False
    for i, c in enumerate(chunks):
        fixed = _balance_fences(c, inside)
        inside ^= (c.count("```") % 2 == 1)
        if i < len(chunks) - 1:
            fixed += DISCORD_CONT
        out.append(fixed)
    return out


def _known_secrets() -> list[str]:
    """Secret values NekoChat itself knows (API keys, webhook URLs and tokens), longest first."""
    vals: set[str] = set()
    for prov, spec in PROVIDERS.items():
        if spec.get("key_env"):
            k = get_api_key(prov)
            if k:
                vals.add(k)
    for h in load_discord_hooks()[0]:
        vals.update((h["url"], h["token"]))
    return sorted((v for v in vals if len(v) >= 8), key=len, reverse=True)


def _redact(text: str, secrets: Any) -> tuple[str, int]:
    count = 0
    for sec in secrets:
        c = text.count(sec)
        if c:
            text = text.replace(sec, "[redacted]")
            count += c
    return text, count


def _discord_messages(
    exs: list[tuple[str, str, str]], picked: list[int], flags: set[str], now: datetime.datetime
) -> list[dict]:
    """Messages to post, in order: [{"ex": exchange index, "part": k, "of": m, "text": ...}]."""
    return _discord_build(exs, picked, flags, now)[0]


def _discord_build(
    exs: list[tuple[str, str, str]], picked: list[int], flags: set[str], now: datetime.datetime,
    secrets: Any = (),
) -> tuple[list[dict], int]:
    """Like _discord_messages, but known secrets are replaced by [redacted].
    Returns (messages, number of values hidden)."""
    stamp = now.strftime("%Y-%m-%d %H:%M")
    out: list[dict] = []
    hidden = 0
    for i in picked:
        question, answer, asker = exs[i]
        parts = [f"**#{i}** : {asker or username} : {stamp}"]
        if "bare" not in flags and question:
            q = question if "full" in flags else _shorten_question(question)
            parts += [_quote(q), ""]
        parts.append(answer.rstrip())
        text, c = _redact("\n".join(parts), secrets)
        hidden += c
        chunks = _discord_split(text)
        for k, c in enumerate(chunks, 1):
            out.append({"ex": i, "part": k, "of": len(chunks), "text": c})
    return out, hidden


def _discord_clean(text: str, hook: dict) -> str:
    for secret in (hook["url"], hook["token"]):
        text = text.replace(secret, "...")
    return " ".join(text.split())[:120]


def _discord_sleep(seconds: float) -> None:
    time.sleep(seconds)


def _discord_clock() -> float:
    return time.monotonic()


def _retry_after(resp: Any) -> float:
    try:
        v = float(resp.json().get("retry_after", 0))
    except (ValueError, TypeError, AttributeError, json.JSONDecodeError):
        v = 0.0
    if v <= 0:
        try:
            v = float(resp.headers.get("Retry-After", 0))
        except (ValueError, TypeError, AttributeError):
            v = 0.0
    return v if v > 0 else 1.0


def _discord_post(hook: dict, content: str) -> None:
    """POST one message to a webhook. Errors never contain the URL or token."""
    payload = {"content": content, "allowed_mentions": {"parse": []}}  # no @everyone / role pings
    for attempt in range(DISCORD_RETRY_MAX + 1):
        try:
            resp = requests.post(hook["url"], json=payload, timeout=30)
        except requests.RequestException as e:
            raise DiscordError(f"network error ({type(e).__name__})") from None
        if resp.status_code == 429:
            if attempt >= DISCORD_RETRY_MAX:
                raise DiscordError(f"rate limited (HTTP 429); gave up after {DISCORD_RETRY_MAX} retries")
            _discord_sleep(min(_retry_after(resp), DISCORD_RETRY_WAIT_MAX))
            continue
        if resp.status_code >= 400:
            detail = ""
            try:
                body = resp.json()
                detail = str(body.get("message", "")) if isinstance(body, dict) else ""
            except (ValueError, json.JSONDecodeError):
                detail = resp.text or ""
            raise DiscordError(f"HTTP {resp.status_code}: {_discord_clean(detail, hook)}".rstrip(": "))
        return


_discord_last: dict[str, float] = {}   # webhook ID -> when its last post finished (shared by all sends)


def _discord_deliver(
    hooks: list[dict], messages: list[dict], last: Optional[dict[str, float]] = None, progress: bool = True
) -> dict:
    """Send every message to every webhook. Posts to different webhooks follow each other
    at once; two posts to the same webhook ID are at least DISCORD_MESSAGE_INTERVAL apart.
    A webhook that fails stops receiving; the others carry on."""
    status = {h["label"]: {"sent": 0, "failed": None} for h in hooks}
    if last is None:
        last = _discord_last   # also spaces a manual send right after an automatic one
    total = len(messages)
    interrupted = False
    try:
        for mi, m in enumerate(messages, 1):
            marks: list[str] = []
            for h in hooks:
                st = status[h["label"]]
                if st["failed"]:
                    continue
                if h["id"] in last:
                    remain = last[h["id"]] + DISCORD_MESSAGE_INTERVAL - _discord_clock()
                    if remain > 0:
                        _discord_sleep(remain)
                try:
                    _discord_post(h, m["text"])
                    st["sent"] += 1
                    marks.append(f"{Fore.GREEN}{h['label']}{Style.RESET_ALL}")
                except DiscordError as ex:
                    st["failed"] = {"exchange": m["ex"], "message": mi, "reason": str(ex)}
                    marks.append(f"{Fore.RED}{h['label']} FAILED{Style.RESET_ALL}")
                finally:
                    last[h["id"]] = _discord_clock()
            if progress:
                print(f"  {mi}/{total}  " + "  ".join(marks))
            if all(st["failed"] for st in status.values()):
                break
    except KeyboardInterrupt:
        interrupted = True
    return {"status": status, "total": total, "interrupted": interrupted}


def _discord_report(result: dict) -> None:
    total = result["total"]
    if result["interrupted"]:
        print(f"{Fore.YELLOW}[~] Interrupted.{Style.RESET_ALL}")
    for label, st in result["status"].items():
        if st["failed"]:
            f = st["failed"]
            print(f"{Fore.RED}[!] {label}: stopped at exchange #{f['exchange']} "
                  f"(message {f['message']}/{total}): {f['reason']} - {st['sent']}/{total} sent{Style.RESET_ALL}")
        elif st["sent"] == total:
            print(f"{Fore.GREEN}[OK] {label}: {st['sent']}/{total} sent{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}[~] {label}: {st['sent']}/{total} sent{Style.RESET_ALL}")


def _discord_targets(names: list[str], hooks: list[dict]) -> tuple[list[dict], Optional[str]]:
    if not names:
        return list(hooks), None
    chosen: list[dict] = []
    for t in names:
        if t in ("all", "webhook"):
            group = list(hooks)
        elif t == "bot":
            return [], "Bot destinations are not available yet."
        else:
            group = [h for h in hooks if h["label"] == t]
            if not group:
                return [], f"Unknown destination '{t}'. Registered: {', '.join(h['label'] for h in hooks)}."
        for h in group:
            if h not in chosen:
                chosen.append(h)
    return chosen, None


def _estimate_seconds(hooks: list[dict], n_messages: int) -> int:
    per_id: dict[str, int] = {}
    for h in hooks:
        per_id[h["id"]] = per_id.get(h["id"], 0) + n_messages
    worst = max(per_id.values()) if per_id else 0
    return int(round(max(worst - 1, 0) * DISCORD_MESSAGE_INTERVAL))


def discord_send(tokens: list[str]) -> None:
    exs = _exchanges()
    if not exs:
        print(f"{Fore.YELLOW}[~] No conversation to send.{Style.RESET_ALL}")
        return
    if tokens.count("to") > 1:
        print(f"{Fore.RED}[!] Use 'to' only once.{Style.RESET_ALL}\n{DISCORD_USAGE}")
        return
    left, right = tokens, []
    if "to" in tokens:
        i = tokens.index("to")
        left, right = tokens[:i], tokens[i + 1:]
        if not right:
            print(f"{Fore.RED}[!] Give at least one destination after 'to'.{Style.RESET_ALL}\n{DISCORD_USAGE}")
            return
    if not any(_EXPORT_INDEX_RE.match(t) or _EXPORT_SLICE_RE.match(t) for t in left):
        print(f"{Fore.RED}[!] Give an index or slice (e.g. -1, 2:5, or : for everything).{Style.RESET_ALL}\n{DISCORD_USAGE}")
        return
    parsed, err = _parse_export_args(" ".join(left), len(exs))
    if err or parsed is None or parsed.get("list"):
        print(f"{Fore.RED}[!] {err or 'Invalid arguments.'}{Style.RESET_ALL}\n{DISCORD_USAGE}")
        return
    picked = parsed["picked"]
    if not picked:
        print(f"{Fore.YELLOW}[~] Nothing matches that selection.{Style.RESET_ALL}")
        return
    hooks, warns, _ = load_discord_hooks()
    for w in warns:
        print(f"{Fore.YELLOW}[~] {w}{Style.RESET_ALL}")
    if not hooks:
        print(f"{Fore.YELLOW}[~] No webhook registered. Add one with [discord add webhook].{Style.RESET_ALL}")
        return
    targets, terr = _discord_targets(right, hooks)
    if terr:
        print(f"{Fore.RED}[!] {terr}{Style.RESET_ALL}")
        return
    messages, hidden = _discord_build(exs, picked, parsed["flags"], datetime.datetime.now(),
                                      _known_secrets())
    if hidden:
        print(f"{Fore.YELLOW}[~] Hid {hidden} known secret value(s) (API keys / webhook URLs) "
              f"before sending.{Style.RESET_ALL}")
    if len(messages) > DISCORD_MAX_MESSAGES:
        print(f"{Fore.RED}[!] That needs {len(messages)} messages per webhook (limit {DISCORD_MAX_MESSAGES}). "
              f"Choose fewer exchanges.{Style.RESET_ALL}")
        return
    chars = sum(len(m["text"]) for m in messages)
    names = ", ".join(h["label"] for h in targets)
    print(f"\n{Fore.YELLOW}Send {len(picked)} exchange(s) -> {len(targets)} webhook(s): {names}{Style.RESET_ALL}")
    print(f"  {len(messages)} message(s) each ({len(messages) * len(targets)} posts in total), "
          f"about {chars:,} characters")
    secs = _estimate_seconds(targets, len(messages))
    print(f"  Takes about {secs} seconds ({DISCORD_MESSAGE_INTERVAL:g} s between messages to the same "
          f"webhook). Ctrl+C stops it.")
    print("  First message:")
    first = messages[0]["text"].split("\n")
    for ln in first[:3]:
        print(f"    {ln[:80]}{'…' if len(ln) > 80 else ''}")
    if len(first) > 3:
        print(f"    … ({len(first) - 3} more line(s))")
    if _ask(f"{Fore.CYAN}[+] Send? (Y/n): {Style.RESET_ALL}").lower() not in ("", "y", "yes"):
        print(f"{Fore.YELLOW}[~] Cancelled; nothing was sent.{Style.RESET_ALL}")
        return
    _discord_report(_discord_deliver(targets, messages))


# ============ DISCORD AUTO MODE ============
# [discord auto on -3:] posts the newest exchanges by itself each time N new ones have piled
# up (-1: = after every reply). It is per session, kept in memory only (off at start-up), and
# only counts exchanges that happen after it was switched on. Leaving the session or quitting
# turns it off (pending exchanges can be sent first). Same webhooks, formatting, pacing and
# safety rules as the manual [discord ...] send, but without a confirmation per send.
DISCORD_AUTO_MAX_EVERY = 20
DISCORD_AUTO_MAX_MESSAGES = 30   # a batch needing more messages is held back, not sent
_AUTO_WINDOW_RE = re.compile(r"-(\d+):")
_discord_auto: dict[str, dict] = {}


def _manual_cmd(lo: int, hi: int, label: Optional[str] = None) -> str:
    """The manual command that sends exchanges lo..hi-1 (to one destination)."""
    return f"[discord {lo}:{hi}" + (f" to {label}" if label else "") + "]"


def _auto_pending(name: str) -> list[int]:
    st = _discord_auto.get(name)
    if not st:
        return []
    n = len(_exchanges(name))
    return list(range(min(st["sent_upto"], n), n))


def _discord_auto_clamp(name: Optional[str] = None) -> None:
    """The history got shorter ([undo], [clear], [load]): never count removed exchanges as sent."""
    name = name or _current_session
    st = _discord_auto.get(name)
    if st:
        st["sent_upto"] = min(st["sent_upto"], len(_exchanges(name)))


def _discord_auto_marker() -> str:
    st = _discord_auto.get(_current_session)
    if not st:
        return ""
    return (f" {Fore.MAGENTA}(discord {len(_auto_pending(_current_session))}/{st['every']})"
            f"{Style.RESET_ALL}")


def _discord_auto_send(name: str) -> None:
    """Send everything pending for `name` to its destinations (no confirmation)."""
    st = _discord_auto[name]
    exs = _exchanges(name)
    n = len(exs)
    first = min(st["sent_upto"], n)
    picked = list(range(first, n))
    if not picked:
        return
    hooks, _, _ = load_discord_hooks()
    registered = {h["label"] for h in hooks}
    for t in st["targets"]:
        if t not in registered:
            _warn_once(f"discord-gone:{name}:{t}", f"Destination '{t}' is no longer registered.")
    active = [h for h in hooks
              if (not st["targets"] or h["label"] in st["targets"]) and h["label"] not in st["paused"]]
    if not active:
        print(f"{Fore.RED}[!] discord: no usable destination left; auto mode is off. Not sent: "
              f"#{first}-#{n - 1}. Send by hand with {_manual_cmd(first, n)}.{Style.RESET_ALL}")
        _discord_auto.pop(name, None)
        return
    ordered = picked[::-1] if "rev" in st["flags"] else picked
    messages, redacted = _discord_build(exs, ordered, st["flags"], datetime.datetime.now(),
                                        _known_secrets())
    if len(messages) > DISCORD_AUTO_MAX_MESSAGES:
        st["sent_upto"] = n
        print(f"{Fore.YELLOW}[~] discord: exchanges #{first}-#{n - 1} need {len(messages)} messages "
              f"(auto mode sends at most {DISCORD_AUTO_MAX_MESSAGES}) and were NOT sent. "
              f"Send them by hand with {_manual_cmd(first, n)} (it asks first).{Style.RESET_ALL}")
        return
    if redacted:
        print(f"{Fore.YELLOW}[~] discord: hid {redacted} known secret value(s) before sending.{Style.RESET_ALL}")
    result = _discord_deliver(active, messages, progress=False)
    st["sent_upto"] = n
    failed = {label: s["failed"] for label, s in result["status"].items() if s["failed"]}
    if result["interrupted"]:
        print(f"{Fore.YELLOW}[~] discord: interrupted; auto mode is off. Not everything was sent; "
              f"resend by hand with {_manual_cmd(first, n, 'LABEL')}.{Style.RESET_ALL}")
        _discord_auto.pop(name, None)
        return
    ok_labels = [h["label"] for h in active if h["label"] not in failed]
    if ok_labels:
        print(f"{Fore.GREEN}[discord] {len(picked)} exchange(s), {len(messages)} message(s) -> "
              f"{', '.join(ok_labels)}{Style.RESET_ALL}")
    for label, f in failed.items():
        st["paused"].add(label)
        print(f"{Fore.RED}[!] discord: {label} stopped at exchange #{f['exchange']}: {f['reason']}. "
              f"Paused for this session; resend with {_manual_cmd(f['exchange'], n, label)}.{Style.RESET_ALL}")
    if failed and all(h["label"] in st["paused"] for h in active):
        print(f"{Fore.YELLOW}[~] discord: every destination is paused; auto mode is off "
              f"([discord auto on] starts it again).{Style.RESET_ALL}")
        _discord_auto.pop(name, None)


def _discord_auto_after_reply() -> None:
    """Called after every completed exchange."""
    name = _current_session
    st = _discord_auto.get(name)
    if not st:
        return
    pending = len(_auto_pending(name))
    if pending < st["every"]:
        if pending:
            print(f"{Fore.MAGENTA}[discord] waiting {pending}/{st['every']}{Style.RESET_ALL}")
        return
    _discord_auto_send(name)


def _discord_auto_leave(name: str) -> None:
    """Switch the mode off for a session that is being left or closed."""
    st = _discord_auto.get(name)
    if not st:
        return
    pending = _auto_pending(name)
    if pending:
        try:
            ans = _ask(f"{Fore.CYAN}[+] Send {len(pending)} pending exchange(s) now? (Y/n): {Style.RESET_ALL}")
        except (EOFError, KeyboardInterrupt):
            ans = "n"
        if ans.lower() in ("", "y", "yes"):
            if name in _discord_auto:
                _discord_auto_send(name)
        else:
            print(f"{Fore.YELLOW}[~] discord: not sent: #{pending[0]}-#{pending[-1]}. "
                  f"Send them later with [discord {pending[0]}:{pending[-1] + 1}].{Style.RESET_ALL}")
    _discord_auto.pop(name, None)


def _discord_auto_exit() -> None:
    for name in list(_discord_auto):
        _discord_auto_leave(name)


def discord_auto_status() -> None:
    name = _current_session
    st = _discord_auto.get(name)
    if not st:
        print(f"{Fore.YELLOW}[~] Auto mode is off for session '{name}'. "
              f"Start it with [discord auto on -3:] (see [discord]).{Style.RESET_ALL}")
        return
    pend = _auto_pending(name)
    print(f"\n{Fore.YELLOW}Auto mode for session '{name}': ON{Style.RESET_ALL}")
    print(f"  Window   : -{st['every']}:  (sends when {st['every']} new exchange(s) are pending)")
    print(f"  Pending  : {len(pend)}" + (f"  (#{pend[0]}-#{pend[-1]})" if pend else ""))
    print(f"  Flags    : {', '.join(sorted(st['flags'])) or '(none)'}")
    print(f"  To       : {', '.join(st['targets']) or 'every registered webhook'}")
    if st["paused"]:
        print(f"  Paused   : {', '.join(sorted(st['paused']))}")
    print()


def discord_auto_on(args: list[str]) -> None:
    left, right = args, []
    if "to" in args:
        i = args.index("to")
        left, right = args[:i], args[i + 1:]
        if not right or "to" in right:
            print(f"{Fore.RED}[!] Give destinations after a single 'to'.{Style.RESET_ALL}\n{DISCORD_USAGE}")
            return
    flags: set[str] = set()
    every: Optional[int] = None
    for t in left:
        m = _AUTO_WINDOW_RE.fullmatch(t)
        if t in ("rev", "bare", "full"):
            flags.add(t)
        elif m:
            if every is not None:
                print(f"{Fore.RED}[!] Give the window only once (e.g. -3:).{Style.RESET_ALL}")
                return
            every = int(m.group(1))
        elif t.isdigit() or _EXPORT_INDEX_RE.match(t) or _EXPORT_SLICE_RE.match(t):
            print(f"{Fore.RED}[!] Auto mode counts from the newest exchange: use -N: "
                  f"(e.g. -3: sends every 3 new exchanges, -1: after every reply).{Style.RESET_ALL}")
            return
        else:
            print(f"{Fore.RED}[!] Unknown argument '{t}'.{Style.RESET_ALL}\n{DISCORD_USAGE}")
            return
    every = 1 if every is None else every
    if not (1 <= every <= DISCORD_AUTO_MAX_EVERY):
        print(f"{Fore.RED}[!] The window must be between -1: and -{DISCORD_AUTO_MAX_EVERY}:.{Style.RESET_ALL}")
        return
    hooks, warns, _ = load_discord_hooks()
    for w in warns:
        print(f"{Fore.YELLOW}[~] {w}{Style.RESET_ALL}")
    if not hooks:
        print(f"{Fore.YELLOW}[~] No webhook registered. Add one with [discord add webhook].{Style.RESET_ALL}")
        return
    targets, terr = _discord_targets(right, hooks)
    if terr:
        print(f"{Fore.RED}[!] {terr}{Style.RESET_ALL}")
        return
    name = _current_session
    what = ("answers only" if "bare" in flags
            else "question (full) + answer" if "full" in flags else "question (shortened) + answer")
    print(f"\n{Fore.YELLOW}Auto mode (session '{name}'): -{every}: -> "
          f"{', '.join(h['label'] for h in targets)}{Style.RESET_ALL}")
    print(f"  Sends   : {what}, {'after every reply' if every == 1 else f'every {every} new exchanges, together'}")
    print("  Not sent: system prompts and plugin texts. Imported files appear in questions "
          "('bare' = answers only)!")
    print(f"  Posts to the same webhook are {DISCORD_MESSAGE_INTERVAL:g} s apart; a batch over "
          f"{DISCORD_AUTO_MAX_MESSAGES} messages is held back. Known API keys and webhook URLs are hidden.")
    print("  Off again when you quit or leave this session. [undo] cannot unsend what was posted.")
    if _ask(f"{Fore.CYAN}[+] Turn on? (Y/n): {Style.RESET_ALL}").lower() not in ("", "y", "yes"):
        print(f"{Fore.YELLOW}[~] Cancelled; auto mode stays as it was.{Style.RESET_ALL}")
        return
    old = _discord_auto.get(name)
    sent_upto = old["sent_upto"] if old else len(_exchanges(name))
    _discord_auto[name] = {
        "every": every, "flags": flags, "targets": [h["label"] for h in targets] if right else [],
        "sent_upto": sent_upto, "paused": set(),
    }
    _discord_auto_clamp(name)
    print(f"{Fore.GREEN}[OK] Auto mode is on for '{name}'. Stop it with [discord auto off].{Style.RESET_ALL}")


def discord_auto_off() -> None:
    name = _current_session
    if name not in _discord_auto:
        print(f"{Fore.YELLOW}[~] Auto mode is not on for session '{name}'.{Style.RESET_ALL}")
        return
    _discord_auto_leave(name)
    print(f"{Fore.GREEN}[OK] Auto mode is off for '{name}'.{Style.RESET_ALL}")


def discord_auto_flush() -> None:
    name = _current_session
    if name not in _discord_auto:
        print(f"{Fore.YELLOW}[~] Auto mode is not on for session '{name}'.{Style.RESET_ALL}")
        return
    if not _auto_pending(name):
        print(f"{Fore.YELLOW}[~] Nothing is pending.{Style.RESET_ALL}")
        return
    _discord_auto_send(name)


def discord_auto_command(args: list[str]) -> None:
    if not args:
        discord_auto_status()
    elif args[0] == "on":
        discord_auto_on(args[1:])
    elif args == ["off"]:
        discord_auto_off()
    elif args == ["flush"]:
        discord_auto_flush()
    else:
        print(f"{Fore.YELLOW}[~] Usage: [discord auto on [-N:] [bare] [full] [to LABEL...]] | "
              f"[discord auto off] | [discord auto flush] | [discord auto]{Style.RESET_ALL}")


def discord_command(norm: str) -> None:
    """Dispatch '[discord ...]' (norm is the lower-cased, whitespace-normalised command)."""
    if not norm.endswith("]"):
        print(f"{Fore.YELLOW}[~] {DISCORD_USAGE}{Style.RESET_ALL}")
        return
    args = norm[1:-1].split()[1:]
    if not args:
        discord_status()
    elif args == ["list"]:
        exs = _exchanges()
        if exs:
            _print_exchange_list(exs)
        else:
            print(f"{Fore.YELLOW}[~] No conversation yet.{Style.RESET_ALL}")
    elif args[0] == "auto":
        discord_auto_command(args[1:])
    elif args[0] == "add":
        if args[1:2] == ["webhook"] and len(args) <= 3:
            discord_add_webhook(args[2] if len(args) == 3 else None)
        elif args[1:2] == ["bot"]:
            print(f"{Fore.YELLOW}[~] Bot destinations are not available yet.{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}[~] Usage: [discord add webhook [LABEL]]{Style.RESET_ALL}")
    elif args[0] == "rm":
        if len(args) == 2:
            discord_remove(args[1])
        else:
            print(f"{Fore.YELLOW}[~] Usage: [discord rm LABEL]{Style.RESET_ALL}")
    else:
        discord_send(args)

# ============ IMPORT ============
def import_file() -> None:
    raw_path = _ask(f"{Fore.CYAN}[+] File path: {Style.RESET_ALL}")
    # Strip surrounding quotes that shell or copy-paste may add
    raw_path = raw_path.strip("'\"")
    path = os.path.expanduser(raw_path)
    if not path or not os.path.isfile(path):
        print(f"{Fore.RED}[!] File not found.{Style.RESET_ALL}")
        return

    ext = os.path.splitext(path)[1].lower()
    if ext not in (".md", ".txt"):
        print(f"{Fore.YELLOW}[!] Only .md and .txt files are supported.{Style.RESET_ALL}")
        return

    size = os.path.getsize(path)
    if size > IMPORT_MAX_BYTES:
        confirm = _ask(
            f"{Fore.YELLOW}[!] {size:,} bytes. Continue? y/N: {Style.RESET_ALL}"
        ).lower()
        if confirm != "y":
            return

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError as e:
        print(f"{Fore.RED}[!] Read failed: {e}{Style.RESET_ALL}")
        return

    print(f"{Fore.GREEN}[OK] Loaded {len(content):,} characters.{Style.RESET_ALL}")
    preview = content[:200].replace("\n", " ")
    suffix = "..." if len(content) > 200 else ""
    print(f"{Fore.CYAN}[Preview]:{Style.RESET_ALL} {preview}{suffix}\n")

    extra = _ask(
        f"{Fore.CYAN}[+] Question about this file (Enter to send file content only): {Style.RESET_ALL}",
        multiline=True,
    )

    full_input = f"{content}\n\n{extra}" if extra else content
    chat_once(full_input)

# ============ UNDO ============
def undo_last() -> None:
    global _last_assistant_text
    history = _sessions[_current_session]
    if len(history) < 2:
        print(f"{Fore.YELLOW}[~] No exchange to undo.{Style.RESET_ALL}")
        return

    removed = []
    if history[-1]["role"] == "assistant":
        removed.append(history.pop())
    if history and history[-1]["role"] == "user":
        removed.append(history.pop())

    _last_assistant_text = ""
    _session_last_text[_current_session] = ""
    _save_session_atomic(_current_session)  # persist immediately
    _discord_auto_clamp()
    print(
        f"{Fore.GREEN}[OK] Undid last exchange ({len(removed)} message(s)). "
        f"History now: {len(history)} messages.{Style.RESET_ALL}"
    )

# ============ TOKEN ESTIMATE ============
def estimate_tokens() -> None:
    all_text = _effective_system_prompt() + "".join(m["content"] for m in _sessions[_current_session])
    total_chars = len(all_text)
    ascii_chars = sum(1 for c in all_text if ord(c) < 128)
    non_ascii_chars = total_chars - ascii_chars
    est = ascii_chars / 4 + non_ascii_chars / 1.5

    print(f"\n{Fore.YELLOW}Token estimate ({_current_session}):{Style.RESET_ALL}")
    print(f"  Approximate tokens : {int(est):,}")
    print(f"  Total characters   : {total_chars:,}")
    print(f"  ASCII chars        : {ascii_chars:,}")
    print(f"  Non-ASCII chars    : {non_ascii_chars:,}")
    print(
        f"{Fore.YELLOW}  ※ Rough estimate. "
        f"Actual API sends only last {MAX_HISTORY} messages (plus system).{Style.RESET_ALL}\n"
    )

# ============ IMAGE GENERATION ============
def _ext_from_content_type(content_type: str) -> str:
    ct = content_type.lower()
    if "jpeg" in ct or "jpg" in ct:
        return ".jpg"
    if "webp" in ct:
        return ".webp"
    return ".png"

def generate_image(
    prompt: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    seed: Optional[int] = None,
    nologo: bool = True,
) -> Optional[str]:
    w = width if width is not None else _img_width
    h = height if height is not None else _img_height
    s = seed if seed is not None else (_img_seed if _img_seed is not None else random.randint(1, 999999))

    if w < 64 or h < 64 or w > 4096 or h > 4096:
        print(f"{Fore.RED}[!] Image size must be between 64 and 4096.{Style.RESET_ALL}")
        return None

    encoded_prompt = quote(prompt, safe="")
    url = (
        f"{IMAGE_BASE}/{encoded_prompt}"
        f"?width={w}&height={h}&seed={s}"
        f"&nologo={str(nologo).lower()}"
    )

    print(
        f"{Fore.CYAN}[~] Generating image... "
        f"prompt: {prompt[:50]}... | size: {w}x{h} | seed: {s}{Style.RESET_ALL}"
    )

    try:
        r = requests.get(url, timeout=60)
        if r.status_code != 200:
            print(
                f"{Fore.RED}[!] Failed to generate image: HTTP {r.status_code}{Style.RESET_ALL}"
            )
            return None

        content_type = r.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            print(
                f"{Fore.RED}[!] Unexpected Content-Type: {content_type} "
                f"(expected image/*){Style.RESET_ALL}"
            )
            return None

        ext = _ext_from_content_type(content_type)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_prompt = "".join(c if c.isalnum() else "_" for c in prompt[:30])
        filename = os.path.join(IMAGE_DIR, f"img_{ts}_{safe_prompt}{ext}")
        with open(filename, "wb") as f:
            f.write(r.content)
        print(f"{Fore.GREEN}[OK] Image saved: {filename}{Style.RESET_ALL}")
        return filename
    except Exception as e:
        print(f"{Fore.RED}[!] Image generation error: {e}{Style.RESET_ALL}")
        return None

def image_mode() -> None:
    global _img_width, _img_height, _img_seed

    print(f"\n{Fore.YELLOW}Image Generation Mode{Style.RESET_ALL}")
    print(
        f"  Current: {_img_width}x{_img_height}, "
        f"seed={_img_seed if _img_seed is not None else 'random'}\n"
    )
    print("  Type your prompt, 'exit' to leave, or:")
    print("  [size] — change width/height")
    print("  [seed] — set/clear a fixed seed\n")

    while True:
        prompt = _ask(f"{Fore.CYAN}[image] {username}: {Style.RESET_ALL}")
        if not prompt:
            continue

        cmd = prompt.lower()
        if cmd in ("exit", "quit", "back"):
            print(f"{Fore.YELLOW}[~] Returning to chat mode.{Style.RESET_ALL}\n")
            break
        elif cmd in ("[size]", "size"):
            w_input = _ask(
                f"{Fore.CYAN}[+] width (current: {_img_width}): {Style.RESET_ALL}"
            )
            h_input = _ask(
                f"{Fore.CYAN}[+] height (current: {_img_height}): {Style.RESET_ALL}"
            )
            # Validate in temporary variables before mutating state
            try:
                w_tmp = int(w_input) if w_input else _img_width
                h_tmp = int(h_input) if h_input else _img_height
            except ValueError:
                print(f"{Fore.RED}[!] Width and height must be integers.{Style.RESET_ALL}")
                continue
            if w_tmp < 64 or h_tmp < 64 or w_tmp > 4096 or h_tmp > 4096:
                print(
                    f"{Fore.RED}[!] Size must be between 64 and 4096. "
                    f"Tried: {w_tmp}x{h_tmp}{Style.RESET_ALL}"
                )
                continue
            _img_width, _img_height = w_tmp, h_tmp
            print(f"{Fore.GREEN}[OK] Size set to {_img_width}x{_img_height}{Style.RESET_ALL}")
            continue
        elif cmd in ("[seed]", "seed"):
            s_input = _ask(
                f"{Fore.CYAN}[+] seed (current: "
                f"{_img_seed if _img_seed is not None else 'random'}, 'none'=random): {Style.RESET_ALL}"
            )
            if s_input.lower() == "none":
                _img_seed = None
                print(f"{Fore.GREEN}[OK] Seed set to random{Style.RESET_ALL}")
            elif s_input.isdigit():
                _img_seed = int(s_input)
                print(f"{Fore.GREEN}[OK] Seed fixed to {_img_seed}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}[~] Kept current seed.{Style.RESET_ALL}")
            continue

        generate_image(prompt)

# ============ MULTILINE INPUT ============
def read_multiline() -> str:
    print(
        f"{Fore.CYAN}[+] Multiline mode. "
        f"Type [end] on its own line to finish:{Style.RESET_ALL}"
    )
    lines, _status, _literal = read_block(allow_reset=False)
    return "\n".join(lines)

# ============ SEARCH ============
def search_history() -> None:
    query = _ask(f"{Fore.CYAN}[+] Search keyword: {Style.RESET_ALL}").lower()
    if not query:
        print(f"{Fore.YELLOW}[~] Empty query.{Style.RESET_ALL}")
        return

    matches = []
    for i, msg in enumerate(_sessions[_current_session]):
        if query in msg["content"].lower():
            role_label = _msg_name(msg) if msg["role"] == "user" else "AI"
            snippet = msg["content"][:120]
            suffix = "..." if len(msg["content"]) > 120 else ""
            matches.append((i, msg["role"], role_label, snippet + suffix))

    if not matches:
        print(f"{Fore.YELLOW}[~] No matches found.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.GREEN}{len(matches)} match(es):{Style.RESET_ALL}")
    for idx, role, role_label, snippet in matches:
        color = Fore.GREEN if role == "user" else Fore.MAGENTA
        print(f"  {color}[{idx}]{role_label}:{Style.RESET_ALL} {snippet}")
    print()

# ============ LEGACY SESSION SAVE/LOAD ============
def save_session() -> None:
    raw = _ask(
        f"{Fore.CYAN}[+] Save current session as (Enter='{_current_session}'): {Style.RESET_ALL}"
    )
    name = _sanitize_session_name(raw) if raw else _current_session
    fname = _safe_session_name(name)
    path = os.path.join(SESSION_DIR, fname)

    if name != _current_session and name in _sessions:
        confirm = _ask(
            f"{Fore.YELLOW}[!] '{name}' already exists. Overwrite? y/N: {Style.RESET_ALL}"
        ).lower()
        if confirm != "y":
            print(f"{Fore.YELLOW}[~] Cancelled.{Style.RESET_ALL}")
            return

    # Assign first: _save_session_atomic() reads _sessions[name]
    if name != _current_session:
        _sessions[name] = list(_sessions[_current_session])
        if _session_prompts.get(_current_session):
            _session_prompts[name] = _session_prompts[_current_session]
        else:
            _session_prompts.pop(name, None)
        if _session_plugins.get(_current_session):
            _session_plugins[name] = [dict(e) for e in _session_plugins[_current_session]]
        else:
            _session_plugins.pop(name, None)
    _save_session_atomic(name)  # atomic write for crash safety
    print(f"{Fore.GREEN}[OK] Session saved: {path}{Style.RESET_ALL}")

def load_session() -> None:
    global _last_assistant_text, _current_session
    global current_model, _temperature, _max_tokens

    files = sorted(f for f in os.listdir(SESSION_DIR) if f.endswith(".json"))
    if not files:
        print(f"{Fore.YELLOW}[!] No saved sessions found.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.YELLOW}Saved sessions:{Style.RESET_ALL}")
    for i, f in enumerate(files, 1):
        print(f"  {i}. {f}")

    choice = _ask(
        f"\n{Fore.CYAN}[+] Select session (number or name): {Style.RESET_ALL}"
    )
    if not choice:
        return
    if choice.isdigit():
        idx = int(choice) - 1
        if not (0 <= idx < len(files)):
            print(f"{Fore.RED}[!] Invalid number.{Style.RESET_ALL}")
            return
        fname = files[idx]
    else:
        fname = _safe_session_name(choice)

    path = os.path.join(SESSION_DIR, fname)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"{Fore.RED}[!] Load failed: {e}{Style.RESET_ALL}")
        return

    history = data.get("history", []) if isinstance(data, dict) else None
    if not _valid_history(history):
        print(f"{Fore.RED}[!] Load failed: invalid session format.{Style.RESET_ALL}")
        return

    _stamp_names(history, data.get("username"))
    name = fname[:-5]
    if name != _current_session:
        _discord_auto_leave(_current_session)
    _sessions[name] = history
    _current_session = name
    _discord_auto_clamp(name)
    _last_assistant_text = _session_last_text.get(name, "")

    model = data.get("model")
    if isinstance(model, str) and model:
        current_model = model
    # The global system prompt is a setting, not session data: [load] leaves it alone
    # (like the user name since v2.8.12). Only the session's own layer is restored.
    sp = data.get("session_prompt")
    if isinstance(sp, str) and sp.strip():
        _session_prompts[name] = sp
    else:
        _session_prompts.pop(name, None)
    pl = _clean_plugin_entries(data.get("plugins"))
    if pl:
        _session_plugins[name] = pl
    else:
        _session_plugins.pop(name, None)
    temp = data.get("temperature")
    if isinstance(temp, (int, float)):
        _temperature = float(temp)
    mt = data.get("max_tokens")
    if mt is None:
        _max_tokens = None
    elif isinstance(mt, int) and not isinstance(mt, bool):
        _max_tokens = mt

    print(
        f"{Fore.GREEN}[OK] Loaded session: {fname} "
        f"({len(history)} messages){Style.RESET_ALL}"
    )

def clear_history() -> None:
    global _last_assistant_text
    _sessions[_current_session] = []
    _last_assistant_text = ""
    _session_last_text[_current_session] = ""
    _save_session_atomic(_current_session)  # persist immediately
    _discord_auto_clamp()
    print(f"{Fore.GREEN}[OK] Conversation history cleared.{Style.RESET_ALL}")

# ============ HELP ============
HELP_TEXT = r"""
NekoChat Commands:

  [service]     — Switch service (PollinationsAI, NVIDIA, Mistral, Cloudflare ...) and pick its model
  [model]       — Select a model of the current service
  [key]         — Set or remove API keys for services that need one
  [system]      — Set the GLOBAL system prompt (shared by every session)
  [system session] — Set a prompt for the current session only (added after the global one)
  [discord]     — Post chosen exchanges to Discord webhooks: [discord -1], [discord 2:5 bare to NAME], add webhook, rm NAME
                  [discord auto on -3:] posts by itself every 3 new exchanges (-1: = every reply); auto off / flush
  [plugin]      — Reusable prompts: [plugin] list, show NAME, on NAME [global], off NAME, new NAME
  [name]        — Change your display name (past messages keep the name they were sent with)
  [config]      — Set temperature / max_tokens
  [stream]      — Toggle streaming / batch display mode (batch recommended on web terminals)
  [guard]       — Toggle turn guard (default OFF). Stops models that spontaneously
                  generate fake User:/Assistant: turns. Requires 2+ role labels
                  outside code blocks before cutting (reduces false positives).
  [image]       — Enter image generation mode
  [long]        — Enter multiline input mode (type [end] to finish)
  [import]      — Import a .md/.txt file and send as user message
  [search]      — Search conversation history
  [render]      — Re-display last response with Markdown formatting
  [savecode]    — Extract and save code blocks from last response
  [export]      — Export conversation to Markdown file
  [export list] — List Q&A exchanges with indexes (0 = oldest, -1 = latest)
  [export -1]   — Export exchange(s) by index or slice (stop excluded):
                  [export -3:]  [export 2:5]  [export ::-1]
                  flags: rev (reverse order) / bare (answers only) / full (keep long questions)
  [undo]        — Remove the last user-assistant exchange
  [token]       — Show rough token estimate for current context

  --- Sessions ---
  [sessions]    — List all sessions
  [switch]      — Switch to another session
  [new]         — Create a new empty session
  [rename]      — Rename the current session
  [delete]      — Delete a session (not current)
  [save]        — Save current session (legacy)
  [load]        — Load a session from file (legacy)

  [clear]       — Clear current session history
  [history]     — Show current session history
  [help]        — Show this help
  [exit]        — Quit NekoChat

Services and keys: API keys live in keys.json ([key]); custom services go in the
"providers" block of config.json (see README).

Just type normally to chat with the AI!
"""

# ============ MAIN ============
def main() -> None:
    global username

    ensure_dirs()

    cfg = load_config()
    apply_config(cfg)

    clear()
    print(Fore.MAGENTA + BANNER + Style.RESET_ALL)
    _flush_config_warnings()

    # Load sessions AFTER clearing screen so broken-JSON warnings are visible
    _auto_load_all_sessions()

    if not cfg.get("username"):
        default_name = os.environ.get("USER", os.environ.get("USERNAME", "User"))
        default_name = _validate_username(default_name)[0] or "User"
        while True:
            name_input = _ask(
                f"{Fore.CYAN}[+] Your name (Enter for '{default_name}'): {Style.RESET_ALL}"
            )
            if not name_input:
                username = default_name
                break
            name, err = _validate_username(name_input)
            if err or name is None:
                print(f"{Fore.RED}[!] {err}{Style.RESET_ALL}")
                continue
            username = name
            break
        save_config(build_config())

    print(f"{Fore.GREEN}[OK] Welcome, {username}! Type [help] for commands.{Style.RESET_ALL}")
    print(
        f"{Fore.GREEN}[OK] Current session: '{_current_session}' "
        f"({len(_sessions[_current_session])} messages){Style.RESET_ALL}\n"
    )

    try:
        while True:
            try:
                # Defensive flush before prompt: ensure no stray output
                # leaks into input() on browser-based terminals (xterm.js, etc.)
                sys.stdout.flush()
                prompt_str = (
                    f"{Fore.GREEN}{username}{Style.RESET_ALL}"
                    f"{Fore.CYAN}[{_current_session}]{Style.RESET_ALL}{_discord_auto_marker()} : "
                )
                user_input, is_paste = _read_input(_rl_safe(prompt_str))
                user_input = user_input.strip()
                if not user_input:
                    continue

                # Pasted multi-line text is always treated as a chat message,
                # never as commands. This prevents pasted text containing
                # bracketed words like [exit] from being interpreted as commands.
                if is_paste:
                    chat_once(user_input)
                    continue

                cmd = user_input.lower()

                m_exp = _EXPORT_CMD_RE.match(user_input)
                if m_exp:
                    export_exchanges(m_exp.group(1))
                    continue
                norm = " ".join(cmd.split())
                if norm == "[system session]":
                    set_session_prompt()
                    continue
                if norm == "[discord]" or norm.startswith("[discord "):
                    discord_command(norm)
                    continue
                if norm == "[plugin]" or norm == "[plugins]" or norm.startswith("[plugin "):
                    plugin_command("[plugin]" if norm == "[plugins]" else norm)
                    continue
                if norm.startswith("[system "):
                    print(f"{Fore.YELLOW}[~] Usage: [system] (global prompt) or [system session] "
                          f"(this session only).{Style.RESET_ALL}")
                    continue
                if cmd.startswith("[name "):
                    print(f"{Fore.YELLOW}[~] [name] takes no arguments; just type [name].{Style.RESET_ALL}")
                    continue
                if cmd.startswith("[export "):
                    print(f"{Fore.RED}[!] Malformed export command.{Style.RESET_ALL}\n{EXPORT_USAGE}")
                    continue

                if cmd in ("[exit]", "exit"):
                    print(f"{Fore.YELLOW}Bye bye, {username}!{Style.RESET_ALL}")
                    break
                elif cmd in ("[help]", "help"):
                    print(HELP_TEXT)
                elif cmd in ("[model]", "model"):
                    select_model()
                elif cmd == "[service]":
                    select_service()
                elif cmd == "[key]":
                    set_key()
                elif cmd in ("[system]", "system"):
                    set_system_prompt()
                elif cmd == "[name]":
                    set_username()
                elif cmd in ("[config]", "config"):
                    edit_config()
                elif cmd in ("[stream]", "stream"):
                    toggle_stream()
                elif cmd in ("[guard]", "guard"):
                    toggle_turn_guard()
                elif cmd in ("[image]", "image"):
                    image_mode()
                elif cmd in ("[long]", "long"):
                    long_text = read_multiline()
                    if long_text.strip():
                        preview = long_text[:300]
                        suffix = "..." if len(long_text) > 300 else ""
                        print(f"\n{Fore.GREEN}[Input preview]:{Style.RESET_ALL}")
                        print(f"{preview}{suffix}\n")
                        chat_once(long_text)
                elif cmd in ("[import]", "import"):
                    import_file()
                elif cmd in ("[search]", "search"):
                    search_history()
                elif cmd in ("[render]", "render"):
                    render_last()
                elif cmd in ("[savecode]", "savecode"):
                    save_code()
                elif cmd in ("[export]", "export"):
                    export_session()
                elif cmd in ("[undo]", "undo"):
                    undo_last()
                elif cmd in ("[token]", "token"):
                    estimate_tokens()
                elif cmd in ("[sessions]", "sessions"):
                    list_sessions()
                elif cmd in ("[switch]", "switch"):
                    switch_session()
                elif cmd in ("[new]", "new"):
                    new_session()
                elif cmd in ("[rename]", "rename"):
                    rename_session()
                elif cmd in ("[delete]", "delete"):
                    delete_session()
                elif cmd in ("[save]", "save"):
                    save_session()
                elif cmd in ("[load]", "load"):
                    load_session()
                elif cmd in ("[clear]", "clear"):
                    clear_history()
                elif cmd in ("[history]", "history"):
                    print(
                        f"\n{Fore.YELLOW}Conversation History [{_current_session}] "
                        f"({len(_sessions[_current_session])} messages):{Style.RESET_ALL}"
                    )
                    for msg in _sessions[_current_session]:
                        role_color = Fore.GREEN if msg["role"] == "user" else Fore.MAGENTA
                        role_label = _msg_name(msg) if msg["role"] == "user" else "AI"
                        truncated = msg["content"][:100]
                        suffix = "..." if len(msg["content"]) > 100 else ""
                        print(f"  {role_color}{role_label}:{Style.RESET_ALL} {truncated}{suffix}")
                    print()
                else:
                    chat_once(user_input)

            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}[!] Use [exit] to quit.{Style.RESET_ALL}")
            except EOFError:
                break
    finally:
        try:
            _discord_auto_exit()
        except Exception as e:
            print(f"{Fore.YELLOW}[~] discord auto mode: {type(e).__name__} while closing.{Style.RESET_ALL}")
        _auto_save_all_sessions()
        print(f"{Fore.GREEN}[OK] All sessions saved.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
