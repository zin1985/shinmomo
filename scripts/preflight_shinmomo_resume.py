#!/usr/bin/env python3
"""Read-only preflight for resuming Shinmomo analysis.

Does not decode, copy, expose or commit ROM contents.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA256 = "f6a345e2f07f0cbc4eff7d4ff06ae88a814a98fdf100c7bf7351168c73916a98"

def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=35, check=True).stdout.strip()

def check_rom(rom):
    if not rom.is_file():
        raise FileNotFoundError(f"canonical ROM not found: {rom}")
    size = rom.stat().st_size
    digest = hashlib.sha256()
    with rom.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if size != EXPECTED_SIZE or actual != EXPECTED_SHA256:
        raise ValueError(f"ROM identity mismatch: size={size}, SHA256={actual}")
    print(f"ROM identity: PASS ({size} bytes, SHA256={actual})")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, help="verified canonical ROM path, if not in the known local Downloads location")
    parser.add_argument("--ci", action="store_true", help="run repository validator after identity checks")
    parser.add_argument("--remote", action="store_true", help="verify GitHub origin main HEAD (requires network)")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    rom = args.rom or (Path.home() / "Downloads" / "Shin Momotarou Densetsu (J)" / "Shin Momotarou Densetsu (J)_original.smc")
    check_rom(rom)
    branch = git(repo, "branch", "--show-current")
    head = git(repo, "rev-parse", "HEAD")
    print(f"Git branch: {branch or '(detached)'}; HEAD={head}")
    if args.remote:
        lines = git(repo, "ls-remote", "origin", "refs/heads/main").splitlines()
        if not lines or lines[0].split()[0] != head:
            raise RuntimeError("local HEAD differs from origin/main; reconcile without reset or force")
        print("Remote main HEAD: PASS")
    summary = json.loads((repo / "progress" / "project_progress.json").read_text(encoding="utf-8"))
    task = json.loads((repo / "progress" / "current_task.json").read_text(encoding="utf-8"))
    gaps = json.loads((repo / "data" / "events" / "event_trigger_crosslink_gaps_summary.json").read_text(encoding="utf-8"))
    print(f"Progress: overall={summary['overall_percent']}%; task={task['workstream']} ({task['status']})")
    print(f"Gap manifest: {gaps['gap_count']} (reconcile with narrative report of 10 before promotion)")
    dirty = git(repo, "status", "--porcelain=v1")
    if dirty:
        print("WARNING: main worktree contains local changes; inspect before commit")
    else:
        print("Main worktree: clean")
    if args.ci:
        completed = subprocess.run([sys.executable, str(repo / "scripts" / "ci_validate.py")], cwd=repo)
        if completed.returncode:
            raise RuntimeError(f"repository validator failed: {completed.returncode}")
    print("Resume preflight: PASS")

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Resume preflight: FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
