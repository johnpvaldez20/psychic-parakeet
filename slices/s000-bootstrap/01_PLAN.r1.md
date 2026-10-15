# 01_PLAN.r1 — Omarchy v3.0 Kernel Specification (slice `s000-bootstrap`)

Author: linus · cloud run bc-f26002ae-4aa5-42ba-b2d3-e19c8bc4a697 · 2026-10-15
Slot: `slices/s000-bootstrap/01_PLAN.r1.md` · stage 1 · round 1
Inputs read: `slices/s000-bootstrap/slice.json`, `slices/s000-bootstrap/00_PROMPT.md`, `.omarchy/omarchy.py`, `.omarchy/batch_runner.py`, `docs/GRAND_COUNCIL/v2.3.1_Test/*`, `agents.lock`, `agents.lock.optional`, `scripts/*.sh`, `tests/test_omarchy_kernel.py`.

Citation shorthand: `P:<n>` means `slices/s000-bootstrap/00_PROMPT.md:<n>`. Every other citation is a full `path:line` at `v3` HEAD `fc61064`.

## 0. Status of this document

- This specification is normative. "MUST", "MUST NOT", and "exactly" carry no implementer discretion. If this document is silent on a point, the approved plan in `00_PROMPT.md` governs. If the two conflict, this document wins, and every such conflict is listed in §20.
- `parent` implements §1–§18 once, as the bootstrap exception (`P:585`, `P:709-719`). After approval, Phase 3 copies §1–§19 of the approved revision into `00_ARCHITECTURE.md` (§17.3).
- Nothing in this document is measured. Every number that is a guess is marked `UNMEASURED` and is listed again in §19.

---

## 1. Conventions

| Term | Definition |
|---|---|
| repo | The git checkout that contains the running kernel package `omarchy/`. The kernel locates it as the parent directory of the package directory and ignores the process cwd. The kernel that runs is always this checkout's working tree (`P:614-616`). |
| repo path | A repo-relative POSIX path matching `REPO_PATH` (below), which also survives sterilization: resolving `<root>/<path>`, following symlinks, stays inside `<root>`. This is the v2 `sterilize_path` rule (`.omarchy/omarchy.py:216-233`) applied to every path the kernel reads or writes. |
| sha256 | Lowercase 64-hex SHA-256 of the exact bytes named. No normalization ever happens before hashing. |
| commit id | 40-hex git object id. |
| text | UTF-8, LF line endings. A CR byte anywhere in a slot file or trailer is a defect. |
| LOC | The sum of additions and deletions reported by `git diff --numstat` (the G2 measure, `P:116`). |
| time | UTC, `YYYY-MM-DDTHH:MM:SSZ`. |
| regex | Python `re` syntax, always applied as a full match. |
| runtime | Python ≥ 3.10, standard library only for `omarchy/**`. `pytest` is used by tests only. There is no dependency manifest. |

```text
REPO_PATH = (?!/)(?!\.git(?:/|$))(?!.*//)(?!(?:.*/)?\.{1,2}(?:/|$))[A-Za-z0-9._@+-]+(?:/[A-Za-z0-9._@+-]+)*
SLICE_ID  = s[0-9]{3}[a-z]?(?:-[a-z0-9]+)+          (max 48 chars; s000-bootstrap, s001-kernel-audit, s001b-...)
SEAT_ID   = [a-z][a-z0-9_]{0,31}
PKT_ID    = pkt-[0-9]{2}
HEX64     = [0-9a-f]{64}
```

Reserved seat ids: `human` (human-authored rows) and `kernel` (kernel actions: merge, QA evaluation, context overflow). Neither may appear in `agents.lock`.

---

## 2. Package and module contract

### 2.1 Files

| Path | Responsibility | v2 salvage (cited) |
|---|---|---|
| `omarchy/__init__.py` | `__version__ = "3.0.0rc0"`; exception types | — |
| `omarchy/__main__.py` | argparse CLI (§13), dispatch, exit codes (§11.6) | `parse_args`, `main` (`.omarchy/omarchy.py:856-905`) |
| `omarchy/lock.py` | `agents.lock` schema 3 strict parse, invariants, seat lookup | `parse_agents_lock`, `locked_local_family_models` (`.omarchy/omarchy.py:60-167`) |
| `omarchy/slice.py` | `slice.json`, `03_PACKETS.json`, `BOOTSTRAP.json` validation; slot-name grammar; path sterilization; manifest test | `sterilize_path` (`.omarchy/omarchy.py:216-233`) |
| `omarchy/trailers.py` | Outer-fence strip, file-block parser, trailer grammar, per-class validation, ruling rendering | fence strip (`.omarchy/omarchy.py:654-658`) |
| `omarchy/proof.py` | Proof row schema, canonical JSON lines, hash chain, flocked append, commit messages and trailers, `kernel_sha256` | `append_locked_log` (`.omarchy/omarchy.py:343-353`) |
| `omarchy/machine.py` | Pure state machine: integrity checks, transitions, step formatting, `STAGES`. No IO, no `subprocess`, no `urllib`, no file reads | — |
| `omarchy/worktree.py` | git plumbing: slice worktree, temporary worktrees, block writes, staged diff and numstat, diff apply, gates with logs, kernel commits, fast-forward, commit listing, slice flock | `WorktreeTransaction`, `run_deterministic_gates`, `apply_agent_changes` (`.omarchy/omarchy.py:317-340`, `:360-497`, `:693-716`) |
| `omarchy/ollama.py` | HTTP client, residency checks, budget, `family_session`, sweep | `invoke_ollama_serial`, `enforce_memory_budget`, `force_unload_model`, `evict_model`, batch `finally` (`.omarchy/omarchy.py:542-690`, `.omarchy/batch_runner.py:50-73`, `:313-317`) |
| `omarchy/runner.py` | Lineage (pure), prompt build (local and cloud), token estimate, job ordering, `run`, `smoke` | `build_agent_prompt` (`.omarchy/omarchy.py:505-539`) |
| `omarchy/ingest.py` | `open`, `record`, `rule`: every path by which human or cloud bytes enter a slice | — |
| `omarchy/report.py` | `load_view` (reads slice tip into a `SliceView`), `verify`, `verify --repo`, `status` | — |
| `omarchy/prompts/*.md` | Stage templates `plan`, `challenge`, `packets`, `propose`, `critique`, `synthesize`, `review`, `qa`; personas `family_a`, `family_b`; `smoke`. All are part of `kernel_sha256` | persona text from `.cursor/agents/qweny.md`, `.cursor/agents/moxie.md` |
| `scripts/omarchy` | Bash shim: `set -euo pipefail`; prepend the repo root to `PYTHONPATH`; `exec python3 -m omarchy "$@"` | — |

Import order (no cycles; a module may import only modules to its left): `__init__` → `lock` → `slice` → `trailers` → `proof` → `machine` → `worktree` → `ollama` → `report` → `runner` → `ingest` → `__main__`. `ollama` imports only `__init__` and `lock`. `machine` imports only `__init__`, `lock`, `slice`, `trailers`, `proof` (types and pure helpers). `omarchy.slice` shadows nothing at runtime, but importers MUST bind it as `from omarchy import slice as slicecfg`.

### 2.2 Exceptions (`omarchy/__init__.py`)

| Type | Fields | Meaning | CLI exit |
|---|---|---|---|
| `OmarchyError(Exception)` | message | Kernel or environment failure (git error, Ollama down, residency failure) | 1 (2 for `subprocess.CalledProcessError`, as v2 `.omarchy/omarchy.py:900-905`) |
| `Refusal(OmarchyError)` | `code: str`, `subject: str` (slot, path, or `-`), `detail: str` | Integrity or precondition refusal (§11.2, §13) | 65 |
| `SeatFailure(OmarchyError)` | `failure: str` (§9.4), `rejected: bytes \| None` | The seat's output is defective; becomes a `SEAT_FAILED` row | n/a (converted to a row) |
| `LockError(Refusal)` | as `Refusal`, `code = "ILLEGAL_LOCK"` | Lock parse or invariant failure | 65 |

### 2.3 Public functions

Types are Python annotations. `Path` is `pathlib.Path`. Frozen dataclasses everywhere.

| Module | Public name | Signature / fields |
|---|---|---|
| lock | `Seat` | `seat_id: str, group: str, runtime: str, family: str, model: str, caps: frozenset[str], weight: str` |
| lock | `Lock` | `seats: tuple[Seat, ...], sha256: str` |
| lock | `parse_lock` | `(text: str, sha256: str) -> Lock` raises `LockError` |
| lock | `load_lock` | `(path: Path) -> Lock` |
| lock | `seat`, `planner`, `family_seat` | `(lock, seat_id) -> Seat`; `(lock) -> Seat`; `(lock, family) -> Seat` |
| lock | `challenger_legal`, `qa_legal` | `(lock, seat_id: str) -> bool` (§4.3) |
| lock | `local_models` | `(lock) -> dict[str, str]` family → model |
| slice | `SliceConfig` | fields of §4.1 plus `review_files` defaulted |
| slice | `parse_slice_config` | `(text: str, slice_id: str) -> SliceConfig` (structural; no lock) |
| slice | `check_config_legal` | `(cfg: SliceConfig, lock: Lock) -> None` raises `Refusal("ILLEGAL_CONFIG")` |
| slice | `Packet`, `Packets` | fields of §6 |
| slice | `parse_packets` | `(text: str, cfg: SliceConfig, approved_plan_sha256: str, plan_files: tuple[str, ...]) -> Packets` raises `SeatFailure("PACKETS_INVALID")` |
| slice | `SlotName` | `name, kind, stage: int, packet_id, qa_round, round, variant, seat_id, ext, eval_index, halt_index, attempt` (absent parts `None`) |
| slice | `parse_slot_name` | `(name: str) -> SlotName` raises `ValueError` |
| slice | `check_repo_path`, `sterilize_path` | `(p: str) -> str`; `(rel: str, root: Path) -> Path` |
| slice | `is_manifest`, `qa_file_ok` | `(path: str) -> bool`; `(slice_id: str, path: str) -> bool` |
| slice | `BootstrapRecord`, `parse_bootstrap` | §8; `(text: str, slice_id: str) -> BootstrapRecord` |
| trailers | `strip_outer_fence` | `(text: str) -> str` (§7.1) |
| trailers | `split_trailer` | `(text: str) -> tuple[str, dict[str, str]]` (body, keys) |
| trailers | `FileBlock`, `parse_file_blocks` | `path: str, content: bytes`; `(body: str) -> tuple[FileBlock, ...]` |
| trailers | `SlotClass` | enum `PLAN, VERDICT, CODE, QA, RULING` |
| trailers | `Parsed` | `status, verdict, blocking_count, plan_files, touched_files, missing_symbols, cited, qa_tests, ruling, halt_code, halt_slot, dismiss_paths, reason, prompt_sha256, blocks` |
| trailers | `parse_slot` | `(cls: SlotClass, raw: bytes, *, local: bool, cloud: bool, allowed_paths: frozenset[str] = frozenset()) -> Parsed` raises `SeatFailure` |
| trailers | `output_contract` | `(cls: SlotClass, *, cloud: bool, targets: tuple[str, ...]) -> str` (text appended to prompts, §10.6) |
| trailers | `render_ruling` | `(n: int, ruling: str, halt_code: str, halt_slot: str, paths: tuple[str, ...], reason: str) -> bytes` |
| proof | `ROW_FIELDS`, `ZERO_SHA` | tuple of §9.1 field names; `"0" * 64` |
| proof | `sha256_bytes`, `canonical_line` | `(b: bytes) -> str`; `(row: dict) -> bytes` |
| proof | `new_row` | `(**fields) -> dict` (fills every absent field with `None`) |
| proof | `parse_rows` | `(data: bytes) -> tuple[dict, ...]` raises `Refusal("CHAIN_BROKEN")` |
| proof | `append_row` | `(path: Path, row: dict) -> dict` (flock, assigns `seq`, `prev_sha256`, writes, fsyncs) |
| proof | `CommitInfo` | `sha: str, parent_count: int, subject: str, trailers: dict[str, str], changes: tuple[tuple[str, str], ...]` (status `A`/`M`/`D`, path), `proof_lines: int` |
| proof | `commit_message`, `parse_commit_trailers` | `(row: dict) -> str`; `(message: str) -> dict[str, str]` |
| proof | `kernel_sha256` | `(package_dir: Path) -> str` (§9.6) |
| machine | `STAGES` | §11.7 |
| machine | `Job` | `kind: "CLOUD"\|"LOCAL"\|"KERNEL", action: "author"\|"merge"\|"qa_eval", seat_id, family, slot, stage, packet_id, qa_round, round, attempt: int, render_commit: str \| None` |
| machine | `Step` | `kind: "NEXT"\|"HALT"\|"DONE"\|"DONE_BOOTSTRAP"\|"REFUSE", jobs: tuple[Job, ...], code: str \| None, subject: str \| None` |
| machine | `SliceView` | `slice_id, cfg, packets: Packets \| None, rows, commits, tip_files: Mapping[str, str]` (path → sha256 for every file under `slices/<id>/` and `tests/qa/<id>/`), `head: str, running_kernel_sha256: str, running_lock: Lock \| None, bootstrap: BootstrapRecord \| None` |
| machine | `check_integrity` | `(view) -> None` raises `Refusal` (§11.2) |
| machine | `derive` | `(view, n_rows: int) -> Step` state after the first `n_rows` rows; no tip checks |
| machine | `runnable` | `(view, n_rows: int) -> tuple[Job, ...]` every runnable job of every kind (empty on HALT/DONE) |
| machine | `next_step` | `(view) -> Step` = `check_integrity` then `derive(view, len(rows))`; a `Refusal` becomes `Step("REFUSE", ...)` |
| machine | `approved_plan`, `legal_rulings` | `(view, n_rows) -> str \| None`; `(step) -> frozenset[str]` |
| machine | `format_step`, `exit_code` | `(step) -> str` (§11.6); `(step) -> int` |
| worktree | `git` | `(cwd: Path, *args: str, stdin: bytes \| None = None) -> bytes` (argv only, `check=True`, captured) |
| worktree | `slice_branch`, `slice_worktree` | `(slice_id) -> str` = `slice/<id>`; `(repo, slice_id) -> Path` = `.omarchy/worktrees/<id>/slice` |
| worktree | `slice_lock` | context manager `(repo, slice_id)`: non-blocking `flock` on `.omarchy/locks/<id>.lock`; busy → `Refusal("SLICE_BUSY")` |
| worktree | `check_clean` | `(wt: Path, branch: str) -> None` raises `Refusal("DIRTY_WORKTREE" \| "WRONG_BRANCH")` |
| worktree | `TempWorktree` | context manager `(repo, slice_id, name: str, base: str) -> Path`; always removes worktree and branch on exit |
| worktree | `write_blocks` | `(wt, blocks, allowed: frozenset[str]) -> None` |
| worktree | `DiffResult`, `stage_diff` | `diff: bytes, numstat_loc: int, paths: tuple[str, ...], manifest_paths: tuple[str, ...]`; `(wt, paths) -> DiffResult` |
| worktree | `apply_diff` | `(wt, diff: bytes) -> DiffResult` raises `SeatFailure`-free `MergeConflict(OmarchyError)` |
| worktree | `GateResult`, `run_gates` | `passed: bool, log: bytes`; `(wt, commands: tuple[tuple[str, ...], ...]) -> GateResult` (§14.4) |
| worktree | `kernel_commit` | `(wt, row: dict, add: Mapping[str, bytes], delete: tuple[str, ...]) -> str` writes files, appends the row, commits; returns commit id |
| worktree | `fast_forward` | `(slice_wt, branch: str, expected_head: str) -> None` |
| worktree | `read_blob`, `list_commits`, `list_tree` | `(repo, commit, path) -> bytes \| None`; `(repo, base, tip) -> tuple[CommitInfo, ...]`; `(repo, commit, prefix) -> dict[str, str]` |
| ollama | constants | §15 |
| ollama | `Client` | `(base_url: str)`; `tags() -> list[dict]`, `ps() -> list[dict]`, `generate(model, prompt, num_ctx) -> dict`, `unload(model) -> None` |
| ollama | `match_model` | `(entries: list[dict], slug: str) -> dict \| None` (§15 K8) |
| ollama | `check_budget` | `(weight_bytes: int, num_ctx: int) -> None` |
| ollama | `evict_all_except`, `sweep` | `(client, keep: str \| None) -> None`; `(client) -> None` |
| ollama | `Generation` | `response: str, done_reason, eval_count, prompt_eval_count, total_duration_ns, resident_bytes` |
| ollama | `family_session` | context manager `(client, lock, family, num_ctx, locks_dir: Path) -> Session`; `Session.generate(prompt: str) -> Generation` |
| report | `load_view` | `(repo, slice_id, n_rows: int \| None = None) -> SliceView` |
| report | `verify`, `verify_repo`, `status` | `(repo, slice_id) -> int`; `(repo) -> int`; `(repo, markdown: bool, tokens: bool) -> int` |
| runner | `Lineage`, `lineage` | `slots: tuple[str, ...], repo_files: tuple[str, ...], render_commit: str \| None`; `(view, job) -> Lineage` (pure) |
| runner | `build_prompt` | `(repo, view, job) -> str` byte-deterministic |
| runner | `estimate_tokens`, `reserve_tokens` | `(text: str) -> int` = ⌈len/3.5⌉; `(repo, view, job) -> int` (§10.5) |
| runner | `order_jobs` | `(jobs, resident_family: str \| None) -> tuple[str, tuple[Job, ...]]` |
| runner | `run`, `smoke` | `(repo, slice_id) -> int`; `(repo) -> int` |
| ingest | `open_slice`, `record`, `rule` | `(repo, slice_id, bootstrap: bool) -> int`; `(repo, slice_id, slot, seat_id, ref, cloud_run) -> int`; `(repo, slice_id, ruling, reason, paths) -> int` |
| ingest | `ingest_allowed` | `(slice_id, slot, path) -> bool` (§13.4) |

