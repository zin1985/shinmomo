# VM branching model

## Status
Partly inferred.

## Candidate branch behavior
Branching may occur at multiple levels:

1. External condition table: `0x41A10` records select target-side blobs.
2. Macro row selection: `0x39850 / 0x39993` rows select label words.
3. VM/script internal branch: byte stream changes local PC/offset.
4. Native command branch: command routine checks state/flags.
5. State transition: object enters/leaves script mode.

## Next proof target
Find the code that consumes the 9-byte macro row tail word and determine whether it changes script pointer, branch label, or dispatch target.
