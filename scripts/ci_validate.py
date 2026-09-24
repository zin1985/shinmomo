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
]
FORBIDDEN_SUFFIXES = {
    ".smc", ".sfc", ".fig", ".swc", ".bs", ".srm", ".sav", ".state", ".7z"
}


def validate_progress(errors: list[str]) -> None:
    path = ROOT / "progress" / "project_progress.json"
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid progress JSON: {exc}")
        return

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
        print(f"dashboard overall progress: {weighted / total_weight:.1f}%")


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
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            forbidden.append(rel.as_posix())

    if forbidden:
        errors.append("forbidden ROM/state/archive files tracked: " + ", ".join(sorted(forbidden)))

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
