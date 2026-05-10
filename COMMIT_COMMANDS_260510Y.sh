#!/usr/bin/env bash
set -euo pipefail

git status --short

git add README.md NOT_INCLUDED_ROM.txt COMMIT_COMMANDS_260510Y.sh \
  docs/handoff/HM_260510Y.md \
  docs/analysis/*.md \
  data/runtime/*.csv \
  data/bg/*.csv \
  data/battle/*.csv \
  tools/python/*.py \
  tools/lua/*.lua \
  manifest/*.md

git status --short

git commit -m "handoff: preserve scheduled goal13 core graphics bridge state" \
  -m "- consolidate scheduled core and graphics analysis outputs" \
  -m "- preserve $0799 finalize-branch append-domain model" \
  -m "- preserve execution_frame/cutoff_index graphics-core bridge workflow" \
  -m "- include manifest, excluded-file notes, goal progress, next tasks" \
  -m "- no ROM binaries, no raw dumps, no nested archives"
