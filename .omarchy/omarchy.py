#!/usr/bin/env python3
"""
.omarchy/omarchy.py — Sterilized Two-Phase Commit (2PC) Multi-Agent Kernel.

Enforces Story/UC contracts under .omarchy/contracts/, isolated git worktrees,
deterministic gates, and serialized Ollama model loading/unloading
(keep_alive: 0 on family boundaries for 128GB boxes).
"""
from __future__ import annotations

import argparse
import datetime
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple


REPO_ROOT = Path(__file__).resolve().parent.parent
LOCK_FILE = REPO_ROOT / "agents.lock"
OMARCHY_ROOT = REPO_ROOT / ".omarchy"
CONTRACTS_DIR = OMARCHY_ROOT / "contracts"
WORKTREES_DIR = OMARCHY_ROOT / "worktrees"
PACKETS_DIR = OMARCHY_ROOT / "packets"
PROOF_LOG = Path(
    os.environ.get("OMARCHY_LOCAL_PROOF_LOG", str(OMARCHY_ROOT / "local-agent-proof.log"))
)
OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://127.0.0.1:11434").rstrip("/")

# Exactly two local families. Each binds ONE exact model slug in agents.lock.
# Never coalesce parameter sizes (:27b vs :14b) — the lock slug is the identity.
LOCAL_FAMILY_A = "local_family_a"
LOCAL_FAMILY_B = "local_family_b"
LEGAL_LOCAL_FAMILIES = frozenset({LOCAL_FAMILY_A, LOCAL_FAMILY_B})

# Packet role → Core seat. Seats must exist in agents.lock (optional seats stay out).
ROLE_TO_SEAT: Dict[str, str] = {
    "build": "qweny",
    "g5_review": "moxie",
    "g4_test": "moxie",  # Core folds Mitnick into moxie (Family B)
    "scrum_audit": "scrum",
    "cloud_g3": "linus",
}
LEGAL_ROLES = frozenset(ROLE_TO_SEAT.keys())


class OmarchyError(Exception):
    """Base exception for deterministic governance and kernel failures."""


def parse_agents_lock() -> Dict[str, Dict[str, str]]:
    """Read agents.lock — the sole SSOT for every model slug in this repo."""
    if not LOCK_FILE.exists():
        raise OmarchyError(f"Missing agents.lock at {LOCK_FILE}")
    seats: Dict[str, Dict[str, str]] = {}
    for line in LOCK_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 6:
            continue
        seats[parts[0]] = {
            "seat_id": parts[0],
            "group": parts[1],
            "runtime": parts[2],
            "family": parts[3],
            "model": parts[4],
            "weight": parts[5],
        }
    if not seats:
        raise OmarchyError("agents.lock contains no seat rows")
    return seats


def resolve_role_binding(packet: Dict[str, Any]) -> Tuple[str, str, str, str, str]:
    """
    Resolve (role, seat_id, family, model, runtime) from packet role + agents.lock.

    Packets MUST declare role. Optional family/model must match the seat row.
    """
    role = packet.get("role")
    if role not in LEGAL_ROLES:
        raise OmarchyError(
            f"Packet '{packet.get('packet_id', '?')}' must set "
            f'"role" to one of {sorted(LEGAL_ROLES)} (got {role!r}).'
        )
    seat_id = ROLE_TO_SEAT[role]
    seats = parse_agents_lock()
    if seat_id not in seats:
        raise OmarchyError(
            f"Role '{role}' maps to seat '{seat_id}', but that seat is missing "
            f"from agents.lock. Core seats: linus, qweny, moxie, scrum, parent. "
            f"Optional rows live in agents.lock.optional."
        )
    row = seats[seat_id]
    family = row["family"]
    model = row["model"]
    runtime = row["runtime"]

    claimed_family = packet.get("family")
    if claimed_family is not None and claimed_family != family:
        raise OmarchyError(
            f"Packet '{packet.get('packet_id')}' role '{role}' → seat '{seat_id}' "
            f"binds family '{family}' in agents.lock, but packet claims "
            f"'{claimed_family}'."
        )
    claimed_model = packet.get("model")
    if claimed_model is not None and claimed_model != model:
        raise OmarchyError(
            f"Packet '{packet.get('packet_id')}' claims model '{claimed_model}' for "
            f"role '{role}' / seat '{seat_id}', but agents.lock binds '{model}'. "
            "Packets cannot invent or downsize models — edit agents.lock."
        )
    return role, seat_id, family, model, runtime


