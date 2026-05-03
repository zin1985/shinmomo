# VM scheduler model

## Status
Working hypothesis derived from object-slot behavior and `$0799` reuse.

## Scheduler hypothesis
For VM-like objects only:

```text
if object inactive:
    skip
if wait_counter > 0:
    wait_counter--
    skip VM step
else:
    execute one VM/action step
```

## Slot assumptions
- `$0619`: state / phase candidate
- `$0799`: wait/timer candidate in script-like objects, but not globally fixed
- `$0759/$0799`: pointer pair only for specific reader path

## Caution
The `$0799 = wait` interpretation is not globally valid. It must be tagged by object routine/object type.
