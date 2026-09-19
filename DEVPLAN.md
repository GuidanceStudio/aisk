# aisk — Development Plan

Archived: M1-M17, M19-M38, M40-M50 -> `DEVPLAN-ARCHIVE.md` (one line per milestone; the sha is the pointer to the full detail).

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

*(M39: nessuna traccia nella storia git — né commit, né `-S`/`-G` pickaxe, né oggetti orfani. Il commit che ha introdotto M40 (`10eadbb`) lo aggiunge subito dopo M38 nello stesso diff: la numerazione è passata da M38 a M40 in fase di stesura, M39 non è mai esistito.)*

## M51: Archiviare le milestone chiuse (M1-M17, M19-M38, M40-M50) ✅

**Why:** Il devplan aveva accumulato ~11.700 parole di lavoro storico ormai immutabile che nessuno rilegge; comprimere le milestone chiuse a un pointer sha riduce il file al lavoro ancora vivo.

**Approach:** Per ogni milestone con heading `✅` e tutti i task `- [x]`, trovare lo sha che l'ha spedita (`git log --oneline --all | grep -i`, incrociato con `git blame`/`git log -S` sull'heading in `DEVPLAN.md`), verificarlo con `git cat-file -e <sha>^{commit}`, e scrivere una riga `MNN | title | date | sha` in `DEVPLAN-ARCHIVE.md`. M18 resta nel piano attivo (porta un task `- [ ]`, quindi non è chiusa); la nota su M39 resta nel piano attivo (nessun commit da puntare).

**Tasks:**
- [x] Enumerare le milestone chiuse (heading `✅` + tutti i task `- [x]`) ed escludere quelle con task non chiusi.
- [x] Trovare e verificare lo sha di ciascuna milestone chiusa (`git cat-file -e`).
- [x] Scrivere `DEVPLAN-ARCHIVE.md` con una riga per milestone, ordine cronologico.
- [x] Rimuovere i blocchi archiviati da `DEVPLAN.md`, lasciando un pointer in testa.
- [x] Verificare che l'insieme degli ID prima e dopo l'archiviazione coincida (script di diff).
- [x] Eseguire `uv run pytest -q` e confermare invarianza rispetto alla baseline.
- [x] Commit di devplan + archivio insieme, push su `main`.

**Done when:** `DEVPLAN.md` contiene solo M18, la nota M39 e questa milestone; `DEVPLAN-ARCHIVE.md` contiene le 48 righe archiviate con sha verificato; il diff dell'insieme degli ID è vuoto; la suite è verde.

