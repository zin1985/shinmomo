# Static actor spawn conditions

Updated: 2026-09-30

## Purpose

Pack-aware scene selection fixes actor-set mixing, but it does not prove that every actor in the selected pack is currently spawned. Actor records themselves contain conditional control flow immediately before opcode 0x59.

The intended model is:

`scene -> actor spawn condition -> actor present/absent -> interaction -> dialogue condition`

## Confirmed branch grammar

Existing compact-VM analysis proves A3 is a WRAM $1246-family flag test, B3 branches on zero, and B4 branches on nonzero. Opcode 0x59 actor commands in this catalog are six bytes.

For an actor command immediately preceded by `B3 08` or `B4 08`, the relative branch skips exactly over that opcode59 actor command:

- `... B3 08 59 ...`: predicate=0 skips spawn; actor spawns when predicate != 0.
- `... B4 08 59 ...`: predicate!=0 skips spawn; actor spawns when predicate == 0.

## Coverage

- actor rows: 817
- unconditional direct opcode59: 327
- immediate skip-guard actors: 447
  - B3 guards: 354
  - B4 guards: 93
- directly evaluable single-A3 flag guards: 182
- simple 0x2D condition producers: 89
- simple 0x08 condition producers: 23
- compound VM predicates: 153
- complex/nonlocal pre-actor control flow: 43

For A3 flag tests, the bit address is mechanically recovered as `WRAM = $1246 + (bit_spec >> 3), bit = bit_spec & 7`.

Opcode 0x2D is already proven to be a two-byte condition operation comparing against $0306 and returning a boolean. Its gameplay meaning is not invented here. Opcode 0x08 and compound expressions retain raw predicate bytecode until their remaining semantics are closed.

## Viewer policy

When story state is unavailable, unconditional actors may be shown normally, while conditional or unresolved actors must be presented only as candidates. Once runtime state is supplied, the same state object should feed both actor spawn evaluation and dialogue-branch evaluation.

## Outputs

- `data/npc_display/static_actor_spawn_conditions_20260930.csv`
- `data/npc_display/static_actor_spawn_conditions_summary_20260930.json`
- `tools/python/catalog_static_actor_spawn_conditions.py`


## F50-L010 decoded compound predicate

F50-L010 is the one conditional-spawn actor in the pack-0x50 / `cfg_t04_l008_v2`
actor set. Its prefix is:

`3D 13 13 3D 15 13 E1 E7 17 07 13 E1 E7 B3 08`

Canonical ROM SHA-256:

`F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`

The shared helper at `81:A862` maps operand/id `0x13` to a 24-bit
one-hot mask at bit index 18. The three predicate terms resolve to:

- `3D 13 13`: test bit18 of `$3FA1..$3FA3`, concretely `$3FA3.bit2`.
- `3D 15 13 E1`: test bit18 of `$3FA4..$3FA6` and zero-test it,
  concretely requiring `$3FA6.bit2 == 0`.
- `17 07 13 E1`: key 0x07 routes through `C4:8D3B -> 81:A8F4`,
  which tests bit18 of `$161D..$161F`; the C4:8951 inversion followed by
  E1 yields positive membership, concretely `$161F.bit2 != 0`.

E7 conjunctions combine the three terms. The final B3 08 skips opcode59 when
the conjunction is zero.

Therefore the neutral, machine-evaluable spawn condition is:

`$3FA3.bit2 = 1 && $3FA6.bit2 = 0 && $161F.bit2 = 1`

The gameplay names of these three bitsets are not yet proven and are not
invented here.
