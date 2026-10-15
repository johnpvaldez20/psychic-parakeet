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
from typing import Any, Dict, List, Optional, Sequence


REPO_ROOT = Path(__file__).resolve().parent.parent
OMARCHY_ROOT = REPO_ROOT / ".omarchy"
CONTRACTS_DIR = OMARCHY_ROOT / "contracts"
WORKTREES_DIR = OMARCHY_ROOT / "worktrees"
PACKETS_DIR = OMARCHY_ROOT / "packets"
PROOF_LOG = Path(
    os.environ.get("OMARCHY_LOCAL_PROOF_LOG", str(OMARCHY_ROOT / "local-agent-proof.log"))
)
OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://127.0.0.1:11434").rstrip("/")


class OmarchyError(Exception):
    """Base exception for deterministic governance and kernel failures."""


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
        "model",
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


def invoke_ollama_serial(
    model: str,
    prompt: str,
    unload_after: bool = True,
    num_ctx: int = 16384,
) -> Dict[str, str]:
    """
    Serialized Ollama /api/generate.
    keep_alive=0 forces immediate eviction after the call (128GB RAM hygiene).
    """
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

def model_family(model: str) -> str:
    """Coarse family key for keep-warm batching (name before ':' or full slug)."""
    return model.split(":")[0].strip().lower()


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

    tx = WorktreeTransaction(packet["packet_id"], packet["base_branch"])
    with tx as wt_path:
        prompt = build_agent_prompt(packet, contracts, wt_path)
        prompt_sha = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

        if dry_run:
            print(
                f"[OMARCHY][DRY-RUN] Packet '{packet['packet_id']}' and contracts verified."
            )
            append_locked_log(
                {
                    "time": now,
                    "packet_id": packet["packet_id"],
                    "story_id": packet["story_id"],
                    "uc_ids": ",".join(packet["uc_ids"]),
                    "model": packet["model"],
                    "packet_sha256": packet_sha,
                    "prompt_sha256": prompt_sha,
                    "tree_sha256": "",
                    "trailer_status": "DRY_RUN",
                    "keep_warm": str(keep_warm),
                }
            )
            return 0

        updated_files = invoke_ollama_serial(
            model=packet["model"],
            prompt=prompt,
            unload_after=not keep_warm,
            num_ctx=int(packet.get("num_ctx", 16384)),
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
            "model": packet["model"],
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
