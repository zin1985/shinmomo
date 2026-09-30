#!/usr/bin/env python3
"""Compatibility entry point for the 2026-09-30 directional-family resolver.

The original script only promoted a small group-5/group-7 visual subset.
Resolution is now centralized in resolve_static_directional_families_20260930.py
so shared-state inheritance, group-4 evidence, direction-invariant objects, and
non-directional four-state pose families cannot be accidentally reverted.
"""
from pathlib import Path
import runpy

runpy.run_path(
    str(Path(__file__).with_name("resolve_static_directional_families_20260930.py")),
    run_name="__main__",
)
