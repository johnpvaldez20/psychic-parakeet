# LINUS_BALLOT — `G3` Structural Review of Omarchy Scrum v2.3 (Lean Core-5 + Packet Role)

Author: linus · cloud run bc-91e81599-d81f-4842-8d23-2354e4e4a214 · 2026-10-15

| Field | Value |
|---|---|
| Seat / Gate | `linus` · `G3` (Chief Architect) |
| Model binding | `agents.lock` row `linus`; the cloud runtime reported the same slug for this run |
| Target | `83ca764` (tag `v2.3`). Cloud branch `cursor/linus-v2-3-1-audit-a214` |
| Companion plan | [`LINUS_AUDIT_PLAN.md`](LINUS_AUDIT_PLAN.md). Local packets must not be fed this ballot |

## 0. What I observed versus what I am asserting

Observed in this cloud VM:

| Check | Result |
|---|---|
| `python3 -m pytest -q tests/` | `16 passed` |
| `scripts/run_local_agent.sh --batch --dry-run` | Printed the documented A→B→A three-wave plan |
| Single-packet `--dry-run` on `_sample_packet.json` | Wrote a `DRY_RUN` proof row |
| Throwaway `cloud_g3` packet (created, run, deleted) | See finding N1 |

None of the observations above is `G1`. The Testing Jig belongs to `parent` on a clean host (Law 7). Every RAM or latency figure in this ballot is `UNMEASURED`.

Everything below is a structural reading of the code at `83ca764`. Line numbers refer to that tree.

## 1. The verdict in one paragraph

The shape of v2.3 is good. One lock, roles instead of model slugs in packets, a 2PC worktree, a scheduler that respects causality, and a kernel that fails closed on invented slugs. That is the right kernel for this job, and trimming the default roster to Core-5 was correct. But v2.3 says three things the code does not do:

1. Law 5 promises cross-family review in **both** directions. Only one direction is routable.
2. The gates say verdicts and trailers are recorded. The kernel never parses one.
3. The lock says only one model may reside in RAM. Nothing checks it.

Those are contract lies, not style nits. Fix them, then ship v2.3.1.

---

## 2. Blocking findings

### B1 — Law 5's reverse direction cannot be routed, and `moxie` holds both the test-author and reviewer roles

- `ROLE_TO_SEAT` sends `g5_review` **and** `g4_test` to `moxie` (`.omarchy/omarchy.py:47-48`). No role maps a Family A seat to `G5`.
- The constitution demands the reverse direction: "Test / `g4_test` artifacts authored by Family B (`moxie`) **must** be peer-reviewed by Family A (`qweny`)" (`AGENTS.md:45`), and "and vice versa" (`01_OMARCHY_AGENT_PROMPTS.md:22`).
- Under Core-5, the only Family A seats are `qweny` and `scrum`. A `build` packet is a builder, not a reviewer, and `scrum` is "never `G5`" (`AGENTS.md:32`). So every `g4_test` landing ships without a legal `G5`.
- `01_OMARCHY_AGENT_PROMPTS.md:42` still routes the reverse review through "`qweny` on `mitnick` tests", but `mitnick` is no longer in the lock. Both trailer tables also still name `mitnick` (`01_OMARCHY_AGENT_PROMPTS.md:50`, `:59`).
- The demo corpus already conflates the two `moxie` roles. `pkt-02-audit` declares `"role": "g5_review"` (`.omarchy/packets/pkt-02-audit.json:6`), but its instructions say "expand tests in tests/demo/test_core_module.py" (`.omarchy/packets/pkt-02-audit.json:13`). That is `g4_test` work under a review label. The tests it writes are Family B code that no Family A seat ever reviews.
- **Required fix (small):**
  - Add a role `g5_review_a → qweny`.
  - Require every `g5_review*` packet to declare `"reviews": [<packet_id>, ...]`.
  - Have `load_packet` resolve each reviewed packet's family (from its packet file or its proof row) and fail closed when reviewer family == author family.
  - Relabel `pkt-02-audit` as `g4_test`.
  - Update `01_OMARCHY_AGENT_PROMPTS.md:42,50,59`, `AGENTS.md:31,45`, `.omarchy/packets/README.md:7-13`, and `docs/SPRINT_DASHBOARD.md:65`.
  - Cost is roughly 30–40 LOC in the kernel plus 4 tests: accept, same-family reject, unknown `reviews` id reject, and missing `reviews` reject.

