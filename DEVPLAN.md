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

## M16: Auto-install completions + refresh ✅

Le shell completions esistono (`aisk completions bash/zsh`) ma l'utente deve aggiungerle manualmente al proprio `.bashrc`/`.zshrc`. Inoltre, dopo aver modificato gli alias in `conf.toml`, serve un modo per aggiornare le completions nella shell corrente.

### Task

#### A. `aisk completions install` — installa le completions nel file rc della shell

- [x] Detecta la shell corrente (`$SHELL`)
- [x] Appende `eval "$(aisk completions bash)"` a `~/.bashrc` (o `zsh` a `~/.zshrc`)
- [x] Se la riga esiste già, non duplicarla
- [x] Stampa messaggio con istruzioni: "Completions installed. Run `source ~/.bashrc` or open a new terminal."

#### B. `install.sh` — chiama `aisk completions install`

- [x] Aggiungere `aisk completions install` dopo `aisk init` nell'installer

#### C. `aisk completions refresh` — rigenera lo script per la shell corrente

- [x] Stampa lo script di completions aggiornato (come `aisk completions bash/zsh` ma auto-detectando la shell)
- [x] L'utente lo usa con: `eval "$(aisk completions refresh)"`
- [x] Documentare nel README

#### D. Test

- [x] Test: `aisk completions install` appende la riga corretta
- [x] Test: `aisk completions install` non duplica se già presente
- [x] Test: `aisk completions refresh` produce output valido

## M17: Allinea alias ad aider+ e fix costi ✅

Due problemi:
1. Gli alias puntano a modelli vecchi/errati rispetto ad aider+
2. I costi non vengono mostrati: il codice cerca `chunk["cost"]` ma OpenRouter li mette in `usage.cost` o `usage.total_cost`

### A. Aggiornamento alias

Allineare `DEFAULT_ALIASES` e `DEFAULT_CONF_TOML` a quelli di aider+ (mantenendo `s` e `sps` Perplexity che non ci sono in aider+):

| Alias | Vecchio | Nuovo (da aider+) |
|---|---|---|
| ge3flash | `google/gemini-2.5-flash-preview` | `google/gemini-3-flash-preview` |
| ge25flash | `google/gemini-2.5-flash-preview` | `google/gemini-2.5-flash` |
| ge25lite | `google/gemini-2.5-flash-lite-preview` | `google/gemini-2.5-flash-lite` |
| clo46 | `anthropic/claude-opus-4` | `anthropic/claude-opus-4.6` |
| cls46 | `anthropic/claude-sonnet-4` | `anthropic/claude-sonnet-4.6` |
| dsv32 | `deepseek/deepseek-chat-v3-0324` | `deepseek/deepseek-v3.2` |
| dsr1 | `deepseek/deepseek-r1` | `deepseek/deepseek-r1-0528` |
| qwen35p | `qwen/qwen3.5-coder-plus` | `qwen/qwen3.5-plus-02-15` |
| qwen35 | `qwen/qwen3.5-coder` | `qwen/qwen3.5-397b-a17b` |
| m25 | `minimax/minimax-m1-80k` | `minimax/minimax-m2.5` |
| glm5 | `zhipu/glm-5-plus` | `z-ai/glm-5` |
| mistral | `mistralai/mistral-large-2411` | `mistralai/mistral-large-2512` |
| l4scout | `meta-llama/llama-4-scout` | `meta-llama/llama-4-scout:groq` |
| l4mav | `meta-llama/llama-4-maverick` | `meta-llama/llama-4-maverick:groq` |

### Task

- [x] Aggiornare `DEFAULT_ALIASES` in `config.py`
- [x] Aggiornare `DEFAULT_CONF_TOML` in `config.py`

### B. Fix costi

- [x] In `client.py`, cercare il costo in `usage.cost` e `usage.total_cost` (come fa a+ask) invece di `chunk.cost`

### C. Test

- [x] Aggiornare test che referenziano i vecchi model name
- [x] Test: il costo viene estratto da `usage.cost`

## M18: Pulizia e aggiornamento alias (marzo 2026) ✅

Audit degli alias default basato sullo stato dei modelli a marzo 2026. Obiettivi: rimuovere modelli ridondanti/superati, aggiornare model ID obsoleti, aggiungere modelli flagship mancanti.

### A. Rimozioni (5 alias)

| Alias | Modello | Motivo |
|---|---|---|
| `gpt5` | `openai/gpt-5` | Superato da GPT-5.4 |
| `gpt51` | `openai/gpt-5.1` | Superato — ridondante tra 5 e 5.2 |
| `gpt52` | `openai/gpt-5.2` | Superato da GPT-5.4 |
| `ge25lite` | `google/gemini-2.5-flash-lite` | Ridondante con ge25flash, differenza minima |
| `k25` | `moonshotai/kimi-k2.5` | SWE-bench 76.8%, più caro di m25 ($0.50/$2.80 vs $0.30/$1.20) — peggiore dei tre cinesi |

### B. Aggiornamenti (2 alias)

| Alias | Vecchio model ID | Nuovo model ID | Motivo |
|---|---|---|---|
| `ge3flash` | `google/gemini-3-flash-preview` | `google/gemini-3.1-flash-lite-preview` | Gemini 3 Flash in dismissione il 26/03/2026 — 3.1 Flash Lite è il successore economico ($0.25/$1.50) |
| `dsr1` | `deepseek/deepseek-r1-0528` | `deepseek/deepseek-r1` | Rimuovere suffisso data — OpenRouter punta già alla versione corrente |

### C. Aggiunte (2 alias)

| Alias | Modello | Prezzo | Motivo |
|---|---|---|---|
| `gpt54` | `openai/gpt-5.4` | $2.50/$20 | Nuovo flagship OpenAI, unifica Codex+GPT, 1M context |
| `clh45` | `anthropic/claude-haiku-4.5` | $0.25/$1.25 | Opzione budget Anthropic mancante |

### D. Rinominare alias ge3flash → ge31lite

L'alias `ge3flash` cambia semantica (da flash a flash-lite, da 3.0 a 3.1). Per coerenza con la nomenclatura:
- Rinominare `ge3flash` → `ge31lite` (punta a `google/gemini-3.1-flash-lite-preview`)
- Questo evita confusione: l'alias dice cosa è

### E. Risultato finale

Da 21 a 18. Lista aggiornata:

| Alias | Modello | Prezzo (in/out per 1M) |
|---|---|---|
| **Google Gemini** | | |
| `ge31pro` | `google/gemini-3.1-pro-preview` | $2.00 / $12.00 |
| `ge31lite` | `google/gemini-3.1-flash-lite-preview` | $0.25 / $1.50 |
| `ge25flash` | `google/gemini-2.5-flash` | ~$0.30 / $2.50 |
| **OpenAI** | | |
| `gpt54` | `openai/gpt-5.4` | $2.50 / $20.00 |
| `gpt5mini` | `openai/gpt-5-mini` | $0.25 / $2.00 |
| `gpt5nano` | `openai/gpt-5-nano` | $0.05 / $0.40 |
| `o4m` | `openai/o4-mini` | $1.10 / $4.40 |
| **Anthropic** | | |
| `clo46` | `anthropic/claude-opus-4.6` | $5.00 / $25.00 |
| `cls46` | `anthropic/claude-sonnet-4.6` | $3.00 / $15.00 |
| `clh45` | `anthropic/claude-haiku-4.5` | $0.25 / $1.25 |
| **DeepSeek** | | |
| `dsv32` | `deepseek/deepseek-v3.2` | $0.26 / $0.38 |
| `dsr1` | `deepseek/deepseek-r1` | $0.70 / $2.50 |
| **Qwen** | | |
| `qwen35p` | `qwen/qwen3.5-plus-02-15` | — |
| `qwen35` | `qwen/qwen3.5-397b-a17b` | — |
| **Perplexity** | | |
| `s` | `perplexity/sonar` | — |
| `sps` | `perplexity/sonar-pro-search` | — |
| **Other** | | |
| `m25` | `minimax/minimax-m2.5` | $0.30 / $1.20 |
| `glm5` | `z-ai/glm-5` | — |
| `mistral` | `mistralai/mistral-large-2512` | — |
| `l4scout` | `meta-llama/llama-4-scout:groq` | — |
| `l4mav` | `meta-llama/llama-4-maverick:groq` | — |

### Task

- [x] Aggiornare `DEFAULT_ALIASES` in `config.py` (rimozioni + aggiunte + aggiornamenti)
- [x] Aggiornare `DEFAULT_CONF_TOML` in `config.py`
- [x] Aggiornare i test in `test_aliases.py` e `test_config.py`
- [x] Aggiornare gli esempi nel README se referenziano alias rimossi
- [ ] Aggiornare la tabella M17 nel DEVPLAN per riflettere lo stato storico (skipped — storico intatto per riferimento)

## M19: Shell shortcuts da conf.toml ✅

Generare funzioni shell (es. `ds()`, `sps()`) direttamente da una sezione `[shortcuts]` in `conf.toml`, eliminando la necessità di definirle manualmente nel `.bashrc`.

