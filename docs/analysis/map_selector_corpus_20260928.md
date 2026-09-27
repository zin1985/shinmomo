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

For same-bank packs, the pack header has the verified form:

```
[record_start16 x N] 00 00 00 <pack_id>
```

The first record pointer itself determines N:

```
N = (first_record_file_offset - pack_start - 4) / 2
```

Four packs cross a bank boundary and are intentionally excluded from this
same-bank parser:

- 0x15
- 0x48
- 0x9E
- 0xF2

The remaining 226 packs produce 4,093 pointer-bounded records. One entry is
independently recognizable as a large pointer/table blob rather than a VM
record:

- pack 0x14 record 0, CA:CBF6..CA:D086

Excluding that blob reproduces the parallel-analysis total exactly:

**4,092 bounded VM records**

This resolves the previous one-record discrepancy without changing the
parallel result.

## 2. Record entry/substream header

A major record class begins with:

```
[entry_id:1][substream_ptr16:2] ... 00
```

All pointers must:

- resolve inside the same bounded record;
- begin at or after the header terminator;
- be strictly increasing.

Across the 4,092-record corpus:

- records satisfying this grammar: **3,730**
- valid substream entries: **7,774**
- structurally different records: 362

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

The structural parser emits:

- **261** primary normal-map-shaped rows
- **152** unique (tileset, layout, variant) configurations
- **56 / 60** tileset IDs represented
- **149 / 203** layout IDs represented
- **207** pack families containing at least one candidate

Variant distribution:

- variant 1: 50
- variant 2: 211
- variant 3: 0

Evidence classes:

- **65** `confirmed_setup_signature`
- **196** `strong_structural_candidate_mode_gate_unresolved`

The 65 confirmed rows are exactly the previously documented family whose
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

Among the 261 primary candidates, **103** are followed immediately by a 0x51
whose two IDs are both valid table indices.

All 103 pass the table-range check.

These rows are classified:

`strong_immediate_secondary_pair`

They cover 51 distinct primary+secondary configuration tuples.

A broader scan finds 77 additional range-plausible standalone 0x51 rows. They
are deliberately left as:

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

Therefore the additional 196 primary rows are not yet promoted to unconditional
runtime map semantics solely from byte shape.

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

The 261-row family is highly coherent and spans most of the known map table
space, so it is a strong candidate for the broad map-configuration corpus.

However, confidence is intentionally tiered:

- 65 rows: confirmed normal map-selector setup family;
- 103 immediate 0x50+0x51 pairings: strong paired structure;
- remaining primary rows: strong structural candidates;
- standalone 0x51 shapes: mode-ambiguous until $1398 state/reachability is
  attached.

## 9. Next work

1. Trace $1399 writers and the $1399 -> $1398 state transition to associate
   pack/substream execution with normal or special VM mode.
2. Promote additional 0x50 rows only when normal-mode evidence is attached.
3. Resolve the 77 standalone 0x51 shapes.
4. Cross-link pack/record/substream locations with dialogue/event/location
   evidence to assign human place/floor labels.
5. Add collision, warp, trigger and encounter layers after selector coverage
   stabilizes.
