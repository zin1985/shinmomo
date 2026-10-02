# CC:1160 destination configuration phase split (2026-10-03)

## Scope
This cycle targeted the last destination-config-only event-trigger gap, `transition_CC_1160`, using the canonical Google Drive ROM plus committed map/config metadata. No ROM bytes or other copyrighted raw dumps are committed.

## Canonical ROM verification
- Drive file: `Shin Momotarou Densetsu (J)_original.smc`
- size: 2,097,152 bytes
- SHA-256: `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`
- result: exact match; canonical ROM was used in this cycle.

## Confirmed facts
1. The source trigger is the already-normalized exact-point predicate at world coordinate `(238,173)` and branches to `CC:1160`.
2. Canonical ROM bytes at `CC:1160` decode the terminal transition as `53 CE 02`: destination pack `0xCE`, destination entry `0x02`.
3. The committed arrival coordinate is `(22,28)`.
4. Pack `0xCE` has five committed canonical configurations relevant to this phase family: `cfg_t04_l085_v2`, `cfg_t04_l086_v2`, `cfg_t05_l087_v2`, `cfg_t04_l088_v2`, `cfg_t04_l089_v2`.
5. Their configuration commands begin at `CD:91CC`, `CD:9156`, `CD:916D`, `CD:9186`, `CD:919F` respectively. Each carries the same native opcode-0x52 bounds `X=16..31, Y=16..28`; therefore arrival `(22,28)` is valid in all five.
6. The previous bounds resolver correctly refused to emit a unique destination config for `CC:1160`: this is not missing bounds data, but a real one-to-many ambiguity at the current evidence layer.

## Strong hypothesis
The five pack-0xCE configurations are phase/state alternatives selected by destination-side control flow. The destination entry `0x02` alone does not identify one canonical visual/map configuration. A phase discriminator, likely the surrounding destination-side state predicates/branches near `CD:9140..91DC`, is required before promoting any single config.

## Not yet confirmed
- Which story/state predicate selects each of the five configs.
- Whether all five are reachable from `CC:1160` specifically, versus a subset sharing the same pack/entry family.
- Runtime phase observed when entering from world coordinate `(238,173)`.

## Consequence
Do not keep treating `CC:1160` as an ordinary destination-config lookup failure. Reclassify it as a phase-dependent destination-set problem. The next high-information task is to recover the selector/state predicate for pack `0xCE` entry `0x02`; after that, proceed to the ten arrival-XY-only trigger gaps.
