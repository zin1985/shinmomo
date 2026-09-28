# Record0 / entry1 prefix mode-safety narrowing

Updated: 2026-09-28

## Context

The conservative prefix decoder reaches 56 of 118 unresolved record0/entry1
primary selector candidates.

Fifty-five of those 56 use only normal opcodes:

- 0x96
- 0x10
- 0x11
- 0x33

The remaining aligned prefix additionally uses opcode 0x15.

No row is promoted in this note.

## Opcode 0x96

Normal handler:

- C4:9BAE

Its relevant external call is:

- 83:8ECA -> 80:A510

Static scans of:

- 83:8ECA..8F19
- 80:A510..A8FF

find no direct:

- STA/STZ $1398
- STA/STZ $1399
- JSL/JML C0:C9E7

This strongly narrows 0x96 as a mode-safe candidate handler, but promotion is
still tied to the complete prefix call graph.

## Opcode 0x11

Normal handler:

- C4:8A72

Its call chain is local to:

- 80:B340
- 80:B36F
- 80:B35C
- 80:B3A6
- 80:B3D6

The bounded C0:B340..B3DB region contains no direct $1398/$1399 writes or
C0:C9E7 re-entry.

## Opcodes 0x10 and 0x33

Normal handlers:

- 0x10 -> C4:8A54 -> 80:B572
- 0x33 -> C4:8A5E -> 80:B557

The two paths converge on the same descriptor/render chain:

- B7A7
- B7FA
- B8F2
- B910
- A151 / A170 / A185 / A30F
- BCEE / BD28 / C03C

Instruction-boundary disassembly across the relevant bounded regions exposes no
direct reference to $1398, $1399, or C0:C9E7.

## Remaining static blocker: B910 indirect dispatch

B7A7 derives $1123 from the high nibble of the selected descriptor byte:

```
LDA [$2A],Y
AND #$F0
LSR
LSR
LSR
STA $1123
```

Therefore $1123 is an even byte offset selected from descriptor data.

B910 then performs:

```
LDX $1123
JSR ($B91C,X)
```

So proving opcode 0x10/0x33 mode safety requires resolving the **actual
descriptor-selected target subset**, not treating the raw B91C area as a
uniform code table.

The first indirect table used by B8F2 is cleanly bounded:

- B8FE -> B906
- B900 -> B90B
- B902 -> B906
- B904 -> B906

The B910 table requires operand/context-sensitive resolution.

## Consequence

The current blocker for 55 fully aligned prefixes is no longer generic VM
parsing. It is specifically:

`0x10/0x33 operand -> B7A7 descriptor -> $1123 -> B910 indirect target`

Once the reachable B910 targets are enumerated and cleared for mode-state
mutation, the aligned selector set can be promoted or rejected without runtime
guessing.

## Current counts remain

- primary shapes: 263
- confirmed normal primary: 126
- unresolved primary: 137
- unresolved record0/entry1: 118
- prefix-aligned record0/entry1: 56

No count is promoted by this note.
