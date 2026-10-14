# 02_PRODUCTION_PLAN.md — Macro Phased Roadmap to Production (Template)

**Document Role:** High-level phased delivery roadmap from Day-0 bootstrap to production release. Active sprint stories and the session resume checkpoint live in [`docs/SPRINT_DASHBOARD.md`](docs/SPRINT_DASHBOARD.md).

---

| Phase | Theme / Epic | Deliverables | Exit Criteria (DoD) |
|---|---|---|---|
| **Phase 0 — Bootstrap & Testing Jig** | Governance + Automated Verification | Build scaffold + Testing Jig (`TESTING_JIG_REPORT.md`) + Local 2-family Ollama check | Testing Jig green; `scrum` audit passes |
| **Phase 1 — Core Domain & Contracts** | Pure domain logic & fail-closed gates | `UC-01..UC-03` core modules + $\ge 85\%$ unit coverage | `G0–G5` green + Cloud `linus` `G3` `APPROVE` |
| **Phase 2 — Integration & Hardware/Edge Smoke** | End-to-end runtime & smoke verification | Target integration + `EVIDENCE.md` measured rows | Zero `P0` defects; all `UNMEASURED` items resolved or gated |
| **Phase 3 — Production Release Gate** | Full Grand Council Nobel Audit | Full branch review across all Cloud + Local seats | Unanimous `SHIP` ballot |
