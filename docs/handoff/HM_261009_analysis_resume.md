# Shinmomo analysis restart handoff | 2026-10-09

## Canonical sources and verification

- Repository: zin1985/shinmomo; main HEAD at the start of this audit: 05c618592f85d66e9518b4e83856a28e893f47ba (2026-10-04).
- Canonical ROM in the previously designated Google Drive folder: Shin Momotarou Densetsu (J)_original.smc, 2,097,152 bytes.
- The local machine's same-named ROM was checked and SHA-256 exactly matched F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98.
- The read-only repo validator passed at this audit. This is preparation only, not new decoded ROM evidence.
- Latest changes include the BizHawk bridge publish retry (05c6185).

## Progress (no unearned percentage changes)

progress/project_progress.json is authoritative: overall 51.4%; G1 47%, G2 63%, G3 49%, G4 49%, G5 49%. Historical workstream maturity 78.0% is not whole-project completion.
Map-transition baseline: 1,295 candidates, 1,063 resolved destination configurations, 793 resolved arrival coordinates, 211 unique destination packs. Event-trigger regions: 57; 56/57 destinations have canonical configurations.
Dialogue and sprite extraction, event completeness, actor-condition integration, and portable rebuild remain incomplete.

## Next atomic work unit

1. Run: py -3 scripts/preflight_shinmomo_resume.py --remote --ci
2. Using ONLY hash-verified canonical ROM, decode pack 0x96 interval CC:DBF2..CC:DC5C in bounded record context to resolve entry 0x02..0x05 boundaries, opcodes, operands, and arrival XY. Separate confirmed facts, hypotheses and unresolved evidence.
3. Publish only derived metadata, tools and proof notes; do not commit ROM, SRAM, savestates, raw VRAM/CGRAM/OAM, or copyrighted raw payloads.
4. Refresh progress/current_task.json and docs/handoff/CURRENT.md, verify main HEAD again, commit, and check CI. Do not increase progress percentages without corresponding verified evidence.

## Subsequent priority

- Decode remaining pinned entry02 boundaries: B7 CD:5409, 9E CC:FFF7, AE CD:3639, BD CD:6CBD, B9 CD:5CAA.
- Reconcile stale event-trigger gap summary: existing JSON manifest says 11 gaps (10 arrival XY, 1 phase-dependent); a later narrative says 10 after CC:0F71 was resolved. Regenerate and prove before changing either count.
- Integrate NPC, sprite, event and dialogue provenance with map-world coordinates. Village dialogue sequencing and character/flag conditions remain important.
- Classify native $0305 writer semantics and update portable rebuild specifications.
- Preserve deferred map-dungeon work: tilesets 5/32/58, tileset 42 inherited setup/palette, and Mode-7 tilesets 2/3.

## Safety / parallel-work notes

At this audit the main worktree was clean before restarting; 42 registered worktrees existed, with tracked uncommitted modifications in 11. These modifications are NOT merged, reset, cleaned or discarded. Worktrees cover dialogue, sprite, transitions, remote lab and related viewer changes. Inspect each before integration.
Follow the project rolling protocol: verify HEAD at cycle start and immediately before changing shared files; keep progress monotonic; use workstream start/update/finish with findings, blockers and commits; never force push.
The previous map-dungeon task has been retained as deferred_pre_20261009_task in progress/current_task.json, not deleted.
