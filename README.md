# aisk

A fast, minimal CLI to ask questions to any LLM from your terminal.

```bash
aisk ge3flash "explain monads in Haskell"
```

## Features

- **Streaming responses** — tokens appear as they arrive
- **Reasoning support** — shows thinking tokens for models like o4-mini, DeepSeek-R1
- **Model aliases** — short names for long model IDs (`ge3flash` → `google/gemini-2.5-flash-preview`)
- **Pass-through models** — use any model directly: `aisk perplexity/sonar "query"`
- **Quiet mode** — `-q` strips all decoration, perfect for piping
- **Stdin support** — `echo "explain this" | aisk cls46`
- **OpenAI-compatible** — works with OpenRouter (default), or any OpenAI-compatible endpoint
- **Zero config** — just set your API key and go

## Install

```bash
# From GitHub
uv tool install git+ssh://git@github.com/Ymx1ZQ/aisk.git

# From local clone
git clone git@github.com:Ymx1ZQ/aisk.git
cd aisk
uv tool install .
```

## Setup

```bash
# Interactive wizard — creates ~/.aisk/, asks for endpoint and API key
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
ge3flash = "google/gemini-2.5-flash-preview"
cls46 = "anthropic/claude-sonnet-4"
# ... add your own
```

## Usage

```bash
# Ask a question (verbose mode, default)
aisk ge3flash "what is the CAP theorem?"

# Quiet mode — only the LLM response, no decoration
aisk -q cls46 "translate to English: buongiorno"

# Pipe from stdin
echo "summarize this" | aisk gpt5mini

# Use a full model name directly (no alias needed)
aisk perplexity/sonar "latest news on Rust 2026"

# List available aliases
aisk models

# Show version
aisk --version
```

### Verbose output (default)

```
──────────────────────────────────────────────────────────────────────────────────────────────────
 Model: google/gemini-2.5-flash-preview | User: what is the CAP theorem?
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

## Shell Completions

Tab-completion for model aliases and subcommands.

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
