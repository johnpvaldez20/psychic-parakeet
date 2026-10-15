# Omarchy Scrum 2.0 — Universal Multi-Agent Software Engineering Blueprint (`psychic-parakeet`)

This repository is the **Day-0 Template & Operating System** for multi-agent software engineering. Clone or copy this template into any new project to get:

1. **Two-Hemisphere Token Routing:** Cloud Grand Council (`linus`, `dhh`, `carmack`, `knuth` on distinct frontier model families) for architecture, specs, and structural gates; Local Council (`qweny`, `moxie`, `mitnick`, `jobs`, `scrum` on two distinct local Ollama model families) for all code, unit tests, adversarial `G5` peer checks, and Scrum audits.
2. **Persona-First Abstraction (`agents.lock`):** Decouples permanent engineering personas from ephemeral LLM version strings.
3. **Strict Document Ontology:** Separates System Architecture (`00_ARCHITECTURE.md`), Agent Laws (`01_OMARCHY_AGENT_PROMPTS.md`), Macro Roadmap (`02_PRODUCTION_PLAN.md`), Product Spec (`docs/PRODUCT_SPEC.md`), and Living Sprint State (`docs/SPRINT_DASHBOARD.md`).
4. **Sterilized 2PC Kernel:** [`.omarchy/omarchy.py`](.omarchy/omarchy.py) runs packet-only worktrees with Story/UC contracts, deterministic gates, serialized Ollama unload (`keep_alive: 0`), and flocked proof logs. `scripts/run_local_agent.sh` is a dumb pipe.

---

## 1. How the Core Documents Work Together

Six governance contracts keep architecture immutable while sprint state moves daily (**conflict `K25`** — never revive monolithic `00_ARCHITECTURE_AND_PLAN.md`):

```text
README.md (You are here: TOC, versioning, release workflow, quickstart)
 ├── 00_ARCHITECTURE.md          → HOW the system is engineered (immutable contracts; Cloud GC only)
 ├── 01_OMARCHY_AGENT_PROMPTS.md → HOW agents work together (12 Iron Laws, Gates G0–G5, Rule 11 packets)
 ├── 02_PRODUCTION_PLAN.md       → Macro phased roadmap (not the daily sprint backlog)
 ├── AGENTS.md (+ agents.lock)   → WHO the agents are (bindings; model slugs live ONLY in agents.lock)
 ├── .cursor/agents/             → Nine immutable persona contracts (bias, owned/forbidden dirs, trailers)
 │    ├── linus.md · dhh.md · carmack.md · knuth.md
 │    └── qweny.md · moxie.md · mitnick.md · jobs.md · scrum.md
 └── docs/
      ├── OMARCHY_SCRUM_2_0_BLUEPRINT.md → Full Universal Multi-Agent Engineering Blueprint & 1.0 Post-Mortem
      ├── PRODUCT_SPEC.md                → WHAT we are building (UC-01..UC-XX, personas, stack & languages)
      ├── DEVELOPER_GUIDE.md             → Human onboarding, package map, Agile hierarchy & DoD templates
      ├── SPRINT_DASHBOARD.md            → Living Sprint state + §2.4 Self-Healing & Gate Retry Loop
      ├── TESTING_JIG_REPORT.md          → Auto-generated module coverage & UC traceability readout
      ├── EVIDENCE.md                    → Measured hardware & integration rows only (no guesses)
      └── HISTORY.md                     → Append-only chronological milestone log
```

---

## 2. Complete Markdown Table of Contents

