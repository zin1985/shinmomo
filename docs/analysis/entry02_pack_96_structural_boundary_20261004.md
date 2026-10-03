# Pack 0x96 entry 0x02 structural boundary (2026-10-04)

## Confirmed

- The unresolved arrival transition `CC:0BD7` targets destination pack `0x96`, record0 entry `0x02`, canonical configuration `cfg_t09_l098_v2`.
- `data/maps/selectors/primary_map_selector_catalog.csv` records pack `0x96` record0 as `CC:DBCB..CC:DC5C` and entry01 as `CC:DBDB..CC:DBF2`.
- Therefore the structural decode boundary for record0 entry `0x02` is `CC:DBF2`.
- Existing transition evidence also confirms entries `0x03`, `0x04`, and `0x05` exist for pack `0x96`, but this cycle does not assign their boundaries or arrival coordinates.

## Strong hypothesis

`CC:DBF2` begins the pack-local entry02 initializer/route used to establish the unresolved arrival state. Direct opcode/operand decoding requires the designated canonical ROM.

## Unconfirmed

- Opcode/operands at `CC:DBF2`.
- Arrival X/Y for pack `0x96` entry `0x02`.
- Exact structural starts for entries `0x03..0x05`.

## ROM availability

The designated Drive file `Shin Momotarou Densetsu (J)_original.smc` was not accessible in this cycle. No substitute ROM was used. Required input for direct decode remains the designated 2,097,152-byte ROM with SHA-256 `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`.
