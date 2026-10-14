# Omarchy Scrum 2.0 — Universal Multi-Agent Software Engineering Blueprint (`psychic-parakeet`)

This repository is the **Day-0 Template & Operating System** for multi-agent software engineering. Clone or copy this template into any new project to get:

1. **Two-Hemisphere Token Routing:** Cloud Grand Council (`linus`, `dhh`, `carmack`, `knuth` on distinct frontier model families) for architecture, specs, and structural gates; Local Council (`qweny`, `moxie`, `mitnick`, `jobs`, `scrum` on two distinct local Ollama model families) for all code, unit tests, adversarial `G5` peer checks, and Scrum audits.
2. **Persona-First Abstraction (`agents.lock`):** Decouples permanent engineering personas from ephemeral LLM version strings.
3. **Strict Document Ontology:** Separates System Architecture (`00_ARCHITECTURE.md`), Agent Laws (`01_OMARCHY_AGENT_PROMPTS.md`), Macro Roadmap (`02_PRODUCTION_PLAN.md`), Product Spec (`docs/PRODUCT_SPEC.md`), and Living Sprint State (`docs/SPRINT_DASHBOARD.md`).
4. **Anti-Hallucination & Cryptographic Provenance (`G0–G5`):** `scripts/run_local_agent.sh` automatically injects `01_` laws and `00_` contracts into every local prompt and logs `packet_sha256` and `output_sha256`.

---

## 1. How the Core Documents Work Together

```text
README.md (You are here: TOC, versioning, release workflow, quickstart)
 ├── 00_ARCHITECTURE.md          → HOW the system is engineered (modules, threads, ABIs, math contracts)
 ├── 01_OMARCHY_AGENT_PROMPTS.md → HOW agents work together (12 Iron Laws, Gates G0–G5, Rule 11 packets)
 ├── 02_PRODUCTION_PLAN.md       → High-level phased roadmap from Day 0 to production release
 ├── AGENTS.md (+ agents.lock)   → WHO the agents are (Personas, cognitive weights, runtime bindings)
 └── docs/
      ├── OMARCHY_SCRUM_2_0_BLUEPRINT.md → Full Universal Multi-Agent Engineering Blueprint & 1.0 Post-Mortem
      ├── PRODUCT_SPEC.md                → WHAT we are building (UC-01..UC-XX, personas, stack & languages)
      ├── DEVELOPER_GUIDE.md             → Human onboarding, package map, Agile hierarchy & DoD templates
      ├── SPRINT_DASHBOARD.md            → Living Sprint state, checkpoint, Executive & Team metrics
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
| [`00_ARCHITECTURE.md`](00_ARCHITECTURE.md) | L0 Architecture | Cloud Grand Council (`linus` chair) | Template for system architecture, module boundaries, and code-owned contracts (auto-injected into local runs) |
| [`01_OMARCHY_AGENT_PROMPTS.md`](01_OMARCHY_AGENT_PROMPTS.md) | L0 Agent Constitution | Cloud Grand Council | Constitutional laws (`Law 1–12`), Merge Gates `G0–G5`, and machine-parseable `OMARCHY_VERDICT:` schemas |
| [`02_PRODUCTION_PLAN.md`](02_PRODUCTION_PLAN.md) | L0 Macro Plan | Cloud Grand Council | Template for macro phased roadmap (`Phase 0` → `Phase 3`) |
| [`AGENTS.md`](AGENTS.md) & [`agents.lock`](agents.lock) | L0 Identity | `parent` + `linus` | Canonical 9-seat persona table + single machine-readable model lock |
| [`docs/PRODUCT_SPEC.md`](docs/PRODUCT_SPEC.md) | L1 Product | `dhh` | Template for product use cases (`UC-01..UC-XX`), personas, stack/languages, and fail-closed degradation |
| [`docs/DEVELOPER_GUIDE.md`](docs/DEVELOPER_GUIDE.md) | L2 Onboarding | `knuth` | Day-1 human onboarding + Agile hierarchy (`Theme → Epic → Feature → Story → Task`), DoD, and QA templates |
| [`docs/SPRINT_DASHBOARD.md`](docs/SPRINT_DASHBOARD.md) | L3 Living State | `scrum` + `parent` | Living Sprint Dashboard (Session Resume Checkpoint + Executive & Team views with `UNMEASURED` honesty) |
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
# 1. Verify local two-family Ollama readiness (Family A: qwen3.8, Family B: gemma4)
scripts/ensure_local_agents.sh

# 2. Run a local coding / review / scrum seat (auto-injects 01_ laws + 00_ architecture)
scripts/run_local_agent.sh qweny   "Task packet..."
scripts/run_local_agent.sh moxie   "G5 peer review..."
scripts/run_local_agent.sh mitnick "Adversarial test plan..."
scripts/run_local_agent.sh scrum   "Audit SPRINT_DASHBOARD.md against git"

# 3. Refresh local vs. cloud token split
scripts/report_token_split.sh --markdown
```