### Motivazione

L'utente ha funzioni manuali nel bashrc (`ds`, `k25`, `sps`) che chiamano il vecchio `a+ask`. Centralizzare in `conf.toml` rende tutto gestibile da aisk: aggiungere/rimuovere shortcut = editare il toml.

### Formato conf.toml

```toml
[shortcuts]
ds = "dsv32"
sps = "sps"
gpt = "gpt54"
cl = "cls46"
ge = "ge25flash"
```

Ogni chiave è il nome della funzione shell, il valore è l'alias aisk (o un model name diretto).

### Generazione

Ogni shortcut `nome = "alias"` genera:

```bash
nome() { aisk alias "$@"; }
```

Per zsh, stessa sintassi (compatibile).

### Integrazione con completions

Lo script generato da `aisk completions bash/zsh` includerà in coda le funzioni shortcut. Così `eval "$(aisk completions bash)"` nel bashrc attiva sia le completions che gli shortcut — zero configurazione manuale.

### Subcomando `aisk shortcuts`

Stampa le funzioni shell generate, utile per debug:

```
$ aisk shortcuts
ds()  { aisk dsv32 "$@"; }
sps() { aisk sps "$@"; }
gpt() { aisk gpt54 "$@"; }
cl()  { aisk cls46 "$@"; }
ge()  { aisk ge25flash "$@"; }
```

### Default shortcuts

Aggiungere una sezione `[shortcuts]` al `DEFAULT_CONF_TOML` con:

| Shortcut | Alias | Modello |
|----------|-------|---------|
| `ds` | `dsv32` | DeepSeek v3.2 |
| `sps` | `sps` | Perplexity sonar-pro-search |

