# Pack 0x2E -> 0x50 trigger narrowing

Updated: 2026-09-30

## Confirmed runtime edge

Existing runtime evidence remains authoritative:

- source: `cfg_t07_l015_v2`, current pack `$0305=0x2E`, selector 7/15/2
- destination: `cfg_t04_l008_v2`, current pack `$0305=0x50`, selector 4/8/2
- observed order: `$0305` changes first, then `$126E/$12B4` converge to 0x50, then the new selector appears
- player action: walk south through the central exit of the shrine/save-like interior

The exact writer/trigger PC was not captured in the original trace.

## VM transition corpus status

The transition catalog now has no structural candidates:

- 1295 retained candidates
- 3 confirmed
- 1292 strong candidates
- 0 structural candidates
- non-terminal CFG blockers: 0
- unmatched terminal CFG blockers: 0
- raw opcode 0x57 backlog: 0

This means the missing 0x2E -> 0x50 trigger is no longer attributable to an unresolved opcode-boundary backlog.

## Direct pack-0x2E scan

All parsed VM records in pack 0x2E were checked for raw direct forms:

- `53 50 xx`: 0
- `55 50 xx`: 0
- `56 50 xx`: 0

Reachable pack-0x2E VM control flow likewise contains no direct 0x53/0x55/0x56 destination-0x50 instruction.

The only reachable external A0 call observed from pack 0x2E is from the entry-0x7A paths to `CB:CDFD` (pack 0x1E, record 21, entry 0x6C). The currently proven call graph does not connect that path to the known destination-0x50 transition entries.

## Known static VM candidates to pack 0x50

The retained static candidates include:

- `CC:C43C`, pack 0x88 / record 17 / entry 0x6C, opcode 0x56 -> pack 0x50 entry 0x04, arrival 29,55
- `CD:E833`, pack 0xED / record 19 / entry 0x2B, opcode 0x56 -> pack 0x50 entry 0x0B, arrival 34,49
- `CC:2FAE`, pack 0x59 / record 9 / entry 0x7C, reachable non-terminal opcode 0x56 -> pack 0x50 entry 0x10, arrival 34,49
- `CC:0B08`, pack 0x4C / record 2 / entry 0x77, opcode 0x53 -> pack 0x50 entry 0x02; independently runtime-confirmed for the world-map-to-village edge

None is currently statically bound to the pack-0x2E central exit.

## Native-writer exclusion

The decoded native routes that finish at pack 0x50 do not match the shrine-interior source:

- `C6:8027`, route `C6:809C`: context 0x50, saved node `0x4C,54,237,entrance 0x02`, final node `0x50,39,37,entrance 0x02`
- `C6:81B9`, route `C6:821E`: saved node beginning with pack 0x4C, then final pack 0x50 / entrance 0x02

These are compatible with a world-map route, not a direct source-pack-0x2E exit.

## Important map/config alias finding

`cfg_t07_l015_v2` is not unique to pack 0x2E in the static map-context crosslink. The same map selector configuration is associated with:

- pack 0x2E, source root `C8:6662`
- pack 0x69, source root `C9:08FD`
- pack 0xF7 record 17, source root `CA:A4EC`

Therefore runtime map identity and the VM/event pack executing the exit path must not be assumed to be identical. A cross-pack exit dispatcher or event-selection layer remains a live explanation.

## Next discriminator

The shortest decisive runtime capture is to break on the write that changes `$0305` from 0x2E to 0x50 and record, at that exact instruction:

- writer PC
- `$126E`, `$12B4`, `$0306`
- `$13B8/$13B9`
- VM pointer `$98-$9A`
- active controller/record identity if available

That will distinguish an opcode-0x53/0x55/0x56 path from a native/map-exit dispatcher without relying on visual-map identity.
