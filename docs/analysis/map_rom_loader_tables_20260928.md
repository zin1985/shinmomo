# ROM-side map loader tables and upload pipeline

Updated: 2026-09-28

## Status

This analysis closes the current "resident VRAM page -> ROM-side map loader"
work unit far enough to drive deterministic extraction.

The first L1 structural sample established scene-specific resident tilemap pages
at VRAM 0x1000 and 0x1800. Static tracing now connects the map renderer to
concrete ROM-side pointer tables and a decompression/staging path.

This document records structure and addresses only. Raw ROM/map payloads are not
stored in Git.

## 1. Two different VRAM queues

### $7E:2040: VRAM relocation queue

C0:A0BA consumes 6-byte entries from $7E:2040. The producer is the
C0:D844 -> C0:C733 -> C0:C77B/C7C6 path.

C0:C7C6 stores source/destination VRAM addresses derived from map coordinates
into the queue. C0:A0F0 then reads existing VRAM through $2139/$213A, stages it
through $7E:2000, and writes it back through $2118/$2119.

Classification: this is a scroll/transition VRAM-to-VRAM relocation mechanism,
not the original ROM-side population path.

### $7E:8000: WRAM-to-VRAM upload command ring

C0:A151 starts a transfer record:
- +0: transfer/control flags from $03AA
- +2: payload byte count, filled by C0:A185
- +4: destination VMADD from $0F
- +6: payload

C0:A170 appends payload words and C0:A185 seals the record.

C0:A1B9 is the NMI consumer. It reads these records, programs VMAIN/VMADD and
either:
- performs DMA from bank $7E for larger payloads; or
- uses C0:A291 and direct $2118/$2119 writes for short payloads.

C0:F0D4 calls C0:A1B9 during NMI.

This is the important upload path for map population.

## 2. Map renderer builds $7E:8000 records

The D2xx-D6xx map routines build upload records through A151/A170/A185.

Important steps:
- C0:D447 computes a VRAM destination and starts an upload record.
- C0:D2C2/D30A/D3A6/D3EE feed expanded tile values into the queue.
- C0:D646/D659 can feed words from the current map source pointer directly.
- C0:D22D/C849 convert logical map coordinates into VRAM addresses.

This connects the generic upload ring to map-specific logic.

## 3. CE:2000 is the tileset/metatile pointer table

C0:D4EC implements:

1. id = ($139C - 1)
2. index = id * 2
3. load 16-bit pointer from CE:2000[index]

The canonical ROM contains 60 non-FFFF entries before padding.

Derived catalog:
- first target: CE:2100
- last target: CE:FB00
- 60 non-FFFF pointers

C0:CD85 combines the selected 16-bit target with bank CE into the long pointer
used as $C6..$C8.

C0:D1B2/D1E9 uses a metatile ID, multiplies it by 8 in the normal mode, then
reads four 16-bit values through [$C6],Y into the $13FD expansion buffer.

Therefore the CE targets are strongly identified as metatile/tileset definition
blocks. In the normal path one metatile expands to four 16-bit SNES tilemap
entries, i.e. 8 bytes per metatile.

The alternate $113C mode uses a different expansion width and remains a
separate format variant.

## 4. CF:0000 is a parallel 60-entry word-pointer table

C0:D457 also indexes CF:0000 with the same ($139C - 1) * 2 index.

The ROM has 60 non-FFFF entries:
- first target: CF:0100
- last target: CF:1D20

Its exact semantic label is not yet final, but its one-to-one cardinality with
CE:2000 and its use in the same map setup path make it part of the tileset/map
configuration family.

Do not label it more specifically until its consumers are fully resolved.

## 5. CF:2000 is a packed 24-bit layout-record pointer table

C0:D4F7 computes:

1. id = ($139E - 1)
2. index = id * 3
3. load an overlapping word from CF:2001[index] into Y
4. load a word from CF:2000[index] into A

The caller stores the overlapping result into three bytes, reconstructing one
packed 24-bit pointer.

The first pointer is CF:2261. Therefore the pointer table occupies exactly:

CF:2000..CF:2260 = 0x261 bytes = 609 bytes = 203 * 3

So the table has exactly 203 entries.

All 203 pointers resolve to structurally valid records in bank CF.

## 6. Layout record header is confirmed

Every one of the 203 records follows the same 5-byte header shape:

- byte 0: mode / flags
- byte 1: width
- byte 2: height
- bytes 3-4: little-endian cell count

