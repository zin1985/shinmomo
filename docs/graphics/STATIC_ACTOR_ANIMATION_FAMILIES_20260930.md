# Static actor animation family catalog — 2026-09-30

The ROM-only display-selector reconstruction has now been extended from one representative
frame per selector to animation-family extraction.

## Coverage

Among the 150 unique reconstructable graphics signatures:

- 123 have a nearby contiguous four-state / two-frame family.
- 105 of those are in sprite groups 2 or 3, where runtime village/player tracing has
  directly confirmed the state order as right, down, left, up.
- 18 are in groups 4, 5, or 7. Their four-state / two-frame structure is static fact,
  but the semantic direction order remains unverified.
- 17 signatures have a fixed one-frame base state.
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

For groups 4, 5, and 7 the catalog records neutral slot0..slot3 ordering until runtime or
control-flow evidence proves the same direction mapping.

## Non-directional actors

The remaining 27 unique signatures are intentionally kept separate:

- 17 fixed-base actors/objects
- 10 special-sequence actors/objects

The special atlas preserves the base-state frame sequence in order, including repeated
frames. It includes effect-like objects, large actors, and special event animations, so
semantic character names should not be inferred from the graphics alone.

## Outputs

- `data/npc_display/static_actor_animation_family_catalog_20260930.csv`
- `data/npc_display/static_actor_animation_family_summary_20260930.json`
- `graphics/static_character_reconstruction/static_directional_animation_atlas_20260930.png`
- `graphics/static_character_reconstruction/static_special_animation_atlas_20260930.png`
- `tools/python/build_static_actor_animation_catalog.py`

The directional atlas renders all eight frames for each detected four-state/two-frame family. Selectors 0x20 and 0xA9 are now included after graphics-reader dispatch 4 was decoded.
The special atlas renders the complete base-state sequence for each non-directional signature.

## Interpretation

The five-byte selector record is now enough to recover both an actor's graphics resources and
its nearby normal animation family for most entries. Runtime analysis is no longer required
to obtain the pixels or animation frame sequence for these 121 families; runtime is mainly
needed for semantic identity, map binding, and direction-order confirmation outside groups 2/3.

A broader "state is drawable by this CHR window" scan was also tested, but large CHR windows
can render many unrelated event templates. That relation is useful as a candidate graph but
is deliberately not treated as actor ownership.
