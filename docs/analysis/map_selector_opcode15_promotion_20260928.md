# Opcode 0x15 terminal-prefix promotion

Updated: 2026-09-28

## Result

One additional record0/entry1 selector is promoted after bounding normal
opcode 0x15.

Target:

- pack 0x53
- primary command: CC:23D9
- primary configuration: tileset 8 / layout 94 / variant 2
- immediate secondary: CC:23DD, tileset 8 / layout 95

The state-0 prefix is:

```
96 04
10 0C
10 0D
11 0A
15 00 03
50 08 5E 02
51 08 5F
```

## Opcode 0x15

Normal handler C4:8AE0 consumes two operands:

```
15 <object_mode> <spawn_arg>
```

Handler behavior:

```
operand1 -> $1134
operand2 -> JSL $80:BAB8
advance 3 bytes
```

For this row:

```
$1134 = 0
BAB8 argument = 3
```

## Mode-safety

The synchronous path:

```
C4:8AE0
 -> 80:BAB8
 -> 80:AC1E
```

contains no direct:

- write to $1398;
- write to $1399;
- re-entry to C0:C9E7.

BAB8 registers callback BAF0 and stores $1134 into its slot state. That callback
can later change $035F. Therefore opcode 0x15 is **not** added as a generally
safe prefix opcode.

It is admitted only under the narrow condition:

```
opcode 0x15 is the final instruction immediately before candidate 0x50
```

That condition holds for CC:23D9, so no later 0x10/0x33 descriptor lookup can
observe an asynchronously changed $035F before this selector.

## Updated counts

- primary shapes: 263
- confirmed normal primary: **182**
- unresolved primary: **81**
- confirmed normal immediate secondary pairs: **85**
- unresolved immediate secondary pairs: **20**
- standalone mode-ambiguous secondary shapes: 79

## Reproduction

The rule is encoded in:

- `tools/python/catalog_map_selectors.py`

and appears in:

- `data/maps/selectors/state0_safe_prefix_promotions.csv`
- `data/maps/selectors/primary_map_selector_catalog.csv`
- `data/maps/selectors/secondary_map_selector_candidates.csv`
- `data/maps/selectors/primary_map_selector_summary.json`

The generator fails closed if the opcode-0x15 handler anchor changes.
