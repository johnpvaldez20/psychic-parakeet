# 02_CHALLENGE.r2 — Final adversarial review of the Omarchy v3.0 kernel specification

Reviewer: knuth · challenger · cloud · round 2

Object reviewed: `slices/s000-bootstrap/01_PLAN.r2.md`

## Round-1 finding disposition

| Finding | Status | r2 location and disposition |
|---|---|---|
| B01 | RESOLVED | `slices/s000-bootstrap/01_PLAN.r2.md:968-980`, with the complete-history test at `slices/s000-bootstrap/01_PLAN.r2.md:1611-1614`. T11 initializes once and T19 jumps to T12 without resetting round 2. |
| B02 | RESOLVED | `slices/s000-bootstrap/01_PLAN.r2.md:347-364`, tested at `slices/s000-bootstrap/01_PLAN.r2.md:1572-1574`. Required files are now outcome-specific. |
| B03 | RESOLVED | `slices/s000-bootstrap/01_PLAN.r2.md:120-127`, `slices/s000-bootstrap/01_PLAN.r2.md:461-468`, and `slices/s000-bootstrap/01_PLAN.r2.md:824-834`. PACKETS has a class, an exact contract, and one comparison point in ingest. |
| B04 | RESOLVED | `slices/s000-bootstrap/01_PLAN.r2.md:638-649`, tested at `slices/s000-bootstrap/01_PLAN.r2.md:1642-1645`. Planning lineage is explicit and duplicate-free. |
| B05 | RESOLVED | `slices/s000-bootstrap/01_PLAN.r2.md:620-628` and `slices/s000-bootstrap/01_PLAN.r2.md:662-668`. QA jobs share immutable dispatch commit `D_q`, and proof growth is excluded. |
| B06 | RESOLVED | `slices/s000-bootstrap/01_PLAN.r2.md:700-708` and `slices/s000-bootstrap/01_PLAN.r2.md:1145-1166`. Read lists carry commit/blob identities and record-time ingest checks them. The new source-verification defect below is distinct from the original stale-input acceptance. |
| B07 | RESOLVED | `slices/s000-bootstrap/01_PLAN.r2.md:36-43`, `slices/s000-bootstrap/01_PLAN.r2.md:275-296`, and `slices/s000-bootstrap/01_PLAN.r2.md:1057-1068`. Indices are unbounded and the dismissal loop is bounded. |
| B08 | RESOLVED | `slices/s000-bootstrap/01_PLAN.r2.md:930-946`, tested at `slices/s000-bootstrap/01_PLAN.r2.md:1611-1615`. Replay accepts only jobs in the emitted step. |
| B09 | RESOLVED | `slices/s000-bootstrap/01_PLAN.r2.md:1230-1240` and `slices/s000-bootstrap/01_PLAN.r2.md:1398-1402`. Coverage is content-based and independent of merge strategy. |
| B10 | RESOLVED | `slices/s000-bootstrap/01_PLAN.r2.md:79-90`, with tests at `slices/s000-bootstrap/01_PLAN.r2.md:1622-1636`. Both exception types now have complete handling contracts. |
| B11 | RESOLVED | `slices/s000-bootstrap/01_PLAN.r2.md:275-323`, with direct tests at `slices/s000-bootstrap/01_PLAN.r2.md:1530-1537`. |
| B12 | RESOLVED | `slices/s000-bootstrap/01_PLAN.r2.md:1489-1498` and `slices/s000-bootstrap/01_PLAN.r2.md:1670-1675`. The divergent-base bootstrap path now has end-to-end positive and negative tests. |
| N01 | RESOLVED | `slices/s000-bootstrap/01_PLAN.r2.md:1528-1530` defines the core-lock-plus-one-optional-row fixture exactly. |
| N02 | RESOLVED | `slices/s000-bootstrap/01_PLAN.r2.md:984-989`, tested at `slices/s000-bootstrap/01_PLAN.r2.md:1613-1616`. Stage-5 verdicts are explicitly advisory. |
| N03 | RESOLVED | `slices/s000-bootstrap/01_PLAN.r2.md:1264-1268`, with the CLI matrix at `slices/s000-bootstrap/01_PLAN.r2.md:1664-1670`. |

## Final-round findings

### B13 — Transition-driving proof fields are not bound to the slot bytes

- Classification: **BLOCKING**
- Location: `slices/s000-bootstrap/01_PLAN.r2.md:490-526`, `slices/s000-bootstrap/01_PLAN.r2.md:914-946`
- Finding: integrity verifies canonical row encoding, file hashes, commit shape, seat, attempt, and ordering, but never reparses an authored slot and compares the result with its row. A challenge file can contain `REQUEST_CHANGES` while its row says `verdict = APPROVE`; all listed checks pass and `derive` advances. The same gap applies to `status`, `blocking_count`, claimed prompt sha, QA mappings, and slot-derived `stage`/packet/round fields. Hashing bytes does not authenticate the interpretation that drives the machine.
- Required change: add a semantic-row integrity check that reparses every authored slot from the commit that introduced it and requires every parsed and slot-name-derived row field to match. Revalidate PACKETS and QA mappings, and add negative tests where immutable slot bytes disagree with otherwise well-formed row metadata.

### B14 — Forged cloud provenance can advance `next`, and `verify` does not recheck canonical inputs

