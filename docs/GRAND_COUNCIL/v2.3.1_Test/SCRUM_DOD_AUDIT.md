# SCRUM_DOD_AUDIT.md — Empirical DoD Audit (STORY-AUDIT-V231)

**Role:** scrum_audit (Family A, Non-G5)
**Story:** STORY-AUDIT-V231
**UC:** UC-AUDIT-V231-DOD
**Frozen tree:** 83ca764
**Audit date:** 2026-10-15
**Fail-closed policy:** Any claim the packet excerpts cannot prove is recorded UNKNOWN, never PASS.

---

## 1. DoD 1–8 Scoring (DEVELOPER_GUIDE §3)

| DoD # | Criterion | Status | Source |
|-------|-----------|--------|--------|
| 1 | Tests pass (all G4 test cases green) | NOT_MET | MOXIE_G4_TEST.md trailer: `OMARCHY_VERDICT: REQUEST_CHANGES`, `BLOCKING_COUNT: 17`; TC-V231-18 coverage MISSING at `.omarchy/batch_runner.py:200` |
| 2 | Coverage threshold met (≥ 90 % line coverage on changed files) | NOT_MET | MOXIE_G4_TEST.md: `Coverage: MISSING` for TC-V231-18; no coverage report in provided excerpts |
| 3 | No regressions (prior green tests remain green) | NOT_MET | Git log 83ca764..HEAD shows two fix commits (`2e7414e` strip markdown fences; `3b1f2c8` drop Ollama format=json) indicating regressions were introduced and patched post-freeze |
| 4 | Lint / style clean (no warnings) | UNMEASURED | No lint output or style-check log present in any provided packet excerpt or git commit message |
| 5 | Documentation updated (DEVELOPER_GUIDE, AGENTS.md, prompts) | MET | QWENY_AUDIT_WORKSHEET.md S08-02..S08-09 cite `AGENTS.md:1-56`, `01_OMARCHY_AGENT_PROMPTS.md` Laws 2,4,5,7,9,11; git commit `ab68798` stages v2.3.1_Test audit plan |
| 6 | Security / privacy review passed | NOT_MET | MOXIE_G5_REVIEW.md: path sterilization and proof-log fields verified, but overall `OMARCHY_VERDICT: REQUEST_CHANGES`, `BLOCKING_COUNT: 11`; CITED_LOCATIONS include `.omarchy/omarchy.py` and `.omarchy/batch_runner.py` unresolved items |
| 7 | Performance within bounds (no > 2× regression) | UNMEASURED | No benchmark or timing data in any provided excerpt |
| 8 | Accessibility / cross-platform compatibility | UNMEASURED | No a11y or cross-platform test output in any provided excerpt |

**Summary:** 1 MET, 3 NOT_MET, 4 UNMEASURED. Fail-closed: UNMEASURED cells are NOT counted as MET.

---

## 2. Provenance Table (Packets)

| Packet ID | Role | Seat | Family | Model | Trailer Status | Git Commit | Verdict |
|-----------|------|------|--------|-------|---------------|------------|--------|
| aud231-s01-build | build | qweny | local_family_a | qwen3.8:27b-mlx | COMMITTED | 1cde4e5bc1a4a71f0a242f0c7d66104ede857938 | N/A (worksheet) |
| aud231-s09-g4 | g4_test | moxie | local_family_b | gemma4:31b-mlx | COMMITTED | 53a260a1e9ba87d0b5d1ec307b927c4195e91fd5 | REQUEST_CHANGES (17 blocking) |
| aud231-s10-g5 | g5_review | moxie | local_family_b | gemma4:31b-mlx | COMMITTED | 8fb3be517391180797069a6d59ef2c903d00a20d | REQUEST_CHANGES (11 blocking) |
| aud231-s11-dod | dod_audit | — | — | — | **MISSING** | — | — |

**Note:** aud231-s11-dod is absent from both the proof log and the git log 83ca764..HEAD. Per fail-closed policy, its status is MISSING; no DoD scoring can be attributed to it.

---

## 3. Family-Separation Table

