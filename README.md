# aisk

A fast, minimal CLI to ask questions to any LLM from your terminal.

```bash
aisk gel "explain monads in Haskell"
```

## Features

- **Streaming responses** — tokens appear as they arrive
- **Default model** — `aisk` with no args starts chat with the default model (`dsf`)
- **Interactive chat** — multi-turn REPL with keyboard shortcuts: `Ctrl+S` search, `Ctrl+O` model selector, `Ctrl+G` help
- **Web search** — toggle with `Ctrl+S` in chat (off by default; cycles off → auto → native → off)
- **Resume** — `aisk --resume` continues your last conversation (per-terminal, no clobber across windows)
- **Prompt caching** — on by default; cuts cost on long chats/resumes (`AISK_PROMPT_CACHE=0` to disable)
- **Reasoning support** — shows thinking tokens for models like GPT-5.5, DeepSeek V4
- **Model aliases** — short names for long model IDs (`gel` → `google/gemini-3.1-flash-lite-preview`)
- **Pass-through models** — use any model directly: `aisk perplexity/sonar "query"`
- **Quiet mode** — `-q` strips all decoration, perfect for piping
- **Buffered mode** — `-S` prints the full response at the end instead of streaming
- **Stdin support** — `echo "explain this" | aisk cls`
- **Any OpenAI-compatible endpoint** — OpenRouter by default, override with one setting
- **Zero config** — just set your API key and go

## Install

### Linux

```bash
# Installs uv if needed, installs/upgrades aisk, runs setup, installs completions.
curl -fsSL https://raw.githubusercontent.com/GuidanceStudio/aisk/main/install.sh | bash
```

### macOS

```bash
# Installs uv if needed, installs/upgrades aisk, runs setup, installs completions.
curl -fsSL https://raw.githubusercontent.com/GuidanceStudio/aisk/main/install.sh | bash
```

### Windows PowerShell

```powershell
# Installs uv if needed, installs/upgrades aisk, runs setup, installs completions.
powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/GuidanceStudio/aisk/main/install.ps1 | iex"
```

The installers are idempotent: rerunning them upgrades an existing `aisk`
install. When run from a local clone, they install that checkout; when piped from
GitHub, they install `git+https://github.com/GuidanceStudio/aisk.git`.

After installation, open a new terminal or run the shell-specific reload command
shown by the installer, then verify:

```bash
aisk --version
```

```powershell
aisk --version
```

### Manual install

From GitHub, on any platform with `uv`:

```bash
uv tool install git+https://github.com/GuidanceStudio/aisk.git
aisk init
aisk completions install
```

From a local clone on Linux/macOS:

```bash
git clone https://github.com/GuidanceStudio/aisk.git
cd aisk
./install.sh
```

From a local clone on Windows:

```powershell
git clone https://github.com/GuidanceStudio/aisk.git
cd aisk
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

For a minimal local developer install without setup or completions:

```bash
uv tool install .
```

### Windows status

Windows support includes install, setup, `models`, one-shot prompts, `--resume`,
and interactive chat. The chat prompt uses `prompt_toolkit` for cross-platform
multiline input, history, `Ctrl+S` search toggle, `Ctrl+O` model selector, and
`Ctrl+G` help.

## Setup

No explicit setup needed. On first run, `aisk` detects the missing configuration and launches the setup wizard automatically:

```bash
aisk gel "hello world"
# → First run detected — launching setup wizard...
# → Asks for endpoint and API key, then runs your query
```

To reconfigure later:

```bash
aisk init
```

The wizard will:
1. Ask for the API endpoint (default: OpenRouter, press Enter to accept)
2. Ask for your API key
3. If config already exists, ask whether to overwrite

### Refreshing the model list

The default aliases evolve as new models ship. Upgrading `aisk` updates the
*code* defaults but leaves your existing `~/.aisk/conf.toml` untouched, so older
aliases linger. Run `sync` to realign the `[aliases]` section to the current
defaults — your endpoint, shortcuts and any custom aliases are kept:

```bash
aisk sync
# + added:   clo, gptmini, …
# - removed: clo47, gpt5mini, o4m, …
# = kept custom: myalias

# then refresh tab-completion in the current shell:
eval "$(aisk completions refresh)"
```

### Configuration

**`~/.aisk/.env`** — API key (loaded automatically):

```
AISK_API_KEY=sk-or-...
```

**`~/.aisk/conf.toml`** — endpoint and model aliases:

```toml
[api]
endpoint = "https://openrouter.ai/api/v1/chat/completions"

[defaults]
model = "dsf"

[aliases]
gel = "google/gemini-3.1-flash-lite-preview"
cls = "anthropic/claude-sonnet-4.6"
# ... add your own
```

### Use any OpenAI-compatible provider

OpenRouter is only the default. Point `aisk` at any OpenAI-compatible
`/chat/completions` endpoint (OpenAI, Groq, a local llama.cpp/vLLM server, …) by
overriding a single setting — there are no per-provider profiles.

Two ways to set the endpoint:

```toml
# 1. Persist it in ~/.aisk/conf.toml
[api]
endpoint = "https://api.openai.com/v1/chat/completions"
```

```bash
# 2. Override on the fly with AISK_ENDPOINT (wins over conf.toml)
export AISK_ENDPOINT="https://api.groq.com/openai/v1/chat/completions"