def locked_local_family_models() -> Dict[str, str]:
    """
    Project agents.lock → {local_family_a: exact_model, local_family_b: exact_model}.

    Fails closed if a family is missing, or if any family binds more than one
    distinct model slug (different sizes = different models = illegal).
    """
    by_family: Dict[str, Set[str]] = defaultdict(set)
    for row in parse_agents_lock().values():
        if row["runtime"] != "local":
            continue
        fam = row["family"]
        if fam not in LEGAL_LOCAL_FAMILIES:
            raise OmarchyError(
                f"agents.lock seat '{row['seat_id']}' has illegal local family "
                f"'{fam}'. Only {sorted(LEGAL_LOCAL_FAMILIES)} are permitted."
            )
        by_family[fam].add(row["model"])

    resolved: Dict[str, str] = {}
    for fam in (LOCAL_FAMILY_A, LOCAL_FAMILY_B):
        models = by_family.get(fam, set())
        if not models:
            raise OmarchyError(
                f"agents.lock missing local family '{fam}'. "
                "Family A and Family B must each bind exactly one model."
            )
        if len(models) > 1:
            raise OmarchyError(
                f"agents.lock family '{fam}' binds multiple models {sorted(models)}. "
                "Exactly ONE model per family — never mix parameter sizes. "
                "Edit agents.lock only."
            )
        resolved[fam] = next(iter(models))

    if resolved[LOCAL_FAMILY_A] == resolved[LOCAL_FAMILY_B]:
        raise OmarchyError(
            "agents.lock Family A and Family B resolve to the same model. "
            "Two distinct models required; only one may reside in RAM at a time."
        )
    return resolved


def resolve_packet_model(packet: Dict[str, Any]) -> Tuple[str, str]:
    """
    Resolve (family_id, exact_model) via role → seat → agents.lock.

    Preferred path: packet declares role (and optional family matching the seat).
    Legacy path: family-only packets still resolve against locked local families.
    """
    if packet.get("role") is not None:
        _role, _seat, family, model, runtime = resolve_role_binding(packet)
        if runtime == "local" and family not in LEGAL_LOCAL_FAMILIES:
            raise OmarchyError(
                f"Seat '{_seat}' has illegal local family '{family}'."
            )
        if runtime == "local":
            locked = locked_local_family_models()
            if locked[family] != model:
                raise OmarchyError(
                    f"agents.lock seat '{_seat}' model '{model}' disagrees with "
                    f"family '{family}' locked model '{locked[family]}'."
                )
        return family, model

    locked = locked_local_family_models()
    family = packet.get("family")
    if family not in LEGAL_LOCAL_FAMILIES:
        raise OmarchyError(
            f"Packet '{packet.get('packet_id', '?')}' must set "
            f'"role" ({sorted(LEGAL_ROLES)}) or '
            f'"family": "{LOCAL_FAMILY_A}" | "{LOCAL_FAMILY_B}" '
            f"(got family={family!r}). Models are read ONLY from agents.lock."
        )
    locked_model = locked[family]
    claimed = packet.get("model")
    if claimed is not None and claimed != locked_model:
        raise OmarchyError(
            f"Packet '{packet.get('packet_id')}' claims model '{claimed}' for "
            f"family '{family}', but agents.lock binds '{locked_model}'. "
            "Packets cannot invent or downsize models — edit agents.lock."
        )
    return family, locked_model


# ============================================================================
# 1. THE FOUR CORE HELPERS (Hardened & Sterilized)
# ============================================================================

def sterilize_path(raw_path: str | Path, allowed_root: Path = OMARCHY_ROOT) -> Path:
    """
    Helper 1: Resolves a path and enforces strict containment within allowed_root.
    Blocks symlink escapes, directory traversal (..), and ad-hoc paths.
    """
    resolved_root = allowed_root.resolve()
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = (Path.cwd() / candidate).resolve()
    else:
        candidate = candidate.resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise OmarchyError(
            f"SECURITY VIOLATION: Path '{candidate}' escapes sterilized root '{resolved_root}'."
        ) from exc
    return candidate