---

## 3. `agents.lock` schema 3

### 3.1 Grammar

- Lines are LF-separated. A line that is empty or starts with `#` is ignored.
- The first other line MUST be exactly `schema=3`. Any other value or position is `ILLEGAL_LOCK` (`.omarchy/omarchy.py:65-79` never checks schema; ballot N7 at `docs/GRAND_COUNCIL/v2.3.1_Test/LINUS_BALLOT.md:133-137`).
- Every remaining line has exactly 7 `|`-separated fields: `SEAT|GROUP|RUNTIME|FAMILY|MODEL|CAPS|WEIGHT`. A field MUST NOT be empty or carry leading or trailing whitespace. Any deviation is fatal, never skipped (contrast `.omarchy/omarchy.py:70-71`).

| Field | Grammar |
|---|---|
| SEAT | `SEAT_ID`, unique, not `human` or `kernel` |
| GROUP | `grand_council` iff RUNTIME `cloud`; `local_council` iff `local`; `orchestrator` iff `host` |
| RUNTIME | `cloud` \| `local` \| `host` |
| FAMILY | `[a-z][a-z0-9_]{0,31}`; local seats: `local_family_a` \| `local_family_b`; host: `host` |
| MODEL | `[^\s|]+` |
| CAPS | comma-separated, no spaces, no duplicates, subset of `{plan, challenge, qa, propose, critique, synthesize, review, host}` |
| WEIGHT | `[^|]+` (free text) |

### 3.2 Invariants (all fatal at parse)

1. Exactly one `host` seat; its id is `parent`, its caps are exactly `host`; `host` appears on no other seat.
2. Exactly one seat has `plan`; it is `cloud`.
3. Exactly one local seat per local family; the two models differ.
4. Cloud seat families are pairwise distinct.
5. `synthesize` only on Family A; `review` only on Family B; `propose` and `critique` on both local seats.
6. `qa` only on cloud seats other than the planner.
7. `challenge` only on cloud seats whose family differs from the planner's, or on the Family A seat.
8. Family A caps ⊇ `{propose, critique, synthesize}`; Family B caps ⊇ `{propose, critique, review}`.

### 3.3 Repo content after Phase 3

`agents.lock` contains exactly the rows at `P:272-276` under a header comment that names the format and invariants. `agents.lock.optional` (same grammar, same header line `schema=3`, never loaded by the kernel) contains exactly:

```text
schema=3
dhh|grand_council|cloud|muse_spark|muse-spark-1.3-high|challenge,qa|Optional challenger or QA seat
carmack|grand_council|cloud|xai_grok|grok-4.7-high|challenge,qa|Optional challenger or QA seat
```

The slugs come from the current optional lock (`agents.lock.optional:6-7`). Model slugs appear only in these two files and in excluded records (§18, T-D2).

---

## 4. `slice.json` schema 3

### 4.1 Fields

Parsed with a strict JSON loader: duplicate keys rejected, `true`/`false` never accepted as integers, unknown keys rejected (`P:333`).

| Key | Type | Required | Rule |
|---|---|---|---|
| `schema` | int | yes | `3` |
| `slice_id` | str | yes | `SLICE_ID`; equals the directory name |
| `title` | str | yes | 1–120 chars, no newline |
| `base_ref` | str | yes | Resolves with `git rev-parse --verify <ref>^{commit}` in the repo at `open` |
| `challenger_seat` | str | yes | Legal per §4.3 |
| `qa_seats` | list[str] | yes | 1–3 unique entries, each legal per §4.3 |
| `test_command` | list[list[str]] | yes | 1–5 argv lists; each 1–64 non-empty strings; `basename(argv[0])` ∉ `{sh, bash, zsh, dash, ksh, fish, env}` |
| `context_files` | list[str] | yes | 0–20 unique repo paths, each present at `base_ref`; inlined into every local prompt |
| `review_files` | list[str] | no (default `[]`) | 0–200 unique repo paths, each present at `base_ref`; listed (not inlined) in cloud prompts; counts for coverage (§13.8). New key, §20 D2 |
| `num_ctx` | int | yes | 4096–131072 |
| `max_packets` | int | yes | 1–20 |

`slices/s000-bootstrap/slice.json:1-12` validates under this schema (it omits `review_files`).

### 4.2 Fixed roles

The planner is the unique `plan` seat. The synthesizer is the Family A seat. The reviewer is the Family B seat. None are configurable (`P:333`).

### 4.3 Legality (checked at `open`, and on every non-terminal `next` while pins hold)

- `challenger_legal(c)`: `c` is in the lock, has cap `challenge`, and either (`runtime(c) = cloud` and `family(c) ≠ family(planner)`) or (`runtime(c) = local` and `family(c) = local_family_a`) (`P:337-342`).
- `qa_legal(s)`: `s` is in the lock, `runtime(s) = cloud`, has cap `qa`, and `s ≠ planner`. The challenger may also be a QA seat.

---

## 5. Slice directory and slot grammar

### 5.1 Layout

All slice state lives on branch `slice/<id>` (worktree `.omarchy/worktrees/<id>/slice`). The human's checkout holds only the inputs to `open`. `status`, `next`, and `verify` read the branch tip, never a working tree.

### 5.2 Slot filename grammar

Every file under `slices/<id>/` on the slice branch MUST match `SLOT` (full match against the basename; no subdirectories):

```text
SLOT = (?:
    slice\.json
  | 00_PROMPT\.md
  | 01_PLAN\.r[12]\.md
  | 02_CHALLENGE\.r[12]\.md
  | 03_PACKETS\.json
  | 04_pkt-[0-9]{2}\.q[12]\.[AB]\.(?:md|diff|gates\.log)
  | 05_pkt-[0-9]{2}\.q[12]\.(?:A_ON_B|B_ON_A)\.md
  | 06_pkt-[0-9]{2}\.q[12]\.SYNTH\.r[12]\.(?:md|diff|gates\.log)
  | 06_pkt-[0-9]{2}\.q[12]\.REVIEW\.r[12]\.md
  | 06_pkt-[0-9]{2}\.q[12]\.MERGE\.r[12]\.gates\.log
  | 07_QA\.q[12]\.[a-z][a-z0-9_]{0,31}\.md
  | 07_QA\.q[12]\.EVAL\.[1-9]\.gates\.log
  | HALT\.[1-9][0-9]?\.HUMAN\.md
  | PROOF\.jsonl
  | BOOTSTRAP\.json
  | BOOTSTRAP\.(?:01_PLAN|02_CHALLENGE)\.r[12]\.md\.prompt
  | (?P<authored>
        01_PLAN\.r[12]\.md | 02_CHALLENGE\.r[12]\.md | 03_PACKETS\.json
      | 04_pkt-[0-9]{2}\.q[12]\.[AB]\.md | 05_pkt-[0-9]{2}\.q[12]\.(?:A_ON_B|B_ON_A)\.md
      | 06_pkt-[0-9]{2}\.q[12]\.(?:SYNTH|REVIEW)\.r[12]\.md | 07_QA\.q[12]\.[a-z][a-z0-9_]{0,31}\.md
    )\.a[1-4]\.rejected
)
```

(Whitespace inside the pattern is layout only; the implementation compiles it with `re.VERBOSE`.)

Files under `tests/qa/<id>/` MUST match `tests/qa/<id>/test_<idu>_[a-z0-9_]{1,40}\.py`, where `<idu>` is the slice id with `-` replaced by `_`. Unique basenames keep pytest's default import mode from colliding across slices. No `conftest.py` and no `__init__.py`.

### 5.3 Slot classes

| Slot | Stage | Class (§7) | Author | Kernel-derived companions |
|---|---|---|---|---|
| `slice.json`, `00_PROMPT.md` | 0 | — | human | — |
| `01_PLAN.r{n}.md` | 1 | PLAN | planner | — |
| `02_CHALLENGE.r{n}.md` | 2 | VERDICT | challenger | — |
| `03_PACKETS.json` | 3 | JSON (§6) | planner | — |
| `04_<p>.q{q}.{A,B}.md` | 4 | CODE | Family A / Family B | `.diff`, `.gates.log` |
| `05_<p>.q{q}.A_ON_B.md` / `B_ON_A.md` | 5 | VERDICT | Family A on B / Family B on A | — |
| `06_<p>.q{q}.SYNTH.r{n}.md` | 6 | CODE | Family A | `.diff`, `.gates.log` |
| `06_<p>.q{q}.REVIEW.r{n}.md` | 6 | VERDICT | Family B | — |
| `06_<p>.q{q}.MERGE.r{n}.gates.log` | 6 | kernel | `kernel` | — |
| `07_QA.q{q}.<seat>.md` | 7 | QA | QA seat | `tests/qa/<id>/**` |
| `07_QA.q{q}.EVAL.{k}.gates.log` | 7 | kernel | `kernel` | — |
| `HALT.{n}.HUMAN.md` | — | RULING | human (via `omarchy rule`) | — |
| `<authored>.a{k}.rejected` | — | raw rejected bytes | kernel | — |

Local `.md` slot files are the exact UTF-8 bytes of the Ollama `response` string. Parsing happens on read, so `output_sha256` is the sha256 of the slot file (`P:314`).

---

## 6. `03_PACKETS.json`

Strict JSON (as §4.1). Unknown keys rejected at every level.

| Key | Type | Rule |
|---|---|---|
| `schema` | int | `3` |
| `plan_sha256` | str | `HEX64`; equals `output_sha256` of the approved plan revision (§11.4) |
| `prompt_sha256` | str | `HEX64`; equals the prompt sha of this slot (§10.7). New key, §20 D3 |
| `packets` | list | 1 to `max_packets` entries |
| `packets[].packet_id` | str | `PKT_ID`; the list is exactly `pkt-01 … pkt-NN` in order |
| `packets[].title` | str | 1–120 chars, no newline |
| `packets[].plan_section` | str | `[0-9]+(?:\.[0-9]+)*` |
| `packets[].instructions` | str | 1–8000 chars |
| `packets[].acceptance` | list[str] | 1–10 non-empty strings |
| `packets[].target_files` | list[str] | 1–5 unique repo paths (`.omarchy/omarchy.py:273-276`) |
| `packets[].context_files` | list[str] | 0–10 unique repo paths, disjoint from the packet's own targets |
| `packets[].verification_commands` | list[list[str]] | 1–5 argv lists, same rule as `test_command` |

Cross-packet rules: `target_files` are pairwise disjoint across packets; each target is in the approved plan's `PLAN_FILES`; no target is under `slices/` or `tests/qa/`; no packet's `context_files` intersects another packet's `target_files` (a sibling's target can change under the reader, which is the hidden dependency the plan bans at `P:123`). Any violation is `SeatFailure("PACKETS_INVALID")`. There are no `role`, `family`, `model`, `depends_on`, or `base_branch` keys (`P:376`).

---

## 7. Response formats and trailers

### 7.1 Outer fence (local slots only, K2)

