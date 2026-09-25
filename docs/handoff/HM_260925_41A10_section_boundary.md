# 41A10 section-boundary reclassification — 2026-09-25

## Runtime input
The designated ROM was not accessible in this execution environment. No substitute ROM was used. This cycle therefore used only committed static evidence.

## Theme
Re-evaluate the apparent end of the 88:9A10 selector resource using the archived extraction.

## Confirmed
The archived CSV shows a clean first 8-byte selector run at records 0..97, covering file offsets 0x41A10..0x41D1F. Keys progress from 00 through DE and the five condition columns remain selector-like.

Records 98..101 at 0x41D20..0x41D3F sharply break that grammar.

At record 102, offset 0x41D40, the prior selector grammar resumes: key 00, small condition columns, and target-like final columns. Records 102..127 form another ordered key run.

Therefore the earlier interpretation that record 98 is simply the end of the table is too strong. The committed evidence supports a segmented-resource model: selector block A at records 0..97, a 32-byte inter-section header/control area at records 98..101, then selector block B beginning at record 102.

## Strong hypothesis
88:9A10 belongs to a larger resource containing multiple selector sections. A generic matcher may receive a section base or descriptor and scan one section rather than a single global flat table. This explains why direct references to 88:9A10 are scarce and makes indirect resource traversal a better search strategy.

## Unconfirmed
- Exact semantics of the 32-byte inter-section area.
- Exact end of selector block B.
- Whether additional section headers exist after record 127.
- The matcher routine itself.
- Whether 0x39993 is a valid target in a later section. It must not be promoted solely from the old flat-record interpretation.

## Impact
Search for code that consumes a section descriptor/base plus an 8-byte stride, rather than only code with an immediate 88:9A10 pointer.

No ROM or raw runtime dump was added.
