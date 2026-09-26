# Family 0x4E local A4 context handoff - 2026-09-26

Priority 1, G2/G4/G5.

## Confirmed
- Family 0x4E script pack spans CC:18D1..CC:1B7A.
- Recovered selections 0x13 and 0x14 are at CC:1AFD and CC:1B01.
- The same local script region continues with selections 0x15 at CC:1B18 and 0x16 at CC:1B1E.
- A later selection 0x17 occurs at CC:1B42 after an intervening local transition cluster.
- The family 0x50 enclosing-record grammar is not assumed universal for family 0x4E.
- 0x15 and 0x16 gain event-local provenance, but visibility is not promoted without display/runtime evidence.

## Strong interpretation
0x13..0x16 belong to one tightly connected local script region. 0x17 remains a separate structural seed until branch ownership is decoded.

## Unconfirmed
- exact transition semantics;
- visibility of 0x15/0x16;
- exact record boundaries;
- runtime reachability.

## Progress impact
No percentage increase: Script VM/Event 71%, Dialogue 77%, overall 50.2%.

## Next
1. decode branch ownership around CC:1B22..CC:1B52;
2. determine display provenance for 0x15/0x16;
3. classify 0x15/0x16 visibility;
4. keep 0x17 separate until its incoming branch is proven;
5. continue the remaining unknown source-pair classification.
