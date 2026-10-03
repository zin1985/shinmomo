# Rolling analysis cycle 2026-10-04 01:12 JST

## Source-of-truth check
- Canonical repository: `zin1985/shinmomo`, `main`.
- Start HEAD: `71437fcd209380797e7da3565f7d1a520ff609c6`.
- Rechecked `progress/project_progress.json`, latest selector catalog, recent arrival-gap cycle material, and current map/event evidence before choosing work.
- Parallel map baseline is not reopened. Current progress evidence records a newer floor of 1,295 transition candidates / 1,063 destination configurations / 793 arrival coordinates / 211 destination packs.

## Canonical ROM availability
Google Drive search did not return `Shin Momotarou Densetsu (J)_original.smc` from the designated source during this run. No substitute ROM was used. Required input for direct decode remains the designated 2,097,152-byte image with SHA-256 `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`.

## Selected theme
**Pack 0x96 multi-entry arrival frontier, starting from entry 0x02.**

Reason: the other unresolved entry-0x02 packs already have exact decode boundaries. Pack 0x96 is the remaining high-information branch because committed evidence indicates multiple destination entrances (0x02..0x05); resolving its local grammar can therefore close more than one arrival gap and provide a reusable witness for the event/transition crosslink work.

## Confirmed facts
1. Selector catalog row 150 identifies pack `0x96` record0 as `CC:DBCB..CC:DC5C`.
2. Its entry `0x01` occupies `CC:DBDB..CC:DBF2`; therefore `CC:DBF2` is the exact structural frontier immediately after entry01 and the decode start already pinned for entry02 work.
3. Pack `0x96` uses tilemap/configuration family metadata distinct from adjacent 0x95/0x97; coordinates from adjacent packs must not be copied.
4. Direct opcode/operand/XY decode at `CC:DBF2` remains canonical-ROM blocked.

## Strong hypothesis
The 0x96 entrances 0x02..0x05 are pack-local route/initializer records inside `CC:DBF2..CC:DC5C`. Once the canonical bytes at that bounded interval are available, decoding the first entry should expose the local record grammar and likely delimit the later entries without a ROM-wide scan.

## Unconfirmed
- Exact boundaries for entries 0x03, 0x04 and 0x05.
- Whether each entrance begins with opcode 0x58 or reaches a coordinate setter indirectly.
- Arrival XY for the unresolved 0x96 entrances.

## Progress decision
No arrival coordinate or new opcode semantics were closed, so percentages are deliberately unchanged: `script-vm 77% -> 77%`; project overall `51.4% -> 51.4%`. This cycle narrows the next canonical-ROM read to the bounded interval `CC:DBF2..CC:DC5C` instead of an open-ended search.

## Rolling schedule
1. **P0** Canonical-ROM decode `CC:DBF2..CC:DC5C`; recover 0x96 entry02 and delimit entries03..05.
2. **P1** Canonical-ROM decode pack 0xB7 entry02 at `CD:5409`; recover opcode/operands/arrival XY.
3. **P2** Canonical-ROM decode pack 0x9E entry02 at `CC:FFF7`; compare structurally with known 0x9F witness without copying coordinates.
4. **P3** Decode pack 0xAE entry02 at `CD:3639`, then 0xBD at `CD:6CBD` and 0xB9 at `CD:5CAA`.
5. **P4** Feed newly resolved arrivals into transition -> event/trigger crosslinks and mark superseded arrival-gap schedule items completed/merged.
6. **P5** Continue native `$0305` writer classification / collision-passability boundary work only after the arrival frontier no longer has higher information gain.

## Progress-file note
`progress/project_progress.json` remains the canonical progress source. Its current text contains legacy mojibake/control-character damage in human-readable fields, so this cycle does not perform a broad destructive rewrite merely to append this ROM-blocked refinement. The confirmed 0x96 frontier and this schedule are preserved here for lossless reconciliation when that file is safely normalized.
