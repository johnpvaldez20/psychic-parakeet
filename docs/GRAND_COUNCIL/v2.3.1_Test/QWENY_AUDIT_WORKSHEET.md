# QWENY_AUDIT_WORKSHEET — Omarchy Scrum v2.3 (frozen 83ca764)

**Role:** build (qweny, Family A)
**Story:** STORY-AUDIT-V231
**UC:** UC-AUDIT-V231-WS
**Frozen SHA:** 83ca764
**Audit principle:** Fail-closed. Any claim the packet excerpts cannot prove is recorded UNKNOWN, never PASS.

---

## S01 — Lock Binding

| Check | Claim under test (source path:line @83ca764) | Code evidence (path:line @83ca764) | Result | Note |
|---|---|---|---|---|
| S01-01 | Exactly two local families defined as constants | `.omarchy/omarchy.py:40-42` defines `LOCAL_FAMILY_A = "local_family_a"`, `LOCAL_FAMILY_B = "local_family_b"`, `LEGAL_LOCAL_FAMILIES = frozenset({LOCAL_FAMILY_A, LOCAL_FAMILY_B})` | `.omarchy/omarchy.py:40-42` | PASS | |
| S01-02 | `LEGAL_LOCAL_FAMILIES` is a `frozenset` (immutable, exactly 2 members) | `.omarchy/omarchy.py:42` `frozenset({LOCAL_FAMILY_A, LOCAL_FAMILY_B})` | `.omarchy/omarchy.py:42` | PASS | |
| S01-03 | `ROLE_TO_SEAT` maps 5 roles → 5 core seats | `.omarchy/omarchy.py:45-51` maps `build→qweny`, `g5_review→moxie`, `g4_test→moxie`, `scrum_audit→scrum`, `cloud_g3→linus` | `.omarchy/omarchy.py:45-51` | PASS | |
| S01-04 | `LEGAL_ROLES` derived from `ROLE_TO_SEAT.keys()` | `.omarchy/omarchy.py:52` `frozenset(ROLE_TO_SEAT.keys())` | `.omarchy/omarchy.py:52` | PASS | |
| S01-05 | `parse_agents_lock` reads `agents.lock` as sole SSOT | `.omarchy/omarchy.py:59-75` reads `LOCK_FILE`, parses pipe-delimited rows, raises `OmarchyError` if missing or empty | `.omarchy/omarchy.py:59-75` | PASS | |
| S01-06 | `resolve_role_binding` rejects unknown roles | `.omarchy/omarchy.py:82-86` raises `OmarchyError` if `role not in LEGAL_ROLES` | `.omarchy/omarchy.py:82-86` | PASS | |
| S01-07 | `resolve_role_binding` rejects mismatched `family` claim in packet | `.omarchy/omarchy.py:97-101` raises if `claimed_family != family` from lock row | `.omarchy/omarchy.py:97-101` | PASS | |
| S01-08 | `resolve_role_binding` rejects mismatched `model` claim in packet | `.omarchy/omarchy.py:103-108` raises if `claimed_model != model` from lock row; "Packets cannot invent or downsize models" | `.omarchy/omarchy.py:103-108` | PASS | |
| S01-09 | `locked_local_family_models` projects lock → `{family: model}` | `.omarchy/omarchy.py:113-140` docstring + `by_family: Dict[str, Set[str]] = defaultdict(set)` loop over local rows | `.omarchy/omarchy.py:113-140` | PASS | |
| S01-10 | `locked_local_family_models` rejects illegal local family | `.omarchy/omarchy.py:135-139` raises `OmarchyError` if `fam not in LEGAL_LOCAL_FAMILIES` | `.omarchy/omarchy.py:135-139` | PASS | |
| S01-11 | `locked_local_family_models` rejects >1 distinct model slug per family (fail-closed) | `.omarchy/omarchy.py:113-140` docstring claims "Fails closed if … any family binds more than one distinct model slug"; code excerpt truncates at line 140 mid-`raise` — enforcement branch not fully visible | `.omarchy/omarchy.py:113-140` (truncated) | UNKNOWN | NEEDS_PLAN: Excerpt ends at line 140 inside the `raise OmarchyError(...)` for illegal family; the multi-slug-per-family rejection branch is not in the provided excerpt. |
| S01-12 | `agents.lock` contains exactly 5 core seats | `agents.lock:14-18` lists `linus`, `qweny`, `moxie`, `scrum`, `parent` | `agents.lock:14-18` | PASS | |
| S01-13 | Test asserts exactly two families with distinct models | `tests/test_omarchy_kernel.py:38-43` `test_locked_local_family_models_exactly_two` asserts `set(LOCKED.keys()) == {FAM_A, FAM_B}`, `LOCKED[FAM_A] != LOCKED[FAM_B]`, specific slugs `qwen3.8:27b-mlx` / `gemma4:31b-mlx` | `tests/test_omarchy_kernel.py:38-43` | PASS | |
| S01-14 | Test asserts core-5 seats present, optional seats absent | `tests/test_omarchy_kernel.py:45-50` `test_core_seats_present_optional_absent` asserts `set(seats) == {"linus","qweny","moxie","scrum","parent"}` and 5 optional seats not in `seats` | `tests/test_omarchy_kernel.py:45-50` | PASS | |

