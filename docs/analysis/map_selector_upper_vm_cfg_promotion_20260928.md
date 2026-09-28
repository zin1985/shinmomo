# Upper-range VM grammar and state-0 CFG selector promotion

Updated: 2026-09-28

## Result

The apparent prefix bytes A3/B2/B3/B4 are not ordinary C4 dispatch-table
opcodes. They are intercepted by the VM scheduler's upper-range grammar before
the ordinary opcode dispatcher.

Adding the proven grammar as a small control-flow graph promotes another
**43** previously unresolved record0/entry1 primary map selectors.

Canonical counts become:

- primary shapes: 263
- confirmed normal primary: **225**
- mode-unresolved primary: **38**
- immediate secondary pairs: 105
- confirmed normal immediate secondary pairs: **101**
- unresolved immediate secondary pairs: **4**
- standalone mode-ambiguous 0x51 shapes: 79

The 43 new primary rows include 16 immediate 0x51 pairs.

## 1. Scheduler byte-range grammar

At C4:809C, the scheduler has already loaded the next script byte and divides
it by range before falling through to the ordinary dispatcher:

- byte < 0xA0 -> ordinary opcode dispatcher at C4:87A2
- 0xA0..0xAF -> C4:8145
- 0xB0..0xBF -> C4:8121
- 0xC0..0xCF -> C4:814F
- 0xD0..0xDF -> C4:8108
- 0xE0..0xFF -> C4:812D

Therefore interpreting A3/B3/B4 through the ordinary C4:87D4 table is invalid.

## 2. Overlapping jump-table/code structure

The upper-range dispatchers themselves use overlapping jump tables:

- A-range: JMP ($817E,X)
- B-range: JMP ($818B,X)
- D-range: JMP ($819E,X)
- E-range: JMP ($81BD,X)

Relevant entries:

- A3 -> C4:83E3
- B2 -> C4:8223
- B3 -> C4:8215
- B4 -> C4:820A

This explains why blindly reading the ordinary dispatch table above A0
produced implausible handler words.

## 3. A3 grammar

A3 consumes one operand byte.

The helper at C4:83ED:

1. reads the operand;
2. advances the script pointer by 2 bytes total;
3. splits the operand into:
   - high bits: index;
   - low 3 bits: bit selector;
4. tests the corresponding bit in the $1246,X family.

A3 then pushes boolean 0/1 to the VM expression stack.

Thus:

```
A3 <bit-spec>
```

is a state/flag test expression.

It does not write:

- $035F
- $1398
- $1399

and does not re-enter C0:C9E7.

## 4. B2/B3/B4 grammar

All three consume a signed rel8 operand at +1.

### B2

C4:8223 sign-extends the operand and replaces the current script pointer with:

```
current_ptr + signed(rel8)
```

So B2 is an unconditional relative branch.

### B3

C4:8215 pops an expression-stack value.

- zero -> branch through C4:8223;
- non-zero -> advance 2 bytes.

### B4

C4:820A pops an expression-stack value.

- non-zero -> branch through C4:8223;
- zero -> advance 2 bytes.

So the common sequence:

```
A3 xx
B4 yy
```

is a flag test followed by conditional control flow.

## 5. Additional safe condition producers

The new successful CFG paths also require only two previously length-bounded
ordinary handlers beyond the already proven 96/10/11/33 family.

### opcode 0x08

C4:8A0D is a 4-byte condition operation. Its handler is local and ends by
advancing 4 bytes through C4:8410.

No mode-state or $035F writer exists in the bounded handler path.

### opcode 0x2D

C4:9679 is a 2-byte condition operation comparing against $0306 and routing the
result through the VM boolean helper.

It contains no external mode transition and no $035F/$1398/$1399 write.

## 6. State-0 descriptor proof remains intact

The state-0 helper 81:98D1 explicitly sets:

```
$035F = 2
```

before entry_id 0x01 is started.

The newly admitted A3/B2/B3/B4/08/2D operations do not change $035F.

Therefore every 0x10/0x33 descriptor lookup on a promoted CFG path still uses:

```
BAAC[2] -> C3:0850
```

and the same previously proven B910 target restriction applies:

- C0:B924
- C0:B944

No wider B91C target set is introduced by this promotion.

## 7. CFG promotion policy

The generator does not linearize conditional branches.

For a record0/entry1 candidate, it builds a deliberately small CFG from the
state-0 substream start.

Allowed operations are limited to the statically bounded mode-safe family:

- 96
- 10
- 11
- 33
- 08
- 2D
- A3
- terminal-only 15
- B2/B3/B4 control flow

For B3/B4 both runtime outcomes are represented.

A candidate is promoted only when its target 0x50 is reachable through this
safe grammar and every 10/33 descriptor encountered resolves through the
state-0-safe B910 target set.

Unknown instructions simply terminate that CFG path.

## 8. Reproducible outputs

The proof is encoded directly in:

- `tools/python/catalog_map_selectors.py`

Derived outputs:

- `data/maps/selectors/primary_map_selector_catalog.csv`
- `data/maps/selectors/secondary_map_selector_candidates.csv`
- `data/maps/selectors/state0_safe_prefix_promotions.csv`
- `data/maps/selectors/primary_map_selector_summary.json`

Current summary fields include:

- confirmed_normal_union = 225
- mode_gate_unresolved = 38
- newly_promoted_state0_safe_prefix = 99
- newly_promoted_state0_cfg_branch_rows = 43
- confirmed_normal_immediate_pairs = 101

## 9. Remaining work

The remaining 38 primary rows now form a much smaller residue.

The next pass should recompute their exact distribution rather than continuing
to use the old A3/B3 stop counts, because those two dominant families have now
been structurally resolved.
