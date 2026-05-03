# Unresolved targets

## Highest priority
1. Find the actual evaluator for `0x39850 / 0x39993` 9-byte rows.
2. Find callers into `$87:82C0` and identify object types using the pointer reader path.
3. Determine whether `F09A/F0DB/F0C6/F0CD/F0D4` are VM entries, branch labels, data labels, or native/data-mixed blob labels.
4. Tie `$0A61` active object list to object routine dispatch and OAM submission.
5. Label `$0619` state values using runtime traces.

## Caution targets
- Do not treat all `$0759/$0799` as script pointer.
- Do not treat late Run Table A / command table model as confirmed until real references are located.
