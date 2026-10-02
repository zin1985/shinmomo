# CC:1160 pack 0xCE phase discriminator frontier (2026-10-03 04:14 JST)

## Scope
This cycle starts from main `71d684c9f4da98826bba87a2c3693def659d0748` and does not re-run completed map rendering/transition extraction. Canonical Drive ROM was searched by exact filename but was not accessible in this runtime, so no alternate ROM was used and no ROM-derived bytes were newly asserted.

## Confirmed from committed evidence
- `transition_CC_1160` targets pack `0xCE`, entry `0x02`, arrival `(22,28)`.
- Five canonical configurations remain compatible: `cfg_t04_l085_v2`, `cfg_t04_l086_v2`, `cfg_t05_l087_v2`, `cfg_t04_l088_v2`, `cfg_t04_l089_v2`.
- All five share native bounds X=16..31 / Y=16..28, so coordinate/bounds disambiguation cannot select one.
- The canonical configuration index gives five distinct configuration command addresses inside the same pack: `CD:9156` (l086), `CD:916D` (l087), `CD:9186` (l088), `CD:919F` (l089), `CD:91CC` (l085). Their command addresses are clustered but distinct, proving the ambiguity is not duplicate naming of one configuration record.
- Four candidates use primary tileset 4 / layout flag 0x80; `cfg_t05_l087_v2` alone uses primary tileset 5 / layout flag 0x00. This gives a high-information discriminator axis for the next ROM-enabled pass.

## Strong hypothesis
Pack 0xCE entry 0x02 dispatches through destination-side state/phase logic that selects one of several configuration commands. The unique tileset-5 candidate may correspond to a qualitatively different phase/state, while the four tileset-4 candidates likely represent layout variants within the other phase family. This is not yet a confirmed story flag mapping.

## Not confirmed
- The exact branch opcodes/flag addresses before the five configuration commands.
- Whether all five candidates are reachable specifically from CC:1160.
- A semantic label for each phase.

## Next evidence target
On the next ROM-accessible cycle, inspect the pack-0xCE entry-0x02 control span immediately preceding and between `CD:9156`, `CD:916D`, `CD:9186`, `CD:919F`, and `CD:91CC`. Record only control-flow metadata: branch predicate, flag/state address, comparison value, target configuration command. Do not commit ROM bytes.

If ROM remains inaccessible, move to the ten arrival-XY-only trigger gaps rather than inventing phase semantics.
