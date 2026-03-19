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

## M21: Opzione output buffered (`--no-stream`)

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

- [ ] Aggiungere flag `--no-stream` / `-S` a `build_parser()` in `cli.py`
- [ ] Nuove funzioni `render_verbose_buffered()` e `render_quiet_buffered()` in `output.py` che accumulano gli eventi e stampano alla fine
- [ ] Wiring in `cli.py`: se `--no-stream`, usare i renderer buffered
- [ ] Test: `--no-stream` produce lo stesso contenuto del modo streaming (solo il timing cambia)
- [ ] Test: `-q --no-stream` produce output identico a `-q` (ma buffered)
- [ ] Aggiornare README con documentazione del flag
