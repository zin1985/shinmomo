# Group-0 selector special path — 2026-09-30

## Result

Selectors 0x61..0x68 are now statically reconstructable. They are not broken B2EE records.
They intentionally use a different object/resource initialization path.

## Selector records

All eight records use sprite group 0 and CHR-window byte 0.

- 0x61: CHR resource 27, base state 58, palette resource 26
- 0x62..0x68: CHR resource 28, base states 59..65 in selector-specific order, palette resource 27

## Context switch

The object/resource setup routine around physical ROM 0x1AE70 sets graphics context 5,
then tests the low nibble of the object's sprite group.

For group 0 or 1 it clears $035F, selecting **graphics context 0**.

Therefore these selectors must not use the context-5 actor resource table.

Context-0 resources:

- resource 27: descriptor C3:0260, source D8:2B3E, decoded size 0x0680 = 52 tiles, dispatch 4
- resource 28: descriptor C3:0268, source D8:2E07, decoded size 0x0100 = 8 tiles, dispatch 0

## Window byte 0

Another object setup path around physical ROM 0x1B42D explicitly:

1. clears $1122
2. clears $1121
3. reads the selector's CHR-window byte
4. calls 80:B25E only if that byte is nonzero

Thus CHR-window byte 0 means **skip B25E and use the full decoded resource from source tile 0**.
It is not a 1-based B2EE index and does not mean "read entry -1".

This resolves the apparent low-WRAM $01FE/$01FF anomaly from naively applying B25E to zero.

## B893 packing correction

The static OBJ packer was generalized beyond one 32-tile block.

For decoded tile index j:

```
block  = (j // 32) * 32
within = j % 32
local_obj_tile = block + (within // 2) + (16 if within is odd else 0)
```

So each 32-tile source block maps as:

```
0,16,1,17,...,15,31
32,48,33,49,...,47,63
...
```

This matters for context-0 resource 27 because its 52 decoded tiles span more than one block.

## Reconstructed outputs

- selector 0x61: purple-gray mask/stone-like 16x16 object
- selectors 0x62..0x68: seven color variants of a small orb/sphere-like object

All 170 nonzero display selectors in the 0x00..0xAA table are now statically reconstructable.
The resulting catalog contains 158 unique graphics signatures.
