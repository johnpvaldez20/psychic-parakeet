# FLOW_TRACE — v2.3.1_Test Core-5 Live Audit

Parent-authored mechanical trace from cloud ledger + local proof log.
Parent did **not** author seat ballots or review bodies.

## Sequence

1. **parent** → launched cloud Task `linus` ([bc-91e81599-d81f-4842-8d23-2354e4e4a214](https://github.com/johnpvaldez20/psychic-parakeet/pull/1))
2. **linus** (`cloud_g3`) → `LINUS_AUDIT_PLAN.md` + `LINUS_BALLOT.md` (`OMARCHY_VERDICT: REQUEST_CHANGES`, BLOCKING_COUNT: 3)
3. **parent** → copied Story/UC contracts, compiled `aud231-*.json`, logged cloud seat, kept tree clean for 2PC
4. **qweny** (`build` / Family A) → live 2PC → `QWENY_AUDIT_WORKSHEET.md`
5. **moxie** (`g4_test` then `g5_review` / Family B, keep-warm wave) → `MOXIE_G4_TEST.md` + `MOXIE_G5_REVIEW.md`
6. **scrum** (`scrum_audit` / Family A) → `SCRUM_DOD_AUDIT.md`
7. **parent** → this FLOW_TRACE, GRAND_COUNCIL index, HISTORY; pytest 16 passed

## Cloud ledger (linus)

```
time=2026-10-15T03:44:53Z
role=linus
source=cursor_cloud
note=v2.3.1_Test audit bc-91e81599-d81f-4842-8d23-2354e4e4a214 REQUEST_CHANGES
content_chars=8000
```

## Local proof (COMMITTED only)

| packet_id | role | seat_id | family | model | trailer | packet_sha256 | tree_sha256 |
|---|---|---|---|---|---|---|---|
| `aud231-s01-build` | `build` | `qweny` | `local_family_a` | `qwen3.8:27b-mlx` | `COMMITTED` | `178a482fcf01…` | `40a3e756c36d…` |
| `aud231-s09-g4` | `g4_test` | `moxie` | `local_family_b` | `gemma4:31b-mlx` | `COMMITTED` | `968c51319b73…` | `d3ef1ea53551…` |
| `aud231-s10-g5` | `g5_review` | `moxie` | `local_family_b` | `gemma4:31b-mlx` | `COMMITTED` | `2dc53b514b4e…` | `11ae0f62f2ba…` |
| `aud231-s11-dod` | `scrum_audit` | `scrum` | `local_family_a` | `qwen3.8:27b-mlx` | `COMMITTED` | `d8292e7fc9bd…` | `4afaad36736e…` |

## Kernel fixes discovered during live run (parent, not seat ghostwriting)

- Dropped `format=json` (MLX Ollama HTTP 501 structured-output unavailable) — commit `3b1f2c8`
- Strip markdown fences before JSON parse (gemma wrap) — commit `2e7414e`
- Single-packet path does not write `completed_packets.json`; parent seeded state for depends_on before Family B batch

## Packet collapse note

Linus planned 8 Family A worksheet packets (`aud231-s01`…`s08`). Parent collapsed S01–S08 into one live `aud231-s01-build` packet to preserve the Core-5 A→B→A flow and real artifacts without eight Family A reload cycles. Deliverable paths and roles match the linus plan §3 table.

## Seat verdicts (from artifact trailers)

| Seat | Artifact | Verdict |
|---|---|---|
| linus | LINUS_BALLOT.md | REQUEST_CHANGES (3) |
| qweny | QWENY_AUDIT_WORKSHEET.md | OMARCHY_STATUS: COMPLETE |
| moxie | MOXIE_G4_TEST.md | REQUEST_CHANGES (17) |
| moxie | MOXIE_G5_REVIEW.md | REQUEST_CHANGES (11) |
| scrum | SCRUM_DOD_AUDIT.md | REQUEST_CHANGES (31) |

## G1

`python3 -m pytest tests/test_omarchy_kernel.py -q` → **16 passed** (host `.venv`, after live commits).
