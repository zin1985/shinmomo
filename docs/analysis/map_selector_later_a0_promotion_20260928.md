# Later-record map selector promotion through state0 A0 nested entries

Updated: 2026-09-28

## Result

The later-record selector backlog is reduced by proving that selected substreams are entered directly by compact opcode A0 from already-proven state0 record0/entry1 execution.

Canonical selector counts after this pass:

- primary shapes: **263**
- confirmed normal primary: **260**
- unresolved primary: **3**
- immediate primary+secondary pairs: **105**
- confirmed immediate secondary pairs: **105 / 105**

Sixteen previously unresolved later-record primaries are newly promoted.

## A0 state-preservation proof

The compact A0 handler at C4:846F is fail-closed anchored by exact bytes in `catalog_map_selectors.py`. It saves the caller VM context, advances/pushes the continuation, loads the embedded 24-bit nested target into $98/$99/$9A, increments $1266, and returns to the scheduler. The anchored body contains no $1398/$1399 write and no C0:C9E7 re-entry.

A target is accepted as a state0 nested-entry seed only when all of these are true:

1. the A0 byte is itself an instruction boundary reachable from the proven state0 record0/entry1 start through the existing fail-closed CFG;
2. the embedded 24-bit A0 target is exactly a parsed substream start;
3. target and caller belong to the same canonical pack;
4. the target substream reaches the candidate 0x50 through the same fail-closed state0 CFG;
5. descriptor-driven 0x10/0x33 operations resolve only to the already-cleared B910 targets B924/B944.

## Newly promoted later-record selectors

| pack | record | entry | A0 caller(s) | nested start | primary 0x50 | config | B910 | branch | secondary |
|---|---:|---:|---|---|---|---|---|---|---|
| 0xED | 1 | 0x90 | CD:E28F | CD:E327 | CD:E330 | 1/1/1 | C0:B944 | False | - |
| 0xED | 2 | 0x90 | CD:E29B | CD:E34F | CD:E353 | 20/117/1 | C0:B924 | False | CD:E357 |
| 0xED | 14 | 0x90 | CD:E2B3 | CD:E6DC | CD:E6E5 | 1/1/1 | C0:B944 | False | - |
| 0xED | 19 | 0x90 | CD:E2BF<br>CD:E2CB | CD:E7CA | CD:E7CE | 1/1/1 | C0:B944 | False | - |
| 0xEE | 4 | 0x6C | CD:E913 | CD:EAE1 | CD:EAEE | 1/2/1 | C0:B944 | False | - |
| 0xEE | 5 | 0x6C | CD:E91F | CD:EB23 | CD:EB29 | 1/2/1 | C0:B944 | False | - |
| 0xEE | 6 | 0x6C | CD:E92B | CD:EB68 | CD:EB75 | 1/2/1 | C0:B944 | False | - |
| 0xEE | 8 | 0x6C | CD:E937 | CD:EC07 | CD:EC1B | 4/91/1 | C0:B944 | True | - |
| 0xF0 | 1 | 0x6C | CD:F68B | CD:F6D8 | CD:F6E1 | 1/1/1 | C0:B944 | False | - |
| 0xF0 | 2 | 0x6C | CD:F677 | CD:F6F7 | CD:F6FF | 4/8/2 | C0:B944 | False | - |
| 0xF0 | 3 | 0x6C | CD:F64C | CD:F710 | CD:F719 | 1/2/1 | C0:B944 | False | - |
| 0xF1 | 2 | 0x6C | CD:F9CE | CD:FA72 | CD:FA80 | 1/1/1 | C0:B944 | False | - |
| 0xF1 | 3 | 0x6C | CD:F9DA | CD:FAC3 | CD:FAC9 | 26/131/1 | C0:B924 | False | - |
| 0xF1 | 4 | 0x6C | CD:F9E6 | CD:FB36 | CD:FB40 | 4/8/2 | C0:B944 | False | - |
| 0xF1 | 5 | 0x6C | CD:F9F2 | CD:FBBE | CD:FBCB | 2/3/1 | C0:B944 | False | - |
| 0xF1 | 6 | 0x6C | CD:F9FE | CD:FC20 | CD:FC22 | 7/7/2 | - | False | - |

## Final immediate secondary pair

Pack 0xED record 2 / entry 0x90 is now resolved:

- proven state0 caller: **CD:E29B**
- A0 target / nested substream start: **CD:E34F**
- primary selector: **CD:E353** = tileset 20 / layout 117 / variant 1
- immediate secondary selector: **CD:E357**
- nested-prefix B910 target: **C0:B924**
- CFG branch before primary: none

Because the parent 0x50 is now confirmed normal and normal 0x50 does not change $1398, the immediately following 0x51 is also promoted. This closes the last unresolved immediate primary+secondary pair.

## Remaining unresolved primary selectors

Only three rows remain:

| pack | record | entry | substream | primary | config |
|---|---:|---:|---|---|---|
| 0x7F | 3 | 0x88 | CC:A6CE | CC:A71F | 42/99/1 |
| 0x9D | 4 | 0x6D | CC:FD57 | CC:FD5C | 14/82/1 |
| 0x9D | 5 | 0x6C | CC:FE68 | CC:FE6D | 16/77/1 |

These are:

- pack 0x7F record 3 / entry 0x88
- pack 0x9D record 4 / entry 0x6D
- pack 0x9D record 5 / entry 0x6C

They are not promoted by this pass because no proven state0 A0 edge targets their substream start.

## Reproducible evidence

- `tools/python/catalog_map_selectors.py`
- `data/maps/selectors/state0_a0_nested_promotions.csv`
- `data/maps/selectors/primary_map_selector_catalog.csv`
- `data/maps/selectors/secondary_map_selector_candidates.csv`
- `data/maps/selectors/primary_map_selector_summary.json`

## Next work

1. Resolve entry-family reachability for the remaining 0x7F/e88 and 0x9D/e6D/e6C rows.
2. Do not borrow the state0 entry1 assumption unless an explicit caller edge proves it.
3. Once the three rows are classified, move from selector semantics to human-facing town/interior/dungeon/world labels.