Let `t` be the response with leading and trailing whitespace removed. If `t` has at least two lines, its first line matches `` ```[A-Za-z0-9_+-]* `` and its last line is exactly `` ``` ``, the parse input is the lines strictly between them. Otherwise the parse input is the response unchanged. Exactly one level is ever removed, and inner fences are never touched. v2 stripped only a json fence by regex on both ends (`.omarchy/omarchy.py:654-658`); the strip was added mid-run (`docs/GRAND_COUNCIL/v2.3.1_Test/FLOW_TRACE.md:38`). The slot file still stores the unstripped bytes.

### 7.2 Trailer block

1. The parse input MUST be valid UTF-8 and contain no CR byte.
2. Split on LF. Discard trailing lines that are empty or whitespace-only.
3. The last remaining line MUST be exactly `---`. The opening delimiter is the nearest earlier line that is exactly `---`. The lines strictly between are the trailer (at least one); everything before the opening delimiter is the body.
4. Every trailer line MUST match `([A-Z][A-Z0-9_]*): (\S(?:.*\S)?)`. Keys are unique. The key set MUST equal the class's required set exactly; extra keys are a defect.

Any failure is `SeatFailure("TRAILER_INVALID")`.

### 7.3 Required keys and value grammars

List values split on `,` and strip spaces from each item; an empty item is a defect. `NONE` stands alone.

| Class | Keys (exact set) |
|---|---|
| PLAN (`01`) | `OMARCHY_STATUS`, `PLAN_FILES`, `OMARCHY_PROMPT_SHA256` |
| VERDICT, cloud (`02` from a cloud seat) | `OMARCHY_VERDICT`, `BLOCKING_COUNT`, `CITED_LOCATIONS`, `OMARCHY_PROMPT_SHA256` |
| VERDICT, local (`02` from Family A, `05`, `06 REVIEW`) | `OMARCHY_VERDICT`, `BLOCKING_COUNT`, `CITED_LOCATIONS` |
| CODE (`04`, `06 SYNTH`) | `OMARCHY_STATUS`, `TOUCHED_FILES`, `MISSING_SYMBOLS` |
| QA (`07`) | `OMARCHY_STATUS`, `QA_TESTS`, `OMARCHY_PROMPT_SHA256` |
| RULING (`HALT.n.HUMAN.md`) | `HUMAN_RULING`, `HALT_CODE`, `HALT_SLOT`, `DISMISS_PATHS`, `REASON` |

| Key | Grammar and consistency |
|---|---|
| `OMARCHY_STATUS` | `READY` \| `NEEDS_PLAN` \| `UNKNOWN`; QA class: `READY` only. `COMPLETE` is illegal (`docs/GRAND_COUNCIL/v2.3.1_Test/QWENY_AUDIT_WORKSHEET.md:141`) |
| `OMARCHY_VERDICT` | `APPROVE` \| `REQUEST_CHANGES` \| `REJECT`. `APPROVE_WITH_FIXES` is illegal (`P:392`) |
| `BLOCKING_COUNT` | `0\|[1-9][0-9]{0,3}`; `APPROVE` ⇔ `0`; `REQUEST_CHANGES` ⇒ ≥ 1; `REJECT` ⇒ ≥ 1 |
| `CITED_LOCATIONS` | `NONE` or list of `REPO_PATH:L` or `REPO_PATH:L-M` with `L,M` matching `[1-9][0-9]*`, `L ≤ M`. Syntax only; existence is not checked |
| `PLAN_FILES` | `NONE` or list of unique repo paths, none under `slices/` or `tests/qa/`. `READY` ⇒ not `NONE` |
| `TOUCHED_FILES` | `NONE` or list of unique repo paths. `READY` ⇒ equals the set of file-block paths. Otherwise `NONE` |
| `MISSING_SYMBOLS` | `NONE` or list of free-text items. `READY` ⇒ `NONE`; `NEEDS_PLAN`/`UNKNOWN` ⇒ not `NONE` |
| `QA_TESTS` | `NONE` or `;`-separated entries `<path> -> <PKT_ID>` (exactly one space each side of `->`). Each path satisfies §5.2, is added by this record, and appears once. Every file the record adds appears exactly once. Every packet exists. Failure → `QA_MAP_INVALID` |
| `OMARCHY_PROMPT_SHA256` | `HEX64`; equals the slot's prompt sha (§10.7). Mismatch → `PROMPT_SHA_MISMATCH` |
| `HUMAN_RULING` | `ABORT` \| `APPROVE_OVERRIDE` \| `APPROVE_DEPENDENCY` \| `RETRY` \| `DISMISS_QA_TEST` |
| `HALT_CODE`, `HALT_SLOT` | The HALT line being ruled on (§12) |
| `DISMISS_PATHS` | `NONE`, or (iff `DISMISS_QA_TEST`) list of existing QA test paths |
| `REASON` | 1–500 chars, no newline |

### 7.4 File blocks (CODE class only)

Code travels in file blocks, never JSON. MLX Ollama returns HTTP 501 for `format` (`docs/GRAND_COUNCIL/v2.3.1_Test/FLOW_TRACE.md:37`, `.omarchy/omarchy.py:621-622`), and JSON-escaping whole files is the main failure mode (`P:396`).

```text
=== FILE: <REPO_PATH> ===
<content lines>
=== END_FILE ===
```

- Blocks appear in the body only. Outside a block, a line starting `=== FILE:` that is not a well-formed opener, or any `=== END_FILE ===` line, is a defect. Inside a block, only the exact closer is special.
- Content bytes are each content line followed by LF (an empty block is an empty file). The content MUST be valid UTF-8.
- Paths are unique across blocks; every path is in the job's allowed set (the packet's `target_files`).
- `READY` ⇒ at least one block. `NEEDS_PLAN`/`UNKNOWN` ⇒ zero blocks.
- Unterminated block, duplicate path, bad UTF-8 → `FILE_BLOCK_INVALID`. Path outside the allowed set or failing sterilization → `PATH_NOT_ALLOWED`.
- File blocks cannot delete files. Deletion is out of scope for v3.0.

PLAN, VERDICT, QA, and RULING classes do not parse file blocks. Their body is prose.

---

## 8. `BOOTSTRAP.json`

Present only in `s000-bootstrap`. Strict JSON, unknown keys rejected. Extends `P:713` (§20 D17).

| Key | Type | Rule |
|---|---|---|
| `schema` | int | `3` |
| `slice_id` | str | `s000-bootstrap` |
| `authored_by` | str | `parent` |
| `authorized_by` | str | `human` |
| `reason` | str | `pipeline cannot build itself` |
| `superseded_by` | str | `s001-kernel-audit` |
| `files` | object | path → `{"sha256": HEX64, "kind": "kernel" \| "test" \| "prompt" \| "script" \| "config" \| "doc"}`. Every path the bootstrap creates or content-modifies in Phases 2–3, except `docs/EVIDENCE.md` and `docs/HISTORY.md` (append-only logs), `archive/**` moves (content unchanged), and files under `slices/` |
| `prompts` | object | slot name → `HEX64`: sha256 of `slices/s000-bootstrap/BOOTSTRAP.<slot>.prompt`, the exact bytes `parent` dispatched to that cloud seat. One entry per s000 cloud slot |

---

## 9. Proof log and kernel commits

### 9.1 Row schema (`slices/<id>/PROOF.jsonl`)

Every row carries every field below. Inapplicable fields are `null`.

| Field | Type | Set on |
|---|---|---|
| `seq` | int ≥ 0 | all; equals line index |
| `prev_sha256` | HEX64 | all; sha256 of the previous line's bytes without its LF; row 0: `ZERO_SHA` |
| `time` | str (§1) | all |
| `slice_id` | str | all |
| `stage` | int 0–7 | all; RULING: stage of `halt_slot` |
| `slot` | str (§5.2) | all; OPEN: `00_PROMPT.md`; MERGE/QA_EVAL: the gates-log slot; RULING: the `HALT.n.HUMAN.md` slot; SEAT_FAILED/CONTEXT_OVERFLOW: the authored slot |
| `packet_id`, `qa_round`, `round` | str / int / int | per-packet and QA slots |
| `attempt` | int 1–4 | authored slots (including SEAT_FAILED and CONTEXT_OVERFLOW) |
| `seat_id`, `family`, `model`, `runtime` | str | all; from the OPEN `roster`, never from slot text; `human` and `kernel` rows use the seat id for all four |
| `kernel_sha256`, `lock_sha256` | HEX64 | all; equal to row 0 |
| `base_commit` | commit id | OPEN: resolved `base_ref`; job rows: commit the job's view was rendered at (§10.3); MERGE: slice head before apply |
| `prompt_sha256` | HEX64 | authored rows and CONTEXT_OVERFLOW |
| `prompt_source` | `kernel` \| `bootstrap` | when `prompt_sha256` is set |
| `output_sha256` | HEX64 | sha256 of `slot` bytes; SEAT_FAILED: of the `.rejected` bytes, or `null` if none |
| `diff_sha256`, `gates_log_sha256` | HEX64 | CODE and MERGE rows |
| `gates` | `PASS` \| `FAIL` \| `NA` | CODE and MERGE rows (`NA` when gates did not run) |
| `numstat_loc` | int | CODE and MERGE rows |
| `manifest_paths` | list[str] | CODE and MERGE rows; paths in the diff where `is_manifest` holds (§14.6) |
| `status`, `verdict`, `blocking_count` | str / str / int | parsed trailer |
| `outcome` | `OPEN` \| `RECORDED` \| `SEAT_FAILED` \| `CONTEXT_OVERFLOW` \| `MERGED` \| `MERGE_FAILED` \| `QA_EVAL` \| `RULING` | all |
| `failure` | §9.4 enum | SEAT_FAILED, MERGE_FAILED, CONTEXT_OVERFLOW |
| `estimated_tokens` | int | CONTEXT_OVERFLOW and local authored rows |
| `cloud_run_id`, `source_ref`, `source_commit` | str / str / commit id | cloud rows |
| `qa_files` | object path → `{"packet": PKT_ID, "sha256": HEX64}` | 07 RECORDED rows (`{}` for `QA_TESTS: NONE`) |
| `qa_result`, `red_files`, `red_packets` | `GREEN`\|`RED` / list / list | QA_EVAL rows |
| `ruling`, `halt_code`, `halt_slot`, `dismissed_paths` | str / str / str / list | RULING rows |
| `ollama` | object `{done_reason, eval_count, prompt_eval_count, total_duration_ns, resident_bytes}` (values int, str, or null) | local authored rows, measured |
| `roster` | object (§9.2) | OPEN only |
| `config_sha256` | HEX64 | OPEN only: sha256 of `slice.json` |
| `bootstrap_sha256` | HEX64 | OPEN only, bootstrap slice |
| `kernel_commit` | commit id | OPEN only: HEAD of the repo when the kernel was pinned |

`HALT` is not an outcome. A HALT is derived from rows and never stored (§20 D5).

### 9.2 `roster` (OPEN row)

`{"planner": SEAT_ID, "challenger": SEAT_ID, "family_a": SEAT_ID, "family_b": SEAT_ID, "qa": [SEAT_ID, ...], "seats": {SEAT_ID: {"family": str, "model": str, "runtime": str}}}`. `seats` covers every seat named in the roster. The replay check (§11.2) uses the roster and never re-reads the lock, so a terminal slice still verifies after the lock changes.

### 9.3 Canonical line and chain

A row serializes as JSON with keys sorted by code point, separators `,` and `:` with no whitespace, non-ASCII written as UTF-8 (not escaped), integers in decimal, no floats. The file is the concatenation of `line + LF`. `parse_rows` re-serializes every row and requires byte equality, checks `seq`, checks `prev_sha256`, checks the field set and types, requires row 0 to be the only `OPEN`, and requires the file to end with LF. Any failure is `CHAIN_BROKEN`. `append_row` takes `LOCK_EX` on the proof file itself, reads the last line, assigns `seq` and `prev_sha256`, writes, flushes, fsyncs, and unlocks (salvaged from `.omarchy/omarchy.py:343-353`).

### 9.4 Failure codes

| Outcome | `failure` values |
|---|---|
| `SEAT_FAILED` | `TIMEOUT`, `DONE_REASON`, `EMPTY_RESPONSE`, `TRAILER_INVALID`, `FILE_BLOCK_INVALID`, `PATH_NOT_ALLOWED`, `PROMPT_SHA_MISMATCH`, `PACKETS_INVALID`, `QA_MAP_INVALID`, `SLOT_MISSING_IN_REF` |
| `MERGE_FAILED` | `APPLY_CONFLICT`, `LOC_LIMIT`, `DEPENDENCY_CHANGE`, `GATES_FAIL` |
| `CONTEXT_OVERFLOW` | `CONTEXT_OVERFLOW` |

### 9.5 Kernel commits

One commit per row, on `slice/<id>`, with exactly one parent. Commit `i` (counting from the OPEN commit as 0) adds row `i`, so `PROOF.jsonl` at commit `i` has exactly `i + 1` lines. The OPEN commit's parent is the OPEN row's `base_commit`. Identity: `-c user.name=omarchy-kernel -c user.email=kernel@omarchy.invalid`, with `--no-verify` and `--no-gpg-sign`. Identity is not proof.

Message: subject `chore(<slice_id>): <outcome lowercased> <slot>`, a blank line, then the trailers:

```text
Omarchy-Slice: <slice_id>
Omarchy-Slot: <slot>
Omarchy-Seat: <seat_id>
Omarchy-Seq: <seq>
Omarchy-Output-Sha256: <HEX64 or none>
```

Allowed changes per commit. Anything else is `FOREIGN_COMMIT`. `<d>` means `slices/<id>/`.

| Row outcome | Allowed changes |
|---|---|
| `OPEN` | A `<d>slice.json`, `<d>00_PROMPT.md`, `<d>PROOF.jsonl`; bootstrap also A `<d>BOOTSTRAP.json`, `<d>BOOTSTRAP.*.prompt` |
| `RECORDED` | M `<d>PROOF.jsonl`; A slot; CODE: A `.diff`, `.gates.log`; 07: A each `qa_files` path |
| `SEAT_FAILED` | M `<d>PROOF.jsonl`; A `<slot>.a<k>.rejected` iff `output_sha256` is set |
| `CONTEXT_OVERFLOW` | M `<d>PROOF.jsonl` |
| `MERGED` | M `<d>PROOF.jsonl`; A MERGE log; A/M exactly the paths of the applied diff |
| `MERGE_FAILED` | M `<d>PROOF.jsonl`; A MERGE log iff `output_sha256` is set |
| `QA_EVAL` | M `<d>PROOF.jsonl`; A EVAL log |
| `RULING` | M `<d>PROOF.jsonl`; A `HALT.n.HUMAN.md`; D each `dismissed_paths` entry |

