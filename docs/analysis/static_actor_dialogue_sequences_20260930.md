# Static actor dialogue sequence / page model

Updated: 2026-09-30

## Purpose

This layer is the machine-readable playback path for the HTML viewer:

`actor click -> event -> condition variant -> dialogue sequence -> page 1 -> page 2 -> ...`

It extends, rather than replaces, the actor/event/source binding layer.

## Family 0x50 canonical direct decode

Family 0x50 is mode 2. Its master entry is `C8:ABC4`; the mode byte occupies the root byte and the fresh BD98 stream starts at `C8:ABC5`.

A canonical-ROM direct chain from `C8:ABC5 / bitcnt=0 / bitbuf=0` decodes subindices `0x00..0x12` continuously. All 19 logical records terminate cleanly at `0x00`.

This closes the previous F50-L001 gap and also recovers the two conditionally reachable source records `0x07` (`C8:AD3D`) and `0x0C` (`C8:AED1`) that the older A4-pair callsite catalog did not emit.

Machine evidence:
- `data/dialogue/family50_canonical_direct_decode_20260930.csv`
- canonical ROM SHA-256: `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`

## Confirmed condition VM grammar

The existing upper-range VM proof is reused:

- `A3 xx`: state/flag bit test, pushes boolean.
- `B2 rel8`: unconditional relative branch.
- `B3 rel8`: branch on zero.
- `B4 rel8`: branch on nonzero.
- `E1`: boolean zero-test.
- `E7`: boolean conjunction with the previously stacked operand.

For F50-L002..L008, the common prefix is:

`A3 65 21 90 80 E1 E7 B3 06`

`A3 65` resolves to WRAM `$1252 bit5`.

Opcode `21 90 80` temporarily uses relation key `$1923=0x90`, subkey/type `$1924=0x00`, and the already analysed `80:DA57` relation-to-entity resolver. `E1` zero-tests that condition result and `E7` ANDs it with the `A3 65` flag result.

The exact semantic identity of relation key `0x90` remains unresolved. It must not be labelled as a specific character merely from dialogue context.

The machine expression is therefore:

`and(flag_test(spec=0x65,wram=$1252,bit=5), zero_test(relation_resolver_condition(key=0x90,subkey=0x00)))`

## Three-way records

F50-L005 and F50-L007 contain a second guard:

`A3 0B B4 06`

`A3 0B` resolves to WRAM `$1247 bit3`.

F50-L005:
- common predicate != 0 -> source `0x07`
- common predicate == 0 and `$1247 bit3 == 0` -> `0x08`
- common predicate == 0 and `$1247 bit3 != 0` -> `0x09`

F50-L007:
- common predicate != 0 -> source `0x0C`
- common predicate == 0 and `$1247 bit3 == 0` -> `0x0D`
- common predicate == 0 and `$1247 bit3 != 0` -> `0x0E`

These variants are kept separately in `static_actor_dialogue_conditions_20260930.csv` and in the sequence JSON.

## Current F50 playback coverage

- static actors: 10 / 10
- source/sequence variants: 19
- canonical-direct decoded variants: 19
- display-page candidates: 36
- maximum recovered page height: 3 lines
- recovered pages over 3 lines: 0
- actors with condition branching: 7

The two hidden source variants add three pages total: one page for `0x07` and two pages for `0x0C`.

## Page and input semantics

Confirmed:
- `0x00` logical text-record terminator
- `0x01` explicit in-record line break
- `0x7D` / `0x7E` literal `「` / `」`

Strong candidate:
- each quote-delimited `0x7D..0x7E` block is a display page. All 36 F50 blocks fit the observed three-line window shape.

Still unresolved:
- the exact controller-input routine that advances between pages
- speaker display/name semantics
- choice/menu control opcode
- event continuation after the text record returns

These remain separate status fields so the HTML viewer can reproduce page order without pretending the input semantics are already proven.


## 2026-09-30 three-line page-transition closure

Canonical-direct family-0x50 has 17 observable page-to-page transitions. All 17 satisfy `internal 0x01 line breaks + post-quote padding 0x01 line breaks = 3`, with zero mismatches. Quote glyphs remain literal characters; the stronger transition evidence is the three-line newline cadence.

The display-state path also narrows input handling. The C4:A00D path distinguishes `$12B2 == 0x01`; the `$12AD & 7` state table includes input-sensitive handler C4:A264, which reads normalized held-input DP `$57` through mask `0xFC` gated by `$12C0` (initialized to `0xFF` at C4:9FEB), with a secondary `0xF4` path. The generic C0:AAC3 joypad pipeline maintains held state in `$57/$59` and new-press edges in `$5B/$5D`. Exact accepted button names and release/autorepeat semantics remain unresolved.


## 2026-09-30 scene-context correction

Actor/dialogue data must not treat `config_id` as a unique in-game place.

Static actor inventory currently has 817 rows across 75 configs. 24 configs are shared by more than one actor-bearing pack. The minimum static scene key is therefore:

`scene_id = config_id + "@" + pack_id_hex`

Runtime selection is stricter:

`scene instance = config_id + active pack + story/event state`

Example: `cfg_t07_l009_v2` has 27 actor rows, but they split into pack 0x51 (11), 0x62 (7), and 0xF9 (9). A viewer that renders all 27 merely because the geometry config matches is incorrect.

Dialogue variants remain branch-separated. A sequence is not labeled as the current line unless its condition is evaluated against the current scene state. If state is unknown, all reachable variants remain conditional candidates.
