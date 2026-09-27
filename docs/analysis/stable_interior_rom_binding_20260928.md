# Stable interior sample: exact ROM binding

Updated: 2026-09-28

## Result

The existing L1 interior runtime sample is now bound to exact ROM-side map
records and independently decoded outside the emulator.

This upgrades the sample from "scene-specific VRAM pages" to a confirmed
ROM->decode->metatile->VRAM path.

Raw ROM, WRAM and VRAM payloads remain outside Git. Only selectors, pointers,
hashes, counts and validation results are recorded here.

## Runtime selector capture

The emulator was paused at the same stable interior scene/frame used by the L1
sample.

Frame: 3253

Derived WRAM selector values:

- $139C = 7: primary tileset/config ID
- $139D = 0: no secondary tileset/config
- $139E = 15: primary layout ID
- $139F = 0: no secondary layout
- $139B = 2: map variant/state byte carried by opcode 0x50
- $113C = 0: normal map mode

The surrounding $1398..$139F bytes at that frame were:

00 00 05 02 07 00 0F 00

This small runtime capture remains local; Git stores only the interpreted
values above.

## Exact ROM records

### Tileset/config ID 7

CE:2000 entry 7 -> CE:44C0

Next CE table target: CE:50B0

The selected metatile block therefore occupies the table-defined interval
starting at CE:44C0 and ending before CE:50B0.

The parallel CF:0000 table entry for ID 7 is CF:0658. Its exact semantic subrole
is still intentionally left provisional.

### Layout ID 15

CF:2000 entry 15 -> CF:2E1D

Header:

- flags = 0x80
- chunk width = 2
- chunk height = 1
- chunk count = 2
- record length = 17 bytes
- next record = CF:2E2E

Flag 0x80 means the record uses two compressed byte streams per chunk. The
decoder combines them as low/high bytes of 16-bit metatile IDs.

For this record the stream descriptors resolve to:

| cell | byte plane | selector | decoder | source |
|---:|---:|---:|---|---|
| 0 | low | 3 | 256-byte ring/back-reference | D0:2FF5 |
| 0 | high | 0 | value/run | CF:8000 |
| 1 | low | 3 | 256-byte ring/back-reference | D0:3074 |
| 1 | high | 0 | value/run | CF:8000 |

The high-byte stream is shared and decodes to the expected zero-valued high
plane for this sample.

## Standalone decoder validation

Tool:

tools/python/decode_map_layout.py

The decoder implements all four stream selectors used by the 203 catalogued
layout records:

- selector 0: value/run stream
- selector 1: binary run stream
- selector 2: flag/new-value-or-reuse stream
- selector 3: 256-byte history-ring literal/back-reference stream

A full corpus smoke test decoded all 203 layout records without exceptions.

Selector usage across those records:

- selector 0: 2880 streams
- selector 1: 171 streams
- selector 2: 25 streams
- selector 3: 2619 streams

This is a structural smoke test. The sample-specific runtime proof below is the
strong validation for selectors 0 and 3.

## $7F staging validation

Layout 15 expands to four 256-byte streams:

- cell 0 low byte
- cell 0 high byte
- cell 1 low byte
- cell 1 high byte

The corresponding $7F staging pages were captured at frame 3253.

Result:

- compared bytes: 1024
- byte differences: 0
- exact match: true

All four page SHA-256 hashes independently matched between ROM-side standalone
decode and runtime WRAM staging.

This confirms the descriptor interpretation and selector-0/selector-3 decoder
semantics for the L1 sample.

## Logical map size

Each layout cell decodes to a 16x16 metatile-ID chunk.

Layout 15 is 2x1 chunks, therefore:

- logical metatile map = 32x16
- unique metatile IDs = 46
- minimum ID = 0
- maximum ID = 193
- logical u16le grid SHA-256:
  ea4946a9cf387b87c7623d720355a22d536cd1d432e282f5ff3edbaedb30ad97

The full logical grid is reproducible with the committed tool but is not stored
here as raw map payload.

## Tileset expansion and VRAM validation

Tileset 7 expands each metatile ID into four 16-bit SNES tilemap entries.

The 32x16 metatile grid therefore becomes:

64x32 SNES tile entries

That size is exactly two 32x32 SNES screen maps placed horizontally.

Derived expanded-grid SHA-256 (u16le):

b76db2a30823307b0ba5a118cf0ab07846e0b3d23067e0685b1a5267ad557595

Screen hashes:

- left 32x32: db9716b4b489ca7f6d355d6d81b5c3eb4471d38ebdc661cac652e880be75d70c
- right 32x32: 96719b46ebeb3bc7ad16640c89f24f77659d1afa36c25083a2e6d20df207b424

Compared with the runtime L1 pages:

- VRAM 0x1000: 922/1024 words exact, 102 different
- VRAM 0x1800: 1012/1024 words exact, 12 different
- combined: 1934/2048 words exact
- total differences: 114 words

Every one of the 114 differing runtime words is exactly 0x0100.

There are zero mismatches where the runtime word is not 0x0100.

Therefore the ROM-derived static map agrees with every non-blank/non-clipped
runtime tile entry in these two pages. The remaining differences are a runtime
blank/clip operation, not a decoder or tileset mismatch.

## Correction to the earlier L1 interpretation

The earlier L1 evidence described 0x1800 as a possible secondary/simple layer.

The exact ROM binding changes that interpretation:

- 0x1000 is the left 32x32 screen of one 64x32 tilemap
- 0x1800 is the right 32x32 screen of the same tilemap

Together they are the resident 64x32 expansion of layout 15 + tileset 7, with
runtime 0x0100 blanking applied to edge/clip positions.

This is stronger than the original structural-only inference.

## Upstream map-selector bytecode

The direct writers of $139C..$139F are in the bank-C4 record interpreter.

C4:87BC dispatches one-byte opcodes through the word table at C4:87D4.

Relevant handlers:

- opcode 0x50 -> C4:8AF0
- opcode 0x51 -> C4:8B06

Opcode 0x50 consumes three argument bytes:

[50, primary_tileset_id, primary_layout_id, map_variant]

and stores them to:

- $139C
- $139E
- $139B

Opcode 0x51 consumes two argument bytes:

[51, secondary_tileset_id, secondary_layout_id]

and stores them to:

- $139D
- $139F

For the stable interior sample the exact primary command bytes are:

50 07 0F 02

That sequence occurs at three ROM addresses:

- CB:DE70
- CC:5391
- CE:0F2B

These are candidate entry-script records selecting the same interior map
configuration. Human location/entry-point names are not assigned yet.

## Reproducer

Derived binding summary:

data/maps/samples/stable_interior_rom_binding.json

Decoder:

tools/python/decode_map_layout.py

Example command shape:

python tools/python/decode_map_layout.py ROM \
  --layout-id 15 \
  --tileset-id 7 \
  --staging-json LOCAL_WRAM_CAPTURE.json \
  --vram LOCAL_MAP_CAPTURE/vram.bin \
  --output data/maps/samples/stable_interior_rom_binding.json

The runtime capture inputs are local-only.

## Remaining work

1. Identify the three 0x50 entry records by human place/entry-point context.
2. Enumerate opcode 0x50/0x51 commands through the bank-C4 script interpreter
   rather than by blind byte search.
3. Bind those commands to the 203-layout / 60-tileset catalogs.
4. Separate village/town/castle/interior/dungeon/world-map entries.
5. Decode collision, warp, event-trigger and encounter layers.
6. Determine the exact runtime rule that replaces 114 static entries with
   0x0100 in this sample.