def load_packet(packet_path_str: str) -> Dict[str, Any]:
    """
    Helper 2: Loads and schema-validates a governance task packet from .omarchy/packets/.
    """
    raw = Path(packet_path_str)
    if not raw.is_absolute() and not raw.exists():
        # Bare filename → .omarchy/packets/<name>
        raw = PACKETS_DIR / raw.name
    packet_path = sterilize_path(raw, PACKETS_DIR)
    if not packet_path.is_file():
        raise OmarchyError(f"Packet file not found: {packet_path}")

    with packet_path.open("r", encoding="utf-8") as f:
        packet = json.load(f)

    required_keys = {
        "packet_id",
        "story_id",
        "uc_ids",
        "role",  # build | g5_review | g4_test | scrum_audit | cloud_g3
        "base_branch",
        "target_files",
        "instructions",
        "verification_commands",
    }
    missing = required_keys - set(packet.keys())
    if missing:
        raise OmarchyError(
            f"Packet '{packet_path.name}' missing required keys: {sorted(missing)}"
        )

    if not isinstance(packet["uc_ids"], list) or not packet["uc_ids"]:
        raise OmarchyError("Packet 'uc_ids' must be a non-empty list.")
    if not isinstance(packet["verification_commands"], list) or not packet["verification_commands"]:
        raise OmarchyError("Packet 'verification_commands' must be a non-empty list.")
    if not isinstance(packet["target_files"], list) or not packet["target_files"]:
        raise OmarchyError("Packet 'target_files' must be a non-empty list.")
    if len(packet["target_files"]) > 5:
        raise OmarchyError(
            f"Gate G2: packet touches {len(packet['target_files'])} files (max 5)."
        )

    # SSOT: role → seat → family/model from agents.lock — packets never choose models.
    role, seat_id, family, model, runtime = resolve_role_binding(packet)
    if runtime == "local":
        locked = locked_local_family_models()
        if family not in locked or locked[family] != model:
            raise OmarchyError(
                f"Seat '{seat_id}' family/model disagrees with locked local families."
            )
    packet["role"] = role
    packet["seat_id"] = seat_id
    packet["family"] = family
    packet["model"] = model
    packet["runtime"] = runtime
    packet["_packet_path"] = str(packet_path)
    return packet


def verify_story_and_uc(story_id: str, uc_ids: List[str]) -> Dict[str, str]:
    """
    Helper 3: Verifies that the Story and Use Case (UC) governance contracts exist
    and returns their contents to anchor the agent's context window.
    """
    story_file = sterilize_path(CONTRACTS_DIR / "stories" / f"{story_id}.md", CONTRACTS_DIR)
    if not story_file.is_file():
        raise OmarchyError(f"Missing Story contract: {story_file}")

    contracts_context: Dict[str, str] = {
        f"STORY:{story_id}": story_file.read_text(encoding="utf-8")
    }

    for uc_id in uc_ids:
        uc_file = sterilize_path(CONTRACTS_DIR / "use_cases" / f"{uc_id}.md", CONTRACTS_DIR)
        if not uc_file.is_file():
            raise OmarchyError(f"Missing Use Case contract: {uc_file}")
        contracts_context[f"UC:{uc_id}"] = uc_file.read_text(encoding="utf-8")

    return contracts_context


def run_deterministic_gates(worktree_path: Path, commands: List[List[str]]) -> None:
    """
    Helper 4: Executes deterministic verification commands inside the isolated worktree.
    Rejects sycophantic 'done' declarations if any gate returns a non-zero exit code.
    """
    for cmd in commands:
        if not isinstance(cmd, list) or not cmd or not all(isinstance(x, str) for x in cmd):
            raise OmarchyError(
                f"Invalid verification command format (expected argv list of strings): {cmd}"
            )
        print(f"[OMARCHY][GATE] Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=str(worktree_path),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise OmarchyError(
                f"Gate FAILED ({' '.join(cmd)}) [exit {result.returncode}]:\n"
                f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )
        print(f"[OMARCHY][GATE] PASSED: {' '.join(cmd)}")


