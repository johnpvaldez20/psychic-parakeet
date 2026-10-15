# LINUS_AUDIT_PLAN — Omarchy Scrum v2.3 Whole-Repository Audit (`v2.3.1_Test`)

Author: linus · cloud run bc-91e81599-d81f-4842-8d23-2354e4e4a214 · 2026-10-15

| Field | Value |
|---|---|
| Seat / Gate | `linus` · `G3` structural planner (Rule 11 packet *plans* only; no code) |
| Model binding | `agents.lock` row `linus` (resolved by the cloud runtime; not restated here) |
| Cloud branch | `cursor/linus-v2-3-1-audit-a214` |
| Frozen audit target | `83ca764` (`v2.3` tag → "feat: Omarchy Scrum 2.3 lean Core-5 seats + packet role") |
| Output directory | `docs/GRAND_COUNCIL/v2.3.1_Test/` (every local deliverable lands here, nowhere else) |
| Companion ballot | [`LINUS_BALLOT.md`](LINUS_BALLOT.md) — **must NOT be inlined into any local packet** (Rule 16 independence: zero shared context) |

---

## 1. Scope

The whole v2.3 control plane, frozen at `83ca764`:

| Surface | Paths |
|---|---|
| Kernel (role binding, lock parse, 2PC, memory budget, Ollama serialize, proof log) | `.omarchy/omarchy.py` |
| Scheduler (causal waves, file write-locks, `finally` eviction, resume state) | `.omarchy/batch_runner.py` |
| Seat lock (Core-5 + optional pack) | `agents.lock`, `agents.lock.optional` |
| Packet corpus (role fields) + contracts | `.omarchy/packets/*.json`, `.omarchy/packets/README.md`, `.omarchy/contracts/**` |
| Constitution & roster docs | `AGENTS.md`, `01_OMARCHY_AGENT_PROMPTS.md`, `docs/HISTORY.md`, `docs/DEVELOPER_GUIDE.md`, `docs/SPRINT_DASHBOARD.md`, `README.md`, `.cursor/rules/omarchy-council.mdc`, `docs/GRAND_COUNCIL.md` |
| Thin invokers | `scripts/run_local_agent.sh`, `scripts/ensure_local_agents.sh`, `scripts/log_cloud_agent.sh` |
| Kernel tests | `tests/test_omarchy_kernel.py` |
| Gates & hemisphere honesty | `G0`–`G5` as defined in `01_OMARCHY_AGENT_PROMPTS.md` §2 vs. what the code mechanically enforces |

Out of scope: `app/**`, `src/**` (none exist at `83ca764`), `docs/OMARCHY_SCRUM_2_0_BLUEPRINT.md` (historical).

---

## 2. Preconditions for `parent` (mechanical; not numbered audit steps)

These are orchestrator chores. They are not seat work and carry no role.

1. **Branch.** Check out the branch carrying this plan with a clean tree. Use that branch name as every packet's `base_branch`. The 2PC merge refuses any other branch and any dirty tree (`.omarchy/omarchy.py:436-460`).
2. **Contracts.** Materialize the Story/UC files below verbatim under `.omarchy/contracts/` (required by `verify_story_and_uc`, `.omarchy/omarchy.py:293-313`). linus authors their text here, so `parent` is copying it, not ghostwriting.
3. **Excerpts.** Local models get no view of the repository (Law 3). For each step, `parent` inlines the listed excerpts into `instructions` as fenced blocks. Each block is headed `path:start-end @83ca764 sha256=<sha256 of the full file at 83ca764>`. Excerpts must come from `git show 83ca764:<path>`, not from the working tree.
4. **Never list an audited source file in `target_files`.** The kernel lets the model overwrite any file listed there (`apply_agent_changes`, `.omarchy/omarchy.py:686-709`). Each packet's `target_files` is **exactly one** `.md` file under `docs/GRAND_COUNCIL/v2.3.1_Test/`.
5. **Explicit queue.** Run `scripts/run_local_agent.sh --batch .omarchy/packets/aud231-*.json`, never bare `--batch`. Bare `--batch` also picks up the demo `pkt-0*` packets (`.omarchy/batch_runner.py:100-105`). Dry-run first with `--dry-run`.
6. **No `cloud_g3` packet in `.omarchy/packets/` during the run.** A single one aborts the whole batch inside `wave_key` (`.omarchy/omarchy.py:723-726`). linus's work is this cloud Task, not a packet.
7. **Proof hand-off.** `.omarchy/local-agent-proof.log` is gitignored (`.gitignore:4`). Before step 11, `parent` inlines into the `scrum_audit` packet the proof-log blocks for `aud231-*` and the `git log --format='%H %s' 83ca764..HEAD` output.
8. **Cloud ledger.** On the host, `parent` runs `scripts/log_cloud_agent.sh linus "v2.3.1_Test plan+ballot · bc-91e81599-d81f-4842-8d23-2354e4e4a214"`.