- Classification: **BLOCKING**
- Location: `slices/s000-bootstrap/01_PLAN.r2.md:914-928`, `slices/s000-bootstrap/01_PLAN.r2.md:1218-1226`, `slices/s000-bootstrap/01_PLAN.r2.md:1673-1675`
- Finding: `SOURCE_MISMATCH` is deliberately “verify only”; T-E4 even requires a forged source row to make `next` return `DONE_BOOTSTRAP`. That violates the state-machine integrity contract: a fabricated cloud source can advance or terminate the slice until a separate command is run. Further, `verify` checks the source slot blob and ancestry, but does not rerun the read-list input checks. A descendant source commit containing the expected slot while changing a canonical REPO/SLOT input passes the stated source check; bootstrap sources are weaker still because ancestry is not checked.
- Required change: make source provenance part of the integrity gate used by `next` and every mutating command. For every cloud row, resolve its retained source, verify the source slot, and rerun the canonical SLOT/REPO input checks appropriate to `prompt_source`. A forged source must yield `REFUSE SOURCE_MISMATCH` from `next`. Replace T-E4's expected `DONE_BOOTSTRAP` and add a case where the source slot exists but a canonical input is stale or altered.

### B15 — Source-tag creation is non-atomic and has no recovery path

- Classification: **BLOCKING**
- Location: `slices/s000-bootstrap/01_PLAN.r2.md:1166-1173`, `slices/s000-bootstrap/01_PLAN.r2.md:1218-1225`
- Finding: `record` commits the proof row first and creates its mandatory source tag afterward. A crash or tag failure between those operations leaves a legitimate committed history that `verify` rejects. Re-running `record` cannot repair it because the slot is no longer a current job, and no repair command or idempotent recovery rule is specified.
- Required change: define crash-safe, idempotent ref/commit ordering—such as creating the source tag before the row commit and tolerating an orphan tag, or an explicit deterministic repair path—and test interruption at the boundary. A completed row must never be permanently unverifiable solely because the following tag operation did not run.

### B16 — A dismissed QA pathname may be re-added, making proof and packet mapping ambiguous

- Classification: **BLOCKING**
- Location: `slices/s000-bootstrap/01_PLAN.r2.md:347-364`, `slices/s000-bootstrap/01_PLAN.r2.md:1149-1167`, `slices/s000-bootstrap/01_PLAN.r2.md:1354-1362`
- Finding: ingest accepts a QA file whenever it is absent at the current head. A dismissed q1 file is absent, so a q2 QA report may add the same pathname again, possibly with different bytes and a different packet mapping. `required_files` is specified as a single path-to-sha map formed by the union of all rows, and QA evaluation says to use “the record that added” a file; both are undefined when two records added that path.
- Required change: either reserve every QA pathname permanently once it has appeared, or define generation-aware latest-live semantics for required hashes and packet mapping. Add a dismiss-then-readd test with different bytes and packet ids.

### B17 — File-block application destroys executable modes

- Classification: **BLOCKING**
- Location: `slices/s000-bootstrap/01_PLAN.r2.md:1289-1300`
- Finding: every block is forced to mode `0644`. A legal packet that edits an existing executable target such as `scripts/omarchy` silently removes its executable bit; the file-block schema provides no way to restore it. The resulting implementation can pass content-oriented tests yet break the shipped command.
- Required change: specify deterministic mode handling. At minimum preserve `100755` versus `100644` for existing targets and define the mode for new files. Add worktree and merge tests for editing an executable target.

### B18 — `open` accepts a base containing its inputs but cannot create the mandated OPEN commit

- Classification: **BLOCKING**
- Location: `slices/s000-bootstrap/01_PLAN.r2.md:590-603`, `slices/s000-bootstrap/01_PLAN.r2.md:1110-1122`
- Finding: `open` reads clean, committed input bytes from repo `HEAD`, and the schema permits `base_ref` to resolve to that same commit. But `allowed_changes(OPEN)` requires `slice.json` and `00_PROMPT.md` to be additions. If they already exist at `base_ref`, writing identical bytes stages no change, so `kernel_commit` rejects a configuration that passed every open precondition. The newly required staging-commit workflow is also absent from §20's deviations.
- Required change: either reject input paths already present at `base_ref` and specify/list the required separate staging commit as a deviation, or allow pre-existing identical inputs and define the corresponding exact OPEN change set. Test both the intended normal-slice topology and the rejection/acceptance boundary.

## Non-blocking finding

### N04 — Commit subjects are normative but not audited

- Classification: **NON-BLOCKING**
- Location: `slices/s000-bootstrap/01_PLAN.r2.md:570-590`, `slices/s000-bootstrap/01_PLAN.r2.md:914-923`
- Finding: §9.5 specifies an exact conventional-commit subject, while `FOREIGN_COMMIT` checks parents, trailers, proof-line count, and changes but not the subject.
- Required change: either include the subject in the commit audit and test it, or state that only the trailers and change set are normative.

The revision substantially improves reachability, replay ordering, bootstrap coverage, and testability, but the six blocking defects above leave legitimate histories unverifiable or permit transition state not justified by the recorded artifacts.

---
OMARCHY_VERDICT: REQUEST_CHANGES
BLOCKING_COUNT: 6
CITED_LOCATIONS: slices/s000-bootstrap/01_PLAN.r2.md:490-526, slices/s000-bootstrap/01_PLAN.r2.md:914-946, slices/s000-bootstrap/01_PLAN.r2.md:1218-1226, slices/s000-bootstrap/01_PLAN.r2.md:1166-1173, slices/s000-bootstrap/01_PLAN.r2.md:347-364, slices/s000-bootstrap/01_PLAN.r2.md:1149-1167, slices/s000-bootstrap/01_PLAN.r2.md:1289-1300, slices/s000-bootstrap/01_PLAN.r2.md:590-603, slices/s000-bootstrap/01_PLAN.r2.md:1110-1122
OMARCHY_PROMPT_SHA256: 80c678c18768765942699688ff60c760617f7776100553538e56ee82b7792708
---
