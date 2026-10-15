#!/usr/bin/env python3
"""
.omarchy/batch_runner.py — Serialized Model-Family Queue Scheduler.

Executes governance packets in dependency-safe waves:
  Family A (load -> run N packets warm -> explicit unload) ->
  Family B (load -> run M packets warm -> explicit unload) ->
  Family A (load -> run next wave -> explicit unload)

Guarantees zero concurrent model residency on a 128GB system, even when a
2PC gate failure aborts mid-wave (evict_model in `finally` at every boundary).
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set

# Allow `from omarchy import ...` when invoked as python3 .omarchy/batch_runner.py
_SYS_DIR = str(Path(__file__).resolve().parent)
if _SYS_DIR not in sys.path:
    sys.path.insert(0, _SYS_DIR)

from omarchy import (  # noqa: E402
    OLLAMA_API_URL,
    OMARCHY_ROOT,
    PACKETS_DIR,
    OmarchyError,
    execute_packet,
    load_packet,
    sterilize_path,
)

STATE_DIR = OMARCHY_ROOT / "state"
COMPLETED_LOG = STATE_DIR / "completed_packets.json"


def evict_model(model: str) -> None:
    """
    Explicitly unloads a model family from Ollama RAM (keep_alive=0).
    Called at every family boundary and in rollback handlers so two model
    families never coexist in the 128GB memory pool.
    """
    payload = {
        "model": model,
        "prompt": "",
        "stream": False,
        "keep_alive": 0,
    }
    req = urllib.request.Request(
        url=f"{OLLAMA_API_URL}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    print(f"[OMARCHY][EVICT] Forcing RAM unload for model family '{model}' (keep_alive=0)")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            resp.read()
    except urllib.error.URLError as exc:
        raise OmarchyError(f"Failed to evict model '{model}' from Ollama: {exc}") from exc


def load_completed_ids() -> Set[str]:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not COMPLETED_LOG.is_file():
        return set()
    with COMPLETED_LOG.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return set(data.get("completed", []))


def record_completed_id(packet_id: str) -> None:
    completed = load_completed_ids()
    completed.add(packet_id)
    with COMPLETED_LOG.open("w", encoding="utf-8") as f:
        json.dump({"completed": sorted(completed)}, f, indent=2)
        f.write("\n")


def discover_pending_packets(
    queue_paths: List[str],
    completed_ids: Set[str],
) -> List[Dict[str, Any]]:
    """Loads pending packets from .omarchy/packets/ and validates uniqueness."""
    if queue_paths:
        raw_files = [sterilize_path(p, PACKETS_DIR) for p in queue_paths]
    else:
        raw_files = sorted(
            p
            for p in PACKETS_DIR.glob("*.json")
            if p.is_file() and not p.name.startswith("_")
        )

    packets: List[Dict[str, Any]] = []
    seen_ids: Set[str] = set()

    for path in raw_files:
        pkt = load_packet(str(path))
        pkt["_path"] = str(path)
        pid = pkt["packet_id"]
        if pid in seen_ids:
            raise OmarchyError(f"Duplicate packet_id '{pid}' detected in queue.")
        seen_ids.add(pid)
        if pid not in completed_ids:
            packets.append(pkt)

    return packets


def plan_serial_family_waves(
    packets: List[Dict[str, Any]],
    completed_ids: Set[str],
    coalesce_families: bool = True,
) -> List[List[Dict[str, Any]]]:
    """
    Schedules packets into sequential single-family batches (waves).

    - Respects `depends_on` (list of packet_ids).
    - Applies automatic target_file write-order locks over the remaining queue
      so packets that share files are never reordered past each other.
    - When coalesce_families=True, groups all currently unblocked packets of the
      same model into one warm batch before unloading and switching families.
      This yields Family A -> Family B -> Family A when Packet 3 depends on Packet 2.
    """
    remaining = list(packets)
    satisfied = set(completed_ids)
    waves: List[List[Dict[str, Any]]] = []

    while remaining:
        ready: List[Dict[str, Any]] = []
        locked_files: Set[str] = set()

        for pkt in remaining:
            deps = set(pkt.get("depends_on", []) or [])
            targets = set(pkt.get("target_files", []) or [])
            if deps.issubset(satisfied) and not (targets & locked_files):
                ready.append(pkt)
            locked_files.update(targets)

        if not ready:
            unresolved = [p["packet_id"] for p in remaining]
            raise OmarchyError(
                f"Deadlock or unsatisfied 'depends_on' cycle in packet queue: {unresolved}"
            )

        if not coalesce_families:
            first_model = ready[0]["model"]
            contiguous_batch: List[Dict[str, Any]] = []
            for pkt in ready:
                if pkt["model"] == first_model:
                    contiguous_batch.append(pkt)
                else:
                    break
            waves.append(contiguous_batch)
            for pkt in contiguous_batch:
                satisfied.add(pkt["packet_id"])
                remaining.remove(pkt)
        else:
            family_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
            family_order: List[str] = []
            for pkt in ready:
                model = pkt["model"]
                if model not in family_groups:
                    family_order.append(model)
                family_groups[model].append(pkt)

            chosen_family = family_order[0]
            batch = family_groups[chosen_family]
            waves.append(batch)
            for pkt in batch:
                satisfied.add(pkt["packet_id"])
                remaining.remove(pkt)

    return waves


def execute_single_packet(
    packet: Dict[str, Any],
    unload_after: bool,
    dry_run: bool,
) -> None:
    """
    Runs a single packet via the sterilized 2PC kernel.

    keep_warm = not unload_after so intermediate same-family packets leave the
    model resident; the wave `finally` still calls evict_model even if a gate
    aborts while keep_warm was true on a prior packet.
    """
    path = packet.get("_path") or packet.get("_packet_path")
    if not path:
        raise OmarchyError(f"Packet '{packet.get('packet_id')}' missing path metadata.")

    rc = execute_packet(
        str(path),
        dry_run=dry_run,
        keep_warm=not unload_after,
    )
    if rc != 0:
        raise OmarchyError(
            f"Packet '{packet['packet_id']}' failed 2PC execution (exit {rc})."
        )
    if not dry_run:
        record_completed_id(packet["packet_id"])


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Omarchy Serial Model-Family Batch Runner (2PC + Explicit RAM Eviction)."
    )
    parser.add_argument(
        "packets",
        nargs="*",
        help="Optional packet JSON paths inside .omarchy/packets/ (defaults to all pending).",
    )
    parser.add_argument(
        "--strict-fifo",
        action="store_true",
        help="Do not reorder independent packets; only keep-warm across contiguous same-model packets.",
    )
    parser.add_argument(
        "--stop-on-failure",
        action="store_true",
        default=True,
        help="Halt batch immediately if any packet fails its 2PC verification gates (default).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned model-family waves and validate contracts without invoking Ollama.",
    )
    return parser.parse_args(argv)


def run_batch(
    packet_paths: Optional[List[str]] = None,
    *,
    strict_fifo: bool = False,
    dry_run: bool = False,
) -> int:
    completed = load_completed_ids()
    pending = discover_pending_packets(packet_paths or [], completed)
    if not pending:
        print("[OMARCHY][BATCH] No pending packets to execute.")
        return 0

    waves = plan_serial_family_waves(
        pending,
        completed_ids=completed,
        coalesce_families=not strict_fifo,
    )

    print(
        f"[OMARCHY][BATCH] Planned {len(waves)} serial model-family wave(s) "
        f"across {len(pending)} packet(s):"
    )
    for idx, wave in enumerate(waves, start=1):
        model_name = wave[0]["model"]
        pids = [p["packet_id"] for p in wave]
        print(
            f"  Wave {idx}: model='{model_name}' -> packets={pids} "
            f"(evict after '{pids[-1]}')"
        )

    for idx, wave in enumerate(waves, start=1):
        model_name = wave[0]["model"]
        print(f"\n[OMARCHY][WAVE {idx}/{len(waves)}] === Loading Family '{model_name}' ===")
        try:
            for pkt_idx, pkt in enumerate(wave):
                is_last_in_wave = pkt_idx == (len(wave) - 1)
                execute_single_packet(
                    packet=pkt,
                    unload_after=is_last_in_wave,
                    dry_run=dry_run,
                )
        finally:
            # Guarantee RAM eviction before the next family wave loads,
            # even if a packet aborted mid-wave while a prior packet used keep-warm.
            if not dry_run:
                evict_model(model_name)

    if dry_run:
        print("\n[OMARCHY][BATCH-SUCCESS] Dry-run: all waves planned and contracts verified.")
    else:
        print("\n[OMARCHY][BATCH-SUCCESS] All model-family waves completed and evicted cleanly.")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        return run_batch(
            list(args.packets),
            strict_fifo=args.strict_fifo,
            dry_run=args.dry_run,
        )
    except OmarchyError as exc:
        print(f"[OMARCHY][BATCH-FATAL] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
