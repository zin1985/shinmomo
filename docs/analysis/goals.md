# Goal progress snapshot 260510Y

## Dynamic-analysis cycle note (2026-09-25)

The canonical ROM was checked from the pinned Drive folder and the Windows analysis copy matched the known SHA-256.
BizHawk/Snes9x executed through the title and into the field, and CPU/WRAM runtime logging is now confirmed working.
Static follow-up placed the $0799,X bit7 routines inside a bank89 script-driven object-state path, so the earlier
"final visibility staging" label is no longer treated as confirmed. Goal13 is reopened at 96% while the direct OAM
link is revalidated; the broader Script VM/Event track advances from this dispatcher mapping.

## Core goals

| Goal | Status | Scheduled-analysis update |
|---|---:|---|
| Goal7 blob runners | 100% | `$83:F09A / F0DB / F0C6` constrained as terminal append-buffer consumers. |
| Goal8 dispatch | 100% | `$0759` dispatch remains append-gated; invisible slots do not execute. |
| Goal9 VM/script | 100% | bank89 object-script dispatch is now directly relevant to the $0799,X path; the older "configuration-only" wording is retired. |
| Goal12 architecture | 100% | one-way VM/config → slot loop → append → dispatch/OAM pipeline stabilized. |
| Goal13 NPC/OAM | revalidation 96% | $0799,X state transitions are real, but their direct visibility/OAM meaning must be proven against the active-list/OAM path. |
| Goal14 slot/state | 100% | contiguous-prefix threshold model stabilized. |

## Extended graphics / validation goals

| Goal | Status | Scheduled-analysis update |
|---|---:|---|
| Goal15 clustering | 100% | fragmentation-resistant cluster persistence validated. |
| Goal16 OAM budget | 95% | budget enforcement still appears emergent via append_count limitation. |
| Goal17 gating | 100% | SKIP/disappearance equivalence stabilized. |
| Goal18 timing | 100% | execution_frame exactness retained under churn. |
| Goal19 dispatch linkage | 97% | CHR grouping and contribution bands align but exact mapping remains open. |
| Goal20 validation | 100% | compression-stable branch-causal datasets preserved. |

## Earlier baseline relation

The March/May Goal13 model remains useful for the active-list/OAM side, but the 2026-09-25 runtime/static cycle showed that the $0799,X path sits inside bank89 script-driven object handling. The next milestone is therefore a cross-layer proof, not another assumption that $0799,X is itself the visibility authority.

