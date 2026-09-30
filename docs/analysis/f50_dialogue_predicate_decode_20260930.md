# Family 0x50 dialogue predicate + L001 decode

Updated: 2026-09-30

## Canonical input

ROM SHA-256: `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`.

## F50-L001 is now directly decoded

Family 0x50 master root is `C8:ABC4`; that byte is mode `02`.
A fresh BD98 reader therefore starts at `C8:ABC5` with bitcnt/bitbuf zero.

Direct decode reaches `C8:ABEF/bitcnt07/bitbufE8`, emits 53 tokens,
has zero unknown tokens, and hashes to
`a653f4d79c63e7b24e71721dbb797a4ae6f4959f090fe233b81ca6a625d4c459`.

This closes the previous L001 gap caused by trying to reuse historical
mid-stream decoder states instead of initializing the family reader fresh.

Machine-readable evidence:
`data/dialogue/f50_l001_direct_decode_20260930.csv`.

## Shared F50 predicate

Raw F50 records L002..L008 share:

`A3 65 21 90 80 E1 E7 B3 06`

before their A4 source-selection alternatives.

The A-class dispatch table maps opcode A3 to `84:83E3`.
Static handler inspection shows A3 calls the bit-index helper and tests the
bitfield rooted at WRAM `$1246`. For operand `0x65`:

- byte offset = `0x65 >> 3 = 0x0C`
- storage byte = `$1246 + 0x0C = $1252`
- bit = `0x65 & 7 = 5`

So `A3 65` is a confirmed test of **story/state flag 0x65 = $1252 bit5**.
Its game-semantic name is still unresolved.

L005 and L007 add `A3 0B B4 06`, a secondary guard. Since A3 uses the
same bit-index mechanism, flag 0x0B maps to `$1247 bit3`; the exact B4
branch polarity/meaning remains unresolved.

## Setter evidence

Opcode A2 uses the same bit-index helper and sets the selected bit. A valid
script-region occurrence at `CC:2F7E` performs `A2 65`, immediately after
an `A3 65` test in the surrounding block. This independently proves that
0x65 is mutable event/story state rather than an actor-local dialogue index.

Nearby source selections decode dialogue referring to the descent from
Oeyama, an oni called `軍神`, and a traveler saying the obstruction has
cleared. This is useful semantic context, but it is not yet sufficient to
name flag 0x65 after a specific boss/event.

Machine-readable predicate inventory:
`data/events/f50_story_flag_predicates_20260930.csv`.

## Current interpretation

F50-L002..L008 are not seven unrelated per-NPC conditions. They share one
global flag predicate and choose dialogue variants from it. L005/L007 have
one additional flag guard, producing three source alternatives.

Next work:
1. trace B2/B3/B4 handler polarity exactly;
2. bind the `CC:2F7E A2 65` setter to its enclosing event/map;
3. use that event identity to assign a semantic name to flag 0x65;
4. feed the direct L001 decode into the generated actor dialogue sequence.
