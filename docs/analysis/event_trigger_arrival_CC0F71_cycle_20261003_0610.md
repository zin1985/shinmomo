# CC:0F71 arrival provenance closure

## Confirmed
- `CC:0F71` is an opcode-0x53 transition wrapper to destination pack `0xBC`, entry `0x02`, canonical config `cfg_t32_l144_v1`.
- Independent transition row `CD:B6A1` is a CFG-reachable opcode-0x57 route with `context_0306=0xBC` and `destination_entrance=0x02`.
- That route-table witness retains final coordinates `(215,40)`.
- The matching pack + entrance pair provides independent arrival provenance for `CC:0F71`; the trigger region is updated to `(215,40)`.

## Strong hypothesis
- The opcode-0x53 and opcode-0x57 paths converge on the same destination entrance semantics for this pack/entry pair.

## Unresolved
- Runtime observation of the `CC:0F71` world trigger itself.
- The remaining nine arrival-XY-only trigger gaps.
- `CC:1160` phase/state discriminator.

## ROM access
Drive指定ROMへアクセスできなかった。No alternate ROM was used. This cycle uses only committed canonical-ROM-derived metadata.

## Next
Resolve `CC:0BD7` arrival provenance from committed transition/route evidence.
