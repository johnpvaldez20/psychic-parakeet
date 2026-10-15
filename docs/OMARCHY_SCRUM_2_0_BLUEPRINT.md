# Omarchy Scrum 2.0 — The Universal Multi-Agent Software Engineering Blueprint

**Document Role:** Foundational operating system for **Omarchy Scrum 2.0** and all future multi-agent software projects.  
**Portability:** Project-agnostic. Drop this document (and its 6-file modular governance ontology) into any new repository on Day 0.

---

## 1. Executive Thesis: Why Multi-Agent 1.0 Broke—and How 2.0 Fixes It

When Scrum was invented for human teams, it solved the problem of opaque waterfall plans, late integration, and unmeasured progress through **empirical process control**: transparency, inspection, and adaptation.

In **Multi-Agent 1.0**, we proved something extraordinary: a hybrid swarm of frontier **Cloud models** (planning, architecture, UX, performance math) and **Local open-weight models** (writing production code, tests, and scripts on local silicon) can build complex, hardware-coupled software with deterministic unit tests and strict ABI gates. **However, the governance and documentation became a 24-conflict ontological tangle (`K01–K24`).** That is why Omarchy Scrum 2.0 starts clean as a project-agnostic template.

### 1.1 The Post-Mortem of 1.0: What Failed, What Worked, What Changes

| Failure Mode in 1.0 | Root Cause | Omarchy Scrum 2.0 Verdict |
|---|---|---|
| **1. "One Name, Four Runtimes" (`K01`, `K02`)** | The same name (`qweny`, `mitnick`, `juan`) meant a Cloud VM Task, a local Cursor subagent running the *parent’s* cloud model, a local Ollama HTTP call, or a shell alias. | **LEAVE BEHIND.** Rename/alias routing is banned. Every seat has **one** immutable Persona ID and **one** permitted execution mechanism. |
| **2. The Invisible Parent (`K04`, `K05`)** | Local Ollama scripts only printed text to `stdout`; the Parent/Orchestrator actually edited files, synthesized matrices, and stood in for failed cloud seats—while having **no row in `AGENTS.md`** and no defined boundaries. | **FIX.** The **Orchestrator (`parent`)** is a formal, audited seat: it is a router, packet compiler, and patch applier. It may **never** ghostwrite a failed council ballot or hand-patch business logic. |
| **3. Fake Proof Trails (`K03`)** | Commits cited `.omarchy/local-agent-proof.log` line numbers that were 160-character warm-up pings while landing large diffs written by a Cursor subagent. | **FIX.** Cryptographic **Packet-to-Diff Provenance (`G0`)**: the proof log records `sha256(prompt_packet)` and `sha256(model_output)`. No hash match = gate failure. |
| **4. Blind Local Context (`K19`)** | `run_local_agent.sh` only injected the first 6,000 chars of `00_ARCHITECTURE.md`, yet prompts told local models to "read `01_` and neighbouring files" they could not see. | **FIX.** **Self-Contained Context Packets (Rule 11)**: the packet compiler automatically bundles target files, exact neighbour signatures, and acceptance criteria into the local prompt payload. |
| **5. Reviewer Weight Collapse (`K12`)** | Two seats (`Mitnick` and `Moxie`, or `Qweny` and `Jobs`) shared the exact same model weights (`gemma4` or `qwen3.8`) and "peer-reviewed" each other. Same weights = same blind spots. | **IRON LAW.** **Cross-Family Double-Check**: a code or test artifact authored by Model Family A **must** be verified by Model Family B (even at 2× token cost). |
| **6. Seat Table & Rule Duplication (`K08`, `K11`)** | Seat-to-model mappings and gate definitions were copy-pasted across 5 markdown files and 3 bash scripts. Every model upgrade caused instant drift. | **FIX.** **Single Source of Truth (`agents.lock` + `AGENTS.md`)**: personas are abstracted from model versions. One machine-readable config drives all scripts and docs. |
| **7. Product Spec Mixed with Swarm Laws** | A single architecture-and-plan file mixed domain contracts with agent prompt rules and session history. | **FIX.** **Strict Separation of Church and State**: Product Architecture (`00_`) knows **nothing** about agents; Agent Laws (`01_`) know **nothing** about the product domain. |