### B2 — Gate verdicts and trailers are never captured, so `G0`/`G5` are not mechanically checkable

- The output contract the model receives is `{"files": {...}}` only (`.omarchy/omarchy.py:524-528`, `:659-662`). No `OMARCHY_STATUS` or `OMARCHY_VERDICT` trailer is requested, parsed, or validated anywhere in the kernel.
- `trailer_status` sounds like the agent's trailer, but it is a kernel constant: `"DRY_RUN"` (`.omarchy/omarchy.py:771`) or `"COMMITTED"` (`.omarchy/omarchy.py:820`). Law 6 presents it as proof (`01_OMARCHY_AGENT_PROMPTS.md:23`).
- `G0` requires a match on `output_sha256` (`01_OMARCHY_AGENT_PROMPTS.md:37`), and so do DoD item 2 (`docs/DEVELOPER_GUIDE.md:51`) and the dashboard proof anchors (`docs/SPRINT_DASHBOARD.md:66`). The kernel computes no such field. The raw model response is never hashed, and only the post-apply diff is (`.omarchy/omarchy.py:423`). `scrum` therefore cannot pass DoD item 2 by construction.
- The dashboard's mechanical loop still parses the v2.0 protocol, `=== FILE: … ===` + `OMARCHY_STATUS` (`docs/SPRINT_DASHBOARD.md:70`). That protocol was retired when the kernel moved to `.omarchy/` (`docs/HISTORY.md:8-9`).
- `G5`/`G3` "must emit `OMARCHY_VERDICT: APPROVE`" (`01_OMARCHY_AGENT_PROMPTS.md:40,42`). A `g5_review` packet's verdict exists only as prose inside a markdown file the model wrote, and nothing reads it.
- **Required fix:**
  - Hash `body["response"]` as `output_sha256` and log it.
  - Rename the kernel field to `kernel_status`.
  - For `g5_review*`/`g4_test`/`scrum_audit` roles, require the single target `.md` to end with a §3.2 trailer, and parse it into `verdict=` / `blocking_count=` in the proof row. Fail closed when it is absent or malformed.
  - For `build`, parse the §3.1 trailer if present, or drop it from the law. Pick one; do not keep both stories.
  - Sync `docs/DEVELOPER_GUIDE.md:51` and `docs/SPRINT_DASHBOARD.md:66,70`.

### B3 — "Only one model in RAM" is asserted but never verified

- The lock states the invariant (`agents.lock:10`). The pre-load guard checks one model's on-disk size against a single-model ceiling (`.omarchy/omarchy.py:547-599`). It never asks Ollama what is **already resident** (no `/api/ps` call anywhere).
- Single-packet `--keep-warm` (`.omarchy/omarchy.py:864-867`) sends `keep_alive: "15m"` (`.omarchy/omarchy.py:625`), and no code path ever evicts it. The `finally` eviction exists only in the batch runner (`.omarchy/batch_runner.py:313-317`). A single-packet keep-warm run followed by an opposite-family packet puts both families in RAM, and the budget guard says "OK".
- A `SIGKILL` or OOM kill mid-wave skips `finally`. The model then stays resident for 15 minutes, and the next run loads on top of it, again unchecked.
- `evict_model` raises inside `finally` (`.omarchy/batch_runner.py:73`, called at `:317`). When a packet fails and eviction also fails, the operator sees `Failed to evict…`. The 2PC gate failure that actually happened is demoted to `__context__`. Law 9 forbids hiding the real cause.
- **Required fix:**
  - Before every load, query `/api/ps`. If any model other than the target is resident, evict it and re-query. If it is still resident, fail closed.
  - Remove `--keep-warm` from the single-packet CLI; keep-warm is the scheduler's business.
  - In `finally`, catch eviction errors, log them to stderr, and re-raise the original exception. When there was none, raise the eviction error.

