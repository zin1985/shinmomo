# State0 A0/B0 nested-call selector promotion

Updated: 2026-09-28

## Scope

This pass closes the final four unresolved record0 / entry1 state0 selectors without flattening compact opcode A0 into a fixed-length no-op.

Before this pass the canonical selector catalog contained 263 primary shapes, 240 confirmed normal primary selectors, 23 unresolved primary selectors, and 104 / 105 confirmed immediate secondary pairs.

## A0 / B0 call-return contract

C4:846F saves the caller VM context, advances the caller continuation by four bytes, pushes the continuation through C4:84B9, loads the embedded 24-bit target into $98/$99/$9A, increments $1266, and transfers execution to the nested script.

Compact B0 enters C4:81EA -> C4:80C5. The return path decrements $1266 and, when returning to the caller level, restores the saved context through C4:84D9.

The analyzer therefore models A0 as a nested call with B0 return. It does not treat A0 as a generic four-byte instruction.
## Concrete nested targets

The four call targets reached from the residual state0 prefixes are bounded and SHA-anchored to their exact substreams:

- CC:1828..CC:1888
- CD:F037..CD:F04C
- CD:6C9C..CD:6CBD
- CD:E34F..CD:E369

The nested evaluator is fail-closed. It explores both outcomes of B3/B4, follows B2, accepts only independently bounded opcode forms, rejects boundary escape or unknown operands, and requires a reachable B0 return.

Concrete nested-only forms include the proven low-branch form of opcode 0x52, exact opcode 0x02 routine-table targets, map selectors 0x50/0x51, C0..CD small literals, mode-safe 0x41/0x42, and narrowly bounded D5/64/7B forms. Descriptor-driven 0x10/0x33 still resolve through the proven state0 $035F=2 domain and B910 targets B924/B944.

The three opcode 0x02 operands used by these substreams resolve to runtime routines 84:CC8A, 83:BB7A and 83:ADE2. Their bounded bodies are SHA-anchored; the middle routine temporarily changes $035F but restores the saved value before returning.

## Outer CFG closure

After returning from A0, the pack-0x4C path immediately uses a C1 small literal. The already anchored C4:814F C-range path proves C0..CD are one-byte low-nibble literals, so the outer state0 CFG now admits that exact family rather than keeping only C2.
With this addition all four residual record0 / entry1 selectors are proven mode-safe:

- CC:0929
- CC:0931
- CD:EF0A
- CD:EF1C

## Result

Regenerating the canonical catalog yields:

- primary shapes: 263
- confirmed normal primary: **244**
- unresolved primary: **19**
- record0 / entry1 unresolved: **0**
- confirmed immediate secondary pairs: **104 / 105**

The only remaining unresolved primary selectors are later-record rows outside the state0 record0 / entry1 family. The one unresolved immediate secondary pair belongs to pack 0xED record 2 / entry 0x90: primary CD:E353 followed by secondary CD:E357.

## Next work

1. Recompute the 19 later-record rows by record index, entry id and first blocking grammar/mode context.
2. Resolve pack 0xED record 2 / entry 0x90 together with its immediate secondary pair.
3. Once selector modes are closed, cross-link pack/record/substream evidence to human-facing location labels.

## Safety boundary

Do not generalize A0 handling to arbitrary targets. Promotion is limited to SHA-anchored concrete substreams whose nested CFG is fully recognized. Raw ROM payloads are not written to repository outputs.
