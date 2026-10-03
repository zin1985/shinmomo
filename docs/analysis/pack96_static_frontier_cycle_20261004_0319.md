# Pack 0x96 static frontier cycle — 2026-10-04 03:19 JST

## Cycle decision
Highest-value unresolved theme remains the pack `0x96` multi-entry arrival frontier because one bounded decode can potentially resolve four missing arrival-coordinate entries (`0x02..0x05`) and provide grammar evidence reusable by the other pinned entry-0x02 gaps.

## Canonical-source checks
- Repository source of truth: `zin1985/shinmomo` main.
- Starting HEAD: `a746220b0c1d1427597ad7d9395a985935359d2d`.
- `progress/project_progress.json` parses again after the preceding CI-recovery cycle and retains overall 51.4%, script-vm 77%, externalization 79%.
- Current rolling priority 1 is the bounded pack96 interval `CC:DBF2..CC:DC5C`; priority 2 is the five pinned entry02 boundaries B7=`CD:5409`, 9E=`CC:FFF7`, AE=`CD:3639`, BD=`CD:6CBD`, B9=`CD:5CAA`.
- Latest map baseline remains monotonic over the 2026-09-29 baseline: 1,295 transition candidates, 1,063 destination configurations, 793 arrival coordinates, 211 destination packs. No completed map renderer/structural-world work was reopened.

## Canonical ROM availability
Google Drive search did not expose `Shin Momotarou Densetsu (J)_original.smc` in this execution environment. Therefore no ROM bytes were read and no substitute ROM was used. Required input remains the named Drive ROM, expected size 2,097,152 bytes and SHA-256 `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`.

## Confirmed facts
1. Pack `0x96` record0 is bounded by committed selector metadata and entry01 ends at `CC:DBF2`; this is the established structural start for entry02.
2. Committed transition metadata already proves entries `0x02..0x05` are arrival gaps for the same canonical configuration `cfg_t09_l098_v2`; no arrival XY is assigned here.
3. The bounded decode target remains `CC:DBF2..CC:DC5C`. This cycle does not infer entry03..05 boundaries from spacing or from another pack.
4. GitHub Actions run #395 for the preceding CI-recovery commit completed successfully. The repository validator is therefore green again at the starting HEAD.

## Strong hypothesis
The bounded interval contains pack-local entry initializer/route structure sufficient to separate at least some of entries `0x02..0x05`; if confirmed on the canonical ROM, its grammar may transfer structurally to the other pinned entry02 packs. Coordinate values remain pack-local until proven.

## Unconfirmed
- Exact opcode/operand sequence at `CC:DBF2`.
- Entry03, entry04 and entry05 exact start addresses.
- Arrival coordinates for pack96 entries `0x02..0x05`.

## Progress decision
No new arrival coordinate or opcode semantics were confirmed, so percentages must not move: overall `51.4% -> 51.4%`, script-vm `77% -> 77%`, externalization `79% -> 79%`.

## Rolling schedule
1. Decode canonical-ROM interval `CC:DBF2..CC:DC5C` after size/hash verification; resolve pack96 entries `0x02..0x05` without copying witness XY.
2. Decode pinned entry02 starts B7 `CD:5409`, 9E `CC:FFF7`, AE `CD:3639`, BD `CD:6CBD`, B9 `CD:5CAA` using canonical ROM only.
3. Resolve visible-object coordinates to canonical map-world coordinates.
4. Integrate NPC/sprite/event/dialogue provenance into one actor/event model.
5. Classify native `$0305` writers and separate controller/event/map semantics.
6. Promote confirmed map/boundary/trigger/object semantics into rebuild schemas and the rebuild-gap manifest.

## Promotion note
The preceding run #395 is green, but Drive promotion cannot be safely performed here because the execution environment did not resolve the intended `Projects/shinmomo/latest` folder identity to a unique writable folder. Do not guess a destination from same-named files. The new commit from this cycle must itself pass Actions before any promotion.
