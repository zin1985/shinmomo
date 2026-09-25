# Progress dashboard data

`project_progress.json` is the machine-readable source of truth for project progress.

## Two-layer model

### Top layer: G1..G5

Whole-project completion is the equal mean of the five top-level goals.

A top-level goal only advances when evidence improves its formal Definition of Done. Historical thread-local percentages are never copied directly.

### Lower layer: analysis workstreams

`tracks` retain local reverse-engineering maturity such as ROM map, Script VM, dialogue reader and NPC/OAM.

A workstream can be 95–100% while the project remains far below 100%.

`legacy_workstream_overall_percent` is informational only.

## Evidence classes

Every progress update should identify whether it is:

- **new analysis** completed now;
- **recovered evidence** already present in historical material but missing from current progress;
- **reclassification** correcting the scope or certainty of an older claim.

Confirmed facts, strong hypotheses and unconfirmed items must remain distinguishable.

## Repository policy

Do not store ROM binaries, SRAM, savestates, raw VRAM/OAM/CGRAM or secrets.

Historical nested ZIPs are noncanonical cleanup debt. New analysis should commit expanded text/data/tool outputs.

## Rolling schedule

At the end of each analysis cycle:

1. verify the canonical Drive ROM;
2. read the latest handoff, top goals and contradiction register;
3. consult the reusable asset index before creating a new scan;
4. complete the highest-value target;
5. update affected G1..G5 only when their completion criteria improve;
6. update affected workstream evidence separately;
7. re-rank at least five next schedule entries;
8. commit and allow CI to validate;
9. promote to Drive only after CI succeeds.
