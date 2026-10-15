# MOXIE_G4_TEST — Adversarial Fail-Closed Test Design (v2.3 Kernel)

**Role:** g4_test (moxie, Family B)
**Audit Target:** v2.3 Control-Plane / Kernel
**Objective:** Verify fail-closed behavior for all security and resource boundaries.

## Test Cases

ID: TC-V231-01
Description: Verify that a packet with a role not present in LEGAL_ROLES is rejected.
Target: .omarchy/omarchy.py:105
Coverage: MISSING

ID: TC-V231-02
Description: Verify that a packet claiming a family that does not match the seat binding in agents.lock is rejected.
Target: .omarchy/omarchy.py:123
Coverage: MISSING

ID: TC-V231-03
Description: Verify that a packet claiming a model slug that does not match the seat binding in agents.lock is rejected.
Target: .omarchy/omarchy.py:129
Coverage: MISSING

ID: TC-V231-04
Description: Verify that the kernel fails closed when agents.lock is missing from the filesystem.
Target: .omarchy/omarchy.py:55
Coverage: MISSING

ID: TC-V231-05
Description: Verify that agents.lock rows with fewer than 6 columns are ignored or cause a failure if no valid rows remain.
Target: .omarchy/omarchy.py:64
Coverage: MISSING

ID: TC-V231-06
Description: Verify that packet paths attempting to escape the sterilized root via ".." are blocked.
Target: .omarchy/omarchy.py:230
Coverage: EXISTING:test_sterilize_path_blocks_traversal

ID: TC-V231-07
Description: Verify that target_files paths attempting to escape the sterilized root are blocked.
Target: .omarchy/omarchy.py:230
Coverage: MISSING

ID: TC-V231-08
Description: Verify that model output containing unauthorized keys (outside the output contract) is rejected by the kernel.
Target: .omarchy/omarchy.py:530
Coverage: MISSING

ID: TC-V231-09
Description: Verify that the kernel aborts the transaction if the resulting file change is zero (no-op).
Target: .omarchy/batch_runner.py:200
Coverage: MISSING

ID: TC-V231-10
Description: Verify that the kernel rejects execution if the current worktree is dirty or on the wrong base branch.
Target: .omarchy/batch_runner.py:200
Coverage: MISSING

ID: TC-V231-11
Description: Verify that a failure/outage of the Ollama /api/tags endpoint results in an OmarchyError.
Target: .omarchy/omarchy.py:565
Coverage: MISSING

ID: TC-V231-12
Description: Verify that the kernel refuses to load a model that is not currently pulled in Ollama (weight_bytes == 0).
Target: .omarchy/omarchy.py:581
Coverage: MISSING

ID: TC-V231-13
Description: Verify that a request with a num_ctx that pushes the estimated total memory over MAX_FAMILY_BUDGET_BYTES is rejected.
Target: .omarchy/omarchy.py:593
Coverage: MISSING

ID: TC-V231-14
Description: Verify that a failure during the evict_model call (URLError) is caught and raised as an OmarchyError.
Target: .omarchy/batch_runner.py:88
Coverage: MISSING

ID: TC-V231-15
Description: Verify that the kernel detects and rejects a stale resume attempt where the state log is inconsistent with the worktree.
Target: .omarchy/batch_runner.py:92
Coverage: MISSING

ID: TC-V231-16
Description: Verify that a circular dependency in the packet queue (depends_on cycle) triggers a deadlock OmarchyError.
Target: .omarchy/batch_runner.py:155
Coverage: MISSING

ID: TC-V231-17
Description: Verify that the cloud_g3 role is correctly handled in the batch runner and does not trigger local family budget checks.
Target: .omarchy/batch_runner.py:165
Coverage: MISSING

ID: TC-V231-18
Description: Verify that ad-hoc CLI string failures (e.g., exit 64/66) are propagated as kernel failures.
Target: .omarchy/batch_runner.py:200
Coverage: MISSING

---
OMARCHY_VERDICT: REQUEST_CHANGES
BLOCKING_COUNT: 17
CITED_LOCATIONS: .omarchy/omarchy.py:105, .omarchy/omarchy.py:123, .omarchy/omarchy.py:129, .omarchy/omarchy.py:55, .omarchy/omarchy.py:64, .omarchy/omarchy.py:230, .omarchy/omarchy.py:530, .omarchy/batch_runner.py:200, .omarchy/omarchy.py:565, .omarchy/omarchy.py:581, .omarchy/omarchy.py:593, .omarchy/batch_runner.py:88, .omarchy/batch_runner.py:92, .omarchy/batch_runner.py:155, .omarchy/batch_runner.py:165
---