This is the durable, trailered proof the v2 kernel lacked (`.gitignore:4`, `.omarchy/omarchy.py:426-428`; ballot N3 at `docs/GRAND_COUNCIL/v2.3.1_Test/LINUS_BALLOT.md:101-107`).

### 9.6 `kernel_sha256` and `lock_sha256`

`kernel_sha256` is computed over every regular file under `<repo>/omarchy/`, recursively, excluding any path with a `__pycache__` segment and any `*.pyc`. For each file, form the line `<sha256 of bytes><two spaces><repo path>\n`. Sort the lines by path bytes and hash their concatenation. `lock_sha256` is the sha256 of `agents.lock` bytes. Both are pinned in the OPEN row. `open` refuses with `KERNEL_DIRTY` if `git status --porcelain -- omarchy agents.lock` in the repo is non-empty, so the pinned kernel always equals `kernel_commit`'s tree.

---

## 10. Lineage and prompts

### 10.1 Approved chain

`Lpp` (per-packet base lineage) = `slice.json`, `00_PROMPT.md`, the approved plan revision, and its approval (the approving `02_CHALLENGE.rN.md`, or the `HALT.n.HUMAN.md` carrying `APPROVE_OVERRIDE` at `PLAN_DEADLOCK`), then `03_PACKETS.json`. Superseded plan revisions and their challenges are excluded for local seats (§20 D6).

### 10.2 Lineage table

Lineage slots are listed in render order. "Per-packet order" for packet `p` in QA round `q` is: `04.A`, `04.B`, `05.A_ON_B`, `05.B_ON_A`, `SYNTH.r1` (+`.gates.log`), `REVIEW.r1`, `MERGE.r1.gates.log`, `SYNTH.r2` (+`.gates.log`), `REVIEW.r2`, `MERGE.r2.gates.log`. Absent slots are skipped.

| Job slot | Lineage slots | Repo files |
|---|---|---|
| `01_PLAN.r1` | `slice.json`, `00_PROMPT.md` | cloud read list: `context_files`, `review_files` |
| `01_PLAN.r2` | above + `01_PLAN.r1`, `02_CHALLENGE.r1` | same |
| `02_CHALLENGE.rN` | `slice.json`, `00_PROMPT.md`, every `01`/`02` slot before it, then `01_PLAN.rN` | cloud: same read list; local challenger: `context_files` inlined at the OPEN `base_commit` |
| `03_PACKETS.json` | `slice.json`, `00_PROMPT.md`, every `01`/`02` slot, every `HALT.*.HUMAN.md` | cloud read list as above |
| per-packet local job (stages 4–6) in round `q` | `Lpp`; if `q = 2`: every `07_QA.q1.<seat>.md` and the `07_QA.q1.EVAL.k.gates.log` that opened round 2; then every slot of `p` in round `q` that precedes the job in per-packet order, excluding `.diff` files, and for a stage-5 job excluding the other stage-5 slot (`P:433`) | rendered at `B_q`: `target_files(p)`, `context_files(p)`, slice `context_files`, and if `q = 2` the red QA files mapped to `p` |
| `07_QA.q{q}.<seat>` | every slot except other seats' `07_QA.q{q}.*`, `.rejected` files, and `BOOTSTRAP.*`, including `.diff` files | cloud read list: every packet's targets and context, slice `context_files`, `review_files`, `tests/qa/<id>/**` |

Sibling packets' slots are never lineage of a per-packet local job (`P:433`).

### 10.3 Render commit `B_q`

`B_1` is the commit of the `03_PACKETS.json` RECORDED row. `B_2` is the commit of the RED `QA_EVAL` row that opened round 2. Every per-packet local job in round `q` renders repo files at `B_q`, including SYNTH, which applies its blocks in a worktree at the current slice head. The two agree on target content: targets are disjoint, a packet's targets change only through that packet's MERGE, and no MERGE of `p` precedes a round of `p` in the same `q`. Rendering at `B_q` makes every local prompt a function of the slice history alone, so `verify` can regenerate it.

### 10.4 Rendering

```text
=== LINEAGE BEGIN ===
--- SLOT slices/<id>/<name> sha256=<hex> lines=<n> ---
<each line as: line number right-aligned in 6 columns, then "|", then the line text>
--- REPO <path> @ <first 12 hex of render commit> sha256=<hex> lines=<n> ---
<numbered lines>
--- REPO <path> @ <12 hex> ABSENT ---
=== LINEAGE END ===
```

Whole files only, never excerpts. Attempt 1's excerpts without line numbers produced citations about 12 lines off and 11 `UNKNOWN` rows (`P:90`; `.omarchy/omarchy.py:521-523` inlined raw text). A non-UTF-8 repo file renders as `--- REPO <path> @ <12 hex> BINARY sha256=<hex> ---` with no body.

### 10.5 Budget (local jobs only)

`estimated = ⌈len(prompt) / 3.5⌉ + reserve`. `len` counts code points; 3.5 is `UNMEASURED` (`P:435`). `reserve = 4096` for VERDICT jobs. For CODE jobs, `reserve = 4096 + ⌈1.3 × T / 3.5⌉`, where `T` is the total character count of the packet's target files at `B_q` (§20 D7). If `estimated > num_ctx`, `run` writes a `CONTEXT_OVERFLOW` row with `estimated_tokens` and calls no model. Nothing is ever truncated.

### 10.6 Prompt composition

Templates are `string.Template` files under `omarchy/prompts/`, substituted with `substitute()` (a missing key is fatal). The only placeholders are `$slice_id`, `$slot`, `$seat_id`, `$stage`, `$packet_block`, `$delivery`.

- `$packet_block`: for per-packet jobs, the packet's `packet_id`, `title`, `plan_section`, `instructions`, `acceptance` (one per line, prefixed `- `), `target_files`, and `verification_commands` (shell-quoted with `shlex.join`), each under a `### <key>` heading. Otherwise the empty string.
- `$delivery`, cloud: "Check out branch `slice/<id>`. Write exactly `slices/<id>/<slot>`" (and, for QA, "and new test files under `tests/qa/<id>/` named per the rule below"). "Commit with message `docs(<id>): <seat> <slot>`, push, and report the branch." Local: "Respond with the document only. The kernel stores your response verbatim."
- Local prompt bytes: `family_a.md` or `family_b.md` (persona), LF LF, substituted stage template, LF LF, the lineage block (§10.4), LF LF, `output_contract(...)`, LF.
- Cloud prompt bytes: substituted stage template, LF LF, read list, LF LF, `output_contract(...)`, LF. The read list is `=== READ LIST BEGIN ===`, then `branch: slice/<id>`, then one `SLOT slices/<id>/<name> sha256=<hex>` line per lineage slot, then one `REPO <path>` line per repo file, then `=== READ LIST END ===`. It contains no slice-head commit id, so it does not change when unrelated slots land (§20 D6, T-R7).
- `output_contract` is generated from the §7 tables, so the trailer grammar a seat sees can never drift from the parser. In attempt 1, parent wrote the trailer enum and qweny emitted `COMPLETE` (`docs/GRAND_COUNCIL/v2.3.1_Test/QWENY_AUDIT_WORKSHEET.md:141`).

### 10.7 Prompt sha

`prompt_sha256 = sha256(prompt bytes)`. `omarchy prompt` prints the prompt bytes followed by one extra line, `OMARCHY_PROMPT_SHA256 value: <hex>`, which is not part of the hashed bytes. Cloud seats echo that value in their trailer (`P:404`). For bootstrap slots the prompt bytes are the stored `BOOTSTRAP.<slot>.prompt` file and `prompt_source = bootstrap`. This shows the seat received the canonical prompt. It does not prove nothing was appended (`P:404`).

---

## 11. State machine

### 11.1 Inputs

`machine.next_step(view)` is pure (`P:603`). `report.load_view` builds the view: parse `PROOF.jsonl` at the slice tip, list the commits from the OPEN commit to the tip, list the tip files under `slices/<id>/` and `tests/qa/<id>/` with their shas, parse `slice.json` structurally, parse `03_PACKETS.json` if present, parse `BOOTSTRAP.json` if present, and compute the running `kernel_sha256` and lock. `load_view(n_rows=k)` produces the view as it was after row `k-1`, for prompt regeneration.

### 11.2 Integrity checks (in this order; the first failure is `REFUSE <code> <subject>`)

| # | Code | Check |
|---|---|---|
| 1 | `NOT_OPEN` | Branch `slice/<id>` missing, or zero rows |
| 2 | `CHAIN_BROKEN` | §9.3 |
| 3 | `FOREIGN_COMMIT` | Commit count ≠ row count; a commit with ≠ 1 parent; first commit's parent ≠ row 0 `base_commit`; missing or mismatched trailers (slice, slot, seat, seq, output sha); `proof_lines ≠ i + 1`; a change outside §9.5's allowed set |
| 4 | `SLOT_SHA_MISMATCH` | Any file a row names (slot, `.diff`, `.gates.log`, `.rejected`, `qa_files` path not later dismissed) is missing at the tip or has a different sha; `slice.json` ≠ `config_sha256`; `00_PROMPT.md` ≠ row 0 `output_sha256` |
| 5 | `UNKNOWN_SLOT_FILE` | A tip file under `slices/<id>/` fails `SLOT` or is named by no row; a tip file under `tests/qa/<id>/` is in no `qa_files` (or was dismissed) |
| 6 | replay | For each row `i ≥ 1`, against `runnable(view, i)` and `derive(view, i)`, in this order: `DUPLICATE_SLOT` (a `RECORDED`, `MERGED`, or `QA_EVAL` row already exists for this slot); `SAME_FAMILY_CRITIQUE` (a VERDICT row on `05`/`06 REVIEW` whose `family` equals the family of the reviewed slot's RECORDED row: `A_ON_B` reviews `04.B`, `B_ON_A` reviews `04.A`, `REVIEW.rN` reviews `SYNTH.rN`; `P:103`); `WRONG_SEAT_FOR_SLOT` (the row's slot is runnable but the row's `seat_id`, `family`, `model`, or `runtime` differs from the job's roster seat); `OUT_OF_ORDER` (the slot is not runnable, the attempt number differs, or a RULING row does not match the derived HALT code and slot, or is illegal for it) |
| 7 | `KERNEL_CHANGED` / `LOCK_CHANGED` | A row's `kernel_sha256` or `lock_sha256` differs from row 0 (always checked). The running kernel or lock sha differs from row 0, checked only when `derive(view, N)` is non-terminal (§20 D8) |
| 8 | `ILLEGAL_CONFIG` | Non-terminal only: `check_config_legal(cfg, running_lock)` fails, or the roster no longer matches the running lock |

Terminal means `DONE`, `DONE_BOOTSTRAP`, or `HALT ABORTED`.

### 11.3 Helper: `want(S, seat)`

For an authored slot `S` with expected seat `seat`: if `S` has a `RECORDED` row, it is satisfied. Else, if a `CONTEXT_OVERFLOW` row exists for `S`, the result is `HALT CONTEXT_OVERFLOW S`. Else let `k` be the number of `SEAT_FAILED` rows for `S` and `budget = 2 + 2 × (number of RETRY rulings with halt_slot S)`. If `k ≥ budget`, the result is `HALT SEAT_FAILED S`. Else it yields a job for `S` with `attempt = k + 1`, of kind `CLOUD` or `LOCAL` by the seat's runtime (`P:503-504`).

### 11.4 Transition rules (evaluated in order; the first that yields a result ends evaluation)

| # | Condition | Result |
|---|---|---|
| T1 | No rows | `REFUSE NOT_OPEN` |
| T2 | Any `RULING` row with `ruling = ABORT` | `HALT ABORTED <that ruling slot>` |
| T3 | `want(01_PLAN.r1, planner)` not satisfied | its job or HALT |
| T4 | Let `n = 2` if `01_PLAN.r2` is RECORDED, else `1`. `status(01_PLAN.rn) ≠ READY` | `HALT PLAN_NEEDS_INPUT 01_PLAN.rn.md` |
| T5 | `want(02_CHALLENGE.rn, challenger)` not satisfied | its job (CLOUD, or LOCAL for a Family A challenger) or HALT |
| T6 | verdict(`02.rn`) = `REJECT` | `HALT PLAN_REJECTED 02_CHALLENGE.rn.md` |
| T7 | verdict = `REQUEST_CHANGES`, `n = 1` | `want(01_PLAN.r2, planner)`'s job or HALT |
| T8 | verdict = `REQUEST_CHANGES`, `n = 2`, no `APPROVE_OVERRIDE` ruling with `halt_slot = 02_CHALLENGE.r2.md` | `HALT PLAN_DEADLOCK 02_CHALLENGE.r2.md` |
| T9 | (approved plan is `01_PLAN.rn`.) Bootstrap slice (row 0 `bootstrap_sha256` set) | `DONE_BOOTSTRAP` |
| T10 | `want(03_PACKETS.json, planner)` not satisfied | its job or HALT |
| T11 | Set `q = 1`, `active` = all packets. For each `p` in `active` (ascending), compute `PS(p, q)` by §11.5 | — |
| T12 | Some `PS` is HALT | the HALT of the lowest packet id (HALT dominates) |
| T13 | Some `PS` has jobs; any KERNEL job among them | `NEXT KERNEL` with only the lowest packet's kernel job |
| T14 | Some `PS` has jobs | `NEXT LOCAL` with all local jobs, ordered by (stage, packet id, slot) |
| T15 | All `PS` DONE. For each QA seat (in `qa_seats` order): `want(07_QA.q{q}.<seat>.md, seat)` | `NEXT CLOUD` with all pending QA jobs, or the first HALT |
| T16 | Let `E` be the latest `QA_EVAL` row with `qa_round = q`. If there is none, or a `DISMISS_QA_TEST` ruling with `halt_slot = E.slot` exists after it | `NEXT KERNEL qa_eval 07_QA.q{q}.EVAL.{k}.gates.log`, where `k` = 1 + count of `QA_EVAL` rows for `q` |
| T17 | `E.qa_result = GREEN` | `DONE` |
| T18 | `E` RED, `q = 1`, `E.red_packets` non-empty | set `q = 2`, `active = E.red_packets`, `B_2` = commit of `E`; re-evaluate from T11 |
| T19 | `E` RED otherwise | `HALT QA_RED <E.slot>` |

`runnable(view, i)` returns the full job set behind T13–T15 (all kinds, before the T13 priority filter), so the replay check accepts a row for any runnable job.

### 11.5 Per-packet state `PS(p, q)` → `DONE` | jobs | HALT

