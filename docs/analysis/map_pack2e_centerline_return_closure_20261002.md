# Pack 0x2E centerline native-return closure

Updated: 2026-10-02

## Purpose

Close one conservative map-transition witness through the south boundary of
`cfg_t07_l015_v2` without guessing which X coordinate was used by the
historical runtime reverse transition.

The witness is:

```text
village source hotspot (29,17)
  -> CC:1CDA / opcode 0x53
  -> pack 0x2E entry 0x02
  -> static arrival (9,12)
  -> Down attempts (9,13)
  -> native Y bound 0..12 is exceeded
  -> C1:8955 / 81:895A native transition request
  -> C1:97BC / 81:8244 saved-state restore
  -> saved village state (29,17)
```

The reverse relation `cfg_t07_l015_v2 -> cfg_t04_l008_v2` is independently
confirmed by runtime evidence. The exact pre-exit X used in that historical
runtime sample was not captured.

## Static centerline witness

The pack-0x2E primary setup has:

- selector: `CB:DE70`
- native bounds opcode: `CB:DE74`
- X bounds: `0..19`
- Y bounds: `0..12`

The forward village transition `CC:1CDA` selects pack `0x2E`, entry
`0x02`. The destination entry has an aligned opcode-0x58 coordinate setter at
`CB:DE7C` and sets both coordinate pairs to `(9,12)`.

The decoded structural layer `t07/l015` has the south opening at
`x=8..10,y=12`, with metatile IDs:

- `(8,12) -> 68`
- `(9,12) -> 69`
- `(10,12) -> 69`

Therefore the statically selected arrival `(9,12)` is the center cell of the
same opening.

A south step from this witness produces attempted coordinate `(9,13)`.
X remains inside `0..19`; Y alone exceeds `maxY=12`. This makes the native
out-of-bounds branch deterministic for the centerline witness.

## Native return chain

The already-proven native chain is:

```text
C1:8943
  -> 81:81DD inclusive bounds check
  -> C1:8955 on out-of-bounds
  -> 81:895A transition request / $13B8 clear
  -> C1:97BC..C1:97C5
  -> 81:8244 indexed saved-state restore
  -> C1:8255 saved pack -> $0305
```

The saved state associated with `CC:1CDA` is exact because its village source
hotspot is one cell. It restores:

- config: `cfg_t04_l008_v2`
- pack: `0x50`
- coordinate: `(29,17)`

## Runtime relation

`data/maps/transitions/stable_interior_to_pack50_shrine_exterior_20260928.json`
independently confirms:

```text
cfg_t07_l015_v2 / pack 0x2E
  -> walk south through central exit
  -> cfg_t04_l008_v2 / pack 0x50
```

The runtime trace also shows `$0305` switching to `0x50` before the old
selector identity has fully converged, followed by the clear/load phase and
the new `50 04 08 02` selector.

This is consistent with native saved-return behavior rather than an unresolved
direct VM transition in pack `0x2E`.

## Evidence boundary

Closed:

- pack-0x2E source configuration and native bounds
- centerline entry witness `(9,12)`
- attempted south coordinate `(9,13)`
- Y-only out-of-bounds result for that witness
- native request / restore mechanism
- exact saved destination `(29,17)`
- reverse config/pack relation by runtime observation

Still unresolved:

- the exact X used by the historical reverse runtime sample
- whether all three opening cells `x=8..10` are collision-passable
- the exact runtime execution PC of the historical reverse sample
- the historical runtime return X/Y, which was not captured directly

Do not promote the three-cell source corridor to a one-cell runtime hotspot
until one of those missing runtime facts is captured.

## Machine-readable output

- `data/maps/transitions/pack2e_centerline_return_closure_20261002.json`
- generator:
  `tools/python/build_pack2e_centerline_return_closure.py`