# …including at install time:
curl -fsSL https://raw.githubusercontent.com/GuidanceStudio/aisk/main/install.sh \
  | AISK_ENDPOINT="https://api.openai.com/v1/chat/completions" bash
```

`AISK_API_KEY` is the key for whatever endpoint you choose. Note that the default
aliases use OpenRouter slugs (`anthropic/claude-sonnet-4.6`); on a direct provider
the model is named natively (e.g. `gpt-5.5`), so use the pass-through form
(`aisk gpt-5.5 "hi"`) or define your own aliases.

## Usage

```bash
# Start chat with the default model (dsf — DeepSeek V4 Flash)
aisk

# Ask a question (verbose mode, default)
aisk gel "what is the CAP theorem?"

# Interactive chat with a specific model.
# ←/→ move in the prompt; ↑/↓ move within multi-line input or recall previous prompts.
# Ctrl-J inserts a newline (Ctrl+Enter/Shift+Enter also work when supported).
# Ctrl+S toggles web search (off → auto → native → off).
# Ctrl+O opens the fuzzy model selector (arrow keys to navigate, type to filter, Enter to select).
# Ctrl+G shows help. Ctrl-C stops the current reply (or exits at the prompt); Ctrl-D exits.
# Each reply shows its cost and the running conversation total.
# A mistyped model is caught up front (e.g. `aisk dsv4` → "did you mean dsf?").
aisk cls

# Resume the last conversation — continue in chat, or one-shot with a message
aisk dsf "explain monads"
aisk --resume                  # reopens it as a chat, history preloaded
aisk --resume "give an example"  # one-shot follow-up

# No quotes needed — all words after the model are joined automatically
aisk gel what is the CAP theorem

# Use quotes if your message contains shell special characters: () ! > | &
aisk glm "what is f(x) = x^2 + (x-1)?"

# Use single quotes for backticks
aisk gel 'explain the `ls -la` command'

# Quiet mode — only the LLM response, no decoration
aisk -q cls "translate to English: buongiorno"

# Buffered mode — print full response at the end (no progressive streaming)
aisk -S gel "explain monads"

# Combine: quiet + buffered — ideal for scripts
aisk -q -S cls "translate to English: buongiorno" | wc -w

# Pipe from stdin
echo "summarize this" | aisk gptmini

# Search with Perplexity
aisk s what is the mass of the sun
aisk sps "latest news on Rust 2026"

# Use a full model name directly (no alias needed)
aisk perplexity/sonar "latest news on Rust 2026"

# Show help
aisk help

# List available aliases (grouped by provider)
aisk models

# Show version
aisk --version
```

### Verbose output (default)

```
──────────────────────────────────────────────────────────────────────────────────────────────────
 Model: google/gemini-3.1-flash-lite-preview | User: what is the CAP theorem?
──────────────────────────────────────────────────────────────────────────────────────────────────
► ANSWER
The CAP theorem states that a distributed system can only guarantee
two of three properties simultaneously: Consistency, Availability,
and Partition tolerance...


──────────────────────────────────────────────────────────────────────────────────────────────────
Tokens: In 12 | Out 234 (Reasoning: 0) | Cost: $0.000456
──────────────────────────────────────────────────────────────────────────────────────────────────
```

### Quiet output (`-q`)

```
The CAP theorem states that a distributed system can only guarantee
two of three properties simultaneously: Consistency, Availability,
and Partition tolerance...
```

## Shell Shortcuts

Define short shell functions that call `aisk` with a specific model. Configure them in `~/.aisk/conf.toml`:

```toml
[shortcuts]
ds = "dsf"
news = "sps"
# gp = "gptpro"
# cl = "cls"
# ge = "gef"
```

Each shortcut becomes a shell function (e.g. `ds "question"` → `aisk dsf "question"`), loaded automatically by the completion script for your shell.

```bash
# See generated functions
aisk shortcuts

# Use directly
ds what is the CAP theorem
news latest developments on Rust 2026
```

## Shell Completions

Tab-completion for model aliases and subcommands. Installed automatically by
`install.sh` on macOS/Linux and `install.ps1` on Windows.

```bash
# Install manually (appends to ~/.bashrc, ~/.zshrc, or PowerShell $PROFILE)
aisk completions install

# Refresh after changing aliases/shortcuts in conf.toml
eval "$(aisk completions refresh)"
```

Or add manually to your shell rc file:

```bash
# Bash — add to ~/.bashrc
eval "$(aisk completions bash)"

# Zsh — add to ~/.zshrc
eval "$(aisk completions zsh)"
```

```powershell
# PowerShell — add to $PROFILE
aisk completions powershell | Invoke-Expression
```

## Dependencies

Minimal by design:

- `httpx` — streaming HTTP
- `prompt-toolkit` — cross-platform interactive chat prompt and shortcuts
- `python-dotenv` — loads `.env`
- `tomli` — TOML parser (Python <3.11 only; 3.11+ uses stdlib `tomllib`)

## Development

The CI runs the pytest suite on Ubuntu and Windows with `uv`:

```bash
uv run pytest -q
```

On Windows, the workflow also runs a focused PowerShell installer smoke test:

```powershell
uv run pytest -q tests/test_install.py
```

## License

MIT