---

## 3. Non-blocking findings (fix in v2.3.1, no re-ballot needed)

### N1 — `cloud_g3` leaks across the hemisphere boundary (verified)

`cloud_g3 → linus` lives in the local kernel's role table (`.omarchy/omarchy.py:50`). As a result:

- A single-packet `--dry-run` of a `cloud_g3` packet appends `seat_id=linus` and `model=<linus lock slug>` to `.omarchy/local-agent-proof.log` (`.omarchy/omarchy.py:744-775`). That is the file AGENTS.md treats as **local Ollama** proof (`AGENTS.md:15`).
- The same packet sitting in `.omarchy/packets/` kills every `--batch` run, including `--dry-run`. The error message, "Packet missing locked family for wave key", is misleading (`.omarchy/batch_runner.py:110-111` → `.omarchy/omarchy.py:723-726`). This contradicts the "dry-run only on local kernel" claim (`.omarchy/packets/README.md:13`).
- The live path does refuse correctly (`.omarchy/omarchy.py:778-784`).

Fix: delete `cloud_g3` from `ROLE_TO_SEAT`. Cloud proof is `scripts/log_cloud_agent.sh` plus a run ID, and the kernel should never see cloud seats. `load_packet` should reject `runtime != "local"` up front.

### N2 — Resume state is keyed by `packet_id`, not content

`record_completed_id` stores ids only (`.omarchy/batch_runner.py:85-90`). `discover_pending_packets` skips any id it has seen (`.omarchy/batch_runner.py:117`). If someone edits a packet's instructions or gates and keeps the id, the new version is silently never run.

Fix: store `{packet_id: packet_sha256}`. On a hash mismatch, fail closed or re-run; never skip.

### N3 — Proof is not durable, and failures leave no trace

The proof log is gitignored (`.gitignore:4`). The 2PC commit message carries only story, UC, and packet id (`.omarchy/omarchy.py:425-427`). Proof is appended only after a successful merge (`.omarchy/omarchy.py:806-823`), so an aborted 2PC writes nothing.

`scrum` "verifies against Git" (`docs/DEVELOPER_GUIDE.md:48`) but cannot see either `packet_sha256` or failures. Law 11 `SEAT_FAILED` is never machine-recorded.

Fix: add `Omarchy-Packet-Sha256:` / `Omarchy-Role:` / `Omarchy-Seat:` / `Omarchy-Tree-Sha256:` trailers to the 2PC commit, and append an `ABORTED` proof row on the exception path.

### N4 — 2PC preconditions are checked after the expensive step

The wrong-branch and dirty-tree checks run after the model call and the gates (`.omarchy/omarchy.py:436-460`). A full model run can be thrown away over a precondition that was knowable at `__enter__`.

Fix: check in `__enter__` and again before `merge --ff-only` (`.omarchy/omarchy.py:463-469`). The window between those two checks remains, but it shrinks to milliseconds.

### N5 — The memory-budget alias match can coalesce sizes; the constants are unmeasured

`model.startswith(f"{name}:")` (`.omarchy/omarchy.py:572`) lets an untagged or base entry from `/api/tags` supply the weight size for a tagged slug. That is the size-coalescing the kernel itself forbids (`.omarchy/omarchy.py:38-39`, `agents.lock:12`).

`105 GiB` and `512 KiB/token` (`.omarchy/omarchy.py:541-544`) have no row in `docs/EVIDENCE.md`. Per Law 10 they must be labelled `UNMEASURED` estimates.

Fix: match the exact slug or `slug:latest` only, and add the `UNMEASURED` row.

### N6 — Dead and duplicated control paths

