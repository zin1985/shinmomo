# VM56 event-framed entry reachability closure (2026-10-11)

Repository: zin1985/shinmomo
Canonical ROM size: 2,097,152 bytes
Canonical SHA-256: F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98

## Results and scope

Ten of ten event-framed terminal VM 0x56 instructions have a *possible*
static CFG route from their bounded entry. One of them, CC:F4F9,
requires a deferred scheduler callback, not synchronous fallthrough.
This is NOT ten runtime-confirmed transitions. Source map/mode/flag
predicates remain unproven.

| Terminal | Blocker resolved | Independently verified handler | Static result |
| --- | --- | --- | --- |
| CC:848E | 0x39/0x40 | C4:9803 and C4:8FB3 | Potential normal VM path |
| CC:F4F9 | 0x25 at CC:F47A | C4:9517 and callback C4:9535 | Deferred-resume possible, callback execution unproven |

Opcode 0x39 reads one operand and increments Y to 2, then advances
through C4:840F. Opcode 0x40 reads two initial operands and four more
in the loop C4:8FC4..8FCF (BCC F5), then BRA CC at C4:8FCF
joins C4:8F9D. That tail calls C4:840F with Y=7.

Normal VM opcode 0x25 dispatches to C4:9517. It queues callback C4:9535
by setting $0F=$9535, $0D=$32 then JSL 80:AC1E (scheduler) and
returns. If the callback runs later, C4:9535 executes the pointer
advance through C4:895E, consuming two bytes total.
Runtime callback execution is not proven. The audit explicitly labels
CC:F4F9 as deferred_callback_possible, stores the exact registration
site CC:F47A, and sets callback_executed_in_runtime=false.

## Reproducible evidence

Verifier files:
- tools/python/verify_vm_opcode39_40_handlers.py
- tools/python/verify_vm_opcode25_deferred.py
- data/maps/transitions/vm_opcode39_40_proof.json
- data/maps/transitions/vm_opcode25_deferred_proof.json

Updated CFG:
- tools/python/catalog_map_transition_candidates.py
  normal VM 0x39 length 2; 0x40 length 7;
  0x25 length 2 ONLY as possible scheduled continuation
- tools/python/audit_vm56_entry_cfg.py
- data/maps/transitions/vm56_entry_cfg_frontier.json

Regression:
- scripts/test_vm_opcode39_40_handlers.py
- scripts/test_vm_opcode25_deferred.py
- scripts/test_vm56_entry_cfg.py

The full canonical transition catalog was rebuilt outside the repository.
It remained 1,295 rows and byte-identical SHA-256:
BEB5F8C603E3ECA35A342BAD6D19778F491FF87EBB33A3B9B2DBE2898392A208.

## Reproduction

Use the local canonical ROM path:
C:\Users\zin\Downloads\Shin Momotarou Densetsu (J)\Shin Momotarou Densetsu (J)_original.smc

Run both verifier scripts above with --rom PATH, rerun the VM56 entry
CFG audit with --rom PATH and run the three regression scripts.
The canonical ROM and raw captures must NOT be committed.

## Next proof, not a speculative source promotion

Use the dedicated hidden BizHawk lab to trace *executed* VM entries and
map transitions. Capture VM opcode PC, normal/special mode ($035F/$1398),
current map pack ($0305), saved return-map state, location, event flags,
and pre/post frame states. Specifically, observe C4:9535 callback execution
before declaring the CC:F4F9 0x25 resume completed.

Also trace real event entry callers and owners for other VM56 entries.
An A4 selection site in a nearby record is not necessarily a caller.
Never infer source map from script pack identity or static CFG path.

The 712 0x56s without framed event owner are still a major source-link
backlog. Viewer remains 149 map configurations, 56 bound edges, and
3 runtime-confirmed edges. Official completion is unchanged at 51.4%.