def append_locked_log(kv_pairs: Dict[str, str]) -> None:
    """Atomic file-locked proof logging (fcntl.LOCK_EX)."""
    PROOF_LOG.parent.mkdir(parents=True, exist_ok=True)
    block = "---\n" + "\n".join(f"{k}={v}" for k, v in kv_pairs.items()) + "\n"
    with open(PROOF_LOG, "a", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            f.write(block)
            f.flush()
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


# ============================================================================
# 2. GIT WORKTREE TWO-PHASE COMMIT (2PC) TRANSACTION MANAGER
# ============================================================================

class WorktreeTransaction:
    """
    Isolated git worktree as a Two-Phase Commit (2PC) transaction:
    - Phase 1 (Prepare): Create isolated branch + worktree, apply agent edits, run gates.
    - Phase 2 (Commit/Rollback): Merge into base_branch on success, or destroy on failure.
    """

    def __init__(self, packet_id: str, base_branch: str) -> None:
        safe_id = "".join(c if c.isalnum() or c in "._-" else "_" for c in packet_id)
        self.packet_id = packet_id
        self.safe_id = safe_id
        self.base_branch = base_branch
        self.tx_branch = f"omarchy/tx-{safe_id}"
        self._committed = False
        WORKTREES_DIR.mkdir(parents=True, exist_ok=True)
        self.worktree_path = sterilize_path(WORKTREES_DIR / safe_id, WORKTREES_DIR)

    def __enter__(self) -> Path:
        if self.worktree_path.exists():
            self._cleanup_worktree()

        print(
            f"[OMARCHY][2PC-PREPARE] Creating worktree '{self.worktree_path}' "
            f"on branch '{self.tx_branch}' from '{self.base_branch}'"
        )
        subprocess.run(
            [
                "git",
                "worktree",
                "add",
                "-B",
                self.tx_branch,
                str(self.worktree_path),
                self.base_branch,
            ],
            cwd=str(REPO_ROOT),
            check=True,
            capture_output=True,
            text=True,
        )
        return self.worktree_path

    def commit_transaction(self, story_id: str, uc_ids: List[str]) -> str:
        """Phase 2 Commit: stage, commit inside worktree, ff-merge into base_branch."""
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(self.worktree_path),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        if not status:
            raise OmarchyError("Agent produced zero file changes in worktree; aborting transaction.")

        # tree_sha256 over the staged diff (Gate G0 provenance)
        subprocess.run(["git", "add", "-A"], cwd=str(self.worktree_path), check=True)
        diff = subprocess.run(
            ["git", "diff", "--cached"],
            cwd=str(self.worktree_path),
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        tree_sha = hashlib.sha256(diff.encode("utf-8")).hexdigest()

        commit_msg = (
            f"[{story_id}][{','.join(uc_ids)}] Automated 2PC commit for packet {self.packet_id}"
        )
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=str(self.worktree_path),
            check=True,
            capture_output=True,
            text=True,
        )

        # Refuse to clobber a dirty main working tree or wrong branch.
        cur = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(REPO_ROOT),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if cur != self.base_branch:
            raise OmarchyError(
                f"Main repo is on '{cur}', not base_branch '{self.base_branch}'. "
                "Checkout the base branch (with a clean tree) before 2PC merge."
            )
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(REPO_ROOT),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if dirty:
            raise OmarchyError(
                "Main working tree is dirty; refusing 2PC merge. "
                "Commit/stash host edits before running the kernel."
            )

        print(f"[OMARCHY][2PC-COMMIT] Fast-forward merging '{self.tx_branch}' into '{self.base_branch}'")
        subprocess.run(
            ["git", "merge", "--ff-only", self.tx_branch],
            cwd=str(REPO_ROOT),
            check=True,
            capture_output=True,
            text=True,
        )
        self._committed = True
        return tree_sha

    def _cleanup_worktree(self) -> None:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(self.worktree_path)],
            cwd=str(REPO_ROOT),
            check=False,
            capture_output=True,
        )
        if self.worktree_path.exists():
            shutil.rmtree(self.worktree_path, ignore_errors=True)
        subprocess.run(
            ["git", "branch", "-D", self.tx_branch],
            cwd=str(REPO_ROOT),
            check=False,
            capture_output=True,
        )

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is not None:
            print(
                f"[OMARCHY][2PC-ABORT] Rolling back worktree '{self.packet_id}': {exc_val}",
                file=sys.stderr,
            )
        # Always remove the worktree; delete tx branch after success or failure.
        self._cleanup_worktree()
        return False


# ============================================================================
# 3. SERIALIZED OLLAMA EXECUTION PATH (Load -> Run -> Unload)
# ============================================================================

