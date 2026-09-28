# Map selector instruction-boundary closure

Updated: 2026-09-28

## Result

The historical primary scan found 263 range-plausible byte shapes matching:

`50 <tileset 1..60> <layout 1..203> <variant 1..3>`

Instruction-boundary analysis now proves that three of those shapes are operands
inside other normal-VM instructions, not opcode 0x50 starts.

Final primary corpus:

- raw range-plausible 0x50 shapes: **263**
- proven non-opcode shapes: **3**
- instruction-level primary selectors: **260**
- confirmed normal primary selectors: **260 / 260**
- unresolved primary selectors: **0**
- immediate 0x50+0x51 pairs: **105 / 105 confirmed**
## CC:A71F is inside opcode 0x63

Pack 0x7F record 3 / entry 0x88 starts at CC:A6CE.

State-0 native initialization directly starts entry 0x88 through
`81:96FE LDA #$88 ; JSL $84:858D`, but the decisive result is instruction
boundary, not mode inheritance.

C4's normal dispatch maps opcode 0x63 to C4:9240. That handler calls C4:9280.
C4:9280 consumes four operand bytes and returns to C4:9240, which advances the
script pointer through C4:840F. Therefore opcode 0x63 is five bytes total.

The branch-reachable sequence beginning at CC:A708 is eight consecutive
five-byte 0x63 instructions. One of them begins at CC:A71C and spans:

`CC:A71C..CC:A720`

The byte at **CC:A71F** is operand 3 of that instruction. It is not an opcode.
## CC:FD5C and CC:FE6D are inside opcode 0x59

Both residual pack-0x9D substreams begin with the same shape:

`09 <24-bit operand> 59 50 ...`

Normal opcode 0x09 dispatches to C4:8A3A and consumes four bytes total.

Normal opcode 0x59 dispatches to C4:8F93. Its loop starts at Y=1, reads five
operand bytes, increments Y until 6, and then advances through C4:840F.
Therefore opcode 0x59 is six bytes total.

Accordingly:

- CC:FD5C is operand 1 of opcode 0x59 starting at CC:FD5B.
- CC:FE6D is operand 1 of opcode 0x59 starting at CC:FE6C.

Neither byte can be a primary map-selector opcode boundary.
## Reproducibility

The negative proofs are fail-closed in `tools/python/catalog_map_selectors.py`.

The tool anchors:

- normal dispatch entries for opcodes 0x09, 0x59 and 0x63;
- C4:8A3A, C4:8F93, C4:9240 and C4:9280 handler bodies;
- the subtype-4 0x3D path needed to bound the entry-0x88 branch;
- SHA-256 hashes of the exact three source stream slices.

Derived negative evidence is written to:

`data/maps/selectors/non_opcode_primary_50_shapes.csv`

The canonical primary catalog now contains only the 260 instruction-level
selectors. No raw ROM payload is stored in GitHub.
