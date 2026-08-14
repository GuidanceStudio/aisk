# Devplan Archive

Closed milestones, compressed to one line each. The sha is the pointer to the
full detail (Why/Approach/Tasks/Deviations) — it already lives in the commit
that shipped the milestone; `git show <sha>` or `git log -S'MNN' -- DEVPLAN.md`
recovers it. Ordered oldest first (newest last).

M1 | Project scaffolding | 2026-03-16 | 45bae9d
M2 | Configuration system (`~/.aisk/`) | 2026-03-16 | b870146
M3 | Model alias resolution | 2026-03-16 | 14dde08
M4 | Streaming HTTP client | 2026-03-16 | beefb16
M5 | Output formatting | 2026-03-16 | dd88e63
M6 | CLI wiring | 2026-03-16 | 423d7f8
M7 | Packaging and distribution | 2026-03-16 | 75cf9a8
M8 | Interactive `aisk init` | 2026-03-16 | 3a75379
M9 | Nuovi alias Perplexity + aggiornamento default | 2026-03-16 | e8ca115
M10 | Shell autocomplete | 2026-03-16 | 32f3293
M11 | Join messaggi senza virgolette | 2026-03-16 | 7c28157
M12 | Auto-init al primo run | 2026-03-16 | fb346e5
M13 | Migliorare `aisk models` | 2026-03-16 | b7a2655
M14 | Aggiornamento README | 2026-03-16 | a7ce580
M15 | Installer lancia il wizard + wizard più smart | 2026-03-17 | 30ffaa8
M16 | Auto-install completions + refresh | 2026-03-17 | 74a79a8
M17 | Allinea alias ad aider+ e fix costi | 2026-03-17 | 17e5a38
M19 | Shell shortcuts da conf.toml | 2026-03-17 | b8c996f
M20 | Timeout idle invece di totale | 2026-03-19 | 8c08894
M21 | Opzione output buffered (`--no-stream`) | 2026-03-19 | 526a21c
M22 | Aggiornamento alias modelli (apr 2026) | 2026-04-24 | 038c443
M23 | Review fix — coerenza e hygiene | 2026-06-02 | 9dd4ed9
M24 | Aggiornamento alias modelli (giugno 2026) | 2026-06-02 | 9dd4ed9
M25 | Migrazione repository a GuidanceStudio | 2026-06-02 | ef94521
M26 | Endpoint generico — qualunque provider OpenAI-compatible | 2026-06-02 | bfe2dff
M27 | Chat interattiva | 2026-06-02 | bfe2dff
M28 | Pulizia default — solo ultima generazione per slot | 2026-06-02 | 2ef6dde
M29 | `aisk sync` — riallinea gli alias del conf.toml ai default | 2026-06-02 | 2ef6dde
M30 | Chat — interrompi il turno + costo cumulativo | 2026-06-02 | 320177c
M31 | Chat — validazione modello immediata (fail-fast) | 2026-06-02 | ed33807
M32 | `--resume` — continua l'ultima conversazione | 2026-06-02 | c5613b4
M33 | Prompt caching sempre attivo (default) | 2026-06-02 | 15db25b
M34 | Code-review follow-ups (D4 + D1) | 2026-06-02 | 42b3e1f
M35 | Chat — cronologia prompt con frecce su/giù | 2026-06-02 | 9276e16
M36 | Fix — prompt chat colorato corrotto con readline (regressione M35) | 2026-06-02 | 1495ecc
M37 | `aisk` → chat diretta + comandi in-chat (`/model`, `/help`, `/search`) | 2026-06-07 | 3371a0d
M38 | Keyboard shortcuts al posto dei comandi slash in-chat | 2026-06-07 | b93018d
M40 | Fix — model selector rendering corrotto alla navigazione | 2026-06-07 | 10eadbb
M41 | Aggiungere installer Windows PowerShell | 2026-06-07 | 640cf07
M42 | Rendere il runtime basic portabile su Windows | 2026-06-07 | 12c77ad
M43 | Aggiungere completions e shortcut PowerShell | 2026-06-07 | 16984a1
M44 | Aggiungere guardrail CI cross-platform | 2026-06-07 | cf33cd2
M45 | Migrare il prompt chat a `prompt_toolkit` | 2026-06-07 | 3baa91a
M46 | Migrare il model selector a `prompt_toolkit` | 2026-06-07 | 7b21855
M47 | Documentazione finale installer e Windows | 2026-06-07 | 1fdb8dd
M48 | Fix UI chat — Enter invia, footer visibile, banner senza search | 2026-06-15 | 61040dc
M49 | Aggiornare alias `dsp` a DeepSeek V4 Pro 0813 (GA) | 2026-08-13 | c8a6bbc
M50 | Devplan bookkeeping — chiudere M40-M48, rimuovere i commenti di test che ripetono l'assert | 2026-08-14 | 898203a