def build_agent_prompt(
    packet: Dict[str, Any],
    contracts: Dict[str, str],
    worktree_path: Path,
) -> str:
    """Constructs a deterministic prompt asking for structured JSON file replacements."""
    file_snapshots: Dict[str, str] = {}
    for rel_path in packet["target_files"]:
        # Containment: target must stay inside the worktree
        candidate = (worktree_path / rel_path).resolve()
        try:
            candidate.relative_to(worktree_path.resolve())
        except ValueError as exc:
            raise OmarchyError(
                f"SECURITY VIOLATION: target_files path escapes worktree: {rel_path}"
            ) from exc
        file_snapshots[rel_path] = (
            candidate.read_text(encoding="utf-8") if candidate.is_file() else ""
        )

    schema_instruction = (
        "Return ONLY valid JSON matching this exact schema:\n"
        '{"files": {"<relative_path>": "<full_updated_file_content>"}}\n'
        "Do not wrap in markdown fences or add commentary."
    )

    return json.dumps(
        {
            "governance_contracts": contracts,
            "task_instructions": packet["instructions"],
            "target_files_current_state": file_snapshots,
            "output_contract": schema_instruction,
        },
        indent=2,
    )


# ~105GB ceiling on a 128GB box (weights + KV + test runner); leave ~23GB for OS/page cache.
MAX_FAMILY_BUDGET_BYTES = int(os.environ.get("OMARCHY_MAX_RAM_BYTES", 105 * (1024**3)))
# Conservative ~0.5MB/token KV+compute buffer for large local models.
BYTES_PER_CTX_TOKEN_ESTIMATE = 512 * 1024


