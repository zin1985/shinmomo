# Dialogue closed-path reference

Updated: 2026-10-02

## Purpose

Define one strict static reference path for the dialogue workstream before expanding the same checks to other actors.

The closure scope is:

`scene -> actor -> spawn -> event -> condition -> dialogue source -> sequence -> page -> text terminator`

It intentionally does not claim to resolve the exact in-game place name, actor semantic name, relation-key gameplay label, or event continuation after the dialogue text record.

## Reference actor

The first fully closed static path remains:

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

The same strict checks are applied mechanically to all ten family-0x50 actors represented by the dialogue sequence model.

Closed to the same static-to-page standard:

- `F50-L001`
- `F50-L002`
- `F50-L003`
- `F50-L004`
- `F50-L005`
- `F50-L006`
- `F50-L007`
- `F50-L008`
- `F50-L009`
- `F50-L010`

Current result: **10/10 family-0x50 actors closed**.

The final five actors were enabled by resolving only independently evidenced text-token semantics:

- `02C5 = ください`
- `02C9 = わたし`
- `0x04 = switch to text table 4`
- `0x03 = switch to text table 3`
- previously verified `0x5B = ?`

Details and proof provenance are in:

`docs/analysis/family50_verified_charset_20261002.md`

and:

`data/dialogue/family50_verified_token_semantics_20261002.csv`

## What 10/10 means

The closure claim is deliberately narrow.

For each modeled family-0x50 actor, the repository now has enough confirmed static evidence to connect:

`scene -> actor -> spawn condition -> actor event -> CFG-resolved dialogue variant -> canonical text source -> page sequence -> 0x00 text terminator`

without unresolved decoder tokens.

It does **not** mean that all story/event semantics are solved.

## Deliberately unresolved

The following remain outside this closure scope:

- exact in-game place name for pack 0x50
- speaker semantic identity / character name where not independently identified
- gameplay meaning of relation key `0x90`
- event continuation after the text record terminates

This keeps the closure claim narrow: actor-to-page playback is statically closed without inventing higher-level semantics.

## Machine-readable outputs

- `data/npc_display/static_actor_dialogue_closure_20261002.json`
- `data/npc_display/static_actor_dialogue_closure_20261002.csv`
- generator: `tools/python/build_static_actor_dialogue_closure.py`
