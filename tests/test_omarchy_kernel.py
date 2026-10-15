#!/usr/bin/env python3
"""Unit tests for .omarchy/omarchy.py and .omarchy/batch_runner.py.

Fixtures use only agents.lock local families/models — never invented slugs.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / ".omarchy"))

import batch_runner  # noqa: E402
import omarchy  # noqa: E402

LOCKED = omarchy.locked_local_family_models()
FAM_A = omarchy.LOCAL_FAMILY_A
FAM_B = omarchy.LOCAL_FAMILY_B


def _pkt(
    pid: str,
    family: str,
    depends_on: list[str],
    targets: list[str],
) -> dict:
    """Build a planner packet bound to agents.lock (exact model slug for family)."""
    return {
        "packet_id": pid,
        "family": family,
        "model": LOCKED[family],
        "depends_on": depends_on,
        "target_files": targets,
    }


def test_locked_local_family_models_exactly_two():
    assert set(LOCKED.keys()) == {FAM_A, FAM_B}
    assert LOCKED[FAM_A] != LOCKED[FAM_B]
    # Core-5: qweny/scrum → Family A; moxie → Family B.
    assert LOCKED[FAM_A] == "qwen3.8:27b-mlx"
    assert LOCKED[FAM_B] == "gemma4:31b-mlx"


def test_core_seats_present_optional_absent():
    seats = omarchy.parse_agents_lock()
    assert set(seats) == {"linus", "qweny", "moxie", "scrum", "parent"}
    for optional in ("dhh", "carmack", "knuth", "mitnick", "jobs"):
        assert optional not in seats


def test_sterilize_path_blocks_traversal():
    with pytest.raises(omarchy.OmarchyError, match="SECURITY VIOLATION"):
        omarchy.sterilize_path(
            REPO_ROOT / ".omarchy" / ".." / "README.md",
            omarchy.OMARCHY_ROOT,
        )


def test_causal_wave_ordering_a_b_a():
    """Family A coalesce → Family B → Family A again (depends_on)."""
    packets = [
        _pkt("pkt-01", FAM_A, [], ["a.py"]),
        _pkt("pkt-01b", FAM_A, [], ["b.py"]),
        _pkt("pkt-02", FAM_B, ["pkt-01"], ["a.py"]),
        _pkt("pkt-03", FAM_A, ["pkt-02"], ["a.py"]),
    ]
    waves = batch_runner.plan_serial_family_waves(
        packets, completed_ids=set(), coalesce_families=True
    )
    wave_ids = [[p["packet_id"] for p in w] for w in waves]
    assert wave_ids == [["pkt-01", "pkt-01b"], ["pkt-02"], ["pkt-03"]]
    assert waves[0][0]["model"] == LOCKED[FAM_A]
    assert waves[1][0]["model"] == LOCKED[FAM_B]
    assert waves[2][0]["model"] == LOCKED[FAM_A]


def test_file_lock_prevents_unsafe_coalescing():
    packets = [
        _pkt("pkt-1", FAM_A, [], ["shared.py"]),
        _pkt("pkt-2", FAM_A, [], ["shared.py"]),
    ]
    waves = batch_runner.plan_serial_family_waves(
        packets, completed_ids=set(), coalesce_families=True
    )
    assert [[p["packet_id"] for p in w] for w in waves] == [["pkt-1"], ["pkt-2"]]


def test_deadlock_detection():
    packets = [
        _pkt("pkt-a", FAM_A, ["pkt-b"], ["a.py"]),
        _pkt("pkt-b", FAM_A, ["pkt-a"], ["b.py"]),
    ]
    with pytest.raises(omarchy.OmarchyError, match="Deadlock"):
        batch_runner.plan_serial_family_waves(packets, completed_ids=set())


def test_resolve_packet_model_rejects_invented_slug():
    with pytest.raises(omarchy.OmarchyError, match="agents.lock"):
        omarchy.resolve_packet_model(
            {
                "packet_id": "evil",
                "role": "build",
                "family": FAM_A,
                "model": "qwen2.5-coder:32b",
            }
        )


def test_resolve_packet_model_rejects_size_downsize():
    with pytest.raises(omarchy.OmarchyError, match="agents.lock"):
        omarchy.resolve_packet_model(
            {
                "packet_id": "evil-size",
                "role": "build",
                "family": FAM_A,
                "model": "qwen3.8:14b-mlx",
            }
        )


def test_resolve_packet_model_accepts_lock_match():
    family, model = omarchy.resolve_packet_model(
        {
            "packet_id": "ok",
            "role": "build",
            "family": FAM_A,
            "model": LOCKED[FAM_A],
        }
    )
    assert family == FAM_A
    assert model == LOCKED[FAM_A]


def test_role_build_maps_to_qweny_family_a():
    role, seat, family, model, runtime = omarchy.resolve_role_binding(
        {"packet_id": "r1", "role": "build"}
    )
    assert (role, seat, family, model, runtime) == (
        "build",
        "qweny",
        FAM_A,
        LOCKED[FAM_A],
        "local",
    )


def test_role_g5_and_g4_map_to_moxie_family_b():
    for role_name in ("g5_review", "g4_test"):
        role, seat, family, model, runtime = omarchy.resolve_role_binding(
            {"packet_id": role_name, "role": role_name}
        )
        assert role == role_name
        assert seat == "moxie"
        assert family == FAM_B
        assert model == LOCKED[FAM_B]
        assert runtime == "local"


def test_role_scrum_audit_maps_to_scrum():
    role, seat, family, model, runtime = omarchy.resolve_role_binding(
        {"packet_id": "s1", "role": "scrum_audit"}
    )
    assert (role, seat, family, runtime) == ("scrum_audit", "scrum", FAM_A, "local")
    assert model == LOCKED[FAM_A]


def test_role_cloud_g3_maps_to_linus():
    role, seat, family, model, runtime = omarchy.resolve_role_binding(
        {"packet_id": "c1", "role": "cloud_g3"}
    )
    assert role == "cloud_g3"
    assert seat == "linus"
    assert runtime == "cloud"
    assert family == "anthropic_opus"
    assert model == "claude-opus-5-5-high"


def test_unknown_role_rejected():
    with pytest.raises(omarchy.OmarchyError, match="role"):
        omarchy.resolve_role_binding({"packet_id": "bad", "role": "ninja"})


def test_role_family_mismatch_rejected():
    with pytest.raises(omarchy.OmarchyError, match="family"):
        omarchy.resolve_role_binding(
            {
                "packet_id": "mismatch",
                "role": "build",
                "family": FAM_B,
            }
        )


def test_missing_core_seat_rejected():
    thin_lock = {
        "linus": {
            "seat_id": "linus",
            "group": "grand_council",
            "runtime": "cloud",
            "family": "anthropic_opus",
            "model": "claude-opus-5-5-high",
            "weight": "G3",
        },
        # qweny intentionally missing
        "moxie": {
            "seat_id": "moxie",
            "group": "local_council",
            "runtime": "local",
            "family": FAM_B,
            "model": LOCKED[FAM_B],
            "weight": "G5",
        },
        "scrum": {
            "seat_id": "scrum",
            "group": "local_council",
            "runtime": "local",
            "family": FAM_A,
            "model": LOCKED[FAM_A],
            "weight": "scrum",
        },
        "parent": {
            "seat_id": "parent",
            "group": "orchestrator",
            "runtime": "host",
            "family": "orchestrator",
            "model": "host_session",
            "weight": "router",
        },
    }
    with mock.patch.object(omarchy, "parse_agents_lock", return_value=thin_lock):
        with pytest.raises(omarchy.OmarchyError, match="missing from agents.lock"):
            omarchy.resolve_role_binding({"packet_id": "no-builder", "role": "build"})
