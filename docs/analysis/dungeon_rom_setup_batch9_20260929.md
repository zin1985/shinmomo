# ROM-derived dungeon/special map batch 9 — 2026-09-29

## Result

Tileset 58 can be partially promoted under the strict ROM-only rendering policy.

All pack-0xE3..0xE8 state-0 selector prefixes use the same explicit map setup:

```text
10 1B
10 0D
11 37
```

This setup fully covers layouts 197 and 198.

Canonical output:

- `data/maps/rendered/dungeon_tileset_58/`
- `map_197.png`
- `map_198.png`

Both PNGs were independently regenerated into a temporary directory from the
same ROM/setup inputs and matched the canonical candidate files byte-for-byte
by SHA-256.

## Layouts

### Layout 197

- tileset: 58
- pack: 0xE8
- size: 2048 x 1792 pixels
- explicit graphics resources: opcode-0x10 operands 0x1B and 0x0D
- explicit palette resource: opcode-0x11 operand 0x37
- graphics coverage: complete
- palette coverage: complete

### Layout 198

- tileset: 58
- pack: 0xE3
- size: 512 x 2048 pixels
- explicit graphics resources: opcode-0x10 operands 0x1B and 0x0D
- explicit palette resource: opcode-0x11 operand 0x37
- graphics coverage: complete
- palette coverage: complete

## Why layout 196 is not promoted

Layouts used by packs 0xE4..0xE7 additionally reference tile 0x0E0.

The reference is extremely narrow:

- layout 196 uses tile 0x0E0 exactly once;
- it occurs at expanded tile coordinate (366, 116);
- tilemap entry: 0x10E0
- palette ID: 4;
- source CE metatile: tileset-58 metatile 0x8C;
- metatile 0x8C itself occurs once.

The explicit pack setup loads map CHR at VRAM byte 0x2000 and above, while tile
0x0E0 resides at byte 0x1C00 in the lower/common CHR region.

The common transition path `80:C9E7 -> 80:CBB6` was checked.  CBB6 does load
shared graphics resources before state-0 entry1, but under descriptor index 1
its opcode-0x10 operands 01/02 target VRAM 0x8800 and above; they do not establish
tile 0x0E0.

Runtime captures also show that the low VRAM region is not globally constant.
Therefore layout 196 remains fail-closed rather than borrowing or zero-filling
tile 0x0E0.

## Validation policy

Only layouts with complete explicit CHR and palette coverage are emitted.

- normal BG color index 0 is alpha-transparent;
- raw ROM/VRAM/CGRAM payloads are not committed;
- no missing CHR is guessed from visual appearance.

Layout 196 remains the only unresolved tileset-58 layout in this batch.
