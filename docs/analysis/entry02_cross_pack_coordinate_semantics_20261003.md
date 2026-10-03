# Cross-pack entry 0x02 coordinate semantics — 2026-10-03 13:19 JST

## Confirmed facts

The committed transition catalog contains **313** rows where destination entry `0x02` already has both arrival coordinates, spanning **152 distinct destination packs** and **108 distinct coordinate pairs**. Representative witnesses are externalized in `data/events/entry02_known_coordinate_witnesses.csv`.

Therefore recurrent entry ID `0x02` is **not a fixed coordinate constant across packs**. The same entry ID is compatible with many arrival coordinates. This rejects the overly broad hypothesis that the six unresolved `0x02` gaps can inherit one shared XY value.

The useful reusable layer is narrower: the engine grammar that maps `(destination pack, entry ID)` to a pack-local coordinate initializer/table may be shared, while the coordinate payload is pack-local.

## Strong hypothesis

For unresolved packs `0x96/0x9E/0xAE/0xB7/0xBD/0xB9`, search the record-0/entry table layout and aligned opcode `0x58` placement using known `0x02` witnesses as structural templates. Do not copy coordinates across packs.

## Unconfirmed

No direction/facing semantic is assigned to `0x02`. No coordinate is assigned to any of the six unresolved gaps.

## ROM policy

Drive指定ROMへアクセスできなかった. No substitute ROM was used.
