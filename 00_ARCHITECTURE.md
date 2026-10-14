# 00_ARCHITECTURE.md — System Architecture & Code-Owned Contracts (Template)

**Document Role:** Pure technical architecture, module boundaries, threading/concurrency rules, and mathematical/ABI invariants for this project.  
**Boundary:** Contains **zero** agent prompt laws (see [`01_OMARCHY_AGENT_PROMPTS.md`](01_OMARCHY_AGENT_PROMPTS.md)) and **zero** daily sprint state (see [`docs/SPRINT_DASHBOARD.md`](docs/SPRINT_DASHBOARD.md)). Sections inside `<!-- section:architecture-contracts -->` are automatically injected into every local coding and review run.

---

<!-- section:architecture-contracts -->
## 1. System Overview & Layer Boundaries

*(Replace with your project's high-level system diagram and layer firewall rules.)*

## 2. Module Ownership & Pure-Logic Extraction Map

Every module must separate **pure, deterministic policy/math/parser classes** ($\ge 85\%$ unit line coverage required) from thin OS/network/hardware glue:

| Module | Pure Testable Classes | OS / IO Glue Classes | Key Invariant |
|---|---|---|---|
| `core` | *e.g. `ContractValidator`, `StatePolicy`* | *e.g. `ServiceAdapter`* | Fail-closed on invalid input; zero silent fallbacks |

## 3. Code-Owned Contracts & Invariants

| Domain | Invariant Contract | Owner |
|---|---|---|
| **Input / Output ABI** | *Specify exact schemas, byte sizes, and reject reasons* | `core/` |
| **Concurrency / Threading** | *Specify thread owners and zero-allocation hot paths* | `core/` |
| **Fail-Closed Degradation** | *Specify exact user-visible status when resources/files are missing* | `core/` |
<!-- /section:architecture-contracts -->
