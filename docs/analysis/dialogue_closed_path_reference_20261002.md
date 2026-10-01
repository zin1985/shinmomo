# Dialogue closed-path reference

Updated: 2026-10-02

## Purpose

Define one strict static reference path for the dialogue workstream before expanding the same checks to other actors.

The closure scope is:

`scene -> actor -> spawn -> event -> condition -> dialogue source -> sequence -> page -> text terminator`

It intentionally does not claim to resolve the exact in-game place name, actor semantic name, relation-key gameplay label, or event continuation after the dialogue text record.

## Reference actor

The first fully closed static path is:

- scene: `cfg_t04_l008_v2@0x50`
- actor: `F50-L004`
- selector: `0x59`
- controller: `CC:1D69`
- spawn: unconditional, `always`

The actor has two mutually exclusive dialogue branches.

### Branch common_true

- condition:
  `and(flag_test(spec=0x65,wram=$1252,bit=5),zero_test(relation_resolver_condition(key=0x90,subkey=0x00))) != 0`
- compact-VM path: `B3 06` falls through to `A4 05`
- dialogue command: `CC:1D62`
- text record: `0x50:0x05`
- text pointer: `C8:ACCE`
- decode: confirmed canonical direct decode, zero unknown tokens
- pages: 1
- final text terminator: `0x00`

### Branch common_false

- condition:
  `and(flag_test(spec=0x65,wram=$1252,bit=5),zero_test(relation_resolver_condition(key=0x90,subkey=0x00))) == 0`
- compact-VM path: `B3 06` branches to `A4 06`
- dialogue command: `CC:1D66`
- text record: `0x50:0x06`
- text pointer: `C8:ACF8`
- decode: confirmed canonical direct decode, zero unknown tokens
- pages: 2
- first inter-page boundary: confirmed family-0x50 three-line cadence
- final text terminator: `0x00`

All twelve closure checks pass.

## Mechanical expansion

The same strict checks were applied to all ten family-0x50 actors already represented by the dialogue sequence model.

Closed to the same static-to-page standard:

- `F50-L001`
- `F50-L004`
- `F50-L008`

The remaining seven actors fail the strict closure gate because at least one dialogue variant is not a zero-unknown canonical direct decode. They remain usable evidence, but are not promoted to `closed_static_to_page`.

## Deliberately unresolved

The following are not required for this closure scope and remain explicit unknowns:

- exact in-game place name for pack 0x50
- speaker semantic identity / character name
- gameplay meaning of relation key `0x90`
- event continuation after the text record terminates

This keeps the closure claim narrow: the actor-to-page playback path is statically closed without inventing higher-level semantics.

## Machine-readable outputs

- `data/npc_display/static_actor_dialogue_closure_20261002.json`
- `data/npc_display/static_actor_dialogue_closure_20261002.csv`
- generator: `tools/python/build_static_actor_dialogue_closure.py`
