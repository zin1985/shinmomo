# State machine model

## Status
Working hypothesis.

## Candidate slot
`$0619` is treated in this handoff as a state/phase candidate for object routines.

## Important caution
The exact enum values are unknown. The values in `state_values.csv` are placeholders for future runtime labeling.

## Verification
Track `$0619,X` around:

- object initialization routines
- `$87:82C0` reader entry
- action/wait command completion
- object deactivation
