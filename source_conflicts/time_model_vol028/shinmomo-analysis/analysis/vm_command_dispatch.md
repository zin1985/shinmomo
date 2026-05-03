# VM command dispatch model

## Status
Speculative layer. The existence of a command table has not been directly proven in the generated files.

## Model
The thread model proposes that a VM opcode or script byte dispatches to higher-level native routines:

```text
script byte / opcode
  -> optional mapping layer
  -> native command routine
  -> object slot update
  -> optional wait/timer update
```

## Evidence level
Medium-low until an actual jump table, pointer table, or indirect JSR/JMP path is located.

## Search signatures
- indirect `JMP (addr)` or `JSR`-like dispatch
- `ASL A` / `TAX` / `LDA table,X` patterns
- dense byte mapping tables near VM reader
- short routines touching `$0619/$0719/$0759/$0799`
