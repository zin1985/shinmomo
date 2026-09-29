# ROM-derived dungeon/special map batch 7 — 2026-09-29

## Result

This batch closes tileset 5 and tileset 32 under the same strict ROM-only
rendering policy used by earlier dungeon batches.

No runtime VRAM/CGRAM payload is committed.  Every promoted image is reconstructed
from ROM CF layout data, CE metatile definitions, normal-VM graphics setup
(opcode 0x10 and, where applicable, opcode 0x33), and opcode-0x11 palette data.

## Tileset 5

Tileset 5 has two explicit setup forms and is kept as two canonical output groups
rather than borrowing graphics from one occurrence to another.

### Graphics setup 08 only

Selector prefixes prove:

```text
10 08
11 08
50 05 <layout> 02
```

Strict coverage passes for layouts:

- 20
- 32
- 41

Canonical directory:

- `data/maps/rendered/dungeon_tileset_05_g08/`

### Graphics setup 08 + 09

Other selector prefixes explicitly prove:

```text
10 08
10 09
11 08
50 05 <layout> 02
```

Strict coverage passes for layouts:

- 42
- 43
- 77
- 83
- 87

Canonical directory:

- `data/maps/rendered/dungeon_tileset_05_g08_g09/`

Opcode-0x10 operand 09 uses the runtime-validated dispatch-0 graphics reader.

## Tileset 32

Layout 144 is referenced by packs 0xBA, 0xBB and 0xBC.

Pack 0xBC contains the explicit complete setup:

```text
10 10
33 00 20 12
11 1F
50 20 90 01
```

The opcode-0x33 operation places graphics descriptor 0x12 at VRAM word 0x2000.
Together with opcode-0x10 operand 0x10 this covers every tile used by layout 144.
The same layout previously failed closed when only the immediate opcode-0x10
resource was modeled.

Canonical directory:

- `data/maps/rendered/dungeon_tileset_32/`

This promotion is grounded specifically in the explicit pack-0xBC setup.  The
other packs using the same layout may rely on inherited graphics state and are
not used as the setup proof.

## Validation policy

For every committed map:

1. all referenced 4bpp tiles are fully contained in ROM-selected graphics
   resources;
2. every non-transparent palette index is inside the selected opcode-0x11
   resource;
3. normal BG color index 0 is emitted as alpha transparency;
4. the renderer fails closed instead of borrowing unproven CHR or palette state.

All nine promoted PNGs form coherent map structures under visual inspection.

## Remaining normal-map blockers

### Tileset 42

Pack 0x9D explicitly loads:

```text
10 13
10 14
50 2A A3 01
```

but does not load an opcode-0x11 palette in the proven selector prefix.
Its palette is inherited from an earlier state.  It remains unresolved until
the incoming transition establishes that palette provenance.

### Tileset 58

Packs 0xE3..0xE8 consistently load:

```text
10 1B
10 0D
11 37
```

but the layouts additionally reference tile 0x0E0, which lies in the common
low VRAM CHR region below byte 0x2000.  Existing runtime captures show that this
low region is not globally constant, so tile 0x0E0 is not guessed or silently
borrowed.

### Mode-0x01 families

Tilesets 2 and 3 use mode-0x01 layouts and belong to the separate Mode-7/world
rendering path, not the normal 4bpp dungeon renderer.
