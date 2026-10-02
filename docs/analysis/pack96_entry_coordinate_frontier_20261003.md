# Pack 0x96 destination-entry coordinate frontier — 2026-10-03

## Confirmed facts

The committed transition catalog contains four transitions into destination pack `0x96`, entries `0x02`, `0x03`, `0x04`, and `0x05`. All four resolve to canonical configuration `cfg_t09_l098_v2`, and none has committed arrival X/Y or a destination coordinate address. The four trigger addresses are `CC:0BD7`, `CC:DC7A`, `CC:DCA2`, and `CC:DDBD`.

Therefore `CC:0BD7` is not an isolated missing catalog join. It belongs to a pack-level destination-entry coordinate provenance gap spanning entries 0x02..0x05. The next useful boundary is the destination record-0 entry grammar / coordinate initializer for pack 0x96, not another search for same-pack+entry transition witnesses.

## Strong hypothesis

Entries 0x02..0x05 likely select entry-specific arrival state inside one shared map configuration. A common initializer or entry table is more likely than four unrelated missing opcode-0x58 witnesses. This remains a hypothesis until the entry grammar or runtime writes are recovered.

## Unconfirmed

No arrival coordinates are assigned here. No relationship between entry ID and map edge/direction is asserted.

## ROM policy

The canonical Drive ROM was not accessible in this run. No substitute ROM was used. This cycle uses committed metadata only.