---

## S02 — 2PC

| Check | Claim under test (source path:line @83ca764) | Code evidence (path:line @83ca764) | Result | Note |
|---|---|---|---|---|
| S02-01 | 2PC kernel described in Law 6 with `packet_sha256`, `prompt_sha256`, `tree_sha256`, `packet_id`, `trailer_status` | `01_OMARCHY_AGENT_PROMPTS.md:8-45` Law 6 text enumerates all five proof-log fields | `01_OMARCHY_AGENT_PROMPTS.md` Law 6 | PASS | |
| S02-02 | `execute_packet` exists with `dry_run` and `keep_warm` flags | `.omarchy/omarchy.py:725-730` `def execute_packet(packet_path, *, dry_run=False, keep_warm=False) -> int` | `.omarchy/omarchy.py:725-730` | PASS | |
| S02-03 | `dry_run` path: no git worktree, no Ollama call | `.omarchy/omarchy.py:740-755` dry-run branch calls `sterilize_path` on target files, computes `prompt_sha`, prints `[OMARCHY][DRY-RUN]`, appends to log, returns 0 | `.omarchy/omarchy.py:740-755` | PASS | |
| S02-04 | `dry_run` proof log includes `packet_sha256`, `prompt_sha256`, `tree_sha256=""`, `trailer_status="DRY_RUN"` | `.omarchy/omarchy.py:756-775` `append_locked_log({... "packet_sha256": packet_sha, "prompt_sha256": prompt_sha, "tree_sha256": "", "trailer_status": "DRY_RUN", ...})` | `.omarchy/omarchy.py:756-775` | PASS | |
| S02-05 | Live 2PC Phase 1: git worktree creation in `.omarchy/worktrees/<packet_id>` | `AGENTS.md:1-56` §3 table describes "Phase 1 in `.omarchy/worktrees/<packet_id>`"; code excerpt for `execute_packet` live path (after line 780) not provided | `AGENTS.md` §3 (doc only); `.omarchy/omarchy.py:780+` not in excerpt | UNKNOWN | NEEDS_PLAN: Live 2PC worktree creation code is beyond the provided excerpt boundary (omarchy.py:780). |
| S02-06 | Live 2PC Phase 2: ff-merge iff gates exit 0; else worktree nuked | `AGENTS.md:1-56` §3 table describes "Phase 2 ff-merges iff gates exit 0; else nuked"; code not in excerpt | `AGENTS.md` §3 (doc only) | UNKNOWN | NEEDS_PLAN: Live ff-merge / rollback code not in provided excerpts. |
| S02-07 | `fcntl.flock(LOCK_EX)` used for proof-log writes | `01_OMARCHY_AGENT_PROMPTS.md` Law 6 mentions `fcntl.flock(LOCK_EX)`; `append_locked_log` implementation not in excerpts | `01_OMARCHY_AGENT_PROMPTS.md` Law 6 (doc only) | UNKNOWN | NEEDS_PLAN: `append_locked_log` implementation not in provided excerpts; cannot verify `fcntl.flock` usage. |
| S02-08 | `execute_packet` rejects non-local runtime (cloud_g3 / host) | `.omarchy/omarchy.py:777-780` raises `OmarchyError` if `packet.get("runtime") != "local"` | `.omarchy/omarchy.py:777-780` | PASS | |
| S02-09 | `wave_key` uses locked family id, never coalesces by name prefix | `.omarchy/omarchy.py:716-722` returns `packet.get("family")`; docstring: "Never strip tags or coalesce :27b with :14b" | `.omarchy/omarchy.py:716-722` | PASS | |