Evaluate in order. A step that yields jobs adds them and stops, except step 1, which collects both proposals.

1. `want(04_p.qq.A.md, family_a)` and `want(04_p.qq.B.md, family_b)`. Collect the jobs of both. A HALT from either is returned.
2. If both are RECORDED and either status is not `READY`, return `HALT PROPOSAL_NEEDS_PLAN` on the first such slot in A, B order.
3. `want(05_p.qq.A_ON_B.md, family_a)` and `want(05_p.qq.B_ON_A.md, family_b)`; collect both.
4. For `r = 1, 2`:
   1. `want(06_p.qq.SYNTH.rr.md, family_a)`. Status ≠ `READY` → `HALT PROPOSAL_NEEDS_PLAN`.
   2. SYNTH `manifest_paths` non-empty and no `APPROVE_DEPENDENCY` ruling with `halt_slot` = that SYNTH slot → `HALT DEPENDENCY_CHANGE <SYNTH slot>` (§20 D9).
   3. `want(06_p.qq.REVIEW.rr.md, family_b)`. Verdict `REJECT` → `HALT SYNTH_REJECTED <REVIEW slot>`.
   4. `mergeable` := (verdict `APPROVE` ∧ SYNTH `gates = PASS` ∧ SYNTH `numstat_loc ≤ 300`) ∨ (`r = 2` ∧ an `APPROVE_OVERRIDE` ruling with `halt_slot = 06_p.qq.REVIEW.r2.md` exists).
   5. If `mergeable`: if `06_p.qq.MERGE.rr.gates.log` has no row, yield the job `KERNEL merge`. If its row is `MERGED`, return `DONE`. If it is `MERGE_FAILED`, the round failed with class `TESTS` for `GATES_FAIL`, else class `BLOCKED`.
   6. If not `mergeable`, the round failed with class `TESTS` if SYNTH gates `FAIL`, else `BLOCKED` if `numstat_loc > 300`, else `REVIEW`.
   7. Round failed and `r = 1`: continue with `r = 2`. Round failed and `r = 2`: return `HALT TESTS_RED` (class `TESTS`), `HALT MERGE_BLOCKED` (class `BLOCKED`), or `HALT SYNTH_DEADLOCK` (class `REVIEW`). The subject is the MERGE log slot if a MERGE row exists, else the REVIEW slot (§20 D10).

### 11.6 Output grammar and exit codes

`next` prints exactly one category on stdout. Each line matches one of:

