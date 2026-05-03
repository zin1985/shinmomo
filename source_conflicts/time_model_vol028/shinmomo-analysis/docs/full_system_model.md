# Full system model / current thread working view

```text
ROM resource side:
  0x41A10 condition table candidate
    -> 0x39850 / 0x39993 9-byte macro row areas
    -> row tail label words F09A/F0DB/F0C6/...
    -> unresolved evaluator/reader

Runtime object side:
  active object list
    -> object type/routine
    -> object slots 0619..07D9
    -> VM-like reader only for selected object types
    -> display/OAM side handled by graphics thread
```

## Split with graphics thread
This thread owns script/VM/event/NPC behavior pointer/core logic.
The other thread owns graphics/mapchip/OAM/VRAM/DMA reconstruction and visual output.
