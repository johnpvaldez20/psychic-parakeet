# 01_PLAN.r2 — Omarchy v3.0 Kernel Specification (slice `s000-bootstrap`)

Author: linus · cloud · 2026-10-15
Slot: `slices/s000-bootstrap/01_PLAN.r2.md` · stage 1 · round 2 (final plan round)
Inputs read: `slices/s000-bootstrap/slice.json`, `slices/s000-bootstrap/00_PROMPT.md`, `slices/s000-bootstrap/01_PLAN.r1.md`, `slices/s000-bootstrap/02_CHALLENGE.r1.md`, `.omarchy/omarchy.py`, `.omarchy/batch_runner.py`, `docs/GRAND_COUNCIL/v2.3.1_Test/*`, `agents.lock`, `agents.lock.optional`, `scripts/*.sh`, `tests/test_omarchy_kernel.py`, `.cursor/agents/qweny.md`, `.cursor/agents/moxie.md`.

Citation shorthand: `P:<n>` means `slices/s000-bootstrap/00_PROMPT.md:<n>`, and `C:<n>` means `slices/s000-bootstrap/02_CHALLENGE.r1.md:<n>`. Every other citation is a full `path:line` at commit `d2e5005`. Outside `slices/` that tree is byte-identical to tag `v2.3.1-attempt1` (`1156b29`), because `fc61064` added only `slices/s000-bootstrap/{slice.json,00_PROMPT.md}`.

This revision is complete and replaces `01_PLAN.r1.md`. §21 maps every finding of `02_CHALLENGE.r1.md` to the sections that changed.

## 0. Status of this document

- This specification is normative. "MUST", "MUST NOT", and "exactly" leave no implementer discretion. Where this document is silent, the approved plan in `00_PROMPT.md` governs. Where the two conflict, this document wins, and every such conflict is listed in §20.
- `parent` implements §1–§18 once, as the bootstrap exception (`P:585`, `P:711-719`). Phase 3 creates `00_ARCHITECTURE.md` from §0–§20 of the approved revision (§17.2).
- Nothing in this document is measured. Every guessed number is marked `UNMEASURED` and listed again in §19.
- §0–§20 name no model slug. Slugs are referenced by `path:line` only, so the `00_ARCHITECTURE.md` copy satisfies T-D2.

---

## 1. Conventions

| Term | Definition |
|---|---|
| repo | The git checkout that contains the running kernel package `omarchy/`. The CLI computes it as the parent directory of the package directory and ignores the process cwd. Library functions take `repo: Path` explicitly, so tests can use `tmp_path` repositories. The kernel that runs is this checkout's working tree (`P:616`). |
| repo path | A repo-relative POSIX path that full-matches `REPO_PATH`. Every **read** of repository content goes through git objects (`worktree.read_blob`). A path resolves only to a regular-file blob (mode `100644` or `100755`). Symlinks (`120000`), gitlinks, and trees never resolve. Every **write** into a worktree goes through `slice.sterilize_path` (the v2 rule at `.omarchy/omarchy.py:216-233`): the resolved `<root>/<path>` stays inside the resolved `<root>`, and no existing component is a symlink. |
| sha256 | Lowercase 64-hex SHA-256 of the exact bytes named. Nothing is normalized before hashing. |
| commit id | 40-hex git object id. |
| commit of row `i` | The commit that appended row `i` to `PROOF.jsonl` (one commit per row, §9.5). |
| text | UTF-8 with LF line endings. A CR byte anywhere in a slot file that is parsed (§7) is a defect. |
| LOC | The sum of additions and deletions reported by `git diff --numstat` (the G2 measure, `P:116`). |
| time | UTC, `YYYY-MM-DDTHH:MM:SSZ`. |
| regex | Python `re` syntax, always applied with `re.fullmatch`. |
| runtime | Python ≥ 3.10, standard library only for `omarchy/**`. Tests use `pytest`. There is no dependency manifest. |

```text
REPO_PATH = (?!/)(?!\.git(?:/|$))(?!.*//)(?!(?:.*/)?\.{1,2}(?:/|$))[A-Za-z0-9._@+-]+(?:/[A-Za-z0-9._@+-]+)*
SLICE_ID  = s[0-9]{3}[a-z]?(?:-[a-z0-9]+)+          (at most 48 characters)
SEAT_ID   = [a-z][a-z0-9_]{0,31}
PKT_ID    = pkt-[0-9]{2}
HEX64     = [0-9a-f]{64}
INDEX     = [1-9][0-9]*                              (unbounded; no leading zeros)
```

Reserved seat ids are `human`, for human-authored rows, and `kernel`, for kernel actions (merge, QA evaluation). Neither may appear in `agents.lock`.

---

## 2. Package and module contract

### 2.1 Files

| Path | Responsibility | v2 salvage (cited) |
|---|---|---|
| `omarchy/__init__.py` | `__version__ = "3.0.0rc0"`; the exception types of §2.3 | — |
| `omarchy/__main__.py` | argparse CLI (§13), dispatch, exit codes (§11.6) | `parse_args`, `main` (`.omarchy/omarchy.py:856-905`) |
| `omarchy/lock.py` | Strict parse of `agents.lock` schema 3, invariants, seat lookup | `parse_agents_lock`, `locked_local_family_models` (`.omarchy/omarchy.py:60-167`) |
| `omarchy/slice.py` | `slice.json`, `03_PACKETS.json`, and `BOOTSTRAP.json` validation; the slot-name grammar; path grammar and sterilization; manifest test | `sterilize_path` (`.omarchy/omarchy.py:216-233`) |
| `omarchy/trailers.py` | Outer-fence strip, file-block parser, trailer grammar, per-class validation, output contracts, ruling rendering | fence strip (`.omarchy/omarchy.py:654-658`) |
| `omarchy/proof.py` | Row schema, canonical JSON lines, hash chain, flocked append, required-file and allowed-change sets, commit messages and trailers, `kernel_sha256` | `append_locked_log` (`.omarchy/omarchy.py:343-353`) |
| `omarchy/machine.py` | Pure state machine: integrity checks, transitions, render commits, step formatting, `STAGES`. No IO | — |
| `omarchy/worktree.py` | git plumbing: slice worktree, temporary worktrees, block writes, staged diff and numstat, diff apply, gates with logs, kernel commits, fast-forward, commit and tree listing, source tags, slice flock | `WorktreeTransaction`, `run_deterministic_gates`, `apply_agent_changes` (`.omarchy/omarchy.py:317-340`, `:360-497`, `:693-716`) |
| `omarchy/view.py` | `load_view`: read a slice branch into a `SliceView` using git objects only | — |
| `omarchy/ollama.py` | HTTP client, residency checks, budget, `family_session`, sweep | `invoke_ollama_serial`, `enforce_memory_budget`, `force_unload_model`, `evict_model`, batch `finally` (`.omarchy/omarchy.py:542-690`, `.omarchy/batch_runner.py:50-73`, `:313-317`) |
| `omarchy/runner.py` | Lineage, prompt build (local and cloud), token estimate, `run`, `smoke` | `build_agent_prompt` (`.omarchy/omarchy.py:505-539`) |
| `omarchy/report.py` | `verify`, `verify --repo`, `status`, coverage labels | — |
| `omarchy/ingest.py` | `open`, `record`, `rule`: every path by which human or cloud bytes enter a slice | — |
| `omarchy/prompts/*.md` | The 11 templates of §10.6, all part of `kernel_sha256` | intent of `.cursor/agents/qweny.md:12-14` and `.cursor/agents/moxie.md:12-15` (§20 D20) |
| `scripts/omarchy` | Bash shim: `#!/usr/bin/env bash`, `set -euo pipefail`, prepend the repo root to `PYTHONPATH`, then `exec python3 -m omarchy "$@"` | — |

### 2.2 Import order

`__init__` → `lock` → `slice` → `trailers` → `proof` → `machine` → `worktree` → `view` → `ollama` → `runner` → `report` → `ingest` → `__main__`. A module may import only modules to its left. Further restrictions:

- `machine` imports only `__init__`, `lock`, `slice`, `trailers`, and `proof`. It calls no `open`, `subprocess`, `urllib`, `socket`, `os.environ`, `time`, or `random`.
- `ollama` imports only `__init__` and `lock`.
- Importers bind `slice` as `from omarchy import slice as slicecfg`.

### 2.3 Exceptions (exhaustive)

Every exception the kernel raises on purpose is one of these types. Any other exception is a kernel bug and propagates with a traceback (process exit 1).

| Type | Base | Fields | Raised by | Handling | CLI exit if it reaches `__main__` |
|---|---|---|---|---|---|
| `OmarchyError` | `Exception` | `message: str` | Environment or kernel failure: Ollama transport error (connection refused, HTTP status ≠ 200, body not JSON), `ollama.lock` busy, a kernel-generated path failing sterilization, a missing slice worktree | Never caught inside the kernel. Writes no row and consumes no seat attempt | 1, stderr `[OMARCHY][FATAL] <message>` |
| `Refusal` | `OmarchyError` | `code: str`, `subject: str` (slot, repo path, or `-`), `detail: str` | Integrity checks (§11.2) and preconditions (§13) | Writes no row | 65, stdout `REFUSE <code> <subject>`, stderr `<detail>` |
| `LockError` | `Refusal` | `code` is always `ILLEGAL_LOCK` | `lock.parse_lock` | As `Refusal` | 65 |
| `SeatFailure` | `OmarchyError` | `failure: str` (a `SEAT_FAILED` value of §9.4), `rejected: bytes \| None` | `trailers.parse_slot`, `slice.parse_packets`, `worktree.write_blocks`, `ollama.Session.generate` (`TIMEOUT`, `DONE_REASON`, `EMPTY_RESPONSE`), and the ingest content checks | Always caught by `runner` (§13.5) or `ingest` (§13.4), which write a `SEAT_FAILED` row | 1 (kernel bug) |
| `MergeConflict` | `OmarchyError` | `detail: str` (`git apply` stderr, decoded with `errors="replace"`) | `worktree.apply_diff` when `git apply` exits non-zero | Always caught by the merge job (§14.5), which writes `MERGE_FAILED APPLY_CONFLICT`. It is a kernel job: no seat attempt is consumed; the synthesis round fails | 1 (kernel bug) |
| `ResidencyError` | `OmarchyError` | `models: tuple[str, ...]`, the names still listed by `/api/ps` after polling | `ollama.family_session` (enter and exit) and `ollama.sweep` | Never caught. Writes no row and consumes no attempt | 1 |

`subprocess.CalledProcessError` from `worktree.git` propagates unchanged, and `__main__` maps it to exit 2 with stderr `[OMARCHY][GIT-ERROR] <cmd>: <stderr>` (as `.omarchy/omarchy.py:900-905`). `__main__` catches, in this order: `Refusal`, `OmarchyError`, `subprocess.CalledProcessError`.

### 2.4 Public names

Types are Python annotations. `Path` is `pathlib.Path`. Every record type is a frozen dataclass.

| Module | Name | Signature or fields |
|---|---|---|
| lock | `LOCAL_FAMILY_A`, `LOCAL_FAMILY_B`, `CAPS` | `"local_family_a"`, `"local_family_b"`, `frozenset({"plan","challenge","qa","propose","critique","synthesize","review","host"})` |
| lock | `Seat` | `seat_id: str, group: str, runtime: str, family: str, model: str, caps: frozenset[str], weight: str` |
| lock | `Lock` | `seats: tuple[Seat, ...], sha256: str` |
| lock | `parse_lock` | `(text: str, sha256: str) -> Lock`, raises `LockError` |
| lock | `load_lock` | `(path: Path) -> Lock`: reads bytes, `sha256` of those bytes, strict UTF-8 decode |
| lock | `seat`, `planner`, `family_seat` | `(lock, seat_id) -> Seat` (raises `KeyError`); `(lock) -> Seat`; `(lock, family) -> Seat` |
| lock | `challenger_legal`, `qa_legal` | `(lock, seat_id: str) -> bool` (§4.3) |
| lock | `local_models` | `(lock) -> dict[str, str]`, family → model |
| slice | `strict_json` | `(text: str) -> object`; rejects duplicate keys, `NaN`, `Infinity`; raises `ValueError` |
| slice | `SliceConfig` | `schema: int, slice_id, title, base_ref, challenger_seat, qa_seats: tuple[str, ...], test_command: tuple[tuple[str, ...], ...], context_files: tuple[str, ...], review_files: tuple[str, ...], num_ctx: int, max_packets: int` |
| slice | `parse_slice_config` | `(text: str, slice_id: str) -> SliceConfig`, structural only, raises `Refusal("ILLEGAL_CONFIG")` |
| slice | `check_config_legal` | `(cfg, lock) -> None`, raises `Refusal("ILLEGAL_CONFIG")` |
| slice | `Packet`, `Packets` | `packet_id, title, plan_section, instructions, acceptance: tuple[str, ...], target_files: tuple[str, ...], context_files: tuple[str, ...], verification_commands: tuple[tuple[str, ...], ...]`; `schema: int, plan_sha256: str, prompt_sha256: str, packets: tuple[Packet, ...]` |
| slice | `parse_packets` | `(raw: bytes, cfg, approved_plan_sha256: str, plan_files: tuple[str, ...]) -> Packets`, raises `SeatFailure("PACKETS_INVALID", rejected=raw)`. It does not compare `prompt_sha256` (§7.5) |
| slice | `SlotName` | `name, kind, ext, stage: int \| None, packet_id, qa_round: int \| None, round: int \| None, variant, seat_id, index: int \| None, attempt: int \| None, target: str \| None`; property `authored: bool`; property `slot_class: SlotClass \| None` (§5.4) |
| slice | `parse_slot_name` | `(name: str) -> SlotName`, raises `ValueError` (§5.2) |
| slice | `companion`, `rejected_name` | `(slot: str, ext: "diff" \| "gates.log") -> str`; `(slot: str, attempt: int) -> str` |
| slice | `qa_file_ok` | `(slice_id: str, path: str) -> bool` (§5.3) |
| slice | `check_repo_path`, `sterilize_path` | `(p: str) -> str`, raises `ValueError`; `(rel: str, root: Path) -> Path`, raises `ValueError("SECURITY VIOLATION: ...")` |
| slice | `is_manifest` | `(path: str) -> bool` (§14.6) |
| slice | `BootstrapRecord`, `parse_bootstrap` | §8; `(text: str, slice_id: str) -> BootstrapRecord`, raises `Refusal("BOOTSTRAP_MISMATCH")` |
| trailers | `SlotClass` | enum `PLAN, VERDICT, CODE, QA, PACKETS, RULING` |
| trailers | `strip_outer_fence` | `(text: str) -> str` (§7.1) |
| trailers | `split_trailer` | `(text: str) -> tuple[str, dict[str, str]]`, raises `SeatFailure("TRAILER_INVALID")` |
| trailers | `FileBlock`, `parse_file_blocks` | `path: str, content: bytes`; `(body: str, allowed: frozenset[str]) -> tuple[FileBlock, ...]` |
| trailers | `Parsed` | `status, verdict, blocking_count, plan_files, touched_files, missing_symbols, cited, qa_tests: tuple[tuple[str, str], ...], ruling, halt_code, halt_slot, dismiss_paths, reason, prompt_sha256, blocks` (absent fields `None`) |
| trailers | `parse_slot` | `(cls, raw: bytes, *, cloud: bool, allowed_paths: frozenset[str] = frozenset()) -> Parsed`, raises `SeatFailure`. `cls = PACKETS` raises `ValueError` |
| trailers | `output_contract` | `(cls, *, cloud: bool, slice_id: str, targets: tuple[str, ...] = (), plan_sha256: str \| None = None, max_packets: int \| None = None) -> str` (§10.7) |
| trailers | `render_ruling` | `(ruling, halt_code, halt_slot, paths: tuple[str, ...], reason) -> bytes` |
| proof | `ROW_FIELDS`, `ZERO_SHA` | the §9.1 field names in table order; `"0" * 64` |
| proof | `sha256_bytes`, `canonical_line`, `new_row` | `(b: bytes) -> str`; `(row: dict) -> bytes`; `(**fields) -> dict` (every absent field is `None`) |
| proof | `parse_rows` | `(data: bytes) -> tuple[dict, ...]`, raises `Refusal("CHAIN_BROKEN")` |
| proof | `append_row` | `(path: Path, row: dict) -> dict` (§9.3) |
| proof | `required_files` | `(rows, slice_id) -> dict[str, str]`, path → sha256 (§5.5) |
| proof | `allowed_changes` | `(row, slice_id) -> frozenset[tuple[str, str]]`, the exact `(status, path)` set of §9.5 |
| proof | `CommitInfo` | `sha: str, parents: tuple[str, ...], subject: str, trailers: dict[str, str], changes: frozenset[tuple[str, str]], proof_lines: int` |
| proof | `commit_message`, `parse_commit_trailers` | `(row) -> str`; `(message: str) -> dict[str, str]` |
| proof | `kernel_sha256` | `(repo: Path) -> str` (§9.6) |
| machine | `STAGES` | §11.7 |
| machine | `Job` | `kind: "CLOUD" \| "LOCAL" \| "KERNEL", action: "author" \| "merge" \| "qa_eval", seat_id, family, slot, stage: int, packet_id, qa_round, round, attempt: int, render_commit: str \| None` |
| machine | `Step` | `kind: "NEXT" \| "HALT" \| "DONE" \| "DONE_BOOTSTRAP" \| "REFUSE", jobs: tuple[Job, ...], code: str \| None, subject: str \| None` |
| machine | `SliceView` | `slice_id, cfg, packets: Packets \| None, rows: tuple[dict, ...], commits: tuple[CommitInfo, ...], tip_files: Mapping[str, str], head: str, running_kernel_sha256: str, running_lock: Lock \| None, bootstrap: BootstrapRecord \| None` |
| machine | `check_integrity` | `(view) -> None`, raises `Refusal` (§11.2) |
| machine | `derive` | `(view, n: int) -> Step`: the state after the first `n` rows; reads only rows, commit ids, `cfg`, `packets`, and the OPEN roster |
| machine | `next_step` | `(view) -> Step`: `check_integrity`, then `derive(view, len(rows))`; a `Refusal` becomes `Step("REFUSE", (), code, subject)` |
| machine | `approved_plan` | `(view, n) -> tuple[str, str] \| None`: (plan slot, approval slot) |
| machine | `legal_rulings` | `(view, n) -> frozenset[str]` (§12) |
| machine | `format_step`, `exit_code` | `(step) -> str` (§11.6); `(step) -> int` |
| worktree | `git`, `git_ok` | `(cwd: Path, *args: str, stdin: bytes \| None = None) -> bytes` (argv only, `check=True`, output captured); `(cwd, *args) -> bool` (exit status 0) |
| worktree | `slice_branch`, `slice_worktree` | `(slice_id) -> str` = `slice/<id>`; `(repo, slice_id) -> Path` = `<repo>/.omarchy/worktrees/<id>/slice` |
| worktree | `slice_lock` | context manager `(repo, slice_id)`: non-blocking `flock` on `<repo>/.omarchy/locks/<id>.lock`; busy → `Refusal("SLICE_BUSY")` |
| worktree | `check_clean` | `(wt: Path, branch: str) -> None`, raises `Refusal("DIRTY_WORKTREE" \| "WRONG_BRANCH")` |
| worktree | `TempWorktree` | context manager `(repo, slice_id, name: str, base: str) -> Path` (§14.1) |
| worktree | `write_blocks` | `(wt, blocks, allowed: frozenset[str]) -> None` (§14.2) |
| worktree | `DiffResult`, `stage_diff` | `diff: bytes, numstat_loc: int, paths: tuple[str, ...], manifest_paths: tuple[str, ...]`; `(wt, paths) -> DiffResult` (§14.3) |
| worktree | `apply_diff` | `(wt, diff: bytes) -> DiffResult`, raises `MergeConflict` |
| worktree | `GateResult`, `run_gates` | `passed: bool, log: bytes`; `(wt, commands) -> GateResult` (§14.4) |
| worktree | `kernel_commit` | `(wt, row: dict, add: Mapping[str, bytes], delete: tuple[str, ...]) -> tuple[dict, str]` (§9.5): the appended row and the commit id |
| worktree | `fast_forward` | `(slice_wt, branch: str, expected_head: str) -> None` |
| worktree | `read_blob`, `list_commits`, `list_tree`, `is_ancestor` | `(repo, commit, path) -> bytes \| None` (regular-file blobs only); `(repo, base, tip) -> tuple[CommitInfo, ...]` (oldest first); `(repo, commit, prefix) -> dict[str, str]` path → sha256 of regular-file blobs; `(repo, a, b) -> bool` |
| worktree | `tag_source` | `(repo, slice_id, seq: int, commit: str) -> None`: `git tag -f omarchy/<slice_id>/source-<seq> <commit>` |
| view | `load_view` | `(repo, slice_id) -> SliceView` (§11.1) |
| ollama | constants | §15 |
| ollama | `Client` | `(base_url: str)`; `tags() -> list[dict]`, `ps() -> list[dict]`, `generate(model, prompt: str, num_ctx: int, keep_alive) -> dict`, `unload(model) -> None` |
| ollama | `match_model`, `check_budget` | `(entries: list[dict], slug: str) -> dict \| None` (K8); `(weight_bytes: int, num_ctx: int) -> None` |
| ollama | `evict_all_except`, `sweep` | `(client, keep: str \| None) -> None`; `(client) -> None` |
| ollama | `Generation` | `response: str, done_reason: str \| None, eval_count, prompt_eval_count, total_duration_ns, resident_bytes` (ints or `None`) |
| ollama | `family_session` | context manager `(client, lock, family, num_ctx, locks_dir: Path) -> Session`; `Session.generate(prompt: str) -> Generation` |
| runner | `Lineage`, `lineage` | `slots: tuple[str, ...], repo_files: tuple[str, ...], render_commit: str`; `(view, job) -> Lineage` (pure, §10.2) |
| runner | `build_prompt` | `(repo, view, job) -> bytes`, byte-deterministic (§10.8) |
| runner | `estimate_tokens`, `reserve_tokens` | `(prompt: bytes) -> int`; `(repo, view, job) -> int` (§10.5) |
| runner | `run`, `smoke` | `(repo, slice_id, client) -> int`; `(repo, client) -> int` |
| report | `verify`, `verify_repo`, `status` | `(repo, slice_id) -> int`; `(repo) -> int`; `(repo, markdown: bool, tokens: bool) -> int` |
| report | `coverage_label` | `(path: str, head_sha256: str \| None, bootstrap_sha256: str, done: tuple[SliceFacts, ...]) -> str` (§13.8, pure) |
| report | `SliceFacts` | `slice_id: str, merged_sha256: Mapping[str, str], reviewed_paths: frozenset[str]` |
| ingest | `open_slice` | `(repo, slice_id, bootstrap: bool) -> int` |
| ingest | `record` | `(repo, slice_id, slot, seat_id, ref, cloud_run) -> int` |
| ingest | `rule` | `(repo, slice_id, ruling, reason, paths: tuple[str, ...], confirm: Callable[[str], str] = tty_confirm) -> int` |
| ingest | `ingest_allowed` | `(slice_id, slot, path) -> bool` (§13.4) |
| ingest | `check_inputs` | `(repo, commit, inputs: Mapping[str, str \| None]) -> tuple[str, ...]`: the paths whose sha256 at `commit` differs from the expected value (`None` means "absent") |
| ingest | `expected_prompt` | `(repo, view, job) -> tuple[bytes, str, str]`: prompt bytes, sha256, and `prompt_source` (§10.9) |
| __main__ | `main` | `(argv: Sequence[str] \| None = None, *, repo: Path \| None = None, client: Client \| None = None) -> int` |

