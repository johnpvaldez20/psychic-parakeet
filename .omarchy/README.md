# `.omarchy/` — Sterilized Runtime & Governance Kernel

| Path | Role |
|---|---|
| [`omarchy.py`](omarchy.py) | 2PC multi-agent kernel (Story/UC, worktrees, Ollama serialize, gates) |
| [`batch_runner.py`](batch_runner.py) | Causal family waves + `finally` eviction (A→B→A safe) |
| [`packets/`](packets/) | Only legal execution inputs (`*.json`; `_*.json` skipped by batch) |
| [`contracts/stories/`](contracts/stories/) | Story markdown contracts (`STORY-*.md`) |
| [`contracts/use_cases/`](contracts/use_cases/) | Use-case markdown contracts (`UC-*.md`) |
| `worktrees/` | Ephemeral git worktrees (gitignored) |
| `state/` | Completed packet ids for resume (gitignored) |
| `local-agent-proof.log` | Flocked G0 proof log (gitignored) |

Invoke via `scripts/run_local_agent.sh <packet.json>` or `--batch`.
