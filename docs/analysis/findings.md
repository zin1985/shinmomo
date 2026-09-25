# Confirmed findings, hypotheses, and unresolved items

## 2026-09-25 FastROM HiROM correction

### Confirmed

- Canonical ROM header at file `0xFFC0` reports map mode `0x31`: FastROM HiROM.
- New canonical CPU labels use the high HiROM mirror, e.g. `0x0487A2 = C4:87A2`, `0x049E10 = C4:9E10`, and `0x070000 = C7:0000`.
- The earlier 2026-09-25 LoROM correction rule is superseded. Historical file offsets remain valid evidence.
- Machine code at `C4:9D4D` directly reads `$C7:0000,X`, independently validating the HiROM mapping.

## 2026-09-25 source-family catalog cycle

### Confirmed

- `C7:0000` is a 250-entry, 24-bit source-family master pointer table occupying file `0x070000..0x0702ED`.
- Every family root begins with reader mode 0, 1 or 2. Distribution is 67 / 55 / 128; no other mode occurs.
- `C4:9D4D` resolves family id to the master pointer, stores the mode in `$12AA`, advances past the mode byte, and installs the payload pointer in `$B1/$B2/$B3`.
- `C4:9D91 -> C4:9DBB` selects a zero-terminated record/subindex. `0x18..0x1F` consume a second byte even when that low byte equals `00`.
- Family 79 root `C8:A7DC` is mode02 and its payload `C8:A7DD` matches the previously restored Ginji-equipment dialogue.
- Family/index `0x16` root `C7:8D13` is used by weapon/descriptor work. Its proven subindex `0xC8` resolves to `C7:A64D`, crossing later master roots and proving that next-entry pointers are not family boundaries.

### Strong hypothesis

- The 250-family table is the common indexed source substrate used by dialogue plus several script/descriptor subsystems. Usage provenance should be sufficient to partition player-visible text from non-dialogue resources.

### Unresolved

- The earlier 7,877 next-root-bounded fragment count is retracted as a complete-record count; overlapping source entries require usage-driven enumeration.
- Complete usage-driven enumeration of `(family, subindex)` pairs, followed by classification into player-visible dialogue, descriptors and other source consumers.
- Event / speaker / location linkage for the player-visible subset.
- Final rendered canonical text corpus with completeness validation.


## 2026-09-25 historical mapping reconciliation

### Confirmed

- Historical full-address maps remain highly useful, but the earlier LoROM correction labels are superseded; reuse historical evidence by file offset and translate with the FastROM HiROM correction table.
- The 41A10 selector-table matcher and the target script VM reader are different layers. The normal target VM reader is already known at `C4:87A2/87BD/87CF/87D4`; the selector matcher for `C4:1A10` remains unresolved.
- 398xx 9-byte-looking rows are normal VM macro rows, not evidence of a dedicated fixed-record reader.
- `81:8D87` is a `$1569[0..9]` count aggregator: `$09` available normal actors, `$0A` normal actors, `$0C` total logical objects, `$0D` special objects.
- `85:86AC` has a condition family over `$180A[entity-1]`: `0x38` set bits, `0x39` clear bits, `0x3A` test selected bits clear.
- Dialogue source reading is independent of the 41A10 selector matcher. `C4:9E10/9E57` and `$B1/$B2/$B3` already define the source-reader core.
- The 64-slot `$0619..$0A18` controller/work SoA and the AF33 visible-object active-list pool must be treated as separate layers unless a handler explicitly stores a visible-object handle.
- Visible-object external handle to physical active-list node mapping is `physical = external + 2`; nodes 0/1 are sentinels.

### Strong hypotheses

- `$180A bit7` is hidden/suppressed/unavailable-like. Multiple feeder/count/event callers agree on this direction, but the exact game-facing label is still open.
- `0x300D3` containing `C4:1A05` is a valid resource clue near the 41A10 table, but not yet a proven selector-matcher bridge.

### Unconfirmed

- The routine that scans `C4:1A10` records and matches key/c1..c5.
- A universal pointer meaning for bytes +3..+5 of the `0x30048` descriptor bundle. Canonical-ROM revalidation shows this does not hold for all 35 records.
- Exact handler-specific controller-slot to visible-object-handle mappings outside the known caller examples.

## 2026-09-25 WRAM object-pool cycle

### Confirmed