Solo questi due di default (quelli che l'utente usa già). Gli altri (`gpt`, `cl`, `ge`) saranno suggeriti come commenti nel template.

### Pulizia bashrc

L'utente rimuoverà manualmente le vecchie funzioni `ds()`, `k25()`, `sps()` dal bashrc. L'installer **non** tocca funzioni esistenti — mostra solo un messaggio se rileva residui.

### Task

- [x] Aggiungere sezione `[shortcuts]` a `DEFAULT_CONF_TOML` in `config.py`
- [x] Aggiungere campo `shortcuts: dict[str, str]` a `Config` dataclass in `config.py`, con parsing da `conf.toml`
- [x] Nuova funzione `generate_shortcuts()` in `completions.py` — genera le funzioni shell dalla config
- [x] Integrare `generate_shortcuts()` nell'output di `generate_bash()` e `generate_zsh()` (append in coda allo script)
- [x] Nuovo subcomando `aisk shortcuts` in `cli.py` — stampa solo le funzioni generate (per debug/verifica)
- [x] `install.sh` — dopo l'installazione, mostrare hint se rileva vecchie funzioni `a+ask` nel bashrc
- [x] Test: `generate_shortcuts()` produce output corretto
- [x] Test: completions bash/zsh includono gli shortcut in coda
- [x] Test: `aisk shortcuts` stampa le funzioni
- [x] Test: config senza `[shortcuts]` → nessun errore, shortcuts vuoti
- [x] Aggiornare README con documentazione shortcuts
- [x] Fix: rimossi branch morti nei template bash/zsh completions (pre-esistenti)

## M20: Timeout idle invece di totale ✅

Il timeout attuale (`client.py:42`) è un timeout **totale** di 120 secondi passato a `httpx.Client(timeout=120.0)`. Questo significa che se una risposta streammata impiega più di 120 secondi in totale (anche se il modello sta ancora mandando token attivamente), la connessione viene chiusa con "Request timed out".

### Problema

Il timeout dovrebbe scattare solo quando il modello **smette di rispondere** per un certo periodo, non quando la risposta totale supera un limite. Risposte lunghe e ragionamento esteso (thinking) possono facilmente superare i 2 minuti.

### Soluzione

Usare `httpx.Timeout` granulare invece di un singolo float:

```python
httpx.Timeout(
    connect=10.0,    # max 10s per stabilire la connessione
    read=120.0,      # max 120s di silenzio tra un chunk e l'altro
    write=10.0,      # max 10s per inviare il payload
    pool=10.0,       # max 10s per ottenere una connessione dal pool
)
```

Il parametro chiave è `read`: è un timeout **tra chunk successivi**, non sulla durata totale. Se il modello manda token ogni secondo, non scade mai. Se smette di mandare dati per 120 secondi, scatta il timeout.

### Task

- [x] Sostituire `timeout: float = 120.0` con `httpx.Timeout` granulare in `stream_chat()`
- [x] Parametro `read_timeout` (default 120s) per controllare il timeout di inattività
- [x] Parametro `connect_timeout` (default 10s) per il timeout di connessione
- [x] Differenziare il messaggio di errore: "Connection timed out" vs "Response timed out (no data for Xs)"
- [x] Test: verificare che il timeout granulare viene passato correttamente a `httpx.Client`
- [x] Test: timeout di connessione produce messaggio distinto da timeout di lettura

## M21: Opzione output buffered (`--no-stream`) ✅

Attualmente l'output è sempre progressivo (streaming token-by-token). Aggiungere un'opzione per accumulare tutta la risposta e stamparla in un colpo solo alla fine.

### Motivazione

Lo streaming è ottimo per l'uso interattivo, ma in alcuni casi un output completo è preferibile:
- Piping verso tool che si aspettano input completo (non parziale)
- Script che processano la risposta intera
- Contesti dove il flickering dello streaming è indesiderato

Nota: `-q` già esiste per output minimale, ma stampa comunque in streaming. `--no-stream` è ortogonale: controlla *quando* stampare, non *cosa* stampare. Combinazioni possibili:
- Default: streaming + verbose
- `-q`: streaming + solo testo
- `--no-stream`: buffered + verbose
- `-q --no-stream`: buffered + solo testo

### Approccio

Due livelli di implementazione:

#### A. Client-side buffering (semplice)

Continuare a fare streaming HTTP (per avere il timeout idle di M20), ma accumulare gli eventi in memoria e renderizzarli alla fine.

#### B. Flag CLI

- `--no-stream` / `-S` — stampa la risposta completa alla fine
- Funziona sia con verbose che con quiet
- Lo streaming HTTP resta attivo (non si cambia `"stream": True` nel payload) — il buffering è solo lato output

### Task

- [x] Aggiungere flag `--no-stream` / `-S` a `build_parser()` in `cli.py`
- [x] Nuove funzioni `render_verbose_buffered()` e `render_quiet_buffered()` in `output.py` che accumulano gli eventi e stampano alla fine
- [x] Wiring in `cli.py`: se `--no-stream`, usare i renderer buffered
- [x] Test: `--no-stream` produce lo stesso contenuto del modo streaming (solo il timing cambia)
- [x] Test: `-q --no-stream` produce output identico a `-q` (ma buffered)
- [x] Aggiornare README con documentazione del flag

## M22: Aggiornamento alias modelli (apr 2026) ✅

Il pool di modelli in `DEFAULT_ALIASES` e `DEFAULT_CONF_TOML` (`config.py`) è invecchiato. Fra il 18 marzo e il 24 aprile 2026 sono usciti nuovi modelli rilevanti — DeepSeek V4 (flash + pro, 1M ctx, prezzi molto aggressivi), Claude Opus 4.7, GPT-5.5, GLM 5.1, Kimi K2.6, MiniMax M2.7, Qwen 3.6 Plus. Rinnoviamo il catalogo sostituendo i vecchi alias con le versioni correnti.

### Sostituzioni (vecchio → nuovo)

| Vecchio alias | Vecchio modello | Nuovo alias | Nuovo modello | I/O $/M |
|---|---|---|---|---|
| `clo46` | `anthropic/claude-opus-4.6` | `clo47` | `anthropic/claude-opus-4.7` | 5 / 25 |
| `gpt54` | `openai/gpt-5.4` | `gpt55` | `openai/gpt-5.5` | 5 / 30 |
| `dsv32` | `deepseek/deepseek-v3.2` | `dsv4f` | `deepseek/deepseek-v4-flash` | 0.14 / 0.28 |
| `dsr1` | `deepseek/deepseek-r1` | `dsv4p` | `deepseek/deepseek-v4-pro` | 1.74 / 3.48 |
| `glm5` | `z-ai/glm-5` | `glm51` | `z-ai/glm-5.1` | 1.05 / 3.50 |
| `m25` | `minimax/minimax-m2.5` | `m27` | `minimax/minimax-m2.7` | 0.30 / 1.20 |
| `qwen35p` | `qwen/qwen3.5-plus-02-15` | `qwen36p` | `qwen/qwen3.6-plus` | — |
| `qwen35` | `qwen/qwen3.5-397b-a17b` | *(rimosso)* | — | — |

### Aggiunte

| Nuovo alias | Modello | I/O $/M | Note |
|---|---|---|---|
| `kimi26` | `moonshotai/kimi-k2.6` | 0.74 / 4.66 | coding |
| `gpt55pro` | `openai/gpt-5.5-pro` | 30 / 180 | reasoning top tier |

### Non modificati

- `ge31pro`, `ge31lite`, `ge25flash` (gemini-3.1-flash-lite-preview è già l'alias corrente)
- `cls46`, `clh45` (Sonnet 4.7 / Haiku 4.6 non ancora rilasciati al 24 apr 2026)
- `o4m`, `gpt5mini`, `gpt5nano` (tier economici OpenAI, li lasciamo)
- `s`, `sps` (Perplexity)
- `mistral`, `l4scout`, `l4mav`

### Shortcut

- `ds` → repuntare da `dsv32` a `dsv4f` (nuovo default DeepSeek, economico e 1M ctx).

### Task

- [x] Aggiornare `DEFAULT_ALIASES` in `src/aisk/config.py` con le sostituzioni e aggiunte sopra
- [x] Aggiornare `DEFAULT_CONF_TOML` con gli stessi alias (sezione `[aliases]`)
- [x] Aggiornare `DEFAULT_SHORTCUTS` e `[shortcuts]` in `DEFAULT_CONF_TOML`: `ds = "dsv4f"`
- [x] Aggiornare i test in `tests/` che referenziano gli alias rinominati/rimossi
- [x] Verificare via `grep` che nessun altro file (README, docs) contenga gli alias vecchi e, se sì, aggiornarli
- [x] Nota: il `conf.toml` già installato nella home dell'utente non viene toccato — la sostituzione riguarda solo i default del codice e il template di `aisk init`
- [x] Aggiunto `tests/conftest.py`: fixture autouse `isolate_user_config` che redirige `CONFIG_DIR/FILE/ENV_FILE` a `tmp_path` per tutti i test. Era un problema pre-esistente di hygiene (alcuni test leggevano il `~/.aisk/conf.toml` reale del dev), riemerso cambiando i default; la fix è ortogonale ma necessaria
- [x] Aggiunto test `test_default_conf_toml_matches_default_aliases`: parseggia `DEFAULT_CONF_TOML` e verifica coerenza con `DEFAULT_ALIASES`/`DEFAULT_SHORTCUTS` — guardia contro drift fra le due sorgenti di verità in `config.py`

## M23: Review fix — coerenza e hygiene ✅

Esito della review del 2 giu 2026 (a parità di funzionalità). Fix raggruppati per priorità.

### Bug / incoerenze reali

- [x] **Completion `-S`/`--no-stream`** — `completions.py` conosce solo `-q`/`--quiet`: il flag `-S` introdotto in M21 non è stato propagato. Aggiornare bash e zsh:
  - guardia che attiva il completamento modelli anche dopo `-S`/`--no-stream` (`completions.py:14` bash, `:34` zsh)
  - aggiungere `-S --no-stream` alla lista flag completabili (`completions.py:19`)
- [x] **Install via HTTPS** — il repo è pubblico (la one-liner `curl` usa `raw.githubusercontent.com` senza auth), ma `install.sh:4` e il README usano `git+ssh://git@github.com/...`, che richiede una chiave SSH su GitHub anche solo per installare. Passare a `git+https://github.com/Ymx1ZQ/aisk.git` in `install.sh` e nel README (la sezione "From local clone" può restare invariata; il remote `origin` di sviluppo resta SSH).
- [x] **Permessi `.env`** — `config.py` scrive `~/.aisk/.env` con l'umask di default (di solito `644`), pur contenendo la API key. Aggiungere `os.chmod(ENV_FILE, 0o600)` dopo ogni scrittura (`init_config` e `_write_env`).

### Pulizie minori

- [x] `client.py:108` — rimuovere la riga morta `reasoning = 0` (riassegnata subito dopo a `:110`).
- [x] `cli.py:16` — aggiornare la stringa `usage=` di argparse con `-S`/`--no-stream` e il sottocomando `completions`.
- [x] `install.sh` — l'etichetta `[1/3]` viene stampata due volte (ramo "installo uv" + ramo install/upgrade): rinumerare o unificare.
- [x] `config.py` / `DEFAULT_CONF_TOML` — l'esempio shortcut `sps = "sps"` (nome shortcut identico all'alias) è confuso: sostituire con un esempio chiaro tipo `news = "sps"`.

### Aggiornamento test

- [x] Aggiornare/estendere i test di `tests/test_completions.py` per coprire la presenza di `-S`/`--no-stream` nello script generato.
- [x] Verificare che la suite resti verde (`pytest`).

### Dedup sorgente alias (singola fonte di verità)

Eliminare la doppia manutenzione fra `DEFAULT_ALIASES` (dict) e `DEFAULT_CONF_TOML` (stringa) in `config.py`.

- [x] Introdurre una struttura unica `_ALIAS_GROUPS: list[tuple[str, list[tuple[str, str]]]]` (etichetta provider → lista `(alias, modello)`), che preserva il raggruppamento usato nei commenti del TOML.
- [x] Derivare `DEFAULT_ALIASES` da `_ALIAS_GROUPS` (comprehension).
- [x] Generare `DEFAULT_CONF_TOML` con un helper `_render_default_conf(endpoint)` a partire da `_ALIAS_GROUPS` + `DEFAULT_SHORTCUTS` (commenti `# Provider` per gruppo + sezione `[shortcuts]` con header e esempi commentati).
- [x] Semplificare `_write_conf(endpoint)` per usare `_render_default_conf(endpoint)`, eliminando il fragile `str.replace` sull'endpoint.
- [x] Il test `test_default_conf_toml_matches_default_aliases` resta verde (ora diventa la guardia che la generazione è corretta).

### Note / fuori scope

- Timeout (`read_timeout`/`connect_timeout` hardcoded in `stream_chat`) non esposti in `conf.toml`: possibile estensione futura, fuori scope qui.

## M24: Aggiornamento alias modelli (giugno 2026) ✅

Fonte: OpenRouter, giugno 2026. Aggiornamento mirato: la maggior parte degli alias di M22 (apr 2026) è ancora corrente.

### Sostituzioni

| Vecchio alias | Vecchio modello | Nuovo alias | Nuovo modello | I/O $/M |
|---|---|---|---|---|
| `clo47` | `anthropic/claude-opus-4.7` | `clo48` | `anthropic/claude-opus-4.8` | 5 / 25 |
| `qwen36p` | `qwen/qwen3.6-plus` | `qwen37` | `qwen/qwen3.7-max` | 1.25 / 3.75 |

### Aggiunte

| Nuovo alias | Modello | I/O $/M | Note |
|---|---|---|---|
| `ge35flash` | `google/gemini-3.5-flash` | 1.50 / 9 | nuovo default Gemini, near-Pro, 1M ctx, multimodale |
| `ge25lite` | `google/gemini-2.5-flash-lite` | 0.10 / 0.40 | tier ultra-economico, 1M ctx |

### Rimozioni

| Alias | Modello | Motivo |
|---|---|---|
| `ge25flash` | `google/gemini-2.5-flash` | superato: tier "flash" coperto da `ge35flash`, economico da `ge25lite`/`ge31lite` |

### Non modificati (ancora correnti a giu 2026)

- Google: `ge31pro` (`gemini-3.1-pro-preview` — Gemini 3.5 Pro non ancora su OpenRouter), `ge31lite` (tier economico)
- OpenAI: `gpt55`, `gpt55pro`, `gpt5mini`, `gpt5nano`, `o4m` (GPT-5.5 ancora il top)
- Anthropic: `cls46` (Sonnet 4.6), `clh45` (Haiku 4.5) — ancora i correnti
- DeepSeek: `dsv4f`, `dsv4p` (v4 flash/pro tuttora correnti)
- Altri: `glm51` (GLM 5.1), `kimi26` (Kimi K2.6), `m27` (Minimax M2.7), `mistral`, `l4scout`, `l4mav`
- Perplexity: `s`, `sps`

### Shortcut

- Nessun cambio necessario: `ds = "dsv4f"` resta valido. (`sps` come shortcut va comunque rivisto in M23.)

### Task

- [x] Aggiornare `_ALIAS_GROUPS` in `src/aisk/config.py` (sostituzioni + aggiunte + rimozione sopra) — dopo il dedup di M23 è l'unica sorgente, `DEFAULT_ALIASES` e `DEFAULT_CONF_TOML` si aggiornano da sé
- [x] Verificare che `test_default_conf_toml_matches_default_aliases` resti verde (coerenza dict ↔ TOML)
- [x] Aggiornare i test che referenziano `clo47` / `qwen36p` / `ge25flash`; togliere `ge25lite` dalla lista "removed" in `tests/test_aliases.py` (ora è un alias valido) e aggiungere asserzioni per `clo48` / `qwen37` / `ge35flash` / `ge25lite`
- [x] `grep` su README/docs per gli alias rinominati/rimossi e aggiornarli (es. esempi nel README, riga `# ge = "ge25flash"`)
- [x] Nota: il `conf.toml` già presente nella home dell'utente non viene toccato — cambia solo il default del codice e il template di `aisk init`

## M25: Migrazione repository a GuidanceStudio ✅

Spostamento del repo su `git@github.com:GuidanceStudio/aisk.git`. I riferimenti storici nei milestone precedenti (es. M23) restano invariati: documentano lo stato del momento.

### Task

- [x] `install.sh`: `REPO` → `git+https://github.com/GuidanceStudio/aisk.git`
- [x] README: one-liner `curl` (raw.githubusercontent), `uv tool install git+https://...`, `git clone https://...` → owner `GuidanceStudio`
- [x] Remote `origin` locale → `git@github.com:GuidanceStudio/aisk.git`
- [x] Push su `GuidanceStudio/aisk` (richiede che il repo esista lato GitHub)

## M26: Endpoint generico — qualunque provider OpenAI-compatible ✅

Rendere aisk usabile con qualunque endpoint OpenAI-compatible mantenendo **un solo setting generico** (endpoint + key), con OpenRouter come semplice valore di default. Nessun profilo provider nominato.

Stato attuale: già single endpoint (`[api] endpoint`) + single key (`AISK_API_KEY`); il delta è l'override comodo (env + install non interattivo) e la documentazione.

### Design

- Risoluzione endpoint: `AISK_ENDPOINT` (env, anche da `~/.aisk/.env`) > `conf.toml [api] endpoint` > default OpenRouter.
- La key resta `AISK_API_KEY` (generica, nessun nome provider).
- Override in fase di install: `curl ... | AISK_ENDPOINT=... bash` → l'endpoint viene scritto nel `conf.toml` generato dall'`init` non interattivo.

### Task

- [x] `load_config`: applicare l'override `AISK_ENDPOINT` con precedenza env > conf.toml > default.
- [x] `init_config` (path non interattivo di `aisk init`, usato da `install.sh`): se `AISK_ENDPOINT` è settato, scriverlo nel `conf.toml` generato (via `_write_conf`); altrimenti default.
- [x] Wizard interattivo: copy provider-neutral ("API endpoint — OpenRouter by default"); verificare default mostrato + Enter = default (già così, solo wording).
- [x] README: nuova sezione "Use any OpenAI-compatible provider" con esempi (OpenAI diretto, Groq, server locale), nota sugli alias di default in formato slug OpenRouter (`vendor/model`) e uso del pass-through / alias custom su endpoint diretti; documentare `AISK_ENDPOINT` e l'override at-install.
- [x] Test: precedenza env > toml > default; `init_config` scrive `AISK_ENDPOINT` quando presente.

## M27: Chat interattiva ✅

`aisk <model>` senza messaggio e su terminale (TTY) → REPL che mantiene lo storico e lo rimanda al modello a ogni turno. `aisk <model> "msg"` e la pipe restano one-shot.

### Design

- Uscita: **solo Ctrl-C** (KeyboardInterrupt), esplicitata nel banner iniziale. Nessun comando `/exit` o `/reset`. Ctrl-D / EOF gestito come uscita pulita standard (non pubblicizzato).
- Storico: in-memory per sessione (nessuna persistenza su disco).

### Task

- [x] `client.stream_chat`: generalizzare da `message: str` a `messages: list[dict]`; mantenere un wrapper/compat per il one-shot (costruisce `[{"role": "user", "content": msg}]`).
- [x] `cli.main`: se c'è il modello, nessun messaggio, e `sys.stdin.isatty()` → entrare nel chat loop (invece dell'errore attuale "no message"). Pipe/stdin e `aisk model "msg"` invariati.
- [x] Nuovo `chat()` (modulo `chat.py` o in `output.py`): banner con modello + "Ctrl-C to exit"; loop: prompt utente → append `{"role": "user", ...}` → stream risposta (renderer leggero, senza header per turno) → append `{"role": "assistant", content}` → ripeti.
- [x] Errore a metà conversazione (`ErrorInfo`): stamparlo, NON appendere il turno assistant fallito, restare nel loop.
- [x] Usage per turno: footer compatto/dim (tokens, cost se presente), riusando la logica esistente.
- [x] Test: più turni con `input` mockato → lo storico cresce e viene passato a `stream_chat`; gestione KeyboardInterrupt/EOF; errore mid-chat non rompe il loop.

