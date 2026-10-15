# Sprint Dashboard (Living State & Empirical Metrics)

**Honesty Rule (Law 10):** Every cell in this dashboard must cite a verifiable source (`TESTING_JIG_REPORT.md @ <timestamp>`, `EVIDENCE.md#<row>`, or `git commit <sha>`). Any metric without a backing store must read **`UNMEASURED`** — never `0`, `0%`, or fabricated progress.

**Audited by:** local `scrum` seat via sterilized packets (`scripts/run_local_agent.sh <packet.json>`)

---

## 0. Session Resume Checkpoint (Overwrite in Place)

| Field | Current Value |
|---|---|
| **Active Sprint** | Sprint 1 — Bootstrap & Phase 1 Core |
| **Current Status** | Day-0 repository initialized with Omarchy Scrum 2.0 governance & templates |
| **Next Action** | Convene Cloud Grand Council on `docs/PRODUCT_SPEC.md` + `00_ARCHITECTURE.md` to emit Sprint 1 Rule 11 Task Packets (`S1..Sn`), wire Testing Jig, and begin local execution |
| **Blockers** | None |

---

## 1. Executive / Release Decision View (Macro Stability & Risk)

| Widget | Value | Backing Source |
|---|---|---|
| **Release Test Health (Unit)** | **UNMEASURED** (run Testing Jig) | `docs/TESTING_JIG_REPORT.md` |
| **Release Test Health (Functional / Device)** | **UNMEASURED** | `docs/EVIDENCE.md` |
| **Use-Case Readiness Breakdown** | `0` Device Proven · `0` JVM Tested · `0` In Progress · All Pending Sprint 1 | `docs/TESTING_JIG_REPORT.md` |
| **Definition of Done (DoD) Compliance** | **UNMEASURED** | `scrum` audit of active sprint stories |
| **Defect Density & Leakage Rate** | **UNMEASURED** | No defect log rows yet |
| **Active Defect Matrix (`S1..S3 × P1..P3`)** | **UNMEASURED** (empty matrix, not zeros) | — |
| **Mean Time to Resolve (MTTR)** | **UNMEASURED** | — |
| **Automation Coverage vs. Manual** | Unit: **UNMEASURED** · Device/Manual: **UNMEASURED** | `docs/TESTING_JIG_REPORT.md` |
| **CI / Pipeline Health** | **UNMEASURED** | No `.github/workflows` configured yet |
| **Local vs. Cloud Token Split** | **UNMEASURED** (run `scripts/report_token_split.sh --markdown`) | `docs/TOKEN_SPLIT.md` |

---

## 2. Team / Standup Execution View (Micro Blockers & Daily Progress)

### 2.1 Active Sprint Story Readiness Pipeline

| Story ID | Title | Use Case | State (`Needs Plan` / `Packet Ready` / `In Local Coding` / `In G5/G3` / `Ready for Smoke` / `Done`) | DoD (8/8) |
|---|---|---|---|---|
| `US-00` | Wire Automated Testing Jig & Coverage Readout | `UC-00` | `Packet Ready` (kernel: `.omarchy/omarchy.py`; sample `.omarchy/packets/sample_packet.json`) | 0/8 |

### 2.2 Testing Burnup / Burndown
- **UNMEASURED** until Sprint 1 task packets (`S1..Sn`) are locked.

### 2.3 Per-Module Coverage & Thin-Spot Alerts
- Run the project Testing Jig host command to populate module coverage from `docs/TESTING_JIG_REPORT.md`.

### 2.4 Active Self-Healing & Gate Retry Loop

**Authority:** This table is the **sole** living sink for orchestrator retry / self-heal state. Do **not** create `EXECUTION_STATE.md` or any parallel runtime-state file. `parent` updates rows mechanically; `scrum` audits honesty against git + `.omarchy/local-agent-proof.log`.

| Field | Current Value | Rules |
|---|---|---|
| **Active Task Packet** | `NONE` | Rule 11 `task_id` currently in the execution loop (`S1..Sn`), or `NONE`. |
| **Linked Story / UC** | `NONE` | Must match a row in §2.1 and a `UC-XX` in `docs/PRODUCT_SPEC.md`. |
| **Current Gate** | `IDLE` | One of: `IDLE` · `G0` · `G1` · `G2` · `G3` · `G4` · `G5`. |
| **Strike Count** | `0` / `3` | Bounded **3-strike** self-heal for `G1`/`G2` compiler or test failures. On strike 3 → halt; do not invent a fourth repair. |
| **Last Failure Class** | `NONE` | `NONE` · `COMPILE` · `TEST` · `TRAILER` · `SCOPE` · `CONTEXT_OVERFLOW` · `SEAT_FAILED`. |
| **Last Error Digest** | `UNMEASURED` | Short compiler/test/trailer excerpt (≤ 500 chars) or `UNMEASURED` if no failure yet. |
| **Healing Action** | `NONE` | `NONE` · `REPAIR_TURN` (re-dispatch builder with exact errors inlined) · `SPLIT_PACKET` · `SWAP_LOCAL_FAMILY` · `ESCALATE_HUMAN`. |
| **Author Seat / Family** | `NONE` | Seat that last emitted code or tests; family must differ from the `G5` reviewer (Law 5). |
| **G5 Reviewer Seat** | `NONE` | Opposite local family from Author. Mitnick test landings → Family A (`qweny`) reviews. |
| **Proof Anchors** | `UNMEASURED` | Latest `packet_sha256` + `output_sha256` from `.omarchy/local-agent-proof.log`, or `UNMEASURED`. |
| **Halt Reason** | `NONE` | Set when strikes exhausted, Law 4 `NEEDS_PLAN`/`UNKNOWN`, Law 11 `SEAT_FAILED`, or Law 12 deadlock. Clear only after human or Cloud replan. |

**Loop (parent, mechanical):**
1. Compile Rule 11 packet → dispatch builder → parse `=== FILE: … ===` + `OMARCHY_STATUS`.
2. On `READY`: apply files (scope-checked) → run `G1`/`G2`. On failure and strikes `< 3`: increment strike, set Healing Action `REPAIR_TURN`, re-dispatch with error digest. On strike `3`: set Halt Reason and stop.
3. On `NEEDS_PLAN` / `UNKNOWN`: set Halt Reason; **never** invent symbols.
4. On green `G1`/`G2`: dispatch cross-family `G5` (require `OMARCHY_VERDICT`) → Cloud `G3`/`G4` as required → `scrum` updates §0–§2.1; reset this table to `IDLE` / `0` / `NONE`.
