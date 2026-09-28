# Map configuration and dialogue-context index

Updated: 2026-09-28

## Configuration index

The closed primary-selector corpus contains 260 confirmed instruction-level
opcode-0x50 occurrences.

`tools/python/build_map_configuration_index.py` groups them by:

`(primary_tileset_id, primary_layout_id, map_variant)`

Result:

- primary occurrences: 260
- unique configurations: **149**
- configurations with an immediate secondary map: **51**
- distinct immediate-secondary configurations: **49**
- maximum reuse count for one primary configuration: **9**

Output:

`data/maps/configurations/map_configuration_index.csv`
The index preserves, per configuration:

- exact CE tileset pointer and CF layout pointer;
- layout flags and logical metatile dimensions;
- every pack/record/entry occurrence;
- every primary command address;
- immediate-secondary configuration set;
- evidence-class counts.

The known stable interior is represented as:

`cfg_t07_l015_v2`

It is the only configuration currently carrying a scene-class hint
(`indoor`), because it has direct runtime evidence.
No human-facing place name is assigned.
## Dialogue source-family cross-link

Existing dialogue work proves that for real packs 0x14..0xF9:

`CA script-pack index == C7 source-family index`

`tools/python/build_map_dialogue_context_crosslink.py` applies that exact join
to every confirmed map-selector occurrence.

Result:

- map occurrences joined to a source family: **260 / 260**
- distinct map packs represented: **209**
- occurrences with an already curated semantic dialogue context: **2**
- configurations with such semantic context: **2**

Outputs:

- `data/maps/context/map_dialogue_pack_crosslink.csv`
- `data/maps/context/map_dialogue_pack_crosslink_summary.json`
The two context-bearing configurations are:

- `cfg_t07_l007_v2`, pack 0x4E
- `cfg_t04_l008_v2`, pack 0x50

These are deliberately marked `context_only`, not named locations.

Pack 0x4E contains contexts spanning a hermitage, farmland, shrine/save advice
and event reactions. Pack 0x50 spans multiple story/location references
including Urashima, Yoro, Netaro, Ice Tower and Hope Capital.

Therefore pack-level dialogue provenance is useful search context but is not
sufficient to assert one human-facing map name.

## First runtime-bound occurrence

The frame-3253 stable interior now provides the first exact runtime join.
Its scalar state has $0305=$126E=$12B4=0x2E and selector 7/15/2.

The selector alone matches three confirmed occurrences, but pack 0x2E reduces
that set to exactly one:

`cfg_t07_l015_v2 -> pack 0x2E -> record 0 / entry 0x01 -> CB:DE70`

`tools/python/resolve_map_runtime_identity.py` reproduces this join from
`data/maps/samples/stable_interior_runtime_identity.json`.
The configuration index now records one runtime-bound configuration and one
runtime-bound unique occurrence. The exact in-game place name remains unset.

## Next bridge

Future map captures should store small derived WRAM metadata, not a raw WRAM
dump:

- current pack id $0305
- current VM pack context $126E / $12B4 when available
- mode state $1398 / pending $1399
- primary selectors $139C / $139E / $139B
- secondary selectors $139D / $139F

That metadata can join a visited screen directly to one of the 260 confirmed
ROM selector occurrences while keeping raw runtime memory out of Git.

This should make human location labeling substantially more reliable than
inferring names from dialogue text alone.
