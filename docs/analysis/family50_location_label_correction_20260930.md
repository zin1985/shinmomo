# Family 0x50 location-label correction

Updated: 2026-09-30

## Finding

The family-0x50 dialogue decode was not the source of the apparent regional
mismatch. The incorrect location identity came from an unsupported hard-code
in `tools/python/build_static_map_actor_selector_crosslink.py`:

`family 0x50 -> 旅立ちの村`

That assignment is invalid as canonical identity evidence.

## Why the old label is unsafe

`cfg_t04_l008_v2` is a structural map configuration, not a unique place ID.
The canonical configuration index shows three occurrences:

- pack 0x50
- pack 0xF0
- pack 0xF1

The pack-0x50 runtime sample uniquely binds pack 0x50 to this configuration,
but its own identity record has:

`exact_in_game_place_name = null`

Therefore a place name must not be attached globally to the shared
configuration unless an independent runtime/game-text identity proves it.

## Family 0x50 semantic context

The 19 statically bound family-0x50 dialogue variants repeatedly mention
浦島, 乙姫, 養老の滝, fishing, 寝太郎, and routes toward 希望の都.

Independent walkthrough/location material also associates 浦島の村 with
浦島's absence and 養老の滝 as the village water source. This makes
`浦島の村` a useful **strong candidate** for pack 0x50, but not a confirmed
canonical identity under the project evidence rules.

The candidate is stored separately in:

`data/maps/context/map_location_identity_candidates_20260930.csv`

and must not be promoted without runtime or in-game text identity evidence.

## Corrections

- removed the `0x50 -> 旅立ちの村` generator hard-code;
- cleared `map_label` for current family-0x50 actor rows;
- cleared the stale `旅立ちの村` display name from the t04/l008 render catalog;
- preserved `浦島の村` only as a candidate;
- extended the viewer builder to retain pack/location context on actor entities;
- added a viewer guard so an old generated world file cannot display the stale
  Tabidachi label for this shared configuration.

The dialogue/event/source bindings themselves remain valid.
