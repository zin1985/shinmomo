# Recovered dialogue event-boundary seeds - 2026-09-26

Priority 1, G2/G4/G5. Static evidence cycle.

The specified ROM /mnt/data/Shin Momotarou Densetsu (J)_original(1).smc was not accessible. No substitute ROM was used.

## Confirmed

- The 19 recovered strong-dialogue pairs form 11 script-local boundary seeds from their exact A4 callsites.
- Seven two-member seeds are exact adjacent A4 selection pairs separated by four bytes: 0x4E:13-14 and 0x50:01-02,03-04,05-06,08-09,0A-0B,0D-0E,0F-10.
- Four recovered selections are isolated at CC:1B42, CC:1DFF and CC:1E10 plus the 0x4E single-member seed; these are not merged across larger gaps.
- This is a structural boundary seed, not a claim that each seed is a complete event record.

## Strong interpretation

The repeated four-byte A4 pairing pattern is a useful event-catalog skeleton and gives G4 a reproducible grouping primitive without relying on decoded dialogue wording.

## Unconfirmed

- exact VM record start/end around each seed;
- branch/condition ownership around each A4 pair;
- speaker and runtime reachability.

## Progress impact

- G2 remains 63%; G4 remains 44%; overall remains 50.2%.
- dialogue workstream remains 77% by evidence; this cycle improves event-boundary structure rather than visibility count.
- unresolved visibility remains 2,206.

## Next

1. decode surrounding VM opcodes around E07-E09 (Netaro/Ice Tower -> route/Hope Capital) to find enclosing record boundaries;
2. extend to E05-E06 (Yoro/Urashima);
3. extend to E10-E11 (Hope Capital/Mashira);
4. attach conditions/actor actions where structurally proven;
5. resume classification of the remaining 2,206 unknown source pairs.
