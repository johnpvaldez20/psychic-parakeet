# 02_CHALLENGE.r1 — Adversarial review of the Omarchy v3.0 kernel specification

Reviewer: knuth · challenger · cloud · round 1

Object reviewed: `slices/s000-bootstrap/01_PLAN.r1.md`

## Verdict

`REQUEST_CHANGES`. The overall fixed-slot design is repairable, but the specification is not yet deterministic enough to implement literally. In particular, QA round 2 is reset to round 1, several legitimate failure rows fail the stated integrity check, the stage-3 output contract is undefined, parallel QA invalidates its own prompt-stability test, and cloud ingest proves slot ancestry without proving that the cloud seat saw the repository bytes named by its canonical prompt.

## Blocking findings

### B01 — QA round 2 is unreachable under the stated transition algorithm

- Classification: **BLOCKING**
- Location: `slices/s000-bootstrap/01_PLAN.r1.md:588-598`
- Finding: T18 sets `q = 2`, sets `active = E.red_packets`, and says to re-evaluate from T11. T11 unconditionally sets `q = 1` and `active = all packets`. A literal implementation therefore discards T18's values and re-enters round 1; T-M19's required q2 behavior cannot follow from the specification.
- Required change: separate one-time initialization from the per-round packet evaluation, or make T11 accept `(q, active)` as parameters and preserve T18's values. Add a transition test that derives the complete q1-RED → q2-proposal history, not merely a hand-constructed q2 state.

### B02 — Integrity requires files that legitimate failure rows intentionally do not create

- Classification: **BLOCKING**
- Location: `slices/s000-bootstrap/01_PLAN.r1.md:473-480`, `slices/s000-bootstrap/01_PLAN.r1.md:560-566`
- Finding: the `SLOT_SHA_MISMATCH` check says any row-named `slot` must exist at the tip. Yet `SEAT_FAILED` names the expected authored slot while creating only `<slot>.a<k>.rejected`, `CONTEXT_OVERFLOW` creates no slot, and `MERGE_FAILED APPLY_CONFLICT` may create no MERGE log. Thus the histories expected by T-M21/T-M22 become `SLOT_SHA_MISMATCH` before they can derive `HALT SEAT_FAILED` or `HALT CONTEXT_OVERFLOW`.
- Required change: define the exact required-file set per outcome. Require the authored slot only for `RECORDED`, the rejected file only when a failed row has `output_sha256`, and a MERGE log only when that row records its hash. Add integrity tests for all three fileless/alternate-file outcomes.

### B03 — Stage 3 has no representable prompt/output contract

- Classification: **BLOCKING**
- Location: `slices/s000-bootstrap/01_PLAN.r1.md:100-106`, `slices/s000-bootstrap/01_PLAN.r1.md:299-312`, `slices/s000-bootstrap/01_PLAN.r1.md:535-545`
- Finding: `03_PACKETS.json` is a cloud-authored slot with a required `prompt_sha256`, but `SlotClass` has no PACKETS member and `output_contract` accepts only a `SlotClass`. Cloud prompt composition nevertheless calls `output_contract(...)` for cloud jobs. `parse_packets` also has no expected-prompt-sha argument, while §13.4 requires the record path to enforce that value. Parent must invent a special case and its emitted contract.
- Required change: specify a PACKETS class (or an explicit separate packets-output-contract function), define its canonical prompt text, and define where expected prompt-sha comparison occurs. Add positive and mismatch tests for `03_PACKETS.json`.

### B04 — Challenge lineage duplicates the plan slot

- Classification: **BLOCKING**
- Location: `slices/s000-bootstrap/01_PLAN.r1.md:500-506`
- Finding: the challenge lineage is “every `01`/`02` slot before it, then `01_PLAN.rN`.” For both r1 and r2, the paired plan is already an earlier slot, so the literal list includes it twice. Since ordering and bytes determine `prompt_sha256`, this is not harmless prose ambiguity.
- Required change: give an exact, duplicate-free sequence, for example all completed earlier plan/challenge pairs followed once by the current plan. Add exact r1 and r2 lineage-order tests.

### B05 — Parallel QA cannot satisfy the promised byte-identical prompt

