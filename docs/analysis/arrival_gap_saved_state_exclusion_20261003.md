# Arrival-gap provenance elimination — 2026-10-03 12:16 JST

## Confirmed facts

The current nine `arrival_xy_only` event-trigger gaps are already classified as requiring new coordinate evidence below the transition catalog. Six use destination entry `0x02`, two use `0x07`, and one uses `0x0C`.

A fresh audit of the committed `saved_state_return_candidates.csv` shows that opcode `0x54` is a terminal saved-state-return path: C4:8B4F calls 81:895A; the engine later restores indexed saved map state through C1:8244/C1:8255. Those rows deliberately leave destination pack/config/X/Y blank because the destination is runtime-dependent saved state.

Therefore the committed opcode-0x54 saved-state-return corpus cannot provide a fixed `(pack, entry) -> arrival XY` witness for the nine direct destination-entry gaps. It should not be joined to those gaps merely because both mechanisms ultimately restore map state.

## Strong hypothesis

The highest-information static frontier is now narrower: search for a fixed destination-entry initializer/table, aligned opcode `0x58`, or independent route-table evidence for recurrent entry `0x02` across packs `0x96/0x9E/0xAE/0xB7/0xBD/0xB9`. Saved-state-return rows are excluded unless a future provenance link proves one of those direct transitions actually enters the saved-state path.

## Unconfirmed

No coordinate, facing, edge, or direction meaning is assigned to entry `0x02`, `0x07`, or `0x0C`. No claim is made that equal entry IDs imply equal coordinates across packs.

## ROM policy

Drive指定ROMへアクセスできなかった. `Shin Momotarou Densetsu (J)_original.smc` was not available through the connected Drive search in this run. No substitute ROM was used, so no ROM hash/size verification or new ROM-derived bytes were produced.