### 2.1 Contract text (copy verbatim)

`.omarchy/contracts/stories/STORY-AUDIT-V231.md`

```markdown
# STORY-AUDIT-V231 — Whole-repository audit of Omarchy Scrum v2.3 (frozen 83ca764)
As the Grand Council, I want every v2.3 control-plane claim checked against the code at 83ca764,
so that v2.3.1 fixes are driven by cited evidence, not by prose.
Fail-closed: any claim the packet excerpts cannot prove is recorded UNKNOWN, never PASS.
```

`.omarchy/contracts/use_cases/UC-AUDIT-V231-WS.md`

```markdown
# UC-AUDIT-V231-WS — Builder worksheet (role build → qweny, Family A)
Given inlined excerpts of the frozen tree, When a numbered step runs,
Then QWENY_AUDIT_WORKSHEET.md gains exactly that step's section, every row cites path:line @83ca764,
and the file ends with one OMARCHY_STATUS trailer (01_OMARCHY_AGENT_PROMPTS.md §3.1).
Negative: a symbol or line not present in the excerpts → row Result = UNKNOWN + NEEDS_PLAN note.
```

`.omarchy/contracts/use_cases/UC-AUDIT-V231-G4.md`

```markdown
# UC-AUDIT-V231-G4 — Adversarial fail-closed test design (role g4_test → moxie, Family B)
Given the kernel/scheduler excerpts and the test-file excerpt, When g4_test runs,
Then MOXIE_G4_TEST.md lists TC-cases (DEVELOPER_GUIDE §4.2 template) each tagged EXISTING:<test_fn> or MISSING,
and ends with one OMARCHY_VERDICT trailer. No file under tests/ is written.
```

`.omarchy/contracts/use_cases/UC-AUDIT-V231-G5.md`

```markdown
# UC-AUDIT-V231-G5 — Cross-family peer review of the Family A worksheet (role g5_review → moxie, Family B)
Given the final QWENY_AUDIT_WORKSHEET.md and its cited excerpts, When g5_review runs,
Then MOXIE_G5_REVIEW.md re-checks every FAIL/UNKNOWN row and a sample of PASS rows,
and ends with one OMARCHY_VERDICT trailer. It never reviews MOXIE_G4_TEST.md (same-family self-grading).
```

`.omarchy/contracts/use_cases/UC-AUDIT-V231-DOD.md`

```markdown
# UC-AUDIT-V231-DOD — Empirical DoD audit (role scrum_audit → scrum, Family A)
Given the four local deliverables, the aud231-* proof-log blocks and the git log, When scrum_audit runs,
Then SCRUM_DOD_AUDIT.md scores DEVELOPER_GUIDE §3 DoD 1–8 for this audit with a cited source per cell
(UNMEASURED where no source exists), and ends with one OMARCHY_VERDICT trailer.
```

---

## 3. Deliverables (local seats; linus writes none of them)

