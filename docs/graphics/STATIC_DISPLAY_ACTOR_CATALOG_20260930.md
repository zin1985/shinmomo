# Static display actor/object catalog — 2026-09-30

The ROM display-selector table has now been bounded structurally to selectors 0x00..0xAA.
At selector 0xAB the byte pattern changes into a different table structure, so bytes after
0xAA must not be interpreted as five-byte display-selector records.

## Coverage

- table records: 171 including selector 0x00
- selector 0x00: reserved/empty
- nonzero selectors: 170
- directly reconstructable with the proven context-5 pipeline: 162
- unique graphics signatures among those 162: 150
- unresolved: 8

The 160 reconstructed entries include player/party-looking actors, village NPCs, animals,
monsters, large field actors, effects, and object-like graphics. Therefore this is a
**display actor/object catalog**, not a semantic character list.

## Unresolved selectors

- 0x20 and 0xA9 were recovered after decoding graphics-reader dispatch 4. Both reconstruct
  as large gray armored/warrior-like field actors.
- 0x61..0x68 remain unresolved. They are group 0 with CHR-window selector 0; B25E therefore
  resolves the window through transient low-WRAM $01FE/$01FF rather than a ROM B2EE table.
  Treat them as a separate runtime-window display/resource subtype until their caller path
  and scratch-window initialization are understood.

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

1. Trace the special low-WRAM window/resource path used by 0x61..0x68.
2. Continue expanding selector animation families while preserving duplicate selectors as aliases.
3. Bind selector ids to event/map actors separately using runtime/event evidence.