---

## 3. `agents.lock` schema 3

### 3.1 Grammar

- Lines are LF-separated. A line that is empty or starts with `#` is ignored.
- The first other line MUST be exactly `schema=3`. Any other value or position is `ILLEGAL_LOCK`. The v2 parser never checked the schema (`.omarchy/omarchy.py:60-80`; ballot N7 at `docs/GRAND_COUNCIL/v2.3.1_Test/LINUS_BALLOT.md:133-137`).
- Every remaining line has exactly 7 `|`-separated fields, `SEAT|GROUP|RUNTIME|FAMILY|MODEL|CAPS|WEIGHT`. A field MUST NOT be empty or carry leading or trailing whitespace. Any deviation is fatal, never skipped (contrast `.omarchy/omarchy.py:70-74`).

| Field | Grammar |
|---|---|
| SEAT | `SEAT_ID`, unique, not `human` or `kernel` |
| GROUP | `grand_council` iff RUNTIME is `cloud`; `local_council` iff `local`; `orchestrator` iff `host` |
| RUNTIME | `cloud` \| `local` \| `host` |
| FAMILY | `[a-z][a-z0-9_]{0,31}`. Local seats: `local_family_a` \| `local_family_b`. The host seat: `host` |
| MODEL | `[^\s\|]+` |
| CAPS | comma-separated, no spaces, no duplicates, a subset of `CAPS` |
| WEIGHT | `[^\|]+` (free text) |

### 3.2 Invariants (all fatal at parse)

1. Exactly one `host` seat. Its id is `parent`, its caps are exactly `host`, and `host` appears on no other seat.
2. Exactly one seat has `plan`, and it is `cloud`.
3. Exactly one local seat per local family, and the two MODEL values differ.
4. Cloud seat families are pairwise distinct.
5. `synthesize` appears only on Family A, `review` only on Family B, and `propose` and `critique` only on local seats.
6. `qa` appears only on cloud seats other than the planner.
7. `challenge` appears only on cloud seats whose family differs from the planner's, or on the Family A seat.
8. Family A caps ⊇ `{propose, critique, synthesize}`; Family B caps ⊇ `{propose, critique, review}`.

### 3.3 Repo content after Phase 3

`agents.lock` is exactly these lines, in order:

1. `# Omarchy v3 seat lock. Format: SEAT|GROUP|RUNTIME|FAMILY|MODEL|CAPS|WEIGHT. Invariants: 00_ARCHITECTURE.md section 3.2.`
2. `schema=3`
3. The five rows at `P:272-276`, byte for byte, in that order (`linus`, `knuth`, `qweny`, `moxie`, `parent`). Their MODEL values equal the current `agents.lock:16-18` for `linus`, `qweny`, and `moxie`, and `agents.lock.optional:8` for `knuth`.

`agents.lock.optional` is exactly these lines. It uses the same grammar and is never loaded by the kernel.

1. `# Optional seats; never loaded by the kernel. Copy one row into agents.lock to enable it.`
2. `schema=3`
3. `dhh|grand_council|cloud|muse_spark|<MODEL of agents.lock.optional:6>|challenge,qa|Optional challenger or QA seat`
4. `carmack|grand_council|cloud|xai_grok|<MODEL of agents.lock.optional:7>|challenge,qa|Optional challenger or QA seat`

`<MODEL of …>` means the fifth field of that line, copied byte for byte.

---

## 4. `slice.json` schema 3

### 4.1 Fields

`slice.strict_json` parses it: duplicate keys, `NaN`, and `Infinity` are rejected; an integer field accepts only a JSON integer (`type(v) is int`, so never `true` or `false`); unknown keys are rejected (`P:333`).

| Key | Type | Required | Rule |
|---|---|---|---|
| `schema` | int | yes | `3` |
| `slice_id` | str | yes | `SLICE_ID`; equals the directory name |
| `title` | str | yes | 1–120 characters, no newline |
| `base_ref` | str | yes | At `open`, resolves with `git rev-parse --verify <ref>^{commit}` |
| `challenger_seat` | str | yes | Legal per §4.3 |
| `qa_seats` | list[str] | yes | 1–3 unique entries, each legal per §4.3 |
| `test_command` | list[list[str]] | yes | 1–5 argv lists, each with 1–64 non-empty strings; `basename(argv[0])` ∉ `{sh, bash, zsh, dash, ksh, fish, env}` |
| `context_files` | list[str] | yes | 0–20 unique repo paths, each a regular-file blob at `base_ref`; inlined into every local prompt |
| `review_files` | list[str] | no (default `[]`) | 0–200 unique repo paths, each a regular-file blob at `base_ref`; listed (never inlined) in cloud prompts; counts toward coverage (§13.8) |
| `num_ctx` | int | yes | 4096–131072 |
| `max_packets` | int | yes | 1–20 |

A grammar failure in `parse_slice_config` is `ILLEGAL_CONFIG`. This includes a path with a `..` segment. A path that is not a regular-file blob at `base_ref` is `ILLEGAL_CONFIG` at `open` (§13.1). `slices/s000-bootstrap/slice.json:1-12` validates under this schema; it omits `review_files`.

### 4.2 Fixed roles

The planner is the unique `plan` seat, the synthesizer is the Family A seat, and the reviewer is the Family B seat. None of them is configurable (`P:333`).

### 4.3 Legality

Legality is checked at `open`, and on every non-terminal `next` while the pins hold (§11.2 check 8).

- `challenger_legal(c)`: `c` is in the lock and has cap `challenge`, and either (`runtime(c) = cloud` and `family(c) ≠ family(planner)`) or (`runtime(c) = local` and `family(c) = local_family_a`) (`P:335-342`).
- `qa_legal(s)`: `s` is in the lock, `runtime(s) = cloud`, `s` has cap `qa`, and `s ≠ planner`. The challenger may also be a QA seat.

---

## 5. Slice directory and slot grammar

### 5.1 Layout

All slice state lives on branch `slice/<id>`. The kernel's worktree for it is `.omarchy/worktrees/<id>/slice`. The human's checkout holds only the inputs to `open`. `next`, `status`, and `verify` read the branch through git objects, never through a working tree. Slice branches are never deleted (§16).

### 5.2 Slot filename grammar

Every file under `slices/<id>/` on the slice branch is a basename (no subdirectories) that full-matches exactly one regex in this table. Indexes use `INDEX` and are unbounded.

| Kind | Regex | ext | stage | Other fields |
|---|---|---|---|---|
| `CONFIG` | `slice\.json` | `json` | 0 | — |
| `PROMPT` | `00_PROMPT\.md` | `md` | 0 | — |
| `PLAN` | `01_PLAN\.r(?P<round>[12])\.md` | `md` | 1 | round |
| `CHALLENGE` | `02_CHALLENGE\.r(?P<round>[12])\.md` | `md` | 2 | round |
| `PACKETS` | `03_PACKETS\.json` | `json` | 3 | — |
| `PROPOSAL` | `04_(?P<packet>pkt-[0-9]{2})\.q(?P<qa>[12])\.(?P<variant>[AB])\.(?P<ext>md\|diff\|gates\.log)` | group | 4 | packet, qa, variant |
| `CRITIQUE` | `05_(?P<packet>pkt-[0-9]{2})\.q(?P<qa>[12])\.(?P<variant>A_ON_B\|B_ON_A)\.md` | `md` | 5 | packet, qa, variant |
| `SYNTH` | `06_(?P<packet>pkt-[0-9]{2})\.q(?P<qa>[12])\.SYNTH\.r(?P<round>[12])\.(?P<ext>md\|diff\|gates\.log)` | group | 6 | packet, qa, round |
| `REVIEW` | `06_(?P<packet>pkt-[0-9]{2})\.q(?P<qa>[12])\.REVIEW\.r(?P<round>[12])\.md` | `md` | 6 | packet, qa, round |
| `MERGE` | `06_(?P<packet>pkt-[0-9]{2})\.q(?P<qa>[12])\.MERGE\.r(?P<round>[12])\.gates\.log` | `gates.log` | 6 | packet, qa, round |
| `QA_REPORT` | `07_QA\.q(?P<qa>[12])\.(?P<seat>[a-z][a-z0-9_]{0,31})\.md` | `md` | 7 | qa, seat |
| `QA_EVAL` | `07_QA\.q(?P<qa>[12])\.EVAL\.(?P<index>[1-9][0-9]*)\.gates\.log` | `gates.log` | 7 | qa, index |
| `RULING` | `HALT\.(?P<index>[1-9][0-9]*)\.HUMAN\.md` | `md` | `None` | index |
| `PROOF` | `PROOF\.jsonl` | `jsonl` | `None` | — |
| `BOOTSTRAP` | `BOOTSTRAP\.json` | `json` | `None` | — |
| `BOOTSTRAP_PROMPT` | `BOOTSTRAP\.(?P<target>(?:01_PLAN\|02_CHALLENGE)\.r[12]\.md)\.prompt` | `prompt` | `None` | target |
| `REJECTED` | `(?P<target>.+)\.a(?P<attempt>[1-4])\.rejected` | `rejected` | stage of target | attempt, target; the remaining fields copied from the target |

`parse_slot_name` applies the rows in table order and returns the first full match. A `REJECTED` match is valid only if `target` parses to an authored name: kind `PLAN`, `CHALLENGE`, `PACKETS`, `CRITIQUE`, `REVIEW`, or `QA_REPORT`, or kind `PROPOSAL` or `SYNTH` with ext `md`. Anything else raises `ValueError`. `authored` is true exactly for those authored names, and false for `REJECTED`. The `[12]` and `[1-4]` bounds are exact, because the machine never produces a third plan, challenge, synthesis, or QA round, or a fifth attempt (§12.1). `companion(s, e)` replaces the final `.md` of an authored `PROPOSAL` or `SYNTH` name with `.<e>`. `rejected_name(s, k)` is `<s>.a<k>.rejected`.

Normative vectors (T-S1, T-S2). Accepted, with the fields that must be returned:

| Name | kind / ext / stage / fields |
|---|---|
| `slice.json` | CONFIG / json / 0 |
| `00_PROMPT.md` | PROMPT / md / 0 |
| `01_PLAN.r2.md` | PLAN / md / 1 / round 2 |
| `02_CHALLENGE.r1.md` | CHALLENGE / md / 2 / round 1 |
| `03_PACKETS.json` | PACKETS / json / 3 |
| `04_pkt-01.q1.A.md`, `04_pkt-01.q1.A.diff`, `04_pkt-99.q2.B.gates.log` | PROPOSAL / md, diff, gates.log / 4 / packet, qa, variant |
| `05_pkt-03.q2.B_ON_A.md` | CRITIQUE / md / 5 / pkt-03, 2, B_ON_A |
| `06_pkt-01.q1.SYNTH.r2.diff` | SYNTH / diff / 6 / pkt-01, 1, round 2 |
| `06_pkt-01.q1.REVIEW.r1.md` | REVIEW / md / 6 |
| `06_pkt-01.q2.MERGE.r2.gates.log` | MERGE / gates.log / 6 |
| `07_QA.q1.knuth.md`, `07_QA.q1.a.md`, `07_QA.q1.<32-char seat id>.md` | QA_REPORT / md / 7 |
| `07_QA.q2.EVAL.1.gates.log`, `07_QA.q2.EVAL.10.gates.log`, `07_QA.q1.EVAL.123.gates.log` | QA_EVAL / gates.log / 7 / index 1, 10, 123 |
| `HALT.1.HUMAN.md`, `HALT.100.HUMAN.md` | RULING / md / None / index |
| `PROOF.jsonl`, `BOOTSTRAP.json` | PROOF / jsonl; BOOTSTRAP / json |
| `BOOTSTRAP.01_PLAN.r2.md.prompt` | BOOTSTRAP_PROMPT / prompt / target `01_PLAN.r2.md` |
| `01_PLAN.r1.md.a1.rejected`, `03_PACKETS.json.a4.rejected`, `04_pkt-01.q1.B.md.a2.rejected`, `07_QA.q2.knuth.md.a3.rejected` | REJECTED / rejected / stage of target / attempt |

Rejected (each raises `ValueError`): `01_PLAN.r0.md`, `01_PLAN.r3.md`, `01_plan.r1.md`, `02_CHALLENGE.r1.MD`, `03_PACKETS.md`, `04_pkt-1.q1.A.md`, `04_pkt-001.q1.A.md`, `04_pkt-01.q0.A.md`, `04_pkt-01.q3.A.md`, `04_pkt-01.q1.C.md`, `04_pkt-01.q1.A.txt`, `05_pkt-01.q1.A_ON_A.md`, `05_pkt-01.q1.A_ON_B.diff`, `06_pkt-01.q1.REVIEW.r1.diff`, `06_pkt-01.q1.MERGE.r1.md`, `06_pkt-01.q1.SYNTH.r3.md`, `07_QA.q1.Knuth.md`, `07_QA.q1.1abc.md`, `07_QA.q1.<33-char seat id>.md`, `07_QA.q3.knuth.md`, `07_QA.q1.EVAL.0.gates.log`, `07_QA.q1.EVAL.01.gates.log`, `07_QA.q1.EVAL.1.md`, `HALT.0.HUMAN.md`, `HALT.01.HUMAN.md`, `HALT.1.human.md`, `PROOF.json`, `BOOTSTRAP.03_PACKETS.json.prompt`, `01_PLAN.r1.md.a0.rejected`, `01_PLAN.r1.md.a5.rejected`, `04_pkt-01.q1.A.diff.a1.rejected`, `PROOF.jsonl.a1.rejected`, `HALT.1.HUMAN.md.a1.rejected`, `06_pkt-01.q1.MERGE.r1.gates.log.a1.rejected`, `sub/01_PLAN.r1.md`, `.01_PLAN.r1.md`, `01_PLAN.r1.md ` (trailing space), the empty string.

### 5.3 QA test files

Files under `tests/qa/<id>/` MUST full-match `tests/qa/<id>/test_<idu>_[a-z0-9_]{1,40}\.py`, where `<idu>` is the slice id with every `-` replaced by `_`. Unique basenames keep pytest's default import mode from colliding across slices. There is no `conftest.py` and no `__init__.py`. `qa_file_ok(slice_id, path)` is this test. Vectors for `s001-kernel-audit` (T-S6): accepted `tests/qa/s001-kernel-audit/test_s001_kernel_audit_lock.py`; rejected `tests/qa/s001-kernel-audit/test_lock.py`, `tests/qa/s001-kernel-audit/sub/test_s001_kernel_audit_x.py`, `tests/qa/s001-kernel-audit/conftest.py`, `tests/qa/s002-x/test_s001_kernel_audit_x.py`, and `tests/qa/s001-kernel-audit/test_s001_kernel_audit_X.py`.

### 5.4 Slot classes and authors

| Kind (authored ext) | Example | Stage | Class (§7) | Author | Kernel-derived companions |
|---|---|---|---|---|---|
| CONFIG, PROMPT | `slice.json`, `00_PROMPT.md` | 0 | — | human | — |
| PLAN | `01_PLAN.r1.md` | 1 | PLAN | planner | — |
| CHALLENGE | `02_CHALLENGE.r1.md` | 2 | VERDICT | challenger | — |
| PACKETS | `03_PACKETS.json` | 3 | PACKETS | planner | — |
| PROPOSAL (md) | `04_pkt-01.q1.A.md` | 4 | CODE | Family A (`A`) / Family B (`B`) | `.diff`, `.gates.log` iff status `READY` |
| CRITIQUE | `05_pkt-01.q1.A_ON_B.md` | 5 | VERDICT | Family A on B / Family B on A | — |
| SYNTH (md) | `06_pkt-01.q1.SYNTH.r1.md` | 6 | CODE | Family A | `.diff`, `.gates.log` iff status `READY` |
| REVIEW | `06_pkt-01.q1.REVIEW.r1.md` | 6 | VERDICT | Family B | — |
| MERGE | `06_pkt-01.q1.MERGE.r1.gates.log` | 6 | kernel log | `kernel` | — |
| QA_REPORT | `07_QA.q1.knuth.md` | 7 | QA | QA seat | `tests/qa/<id>/**` files |
| QA_EVAL | `07_QA.q1.EVAL.1.gates.log` | 7 | kernel log | `kernel` | — |
| RULING | `HALT.1.HUMAN.md` | — | RULING | human, through `omarchy rule` | — |
| REJECTED | `01_PLAN.r1.md.a1.rejected` | — | raw rejected bytes | kernel | — |
| PROOF, BOOTSTRAP, BOOTSTRAP_PROMPT | `PROOF.jsonl`, … | — | — | kernel; human (bootstrap inputs) | — |

`SlotName.slot_class` returns the Class column, or `None` where it is `—` or a kernel log. Local authored `.md` files hold the exact UTF-8 bytes of the Ollama `response` string. Parsing happens on read, so `output_sha256` is the sha256 of the slot file (`P:314`).

### 5.5 Required files per row

`proof.required_files(rows, slice_id)` is the union, over every row, of the entries below. `<d>` is `slices/<id>/`. A `qa_files` path is **live** unless a later `RULING` row lists it in `dismissed_paths`. Only live paths are required.

| Row | Required path → sha256 |
|---|---|
| `OPEN` | `<d>slice.json` → `config_sha256`; `<d>00_PROMPT.md` → `output_sha256`. In the bootstrap slice also `<d>BOOTSTRAP.json` → `bootstrap_sha256`, and every `<d>BOOTSTRAP.<slot>.prompt` → its sha from `BOOTSTRAP.json` `prompts` |
| `RECORDED`, class other than CODE or QA | `<d><slot>` → `output_sha256` |
| `RECORDED`, CODE, status `READY` | `<d><slot>` → `output_sha256`; `<d><companion diff>` → `diff_sha256`; `<d><companion gates.log>` → `gates_log_sha256` |
| `RECORDED`, CODE, status not `READY` | `<d><slot>` → `output_sha256` only |
| `RECORDED`, QA | `<d><slot>` → `output_sha256`; every live `qa_files` path → its `sha256` |
| `SEAT_FAILED` | `<d><rejected_name(slot, attempt)>` → `output_sha256` iff `output_sha256` is non-null; otherwise nothing |
| `CONTEXT_OVERFLOW` | nothing |
| `MERGED`, `MERGE_FAILED` | `<d><slot>` (the MERGE log) → `output_sha256`. A MERGE log is always written (§14.5) |
| `QA_EVAL` | `<d><slot>` (the EVAL log) → `output_sha256` |
| `RULING` | `<d><slot>` (the HALT file) → `output_sha256` |

No row ever requires an authored slot that the row did not create. A `SEAT_FAILED` or `CONTEXT_OVERFLOW` row names its authored slot in `slot`, but the slot file is required only by that slot's later `RECORDED` row.

---

## 6. `03_PACKETS.json`

The file is strict JSON (as §4.1), with unknown keys rejected at every level.

| Key | Type | Rule |
|---|---|---|
| `schema` | int | `3` |
| `plan_sha256` | str | `HEX64`; equals `output_sha256` of the approved plan revision (§11.4) |
| `prompt_sha256` | str | `HEX64`; compared only by `ingest` (§7.5) |
| `packets` | list | 1 to `max_packets` entries |
| `packets[].packet_id` | str | `PKT_ID`; the list is exactly `pkt-01 … pkt-NN` in order |
| `packets[].title` | str | 1–120 characters, no newline |
| `packets[].plan_section` | str | `[0-9]+(?:\.[0-9]+)*` |
| `packets[].instructions` | str | 1–8000 characters |
| `packets[].acceptance` | list[str] | 1–10 non-empty strings |
| `packets[].target_files` | list[str] | 1–5 unique repo paths (`.omarchy/omarchy.py:273-276`) |
| `packets[].context_files` | list[str] | 0–10 unique repo paths |
| `packets[].verification_commands` | list[list[str]] | 1–5 argv lists, with the same rule as `test_command` |

Cross-packet rules:

- `target_files` are pairwise disjoint across packets.
- Every target is in the approved plan's `PLAN_FILES`.
- No target is under `slices/` or `tests/qa/`.
- No packet's `context_files` contains any packet's target, its own included. A sibling's target can change under the reader, which is the hidden dependency `P:123` bans.

Any violation is `SeatFailure("PACKETS_INVALID")`. There are no `role`, `family`, `model`, `depends_on`, or `base_branch` keys (`P:376`).

---

## 7. Response formats and trailers

### 7.1 Outer fence (local slots only, K2)

Let `t` be the response with leading and trailing whitespace removed. The parse input is the lines strictly between the first and last lines of `t` when all three hold: `t` has at least two lines, its first line full-matches `` ```[A-Za-z0-9_+-]* ``, and its last line is exactly `` ``` ``. Otherwise the parse input is the response unchanged. At most one level is ever removed, and inner fences are never touched. v2 stripped only a json fence, by regex on both ends (`.omarchy/omarchy.py:654-658`), and that strip was added mid-run (`docs/GRAND_COUNCIL/v2.3.1_Test/FLOW_TRACE.md:38`). The slot file still stores the unstripped bytes. Cloud slots are never fence-stripped.

### 7.2 Trailer block

1. The parse input MUST be valid UTF-8 and contain no CR byte.
2. Split it on LF and discard trailing lines that are empty or whitespace-only.
3. The last remaining line MUST be exactly `---`. The opening delimiter is the nearest earlier line that is exactly `---`. The lines strictly between them are the trailer, and there must be at least one. Everything before the opening delimiter is the body.
4. Every trailer line MUST full-match `([A-Z][A-Z0-9_]*): (\S(?:.*\S)?)`. Keys are unique. The key set MUST equal the class's required set exactly. Order is not checked, and extra keys are a defect.

Any failure is `SeatFailure("TRAILER_INVALID")`.

### 7.3 Required keys and value grammars

List values are split on `,`, with spaces stripped from each item, and an empty item is a defect. `NONE` stands alone.

