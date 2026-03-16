# aisk — Development Plan

## M1: Project scaffolding ✅

- [x] `pyproject.toml` with uv-compatible build (hatchling), entry point `aisk`, Python >=3.10
- [x] `src/aisk/__init__.py` with `__version__`
- [x] `src/aisk/cli.py` — argparse-based CLI skeleton
- [x] `.gitignore` for Python
- [x] Minimal `README.md` (already written)

## M2: Configuration system (`~/.aisk/`) ✅

- [x] `src/aisk/config.py` — loads `~/.aisk/conf.toml` and `~/.aisk/.env`
  - Uses `tomllib` (3.11+) with `tomli` fallback
  - Uses `python-dotenv` to load `.env` into env vars
  - Provides typed config dataclass: `endpoint`, `api_key`, `aliases`
- [x] Default config template embedded in code (used by `aisk init`)
- [x] `aisk init` subcommand — creates `~/.aisk/` with `conf.toml` and `.env` templates
  - If files already exist, skip with message (never overwrite)

### Default `conf.toml` structure

```toml
[api]
endpoint = "https://openrouter.ai/api/v1/chat/completions"

[aliases]
# Google Gemini
ge31pro = "google/gemini-3.1-pro-preview"
ge3flash = "google/gemini-2.5-flash-preview"
ge25flash = "google/gemini-2.5-flash-preview"
ge25lite = "google/gemini-2.5-flash-lite-preview"

# OpenAI
gpt52 = "openai/gpt-5.2"
gpt51 = "openai/gpt-5.1"
gpt5 = "openai/gpt-5"
gpt5mini = "openai/gpt-5-mini"
gpt5nano = "openai/gpt-5-nano"
o4m = "openai/o4-mini"

# Anthropic
clo46 = "anthropic/claude-opus-4"
cls46 = "anthropic/claude-sonnet-4"

# DeepSeek
dsv32 = "deepseek/deepseek-chat-v3-0324"
dsr1 = "deepseek/deepseek-r1"

# Qwen
qwen35p = "qwen/qwen3.5-coder-plus"
qwen35 = "qwen/qwen3.5-coder"

# Other
m25 = "minimax/minimax-m1-80k"
glm5 = "zhipu/glm-5-plus"
k25 = "moonshotai/kimi-k2.5"
mistral = "mistralai/mistral-large-2411"
l4scout = "meta-llama/llama-4-scout"
l4mav = "meta-llama/llama-4-maverick"
```

### Default `.env` structure

```
AISK_API_KEY=
```

## M3: Model alias resolution ✅

- [x] `src/aisk/aliases.py` — resolves alias → full model name
  - Lookup in `conf.toml` `[aliases]` section
  - If no match, pass through as-is (allows `aisk perplexity/sonar "query"`)
  - No prefix stripping needed — user writes what the API expects

## M4: Streaming HTTP client ✅

- [x] `src/aisk/client.py` — streaming request to OpenAI-compatible endpoint
  - Uses `httpx` with streaming SSE parsing
  - Sends `Authorization: Bearer <token>` header
  - Payload: `model`, `messages`, `stream: true`, `stream_options: {include_usage: true}`
  - Yields typed events: `ReasoningChunk`, `ContentChunk`, `UsageInfo`, `ErrorInfo`
  - Handles error JSON responses (non-stream)

## M5: Output formatting ✅

- [x] `src/aisk/output.py` — two formatters
  - **Verbose (default):** replicates current `a+ask` output
    - Header with model + user message
    - `THINKING` section (dim italic) for reasoning tokens
    - `ANSWER` section for content
    - Footer with token counts + cost
  - **Quiet (`-q`):** raw LLM text only
    - No colors, no ANSI escapes
    - No headers/footers/decorations
    - Only content tokens (skip reasoning)
    - Suitable for piping (`aisk -q model "msg" | pbcopy`)

## M6: CLI wiring ✅

- [x] Wire everything together in `cli.py`
  - `aisk <model> <message>` — main flow (verbose)
  - `aisk -q <model> <message>` — quiet mode
  - `aisk <model>` (no message) — read from stdin
  - `aisk init` — config setup
  - `aisk models` — list aliases from config
  - `aisk --version` — print version
- [x] Stdin support: if no message arg and stdin is not a TTY, read from stdin
- [x] Exit codes: 0 success, 1 API/config error, 2 usage error

## M7: Packaging and distribution ✅

- [x] Ensure `uv tool install .` works from local clone
- [x] Ensure `uv tool install git+ssh://git@github.com/Ymx1ZQ/aisk.git` works
- [ ] Add bash/zsh completion script (optional, stretch — deferred)
- [x] Final README polish with install instructions and examples
- [x] MIT LICENSE file added
