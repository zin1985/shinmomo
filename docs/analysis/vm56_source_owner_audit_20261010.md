# VM opcode 0x56 source-ownership and canonical ROM verification
Date: 2026-10-10. Canonical repository: zin1985/shinmomo.

## Motivation
The event-aware map graph currently has 149 map configurations and 56
source+destination bound edges (3 runtime-confirmed). The viewer has 1,238
source-unbound derived candidates; 721 of those are terminal 0x56 forms.

The opcode 0x56 normal-VM handler C4:8B6A sets global map state from its two
operands, but **the script pack holding an opcode is not necessarily the
player's active map pack**. Moreover the dispatch of 0x50+ opcodes is
VM-mode-dependent. Never infer a source configuration by script-pack equality.

## Independent exact-ROM audit

Command on the authorized Windows analysis machine:

    py -3 tools/python/audit_vm56_source_ownership.py --rom "C:\Users\zin\Downloads\Shin Momotarou Densetsu (J)\Shin Momotarou Densetsu (J)_original.smc"

The audit verifies canonical ROM size 2,097,152 bytes and SHA-256
F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98,
then checks for each indexed terminal opcode:

    0x56, destination_pack, destination_entry, 0xB0

At the exact CPU address derived from the candidate catalog. It does not
extract or commit the ROM or script payload.

Verified corpus:
- 722 / 722 terminal 0x56 byte sequences matched.
- 721 still source-unbound in generated Viewer; 1 source-bound.
- 10 / 722 overlap with a structurally framed event record.
- Only 7 / 722 additionally have validated source-selection / script-callsite
  crosslink evidence.
- Three frame-linked rows have no source-selection crosslink.
- 712 rows lack an event-record frame match; this is missing ownership
  evidence, NOT proof the opcode is invalid or never reachable.
- Zero mismatched record containment, opcode, or operand evidence.

High-priority event record + source-selection targets:
- CC:AD64 (F81-L007): 7 selected-source links
- CC:3DF1 (F60-L010): 3
- CC:3FAF (F60-L012): 2
- CC:B67B (F82-L009): 2
- CC:F4F9 (F9B-L021): 2
- CC:4A21 (F66-L010): 1
- CC:848E (F75-L013): 1

Three further frame-only candidates: CD:C288, CE:126A, CE:1303.

## Artifact and validation

- tools/python/audit_vm56_source_ownership.py
- data/maps/transitions/vm56_source_ownership_audit.json
- scripts/test_vm56_source_ownership.py (six synthetic + corpus tests)
- Existing tests and Viewer remain unchanged in graph semantics.

The JSON owner_trace_queue includes validated script_callsite and
selected_source_cpu addresses, as well as destination identifiers. These
are script event selection sites, not independently established source
map coordinates or player-facing actions.

## Next experiment

Start at CC:AD64; trace F81-L007's validated source selections back to
their script event dispatcher, then determine active $0305 map pack,
$035F/$1398 VM mode, caller route and saved map state at the moment the
0x56 is executed. Compare independent map selector configuration evidence;
only when active source context is proven can the source_config_id be bound.
Repeat for CC:3DF1, CC:3FAF and the other prioritized targets.

The hidden dedicated BizHawk lab can capture commands/screens/WRAM without
foreground GUI interaction. A complete village/interior/world runtime round
trip has not yet been recorded in this cycle. Keep all savestates, ROM and
raw captures local-only.

Important: completion remains 51.4%. ROM-opcode validity is not runtime
reachability, and a source selection pointer is not a proven map identity.


## Source selection versus actual VM caller (important refinement)

The seven frame-linked records contain A4-style source-selection instructions
with validated source pointers. This is **not** evidence that those instructions
call opcode 0x56, nor that their pointer target names a player map. Within
F81-L007, CC:AD64 has six selection sites at lower ROM addresses and one
at a higher address. Some other records also contain sites on both sides.
ROM address order does not imply runtime execution order, especially across
branches. The audit now labels each site with before/after address order,
retains its pattern and explicitly sets is_proven_vm_caller=false.

The next actual proof must reconstruct the VM call path plus active global
map pack and mode at the transition handler, rather than assuming a source
selection is a caller.
