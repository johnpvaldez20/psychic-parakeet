# UC-BATCH-B: Cross-Family Audit (Family B)

- Given `pkt-01-impl` completed, When `pkt-02-audit` runs, Then Family A was evicted (`keep_alive=0`) before Family B loaded.
- Given a mid-wave 2PC gate failure under `--keep-warm`, When the wave aborts, Then `evict_model` still runs in `finally`.