## M28: Pulizia default — solo ultima generazione per slot ✅

Richiesta: togliere dai modelli suggeriti (default aliases) i modelli vecchi quando esiste l'equivalente di nuova generazione. Analisi: dopo M24 la lista è già quasi tutta corrente; gli unici "vecchia generazione con equivalente nuovo" sono lato OpenAI.

### Sostituzioni (uccidi vecchio, tieni nuovo)

| Vecchio alias | Vecchio modello | Nuovo alias | Nuovo modello | I/O $/M |
|---|---|---|---|---|
| `gpt5mini` | `openai/gpt-5-mini` | `gpt54mini` | `openai/gpt-5.4-mini` | 0.75 / 4.50 |
| `gpt5nano` | `openai/gpt-5-nano` | `gpt54nano` | `openai/gpt-5.4-nano` | 0.20 / 1.25 |

I "piccoli" correnti OpenAI sono GPT-5.4 mini/nano (mar 2026); non esiste gpt-5.5-mini/nano.

### Rimozioni

| Alias | Modello | Motivo |
|---|---|---|
| `o4m` | `openai/o4-mini` | serie-o (o1/o3/o4-mini) ritirata feb 2026; slot reasoning/economico coperto da GPT-5.4 mini/nano e GPT-5.5 |

### Tenuti volutamente (NON sono vecchi-equivalenti: slot di prezzo distinti)

- `ge25lite` (`gemini-2.5-flash-lite`, $0.10/$0.40) vs `ge31lite` (`gemini-3.1-flash-lite`, $0.25/$1.50): il 2.5 è 2.5–4× più economico → resta come tier ultra-cheap. `ge35flash` ($1.50/$9) è lo slot "flash" pieno. Tre fasce di prezzo distinte.
- `ge31pro` (`gemini-3.1-pro-preview`): Gemini 3.5 Pro non è ancora su OpenRouter.
- Anthropic (clo48/cls46/clh45), DeepSeek (dsv4f/dsv4p), Qwen (qwen37), Perplexity (s/sps): già ultima gen.
- `m27`, `glm51`, `kimi26`, `mistral`, `l4scout`, `l4mav`: correnti al check di M24 (non rivisti qui).

### Task

- [x] `_ALIAS_GROUPS` in `config.py`: `gpt5mini`→`gpt54mini`, `gpt5nano`→`gpt54nano`, rimuovere `o4m`
- [x] Test in `tests/test_aliases.py`: nuovi alias risolvono; `gpt5mini`/`gpt5nano`/`o4m` passano in pass-through (removed)
- [x] `grep` README/docs per `gpt5mini`/`gpt5nano`/`o4m` ed eventuali esempi
- [x] Drift test resta verde

## M29: `aisk sync` — riallinea gli alias del conf.toml ai default ✅

Problema emerso: i cambi ai default *del codice* (M24/M28) non toccano il `~/.aisk/conf.toml` già presente nella home. `load_config` fonde `DEFAULT_ALIASES` con gli alias del conf.toml utente (`update`), quindi l'utente continua a vedere i vecchi alias (in `aisk models` e nell'autocomplete) finché non rigenera il file. `aisk init` salta se il file esiste; l'overwrite del wizard resetta anche endpoint/shortcuts.

### Design

Nuovo comando `aisk sync` che riscrive **solo** gli alias del `conf.toml` ai default correnti, preservando `[api]` (endpoint), `[shortcuts]` e gli alias realmente custom.

Per distinguere "ex-default da rimuovere" da "custom da tenere" serve la storia degli alias ritirati:
- `RETIRED_ALIASES: frozenset[str]` in `config.py` = tutte le chiavi alias mai spedite come default e poi rimosse/rinominate. Diventa la sorgente unica usata anche dal test `test_removed_aliases_passthrough` (consolidamento, non nuova manutenzione). Invariante: `RETIRED_ALIASES ∩ DEFAULT_ALIASES = ∅`.

Logica di sync:
- `managed = set(DEFAULT_ALIASES) | RETIRED_ALIASES`
- `custom = { k:v del conf utente | k ∉ managed }`  → preservati
- nuovo `[aliases]` = default correnti + `custom` (sotto un gruppo `# Custom`)
- gli ex-default (in `RETIRED_ALIASES`) spariscono; i default aggiornano i valori
- `[api].endpoint` e `[shortcuts]` riletti dal file e riscritti invariati

### Task

- [x] `config.py`: `RETIRED_ALIASES` (M22+M24+M28 + stale pre-M22); generalizzare il renderer in `_render_conf(endpoint, custom_aliases, shortcuts, *, shortcut_examples)` e far derivare `_render_default_conf` da esso (output invariato → drift/init test verdi).
- [x] `config.py`: `sync_aliases()` → riscrive il conf.toml e ritorna un summary `{added, updated, removed, kept}`. Se il file non esiste, equivale a `init_config`.
- [x] `cli.py`: comando `aisk sync` → esegue e stampa il summary + suggerisce `eval "$(aisk completions refresh)"`.
- [x] `completions.py`: aggiungere `sync` ai subcommand completabili (bash + zsh).
- [x] `cli.py`: aggiornare `usage=` con `sync`.
- [x] Test: `sync_aliases` su un conf con ex-default + alias custom + endpoint custom + shortcuts → ritirati rimossi, default presenti/aggiornati, custom + endpoint + shortcuts preservati; invariante RETIRED∩DEFAULT vuoto; `test_removed_aliases_passthrough` usa `RETIRED_ALIASES`.
- [x] README: documentare `aisk sync` (e nota: dopo un upgrade che cambia i modelli, lancia `aisk sync` per riallineare i suggeriti).

