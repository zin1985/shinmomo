# Cross-track architecture map

Updated: 2026-09-25

This document reconciles historical analysis with the current rolling work. It is a routing map for future analysis, not a claim that every historical hypothesis is confirmed.

## 1. Addressing baseline

The canonical ROM is 2 MiB LoROM.

Important corrected mappings:

| File PC | CPU | Meaning |
|---|---|---|
| `0x039850` | `87:9850` | 398xx VM macro area |
| `0x03F09A` | `87:F09A` | high-op/blob target area |
| `0x041A10` | `88:9A10` | 8-byte selector/condition table |
| `0x0487A2` | `89:87A2` | normal script VM entry |
| `0x0487BD` | `89:87BD` | opcode → handler lookup |
| `0x0487CF` | `89:87CF` | indirect handler jump |
| `0x0487D4` | `89:87D4` | VM dispatch table |

Historical documents using older flat-bank labels must be translated through the LoROM correction table before reuse.

## 2. ROM/data layer

### Fixed gameplay tables

- `0x442BF`: item table, 11-byte fixed records, high confidence.
- `0x449D0`: equipment table, 16-byte fixed records, high confidence.
- `0x41A10 = 88:9A10`: 8-byte condition/selector records.
- `0x30000` range: event/UI script resources and descriptors.
- `0x398xx`: normal VM bytecode organized in visually regular macro rows, not a separate fixed-record CPU reader.

### 41A10 selector table

Historical reconstruction:

`[key][c1][c2][c3][c4][c5][target_lo][target_hi]`

Target is interpreted as `0x30000 + target16` for known records.

Known target examples include scripts around `0x31DDF` and `0x320A4`.

Important distinction:

- **selector-table matcher** that scans `0x41A10`: still unresolved.
- **target script VM reader**: already identified at `89:87A2/87BD/87CF/87D4`.

Do not call both of these “the 41A10 reader”.

### 0x30048 descriptor bridge

`0x30048` begins a historical 8-byte descriptor bundle. On the canonical ROM, record index 17 begins at `0x300D0`:

`00 28 00 05 9A 88 D7 32`

Bytes +3..+5 are `05 9A 88`, i.e. `88:9A05`, 11 bytes before the `88:9A10` table.

This confirms the historical pointer occurrence on the canonical ROM. Whether +3..+5 is a universal pointer field for every descriptor remains unconfirmed.

## 3. Script / VM layer

### Normal event/UI VM

Historical reader-hunt work already identified the normal VM core:

```
script pointer $98/$99/$9A
  ↓
89:87A2 VM entry
  ↓
89:87BD opcode lookup
  ↓
89:87CF indirect jump
  ↓
89:87D4 handler table
```

Therefore 398xx rows should be decoded through the normal VM unless a specific high-op handler proves otherwise.

The later 398xx reparse found a useful macro-row view:

- slot0: predicate-like instruction, often `38/37 05 01`
- slot1: selector/value instruction
- slot2: threshold/value instruction
- slot3: high-op pair such as `9A F0`, `DB F0`, `C6 F0`

The remaining question is the semantics of the high-op family, not the existence of a generic 9-byte-row reader.

### UI field extractor

Opcode `0x4F` → `89:9A44`.

Known selector sources:

- selector 1/2 use `$1923`: current item/equipment-like record ID.
- selector 3 uses `$193B`: current actor/entity-like ID.
- field extraction uses schemas such as `C4:06BE`, `C4:0000`, `C4:7BF9`.
- results are staged through `$1FC8/$1FC9` and the bank89 display/operand stack.

This links the script VM directly to item/equipment and character metadata.

## 4. Condition / logical actor layer

### Generic condition evaluator

`85:86AC` is a condition dispatcher.

Condition `0x3A` resolves to a handler that tests:

`$180A[entity-1] & 0x80`

Carry is set when the bit is clear.

### Candidate feeder

`C4:C8AA` scans candidates `0x10..0x13`:

```
$195E processed-bit mask
  ↓
$1923/$1924 candidate pair
  ↓
$80:DA57 relation/entity resolver
  ↓
$192A resolved entity
  ↓
condition 0x3A / $180A bit7
  ↓
$1958 next candidate entity
```

The candidate can then enter the logical actor/object list.

### Logical actor list

`$1569[0..9]`: logical object/entity IDs.

Known coordinate/cache fields from historical C1 analysis include:

- `$1573,X`: logical map X
- `$157D,X`: logical map Y/depth
- `$15DF,X`: render-cache X
- `$15E9,X`: render-cache Y/depth
- `$1591,X`: main visible-object external handle for the C1 logical-actor path

### 81:8D87 count aggregator

This routine is already highly characterized:

- `$09`: available normal actor count
- `$0A`: normal actor count
- `$0C`: total logical object count
- `$0D`: special object count

