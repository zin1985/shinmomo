# Opcode inference strategy

## Goal
Infer script/VM opcode meaning without needing the full command table first.

## Runtime probing idea
For each opcode-like byte candidate:

1. Run or patch a controlled object/script.
2. Observe slot deltas.
3. Categorize behavior by effects.

## Observation fields
- coordinate delta
- facing/direction delta
- state/phase change
- wait/timer change
- text/display trigger
- branch/pointer change
- OAM visible count change

## Output
`opcode_behavior_inference.csv`