## M30: Chat — interrompi il turno + costo cumulativo ✅

Due problemi emersi usando la chat:
1. Una risposta che degenera/non termina (es. DeepSeek che sputa `\` e righe vuote) blocca la REPL: non c'è modo di fermare il singolo turno, Ctrl-C ucciderebbe l'intera sessione, e l'idle-timeout è 120s. → serve poter interrompere il turno corrente restando in chat.
2. Manca il costo cumulativo della conversazione (c'è solo quello per turno).

### Design

- **Interruzione del turno (Ctrl-C a due livelli):**
  - Ctrl-C **durante** una risposta → interrompe lo stream di quel turno (chiude la connessione httpx), stampa `(interrupted)`, fa rollback dell'exchange (toglie il turno user + parziale) e torna al prompt.
  - Ctrl-C **al prompt vuoto** (o Ctrl-D) → esce dalla chat.
  - Banner aggiornato di conseguenza. Per uscire quindi: Ctrl-C da fermo, o due volte se in mezzo a una risposta.
- **Costo cumulativo:** accumulare `cost` (e token) su tutta la conversazione; footer per-turno mostra sia il costo della chiamata sia il cumulativo, es. `In 13 | Out 99 | Reasoning 66 | $0.000029  ·  Σ $0.000058`. Approssimazione a 6 decimali. Se il provider non riporta il costo, mostrare almeno i token cumulativi.

### Task

- [x] `chat.py`: `_render_turn` ritorna anche l'`UsageInfo`; lo streaming è racchiuso in un try che cattura `KeyboardInterrupt` → abort del turno (rollback) e ritorno al prompt.
- [x] `chat.py`: Ctrl-C/EOF al prompt input → uscita pulita (come ora per EOF).
- [x] `chat.py`: accumulo costi/token di sessione; footer per-turno + cumulativo (Σ) spostato in `chat()`.
- [x] Banner: descrivere il nuovo comportamento di Ctrl-C.
- [x] Test: KeyboardInterrupt durante un turno → loop prosegue, storico rollback; KeyboardInterrupt al prompt → esce; costo cumulativo somma correttamente su più turni.
- [x] README: aggiornare la nota sulla chat (Ctrl-C interrompe la risposta / esce al prompt; costi per-turno e cumulativi).

## M31: Chat — validazione modello immediata (fail-fast) ✅

Problema: entrando in chat con un modello inesistente/typo (`dsv4` invece di `dsv4f`), l'errore arriva solo dopo aver scritto il primo messaggio (`Error: dsv4 is not a valid model ID`). Il pass-through è voluto (qualunque model ID accettato dall'endpoint), quindi localmente non si distingue valido da typo — ma l'endpoint sì.

### Design (combinato)

0. **Skip se è un alias ("shortener"):** se `model_input` è una chiave in `cfg.aliases`, è un modello curato → nessuna chiamata a `/models`, si entra dritti in chat. Il preflight scatta **solo** per i pass-through (ID grezzi digitati), dove nascono i typo (`dsv4`).
1. **Preflight in chat (best-effort) con cache:** per i pass-through, controllare la lista modelli dell'endpoint: `GET {endpoint senza /chat/completions}/models` (standard OpenAI-compatible; OpenRouter, OpenAI, Groq, server locali; degrada in silenzio dove `/models` non esiste).
   - **Cache** in `~/.aisk/models-cache.json`, per endpoint, con TTL 24h.
   - **Hit positivo** (modello presente nella lista in cache fresca) → valido, zero chiamate.
   - **Negativo/cache miss/scaduta** → fetch live, aggiorna cache, poi decidi. (La cache non è mai autorevole sul "no": un modello appena aggiunto non sarebbe nella lista vecchia.)
   - Se la fetch live fallisce/non parsabile → procedere in silenzio (non bloccare).
   - Modello non in lista (confermato live) → errore + suggerimenti, uscita rc 1 *prima* del prompt.
2. **Fail-fast:** se il primo turno va in errore prima di qualunque scambio riuscito, uscire dalla chat con quell'errore invece di restare nel loop a sbagliare ogni volta.
3. **Suggerimenti typo:** via `difflib.get_close_matches` sulle chiavi alias (sull'input digitato) e, in fallback, sugli ID modello disponibili. Es. `dsv4` → "Did you mean: dsv4f, dsv4p?".

One-shot invariato: l'errore è già immediato (una sola richiesta).

### Task

- [x] `client.py`: `list_models(endpoint, api_key)` best-effort → `set[str] | None`; helper `_models_url(endpoint)` (deriva da `…/chat/completions` → `…/models`).
- [x] `config.py` (o nuovo `cache.py`): cache modelli per-endpoint in `~/.aisk/models-cache.json` con TTL 24h; helper get/set; `is_model_valid(endpoint, key, model)` → True/False/None con la logica hit-positivo / refetch-su-negativo.
- [x] `chat.py`: skip preflight se alias; altrimenti validazione via cache+live; messaggio d'errore con suggerimenti; uscita rc 1 se non valido.
- [x] `chat.py`: fail-fast sul primo turno in errore (nessuno scambio riuscito) → uscita.
- [x] `cli.py`: passare anche il `model_input` originale e la mappa alias a `chat()` (per skip-alias e suggerimenti).
- [x] Test: alias → nessuna chiamata a `/models`; pass-through in lista → ok; non in lista → rc 1 + suggerimenti; cache negativa → refetch live; `list_models` None → si procede; primo turno in errore → esce; TTL cache.
- [x] README: nota sulla validazione del modello in chat + cache.


**Note esecuzione (TDD):** preflight saltato anche quando `model_input` è `None` (es. resume: già validato). Il fail-fast sul primo turno in errore sostituisce il vecchio "rollback e continua" SOLO finché non c'è stato uno scambio riuscito; dopo un successo, un errore fa rollback e prosegue. Cache modelli in `~/.aisk/models-cache.json` (chmod 600).
## M32: `--resume` — continua l'ultima conversazione ✅

Richiesta: dopo `aisk dsv4f "ciao"` (one-shot), poter continuare quella conversazione con `aisk --resume`, senza che si faccia casino con altre sessioni aisk aperte in parallelo.

### Design

- **Persistenza per-terminale (anti-conflitto):** la conversazione viene salvata in `~/.aisk/sessions/<key>.json`, dove `key` deriva dal PID della shell padre (`os.getppid()`), stabile entro lo stesso terminale. Terminali diversi → file diversi → nessun clobber tra sessioni parallele. Contenuto: `{model, messages, updated_at}`. `chmod 600`; pruning dei file > 7 giorni a ogni scrittura.
- **Salvataggio:** dopo ogni scambio riuscito — one-shot (tramite un "tee" sul generatore di eventi che accumula i `ContentChunk`, senza toccare i renderer) e ogni turno di chat.
- **`aisk --resume` (senza messaggio):** carica la sessione del terminale corrente; se assente, la più recente in assoluto (fallback). Se non c'è nulla → errore "nothing to resume". Entra in **chat** precaricata con `messages`, modello dalla sessione. Stampa un recap breve (modello + n. messaggi).
- **`aisk --resume "msg"`:** continuazione one-shot: appende `msg`, risponde, ripersiste. Rispetta `-q`/`-S`.
- `--resume` non prende il modello come positional: gli eventuali positional sono il messaggio.

### Task

- [x] Nuovo `session.py` (o in `config.py`): `session_path()` (key da `getppid()`), `save_session(model, messages)`, `load_session()` (corrente → fallback più recente), pruning > 7gg, `chmod 600`.
- [x] `cli.py`: flag `--resume`; ramo dedicato che carica la sessione, instrada a chat (no msg) o one-shot (con msg); errore se niente da riprendere.
- [x] `cli.py`/one-shot: "tee" sugli eventi per catturare il testo assistant e persistere `{user, assistant}` dopo una risposta riuscita.
- [x] `chat.py`: `chat()` accetta `history` precaricato e persiste dopo ogni turno riuscito; integra il recap iniziale.
- [x] Test: save/load round-trip; scoping per-PID (key diversa → file diverso); fallback al più recente; `--resume` senza sessione → errore; continuazione one-shot appende e ripersiste; pruning TTL.
- [x] README: documentare `--resume` (e il comportamento per-terminale).


**Note esecuzione (TDD):** la persistenza è ora attiva anche per il one-shot normale (non solo resume), via `_run_oneshot` con tee sugli eventi → ogni `aisk MODEL "msg"` riuscito salva la sessione. Chat salva dopo ogni turno. Scoping per `getppid()`, fallback al più recente.
## M33: Prompt caching sempre attivo (default) ✅

Ridurre i costi quando si rimanda lo storico (chat/resume) e su prompt lunghi. Caching attivo di default, senza intervento dell'utente.

### Realtà per provider

- OpenAI, DeepSeek, Grok, ecc.: caching **automatico** lato provider → nessuna azione.
- Anthropic (Claude) e Gemini: serve un breakpoint esplicito `cache_control: {"type": "ephemeral"}` sui blocchi messaggio; OpenRouter lo inoltra al provider.

Quindi "sempre attivo" = automatico dove supportato + breakpoint espliciti dove servono.

### Design

- Default **ON**. Escape hatch via env `AISK_PROMPT_CACHE` (`0`/`false`/`no` → off). Nessun campo nuovo nel conf.toml (niente churn su renderer/drift).
- In `stream_chat`: se `prompt_cache` è on **e** l'endpoint è OpenRouter **e** il modello è Anthropic/Gemini → marca l'**ultimo** messaggio con `cache_control` (content convertito in block-form). Altri endpoint/modelli → invariato (auto-cache, e non si rischia un 400 su endpoint generici stretti).
- Breakpoint sull'ultimo messaggio → cacha l'intero prefisso → il turno successivo (chat/resume) è cache-hit (prefisso rolling).

### Task

- [x] `config.py`: `Config.prompt_cache: bool = True`; `load_config` lo deriva da `AISK_PROMPT_CACHE` (default True).
- [x] `client.py`: `_supports_explicit_cache(model)` (claude/anthropic/gemini/google) + `_apply_prompt_cache(messages, model, endpoint)` (gating su `openrouter.ai` nell'endpoint, marca l'ultimo blocco); `stream_chat(..., prompt_cache=True)` applica la trasformazione dopo la normalizzazione dei messaggi.
- [x] `cli.py`/`chat.py`: passare `cfg.prompt_cache` a `stream_chat` (one-shot e chat).
- [x] Test: anthropic+openrouter → ultimo messaggio in block-form con `cache_control`; openai+openrouter → invariato; endpoint non-openrouter → invariato; `prompt_cache=False` → invariato; idempotenza/struttura blocchi.
- [x] README: nota su prompt caching attivo di default (+ `AISK_PROMPT_CACHE=0` per disattivarlo).

**Note esecuzione (TDD):** breakpoint `cache_control` aggiunto solo per Anthropic/Gemini via OpenRouter (gating su `openrouter.ai` nell'endpoint); altri provider cachano in automatico e su endpoint generici stretti si evita un possibile 400. Default ON; `AISK_PROMPT_CACHE=0/false/no/off` per disattivare.

## M34: Code-review follow-ups (D4 + D1) ✅

Esito della `/code-review` su M31–M33. Gemini+`cache_control` testato live su OpenRouter → nessun errore, quindi il gating del prompt caching resta invariato (Anthropic+Gemini).

### Task

- [x] D4 — `session.py:save_session`: `chmod 0o700` sulla dir `~/.aisk/sessions/` (i file sono già 0o600; la dir era coi permessi di default). Coerente con la postura `chmod 600` del `.env`.
- [x] D1 — `client.py:_supports_explicit_cache`: rimuovere la ridondanza dei token (`anthropic`/`claude` e `google`/`gemini` matchano entrambi lo stesso slug) → tenere i nomi-famiglia più precisi: `"claude" in m or "gemini" in m`.
- [x] Test: dir sessioni a `0o700`; `_supports_explicit_cache` resta verde.

## M35: Chat — cronologia prompt con frecce su/giù ✅

Nella REPL interattiva, poter richiamare i prompt precedenti con ↑/↓ (e tornare giù).

### Design

`input()` di Python abilita automaticamente line-editing e cronologia (frecce su/giù) quando il modulo stdlib `readline` è caricato. Basta importarlo in `chat.py`, con guard per le piattaforme senza readline (es. Windows). Cronologia in-sessione, nessun file nuovo, nessuna dipendenza esterna.

### Task

- [x] `chat.py`: `import readline` con `try/except ImportError`, all'avvio del modulo.
- [x] Verificare che la suite resti verde (i test mockano `input`, quindi non toccati).
- [x] README: nota che la chat supporta ↑/↓ per i prompt precedenti.

## M36: Fix — prompt chat colorato corrotto con readline (regressione M35) ✅

Dopo M35 (`import readline`), il prompt `❯` mostrava i codici ANSI letterali (`[36m❯[0m`): readline, sul prompt di `input()`, **rimuove il byte ESC** delle sequenze invisibili se non sono "bracketate" con `\x01` (RL_PROMPT_START_IGNORE) / `\x02` (RL_PROMPT_END_IGNORE). Verificato in pty: unbracketed → ESC stripped; bracketed → ESC preservato.

### Task

- [x] `chat.py`: bracketare i codici colore del prompt con `\x01`/`\x02`. Guard: se readline non è disponibile, usare il prompt semplice (i marcatori `\x01`/`\x02` apparirebbero come garbage senza readline). Esporre `_HAS_READLINE` e `_PROMPT`.
- [x] Test: con readline disponibile `_PROMPT` contiene i bracket `\x01`/`\x02`.
- [x] Verificare via pty che il fix preservi l'ESC.

## M37: `aisk` → chat diretta + comandi in-chat (`/model`, `/help`, `/search`) ✅

Rendere `aisk` senza argomenti l'entry point diretto alla chat col modello di default (`dsf`), spostando l'help attuale su `aisk help`. Aggiungere comandi interni alla chat REPL per cambiare modello, vedere l'help e attivare/disattivare la ricerca web.

### A. Modello di default

Aggiungere `default_model` al `Config` dataclass (`config.py`), leggibile da `conf.toml` sezione `[defaults]`:

```toml
[defaults]
model = "dsf"
```

Se non specificato, default hardcoded = `"dsf"`. Se il valore non è un alias valido, usarlo comunque come pass-through (coerente col comportamento esistente).

### B. `aisk` senza argomenti → chat

In `cli.py`, quando `positional` è vuoto:

- **TTY** (`sys.stdin.isatty()`) → lancia `chat()` col `default_model` (stesso flusso di `aisk <model>` senza messaggio oggi).
- **Non-TTY** → mostra help (comportamento attuale).

### C. `aisk help` — nuovo sottocomando

Aggiungere `"help"` alla lista dei sottocomandi in `cli.py`. Stampa l'help di argparse ed esce.

### D. Comandi in-chat

Messaggi che iniziano con `/` vengono interpretati come comandi interni e **non** inviati al modello. Comandi disponibili:

| Comando | Effetto |
|---|---|
| `/model <alias>` | Cambia modello per la sessione corrente. Valida via cache (stessa logica preflight di M31: skip se alias, check `/models` se pass-through). Mostra "Switched to `<model_id>`" e continua la chat con la history intatta. |
| `/search` | Cicla la modalità ricerca: `auto` → `native` → `off` → `auto`. Mostra la nuova modalità attiva. |
| `/help` | Mostra i comandi disponibili nella chat. |
| `/xxx` (sconosciuto) | "Unknown command. Type /help for available commands." |

Per mandare un messaggio che inizia con `/` al modello (non come comando), l'utente antepone uno spazio.

### E. Toggle ricerca web

La modalità ricerca è per-sessione (non persistita), default `auto`. Il modello riceve il tool `openrouter:web_search` e decide autonomamente quando usarlo (non cerca a ogni messaggio). Tre stati:

| Modalità | `tools` inviato | Comportamento |
|---|---|---|
| `auto` | `[{"type": "openrouter:web_search"}]` | OpenRouter sceglie l'engine migliore (native se supportato, Exa altrimenti). Il modello decide quando cercare. |
| `native` | `[{"type": "openrouter:web_search", "parameters": {"engine": "native"}}]` | Forza la ricerca nativa del provider. Il modello decide quando cercare. |
| `off` | nessun `tools` | Nessuna capacità di ricerca. |

Mostrata nel banner iniziale e a ogni toggle: `Search: auto | native | off`.

### F. Modifiche a `client.py`

Aggiungere parametro opzionale `tools: list[dict] | None = None` a `stream_chat()`. Se fornito, incluso nel payload. Questo abilita sia la ricerca web che eventuali future estensioni (tool/function calling).

### Task

- [x] `config.py`: `Config.default_model: str = "dsf"`, parsing da `[defaults].model` in `conf.toml`.
- [x] `config.py`: `_render_default_conf` — aggiungere sezione `[defaults]` al template con `model = "dsf"`.
- [x] `cli.py`: dispatch `aisk` senza args → TTY: chat(default_model); non-TTY: help.
- [x] `cli.py`: sottocomando `help` → stampa help argparse.
- [x] `cli.py`: aggiornare `usage=` con `help` e nuovo comportamento default.
- [x] `chat.py`: `chat()` accetta ora anche `default_model` (per il banner) e `aliases` (per `/model`).
- [x] `chat.py`: loop principale — se l'input inizia con `/`, parsare il comando; altrimenti inviare al modello.
- [x] `chat.py`: implementare `/model`, `/help`, `/search`.
- [x] `chat.py`: banner mostra modello + stato ricerca (es. `Model: dsf (deepseek/deepseek-v4-flash) · Search: auto`).
- [x] `chat.py`: `/search` toggle cicla e aggiorna lo stato; `stream_chat` riceve `tools` in base allo stato attuale.
- [x] `client.py`: `stream_chat(..., tools=None)` → aggiunto al payload se non-None.
- [x] `completions.py`: aggiungere `help` ai subcommand completabili (bash + zsh).
- [x] Test: `aisk` senza args TTY → chat; non-TTY → help. `aisk help` → help. `/model` in chat valida e switcha. `/search` cicla correttamente. `stream_chat` con tools. Config `default_model` custom.
- [x] README: aggiornare sezione Usage con il nuovo comportamento default + comandi chat. Rimpiazzare gli esempi `aisk` a vuoto che mostrano help con `aisk help`.

## M38: Keyboard shortcuts al posto dei comandi slash in-chat ✅

Eliminare tutti i comandi slash (`/model`, `/search`, `/help`) introdotti in M37 e sostituirli con shortcut da tastiera, accessibili solo in raw-TTY mode.

### Design

#### Keybinding

| Tasto | Azione |
|---|---|
| `Ctrl+S` | Toggle search mode (`auto → native → off → auto`). Lo stato aggiornato è visibile nella barra in basso. |
| `Ctrl+O` | Apre il model selector fuzzy con navigazione a frecce. |
| `Ctrl+G` | Mostra help (comandi disponibili). |

Nessun comando slash rimane: messaggi che iniziano con `/` vanno al modello normalmente. Il banner mostra i tasti.

Nota: `Ctrl+H` richiesto dall'utente ma è già backspace (`\b`) nel raw handler — lo lasciamo com'è. Per help usiamo `Ctrl+G` che è libero. `Ctrl+M` richiesto per model ma è già Enter (`\r`) in raw mode — usiamo `Ctrl+O` che è libero.

#### Ctrl+S — search toggle

- `Ctrl+S` (ASCII 0x13) è XOFF nei terminali, ma `tty.setraw()` disabilita già `IXON`. Come safety aggiuntiva, `stty -ixon` all'inizio del raw mode.
- Il toggle cicla `_SEARCH_MODES`; `_read_tty_input` ridisegna subito il footer, quindi non serve una notifica separata.
- Implementazione: callback `on_search_toggle()` passata a `_read_tty_input`.

#### Ctrl+O — model selector (fuzzy menu)

Premendo `Ctrl+O` (ASCII 0x0F), si apre un overlay sopra l'area del terminale:

```
── Model ─────────────────────────────────────────────
> dsf          deepseek/deepseek-v4-flash
  dsp          deepseek/deepseek-v4-pro
  cls          anthropic/claude-sonnet-4.6
  gpt55        openai/gpt-5.5
─────────────────────────────────────────────────────
Filter: ▌
```

Interazione:
- Digitando: filtro case-insensitive su alias e model name. Se nessun match → riga `(no matches — Enter to use as pass-through)`.
- ↑/↓: naviga la lista; primo elemento selezionato di default.
- Enter: seleziona l'alias evidenziato, o usa il testo filtro come pass-through.
- Esc / Ctrl+C: annulla, torna al prompt senza cambiare modello.
- Dopo selezione: validazione (skip se alias noto, check cache se pass-through, come faceva `/model`). Se valido → `Switched to <model>`. Se invalido → errore con suggerimenti.
- L'input utente in corso non viene toccato (il selettore è un overlay separato).

#### Ctrl+G — help

Premendo `Ctrl+G` (ASCII 0x07), stampa i tasti disponibili e continua. Non interrompe l'input corrente.

#### Rimozione slash-commands

- Parsing `/xxx` rimosso dal loop di `chat()`.
- `_SEARCH_HELP` → `_SHORTCUT_HELP` con i nuovi tasti.
- Test `test_chat_commands.py` riscritto per testare gli shortcut via raw-TTY (pty).
- I messaggi che iniziano con `/` vanno al modello normalmente.
- Banner aggiornato: `Ctrl+S: search · Ctrl+O: model · Ctrl+G: help · Enter: send · Ctrl-J: newline · Ctrl-C: stop/exit`.

### Task

- [x] `chat.py`: `_read_tty_input` accetta callback opzionali `on_ctrl_s`, `on_ctrl_o`, `on_ctrl_g`; le invoca intercettando i byte `\x13`, `\x0f`, `\x07`. Per `Ctrl+S`/`Ctrl+G` chiama la callback e torna al loop; per `Ctrl+O` chiama la callback che restituisce il model name (o None).
- [x] `chat.py`: funzione `_model_selector(aliases)` — overlay fuzzy. Legge da stdin via `os.read` in un loop interno, ridisegna l'overlay a ogni evento. Ritorna il model name o None.
- [x] `chat.py`: funzione `_filter_items(query, aliases)` — filtro case-insensitive su alias e model name.
- [x] `chat.py`: `chat()` — rimosso tutto il parsing slash-command. Il loop principale chiama `stream_chat` per ogni input non-vuoto.
- [x] `chat.py`: `chat()` — callback closures `_toggle_search`, `_select_model`, `_show_help` passate a `_read_user_input`.
- [x] `chat.py`: `_SEARCH_HELP` → `_SHORTCUT_HELP` con i tasti.
- [x] `chat.py`: `_handle_model_switch()` estratta come funzione separata (validazione + switch e notifica).
- [x] `chat.py`: banner aggiornato con i tasti shortcut: `Ctrl+S: search · Ctrl+O: model · Ctrl+G: help`.
- [x] `chat.py`: `_model_selector` gestisce `\x1b` con `select.select` (timeout 50ms) per distinguere Esc standalone da sequenze freccia.
- [x] `chat.py`: rimosso `_format_model_list` (non più usato).
- [x] Test: `tests/test_chat_commands.py` rimosso; nuovo `tests/test_chat_shortcuts.py` con 12 test (mock + pty).
- [x] Test: `Ctrl+S` cicla search mode via pty.
- [x] Test: `Ctrl+O` apre il selettore, ↑/↓ naviga, Enter seleziona, Esc annulla.
- [x] Test: `Ctrl+G` stampa help con i tasti.
- [x] Test: messaggio che inizia con `/` va al modello (non più interpretato).
- [x] Test: `_filter_items` unit test.
- [x] README: aggiornata documentazione chat (shortcut al posto di comandi slash).

## M40: Fix — model selector rendering corrotto alla navigazione

Quando si naviga la lista modelli con ↑/↓ nel fuzzy selector (`Ctrl+O`), il draw completo lascia il cursore sull'ultima riga dell'overlay, mentre `_move_marker` calcola gli spostamenti come se partisse dalla riga `Filter:`. Il primo `Down` quindi ridisegna le righe una posizione sotto quella corretta. Quando si digita un filtro, il repaint parte dalla riga sbagliata e può appendere un secondo overlay invece di sostituire quello esistente.

### Fix

Tracciare la riga corrente dell'overlay e usare `Filter:` come posizione stabile: i redraw completi tornano prima alla cima dell'overlay, cancellano verso il basso, ridisegnano e riportano il cursore sul filtro; la navigazione incrementale parte e termina sempre da quella riga. Le righe aggiornate da `_move_marker` continuano a usare `\x1b[K` per cancellare eventuali residui a fine riga.

### Task

- [x] `chat.py:_model_selector`: aggiungere tracking esplicito della riga corrente e cleanup dalla cima dell'overlay.
- [x] `chat.py:_move_marker`: partire/terminare sempre dalla riga `Filter:` e cancellare i residui con `\x1b[K`.
- [x] Test pty: navigazione `Down` mantiene le righe allineate.
- [x] Test pty: il filtro ridisegna lo stesso overlay senza lasciare la lista precedente visibile.

## M41: Aggiungere installer Windows PowerShell

**Why:** `aisk` oggi si installa bene su Unix via `install.sh`, ma su Windows l'utente deve conoscere `uv` e fare setup manuale. Un installer PowerShell rende il primo utilizzo accessibile senza WSL o Git Bash.

**Approach:** Aggiungere `install.ps1` come installer Windows di prima classe, mantenendo `install.sh` per bash/zsh. Lo script deve rilevare checkout locale tramite `$PSScriptRoot` e usare GitHub quando eseguito da remoto, installare `uv` se manca, fare install/upgrade con `uv tool install`, lanciare `aisk init` e stampare istruzioni Windows chiare. Non aggiungere un `.bat` in questa fase: PowerShell è lo standard giusto per download, PATH e profili; un wrapper batch si valuta solo se serve davvero.

**Tasks:**
- [x] Creare `install.ps1` con rilevamento local checkout vs GitHub.
- [x] Gestire installazione di `uv` mancante usando il percorso ufficiale Windows.
- [x] Eseguire install/upgrade `uv tool install` e poi `aisk init`.
- [x] Aggiungere test per il comportamento dell'installer con `uv`/`aisk` finti, saltando solo se PowerShell non è disponibile.
- [x] Aggiornare README con installazione Windows via PowerShell.
- [x] Commit & push.

**Done when:** `install.ps1` installa o aggiorna `aisk` in un ambiente Windows/PowerShell simulato dai test, e README mostra il comando Windows consigliato.

**Notes:** Niente `install.bat` per ora. Meno entrypoint significa meno comportamento divergente da mantenere.

**Execution notes:** Test locali M41: `uv run pytest -q tests/test_install.py` → `3 passed, 2 skipped`; i due test skippati richiedono PowerShell (`pwsh`/`powershell`) e sono pronti per Windows/CI. Suite completa dopo la correzione del drain pty nei test chat: `uv run pytest -q` → `202 passed, 2 skipped`.

## M42: Rendere il runtime basic portabile su Windows

**Why:** L'installer da solo non basta: `aisk init`, one-shot, resume e chat base devono funzionare anche quando mancano `termios`, `tty` e `readline`. Questo dà supporto Windows utile prima della parità completa della REPL.

**Approach:** Rendere best-effort le operazioni POSIX-only (`chmod` su config/cache/sessioni) e verificare esplicitamente il fallback `input()` quando il raw TTY non è disponibile. La chat Windows basic non avrà ancora shortcut raw (`Ctrl+S`, `Ctrl+O`, `Ctrl+G`), ma non deve crashare; il comportamento deve essere documentato con la combinazione EOF corretta per Windows (`Ctrl+Z` poi Enter).

**Tasks:**
- [x] Introdurre helper interni per permessi file best-effort in `config.py`, `cache.py`, `session.py`.
- [x] Coprire con test il fallback chat quando `termios`/`tty` non sono disponibili.
- [x] Verificare `aisk init`, `models`, one-shot e `--resume` con path Windows simulati dove possibile.
- [x] Documentare nel README lo stato "Windows basic" e le differenze temporanee della chat.
- [x] Commit & push.

**Done when:** La suite copre un ambiente senza `termios` e i comandi non-interattivi più chat `input()` non dipendono da primitive POSIX.

**Execution notes:** Aggiunto `permissions.chmod_private()` e sostituiti i `chmod` diretti su config/cache/session. Test coprono `NotImplementedError` da `chmod`, fallback chat senza `termios`/`tty`, e un flusso `models` → one-shot → `--resume` sotto path tipo Windows con spazio. La chat ora parte con `Search: off` per mantenere lo streaming progressivo identico al one-shot; `Ctrl+S` abilita `off → auto → native → off`. Test locali: `uv run pytest -q` → `210 passed, 2 skipped`.

## M43: Aggiungere completions e shortcut PowerShell

**Why:** Su Windows l'integrazione shell non può dipendere da bash/zsh. PowerShell deve avere completamento di alias/subcommand e funzioni shortcut equivalenti a quelle generate per Unix.

**Approach:** Estendere `completions.py` con `generate_powershell()` e aggiornare `cli.py` per accettare `aisk completions powershell`. Generare `Register-ArgumentCompleter` per alias, subcommand e flag; generare shortcut come funzioni PowerShell (`function ds { aisk dsf @args }`). L'installazione nel profilo PowerShell può essere gestita da `install.ps1` o da `aisk completions install` quando il runtime rileva PowerShell.

**Tasks:**
- [x] Implementare `generate_powershell()` in `completions.py`.
- [x] Aggiornare CLI usage/help: `completions <bash|zsh|powershell|install|refresh>`.
- [x] Aggiornare `install_completions()`/`generate_refresh()` per gestire PowerShell su Windows senza rompere bash/zsh.
- [x] Agganciare `install.ps1` alla configurazione del profilo PowerShell, evitando duplicati.
- [x] Test: generazione completions PowerShell con alias, subcommand, flag e shortcut.
- [x] Test: installazione nel profilo PowerShell simulato senza duplicati.
- [x] Aggiornare README.
- [x] Commit & push.

**Done when:** `aisk completions powershell` produce uno script caricabile e l'installer Windows può installarlo nel profilo PowerShell senza duplicazioni.

**Execution notes:** `generate_powershell()` registra un `Register-ArgumentCompleter` nativo per alias/subcommand/flag e aggiunge funzioni shortcut PowerShell da `[shortcuts]`. `install_completions()` ora rileva PowerShell, usa `$env:AISK_POWERSHELL_PROFILE` quando fornito dall'installer, crea il profilo se manca e non duplica la riga `aisk completions powershell | Invoke-Expression`. `install.ps1` esegue `aisk completions install` dopo `aisk init`. Test locali: `uv run pytest -q` → `215 passed, 2 skipped`; i due skip richiedono PowerShell reale.

## M44: Aggiungere guardrail CI cross-platform

**Why:** Senza una matrice Windows reale, il supporto rischia di regredire appena si tocca input, config o installazione. Serve un controllo automatico minimo prima di affrontare la REPL avanzata.

**Approach:** Aggiungere una GitHub Actions matrix su Ubuntu e Windows usando `uv`, con pytest completo dove possibile. I test pty POSIX devono restare skip automatici su Windows; i test PowerShell devono girare solo quando `pwsh` esiste. Questo milestone non cambia feature utente, ma rende verificabile il supporto appena introdotto.

**Tasks:**
- [x] Creare workflow CI con Python supportato dal progetto e `uv`.
- [x] Eseguire pytest su Ubuntu e Windows.
- [x] Marcare o adattare i test POSIX-only perché saltino in modo esplicito su Windows.
- [x] Aggiungere un check dedicato per `install.ps1` quando `pwsh` è disponibile.
- [x] Documentare nel README/badge o nella sezione contributor il comando locale equivalente.
- [x] Commit & push.

**Done when:** La CI esegue la suite su Windows e Ubuntu, con skip intenzionali solo per funzionalità POSIX non ancora migrate.

**Execution notes:** Aggiunto `.github/workflows/ci.yml` con matrix `ubuntu-latest`/`windows-latest`, Python 3.12, `astral-sh/setup-uv@v8`, `uv run pytest -q` e smoke Windows dedicato via `pwsh` su `tests/test_install.py` dopo `Test-Path .\install.ps1`. I test pty sono già guarded da import `pty` e saltano sulle piattaforme senza pty. README documenta il comando locale equivalente. Test locali: `uv run pytest -q` → `217 passed, 2 skipped`.

## M45: Migrare il prompt chat a `prompt_toolkit`

**Why:** Il raw terminal code attuale ha già richiesto fix delicati e resta POSIX-only. `prompt_toolkit` è la strada più solida per input multilinea, history, keybinding e footer cross-platform senza duplicare backend Unix/Windows.

**Approach:** Aggiungere `prompt_toolkit` come dipendenza runtime e introdurre un nuovo backend input per la chat. Il primo step deve coprire prompt multilinea, history in-sessione, footer con modello/search, `Ctrl+S` toggle search e `Ctrl+G` help. Il backend raw POSIX può restare come fallback temporaneo finché la parità non è completa.

**Tasks:**
- [ ] Aggiungere `prompt_toolkit` alle dipendenze e aggiornare lockfile.
- [ ] Implementare backend input `prompt_toolkit` per prompt, multilinea, history e footer.
- [ ] Collegare `Ctrl+S` e `Ctrl+G` nel nuovo backend.
- [ ] Mantenere o limitare il backend raw POSIX come fallback temporaneo, con selezione esplicita e testata.
- [ ] Test: input multilinea, history, toggle search e help sul nuovo backend con test non-pty.
- [ ] Aggiornare README sulle shortcut cross-platform disponibili.
- [ ] Commit & push.

**Done when:** La chat usa un backend cross-platform per input base e shortcut `Ctrl+S`/`Ctrl+G`, con test deterministici senza pty.

## M46: Migrare il model selector a `prompt_toolkit`

**Why:** `Ctrl+O` e il fuzzy selector sono la parte più fragile del raw terminal code e la più importante per parità Windows. Migrarlo chiude il gap funzionale della chat interattiva.

**Approach:** Reimplementare il selector modelli usando `prompt_toolkit` invece di disegnare manualmente con sequenze ANSI. Deve preservare filtro case-insensitive, navigazione ↑/↓, Enter per selezionare alias o pass-through, Esc/Ctrl+C per annullare e ripristino dell'input corrente. Dopo la parità, rimuovere o isolare il vecchio `_model_selector` raw.

**Tasks:**
- [ ] Implementare selector modelli `prompt_toolkit` con filtro e navigazione.
- [ ] Collegare `Ctrl+O` nel backend chat cross-platform.
- [ ] Preservare validazione modello e messaggio `Switched to ...`.
- [ ] Test: filtro, navigazione, selezione, pass-through e cancel senza pty.
- [ ] Rimuovere o confinare il vecchio selector raw POSIX se non più usato.
- [ ] Aggiornare README: Windows chat con `Ctrl+S`, `Ctrl+O`, `Ctrl+G`.
- [ ] Commit & push.

**Done when:** Windows e Unix hanno lo stesso comportamento per il selector modelli, coperto da test senza dipendere da pty.
