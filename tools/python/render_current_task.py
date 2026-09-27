#!/usr/bin/env python3
"""Render progress/current_task.json as docs/handoff/CURRENT.md.

The JSON file is canonical. If the Markdown handoff disagrees with it, the JSON
wins. This renderer makes the rolling human-readable handoff deterministic.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "progress" / "current_task.json"
DST = ROOT / "docs" / "handoff" / "CURRENT.md"


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {x}" for x in items)


def main() -> None:
    task = json.loads(SRC.read_text(encoding="utf-8-sig"))
    lines = [
        "# CURRENT rolling handoff",
        "",
        f"Updated: {task.get('updated_at', '')}",
        "",
        "> Canonical machine-readable state: `progress/current_task.json`.",
        "> If this file disagrees with the JSON checkpoint, the JSON wins.",
        "",
        "## Current task",
        "",
        f"- Status: **{task.get('status', '')}**",
        f"- Workstream: `{task.get('workstream', '')}`",
        f"- Title: **{task.get('title', '')}**",
        f"- Base main HEAD verified: `{task.get('base_main_head_verified', '')}`",
        "",
        task.get("goal", ""),
        "",
        "## Definition of done",
        "",
        bullets(task.get("definition_of_done", [])),
        "",
        "## Done",
        "",
    ]

    for item in task.get("done", []):
        lines.append(f"- {item.get('item', '')}")
        for ev in item.get("evidence", []):
            lines.append(f"  - `{ev}`")

    lines += ["", "## Observed but not yet promoted", ""]
    for item in task.get("observed_not_yet_promoted", []):
        lines.append(f"- **{item.get('confidence', '')}**: {item.get('observation', '')}")
        reason = item.get("reason_not_promoted", "")
        if reason:
            lines.append(f"  - Why not promoted: {reason}")

    lines += ["", "## In progress", "", bullets(task.get("in_progress", []))]
    lines += ["", "## Next actions", ""]
    for item in sorted(task.get("next_actions", []), key=lambda x: x.get("order", 999)):
        lines.append(f"{item.get('order', '?')}. {item.get('action', '')}")

    lines += ["", "## Do not redo", "", bullets(task.get("do_not_redo", []))]
    lines += ["", "## Runtime-only artifacts", ""]
    for item in task.get("runtime_only_artifacts", []):
        lines.append(f"- `{item.get('path', '')}`")
        lines.append(f"  - {item.get('description', '')}")

    lines += ["", "## Canonical evidence / save locations", ""]
    for path in task.get("canonical_evidence", []):
        lines.append(f"- `{path}`")

    lines += [
        "",
        "## Resume instruction",
        "",
        "On a short request such as **「続きを進めて」**:",
        "",
        "1. verify latest `main`;",
        "2. read `progress/current_task.json`;",
        "3. preserve newer parallel results;",
        "4. continue from the first unfinished `next_actions` entry;",
        "5. do not redo `done` / `do_not_redo` items;",
        "6. checkpoint again after the next meaningful durable result.",
        "",
    ]

    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
