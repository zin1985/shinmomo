# HM 260926 family 0x4E A4 revalidation

This cycle is a correction/reclassification cycle.

Confirmed from the canonical analysis input and current main:
- family 0x4E script pack spans CC:18D1..CC:1B7A.
- proven recovered-dialogue source selections are 0x13 at CC:1AFD, 0x14 at CC:1B01, and 0x17 at CC:1B42.
- those three are backed by accepted A4 source-selection grammar, source-reader reachability, and historical dialogue crosslink evidence.

Reclassified:
- raw A4 15 at CC:1B18 and A4 16 at CC:1B1E do not match the currently accepted high-confidence A4 source-selection forms.
- they are absent from historical_dialogue_callsite_context.csv.
- therefore recent rolling notes promoting 0x15/0x16 to source selections or branch members are withdrawn.
- bytes after CC:1B20 remain unclassified mini-VM grammar evidence; a five-arm dispatch is not confirmed.

Progress:
- no percentage increase.
- G1/G2/G3/G4/G5 remain 47/63/49/44/48.
- overall remains 50.2%, dialogue 77%, script-vm 71%.

Next:
1. prove mini-VM opcode boundaries around CC:1B18..CC:1B52.
2. continue visibility/context classification using only proven consumer provenance.
3. identify the segmented 41A10 matcher.
4. canonical sprite inventory/exporter.
5. complete event-catalog skeleton.