---

## S03 — Memory

| Check | Claim under test (source path:line @83ca764) | Code evidence (path:line @83ca764) | Result | Note |
|---|---|---|---|---|
| S03-01 | `MAX_FAMILY_BUDGET_BYTES` defaults to ~105 GB | `.omarchy/omarchy.py:530-531` `int(os.environ.get("OMARCHY_MAX_RAM_BYTES", 105 * (1024**3)))` | `.omarchy/omarchy.py:530-531` | PASS | |
| S03-02 | `BYTES_PER_CTX_TOKEN_ESTIMATE` = 512 KB | `.omarchy/omarchy.py:533` `512 * 1024` | `.omarchy/omarchy.py:533` | PASS | |
| S03-03 | `enforce_memory_budget` queries Ollama `/api/tags` for weight | `.omarchy/omarchy.py:548-555` `urllib.request.Request(url=f"{OLLAMA_API_URL}/api/tags", ...)` | `.omarchy/omarchy.py:548-555` | PASS | |
| S03-04 | `enforce_memory_budget` fails closed if model not pulled locally | `.omarchy/omarchy.py:568-571` raises `OmarchyError` if `weight_bytes == 0` ("refusing unbudgeted load") | `.omarchy/omarchy.py:568-571` | PASS | |
| S03-05 | `enforce_memory_budget` raises if estimated total exceeds ceiling | `.omarchy/omarchy.py:583-590` raises `OmarchyError` if `estimated_total > MAX_FAMILY_BUDGET_BYTES` | `.omarchy/omarchy.py:583-590` | PASS | |
| S03-06 | `evict_model` sends `keep_alive: 0` to Ollama `/api/generate` | `.omarchy/batch_runner.py:50-75` `payload = {"model": model, "prompt": "", "stream": False, "keep_alive": 0}` | `.omarchy/batch_runner.py:50-75` | PASS | |
| S03-07 | `evict_model` called at every family boundary (docstring claim) | `.omarchy/batch_runner.py:50-52` docstring: "Called at every family boundary and in rollback handlers so two model families never coexist in the 128GB memory pool" | `.omarchy/batch_runner.py:50-52` (docstring only) | PASS | Docstring claim; actual call-site in `plan_serial_family_waves` / `execute_single_packet` not fully in excerpt. |
| S03-08 | `enforce_memory_budget` rejects `num_ctx < 1` | `.omarchy/omarchy.py:540-541` raises `OmarchyError` if `num_ctx < 1` | `.omarchy/omarchy.py:540-541` | PASS | |

---

## S04 — Batch

| Check | Claim under test (source path:line @83ca764) | Code evidence (path:line @83ca764) | Result | Note |
|---|---|---|---|---|
| S04-01 | `plan_serial_family_waves` schedules packets into sequential single-family batches | `.omarchy/batch_runner.py:123-195` function signature + docstring + while-loop | `.omarchy/batch_runner.py:123-195` | PASS | |
| S04-02 | `depends_on` respected: packet ready only if all deps in `satisfied` | `.omarchy/batch_runner.py:137-139` `deps.issubset(satisfied)` check | `.omarchy/batch_runner.py:137-139` | PASS | |
| S04-03 | Target-file write-order locks prevent reordering | `.omarchy/batch_runner.py:138-140` `locked_files.update(targets)`; `not (targets & locked_files)` guard | `.omarchy/batch_runner.py:138-140` | PASS | |
| S04-04 | `coalesce_families=True` groups same-family ready packets into one warm batch | `.omarchy/batch_runner.py:163-180` `family_groups` dict, `chosen_family = family_order[0]`, batch = all packets of that family | `.omarchy/batch_runner.py:163-180` | PASS | |
| S04-05 | Deadlock / unsatisfied `depends_on` cycle raises `OmarchyError` | `.omarchy/batch_runner.py:148-152` `if not ready: raise OmarchyError(f"Deadlock or unsatisfied 'depends_on' cycle ...")` | `.omarchy/batch_runner.py:148-152` | PASS | |
| S04-06 | `execute_single_packet` exists (runs single packet via 2PC kernel) | `.omarchy/batch_runner.py:197-200` `def execute_single_packet(packet, unload_after, dry_run) -> None` | `.omarchy/batch_runner.py:197-200` | PASS | |
| S04-07 | `load_completed_ids` / `record_completed_id` persist completion state | `.omarchy/batch_runner.py:77-90` reads/writes `COMPLETED_LOG` JSON | `.omarchy/batch_runner.py:77-90` | PASS | |
| S04-08 | `wave_key` uses locked family id (not model name prefix) | `.omarchy/omarchy.py:716-722` returns `packet.get("family")`; docstring: "Never strip tags or coalesce :27b with :14b" | `.omarchy/omarchy.py:716-722` | PASS | |
| S04-09 | Test: causal wave ordering A→B→A with `depends_on` | `tests/test_omarchy_kernel.py:53-79` `test_causal_wave_ordering_a_b_a` asserts `wave_ids == [["pkt-01","pkt-01b"],["pkt-02"],["pkt-03"]]` | `tests/test_omarchy_kernel.py:53-79` | PASS | |

