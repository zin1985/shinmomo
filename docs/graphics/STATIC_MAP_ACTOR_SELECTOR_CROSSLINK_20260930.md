# Static map -> display-selector actor crosslink — 2026-09-30

## Result

A direct static bridge now connects event/map records to the display-selector table.

The proven path is:

```
map configuration
 -> pack / event family
 -> framed event record
 -> normal VM opcode 0x59
 -> display selector id
 -> static selector record
 -> CHR / palette / sprite group / animation family
```

This is the first ROM-only path that can answer "which display selector is placed in
which map context" without requiring a live object-manager capture.

## Opcode 0x59 is the actor/controller placement instruction

Normal VM opcode 0x59 dispatches through the 84:87D4 table to 84:8F93.

The handler copies its five operands to staging:

- operand 1 -> $1856
- operand 2 -> $1857
- operand 3 -> $1858
- operand 4 -> $1859
- operand 5 -> $185A

81:ADBD then allocates a controller/work slot and stores:

- $1856 -> $0859,X
- $1857 -> $0659,X
- $1858 -> $0699,X
- $1859 -> $06D9,X
- $185A -> $0719,X

81:B450 independently proves that $0859,X is a display-selector id: B450 indexes
the five-byte selector table and returns byte 2, the animation-state seed.

Therefore the static instruction format is:

```
59 <selector> <field0659_seed> <field0699_seed> <field06D9_seed> <field0719_seed>
```

The second and third seed fields behave position-like in the runtime village sample,
but this catalog deliberately keeps the WRAM field names until the coordinate units are
fully proven.

## Event-record extraction

The existing framed event catalog contains 816 structurally validated records.

For records whose body begins with opcode 0x59, the selector and four controller seeds
can be read directly from ROM. The extraction currently yields:

- 318 distinct opcode-59 actor records
- 41 unique display selectors
- 53 event families
- 40 map configurations after joining the existing map/pack crosslink
- 327 map-context rows because some event families are shared by more than one config
- zero selectors missing from the 170/170 static selector catalog

Outputs:

- `data/npc_display/static_map_actor_selector_crosslink_20260930.csv`
- `data/npc_display/static_map_actor_selector_crosslink_summary_20260930.json`
- `data/npc_display/static_map_actor_selector_by_map_20260930.json`
- `data/npc_display/static_map_bound_selector_summary_20260930.csv`
- `graphics/static_character_reconstruction/static_map_bound_selector_atlas_20260930.png`
- generators:
  - `tools/python/build_static_map_actor_selector_crosslink.py`
  - `tools/python/build_static_map_bound_selector_summary.py`

## Pack 0x50 / 旅立ちの村 validation

Pack 0x50 maps to `cfg_t04_l008_v2`.

The first nine opcode-59 records statically decode as:

| record | selector | field0659 | field0699 | field06D9 | field0719 |
| --- | --- | ---: | ---: | ---: | ---: |
| F50-L001 | 0x40 | 23 | 30 | 2 | 0 |
| F50-L002 | 0x24 | 24 | 36 | 2 | 0 |
| F50-L003 | 0x59 | 18 | 42 | 2 | 0 |
| F50-L004 | 0x59 | 25 | 45 | 2 | 0 |
| F50-L005 | 0x5A | 45 | 41 | 2 | 0 |
| F50-L006 | 0x40 | 36 | 48 | 2 | 0 |
| F50-L007 | 0x27 | 47 | 49 | 2 | 0 |
| F50-L008 | 0x25 | 11 | 34 | 2 | 80 |
| F50-L009 | 0x5B | 57 | 41 | 2 | 16 |

A live village capture was used only as validation. Controller slots 9..17 contained
the exact same nine selector ids in the exact same order.

More strongly, the three controller pointer columns
`$0799/$07D9/$0819` matched each record's static trailer pointer exactly:

- F50-L001 -> CC:1D0F
- F50-L002 -> CC:1D2D
- F50-L003 -> CC:1D4B
- F50-L004 -> CC:1D69
- F50-L005 -> CC:1D8F
- F50-L006 -> CC:1DAD
- F50-L007 -> CC:1DD3
- F50-L008 -> CC:1DF1
- F50-L009 -> CC:1E02

Result: **9/9 selector matches and 9/9 pointer matches**.

The derived validation scalars are stored in
`data/npc_display/runtime_pack50_static_selector_validation_20260930.json`.
Raw WRAM remains local-only.

## Existing pointer bridge

Opcode 0x59 also copies the current event pointer from DP $A4/$A5/$A6 into
$185B/$185C/$185D; 81:ADBD stores that value into
$0799/$07D9/$0819. This links each created actor controller back to its event
record / keyed behavior table.

The earlier analysis in
`docs/analysis/event_controller_pointer_bridge.md` remains valid; the new result adds
the missing semantic meaning of operand 1 / $0859: **display selector id**.

## Current map coverage and caveat

The current static crosslink covers every framed event record whose body starts with opcode
0x59. This is a strong exact subset, not yet every possible actor creation path.

Map binding is recorded as `pack_family_context`. When one event family is shared by
multiple map configurations, the actor row is associated with each compatible configuration
rather than falsely choosing one.

At present only pack 0x50 has a human map label promoted in this file. The other 39
configuration ids are structurally known but still need the separate map-name/location
catalog work.

## Most reused map-bound selectors

The current subset already shows strong reuse:

- selector 0x40: 14 map configs / 25 event records
- selector 0x43: 13 map configs / 24 records
- selector 0x59: 10 map configs / 13 records
- selector 0x5A: 10 map configs / 13 records
- selector 0x30: 9 map configs / 15 records
- selector 0x2F: 8 map configs / 11 records

This is useful for later semantic clustering: highly reused humanoid-looking selectors are
likely generic NPC families, while low-frequency monster/animal/object shapes can be checked
against event behavior and dialogue.

## What is still separate

This does not yet assign every selector to "NPC / enemy / animal" as a semantic fact.
The static pixels give visual form, but allegiance/role must come from behavior/event/dialogue
evidence. The map-bound selector atlas is therefore intentionally unclassified by default.

The next static layers are:

1. parse instruction-aligned opcode 0x59 occurrences that appear later inside longer event bodies,
   not only bodies whose first instruction is 0x59;
2. bind selector rows to dialogue/event semantics and controller behavior keys;
3. merge human-readable map/location labels;
4. connect the separate logical-actor path ($1569 ids) and special/event object-preset path
   to the same selector-centric catalog.
