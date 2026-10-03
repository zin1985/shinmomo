# Cross-pack arrival entry-ID frontier — 2026-10-03

## Confirmed facts

The nine remaining `arrival_xy_only` trigger gaps collapse into only three destination entry IDs. Entry `0x02` accounts for six gaps across six distinct packs (`0x96`, `0x9E`, `0xAE`, `0xB7`, `0xBD`, `0xB9`). Entry `0x07` accounts for two gaps across packs `0x91` and `0xB6`. Entry `0x0C` occurs once (`0xA8`).

This is a stronger static frontier than treating pack `0x96` alone: an entry-ID-level grammar, if confirmed, could close several packs at once. The committed transition catalog still contains no same `(pack,entry)` coordinate witness for these gaps.

## Strong hypothesis

Arrival-coordinate initialization may contain reusable entry-ID semantics above pack-local map selection. Entry `0x02` is the highest-information probe because it spans six unrelated destination packs.

## Unconfirmed

No coordinate, map edge, facing, or direction meaning is assigned to `0x02`, `0x07`, or `0x0C`. Recurrence alone does not prove identical coordinates or identical behavior.

## ROM policy

Drive指定ROMへアクセスできなかった. No substitute ROM was used. This cycle uses committed metadata only.
