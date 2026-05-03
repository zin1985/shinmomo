# VM time slicing model

## Purpose
Preserve the Run17 model that NPC/event objects likely avoid doing expensive work every frame.

## Proposed model
Script-like NPC/event objects are time-sliced:

```text
frame N:   NPC A executes, NPC B waits, NPC C waits
frame N+1: NPC A waits, NPC B executes, NPC C waits
frame N+2: NPC A waits, NPC B waits, NPC C executes
```

## Why this matters for Goal 13
If true, NPC load reduction can be modeled as reduced action/command execution frequency, not just OAM culling.

## Verification target
Need runtime logs tying:

- active object list
- object routine id/type
- `$0799` changes
- OAM submission count
- VM reader calls
