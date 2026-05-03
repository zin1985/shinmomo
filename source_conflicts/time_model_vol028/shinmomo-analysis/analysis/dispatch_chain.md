# Dispatch chain model

## Confirmed historic chain
Older handoffs identify:

- `0x41A10..` as an 8-byte condition table candidate.
- `0x39850 / 0x39993` as target-side blob/macro areas.
- `0x41A10 -> 39850/39993` as a major Goal 8 path.

## Current thread correction
Do not jump directly from `0x39850` row tail to `$0759/$0799` object-slot pointer writes.
No direct writer path was confirmed.

## Current safe chain
```text
0x41A10 table candidate
  -> target-side blob/macro rows at 0x39850/0x39993
  -> row tail words such as F09A/F0DB...
  -> unresolved consumer/evaluator
```

## Next proof
Find the evaluator/reader that consumes the 9-byte rows and uses the tail words.
