# 新桃太郎伝説解析 vol015: A4 handler / 9EB1 token trace (2026-04-30)

## Scope
User request:

1. Trace the A-value supply into the computed-dispatch side that reaches `84:8763`.
2. Trace what `C7:8D9E` token `02` and `C7:8DE9` token `0F` activate under the `9EB1` control-family path.

## Important correction
The prior note referred to `84:8763` as the A-saving entry, but the actual entry that saves A is:

```asm
84:876D  48        PHA
84:876E  EE 68 12  INC $1268
...
84:8785  68        PLA
84:8786  20 54 85  JSR $8554
84:8789  22 C3 A0 84  JSL $84:A0C3
```

`84:8763` is in the middle of the preceding routine (`LDA $1268 / CMP $0619,X`). The correct label to use is therefore **`84:876D`**.

## 1. A-value supply into `84:876D -> 84:8786 -> 84:A0C3`

The only static `JSR $876D` found is:

```asm
84:84AE  B7 98     LDA [$98],Y
84:84B0  20 6D 87  JSR $876D
84:84B3  A0 02     LDY #$02
84:84B5  20 0F 84  JSR $840F
84:84B8  60        RTS
```

This handler is reached through the A-class mini-VM dispatch table:

```asm
84:8145  29 0F     AND #$0F
84:8147  0A        ASL A
84:8148  AA        TAX
84:8149  20 7B 81  JSR $817B
...
84:817B  7C 7E 81  JMP ($817E,X)
```

The table entry for opcode `A4` is:

```text
A4 -> 84:84AE
```

Therefore the A reaching `84:876D` is **the 1-byte operand immediately after inner mini-VM opcode `A4`**, read by `LDA [$98],Y`.

The full flow is:

```text
inner mini-VM sees opcode A4
  -> A-class table dispatch via 84:817E
  -> A4 handler 84:84AE
  -> A = byte at [$98]+Y, normally operand after A4
  -> JSR 84:876D
  -> PHA / callback setup / PLA
  -> JSR 84:8554, which preserves A while resolving CA:C000 master index into $126E/$12B4
  -> JSL 84:A0C3, where A is stored to $12B5
```

So `84:8554` still provides the master-table index side (`$12B4`), but **it does not create the A value**. A comes from the `A4` operand.

## 2. `C7:8D9E` token `02` under `9EB1`

Normal `9E10` handling:

```asm
84:9E18  JSR $9E34     ; read next token
84:9E20  CMP #$50
84:9E22  BCS literal
84:9E24  TAX
84:9E25  BEQ end
84:9E27  JMP $9EB1     ; control token 01..4F
```

`9EB1` recognizes token `02` explicitly:

```asm
84:9EB1  C9 02      CMP #$02
84:9EB3  D0 03      BNE ...
84:9EB5  4C 34 9F   JMP $9F34
```

At `C7:8D9E`, the byte stream is:

```text
C7:8D9D  A2
C7:8D9E  02
C7:8D9F  C5
C7:8DA0  5C
C7:8DA1  01
C7:8DA2  0F
```

If the cursor points to `C7:8D9E`, token `02` performs:

```text
read token 02
read next byte C5
value = C5 - A0 = 25
family type = 01
try AE3A(value=25, type=01)
```

`AE3A` direct-hit table does not contain `(25,01)`, so the path falls back to the C7 descriptor table. For type `01`, fallback entry is table index 0:

```text
C7:0000[0] = C7:02EE
C7:02EE first byte = 00, so $12AA = 00
stream cursor becomes C7:02EF
```

Then `9DBB` skips `0x25` zero-terminated records from `C7:02EF`, landing at:

```text
C7:0477  97 DA 9A 91 00 ...
```

So token `02 C5` activates:

```text
family type 01 / value 25
fallback root C7:02EE
selected record C7:0477
next returned token/raw-id begins with 97
```

## 3. `C7:8DE9` token `0F` under `9EB1`

At `C7:8DE9`, the stream is:

```text
C7:8DE8  01
C7:8DE9  0F
C7:8DEA  00
C7:8DEB  18 42 ...
```

Under the normal `9E10 -> 9EB1` path, token `0F` is **not handled** by any explicit branch in `9EB1`:

```asm
84:9EB1  CMP #$02  -> no
84:9EB8  CMP #$09  -> no
84:9EBC  CMP #$0A  -> no
84:9EC0  CMP #$11  -> no
84:9EC4  JMP $9E32
84:9E32  CLC
84:9E33  RTS
```

Therefore token `0F` activates **no family root** in this path. It is consumed as an unsupported/inactive control marker and returns with carry clear. The next byte remains `00`, so a subsequent normal read would hit an end marker.

## 4. Re-correction of the previous `9D91/9DBB` mini-trace

Previous cursor positions such as `C7:8D9D`, `C7:8D9E`, `C7:8DE9` should not be treated as the direct results of `$12B5=82/83/84/C1/C2/C8` without care.

`9DBB` does **record skip**, not byte skip:

```text
repeat X times:
  read tokens until 00
  if token is 18..1F, consume one extra byte
  when token 00 appears, decrement X
```

Using that actual rule, for weapon descriptor index `0x16` (`C7:8D13`, stream starts at `C7:8D14`), the corrected cursors are:

```text
$12B5=82 -> C7:9EA5, next 09
$12B5=83 -> C7:9EB0, next B3
$12B5=84 -> C7:9EC3, next 09
$12B5=C1 -> C7:A566, next 09
$12B5=C2 -> C7:A57D, next 09
$12B5=C8 -> C7:A64D, next 7D
```

Thus `C7:8D9E` and `C7:8DE9` are valid stream positions to understand token semantics, but they are **not** the corrected direct cursor results for the weapon hook ordinals listed above.

## Current progress impact

- Goal 7: 85% -> 88%
- Goal 8: 75% -> 76%
- Goal 9: 66% -> 69%

The most important update is that the A4 inner opcode path now connects cleanly to `84:876D -> 84:8554 -> 84:A0C3`, and token `02` is confirmed as recursive family selection while token `0F` is inactive/default under `9EB1`.
