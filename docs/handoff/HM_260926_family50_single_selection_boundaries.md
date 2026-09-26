# Family 0x50 single-selection boundary handoff - 2026-09-26

Priority 1, G2/G4/G5. Static event-context cycle.

The pinned Drive ROM was fetched and verified before analysis: 2,097,152 bytes, SHA-256 F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98, header map mode 0x31 FastROM HiROM.

## Confirmed

- Latest-main family 0x50 boundary work is preserved.
- The previously unresolved selection 0x11 is a distinct enclosing record: CC:1DFE..CC:1E0F, 17 bytes.
- The previously unresolved selection 0x12 is a distinct enclosing record: CC:1E0F..CC:1E2F, 32 bytes.
- Both use the single-selection header grammar:
  - B0 A4 <subindex> B0 7A <body_cpu16> 7C <next_record_plus_1_cpu16> 00
- The body target is at record offset +0x0B.
- The 7C target is next enclosing-record start + 1.
- Selection 0x00 at CC:1D0B..CC:1D1C provides an independent same-family cross-check; it is the same 17-byte form as 0x11.
- Therefore 0x11 is not part of F50-R07, and 0x12 is not part of the 0x11 record.
- Semantic-context evidence can now keep Hope Capital shops (0x11) and Mashira song/repeat-talk (0x12) as separate event records.

## Strong interpretation

The 17-byte and 32-byte variants share one enclosing-record grammar and differ in body payload length/commands rather than source-selection mechanism.

## Unconfirmed

- exact speaker identity;
- runtime reachability;
- exact semantics of the body commands;
- cross-family universality of this enclosing-record grammar.

## Progress impact

- local Script VM/Event is 71%;
- local Dialogue workstream is 77%;
- G1/G2/G3/G4/G5 remain 47/63/49/44/48;
- overall remains 50.2%;
- unresolved visibility remains 2,206.

## Next

1. derive enclosing-event boundaries around family 0x4E selections 0x13/0x14/0x17;
2. attach speaker/location only with independent evidence;
3. resume visibility classification of the remaining 2,206 pairs;
4. render only player-visible records;
5. keep runtime reachability proof separate.
