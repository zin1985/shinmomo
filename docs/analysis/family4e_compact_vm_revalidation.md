# Family 0x4E compact-VM revalidation

Updated: 2026-09-26

## Purpose

This cycle resolves the ambiguity left by `HM_260926_family4e_a4_revalidation.md`.
That handoff correctly withdrew raw `A4 15` / `A4 16` from the byte-pattern heuristic because they did not match the then-accepted forms. New handler-level evidence now proves both are real compact-VM A4 instructions.

The correction is therefore additive: the heuristic withdrawal remains valid, while the stronger VM-boundary proof supersedes the conclusion that 0x15/0x16 are not source selections.

## Canonical input

- ROM size: 2,097,152 bytes
- SHA-256: `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`
- map mode: `0x31` FastROM HiROM
- family 0x4E script pack: `CC:18D1..CC:1B7A`

## Compact interpreter

The interpreter at `C4:809D` reads the current command byte and splits compact command classes by high nibble.

The A-class path reaches `C4:8145`, masks the low nibble, doubles the index and dispatches through `C4:817B -> JMP ($817E,X)`.

The A-class table is:

- A0 -> C4:846F
- A1 -> C4:83CD
- A2 -> C4:83D7
- A3 -> C4:83E3
- A4 -> C4:84AE

Thus A4 is a real compact opcode, not merely an observed byte pattern.

## A4 source-selection semantics

`C4:84AE` reads one operand byte from the current script pointer and calls `C4:876D`; it then advances the script by two bytes total.

The downstream path is:

`A4 <subindex>`
-> `C4:84AE`
-> `C4:876D`
-> `C4:8554` current-pack/family resolver
-> family stored in `$12B4`
-> `JSL C4:A0C3`
-> subindex stored in `$12B5`

This independently confirms the previously established A4 source-selection model.

## Normal-opcode lengths needed for family 0x4E

The normal dispatcher table at `C4:87D4` and its handlers establish:

- opcode `09` -> `C4:8A3A`: reads a 24-bit operand and advances four bytes total.
- opcode `43` -> `C4:9851`: one operand, two bytes total.
- opcode `71` -> `C4:940E`: two-byte operand, three bytes total.
- opcode `2A` -> `C4:9652`: one byte total.
- compact `A4` -> `C4:84AE`: one operand, two bytes total.
- compact `B0` -> `C4:81EA`: one-byte compact control/terminator form for parsing.
- compact `B2` -> `C4:8223`: one signed-relative operand, two bytes total.

## Family 0x4E command-boundary proof

The known section beginning at `CC:1AFD` parses without overlap:

- `CC:1AFD A4 13`
- `CC:1AFF B2 04`
- `CC:1B01 A4 14`
- `CC:1B03 B0`
- `CC:1B04 09 B9 1A CC`
- `CC:1B08 43 40`
- `CC:1B0A 71 02 00`
- `CC:1B0D 43 60`
- `CC:1B0F 71 03 00`
- `CC:1B12 43 20`
- `CC:1B14 09 B9 1A CC`

Because opcode 09 is exactly four bytes, the next opcode boundary is `CC:1B18`.

Therefore:

- `CC:1B18 A4 15` is a confirmed compact A4 source selection.
- it consumes two bytes, so `CC:1B1A 09 24 1B CC` is the next command.
- that opcode 09 consumes four bytes, so `CC:1B1E A4 16` is also a confirmed compact A4 source selection.
- A4 16 consumes two bytes, so `CC:1B20 43 B4` begins on the next valid command boundary.

This proof does not rely on the generic A4 byte-pattern scanner.

## Source-reader confirmation

The canonical mode-2 source reader resolves:

- 0x4E:15 -> `C8:AB58`, 94 logical tokens, SHA-256 `2fb61b722a52ca89645348f389048cf06c1481fad81adad76256e88dbaf2bc0e`.
- 0x4E:16 -> `C8:ABA0`, 12 logical tokens, SHA-256 `a56cb590637f9c4c3a2f32fee767a348c5865d2be476debdd92ff7a8bddb307e`.

## Historical-v33 reconciliation

The retained v33 decoder provides an exact independent cross-check.

### 0x4E:15

The retained stream beginning at `C8:AB58` was incorrectly split across historical segments 19 and 20. Segment 19 ended with byte pair `18 00`. Under the corrected logical-token rule, token `0x18` consumes the following byte even when that low byte is `0x00`, so that zero is not a record terminator.

Concatenating the state-contiguous segments 19+20 yields exactly 94 tokens and SHA-256 `2fb61b...bc0e`, identical to the current source reader.

The retained decoded context is coherent spoken dialogue. New metadata class: `strong_dialogue`. Speaker identity is not promoted.

### 0x4E:16

Historical segment 21 begins at `C8:ABA0` and is an exact 12-token match with SHA-256 `a56cb5...307e`.

It is a parameterized event/system text record rather than quote-delimited dialogue. New metadata class: `strong_visible_text`. The exact item/object represented by control/parameter token 0x09 remains unresolved.

## Impact

- family 0x4E proven source selections are now 0x13, 0x14, 0x15, 0x16 and 0x17.
- the generic heuristic remains conservative; 0x15/0x16 are added by explicit VM-boundary evidence.
- the historical crosslink tool is updated to stitch state-contiguous v33 rows when a trailing 0x00 is consumed as the low byte of token 0x18..0x1F.
- this repairs a reusable historical-decoder failure mode rather than special-casing one dialogue.

## Still unresolved

- semantic event boundaries for the surrounding family 0x4E mini-VM/data structure;
- exact meaning of the pointer loaded by `09 24 1B CC`;
- speaker identity for 0x15;
- exact parameter substitution represented by the leading 0x09 in 0x16;
- runtime reachability.
