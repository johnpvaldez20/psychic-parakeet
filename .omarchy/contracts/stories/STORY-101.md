# STORY-101: Idempotent Ledger Transaction

Must enforce prepare before commit.

- No state mutation is durable until Phase-2 commit succeeds.
- Verification failure must leave the base branch unchanged.
