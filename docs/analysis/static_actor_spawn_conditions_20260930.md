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
