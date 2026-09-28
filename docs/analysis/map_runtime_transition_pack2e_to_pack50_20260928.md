# Runtime map transition: pack 0x2E interior -> pack 0x50 exterior

Updated: 2026-09-28

## Result

The active BizHawk Lua bridge was refreshed from the current repository file and a fresh map capture returned manifest schema version 2. The schema-v2 capture reproduced the already proven stable-interior state at frame 3253:

- pack $0305/$126E/$12B4 = 0x2E
- mode $1398/$1399 = 0
- selector = tileset 7 / layout 15 / variant 2
- exact ROM occurrence = pack 0x2E / CB:DE70

Walking south through the central room exit produced a directly observed map transition to:

- pack $0305/$126E/$12B4 = 0x50
- mode $1398/$1399 = 0
- selector = tileset 4 / layout 8 / variant 2
- configuration = cfg_t04_l008_v2
- exact ROM occurrence = pack 0x50 / record 0 / entry 0x01 / CC:1C3F

The selector-only configuration has three ROM occurrences, but runtime pack 0x50 makes CC:1C3F unique.

## Transition phases
Observed schema-v2 manifests show the transition order clearly:

| frame | observed phase | $0305 | $126E/$12B4 | selector |
|---:|---|---:|---:|---|
| 3277 | destination pack selected while old room still visible | 0x50 | 0x2E | 7/15/2 |
| 3315 | black transition / selector cleared | 0x50 | 0x50 | 0/0/0 |
| 3357 | new selector installed while screen remains black | 0x50 | 0x50 | 4/8/2 |
| 3447 | destination exterior visible | 0x50 | 0x50 | 4/8/2 |

This gives the first runtime-confirmed map edge:

`CB:DE70 -> CC:1C3F`

The target view is a forest shrine/village exterior with cultivated fields and village buildings south of the shrine.

## Human-facing name

The exact in-game location name has not yet been obtained from game text, so `display_name` remains blank.

A strong external corroboration candidate is **旅立ちの村**: the current playlog shows 桃太郎1段・銀次1段・100両, matching published opening walkthroughs that place this exact starting state immediately before the first visit to 旅立ちの村. Independent location references also describe 旅立ちの村 as containing a shrine and fields.

This candidate must remain separate from the confirmed ROM/runtime identity until an in-game text, event, or other direct location-name source is captured.
## Canonical derived evidence

- `data/maps/samples/stable_interior_runtime_identity.json`
- `data/maps/samples/pack50_shrine_exterior_runtime_identity.json`
- `data/maps/samples/pack50_shrine_exterior_runtime_resolution.json`
- `data/maps/transitions/stable_interior_to_pack50_shrine_exterior_20260928.json`
- `data/maps/configurations/map_configuration_index.csv`
- `data/maps/configurations/map_configuration_summary.json`
- `tools/python/resolve_map_runtime_identity.py`

Raw screenshots, VRAM/CGRAM files and local capture manifests remain outside Git.

## External corroboration used only for the label candidate

- 新桃太郎伝説 攻略チャート1 OP～花咲き村: https://tvgamedb.com/snec/shinmomoden/kouryaku-1/
- 旅立ちの村: https://shinmomotaroudennsetu.kouryaku.red/entry21.html
- 新桃太郎伝説 オープニング: https://asami-book.com/shinmomo-1/

## Next

1. Obtain direct in-game text or event evidence naming the pack-0x50 village.
2. Promote the human-facing name only after that independent confirmation.
3. Use the confirmed CB:DE70 -> CC:1C3F edge as the first warp/transition-layer record.
4. Continue binding additional visited maps through schema-v2 captures.
