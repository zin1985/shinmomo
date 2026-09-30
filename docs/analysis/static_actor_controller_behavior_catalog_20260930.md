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
