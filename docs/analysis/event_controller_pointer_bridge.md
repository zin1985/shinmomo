# Event VM -> controller behavior-pointer bridge

Updated: 2026-09-26

## Summary

A concrete cross-layer path now connects the event/script VM to the 64-slot controller/work SoA and back into later keyed script dispatch.

For the opcode-59 controller overlay:

`opcode 09 <ptr24>`
-> DP `$A4/$A5/$A6`
-> opcode `59 <five params>`
-> staging `$1856..$185D`
-> `81:ADBD` controller allocation
-> slot fields including `$0799/$07D9/$0819 = ptr24`
-> later C1 code reloads that pointer
-> `84:867D/8699` generic key-to-target matcher
-> selected target script.

This is handler-specific. It must not be generalized to every use of the same SoA columns.

## 1. Opcode 09: 24-bit pointer setter

Normal VM opcode 09 dispatches to `C4:8A3A`.

The handler:

- switches to 16-bit A;
- reads two operand bytes into DP `$A4/$A5`;
- returns to 8-bit A;
- reads the third operand byte into DP `$A6`;
- advances four bytes total including the opcode.

Thus:

`09 lo hi bank` -> `$A4/$A5/$A6 = bank:hi:lo`.

## 2. Opcode 59: five parameters plus current pointer

Normal VM opcode 59 dispatches to `C4:8F93`.

It reads five operand bytes into the staging area `$1856..$185A`, then copies the current pointer:

- DP `$A4/$A5` -> `$185B/$185C`
- DP `$A6` -> `$185D`

and calls `JSL 81:ADBD`.

The instruction is six bytes total including opcode.

## 3. 81:ADBD controller allocation

After allocation, the staged values are copied into a controller/work slot X.

Confirmed stores include:

- `$1857 -> $0659,X`
- `$1858 -> $0699,X`
- `$1859 -> $06D9,X`
- `$185A -> $0719,X`
- `$185B -> $0799,X`
- `$185C -> $07D9,X`
- `$185D -> $0819,X`
- `$1856 -> $0859,X`

Therefore, for this opcode-59-created overlay, `$0799/$07D9/$0819` form the 24-bit pointer previously loaded by opcode 09.

This is a new exact overlay and reinforces the existing union/type-dependent model of `$0619..$0A18`. It does not invalidate bank89 cases where some of these columns are movement/state work.

## 4. Downstream pointer reload

The same three columns are reloaded as a 24-bit DP pointer by later C1 paths.

At `C1:A250`:

- `LDA $0799,X -> $A4`
- `LDA $07D9,X -> $A5`
- `LDA $0819,X -> $A6`

At `C1:B1C0`, the same triple is reloaded before `A9 #$86; JSL 84:867D`.

At `C1:B3F1`, the same triple is compared against DP `$A4/$A5/$A6`, proving that the pointer is also used as a controller identity/selection key.

## 5. Generic key-to-target matcher

`84:867D` stores the requested key in `$126B` and calls `84:8699`.

`84:8699` copies DP `$A4/$A5/$A6` to a 24-bit indirect pointer and scans records:

`[key:1][target16:2]`

with a three-byte stride.

- key 0 terminates the table;
- matching key loads target16;
- the base bank is adjusted when the 16-bit target crosses the HiROM half-bank boundary;
- Carry reports match/no-match.

This confirms a generic keyed dispatch table, not just a family-specific byte pattern.

## 6. Family 0x4E concrete event graph

Family 0x4E executes:

`CC:1B1A 09 24 1B CC`

so the current VM pointer becomes `CC:1B24`.

At `CC:1B24` the generic matcher-compatible table is:

- key `0x48` -> `CC:1B34`
- key `0x49` -> `CC:1B3B`
- key `0x7C` -> `CC:1B42`
- key `0x6C` -> `CC:1B45`
- key `0x7B` -> `CC:1B52`
- key `0x00` -> terminator

The first two targets are opcode-59 controller creation blocks:

- `CC:1B34: 59 24 07 05 01 10 B0`
- `CC:1B3B: 59 24 06 03 01 10 B0`

Both inherit pointer `CC:1B24` through opcode 59, creating two controller slots with the same keyed behavior table and different parameter sets.

A concrete downstream caller at `C1:A1F2` loads key `0x7C` and calls `84:867D`. When the current controller carries pointer `CC:1B24`, the matcher resolves:

`0x7C -> CC:1B42`

and that target is:

`CC:1B42 A4 17 B0`

Source 0x4E:17 is the already recovered strong dialogue context for the falling-object reaction.

This is the first current cycle path that links:

controller state -> keyed event-table dispatch -> exact target script -> exact source selection -> recovered dialogue context.

## 7. Remaining targets

Targets `CC:1B45` and `CC:1B52` are longer scripts and remain to be semantically decomposed. Keys 0x48/0x49/0x6C/0x7B are not assigned game-facing meanings yet.

The dynamic caller around `C2:8725` also invokes `84:867D` with a runtime-loaded key, so the table mechanism is broader than the fixed 0x7C caller.

## Impact

This closes a previously missing bridge between:

- Script VM
- event/resource pointer setup
- controller/work SoA
- generic keyed dispatch
- dialogue/source selection.

It directly advances Script VM/Event, WRAM overlay characterization, G4 effect linkage, and portable architecture documentation.