**Execution notes:** 48 milestone archiviate (0 senza commit trovato), tutti gli sha verificati con `git cat-file -e`. Diff ID set prima/dopo: vuoto (nessuna milestone persa; M51 è l'unico ID nuovo). `uv run pytest -q` non torna pulito in questo sandbox: 3-5 test falliscono in modo non deterministico tra run diversi (`test_chat.py`/`test_chat_shortcuts.py`, tutti basati su `pty.openpty()` con timeout 2s). Confermato non causato da questa milestone: `git status` mostra zero file di codice toccati (solo `DEVPLAN.md` modificato, `DEVPLAN-ARCHIVE.md` nuovo), e `tty`/`sys.stdout.isatty()` confermano che questa shell non ha un tty di controllo reale — i sottoprocessi pty timeoutano per limite dell'ambiente, non per regressione. Nessuna modifica al codice applicativo.

## M52: Aggiornare gli alias default al catalogo di settembre 2026 ✅

**Why:** Tre alias non funzionano più e otto puntano a modelli superati. `mistral` →
`mistralai/mistral-large-2512` è stato delistato da OpenRouter (sopravvive solo la variante
`:batch`, che non è utilizzabile in chat); `lscout`/`lmav` pinnano Groq con il suffisso
`:groq`, ma l'API `/models/<id>/endpoints` di OpenRouter mostra che llama-4-scout è servito
solo da DeepInfra, Novita e Vertex e maverick da DigitalOcean, DeepInfra, Novita, Parasail e
Vertex — Groq non compare per nessuno dei due, quindi con `allow_fallbacks` implicito su un
provider assente la richiesta fallisce. Gli altri otto sono semplicemente indietro di una o
due generazioni, e per quattro di essi il modello nuovo costa uguale o meno.

**Approach:** Ogni target è stato verificato contro `/api/v1/models` (445 modelli, scaricato
il 2026-09-18) prima di essere scritto: presenza dello slug esatto, data di rilascio e
prezzo. Due slug "ovvi" non esistono e sarebbero passati inosservati scrivendoli a mano:
`qwen/qwen3.8-max` (l'id reale è `qwen3.8-max-0902`) e `meta-llama/llama-4-scout:groq`. Gli
alias rotti si dividono: `mistral` viene ripuntato al generalista Mistral più recente
(`mistral-medium-3-5`, apr 2026), mentre `lscout`/`lmav` vengono ritirati — Llama 4 è di
aprile 2025 e nessuno dei due è più competitivo nella fascia in cui veniva usato. Ritirare
un alias significa toglierlo da `_ALIAS_GROUPS` **e** rimuovere la sua voce da
`ALIAS_RENAMES`: quel dict viene splattato dentro `RETIRED_ALIASES`, e l'invariante
`set(ALIAS_RENAMES.values()).issubset(DEFAULT_ALIASES)` andrebbe rossa lasciandolo lì. Le
chiavi vecchie `l4scout`/`l4mav` vanno quindi elencate esplicitamente fra i ritirati.

Scelte con un costo in più, decise dall'utente: `dsf` (il default di `aisk`) passa a
`deepseek-v4.1-flash` a 0.30/1.20 $/M contro 0.089/0.177 del v4-flash; `qwen`, `glm`, `kimi`
e `gel` salgono di prezzo in cambio di modelli più recenti e, per glm/kimi/mm, di un
contesto da 1M+ token contro i 200-260k attuali. `gef` e `cls` costano meno di prima.

**Tasks:**
- [x] Aggiornare gli otto alias superati in `_ALIAS_GROUPS` (`clo`, `cls`, `gef`, `gel`, `dsf`, `qwen`, `mm`, `glm`, `kimi`) e ripuntare `mistral`.
- [x] Ritirare `lscout`/`lmav`: fuori da `_ALIAS_GROUPS`, fuori da `ALIAS_RENAMES`, dentro `RETIRED_ALIASES` insieme a `l4scout`/`l4mav`.
- [x] Portare `gpt`/`gptpro` alla famiglia 5.6: scelto Sol, il flagship della serie secondo le descrizioni di catalogo, perché `gpt`/`gptpro` occupavano già lo slot flagship (5.5 e 5.5-pro). Costa meno di prima: 2/10 contro 5/30 $/M.
- [x] Aggiornare i test: nuovo `test_aliases_sep_2026_refresh`, ridurre i test M22/M24/M28 alle asserzioni ancora vere, test dei due llama ritirati, valori in `test_config.py`.
- [x] Aggiornare gli id di modello citati nel README (esempio `gel`, conf di esempio, riga del default).
- [x] Eseguire `aisk sync` e verificare che `~/.aisk/conf.toml` rifletta i nuovi default mantenendo `[api]`, `[shortcuts]` e gli alias custom.

**Done when:** `uv run pytest -q` è verde a meno dei test pty già noti come flaky in questo
ambiente (vedi M51); nessun alias default punta a uno slug assente dal catalogo OpenRouter;
`aisk sync` riporta i dieci alias aggiornati in `updated` e i due llama in `removed`.

**Execution notes:** Dodici alias aggiornati (`clo`, `cls`, `dsf`, `gef`, `gel`, `glm`, `gpt`,
`gptpro`, `kimi`, `mistral`, `mm`, `qwen`) e due ritirati (`lscout`, `lmav`), come riportato da
`aisk sync`: `[api]`, `[shortcuts]` e la sezione `[defaults]` sono rimasti intatti. Suite:
`234 passed, 2 skipped` — i test pty che M51 segnalava come flaky qui sono passati.

La verifica che conta non è stata la suite ma una chiamata reale per ognuno dei dodici alias
cambiati (`aisk -q <alias> "rispondi con una sola parola: ok"`): tutti e dodici hanno risposto.
Un test unitario confronta due stringhe e resta verde anche se lo slug non esiste più — è
esattamente il modo in cui `mistral` e i due llama sono rimasti rotti senza che nessuno se ne
accorgesse. Due slug plausibili e sbagliati erano già pronti a ripetere la storia:
`qwen/qwen3.8-max` (l'id reale porta il suffisso `-0902`) e `meta-llama/llama-4-scout:groq`.

Nessuna regressione sul prompt caching: `_supports_explicit_cache` decide su `"claude" in m or
"gemini" in m`, quindi `claude-opus-5` e `gemini-3.8-flash` continuano a ricevere il breakpoint
`cache_control` senza toccare la funzione.
