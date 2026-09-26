# Event-record structural frame catalog

Updated: 2026-09-26

## Purpose

Recent family 0x50 work proved that source selections can sit inside a larger enclosing record. This cycle tests whether the surrounding framing grammar generalizes beyond one family without reviving rejected raw-A4 heuristics.

The family 0x4E correction remains authoritative: raw `A4 15` / `A4 16` near `CC:1B18..CC:1B20` are not promoted. Only source selections already accepted by the source-reader reachability model are used for the source crosslink.

## Canonical input

The pinned Drive ROM was fetched and verified before analysis:

- size: 2,097,152 bytes
- SHA-256: `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`
- map mode: `0x31` FastROM HiROM

## Structural framing invariant

Across CA:C000 real script packs, the following 7-byte trailer can be validated without assigning opcode semantics:

`7A <body16> 7C <next_record_plus_1_16> 00`

A trailer candidate is accepted only when:

1. `body16` resolves inside the current script pack;
2. the resolved body address is exactly the byte after the 7-byte trailer;
3. `next_record_plus_1 - 1` resolves forward inside the same pack.

Adjacent accepted trailers provide an independent record-start anchor: the preceding trailer's next-record pointer identifies the following record start.

For all emitted linked records, that start byte is `0xB0`.

## Result

Canonical-ROM scan:

- real script-pack intervals: **230**
- families containing at least one valid trailer: **131**
- valid trailer candidates: **947**
- linked records satisfying the independent `B0` start invariant: **816**
- families containing linked records: **107**

This is structural framing only. It is not yet a claim that all 816 frames are complete semantic game events.

The most common bytes before the trailer are 4 (390 records), 12 (79), 20 (34), 18 (26), 10 (25), and 11 (21). The most common body sizes are 6 (317 records), 10 (236), 13 (39), 3 (39), 18 (29), and 17 (26). This shows a repeated family of record layouts rather than a single fixed-length structure.

## Family 0x50 validation

The generic scanner reproduces ten linked family 0x50 records, including the previously hand-verified boundaries:

- the `0x00` single-selection record;
- the seven `0x01..0x10` records;
- `0x11` at `CC:1DFE..CC:1E0F`;
- `0x12` at `CC:1E0F..CC:1E2F`.

This independently reproduces the local family 0x50 boundary analysis from a ROM-wide structural rule.

## Event -> source crosslink

The frame catalog was crosslinked only against the existing high-confidence source-pair usage catalog. No raw A4-looking byte is promoted by this step.

Results:

- validated high-confidence A4 source pairs/callsites considered: **2,202**
- validated source callsites that fall inside a linked structural record: **1,124**
- linked records containing at least one validated source selection: **713 / 816**
- families with event-frame -> source linkage: **98**
- linked records with no mapped source selection: **103**
- validated source callsites outside this framing grammar: **1,078**

Mapped-source multiplicity per record:

- one source: 444 records
- two sources: 174
- three sources: 64
- four sources: 22
- five sources: 5
- six sources: 1
- seven sources: 3

The 1,078 unmapped validated source callsites are not failures. They prove that this `B0 ... 7A ... 7C ... 00` grammar is one major event/resource framing class, not the only script-pack grammar.

## Family 0x4E implication

Family 0x4E's proven dialogue selections `0x13`, `0x14`, and `0x17` do not fall in the linked trailer grammar above.

Therefore:

- do not force family 0x4E into the family 0x50 frame model;
- keep `0x13/0x14/0x17` as proven source selections;
- keep `A4 15/A4 16` withdrawn;
- treat `CC:1B18..CC:1B52` as a separate mini-VM grammar problem.

This cleanly separates two parsing problems instead of making the family 0x50 rule artificially universal.

## Reproducible outputs

- `tools/python/catalog_event_record_frames.py`
- `data/events/event_record_frame_summary.json`
- generated `data/events/event_record_frame_catalog.csv`
- `tools/python/crosslink_event_source_records.py`
- `data/events/event_source_crosslink_summary.json`
- generated `data/events/event_source_crosslink.csv`

The generated CSVs contain addresses and metadata only; no unrestricted dialogue body or raw ROM dump is required.

## Progress impact

Conservative promotion:

- Script VM / Event workstream: **71 -> 72**
- Externalization workstream: **73 -> 74**
- G4 selector/resource semantics component: **55 -> 57**
- G4 complete-event-inventory component: **22 -> 26**
- G4 top-level: **44 -> 45**
- G1/G2/G3/G5 remain **47/63/49/48**
- overall G1..G5 mean: **50.2 -> 50.4**

The increase is deliberately limited because condition semantics, actor actions, state mutations and runtime reachability are not yet attached to most records.

## Next high-leverage work

1. Generate the full event-frame CSV in the canonical repo environment and retain it as the machine-readable event skeleton.
2. Join condition/selector evidence and known dialogue overlays into the 713 source-linked records.
3. Parse the complementary grammars represented by the 1,078 validated source callsites outside this frame class, starting with family 0x4E.
4. Promote records to semantic events only when conditions/actions/state transitions are independently linked.
