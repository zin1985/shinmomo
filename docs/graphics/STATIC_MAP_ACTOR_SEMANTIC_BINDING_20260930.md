# Static map actor semantic binding — 2026-09-30

## Purpose

This layer adds semantic evidence on top of the proven static map -> display-selector
crosslink without collapsing visual appearance and gameplay role into one guess.

The evidence chain is:

```
map/config
 -> event record
 -> opcode 0x59 actor/controller placement
 -> selector id
 -> static reconstructed sprite
 -> visual-form evidence
 -> dialogue/source evidence
 -> role candidate
```

Roles in this file are **candidates**, unless independently proven elsewhere.
In particular, a monster-looking sprite is not automatically called an enemy.

## Visual-form layer

The 41 selectors currently bound to maps through opcode 0x59 were manually classified
from the ROM-reconstructed static sprite atlas into conservative visual forms:

- humanoid_like
- animal_like
- monster_like
- small_creature_like
- object_like
- plant_or_effect_like

The visual classification is stored separately in:

`data/npc_display/static_map_bound_selector_visual_form_20260930.csv`

This separation is intentional: appearance is evidence about form, not allegiance or
story role.

## Dialogue layer

`tools/python/build_static_map_actor_dialogue_crosslink.py` joins:

- static map actor records
- `event_source_crosslink.csv`
- `historical_decode_crosswalk.csv`
- canonical historical decoded dialogue CSVs under `data/csv/`

Current coverage for the 327 map-context actor rows:

- 327 total crosslink rows
- 292 rows have at least one statically selected source but no historical decoded text
  currently joined
- 8 rows have historically decoded Japanese dialogue
- 27 rows have no source link in the existing event-source crosslink
- 7 distinct selectors currently have at least one decoded-dialogue actor record

The small decoded-dialogue count is a coverage limit of the historical text corpus, not
evidence that the other actors are silent.

Selectors with currently decoded dialogue evidence:

- 0x24
- 0x25
- 0x27
- 0x40
- 0x59
- 0x5A
- 0x5B

For a humanoid-looking selector, decoded dialogue promotes the record to
`dialogue_npc_candidate`.

## Pack 0x50 / 旅立ちの村 examples

The static record-to-selector binding is already runtime-validated 9/9 for pack 0x50.

Examples now connected further into decoded text:

- F50-L002 / selector 0x24:
  dialogue discusses Ginji handling four kitchen knives and Urashima being called away.
- F50-L003 / selector 0x59:
  dialogue addresses Urashima and Momotaro and mentions Otohime.

The exact Japanese text is preserved in
`static_map_actor_dialogue_crosslink_20260930.csv`.
These records are therefore strong conversation-NPC candidates.

## Current role candidates

Across the 41 map-bound selectors:

### Animal-like actor candidates

| selector | visual form | mapped configs / packs |
| --- | --- | --- |
| 0x17 | white cat-like | cfg_t33_l146_v1 / pack 0x48 |
| 0x39 | white rabbit-like | cfg_t53_l184_v2 / packs 0xD0,0xD5,0xD7,0xD8 |
| 0x3A | gray rabbit-like | cfg_t08_l094_v2 / 0x53; cfg_t08_l092_v2 / 0x92,0x93 |
| 0x49 | snail-like | cfg_t55_l192_v2 / 0xE0; cfg_t07_l009_v2 / 0xF9 |

These are called animal candidates from visual evidence plus exact static map binding.
Whether any are battle enemies, neutral animals, event actors, or transformations remains a
separate behavioral question.

### Monster / enemy-role candidates

| selector | visual form | mapped configs / packs |
| --- | --- | --- |
| 0x0E | yellow humanoid creature | cfg_t04_l062_v2 / 0x8C |
| 0x0F | small black-white creature | cfg_t45_l168_v2 / 0x88 |
| 0x53 | red-orange monster-like | cfg_t29_l138_v2 / 0xB5 |
| 0x54 | gray-black monster-like | cfg_t08_l094_v2 / 0x53 |
| 0x56 | green monster-like | cfg_t15_l107_v2 / 0xC1; cfg_t17_l111_v2 / 0xC4 |
| 0x6F | green-yellow monster-like | cfg_t16_l109_v2 / 0xC2 |

These remain `monster_or_enemy_actor_candidate`; enemy allegiance is not yet proven.

### Object / effect candidates

