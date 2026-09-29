# Native map transition catalog

Updated: 2026-09-29

## Scope

This pass inventories exact native STA $0305 sites outside the already
cataloged C4 VM opcode 0x53/0x55/0x56 transition grammar. No HTML viewer or NPC/sprite
integration is included.

Canonical ROM SHA-256: F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98
Git HEAD used for generation: 8a9729d9b01629b29f7b1bcc74bca3d86f9e6701

## Writer classification

There are **11** exact native STA $0305 sites outside C4:8B7B.
Five are restore/temporary-context writes and are excluded from the
statically enumerable destination-candidate rows. This does not mean they can
never realize a runtime edge: C1:8244/C1:8255 is now a strong mechanism
candidate for the confirmed 0x50 -> 0x4C return transition. Six other sites
belong to routines that construct or leave an explicit destination map state.

The key correction in this pass is 81:8207: it is a map-state **save** routine,
not a renderer. It copies active $0305/$1573/$157D/$15C3/$15C4/$13B9 into
indexed $151D..$1522 slots and advances $DD by six. 81:8204 clears that stack
and C1:8244 restores an indexed saved state. The exact caller PC for the
confirmed 旅立ちの村 -> world-map return edge was not captured, so this restore
mechanism is not promoted to an observed trigger address.

## Candidate families

C5:92F2 / writer C5:9310 selects one of eight X/Y pairs from C5:9323, writes
literal pack 0x4C to $0305, then calls the same 81:837F transition-state helper
used by VM opcode 0x56.

C6:8000 uses a 16-entry pointer table at C6:8060. Each selected route is:
context_0306, repeated [pack,x,y,entrance], then 00. Non-final nodes are saved
with 81:8207; the final node remains in active map state. Only that final node
is promoted into the candidate CSV.

C6:8164 searches the key/pointer table at C6:81C9 using $0306. Each route stores
zero or more [pack,x,y,entrance] states via 81:8207, then after a zero terminator
leaves final_pack and final_entrance active at C6:81B9.

C5:CB7C writes pack 0xF1 with an entrance derived from $195B but has no local
finalizer, so it remains structural_candidate. C6:82DD writes pack 0xED,
entrance 0x02, clears $1399, and jumps to 80:C9E7.

## Counts

- native writer sites: 11
- writer sites producing candidate families: 6
- restore/temporary-context writer sites excluded from statically enumerable destination rows: 5
- native transition candidate rows: 54
- strong candidates: 53
- structural candidates: 1
- rows with unique destination configuration: 39
- rows with destination X/Y: 24
- distinct destination packs: 39

## Conservative policy

source_pack/source_config_id remain blank. These native routines prove the
destination state they construct, but not the caller-time current map. The C6
route-stack intermediates are preserved as route evidence, not promoted as
visible map-to-map edges. Only the final active destination state is cataloged.

## Outputs

- data/maps/transitions/native_map_transition_candidates.csv
- data/maps/transitions/native_0305_writer_catalog.csv
- data/maps/transitions/native_map_transition_summary.json
- docs/analysis/native_map_transition_catalog.md
- tools/python/catalog_native_map_transitions.py

## Remaining blockers
- native routine callers/triggers are not yet semantically named; the 0x50->0x4C runtime return edge narrows C1:8244/C1:8255 to a strong mechanism candidate without an observed execution PC
- source map/config remains null because caller-time $0305 is not statically proven
- C5:CB81 has no local transition-finalizer call and stays structural_candidate
- native route stack entries are state-stack construction; only the final active destination is promoted
