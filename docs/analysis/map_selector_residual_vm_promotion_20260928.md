# Residual state0 VM grammar promotion

Updated: 2026-09-28

## Scope

After the upper-range A3/B2/B3/B4 CFG promotion, the canonical map-selector
catalog had:

- primary shapes: 263
- confirmed normal primary: 225
- unresolved primary: 38
- confirmed immediate secondary pairs: 101 / 105

This pass targets the residual record0 / entry1 state0 family only.

## Fresh residual distribution

Before this pass, 19 unresolved rows were record0 / entry1.

Their first CFG blockers were concentrated in:

- E8: 6 blocker instances
- E1: 5
- 3D: 4
- A0: 2 rows / multiple nested instances
- D0: 1
- 64: 1

As each family was resolved, later blockers surfaced. The final remaining
record0 / entry1 rows are four A0-call cases only.

## E-range expression operators

C4:812D handles E0..EF by:

1. subtracting E0;
2. advancing the script pointer by one byte;
3. preparing the expression accumulator;
4. dispatching through the table at C4:81BD.

The following one-byte operators are now admitted as mode-safe:

- E0 -> C4:82BC, trivial return
- E1 -> C4:8351, zero-test/boolean operator
- E7 -> C4:832F, boolean conjunction-style operator
- E8 -> C4:8340, comparison/boolean operator

Their bounded handler/helper region has no direct $1398/$1399 mutation and no
C0:C9E7 re-entry.

## C2 literal

The C-range scheduler at C4:814F encodes C0..CD as small unsigned literals in
the opcode low nibble.

C2 is therefore a one-byte expression literal and is admitted directly.

CE/CF extended literal forms are not generalized by this proof.

## Opcode 0x3D subtype 0x02

Normal opcode 0x3D is variable length.

The residual family uses only:

`3D 02 xx`

C4:935C delegates through 84:C2CC. Subtype 0x02 dispatches to C4:C3A9.
Both branches from C3A9 return A=2; C4:935C increments that value and advances
the VM pointer by exactly three bytes including the opcode.

Only subtype 0x02 is admitted.

This closes the four pack-0x54 record0 / entry1 selectors.

## D-range concrete forms

C4:8108 proves D0..DF consume two operand bytes before dispatch, so the
instruction length is three bytes.

Two concrete residual forms are admitted:

- `D0 84 19`: read 16-bit value through pointer $1984
- `D5 5E 03`: pop expression value and store through pointer $035E

Neither operand aliases $035F, $1398 or $1399.

The D0/D5 handlers and stack helpers do not re-enter C0:C9E7.

## Opcode 0x13 concrete form

C4:8A94 consumes one operand and writes it to $035F.

The residual state0 path uses:

`13 02`

State0 entry1 already seeds $035F=2 at 81:98D1, so this command preserves the
proven descriptor-table selection rather than changing it.

Only operand 0x02 is admitted by the safe CFG.

## Opcode 0x64 concrete form

C4:92A9 consumes one flag byte.

The residual pack-F6 path uses:

`64 00`

With operand zero the optional flag branches are skipped, 81:98A6 is called,
and C4:895E advances the VM pointer by two bytes.

The bounded path does not mutate $035F/$1398/$1399 and does not re-enter
C0:C9E7.

Only `64 00` is admitted.

## Result

After regenerating the canonical catalog:

- primary shapes: 263
- confirmed normal primary: **240**
- unresolved primary: **23**
- confirmed immediate secondary pairs: **104 / 105**
- unresolved immediate secondary pairs: **1**

The state0 record0 / entry1 backlog fell from 19 to **4**.

Those four rows are:

- pack 0x4C: CC:0929
- pack 0x4C: CC:0931
- pack 0xEF: CD:EF0A
- pack 0xEF: CD:EF1C

All four are blocked exclusively by opcode A0 call semantics.

The later-record backlog remains 19 rows.

## A0 blocker

A0 is not safe to model as a simple fixed-length instruction.

C4:846F:

- saves the current script context;
- advances the caller by four bytes;
- pushes a return frame through C4:84B9;
- replaces $98/$99/$9A with the embedded 24-bit target pointer;
- increments call-depth-like $1266;
- transfers execution into the nested script.

B0 routes through C4:81EA -> C4:80C5, decrements $1266 and conditionally restores
the saved frame through C4:84D9, strongly supporting an A0-call / B0-return
pair.

The four residual selectors invoke these concrete A0 targets:

- CC:1828
- CD:F037
- CD:6C9C
- CD:E34F

A0 should therefore be closed with a recursive/nested CFG over these concrete
targets rather than flattened as a four-byte instruction.

## Next work

1. Build a fail-closed A0/B0 nested-call evaluator for the four concrete
   targets above.
2. Promote only callers whose entire nested call path is mode-safe and returns.
3. Then recompute the 19 later-record unresolved selectors by entry family and
   first blocking grammar.
4. Resolve the final one immediate 0x51 pair together with its parent primary.