def enforce_memory_budget(model: str, num_ctx: int) -> None:
    """
    Pre-load guard: model weights (Ollama /api/tags size) + KV/ctx estimate + 4GB
    test-runner headroom must stay within the ~105GB family ceiling.
    """
    if num_ctx < 1:
        raise OmarchyError(f"num_ctx must be >= 1 (got {num_ctx})")

    req = urllib.request.Request(
        url=f"{OLLAMA_API_URL}/api/tags",
        headers={"Content-Type": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            tags_data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise OmarchyError(
            f"Cannot query Ollama /api/tags for memory budget check: {exc}"
        ) from exc

    weight_bytes = 0
    for m in tags_data.get("models", []):
        name = m.get("name") or m.get("model") or ""
        # Exact match, or Ollama's name:tag / name:latest aliases for the locked slug.
        if name == model or name.startswith(f"{model}:") or model.startswith(f"{name}:"):
            weight_bytes = int(m.get("size", 0) or 0)
            if weight_bytes > 0:
                break

    if weight_bytes == 0:
        raise OmarchyError(
            f"Model '{model}' is not pulled locally in Ollama; refusing unbudgeted load."
        )

    kv_and_runner_bytes = (num_ctx * BYTES_PER_CTX_TOKEN_ESTIMATE) + (4 * (1024**3))
    estimated_total = weight_bytes + kv_and_runner_bytes

    print(
        f"[OMARCHY][BUDGET] model='{model}' weights={weight_bytes / (1024**3):.1f}GB "
        f"ctx/runner={kv_and_runner_bytes / (1024**3):.1f}GB "
        f"total≈{estimated_total / (1024**3):.1f}GB "
        f"limit={MAX_FAMILY_BUDGET_BYTES / (1024**3):.1f}GB"
    )

    if estimated_total > MAX_FAMILY_BUDGET_BYTES:
        raise OmarchyError(
            f"MEMORY BUDGET EXCEEDED for '{model}': estimated "
            f"{estimated_total / (1024**3):.1f}GB "
            f"(weights={weight_bytes / (1024**3):.1f}GB, "
            f"ctx/runner={kv_and_runner_bytes / (1024**3):.1f}GB) "
            f"> limit {MAX_FAMILY_BUDGET_BYTES / (1024**3):.1f}GB."
        )


def invoke_ollama_serial(
    model: str,
    prompt: str,
    unload_after: bool = True,
    num_ctx: int = 16384,
) -> Dict[str, str]:
    """
    Serialized Ollama /api/generate.
    keep_alive=0 forces immediate eviction after the call (128GB RAM hygiene).
    Model MUST be one of the two exact slugs from agents.lock.
    """
    allowed = set(locked_local_family_models().values())
    if model not in allowed:
        raise OmarchyError(
            f"Refusing to load '{model}'. Only agents.lock local models are legal: "
            f"{sorted(allowed)}"
        )
    enforce_memory_budget(model, num_ctx)
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "keep_alive": 0 if unload_after else "15m",
        "options": {
            "temperature": 0.0,
            "num_ctx": num_ctx,
        },
    }

    req = urllib.request.Request(
        url=f"{OLLAMA_API_URL}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    print(
        f"[OMARCHY][OLLAMA] Running model='{model}' "
        f"(unload_after={unload_after}, num_ctx={num_ctx})"
    )
    try:
        with urllib.request.urlopen(req, timeout=3600) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise OmarchyError(
            f"Failed to communicate with Ollama at {OLLAMA_API_URL}: {exc}"
        ) from exc

    raw_response = body.get("response", "")
    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise OmarchyError(
            f"Model '{model}' returned invalid JSON: {raw_response[:500]}"
        ) from exc

    if "files" not in parsed or not isinstance(parsed["files"], dict):
        raise OmarchyError(f"Model response missing 'files' dictionary: {parsed}")

    return {str(k): str(v) for k, v in parsed["files"].items()}


def force_unload_model(model: str) -> None:
    """Explicit eviction if a keep-warm batch ends or a family boundary is crossed."""
    payload = {
        "model": model,
        "keep_alive": 0,
        "prompt": "",
    }
    req = urllib.request.Request(
        url=f"{OLLAMA_API_URL}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            resp.read()
        print(f"[OMARCHY][OLLAMA] Evicted model='{model}' (keep_alive=0)")
    except urllib.error.URLError as exc:
        print(f"[OMARCHY][OLLAMA] Eviction warning for '{model}': {exc}", file=sys.stderr)


def apply_agent_changes(
    worktree_path: Path,
    allowed_files: List[str],
    new_files: Dict[str, str],
) -> None:
    """Applies only changes to files explicitly authorized by the governance packet."""
    allowed_set = set(allowed_files)
    for rel_path, content in new_files.items():
        if rel_path not in allowed_set:
            raise OmarchyError(
                f"Agent attempted unauthorized file modification: '{rel_path}'"
            )
        dest = (worktree_path / rel_path).resolve()
        try:
            dest.relative_to(worktree_path.resolve())
        except ValueError as exc:
            raise OmarchyError(
                f"SECURITY VIOLATION: write path escapes worktree: {rel_path}"
            ) from exc
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not content.endswith("\n"):
            content = content + "\n"
        dest.write_text(content, encoding="utf-8")
        print(f"[OMARCHY][WRITE] Updated '{rel_path}' in worktree")


# ============================================================================
# 4. PACKET EXECUTION + FAMILY QUEUE
# ============================================================================

def wave_key(packet: Dict[str, Any]) -> str:
    """
    Wave identity = locked family id (local_family_a | local_family_b).

    Never strip tags or coalesce :27b with :14b — different slugs are different
    models and agents.lock forbids more than one slug per family.
    """
    family = packet.get("family")
    if family not in LEGAL_LOCAL_FAMILIES:
        raise OmarchyError(f"Packet missing locked family for wave key: {packet.get('packet_id')}")
    return family


def execute_packet(
    packet_path: str,
    *,
    dry_run: bool = False,
    keep_warm: bool = False,
) -> int:
    packet = load_packet(packet_path)
    contracts = verify_story_and_uc(packet["story_id"], packet["uc_ids"])
    packet_sha = hashlib.sha256(
        Path(packet["_packet_path"]).read_bytes()
    ).hexdigest()
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    num_ctx = int(packet.get("num_ctx", 16384))

    # --dry-run: no git worktree, no Ollama (CI / shallow clones safe).
    if dry_run:
        for rel_path in packet["target_files"]:
            sterilize_path(REPO_ROOT / rel_path, REPO_ROOT)
        prompt_sha = hashlib.sha256(
            f"DRY_RUN|{packet['packet_id']}|{packet['role']}|{packet['seat_id']}|"
            f"{packet['family']}|{packet['model']}".encode()
        ).hexdigest()
        print(
            f"[OMARCHY][DRY-RUN] packet={packet['packet_id']} "
            f"role={packet['role']} seat={packet['seat_id']} "
            f"family={packet['family']} model={packet['model']} "
            f"contracts={list(contracts.keys())} (worktree-free)"
        )
        append_locked_log(
            {
                "time": now,
                "packet_id": packet["packet_id"],
                "story_id": packet["story_id"],
                "uc_ids": ",".join(packet["uc_ids"]),
                "role": packet["role"],
                "seat_id": packet["seat_id"],
                "family": packet["family"],
                "model": packet["model"],
                "model_source": "agents.lock",
                "packet_sha256": packet_sha,
                "prompt_sha256": prompt_sha,
                "tree_sha256": "",
                "trailer_status": "DRY_RUN",
                "keep_warm": str(keep_warm),
            }
        )
        return 0

    # Live local Ollama path only — cloud_g3 / host seats are not 2PC workers.
    if packet.get("runtime") != "local":
        raise OmarchyError(
            f"Packet '{packet['packet_id']}' role '{packet['role']}' resolves to "
            f"runtime '{packet.get('runtime')}' (seat '{packet['seat_id']}'). "
            "Local 2PC/Ollama accepts only local_council seats. "
            "Use --dry-run to validate cloud_g3 packets, or dispatch via cloud Tasks."
        )

    # Live path: budget → worktree 2PC → Ollama → gates → commit.
    enforce_memory_budget(packet["model"], num_ctx)

    tx = WorktreeTransaction(packet["packet_id"], packet["base_branch"])
    with tx as wt_path:
        prompt = build_agent_prompt(packet, contracts, wt_path)
        prompt_sha = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

        updated_files = invoke_ollama_serial(
            model=packet["model"],  # always resolved from agents.lock in load_packet
            prompt=prompt,
            unload_after=not keep_warm,
            num_ctx=num_ctx,
        )
        apply_agent_changes(wt_path, packet["target_files"], updated_files)
        run_deterministic_gates(wt_path, packet["verification_commands"])

        # Phase 2 on the SAME transaction instance (not a new one).
        tree_sha = tx.commit_transaction(packet["story_id"], packet["uc_ids"])

    append_locked_log(
        {
            "time": now,
            "packet_id": packet["packet_id"],
            "story_id": packet["story_id"],
            "uc_ids": ",".join(packet["uc_ids"]),
            "role": packet["role"],
            "seat_id": packet["seat_id"],
            "family": packet["family"],
            "model": packet["model"],
            "model_source": "agents.lock",
            "packet_sha256": packet_sha,
            "prompt_sha256": prompt_sha,
            "tree_sha256": tree_sha,
            "trailer_status": "COMMITTED",
            "keep_warm": str(keep_warm),
        }
    )
    print(f"[OMARCHY][SUCCESS] Packet '{packet['packet_id']}' committed cleanly.")
    return 0


def list_pending_packets() -> List[Path]:
    if not PACKETS_DIR.is_dir():
        return []
    return sorted(
        p for p in PACKETS_DIR.glob("*.json") if p.is_file() and not p.name.startswith("_")
    )


def run_queue(*, dry_run: bool = False, strict_fifo: bool = False) -> int:
    """
    Delegate to batch_runner: dependency-safe family waves + finally-block eviction.
    """
    from batch_runner import run_batch  # local import — same .omarchy/ directory

    return run_batch([], strict_fifo=strict_fifo, dry_run=dry_run)


# ============================================================================
# 5. CLI ENTRYPOINT
# ============================================================================

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Omarchy 2PC Governance Kernel — executes sterilized task packets only."
    )
    parser.add_argument(
        "--packet",
        help="Path to the packet JSON file inside .omarchy/packets/",
    )
    parser.add_argument(
        "--queue",
        action="store_true",
        help="Run all .omarchy/packets/*.json grouped by model family "
        "(keep-warm within family; unload on family boundary).",
    )
    parser.add_argument(
        "--keep-warm",
        action="store_true",
        help="Keep model loaded after task (same-family batching only).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate packet, Story/UC contracts, and worktree setup without calling Ollama.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        if args.queue:
            if args.packet:
                raise OmarchyError("Use either --queue or --packet, not both.")
            return run_queue(dry_run=args.dry_run)
        if not args.packet:
            raise OmarchyError("Required: --packet <path> or --queue")
        return execute_packet(
            args.packet,
            dry_run=args.dry_run,
            keep_warm=args.keep_warm,
        )
    except OmarchyError as exc:
        print(f"[OMARCHY][FATAL] {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(
            f"[OMARCHY][GIT-ERROR] Command {exc.cmd} failed:\n{exc.stderr or exc.stdout}",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
