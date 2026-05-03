# Two-stage dispatch hypothesis

## Status
Hypothesis from later Run notes, preserved separately to avoid mixing with confirmed facts.

## Proposed flow
```text
script opcode
  -> Table A: opcode to behavior/command id
  -> Table B: command id to routine pointer
  -> native command routine
```

## Why it was proposed
- Many games separate compact script codes from native routines.
- A dense byte table would allow opcode reuse and compression.

## Required proof
To promote this from hypothesis to confirmed:

1. Locate Table A as an actual byte table referenced by code.
2. Locate Table B as an actual pointer table referenced using Table A output.
3. Tie one known script byte to one specific native routine.