It scans `$1569[0..9]` and uses condition semantics related to `$180A bit7`.

## 5. Shared controller/work SoA layer

`$0619..$0A18` is a 64-slot × 16-column SoA work region.

Important correction: this is a handler-dependent overlay pool, not a fixed semantic C struct.

Bank89 overlay evidence:

- `$0859/$0899/$08D9`: 24-bit object-script pointer
- `$07D9/$0819`: movement work pair
- `$0919/$0959`: position-like pair
- `$0799 bit7`: transient object-script state latch

Historical bank87 evidence shows the same columns can instead participate in pointer/state/position-like overlays.

Some historical AF33 callers store the returned visible-object external handle into `$0619,X`. This proves that at least some controller/work slots reference a separate visible object.

## 6. Visible-object / active-list layer

The visible-object allocator/list is separately characterized.

### Allocation

`C0/80:AF33`

- sorted allocation by `$0AA3`
- active count checked against `0x40`, so at most 64 real visible objects
- initializes visible-object animation/render work

### External versus physical handle

The active list has sentinel nodes 0 and 1.

`C0:AFEC` converts the external handle to the physical linked-list node:

`physical_slot = external_handle + 2`

Thus the useful numbering model is:

- external handle: 0..63
- physical active-list node: 2..65
- sentinels: 0 and 1

This is why historical OAM fields sometimes appear with base addresses shifted by two bytes depending on whether code is indexed by external or physical handle.

### Active linked list

- `$0A1F[physical]`: previous
- `$0A61[physical]`: next
- `$0AA3[physical]`: sort / depth / priority key
- `$0AE5`: active visible-object count

`C0:AFEC` reorders objects. A key caller `C1:90ED` derives a sort key from relative Y/depth.

## 7. OAM/render layer

```
$0A61 active chain
  ↓
C0:B03D chain walk
  ↓
C0:B100 object → sprite pieces
  ↓
$0EE9 OAM mirror
  ↓
C0:B0C7 DMA
```

Known render fields include:

- `$0B27`: sprite group/attributes; bit6 is draw-skip in the known builder path
- `$0AE5,X`: 1-based animation frame/pattern in the physical-slot view
- `$0BA5/$0BE5`: X coordinate pair
- `$0C65/$0CA5`: Y coordinate pair
- `$0CE5`: vertical anchor/pivot
- `$0A1C`: remaining sprite-piece/OAM budget, initialized to 0x80
- `$0EE9..`: OAM mirror

## 8. Dialogue/text layer

Dialogue source reading is a separate pipeline from the 41A10 selector-table matcher.

Historical static analysis identifies:

- `C9:9E57`: source byte reader
- `$B1/$B2/$B3`: 24-bit source pointer
- `C9:9E10`: main source/control dispatcher
- `C9:9F34`: `0x02 xx` dictionary token handler
- `$12AA`: source mode
- `$12A9`: table ID
- `$12B2/$12B3`: display token/glyph work
- `$1274` plus `$1275/$1277/$1279`: nested source context stack

Do not block dialogue extraction on discovering the 41A10 selector matcher; these are different reader layers.

## 9. Cross-track bridges to exploit

### Script → metadata

`opcode 4F → selector → item/equipment/actor schema → staging`

Useful for Item/Equipment, Script VM, UI, and Dialogue/UI labels.

### Script/condition → logical actors

`C4 candidate feeder → relation resolver → condition 0x3A → $1958 → $1569`

Useful for Condition Dispatch, 81:8D87, event NPC logic, and Goal13.

### Logical actor → visible object

C1 logical actor allocates a visible object through `AF33` and stores its external handle, then updates/reorders it through the visible-object layer.

### Controller work → visible object

Some effect/controller families store an `AF33` returned external handle in a `$0619,X` overlay field.

This is a concrete bridge but is handler-specific, not a global identity between the two pools.

### Visible object → OAM

The active list and B100 path are already strongly established.

## 10. Highest-value remaining gaps

1. Find the **41A10 selector-table matcher**, distinct from the already-known target VM reader. Follow the `0x30048` descriptor/resource path and the `88:9A05` descriptor occurrence rather than rescanning the VM.
2. Decode the **high-op VM family** used by 398xx slot3 pairs such as `9A F0 / DB F0 / C6 F0`.
3. Runtime-map a controller/work slot holding an AF33 external handle to physical active-list node `handle+2`, closing the controller → visible-object bridge.
4. Integrate the already-known dialogue source reader into the bulk extraction pipeline.
5. Continue weapon-special selector/commit semantics.

## 11. Confidence rules

- “confirmed”: direct code/data path is known and not contradicted by later evidence.
- “strong”: multiple independent static/runtime facts align, but one bridge or label remains.
- “historical hypothesis”: useful search lead only; do not copy it into a current confirmed field without revalidation.
