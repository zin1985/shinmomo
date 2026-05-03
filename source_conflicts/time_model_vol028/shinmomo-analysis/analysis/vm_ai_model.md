# NPC / event AI model

## Status
High-level model for the current thread, not confirmed full engine spec.

## Model
NPC/event behavior likely consists of:

```text
object active slot
  -> state/phase
  -> timer/wait
  -> script/behavior pointer or data fragment
  -> routine dispatch
```

The goal is to separate:
- object update
- script/VM-like behavior
- OAM submission/display

Graphics reconstruction remains out of scope for this thread.
