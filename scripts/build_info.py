from __future__ import annotations

import datetime as dt
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def git(*args: str) -> str:
    try:
        value = subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
        return value or "unknown"
    except Exception:
        return "unknown"


def project_value(key: str, default: str = "unknown") -> str:
    path = ROOT / "project.yml"
    if not path.exists():
        return default
    prefix = f"{key}:"
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith(prefix):
            value = line[len(prefix):].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            return value or default
    return default


def main() -> None:
    DIST.mkdir(exist_ok=True)
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    branch = os.environ.get("GITHUB_REF_NAME") or git("branch", "--show-current")
    commit = os.environ.get("GITHUB_SHA") or git("rev-parse", "HEAD")
    lines = [
        f"project={project_value('name', 'shinmomo')}",
        f"build_at={dt.datetime.now(dt.timezone.utc).isoformat()}",
        f"version={version}",
        f"branch={branch or 'unknown'}",
        f"commit={commit}",
        f"change_summary={project_value('change_summary')}",
        "build_result=PASS",
    ]
    (DIST / "build-info.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
