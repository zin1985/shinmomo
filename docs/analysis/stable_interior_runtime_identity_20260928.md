# Stable interior runtime identity

Updated: 2026-09-28

## Result

The existing stable interior sample at frame 3253 is now bound to one exact
script occurrence, not only to a tileset/layout configuration.

Runtime-derived scalar state:

- current pack $0305 = 0x2E
- VM pack $126E = 0x2E
- resolved pack $12B4 = 0x2E
- current mode $1398 = 0
- pending mode $1399 = 0
- previous mode $139A = 5
- map variant $139B = 2
- primary tileset $139C = 7
- secondary tileset $139D = 0
- primary layout $139E = 15
- secondary layout $139F = 0
The selector tuple therefore remains:

`50 07 0F 02`

The confirmed primary corpus contains three occurrences of this configuration:

- pack 0x2E: CB:DE70
- pack 0x69: CC:5391
- pack 0xF7: CE:0F2B

Runtime pack identity 0x2E reduces those three candidates to exactly one:

**pack 0x2E / record 0 / entry 0x01 / CB:DE70**

The reusable resolver is:

`tools/python/resolve_map_runtime_identity.py`

Its derived output is:

`data/maps/samples/stable_interior_runtime_resolution.json`
## Evidence policy

The WRAM reads used to establish the scalar values remain local-only.

Git contains only:

- capture IDs;
- SHA-256 hashes of the local evidence files;
- the small scalar map-state values;
- the derived selector-corpus join.

Canonical derived evidence:

`data/maps/samples/stable_interior_runtime_identity.json`

No raw WRAM, screenshot, VRAM, CGRAM or OAM payload from this probe is added to
the repository.
## Location semantics

This scene is structurally classified as an indoor map and was visually
described in the playlog as a shrine-like/save-point vicinity.

The exact in-game place name is still not independently proven.

Pack 0x2E's current dialogue-source family does not provide useful place-name
text: its known selected source rows are effectively empty/minimal. Therefore
no human-facing display_name is assigned from dialogue inference.

The runtime identity result should be used as the anchor for later warp/event
or playlog evidence that can establish the actual place name.
## Remote-lab note

The active BizHawk session was still running the previous Lua bridge when the
identity probe was taken, so its map-capture manifest remained schema version 1.

The committed bridge now implements schema version 2 with the same scalar
map-state fields embedded directly in each future map-capture manifest.
That implementation still requires a fresh bridge reload/runtime validation.

Until then, the frame-3253 identity above is independently reproducible from
the local bounded WRAM scalar captures and the committed resolver.