For all 203 records:

cell_count == width * height

Mode distribution:
- 0x00: 118 records
- 0x01: 5 records
- 0x80: 80 records

Payload sizing is exact for every non-final record:
- mode 0x00: 3 bytes per cell
- mode 0x01: 3 bytes per cell
- mode 0x80: 6 bytes per cell

Thus:

record_length = 5 + width * height * payload_stride

Examples:
- layout 1: CF:2261, mode 0x01, 16x16, 256 cells, 773 bytes
- layout 6: CF:2CFA, mode 0x80, 3x3, 9 cells, 59 bytes
- layout 34: CF:302F, mode 0x80, 4x4, 16 cells, 101 bytes
- layout 45: CF:3477, mode 0x80, 7x7, 49 cells, 299 bytes

This is strong enough to enumerate the ROM layout corpus without visiting each
map in the emulator.

## 7. Layout record -> staging buffer

C0:D457 resolves the selected CF:2000 layout pointer into DP $C3..$C5.

C0:D0AE consumes the record and decodes descriptor streams. The decoded map
grid is staged in bank $7F through the $C9..$CB long pointer family.

C0:CFF4 reads the staged grid through [$C9],Y and builds metatile-ID rows at
$13BD/$13DD.

Then:
- D19E expands those IDs through the CE tileset pointer into $13FD...
- D2xx/D3xx emit $7E:8000 upload records
- A1B9 uploads them to VRAM in NMI.

## 8. Four decoder modes

The D0AE path derives a decoder selector from the top two bits of a descriptor
byte and dispatches through two 4-entry function tables at C0:D157 and C0:D173.

Confirmed decoder pairs:

| selector | initializer | next-value routine | structural behavior |
|---:|---|---|---|
| 0 | C0:C057 | C0:C0C8 | value + run-count stream |
| 1 | C0:C067 | C0:C0F2 | compact binary run stream; high bit contributes the value and low 7 bits the run length |
| 2 | C0:C02A | C0:C077 | flag-byte stream with previous-value reuse |
| 3 | C0:BCEE | C0:BD28 | bit-controlled literal/back-reference style stream with internal history buffer |

The exact compression-format names should remain provisional. The dispatch and
state-machine behavior are static facts; naming can be refined after a
standalone decoder reproduces known map grids.

## 9. End-to-end map pipeline

The strongest current model is:

CF:2000 layout-pointer table
-> CF:xxxx layout record
-> D0AE + one of four decoder modes
-> decoded/staged grid in $7F:xxxx
-> CFF4 extracts metatile IDs
-> CE:2000 tileset pointer table
-> CE:xxxx metatile definitions
-> D19E expands metatile IDs into SNES tile entries
-> D2xx/D3xx build $7E:8000 VRAM upload commands
-> A1B9 consumes commands in NMI
-> resident BG tilemap pages in VRAM

This is now a ROM-side source path, not merely a runtime VRAM observation.

## 10. Derived catalog tool

Use:

python tools/python/catalog_map_rom_tables.py <ROM> --out-dir data/maps/rom_tables

It writes metadata only:
- data/maps/rom_tables/tileset_pointer_catalog.csv
- data/maps/rom_tables/layout_record_catalog.csv
- data/maps/rom_tables/map_rom_table_summary.json

The tool does not export record payload bytes.

For the canonical ROM it reports:
- 60 CE tileset/metatile pointers
- 60 parallel CF:0000 pointers
- 203 CF:2000 layout pointers
- all 203 cell counts equal width * height
- all 202 non-final layout lengths exactly match the inferred header/stride
  schema

## 11. Remaining gaps

The ROM-side map loader goal is now substantially closed, but these items remain:

1. Bind the L1 interior sample to its exact runtime IDs:
   - $139C/$139D: tileset/config IDs
   - $139E/$139F: primary/secondary layout IDs
2. Trace where those four IDs are loaded. C0:C9BA calls bank 83/84 routines,
   and C0-CF contains no direct writers for $139C..$139F, so the producer likely
   lives in bank 83/84 scene/map setup code.
3. Implement standalone payload decoders and prove the reconstructed logical
   grid against the L1 runtime sample.
4. Identify collision, warp, event-trigger and encounter layers separately.
5. Map human place/floor names to the 203 layout records and 60 tileset/config
   records.

The next highest-leverage experiment is a small runtime capture of
$139C..$139F in the known L1 room, followed by standalone decode of that exact
CF layout record and CE tileset entry.
