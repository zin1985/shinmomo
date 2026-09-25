# Confirmed findings, hypotheses, and unresolved items

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

