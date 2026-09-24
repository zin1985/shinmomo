from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    ROOT / "project.yml",
    ROOT / "VERSION",
    ROOT / "CHANGELOG.md",
    ROOT / ".gitignore",
    ROOT / "manifest" / "EXCLUDED.md",
]
FORBIDDEN_SUFFIXES = {
    ".smc", ".sfc", ".fig", ".swc", ".bs", ".srm", ".sav", ".state", ".7z"
}


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

    if errors:
        raise SystemExit("\n".join(errors))

    print("repository validation: PASS")


if __name__ == "__main__":
    main()
