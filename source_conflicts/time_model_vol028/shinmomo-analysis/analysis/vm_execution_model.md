# VM execution model / Run17 supplemental handoff

## Status
Working model, not a fully verified final spec. This file exists to preserve the Run17 thread model as a separate artifact.

## Core model
The current thread model separates two layers:

1. Static/resource layer
   - `0x41A10` 8-byte condition table candidates
   - `0x39850 / 0x39993` 9-byte macro rows
   - row tail words such as `F09A / F0DB / F0C6 / F0CD / F0D4`

2. Runtime/object layer
   - active object iteration
   - object slot fields such as `$0619`, `$0719`, `$0759`, `$0799`
   - VM-like reader candidate at `$87:82C0..83C7`

## Important correction
`$0759/$0799` must not be treated as a universal pointer pair. It is an object-type-dependent generic slot field.
Known usages observed in this thread:

- pointer low/high, only in VM-like object reader cases
- state/timer or phase flag
- long/script pointer component
- position/velocity/fixed-point component
- save/restore slot field

## Current highest-value next step
Do not assume the VM model is complete. The next concrete task is to find callers and actual object types that enter `$87:82C0`.
