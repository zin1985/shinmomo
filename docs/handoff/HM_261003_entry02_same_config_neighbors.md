# HM_261003_entry02_same_config_neighbors

Cycle focus: unresolved destination entry `0x02` arrival provenance.

Confirmed: three of six unresolved entry-0x02 packs have known entry-0x02 witnesses on the same canonical config. Highest-value pairs are `0x9E -> 0x9F` (`cfg_t24_l125_v2`) and `0xB7 -> 0xB8` (`cfg_t47_l172_v2`), both pack-distance 1. `0xAE -> 0xB0` shares `cfg_t11_l101_v2` at distance 2. Witness XY differs across same-config packs, so do not infer coordinates from config or entry ID.

Next: inspect committed route/address structure around `0xB7/0xB8` first, then `0x9E/0x9F`; if canonical Drive ROM becomes available, verify the pack-local initializer/table directly after size/SHA-256 validation.

ROM status: Drive-specified `Shin Momotarou Densetsu (J)_original.smc` was not accessible in this cycle; no substitute ROM was used.