- selector 0x5C: cabinet/shrine-box-like object
  - cfg_t07_l009_v2 / pack 0xF9
- selector 0x11: purple plant/flower/effect-like form
  - cfg_t45_l168_v2 / packs 0x88 and 0x89

### Humanoid map actors

28 selectors in the current map-bound subset have humanoid visual form.
Seven of those currently have decoded-dialogue evidence and are promoted to
`dialogue_npc_candidate`. The rest remain `humanoid_map_actor_candidate` until dialogue,
behavior, shop/event, enemy, or party evidence resolves their role.

## Graphics aliases matter

Several distinct selectors share the same reconstructed graphics while remaining different
event/controller identities. Examples:

- 0x59 -> graphics of 0x3F
- 0x3E -> graphics of 0x24
- 0x5A -> graphics of 0x15
- 0x22 -> graphics of 0x16
- 0x2F -> graphics of 0x1C
- 0x30 -> graphics of 0x1D
- 0x3D -> graphics of 0x23

The map-bound atlas now resolves these aliases to their canonical image instead of showing
blank cells. This is why semantic identity must be keyed by selector, not only by sprite art.

## Outputs

- `data/npc_display/static_map_actor_dialogue_crosslink_20260930.csv`
- `data/npc_display/static_map_actor_dialogue_summary_20260930.json`
- `data/npc_display/static_map_bound_selector_visual_form_20260930.csv`
- `data/npc_display/static_map_actor_semantic_candidates_20260930.csv`
- `data/npc_display/static_map_actor_semantic_candidates_summary_20260930.json`
- updated `static_map_bound_selector_summary_20260930.csv`
- updated alias-aware atlas:
  `graphics/static_character_reconstruction/static_map_bound_selector_atlas_20260930.png`
- generators:
  - `tools/python/build_static_map_actor_dialogue_crosslink.py`
  - `tools/python/build_static_map_actor_semantic_candidates.py`
  - `tools/python/build_static_map_bound_selector_summary.py`

## Next static steps

1. Expand opcode-0x59 parsing beyond records whose first body instruction is 0x59,
   using the already-proven bank84 VM instruction grammar.
2. Join selector records to controller behavior keys/pointers and classify behavior:
   stationary talker, wandering NPC, animal movement, scripted monster, prop/effect.
3. Resolve human-readable place names for the remaining config ids from independent map-name
   evidence rather than dialogue guesses.
4. Merge the separate logical-actor path ($1569 IDs) and special 9-byte object-preset path
   into the same selector-centric actor catalog.

## Promoted actor semantic output

The later actor-bound dialogue CFG work closes all ten opcode-0x59 actors in the
旅立ちの村 pack/config at speaker-record level. F50-L001 and F50-L010 are no
longer left semantically unknown: both have direct actor-bound decoded dialogue,
and all F50-L001..L010 are now conservatively promoted to `villager` with high
confidence.

This promotion proves that they are speaking village NPC actors. It does not
infer an occupation or named identity from dialogue wording alone.

Across the full 817-row static opcode-0x59 actor corpus, the generated semantic
layer now has:

- 10 high-confidence `villager` rows (旅立ちの村 F50-L001..L010)
- 1 `talking_npc` strong candidate outside pack 0x50 (F4F-L001 / selector 0x3C)
- 47 high-confidence `animal` rows
- 6 `effect` candidates from object/plant-effect visual classes
- 23 monster/small-creature rows retained as `unknown` candidates because enemy allegiance is not proven
- 730 rows remaining fully unknown

The generated per-actor output is
`data/npc_display/static_actor_sprite_semantics_20260930.csv`.

The HTML viewer loads `viewer/data/actor_semantics.json` as a small semantic
override layer. This lets semantic-only improvements reach the viewer without
rewriting the multi-megabyte `world.json` every time. The canonical build
pipeline can still regenerate embedded `sprite_semantics` through
`tools/python/build_structural_world_viewer.py`.

### Full-corpus visual join correction

The first promoted semantic pass joined through the older 327-row semantic-candidate
table. That missed tail-opcode59 actors even when their selector already had a visual-form
classification. The current generator instead joins all 817 actor rows to the
selector-level visual-form table directly.

This recovers, for example, F4F-L001 / selector 0x3C as a yellow-clad humanoid
and preserves its actor-bound decoded dialogue as a generic `talking_npc` strong
candidate. The dialogue proves a speaking actor association, but does not prove a
specific profession or named identity.
