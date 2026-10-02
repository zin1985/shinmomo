# Event-trigger destination config bounds disambiguation ? 2026-10-03 02:14 JST

## Scope

This cycle addresses the five `destination_config_only` trigger gaps using committed static evidence only. The designated Google Drive ROM was not accessible in this run, so no substitute ROM was used and no new ROM-derived bytes were generated.

## Method

For each transition with a known destination pack and committed arrival `(x,y)`, enumerate committed `map_native_bounds_catalog.csv` rows for that pack. Keep only configs whose inclusive opcode-0x52 bounds contain the arrival coordinate. Promote a destination config only when exactly one config survives. This is stricter than sibling-order or coordinate-neighbor inference.

## Confirmed resolutions

| trigger | pack | arrival | unique config | discriminator |
|---|---:|---:|---|---|
| `CC:0BCA` | `0x60` | `(37,56)` | `cfg_t04_l035_v2` | only committed 0x60 config bounds contain arrival |
| `CC:0C17` | `0x68` | `(36,72)` | `cfg_t06_l038_v2` | only committed 0x68 config bounds contain arrival |
| `CC:0E0D` | `0x81` | `(37,15)` | `cfg_t04_l058_v2` | only committed 0x81 config bounds contain arrival |
| `CC:1CC0` | `0x2C` | `(6,10)` | `cfg_t07_l011_v2` | 0x2C also maps to `cfg_t07_l033_v2`, but that config has native Y max 8; arrival Y=10 excludes it. `cfg_t07_l011_v2` has Y max 10. |

`CC:1160` remains unresolved and is not promoted.

## Wider result

The generic resolver finds 110 previously unresolved transition rows where destination pack + committed arrival XY + committed native bounds leave exactly one config. This derived overlay is machine-readable and does not rewrite raw transition extraction. For the 57 normalized trigger regions, destination config coverage improves 52?56, complete region crosslinks improve 42?46, and the gap manifest shrinks 15?11 (destination-config-only 5?1; arrival-XY-only remains 10).

## Evidence classes

- **Confirmed from committed evidence:** the four unique bounds intersections above and the 110-row derived overlay.
- **Strong hypothesis:** none required for the four promoted rows.
- **Unconfirmed:** `CC:1160` destination config; all ten arrival-XY-only gaps.

## Next target

Resolve `CC:1160` using pack/entry/config provenance that does not rely on spatial guessing. Then move to the ten arrival-XY-only gaps.