| File | Role | Seat (via `ROLE_TO_SEAT`, `.omarchy/omarchy.py:45-51`) | Family | Trailer |
|---|---|---|---|---|
| `docs/GRAND_COUNCIL/v2.3.1_Test/QWENY_AUDIT_WORKSHEET.md` | `build` | `qweny` | `local_family_a` | `OMARCHY_STATUS` (§3.1) |
| `docs/GRAND_COUNCIL/v2.3.1_Test/MOXIE_G4_TEST.md` | `g4_test` | `moxie` | `local_family_b` | `OMARCHY_VERDICT` (§3.2) |
| `docs/GRAND_COUNCIL/v2.3.1_Test/MOXIE_G5_REVIEW.md` | `g5_review` | `moxie` | `local_family_b` | `OMARCHY_VERDICT` (§3.2) |
| `docs/GRAND_COUNCIL/v2.3.1_Test/SCRUM_DOD_AUDIT.md` | `scrum_audit` | `scrum` | `local_family_a` | `OMARCHY_VERDICT` (§3.2) |

### 3.1 Worksheet row schema (steps 1–8)

Every section of `QWENY_AUDIT_WORKSHEET.md` is one table with exactly these columns:

```text
| Check | Claim under test (source path:line @83ca764) | Code evidence (path:line @83ca764) | Result | Note |
```

`Result` ∈ `PASS` · `FAIL` · `UNKNOWN`. A `PASS` without a code-evidence citation is invalid, and step 10 must flag it. The model reports what the excerpts show. It does not propose fixes; a fix is a planning act and belongs to linus.

---

## 4. Numbered Audit Steps

Every step lists its **role**, a packet skeleton, the excerpts to inline, the checks to run, and acceptance gates. Gates are argv lists, as `run_deterministic_gates` requires (`.omarchy/omarchy.py:316-339`).

The checks below are phrased as neutral questions. Do not rewrite them into conclusions, and do not copy in findings from `LINUS_BALLOT.md`.

Common packet fields for steps 1–8:

```json
{
  "story_id": "STORY-AUDIT-V231",
  "uc_ids": ["UC-AUDIT-V231-WS"],
  "role": "build",
  "family": "local_family_a",
  "num_ctx": 32768,
  "base_branch": "<branch carrying this plan>",
  "target_files": ["docs/GRAND_COUNCIL/v2.3.1_Test/QWENY_AUDIT_WORKSHEET.md"]
}
```

Common gates for steps 1–8 (`$W` = `docs/GRAND_COUNCIL/v2.3.1_Test/QWENY_AUDIT_WORKSHEET.md`):

```json
[["grep", "-Eq", "^## S0N — ", "$W"],
 ["grep", "-Eq", "^OMARCHY_STATUS: (READY|NEEDS_PLAN|UNKNOWN)$", "$W"],
 ["grep", "-Eq", "^MISSING_SYMBOLS: ", "$W"]]
```