- Classification: **BLOCKING**
- Location: `slices/s000-bootstrap/01_PLAN.r1.md:505-509`, `slices/s000-bootstrap/01_PLAN.r1.md:540-545`, `slices/s000-bootstrap/01_PLAN.r1.md:1040-1044`
- Finding: QA excludes another seat's current `07_QA` slot, but its repo read list includes `tests/qa/<id>/**`. Recording the first QA seat adds files under that prefix, so rebuilding the second seat's prompt adds `REPO` lines and changes its sha. If “every slot” includes `PROOF.jsonl`, that file changes too. T-R7 requires the prompt to remain byte-identical, so the lineage table, prompt builder, and test disagree.
- Required change: pin a QA dispatch view and define each current-round QA prompt from that immutable view, excluding other current-round QA outputs and proof-log growth. State whether `PROOF.jsonl` is lineage; do not leave “every slot” to interpretation.

### B06 — Cloud ingest proves slot lineage but not repository-input provenance

- Classification: **BLOCKING**
- Location: `slices/s000-bootstrap/01_PLAN.r1.md:704-714`
- Finding: record-time lineage checking compares only lineage slot shas. Canonical cloud prompts also name repository files, but the read list contains no blob shas and ingest never checks their blobs at `R`. The D12 exception explicitly ignores an out-of-allow-list path when its blob at `R` equals the merge base. Consequently a QA ref can carry all canonical slot bytes while retaining pre-merge code; that stale code is ignored as “slice progress the seat never touched,” and the QA result is accepted as provenance for code the seat did not test.
- Required change: include expected commit/blob shas for every cloud `REPO` input in the canonical prompt and require those blobs at `source_commit` to match. Preserve parallel QA by pinning all QA jobs to one dispatch view. Add a negative ingest test with exact lineage slots but stale target-file content.

### B07 — Legal QA-dismissal histories exceed the slot grammar

- Classification: **BLOCKING**
- Location: `slices/s000-bootstrap/01_PLAN.r1.md:252-256`, `slices/s000-bootstrap/01_PLAN.r1.md:593-598`, `slices/s000-bootstrap/01_PLAN.r1.md:668-674`
- Finding: each `DISMISS_QA_TEST` ruling can delete any non-empty subset of existing QA files and trigger another evaluation. The number of QA files is unbounded, but EVAL filenames permit only indices 1–9. A legitimate sequence of nine one-file dismissals asks T16 to create `EVAL.10`, which `SLOT` rejects. The ruling index has a different unexplained ceiling of 99.
- Required change: either use an unbounded canonical positive-integer grammar for EVAL/ruling indices or impose and validate a budget that makes the filename bounds sufficient. Test the boundary and prove the dismissal loop terminates within it.

### B08 — Replay accepts histories that `next` and `run` declare out of order

- Classification: **BLOCKING**
- Location: `slices/s000-bootstrap/01_PLAN.r1.md:590-599`, `slices/s000-bootstrap/01_PLAN.r1.md:719-726`
- Finding: T13 says a runnable KERNEL job pre-empts all local jobs, and `run` executes a newly runnable KERNEL job before continuing the family session. But replay deliberately uses the full job set behind T13–T15 and accepts a row for *any* such job. A forged local row inserted while `next` says only `NEXT KERNEL` therefore passes replay. T-M28 tests presentation priority, not rejection of that forged history.
- Required change: define one legal ordering. If kernel pre-emption is normative, replay must accept only the emitted step's jobs and a test must reject the skipped-kernel history. If independent reordering is intended, remove the pre-emption claim and specify how an authorized command can produce that history.

### B09 — Post-merge verification silently requires an unspecified Git merge strategy

- Classification: **BLOCKING**
- Location: `slices/s000-bootstrap/01_PLAN.r1.md:740-748`
- Finding: `pipeline-authored` requires the last first-parent commit to be “a merge of a slice.” The approved workflow says the human merges s001 by PR, but neither §13.8, §17, nor §20 requires a merge commit. A legitimate squash, rebase, or fast-forward PR merge changes a bootstrap file, misses both pipeline labels, and becomes `FOREIGN_EDIT`.
- Required change: either make merge-commit integration a normative human precondition and test it, or define provenance recognition that works for every permitted PR merge strategy. List this workflow restriction as a deviation if it is retained.

### B10 — Publicly required exception types are undefined

- Classification: **BLOCKING**
- Location: `slices/s000-bootstrap/01_PLAN.r1.md:69-75`, `slices/s000-bootstrap/01_PLAN.r1.md:130-136`, `slices/s000-bootstrap/01_PLAN.r1.md:830-836`
- Finding: the public contract says `apply_diff` raises `MergeConflict` and K5/T-O2 require `ResidencyError`, but neither type appears in the exhaustive exception table. Their fields, inheritance, CLI behavior, and whether they consume an attempt are unspecified.
- Required change: add both types to §2.2 with exact inheritance and handling, or replace them everywhere with an already-defined type and code. Align the named tests with that decision.

