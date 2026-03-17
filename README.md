# aisk

A fast, minimal CLI to ask questions to any LLM from your terminal.

```bash
aisk ge31lite "explain monads in Haskell"
```

## Features

- **Streaming responses** — tokens appear as they arrive
- **Reasoning support** — shows thinking tokens for models like o4-mini, DeepSeek-R1
- **Model aliases** — short names for long model IDs (`ge31lite` → `google/gemini-3.1-flash-lite-preview`)
- **Pass-through models** — use any model directly: `aisk perplexity/sonar "query"`
- **Quiet mode** — `-q` strips all decoration, perfect for piping
- **Stdin support** — `echo "explain this" | aisk cls46`
- **OpenAI-compatible** — works with OpenRouter (default), or any OpenAI-compatible endpoint
- **Zero config** — just set your API key and go

## Install

```bash
# One-liner (installs uv if needed, upgrades if already installed)
curl -fsSL https://raw.githubusercontent.com/Ymx1ZQ/aisk/main/install.sh | bash
```

Or manually:

```bash
# From GitHub
uv tool install git+ssh://git@github.com/Ymx1ZQ/aisk.git

# From local clone
git clone git@github.com:Ymx1ZQ/aisk.git
cd aisk
uv tool install .
```

## Setup

No explicit setup needed. On first run, `aisk` detects the missing configuration and launches the setup wizard automatically:

```bash
aisk ge31lite "hello world"
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

### Configuration

**`~/.aisk/.env`** — API key (loaded automatically):

```
AISK_API_KEY=sk-or-...
```

**`~/.aisk/conf.toml`** — endpoint and model aliases:

```toml
[api]
endpoint = "https://openrouter.ai/api/v1/chat/completions"

[aliases]
ge31lite = "google/gemini-3.1-flash-lite-preview"
cls46 = "anthropic/claude-sonnet-4.6"
# ... add your own
```

## Usage

```bash
# Ask a question (verbose mode, default)
aisk ge31lite "what is the CAP theorem?"

# No quotes needed — all words after the model are joined automatically
aisk ge31lite what is the CAP theorem

# Use quotes if your message contains shell special characters: () ! > | &
aisk glm5 "what is f(x) = x^2 + (x-1)?"

# Use single quotes for backticks
aisk ge31lite 'explain the `ls -la` command'

# Quiet mode — only the LLM response, no decoration
aisk -q cls46 "translate to English: buongiorno"

# Pipe from stdin
echo "summarize this" | aisk gpt5mini

# Search with Perplexity
aisk s what is the mass of the sun
aisk sps "latest news on Rust 2026"

# Use a full model name directly (no alias needed)
aisk perplexity/sonar "latest news on Rust 2026"

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
ds = "dsv32"
sps = "sps"
# gpt = "gpt54"
# cl = "cls46"
# ge = "ge25flash"
```

Each shortcut becomes a shell function (e.g. `ds "question"` → `aisk dsv32 "question"`), loaded automatically via `eval "$(aisk completions bash)"`.

```bash
# See generated functions
aisk shortcuts

# Use directly
ds what is the CAP theorem
sps latest news on Rust 2026
```

## Shell Completions

Tab-completion for model aliases and subcommands. Installed automatically by `install.sh`.

```bash
# Install manually (appends to ~/.bashrc or ~/.zshrc)
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

## Dependencies

Minimal by design:

- `httpx` — streaming HTTP
- `python-dotenv` — loads `.env`
- `tomli` — TOML parser (Python <3.11 only; 3.11+ uses stdlib `tomllib`)

## License

MIT
