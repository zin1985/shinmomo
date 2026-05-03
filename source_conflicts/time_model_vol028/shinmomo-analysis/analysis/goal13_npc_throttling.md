# Goal 13 core logic model

## Scope of this thread
This thread handles the logic side of Goal 13, not graphics reconstruction.

## Current corrected model
Goal 13 should be investigated through:

```text
active object list
  -> object type/routine
  -> slot field semantics
  -> script/VM-like work frequency
  -> OAM submit / display layer
```

## Important correction from this thread
`$0759/$0799` cannot be interpreted uniformly as a pointer pair. For Goal 13 logs, each object type must be decoded first.

## Candidate throttling mechanisms
- active list inclusion/exclusion
- state/phase gate
- timer/wait gate
- OAM submit skip

## Next concrete target
Connect runtime logs to code around:

- `$0A61` active list
- `C0:B100` / `B294` area
- `$0A1C / $0B27` candidates
- `$87:82C0` caller and object type
