# Static display actor/object catalog — 2026-09-30

The ROM display-selector table has now been bounded structurally to selectors 0x00..0xAA.
At selector 0xAB the byte pattern changes into a different table structure, so bytes after
0xAA must not be interpreted as five-byte display-selector records.

## Coverage

- table records: 171 including selector 0x00
- selector 0x00: reserved/empty
- nonzero selectors: 170
- directly reconstructable with the proven context-5 pipeline: 160
- unique graphics signatures among those 160: 148
- unresolved: 10

The 160 reconstructed entries include player/party-looking actors, village NPCs, animals,
monsters, large field actors, effects, and object-like graphics. Therefore this is a
**display actor/object catalog**, not a semantic character list.

## Unresolved selectors

- 0x20 and 0xA9 share CHR resource 0x25, whose graphics reader uses dispatch 4.
  The current decoder intentionally does not implement that reader yet.
- 0x61..0x68 do not resolve through the same B2EE CHR-window indexing used by the proven
  actor families. Treat them as a separate display/resource subtype until their caller
  path is understood.

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

1. Decode graphics reader dispatch 4 to recover selectors 0x20 and 0xA9.
2. Trace the special window/resource path used by 0x61..0x68.
3. Expand each selector from the representative first frame into complete animation-state
   families, while preserving duplicate selectors as aliases rather than duplicate art.
4. Bind selector ids to event/map actors separately using runtime/event evidence.