| Class | Keys (exact set) |
|---|---|
| PLAN (`01`) | `OMARCHY_STATUS`, `PLAN_FILES`, `OMARCHY_PROMPT_SHA256` |
| VERDICT, cloud (`02` from a cloud seat) | `OMARCHY_VERDICT`, `BLOCKING_COUNT`, `CITED_LOCATIONS`, `OMARCHY_PROMPT_SHA256` |
| VERDICT, local (`02` from Family A, `05`, `06 REVIEW`) | `OMARCHY_VERDICT`, `BLOCKING_COUNT`, `CITED_LOCATIONS` |
| CODE (`04`, `06 SYNTH`) | `OMARCHY_STATUS`, `TOUCHED_FILES`, `MISSING_SYMBOLS` |
| QA (`07`) | `OMARCHY_STATUS`, `QA_TESTS`, `OMARCHY_PROMPT_SHA256` |
| RULING (`HALT.n.HUMAN.md`) | `HUMAN_RULING`, `HALT_CODE`, `HALT_SLOT`, `DISMISS_PATHS`, `REASON` |
| PACKETS (`03`) | no trailer; JSON per §6 |

| Key | Grammar and consistency |
|---|---|
| `OMARCHY_STATUS` | `READY` \| `NEEDS_PLAN` \| `UNKNOWN`; QA class: `READY` only. `COMPLETE` is illegal (`docs/GRAND_COUNCIL/v2.3.1_Test/QWENY_AUDIT_WORKSHEET.md:141`) |
| `OMARCHY_VERDICT` | `APPROVE` \| `REQUEST_CHANGES` \| `REJECT`. `APPROVE_WITH_FIXES` is illegal (`P:393`) |
| `BLOCKING_COUNT` | `0\|[1-9][0-9]{0,3}`. `APPROVE` ⇔ `0`; `REQUEST_CHANGES` ⇒ ≥ 1; `REJECT` ⇒ ≥ 1 |
| `CITED_LOCATIONS` | `NONE`, or a list of `REPO_PATH:L` or `REPO_PATH:L-M` with `L` and `M` matching `[1-9][0-9]*` and `L ≤ M`. Syntax only; existence is not checked |
| `PLAN_FILES` | `NONE`, or a list of unique repo paths, none under `slices/` or `tests/qa/`. `READY` ⇒ not `NONE` |
| `TOUCHED_FILES` | `NONE`, or a list of unique repo paths. `READY` ⇒ equals the set of file-block paths; otherwise `NONE` |
| `MISSING_SYMBOLS` | `NONE`, or a list of free-text items. `READY` ⇒ `NONE`; `NEEDS_PLAN` or `UNKNOWN` ⇒ not `NONE` |
| `QA_TESTS` | `NONE`, or entries separated by `; ` of the form `<REPO_PATH> -> <PKT_ID>`, with exactly one space on each side of `->`. Paths are unique. Semantic checks happen at ingest (§13.4) |
| `OMARCHY_PROMPT_SHA256` | `HEX64`. Compared only by `ingest` (§7.5) |
| `HUMAN_RULING` | `ABORT` \| `APPROVE_OVERRIDE` \| `APPROVE_DEPENDENCY` \| `RETRY` \| `DISMISS_QA_TEST` |
| `HALT_CODE`, `HALT_SLOT` | The HALT line being ruled on (§12) |
| `DISMISS_PATHS` | `NONE`, or (iff `DISMISS_QA_TEST`) a list of QA test paths |
| `REASON` | 1–500 characters, no newline |

### 7.4 File blocks (CODE class only)

Code travels in file blocks, never JSON. MLX Ollama returns HTTP 501 for `format` (`docs/GRAND_COUNCIL/v2.3.1_Test/FLOW_TRACE.md:37`, `.omarchy/omarchy.py:621-622`), and JSON-escaping whole files is the main failure mode (`P:396`).

```text
=== FILE: <REPO_PATH> ===
<content lines>
=== END_FILE ===
```

- Blocks appear in the body only. Outside a block, a line that starts with `=== FILE:` but is not a well-formed opener (full match `=== FILE: (REPO_PATH) ===`) is a defect, and so is any `=== END_FILE ===` line. Inside a block, only the exact closer is special.
- A block's content bytes are each content line followed by LF. An empty block is an empty file. Content MUST be valid UTF-8.
- Paths are unique across blocks, and every path is in the job's allowed set (the packet's `target_files`).
- `READY` ⇒ at least one block; `NEEDS_PLAN` or `UNKNOWN` ⇒ zero blocks.
- An unterminated block, a duplicate path, or bad UTF-8 is `FILE_BLOCK_INVALID`. A path outside the allowed set is `PATH_NOT_ALLOWED`.
- File blocks cannot delete files. Deletion is out of scope for v3.0.

The PLAN, VERDICT, QA, and RULING classes do not parse file blocks; their body is prose.

### 7.5 Parse entry points and the prompt-sha comparison

- `trailers.parse_slot(cls, raw, cloud=…)` handles PLAN, VERDICT, CODE, QA, and RULING. With `cloud=False` it applies §7.1 first. It validates grammar and consistency, and returns `Parsed.prompt_sha256` for cloud classes without comparing it.
- `slice.parse_packets(raw, cfg, approved_plan_sha256, plan_files)` handles PACKETS. It returns `Packets.prompt_sha256` without comparing it.
- The only comparison of a claimed prompt sha against the expected one is `ingest.record` step B5 (§13.4). For PACKETS the claimed value is `Packets.prompt_sha256`; for every other cloud class it is `Parsed.prompt_sha256`. The expected value comes from `ingest.expected_prompt` (§10.9).

---

## 8. `BOOTSTRAP.json`

This file is present only in `s000-bootstrap`. It is strict JSON with unknown keys rejected, and it extends `P:713` (§20 D17).

| Key | Type | Rule |
|---|---|---|
| `schema` | int | `3` |
| `slice_id` | str | `s000-bootstrap` |
| `authored_by` | str | `parent` |
| `authorized_by` | str | `human` |
| `reason` | str | `pipeline cannot build itself` |
| `superseded_by` | str | `s001-kernel-audit` |
| `files` | object | path → `{"sha256": HEX64, "kind": "kernel" \| "test" \| "prompt" \| "script" \| "config" \| "doc"}`. It lists every path that Phases 2–3 create or content-modify, except `docs/EVIDENCE.md` and `docs/HISTORY.md` (append-only logs), `archive/**` (content-unchanged moves), and files under `slices/` |
| `prompts` | object | slot name → `HEX64`. Keys are a non-empty subset of `{01_PLAN.r1.md, 02_CHALLENGE.r1.md, 01_PLAN.r2.md, 02_CHALLENGE.r2.md}`. Each value is the sha256 of `slices/s000-bootstrap/BOOTSTRAP.<slot>.prompt`, the exact bytes `parent` dispatched to that cloud seat, excluding the final `OMARCHY_PROMPT_SHA256 value: …` line |

---

## 9. Proof log and kernel commits

### 9.1 Row schema (`slices/<id>/PROOF.jsonl`)

Every row carries every field below, in canonical form (§9.3). Inapplicable fields are `null`. Values are integers, strings, lists, objects, or `null`; never floats.

| Field | Type | Set on |
|---|---|---|
| `seq` | int ≥ 0 | all; equals the line index |
| `prev_sha256` | HEX64 | all; sha256 of the previous line's bytes without its LF; row 0 has `ZERO_SHA` |
| `time` | str (§1) | all |
| `slice_id` | str | all |
| `stage` | int 0–7 | all except RULING, which carries the stage of `halt_slot` |
| `slot` | str (§5.2) | all. OPEN: `00_PROMPT.md`. Authored rows (RECORDED, SEAT_FAILED, CONTEXT_OVERFLOW): the authored slot. MERGED and MERGE_FAILED: the MERGE log. QA_EVAL: the EVAL log. RULING: the `HALT.<n>.HUMAN.md` file |
| `packet_id`, `qa_round`, `round` | str / int / int | taken from `parse_slot_name(slot)`; `null` where absent |
| `attempt` | int 1–4 | authored rows: the job's attempt; kernel rows: `1`; OPEN and RULING: `null` |
| `seat_id`, `family`, `model`, `runtime` | str | Authored rows: the job seat's roster entry. OPEN and RULING: `human` in all four. Kernel rows: `kernel` in all four. Never taken from slot text |
| `kernel_sha256`, `lock_sha256` | HEX64 | all; equal to row 0 |
| `render_commit` | commit id | authored rows: `job.render_commit` (§10.1) |
| `base_commit` | commit id | OPEN: the resolved `base_ref`. CODE RECORDED rows with status `READY`: the worktree base (`B_q` for stage 4, the slice head for SYNTH). MERGED and MERGE_FAILED: the slice head before apply |
| `prompt_sha256`, `prompt_source` | HEX64 / `kernel` \| `bootstrap` | authored rows |
| `output_sha256` | HEX64 \| null | sha256 of the row's own file (§5.5). SEAT_FAILED: of the rejected bytes, or `null`. CONTEXT_OVERFLOW: `null` |
| `diff_sha256`, `gates_log_sha256`, `numstat_loc`, `manifest_paths`, `diff_paths` | HEX64 / HEX64 / int / list / list | CODE RECORDED rows with status `READY`. MERGE rows set `diff_sha256` (the applied SYNTH diff) and, when the apply succeeded, `numstat_loc`, `manifest_paths`, and `diff_paths`; their `gates_log_sha256` is `null` because the log is the slot |
| `gates` | `PASS` \| `FAIL` \| `NA` | CODE RECORDED rows (`NA` when status is not `READY`) and MERGE rows (`NA` when gates did not run) |
| `status` | str | PLAN, CODE, and QA RECORDED rows |
| `verdict`, `blocking_count` | str / int | VERDICT RECORDED rows |
| `outcome` | `OPEN` \| `RECORDED` \| `SEAT_FAILED` \| `CONTEXT_OVERFLOW` \| `MERGED` \| `MERGE_FAILED` \| `QA_EVAL` \| `RULING` | all |
| `failure` | §9.4 | SEAT_FAILED, MERGE_FAILED, CONTEXT_OVERFLOW |
| `estimated_tokens` | int | local authored rows |
| `cloud_run_id`, `source_ref`, `source_commit` | str / str / commit id | cloud authored rows |
| `qa_files` | object path → `{"packet": PKT_ID, "sha256": HEX64}` | 07 RECORDED rows (`{}` for `QA_TESTS: NONE`) |
| `qa_result`, `red_files`, `red_packets` | `GREEN` \| `RED` / list / list | QA_EVAL rows |
| `ruling`, `halt_code`, `halt_slot`, `dismissed_paths` | str / str / str / list | RULING rows (`dismissed_paths` is `[]` unless `DISMISS_QA_TEST`) |
| `ollama` | object `{done_reason, eval_count, prompt_eval_count, total_duration_ns, resident_bytes}` | local authored rows whose `generate` call returned; `null` on `TIMEOUT` and `CONTEXT_OVERFLOW` |
| `roster` | object (§9.2) | OPEN only |
| `config_sha256` | HEX64 | OPEN only: sha256 of `slice.json` |
| `bootstrap_sha256` | HEX64 | OPEN only, bootstrap slice only |
| `kernel_commit` | commit id | OPEN only: the repo `HEAD` when the kernel was pinned |

`HALT` is not an outcome. A HALT is derived from rows and never stored (§20 D5).

### 9.2 `roster` (OPEN row)

The roster has the form `{"planner": SEAT_ID, "challenger": SEAT_ID, "family_a": SEAT_ID, "family_b": SEAT_ID, "qa": [SEAT_ID, ...], "seats": {SEAT_ID: {"family": str, "model": str, "runtime": str}}}`, and `seats` covers every seat named in it. `derive` resolves seats only through the roster, never through the running lock, so a terminal slice still verifies after the lock changes.

### 9.3 Canonical line and chain

A row serializes as JSON with these rules:

- Keys are sorted by code point.
- Separators are `,` and `:`, with no whitespace.
- Non-ASCII characters are written as UTF-8 (`ensure_ascii=False`).
- Integers are written in decimal, and floats never appear.

The file is the concatenation of `line + LF`. `parse_rows` performs these checks, and any failure is `CHAIN_BROKEN`:

- Every row re-serializes to byte-identical bytes.
- `seq` and `prev_sha256` are correct for every row.
- The field set equals `ROW_FIELDS`, and every value has the §9.1 type.
- Row 0 is the only `OPEN` row.
- The file ends with LF.

`append_row` does the following, in order:

1. Take `LOCK_EX` on the proof file.
2. Read the last line, then assign `seq` and `prev_sha256`.
3. Write the new line, flush, and fsync.
4. Unlock.

This is salvaged from `.omarchy/omarchy.py:343-353`.

### 9.4 Failure codes

| Outcome | `failure` | Rejected bytes stored (`output_sha256` non-null) |
|---|---|---|
| `SEAT_FAILED` | `TIMEOUT` | never |
| | `SLOT_MISSING_IN_REF` | never |
| | `DONE_REASON`, `EMPTY_RESPONSE` | iff the response is at least 1 byte |
| | `TRAILER_INVALID`, `FILE_BLOCK_INVALID`, `PATH_NOT_ALLOWED`, `PROMPT_SHA_MISMATCH`, `PACKETS_INVALID`, `QA_MAP_INVALID`, `INPUT_MISMATCH` | iff slot bytes exist (local: the response; cloud: the slot file at the ref) |
| `MERGE_FAILED` | `APPLY_CONFLICT`, `LOC_LIMIT`, `DEPENDENCY_CHANGE`, `GATES_FAIL` | not applicable; the MERGE log is the row's file |
| `CONTEXT_OVERFLOW` | `CONTEXT_OVERFLOW` | never |

### 9.5 Kernel commits

There is one commit per row on `slice/<id>`, and each has exactly one parent. Commit `i` (the OPEN commit is 0) appends row `i`, so `PROOF.jsonl` at commit `i` has exactly `i + 1` lines. The OPEN commit's parent is the OPEN row's `base_commit`. The identity is `-c user.name=omarchy-kernel -c user.email=kernel@omarchy.invalid`, committed with `--no-verify` and `--no-gpg-sign`. Identity is not proof.

`kernel_commit(wt, row, add, delete)` works in four steps:

1. Write each `add` path under `wt` through `sterilize_path`, and run `git rm -q --` on each `delete` path.
2. Call `append_row`.
3. Run `git add -- <add paths> slices/<id>/PROOF.jsonl`.
4. Require that `git diff --cached --name-status --no-renames` equals `allowed_changes(row)` exactly, raising `OmarchyError` otherwise, then commit.

Message: the subject `chore(<slice_id>): <outcome lowercased> <slot>`, a blank line, then exactly these trailers:

```text
Omarchy-Slice: <slice_id>
Omarchy-Slot: <slot>
Omarchy-Seat: <seat_id>
Omarchy-Seq: <seq>
Omarchy-Output-Sha256: <HEX64 or none>
```

`parse_commit_trailers` takes the final paragraph of the message, requires every line to full-match `(Omarchy-[A-Za-z0-9-]+): (\S+)`, and returns them as a dict.

`allowed_changes(row)`, where `<d>` is `slices/<id>/`. The set is exact: a commit whose change set differs is `FOREIGN_COMMIT`.

| Row outcome | Exact `(status, path)` set |
|---|---|
| `OPEN` | A `<d>slice.json`, A `<d>00_PROMPT.md`, A `<d>PROOF.jsonl`; bootstrap also A `<d>BOOTSTRAP.json` and A each `<d>BOOTSTRAP.<slot>.prompt` |
| `RECORDED` | M `<d>PROOF.jsonl`; A `<d><slot>`; CODE with status `READY`: A both companions; QA: A each `qa_files` path |
| `SEAT_FAILED` | M `<d>PROOF.jsonl`; A `<d><rejected_name>` iff `output_sha256` is non-null |
| `CONTEXT_OVERFLOW` | M `<d>PROOF.jsonl` |
| `MERGED` | M `<d>PROOF.jsonl`; A `<d><slot>`; and for each path in `diff_paths`, A if absent at the parent commit, else M |
| `MERGE_FAILED`, `QA_EVAL` | M `<d>PROOF.jsonl`; A `<d><slot>` |
| `RULING` | M `<d>PROOF.jsonl`; A `<d><slot>`; D each `dismissed_paths` entry |

This is the durable, trailered proof the v2 kernel lacked (`.gitignore:4`; ballot N3 at `docs/GRAND_COUNCIL/v2.3.1_Test/LINUS_BALLOT.md:101-107`).

### 9.6 `kernel_sha256` and `lock_sha256`

`kernel_sha256(repo)` covers every regular file under `<repo>/omarchy/`, recursively, excluding any path with a `__pycache__` segment and any `*.pyc` file. For each file, form the line `<sha256 of bytes><two spaces><repo path>\n`. Sort the lines by path bytes and hash their concatenation. `lock_sha256` is the sha256 of the `agents.lock` bytes. Both are pinned in the OPEN row. `open` refuses with `KERNEL_DIRTY` if `git status --porcelain -- omarchy agents.lock` in the repo is non-empty, so the pinned kernel always equals the tree of `kernel_commit`.

---

## 10. Lineage and prompts

### 10.1 Render commits

Every authored job has a `render_commit`. Its lineage slot bytes are read from the commit of the row that introduced each slot (slot files are immutable, §11.2 checks 3–4). Its repo files are read at `render_commit`. A prompt is therefore a function of history fixed before the job became runnable, and `verify` can regenerate it.

| Job | `render_commit` |
|---|---|
| `01_PLAN.r1.md` | commit of row 0 (OPEN) |
| `02_CHALLENGE.rN.md` | commit of the RECORDED row of `01_PLAN.rN.md` |
| `01_PLAN.r2.md` | commit of the RECORDED row of `02_CHALLENGE.r1.md` |
| `03_PACKETS.json` | commit of the approval row: the RECORDED row of the approving `02_CHALLENGE.rN.md`, or the RULING row carrying `APPROVE_OVERRIDE` at `PLAN_DEADLOCK` |
| every per-packet job of QA round `q` (stages 4–6) | `B_q`. `B_1` is the commit of the `03_PACKETS.json` RECORDED row. `B_2` is the commit of the RED `QA_EVAL` row `E` that opened round 2 (§11.4 T19) |
| `07_QA.q{q}.<seat>.md` | `D_q`, the QA dispatch commit: the commit of the MERGED row with the greatest `seq` among MERGED rows with `qa_round = q` |
| KERNEL jobs | `None`; they act on the slice head |

`D_q` is fixed once every active packet of round `q` is MERGED. No row after it and before the round's QA records changes any file it names, so every QA seat of round `q` sees the same inputs, however many other QA seats record first (§20 D6).

Per-packet jobs render repo files at `B_q`, and SYNTH applies its blocks at the current slice head. The two agree on target content:

- Targets are disjoint.
- A packet's targets change only through that packet's MERGE.
- No MERGE of `p` precedes a later job of `p` within the same `q`.

### 10.2 Lineage tables

Slots are listed in render order, and each appears exactly once. `[x]` means `x` is included iff a RECORDED row (for companions, the file) exists for it at dispatch.

**Planning chain.**

| Job | Lineage slots | Repo files |
|---|---|---|
| `01_PLAN.r1.md` | `slice.json`, `00_PROMPT.md` | cloud read list: `context_files`, then `review_files` |
| `02_CHALLENGE.r1.md` | `slice.json`, `00_PROMPT.md`, `01_PLAN.r1.md` | cloud: as above; local challenger: `context_files` only, inlined |
| `01_PLAN.r2.md` | `slice.json`, `00_PROMPT.md`, `01_PLAN.r1.md`, `02_CHALLENGE.r1.md` | as `01_PLAN.r1.md` |
| `02_CHALLENGE.r2.md` | `slice.json`, `00_PROMPT.md`, `01_PLAN.r1.md`, `02_CHALLENGE.r1.md`, `01_PLAN.r2.md` | as `02_CHALLENGE.r1.md` |
| `03_PACKETS.json` | `slice.json`, `00_PROMPT.md`, `01_PLAN.r1.md`, `02_CHALLENGE.r1.md`, [`01_PLAN.r2.md`], [`02_CHALLENGE.r2.md`], then every `HALT.<n>.HUMAN.md` whose row precedes `render_commit`'s row, in ascending `n` | as `01_PLAN.r1.md` |

**Per-packet local jobs** for packet `p` in round `q`. `Lpp` is `slice.json`, `00_PROMPT.md`, the approved plan, the approval slot (the approving `02_CHALLENGE.rN.md`, or the `HALT.<n>.HUMAN.md` carrying `APPROVE_OVERRIDE`), and `03_PACKETS.json`. Superseded plan revisions and their challenges are excluded (§20 D6). `Q(q)` is empty for `q = 1`. For `q = 2` it is every RECORDED `07_QA.q1.<seat>.md` in `qa_seats` order, then the slot of `E`. `X.*` below stands for `X.md` and `X.gates.log`, never `X.diff`.

| Job | Lineage slots, in order |
|---|---|
| `04_p.qq.A.md`, `04_p.qq.B.md` | `Lpp`, `Q(q)` (neither proposal sees the other) |
| `05_p.qq.A_ON_B.md`, `05_p.qq.B_ON_A.md` | `Lpp`, `Q(q)`, `04_p.qq.A.*`, `04_p.qq.B.*` (neither critique sees the other, `P:433`) |
| `06_p.qq.SYNTH.r1.md` | the stage-5 list, `05_p.qq.A_ON_B.md`, `05_p.qq.B_ON_A.md` |
| `06_p.qq.REVIEW.r1.md` | the `SYNTH.r1` list, `06_p.qq.SYNTH.r1.*` |
| `06_p.qq.SYNTH.r2.md` | the `REVIEW.r1` list, `06_p.qq.REVIEW.r1.md`, [`06_p.qq.MERGE.r1.gates.log`] |
| `06_p.qq.REVIEW.r2.md` | the `SYNTH.r2` list, `06_p.qq.SYNTH.r2.*` |

Repo files, rendered at `B_q` with duplicates removed (keeping the first occurrence): `target_files(p)`, `context_files(p)`, slice `context_files`, and for `q = 2` the red files of `E` mapped to `p`, sorted. Sibling packets' slots are never lineage (`P:433`).

**QA jobs.** For `07_QA.q{q}.<seat>.md`, the lineage slots are every file under `slices/<id>/` at `D_q` except `PROOF.jsonl`, `*.rejected`, `BOOTSTRAP.json`, and `BOOTSTRAP.*.prompt`. They are ordered by the `seq` of the row that introduced them. Within the OPEN row the order is `slice.json` then `00_PROMPT.md`; within a CODE row it is the slot, `.gates.log`, then `.diff`. `PROOF.jsonl` is never lineage for any job. The repo files, rendered at `D_q` with duplicates removed, are:

1. For each packet in ascending order: its `target_files`, then its `context_files`.
2. The slice `context_files`.
3. `review_files`.
4. Every live `tests/qa/<id>/` file at `D_q`, sorted.

### 10.3 Token estimate

`estimate_tokens(prompt) = ⌈2 × cp / 7⌉`, where `cp` is the number of code points of the decoded prompt. This is the chars / 3.5 heuristic, `UNMEASURED` (`P:435`).

### 10.4 Rendering

Local lineage block:

```text
=== LINEAGE BEGIN ===
--- SLOT slices/<id>/<name> sha256=<hex> lines=<n> ---
<numbered lines>
--- REPO <path> @ <first 12 hex of render_commit> sha256=<hex> lines=<n> ---
<numbered lines>
--- REPO <path> @ <12 hex> ABSENT ---
=== LINEAGE END ===
```

