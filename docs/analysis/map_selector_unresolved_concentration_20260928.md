# Map selector unresolved concentration — 2026-09-28

## Confirmed from committed selector catalog

The canonical `data/maps/selectors/primary_map_selector_catalog.csv` contains 261 structurally strong primary 0x50 candidates: 126 normal-mode confirmed and 135 mode-unresolved.

Of the 135 unresolved rows, 116 are record_index 0 and only 19 are later records. Thus 85.9% of the unresolved primary-selector backlog is concentrated at pack record 0.

Across the full 261-row corpus, record_index 0 accounts for 224 rows (85.8%). Within record 0, 108 rows are already normal-confirmed and 116 remain unresolved.

Variant does not by itself resolve mode: record-0 variant 2 contains 93 confirmed and 98 unresolved rows; record-0 variant 1 contains 15 confirmed and 18 unresolved rows.

## Interpretation

This concentration makes pack-entry reachability the highest-information next step. Binding direct mode-state seeds/callers to pack entry contexts can potentially classify most of the 135-row backlog before deeper per-record parsing is needed.

This is a corpus-distribution result only. It does not prove that every record-0 selector executes at pack entry, nor that one mode state applies to an entire pack.

## Next

1. Bind direct mode-state seed callers to CA:C000 pack entry contexts.
2. Emit per-pack/per-record reachable-state metadata.
3. Join that metadata to the 116 unresolved record-0 rows first.
4. Handle the remaining 19 later-record rows with local control-flow evidence.
5. Propagate resolved parent evidence into unresolved 0x51 candidates.
