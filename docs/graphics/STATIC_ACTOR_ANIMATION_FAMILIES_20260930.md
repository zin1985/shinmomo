# Static actor animation family catalog — 2026-09-30

The ROM-only display-selector reconstruction has now been extended from one representative
frame per selector to animation-family extraction.

## Coverage

Among the 158 unique reconstructable graphics signatures:

- 123 have a nearby contiguous four-state / two-frame family.
- 105 of those are in sprite groups 2 or 3, where runtime village/player tracing has
  directly confirmed the state order as right, down, left, up.
- 12 additional group-4/group-5/group-7 families are now resolved as directional, bringing
  the unique confirmed total to 117. Eight are directly visual-confirmed; four inherit the
  exact same group/state family from a visual-confirmed peer.
- No four-state/two-frame direction candidate remains unclassified.
- 2 four-state families are explicitly direction-invariant: all four states render the same
  frame pair, so direction has no visible effect.
- 4 four-state/two-frame families are now classified as pose/animation sequences rather than
  four-direction walk families.
- 25 signatures have a fixed one-frame base state.
- 10 signatures begin with longer/special animation sequences.

The family finder searches up to seven states after the selector's base state. This matters
because many actors have an idle or transition state before their normal directional walk.

Observed offsets from selector base state to the detected 4x2 family:

- +0: 93
- +1: 17
- +2: 3
- +3: 2
- +4: 5
- +5: 3

For example, several group-2 NPC selectors use a fixed idle state first, followed by the
four directional states. The runtime-confirmed elder NPC is one such pattern.

## Directional order

For groups 2 and 3 the order is:

1. right
2. down/front
3. left
4. up/back

This order is supported by live movement observations for Momotaro and multiple village NPCs.

For groups 4, 5, and 7 the catalog remains neutral by default. A family is promoted only
when independent evidence resolves its semantics. C1:9090 converts motion pattern 1..4 to
animation offsets 0..3, while the 81:81D3/81D4 delta table proves 1=right, 2=down/front,
3=left, 4=up/back. Direct visual inspection confirms that ordering for selectors 0x17, 0x29,
0x6A, 0x76, 0x7F, 0x9E, 0x9F, and 0xA3. Selectors 0x5F, 0x60, 0x83, and 0x9D reuse the exact
same group/state families as 0x17, 0x6A, 0x7F, and 0x9E respectively, so the proven state
order is inherited without claiming that their own CHR windows can render those family frames.

## Non-directional / direction-invariant families

The 35 families that never matched the nearby four-state/two-frame shape remain separate:

- 25 fixed-base actors/objects
- 10 special-sequence actors/objects

Among the 123 four-state/two-frame shapes, six are also deliberately excluded from the
four-direction count after visual review:

- 0x5C and 0x5D: direction-invariant four-state objects; every slot uses the same frame pair.
- 0x77, 0x7C, 0x7D, and 0x9C: four-state pose/animation sequences whose frames do not form
  right/front/left/back.

The special atlas preserves the base-state frame sequence in order, including repeated
frames. Semantic character names should not be inferred from graphics alone.

## Outputs

- `data/npc_display/static_actor_animation_family_catalog_20260930.csv`
- `data/npc_display/static_actor_animation_family_summary_20260930.json`
- `data/npc_display/group5_group7_directional_family_evidence_20260930.csv` (legacy/subset evidence)
- `data/npc_display/static_directional_family_resolution_20260930.csv` (current resolution catalog)
- `data/npc_display/actor_motion_direction_pattern_table_20260930.csv`
- `data/npc_display/static_character_directional_catalog_20260930.csv`
- `graphics/static_character_reconstruction/static_directional_animation_atlas_20260930.png`
- `graphics/static_character_reconstruction/static_special_animation_atlas_20260930.png`
- `tools/python/build_static_actor_animation_catalog.py`
- `tools/python/resolve_static_directional_families_20260930.py`

The directional atlas renders all eight frames for each detected four-state/two-frame family. Selectors 0x20 and 0xA9 are now included after graphics-reader dispatch 4 was decoded.
The special atlas renders the complete base-state sequence for each non-directional signature.

## Interpretation

The five-byte selector record is now enough to recover both an actor's graphics resources and
its nearby normal animation family for most entries. All 123 four-state/two-frame shapes now
have an explicit resolution: 117 directional, 2 direction-invariant, and 4 non-directional
pose/animation families. Runtime analysis is therefore mainly needed for semantic identity,
map binding, and behavior, not to leave four-state families in an ambiguous bucket.

A broader "state is drawable by this CHR window" scan was also tested, but large CHR windows
can render many unrelated event templates. That relation is useful as a candidate graph but
is deliberately not treated as actor ownership.
