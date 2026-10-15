# STORY-BATCH: Causal Family A → B → A Demo

Demonstrates dependency-safe model waves on a 128GB box:

1. Family A implements a module.
2. Family B audits and expands tests (depends on step 1).
3. Family A optimizes against the audit suite (depends on step 2).

Blind sorting by model name is forbidden — the batch runner must emit three waves.
