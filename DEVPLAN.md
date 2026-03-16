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
- [x] Add bash/zsh completion script (implemented in M10)
- [x] Final README polish with install instructions and examples
- [x] MIT LICENSE file added

## M8: Interactive `aisk init` ✅

`aisk init` diventa un wizard interattivo che guida l'utente nella configurazione.

### Flusso

1. Crea `~/.aisk/` se non esiste
2. **Endpoint**
   - Se `conf.toml` non esiste → lo crea con i default, mostra l'endpoint default e chiede conferma (`Enter` per accettare, oppure inserire un URL custom)
   - Se `conf.toml` esiste già → chiede se si vuole sovrascrivere (`conf.toml already exists. Overwrite? [y/N]`)
3. **API key**
   - Se `.env` non esiste **oppure** esiste già → chiede il token con prompt interattivo
   - Se `.env` esiste, mostra il valore attuale mascherato (`Current key: sk-or-...****`) e chiede se sovrascrivere (`Overwrite? [y/N]`)
   - Se `.env` non esiste → chiede direttamente il token
   - Usa `input()` (non `getpass`) per compatibilità con paste da clipboard
4. **Conferma finale** — `✓ Configuration saved to ~/.aisk/`

### Task

- [x] Refactor `init_config()` in `config.py` → estrarre la logica di creazione file in funzioni più piccole
- [x] Nuova funzione `interactive_init()` in `config.py` che implementa il wizard
- [x] Collegare `interactive_init()` al comando `aisk init` in `cli.py`
- [x] Se `aisk init` viene invocato in contesto non-TTY (pipe), fallback al comportamento attuale (crea file senza chiedere)
- [x] Test con mock di `input()` / `builtins.input`

## M9: Nuovi alias Perplexity + aggiornamento default ✅

Aggiungere alias Perplexity ai default e aggiornare il template `conf.toml`.

### Nuovi alias

| Alias | Modello |
|-------|---------|
| `s` | `perplexity/sonar` |
| `sps` | `perplexity/sonar-pro-search` |

### Task

- [x] Aggiungere `s` e `sps` a `DEFAULT_ALIASES` in `config.py`
- [x] Aggiungere la sezione `# Perplexity` al template `DEFAULT_CONF_TOML`
- [x] Aggiornare i test per includere i nuovi alias
- [x] Aggiornare la tabella alias nel DEVPLAN (sezione M2) — non necessario, la sezione M2 elenca solo la struttura originale

## M10: Shell autocomplete ✅

Tab-completion per bash e zsh. Completa il nome del modello (alias + eventuali modelli diretti usati di recente).

### Approccio

Generare uno script di completion che legge gli alias da `~/.aisk/conf.toml` a runtime.

### Task

- [x] `aisk completions bash` — stampa lo script bash completion su stdout
- [x] `aisk completions zsh` — stampa lo script zsh completion su stdout
- [x] Lo script completa:
  - Primo argomento: alias da `conf.toml` + subcomandi (`init`, `models`, `completions`)
  - Flag: `-q`, `--quiet`, `--version`
- [x] Istruzioni di installazione nel README:
  - bash: `eval "$(aisk completions bash)"` in `.bashrc`
  - zsh: `eval "$(aisk completions zsh)"` in `.zshrc`
- [x] Test: verificare che gli script generati contengano gli alias corretti
- [x] Rimuovere la nota "deferred" da M7

## M11: Join messaggi senza virgolette ✅

Bug pratico: `aisk ge3flash what is the CAP theorem` (senza quote) cattura solo "what" come messaggio.

### Task

- [x] In `cli.py`, joinare tutti gli args da posizione 1 in poi come messaggio: `" ".join(positional[1:])`
- [x] Se il risultato è vuoto, fallback a stdin come prima
- [x] Aggiornare i test CLI per coprire il caso multi-word senza quote
- [x] Aggiornare README con esempio senza virgolette

## M12: Auto-init al primo run ✅

Eliminare la necessità di `aisk init` esplicito. Al primo utilizzo (qualsiasi comando che richiede la config), se manca `~/.aisk/` o la API key è vuota, lanciare il wizard interattivo automaticamente.