- `$0619..$0A18` is a 0x400-byte object work region that fits 64 slots × 16 SoA columns at 0x40-byte stride.
- In bank89, `$0859/$0899/$08D9` are loaded into DP `$B9/$BA/$BB` and consumed through `[$B9],Y`; this is a 24-bit object-script pointer overlay.
- In bank89, `$0819,X` is assigned signed movement deltas and driven toward zero while `$07D9,X` moves in the corresponding direction.
- Cross-bank use shows that later columns are reused by different handlers. The pool therefore has union-like, type-dependent semantics rather than one permanent meaning per column.
- Bank85 demonstrates `$0999/$09D9` reuse as parameter/counter work, so those columns must not be globally named only as dimensions.

### Strong hypotheses

- In the bank89 overlay, `$0919/$0959` are an X/Y-like position pair.
- In the same overlay, `$09D9` participates in an edge/extent calculation, but its global meaning remains type-dependent.

### Unresolved

- Exact universal meanings of the first six columns `$0619..$0759`.
- Exact axis/name assignment for `$0919/$0959`.
- Runtime mapping from bank89 slot index to the downstream active-list/OAM object.

## Confirmed facts

### Core

- `$0799,X` state transitions are confirmed, but their direct visibility meaning is not.
- The `$0799,X` path is now known to sit inside bank89 script-driven object processing; its connection to the independent OAM path remains open.
- Branch outcome determines append/skip irreversibly for a frame.
- Append acceptance is branch-exclusive.
- Append traversal is contiguous-prefix-only.
- `append_count` ownership terminates at slot-loop finalization.
- Append buffer is immutable after finalization.
- `$0759` is append-gated execution dispatch only.
- NPC behavior pointers are execution-only selectors.
- VM/event/script are not configuration-only for the `$0799,X` path; object-script dispatch feeds this state-processing chain.
- Blob-runner family is terminal-only and cardinality-passive.
- Threshold crossing excludes the crossing slot immediately.
- Post-threshold append recovery is unsupported.
- `0x39850` macro rows are accumulation-domain, not canonicalization-domain.
- OAM pre-registration is downstream of append finalization.

### Graphics

- Runtime bridge CSV creation is compression-stable.
- `execution_frame + cutoff_index` improves branch-window isolation.
- Minimal branch-causal summaries remain sufficient for Goal13 verification.
- Frame reconstruction stays stable during severe transition churn.
- Visible-object summary reconstructs append_count proxy reliably.
- DMA, VRAM, and CGRAM remain presentation-only for Goal13.
- BG tilemap streaming is incremental.
- Tilemap world coordinates remain globally coherent.
- BG invalidation is spatially bounded.
- Metatile reconstruction converges deterministically after interrupted streaming.
- Sprite clustering survives severe OAM fragmentation.
- Contribution estimates remain logical-entity bound.
- CHR atlas transitions remain contribution-stable.
- BG invalidation and sprite redistribution remain causally orthogonal.

## Hypotheses

- `$0799,X bit7` may be an NPC/object state flag rather than a visibility authority; same-frame OAM correlation is required.
- `SKIP_MASK = $80`.
- Threshold `T` approximates visible-object plateau.
- `0x39850` rows encode compact contribution weights.
- Normalization resembles `AND #A / ORA #B`.
- `shared_state` likely resides in fast WRAM/zero-page-like working storage.
- Rank ordering approximates true slot ordering.
- Invisible contributors are probably off-camera active NPC slots.
- `execution_frame + cutoff_index` is the optimal branch-window narrowing pair.

## Unresolved items

### 2026-09-25 dynamic-analysis cycle

- The pinned Drive ROM source was checked and the matching analysis ROM was executed with BizHawk/Snes9x.
- Runtime execution reached a field scene; CPU callback and WRAM observation are operational.
- The current BAxx target probes did not fire during the observed field run, so no direct visibility claim is made from them.
- Static follow-up places the $0799,X processing inside a bank89 object-script path, so the prior visibility interpretation is reopened.
- Next step: exercise an NPC/event movement case and correlate $0799,X state with the known active-list/OAM path.

### Constants

- `SKIP_MASK`
- threshold `T`
- normalization masks

### RAM

- `shared_state` address
- `append_buffer` base
- `append_count` address
- slot-table bounds

### Opcode locations

- bank87 slot-loop entry
- normalize block
- `STA $0799`
- `AND #imm`
- skip branch target

### Graphics / cross-layer

- exact OAM scanline limits
- sprite priority arbitration rules
- CHR reuse saturation behavior
- palette overflow handling
- `contribution_est ↔ 0x39850 row` mapping
- `rank ↔ true slot index` calibration
- invisible contributor validation

