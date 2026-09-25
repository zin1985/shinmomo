# Historical dialogue semantic-context handoff - 2026-09-26

Priority 1, G2/G4/G5. Static evidence cycle.

The specified attached ROM `/mnt/data/Shin Momotarou Densetsu (J)_original(1).smc` was not accessible in this run. No substitute ROM was used.

## Confirmed

- The 19 historical-hash-recovered strong-dialogue pairs already linked to exact A4 callsites were re-read through retained v33 decoder outputs.
- All 19 now have metadata-only semantic context labels without copying dialogue bodies into the new artifact.
- Family 0x4E covers farmland, shrine/save advice and a falling-object reaction.
- Family 0x50 spans Ginji equipment, Urashima/Yoro threads, Netaro/Ice Tower quest guidance, Hope Capital route/shops and a Mashira song/repeat-talk context.
- Provenance is historical token hash -> family/subindex -> selected source -> A4 callsite -> semantic context.

## Strong interpretation

These pairs are coherent NPC/tutorial/event/world-route dialogue and can seed event-context grouping.

## Unconfirmed

- exact speaker identity for most pairs;
- exact event record boundaries;
- runtime reachability in the specified attached ROM;
- location labels not independently supported outside the text.

## Progress impact

- G2 remains 63%; context linkage evidence improves.
- dialogue workstream evidence supports 77%.
- G1/G3/G4/G5 unchanged; overall remains 50.2%.
- unresolved visibility remains 2,206 because this cycle enriches context rather than classifying additional pairs.

## Next

1. derive event boundaries for Netaro/Ice Tower, Yoro, Hope Capital and Mashira clusters;
2. attach speaker/location only with independent evidence;
3. resume visibility classification of the remaining 2,206 pairs;
4. render only player-visible records;
5. keep runtime reachability proof separate.
