# Static actor controller / behavior catalog — 2026-09-30

## Purpose

This layer sits between visual semantics and full gameplay-role identification.

It deliberately does **not** infer that a humanoid-looking actor is a shopkeeper, enemy,
villager, or story character from appearance alone. Instead it records what the static
controller/event structure proves for each opcode-0x59 actor row.

The evidence chain is:

```
map/config + pack
 -> framed event record
 -> opcode 0x59 actor placement
 -> controller pointer
 -> structural 7A/7C dispatch trailer
 -> validated event-source linkage
 -> decoded dialogue when available
 -> behavior evidence class
```

## Controller pointer closure

Current corpus:

- 817 map-context opcode-0x59 actor rows
- 752 unique framed actor records
- **817 / 817 controller pointers equal the corresponding event-record trailer pointer**
- zero pointer mismatches

This extends the pack-0x50 runtime validation into a full static corpus invariant for the
currently emitted framed actor records.

The recurring structural trailer remains:

```
7A <body16> 7C <next_record_plus_1_16> 00
```

The catalog records this as a controller dispatch structure only. The keys are not given
game-facing names until their callers are independently closed.

## Event-source behavior classes

Actor rows are classified conservatively:

| class | actor rows | meaning |
| --- | ---: | --- |
| `dialogue_actor_confirmed_cfg` | 10 | actor -> conditional source selection -> canonical direct dialogue decode is confirmed statically |
| `dialogue_actor_strong_candidate` | 1 | actor-bound decoded dialogue is strong, but not at the pack-0x50 CFG proof level |
| `event_source_bound_actor` | 702 | at least one validated event source is statically connected; source semantics are not promoted to dialogue without decode/proof |
| `placed_actor_no_validated_source` | 104 | actor placement/controller is proven, but no validated source selection is currently attached |

Thus **713 / 817 actor rows** already have at least one validated event-source connection.
Only 11 of those are currently decoded to dialogue text. This separation prevents the
remaining 702 source-bound actors from being mislabeled as talking NPCs.

At unique framed-record level:

- 10 confirmed CFG dialogue records
- 1 strong decoded-dialogue record
- 653 event-source-bound records
- 88 placement-only records

## field06D9: initial-facing candidate

The fourth opcode-0x59 operand, stored into `$06D9,X`, has a strikingly constrained corpus
domain:

| value | rows | confirmed motion-pattern meaning |
| ---: | ---: | --- |
| 1 | 27 | right |
| 2 | 717 | down/front |
| 3 | 31 | left |
| 4 | 42 | up/back |

The value domain exactly matches the independently proven motion-pattern table:

```
1 -> (+1, 0) -> right
2 -> ( 0,+1) -> down/front
3 -> (-1, 0) -> left
4 -> ( 0,-1) -> up/back
```

This is strong structural evidence that opcode-0x59 `field06D9` seeds initial facing or a
closely related direction state. However, the controller reader that consumes this exact
`$06D9,X` overlay has not yet been statically linked in the current repository evidence.

Therefore the machine-readable catalog exposes:

- `initial_facing_candidate`
- `initial_facing_status=candidate_value_domain_matches_confirmed_motion_pattern`

and intentionally does **not** mark the field as proven facing yet.

## field0719: raw flags only

The fifth opcode-0x59 operand remains semantically unresolved. Current values are:

- 0x10: 549 rows
- 0x00: 207 rows
- 0x90: 27 rows
- 0x80: 16 rows
- 0x50: 13 rows
- 0x41: 5 rows

The bit-like distribution is preserved in the catalog, but no gameplay meaning is assigned.

## Viewer integration

The viewer loads `viewer/data/actor_behavior.json` as a behavior overlay.

Clicking an actor now exposes, alongside dialogue and sprite semantics:

- behavior evidence class
- controller pointer
- structural dispatch grammar
- initial-facing candidate and its candidate status
- raw field0719 seed
- validated event-source count
- decoded dialogue-source count
- behavior evidence string

This keeps behavior evidence separate from semantic-role guesses.

## Outputs

- `data/npc_display/static_actor_behavior_catalog_20260930.csv`
- `data/npc_display/static_actor_behavior_summary_20260930.json`
- `viewer/data/actor_behavior.json`
- `tools/python/build_static_actor_behavior_catalog.py`

## Next steps

1. Close the actual controller-field reader for `$06D9,X`. If it feeds the already-proven
   motion-pattern path, promote `initial_facing_candidate` to confirmed initial facing.
2. Decode `$0719,X` bit semantics by locating handler-specific readers.
3. Assign game-facing meanings to controller dispatch keys such as 0x7A / 0x7C only from
   caller evidence.
4. Use controller/event actions, not dialogue wording, to promote service/shop/inn/scripted
   actor roles.


## Record-body placement structure

The framed opcode-0x59 actor corpus also separates cleanly by where the six-byte actor
placement command appears inside the validated event body:

| record body shape | actor rows | meaning |
| --- | ---: | --- |
| `head_exact_placement_only` | 326 | the body is exactly the six-byte opcode-0x59 placement command |
| `prefix_plus_tail_placement` | 490 | validated VM/control prefix appears before a final six-byte opcode-0x59 placement |
| `head_placement_plus_suffix` | 1 | placement is at the body head and a short suffix follows |