### Flusso

1. L'utente installa con `uv tool install .`
2. Fa `aisk ge3flash "ciao"` — primo run
3. Rileva che `~/.aisk/` non esiste o `AISK_API_KEY` è vuoto
4. Se TTY → lancia `interactive_init()` automaticamente, poi procede con la query
5. Se non TTY → errore con messaggio "Run 'aisk init' first"

### Task

- [x] Estrarre la logica di check config in una funzione `ensure_config()` in `config.py`
  - Ritorna `Config` se tutto ok
  - Se manca config/key e TTY → lancia wizard, poi ricarica e ritorna
  - Se manca config/key e non TTY → raise/return errore
- [x] Usare `ensure_config()` in `cli.py` al posto di `load_config()` + check manuale della key
- [x] `aisk init` resta disponibile per riconfigurare manualmente
- [x] Test: primo run senza config lancia wizard (mock), poi procede

## M13: Migliorare `aisk models` ✅

Rendere l'output di `aisk models` più leggibile.

### Task

- [x] Raggruppare alias per provider (Google, OpenAI, Anthropic, Perplexity, etc.) basandosi sul prefisso del model name (prima di `/`)
- [x] Formattare con header di sezione e colonne allineate
- [x] Output esempio:
  ```
  Google
    ge31pro      google/gemini-3.1-pro-preview
    ge3flash     google/gemini-2.5-flash-preview

  Perplexity
    s            perplexity/sonar
    sps          perplexity/sonar-pro-search
  ```
- [x] Test: verificare raggruppamento e formattazione

## M14: Aggiornamento README ✅

Allineare il README allo stato attuale del progetto.

### Task

- [x] Aggiungere esempio d'uso senza virgolette (`aisk ge3flash what is the CAP theorem`)
- [x] Aggiungere Perplexity alias (`s`, `sps`) negli esempi
- [x] Rimuovere la necessità di `aisk init` esplicito dalla sezione Setup — spiegare che il wizard parte automaticamente al primo run
- [x] Mantenere `aisk init` documentato come comando per riconfigurare
- [x] Aggiornare sezione Usage con il flusso primo-run

## M15: Installer lancia il wizard + wizard più smart ✅

Il flusso attuale ha due problemi:
1. `install.sh` non lancia il wizard — l'utente deve aspettare il primo `aisk` per configurare
2. Quando il wizard parte automaticamente (auto-init) e `conf.toml` esiste già (ma manca la API key), chiede "Overwrite conf.toml?" — confondendo l'utente. Il vero problema è la key mancante, non il conf.toml.

### Modifiche

#### A. `install.sh` — lanciare `aisk init` dopo l'installazione

- [x] Aggiungere `aisk init` alla fine di `install.sh`, dopo l'install/upgrade
- [x]Il wizard parte direttamente al termine dell'installazione, senza aspettare il primo utilizzo

#### B. `interactive_init()` — comportamento più intelligente nel contesto auto-init

- [x]Aggiungere parametro `auto` (default `False`) a `interactive_init()`
- [x]Quando `auto=True` (chiamato da `ensure_config()`):
  - Se `conf.toml` esiste → **non chiedere** di sovrascriverlo, saltalo silenziosamente
  - Se la API key esiste → **non chiedere** di sovrascriverla, saltala silenziosamente
  - Chiedere solo ciò che manca (tipicamente: solo la API key)
- [x]Quando `auto=False` (chiamato da `aisk init` esplicito):
  - Comportamento attuale invariato — chiede conferma per sovrascrivere tutto

#### C. `ensure_config()` — passare `auto=True`

- [x]Modificare la chiamata in `ensure_config()`: `interactive_init(auto=True)`

#### D. Test

- [x]Test: auto-init con conf.toml esistente + key mancante → chiede solo la key, non tocca conf.toml
- [x]Test: `aisk init` esplicito con conf.toml esistente → chiede overwrite come prima
- [x]Test: install.sh contiene `aisk init` alla fine
