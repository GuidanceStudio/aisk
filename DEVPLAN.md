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
