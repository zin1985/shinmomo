# Graphics reader dispatch 4 — 2026-09-30

## Scope

Selectors 0x20 and 0xA9 use context-5 CHR resource 0x25. Its graphics descriptor is:

- descriptor C3:0798
- raw: 00 00 80 04 DF C8 D9 25
- output size: 0x0480 bytes
- source: D9:C8DF
- reader kind: 5
- reader dispatch index: 4

## Engine behavior

The reader jump table at 80:B910 routes dispatch index 4 to 80:B92C.

80:B92C checks the per-output-byte counter $1124:

- if bit 4 is clear, read the next byte through the normal 80:BD28 source reader
- if bit 4 is set but bit 0 is clear, read the next byte normally
- if bit 4 and bit 0 are both set, return 0x00 without advancing the source reader

Equivalent reconstruction rule:

```
for output_index in range(output_size):
    if (output_index & 0x10) and (output_index & 0x01):
        output_byte = 0
    else:
        output_byte = next(normal_BD28_stream)
```

Therefore dispatch 4 is not a separate compression codec. It is the normal dispatch-0
BD28/LZSS byte stream plus deterministic zero insertion.

Within each 32-byte 4bpp tile-sized block, the zeroed positions are odd bytes in the second
16-byte half. This is consistent with leaving one subset of SNES bitplanes empty.

## Result

After adding dispatch 4 to the common graphics decoder:

- selector 0x20 reconstructs successfully
- selector 0xA9 reconstructs successfully
- both render as coherent large gray armored/warrior-like field actors
- static selector coverage rises from 160 to 162 selectors
- unique reconstructed graphics signatures rise from 148 to 150
- unresolved selectors are reduced to 0x61..0x68 only

The dispatch-4 branch was added to
`tools/python/render_normal_map_family_from_setup.py`, so the behavior is available to
other graphics reconstruction tools that reuse the common decoder.