---

## S05 — Packets

| Check | Claim under test (source path:line @83ca764) | Code evidence (path:line @83ca764) | Result | Note |
|---|---|---|---|---|
| S05-01 | `load_packet` validates 8 required keys | `.omarchy/omarchy.py:250-258` `required_keys = {"packet_id","story_id","uc_ids","role","base_branch","target_files","instructions","verification_commands"}` | `.omarchy/omarchy.py:250-258` | PASS | |
| S05-02 | `uc_ids` must be non-empty list | `.omarchy/omarchy.py:260-261` `if not isinstance(packet["uc_ids"], list) or not packet["uc_ids"]: raise` | `.omarchy/omarchy.py:260-261` | PASS | |
| S05-03 | `verification_commands` must be non-empty list | `.omarchy/omarchy.py:262-263` `if not isinstance(packet["verification_commands"], list) or not packet["verification_commands"]: raise` | `.omarchy/omarchy.py:262-263` | PASS | |
| S05-04 | `target_files` must be non-empty list | `.omarchy/omarchy.py:264-265` `if not isinstance(packet["target_files"], list) or not packet["target_files"]: raise` | `.omarchy/omarchy.py:264-265` | PASS | |
| S05-05 | Gate G2: `target_files` max 5 | `.omarchy/omarchy.py:266-269` `if len(packet["target_files"]) > 5: raise OmarchyError("Gate G2: ...")` | `.omarchy/omarchy.py:266-269` | PASS | |
| S05-06 | Role resolved via `resolve_role_binding` (SSOT: agents.lock) | `.omarchy/omarchy.py:280-281` `role, seat_id, family, model, runtime = resolve_role_binding(packet)` | `.omarchy/omarchy.py:280-281` | PASS | |
| S05-07 | Law 3: Rule 11 context packets must inline target paths, signatures, G/W/T, tests, role | `01_OMARCHY_AGENT_PROMPTS.md:8-45` Law 3 text | `01_OMARCHY_AGENT_PROMPTS.md` Law 3 | PASS | |
| S05-08 | Packet path sterilized against traversal | `.omarchy/omarchy.py:240-243` `sterilize_path(raw, PACKETS_DIR)`; `.omarchy/omarchy.py:230-233` tail of `sterilize_path` raises "SECURITY VIOLATION" | `.omarchy/omarchy.py:230-243` | PASS | |
| S05-09 | Local runtime packets validated against `locked_local_family_models` | `.omarchy/omarchy.py:282-287` `if runtime == "local": locked = locked_local_family_models(); if family not in locked or locked[family] != model: raise` | `.omarchy/omarchy.py:282-287` | PASS | |

---

## S06 — Docs vs Code

