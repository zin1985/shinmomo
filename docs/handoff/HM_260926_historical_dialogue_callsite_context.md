# Historical dialogue callsite context handoff - 2026-09-26

Priority 1, G2/G4/G5. Static evidence cycle.

The specified attached ROM /mnt/data/Shin Momotarou Densetsu (J)_original(1).smc was not accessible in this run. No substitute ROM was used.

Confirmed:
- All 19 previously visibility-unknown pairs recovered by exact historical token-hash matching have high-confidence A4 source-selection callsites in the current usage catalog.
- Family 0x4E subindices 0x13, 0x14, 0x17 map to CC:1AFD, CC:1B01, CC:1B42.
- Family 0x50 recovered pairs map to CC:1D26 through CC:1E10.
- Provenance is now historical token hash -> current family/subindex -> selected source CPU -> same-family script-pack A4 callsite/pattern.
- No dialogue body is copied.

Strong interpretation:
The recovered pairs are actively selected by the same-index script-pack A4 source-selection mechanism, not merely adjacent source records. Speaker, location and named event remain unresolved.

Progress impact:
- G2 stays 63 percent; context_linkage component 38 -> 40.
- dialogue workstream 76 -> 77.
- G1/G3/G4/G5 unchanged; overall remains 50.2 percent.
- remaining visibility-unknown pairs: 2,206.

Next:
1. derive event boundaries around these 19 A4 callsites;
2. attach speaker/location evidence where possible;
3. classify remaining 2,206 pairs;
4. render only player-visible records;
5. keep runtime reachability proof separate.
