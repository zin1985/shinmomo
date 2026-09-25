# Goal13 / NPC-object-OAM canonical model

Updated: 2026-09-25 after runtime/static revalidation.

The old 260510Y model that treated `$0799` as a canonical global visibility staging field is superseded.

## Confirmed architecture

There are multiple layers that must remain separate:

```text
event/script/logical actor
        ↓
controller/work object slots
  $0619..$0A18, handler-dependent overlays
        ↓ explicit handle creation/storage in some handlers
visible-object pool
  C0:AF33 create/sorted insert
  C0:AFAA remove
  C0:AFEC re-sort
  physical node = external handle + 2
        ↓
$0A61 active list / $0AA3 sort key
        ↓
C0:B03D active-list walk
        ↓
C0:B100 object → sprite pieces
        ↓
$0EE9 OAM mirror
        ↓
C0:B0C7 OAM transfer
```

## $0799 status

Confirmed:

- `$0799,X` is an indexed controller/object-slot field.
- bank89 contains read/write/DEC and bit7 set/consume sequences for it.
- `89:BAC8` performs `LDA $0799,X / ORA #$80 / STA $0799,X`.
- `89:BA70` tests bit7 and normalizes the value.
- the path is inside script-driven object processing.

Not confirmed:

- that `$0799` has one global semantic across all handlers;
- that bit7 directly means final visibility;
- that this field is itself the OAM/active-list authority.

Use handler-qualified labels until an explicit controller → visible-object → OAM correlation is proven.

## $0759/$0799 historical correction

Bank87 evidence already showed these columns can behave differently by routine/object type, including pointer/state/position-like overlays.

Therefore:

```text
WRONG: $0759/$0799 = universal pointer pair
WRONG: $0799 = universal wait counter
WRONG: $0799 = universal visibility field

RIGHT: handler-dependent controller/work fields; assign semantics per routine/object type.
```

## Stable visible-object facts

- `$0A61[slot]`: next node in active list
- `$0A1F[slot]`: previous node
- `$0AA3[slot]`: sort/depth key
- external visible-object handle maps to physical node with `physical = external + 2`
- nodes 0/1 are structural/sentinel space in the current model
- C1 object-management callers demonstrate explicit bridges from logical/controller work to visible objects

## Animation/render facts

```text
$0B27 lower nibble
→ C0:B2C1 animation group
→ group-specific state pointer table
→ [frame, duration] script
→ $0AE7 current frame
→ B294 sprite frame definition
→ OAM pieces
```

`$0E27` is a group-dependent animation state number. State 0 disables animation/frame output; other state labels must be assigned per group.

## Remaining Goal13 work

The highest-value unresolved proof is not another global `$0799` label.

It is:

```text
one controller/work object
→ explicit visible-object external handle
→ physical handle+2
→ active-list node
→ B03D/B100 render
→ same-frame OAM pieces
```

A successful end-to-end correlation will close the most important remaining cross-layer ambiguity.

## Historical references

The 260510Y threshold/append model remains historical evidence only. Any claim copied from it must be checked against:

- `docs/handoff/HM_260925_goal13_runtime_revalidation.md`
- `docs/reports/bank87_object_slot_0759_0799_reclassification_20260503.md`
- `docs/analysis/wram_object_pool.md`
- `data/audit/contradiction_register_20260925.csv`
