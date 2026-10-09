# VM 0x56 substream CFG frontier (2026-10-10)

## Scope

Continue from `825c014087fbf9bd60b877f5f731cad0c2d6a65c`.
Canonical ROM (local-only): 2,097,152 bytes; SHA-256
`F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`.

The prior VM56 audit confirmed all **722 / 722** terminal
`56 <destination pack> <entry> B0` byte patterns, but did NOT establish a
source-map config for 721 of them. Only ten of the terminal instructions
overlap structurally framed event records, and seven of those records
carry independently validated A4 source-selection crosslinks. This pass
focuses on those ten framed entries.

## Method

`tools/python/audit_vm56_entry_cfg.py` parses the **real canonical ROM**
using `catalog_map_selectors.py`'s pack, record and entry grammar.
For each of the ten targets, it requires one exact parsed substream
containing the 0x56 tail; then it reuses the **same proven CFG functions
and safe instruction-length table** already implemented as nested
functions in `catalog_map_transition_candidates.py`.

For now the tool extracts those functions from the trusted source file
AST instead of duplicating and gradually diverging from the original
decoder. Any missing expected functions or changed AST initialization
shape makes the analyzer abort. It does not inspect or modify the
interactive emulator or commit ROM/script bytes.

The CFG is a **possible static path** search with conservative
blocking for unknown opcodes/callees, not a full state-constrained
gameplay trace. `A0` callsite return proof and `B1/B2/B3/B4` control
flow follow existing proven grammar. A reachable VM instruction is not
equivalent to a proven transition in normal VM mode or proven map source.

## Results

| Trigger | Parsed substream [start,end) | CFG possible path | Blockers |
| --- | --- | --- | --- |
| CC:AD64 | CC:AC74..CC:AD68 | yes | none (normal VM 0x6E verified) |
| CC:3DF1 | CC:3DAE..CC:3DF5 | yes | none |
| CC:3FAF | CC:3F18..CC:3FB3 | yes | none |
| CC:B67B | CC:B5FC..CC:B67F | yes | none |
| CC:F4F9 | CC:F413..CC:F4FD | no proof | op:25 |
| CC:4A21 | CC:4A02..CC:4A25 | yes | none |
| CC:848E | CC:8421..CC:8492 | no proof | op:39, op:40 |
| CD:C288 | CD:C25B..CD:C28C | yes | none |
| CE:126A | CE:1264..CE:126E | yes | none |
| CE:1303 | CE:12FB..CE:1307 | yes | none (normal VM opcode 0x02 operand 0x13 verified) |

Results: 10/10 exact substream bounds and terminal signatures,
**8 statically reachable under current proven grammar** and **2 blocked**.
These are not runtime-confirmed edge counts.

**Crucial disambiguation:** for all ten records, **zero** validated
A4 selected-source callsites fall *inside* the parsed VM substream
containing the terminal 0x56. For CC:AD64 specifically, its seven
validated A4 selection sites have 6 locations **before the substream**
(start CC:AC74) and 1 **after its end** (CC:AD68).
They share a framed event record, not an established direct VM caller.
ROM address order does not imply execution order.

### CC:AD64 nested caller targets now bounded

The three unresolved A0 callee addresses are each **unique parsed
entry identities** in the canonical ROM:

| A0 callee | Exact bounded entry [start,end) | Pack, record, entry |
| --- | --- | --- |
| CA:DA86 | CA:DA86..CA:DA93 | pack 0x14, record 16, entry 0x6C |
| CA:DA93 | CA:DA93..CA:DAAC | pack 0x14, record 16, entry 0x6D |
| CC:AE86 | CC:AE86..CC:AE9C | pack 0x81, record 19, entry 0x6C |

The canonical VM 0x6E handler proof now gives a two-byte instruction
in normal mode. Re-running the existing bounded CFG decoder resolves the
CC:AD64 target and independently verifies a returning static path for all
three A0 callees. The analysis records callee_return_proven=true and no
remaining blockers. This does not prove an actual runtime visit to the
caller, the VM mode or an active player map.

No candidate source map was promoted and no Viewer graph edge was
added. The project overall score remains 51.4%.

## Reproduction

```powershell
$rom = "$env:USERPROFILE\Downloads\Shin Momotarou Densetsu (J)\Shin Momotarou Densetsu (J)_original.smc"
py -3 tools/python/audit_vm56_entry_cfg.py --rom "$rom"
py -3 scripts/test_vm56_entry_cfg.py
```

Generated metadata:
`data/maps/transitions/vm56_entry_cfg_frontier.json`.

## Normal VM 0x6E proof and next task

The canonical ROM table C4:87D4 indexes opcode 0x6E to C4:93A9
(independently agreeing with known opcode 0x53 and 0x56 anchors). Both
handler branch paths join at C4:93D5 and jump to C4:895E, which loads
the VM pointer advance of 2 and jumps to C4:8410. The signature proof
validates the table, branch forms and common pointer advance. It
remains normal-VM-mode-specific.

Independent verifier: tools/python/verify_vm_opcode6e_handler.py
Generated proof: data/maps/transitions/vm_opcode6e_handler_proof.json
Mutation regression: scripts/test_vm_opcode6e_handler.py

The complete canonical transition catalog was rebuilt in a temporary
location after adding opcode 0x6E:2 to the shared CFG grammar. The
1,295-row regenerated catalog is byte-for-byte identical to the current
committed CSV.

Next investigate actual VM owner/caller, runtime $0305 map pack,
$035F/$1398 mode, story flags and saved-map state for the seven
statically reachable VM56 targets (including CC:AD64).
A second concrete normal-VM dispatch was independently verified:
opcode 0x02 with operand 0x13 uses C4:89A5 and
C4:9BEE[3*(0x13-1)] -> 83:BBAB. The mirrored ROM target
has a concrete RTL after JSL 80:AC14. The normal 0x02 handler
advances two bytes at C4:895E before the indirect call.
This enables the CE:1303 static CFG path, while still not proving
runtime mode, return of the nested external JSL, story conditions
or the current map.

Verifier: tools/python/verify_vm_opcode02_13_handler.py
Evidence: data/maps/transitions/vm_opcode02_13_proof.json
Regression: scripts/test_vm_opcode02_13_handler.py

The transition catalog was regenerated in an isolated temporary
directory and the canonical 1,295-row CSV remains byte-for-byte
identical after adding only this proven operand to the CFG grammar.

The two remaining CFG blockers are CC:F4F9 (normal opcode 0x25
handler C4:9517) and CC:848E (0x39 handler C4:9803 and
0x40 handler C4:8FB3). Neither is promoted to an invented
constant length: inspect scheduler, pointer update, conditional
paths and mode behavior before further CFG expansion.

Then perform an isolated hidden BizHawk runtime traversal test.

Safety: Never commit raw ROM bytes, captures, or savestates; never infer
current map from script pack, source-selection pointers, or mere static
reachability.