(`S0N` is the step's own header, e.g. `^## S03 — `. From step 2 onward, also re-grep every earlier header so a rewrite cannot drop a prior section.)

---

### Step 1 — Lock parse & role→seat→family binding · **role: `build`**

- **packet_id:** `aud231-s01-lock-binding` · `depends_on: []`
- **Section header:** `## S01 — Lock & Role Binding`
- **Inline:** `agents.lock` (all), `agents.lock.optional` (all), `.omarchy/omarchy.py:37-208`, `.omarchy/omarchy.py:236-291`, `scripts/ensure_local_agents.sh:29-48`.
- **Checks (minimum IDs):**
  - `S01-01` Does `ROLE_TO_SEAT` map each of `build|g5_review|g4_test|scrum_audit|cloud_g3` to a seat present in `agents.lock`?
  - `S01-02` Does `load_packet` reject a packet with no `role`, or with an unknown `role`?
  - `S01-03` Does a packet `family` or `model` that disagrees with the lock row fail closed?
  - `S01-04` Does `locked_local_family_models` fail closed when a family is missing, when a family binds two slugs, or when A == B?
  - `S01-05` How does `parse_agents_lock` handle a row with fewer than 6 fields, or a duplicate seat id: fail closed or silently?
  - `S01-06` Is `resolve_packet_model` (legacy family-only path) reachable from `load_packet` / `execute_packet`? List its callers.
  - `S01-07` Is the `schema=2` header line validated anywhere?
  - `S01-08` Is every optional-seat row in `agents.lock.optional` absent from `agents.lock`, and does the kernel ever read `agents.lock.optional`?
  - `S01-09` Does `ensure_local_agents.sh` derive its pull list from the same lock rows the kernel binds?
- **Acceptance:** at least 9 rows. Every row has a code-evidence `path:line`. Common gates are green.

### Step 2 — 2PC worktree transaction & G0 proof log · **role: `build`**

- **packet_id:** `aud231-s02-2pc` · `depends_on: ["aud231-s01-lock-binding"]`
- **Section header:** `## S02 — 2PC Transaction & Proof Log`
- **Inline:** `.omarchy/omarchy.py:215-232`, `.omarchy/omarchy.py:316-353`, `.omarchy/omarchy.py:359-497`, `.omarchy/omarchy.py:504-538`, `.omarchy/omarchy.py:686-709`, `.omarchy/omarchy.py:729-825`, `.gitignore`.
- **Checks:**
  - `S02-01` Phase 1: is the worktree created from `base_branch` on a dedicated `omarchy/tx-*` branch?
  - `S02-02` Is a zero-change result rejected?
  - `S02-03` At what point are the base-branch and clean-tree checks made: before or after the model call? Is there a window between the check and `merge --ff-only`?
  - `S02-04` On any exception, is the worktree removed and the tx branch deleted? On success?
  - `S02-05` Does `apply_agent_changes` reject writes outside `target_files` and outside the worktree?
  - `S02-06` Which fields does the proof log record, on which paths (dry-run / committed / aborted)? Is anything recorded on abort?
  - `S02-07` Is `trailer_status` taken from the agent output, or set by the kernel?
  - `S02-08` Is the raw model response hashed anywhere (an `output_sha256`)?
  - `S02-09` Is the proof log committed to git? Does the 2PC commit message carry `packet_sha256`, `role`, or `seat_id`?
  - `S02-10` Do `verification_commands` run inside the worktree, with argv-only (no shell) execution?
- **Acceptance:** at least 10 rows, and S01 + S02 headers present.

### Step 3 — Memory budget & single-model residency · **role: `build`**

- **packet_id:** `aud231-s03-memory` · `depends_on: ["aud231-s02-2pc"]`
- **Section header:** `## S03 — Memory Budget & Residency`
- **Inline:** `agents.lock:6-13`, `.omarchy/omarchy.py:540-683`, `.omarchy/omarchy.py:785-799`, `.omarchy/omarchy.py:848-873`, `docs/EVIDENCE.md`.
- **Checks:**
  - `S03-01` What inputs does `enforce_memory_budget` sum (weights, ctx, runner headroom)? Is the result compared against a single-model ceiling?
  - `S03-02` Does any code query which models are *currently resident* (e.g. Ollama `/api/ps`) before loading?
  - `S03-03` Can the alias match in the `/api/tags` loop (`.omarchy/omarchy.py:572`) bind a size-variant or untagged entry to the locked slug?
  - `S03-04` Are `105 GiB` and `512 KiB/token` backed by a measured row in `docs/EVIDENCE.md`? If not, they are `UNMEASURED` (Law 10).
  - `S03-05` Single-packet `--keep-warm`: which `keep_alive` value is sent, and which code path evicts that model afterwards?
  - `S03-06` Does `invoke_ollama_serial` refuse any slug not in the two locked families?
  - `S03-07` Is the budget check executed once or more than once per live packet?
- **Acceptance:** at least 7 rows. Any numeric RAM figure is either cited to `docs/EVIDENCE.md` or written as `UNMEASURED`.

### Step 4 — Causal waves, write-locks, `finally` eviction, resume · **role: `build`**

- **packet_id:** `aud231-s04-batch` · `depends_on: ["aud231-s03-memory"]`
- **Section header:** `## S04 — Batch Runner`
- **Inline:** `.omarchy/batch_runner.py` (all), `.omarchy/omarchy.py:716-726`, `.omarchy/omarchy.py:836-842`.
- **Checks:**
  - `S04-01` Does `plan_serial_family_waves` honour `depends_on`, and detect cycles or unknown deps?
  - `S04-02` Does the write-lock prevent two packets sharing a target from landing in one wave?
  - `S04-03` Are two same-family packets linked by `depends_on` (or by a shared file) placed in the same wave or in separate waves? How many evict/reload cycles does that cost?
  - `S04-04` Does the `finally` block evict on both success and failure? If `evict_model` raises inside `finally`, which exception reaches the operator?
  - `S04-05` Is the last packet of a wave unloaded twice (`keep_alive: 0`, then `evict_model`)? Is that harmful?
  - `S04-06` What key does resume state use (`completed_packets.json`)? Does editing a packet without changing its `packet_id` re-run it?
  - `S04-07` Does batch dry-run go through the same code path as single-packet dry-run? Do both write a proof row?
  - `S04-08` Is `--stop-on-failure` able to change behaviour? Is `run_queue(strict_fifo=...)` reachable from the CLI?
  - `S04-09` What happens to a batch when a `cloud_g3` packet is present in the queue?
- **Acceptance:** at least 9 rows, and S01–S04 headers present.

### Step 5 — Packet corpus role fields & contracts · **role: `build`**

- **packet_id:** `aud231-s05-packets` · `depends_on: ["aud231-s04-batch"]`
- **Section header:** `## S05 — Packet Corpus`
- **Inline:** every `.omarchy/packets/*.json` at `83ca764` (`pkt-01-impl`, `pkt-02-audit`, `pkt-03-optimize`, `_sample_packet`), `.omarchy/packets/README.md`, `ls -R .omarchy/contracts` output, `.omarchy/omarchy.py:250-275`.
- **Checks:**
  - `S05-01` One row per packet: does it carry every `required_keys` field, a legal `role`, and a `family` equal to its seat's lock family?
  - `S05-02` One row per packet: does the `role` match what `instructions` asks the seat to do (e.g. a `g5_review` packet whose instructions say "expand tests")?
  - `S05-03` Does each `story_id`/`uc_id` have a contract file?
  - `S05-04` Does every packet stay ≤ 5 `target_files`? Is the ≤ 300 LOC half of `G2` enforced anywhere?
  - `S05-05` Does `README.md`'s role table match `ROLE_TO_SEAT` exactly? Does its `cloud_g3` "dry-run only" note hold for `--batch --dry-run`?
  - `S05-06` Does `README.md`'s expected wave output match an actual `--batch --dry-run` run? `parent` inlines the captured stdout.
- **Acceptance:** at least one S05-01 row and one S05-02 row per packet (8 rows minimum), plus S05-03..06.

### Step 6 — Constitution & roster consistency · **role: `build`**

- **packet_id:** `aud231-s06-docs` · `depends_on: ["aud231-s05-packets"]`
- **Section header:** `## S06 — Docs vs Code`
- **Inline:** `AGENTS.md` (all), `01_OMARCHY_AGENT_PROMPTS.md:8-82`, `docs/HISTORY.md` (all), `docs/DEVELOPER_GUIDE.md:46-57`, `docs/SPRINT_DASHBOARD.md:9-16,39-44,51-73`, `README.md:1-30,41-90`, `.cursor/rules/omarchy-council.mdc` (all), `docs/GRAND_COUNCIL.md` (all), `scripts/log_cloud_agent.sh` (all).
- **Checks:**
  - `S06-01` For each doc, does it name the Core-5 roster, or a pre-v2.3 roster (`mitnick`/`jobs`/four cloud seats as default)? One row per doc.
  - `S06-02` Does every proof field named in docs (`packet_sha256`, `prompt_sha256`, `tree_sha256`, `output_sha256`, `trailer_status`) exist in the kernel's log dict?
  - `S06-03` Do the dashboard loop's parse markers (`=== FILE: … ===`, `OMARCHY_STATUS`) match the kernel's actual output contract (`{"files": {...}}`)?
  - `S06-04` Under the default Core-5 `agents.lock`, can Rule 16 (`01_…:78-81`) be satisfied, given that `log_cloud_agent.sh` rejects seats absent from the lock?
  - `S06-05` Does `docs/HISTORY.md` record v2.3 and the tags that exist (`v2.1`, `v2.2.1`, `v2.3`)?
  - `S06-06` Do the packet filenames cited in docs exist (e.g. `sample_packet.json` vs `_sample_packet.json`)?
- **Acceptance:** at least 12 rows (S06-01 alone covers 8 docs), and S01–S06 headers present.

### Step 7 — Kernel test coverage map · **role: `build`**

- **packet_id:** `aud231-s07-tests` · `depends_on: ["aud231-s06-docs"]`
- **Section header:** `## S07 — Test Coverage Map`
- **Inline:** `tests/test_omarchy_kernel.py` (all), the list of every `def ` in `.omarchy/omarchy.py` and `.omarchy/batch_runner.py` with line numbers, and the `G1` Testing Jig stdout of `python3 -m pytest -q tests/test_omarchy_kernel.py`. `parent` runs that command on the host at the frozen SHA. If `parent` cannot run it, the jig result is `UNMEASURED`.
- **Checks:**
  - `S07-01` One row per kernel/scheduler function: which test exercises it (`test_fn`), or `NONE`.
  - `S07-02` Which guarantees in `AGENTS.md:55` / `01_…:23` have no test? (At minimum: mid-wave abort eviction, unauthorized write rejection, worktree cleanup on abort, `load_packet` schema / 5-file cap, live `cloud_g3` refusal, budget fail-closed.)
  - `S07-03` Which assertions hardcode model slugs instead of reading `agents.lock`? Does that contradict the module docstring (`tests/test_omarchy_kernel.py:1-5`)?
  - `S07-04` If a team follows `AGENTS.md:40` and copies an optional row into `agents.lock`, which test fails?
  - `S07-05` `G1` result as `passed/failed/errors` from the inlined jig output, or `UNMEASURED`.
- **Acceptance:** one S07-01 row per `def`. S07-05 is cited to jig output or reads `UNMEASURED`.

### Step 8 — Gates G0–G5 & hemisphere honesty matrix (finalize worksheet) · **role: `build`**

- **packet_id:** `aud231-s08-gates` · `depends_on: ["aud231-s07-tests"]`
- **Section header:** `## S08 — Gates & Hemisphere Honesty`
- **Inline:** `01_OMARCHY_AGENT_PROMPTS.md:33-66`, `AGENTS.md:7-16,44-56`, `.omarchy/omarchy.py:44-51,250-291,729-825`, `docs/DEVELOPER_GUIDE.md:46-57`, `docs/SPRINT_DASHBOARD.md:55-73`.
- **Checks:**
  - `S08-G0` … `S08-G5`: one row per gate. Columns: who owns it, what the doc requires, which code mechanically enforces it (`path:line`), or `NOT_ENFORCED`.
  - `S08-L5a` Law 5 forward direction: Family A `build` → Family B `g5_review`. Is it routable via `ROLE_TO_SEAT`?
  - `S08-L5b` Law 5 reverse direction: a Family B `g4_test` artifact → a Family A reviewer. Which role routes it? Is that seat permitted to do `G5` (`AGENTS.md:32`)?
  - `S08-H1` Can a cloud seat's packet produce a row in `.omarchy/local-agent-proof.log`? (`parent` inlines the captured stdout and proof-log block of a `--dry-run` on a throwaway `cloud_g3` packet, then deletes the packet.)
  - `S08-H2` Does anything in the kernel distinguish a Cursor local subagent from a real Ollama run (`AGENTS.md:56`)?
  - Finalize: replace the running trailer with the final §3.1 trailer. `TOUCHED_FILES` must list only `$W`.
- **Acceptance:** S01–S08 headers present, and exactly one line that *starts with* `OMARCHY_STATUS:` (gate: `["python3", "-c", "import re,sys;sys.exit(0 if len(re.findall(r'^OMARCHY_STATUS: ',open(sys.argv[1]).read(),re.M))==1 else 1)", "$W"]`).

---

### Step 9 — Adversarial fail-closed test design · **role: `g4_test`**

- **packet_id:** `aud231-s09-g4` · `depends_on: ["aud231-s08-gates"]`
- **Packet:** `uc_ids: ["UC-AUDIT-V231-G4"]`, `role: "g4_test"`, `family: "local_family_b"`, `num_ctx: 32768`, `target_files: ["docs/GRAND_COUNCIL/v2.3.1_Test/MOXIE_G4_TEST.md"]`.
- **Inline:** `tests/test_omarchy_kernel.py` (all), `.omarchy/omarchy.py:59-208,236-291,359-497,540-683,686-709`, `.omarchy/batch_runner.py:50-120,260-324`, `scripts/run_local_agent.sh` (all). Do **not** inline the worksheet. The test design must be independent of the builder's conclusions.
- **Output:** at least 15 `TC-V231-NN` cases in the `docs/DEVELOPER_GUIDE.md` §4.2 format. Each case adds `Target: <path:line>` and `Coverage: EXISTING:<test_fn> | MISSING`. It must cover, at minimum:
  - illegal role, family, or model claims
  - malformed or duplicate lock rows
  - a packet path that escapes `.omarchy/packets/`
  - a `target_files` entry that escapes the worktree
  - an unauthorized output key from the model
  - a zero-change result
  - a dirty or wrong base branch
  - an Ollama `/api/tags` outage
  - a model that is not pulled
  - an over-budget `num_ctx`
  - `evict_model` failing inside `finally`
  - an edited packet hitting stale resume state
  - a `depends_on` cycle or unknown dep
  - a `cloud_g3` packet in the batch
  - ad-hoc strings passed to `run_local_agent.sh` (exit 64/66)
- **Forbidden:** writing any file under `tests/`. This step designs the tests; landing them is a later `build` slice.
- **Gates:** `["python3", "-c", "import re,sys;sys.exit(0 if len(re.findall(r'^ID: TC-V231-',open(sys.argv[1]).read(),re.M))>=15 else 1)", "<file>"]`, plus `["grep", "-Eq", "^OMARCHY_VERDICT: (APPROVE|APPROVE_WITH_FIXES|REQUEST_CHANGES|REJECT)$", "<file>"]`, `["grep", "-Eq", "^BLOCKING_COUNT: [0-9]+$", "<file>"]`, `["grep", "-Eq", "^CITED_LOCATIONS: ", "<file>"]`.

### Step 10 — Cross-family peer review of the worksheet · **role: `g5_review`**

- **packet_id:** `aud231-s10-g5` · `depends_on: ["aud231-s08-gates"]` (same Family B wave as step 9; different target, so the scheduler may keep the model warm between them)
- **Packet:** `uc_ids: ["UC-AUDIT-V231-G5"]`, `role: "g5_review"`, `family: "local_family_b"`, `num_ctx: 49152`, `target_files: ["docs/GRAND_COUNCIL/v2.3.1_Test/MOXIE_G5_REVIEW.md"]`.
- **Inline:** the final `QWENY_AUDIT_WORKSHEET.md`, plus every excerpt cited by its `FAIL`/`UNKNOWN` rows and by a sample of `PASS` rows (at least 1 per section). **Never** inline `MOXIE_G4_TEST.md`, because the reviewer family authored it.
- **Output:**
  - A table with columns `| Worksheet Check | Builder Result | Reviewer Result | Agree? | Evidence path:line | Note |` covering every `FAIL`/`UNKNOWN` row plus the sampled `PASS` rows.
  - A section listing `PASS` rows with no code evidence (invalid per §3.1).
  - A section on privacy and trust boundaries (path sterilization, proof-log integrity, the trust placed in `verification_commands`).
  - The §3.2 trailer.
- **Gates:** the trailer greps from step 9, plus `["grep", "-Eq", "^\\| S0[1-8]-", "<file>"]`.

### Step 11 — Empirical DoD audit of this audit · **role: `scrum_audit`**

- **packet_id:** `aud231-s11-dod` · `depends_on: ["aud231-s09-g4", "aud231-s10-g5"]`
- **Packet:** `uc_ids: ["UC-AUDIT-V231-DOD"]`, `role: "scrum_audit"`, `family: "local_family_a"`, `num_ctx: 32768`, `target_files: ["docs/GRAND_COUNCIL/v2.3.1_Test/SCRUM_DOD_AUDIT.md"]`.
- **Inline:** the trailers (last 6 lines) of all three prior deliverables, the `aud231-*` proof-log blocks, `git log --format='%H %s' 83ca764..HEAD`, `docs/DEVELOPER_GUIDE.md:46-57`, and `01_OMARCHY_AGENT_PROMPTS.md:33-43`.
- **Output:**
  - **DoD 1–8 table** with columns `| DoD # | Criterion | Status (MET/NOT_MET/UNMEASURED) | Source (proof-log packet_id / commit sha / file:line) |`.
  - **Provenance table**: one row per `aud231-s01..s10` packet, giving `packet_sha256`, `tree_sha256`, `trailer_status`, and the matching 2PC commit SHA, or `MISSING`.
  - **Family-separation table** giving the author family and reviewer family per deliverable. The row for `MOXIE_G4_TEST.md` must state whether any Core-5 role could deliver its Family A `G5`. Scrum is Non-G5 (`AGENTS.md:32`) and must not self-promote into that seat.
  - The §3.2 trailer.
- **Gates:** the trailer greps from step 9, plus `["grep", "-Eq", "^\\| aud231-s10-g5 ", "<file>"]`.

---

## 5. Expected Wave Plan (from `plan_serial_family_waves`, `.omarchy/batch_runner.py:123-189`)

| Wave | Family (lock) | Packets | Why separate |
|---|---|---|---|
| 1–8 | `local_family_a` | `s01` … `s08` (one per wave) | `depends_on` chain plus the shared target `$W`. The scheduler cannot coalesce dependent same-family packets, so expect 8 evict/reload cycles of Family A. Wall-clock cost is `UNMEASURED`. |
| 9 | `local_family_b` | `s09`, `s10` (one warm wave) | Independent of each other, distinct targets, both depend only on `s08` |
| 10 | `local_family_a` | `s11` | Depends on `s09` + `s10` |

`parent` confirms this with `--batch --dry-run` before the live run and pastes the stdout into the step 5 packet (S05-06) and the step 11 packet.

## 6. Exit Criteria for the Audit

1. All four deliverables exist at the paths in §3, on the plan branch, each landed by a `COMMITTED` 2PC packet whose proof row is present.
2. All gates in §4 pass in the live run. `parent` then runs `G1` and records it in `docs/TESTING_JIG_REPORT.md`, or records `UNMEASURED` there.
3. Any `NEEDS_PLAN`/`UNKNOWN` emitted by a local seat returns to linus as a replan input. `parent` does not patch it (Law 4, Law 11).
4. linus re-ballots `v2.3.1` only after reading all four local deliverables. Until then, `LINUS_BALLOT.md` covers the v2.3 tree alone.