Rules:

- Each numbered line is its 1-based number right-aligned in 6 columns, then `|`, then the line text.
- The lines are the bytes decoded as UTF-8 and split on LF, with the empty string after a final LF dropped, so `lines` is that count.
- A file that is non-empty and does not end with LF gets ` noeol` after `lines=<n>` in its header.
- A file that is not valid UTF-8 renders as `--- SLOT … BINARY sha256=<hex> ---` or `--- REPO … BINARY sha256=<hex> ---`, with no body.

Whole files only, never excerpts. Attempt 1's excerpts without line numbers produced citations about 12 lines off and 11 `UNKNOWN` rows (`P:90`); `.omarchy/omarchy.py:521-523` inlined raw text.

Cloud read list:

```text
=== READ LIST ===
commit: <render_commit, 40 hex>
SLOT slices/<id>/<name> sha256=<hex>
REPO <path> sha256=<hex>
REPO <path> ABSENT
```

There is one `SLOT` line per lineage slot and one `REPO` line per repo file, in §10.2 order. The `sha256` of a `REPO` line is that of the blob at `render_commit`. These lines are the canonical inputs that `record` checks (§13.4).

### 10.5 Budget (local jobs only)

`estimated = estimate_tokens(prompt) + reserve`. `reserve = 4096` for VERDICT jobs. For CODE jobs, `reserve = 4096 + ⌈1.3 × T / 3.5⌉`, where `T` is the total code-point count of the packet's target files at `render_commit` (§20 D7). If `estimated > num_ctx`, `run` writes a `CONTEXT_OVERFLOW` row with `estimated_tokens` and calls no model. Nothing is ever truncated.

### 10.6 Templates (`omarchy/prompts/*.md`)

Each file's content is the block below followed by one LF. The files are loaded as `string.Template` and filled with `substitute()`, so a missing key is fatal, and the mapping is exactly `{"slice_id", "slot", "seat_id"}`. No template contains any other `$`.

`family_a.md`:

```text
You are the Local Family A seat of the Omarchy council. You write complete implementations, critique Family B's work, and synthesize the best result from competing proposals and critiques.
Rules:
- Use only the files, symbols, and facts shown in the lineage. Never invent an API, an import, or a constant.
- If something you need is missing, say so: OMARCHY_STATUS NEEDS_PLAN or UNKNOWN for code, REQUEST_CHANGES with the gap named for a verdict.
- Return complete files, never fragments or placeholders.
- Cite evidence as path:line using the line numbers shown in the lineage.
```

`family_b.md`:

```text
You are the Local Family B seat of the Omarchy council. You write independent implementations, critique Family A's work, and review Family A's synthesis before it can merge.
Rules:
- Prefer the simplest auditable design. Distrust hidden state, silent fallbacks, unchecked inputs, time-of-check to time-of-use gaps, and status claims the code does not earn.
- Use only the files, symbols, and facts shown in the lineage. Never invent an API, an import, or a constant.
- If something you need is missing, say so: OMARCHY_STATUS NEEDS_PLAN or UNKNOWN for code, REQUEST_CHANGES with the gap named for a verdict.
- Cite evidence as path:line using the line numbers shown in the lineage.
```

`plan.md`:

```text
Omarchy slice $slice_id, slot $slot, seat $seat_id (planner).
Write the specification for this slice that local seats will implement through packets. Read every input in the read list. If a challenge is listed, resolve each of its blocking findings, or show with citations why it is factually wrong, and add a section titled "Response to" followed by the challenge slot name, with one row per finding. Cite repository evidence as path:line. If the specification cannot be completed, set OMARCHY_STATUS to NEEDS_PLAN and say what is missing.
```

`challenge.md`:

```text
Omarchy slice $slice_id, slot $slot, seat $seat_id (challenger).
Contest the latest plan revision among the inputs. For each defect give an id, BLOCKING or NON-BLOCKING, the location as path:line, the finding, and the required change. A finding is blocking if it prevents a literal implementation or contradicts the prompt. APPROVE only with zero blocking findings. REJECT only if the plan cannot be repaired.
```

`packets.md`:

```text
Omarchy slice $slice_id, slot $slot, seat $seat_id (planner).
Compile the approved plan into packets. Each packet is an independent unit of work for the local families. Its target files are disjoint from every other packet's targets, and its context files contain no packet's target. Dependent work belongs in a later slice. Every target must be listed in the approved plan's PLAN_FILES.
```

`propose.md`:

```text
Omarchy slice $slice_id, slot $slot, seat $seat_id (proposal).
Implement the packet below on your own. Return every target file you create or change as a complete file block, and touch no other file. The kernel runs the packet's verification commands and the slice test command on your files.
```

`critique.md`:

```text
Omarchy slice $slice_id, slot $slot, seat $seat_id (critique).
The slot name says whose proposal you critique: A_ON_B means Family A on Family B's proposal, B_ON_A the reverse. Judge it against the packet's instructions and acceptance criteria, its gate log, and the repository files. Your own family's proposal is shown for comparison. List each defect with path:line. Your verdict is advice for the synthesis and does not stop the pipeline.
```

`synthesize.md`:

```text
Omarchy slice $slice_id, slot $slot, seat $seat_id (synthesis).
Produce the single best implementation of the packet below from both proposals, both critiques, and any earlier review. Return every target file you create or change as a complete file block, and touch no other file. This synthesis merges only if its gates pass and Family B approves it.
```

`review.md`:

```text
Omarchy slice $slice_id, slot $slot, seat $seat_id (review).
Review the latest synthesis of the packet below. APPROVE only if it meets every acceptance criterion and you have zero blocking findings; an approved synthesis with passing gates is merged. REQUEST_CHANGES lists each blocking finding with path:line. REJECT only if the packet cannot be implemented as specified.
```

`qa.md`:

```text
Omarchy slice $slice_id, slot $slot, seat $seat_id (adversarial QA).
Attack the merged result of this slice with tests. Write a short report, and add new pytest files under tests/qa/$slice_id/ that fail when a packet's acceptance criteria are not met. Map every test file you add to exactly one packet.
```

`smoke.md`:

```text
Omarchy smoke test. Return exactly one file block for the path smoke/hello.txt whose content is the single line hello, followed by the trailer.
```

The template for each job class: `01` → `plan.md`; `02` → `challenge.md`; `03` → `packets.md`; `04` → `propose.md`; `05` → `critique.md`; `06 SYNTH` → `synthesize.md`; `06 REVIEW` → `review.md`; `07` → `qa.md`. `smoke` uses `smoke.md`. The persona is `family_a.md` or `family_b.md`, chosen by the job's family.

### 10.7 Output contracts

`output_contract` returns lines joined with LF and no final LF. Tokens in braces are replaced literally with `str.replace`:

| Token | Replacement |
|---|---|
| `{slice_id}` | the slice id |
| `{slice_idu}` | the slice id with `-` → `_` |
| `{targets}` | the targets joined with `, ` |
| `{plan_sha256}` | the approved plan's sha256 |
| `{max_packets}` | the decimal value |

Every other character is literal.

Shared lines:

- `H` = `=== OUTPUT CONTRACT ===`
- `V` (local classes only) = `The kernel stores your response verbatim as the slot.`
- `F` (CODE only) = `Put every file you create or change in a file block: a line "=== FILE: <path> ===", then the complete file content, then a line "=== END_FILE ===". Allowed paths: {targets}. A file block cannot delete a file.`
- `Q` (QA only) = `Add 0 to 10 new test files named tests/qa/{slice_id}/test_{slice_idu}_<name>.py, where <name> is 1 to 40 characters from a-z, 0-9, and _. Do not change or delete any existing file.`
- `T` = `End your response with exactly one trailer block: a line "---", then each line below with its <...> part replaced, then a line "---". Nothing may follow the closing "---" except blank lines. Use every key exactly once and no other key.`
- `S` = `OMARCHY_PROMPT_SHA256: <the hex value printed on the line after this prompt>`

| Class | Lines |
|---|---|
| PLAN (cloud) | `H`, `T`, `OMARCHY_STATUS: <READY, NEEDS_PLAN, or UNKNOWN>`, `PLAN_FILES: <comma-separated repository paths the plan creates or modifies, none under slices/ or tests/qa/; NONE only when not READY>`, `S` |
| VERDICT | `H`, [`V` if local], `T`, `OMARCHY_VERDICT: <APPROVE, REQUEST_CHANGES, or REJECT>`, `BLOCKING_COUNT: <number of blocking findings: 0 for APPROVE, at least 1 otherwise>`, `CITED_LOCATIONS: <comma-separated path:line or path:line-line entries, or NONE>`, [`S` if cloud] |
| CODE (local) | `H`, `V`, `F`, `T`, `OMARCHY_STATUS: <READY with at least one file block, or NEEDS_PLAN or UNKNOWN with no file blocks>`, `TOUCHED_FILES: <comma-separated paths of your file blocks; NONE when not READY>`, `MISSING_SYMBOLS: <NONE when READY; otherwise comma-separated items you need but were not given>` |
| QA (cloud) | `H`, `Q`, `T`, `OMARCHY_STATUS: READY`, `QA_TESTS: <entries "<path> -> <packet id>" joined by "; ", one per test file you added, or NONE>`, `S` |
| PACKETS (cloud) | `H`, then: `The slot is one JSON object: UTF-8, no comments, no duplicate keys, and no keys other than those named here.`, `"schema": 3`, `"plan_sha256": "{plan_sha256}"`, `"prompt_sha256": "<the hex value printed on the line after this prompt>"`, `"packets": a list of 1 to {max_packets} objects with packet_id "pkt-01", "pkt-02", and so on in order, each with exactly the keys packet_id, title, plan_section, instructions, acceptance, target_files, context_files, verification_commands.`, `title: 1 to 120 characters on one line. plan_section: a section number such as "3.2". instructions: 1 to 8000 characters. acceptance: 1 to 10 non-empty strings.`, `target_files: 1 to 5 repository paths, each listed in the approved plan's PLAN_FILES, none under slices/ or tests/qa/, and no path a target of two packets.`, `context_files: 0 to 10 repository paths, none of them a target of any packet.`, `verification_commands: 1 to 5 argument lists of strings whose first string is never a shell.` |
| RULING | never prompted; `output_contract(RULING, …)` raises `ValueError` |

The tables of §7 generate these lines, so the trailer grammar a seat sees cannot drift from the parser (T-T8). In attempt 1, parent wrote the trailer enum and qweny emitted `COMPLETE` (`docs/GRAND_COUNCIL/v2.3.1_Test/QWENY_AUDIT_WORKSHEET.md:141`).

### 10.8 Prompt composition

The prompt is the UTF-8 encoding of `"\n\n".join(part.rstrip("\n") for part in parts) + "\n"`.

