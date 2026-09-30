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

The extractor now keeps two separate fail-closed evidence classes:

- body-head opcode 0x59: the original exact case;
- body-tail opcode 0x59: the final six bytes of a framed VM body are exactly
  `59 <selector> <five-byte-command remainder>`, with the selector present in the
  proven static selector catalog.

The current union yields:

- 752 distinct opcode-59 actor records
- 318 body-head records
- 434 additional body-tail records
- 68 unique display selectors
- 105 event families
- 75 map configurations after joining the existing map/pack crosslink
- 817 map-context rows because some event families are shared by more than one config
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
0x59 plus the additional framed records whose body ends in one complete six-byte opcode-0x59
actor command. The two evidence classes remain distinct in the CSV. This is still not every
possible actor creation path: instruction-aligned 0x59 commands in the middle of longer bodies
require CFG parsing before promotion.

Map binding is recorded as `pack_family_context`. When one event family is shared by
multiple map configurations, the actor row is associated with each compatible configuration
rather than falsely choosing one.

At present only pack 0x50 has a human map label promoted in this file. The other 74
configuration ids are structurally known but still need the separate map-name/location
catalog work.

## Reuse and coverage

The tail-aligned expansion changes the reuse rankings substantially, so selector reuse is now
derived from the generated CSV/JSON rather than frozen as a hand-maintained list in this note.
The important structural result is the coverage jump from 41 to 68 selectors and from 40 to
75 map configurations. Reuse remains useful for later semantic clustering, but role assignment
still requires behavior, dialogue, or other independent evidence.

## What is still separate

This does not yet assign every selector to "NPC / enemy / animal" as a semantic fact.
The static pixels give visual form, but allegiance/role must come from behavior/event/dialogue
evidence. The map-bound selector atlas is therefore intentionally unclassified by default.

The next static layers are:

1. prove instruction-aligned opcode 0x59 occurrences in the middle of longer event bodies
   with the bank84 VM CFG, rather than raw byte search;
2. bind selector rows to controller behavior keys and classify stationary/wandering/scripted roles;
3. merge human-readable map/location labels;
4. connect the separate logical-actor path ($1569 ids) and special/event object-preset path
   to the same selector-centric catalog.
