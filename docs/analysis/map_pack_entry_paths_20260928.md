# Map pack entry paths — 2026-09-28

Canonical ROM was revalidated before deriving this result.

This pass separates two pack-local startup mechanisms that had previously been
mixed together:

1. the CA:C2F4 entry-0x79 seed index;
2. the state-0 record search for entry 0x01, which contains the map-selector
   record-0 family.

## 1. State 0 explicitly starts current-pack entry 0x01

The already-confirmed state-0 mode routine is 81:964E.

Inside that routine:

```
81:96CE  LDA $0305
81:96D1  JSL $84:8508
...
81:96DC  JSR $98D1
```

Helper 81:98D1 contains:

```
81:98DC  LDA $0305
81:98DF  JSL $84:8508
81:98E3  LDA #$01
81:98E5  JSL $84:858D
81:98E9  RTS
```

Therefore state 0 explicitly performs:

```
current pack id $0305
-> establish CA:C000 pack context
-> search/start entry_id 0x01
```

This is a direct static call chain, not a byte-pattern inference.

## 2. 84:8508 establishes the pack record-table base

84:8508 receives a pack id.

It computes:

```
CA:C000 + 3 * pack_id
```

and loads that 24-bit master entry into:

- $A7/$A9: pack-local record-table root used by the record scanners;
- temporary $98/$9A for inverse normalization;
- $126A/$126E pack context.

The helper then restores the caller's original current script pointer.

Thus setting a pack context does not by itself replace the running script
pointer; it establishes the pack-local tables used by later record/entry
selection.

84:850B is a second supported entry into the same body. It skips the initial
STA $126A and therefore updates current $126E while preserving base $126A.
There are many direct callers of this temporary/current-pack form.

## 3. 84:858D -> 859A starts the record scan

84:858D is a bank-safe wrapper around local 84:859A.

84:859A begins with:

```
STA $126B        ; requested entry id
STZ $AA
...
LDA $A7
STA $AB
LDA $A9
STA $AD
STZ $126F        ; record index starts at zero
```

It therefore begins scanning the current pack's record-pointer table from
record index 0.

The scan advances record pointers in order until the requested entry is found
and a VM slot is started.

## 4. 84:8699 is the CPU reader for the proven record header

The static catalog had independently established:

```
[entry_id:1][substream_ptr16:2] ... 00
```

84:8699 is now confirmed as the runtime reader for that exact grammar.

It:

1. copies the selected record pointer to a temporary 24-bit pointer;
2. starts Y=0;
3. reads one entry id;
4. zero means no match/end of header;
5. otherwise compares the byte with $126B;
6. on mismatch advances Y by 3 and repeats;
7. on match reads the following 16-bit substream pointer;
8. applies bank-wrap correction;
9. returns the selected pointer in $06/$08.

84:8684 then calls 84:8021 to create/run the selected VM substream.

This closes the runtime reader for:

```
pack -> record_index -> entry_id -> substream
```

which is the same hierarchy used by
`tools/python/catalog_map_selectors.py`.

## 5. Every record-0 primary map selector is entry 0x01

The full primary catalog contains 226 rows at record_index 0.

All **226 / 226** have:

```
entry_id = 0x01
```

Breakdown:

- confirmed normal: 108 / 108 are record0 entry 0x01;
- mode unresolved: 118 / 118 are record0 entry 0x01.

Therefore the state-0 startup path above reaches the exact substream family
containing the dominant map-selector backlog.

This proves **state-0 seed reachability** for the record-0 entry-1 family.

It does not yet prove that every later opcode in a persistent VM slot executes
before a subsequent global mode transition.

## 6. CA:C2F4 is a different seed family: entry 0x79

84:C26E indexes CA:C2F4 with:

```
($0305 - 1) * 2
```

The table is self-bounded:

- table: CA:C2F4;
- first data pointer: CA:C4E8;
- distance: 500 bytes;
- entry count: **250**.

IDs 0x01..0x13 are null.

IDs 0x14..0xFA contain 231 list pointers.

Each list is a sequence of 24-bit script pointers terminated by 00 00 00.

Full verification:

- non-empty pack lists: **55**;
- seed scripts: **90**;
- malformed lists: **0**;
- seed outside same-numbered CA:C000 pack: **0**;
- seed not exactly at a valid substream start: **0**;
- seed entry id other than 0x79: **0**.

So all 90 seeds satisfy:

```
CA:C2F4[pack_id]
-> script inside CA:C000[pack_id]
-> exact substream start
-> entry_id 0x79
```

This proves that $0305 is used as the CA:C000 pack id in this seed path.

The reproducible outputs are:

- `tools/python/catalog_map_pack_seeds.py`
- `data/maps/selectors/map_pack_entry79_seed_catalog.csv`
- `data/maps/selectors/map_pack_entry79_seed_summary.json`

## 7. Entry 0x79 and record0 entry 0x01 must stay separate

CA:C2F4 does **not** point to the record0 map-selector entry.

The 90 seed pointers are all entry 0x79, often in later records.

The map-selector family is record0 / entry 0x01.

The two paths serve different startup/dispatch roles and should not be merged
in future reachability analysis.

## 8. Why the remaining 118 are not bulk-promoted yet

State 0 creates the record0 entry-1 VM path, but the C4 scheduler stores only
pack context per slot:

```
$126E <-> $0759,X
```

It does not freeze $1398 into the slot.

The pointer advance helper 84:840F/8410 only advances $98 and returns; VM
commands are scheduled discretely rather than consuming the whole substream in
one atomic native call.

Therefore a later global mode transition remains theoretically possible before
a deeper opcode executes.

For that reason the 118 record0 rows receive stronger reachability evidence,
but their existing mode-unresolved status is retained until mode persistence to
the 0x50 boundary is proven.

## 9. Next target

The problem is now much smaller:

```
state0 starts record0/entry1
        |
        v
first VM dispatch is normal mode
        |
        ?  prove mode remains 0 to candidate 0x50
        v
118 unresolved record0 selectors
```

Useful next steps:

1. classify the normal VM instructions before each candidate 0x50;
2. identify any prefix command that can trigger a $1399 transition;
3. promote prefixes whose state-0 path cannot leave mode 0 before 0x50;
4. leave only true branch/wait/state-transition cases for runtime tracing.

This is now preferable to assigning one mode globally per pack.
