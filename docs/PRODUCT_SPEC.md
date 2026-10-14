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

## 3. Use Cases (`UC-01..UC-XX`)

### `UC-01` — *<Use Case Title>*
- **Goal:**
- **Deterministic Behavior:**
- **Acceptance Criteria (`Given / When / Then`):**
- **Fail-Closed Degradation:**
