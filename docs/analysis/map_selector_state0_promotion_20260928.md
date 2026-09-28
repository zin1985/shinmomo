# State-0 safe-prefix map-selector promotion

Updated: 2026-09-28

## Result

A narrowly bounded static proof promotes **55** previously unresolved
record0/entry1 primary opcode-0x50 rows to confirmed normal map selectors.

Canonical full-corpus counts become:

- primary shapes: 263
- confirmed normal primary: **181**
- mode-unresolved primary: **82**
- immediate secondary pairs: 105
- confirmed normal immediate secondary pairs: **84**
- unresolved immediate secondary pairs: **21**
- standalone mode-ambiguous 0x51 shapes: 79

The 55 promoted primary rows occupy 55 distinct packs and 37 distinct
(tileset, layout, variant) configurations.

Thirty-one of the 55 have an immediate valid opcode 0x51, so those secondary
rows are promoted at the same time.

## 1. State-0 entry1 seeds $035F = 2

The common transition path calls CBB6 before mode dispatch, but the stronger
record-local fact is inside the already-proven state-0 entry1 helper itself.

81:98D1 begins:

```
STZ $0307
LDA #$02
STA $035F
STZ $1619
LDA $0305
JSL $84:8508
LDA #$01
JSL $84:858D
RTS
```

Therefore the state-0 record0/entry1 VM family starts with:

```
$035F = 2
```

immediately before the current-pack entry_id 0x01 is requested.

## 2. Descriptor base is fixed

B7A7 uses:

```
LDA $035F
ASL
TAX
LDA $BAAC,X
```

With $035F=2:

```
BAAC[2] -> C3:0850
```

So the common aligned prefix family does not need a game-wide union of every
possible $035F value. Its descriptor records come from C3:0850.

## 3. Prefix family

The conservative prefix decoder previously found 56 unresolved record0/entry1
rows whose instruction boundaries reach the candidate 0x50 exactly.

Fifty-five use only:

- opcode 0x96
- opcode 0x10
- opcode 0x11
- opcode 0x33

The remaining aligned row additionally uses opcode 0x15 and is intentionally
left unresolved in this promotion.

The 55-row operand-selected descriptor IDs are:

```
04, 05, 06, 07, 08, 09, 0C, 0D, 0F, 10, 11, 1B
```

## 4. Prefix handlers preserve the proof state

Static bounded call-graph analysis of the 0x96 / 0x10 / 0x11 / 0x33 paths
finds no write to:

- $035F
- $1398
- $1399

and no re-entry to:

- C0:C9E7

before the candidate 0x50.

Relevant chains include:

- 0x96 -> 83:8ECA -> 80:A510 family
- 0x11 -> 80:B340/B36F/B35C/B3A6/B3D6
- 0x10/0x33 -> 80:B557/B572 -> B7A7/B7FA -> render/decode helpers

## 5. B910 indirect dispatch is fully resolved for this family

For each 0x10/0x33 operation, B7A7 loads one 8-byte descriptor from C3:0850.

The descriptor's final byte determines:

```
$1123 = (last_byte & 0xF0) >> 3
```

Across every descriptor selected by the 55 prefixes, $1123 is only:

- 0x00
- 0x02

B910 performs:

```
LDX $1123
JSR ($B91C,X)
```

Thus the only reachable B910 targets are:

- 80:B944
- 80:B924

No other overlapping B91C/code-table target is reachable in this state-0
family.

### B924

Exact routine:

```
LDA $1124
JSL $80:C07F
RTS
```

C07F/C093/C0B5 are local stream-state readers and do not mutate the map mode.

### B944

Exact routine:

```
JSL $80:BD28
RTS
```

BD28 is a local compressed-stream copy/decode routine and does not mutate the
map mode.

This closes the last indirect edge in the common 55-row prefix family.

## 6. Promotion rule encoded in the catalog generator

`tools/python/catalog_map_selectors.py` now reproduces this proof directly.

A candidate is promoted by this new rule only when:

1. record_index == 0;
2. entry_id == 0x01;
3. the entire prefix uses only 96/10/11/33;
4. canonical state-0 helper bytes prove $035F=2 immediately before entry1;
5. BAAC[2] resolves to C3:0850;
6. every 10/33 descriptor resolves B910 only to B924/B944;
7. exact B924/B944 routine anchor bytes still match.

If any anchor changes, generation fails closed.

## 7. Outputs

- `tools/python/catalog_map_selectors.py`
- `data/maps/selectors/primary_map_selector_catalog.csv`
- `data/maps/selectors/secondary_map_selector_candidates.csv`
- `data/maps/selectors/state0_safe_prefix_promotions.csv`
- `data/maps/selectors/primary_map_selector_summary.json`
- `docs/analysis/map_selector_prefix_decode_20260928.md`
- `docs/analysis/map_selector_prefix_mode_safety_20260928.md`

## 8. Remaining backlog

Primary unresolved is now **82**.

Of the original 56 instruction-aligned record0/entry1 rows, one remains because
its prefix additionally uses opcode 0x15.

The next static step is therefore:

1. bound opcode 0x15 and its callees for mode-state/$035F effects;
2. evaluate that one aligned row;
3. then expand safe prefix decoding into the A3/B3/E8/3D/A0/E1/D0/B4/64 stop
   families one family at a time.
