# Sterilized Governance Packets

Packets declare **`family`** only (`local_family_a` | `local_family_b`).
The exact Ollama model slug is read from [`agents.lock`](../../agents.lock) — never from the packet.

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
