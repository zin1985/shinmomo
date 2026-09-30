# Static display actor/object catalog — 2026-09-30

The ROM display-selector table has now been bounded structurally to selectors 0x00..0xAA.
At selector 0xAB the byte pattern changes into a different table structure, so bytes after
0xAA must not be interpreted as five-byte display-selector records.

## Coverage

- table records: 171 including selector 0x00
- selector 0x00: reserved/empty
- nonzero selectors: 170
- directly reconstructable: 170 / 170 nonzero selectors
- unique graphics signatures among those 170: 158
- unresolved: 0

The 160 reconstructed entries include player/party-looking actors, village NPCs, animals,
monsters, large field actors, effects, and object-like graphics. Therefore this is a
**display actor/object catalog**, not a semantic character list.

## Unresolved selectors

- 0x20 and 0xA9 were recovered after decoding graphics-reader dispatch 4. Both reconstruct
  as large gray armored/warrior-like field actors.
- 0x61..0x68 were recovered by following the group-0 setup path. The setup selects graphics
  context 0, clears $1122/$1121, and skips B25E when the selector's CHR-window byte is zero.
  This means window 0 is a special full-resource path rather than an invalid B2EE index.
  Selector 0x61 reconstructs as a purple-gray mask/stone-like object; 0x62..0x68 are seven
  color variants of a small orb/sphere-like object.

## Validation basis

The static pipeline was already byte-validated against live village VRAM for Momotaro,
Ginji-family CHR, elder NPC, red-hat NPC, purple/green NPC, and blue NPC, and the static
palette resource matched the game-side runtime palette staging 32/32 colors.

The atlas extends that same ROM-only reconstruction rule to every selector that passes
the same structural checks. Runtime evidence is still required before assigning semantic
names to unknown entries.

## Outputs

- `data/npc_display/static_character_selector_catalog_20260930.csv`
- `data/npc_display/static_character_selector_catalog_summary_20260930.json`
- `graphics/static_character_reconstruction/static_character_catalog_atlas_20260930.png`
- representative thumbnails `catalog_selector_XX.png`
- generator `tools/python/build_static_character_catalog.py`

## Next static targets

1. Bind selector ids to event/map actors separately using runtime/event evidence.
2. Classify the 158 unique display signatures semantically: party/NPC/enemy/animal/effect/object.
3. Continue expanding special animation sequences beyond the normal four-state/two-frame families.