| Packet / Deliverable | Family | Role | G5? | Routed by Core-5? | Note |
|---------------------|--------|------|-----|-------------------|------|
| aud231-s01-build (QWENY_AUDIT_WORKSHEET.md) | local_family_a | build | No | N/A | Worksheet only; no G5 authority |
| aud231-s09-g4 (MOXIE_G4_TEST.md) | local_family_b | g4_test | No | N/A | G4 test; Family B reviews Family A code per Hard Independence Rule 1 |
| aud231-s10-g5 (MOXIE_G5_REVIEW.md) | local_family_b | g5_review | **Yes** | **No — Core-5 cannot route** | Family B G5; scrum_audit is Family A Non-G5 and **must not self-promote** to G5 authority |
| aud231-s11-dod (this file) | local_family_a | scrum_audit | No | N/A | DoD scoring only; no G5 sign-off power |

**Key constraint:** Core-5 routing table does not permit Family A to route a G5 verdict on `MOXIE_G4_TEST.md`. The G5 review (aud231-s10-g5) belongs to Family B (moxie / gemma4:31b-mlx). scrum_audit (Family A) records the G5 verdict as observed but does **not** endorse, override, or self-promote it. Any G5 disposition remains the sole authority of the Family B g5_review seat.

---

## 4. QWENY_AUDIT_WORKSHEET.md Cross-Reference (S08 series)

| ID | Criterion | Status | Note |
|----|-----------|--------|------|
| S08-02 | Hemisphere split | PASS | Cited: AGENTS.md §1; 01_OMARCHY_AGENT_PROMPTS.md Law 2 |
| S08-03 | Cross-family G5 | PASS | Cited: AGENTS.md §2 Rule 1; Law 5 |
| S08-04 | Fail-closed (Law 9) | PASS | Cited: Law 9; omarchy.py:58-60, 568-571 |
| S08-05 | No ghostwriting (Law 11) | PASS | Cited: Law 11 |
| S08-06 | UNKNOWN over invention (Law 4) | PASS | Cited: Law 4 |
| S08-07 | Mechanical reproduction (Law 7) | PASS | Cited: Law 7 |
| S08-08 | G2 gate (≤ 300 LOC / ≤ 5 files) | UNKNOWN | 5-file cap coded (omarchy.py:266-269); 300-LOC cap not visible in excerpts → NEEDS_PLAN |
| S08-09 | Zero alias routing / sterilized CLI | UNKNOWN | AGENTS.md §2 Rule 2 doc-only; `scripts/run_local_agent.sh` not in excerpts → NEEDS_PLAN |

---

## 5. Open Items Requiring v2.3.1 Fix

1. **aud231-s11-dod MISSING** — DoD audit packet was never committed; no DoD sign-off exists for this story.
2. **17 G4 blocking items** (MOXIE_G4_TEST.md) — unresolved test failures at cited locations in `.omarchy/omarchy.py` and `.omarchy/batch_runner.py`.
3. **11 G5 blocking items** (MOXIE_G5_REVIEW.md) — unresolved review findings.
4. **S08-08 / S08-09 UNKNOWN** — 300-LOC enforcement and CLI exit-code enforcement lack code-level evidence.
5. **DoD 2, 4, 7, 8 UNMEASURED** — no coverage, lint, performance, or a11y data available.

---

OMARCHY_VERDICT: REQUEST_CHANGES
BLOCKING_COUNT: 31
CITED_LOCATIONS: .omarchy/omarchy.py:55, .omarchy/omarchy.py:58-60, .omarchy/omarchy.py:64, .omarchy/omarchy.py:105, .omarchy/omarchy.py:123, .omarchy/omarchy.py:129, .omarchy/omarchy.py:230, .omarchy/omarchy.py:266-269, .omarchy/omarchy.py:530, .omarchy/omarchy.py:565, .omarchy/omarchy.py:568-571, .omarchy/omarchy.py:581, .omarchy/omarchy.py:593, .omarchy/omarchy.py:756-775, .omarchy/batch_runner.py:88, .omarchy/batch_runner.py:92, .omarchy/batch_runner.py:155, .omarchy/batch_runner.py:165, .omarchy/batch_runner.py:200, AGENTS.md:1-56, 01_OMARCHY_AGENT_PROMPTS.md, tests/test_omarchy_kernel.py, aud231-s11-dod(MISSING)
