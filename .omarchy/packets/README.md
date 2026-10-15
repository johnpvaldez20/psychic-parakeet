# Sterilized Governance Packets

Only JSON files here may be executed. Filenames starting with `_` are skipped by `--batch`.

```bash
# Causal A → B → A wave planner (no Ollama)
scripts/run_local_agent.sh --batch --dry-run

# Single packet
scripts/run_local_agent.sh _sample_packet.json --dry-run
```

Optional packet key: `"depends_on": ["other-packet-id"]` — required for Family A → B → A scheduling.
