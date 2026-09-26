# Family 0x50 event-record boundaries

Updated: 2026-09-26

The pinned Drive ROM was fetched and verified before analysis: 2,097,152 bytes, SHA-256 F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98, header map mode 0x31 FastROM HiROM.

## Confirmed

Family 0x50 script pack spans CC:1BE5..CC:1F16. Seven repeated enclosing records begin at CC:1D1C, CC:1D3A, CC:1D58, CC:1D76, CC:1D9C, CC:1DBA, CC:1DE0.

F50-R01 CC:1D1C..CC:1D3A, 30 bytes, selections 01/02.
F50-R02 CC:1D3A..CC:1D58, 30 bytes, selections 03/04.
F50-R03 CC:1D58..CC:1D76, 30 bytes, selections 05/06.
F50-R04 CC:1D76..CC:1D9C, 38 bytes, selection 07 then pair 08/09.
F50-R05 CC:1D9C..CC:1DBA, 30 bytes, selections 0A/0B.
F50-R06 CC:1DBA..CC:1DE0, 38 bytes, selection 0C then pair 0D/0E.
F50-R07 CC:1DE0..CC:1DFE, 30 bytes, selections 0F/10.

The recovered A4 pairs are therefore embedded in a repeated enclosing record grammar. The two longer variants prove that 07 and 0C belong to the same enclosing records as 08/09 and 0D/0E.

## Strong hypothesis

The extra selection in the 38-byte form is a guarded or alternate-selection subform. Exact opcode semantics are not promoted until handler linkage is proven.

## Unconfirmed

Exact speaker/runtime reachability, the semantics of the extra-selection subform, the following 11/12 short forms, and cross-family universality.

## Impact

NEW ANALYSIS from the canonical ROM. Local Script VM/Event 70 to 71 and Dialogue 76 to 77. Top-level G1..G5 remain unchanged.