| File | Layer | Owner | Role |
|---|---|---|---|
| [`README.md`](README.md) | Entry | `knuth` (intent) / `qweny` (edits) | Table of contents, versioning, release gates, how the core files fit together |
| [`docs/OMARCHY_SCRUM_2_0_BLUEPRINT.md`](docs/OMARCHY_SCRUM_2_0_BLUEPRINT.md) | L0 Blueprint | Visionary / Scrum | **The Complete Blueprint:** Post-mortem of Multi-Agent 1.0, the 12 Iron Laws, Agile Scrum ceremonies, Testing Jig spec, and Day-0 checklist |
| [`00_ARCHITECTURE.md`](00_ARCHITECTURE.md) | L0 Architecture | Cloud Grand Council (`linus` chair) | Immutable system architecture, module boundaries, and code-owned contracts (auto-injected into local runs) |
| [`01_OMARCHY_AGENT_PROMPTS.md`](01_OMARCHY_AGENT_PROMPTS.md) | L0 Agent Constitution | Cloud Grand Council | Constitutional laws (`Law 1–12`), Merge Gates `G0–G5`, and machine-parseable `OMARCHY_STATUS` / `OMARCHY_VERDICT` schemas |
| [`02_PRODUCTION_PLAN.md`](02_PRODUCTION_PLAN.md) | L0 Macro Plan | Cloud Grand Council | Macro phased roadmap (`Phase 0` → `Phase N`); not daily story state |
| [`AGENTS.md`](AGENTS.md) & [`agents.lock`](agents.lock) | L0 Identity | `parent` + `linus` | Canonical 9-seat persona table + single machine-readable model lock |
| [`.cursor/agents/linus.md`](.cursor/agents/linus.md) | L0 Persona | Cloud `linus` | Immutable persona: cognitive bias, owned/forbidden dirs, `OMARCHY_VERDICT` |
| [`.cursor/agents/dhh.md`](.cursor/agents/dhh.md) | L0 Persona | Cloud `dhh` | Immutable persona: product/UX bias, owned/forbidden dirs, `OMARCHY_VERDICT` |
| [`.cursor/agents/carmack.md`](.cursor/agents/carmack.md) | L0 Persona | Cloud `carmack` | Immutable persona: perf/math bias, owned/forbidden dirs, `OMARCHY_VERDICT` |
| [`.cursor/agents/knuth.md`](.cursor/agents/knuth.md) | L0 Persona | Cloud `knuth` | Immutable persona: algorithmic rigor / onboarding, `OMARCHY_VERDICT` |
| [`.cursor/agents/qweny.md`](.cursor/agents/qweny.md) | L0 Persona | Local `qweny` | Immutable builder persona: `=== FILE ===` blocks + `OMARCHY_STATUS` |
| [`.cursor/agents/moxie.md`](.cursor/agents/moxie.md) | L0 Persona | Local `moxie` | Immutable `G5` reviewer persona: privacy bias + `OMARCHY_VERDICT` |
| [`.cursor/agents/mitnick.md`](.cursor/agents/mitnick.md) | L0 Persona | Local `mitnick` | Immutable adversarial QA persona: builder trailers for tests + `OMARCHY_VERDICT` for audits |
| [`.cursor/agents/jobs.md`](.cursor/agents/jobs.md) | L0 Persona | Local `jobs` | Immutable UX taste persona: briefs + `OMARCHY_VERDICT` (never `G5`) |
| [`.cursor/agents/scrum.md`](.cursor/agents/scrum.md) | L0 Persona | Local `scrum` | Immutable process auditor: dashboard / DoD / §2.4; never app code; never `G5` |
| [`docs/PRODUCT_SPEC.md`](docs/PRODUCT_SPEC.md) | L1 Product | `dhh` | Product use cases (`UC-01..UC-XX`), personas, stack/languages, and fail-closed degradation |
| [`docs/DEVELOPER_GUIDE.md`](docs/DEVELOPER_GUIDE.md) | L2 Onboarding | `knuth` | Day-1 human onboarding + Agile hierarchy (`Theme → Epic → Feature → Story → Task`), DoD, and QA templates |
| [`docs/SPRINT_DASHBOARD.md`](docs/SPRINT_DASHBOARD.md) | L3 Living State | `scrum` + `parent` | Living Sprint Dashboard (checkpoint, Executive & Team views, **§2.4 Self-Healing & Gate Retry Loop** — sole runtime-state sink; no `EXECUTION_STATE.md`) |
| [`docs/TESTING_JIG_REPORT.md`](docs/TESTING_JIG_REPORT.md) | L6 Generated | Testing Jig script | Auto-generated Testing Jig readout sink |
| [`docs/EVIDENCE.md`](docs/EVIDENCE.md) & [`docs/HISTORY.md`](docs/HISTORY.md) | L3 Results / Log | `mitnick` / `parent` | Measured hardware evidence sink + append-only milestone log |
| [`docs/GRAND_COUNCIL.md`](docs/GRAND_COUNCIL.md) | L3 Governance | Cloud Grand Council | Index of independent Nobel milestone ballots |

---

## 3. Versioning & Release Workflow

1. **Semantic Versioning:** Application version follows `MAJOR.MINOR.PATCH` (`0.1.0` at bootstrap). Documentation history is tracked via Git commits and append-only rows in [`docs/HISTORY.md`](docs/HISTORY.md).
2. **Release Gate (Rule 16):** Before cutting any version tag or merging a milestone branch:
   - The automated **Testing Jig** must report `0` unit failures and `100%` UC linkage.
   - Local `scrum` audits [`docs/SPRINT_DASHBOARD.md`](docs/SPRINT_DASHBOARD.md) for Definition-of-Done compliance and ensures unverified hardware items remain marked `UNMEASURED`.
   - The **Cloud Grand Council** (`linus`, `dhh`, `carmack`, `knuth`) and **Local Council** (`qweny`, `moxie`, `mitnick`, `scrum`) cast independent Nobel ballots (`SHIP` / `SHIP_WITH_FIXES` / `HOLD`).

---

## 4. Day-0 Quickstart

```bash
# 1. Verify local Ollama readiness
scripts/ensure_local_agents.sh

# 2. Dry-run a sterilized packet (Story/UC + worktree prepare; no Ollama)
scripts/run_local_agent.sh _sample_packet.json --dry-run

# 3. Execute one packet (2PC: worktree → gates → ff-merge; keep_alive:0 unload)
scripts/run_local_agent.sh _sample_packet.json

# 4. Causal family waves A→B→A (depends_on + finally eviction; keep-warm within wave)
scripts/run_local_agent.sh --batch --dry-run
scripts/run_local_agent.sh --batch

# 5. Refresh local vs. cloud token split
scripts/report_token_split.sh --markdown
```