---

## 2. The Two-Hemisphere Multi-Agent Architecture

Software engineering divides naturally into **High-Context Reasoning** (architecture, domain modeling, UX compression, algorithmic complexity, adversarial review) and **High-Volume Execution** (writing implementation slices, unit tests, boilerplate, build scripts).

```text
================================================================================
 HEMISPHERE 1: CLOUD GRAND COUNCIL (High-Context Planning & Independent Audit)
   • Never writes production code (`src/**`, `app/**`) or build scripts.
   • Every seat runs on a DISTINCT frontier model family (Nobel Independence).
   • Produces: Architecture Plans, Product Specs, Rule 11 Packets, Gate Verdicts.
================================================================================
   │  ▲
   │  │  1. Dispatches Self-Contained Rule 11 Work Packets (Story/Task level)
   │  │  4. Returns Diff + JUnit/Coverage Readout + Local G5 Peer Verdict
   ▼  │
================================================================================
 THE ORCHESTRATOR (`parent`) — Deterministic Router & Mechanical Gatekeeper
   • Bundles file context into packets; applies local diffs; runs Testing Jig.
   • NEVER invents product requirements, ghostwrites ballots, or patches logic.
================================================================================
   │  ▲
   │  │  2. Executes Local Coding (Family A) & Local Adversarial Peer (Family B)
   │  │  3. Local Scrum Master audits Git + Testing Jig + Sprint Dashboard
   ▼  │
================================================================================
 HEMISPHERE 2: LOCAL COUNCIL (Zero-Marginal-Cost Execution & Adversarial Check)
   • Runs 100% on local hardware (Ollama / MLX / vLLM).
   • Author (Family A) ≠ Verifier (Family B).
   • Produces: Production Code, Unit/Functional Tests, UX Briefs, Scrum Audits.
================================================================================
```

### 2.1 Why Double the Tokens Is Cheaper Than One Hallucination
A single LLM reviewing its own output—or a second persona running on the *same* underlying model weights—suffers from **correlated failure modes**. If Model Family A hallucinates a non-existent API, or misses a race condition, asking Model Family A to review that diff yields rubber-stamp approval.

By mandating **Two Independent Model Families** for every slice of work:
1. **Local Execution + Local Cross-Check:** Local Coder (**Family A**) writes the code; Local Peer Reviewer (**Family B**) attempts to break it and audits privacy/trust boundaries.
2. **Cloud Specification + Cloud Audit:** Cloud Architect/Specialist (**Families C/D/E**) writes the specification packet and performs the final structural merge gate (`G3`/`G4`) against the diff.

Paying **2× tokens** at generation/review time eliminates the **10×–50× token spiral** of debugging hallucinated architectures, broken builds, and fake test passes.

---

## 3. Persona-First Abstraction (Decoupling Identity from Model Weights)

Model versions are ephemeral (`qwen3.8`, `gemma4`, `claude-opus-5-5`, `gpt-5.6`, `grok-4.7` will all be superseded). **Engineering archetypes are permanent.**

In Omarchy Scrum 2.0, **code, rules, and workflows reference only the Persona Seat ID**, never a hardcoded model string.

### 3.1 The 3-Layer Persona Abstraction
1. **Immutable Persona Contract (`.cursor/agents/<seat>.md`):**
   - Defines **Who they are** (cognitive bias, historical archetype, what they hate, what they protect), **What they own**, and **What they are forbidden to touch**.
   - Contains **zero** hardcoded model version strings.
2. **Single Machine-Readable Binding (`agents.lock`):**
   - A single key-value file in the repository root maps each `seat_id` to its `runtime` (`cloud` | `local`), `model_slug`, `model_family`, and `role_group`.
   - All runner scripts (`run_local_agent.sh`, `ensure_local_agents.sh`, `log_cloud_agent.sh`, `report_token_split.sh`) parse `agents.lock`.
3. **Model Upgrade Protocol (Cook-Off Gate):**
   - When a new local or cloud model releases, you change **one line** in `agents.lock` after running a 1-task A/B cook-off (verifying the candidate obeys `UNKNOWN` / fail-closed honesty and passes `G1` mechanical gates). No markdown files break.

### 3.2 The Canonical 9 Seats (Portable Across All Projects)

| Seat ID | Archetype Persona | Cognitive Weight (Why This Persona Exists) | Group | Permitted Runtime | Family Constraint |
|---|---|---|---|---|---|
| **`linus`** | **Linus Torvalds** | **Chief Architect (`G3`).** Kernel-grade intolerance for broken boundaries, over-abstraction, bloated diffs, and hidden errors. Owns system interfaces. | Grand Council | Cloud Only | Must be distinct Cloud Family 1 |
| **`dhh`** | **David Heinemeier Hansson** | **Product & UI Lead (`G4-UI`).** Conceptual compression; status lines over bloated dashboards; hates ceremony and premature DI/routing frameworks. | Grand Council | Cloud Only | Must be distinct Cloud Family 2 |
| **`carmack`** | **John Carmack** | **Performance & Engine Lead (`G4-Perf`).** id Tech math rigor; zero frame-loop allocations; explicit latency/memory budgets; refuses unmeasured hardware claims. | Grand Council | Cloud Only | Must be distinct Cloud Family 3 |
| **`knuth`** | **Donald Ervin Knuth** | **Algorithmic Rigor & Onboarding.** Literate programming clarity; formal invariants; $O(1)$ vs amortized honesty; owns `DEVELOPER_GUIDE.md` so a junior can build on Day 1. | Grand Council | Cloud Only | Must be distinct Cloud Family 4 |
| **`qweny`** | **Primary Builder** | **Lead Local Implementer.** Translates cited Rule 11 packets into clean production code and unit tests. Never invents APIs; emits `NEEDS_PLAN` when blocked. | Local Council | Local Only | **Local Family A** |
| **`moxie`** | **Moxie Marlinspike** | **Standing Peer Reviewer (`G5`) & Privacy.** Distrusts complex trust; hunts TOCTOU, cleartext, session leaks, and silent fallbacks. Reviews every `qweny` landing. | Local Council | Local Only | **Local Family B (`≠ qweny`)** |
| **`mitnick`** | **Kevin Mitnick** | **Adversarial QA & Honesty (`G4-Test`).** Defensive red-team mindset; assumes inputs and states will fail; owns fail-closed tests, smoke procedures, and the Testing Jig. | Local Council | Local Only | **Local Family B (`≠ qweny`)** |
| **`jobs`** | **Steve Jobs** | **User Taste & Friction Auditor.** One primary action per screen; human language over engineering jargon; high-contrast glanceability; says "no" to fake features. | Local Council | Local Only | Local Family A or B (Non-G5) |
| **`scrum`** | **Jeff Sutherland / Ken Schwaber** | **Scrum Master & Empirical Auditor.** Audits Git history, Testing Jig readouts, Definition of Done (DoD), and `SPRINT_DASHBOARD.md`. Never writes app code; never acts as `G5`. | Local Council | Local Only | Local Family A or B (Non-G5) |
| **`parent`** | **Deterministic Orchestrator** | **Dispatcher & Mechanical Gatekeeper.** Compiles context packets, applies local stdout patches, runs the project build/test/jig commands, logs proofs. Zero opinion authority. | Orchestrator | Host Session | N/A (Mechanical) |

---

## 4. The 12 Iron Laws for Every Agent

Every agent prompt and repository rule must enforce these 12 non-negotiable laws:

1. **Law 1 — Plan Before Code:** No line of production code is written unless it maps to an active Story/Task in `docs/SPRINT_DASHBOARD.md`, backed by immutable contracts in `00_ARCHITECTURE.md` and a User Story in `docs/PRODUCT_SPEC.md`. Macro phasing lives in `02_PRODUCTION_PLAN.md` and is never the daily sprint backlog.
2. **Law 2 — Strict Hemisphere Separation:** Cloud Grand Council agents **never** author production code, test code, or build scripts. Local Council agents **never** alter architecture plans or product specs (they output `NEEDS_PLAN: <reason>` and halt).
3. **Law 3 — Self-Contained Rule 11 Context Packets:** Local models have zero repo telepathy. Every local task invocation must automatically inline: (a) the exact target files, (b) quoted signatures of neighbour dependencies, (c) the Given-When-Then acceptance criteria, and (d) the required test names.
4. **Law 4 — `UNKNOWN` Over Invention:** If a symbol, API, schema, or requirement is missing from the packet, the agent must output `UNKNOWN — NEEDS_PLAN` and stop. Guessing an import or API is an automatic discard.
5. **Law 5 — Cross-Family Double-Check (`G5`):** Every code diff produced by Local Family A (`qweny`) must be reviewed by Local Family B (`moxie`) **and** audited by the relevant Cloud Grand Council seat (`linus` / `carmack` / `dhh`) before merge.
6. **Law 6 — Cryptographic Proof of Execution (`G0`):** Every local run appends `{timestamp, seat_id, response_model, packet_sha256, output_sha256}` to `.omarchy/local-agent-proof.log`. Using a local Cursor subagent on the parent’s cloud model and claiming it as local Ollama is a critical integrity violation.
7. **Law 7 — Mechanical Reproduction (`G1`):** An agent’s claim that "tests pass" or "build succeeds" is **void**. Only the Orchestrator running the automated **Testing Jig** (`G1`) in a clean working tree counts.
8. **Law 8 — Zero Silent Dependencies (`G2`):** No agent may add a library, package, or native dependency without a Cloud Grand Council vote and explicit human approval.
9. **Law 9 — Fail-Closed Product & Test Honesty:** Missing models, missing sensors, network errors, or corrupt files must fail closed with explicit user-visible status and test assertions—never silent no-ops, dummy zeros, or fabricated success.
10. **Law 10 — `UNMEASURED` Until Proven on Target:** Hardware latency, accelerator partitioning, thermal behavior, battery drain, and manual smoke steps must be marked `UNMEASURED` until a timestamped hardware evidence row exists in `docs/EVIDENCE.md`.
11. **Law 11 — No Ghostwriting:** If a cloud or local agent run fails or times out, the Orchestrator (`parent`) must retry or log `SEAT_FAILED`—it may **never** write a ballot or review under that seat’s name.
12. **Law 12 — Two-Iteration Deadlock Halt:** If two Grand Council seats (`dhh` ↔ `carmack`) disagree after two independent cloud passes, halt and escalate to `linus`. If `linus` is a party to the deadlock, halt and present a 1-page pros/cons decision brief to the human.

---

## 5. The Multi-Agent Agile Scrum Method

Both humans and agents operate inside one unified Agile hierarchy. There is no separate "agent todo list" vs. "human backlog."

### 5.1 The 5-Level Agile Work Breakdown Hierarchy

```text
Theme (Strategic Multi-Sprint Pillar — e.g., "Core Platform Reliability")
 └── Epic (Multi-Sprint Deliverable — e.g., "Contract-Verified Runtime")
      └── Feature (Module-Scoped Capability — e.g., "Strict ABI / Schema Loader")
           └── User Story (User-Visible Value + Given/When/Then Acceptance Criteria)
                └── Task = Rule 11 Packet (1 Local Coding Slice: ≤ 300 LOC, ≤ 5 files)
```

- **Sizing law:** A **Task** is the atomic unit of multi-agent work. It must be small enough that a local model can read all neighbour signatures in one prompt, implement the code + unit tests, and pass `G0–G5` in a single cycle.

### 5.2 The Sprint Ceremonies (How Cloud, Local, and Human Interact)

| Scrum Ceremony | Participants | Inputs | Outputs |
|---|---|---|---|
| **1. Sprint Planning (Nobel Pass)** | Human + Cloud Grand Council (`linus`, `dhh`, `carmack`, `knuth` in parallel) | `docs/PRODUCT_SPEC.md` + `00_ARCHITECTURE.md` + `02_PRODUCTION_PLAN.md` | Prioritized Sprint Backlog written into `docs/SPRINT_DASHBOARD.md` (User Stories with `Given/When/Then`), broken into numbered Rule 11 Task Packets (`S1`, `S2`, …). |
| **2. Packet Execution Loop (The Daily Slice)** | `parent` → `qweny` (code) → `mitnick` (adversarial tests) → `moxie` (`G5` peer) → Cloud `G3/G4` | One Task Packet (`SN`) | Green Testing Jig (`G1`), `moxie` `G5` approval, Cloud `linus`/`carmack` `G3/G4` approval, atomic git commit. |
| **3. Automated Scrum Audit (After Every Commit)** | Local `scrum` seat + Testing Jig script | Git log, `TESTING_JIG_REPORT.json`, `EVIDENCE.md`, `SPRINT_DASHBOARD.md` | Verifies DoD compliance for the story, updates `SPRINT_DASHBOARD.md`, flags any unbacked metric as `UNMEASURED`. |
| **4. Sprint Review & Grand Council Release Gate** | All 4 Cloud GC seats + All 5 Local Council seats + Human | Full branch diff, `TESTING_JIG_REPORT.md`, `EVIDENCE.md`, `SPRINT_DASHBOARD.md` | Independent Nobel ballots (`SHIP` / `SHIP_WITH_FIXES` / `HOLD`). Version tag is cut only on unanimous `SHIP`. |
| **5. Sprint Retrospective (Cook-Off & Rule Tune)** | `scrum` + `linus` + Human | `TOKEN_SPLIT.md`, defect leakage, rejected packets | Updates to `agents.lock` (if a model underperformed) or `01_OMARCHY_AGENT_PROMPTS.md`. |

### 5.3 Universal Definition of Done (DoD) for Every User Story
A User Story may **only** move to `DONE` on the Sprint Dashboard when the `scrum` agent verifies all 8 checkboxes against git:
- [ ] **1. Spec Link:** Linked to a `UC-XX` / `US-XX` ID with `Given / When / Then` acceptance criteria.
- [ ] **2. Local Provenance (`G0`):** Authored via local runner with matching packet/output SHA in `.omarchy/local-agent-proof.log`.
- [ ] **3. Testing Jig Green (`G1`):** Automated unit suite 100% passing (`0` failures, `0` errors) and module coverage recorded in `TESTING_JIG_REPORT.md`.
- [ ] **4. Fail-Closed Adversarial Tests (`G4-Test`):** `mitnick` negative/corrupt/missing-input tests exist and pass for every new code path.
- [ ] **5. Cross-Family Peer Review (`G5`):** `moxie` (different model family from coder) voted `APPROVE` with `file:line` cites.
- [ ] **6. Cloud Structural Review (`G3`/`G4`):** `linus` (+ `carmack` on hot paths / `dhh` on UI) voted `APPROVE`.
- [ ] **7. Hardware / Integration Honesty:** Either verified on target hardware with a row in `EVIDENCE.md`, or explicitly tracked as `Device Smoke: PENDING / UNMEASURED` (never silently marked "Done").
- [ ] **8. Documentation Sync:** Package map and status surfaces in `DEVELOPER_GUIDE.md` match the code.

---

## 6. Mandatory Test Coverage & The Automated Testing Jig

In a multi-agent codebase, **untested code is hallucinated code**. Every project must ship with a single host command (project-specific: e.g. `cargo xtask jig`, `pytest --jig`, or an equivalent Gradle task) that executes on every slice and outputs `docs/TESTING_JIG_REPORT.md` and `.json`.

### 6.1 What the Testing Jig Must Measure Automatically
1. **Module Inventory:** Auto-discovered from real source directories (never a hand-typed wish list).
2. **Per-Module Unit Coverage (Measured):** Line and branch coverage via the stack’s coverage tool (e.g. Coverage.py / LLVM-cov / JaCoCo).
   - **Pure domain / math / parser / state-machine modules:** Mandatory **$\ge 85\%$ line coverage** and **100% reject-branch coverage**.
   - **Hardware / OS wrapper modules:** Must extract pure policy/math classes so the decision logic is unit-tested at $\ge 85\%$, while thin OS glue is covered by Functional/Device tests.
3. **Per-Module Functional / Instrumented Coverage:** Reported honestly from connected device/integration runs—or explicitly stamped **`UNMEASURED`** if no device suite ran.
4. **Use-Case-to-Test Traceability Matrix:** Every `UC-XX` in `PRODUCT_SPEC.md` is mapped in `testing_jig_uc_links.tsv` to the exact test files that exercise it. A meta-test (`TestingJigLinkageTest`) fails the build if a linked test file is deleted or has zero `@Test` methods, or if a `UC-XX` is missing from the table.
5. **Release Execution Totals:** Total test cases in tree, total executed, passed, failed, skipped, errors, and exact UTC generation timestamp.

---

## 7. The Living Sprint Dashboard (`docs/SPRINT_DASHBOARD.md`)

Every project maintains `docs/SPRINT_DASHBOARD.md`, audited by the local `scrum` seat after every story.

### 7.1 The Dashboard Honesty Law
- Every cell in the dashboard must cite its source (`TESTING_JIG_REPORT.md @ <timestamp>`, `EVIDENCE.md#<row>`, or `git commit <sha>`).
- If a metric has no backing store yet, the cell **must** read **`UNMEASURED`**—never `0`, `0%`, or a made-up chart.

### 7.2 Dual-View Architecture (Executive vs. Team Standup)

#### View A: Executive / Release Decision View (Macro Stability & Risk)
| Widget | What It Measures | Backing Source |
|---|---|---|
| **Release Test Health** | `Passed / Total` unit & functional tests + overall measured line coverage % | `docs/TESTING_JIG_REPORT.md` (with UTC timestamp) |
| **Use-Case Readiness Breakdown** | Count of Use Cases in: `Shipped (Device Proven)` · `JVM Tested (Device Pending)` · `In Progress` · `Unimplemented` | `TESTING_JIG_REPORT.md` + `docs/EVIDENCE.md` |
| **DoD Compliance Rate** | `%` of stories in current sprint meeting all 8 DoD gates (`G0–G5` + Jig + Honesty) | `scrum` audit of sprint stories |
| **Defect Leakage & Active Severity Matrix** | `S1 (Critical) / S2 (Major) / S3 (Minor)` × `P1 / P2 / P3` open grid + escaped bugs | `docs/DEFECTS.md` or issue tracker (`UNMEASURED` if none) |
| **Sprint-over-Sprint Velocity & Automation ROI** | Completed stories/points per sprint + Local vs. Cloud token split (`%` local execution) | `docs/HISTORY.md` + `docs/TOKEN_SPLIT.md` |

#### View B: Team / Execution View (Micro Blockers & Daily Standup)
| Widget | What It Measures | Backing Source |
|---|---|---|
| **Sprint Testing Burnup / Burndown** | Planned tasks/tests vs. verified-green tasks/tests across the sprint | Active Sprint table in `SPRINT_DASHBOARD.md` |
| **Story Readiness Pipeline** | Stories by state: `Needs Plan` → `Packet Ready` → `In Local Coding` → `In G5/G3 Review` → `Ready for Device Smoke` → `Passed QA` | Git commits + `docs/SPRINT_DASHBOARD.md` §2.1 |
| **Per-Module Coverage & Thin-Spot Alert** | Modules below coverage threshold (e.g., `0.0%` or `< 50%`) flagged for `mitnick` test packets | `TESTING_JIG_REPORT.md` module table |
| **Blocked Test Cases & Hardware Gates** | Exact tests/smokes blocked by missing hardware, external weights, or unbuilt servers | `docs/EVIDENCE.md` `UNMEASURED` ledger |
| **Mean Time to Resolve (MTTR) & Pipeline Health** | Time from red gate (`G1`/`G3`/`G5` reject) to green commit | Git log timestamps |

---

## 8. The Canonical 6-File Modular Ontology (Drop-In Starter Kit)

To prevent documentation sprawl from Multi-Agent 1.0 — and to close conflict **`K25`** (monolithic `00_ARCHITECTURE_AND_PLAN.md` vs modular split) — **every new project starts with six governance contracts**, each with a strict boundary of what it **Is** and **Is Not**. The modular split is **structurally superior** to a single architecture-and-plan file because daily sprint updates authored by the local `scrum` seat must never mutate the immutable architectural contract owned by the Cloud Grand Council.

| File | What It IS (Allowed Content) | What It IS NOT (Forbidden Content) | Owner |
|---|---|---|---|
| **1. `00_ARCHITECTURE.md`** | **How the system is engineered** — modules, threads, ABIs, math contracts, and code-owned invariants. Auto-injected into local runs via `<!-- section:architecture-contracts -->`. | **Not** the agent swarm manual, **not** the macro roadmap, **not** the living sprint backlog. Zero prompt rules, zero gate tables, zero model-alias tables, zero story-state cells. | Cloud Grand Council (`linus` chair) |
| **2. `01_OMARCHY_AGENT_PROMPTS.md`** | **How the agents work together:** the 12 Iron Laws, Cloud vs. Local hemisphere routing, Rule 11 packet format, Merge Gates `G0–G5`, deadlock escalation, and Nobel review procedure. | **Not** the product architecture. Contains zero product use cases or domain math. | Cloud Grand Council |
| **3. `02_PRODUCTION_PLAN.md`** | **Macro phased roadmap** from Day 0 to production release (`Phase 0` → `Phase N`). Strategic sequencing only. | **Not** the daily sprint story table. Active Story/Task checkpoints live only in `docs/SPRINT_DASHBOARD.md`. | Cloud Grand Council |
| **4. `AGENTS.md` (+ `agents.lock`)** | **Who the agents are:** the canonical Seat → Persona → Weight → Runtime/Model table, the runtime mechanism glossary, and the model-swap protocol. Persona contracts live in `.cursor/agents/<seat>.md`. | Not a second copy of Rules 1–12 or the product roadmap. Model version strings live **only** in `agents.lock`. | `parent` + `linus` |
| **5. `docs/PRODUCT_SPEC.md`** | Use cases (`UC-XX`), user personas, languages/stack, product boundaries, and `Given/When/Then` acceptance criteria. | Not agent prompt files and not sprint state. | `dhh` |
| **6. `docs/SPRINT_DASHBOARD.md`** | **Living runtime state:** session resume checkpoint, Executive & Team metrics, active story pipeline, and the Active Self-Healing & Gate Retry Loop (§2.4). Single authoritative location for operational tracking (no separate `EXECUTION_STATE.md`). | Not an architecture contract. `scrum` may update cells here; `scrum` may **never** edit `00_ARCHITECTURE.md`. | `scrum` + `parent` |

Supporting documents (not part of the six governance contracts):
- `README.md` — human entry point, TOC, versioning, quickstart (`knuth` intent / `qweny` edits)
- `docs/DEVELOPER_GUIDE.md` — Day-1 human onboarding, package map, Agile/DoD templates (`knuth`)
- `docs/OMARCHY_SCRUM_2_0_BLUEPRINT.md` — this blueprint (portable OS narrative)
- `docs/TESTING_JIG_REPORT.md` — auto-generated by the project Testing Jig (never hand-edited)
- `docs/EVIDENCE.md` — measured hardware/integration rows only
- `docs/HISTORY.md` — chronological append-only log of completed milestones
- `.cursor/agents/<seat>.md` — nine immutable persona contracts (zero hardcoded model strings)

---

## 9. Day-0 Bootstrap Checklist for Omarchy Scrum 2.0 (Every Future Project)

When initializing a new repository from this template:
1. **Fill the Product Contract:** Replace the placeholders in `docs/PRODUCT_SPEC.md` with this project's use cases, personas, and stack.
2. **Confirm the Operating System:** Keep this blueprint and the six governance contracts (`00_ARCHITECTURE.md`, `01_OMARCHY_AGENT_PROMPTS.md`, `02_PRODUCTION_PLAN.md`, `AGENTS.md` + `agents.lock`, `docs/PRODUCT_SPEC.md`, `docs/SPRINT_DASHBOARD.md`) plus the nine persona contracts under `.cursor/agents/`.
3. **Wire the Testing Jig on Commit #1:** Before implementing `UC-01`, wire the project's Testing Jig host command and ensure `docs/SPRINT_DASHBOARD.md` §2.4 (Self-Healing & Gate Retry Loop) is the sole runtime-state sink — never a separate `EXECUTION_STATE.md`.
4. **Verify Local Two-Family Readiness:** Run `scripts/ensure_local_agents.sh` to confirm Local Family A (`qweny` / `scrum` / `jobs`) and Local Family B (`moxie` / `mitnick`) are warm and writing cryptographic packet/output hashes to `.omarchy/local-agent-proof.log`.
5. **Run Sprint 1 Planning:** Convene the Cloud Grand Council (`linus`, `dhh`, `carmack`, `knuth`) on `docs/PRODUCT_SPEC.md` to emit the Sprint 1 Rule 11 Task Packets (`S1..Sn`), and begin the empirical loop.
