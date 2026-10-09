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
| CC:AD64 | CC:AC74..CC:AD68 | no proof | A0:CA:DA86, A0:CA:DA93, A0:CC:AE86, op:6E |
| CC:3DF1 | CC:3DAE..CC:3DF5 | yes | none |
| CC:3FAF | CC:3F18..CC:3FB3 | yes | none |
| CC:B67B | CC:B5FC..CC:B67F | yes | none |
| CC:F4F9 | CC:F413..CC:F4FD | no proof | op:25 |
| CC:4A21 | CC:4A02..CC:4A25 | yes | none |
| CC:848E | CC:8421..CC:8492 | no proof | op:39, op:40 |
| CD:C288 | CD:C25B..CD:C28C | yes | none |
| CE:126A | CE:1264..CE:126E | yes | none |
| CE:1303 | CE:12FB..CE:1307 | no proof | op:02 |

Results: 10/10 exact substream bounds and terminal signatures,
**6 statically reachable under current proven grammar** and **4 blocked**.
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

This narrows the next decoder task considerably, but their **return
behavior is still unproven**, so these links remain blockers in the
reachability audit. The analyzer explicitly records
\`callee_return_proven=false\`.

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

## Next precise task

1. Decode opcode `0x6E` with original C4 normal-VM dispatcher and verify
   *actual* handler length and return behavior, not by a guessed byte shape.
2. Inspect nested callees `CA:DA86`, `CA:DA93` and `CC:AE86` for
   bounded entry identity and return proof. They currently block the
   CC:AD64 entry proof.
3. For all six static-path targets, independently trace the **actual
   VM caller/entry event** and active `$0305` map pack, `$035F/$1398`
   VM mode and saved-map context. Bind a source map only when active
   map configuration is independently proven.
4. Complete local hidden BizHawk world/village/interior return-path
   capture; current static audit is not a runtime round-trip test.

Safety: Never commit raw ROM bytes, captures, or savestates; never infer
current map from script pack, source-selection pointers, or mere static
reachability.
