# Event-trigger destination-config gap priority (2026-10-03)

## Scope
This cycle starts from the committed 15-row crosslink gap manifest and narrows the five `destination_config_only` rows into a deterministic static-analysis queue. No transition corpus, map renderer, or viewer logic is re-extracted/reimplemented.

## Confirmed facts
The five rows already have source config, trigger geometry and arrival coordinates, but lack canonical destination config:

| priority | transition | source config | trigger | arrival XY | next static evidence |
|---:|---|---|---|---|---|
| 1 | `CC:1CC0` | `cfg_t04_l008_v2` | point | `(6,10)` | resolve destination pack/entry from the local non-world-map source first, then join to canonical config |
| 2 | `CC:0BCA` | `cfg_t01_l001_v1` | rectangle | `(37,56)` | resolve destination pack/entry/config |
| 3 | `CC:0C17` | `cfg_t01_l001_v1` | rectangle | `(36,72)` | resolve destination pack/entry/config |
| 4 | `CC:0E0D` | `cfg_t01_l001_v1` | rectangle | `(37,15)` | resolve destination pack/entry/config |
| 5 | `CC:1160` | `cfg_t01_l001_v1` | point | `(22,28)` | resolve destination pack/entry/config |

`CC:1CC0` is first because it is the only config-only gap whose source is not the shared world configuration `cfg_t01_l001_v1`. It therefore has the best chance of yielding a locally constrained pack/entry relation without conflating the four world-map cases.

## Strong interpretation
The five config-only gaps should not be attacked as coordinate-matching problems. Arrival XY is not globally unique enough to identify a canonical configuration. The correct join key remains destination pack/entry provenance from the transition payload or its native/VM consumer, followed by the existing pack/config mapping.

## Not claimed
- No destination config is inferred from arrival coordinate similarity.
- No map identity is inferred from trigger shape or source metatile.
- The four world-map rows are not assumed to share a destination family.
- This cycle does not change terrain passability, collision, or object-occupancy conclusions.

## Drive ROM status
The designated Drive ROM was not accessible in this run, so no ROM bytes were read and no substitute ROM was used. Runtime/ROM validation remains blocked until `Shin Momotarou Densetsu (J)_original.smc` is accessible and can be checked against size 2,097,152 bytes and SHA-256 `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`.

## Next analysis
Trace `transition_CC_1CC0` first to its destination pack/entry payload and canonical config. If that closes cleanly, apply the same provenance join to `CC:0BCA`, `CC:0C17`, `CC:0E0D`, and `CC:1160`; only then move to the ten arrival-XY-only gaps.
