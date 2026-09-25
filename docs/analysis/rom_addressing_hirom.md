# Canonical ROM addressing: FastROM HiROM

Updated: 2026-09-25

## Confirmed mapper

The canonical 2 MiB ROM has the internal header at file offset `0x00FFC0`.
The title field is `NEW MOMOTARO DENSETSU` and the map-mode byte at `0x00FFD5` is `0x31`.

`0x31` is FastROM HiROM. Therefore current analysis must not use the 2026-09-25 LoROM correction rule.

Canonical documentation uses the high HiROM mirror:

`file_offset = ((bank - 0xC0) << 16) | address` for `C0:0000..DF:FFFF` in this 2 MiB ROM.

For addresses `>= 0x8000`, the lower `80..9F` HiROM mirrors may also be executable aliases, but the `C0..` form is canonical in new documentation.

## Representative corrections

| File offset | Canonical HiROM | Valid low mirror | Superseded LoROM label |
|---|---|---|---|
| `0x039850` | `C3:9850` | `83:9850` | `87:9850` |
| `0x03F09A` | `C3:F09A` | `83:F09A` | `87:F09A` |
| `0x041A10` | `C4:1A10` | n/a for ROM at this low address | `88:9A10` |
| `0x0487A2` | `C4:87A2` | `84:87A2` | `89:87A2` |
| `0x049D4D` | `C4:9D4D` | `84:9D4D` | `89:9D4D` |
| `0x049E10` | `C4:9E10` | `84:9E10` | `C9:9E10` |
| `0x070000` | `C7:0000` | `47:0000` | n/a |

## Direct machine-code validation

The source-family resolver at file `0x049D4D` executes a long indexed load from literal address `$C7:0000,X`.
That literal points exactly at file `0x070000` under HiROM and directly validates the mapping against running code structure.

Historical documents are evidence records and are not mass-rewritten. Any document explicitly based on the LoROM correction table is superseded for CPU-address labels; its file offsets and byte evidence remain reusable.
