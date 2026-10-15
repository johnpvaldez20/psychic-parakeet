# Product Specification (Template)

**Owner:** `dhh` (Cloud Grand Council) + Human Product Lead.  
**Honesty Rule:** Never invent outputs, sensor states, or background sync success. Missing dependencies or capabilities must surface honestly.

---

## 1. Product One-Liner & Personas

| Persona | Needs |
|---|---|
| **Primary User** | *Describe primary user needs* |
| **Operator / Admin / Trainer** | *Describe secondary user needs* |

## 2. Languages & Runtime Stack

| Tier | Language / Framework | Role |
|---|---|---|
| **Client / Edge Runtime** | *e.g. Kotlin / Rust / Swift / TypeScript* | *Core runtime responsibility* |
| **Host Tooling & Testing Jig** | *Python 3 + Bash* | *Coverage aggregation, UC traceability, artifact verification* |
| **Cloud / Server** | *Docker / Rust / Python / Postgres / MQTT* | *API, storage, queues* |

## 3. Use Cases (`UC-00..UC-XX`)

### `UC-00` — Bootstrap Testing Jig & Coverage Readout
- **Goal:** Every project has a host command that produces `docs/TESTING_JIG_REPORT.md` with honest `UNMEASURED` cells when inputs are absent.
- **Deterministic Behavior:** Running the jig never fabricates coverage percentages or pass counts.
- **Acceptance Criteria (`Given / When / Then`):**
  - Given no coverage artifacts, When the jig runs, Then the report marks metrics `UNMEASURED`.
  - Given Gate G0, When a builder lands the jig script, Then only packet `allowed_files` are mutated in the isolated worktree.
- **Fail-Closed Degradation:** Missing inputs → explicit `UNMEASURED`, never silent zeros.

### `UC-01` — *<Use Case Title>*
- **Goal:**
- **Deterministic Behavior:**
- **Acceptance Criteria (`Given / When / Then`):**
- **Fail-Closed Degradation:**
