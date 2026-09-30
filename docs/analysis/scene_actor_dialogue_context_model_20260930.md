# Scene / actor / dialogue context model

Updated: 2026-09-30

## Separation of identities

- geometry/configuration: `config_id`
- minimum static scene: `config_id + active pack`
- runtime scene instance: `config_id + active pack + story/event state`
- actor instance: scene context + spawn condition + selector + position + event
- dialogue variant: actor/event + condition + sequence + pages

Do not use `config_id` alone as a place identity.

## Static inventory evidence

- actor rows: 817
- actor-bearing configs: 75
- configs associated with multiple actor-bearing packs: 24
- minimum static scenes (config/pack pairs): 114

`cfg_t07_l009_v2` is a direct example:
- pack 0x51: 11 actors
- pack 0x62: 7 actors
- pack 0xF9: 9 actors

The geometry may be reused by additional transition contexts even when those
packs do not currently have actor rows in the selector crosslink. Therefore
transition/geometry sharing and actor-family sharing remain separate evidence layers.

## Viewer rule

On transition, carry both destination_config_id and destination_pack.
Filter actors by scene_id before evaluating spawn conditions.
After actor selection, evaluate dialogue conditions against the same runtime
state. If state is unknown, present branch-separated candidates and never
concatenate them into one representative speech.

## Viewer implementation status

The world-viewer build now preserves scene context through dialogue association.

- dialogue actor lookup uses scene_id + record_id + selector_hex;
- dialogue sequence objects retain scene_id, pack_id_hex, and scene_context;
- static actor entities retain scene_id;
- config_id remains geometry identity rather than runtime scene identity;
- story/event flags remain a later selection layer and unresolved branches stay separate.