- `resolve_packet_model` and its legacy family-only path are unreachable from `load_packet`/`execute_packet`; only tests call them (`.omarchy/omarchy.py:169-208`).
- `run_queue(strict_fifo=…)` is never wired to the CLI (`.omarchy/omarchy.py:836-842`).
- `--stop-on-failure` is `store_true` with `default=True`, so it can never change anything (`.omarchy/batch_runner.py:246-251`).
- There are two dry-run implementations, and they have drifted. The batch dry-run (`.omarchy/batch_runner.py:207-218`) writes **no** proof row and omits role/seat. The single dry-run (`.omarchy/omarchy.py:744-775`) does both.
- The budget is checked twice per live packet (`.omarchy/omarchy.py:787` and `:619`).

Fix: delete what is dead, and have batch dry-run call `execute_packet(dry_run=True)`.

### N7 — The lock parser silently tolerates corruption

Rows with fewer than 6 fields are skipped (`.omarchy/omarchy.py:69-70`), and duplicate seat ids overwrite each other (`.omarchy/omarchy.py:71`). `schema=2` is never checked.

The downstream "missing seat" error usually catches this, but a duplicated `moxie` row with a different slug would win silently if it appeared last. Law 9 says fail at the parse.

### N8 — The tests contradict their own docstring and block the documented optional-pack flow

The module promises "fixtures use only agents.lock" (`tests/test_omarchy_kernel.py:1-5`), yet `:46-47`, `:181`, and `:207` hardcode slugs, so a lock cook-off breaks `G1`. Separately, `:50-54` asserts that the seat set is exactly Core-5. Following `AGENTS.md:40` (copying an optional row into the lock) therefore fails the suite.

Missing tests for headline guarantees:

- `finally` eviction on a mid-wave abort, which is *the* `batch_runner` promise (`AGENTS.md:55`)
- unauthorized-write rejection (`.omarchy/omarchy.py:692-704`)
- worktree and branch cleanup on abort (`.omarchy/omarchy.py:489-497`)
- the `load_packet` schema, missing `role`, and the 5-file `G2` cap (`.omarchy/omarchy.py:250-275`)
- live `cloud_g3` refusal
- budget fail-closed

Step 9 of the plan turns this list into `TC-V231-*` cases.

### N9 — Pre-v2.3 roster drift in always-applied and entry docs

- `.cursor/rules/omarchy-council.mdc:2,6,10-12` is always applied to every agent. It still describes the v2.0 roster (`mitnick`/`jobs` as Local Council, four cloud seats).
- Other stale roster references: `README.md:1,5,24,53,60,71`, `docs/GRAND_COUNCIL.md:5`, `01_OMARCHY_AGENT_PROMPTS.md:75,80`.
- Rule 16 requires all four cloud seats plus `mitnick` (`01_OMARCHY_AGENT_PROMPTS.md:80`). `scripts/log_cloud_agent.sh:15-19` rejects any seat not in the lock, so Rule 16 cannot be satisfied on the default Core-5 lock. The usage text at `scripts/log_cloud_agent.sh:9` still lists `dhh|carmack|knuth`.
- `docs/SPRINT_DASHBOARD.md:14` says "2.0", and `:43` cites `sample_packet.json`, but the file is `_sample_packet.json`.

The `.mdc` rule is the highest-leverage fix of the set, because it overrides what every agent reads first.

### N10 — Same-family dependency chains are never kept warm

Any `depends_on` edge or shared target between two same-family packets puts them in separate waves. Each wave ends in `evict_model`, so the next wave reloads the same model (`.omarchy/batch_runner.py:146-151,182-187`).

This is correct for safety, but it means the common case (a builder making sequential edits to one file) pays a full reload per packet. Cost is `UNMEASURED`. This audit's own plan pays 8 Family A reloads (`LINUS_AUDIT_PLAN.md` §5).

Fix (optional): when consecutive waves share a family, skip the inter-wave eviction and evict at the family boundary only.

