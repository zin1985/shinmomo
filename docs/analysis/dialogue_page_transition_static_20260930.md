# Dialogue page transition and input-gate static analysis

Updated: 2026-09-30

## Three-line transition invariant

The 19 canonical family-0x50 dialogue records contain 36 recovered display pages and 17 page-to-page transitions. Every transition satisfies:

`(page line count - 1) + padding 0x01 tokens before the next page = 3`

Mismatch count: 0.

This makes the three-line 0x01 cadence the stronger page-control evidence. The `0x7D/0x7E` tokens remain literal Japanese quote glyphs. Quote blocks align with presentation pages but are not themselves page-control commands.

## Input-sensitive display state

Static ROM evidence narrows the wait/advance side:

- C4:A00D distinguishes current display token `$12B2 == 0x01`.
- `$12AD & 7` selects a display-state handler table at C4:A214.
- State handler C4:A264 reads normalized held-input DP `$57`, primarily masked by `0xFC` and gated by `$12C0`; another path uses `0xF4`.
- C4:9FEB initializes `$12C0 = 0xFF`.
- C0:AAC3 reads `$4218..$421B`; downstream input work separates held state (`$57/$59`) from new-press edges (`$5B/$5D`).

The strongest current interpretation is that exhaustion of the three-line cadence enters an input-sensitive display state. Exact accepted human button names and release/autorepeat behavior are not yet closed, so the HTML model must not label this as A-button-only.

## Outputs

- `data/dialogue/family50_page_transition_invariants_20260930.csv`
- `data/dialogue/family50_page_transition_summary_20260930.json`
- `tools/python/catalog_family50_page_transitions.py`
- `data/npc_display/static_actor_dialogue_sequences_20260930.json`
- `data/npc_display/static_actor_dialogue_sequence_pages_20260930.csv`

## Normalized button mapping

The SNES standard-pad auto-read layout is `JOY1L=$4218: AXLR0000` and `JOY1H=$4219: BY Select Start Up Down Left Right`.
The game's C0 input normalization keeps `$4218 & 0xF0` and ORs `($4219 >> 4)` into DP `$57`, so `$57` is:

- bit7 A
- bit6 X
- bit5 L
- bit4 R
- bit3 B
- bit2 Y
- bit1 Select
- bit0 Start

DP `$59` separately holds the D-pad nibble.

Therefore C4:A264 primary mask `0xFC` corresponds to A/X/L/R/B/Y, while secondary mask `0xF4` corresponds to A/X/L/R/Y. This closes the mask-to-button mapping. It does not yet prove that every one of those buttons advances in every substate, nor does it close release/autorepeat semantics.

Hardware reference: https://snes.nesdev.org/wiki/Standard_controller