```text
NEXT (CLOUD|LOCAL) <SEAT_ID> <slot> a[1-4]           one line per job, all of the same kind
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

Other exits, all commands: 1 kernel error, 2 git error, 64 usage, 66 `run` found nothing runnable locally (§13.5).

### 11.7 `STAGES`

A tuple of 8 rows `(stage, slot_pattern, author_cap, runtime)`. This is the table `01_OMARCHY_AGENT_PROMPTS.md` must reproduce (T-D3):

| Stage | Slot | Author cap | Runtime |
|---|---|---|---|
| 0 | `slice.json`, `00_PROMPT.md` | human | human |
| 1 | `01_PLAN.r{n}.md` | plan | cloud |
| 2 | `02_CHALLENGE.r{n}.md` | challenge | cloud or local_family_a |
| 3 | `03_PACKETS.json` | plan | cloud |
| 4 | `04_<pkt>.q{q}.{A,B}.md` | propose | local |
| 5 | `05_<pkt>.q{q}.{A_ON_B,B_ON_A}.md` | critique | local |
| 6 | `06_<pkt>.q{q}.{SYNTH,REVIEW,MERGE}.r{n}` | synthesize, review, kernel | local, kernel |
| 7 | `07_QA.q{q}.{<seat>,EVAL.<k>}` | qa, kernel | cloud, kernel |

---

## 12. HALT codes and human rulings

| HALT code | Arises at | Legal rulings besides `ABORT` | Effect |
|---|---|---|---|
| `PLAN_NEEDS_INPUT` | T4 | none | — |
| `PLAN_REJECTED` | T6 | none | — |
| `PLAN_DEADLOCK` | T8 | `APPROVE_OVERRIDE` | `01_PLAN.r2` approved; T9/T10 next |
| `PROPOSAL_NEEDS_PLAN` | §11.5 steps 2 and 4.1 | none | — |
| `DEPENDENCY_CHANGE` | §11.5 step 4.2 | `APPROVE_DEPENDENCY` | REVIEW job next; the merge accepts those manifest paths |
| `SYNTH_REJECTED` | §11.5 step 4.3 | none | — |
| `SYNTH_DEADLOCK` | §11.5 step 4.7 | `APPROVE_OVERRIDE` | r2 merge job next |
| `TESTS_RED` | §11.5 step 4.7 | none | tests cannot be overridden (`P:515`) |
| `MERGE_BLOCKED` | §11.5 step 4.7 | none | human splits the work into a new slice (`P:755`) |
| `QA_RED` | T19 | `DISMISS_QA_TEST` | listed tests deleted in the ruling commit; a new `qa_eval` next (T16) |
| `SEAT_FAILED` | §11.3 | `RETRY`, at most once per slot | attempt budget becomes 4 |
| `CONTEXT_OVERFLOW` | §11.3 | none | — |
| `ABORTED` | T2 | none (terminal) | a new slice may cite it (`P:506`) |

`ABORT` is legal at every HALT except `ABORTED`. `legal_rulings(step)` returns exactly this table's set.

---

## 13. Commands

Every mutating command (`open`, `record`, `run`, `rule`) does the following, in this order: take `slice_lock`, then (except `open`) `check_clean` on the slice worktree and integrity via `next_step`. It does all work, and immediately before each commit or fast-forward it re-checks that the slice worktree is clean and its head is the expected commit. This places the precondition checks before the expensive step (ballot N4, `.omarchy/omarchy.py:437-461`).

Precondition refusal codes (`REFUSE`, exit 65): `NOT_OPEN`, `ALREADY_OPEN`, `SLICE_BUSY`, `DIRTY_WORKTREE`, `WRONG_BRANCH`, `KERNEL_DIRTY`, `SLICE_DIR_INVALID`, `BOOTSTRAP_MISMATCH`, `ILLEGAL_CONFIG`, `ILLEGAL_LOCK`, `NOT_EXPECTED_SLOT`, `NOT_CLOUD_JOB`, `MISSING_RUN_ID`, `REF_NOT_FOUND`, `LINEAGE_MISMATCH`, `ILLEGAL_RULING`, `NO_TTY`, `PROMPT_SHA_MISMATCH` (`verify` only).

### 13.1 `omarchy open <slice_id> [--bootstrap]`

1. `<repo>/slices/<id>/` exists. Every file in it matches `SLOT`, else `SLICE_DIR_INVALID`. It contains `slice.json` and `00_PROMPT.md` (non-empty, valid UTF-8, no CR). Other slot-grammar files are ignored and not copied.
2. `slice/<id>` does not exist (else `ALREADY_OPEN`). The kernel is not dirty (§9.6). The lock parses.
3. Parse `slice.json`; `check_config_legal`; `base_ref` resolves; every `context_files` and `review_files` path exists at `base_ref`.
4. `--bootstrap` is legal only if `BOOTSTRAP.json` is present and parses, `slice_id` matches, every `files[path].sha256` equals the blob at repo `HEAD`, and every `prompts` entry has its `BOOTSTRAP.<slot>.prompt` file with that sha. Else `BOOTSTRAP_MISMATCH`. Without `--bootstrap`, the presence of `BOOTSTRAP.json` is `SLICE_DIR_INVALID`.
5. Create branch `slice/<id>` at the `base_ref` commit and the worktree `.omarchy/worktrees/<id>/slice`. Copy the input files (plus bootstrap files if bootstrapping). Append the OPEN row (seat `human`, roster, pins, `kernel_commit`, `config_sha256`, `bootstrap_sha256`). Commit.

### 13.2 `omarchy next <slice_id>`

Read-only: no writes, no network, no model. Prints per §11.6. This is the only dry path (`P:111`).

### 13.3 `omarchy prompt <slice_id> <slot>`

If `slot` is a runnable authored job, build its prompt from the current view. If `slot` has a row, build it from `load_view(n_rows = seq of that row)`. Else `NOT_EXPECTED_SLOT`. Print per §10.7.

### 13.4 `omarchy record <slice_id> --slot S --seat X --ref R --cloud-run ID`

Operator errors refuse without writing a row:

- `S` must be a current CLOUD job (`NOT_EXPECTED_SLOT`). If its seat is local, the refusal is `NOT_CLOUD_JOB`.
- `X` must equal the job's seat (`WRONG_SEAT_FOR_SLOT`).
- `ID` must match `[A-Za-z0-9._:-]{1,128}` (`MISSING_RUN_ID`).
- `R` must resolve with `git rev-parse --verify R^{commit}` (`REF_NOT_FOUND`). The kernel never fetches or pushes; `parent` fetches first.
- Lineage at ref: every lineage slot of `S` (§10.2) exists at `R` with the recorded sha (`LINEAGE_MISMATCH`). This proves the seat's tree held the canonical inputs.

Content checks write a `SEAT_FAILED` row (counting toward the attempt budget), store `<S>.a<k>.rejected` when slot bytes exist, print `SEAT_FAILED <failure> <S> a<k>`, and exit 65 (§20 D11):

1. Let `H` = slice head and `D = merge-base(R, H)`. For every path `x` in `git diff --name-only H R`: if `ingest_allowed(S, x)`, take it. Else, if the blob of `x` at `R` equals its blob at `D` (or both are absent), ignore it as slice progress the seat never touched. Else fail with `PATH_NOT_ALLOWED`. `ingest_allowed` permits `slices/<id>/<S>`, and for `07` slots new files only under `tests/qa/<id>/` satisfying §5.2. Changing an existing QA file is `PATH_NOT_ALLOWED`. This rule replaces the merge-base equality check (§20 D12).
2. The slot file is absent at `R` → `SLOT_MISSING_IN_REF`.
3. Parse per class (cloud). Check `OMARCHY_PROMPT_SHA256` against §10.7 (`PROMPT_SHA_MISMATCH`). For `01`: PLAN_FILES grammar. For `03`: `parse_packets` with the approved plan's sha and `PLAN_FILES`. For `07`: `QA_TESTS` against the added files.
4. Success: write the slot bytes exactly as in `R` and the QA files, append a `RECORDED` row (`cloud_run_id`, `source_ref = R`, `source_commit`, parsed fields, `qa_files`), commit, and print `RECORDED <S>`. Exit 0.

### 13.5 `omarchy run <slice_id>`

1. Preconditions as above. If the first step is not `NEXT LOCAL` or `NEXT KERNEL`, print it and exit with its category code, or 66 when it is `NEXT CLOUD` (T-R2).
2. If any LOCAL job is runnable, `ollama.sweep(client)` (K7).
3. Loop: compute the step. For `KERNEL`, execute it (§14.5, §14.7). For `LOCAL`, choose family `F`: the resident family if it has jobs, else `local_family_a` if it has jobs, else `local_family_b`. Open `family_session(F)`. Inside it, repeat: execute the first `F` job in the step order (§11.4 T14); recompute; execute any KERNEL job that became runnable; continue while the step has `F` jobs; exit the session otherwise. Any other step ends the loop: print it and exit with its code (0 for `NEXT CLOUD` after work was done).
4. Local job execution:
   1. Build the prompt; compute `estimated_tokens`. Overflow → commit a `CONTEXT_OVERFLOW` row; continue.
   2. `session.generate`. A timeout is `SEAT_FAILED TIMEOUT`. `done_reason ≠ "stop"` is `SEAT_FAILED DONE_REASON`, with bytes kept. An empty or whitespace-only response is `EMPTY_RESPONSE`.
   3. `parse_slot` (local). A defect gives a `SEAT_FAILED` row and a `.rejected` file.
   4. CODE: in a `TempWorktree` at `B_q` (stage 4) or the slice head (SYNTH), `write_blocks`, `stage_diff`, then `run_gates` (§14.4). Store `.md`, `.diff`, `.gates.log`.
   5. Append the `RECORDED` row (`ollama` stats, `estimated_tokens`) and commit.
5. Ollama transport errors (connection refused, non-200) raise `OmarchyError`. They write no row and exit 1; infrastructure failure never consumes a seat attempt (§20 D11).

### 13.6 `omarchy rule <slice_id> --ruling R --reason TEXT [--paths a,b]`

The current step must be HALT and `R` legal for it, with `--paths` only for `DISMISS_QA_TEST` (non-empty, existing QA files), else `ILLEGAL_RULING`. The kernel opens `/dev/tty` (absent → `NO_TTY`), prints the HALT line and the ruling, and requires the operator to type the slice id exactly. Then it renders `HALT.<n>.HUMAN.md` with `render_ruling`, where `n` = 1 + the number of RULING rows, and the body states the HALT line and the reason. It deletes the dismissed paths, appends a `RULING` row (seat `human`), and commits (§20 D13). The TTY check is friction, not authentication; the host can still forge it (`P:756`).

### 13.7 `omarchy verify <slice_id>`

Run §11.2. Then, if the slice is non-terminal or its pins still hold, regenerate every row's prompt with `prompt_source = kernel` from `load_view(n_rows = seq)` and compare it to `prompt_sha256` (`PROMPT_SHA_MISMATCH`). Print `VERIFIED <id> rows=<n> <step line>`. Exit 0 or 65.

### 13.8 `omarchy verify --repo`

Verify every `slice/*` branch. Then, for `slices/s000-bootstrap/BOOTSTRAP.json` at repo HEAD, print one line per file, `<label>\t<path>`. Labels are evaluated in order:

1. `pipeline-authored by <S>`: the file's last commit on HEAD's first-parent history is a merge of a slice `S` whose step is DONE, and `S`'s MERGED rows touched the file.
2. `parent-authored, pipeline-reviewed by <S>`: the HEAD blob equals the BOOTSTRAP sha, and a DONE slice `S` lists the file in its `context_files`, its `review_files`, or any packet's `target_files` or `context_files`.
3. `parent-authored, unreviewed`: the HEAD blob equals the BOOTSTRAP sha.
4. `FOREIGN_EDIT`: anything else.

Exit 65 if any slice fails verification or any line is `FOREIGN_EDIT`, else 0 (`P:717`).

### 13.9 `omarchy status [--markdown] [--tokens]`

One line per `slice/*` branch: `<slice_id>\t<step line>\t<rows>\t<last outcome>\t<last time>`. `--markdown` renders the same columns as a markdown table; this replaces `docs/SPRINT_DASHBOARD.md`. `--tokens` adds a per-seat table: `seat`, `runtime`, `rows`, Σ`eval_count`, Σ`prompt_eval_count`, Σ`total_duration_ns`/1e9 s, from local rows, plus cloud row counts with tokens `UNMEASURED`. This replaces `scripts/report_token_split.sh`, which always reports zero local work (`scripts/report_token_split.sh:48`).

### 13.10 `omarchy smoke`

For Family A then Family B: open a `family_session`, send `prompts/smoke.md`, and parse as CODE with allowed path `smoke/hello.txt`. Print one canonical JSON line per family: `{"family", "model", "parse_ok", "failure", "done_reason", "eval_count", "prompt_eval_count", "total_duration_ns", "resident_bytes"}`. Write nothing to the repo. Exit 0 iff both parse.

### 13.11 `omarchy lock [--check | --local-models | --check-pulled]`

- `--check` (the default): parse; print `LOCK_OK <lock_sha256>`.
- `--local-models`: print `<family> <model>` per local seat.
- `--check-pulled`: query `/api/tags` and print `PULLED <model> <bytes>` or `MISSING <model>` per local model, using `match_model`, the same matcher as the budget guard. Exit 0 iff every model is pulled. This removes the disagreement between `scripts/ensure_local_agents.sh:41` (exact match) and `.omarchy/omarchy.py:573` (prefix match).

---

## 14. Worktrees, gates, and merge

### 14.1 Paths

| Worktree | Path | Branch | Base | Lifetime |
|---|---|---|---|---|
| slice | `.omarchy/worktrees/<id>/slice` | `slice/<id>` | `base_ref` | permanent |
| proposal | `.omarchy/worktrees/<id>/<pkt>.q<q>.<A\|B>` | `omarchy/<id>/<pkt>/q<q>/<A\|B>` | `B_q` | one job |
| synthesis | `.omarchy/worktrees/<id>/<pkt>.q<q>.SYNTH.r<r>` | `omarchy/<id>/<pkt>/q<q>/synth-r<r>` | slice head | one job |
| merge | `.omarchy/worktrees/<id>/merge` | `omarchy/<id>/merge` | slice head | one merge |
| QA eval | `.omarchy/worktrees/<id>/qa` | `omarchy/<id>/qa` | slice head | one eval |

`TempWorktree` runs `git worktree add -B <branch> <path> <base>`. On exit, success or exception, it runs `git worktree remove --force <path>`, removes the directory if it remains, and runs `git branch -D <branch>` (salvaged from `.omarchy/omarchy.py:474-497`). The kernel never touches `main` or the human's checkout (`P:125`).

### 14.2 Block writes

Write each block to `<wt>/<path>` after sterilization against `<wt>`. Create parent directories. A symlink at any component is `PATH_NOT_ALLOWED`. Mode 0644. Content is written exactly (§7.4); v2 appended a newline only when one was missing (`.omarchy/omarchy.py:713-714`).

### 14.3 Diff before gates

Run `git add -- <block paths>`. The diff is `git diff --cached --binary --full-index --no-color --no-ext-diff --no-renames`, and `numstat_loc` comes from `git diff --cached --numstat --no-renames`. Both are computed **before** gates run, so files the gates create never enter the diff. v2 hashed `git add -A` after gates (`.omarchy/omarchy.py:416-424` after `:808`).

### 14.4 Gates

The command list is the packet's `verification_commands`, then (in round 2) `python3 -m pytest -q -p no:cacheprovider <file>` for each red QA file mapped to the packet, then `test_command`. Each runs as argv (`.omarchy/omarchy.py:322-333`) with cwd at the worktree root, stdin `/dev/null`, the inherited environment plus `PYTHONDONTWRITEBYTECODE=1`, and a 1800 s timeout (`UNMEASURED`). **All** commands run, even after a failure. The log is bytes. For each command: `$ <shlex.join(argv)>` LF, `exit=<int|TIMEOUT>` LF, `--- stdout ---` LF, the raw stdout, LF, `--- stderr ---` LF, the raw stderr, LF. The log ends with `GATES: PASS` or `GATES: FAIL` and LF. `PASS` iff every exit is 0. Stage 4 gates are recorded and never block (`P:239`).

### 14.5 Merge (stage 6 commit phase)

The two-phase commit: prepare is SYNTH (gated, recorded), vote is REVIEW, and commit is this kernel job.

1. Re-check the slice worktree is clean, and note `H` = head.
2. `TempWorktree(merge, H)`. Verify `sha256(SYNTH .diff) = diff_sha256`. Apply with `git apply --index --binary --whitespace=nowarn` from stdin. Failure is `MERGE_FAILED APPLY_CONFLICT` (§20 D14).
3. Numstat of the applied index > 300 → `LOC_LIMIT` (ballot N11, `docs/GRAND_COUNCIL/v2.3.1_Test/LINUS_BALLOT.md:171-173`). Applied manifest paths not covered by an `APPROVE_DEPENDENCY` ruling → `DEPENDENCY_CHANGE`.
4. Gates per §14.4. `FAIL` → `GATES_FAIL`.
5. Pass: in the merge worktree, write the MERGE log, append the `MERGED` row, and commit (code, log, and row together). Then `fast_forward(slice_wt, omarchy/<id>/merge, expected_head = H)`.
6. Fail: commit the log (if gates ran) and the `MERGE_FAILED` row on the slice worktree. A commit-phase failure is a failed round (§11.5).

### 14.6 Dependency manifests

`is_manifest(path)` is true iff the basename matches:

```text
pyproject\.toml|setup\.py|setup\.cfg|requirements[^/]*\.txt|Pipfile(?:\.lock)?|poetry\.lock|uv\.lock|package(?:-lock)?\.json|yarn\.lock|pnpm-lock\.yaml|Cargo\.(?:toml|lock)|go\.(?:mod|sum)|Gemfile(?:\.lock)?|build\.gradle(?:\.kts)?|settings\.gradle(?:\.kts)?|gradle\.properties
```

### 14.7 QA evaluation (kernel action)

In `TempWorktree(qa, head)`, run `test_command`, then for every file under `tests/qa/<id>/` (sorted) `python3 -m pytest -q -p no:cacheprovider <file>`, with the same execution rules and log format as §14.4.

- `red_files`: the QA files with a non-zero exit.
- `red_packets`: the sorted unique packets of the red files, from the `qa_files` of the record that added each file.
- `qa_result`: `GREEN` iff every exit is 0.

Commit the EVAL log and the `QA_EVAL` row on the slice worktree. QA tests stay committed whether they pass or fail (`P:442`) (§20 D15).

---

## 15. Ollama and MLX requirements

Constants live in `omarchy/ollama.py` and are part of `kernel_sha256`. They are not environment-overridable (§20 D16). Only `OLLAMA_API_URL` (default `http://127.0.0.1:11434`, as `.omarchy/omarchy.py:37`) is read from the environment.

| ID | Requirement |
|---|---|
| K1 | The `/api/generate` payload is exactly `{"model", "prompt", "stream": false, "keep_alive": "15m", "options": {"temperature": 0, "num_ctx": <cfg.num_ctx>}}`. Never `format` (HTTP 501 on MLX; `.omarchy/omarchy.py:621-622`, commit `3b1f2c8`) |
| K2 | Outer-fence strip per §7.1 |
| K3 | File blocks per §7.4; trailer per §7.2 |
| K4 | `done_reason` must equal `"stop"`. Anything else, including missing or `"length"`, is `SEAT_FAILED DONE_REASON` with no parse attempt |
| K5 | `family_session` enter: take an exclusive non-blocking flock on `.omarchy/locks/ollama.lock` (busy → `OmarchyError`). `GET /api/ps`; unload every resident model that is not the target; poll `/api/ps` up to 10 times, 1 s apart; if any remains, raise `ResidencyError` (fail closed). Budget check (K8). The model loads lazily on the first `generate`; after each `generate`, `GET /api/ps` and record the target entry's `size` as `resident_bytes` (null if absent) (`docs/GRAND_COUNCIL/v2.3.1_Test/LINUS_BALLOT.md:70-79`) |
| K6 | `keep_alive: "15m"` exists only inside `family_session`. On exit, send `{"model", "prompt": "", "stream": false, "keep_alive": 0}` and poll `/api/ps` as in K5. On exception exit, eviction errors go to stderr and the original exception is re-raised. On normal exit, an eviction error is raised. This fixes `.omarchy/batch_runner.py:73` masking the real error via `:313-317` |
| K7 | `run` sweep: unload every model listed by `/api/ps` and verify as in K5 (SIGKILL leftovers) |
| K8 | `match_model(entries, slug)`: an entry whose `name` (or `model`) equals `slug`, or, iff `slug` has no `:`, equals `slug + ":latest"`. Never a prefix match (`.omarchy/omarchy.py:573`). Budget: `weights + num_ctx × 512 KiB + 4 GiB ≤ 105 GiB`; constants `UNMEASURED` (`.omarchy/omarchy.py:542-545`) |
| K9 | Temperature 0, determinism not assumed. Per-call HTTP timeout 3600 s → `SEAT_FAILED TIMEOUT`. One automatic retry is the second attempt in §11.3; then HALT |
| K10 | Models are only the two local lock models; any other target → `OmarchyError` (`.omarchy/omarchy.py:614-619`) |

Running both families in RAM at once is out of scope until `docs/EVIDENCE.md` shows both fit (`P:458`, `P:761`).

---

## 16. Kernel pinning for self-hosting

The kernel that runs is the repo's working tree, pinned at `open` by `kernel_sha256` and `kernel_commit`. A slice that edits kernel files changes only `slice/<id>`. The new kernel takes effect after a human merges the slice and a new slice is opened (`P:616`). Recovering from `REFUSE KERNEL_CHANGED` means checking out the OPEN row's `kernel_commit`. Attempt 1 patched the kernel mid-run twice (`docs/GRAND_COUNCIL/v2.3.1_Test/FLOW_TRACE.md:36-38`).

---

## 17. Bootstrap execution and repo surgery

### 17.1 Phase 2: kernel (parent, on `v3`)

Commit order. A test commit immediately precedes its module commit (tests first). Each commit changes ≤ 300 LOC under `omarchy/**`; a module larger than that lands across consecutive commits. Every commit carries the trailer `Omarchy-Bootstrap: parent`. Subjects are `test(s000): <file>` and `feat(s000): <module>`. `python3 -m pytest -q` is green at every `feat` commit.

1. `tests/conftest.py` (fixtures: a `tmp_path` git repo with `base` commit; fixture lock text with fake slugs; mock Ollama HTTP server on `127.0.0.1:0`), then `omarchy/__init__.py`
2. `tests/test_lock.py`, then `omarchy/lock.py`
3. `tests/test_slice_config.py`, then `omarchy/slice.py`
4. `tests/test_trailers.py`, then `omarchy/trailers.py`
5. `tests/test_proof.py`, then `omarchy/proof.py`
6. `tests/test_machine.py`, then `omarchy/machine.py`
7. `tests/test_worktree.py`, then `omarchy/worktree.py`
8. `tests/test_ollama.py`, then `omarchy/ollama.py`
9. `tests/test_report.py`, then `omarchy/report.py`
10. `tests/test_runner.py`, then `omarchy/runner.py` and `omarchy/prompts/*.md`
11. `tests/test_ingest.py`, then `omarchy/ingest.py`
12. `omarchy/__main__.py`, `scripts/omarchy`

### 17.2 Phase 3: surgery (one atomic commit `chore(s000): v3 repo surgery`, trailer `Omarchy-Bootstrap: parent`)

**Archive** (`git mv`; plan `P:220`):

| From | To |
|---|---|
| `docs/GRAND_COUNCIL/v2.3.1_Test/{FLOW_TRACE,LINUS_AUDIT_PLAN,LINUS_BALLOT,MOXIE_G4_TEST,MOXIE_G5_REVIEW,QWENY_AUDIT_WORKSHEET,SCRUM_DOD_AUDIT}.md` | `archive/v2.3.1-attempt1/council/<same name>` |
| `.omarchy/packets/aud231-{s01-build,s09-g4,s10-g5,s11-dod}.json` | `archive/v2.3.1-attempt1/packets/<same name>` |
| `.omarchy/contracts/stories/STORY-AUDIT-V231.md`, `.omarchy/contracts/use_cases/UC-AUDIT-V231-{WS,G4,G5,DOD}.md` | `archive/v2.3.1-attempt1/contracts/<same name>` |

**Delete** (reachable at tag `v2.3.1-attempt1` = `1156b29`):

- `.cursor/agents/{qweny,moxie,scrum,mitnick,jobs}.md`
- `.omarchy/omarchy.py`, `.omarchy/batch_runner.py`, `.omarchy/README.md`, `.omarchy/packets/{README.md,_sample_packet.json,pkt-01-impl.json,pkt-02-audit.json,pkt-03-optimize.json}`
- `.omarchy/contracts/stories/{STORY-101,STORY-BATCH}.md`, `.omarchy/contracts/use_cases/{UC-101-A,UC-101-B,UC-BATCH-A,UC-BATCH-B}.md`
- `02_PRODUCTION_PLAN.md`
- `docs/{DEVELOPER_GUIDE,SPRINT_DASHBOARD,PRODUCT_SPEC,OMARCHY_SCRUM_2_0_BLUEPRINT,TESTING_JIG_REPORT,GRAND_COUNCIL}.md`
- `packets/README.md`
- `scripts/{run_local_agent.sh,log_cloud_agent.sh,report_token_split.sh,omarchy.py}`
- `tests/test_omarchy_kernel.py`

**Rewrite or create**:

- `agents.lock` and `agents.lock.optional` per §3.3.
- `.gitignore`, exactly these lines: `.omarchy/worktrees/`, `.omarchy/locks/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.venv/`, `.DS_Store`, `build/`, `.gradle/`, `local.properties`.
- `AGENTS.md`: §1 the stage hemisphere matrix (`P:248-257`). §2 the seat table between `<!-- seat-table:canonical -->` and `<!-- /seat-table:canonical -->`, with columns `Seat | Group | Runtime | Family | Caps | Weight` and plain cell values. There is no model column (§20 D18). §3 the command glossary of §13.
- `01_OMARCHY_AGENT_PROMPTS.md`: the 12 v3 laws (`P:551-564`), the stage table of §11.7 between `<!-- stage-table -->` and `<!-- /stage-table -->`, and the trailer grammar of §7.
- `00_ARCHITECTURE.md`: a header line `Source: slices/s000-bootstrap/<approved plan slot> sha256=<output_sha256>`, then §1–§19 of the approved revision verbatim.
- `.cursor/rules/omarchy-council.mdc`: run `omarchy next` first; the stage hemisphere matrix; no hand edits under `slices/`; cloud seats write only plan, challenge, packet, and `tests/qa/<id>/` slots.
- `.cursor/agents/{linus,knuth,dhh,carmack}.md`: hemisphere line, owned slots, and a pointer that the kernel template owns the trailer grammar. No model slugs.
- `README.md`: entry point plus quickstart.
- `scripts/ensure_local_agents.sh`: keep the start-or-wait loop (`scripts/ensure_local_agents.sh:16-27`), then `exec "$ROOT/scripts/omarchy" lock --check-pulled`.
- `tests/test_docs_sync.py`.
- `archive/v2.3.1-attempt1/README.md`: the four interventions with commits `3b1f2c8`, `2e7414e`, `ececfcc`, `3aa8c8f` and the packet collapse (`docs/GRAND_COUNCIL/v2.3.1_Test/FLOW_TRACE.md:41-43`).
- `docs/EVIDENCE.md`: append `UNMEASURED` rows for 105 GiB, 512 KiB/token, 4 GiB headroom, chars/3.5, the 1.3 reserve factor, and the 1800 s gate timeout.
- `docs/HISTORY.md`: append rows `v2.3.1 attempt 1 archived` and `BOOTSTRAP_EXCEPTION` (`P:715`).
- `slices/s000-bootstrap/BOOTSTRAP.json` (§8) and `slices/s000-bootstrap/BOOTSTRAP.<slot>.prompt` for every s000 cloud dispatch. These are slice records, not plan files, so they are absent from `PLAN_FILES` by §7.3's grammar.

`python3 -m pytest -q` is green after this commit, including `tests/test_docs_sync.py`.

### 17.3 Phase 4: smoke and ingest (parent, then human)

1. `scripts/ensure_local_agents.sh`; `scripts/omarchy smoke`. Append measured rows to `docs/EVIDENCE.md` (date, commit, model, `resident_bytes`, `parse_ok`, durations).
2. `scripts/omarchy open s000-bootstrap --bootstrap`. The branch is created from `base_ref` `v2.3.1-attempt1` (`slices/s000-bootstrap/slice.json:5`), which lacks `slices/s000-bootstrap/`; the OPEN commit adds it.
3. For each s000 cloud slot in order: `scripts/omarchy record s000-bootstrap --slot <S> --seat <seat> --ref <seat branch> --cloud-run <bc id>`. Requirement on Phase 1 dispatch: each challenger's branch MUST contain the exact plan revision it challenged, so the lineage-at-ref check passes. Any s000 HALT rulings are entered with `omarchy rule`.
4. `scripts/omarchy next s000-bootstrap` prints `DONE_BOOTSTRAP`. `scripts/omarchy verify --repo` labels every BOOTSTRAP file `parent-authored, unreviewed`. `parent` pushes `slice/s000-bootstrap`, which is never merged.

---

## 18. Required tests

All tests run without Ollama or network. Git tests use a `tmp_path` repo; Ollama tests use the mock server from `tests/conftest.py`. Fixture locks use fake slugs. IDs are stable. "Adapted" marks a test reworded from `P:620-707`.

| ID | File | Asserts |
|---|---|---|
| T-L1 | `test_lock.py` | `schema` ≠ 3, or the schema line not first → `ILLEGAL_LOCK` |
| T-L2 | | Row with 6 or 8 fields → error (not skipped) |
| T-L3 | | Duplicate seat id → error |
| T-L4 | | Two seats in one local family → error |
| T-L5 | | Family A model equals Family B model → error |
| T-L6 | | Two cloud seats share a family → error |
| T-L7 | | Zero or two `plan` seats; planner local → error |
| T-L8 | | `synthesize` on B, or `review` on A → error |
| T-L9 | | `qa` on planner; `challenge` on Family B; `challenge` on a cloud seat with the planner's family → error |
| T-L10 | | Repo `agents.lock` satisfies all invariants (no literal slugs, no exact seat-set assertion) |
| T-L11 | | Lock-bound model resolution rejects an invented slug and a size downsize (adapted v2 `tests/test_omarchy_kernel.py:103-124`) |
| T-L12 | | Seat `human` or `kernel` in the lock; a field with surrounding whitespace; an unknown cap; a host seat other than `parent` → error |
| T-L13 | | Repo lock plus each `agents.lock.optional` row still satisfies the invariants |
| T-C1 | `test_slice_config.py` | Cloud challenger with a family different from the planner → legal |
| T-C2 | | Challenger `qweny`-shaped (Family A) seat → legal |
| T-C3 | | Family B challenger → `ILLEGAL_CONFIG` |
| T-C4 | | Challenger is the planner → `ILLEGAL_CONFIG` |
| T-C5 | | Empty `qa_seats`; QA seat is the planner; QA seat local → `ILLEGAL_CONFIG` |
| T-C6 | | Unknown key, duplicate key, or `true` as an int in `slice.json` → rejected |
| T-C7 | | `context_files` path escaping the repo, or via symlink → `SECURITY VIOLATION` refusal (adapted v2 traversal test) |
| T-C8 | | `review_files` absent → `[]`; a context or review path absent at `base_ref` → `ILLEGAL_CONFIG` |
| T-C9 | | `slice_id` ≠ directory name, or failing `SLICE_ID`; `test_command` with argv[0] `bash` → rejected |
| T-C10 | | `slices/s000-bootstrap/slice.json` parses (repo fixture) |
| T-T1 | `test_trailers.py` | Review slot missing `OMARCHY_VERDICT` → `TRAILER_INVALID` |
| T-T2 | | Duplicate key; extra key; CR byte; `KEY:value` without a space → refused |
| T-T3 | | `APPROVE` with `BLOCKING_COUNT: 2`; `REQUEST_CHANGES` or `REJECT` with 0 → refused |
| T-T4 | | `OMARCHY_STATUS: COMPLETE`; `APPROVE_WITH_FIXES` → refused |
| T-T5 | | Whole response in a json fence → parsed; inner fences in file content preserved; a two-level fence strips one level only |
| T-T6 | | File block outside `target_files` → `PATH_NOT_ALLOWED` |
| T-T7 | | File block path escaping the worktree, `..` segment, or absolute → refused |
| T-T8 | | Cloud slot `OMARCHY_PROMPT_SHA256` mismatch → `PROMPT_SHA_MISMATCH` |
| T-T9 | | `READY` proposal with zero file blocks; `NEEDS_PLAN` with blocks → refused |
| T-T10 | | Plan without `PLAN_FILES`; `READY` with `PLAN_FILES: NONE`; a path under `slices/` or `tests/qa/` → refused |
| T-T11 | | Trailing blank lines after the closing `---` accepted; body `---` lines ignored |
| T-T12 | | `QA_TESTS`: bad basename, path outside `tests/qa/<id>/`, an added file unmapped, an unknown packet → `QA_MAP_INVALID` |
| T-T13 | | `render_ruling` output parses back to the same fields under the RULING class |
| T-T14 | | Unterminated block; duplicate block path; non-UTF-8 content → `FILE_BLOCK_INVALID`; content bytes end with exactly one LF per line |
| T-T15 | | `READY` with `MISSING_SYMBOLS` ≠ `NONE`; `TOUCHED_FILES` ≠ block paths → refused |
| T-P1 | `test_proof.py` | Append and verify a chain |
| T-P2 | | Slot file edited after record → `REFUSE SLOT_SHA_MISMATCH` |
| T-P3 | | Middle row edited or deleted → `REFUSE CHAIN_BROKEN` |
| T-P4 | | Running kernel sha differs from `OPEN` on a non-terminal slice → `REFUSE KERNEL_CHANGED` |
| T-P5 | | Running lock sha differs on a non-terminal slice → `REFUSE LOCK_CHANGED` |
| T-P6 | | Two concurrent appenders under flock → chain valid |
| T-P7 | | Hand commit on `slice/<id>` without trailers → `REFUSE FOREIGN_COMMIT` |
| T-P8 | | Commit count ≠ row count; a two-parent commit; a commit touching a path outside its allowed set; a trailer seq mismatch → `FOREIGN_COMMIT` |
| T-P9 | | Non-canonical line (whitespace, unsorted keys, missing field, float) → `CHAIN_BROKEN` |
| T-P10 | | `kernel_sha256` deterministic; ignores `__pycache__`/`*.pyc`; changes when a prompt template changes |
| T-M1 | `test_machine.py` | Fresh open → `NEXT CLOUD linus 01_PLAN.r1.md a1` (planner id from fixture lock) |
| T-M2 | | Plan recorded by a non-planner seat → `REFUSE WRONG_SEAT_FOR_SLOT` |
| T-M3 | | Plan `NEEDS_PLAN` → `HALT PLAN_NEEDS_INPUT` |
| T-M4 | | Challenge by a seat other than the configured challenger → `REFUSE WRONG_SEAT_FOR_SLOT` |
| T-M5 | | `REQUEST_CHANGES` r1 → plan r2; r2 `REQUEST_CHANGES` → `HALT PLAN_DEADLOCK` |
| T-M6 | | `REJECT` r1 → `HALT PLAN_REJECTED` |
| T-M7 | | Cloud challenger → `NEXT CLOUD`; Family A challenger → `NEXT LOCAL` (both legal) |
| T-M8 | | `plan_sha256` ≠ approved revision → `PACKETS_INVALID` |
| T-M9 | | Overlapping targets; target outside `PLAN_FILES`; 6 targets; packets above `max_packets`; non-contiguous ids → `PACKETS_INVALID` |
| T-M10 | | Stage-4 proposal row from a cloud seat → `REFUSE WRONG_SEAT_FOR_SLOT` |
| T-M11 | | Only A proposals present → `NEXT LOCAL` lists the B proposals, not stage 5 |
| T-M12 | | Proposal `NEEDS_PLAN` → `HALT PROPOSAL_NEEDS_PLAN` |
| T-M13 | | `A_ON_B` authored by Family B → `REFUSE SAME_FAMILY_CRITIQUE` |
| T-M14 | | `SYNTH` authored by B → `WRONG_SEAT_FOR_SLOT`; `REVIEW` authored by A → `SAME_FAMILY_CRITIQUE` |
| T-M15 | | Gates FAIL with `APPROVE` → no merge job, `SYNTH.r2`; r2 gates FAIL → `HALT TESTS_RED` (adapted) |
| T-M16 | | Gates PASS with `REQUEST_CHANGES` r1, r2 `APPROVE` → `NEXT KERNEL merge … MERGE.r2.gates.log` (adapted) |
| T-M17 | | All packets merged → `NEXT CLOUD <qa_seat>` for each QA seat |
| T-M18 | | QA row with a `qa_files` path outside `tests/qa/<id>/` → refused |
| T-M19 | | QA red mapped to `pkt-02` → q2 proposals for `pkt-02` only; q2 red → `HALT QA_RED` |
| T-M20 | | QA green → `DONE` |
| T-M21 | | `SEAT_FAILED` attempt 1 → same job `a2`; attempt 2 → `HALT SEAT_FAILED` |
| T-M22 | | `CONTEXT_OVERFLOW` row → `HALT CONTEXT_OVERFLOW` |
| T-M23 | | `legal_rulings` equals §12 for every HALT code; `ABORT` at all but `ABORTED` (adapted) |
| T-M24 | | Stage-5 row before both stage-4 rows → `REFUSE OUT_OF_ORDER` |
| T-M25 | | Same slot recorded twice → `REFUSE DUPLICATE_SLOT` |
| T-M26 | | SYNTH with `manifest_paths: ["pyproject.toml"]` → `HALT DEPENDENCY_CHANGE` before any REVIEW job; numstat 301 → failed round (adapted) |
| T-M27 | | `next_step` is pure: identical inputs → identical output; exactly one category |
| T-M28 | | A KERNEL job pre-empts LOCAL jobs; one packet's HALT dominates other packets' jobs |
| T-M29 | | DONE slice with a changed running kernel and lock → still `DONE`, not REFUSE |
| T-M30 | | Bootstrap slice: approved plan → `DONE_BOOTSTRAP`; `03_PACKETS.json` never offered |
| T-M31 | | `APPROVE_DEPENDENCY` ruling → REVIEW job next |
| T-M32 | | r2 classes: gates FAIL → `TESTS_RED`; gates PASS with numstat 301 → `MERGE_BLOCKED`; only `REQUEST_CHANGES` → `SYNTH_DEADLOCK`; override → merge job; merge `GATES_FAIL` after override → `TESTS_RED` |
| T-M33 | | `ABORT` → `HALT ABORTED`; no legal rulings afterwards |
| T-M34 | | `DISMISS_QA_TEST` → `NEXT KERNEL qa_eval … EVAL.2.gates.log` for the same q; RED with empty `red_packets` at q1 → `HALT QA_RED` |
| T-M35 | | Packet `context_files` intersecting a sibling's targets → `PACKETS_INVALID` |
| T-M36 | | Row family or model differing from the OPEN roster → `WRONG_SEAT_FOR_SLOT` |
| T-M37 | | `RETRY` raises the budget to 4; a second `RETRY` on the same slot → `OUT_OF_ORDER` at replay, `ILLEGAL_RULING` at `rule` |
| T-O1 | `test_ollama.py` | Generate payload has exactly the K1 keys and never `format` |
| T-O2 | | `/api/ps` shows the other family resident → unload, re-poll; still resident → `ResidencyError` |
| T-O3 | | Entry `qwen3.8` does not satisfy `qwen3.8:27b-mlx`; entry `foo:latest` satisfies slug `foo`; `foo:latest:x` never (adapted) |
| T-O4 | | Job raises and eviction raises → original exception surfaces; eviction error on stderr |
| T-O5 | | Normal session → exactly one unload at exit, verified via `/api/ps` |
| T-O6 | | Model not in lock → refused |
| T-O7 | | `done_reason: "length"` → `SEAT_FAILED DONE_REASON`; stats copied into the row |
| T-O8 | | Connection refused → `OmarchyError`, no row written |
| T-O9 | | `done_reason` missing → `DONE_REASON` |
| T-O10 | | Budget over 105 GiB → refused before any load; held `ollama.lock` → refused |
| T-W1 | `test_worktree.py` | Proposal worktree and branch removed on success and on exception |
| T-W2 | | Slice head unchanged after stage 4 |
| T-W3 | | Merge applies the recorded `.diff`, re-gates, fast-forwards; a failed merge leaves head at the `MERGE_FAILED` commit with no code change (adapted) |
| T-W4 | | Dirty slice worktree → `DIRTY_WORKTREE` before any model call |
| T-W5 | | Merge after a sibling packet merged applies cleanly; a diff whose context no longer matches → `APPLY_CONFLICT` |
| T-W6 | | Files created by gates are absent from `.diff` |
| T-W7 | | All gate commands run after a failure; log format exact; timeout → `exit=TIMEOUT`, `FAIL` |
| T-I1 | `test_ingest.py` | Cloud ref changing a file outside the allow-list that differs from the merge-base → `SEAT_FAILED PATH_NOT_ALLOWED` |
| T-I2 | | `--seat` ≠ expected seat → `WRONG_SEAT_FOR_SLOT`, no row |
| T-I3 | | Recording a local job's slot → `NOT_CLOUD_JOB`, no row |
| T-I4 | | Missing or malformed `--cloud-run` → `MISSING_RUN_ID`; ref lacking a lineage slot → `LINEAGE_MISMATCH`, no row (adapted) |
| T-I5 | | Two QA seats from the same dispatch head: the second record succeeds after the first moved the head |
| T-I6 | | Bootstrap slot: trailer sha equals the `BOOTSTRAP.<slot>.prompt` sha → recorded with `prompt_source = bootstrap`; mismatch → `PROMPT_SHA_MISMATCH` |
| T-I7 | | QA ref modifying an existing `tests/qa/<id>/` file → `PATH_NOT_ALLOWED` |
| T-I8 | | `open`: `ALREADY_OPEN`, `KERNEL_DIRTY`, `SLICE_DIR_INVALID`, `BOOTSTRAP_MISMATCH` |
| T-I9 | | `rule` with no TTY → `NO_TTY`; ruling illegal for the HALT → `ILLEGAL_RULING` |
| T-I10 | | `SEAT_FAILED` record stores `<slot>.a<k>.rejected` with the row's `output_sha256` |
| T-R1 | `test_runner.py` | Prompt build is byte-deterministic; context rendered with line numbers |
| T-R2 | | `run` with a CLOUD first step → exit 66, nothing written |
| T-R3 | | Jobs grouped by family; resident family preferred; one session per family block |
| T-R4 | | Stage-5 critique prompt excludes the other critique |
| T-R5 | | CODE reserve includes target size; overflow → `CONTEXT_OVERFLOW` row and no generate call |
| T-R6 | | Local per-packet lineage excludes superseded plan revisions and `.diff` files; q2 includes `07_QA.q1.*` and mapped red QA files |
| T-R7 | | A cloud QA prompt is byte-identical before and after another QA seat's record |
| T-R8 | | Inside a session, a newly runnable KERNEL job runs and the session continues with newly runnable same-family jobs |
| T-V1 | `test_report.py` | `verify` regenerates prompt shas; a template edit on a non-terminal slice → `KERNEL_CHANGED`; a forged `prompt_sha256` → `PROMPT_SHA_MISMATCH` |
| T-V2 | | `verify --repo` produces each of the four labels |
| T-V3 | | `status --tokens` sums `eval_count` per seat from rows |
| T-D1 | `test_docs_sync.py` | The `AGENTS.md` seat table equals `agents.lock` rows on Seat, Group, Runtime, Family, Caps, Weight (adapted) |
| T-D2 | | No lock or optional-lock model slug in tracked files outside `agents.lock`, `agents.lock.optional`, `archive/**`, `slices/**`, `docs/EVIDENCE.md`, `docs/HISTORY.md` (adapted) |
| T-D3 | | The stage table in `01_OMARCHY_AGENT_PROMPTS.md` equals `machine.STAGES` |

---

## 19. Measurements and stated limits (all `UNMEASURED` until rows land in `docs/EVIDENCE.md`)

| Item | How it gets measured |
|---|---|
| File-block parse success per family | `omarchy smoke`; then the `SEAT_FAILED` rate in rows |
| `resident_bytes` per model at `num_ctx` 32768 | `/api/ps` after load, in every local row |
| 105 GiB ceiling, 512 KiB/token, 4 GiB headroom | Compare against measured `resident_bytes` |
| chars/3.5 estimate and the 1.3 CODE reserve factor | Compare against `prompt_eval_count` and `eval_count` |
| 1800 s gate timeout, 3600 s generate timeout | Gate durations and `total_duration_ns` |
| Wall clock per slice (≥ 4 loads per synthesis round, `P:458`) | `omarchy status --tokens` |

Stated limits: the chain is tamper-evident, not adversary-proof, because the host can rewrite a branch and forge rows (`P:756`). The prompt sha proves receipt of the canonical prompt, not the absence of additions. File blocks cannot delete files. `CITED_LOCATIONS` is syntax-checked only.

---

## 20. Deviations from 00_PROMPT

Each change below is structural. Anything not listed keeps the approved plan's decision.

| # | Change | Reason (evidence) |
|---|---|---|
| D1 | Adds module `omarchy/report.py` (`load_view`, `verify`, `status`), puts `lineage` in `runner.py`, adds `prompts/smoke.md`, `tests/conftest.py`, `tests/test_report.py`, and the `omarchy lock` command | The plan lists `omarchy lock --local-models` (`P:185`) but no such command (`P:462-472`). `machine.py` must stay pure (`P:603`), and `proof.py` cannot import the machine that verify needs. `smoke` (`P:472`) needs a template |
| D2 | Optional `slice.json` key `review_files` (cloud read list, counts for coverage) | s001 audits every BOOTSTRAP file (`P:721`). Putting them in `context_files` inlines them into every local prompt (`P:431`) and guarantees `CONTEXT_OVERFLOW` at 32768. `verify --repo` needs a mechanical "reviewed" rule (`P:717`) |
| D3 | `03_PACKETS.json` gains `prompt_sha256`; ids are contiguous; packet context may not intersect sibling targets; argv[0] may not be a shell | A JSON slot cannot carry a trailer, yet every cloud slot must echo the prompt sha (`P:736`). A sibling target in a packet's context is a hidden dependency (`P:123`). Argv-only gates mean nothing if argv is `sh -c` (`.omarchy/omarchy.py:322-333`) |
| D4 | Trailers: exact key sets; ruling keys `HALT_CODE`, `HALT_SLOT`, `DISMISS_PATHS`; `QA_TESTS` maps files, not test ids; `TOUCHED_FILES`/`MISSING_SYMBOLS` consistency; `PLAN_FILES` excludes `slices/` and `tests/qa/` | A ruling must name the HALT it settles, or it can be replayed against the wrong one. File-level mapping can be checked without parsing a runner's node ids. A plan file under `slices/` could never be a packet target (`P:372`) |
| D5 | `HALT` removed as a row outcome; `MERGE_FAILED` added, plus the `failure` field; reserved seat `kernel`; added row fields (§9.1) including `roster`; one commit per row | A stored HALT duplicates derived state, giving two sources of truth: the N2 resume-file failure in another form (`.omarchy/batch_runner.py:85-90`). Commit-phase failure (`P:441`) needs an outcome. Merges need an author that is neither an LLM nor `parent` |
| D6 | Local per-packet lineage carries only the approved plan chain, excludes `.diff`, renders repo files at `B_q`, and gives q2 the q1 QA reports and red tests; cloud prompts carry no head commit | `P:430` would feed superseded, contradictory revisions to 32k-context models. The plan gives q2 no QA evidence at all, though it must fix QA failures. Rendering at a moving head would make prompts unreproducible (`P:415`), and a head id in cloud prompts breaks parallel QA seats |
| D7 | CODE reserve = 4096 + ⌈1.3 × target chars / 3.5⌉ | File blocks return complete files (`P:394`). A flat 4,096 reserve (`P:435`) guarantees `done_reason: length` on any non-trivial packet |
| D8 | Pins (`KERNEL_CHANGED`, `LOCK_CHANGED`, `ILLEGAL_CONFIG`) enforced only on non-terminal slices; roster pinned in OPEN | Otherwise every DONE slice REFUSEs as soon as its own kernel change merges (`P:616`), and `status` breaks permanently |
| D9 | The dependency-manifest check runs at SYNTH record and HALTs before REVIEW; `APPROVE_DEPENDENCY` continues to REVIEW | Under first-match evaluation, row 14 (merge) precedes row 15 (manifest) (`P:493-494`), so the HALT was unreachable before merge. Checking earlier also saves a Family B load |
| D10 | Adds HALT codes `MERGE_BLOCKED` and `ABORTED`; `SYNTH_DEADLOCK` only when gates PASS and LOC ≤ 300 | Row 18 has two outcomes (`P:497`). An override on a LOC or conflict failure would merge a G2 violation; those need a split, not an override (`P:755`) |
| D11 | Cloud content defects at record time write `SEAT_FAILED` rows for every cloud slot; operator errors refuse without a row; Ollama transport errors consume no attempt | Only stage 3 had a record bound (`P:238`), so a bad cloud seat could loop forever in stages 1, 2, and 7. An Ollama outage is not a seat failure |
| D12 | Cloud ingest: lineage-at-ref plus per-path provenance replace "ref merge-base equals slice head" | With two QA seats, the first record moves the head and the second always fails `P:442`. s000's cloud branches fork from `v3`, while `slice/s000-bootstrap` forks from `1156b29`, so the check can never pass for the bootstrap |
| D13 | The kernel renders the ruling file from `omarchy rule` arguments, behind a TTY confirmation | A hand-written slot file is exactly what the plan bans (`P:265`). The TTY prompt is friction against an agent issuing rulings, and is stated as no stronger than that |
| D14 | Merge applies the recorded SYNTH `.diff` to the current head; no kept tx branch, no cherry-pick | A kept tx branch (`P:441`) is unrecorded mutable state outside the proof, exactly the N2 class. The `.diff` is already hashed in the row, and disjoint targets make it apply cleanly |
| D15 | QA evaluation runs `test_command`, then pytest per QA file; QA file naming rule; `07_QA.q{q}.EVAL.{k}.gates.log` slot | Red-to-packet mapping needs per-file results. pytest's default import mode breaks on duplicate basenames across `tests/qa/*`. The evaluation log needs a slot to be hashed |
| D16 | `done_reason` must be `"stop"`; budget constants not env-overridable; global `ollama.lock` | K4 only named `length` (`P:451`). An env override bypasses a pinned safety constant (`.omarchy/omarchy.py:543`). Two concurrent `run`s on different slices would co-load families |
| D17 | Bootstrap mechanics: `open --bootstrap`, `BOOTSTRAP.json` with `schema`, `slice_id`, `kind`, and `prompts`, covering Phase 3 files except append-only logs, plus `BOOTSTRAP.<slot>.prompt` files | `P:587` requires a real proof chain for s000, but its prompts were not kernel-generated. Phase 3 also writes code (`scripts/ensure_local_agents.sh`) and the lock, which s001 must audit (`P:721`) |
| D18 | The `AGENTS.md` seat table has no model column; T-D1 compares six columns; T-D2's exclusions add `slices/**`, `docs/EVIDENCE.md`, `docs/HISTORY.md` | T-D1 (`P:705`) requires slugs in `AGENTS.md`, which T-D2 (`P:706`) forbids. Proof rows and `docs/HISTORY.md:11` legitimately contain slugs |
| D19 | `next` prints one `NEXT <KIND> <seat> <slot> a<k>` line per job, with seat ids rather than family names | The plan gives examples, not a grammar (`P:480-504`). A machine-readable, line-per-job form lets `parent` dispatch without parsing prose, and the attempt token makes retries visible |

---
OMARCHY_STATUS: READY
PLAN_FILES: omarchy/__init__.py, omarchy/__main__.py, omarchy/lock.py, omarchy/slice.py, omarchy/trailers.py, omarchy/proof.py, omarchy/machine.py, omarchy/worktree.py, omarchy/ollama.py, omarchy/runner.py, omarchy/ingest.py, omarchy/report.py, omarchy/prompts/plan.md, omarchy/prompts/challenge.md, omarchy/prompts/packets.md, omarchy/prompts/propose.md, omarchy/prompts/critique.md, omarchy/prompts/synthesize.md, omarchy/prompts/review.md, omarchy/prompts/qa.md, omarchy/prompts/family_a.md, omarchy/prompts/family_b.md, omarchy/prompts/smoke.md, scripts/omarchy, scripts/ensure_local_agents.sh, tests/conftest.py, tests/test_lock.py, tests/test_slice_config.py, tests/test_trailers.py, tests/test_proof.py, tests/test_machine.py, tests/test_ollama.py, tests/test_worktree.py, tests/test_ingest.py, tests/test_runner.py, tests/test_report.py, tests/test_docs_sync.py, agents.lock, agents.lock.optional, AGENTS.md, README.md, 00_ARCHITECTURE.md, 01_OMARCHY_AGENT_PROMPTS.md, .gitignore, .cursor/rules/omarchy-council.mdc, .cursor/agents/linus.md, .cursor/agents/knuth.md, .cursor/agents/dhh.md, .cursor/agents/carmack.md, docs/EVIDENCE.md, docs/HISTORY.md, archive/v2.3.1-attempt1/README.md, archive/v2.3.1-attempt1/council/FLOW_TRACE.md, archive/v2.3.1-attempt1/council/LINUS_AUDIT_PLAN.md, archive/v2.3.1-attempt1/council/LINUS_BALLOT.md, archive/v2.3.1-attempt1/council/MOXIE_G4_TEST.md, archive/v2.3.1-attempt1/council/MOXIE_G5_REVIEW.md, archive/v2.3.1-attempt1/council/QWENY_AUDIT_WORKSHEET.md, archive/v2.3.1-attempt1/council/SCRUM_DOD_AUDIT.md, archive/v2.3.1-attempt1/packets/aud231-s01-build.json, archive/v2.3.1-attempt1/packets/aud231-s09-g4.json, archive/v2.3.1-attempt1/packets/aud231-s10-g5.json, archive/v2.3.1-attempt1/packets/aud231-s11-dod.json, archive/v2.3.1-attempt1/contracts/STORY-AUDIT-V231.md, archive/v2.3.1-attempt1/contracts/UC-AUDIT-V231-WS.md, archive/v2.3.1-attempt1/contracts/UC-AUDIT-V231-G4.md, archive/v2.3.1-attempt1/contracts/UC-AUDIT-V231-G5.md, archive/v2.3.1-attempt1/contracts/UC-AUDIT-V231-DOD.md
OMARCHY_PROMPT_SHA256: 6915f627db334c68d18cf674878f69217e2ae7f5760fe0437c505eda2e15ccfc
---