The single suffix case is:

```
FF9-L005 / selector 0x03
59 03 02 03 01 10 71 0C 00
```

The existing opcode table maps 0x71 to the special >=0x50 handler at 82:8840 with a
two-byte instruction model. The current evidence does not yet provide a safe game-facing
label for opcode 0x71, so the catalog preserves the suffix bytes without inventing a role.

This body-shape classification is structural only. Prefix bytes are not equated with
movement, shop, dialogue, or other gameplay actions unless their VM semantics are
independently proven.

## Spawn-condition integration

The behavior catalog now also carries the independently generated actor-spawn condition
classification. Current actor-row counts are:

- 327 `confirmed_static_unconditional`
- 182 `confirmed_static_flag`
- 153 `confirmed_static_branch_unresolved_predicate`
- 112 `confirmed_static_control_partial_predicate`
- 43 `unresolved_complex_control_flow`

These fields remain orthogonal to semantic role. A conditional actor is not automatically
a story NPC, enemy, or service actor; the catalog only records that its placement is gated.

The machine-readable columns include:

- `record_body_shape`
- `record_body_size`
- `body_prefix_size`
- `body_suffix_size`
- `body_suffix_hex`
- `spawn_condition_status`
- `spawn_condition_expr`
- `spawn_visibility_when_state_unknown`


## field06D9 runtime corroboration and shared-overlay counterexample

The initial-facing interpretation has gained two independent pieces of evidence, but is
still intentionally **not promoted to confirmed**.

### Runtime front corroboration

All ten pack-0x50 actor records use `field06D9=2`. Three independently reconstructed
runtime sprite families provide direct visual cross-checks:

| selector | actor record scope | runtime group/frame | statically confirmed front frames |
| --- | --- | --- | --- |
| 0x24 | F50-L002 | group 2 / F240 | F239,F240 |
| 0x59 | F50-L003 / F50-L004 | group 3 / F35 | F35,F36 |
| 0x40 | F50-L001 / F50-L006 | group 3 / F11 | F11,F12 |

Thus three distinct selector families independently agree with the candidate mapping
`field06D9=2 -> down/front`.

### Shared-SoA counterexample

The same WRAM column cannot be given a universal global label. The available C0
disassembly contains a separate non-opcode59 handler:

```
C0:BAE8  LDA #$FE
C0:BAEA  STA $06D9,X

C0:BB33  LDA $06D9,X
C0:BB36  CLC
C0:BB37  ADC #$02
C0:BB39  TAY
C0:BB3A  LDA [$2A],Y
...
C0:BB4C  TYA
C0:BB4D  STA $06D9,X
```

Here the field is plainly acting as a script/table cursor or index. This directly
validates the repository's shared-SoA warning: column semantics are handler-local.

### Current conclusion

For the opcode59 actor path:

- the 817-row value domain exactly matches cardinal motion patterns 1..4;
- value 2 is independently runtime-corroborated as front in three sprite families;
- but the exact opcode59-specific reader from `$06D9,X` into a facing/animation path
  remains missing from the committed static evidence.

Therefore the field remains a **strong initial-facing candidate**, not a confirmed label.

Machine-readable evidence:

- `data/npc_display/field06d9_direction_evidence_20260930.csv`
- `data/npc_display/field06d9_direction_evidence_summary_20260930.json`
- `tools/python/build_field06d9_direction_evidence.py`


## field0719 corpus decomposition — 2026-10-01

A full re-aggregation of all 817 opcode-0x59 actor rows narrows the fifth operand from an
opaque byte to a sparse handler-local seed bitfield.

Observed byte values are exactly:

| value | rows | active bits |
| ---: | ---: | --- |
| 0x00 | 207 | none |
| 0x10 | 549 | bit4 |
| 0x41 | 5 | bit6 + bit0 |
| 0x50 | 13 | bit6 + bit4 |
| 0x80 | 16 | bit7 |
| 0x90 | 27 | bit7 + bit4 |

Therefore only bits 7, 6, 4 and 0 are seeded by the current static actor corpus. Bits 5, 3,
2 and 1 are never seeded in any of the 817 rows. The low two-bit field is consequently
restricted to values 0 or 1 in this corpus.

Cross-field correlation gives one additional fail-closed constraint: all 207 rows with
field0719=0x00 have field06D9=2, and all 16 rows with field0719=0x80 also have
field06D9=2. This is useful for future consumer tracing but is not enough to name either
bit as a facing or movement flag. The 0x10 population spans all four facing seeds, so bit4
is not merely a duplicate encoding of initial facing.

Current evidence classification:

- **confirmed:** opcode59 static actors seed a sparse field0719 bitfield using only
  bits {7,6,4,0}; bit4 is the dominant seed (589/817 rows when 0x10/0x50/0x90 are
  combined).
- **confirmed negative:** bit4 cannot be a simple copy of field06D9 initial facing,
  because its population spans facing values 1..4.
- **strong hypothesis:** the active bits are independent actor-state/behavior gates.
- **unconfirmed:** game-facing meanings of bit7, bit6, bit4 and bit0.

The next useful boundary is therefore not further corpus counting but tracing the
handler-local consumers of these four active bits. ROM-dependent naming must remain
fail-closed until those consumers are recovered.