### N11 — `G2` is half-enforced

The 5-file cap is in code (`.omarchy/omarchy.py:272-275`). The ≤ 300 LOC budget and the Law 8 dependency check (`01_OMARCHY_AGENT_PROMPTS.md:25,39`) are not. Either add a `git diff --cached --numstat` LOC gate in `commit_transaction`, or mark `G2` LOC as `parent`-manual in the gate table.

---

## 4. What is right (keep it)

- **Lock SSOT for slugs.** Packets cannot invent or downsize a model (`.omarchy/omarchy.py:116-122`, `:153-165`, `:613-618`), and tests pin this behaviour (`tests/test_omarchy_kernel.py:103-124`).
- **Path sterilization.** Packet paths, worktree targets, and write paths are all contained (`.omarchy/omarchy.py:215-232`, `:512-519`, `:698-704`).
- **Argv-only gates.** There is no shell interpolation (`.omarchy/omarchy.py:321-333`).
- **The causal scheduler.** Write-order locks plus deadlock detection (`.omarchy/batch_runner.py:142-157`) are the right primitive, and the A→B→A test is the right test (`tests/test_omarchy_kernel.py:65-80`).
- **Live `cloud_g3` refusal.** The live path refuses with an actionable message (`.omarchy/omarchy.py:778-784`).

## 5. Conditions for v2.3.1 `APPROVE`

1. B1, B2, and B3 land as three separate `build` slices, each ≤ 5 files and ≤ 300 LOC. Each gets a Family B `g5_review`, plus a Family A `g5_review_a` on any `g4_test` tests.
2. `G1` is green on the host and recorded in `docs/TESTING_JIG_REPORT.md`.
3. N1 and N9 (`.mdc` rule plus `01_OMARCHY_AGENT_PROMPTS.md`) land in the same release. The rest can trail.
4. The four local deliverables from `LINUS_AUDIT_PLAN.md` exist. linus reads them before re-balloting, and any finding they raise that this ballot missed counts against this ballot.

---
OMARCHY_VERDICT: REQUEST_CHANGES
BLOCKING_COUNT: 3
CITED_LOCATIONS: .omarchy/omarchy.py:47, .omarchy/omarchy.py:48, AGENTS.md:45, 01_OMARCHY_AGENT_PROMPTS.md:22, 01_OMARCHY_AGENT_PROMPTS.md:42, .omarchy/packets/pkt-02-audit.json:6, .omarchy/packets/pkt-02-audit.json:13, .omarchy/omarchy.py:524, .omarchy/omarchy.py:659, .omarchy/omarchy.py:771, .omarchy/omarchy.py:820, 01_OMARCHY_AGENT_PROMPTS.md:23, 01_OMARCHY_AGENT_PROMPTS.md:37, docs/DEVELOPER_GUIDE.md:51, docs/SPRINT_DASHBOARD.md:66, docs/SPRINT_DASHBOARD.md:70, agents.lock:10, .omarchy/omarchy.py:547, .omarchy/omarchy.py:625, .omarchy/omarchy.py:864, .omarchy/batch_runner.py:73, .omarchy/batch_runner.py:317, .omarchy/omarchy.py:50, .omarchy/omarchy.py:744, .omarchy/omarchy.py:723, .omarchy/batch_runner.py:117, .gitignore:4, .omarchy/omarchy.py:425, .omarchy/omarchy.py:436, .omarchy/omarchy.py:572, .omarchy/omarchy.py:541, .omarchy/omarchy.py:169, .omarchy/batch_runner.py:249, .omarchy/batch_runner.py:207, .omarchy/omarchy.py:69, tests/test_omarchy_kernel.py:46, tests/test_omarchy_kernel.py:52, .cursor/rules/omarchy-council.mdc:11, 01_OMARCHY_AGENT_PROMPTS.md:80, scripts/log_cloud_agent.sh:15, .omarchy/batch_runner.py:182, .omarchy/omarchy.py:272
---
