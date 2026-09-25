# WRAM object slot SoA pool

> **Historical-map reconciliation (2026-09-25):** later review of the 2026-05-03 bank87 reclassification shows that `$0759/$0799` are handler-dependent overlay columns. In some bank87 routines they form pointer/state/position-like work; in bank89 `$0799 bit7` is a transient object-script latch. Do not give these columns one universal semantic name.
>
> The `$0619..$09D9` 64-slot SoA is also **not automatically identical** to the visible-object active-list pool. Historical `AF33` caller analysis shows some handlers storing an allocated visible-object handle into `$0619,X`, which indicates a controller/work slot can reference a separate visible object. The visible-object list uses physical nodes 2..65 plus sentinels 0/1.

## Summary

The WRAM region from `$0619` through `$0A18` is best modeled as a 64-slot object pool stored in structure-of-arrays form.

- column stride: `0x40`
- columns: 16
- slot count: 64
- total size: `0x400` bytes
- indexed access: predominantly `base,X`

This is not a fixed C-like struct with one permanent semantic for every byte. Multiple banks reuse later columns as type-specific work fields. Treat the pool as a shared object slot with handler-dependent union semantics.

## Column map

| Base | Current interpretation | Confidence |
|---|---|---|
| `$0619` | core work 0 | unresolved |
| `$0659` | core work 1 | unresolved |
| `$0699` | core work 2 | unresolved |
| `$06D9` | core work 3 | unresolved |
| `$0719` | core work 4 | unresolved |
| `$0759` | handler-dependent overlay work | type-dependent |
| `$0799` | handler-dependent overlay; bank89 bit7 is a transient state latch | type-dependent |
| `$07D9` | movement offset/work in bank89 | strong |
| `$0819` | signed movement delta/work in bank89 | strong |
| `$0859` | script pointer low byte or generic work | confirmed in bank89 |
| `$0899` | script pointer middle byte or generic work | confirmed in bank89 |
| `$08D9` | script pointer bank byte or generic work | confirmed in bank89 |
| `$0919` | X-like position/work A in bank89 | strong |
| `$0959` | Y-like position/work B in bank89 | strong |
| `$0999` | auxiliary parameter/timer A | type-dependent |
| `$09D9` | auxiliary extent/timer B | type-dependent |

## Strong evidence

### 24-bit object-script pointer

Bank89 loads:

`$0859,X -> $B9`
`$0899,X -> $BA`
`$08D9,X -> $BB`

and the object-script dispatcher subsequently reads operands through `[$B9],Y`.

This confirms that these three columns form a 24-bit script pointer for the bank89 object-script family.

### Movement pair

Bank89 writes signed `+2/-2` style values into `$0819,X`. Update code moves `$07D9,X` in the corresponding direction while driving `$0819,X` back toward zero.

This supports:

- `$07D9,X`: movement offset / accumulated displacement
- `$0819,X`: signed remaining movement delta

The exact coordinate axis remains open.

### Position-like pair

Bank89 commits `$030B/$030D` into `$0919,X/$0959,X`. Later collision/edge logic uses `$0959,X` directly and also probes `$0959,X + $09D9,X + 1`.

This makes a coordinate interpretation strong for bank89, with `$09D9,X` acting as a vertical span/extent in that handler family.

The same columns can have different meanings in other object families, so these are bank89-specific semantic names rather than universal names.

### Type-dependent reuse

Bank85 uses `$0999,X` as a saved object parameter and `$09D9,X` as an incrementing counter. Bank87 also initializes/decrements these columns as work counters.

Therefore `$0999/$09D9` cannot be globally named only as dimensions. They are shared per-slot work columns whose semantics depend on the object handler.

## Architectural consequence

The earlier model treated individual addresses such as `$0799` too independently. The new model is:

```
64 object slots
  x
16 SoA columns
  =
WRAM $0619..$0A18
```

The bank89 object-script system overlays script pointer, movement state, position-like values, and auxiliary extent/state on this shared pool. Other banks reuse the same pool for different object families.

This explains why cross-bank xrefs can appear contradictory when a single permanent meaning is assigned to one column.

## Next validation

1. Runtime-sample the full 16-column row for a small number of active slots during NPC movement.
2. Correlate the bank89 slot index with the downstream active-list/OAM object.
3. Determine exact meanings for the first six core columns.
4. Split universal field names from handler-specific overlays in the external schema.
