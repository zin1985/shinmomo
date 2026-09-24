# Confirmed findings, hypotheses, and unresolved items

## Confirmed facts

### Core

- `$0799` is treated as finalized branch-ready visibility state.
- Canonical visibility ownership is bank87-local in the current model.
- Branch outcome determines append/skip irreversibly for a frame.
- Append acceptance is branch-exclusive.
- Append traversal is contiguous-prefix-only.
- `append_count` ownership terminates at slot-loop finalization.
- Append buffer is immutable after finalization.
- `$0759` is append-gated execution dispatch only.
- NPC behavior pointers are execution-only selectors.
- VM/event/script layers are upstream configuration-only.
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

- The supplied 2 MiB ROM was available out-of-tree and identified by SHA-256 in
  `data/dynamic_probe_static/ROM_INPUT_MANIFEST.json`; the ROM itself was not
  copied into the repository.
- No supported SNES debugger executable (Mesen2/bsnes-plus) is installed in
  the Work environment, so this cycle produced **no dynamic trace**. Existing
  runtime summaries remain prior-cycle evidence and are not relabeled as a new
  execution.
- The next required observation is a debugger run covering normal-visible and
  off-screen NPC cases, with `$0799,X` writes correlated to append buffer/count
  changes. Until then, the Goal13 evidence level remains unchanged.
- A user-area survey found an existing reusable BizHawk 2.11 installation with
  `EmuHawk.exe`, Snes9x/bsnes cores, and prior Lua probes. The new launcher and
  probe are checked in, but the Work terminal policy prevented starting the GUI
  process, so the minimum CPU/frame/register/WRAM smoke test remains pending.

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

