# Sterilized Governance Packets

Packets declare a required **`role`** (`build` | `g5_review` | `g4_test` | `scrum_audit` | `cloud_g3`).
The kernel maps `role` → seat → `family` / model via [`agents.lock`](../../agents.lock).
Optional `"family"` must match the seat row; packets never invent model slugs.

| Role | Seat | Family |
|---|---|---|
| `build` | `qweny` | `local_family_a` |
| `g5_review` | `moxie` | `local_family_b` |
| `g4_test` | `moxie` | `local_family_b` |
| `scrum_audit` | `scrum` | `local_family_a` |
| `cloud_g3` | `linus` | cloud (dry-run only on local kernel) |

```bash
scripts/run_local_agent.sh --batch --dry-run
```

Expected waves (models from agents.lock):

```text
Wave 1: family='local_family_a' model='qwen3.8:27b-mlx' -> packets=['pkt-01-impl']
Wave 2: family='local_family_b' model='gemma4:31b-mlx'  -> packets=['pkt-02-audit']
Wave 3: family='local_family_a' model='qwen3.8:27b-mlx' -> packets=['pkt-03-optimize']
```

Optional: `"depends_on": ["other-packet-id"]` for causal A→B→A ordering.
Filenames starting with `_` are skipped by `--batch`.
