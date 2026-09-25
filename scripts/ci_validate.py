from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    ROOT / "project.yml",
    ROOT / "VERSION",
    ROOT / "CHANGELOG.md",
    ROOT / ".gitignore",
    ROOT / "manifest" / "EXCLUDED.md",
    ROOT / "progress" / "project_progress.json",
    ROOT / "docs" / "project" / "PROJECT_GOALS_V2.md",
    ROOT / "data" / "audit" / "contradiction_register_20260925.csv",
]
FORBIDDEN_SUFFIXES = {
    ".smc", ".sfc", ".fig", ".swc", ".bs", ".srm", ".sav", ".state", ".7z"
}
FORBIDDEN_RAW_NAMES = {"vram.bin", "oam.bin", "cgram.bin"}


def validate_progress(errors: list[str]) -> None:
    path = ROOT / "progress" / "project_progress.json"
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid progress JSON: {exc}")
        return

    top_goals = data.get("top_goals")
    if not isinstance(top_goals, list) or len(top_goals) != 5:
        errors.append("progress JSON requires exactly five top_goals")
    else:
        ids = [str(g.get("id", "")) for g in top_goals]
        if ids != ["G1", "G2", "G3", "G4", "G5"]:
            errors.append(f"top_goals must be ordered G1..G5, got: {ids}")
        values = []
        for goal in top_goals:
            gid = str(goal.get("id", ""))
            try:
                percent = float(goal["percent"])
            except (KeyError, TypeError, ValueError):
                errors.append(f"invalid top goal percent: {gid}")
                continue
            if not 0 <= percent <= 100:
                errors.append(f"top goal percent out of range {gid}: {percent}")
            if not goal.get("definition_of_done") or not goal.get("evidence"):
                errors.append(f"top goal {gid} requires definition_of_done and evidence")
            components = goal.get("components")
            if not isinstance(components, list) or not components:
                errors.append(f"top goal {gid} requires components")
            else:
                weight_sum = sum(float(c.get("weight", 0)) for c in components)
                if abs(weight_sum - 1.0) > 1e-6:
                    errors.append(f"top goal {gid} component weights must sum to 1.0, got {weight_sum}")
            values.append(percent)
        if len(values) == 5:
            calculated = sum(values) / 5
            declared = float(data.get("overall_percent", -1))
            if abs(calculated - declared) > 0.11:
                errors.append(
                    f"overall_percent mismatch: declared={declared:.1f}, calculated={calculated:.1f}"
                )
            print(f"top-goal overall progress: {calculated:.1f}%")

    tracks = data.get("tracks")
    schedule = data.get("schedule")
    if not isinstance(tracks, list) or not tracks:
        errors.append("progress JSON requires non-empty tracks")
        return
    if not isinstance(schedule, list) or len(schedule) < 5:
        errors.append("progress JSON requires at least five rolling schedule entries")

    seen: set[str] = set()
    total_weight = 0.0
    weighted = 0.0
    for track in tracks:
        tid = str(track.get("id", ""))
        if not tid or tid in seen:
            errors.append(f"invalid or duplicate track id: {tid!r}")
        seen.add(tid)
        try:
            percent = float(track["percent"])
            weight = float(track.get("weight", 1))
        except (KeyError, TypeError, ValueError):
            errors.append(f"invalid percent/weight for track: {tid}")
            continue
        if not 0 <= percent <= 100:
            errors.append(f"percent out of range for track {tid}: {percent}")
        if weight <= 0:
            errors.append(f"weight must be positive for track {tid}: {weight}")
        if not track.get("scope") or not track.get("evidence"):
            errors.append(f"track {tid} requires scope and evidence")
        total_weight += weight
        weighted += percent * weight

    if total_weight:
        local = weighted / total_weight
        print(f"legacy workstream maturity: {local:.1f}%")
        declared = data.get("legacy_workstream_overall_percent")
        if declared is not None and abs(local - float(declared)) > 0.11:
            errors.append(
                f"legacy_workstream_overall_percent mismatch: declared={declared}, calculated={local:.1f}"
            )


def main() -> None:
    errors: list[str] = []

    for path in REQUIRED:
        if not path.exists():
            errors.append(f"missing required file: {path.relative_to(ROOT)}")

    forbidden = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if ".git" in rel.parts or "dist" in rel.parts:
            continue
        if path.suffix.lower() in FORBIDDEN_SUFFIXES or path.name.lower() in FORBIDDEN_RAW_NAMES:
            forbidden.append(rel.as_posix())

    if forbidden:
        errors.append("forbidden ROM/state/raw-dump files tracked: " + ", ".join(sorted(forbidden)))

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in ("*.smc", "*.sfc", "*.state", "*.zip"):
        if pattern not in gitignore:
            errors.append(f".gitignore missing protection: {pattern}")

    validate_progress(errors)

    if errors:
        raise SystemExit("\n".join(errors))

    print("repository validation: PASS")


if __name__ == "__main__":
    main()
