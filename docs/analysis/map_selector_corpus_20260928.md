# Map-selector corpus expansion

Updated: 2026-09-28

## Purpose

This pass generalizes the previously confirmed 65-command primary map-selector
family without falling back to blind whole-ROM byte search.

The result is a reproducible, structurally bounded candidate corpus. It also
repairs the rolling checkpoint's missing
`data/maps/selectors/primary_map_selector_summary.json` artifact.

Raw ROM bytes are not emitted.

## 1. Script-pack record corpus

The CA:C000 master table points to real packs 0x14..0xF9.

The pack header has the verified form:

```
[record_start16 x N] 00 00 00 <pack_id>
```

The first record pointer itself determines N:

```
N = (first_record_file_offset - pack_start - 4) / 2
```

Four packs cross a bank boundary:

- 0x15
- 0x48
- 0x9E
- 0xF2

Their record pointers remain 16-bit. When the pointer word decreases, the
implied bank advances by one. Applying that rule makes all four packs parse
cleanly, including their trailer and monotonic file offsets.

All **230** real packs now parse with zero failures.

Before adding the four bank-wrap packs, the same-bank subset produced 4,093
pointer-bounded records. One entry is independently recognizable as a large
pointer/table blob rather than a VM record:

- pack 0x14 record 0, CA:CBF6..CA:D086

Excluding that blob gave the earlier 4,092-record corpus.

The four bank-wrap packs add:

- pack 0x15: 197 records
- pack 0x48: 13 records
- pack 0x9E: 13 records
- pack 0xF2: 9 records

The complete corpus is therefore:

**4,324 bounded VM records**

## 2. Record entry/substream header

A major record class begins with:

```
[entry_id:1][substream_ptr16:2] ... 00
```

All pointers must:

- resolve inside the same bounded record;
- begin at or after the header terminator;
- be strictly increasing.

Across the full 4,324-record corpus:

- records satisfying this grammar: **3,832**
- valid substream entries: **8,039**
- structurally different records: 492

The stable-interior examples are reproduced exactly.

### Pack 0x2E record 0

Record: CB:DE63..CB:DE82

```
01 6A DE
02 7C DE
00
```

So entry 1 starts at CB:DE6A and entry 2 at CB:DE7C.
The confirmed primary selector at CB:DE70 lies inside entry 1.

### Pack 0x69 record 0

Record: CC:5382..CC:53A8

```
01 89 53
02 9D 53
00
```

The selector at CC:5391 lies inside entry 1.

### Pack 0xF7 record 17

Record: CE:0F18..CE:0F47

The header exposes multiple substreams; the selector at CE:0F2B is again
inside a pointer-bounded substream rather than header data.

## 3. Primary normal-map-shaped opcode 0x50

Normal C4 handler:

- opcode 0x50 -> C4:8AF0
- format:
  `[50, primary_tileset_id, primary_layout_id, map_variant]`
- stores to:
  - $139C
  - $139E
  - $139B

Candidate acceptance requires all of:

1. command lies inside a valid record substream;
2. primary tileset ID is 1..60, matching CE:2000 cardinality;
3. primary layout ID is 1..203, matching CF:2000 cardinality;
4. map variant is 1..3.

The variant range is not heuristic. C0:C6FD decrements the incoming value and
uses it as a 1-based table index; the adjacent wrappers feed values 1, 2 and 3.

Three superficially plausible variant-0 byte sequences are therefore rejected:

- CB:978F: 50 02 0B 00
- CC:06EF: 50 02 52 00
- CC:B1A2: 50 30 1F 00

## 4. Primary candidate result

The full-corpus structural parser emits:

- **263** primary normal-map-shaped rows
- **152** unique (tileset, layout, variant) configurations
- **56 / 60** tileset IDs represented
- **149 / 203** layout IDs represented
- **209** pack families containing at least one candidate

Variant distribution:

- variant 1: 51
- variant 2: 212
- variant 3: 0

The bank-wrap packs add only two primary rows:

- F48 r0, CC:0020 -> tileset 33 / layout 146 / variant 1
- F9E r0, CC:FFE8 -> tileset 24 / layout 125 / variant 2

Both remain mode-gate unresolved, so the confirmed-normal count is unchanged.

Initial evidence classes from record/setup structure were:

- **65** setup-signature confirmed rows
- **196** additional structural candidates

A follow-up special-dispatch parse test now promotes more rows; see section 6.

The 65 setup-signature rows are exactly the previously documented family whose
immediate prefix is:

```
10 0A 10 0B 11 09 50
```

Thus the new catalog preserves the parallel result and expands around it
without silently promoting the additional 196 rows.

