from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
FORBIDDEN_SUFFIXES = {
    ".smc", ".sfc", ".fig", ".swc", ".bs", ".srm", ".sav", ".state", ".zip", ".7z"
}
SKIP_PARTS = {".git", "dist", "__pycache__", ".pytest_cache", ".venv"}


def include(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in SKIP_PARTS for part in rel.parts):
        return False
    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        return False
    return path.is_file()


def write_source_zip(destination: Path) -> None:
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            if include(path):
                archive.write(path, path.relative_to(ROOT))


def main() -> None:
    DIST.mkdir(exist_ok=True)
    source_zip = DIST / "source.zip"
    write_source_zip(source_zip)

    shutil.copy2(ROOT / "CHANGELOG.md", DIST / "CHANGELOG.md")

    bundle = DIST / "shinmomo-analysis.zip"
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            if not include(path):
                continue
            archive.write(path, path.relative_to(ROOT))
        archive.write(source_zip, "source.zip")
        archive.write(DIST / "build-info.txt", "build-info.txt")
        archive.write(DIST / "CHANGELOG.md", "CHANGELOG.md")


if __name__ == "__main__":
    main()
