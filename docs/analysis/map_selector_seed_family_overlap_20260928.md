# Map selector seed-family overlap — 2026-09-28

## Purpose

Cross-link the current primary map-selector backlog with the independently proven
CA:C2F4 entry-0x79 seed family. This pass uses only committed derived catalogs;
no ROM bytes or raw copyrighted data are added.

## Confirmed catalog join

Inputs:

- `data/maps/selectors/primary_map_selector_catalog.csv`
- `data/maps/selectors/map_pack_entry79_seed_catalog.csv`

Current primary corpus:

- 263 primary 0x50 shapes total
- 137 mode-unresolved
- 118 mode-unresolved rows at record_index 0
- those 118 rows occupy 99 distinct packs

The entry-0x79 seed catalog contains 55 distinct seeded packs.

Joining by canonical pack id gives:

- 39 / 118 unresolved record-0 selector rows are in a pack that also has at
  least one CA:C2F4 entry-0x79 seed
- those 39 rows occupy 33 / 99 unresolved record-0 packs
- therefore 66 / 99 unresolved record-0 packs have no entry-0x79 seed

The 33 overlapping pack ids are:

`0x4C, 0x56, 0x5C, 0x68, 0x6B, 0x6D, 0x6E, 0x82, 0x85, 0x8B, 0x8E,
0x90, 0x91, 0x95, 0x96, 0x98, 0x99, 0x9A, 0x9B, 0xA3, 0xA6, 0xA8, 0xAE,
0xB6, 0xBA, 0xBB, 0xBE, 0xC0, 0xC6, 0xCB, 0xCF, 0xE9, 0xF6`.

## Interpretation

This is a useful negative control for reachability modeling.

The same canonical pack can contain both:

1. the state-0-reachable record0 / entry-0x01 family containing a currently
   unresolved primary map selector; and
2. one or more independently indexed entry-0x79 seed substreams.

Therefore the presence of an entry-0x79 seed cannot be used as a pack-wide mode
label for record0/entry1. The two startup families demonstrably coexist in 33
packs.

Conversely, absence of an entry-0x79 seed in 66 of the 99 unresolved record-0
packs does not prove state-0 persistence either. It only removes that particular
seed family from those packs.

## Confirmed fact vs hypothesis

Confirmed:

- the counts above are exact joins of the current committed catalogs;
- entry-0x79 and record0/entry1 coexist in 33 unresolved-selector packs;
- pack id alone remains insufficient to infer the mode at a later 0x50.

Strong working hypothesis:

- prefix-level mode-persistence analysis remains the highest-information static
  discriminator for the 118 record0 backlog.

Unconfirmed:

- whether any entry-0x79 substream can causally alter $1399 before a particular
  record0/entry1 0x50 executes;
- whether the 33 overlapping packs are disproportionately associated with
  transitions, cutscenes, or other location classes.

## Next

Keep the current priority: decode the normal-mode prefix from each state-0
record0/entry1 seed to its candidate 0x50, stopping conservatively at branch,
wait, unknown, or mode-transition-capable handlers. Use this overlap catalog as
a guard against reintroducing pack-wide mode assumptions.
