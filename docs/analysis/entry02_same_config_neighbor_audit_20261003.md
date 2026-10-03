# Entry 0x02 same-config neighbor audit (2026-10-03 14:11 JST)

## Confirmed

The six unresolved trigger arrivals using destination entry `0x02` were joined against committed known-entry-0x02 witnesses by canonical destination configuration. Three gaps have same-config witnesses: `0x9E/cfg_t24_l125_v2` has packs `0x9F,0xA0,0xA1,0xA2,0xA5`; `0xAE/cfg_t11_l101_v2` has pack `0xB0`; `0xB7/cfg_t47_l172_v2` has pack `0xB8`. Two are immediately adjacent in pack ID: `0x9E -> 0x9F` and `0xB7 -> 0xB8`.

The witness XY values vary even when canonical config and entry ID are identical. Therefore neither entry `0x02` nor `(canonical config, entry 0x02)` is sufficient to assign an arrival coordinate. This further narrows the missing layer to pack-local entry/initializer provenance.

## Strong hypothesis

Adjacent packs sharing the same canonical config are high-value structural templates because their coordinate addresses and route shapes can expose how neighboring pack records encode or reach entry-local XY. `0xB7/0xB8` and `0x9E/0x9F` should be inspected before broader scans. This is an address/provenance hypothesis, not a coordinate inference.

## Unconfirmed

No XY is assigned to `0x9E`, `0xAE`, or `0xB7` from these witnesses. Pack-number adjacency is not claimed to imply spatial adjacency. Canonical Drive ROM was unavailable in this cycle, so no raw-ROM verification was performed.
