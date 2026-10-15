#!/usr/bin/env python3
"""Deprecated shim — the sterilized 2PC kernel lives at .omarchy/omarchy.py."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

KERNEL = Path(__file__).resolve().parent.parent / ".omarchy" / "omarchy.py"
if not KERNEL.is_file():
    sys.stderr.write(f"[OMARCHY] Missing sterilized kernel: {KERNEL}\n")
    sys.exit(1)
sys.stderr.write(
    "[OMARCHY] WARN: scripts/omarchy.py is a shim; prefer "
    "python3 .omarchy/omarchy.py or scripts/run_local_agent.sh\n"
)
sys.argv[0] = str(KERNEL)
runpy.run_path(str(KERNEL), run_name="__main__")