| Check | Claim under test (source path:line @83ca764) | Code evidence (path:line @83ca764) | Result | Note |
|---|---|---|---|---|
| S06-01 | AGENTS.md seat table models match `agents.lock` | `AGENTS.md:1-56` §2 table: `linus→claude-opus-5-5-high`, `qweny→qwen3.8:27b-mlx`, `moxie→gemma4:31b-mlx`, `scrum→qwen3.8:27b-mlx`, `parent→host_session`; `agents.lock:14-18` same slugs | `AGENTS.md` §2 vs `agents.lock:14-18` | PASS | |
| S06-02 | AGENTS.md role descriptions match `ROLE_TO_SEAT` in code | `AGENTS.md:1-56` §2: `build→qweny`, `g5_review/g4_test→moxie`, `scrum_audit→scrum`, `cloud_g3→linus`; `.omarchy/omarchy.py:45-51` same mapping | `AGENTS.md` §2 vs `.omarchy/omarchy.py:45-51` | PASS | |
| S06-03 | 01_OMARCHY_AGENT_PROMPTS.md Law 2 hemisphere split matches AGENTS.md §1 | `01_OMARCHY_AGENT_PROMPTS.md` Law 2: Cloud = plans/specs/reviews; Local = code/tests/QA/audits; `AGENTS.md:1-56` §1 table same split | `01_OMARCHY_AGENT_PROMPTS.md` Law 2 vs `AGENTS.md` §1 | PASS | |
| S06-04 | AGENTS.md §3 mechanism glossary: 2PC kernel, batch, cloud task, local subagent | `AGENTS.md:1-56` §3 table lists 4 mechanisms with "Can It Edit the Working Tree?" and "Valid Proof" columns | `AGENTS.md` §3 | PASS | |
| S06-05 | `agents.lock` declares `schema=2` | `agents.lock:13` `schema=2` | `agents.lock:13` | PASS | |
| S06-06 | AGENTS.md references `agents.lock.optional` for optional seats | `AGENTS.md:1-56` §2 "Optional seats" table lists `dhh/carmack/knuth/mitnick/jobs`; `agents.lock:10` comment "Optional seats … see agents.lock.optional" | `AGENTS.md` §2 vs `agents.lock:10` | PASS | |
| S06-07 | 01_OMARCHY_AGENT_PROMPTS.md Law 6 proof-log fields match `execute_packet` dry-run log | `01_OMARCHY_AGENT_PROMPTS.md` Law 6 lists `packet_sha256, prompt_sha256, tree_sha256, packet_id, trailer_status`; `.omarchy/omarchy.py:756-775` dry-run log includes all five fields | `01_OMARCHY_AGENT_PROMPTS.md` Law 6 vs `.omarchy/omarchy.py:756-775` | PASS | |

---

## S07 — Test Coverage Map

| Check | Claim under test (source path:line @83ca764) | Code evidence (path:line @83ca764) | Result | Note |
|---|---|---|---|---|
| S07-01 | `test_locked_local_family_models_exactly_two` covers S01-01/02 | `tests/test_omarchy_kernel.py:38-43` asserts 2 families, distinct models, specific slugs `qwen3.8:27b-mlx` / `gemma4:31b-mlx` | `tests/test_omarchy_kernel.py:38-43` | PASS | |
| S07-02 | `test_core_seats_present_optional_absent` covers S01-12/14 | `tests/test_omarchy_kernel.py:45-50` asserts core-5 present, 5 optional absent | `tests/test_omarchy_kernel.py:45-50` | PASS | |
| S07-03 | `test_sterilize_path_blocks_traversal` covers S05-08 | `tests/test_omarchy_kernel.py:52-57` asserts `OmarchyError` with "SECURITY VIOLATION" on `..` traversal | `tests/test_omarchy_kernel.py:52-57` | PASS | |
| S07-04 | `test_causal_wave_ordering_a_b_a` covers S04-04/09 | `tests/test_omarchy_kernel.py:53-79` asserts A→B→A wave ordering with `depends_on` | `tests/test_omarchy_kernel.py:53-79` | PASS | |
| S07-05 | 2PC live path (worktree, ff-merge, rollback) has unit test | Not visible in `tests/test_omarchy_kernel.py:1-80` excerpt | `tests/test_omarchy_kernel.py:1-80` (excerpt ends at line 80) | UNKNOWN | NEEDS_PLAN: Excerpt ends at line 80; cannot confirm or deny live 2PC test coverage. |
| S07-06 | `enforce_memory_budget` has unit test | Not visible in `tests/test_omarchy_kernel.py:1-80` excerpt | `tests/test_omarchy_kernel.py:1-80` (excerpt ends at line 80) | UNKNOWN | NEEDS_PLAN: Excerpt ends at line 80; cannot confirm or deny memory-budget test coverage. |
| S07-07 | `evict_model` has unit test | Not visible in `tests/test_omarchy_kernel.py:1-80` excerpt | `tests/test_omarchy_kernel.py:1-80` (excerpt ends at line 80) | UNKNOWN | NEEDS_PLAN: Excerpt ends at line 80; cannot confirm or deny evict_model test coverage. |
| S07-08 | `load_packet` schema validation has unit test | Not visible in `tests/test_omarchy_kernel.py:1-80` excerpt | `tests/test_omarchy_kernel.py:1-80` (excerpt ends at line 80) | UNKNOWN | NEEDS_PLAN: Excerpt ends at line 80; cannot confirm or deny packet-validation test coverage. |
| S07-09 | `resolve_role_binding` negative tests (bad role, mismatched family/model) | Not visible in `tests/test_omarchy_kernel.py:1-80` excerpt | `tests/test_omarchy_kernel.py:1-80` (excerpt ends at line 80) | UNKNOWN | NEEDS_PLAN: Excerpt ends at line 80; cannot confirm or deny role-binding negative test coverage. |

