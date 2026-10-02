# Static actor selector visual expansion (2026-10-02)

## Scope

This pass expands visual-form coverage for the selector set that is actually referenced by the 817 static opcode-0x59 actor rows.

The existing selector visual-form table covered 41 of 68 actor-used selectors. The remaining 27 selectors were reviewed directly from the ROM-reconstructed static selector atlas and added conservatively as visual form only.

Visual form is not a gameplay-role assertion. In particular, `monster_like` does not prove enemy allegiance and `object_like` does not prove service/event semantics.

## Coverage

- static opcode-0x59 actor rows: 817
- unique selectors used by those rows: 68
- visual-form selectors before this pass: 41 / 68
- selectors added in this pass: 27
- visual-form selectors after this pass: 68 / 68
- viewer semantic/appearance overrides after regeneration: 817 / 817

## Newly classified selectors

`0x02 0x04 0x05 0x06 0x07 0x08 0x09 0x0A 0x0B 0x0D 0x12 0x13 0x14 0x32 0x45 0x46 0x48 0x51 0x52 0x55 0x6A 0x6C 0x6D 0x71 0x77 0x7C 0xA4`

The classifications remain intentionally broad: humanoid-like, animal-like, monster-like, small-creature-like, and object-like. Ambiguous silhouettes use medium confidence rather than a specific character or object identity.

## Regenerated outputs

- `data/npc_display/static_map_bound_selector_visual_form_20260930.csv`
- `data/npc_display/static_actor_sprite_semantics_20260930.csv`
- `viewer/data/actor_semantics.json`

Current generated role counts are:

- villager / high: 10
- talking_npc / strong_candidate: 1
- animal / high: 49
- effect / candidate: 10
- unknown: 747

The rise in `effect` candidates comes from additional object-like selectors and remains a candidate-level semantic only.

## Next sprite frontier

1. Classify selector graphics that are reconstructable but not currently used by the static opcode-0x59 actor corpus.
2. Separate true character sprites from props, effects, and special pose sequences.
3. Inventory field/background/mapchip graphics independently from actor sprites so background tiles are not mixed into character semantics.
4. Join object-like selector families to controller/event evidence before assigning game-facing names.
