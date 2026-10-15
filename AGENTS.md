# AGENTS.md — Canonical Personas, Cognitive Weights, and Runtime Bindings

**Single Source of Truth:** Machine-readable bindings live in [`agents.lock`](agents.lock). System architecture lives in [`00_ARCHITECTURE.md`](00_ARCHITECTURE.md). Agent behavior laws live in [`01_OMARCHY_AGENT_PROMPTS.md`](01_OMARCHY_AGENT_PROMPTS.md). Macro roadmap lives in [`02_PRODUCTION_PLAN.md`](02_PRODUCTION_PLAN.md). Product requirements live in [`docs/PRODUCT_SPEC.md`](docs/PRODUCT_SPEC.md).

---

## 1. Token Routing & Hemisphere Split

**Cloud Grand Council = High-Context Planning & Structural Review.**  
**Local Council = All Code, Unit Tests, Adversarial QA, UX Briefs & Scrum Audits.**

| Artifact Class | Permitted Hemisphere | Mechanism | Proof Required |
|---|---|---|---|
| Architecture (`00_`), Agent Laws (`01_`), Roadmap (`02_`), `PRODUCT_SPEC.md`, `G3`/`G4` Reviews, Grand Council Ballots | **Cloud Grand Council** (Core: `linus`; optional: `dhh`, `carmack`, `knuth`) | Separate Cursor Cloud Task per seat (distinct model family) | `scripts/log_cloud_agent.sh <seat>` + cloud run ID |
| Production code (`app/**`, `src/**`), unit/functional tests, build scripts, Testing Jig, Scrum audits | **Local Council** (Core: `qweny`, `moxie`, `scrum`) | `scripts/run_local_agent.sh <packet.json>` → `.omarchy/omarchy.py` 2PC kernel | `.omarchy/local-agent-proof.log` (`role` + `seat_id` + `packet_sha256` + `tree_sha256`) |
| Packet compilation, applying local diffs, running the Testing Jig (`G1`) | **Orchestrator** (`parent`) | Host session | Git commit + `TESTING_JIG_REPORT.md` |

---

## 2. Canonical Seat Table (Abstracted Personas → Bound Models)

Workflows and prompts reference **only the Seat ID**, never a hardcoded model version. When a newer model is released, update [`agents.lock`](agents.lock) after a 1-task cook-off.

**Day-0 Core** lives in [`agents.lock`](agents.lock). **Optional seats** live in [`agents.lock.optional`](agents.lock.optional) until copied into the lock. Packets declare `role` (`build` / `g5_review` / `g4_test` / `scrum_audit` / `cloud_g3`); the kernel maps role → seat → family/model.

<!-- seat-table:canonical -->
| Seat ID | Archetype Persona | Cognitive Weight (Why This Seat Exists) | Group | Permitted Runtime | Family / Default Model (`agents.lock`) |
|---|---|---|---|---|---|
| **`linus`** | **Linus Torvalds** | **Chief Architect (`G3`).** Kernel-grade intolerance for broken boundaries, over-abstraction, bloated diffs, and hidden errors. Role: `cloud_g3`. | Grand Council | Cloud Task | Cloud Family 1 · `claude-opus-5-5-high` |
| **`qweny`** | **Primary Builder** | **Lead Local Implementer.** Translates Rule 11 packets into clean code and unit tests; outputs `UNKNOWN`/`NEEDS_PLAN` instead of guessing. Role: `build`. | Local Council | Local Ollama | **Local Family A** · `qwen3.8:27b-mlx` |
| **`moxie`** | **Moxie Marlinspike** | **Standing Peer Reviewer (`G5`) & adversarial QA (`g4_test`).** Distrusts complex trust; hunts TOCTOU, cleartext, session leaks, and silent fallbacks. Roles: `g5_review`, `g4_test`. | Local Council | Local Ollama | **Local Family B** · `gemma4:31b-mlx` |
| **`scrum`** | **Scrum Master** | **Empirical Process Auditor.** Audits `SPRINT_DASHBOARD.md`, DoD compliance, and Testing Jig vs. Git. Never writes app code; never `G5`. Role: `scrum_audit`. | Local Council | Local Ollama | Local Family A · `qwen3.8:27b-mlx` |
| **`parent`** | **Orchestrator** | **Deterministic Router & Gatekeeper.** Compiles Rule 11 packets, applies local diffs, runs `G1` tests. Never ghostwrites a seat ballot. | Orchestrator | Host Session | Host session |
<!-- /seat-table:canonical -->

### Optional seats (`agents.lock.optional`)

| Seat ID | When to enable | Notes |
|---|---|---|
| `dhh` / `carmack` / `knuth` | Full Cloud Grand Council pack | Copy rows into `agents.lock` before cloud Tasks |
| `mitnick` | Dedicated adversarial-QA seat split from `moxie` | Still Family B; keep cross-family `G5` |
| `jobs` | UX taste auditor | Non-G5; Family A |

### Hard Independence Rules
1. **Cross-Family Review (`G5`):** Code written by Local Family A (`qweny`) **must** be peer-reviewed by Local Family B (`moxie`). Test / `g4_test` artifacts authored by Family B (`moxie`) **must** be peer-reviewed by Family A (`qweny`). Neither model family ever grades its own weights.
2. **Zero Alias Routing / Sterilized CLI:** `scripts/run_local_agent.sh` accepts only a `.json` packet under `.omarchy/packets/` (or `--queue`). Ad-hoc strings and bare seat names are rejected (exit `64` / `66`).

---

## 3. Runtime Mechanism Glossary (Do Not Collapse)

| Mechanism | What Actually Runs | Can It Edit the Working Tree? | Valid Proof |
|---|---|---|---|
| **Cursor Cloud Task** (`environment: cloud`) | Independent Cloud VM on the seat's locked model family | Yes, on its cloud branch | `scripts/log_cloud_agent.sh` + cloud run ID |
| **`scripts/run_local_agent.sh <packet.json>`** / **`--batch`** | Thin pipe → [`.omarchy/omarchy.py`](.omarchy/omarchy.py) or [`.omarchy/batch_runner.py`](.omarchy/batch_runner.py). Single packet = 2PC. **`--batch`** = dependency-safe family waves (`depends_on`) with keep-warm inside a wave and `evict_model` in `finally` at every family boundary (even on 2PC abort). | **Phase 1** in `.omarchy/worktrees/<packet_id>`. **Phase 2** ff-merges iff gates exit 0; else nuked. Resume ids in `.omarchy/state/`. | `.omarchy/local-agent-proof.log` (`packet_sha256`, `prompt_sha256`, `tree_sha256`, `packet_id`, `trailer_status`) |
| **Cursor Local Subagent** (`environment: local`) | Cursor subagent running on the **parent's cloud model** | Yes, directly in the working tree | **None.** Never counts as local Ollama tokens or `G0`/`G5` proof |