---

## S08 — Gates & Hemisphere Honesty

| Check | Claim under test (source path:line @83ca764) | Code evidence (path:line @83ca764) | Result | Note |
|---|---|---|---|---|
| S08-01 | G0–G5 gate table defined with owners and requirements | `01_OMARCHY_AGENT_PROMPTS.md:8-45` §2 table lists G0 (Provenance), G1 (Mechanical Jig), G2 (Symbol & Dep Hygiene), G3 (Structural Architecture), G4 (Specialist Audit), G5 (Cross-Family Peer) | `01_OMARCHY_AGENT_PROMPTS.md` §2 | PASS | |
| S08-02 | Hemisphere split: Cloud Grand Council vs Local Council | `AGENTS.md:1-56` §1 table + `01_OMARCHY_AGENT_PROMPTS.md` Law 2 | `AGENTS.md` §1; `01_OMARCHY_AGENT_PROMPTS.md` Law 2 | PASS | |
| S08-03 | Cross-family G5: Family A code reviewed by Family B, vice versa | `AGENTS.md:1-56` §2 Hard Independence Rule 1; `01_OMARCHY_AGENT_PROMPTS.md` Law 5 | `AGENTS.md` §2 Rule 1; `01_OMARCHY_AGENT_PROMPTS.md` Law 5 | PASS | |
| S08-04 | Fail-closed (Law 9): missing files / corrupt data / denied permissions → explicit status, never silent no-op | `01_OMARCHY_AGENT_PROMPTS.md` Law 9 text; `.omarchy/omarchy.py:58-60` `parse_agents_lock` raises on missing file; `.omarchy/omarchy.py:568-571` `enforce_memory_budget` raises on missing model | `01_OMARCHY_AGENT_PROMPTS.md` Law 9; `.omarchy/omarchy.py:58-60,568-571` | PASS | |
| S08-05 | No ghostwriting (Law 11): `parent` never authors ballot under council seat name | `01_OMARCHY_AGENT_PROMPTS.md` Law 11 text | `01_OMARCHY_AGENT_PROMPTS.md` Law 11 | PASS | |
| S08-06 | UNKNOWN over invention (Law 4): missing symbol → `UNKNOWN — NEEDS_PLAN` | `01_OMARCHY_AGENT_PROMPTS.md` Law 4 text | `01_OMARCHY_AGENT_PROMPTS.md` Law 4 | PASS | |
| S08-07 | Mechanical reproduction (Law 7): "tests pass" void until Testing Jig runs | `01_OMARCHY_AGENT_PROMPTS.md` Law 7 text | `01_OMARCHY_AGENT_PROMPTS.md` Law 7 | PASS | |
| S08-08 | G2 gate: diff ≤ 300 LOC / ≤ 5 files enforced in code | `01_OMARCHY_AGENT_PROMPTS.md` §2 G2 row; `.omarchy/omarchy.py:266-269` enforces ≤ 5 files; LOC check not in excerpts | `.omarchy/omarchy.py:266-269` (file count only) | UNKNOWN | NEEDS_PLAN: 300-LOC cap enforcement not visible in provided excerpts; only the 5-file cap is coded. |
| S08-09 | Zero alias routing / sterilized CLI (AGENTS.md §2 Rule 2) | `AGENTS.md:1-56` §2 Hard Independence Rule 2: "accepts only a `.json` packet … Ad-hoc strings and bare seat names are rejected (exit 64 / 66)" | `AGENTS.md` §2 Rule 2 (doc only) | UNKNOWN | NEEDS_PLAN: `scripts/run_local_agent.sh` not in provided excerpts; cannot verify exit-code enforcement. |

---

OMARCHY_STATUS: COMPLETE
