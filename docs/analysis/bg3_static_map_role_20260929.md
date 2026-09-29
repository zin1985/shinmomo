# BG3 role in normal-map reconstruction — 2026-09-29

## Conclusion

For the recovered normal-map system, canonical static map geometry is carried by
the primary and optional secondary map layers assigned to BG1/BG2.

BG3 is not fed by a third canonical map selector/layout pair in the recovered
normal-map loader.  It remains available to script-driven/runtime graphics,
UI/text, effects and other dynamic uses, but it is not part of the canonical
full-map geometry exported by the BG1+BG2 composite renderer.

Therefore:

```text
canonical static background geometry = BG1 + BG2
BG3 = dynamic / non-canonical-map layer unless separately proven per scene
OBJ = sprite/event layer, kept separate
```

## Canonical map-state structure

The normal-map runtime state exposes two map-selector pairs:

```text
$139C primary tileset
$139E primary layout

$139D secondary tileset
$139F secondary layout
```

Opcode `0x50` populates the primary pair.
Opcode `0x51` populates the secondary pair.

There is no third equivalent tileset/layout pair in this recovered selector
path.

## Normal initialization assigns BG1/BG2

The normal map setup at `C0:CD85` sets `$1503 = 1`, takes the map variant
from `$139B`, and calls `80:C6FD`.

The optional secondary setup at `C0:CDD1` sets `$1503 = 0`, computes
`3 - $139B`, and calls the same `80:C6FD`.

`80:C6A8` mirrors the SNES screen-base registers as:

```text
$1142 = BG1SC
$1144 = BG2SC
$1146 = BG3SC
$1148 = BG4SC
```

`80:C6FD` converts selector N to the corresponding entry beginning at
`$1142`:

```text
1 -> BG1
2 -> BG2
3 -> BG3
4 -> BG4
```

All recovered immediate-secondary map configurations use map variant 1 or 2.
Consequently:

```text
variant 1: primary BG1, secondary BG2
variant 2: primary BG2, secondary BG1
```

The normal primary/secondary map loader never requires selector 3 for these
canonical map configurations.

## Base normal initialization

The broader normal-map initialization path at `C0:CBF9` also selects BG1
explicitly:

```text
LDA #$01
JSL $80:C6FD
```

This establishes BG1 as the initial normal-map background target before the
primary/secondary configuration loader applies the variant-specific BG1/BG2
assignment.

## Other 80:C6FD callers

There are additional `80:C6FD` calls outside the canonical
primary/secondary geometry setup.

These include VM/script handlers and runtime object/effect logic where the layer
selector is supplied dynamically from script or runtime state.

Their existence proves that BG3 is usable by the engine, but does not define a
third ROM map layout for the canonical full-map geometry.

Accordingly, those paths are intentionally treated as runtime/dynamic layers
until a particular scene proves otherwise.

## BGMODE

Normal-map initialization selects SNES Mode 1 through:

```text
80:CB60 / 80:CBCD
  LDA #$01
  JSL $80:A065
```

`80:A065` writes the low three BGMODE bits in WRAM mirror `$0376`.

Mode 1 supports BG1, BG2 and BG3, but support at the PPU level does not imply
that every layer is a canonical map-storage layer.  The ROM map selector
pipeline above binds only primary/secondary geometry to BG1/BG2.

## Export policy

The canonical map outputs are therefore:

1. primary layer PNG;
2. optional opcode-0x51 secondary layer PNG;
3. Mode-1 BG1+BG2 priority composite PNG.

BG3 and OBJ are not flattened into those canonical images.

If later analysis proves scene-static BG3 material that should be preserved, it
should be exported as a distinct runtime/scene overlay rather than silently
changing the canonical source-map geometry.

## Current consequence

`data/maps/rendered/bg12_composites/` is the highest-confidence complete
static background representation currently recoverable from the ROM map
configuration system.

All recovered immediate-secondary configurations are represented there,
including the three proven unequal-dimension cases.