### B11 — The required tests do not decide the slot grammar

- Classification: **BLOCKING**
- Location: `slices/s000-bootstrap/01_PLAN.r1.md:239-267`, `slices/s000-bootstrap/01_PLAN.r1.md:920-1049`
- Finding: `SLOT` is security- and replay-critical and `parse_slot_name` is public, but §18 has no table-driven test of accepted names, rejected near-misses, parsed fields, index bounds, rejected-output names, or the agreement between §5.2 and §5.3. Existing tests incidentally use a few names; they do not make the grammar decidable as a contract.
- Required change: add direct slot-name tests covering every alternative and malformed boundary, including all kernel-derived companions and rejected files. Resolve B07 before fixing the expected index cases.

### B12 — The unique s000 bootstrap-ingest path has no end-to-end acceptance test

- Classification: **BLOCKING**
- Location: `slices/s000-bootstrap/01_PLAN.r1.md:909-916`, `slices/s000-bootstrap/01_PLAN.r1.md:970-1049`
- Finding: T-M30 starts from prebuilt rows, and T-I6 checks only a bootstrap prompt sha. No test opens s000 from `v2.3.1-attempt1`, records planner and challenger refs forked from the later v3 history, verifies commit/row correspondence, reaches `DONE_BOOTSTRAP`, and obtains the required `verify --repo` labels. This divergent-base path is the justification for D12 and is the only migration path that can create the claimed real s000 proof chain.
- Required change: add a tmp-repo end-to-end test that follows §17.3 exactly, plus negative variants for a stale/missing challenged plan and a forged source commit. The test must assert the final chain, commit trailers, source provenance, `DONE_BOOTSTRAP`, and coverage labels.

## Non-blocking findings

### N01 — Optional-lock invariant wording is needlessly ambiguous

- Classification: **NON-BLOCKING**
- Location: `slices/s000-bootstrap/01_PLAN.r1.md:184-193`, `slices/s000-bootstrap/01_PLAN.r1.md:934-937`
- Finding: the optional file cannot satisfy the full §3.2 invariants by itself because it has no host, planner, or local families. T-L13 likely means “parse each optional row after union with the core lock,” but does not say so.
- Required change: state that exact fixture construction.

### N02 — Stage-5 verdict values have no state-machine meaning

- Classification: **NON-BLOCKING**
- Location: `slices/s000-bootstrap/01_PLAN.r1.md:603-614`
- Finding: stage 5 requires verdict trailers but the machine proceeds identically for `APPROVE`, `REQUEST_CHANGES`, and `REJECT`. This is consistent with the approved plan's “both verdict trailers parse” exit, but surprising enough to invite an accidental implementation branch.
- Required change: state explicitly that stage-5 verdict values are advisory synthesis input and never transition controls.

### N03 — The exact CLI boundary remains weakly tested

- Classification: **NON-BLOCKING**
- Location: `slices/s000-bootstrap/01_PLAN.r1.md:619-636`, `slices/s000-bootstrap/01_PLAN.r1.md:920-1049`
- Finding: machine tests cover examples, but no dedicated CLI test exercises argparse wiring, stdout/stderr separation, and all category exit codes through `omarchy.__main__`.
- Required change: add a small CLI test matrix; this can be done without changing the design.

---
OMARCHY_VERDICT: REQUEST_CHANGES
BLOCKING_COUNT: 12
CITED_LOCATIONS: slices/s000-bootstrap/01_PLAN.r1.md:588-598, slices/s000-bootstrap/01_PLAN.r1.md:473-480, slices/s000-bootstrap/01_PLAN.r1.md:100-106, slices/s000-bootstrap/01_PLAN.r1.md:500-506, slices/s000-bootstrap/01_PLAN.r1.md:505-509, slices/s000-bootstrap/01_PLAN.r1.md:704-714, slices/s000-bootstrap/01_PLAN.r1.md:252-256, slices/s000-bootstrap/01_PLAN.r1.md:590-599, slices/s000-bootstrap/01_PLAN.r1.md:740-748, slices/s000-bootstrap/01_PLAN.r1.md:69-75, slices/s000-bootstrap/01_PLAN.r1.md:239-267, slices/s000-bootstrap/01_PLAN.r1.md:909-916
OMARCHY_PROMPT_SHA256: bb4e4b8c69e3e14aaa9a02aba7f66725bb0d4a7f1dc143d78849f631d4d2c8b8
---
