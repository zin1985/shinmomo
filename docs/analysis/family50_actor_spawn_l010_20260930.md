# Family 0x50 actor F50-L010 spawn predicate

Updated: 2026-09-30

## Result

The F50-L010 actor-spawn prefix is fully reducible to a neutral bitset
expression. No gameplay label is assigned to the bitsets.

Raw prefix:

`3D 13 13 3D 15 13 E1 E7 17 07 13 E1 E7 B3 08`

Final spawn expression:

`$3FA3.bit2 != 0 && $3FA6.bit2 == 0 && $161F.bit2 != 0`

B3 08 skips the following six-byte opcode59 placement when the final expression
is zero, so the actor exists only when all three terms above hold.

## 0x13 one-hot mapping

`81:A862` receives the id, validates/caps its range, then constructs a 24-bit
one-hot value across A / $1E / $1F. For id 0x13, the result is bit index 18,
i.e. byte 2 bit 2.

## First 3D term

Normal opcode 0x3D dispatches at C4:935C. It calls the C4:C2CC subtype table.

Subtype 0x13 -> C4:C705.

C4:C705 calls 81:A862, then ANDs the resulting mask against:

- $7E:3FA1
- $7E:3FA2
- $7E:3FA3

The nonzero path reaches C4:C353, which stores a nonzero value in $1957; the
zero path reaches C4:C362, which clears $1957. The outer 3D handler pushes that
result to the VM expression stack.

For id 0x13 this term is therefore `$3FA3.bit2 != 0`.

## Second 3D term

Subtype 0x15 -> C4:C750.

It performs the same one-hot test against $3FA4..$3FA6. The immediately
following E1 is the proven VM zero-test.

For id 0x13 this term is therefore `$3FA6.bit2 == 0`.

## Opcode 0x17 key 0x07 term

Opcode 0x17 dispatches at C4:8C04. Key 0x07 selects C4:8D3B.

C4:8D3B calls 81:A8F4 with operand 0x13. A8F4 calls the same one-hot helper
and tests the mask against $161D/$161E/$161F. It returns carry set on overlap.

C4:8951 converts carry clear to VM boolean 1 and carry set to VM boolean 0.
The following E1 zero-test therefore restores positive membership.

For id 0x13 this term is `$161F.bit2 != 0`.

## Composition

E7 is the proven boolean conjunction operator. The sequence composes:

`member($3FA1-set,0x13) AND NOT member($3FA4-set,0x13) AND member($161D-set,0x13)`

The semantic identities of the three sets remain unresolved.

## Machine-readable output

`data/npc_display/static_actor_spawn_predicate_terms_20260930.csv`