The stable interior is reproduced at exactly the three already proven
addresses:

- CB:DE70
- CC:5391
- CE:0F2B

## 5. Secondary opcode 0x51

Normal C4 handler:

- opcode 0x51 -> C4:8B06
- format:
  `[51, secondary_tileset_id, secondary_layout_id]`
- stores to:
  - $139D
  - $139F

Among the 263 primary candidates, **105** are followed immediately by a 0x51
whose two IDs are both valid table indices.

All 105 pass the table-range check and still cover 51 distinct
primary+secondary configuration tuples.

After the special-dispatch disambiguation in section 6:

- **53** are `confirmed_normal_immediate_secondary_pair` because their parent
  0x50 is confirmed normal and the 0x50 handler does not change $1398;
- **52** remain `strong_immediate_secondary_pair_mode_gate_unresolved`.

A broader scan finds **79** additional range-plausible standalone 0x51 rows.
They remain:

`mode_ambiguous_secondary_shape`

because many contexts are compatible with the alternate bank82 special
dispatcher.

## 6. Normal-versus-special dispatch caveat

C4:87A2 does not give opcode >= 0x50 one universal meaning.

If:

```
$1398 == 0
```

the opcode uses the normal C4 dispatch table and 0x50/0x51 are the map-selector
handlers above.

If:

```
$1398 != 0
```

opcode >= 0x50 is routed to the separate $82:8000 dispatcher, where 0x50..0x92
have different meanings.

The bank82-special 0x50 handler is also now length-bounded. It calls
C4:9BC5, which loads A=2 and jumps through C4:8410, so special opcode 0x50
advances the script pointer by exactly **2 bytes**.

Therefore a normal-map-shaped sequence:

`50 <tileset> <layout> <variant>`

would be parsed in special mode as:

`50 <special-operand>` followed by `<layout>` as the next opcode.

That next opcode is statically impossible in two cases:

- layout > 0x92: outside the proven bank82 special opcode table;
- layout < 0x50 but its C4 dispatch entry is the C4:8963 BRK guard
  (00/05/0C/0D/0E/0F class).

Across the 263 primary rows:

- **60** have layout > 0x92;
- **10** map to the low-opcode BRK guard;
- total special-interpretation-impossible rows: **70**.

Nine of those 70 overlap the 65 setup-signature rows. The union is therefore:

**126 confirmed normal map selectors**

leaving **137 mode-gate-unresolved primary candidates**.

This promotion does not depend on guessing the meaning of $1398; it follows
from the incompatible instruction boundaries of the two dispatch modes.

The mode state is itself now bounded:

- $1398 is copied from $1399 by C0:CA04..CA07;
- direct $1399 writers observed in the ROM use states 0, 1, 2, 3, 5 and 6
  (plus initialization behavior);
- stable interior runtime has $1398 = 0.

Resolving this mode gate is the next parser-strengthening step.

## 7. Reproducible outputs

Tool:

`tools/python/catalog_map_selectors.py`

Derived outputs:

- `data/maps/selectors/primary_map_selector_catalog.csv`
- `data/maps/selectors/secondary_map_selector_candidates.csv`
- `data/maps/selectors/primary_map_selector_summary.json`

The primary catalog already joins each candidate to:

- exact CE tileset pointer;
- exact CF layout pointer;
- layout flags;
- chunk width/height;
- logical metatile dimensions;
- optional immediate secondary pointers.

## 8. Current interpretation

The 263-row full-pack family is highly coherent and spans most of the known map
table space, so it is a strong candidate for the broad map-configuration
corpus.

Confidence is now tiered as follows:

- **126 primary rows**: confirmed normal map selectors, by setup signature,
  special-parse impossibility, or both;
- **137 primary rows**: strong structural candidates with mode gate unresolved;
- **53 immediate secondary rows**: confirmed normal secondary pairs;
- **52 immediate secondary rows**: strong pairs with mode gate unresolved;
- **79 standalone 0x51 shapes**: mode-ambiguous until $1398 state/reachability
  is attached.

## 9. Next work

1. Trace $1399 writers and the $1399 -> $1398 state transition to associate
   the remaining 137 pack/substream candidates with normal or special VM mode.
2. Extend special-mode instruction-boundary rejection beyond the immediate
   post-0x50 opcode where safe, to promote more of the 137 without runtime
   guessing.
3. Resolve the 52 unresolved immediate secondary pairs and 79 standalone 0x51
   shapes.
4. Cross-link pack/record/substream locations with dialogue/event/location
   evidence to assign human place/floor labels.
5. Add collision, warp, trigger and encounter layers after selector coverage
   stabilizes.
