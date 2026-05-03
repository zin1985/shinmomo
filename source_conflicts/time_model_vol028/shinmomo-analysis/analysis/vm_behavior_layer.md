# Behavior layer model

## Status
Working classification layer.

## Proposed behavior categories
- `IDLE`
- `MOVE`
- `TURN`
- `WAIT`
- `TALK`
- `EVENT`
- `STATE_CHANGE`
- `BRANCH`

These are analysis categories, not confirmed in-ROM enum names.

## Use
This layer is meant for reverse-compiling unknown opcodes into readable behavior classes before exact command names are known.