- **Local per-packet job**, parts:
  1. persona
  2. the substituted stage template
  3. the packet block
  4. the lineage block
  5. the output contract (with `targets` = the packet's `target_files` for CODE)
- **Local challenger**, parts: persona, template, lineage block, contract.
- **Cloud job**, parts:
  1. the substituted stage template
  2. the read list
  3. the delivery block
  4. the output contract (PACKETS: with `plan_sha256` and `max_packets`)
- **Smoke**, parts: persona, `smoke.md`, then `output_contract(CODE, cloud=False, slice_id="smoke", targets=("smoke/hello.txt",))`.

Packet block:

```text
=== PACKET ===
packet_id: <packet_id>
title: <title>
plan_section: <plan_section>
instructions:
<instructions>
acceptance:
- <each item>
target_files:
- <each path>
context_files:
- <each path, or the single line "- NONE">
verification_commands:
- <shlex.join(argv) for each command>
```

Delivery block (cloud). The middle line appears for QA jobs only.

```text
=== DELIVERY ===
Check out commit <render_commit> (branch slice/<id> at or after it). Write exactly slices/<id>/<slot>.
You may also add test files as described in the output contract. Add or change nothing else.
Commit with message "docs(<id>): <seat_id> <slot>" and push. Report the branch, the commit id of that commit, and your cloud run id.
```

### 10.9 Prompt sha and source

`ingest.expected_prompt(repo, view, job)` works as follows:

- If the slice is the bootstrap slice and `job.slot` is a key of `BOOTSTRAP.json` `prompts`, it returns the bytes of `BOOTSTRAP.<slot>.prompt`, that key's sha, and `bootstrap`.
- If the slice is the bootstrap slice and the slot is not a key, it raises `Refusal("BOOTSTRAP_MISMATCH")`.
- Otherwise it returns `build_prompt(repo, view, job)`, its sha256, and `kernel`.

`omarchy prompt` prints the prompt bytes, then one extra line, `OMARCHY_PROMPT_SHA256 value: <hex>` followed by LF. That line is not part of the hashed bytes. Cloud seats echo the value (`P:404`). The echo shows the seat received the canonical prompt. It does not prove nothing was appended (`P:404`).

---

## 11. State machine

### 11.1 Inputs

`view.load_view(repo, slice_id)` builds the view from git objects:

1. Resolve `slice/<id>`; a missing branch yields zero rows.
2. Parse `PROOF.jsonl` at the tip.
3. List the commits from the OPEN commit's parent to the tip with `list_commits`.
4. List the tip files under `slices/<id>/` and `tests/qa/<id>/` with their sha256 values.
5. Parse `slice.json` structurally.
6. Parse `03_PACKETS.json` with `parse_packets` if it is present, using the approved plan and its `PLAN_FILES`.
7. Parse `BOOTSTRAP.json` if it is present.
8. Compute the running `kernel_sha256` and load the running lock. `running_lock` is `None` if the lock fails to parse.

`machine.next_step(view)` is pure (`P:603`).

### 11.2 Integrity checks

The checks run in this order. The first failure becomes `REFUSE <code> <subject>`.

| # | Code | Check |
|---|---|---|
| 1 | `NOT_OPEN` | Branch `slice/<id>` is missing, or the proof has zero rows |
| 2 | `CHAIN_BROKEN` | §9.3 |
| 3 | `FOREIGN_COMMIT` | Any of these: the commit count ≠ the row count; a commit with ≠ 1 parent; the first commit's parent ≠ row 0 `base_commit`; commit `i` lacks a trailer or has a mismatched one (slice, slot, seat, seq = `i`, output sha); `proof_lines ≠ i + 1`; the change set ≠ `allowed_changes(row i)` |
| 4 | `SLOT_SHA_MISMATCH` | A path in `required_files(rows)` (§5.5) is missing at the tip or has a different sha256 |
| 5 | `UNKNOWN_SLOT_FILE` | A tip file under `slices/<id>/` is neither `PROOF.jsonl` nor a key of `required_files`, or fails §5.2. Or a tip file under `tests/qa/<id>/` is not a key of `required_files` |
| 6 | replay | For each row `i ≥ 1`, with `step_i = derive(view, i)`, in this order: `DUPLICATE_SLOT`, `SAME_FAMILY_CRITIQUE`, `WRONG_SEAT_FOR_SLOT`, `OUT_OF_ORDER` (§11.3) |
| 7 | `KERNEL_CHANGED` / `LOCK_CHANGED` | A row's `kernel_sha256` or `lock_sha256` differs from row 0 (always checked). The running kernel or lock sha differs from row 0, checked only when `derive(view, N)` is non-terminal (§20 D8) |
| 8 | `ILLEGAL_CONFIG` | Non-terminal only: `running_lock` is `None`, `check_config_legal(cfg, running_lock)` fails, or the roster no longer matches the running lock |

Terminal means `DONE`, `DONE_BOOTSTRAP`, or `HALT ABORTED`.

### 11.3 Replay acceptance

Row `i` is accepted against `step_i` only as follows. The first failing rule gives the code.

1. `DUPLICATE_SLOT`: an earlier row has the same `slot` and an outcome in `{RECORDED, CONTEXT_OVERFLOW, MERGED, MERGE_FAILED, QA_EVAL, RULING}`.
2. `SAME_FAMILY_CRITIQUE`: the row's slot reviews another slot (`02_CHALLENGE.rN` reviews `01_PLAN.rN`; `A_ON_B` reviews `04.B`; `B_ON_A` reviews `04.A`; `REVIEW.rN` reviews `SYNTH.rN`), the reviewed slot has a RECORDED row before `i`, and that row's `family` equals row `i`'s `family` (`P:103`).
3. If `step_i` is `NEXT`, let `J` be the job in `step_i.jobs` whose `slot` equals the row's `slot`. If there is no such job, the result is `OUT_OF_ORDER`.
   - `WRONG_SEAT_FOR_SLOT`: the row's `seat_id`, `family`, `model`, or `runtime` differs from the roster entry of `J.seat_id` (`kernel` in all four for KERNEL jobs).
   - `OUT_OF_ORDER`: any of the following:
     - The row's `attempt` ≠ `J.attempt`.
     - The row's `render_commit` ≠ `J.render_commit`.
     - The outcome is not allowed for `J`. Allowed outcomes: CLOUD author `{RECORDED, SEAT_FAILED}`; LOCAL author `{RECORDED, SEAT_FAILED, CONTEXT_OVERFLOW}`; merge `{MERGED, MERGE_FAILED}`; qa_eval `{QA_EVAL}`.
4. If `step_i` is `HALT` with a code other than `ABORTED`, the row MUST be a `RULING` with seat `human`. Its `halt_code` and `halt_slot` MUST equal the step's, its `ruling` MUST be in `legal_rulings(view, i)`, and its `dismissed_paths` MUST obey §12. Otherwise the result is `OUT_OF_ORDER` (or `WRONG_SEAT_FOR_SLOT` for a non-human seat).
5. If `step_i` is `DONE`, `DONE_BOOTSTRAP`, or `HALT ABORTED`, the result is `OUT_OF_ORDER`.

Only the emitted step's jobs are acceptable. Kernel pre-emption (T14) is therefore normative for histories: a LOCAL row appended while `next` prints `NEXT KERNEL` is `OUT_OF_ORDER` (T-M39). `run` never produces such a row, because it recomputes the step before every job (§13.5).

### 11.4 Transitions

`want(S, seat, render)` applies to an authored slot `S`:

- If `S` has a RECORDED row, it is satisfied.
- Else, if `S` has a CONTEXT_OVERFLOW row, the result is `HALT CONTEXT_OVERFLOW S`.
- Else let `k` be the number of SEAT_FAILED rows for `S`, and `budget = 2 + 2 × (number of RETRY rulings with halt_slot = S)`. If `k ≥ budget`, the result is `HALT SEAT_FAILED S`.
- Otherwise it yields a job for `S` with `attempt = k + 1` and `render_commit = render`. The job's kind is `CLOUD` or `LOCAL` by the seat's roster runtime (`P:503-504`).

`derive(view, n)` evaluates the rules below in order over the first `n` rows. The first rule that yields a result ends evaluation. `planner`, `challenger`, `family_a`, `family_b`, and the QA seats come from the roster.

| # | Condition | Result |
|---|---|---|
| T1 | `n = 0` | `REFUSE NOT_OPEN -` |
| T2 | A RULING row with `ruling = ABORT` | `HALT ABORTED <that ruling's slot>` |
| T3 | `want(01_PLAN.r1.md, planner, commit of row 0)` not satisfied | its job or HALT |
| T4 | Let `m = 2` if `01_PLAN.r2.md` is RECORDED, else `1`. `status(01_PLAN.rm) ≠ READY` | `HALT PLAN_NEEDS_INPUT 01_PLAN.rm.md` |
| T5 | `want(02_CHALLENGE.rm.md, challenger, commit of 01_PLAN.rm's row)` not satisfied | its job (CLOUD, or LOCAL for a Family A challenger) or HALT |
| T6 | verdict(`02.rm`) = `REJECT` | `HALT PLAN_REJECTED 02_CHALLENGE.rm.md` |
| T7 | verdict = `REQUEST_CHANGES` and `m = 1` | the job or HALT from `want(01_PLAN.r2.md, planner, commit of 02.r1's row)` |
| T8 | verdict = `REQUEST_CHANGES`, `m = 2`, and no `APPROVE_OVERRIDE` RULING with `halt_slot = 02_CHALLENGE.r2.md` | `HALT PLAN_DEADLOCK 02_CHALLENGE.r2.md` |
| T9 | The approved plan is `01_PLAN.rm.md`. Row 0 has `bootstrap_sha256` set | `DONE_BOOTSTRAP` |
| T10 | `want(03_PACKETS.json, planner, commit of the approval row)` not satisfied | its job or HALT |
| T11 | **Initialize once:** `q := 1`; `A := ` all packet ids ascending; `B := ` the commit of the `03_PACKETS.json` RECORDED row | continue |
| T12 | **Round body.** For each `p` in `A` (ascending), compute `PS(p, q, B)` by §11.5 | continue |
| T13 | Some `PS` is HALT | the HALT of the lowest packet id |
| T14 | Some `PS` has a KERNEL job | `NEXT KERNEL` with only the lowest packet's KERNEL job |
| T15 | Some `PS` has jobs | `NEXT LOCAL` with every LOCAL job, ordered by (stage, packet id, slot) |
| T16 | All `PS` are DONE. Let `D := D_q` (§10.1). For each seat `s` in `qa_seats` order, `want(07_QA.q{q}.<s>.md, s, D)` | the first HALT in `qa_seats` order, or else `NEXT CLOUD` with every pending QA job, or else continue |
| T17 | Let `E` be the QA_EVAL row with `qa_round = q` and the greatest `seq`. `E` does not exist, or a `DISMISS_QA_TEST` RULING with `halt_slot = E.slot` exists | `NEXT KERNEL qa_eval 07_QA.q{q}.EVAL.{k}.gates.log`, with `k = 1 +` the number of QA_EVAL rows with `qa_round = q` |
| T18 | `E.qa_result = GREEN` | `DONE` |
| T19 | `E` is RED, `q = 1`, and `E.red_packets` is non-empty | `q := 2`; `A := E.red_packets`; `B := ` the commit of `E`; **go to T12**. T11 is not re-executed |
| T20 | `E` is RED otherwise | `HALT QA_RED <E.slot>` |

T19 fires only while `q = 1` and sets `q = 2`, so the round body runs at most twice and `derive` terminates. `NEXT KERNEL` and `NEXT CLOUD` steps carry jobs of one kind only, and `NEXT LOCAL` steps carry LOCAL jobs only.

### 11.5 Per-packet state `PS(p, q, B)` → `DONE` | jobs | HALT

Evaluate the steps in order. Every `want` here uses `render = B`. A step that yields jobs returns them, except steps 1 and 3, which collect the jobs of both slots first. A HALT returned by either slot of a pair dominates that pair's jobs, with A checked before B.

1. `want(04_p.qq.A.md, family_a)` and `want(04_p.qq.B.md, family_b)`.
2. Both proposals are RECORDED here. If either status is not `READY`, return `HALT PROPOSAL_NEEDS_PLAN` on the first such slot, in A, B order.
3. `want(05_p.qq.A_ON_B.md, family_a)` and `want(05_p.qq.B_ON_A.md, family_b)`. Stage-5 verdict values are advisory input to the synthesis. No rule reads them, and `APPROVE`, `REQUEST_CHANGES`, and `REJECT` lead to the same next step (T-M40).
4. For `r = 1, 2`:
   1. `want(06_p.qq.SYNTH.rr.md, family_a)`. If its status ≠ `READY`, return `HALT PROPOSAL_NEEDS_PLAN <SYNTH slot>`.
   2. If the SYNTH row's `manifest_paths` is non-empty and no `APPROVE_DEPENDENCY` RULING has `halt_slot` = that SYNTH slot, return `HALT DEPENDENCY_CHANGE <SYNTH slot>` (§20 D9).
   3. `want(06_p.qq.REVIEW.rr.md, family_b)`. If its verdict is `REJECT`, return `HALT SYNTH_REJECTED <REVIEW slot>`.
   4. `mergeable := (verdict = APPROVE ∧ SYNTH gates = PASS ∧ SYNTH numstat_loc ≤ 300) ∨ (r = 2 ∧ an APPROVE_OVERRIDE RULING with halt_slot = 06_p.qq.REVIEW.r2.md exists)`.
   5. If `mergeable`: if `06_p.qq.MERGE.rr.gates.log` has no row, yield the job `KERNEL merge` on that slot. If its row is `MERGED`, return `DONE`. If it is `MERGE_FAILED`, the round failed, with class `TESTS` for `GATES_FAIL` and class `BLOCKED` otherwise.
   6. If not `mergeable`, the round failed with class `TESTS` if SYNTH gates are `FAIL`, else class `BLOCKED` if `numstat_loc > 300`, else class `REVIEW`.
   7. If the round failed and `r = 1`, continue with `r = 2`. If it failed and `r = 2`, return `HALT TESTS_RED` (class `TESTS`), `HALT MERGE_BLOCKED` (class `BLOCKED`), or `HALT SYNTH_DEADLOCK` (class `REVIEW`). The subject is the MERGE log slot if a MERGE row exists, else the REVIEW slot (§20 D10).

### 11.6 Output grammar and exit codes

`next` prints exactly one category on stdout, one line per entry:

```text
NEXT (CLOUD|LOCAL) <SEAT_ID> <slot> a[1-4]           one line per job, all of one kind
NEXT KERNEL (merge|qa_eval) <slot> a1                exactly one line
HALT <HALT_CODE> <slot>
DONE
DONE_BOOTSTRAP
REFUSE <REFUSE_CODE> (<slot or repo path>|-)          detail on stderr
```

| Category | `next` exit |
|---|---|
| `NEXT` | 0 |
| `HALT` | 3 |
| `DONE`, `DONE_BOOTSTRAP` | 4 |
| `REFUSE` | 65 |

Other exit codes, for all commands: 1 kernel error, 2 git error, 64 usage error, and 66 when `run` finds nothing runnable locally (§13.5).

### 11.7 `STAGES`

`STAGES` is a tuple of 8 tuples `(stage, slot, author_cap, runtime)` of these exact strings. `01_OMARCHY_AGENT_PROMPTS.md` reproduces it (T-D3).

| Stage | Slot | Author cap | Runtime |
|---|---|---|---|
| 0 | `slice.json, 00_PROMPT.md` | `human` | `human` |
| 1 | `01_PLAN.r{n}.md` | `plan` | `cloud` |
| 2 | `02_CHALLENGE.r{n}.md` | `challenge` | `cloud or local_family_a` |
| 3 | `03_PACKETS.json` | `plan` | `cloud` |
| 4 | `04_<pkt>.q{q}.{A,B}.md` | `propose` | `local` |
| 5 | `05_<pkt>.q{q}.{A_ON_B,B_ON_A}.md` | `critique` | `local` |
| 6 | `06_<pkt>.q{q}.{SYNTH,REVIEW,MERGE}.r{n}` | `synthesize, review, kernel` | `local, kernel` |
| 7 | `07_QA.q{q}.{<seat>,EVAL.<k>}` | `qa, kernel` | `cloud, kernel` |

---

## 12. HALT codes and human rulings

| HALT code | Arises at | Legal rulings besides `ABORT` | Effect |
|---|---|---|---|
| `PLAN_NEEDS_INPUT` | T4 | none | — |
| `PLAN_REJECTED` | T6 | none | — |
| `PLAN_DEADLOCK` | T8 | `APPROVE_OVERRIDE` | `01_PLAN.r2` is approved; T9 or T10 comes next |
| `PROPOSAL_NEEDS_PLAN` | §11.5 steps 2 and 4.1 | none | — |
| `DEPENDENCY_CHANGE` | §11.5 step 4.2 | `APPROVE_DEPENDENCY` | The REVIEW job comes next, and the merge accepts those manifest paths |
| `SYNTH_REJECTED` | §11.5 step 4.3 | none | — |
| `SYNTH_DEADLOCK` | §11.5 step 4.7 | `APPROVE_OVERRIDE` | The r2 merge job comes next |
| `TESTS_RED` | §11.5 step 4.7 | none | Tests cannot be overridden (`P:515`) |
| `MERGE_BLOCKED` | §11.5 step 4.7 | none | The human splits the work into a new slice (`P:755`) |
| `QA_RED` | T20 | `DISMISS_QA_TEST`, only while `E.red_files` contains at least one live path | The listed tests are deleted in the ruling commit; a new `qa_eval` comes next (T17) |
| `SEAT_FAILED` | §11.4 `want` | `RETRY`, only if no earlier `RETRY` has this `halt_slot` | The attempt budget becomes 4 |
| `CONTEXT_OVERFLOW` | §11.4 `want` | none | — |
| `ABORTED` | T2 | none (terminal) | A new slice may cite it (`P:506`) |

`ABORT` is legal at every HALT except `ABORTED`. `legal_rulings(view, n)` derives the step after `n` rows and returns exactly this table's set for it, applying the two history conditions in the table. A `DISMISS_QA_TEST` ruling's `dismissed_paths` MUST be a non-empty subset of `E.red_files` whose members are all live. Every other ruling has `dismissed_paths = []`.

### 12.1 Termination and index bounds

- **Attempts.** `RETRY` is legal at most once per slot, so `budget ∈ {2, 4}` and `attempt ∈ {1, …, 4}`, which is exactly `a[1-4]`.
- **QA evaluations.** A QA record adds at most 10 files (§13.4), so at most `10 × |qa_seats| × 2 ≤ 60` QA files ever exist in a slice. QA files are added only by `07` records, and T16 offers those only before a round's first evaluation. Each `DISMISS_QA_TEST` removes at least one live file. So within round `q` there are at most `1 + 60` QA_EVAL rows, and the dismissal loop terminates.
- **Rulings.** Each ruling settles a derived HALT whose recurrence is bounded:
  - `RETRY`: once per authored slot.
  - `APPROVE_OVERRIDE`: once per deadlock slot.
  - `APPROVE_DEPENDENCY`: once per SYNTH slot.
  - `DISMISS_QA_TEST`: at most 60 in total.
  - `ABORT`: at most once, because it is terminal.

  The ruling count is therefore finite.
- **Grammar.** `EVAL.<k>` and `HALT.<n>` use the unbounded `INDEX` grammar (§5.2), so no legal history exceeds the slot grammar (T-M41).

---

## 13. Commands

Every mutating command (`open`, `record`, `run`, `rule`) does the following, in this order:

1. Take `slice_lock`.
2. Except for `open`, run `check_clean` on the slice worktree, then check integrity through `next_step`.
3. Do the work.
4. Immediately before each commit or fast-forward, re-check that the slice worktree is clean and its head is the expected commit.

This places the precondition checks before the expensive step (ballot N4, `.omarchy/omarchy.py:437-461`).

Precondition refusal codes (`REFUSE`, exit 65):

| Code | Meaning |
|---|---|
| `NOT_OPEN` | The slice is not open |
| `ALREADY_OPEN` | `slice/<id>` already exists at `open` |
| `SLICE_BUSY` | Another command holds the slice lock |
| `DIRTY_WORKTREE` | The slice worktree has uncommitted changes |
| `WRONG_BRANCH` | The slice worktree is not on `slice/<id>` |
| `KERNEL_DIRTY` | `omarchy/` or `agents.lock` has uncommitted changes at `open` |
| `SLICE_DIR_INVALID` | The input directory fails §13.1 step 1 |
| `BOOTSTRAP_MISMATCH` | Bootstrap inputs do not match (§13.1, §10.9) |
| `ILLEGAL_CONFIG` | §4 |
| `ILLEGAL_LOCK` | §3 |
| `NOT_EXPECTED_SLOT` | The slot is not a current job |
| `NOT_CLOUD_JOB` | `record` was given a local job's slot |
| `WRONG_SEAT_FOR_SLOT` | `record --seat` differs from the job's seat |
| `MISSING_RUN_ID` | `--cloud-run` is missing or malformed |
| `REF_NOT_FOUND` | `--ref` does not resolve to a commit |
| `LINEAGE_MISMATCH` | The ref does not descend from, or does not hold, the canonical inputs |
| `ILLEGAL_RULING` | The ruling is not legal at the current HALT |
| `NO_TTY` | `rule` cannot open `/dev/tty` |
| `PROMPT_SHA_MISMATCH` | `verify` only: a regenerated prompt differs from the row |
| `SOURCE_MISMATCH` | `verify` only: §13.7 |

### 13.1 `omarchy open <slice_id> [--bootstrap]`

1. In the repo `HEAD` tree, `slices/<id>/` exists, and `git status --porcelain -- slices/<id>` is empty. Every file in it full-matches §5.2. It contains `slice.json` and a non-empty `00_PROMPT.md`, valid UTF-8 with no CR. Otherwise the result is `SLICE_DIR_INVALID`. Input bytes are read from `HEAD` blobs, never from the working tree. Other slot-grammar files are ignored and not copied.
2. `slice/<id>` MUST NOT exist (`ALREADY_OPEN`). The kernel MUST be clean (`KERNEL_DIRTY`, §9.6). The lock MUST parse.
3. Parse `slice.json`, then run `check_config_legal`. `base_ref` MUST resolve, and every `context_files` and `review_files` path MUST be a regular-file blob at `base_ref` (`ILLEGAL_CONFIG`).
4. `--bootstrap` is legal only if all of the following hold. Otherwise the result is `BOOTSTRAP_MISMATCH`.
   - `BOOTSTRAP.json` is present and parses, and its `slice_id` matches.
   - Every `files[path].sha256` equals the sha256 of the `HEAD` blob.
   - Every `prompts` entry has its `BOOTSTRAP.<slot>.prompt` file, with that sha.

   Without `--bootstrap`, the presence of `BOOTSTRAP.json` is `SLICE_DIR_INVALID`.
5. Create branch `slice/<id>` at the `base_ref` commit, and the worktree `.omarchy/worktrees/<id>/slice`. Then `kernel_commit` the OPEN row (seat `human`, roster, pins, `kernel_commit`, `config_sha256`, `bootstrap_sha256`) together with the input files (and, when bootstrapping, the bootstrap files). Print `OPENED <id> <commit>`. Exit 0.

### 13.2 `omarchy next <slice_id>`

Read-only: no writes, no network, no model call. It prints per §11.6. This is the only dry path (`P:111`).

### 13.3 `omarchy prompt <slice_id> <slot>`

- If `slot` is the slot of a job in the current step, print `expected_prompt` for that job.
- Else, if `slot` has an authored row with `seq = i`, take the job for `slot` in `derive(view, i)` and print its `expected_prompt`.
- Otherwise the result is `NOT_EXPECTED_SLOT`.

The output format is §10.9.

### 13.4 `omarchy record <slice_id> --slot S --seat X --ref R --cloud-run ID`

`parent` fetches first; the kernel never fetches or pushes. `R` MUST be the commit the seat reported, not a branch tip that later work extended (§17.3).

**A. Operator checks.** Each one refuses with no row and consumes no attempt.

1. `S` MUST be the slot of a job in the current `NEXT CLOUD` step (`NOT_EXPECTED_SLOT`). A job of another kind gives `NOT_CLOUD_JOB`.
2. `X` MUST equal the job's seat (`WRONG_SEAT_FOR_SLOT`).
3. `ID` MUST full-match `[A-Za-z0-9._:-]{1,128}` (`MISSING_RUN_ID`).
4. `R` MUST resolve with `git rev-parse --verify R^{commit}` (`REF_NOT_FOUND`).
5. `expected_prompt` MUST succeed (`BOOTSTRAP_MISMATCH`).
6. Provenance:
   - **Kernel prompts:** `render_commit` MUST be an ancestor of, or equal to, `R`.
   - **Bootstrap prompts:** every lineage slot of `S` (§10.2) MUST exist at `R` with its recorded sha.

   Failure is `LINEAGE_MISMATCH`.

**B. Content checks.** The first failure writes a `SEAT_FAILED` row that counts toward the attempt budget. The row stores `rejected_name(S, k)` when slot bytes exist at `R` (§9.4). The command then prints `SEAT_FAILED <failure> <S> a<k>` and exits 65. Let `H` be the slice head and `D = merge-base(R, H)`.

1. **Path provenance.** For each path `x` in `git diff --name-only --no-renames H R`, apply the first matching case:
   - `x` passes `ingest_allowed(S, x)` and, if `x` is under `tests/qa/`, is absent at `H`: take it.
   - The blob of `x` at `R` equals its blob at `D`, or `x` is absent at both: ignore it. This is slice progress the seat never touched.
   - Otherwise the result is `PATH_NOT_ALLOWED`.

   `ingest_allowed(S, x)` permits `slices/<id>/<S>`, and for `07` slots any `x` with `qa_file_ok(id, x)`. A seat that edited a lineage slot, a repo input, or an existing QA file therefore fails here.
2. **Inputs.** For kernel prompts, `check_inputs(R, …)` over every `SLOT` and `REPO` line of the read list (§10.4) MUST return no path, else `INPUT_MISMATCH`. Given A6 and B1 this check cannot fail; it is kept as a direct check of the canonical inputs (`C:52-53`) and is unit-tested through `check_inputs` (T-I12).
3. **Slot present.** The slot file MUST exist at `R`, else `SLOT_MISSING_IN_REF`.
4. **Parse.** Parse by class with `cloud=True`, so `TRAILER_INVALID` and the other grammar failures apply.
   - `03`: `parse_packets` with the approved plan's sha and `PLAN_FILES` (`PACKETS_INVALID`).
   - `07`: the taken QA files number 0–10. `QA_TESTS` lists each taken file exactly once, every packet in it exists, and `NONE` ⇔ zero files. Any failure is `QA_MAP_INVALID`.
5. **Prompt sha.** The claimed prompt sha (§7.5) MUST equal the sha from `expected_prompt`, else `PROMPT_SHA_MISMATCH`.

**C. Success.**

1. `kernel_commit` the slot bytes exactly as they are at `R`, the taken QA files, and a `RECORDED` row. The row carries `cloud_run_id`, `source_ref = R` as given, `source_commit` (the resolved id), the parsed fields, `qa_files`, `prompt_sha256`, `prompt_source`, and `render_commit`.
2. Call `tag_source(seq, source_commit)`.
3. Print `RECORDED <S>`. Exit 0.

A `SEAT_FAILED` row from step B also calls `tag_source`. Pushing those tags is `parent`'s job (§16).

### 13.5 `omarchy run <slice_id>`

1. Run the preconditions above. If the step is neither `NEXT LOCAL` nor `NEXT KERNEL`, print it and exit: 66 for `NEXT CLOUD`, otherwise `exit_code(step)` (T-R2).
2. If the step is `NEXT LOCAL`, call `ollama.sweep(client)` (K7).
3. Set `wrote := 0`, then loop:
   1. Recompute the step from a fresh `load_view`.
   2. On `NEXT KERNEL`, execute its single job (§14.5, §14.7), set `wrote += 1`, and go to 3.1.
   3. On `NEXT LOCAL`, let `F = local_family_a` if the step has a Family A job, else `local_family_b`. Every session evicts at exit (K6), so no family is ever resident when `F` is chosen, and the plan's preference for the resident family (`P:458`) reduces to this rule (§20 D23).
   4. Enter `family_session(F)`. Inside it, repeat:
      - Recompute the step.
      - On `NEXT KERNEL`, execute its job.
      - On `NEXT LOCAL` with at least one `F` job, execute the first `F` job in step order.
      - Otherwise, leave the session.

      Each execution increments `wrote`. After leaving the session, go to 3.1.
   5. On any other step, print `format_step(step)` and exit. The exit code is `exit_code(step)`, except `NEXT CLOUD`, which exits 0 if `wrote > 0` and 66 otherwise.
4. Local job execution:
   1. Build the prompt and compute `estimated` (§10.5). On overflow, commit a `CONTEXT_OVERFLOW` row and return.
   2. Call `session.generate`. Its failures become `SEAT_FAILED` rows:
      - A socket timeout is `TIMEOUT`.
      - `done_reason ≠ "stop"` is `DONE_REASON`, and the bytes are kept.
      - An empty or whitespace-only response is `EMPTY_RESPONSE`.
   3. `parse_slot(cls, response, cloud=False, allowed_paths=targets)`. A `SeatFailure` becomes a `SEAT_FAILED` row with the rejected bytes.
   4. For CODE with status `READY`:
      1. Open `TempWorktree` at `render_commit` for stage 4, or at the slice head for SYNTH.
      2. Run `write_blocks` (a `SeatFailure` becomes a `SEAT_FAILED` row), then `stage_diff`, then `run_gates` (§14.4).
      3. Commit the `.md`, `.diff`, and `.gates.log` with the RECORDED row.

      For CODE that is not `READY`, commit only the `.md`, with `gates: NA`.
   5. Otherwise, commit the `.md` with the RECORDED row, including the `ollama` stats and `estimated_tokens`.
5. Ollama transport errors raise `OmarchyError`. They write no row and exit 1, because infrastructure failure never consumes a seat attempt (§20 D11).

### 13.6 `omarchy rule <slice_id> --ruling R --reason TEXT [--paths a,b]`

The current step MUST be `HALT`, and `R` MUST be in `legal_rulings`. `--paths` is required for `DISMISS_QA_TEST` and only for it, and it MUST obey §12. Otherwise the result is `ILLEGAL_RULING`.

1. Call `confirm(text)`, where `text` is the HALT line, the ruling, and `Type the slice id to confirm: `. The default `tty_confirm` opens `/dev/tty`; when it cannot, the result is `NO_TTY`.
2. The returned line, stripped of its trailing LF, MUST equal the slice id, else `ILLEGAL_RULING`.
3. Render `HALT.<n>.HUMAN.md` with `render_ruling`, where `n = 1 +` the number of RULING rows. The body is `# Ruling <n>`, a blank line, then `HALT line: <HALT line>`.
4. `kernel_commit` the file, deletions of the dismissed paths, and a `RULING` row (seat `human`) (§20 D13).

The CLI always uses `tty_confirm`; tests pass a stub. The TTY check is friction, not authentication: the host can still forge it (`P:756`).

### 13.7 `omarchy verify <slice_id>`

1. Run §11.2.
2. **Source check.** For every cloud authored row:
   - Tag `omarchy/<id>/source-<seq>` exists and points at `source_commit`.
   - For RECORDED rows, the blob `slices/<id>/<slot>` at `source_commit` has sha256 `output_sha256`.
   - For rows with `prompt_source = kernel`, `render_commit` is an ancestor of `source_commit`.

   Failure is `REFUSE SOURCE_MISMATCH <slot>`.
3. **Prompt check.** If the slice is non-terminal or its pins still hold, regenerate the prompt of every row with `prompt_source = kernel` (as §13.3) and compare its sha to `prompt_sha256`. A difference is `PROMPT_SHA_MISMATCH`.
4. Print `VERIFIED <id> rows=<n> <step line>`. Exit 0 or 65.

### 13.8 `omarchy verify --repo`

Run `verify` on every `refs/heads/slice/*` branch. Then, for `slices/s000-bootstrap/BOOTSTRAP.json` at repo `HEAD`, print one line `<label>\t<path>` per file, in path order. `coverage_label` is pure and depends only on `HEAD` content and the slice branches, so every PR merge strategy (merge commit, squash, rebase, fast-forward) yields the same labels (§20 D21).

A `SliceFacts` entry exists for each slice whose step is `DONE`. `merged_sha256[path]` is the sha256 of `path` at the commit of the last MERGED row whose `diff_paths` contains it. `reviewed_paths` is the union of the slice's `context_files`, its `review_files`, and every packet's `target_files` and `context_files`. Labels are evaluated in order, and when several slices qualify, the greatest slice id in code-point order wins:

1. `pipeline-authored by <S>`: `head_sha256 = S.merged_sha256[path]`.
2. `parent-authored, pipeline-reviewed by <S>`: `head_sha256 = bootstrap_sha256` and `path ∈ S.reviewed_paths`.
3. `parent-authored, unreviewed`: `head_sha256 = bootstrap_sha256`.
4. `FOREIGN_EDIT`: anything else, including a path absent at `HEAD`.

Exit 65 if any slice fails verification or any line is `FOREIGN_EDIT`, else 0 (`P:717`).

### 13.9 `omarchy status [--markdown] [--tokens]`

`status` prints one line per `slice/*` branch: `<slice_id>\t<step line>\t<rows>\t<last outcome>\t<last time>`. `--markdown` renders the same columns as a markdown table, replacing `docs/SPRINT_DASHBOARD.md`. `--tokens` adds a per-seat table with the columns `seat`, `runtime`, `rows`, Σ`eval_count`, Σ`prompt_eval_count`, and Σ`total_duration_ns` / 1e9 s, built from local rows. Cloud seats get a row count, with tokens shown as `UNMEASURED`. This replaces `scripts/report_token_split.sh`, which always reports zero local work (`scripts/report_token_split.sh:48`).

### 13.10 `omarchy smoke`

For Family A, then Family B:

1. Open a `family_session`.
2. Send the smoke prompt (§10.8).
3. Parse the response as CODE with allowed path `smoke/hello.txt`.
4. Print one canonical JSON line with the keys `{"family", "model", "parse_ok", "failure", "done_reason", "eval_count", "prompt_eval_count", "total_duration_ns", "resident_bytes"}`.

`smoke` writes nothing to the repo. Exit 0 iff both families parse.

### 13.11 `omarchy lock [--check | --local-models | --check-pulled]`

- `--check` (the default) parses the lock and prints `LOCK_OK <lock_sha256>`.
- `--local-models` prints `<family> <model>` for each local seat.
- `--check-pulled` queries `/api/tags` and prints `PULLED <model> <bytes>` or `MISSING <model>` for each local model. It uses `match_model`, the same matcher as the budget guard, and exits 0 iff every model is pulled. This removes the disagreement between `scripts/ensure_local_agents.sh:41` (exact match) and `.omarchy/omarchy.py:573` (prefix match).

### 13.12 CLI surface

`__main__` builds an `argparse.ArgumentParser` subclass whose `error()` prints the usage line to stderr and exits 64 (argparse's default exit 2 would collide with the git-error code). It has one subparser per command of §13.1–§13.11, with exactly the arguments shown; `--paths` is comma-separated. stdout carries only the command's result lines (step lines, `REFUSE` lines, `OPENED`, `RECORDED`, `SEAT_FAILED`, `VERIFIED`, labels, status, prompt bytes, smoke JSON, lock lines). Everything else goes to stderr. `main` takes the repo from its `repo` argument, or else from the package location (§1). It takes the Ollama client from its `client` argument, or else builds `Client(OLLAMA_API_URL)`.

---

## 14. Worktrees, gates, and merge

### 14.1 Paths

| Worktree | Path | Branch | Base | Lifetime |
|---|---|---|---|---|
| slice | `.omarchy/worktrees/<id>/slice` | `slice/<id>` | `base_ref` | permanent |
| proposal | `.omarchy/worktrees/<id>/<pkt>.q<q>.<A\|B>` | `omarchy/<id>/<pkt>/q<q>/<A\|B>` | `B_q` | one job |
| synthesis | `.omarchy/worktrees/<id>/<pkt>.q<q>.SYNTH.r<r>` | `omarchy/<id>/<pkt>/q<q>/synth-r<r>` | slice head | one job |
| merge | `.omarchy/worktrees/<id>/merge` | `omarchy/<id>/merge` | slice head | one merge |
| QA eval | `.omarchy/worktrees/<id>/qa` | `omarchy/<id>/qa` | slice head | one evaluation |

`TempWorktree` runs `git worktree add -B <branch> <path> <base>`. On exit, after success or an exception, it does three things, salvaged from `.omarchy/omarchy.py:474-497`:

1. Run `git worktree remove --force <path>`.
2. Remove the directory if it remains.
3. Run `git branch -D <branch>`.

The kernel never touches `main` or the human's checkout (`P:125`).

### 14.2 Block writes

Each block is written to `<wt>/<path>` after `sterilize_path` against `<wt>`; a `ValueError` becomes `SeatFailure("PATH_NOT_ALLOWED")`. Parent directories are created, the mode is 0644, and the content is written exactly as parsed (§7.4). v2 appended a newline only when one was missing (`.omarchy/omarchy.py:713-714`).

### 14.3 Diff before gates

1. Run `git add -- <block paths>`.
2. The diff is `git diff --cached --binary --full-index --no-color --no-ext-diff --no-renames`.
3. `numstat_loc` comes from `git diff --cached --numstat --no-renames`.
4. `paths` and `diff_paths` are the sorted paths of `git diff --cached --name-only --no-renames`.

All of these are computed **before** gates run, so files the gates create never enter the diff. v2 hashed `git add -A` after gates (`.omarchy/omarchy.py:416-424`).

### 14.4 Gates

The command list is:

1. The packet's `verification_commands`.
2. In round 2 only, `python3 -m pytest -q -p no:cacheprovider <file>` for each red QA file of `E` mapped to the packet, in sorted order.
3. `test_command`.

Each command runs as an argv list (`.omarchy/omarchy.py:317-340`):

- cwd is the worktree root, and stdin is `/dev/null`.
- The environment is inherited, plus `PYTHONDONTWRITEBYTECODE=1`.
- The timeout is 1800 s, `UNMEASURED`.

**All** commands run, even after one fails. The log is bytes. For each command, it contains these pieces in order, each followed by LF:

1. `$ <shlex.join(argv)>`
2. `exit=<int|TIMEOUT>`
3. `--- stdout ---`
4. the raw stdout
5. `--- stderr ---`
6. the raw stderr

The log ends with `GATES: PASS` or `GATES: FAIL` and LF. The result is `PASS` iff every exit is 0. Stage-4 gates are recorded and never block (`P:239`).

### 14.5 Merge (stage 6 commit phase)

This is the two-phase commit. Prepare is SYNTH (gated and recorded), vote is REVIEW, and commit is this kernel job. The MERGE log is always written. Each of its lines below ends with LF.

1. Re-check that the slice worktree is clean, and note the head `H`.
2. Open `TempWorktree(merge, H)`. Require `sha256(SYNTH .diff) = diff_sha256`, else raise `OmarchyError`.
3. Apply the diff:
   - **Empty diff:** log `$ git apply (skipped: empty diff)` and `exit=0`.
   - **Otherwise:** run `apply_diff`, which is `git apply --index --binary --whitespace=nowarn -` fed from stdin. Log the command line, `exit=<int>`, `--- stderr ---`, and the stderr.
   - A `MergeConflict` adds `MERGE: FAIL APPLY_CONFLICT` and goes to step 7.
4. Log `numstat_loc=<n>` and `manifest_paths=<comma list or NONE>` for the applied index.
   - If `numstat_loc > 300`, log `MERGE: FAIL LOC_LIMIT` (ballot N11, `docs/GRAND_COUNCIL/v2.3.1_Test/LINUS_BALLOT.md:171-173`).
   - Else, if a manifest path is not covered by an `APPROVE_DEPENDENCY` ruling, log `MERGE: FAIL DEPENDENCY_CHANGE`. This failure is unreachable after §11.5 step 4.2 and is kept as defense in depth.

   Either failure goes to step 7.
5. Run gates per §14.4 and append their log. On `FAIL`, log `MERGE: FAIL GATES_FAIL` and go to step 7.
6. On pass, log `MERGE: PASS`. In the merge worktree, `kernel_commit` the MERGE log and a `MERGED` row (code and row in one commit). Then call `fast_forward(slice_wt, omarchy/<id>/merge, expected_head = H)`.
7. On failure, `kernel_commit` the MERGE log and a `MERGE_FAILED` row in the slice worktree. The code changes stay in the discarded merge worktree. A commit-phase failure is a failed round (§11.5).

### 14.6 Dependency manifests

`is_manifest(path)` is true iff the basename full-matches:

```text
pyproject\.toml|setup\.py|setup\.cfg|requirements[^/]*\.txt|Pipfile(?:\.lock)?|poetry\.lock|uv\.lock|package(?:-lock)?\.json|yarn\.lock|pnpm-lock\.yaml|Cargo\.(?:toml|lock)|go\.(?:mod|sum)|Gemfile(?:\.lock)?|build\.gradle(?:\.kts)?|settings\.gradle(?:\.kts)?|gradle\.properties
```

### 14.7 QA evaluation (kernel action)

In `TempWorktree(qa, head)`, run `test_command`, then `python3 -m pytest -q -p no:cacheprovider <file>` for every live file under `tests/qa/<id>/`, in sorted order. Execution rules and the log format are those of §14.4.

- `red_files` are the QA files whose command exited non-zero.
- `red_packets` are the sorted unique packets of the red files, taken from the `qa_files` of the record that added each file.
- `qa_result` is `GREEN` iff every exit is 0.

`kernel_commit` the EVAL log and the `QA_EVAL` row in the slice worktree. QA tests stay committed whether they pass or fail (`P:442`; §20 D15).

---

## 15. Ollama and MLX requirements

Constants live in `omarchy/ollama.py` and are part of `kernel_sha256`. They are not environment-overridable (§20 D16). The only environment value read is `OLLAMA_API_URL`, defaulting to `http://127.0.0.1:11434` (as `.omarchy/omarchy.py:37`), and only `__main__` reads it.

| Constant | Value |
|---|---|
| `MAX_FAMILY_BUDGET_BYTES` | `105 * 1024**3`, `UNMEASURED` |
| `BYTES_PER_CTX_TOKEN` | `512 * 1024`, `UNMEASURED` |
| `HEADROOM_BYTES` | `4 * 1024**3`, `UNMEASURED` |
| `GENERATE_TIMEOUT_S` | `3600`, `UNMEASURED` |
| `CONTROL_TIMEOUT_S` | `60` |
| `RESIDENCY_POLLS` | `10`, 1 s apart |
| `KEEP_ALIVE` | `"15m"` |

| ID | Requirement |
|---|---|
| K1 | The `/api/generate` payload is exactly `{"model", "prompt", "stream": false, "keep_alive": KEEP_ALIVE, "options": {"temperature": 0, "num_ctx": <cfg.num_ctx>}}`. It never contains `format`, which returns HTTP 501 on MLX (`.omarchy/omarchy.py:621-622`, commit `3b1f2c8`) |
| K2 | Outer-fence strip per §7.1 |
| K3 | File blocks per §7.4; trailer per §7.2 |
| K4 | `done_reason` MUST equal `"stop"`. Anything else, including a missing value or `"length"`, is `SEAT_FAILED DONE_REASON`, with no parse attempt |
| K5 | `family_session` enter: (1) take an exclusive non-blocking flock on `<repo>/.omarchy/locks/ollama.lock`; if it is busy, raise `OmarchyError`. (2) `GET /api/ps` and unload every resident model that is not the target. (3) Poll `/api/ps` `RESIDENCY_POLLS` times; if any non-target model remains, raise `ResidencyError(models)` (fail closed). (4) Run the budget check (K8). The model loads lazily on the first `generate`. After each `generate`, `GET /api/ps` and record the target entry's `size` as `resident_bytes`, or `null` if absent (`docs/GRAND_COUNCIL/v2.3.1_Test/LINUS_BALLOT.md:70-79`) |
| K6 | `KEEP_ALIVE` is sent only inside `family_session`. On exit, send `{"model", "prompt": "", "stream": false, "keep_alive": 0}` and poll as in K5; if the target remains, the eviction failed with `ResidencyError`. On exception exit, eviction errors are printed to stderr and the original exception is re-raised. On normal exit, an eviction error is raised. This fixes `.omarchy/batch_runner.py:73` masking the real error through `:313-317` |
| K7 | `run` sweep: unload every model listed by `/api/ps`, then poll as in K5. Any model that remains raises `ResidencyError` (this covers SIGKILL leftovers) |
| K8 | `match_model(entries, slug)` returns the entry whose `name` (or, if `name` is absent, `model`) equals `slug`, or, iff `slug` contains no `:`, equals `slug + ":latest"`. It never matches by prefix (`.omarchy/omarchy.py:573`). Budget: `weights + num_ctx × BYTES_PER_CTX_TOKEN + HEADROOM_BYTES ≤ MAX_FAMILY_BUDGET_BYTES`, where `weights` is the matched `/api/tags` entry's `size`. A missing entry raises `OmarchyError` (`.omarchy/omarchy.py:542-545`) |
| K9 | Temperature is 0, and determinism is not assumed. A per-call HTTP timeout of `GENERATE_TIMEOUT_S` gives `SEAT_FAILED TIMEOUT`. The second attempt of §11.4 is the one automatic retry; after it, the slice HALTs |
| K10 | `family_session` loads only `lock.family_seat(family).model`. Any other target, including a size variant of the lock model, raises `OmarchyError` (`.omarchy/omarchy.py:614-619`) |

Running both families in RAM at once is out of scope until `docs/EVIDENCE.md` shows both fit (`P:458`, `P:761`). `ollama.lock` serializes sessions per repo. Two repos on one host are not serialized; this is stated in §19.

---

## 16. Kernel pinning, slice branches, and source tags

- **Pinning.** The kernel that runs is the repo's working tree, pinned at `open` by `kernel_sha256` and `kernel_commit`. A slice that edits kernel files changes only `slice/<id>`. The new kernel takes effect after a human merges the slice and a new slice is opened (`P:616`). Recovering from `REFUSE KERNEL_CHANGED` means checking out the OPEN row's `kernel_commit`. Attempt 1 patched the kernel mid-run twice (`docs/GRAND_COUNCIL/v2.3.1_Test/FLOW_TRACE.md:36-38`).
- **Retention.** Branches `slice/*` and tags `omarchy/*` are proof and are never deleted. `parent` pushes `slice/<id>` before dispatching any cloud job, so the seat can check out `render_commit`, and pushes `refs/tags/omarchy/<id>/*` after each `record`.
- **Merge strategy.** The human may merge a DONE slice's PR with any GitHub merge strategy. `verify --repo` does not depend on the strategy (§13.8).

---

## 17. Bootstrap execution and repo surgery

### 17.1 Phase 2: kernel (parent, on `v3`)

Commit order:

- A test commit immediately precedes its module commit (tests first).
- Each commit changes ≤ 300 LOC under `omarchy/**`. A larger module lands across consecutive `feat` commits.
- Every commit carries the trailer `Omarchy-Bootstrap: parent`.
- Subjects are `test(s000): <file>` and `feat(s000): <module>`.
- `python3 -m pytest -q` is green at every `feat` commit, and at the final `test(s000): e2e` commit.

1. `tests/conftest.py` (§18.1), then `omarchy/__init__.py`
2. `tests/test_lock.py`, then `omarchy/lock.py`
3. `tests/test_slots.py` and `tests/test_slice_config.py`, then `omarchy/slice.py`
4. `tests/test_trailers.py`, then `omarchy/trailers.py`
5. `tests/test_proof.py`, then `omarchy/proof.py`
6. `tests/test_machine.py`, then `omarchy/machine.py`
7. `tests/test_worktree.py`, then `omarchy/worktree.py`, then `omarchy/view.py`
8. `tests/test_ollama.py`, then `omarchy/ollama.py`
9. `tests/test_runner.py`, then `omarchy/runner.py` and `omarchy/prompts/*.md`
10. `tests/test_report.py`, then `omarchy/report.py`
11. `tests/test_ingest.py`, then `omarchy/ingest.py`
12. `tests/test_cli.py`, then `omarchy/__main__.py` and `scripts/omarchy`
13. `tests/test_bootstrap_e2e.py` and `tests/test_pipeline_e2e.py` (subject `test(s000): e2e`)

### 17.2 Phase 3: surgery

Phase 3 is one atomic commit, `chore(s000): v3 repo surgery`, with the trailer `Omarchy-Bootstrap: parent`.

**Archive** (`git mv`; plan `P:220`):

| From | To |
|---|---|
| `docs/GRAND_COUNCIL/v2.3.1_Test/{FLOW_TRACE,LINUS_AUDIT_PLAN,LINUS_BALLOT,MOXIE_G4_TEST,MOXIE_G5_REVIEW,QWENY_AUDIT_WORKSHEET,SCRUM_DOD_AUDIT}.md` | `archive/v2.3.1-attempt1/council/<same name>` |
| `.omarchy/packets/aud231-{s01-build,s09-g4,s10-g5,s11-dod}.json` | `archive/v2.3.1-attempt1/packets/<same name>` |
| `.omarchy/contracts/stories/STORY-AUDIT-V231.md`, `.omarchy/contracts/use_cases/UC-AUDIT-V231-{WS,G4,G5,DOD}.md` | `archive/v2.3.1-attempt1/contracts/<same name>` |

**Delete.** These files stay reachable at tag `v2.3.1-attempt1` = `1156b29`.

- `.cursor/agents/{qweny,moxie,scrum,mitnick,jobs}.md`
- `.omarchy/omarchy.py`, `.omarchy/batch_runner.py`, `.omarchy/README.md`, `.omarchy/packets/{README.md,_sample_packet.json,pkt-01-impl.json,pkt-02-audit.json,pkt-03-optimize.json}`
- `.omarchy/contracts/stories/{STORY-101,STORY-BATCH}.md`, `.omarchy/contracts/use_cases/{UC-101-A,UC-101-B,UC-BATCH-A,UC-BATCH-B}.md`
- `02_PRODUCTION_PLAN.md`
- `docs/{DEVELOPER_GUIDE,SPRINT_DASHBOARD,PRODUCT_SPEC,OMARCHY_SCRUM_2_0_BLUEPRINT,TESTING_JIG_REPORT,GRAND_COUNCIL}.md`
- `packets/README.md`
- `scripts/{run_local_agent.sh,log_cloud_agent.sh,report_token_split.sh,omarchy.py}`
- `tests/test_omarchy_kernel.py`

**Rewrite or create:**

- `agents.lock` and `agents.lock.optional` per §3.3.
- `.gitignore`, exactly these lines in order: `.omarchy/worktrees/`, `.omarchy/locks/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.venv/`, `.DS_Store`, `build/`, `.gradle/`, `local.properties`.
- `AGENTS.md`, in three sections:
  - §1 is the stage hemisphere matrix (`P:248-257`).
  - §2 is the seat table between `<!-- seat-table:canonical -->` and `<!-- /seat-table:canonical -->`. Its columns are `Seat | Group | Runtime | Family | Caps | Weight`, with plain cell values and no model column (§20 D18).
  - §3 is the command glossary of §13, including the §16 retention rule.
- `01_OMARCHY_AGENT_PROMPTS.md`:
  - the 12 v3 laws (`P:551-564`);
  - the stage table of §11.7 between `<!-- stage-table -->` and `<!-- /stage-table -->`, with columns `Stage | Slot | Author cap | Runtime` and each Slot, Author cap, and Runtime cell wrapped in one pair of backticks;
  - the trailer grammar of §7.
- `00_ARCHITECTURE.md`:
  - first line `Source: slices/s000-bootstrap/<approved plan slot> sha256=<output_sha256>`;
  - one blank line;
  - the approved plan's bytes from its first line up to, but excluding, the line that starts with `## 21.`
- `slices/s000-bootstrap/<every recorded s000 cloud slot>`: brought onto `v3` with `git checkout <seat commit> -- <path>`, so T-D4 can check the copy.
- `.cursor/rules/omarchy-council.mdc`, saying four things:
  - run `omarchy next` first;
  - the stage hemisphere matrix;
  - no hand edits under `slices/`;
  - cloud seats write only plan, challenge, packet, and QA slots, plus `tests/qa/<id>/` files.
- `.cursor/agents/{linus,knuth,dhh,carmack}.md`: the hemisphere line, the owned slots, and a pointer saying the kernel template owns the trailer grammar. No model slugs.
- `README.md`: the entry point plus a quickstart.
- `scripts/ensure_local_agents.sh`: keep the start-or-wait loop (`scripts/ensure_local_agents.sh:16-27`), then `exec "$ROOT/scripts/omarchy" lock --check-pulled`.
- `tests/test_docs_sync.py`.
- `archive/v2.3.1-attempt1/README.md`: the four interventions, with commits `3b1f2c8`, `2e7414e`, `ececfcc`, and `3aa8c8f`, and the packet collapse (`docs/GRAND_COUNCIL/v2.3.1_Test/FLOW_TRACE.md:41-43`).
- `docs/EVIDENCE.md`: append `UNMEASURED` rows for the six constants of §15 marked `UNMEASURED`, for chars / 3.5, for the 1.3 reserve factor, and for the 1800 s gate timeout.
- `docs/HISTORY.md`: append the rows `v2.3.1 attempt 1 archived` and `BOOTSTRAP_EXCEPTION` (`P:715`).
- `slices/s000-bootstrap/BOOTSTRAP.json` (§8) and `slices/s000-bootstrap/BOOTSTRAP.<slot>.prompt` for every s000 cloud dispatch. These are slice records, not plan files, so they are absent from `PLAN_FILES` under §7.3's grammar.

`PLAN_FILES` lists every path that exists after Phase 3 with new content or a new location. Deleted paths appear only in the Delete list above. `python3 -m pytest -q` is green after this commit.

### 17.3 Phase 4: smoke and ingest (parent, then human)

1. Run `scripts/ensure_local_agents.sh`, then `scripts/omarchy smoke`. Append measured rows to `docs/EVIDENCE.md` (date, commit, model, `resident_bytes`, `parse_ok`, durations) and commit them.
2. Run `scripts/omarchy open s000-bootstrap --bootstrap`. The branch is created from `base_ref` `v2.3.1-attempt1` (`slices/s000-bootstrap/slice.json:5`), which lacks `slices/s000-bootstrap/`; the OPEN commit adds it.
3. For each s000 cloud slot in order, run `scripts/omarchy record s000-bootstrap --slot <S> --seat <seat> --ref <seat commit> --cloud-run <run id>`. `<seat commit>` is the commit the seat reported: `90e4780` for `01_PLAN.r1.md`, `d2e5005` for `02_CHALLENGE.r1.md`, and the reported commits for `01_PLAN.r2.md` and `02_CHALLENGE.r2.md`. A branch tip that also contains a later slot fails B1 with `PATH_NOT_ALLOWED` (T-E3). Phase 1 dispatch requirements:
   - Each challenger's commit MUST contain the exact plan revision it challenged.
   - `parent` MUST keep the exact dispatched prompt bytes for every s000 cloud slot. Without them, `BOOTSTRAP.<slot>.prompt` cannot match the echoed sha, and `record` fails `PROMPT_SHA_MISMATCH`.
   - If `02_CHALLENGE.r2.md` is `REQUEST_CHANGES`, the human enters `APPROVE_OVERRIDE` or `ABORT` with `omarchy rule` (`P:22`).
4. `scripts/omarchy next s000-bootstrap` prints `DONE_BOOTSTRAP`, and `scripts/omarchy verify --repo` labels every BOOTSTRAP file `parent-authored, unreviewed`. `parent` pushes `slice/s000-bootstrap` and `refs/tags/omarchy/s000-bootstrap/*`. That branch is never merged.

---

## 18. Required tests

All tests run without Ollama and without network access. Git tests use `tmp_path` repositories, and Ollama tests use the mock server of §18.1. Fixture locks use fake slugs, such as `fam-a:27b-x`, `fam-b:31b-x`, `cloud-p-1`, and `cloud-q-1`. IDs are stable. "Adapted" marks a test reworded from `P:620-707` or from `tests/test_omarchy_kernel.py`.

### 18.1 Fixtures (`tests/conftest.py`)

| Fixture | Contract |
|---|---|
| `fixture_lock_text` | A schema-3 lock with seats `linus` (cloud, family `cloud_p`, `plan`), `knuth` (cloud, `cloud_q`, `challenge,qa`), `qweny` (Family A, `challenge,propose,critique,synthesize`), `moxie` (Family B, `propose,critique,review`), and `parent` (host), all with fake slugs |
| `kernel_repo` | A `tmp_path` git repo with: `.gitignore` per §17.2; a copy of the real `omarchy/` package without `__pycache__`; `agents.lock` = `fixture_lock_text`; and one commit on branch `main`. It returns the repo path |
| `mock_ollama` | An HTTP server on `127.0.0.1:0` implementing `/api/tags`, `/api/ps`, and `/api/generate`. It takes a mapping slot → response text, and finds the slot in a prompt with `re.search(r"slot (\S+), seat", prompt)`; no match uses the `default` entry. It records every request in order and tracks residency: a model becomes resident on its first `generate` and leaves on `keep_alive: 0`. Knobs inject a `done_reason`, a delay, HTTP errors, and models that refuse to unload. It returns `(Client, recorder)` |
| `History` | A builder over `SliceView` for machine tests. It starts from an OPEN row and offers `record(slot, **parsed)`, `fail(slot, failure)`, `overflow(slot)`, `merge(slot, outcome, failure=None)`, `qa_eval(red_files, red_packets)`, and `rule(ruling, paths=())`. Each method asserts that its slot (or the HALT) is in `derive(view, len(rows))`, builds the row with roster seat fields and the job's `render_commit` and `attempt`, assigns the synthetic commit id `f"{seq:040x}"`, and returns the new view. `forge(row)` appends an arbitrary row for negative tests |
| `cloud_commit` | `(repo, parent_commit, files: dict[str, bytes]) -> str`: creates a commit with those files on top of `parent_commit`, on a throwaway branch, and returns its id |

### 18.2 Test list

| ID | File | Asserts |
|---|---|---|
| T-L1 | `test_lock.py` | `schema` ≠ 3, or the schema line is not the first non-comment line → `ILLEGAL_LOCK` |
| T-L2 | | A row with 6 or 8 fields → error, never skipped |
| T-L3 | | Duplicate seat id → error |
| T-L4 | | Two seats in one local family → error |
| T-L5 | | Family A model equals Family B model → error |
| T-L6 | | Two cloud seats share a family → error |
| T-L7 | | Zero or two `plan` seats; a local planner → error |
| T-L8 | | `synthesize` on B, or `review` on A → error |
| T-L9 | | `qa` on the planner; `challenge` on Family B; `challenge` on a cloud seat with the planner's family → error |
| T-L10 | | The repo `agents.lock` satisfies every invariant, with no literal slugs and no exact seat-set assertion |
| T-L11 | | `local_models(lock)` equals the two local MODEL fields; `family_seat` returns the unique seat per family |
| T-L12 | | Seat `human` or `kernel` in the lock; a field with surrounding whitespace; an unknown cap; a host seat other than `parent`; a GROUP/RUNTIME mismatch → error |
| T-L13 | | For each non-comment row after `schema=3` in the repo `agents.lock.optional`, `parse_lock(<repo agents.lock text> + row + "\n")` succeeds. The optional file alone is never parsed against the invariants |
| T-S1 | `test_slots.py` | Every accepted vector of §5.2 parses with exactly the listed kind, ext, stage, and fields |
| T-S2 | | Every rejected vector of §5.2 raises `ValueError` |
| T-S3 | | Each §5.4 example parses to the listed kind, stage, and `slot_class`, and every kind of §5.2 has at least one accepted vector |
| T-S4 | | No accepted vector full-matches more than one kind regex |
| T-S5 | | For every authored vector and `k = 1..4`, `rejected_name(s, k)` parses as REJECTED with `target = s` and `attempt = k`; `k = 5` raises. `companion` maps `.md` to `.diff` and `.gates.log` for PROPOSAL and SYNTH only |
| T-S6 | | The `qa_file_ok` vectors of §5.3 |
| T-C1 | `test_slice_config.py` | A cloud challenger with a family different from the planner's → legal |
| T-C2 | | A Family A challenger → legal |
| T-C3 | | A Family B challenger → `ILLEGAL_CONFIG` |
| T-C4 | | The challenger is the planner → `ILLEGAL_CONFIG` |
| T-C5 | | Empty `qa_seats`; the planner as a QA seat; a local QA seat → `ILLEGAL_CONFIG` |
| T-C6 | | An unknown key, a duplicate key, `true` as an int, or `NaN` in `slice.json` → rejected |
| T-C7 | | A `context_files` path with `..` → `ILLEGAL_CONFIG`. A symlink blob at `base_ref` → `ILLEGAL_CONFIG` at `open`. `sterilize_path` through a symlink that escapes → `ValueError` whose message starts `SECURITY VIOLATION` (adapted v2 traversal test) |
| T-C8 | | `review_files` absent → `()`. A context or review path absent at `base_ref` → `ILLEGAL_CONFIG` |
| T-C9 | | `slice_id` ≠ directory name, or failing `SLICE_ID`; a `test_command` with argv[0] `bash` → rejected |
| T-C10 | | `slices/s000-bootstrap/slice.json` parses (repo fixture) |
| T-T1 | `test_trailers.py` | A review slot missing `OMARCHY_VERDICT` → `TRAILER_INVALID` |
| T-T2 | | A duplicate key; an extra key; a CR byte; `KEY:value` without a space → refused |
| T-T3 | | `APPROVE` with `BLOCKING_COUNT: 2`; `REQUEST_CHANGES` or `REJECT` with 0 → refused |
| T-T4 | | `OMARCHY_STATUS: COMPLETE`; `APPROVE_WITH_FIXES` → refused |
| T-T5 | | A whole response in a json fence parses with `cloud=False`; inner fences in file content are preserved; a two-level fence loses one level only; with `cloud=True` no fence is stripped |
| T-T6 | | A file block outside `target_files` → `PATH_NOT_ALLOWED` |
| T-T7 | | A file-block path with a `..` segment or an absolute path → `FILE_BLOCK_INVALID` |
| T-T8 | | For each class, the key lines of `output_contract` name exactly the §7.3 key set. The PACKETS contract contains `plan_sha256` and `max_packets` literally. `output_contract(RULING)` raises |
| T-T9 | | `READY` proposal with zero file blocks; `NEEDS_PLAN` with blocks → refused |
| T-T10 | | A plan without `PLAN_FILES`; `READY` with `PLAN_FILES: NONE`; a path under `slices/` or `tests/qa/` → refused |
| T-T11 | | Trailing blank lines after the closing `---` are accepted, and body `---` lines are ignored |
| T-T12 | | `QA_TESTS` grammar: a missing ` -> `, a bad PKT_ID, or a duplicate path → `TRAILER_INVALID` |
| T-T13 | | `render_ruling` output parses back to the same fields under the RULING class |
| T-T14 | | Unterminated block; duplicate block path; non-UTF-8 content → `FILE_BLOCK_INVALID`. Content bytes end with exactly one LF per line |
| T-T15 | | `READY` with `MISSING_SYMBOLS` ≠ `NONE`; `TOUCHED_FILES` ≠ the block paths → refused |
| T-T16 | | `parse_slot(PACKETS, …)` raises `ValueError`. A cloud slot with a well-formed but wrong `OMARCHY_PROMPT_SHA256` parses, because the comparison is ingest's (§7.5) |
| T-P1 | `test_proof.py` | Append and verify a chain |
| T-P2 | | A slot file edited after record → `REFUSE SLOT_SHA_MISMATCH` |
| T-P3 | | A middle row edited or deleted → `REFUSE CHAIN_BROKEN` |
| T-P4 | | Running kernel sha differs from `OPEN` on a non-terminal slice → `REFUSE KERNEL_CHANGED` |
| T-P5 | | Running lock sha differs on a non-terminal slice → `REFUSE LOCK_CHANGED` |
| T-P6 | | Two concurrent appenders under flock → the chain stays valid |
| T-P7 | | A hand commit on `slice/<id>` without trailers → `REFUSE FOREIGN_COMMIT` |
| T-P8 | | Commit count ≠ row count; a two-parent commit; a change outside `allowed_changes`; a trailer seq mismatch → `FOREIGN_COMMIT` |
| T-P9 | | A non-canonical line (whitespace, unsorted keys, a missing field, a float) → `CHAIN_BROKEN` |
| T-P10 | | `kernel_sha256` is deterministic, ignores `__pycache__` and `*.pyc`, and changes when a prompt template changes |
| T-P11 | | `required_files` per §5.5 (B02). (a) A `SEAT_FAILED TIMEOUT` row without a file passes integrity, and `next` yields `a2`. (b) A `SEAT_FAILED TRAILER_INVALID` row requires its `.rejected` file; deleting it → `SLOT_SHA_MISMATCH`. (c) A `CONTEXT_OVERFLOW` row without a file → `HALT CONTEXT_OVERFLOW`. (d) `MERGE_FAILED APPLY_CONFLICT` requires only its MERGE log. (e) A CODE `NEEDS_PLAN` row requires no companions, and a stray `.diff` → `UNKNOWN_SLOT_FILE` |
| T-P12 | | A dismissed QA file that is absent passes; a dismissed QA file that is present → `UNKNOWN_SLOT_FILE` |
| T-M1 | `test_machine.py` | Fresh open → `NEXT CLOUD linus 01_PLAN.r1.md a1`, with the planner id from the fixture lock |
| T-M2 | | A plan recorded by a non-planner seat → `REFUSE WRONG_SEAT_FOR_SLOT` |
| T-M3 | | Plan `NEEDS_PLAN` → `HALT PLAN_NEEDS_INPUT` |
| T-M4 | | A challenge by a seat other than the configured challenger → `REFUSE WRONG_SEAT_FOR_SLOT` |
| T-M5 | | `REQUEST_CHANGES` at r1 → plan r2; `REQUEST_CHANGES` at r2 → `HALT PLAN_DEADLOCK` |
| T-M6 | | `REJECT` at r1 → `HALT PLAN_REJECTED` |
| T-M7 | | Cloud challenger → `NEXT CLOUD`; Family A challenger → `NEXT LOCAL` (both legal) |
| T-M8 | | `plan_sha256` ≠ the approved revision → `PACKETS_INVALID` |
| T-M9 | | Overlapping targets; a target outside `PLAN_FILES`; 6 targets; more packets than `max_packets`; non-contiguous ids → `PACKETS_INVALID` |
| T-M10 | | A stage-4 proposal row from a cloud seat → `REFUSE WRONG_SEAT_FOR_SLOT` |
| T-M11 | | Only A proposals present → `NEXT LOCAL` lists the B proposals, not stage 5 |
| T-M12 | | Proposal `NEEDS_PLAN` → `HALT PROPOSAL_NEEDS_PLAN` |
| T-M13 | | `A_ON_B` authored by Family B → `REFUSE SAME_FAMILY_CRITIQUE` |
| T-M14 | | `SYNTH` authored by B → `WRONG_SEAT_FOR_SLOT`; `REVIEW` authored by A → `SAME_FAMILY_CRITIQUE` |
| T-M15 | | Gates FAIL with `APPROVE` → no merge job, `SYNTH.r2` next; r2 gates FAIL → `HALT TESTS_RED` (adapted) |
| T-M16 | | Gates PASS with `REQUEST_CHANGES` at r1, then `APPROVE` at r2 → `NEXT KERNEL merge 06_pkt-01.q1.MERGE.r2.gates.log a1` (adapted) |
| T-M17 | | All packets merged → `NEXT CLOUD <qa_seat>` for each QA seat, with `render_commit = D_1` |
| T-M18 | | A QA row whose `qa_files` path is outside `tests/qa/<id>/` → refused |
| T-M19 | | QA red mapped to `pkt-02` → q2 proposals for `pkt-02` only; q2 red → `HALT QA_RED` |
| T-M20 | | QA green → `DONE` |
| T-M21 | | `SEAT_FAILED` at attempt 1 → the same job at `a2`; at attempt 2 → `HALT SEAT_FAILED` |
| T-M22 | | A `CONTEXT_OVERFLOW` row → `HALT CONTEXT_OVERFLOW` |
| T-M23 | | `legal_rulings` equals §12 for every HALT code, including the two history conditions. `ABORT` is legal at every HALT but `ABORTED` (adapted) |
| T-M24 | | A stage-5 row before both stage-4 rows → `REFUSE OUT_OF_ORDER` |
| T-M25 | | The same slot recorded twice → `REFUSE DUPLICATE_SLOT` |
| T-M26 | | SYNTH with `manifest_paths: ["pyproject.toml"]` → `HALT DEPENDENCY_CHANGE` before any REVIEW job; numstat 301 → failed round (adapted) |
| T-M27 | | `next_step` is pure: identical inputs give identical output, with exactly one category. `machine.py` source contains none of the IO names of §2.2 |
| T-M28 | | A KERNEL job pre-empts LOCAL jobs; one packet's HALT dominates other packets' jobs |
| T-M29 | | A DONE slice with a changed running kernel and lock → still `DONE`, not REFUSE |
| T-M30 | | Bootstrap slice: an approved plan → `DONE_BOOTSTRAP`; `03_PACKETS.json` is never offered |
| T-M31 | | An `APPROVE_DEPENDENCY` ruling → the REVIEW job is next |
| T-M32 | | r2 classes: gates FAIL → `TESTS_RED`; gates PASS with numstat 301 → `MERGE_BLOCKED`; only `REQUEST_CHANGES` → `SYNTH_DEADLOCK`; an override → merge job; merge `GATES_FAIL` after an override → `TESTS_RED` |
| T-M33 | | `ABORT` → `HALT ABORTED`; no legal rulings afterwards |
| T-M34 | | `DISMISS_QA_TEST` → `NEXT KERNEL qa_eval … EVAL.2.gates.log` for the same q. RED with empty `red_packets` at q1 → `HALT QA_RED`, where `legal_rulings` = `{ABORT}` |
| T-M35 | | A packet's `context_files` containing a sibling's target → `PACKETS_INVALID` |
| T-M36 | | A row whose family or model differs from the OPEN roster → `WRONG_SEAT_FOR_SLOT` |
| T-M37 | | `RETRY` raises the budget to 4. A second `RETRY` on the same slot → `OUT_OF_ORDER` at replay and `ILLEGAL_RULING` at `rule` |
| T-M38 | | (B01) A complete `History` from open: plan, approve, 2 packets, both packets through MERGED, a QA record mapping one file to `pkt-02`, and `qa_eval` RED with `red_packets = ["pkt-02"]`. Asserts `next` is `NEXT LOCAL` with exactly `04_pkt-02.q2.A.md` and `04_pkt-02.q2.B.md`, `render_commit` = commit of the QA_EVAL row, and attempt `a1`. Continuing q2 to MERGED gives `NEXT CLOUD knuth 07_QA.q2.knuth.md` with `render_commit = D_2`; a GREEN q2 eval gives `DONE` |
| T-M39 | | (B08) While `next` is `NEXT KERNEL merge`, a forged LOCAL row for a still-listed sibling job → `OUT_OF_ORDER`. A row whose `render_commit` differs from its job's → `OUT_OF_ORDER` |
| T-M40 | | (N02) Stage-5 verdicts `APPROVE`/`APPROVE`, `REQUEST_CHANGES`/`REJECT`, and `REJECT`/`REJECT` all give the identical next step (`SYNTH.r1`) |
| T-M41 | | (B07) Two QA seats, each adding 10 red files at q2. Twelve single-file `DISMISS_QA_TEST` rulings in sequence produce `HALT.12.HUMAN.md` and `07_QA.q2.EVAL.13.gates.log`, and both are accepted by integrity. When the latest eval is RED with no live red file, `legal_rulings` = `{ABORT}` |
| T-W1 | `test_worktree.py` | The proposal worktree and branch are removed on success and on exception |
| T-W2 | | The slice head is unchanged after stage 4 |
| T-W3 | | Merge applies the recorded `.diff`, re-gates, and fast-forwards. A failed merge leaves the head at the `MERGE_FAILED` commit with no code change (adapted) |
| T-W4 | | A dirty slice worktree → `DIRTY_WORKTREE` before any model call |
| T-W5 | | A merge after a sibling packet merged applies cleanly; a diff whose context no longer matches → `APPLY_CONFLICT` |
| T-W6 | | Files created by gates are absent from `.diff` |
| T-W7 | | All gate commands run after a failure; the log format is exact; a timeout → `exit=TIMEOUT`, `FAIL` |
| T-W8 | | (B10) `apply_diff` on a non-applying diff raises `MergeConflict` with git's stderr. The merge job turns it into `MERGE_FAILED APPLY_CONFLICT` with a MERGE log ending `MERGE: FAIL APPLY_CONFLICT`; no `SEAT_FAILED` row is written and no attempt changes |
| T-W9 | | An empty SYNTH diff merges with only the MERGE log and the row changed |
| T-W10 | | `kernel_commit` refuses (`OmarchyError`) when the staged change set differs from `allowed_changes` |
| T-O1 | `test_ollama.py` | The generate payload has exactly the K1 keys and never `format` |
| T-O2 | | `/api/ps` shows the other family resident → unload and re-poll; still resident → `ResidencyError` |
| T-O3 | | Entry `fam-a` does not satisfy slug `fam-a:27b-x`; entry `foo:latest` satisfies slug `foo`; entry `foo:latest` never satisfies slug `foo:latest:x` (adapted) |
| T-O4 | | The job raises and eviction raises → the original exception surfaces, with the eviction error on stderr |
| T-O5 | | A normal session → exactly one unload at exit, verified through `/api/ps` |
| T-O6 | | A model not in the lock, or a size variant of the lock model (`fam-a:14b-x` for `fam-a:27b-x`) → `OmarchyError` (adapted `tests/test_omarchy_kernel.py:103-124`) |
| T-O7 | | `done_reason: "length"` → `SEAT_FAILED DONE_REASON`, with stats copied into the row |
| T-O8 | | Connection refused → `OmarchyError`, and no row is written |
| T-O9 | | A missing `done_reason` → `DONE_REASON` |
| T-O10 | | Budget over the ceiling → refused before any load; a held `ollama.lock` → refused |
| T-O11 | | (B10) `ResidencyError.models` lists the names still resident. `run` exits 1, writes no row, and leaves the attempt number of the pending job unchanged |
| T-R1 | `test_runner.py` | Prompt build is byte-deterministic, with context rendered with line numbers per §10.4 |
| T-R2 | | `run` with a CLOUD first step → exit 66, nothing written |
| T-R3 | | Jobs are grouped by family, Family A first, with one session per family block |
| T-R4 | | The stage-5 critique prompt excludes the other critique |
| T-R5 | | The CODE reserve includes target size; overflow → a `CONTEXT_OVERFLOW` row and no generate call |
| T-R6 | | Local per-packet lineage excludes superseded plan revisions and `.diff` files; q2 includes `07_QA.q1.*`, `E`'s slot, and the mapped red QA files |
| T-R7 | | (B05) With two QA seats, the prompt for the second seat is byte-identical before and after the first seat's record, which adds files under `tests/qa/<id>/` and a proof row |
| T-R8 | | Inside a session, a newly runnable KERNEL job runs, and the session continues with newly runnable same-family jobs |
| T-R9 | | (B04) `lineage(...).slots` equals the exact §10.2 sequences for `01_PLAN.r1`, `02_CHALLENGE.r1`, `01_PLAN.r2`, `02_CHALLENGE.r2`, and `03_PACKETS.json` (both with and without a `PLAN_DEADLOCK` override), with no duplicates |
| T-R10 | | The `04_p.q1.B.md` prompt is byte-identical whether or not `04_p.q1.A.md` is recorded; `A_ON_B` lineage contains both proposals and not `B_ON_A` |
| T-R11 | | The cloud read list starts with `commit: <render_commit>` and carries a sha256 for each SLOT and REPO line, with `ABSENT` for a missing repo file |
| T-V1 | `test_report.py` | `verify` regenerates prompt shas; a template edit on a non-terminal slice → `KERNEL_CHANGED`; a forged `prompt_sha256` → `PROMPT_SHA_MISMATCH` |
| T-V2 | | `verify --repo` produces each of the four labels |
| T-V3 | | `status --tokens` sums `eval_count` per seat from rows |
| T-V4 | | (B09) `coverage_label` cases: pipeline-authored beats reviewed; the greatest slice id wins; a HEAD blob equal to neither the BOOTSTRAP sha nor a merged sha → `FOREIGN_EDIT`; absent at HEAD → `FOREIGN_EDIT` |
| T-I1 | `test_ingest.py` | A cloud ref changing a file outside the allow-list that differs from the merge base → `SEAT_FAILED PATH_NOT_ALLOWED` |
| T-I2 | | `--seat` ≠ the expected seat → `WRONG_SEAT_FOR_SLOT`, no row |
| T-I3 | | Recording a local job's slot → `NOT_CLOUD_JOB`, no row |
| T-I4 | | A missing or malformed `--cloud-run` → `MISSING_RUN_ID`. A kernel-prompt ref not descending from `render_commit` → `LINEAGE_MISMATCH`, no row (adapted) |
| T-I5 | | Two QA seats from the same dispatch commit: the second record succeeds after the first moved the head |
| T-I6 | | Bootstrap slot: a trailer sha equal to the `BOOTSTRAP.<slot>.prompt` sha → recorded with `prompt_source = bootstrap`; a mismatch → `SEAT_FAILED PROMPT_SHA_MISMATCH` |
| T-I7 | | A QA ref modifying an existing `tests/qa/<id>/` file → `PATH_NOT_ALLOWED` |
| T-I8 | | `open`: `ALREADY_OPEN`, `KERNEL_DIRTY`, `SLICE_DIR_INVALID` (including an uncommitted input), `BOOTSTRAP_MISMATCH` |
| T-I9 | | `rule` with no TTY → `NO_TTY`; a ruling illegal for the HALT → `ILLEGAL_RULING`; a wrong confirmation → `ILLEGAL_RULING` |
| T-I10 | | A `SEAT_FAILED` record stores `<slot>.a<k>.rejected` with the row's `output_sha256` |
| T-I11 | | (B06) A QA ref descending from `D_q` that reverts a merged target to its pre-merge bytes → `SEAT_FAILED PATH_NOT_ALLOWED`. A QA ref built on a pre-merge commit that carries exact copies of every lineage slot → `LINEAGE_MISMATCH`, no row |
| T-I12 | | `check_inputs` returns exactly the stale, missing, and unexpectedly present paths for a hand-built commit |
| T-I13 | | (B03) `03_PACKETS.json` with the correct `prompt_sha256` → RECORDED with the packets parsed. A wrong `prompt_sha256` → `SEAT_FAILED PROMPT_SHA_MISMATCH` with a `.rejected` file. Invalid packets → `PACKETS_INVALID` |
| T-I14 | | `record` creates tag `omarchy/<id>/source-<seq>` at `source_commit`; a QA record adding 11 files → `QA_MAP_INVALID` |
| T-X1 | `test_cli.py` | (N03) `main(["next", id], repo=…)` on NEXT, HALT, DONE, and REFUSE states returns 0, 3, 4, and 65, with exactly the §11.6 lines on stdout; REFUSE detail goes to stderr only |
| T-X2 | | An unknown subcommand or a missing argument → 64, empty stdout, usage on stderr |
| T-X3 | | `run` with a CLOUD step → 66, with the NEXT line on stdout |
| T-X4 | | A client pointing at a closed port during `run` → 1, `[OMARCHY][FATAL]` on stderr, no row |
| T-X5 | | `next` with `repo` set to a non-git directory → 2, `[OMARCHY][GIT-ERROR]` on stderr |
| T-X6 | | `prompt` prints the prompt bytes plus a final `OMARCHY_PROMPT_SHA256 value: <hex>` line, and the hex equals sha256 of the preceding bytes |
| T-E1 | `test_bootstrap_e2e.py` | (B12) Build the §17.3 topology in `kernel_repo`. (1) Commit `X` is tagged (annotated) `v2.3.1-attempt1`. (2) Branch `v3` commit `Y` adds `slices/s000-bootstrap/{slice.json,00_PROMPT.md}`. (3) `cloud_commit` chain `P1` (plan r1 READY) → `C1` (challenge r1 REQUEST_CHANGES) → `P2` (plan r2) → `C2` (challenge r2 APPROVE), each echoing its bootstrap prompt sha. (4) `v3` commit `Z` adds `BOOTSTRAP.json` (listing every kernel file and `agents.lock` at `HEAD`) and the four `BOOTSTRAP.*.prompt` files. Then `open --bootstrap` and four `record` calls with refs `P1`, `C1`, `P2`, `C2`. Asserts: `next` = `DONE_BOOTSTRAP`; 5 rows with outcomes `OPEN, RECORDED×4`, each `prompt_source = bootstrap`; every commit has one parent and the five trailers; `source_commit` values equal the four refs, with source tags present; `verify` = 0; `verify --repo` labels every BOOTSTRAP file `parent-authored, unreviewed` |
| T-E2 | | As T-E1, but `C2` is REQUEST_CHANGES → `HALT PLAN_DEADLOCK`. Then `rule APPROVE_OVERRIDE` with a stub confirm → `DONE_BOOTSTRAP`; `HALT.1.HUMAN.md` parses as RULING |
| T-E3 | | Negatives, each leaving the row count unchanged unless noted: a challenger commit without `01_PLAN.r1.md` → `LINEAGE_MISMATCH`; a challenger commit with different `01_PLAN.r1.md` bytes → `LINEAGE_MISMATCH`; recording `01_PLAN.r1.md` from `C1` (which also adds `02_CHALLENGE.r1.md`) → `SEAT_FAILED PATH_NOT_ALLOWED` (one row); a trailer sha ≠ `prompts[slot]` → `SEAT_FAILED PROMPT_SHA_MISMATCH` (one row) |
| T-E4 | | Forged source: reset `slice/s000-bootstrap` to before the last record, then append through `kernel_commit` a RECORDED row for `02_CHALLENGE.r2.md` whose `source_commit` is `P2`, which lacks that slot. `next` = `DONE_BOOTSTRAP`, and `verify` = 65 with `SOURCE_MISMATCH 02_CHALLENGE.r2.md` |
| T-E5 | `test_pipeline_e2e.py` | Slice `s900-e2e` with one packet, cloud slots made by `cloud_commit` from each `render_commit`, and local slots from `mock_ollama`. `run` and `record` reach `DONE` through every stage. The mock's generate sequence has exactly 4 maximal same-model runs (`P:458`). `verify` = 0 |
| T-E6 | | (B09) From the T-E5 end state, with a `BOOTSTRAP.json` on `main` listing the packet's target, one of its context files, and one unrelated file. For each of merge commit, squash, rebase, and fast-forward integration of `slice/s900-e2e` into a copy of `main`: `verify --repo` prints `pipeline-authored by s900-e2e`, `parent-authored, pipeline-reviewed by s900-e2e`, and `parent-authored, unreviewed` respectively. A later hand edit of the target → `FOREIGN_EDIT`, exit 65 |
| T-D1 | `test_docs_sync.py` | The `AGENTS.md` seat table equals the `agents.lock` rows on Seat, Group, Runtime, Family, Caps, and Weight (adapted) |
| T-D2 | | Let `M` be the MODEL fields of every `cloud` or `local` row in `agents.lock` and `agents.lock.optional`. No tracked file outside `agents.lock`, `agents.lock.optional`, `archive/**`, `slices/**`, `docs/EVIDENCE.md`, and `docs/HISTORY.md` contains any member of `M` as a byte substring (adapted) |
| T-D3 | | The stage table in `01_OMARCHY_AGENT_PROMPTS.md`, with one pair of surrounding backticks stripped from each cell, equals `machine.STAGES` |
| T-D4 | | The first line of `00_ARCHITECTURE.md` names a slot whose file exists in `slices/s000-bootstrap/` with that sha256, and the rest of the file equals that slot's bytes up to the `## 21.` line |

---

## 19. Measurements and stated limits (all `UNMEASURED` until rows land in `docs/EVIDENCE.md`)

| Item | How it gets measured |
|---|---|
| File-block parse success per family | `omarchy smoke`, then the `SEAT_FAILED` rate in rows |
| `resident_bytes` per model at `num_ctx` 32768 | `/api/ps` after load, recorded in every local row |
| 105 GiB ceiling, 512 KiB/token, 4 GiB headroom | Compare against measured `resident_bytes` |
| chars / 3.5 estimate and the 1.3 CODE reserve factor | Compare against `prompt_eval_count` and `eval_count` |
| 1800 s gate timeout, 3600 s generate timeout | Gate durations and `total_duration_ns` |
| Wall clock per slice (≥ 4 loads per synthesis round, `P:458`) | `omarchy status --tokens` |

Stated limits:

- The chain is tamper-evident, not adversary-proof: the host can rewrite a branch and forge rows (`P:756`). Source tags and `SOURCE_MISMATCH` tie cloud rows to real commits, but a host that also forges those commits is not detected.
- The prompt sha proves receipt of the canonical prompt, not the absence of additions.
- s000 cloud rows carry `prompt_source = bootstrap`. Their prompts were not kernel-generated, and their inputs are checked only as lineage slots.
- File blocks cannot delete files.
- `CITED_LOCATIONS` is checked for syntax only.
- `ollama.lock` serializes sessions within one repo only.
- `verify --repo` needs every `slice/*` branch and `omarchy/*` tag (§16).

---

## 20. Deviations from 00_PROMPT

Each change below is structural. Anything not listed keeps the approved plan's decision.

| # | Change | Reason (evidence) |
|---|---|---|
| D1 | Adds the modules `omarchy/view.py` and `omarchy/report.py`, puts lineage in `runner.py`, and adds `prompts/smoke.md`, the `omarchy lock` command, and the test files `conftest.py`, `test_slots.py`, `test_report.py`, `test_cli.py`, `test_bootstrap_e2e.py`, and `test_pipeline_e2e.py` | The plan lists `omarchy lock --local-models` (`P:185`) but no such command (`P:462-472`). `machine.py` must stay pure (`P:603`). `report` needs `runner.build_prompt` to verify, and `runner` needs the view loader, so the loader takes its own module to the left of both (§2.2). `smoke` (`P:472`) needs a template. The added tests close B11, B12, and N03 |
| D2 | Optional `slice.json` key `review_files` (cloud read list; counts for coverage) | s001 audits every BOOTSTRAP file (`P:721`). Putting them in `context_files` inlines them into every local prompt (`P:431`) and guarantees `CONTEXT_OVERFLOW` at 32768. `verify --repo` needs a mechanical "reviewed" rule (`P:717`) |
| D3 | `03_PACKETS.json` gains `prompt_sha256`; ids are contiguous; no packet's context contains any target; argv[0] may not be a shell | A JSON slot cannot carry a trailer, yet every cloud slot must echo the prompt sha (`P:736`). A sibling target in a packet's context is a hidden dependency (`P:123`). Argv-only gates mean nothing if argv is `sh -c` (`.omarchy/omarchy.py:317-340`) |
| D4 | Trailers: exact key sets; ruling keys `HALT_CODE`, `HALT_SLOT`, `DISMISS_PATHS`; `QA_TESTS` maps files rather than test ids; `TOUCHED_FILES` and `MISSING_SYMBOLS` consistency rules; `PLAN_FILES` excludes `slices/` and `tests/qa/` | A ruling must name the HALT it settles, or it can be replayed against the wrong one. A file-level mapping can be checked without parsing a test runner's node ids. A plan file under `slices/` could never be a packet target (`P:372`) |
| D5 | `HALT` is not a row outcome. `MERGE_FAILED` is added, together with the `failure` field, the reserved seat `kernel`, and the added row fields of §9.1 (`roster`, `render_commit`, `diff_paths`, `prompt_source`, and the rest). There is one commit per row | A stored HALT duplicates derived state, giving two sources of truth: the N2 resume-file failure in another form (`.omarchy/batch_runner.py:85-90`). The commit-phase failure (`P:441`) needs an outcome. Merges need an author that is neither an LLM nor `parent` |
| D6 | Lineage is defined by explicit per-job tables with render commits (§10.1–§10.2). Local per-packet lineage carries only the approved plan chain, excludes `.diff`, and gives q2 the q1 QA reports and red tests. Neither stage-4 proposal sees the other. Every QA seat of a round is pinned to the dispatch commit `D_q`. Cloud read lists carry that immutable commit and a sha256 for every input | `P:430` would feed superseded, contradictory revisions to 32k-context models and let `04.B` read `04.A`, breaking N-version independence. The plan gives q2 no QA evidence, though q2 must fix QA failures. Rendering at a moving head makes prompts unreproducible (`P:415`) and breaks parallel QA (`C:43-46`) |
| D7 | CODE reserve = 4096 + ⌈1.3 × target characters / 3.5⌉ | File blocks return complete files (`P:400`). A flat 4,096 reserve (`P:435`) guarantees `done_reason: length` on any non-trivial packet |
| D8 | The pins (`KERNEL_CHANGED`, `LOCK_CHANGED`, `ILLEGAL_CONFIG`) are enforced only on non-terminal slices, and the roster is pinned in OPEN | Otherwise every DONE slice REFUSEs as soon as its own kernel change merges (`P:616`), and `status` breaks permanently |
| D9 | The dependency-manifest check runs at SYNTH record time and HALTs before REVIEW; `APPROVE_DEPENDENCY` continues to REVIEW | Under first-match evaluation, row 14 (merge) precedes row 15 (manifest) (`P:493-494`), so the HALT was unreachable before the merge. Checking earlier also saves a Family B load |
| D10 | Adds the HALT codes `MERGE_BLOCKED` and `ABORTED`; `SYNTH_DEADLOCK` only when gates PASS and LOC ≤ 300 | Row 18 has two outcomes (`P:497`). An override on a LOC or conflict failure would merge a G2 violation; those need a split, not an override (`P:755`) |
| D11 | Cloud content defects at record time write `SEAT_FAILED` rows for every cloud slot; operator errors refuse without a row; Ollama transport and residency errors consume no attempt | Only stage 3 had a record bound (`P:238`), so a bad cloud seat could loop forever in stages 1, 2, and 7. An Ollama outage is not a seat failure |
| D12 | Cloud ingest uses ancestry from `render_commit` (kernel prompts) or a lineage-slot check (bootstrap prompts), plus per-path provenance and an input check. These replace "ref merge-base equals slice head". `--ref` is the seat's own commit | With two QA seats, the first record moves the head, so the second always fails `P:442`. s000's cloud commits fork from `v3`, while `slice/s000-bootstrap` forks from `1156b29`, so the plan's check can never pass for the bootstrap. Ancestry plus provenance proves the seat saw the canonical inputs (`C:50-53`) |
| D13 | The kernel renders the ruling file from `omarchy rule` arguments, behind a TTY confirmation | A hand-written slot file is exactly what the plan bans (`P:265`). The TTY prompt is friction against an agent issuing rulings, and is stated as no stronger than that |
| D14 | The merge applies the recorded SYNTH `.diff` to the current head. There is no kept tx branch and no cherry-pick | A kept tx branch (`P:441`) is unrecorded mutable state outside the proof, exactly the N2 class. The `.diff` is already hashed in the row, and disjoint targets make it apply cleanly |
| D15 | QA evaluation runs `test_command`, then pytest per QA file. Adds the QA file naming rule, at most 10 QA files per record, dismissal limited to live red files, and the slot `07_QA.q{q}.EVAL.{k}.gates.log` with an unbounded index | Mapping red tests to packets needs per-file results. pytest's default import mode breaks on duplicate basenames across `tests/qa/*`. The file cap and the red-only dismissal bound the dismissal loop (§12.1). The evaluation log needs a slot to be hashed |
| D16 | `done_reason` must be `"stop"`; budget constants are not environment-overridable; a per-repo `ollama.lock` | K4 named only `length` (`P:451`). An environment override bypasses a pinned safety constant (`.omarchy/omarchy.py:542-545`). Two concurrent `run` commands on different slices would co-load families |
| D17 | Bootstrap mechanics: `open --bootstrap`; `BOOTSTRAP.json` with `schema`, `slice_id`, `kind`, and `prompts`, covering the Phase 3 files except append-only logs; `BOOTSTRAP.<slot>.prompt` files; `prompt_source = bootstrap` | `P:587` requires a real proof chain for s000, but its prompts were not kernel-generated. Phase 3 also writes code (`scripts/ensure_local_agents.sh`) and the lock, which s001 must audit (`P:721`) |
| D18 | The `AGENTS.md` seat table has no model column, and T-D1 compares six columns. T-D2's exclusions add `slices/**`, `docs/EVIDENCE.md`, and `docs/HISTORY.md`, and its slug set is the MODEL fields of cloud and local rows. This specification names no slug | T-D1 (`P:705`) requires slugs in `AGENTS.md`, which T-D2 (`P:706`) forbids. Proof rows and `docs/HISTORY.md:11` legitimately contain slugs. `00_ARCHITECTURE.md` is a copy of this text and is not excluded |
| D19 | `next` prints one `NEXT <KIND> <seat> <slot> a<k>` line per job, with seat ids rather than family names | The plan gives examples, not a grammar (`P:478-504`). A machine-readable, line-per-job form lets `parent` dispatch without parsing prose, and the attempt token makes retries visible |
| D20 | The prompt templates are specified verbatim (§10.6) rather than copied from the persona files | `P:608` salvages persona text from `.cursor/agents/qweny.md` and `.cursor/agents/moxie.md`. That text carries v2 vocabulary the v3 grammar forbids: `APPROVE_WITH_FIXES` at `.cursor/agents/moxie.md:33`, and proof-log and Rule 11 references at `.cursor/agents/qweny.md:8,12`. The intent of `.cursor/agents/qweny.md:12-14` and `.cursor/agents/moxie.md:12-15` is kept |
| D21 | `verify --repo` labels by content (`coverage_label`), so they do not depend on the PR merge strategy. `slice/*` branches and `omarchy/*` source tags are retained, and `verify` adds `SOURCE_MISMATCH` | `P:257` and `P:738` have the human merge by PR without fixing a strategy, and a "merge commit of a slice" rule labels squash, rebase, and fast-forward merges `FOREIGN_EDIT` (`C:69-74`). Source tags keep cloud commits reachable after cloud branches are deleted |
| D22 | The refusal code set extends `P:474` with the precondition codes of §13 and `SOURCE_MISMATCH` | Each of them is a distinct, operator-actionable reason that previously had no name |
| D23 | Family choice in `run` is "Family A first". The plan's "prefer the resident family" never applies | Every session evicts at exit (K6, `P:453`) and `run` sweeps at start (K7), so no family is ever resident when one is chosen. The four-load schedule of `P:458` still holds (T-E5) |

---

## 21. Response to 02_CHALLENGE.r1

Every finding was checked against `01_PLAN.r1.md` and found factually correct, so none is disputed.

| Id | Resolution | Section(s) changed | Change |
|---|---|---|---|
| B01 (`C:13`) | FIXED | §11.4 (T11, T12, T19), §18 T-M38 | T11 initializes `q`, `A`, and `B` once. T19 jumps to the round body T12 with its new values. Termination is argued in §11.4. T-M38 derives the whole q1-RED → q2 history with `History` |
| B02 (`C:20`) | FIXED | §5.5, §9.1, §9.4, §9.5, §11.2 checks 4–5, §14.5, §18 T-P11, T-P12 | A per-outcome required-file table, with the authored slot required only by its own `RECORDED` row. The rejected-bytes rule is per failure code. The MERGE log is always written. Integrity tests cover every fileless or alternate-file outcome |
| B03 (`C:27`) | FIXED | §2.4, §7.3, §7.5, §10.7, §13.4 B4–B5, §18 T-T8, T-T16, T-I13 | `SlotClass.PACKETS` with a verbatim output contract. `parse_packets` returns the claimed sha. The single comparison point is `record` B5, for every cloud class. Positive and mismatch tests |
| B04 (`C:34`) | FIXED | §10.2 planning-chain table, §18 T-R9 | Exact, duplicate-free sequences for each planning job, tested for exact order |
| B05 (`C:41`) | FIXED | §10.1 (`D_q`), §10.2 QA lineage, §10.4, §18 T-R7 | Every QA job of round `q` renders from the immutable dispatch commit `D_q`, which excludes current-round QA outputs and proof growth. `PROOF.jsonl` is never lineage |
| B06 (`C:48`) | FIXED | §10.4 read list, §13.4 A6 and B1–B2, §13.7, §18 T-I11, T-I12, T-E4 | The read list carries `commit:` and a sha256 for every SLOT and REPO input. Kernel-prompt refs must descend from `render_commit`. Path provenance then rejects any edited input, and `check_inputs` re-checks the blobs. Tests cover a stale-target ref and a non-descendant ref with exact lineage copies |
| B07 (`C:55`) | FIXED | §1 `INDEX`, §5.2, §12, §12.1, §13.4 B4, §18 T-M41, T-S1, T-S2 | `EVAL.<k>` and `HALT.<n>` use an unbounded canonical index. At most 10 QA files per record, and dismissal only of live red files, give a termination proof. Boundary tests at 10, 13, and 100 |
| B08 (`C:62`) | FIXED | §11.3, §11.4 T14, §13.5 step 3, §18 T-M39 | Replay accepts only the emitted step's jobs (with attempt and render commit), so kernel pre-emption is normative. `run` recomputes the step before every job. A forged skipped-kernel history is rejected |
| B09 (`C:69`) | FIXED | §13.8, §16, §2.4 `coverage_label`, §18 T-V4, T-E6; §20 D21 | Labels by content equality against each DONE slice's last merged blob, independent of merge strategy. Tested under merge, squash, rebase, and fast-forward. Branch and tag retention is stated as a requirement |
| B10 (`C:76`) | FIXED | §2.3, §14.5, §15 K5–K7, §18 T-W8, T-O11 | The exhaustive exception table adds `MergeConflict` and `ResidencyError`, each with base, fields, raiser, handling, attempt effect, and exit code |
| B11 (`C:83`) | FIXED | §5.2 (per-kind regex table, normative vectors), §5.3, §5.4, §18 T-S1–T-S6 | The grammar is a table of mutually exclusive regexes with field extraction. Normative accept and reject vectors cover every alternative, every boundary, companions, rejected files, and agreement with the class table |
| B12 (`C:90`) | FIXED | §17.3, §18.1 fixtures, §18 T-E1–T-E4, §13.7 | A tmp-repo end-to-end test of the exact divergent-base topology. Variants cover a deadlock override, a missing or stale challenged plan, a branch-tip ref, a prompt-sha mismatch, and a forged source commit detected by the new `SOURCE_MISMATCH` |
| N01 (`C:99`) | FIXED | §18 T-L13 | The exact fixture: the repo lock text plus one optional row, parsed together; the optional file is never parsed alone |
| N02 (`C:106`) | FIXED | §11.5 step 3, §18 T-M40 | Stated as advisory and never a transition control, and tested across verdict combinations |
| N03 (`C:113`) | FIXED | §13.12, §18 T-X1–T-X6 | CLI surface specified (usage errors exit 64, stdout and stderr split, `main` injection points) and tested for every exit code |

Further corrections in this revision, found while resolving the findings:

- **Import cycle.** `report` needed `runner` and the reverse; `view.py` breaks the cycle (§2.2).
- **Proposal independence.** r1 let `04.B` see `04.A` (§10.2).
- **Exit-code collision.** argparse's default exit 2 collided with the git-error code (§13.12).
- **Model slugs.** r1 named model slugs in text that `00_ARCHITECTURE.md` copies, which would fail T-D2 (§0, §3.3, T-O3).
- **Render vs worktree base.** `render_commit` is now separated from `base_commit` (§9.1).
- **Empty diffs and non-READY code.** Both now have defined companions and merge behavior (§5.4, §14.5).
- **Rulings depend on history.** `legal_rulings` now takes the history, because two of its conditions depend on it (§12).
- **Input source.** `open` reads its inputs from `HEAD` blobs (§13.1).
- **Exact staging.** `kernel_commit` checks the staged change set exactly (§9.5).

---
OMARCHY_STATUS: READY
PLAN_FILES: omarchy/__init__.py, omarchy/__main__.py, omarchy/lock.py, omarchy/slice.py, omarchy/trailers.py, omarchy/proof.py, omarchy/machine.py, omarchy/worktree.py, omarchy/view.py, omarchy/ollama.py, omarchy/runner.py, omarchy/report.py, omarchy/ingest.py, omarchy/prompts/plan.md, omarchy/prompts/challenge.md, omarchy/prompts/packets.md, omarchy/prompts/propose.md, omarchy/prompts/critique.md, omarchy/prompts/synthesize.md, omarchy/prompts/review.md, omarchy/prompts/qa.md, omarchy/prompts/family_a.md, omarchy/prompts/family_b.md, omarchy/prompts/smoke.md, scripts/omarchy, scripts/ensure_local_agents.sh, tests/conftest.py, tests/test_lock.py, tests/test_slots.py, tests/test_slice_config.py, tests/test_trailers.py, tests/test_proof.py, tests/test_machine.py, tests/test_worktree.py, tests/test_ollama.py, tests/test_runner.py, tests/test_report.py, tests/test_ingest.py, tests/test_cli.py, tests/test_bootstrap_e2e.py, tests/test_pipeline_e2e.py, tests/test_docs_sync.py, agents.lock, agents.lock.optional, AGENTS.md, README.md, 00_ARCHITECTURE.md, 01_OMARCHY_AGENT_PROMPTS.md, .gitignore, .cursor/rules/omarchy-council.mdc, .cursor/agents/linus.md, .cursor/agents/knuth.md, .cursor/agents/dhh.md, .cursor/agents/carmack.md, docs/EVIDENCE.md, docs/HISTORY.md, archive/v2.3.1-attempt1/README.md, archive/v2.3.1-attempt1/council/FLOW_TRACE.md, archive/v2.3.1-attempt1/council/LINUS_AUDIT_PLAN.md, archive/v2.3.1-attempt1/council/LINUS_BALLOT.md, archive/v2.3.1-attempt1/council/MOXIE_G4_TEST.md, archive/v2.3.1-attempt1/council/MOXIE_G5_REVIEW.md, archive/v2.3.1-attempt1/council/QWENY_AUDIT_WORKSHEET.md, archive/v2.3.1-attempt1/council/SCRUM_DOD_AUDIT.md, archive/v2.3.1-attempt1/packets/aud231-s01-build.json, archive/v2.3.1-attempt1/packets/aud231-s09-g4.json, archive/v2.3.1-attempt1/packets/aud231-s10-g5.json, archive/v2.3.1-attempt1/packets/aud231-s11-dod.json, archive/v2.3.1-attempt1/contracts/STORY-AUDIT-V231.md, archive/v2.3.1-attempt1/contracts/UC-AUDIT-V231-WS.md, archive/v2.3.1-attempt1/contracts/UC-AUDIT-V231-G4.md, archive/v2.3.1-attempt1/contracts/UC-AUDIT-V231-G5.md, archive/v2.3.1-attempt1/contracts/UC-AUDIT-V231-DOD.md
OMARCHY_PROMPT_SHA256: bdf4b37738520f33795cb46b0078682f18d2ee288648d1ace362e4a4e2dd0882
---
