# Unreferenced CF-layout render probes — 2026-09-29

## Scope

After rendering all recovered primary configurations and opcode-0x51 secondary
layers, the 203-entry CF layout table was re-audited.

The apparent unreferenced set was initially:

```text
17, 66, 79, 161, 162, 164
```

Layout 164 is **not actually unreferenced**.  Batch 8 already proves a
non-immediate normal-mode secondary path in pack 0x9D:

```text
CC:FB61  50 2A A3 01   ; TS42 / layout163
...
CC:FB93  11 28
CC:FB98  51 2A A4      ; TS42 / layout164
```

Seeding the existing fail-closed normal-mode CFG immediately after the proven
normal primary selector at CC:FB61 shows that CC:FB98 is reachable while normal
mode remains active.  Layout 164 is therefore a real TS42 secondary layer and
was already rendered canonically under:

```text
data/maps/rendered/dungeon_tileset_42_p28_secondary/map_164.png
```

The configuration-index builder currently misses this case because it records
only immediate 0x51 pairs.

That leaves five CF layouts with no recovered selector reference:

```text
17, 66, 79, 161, 162
```

## Layouts 17, 66 and 79

These three layouts are structurally consistent with tileset 7:

- layout 17 follows TS7 layouts 14, 15 and 16 in CF order;
- layout 66 lies directly between referenced TS7 layouts 65 and 67;
- layout 79 lies directly between referenced TS7 layouts 78 and 80.

Rendering them with the already proven TS7 ROM resource state:

```text
10 0A
10 0B
11 09
```

passes the same strict checks used by canonical normal maps:

- complete CHR coverage;
- complete non-zero palette coverage;
- no borrowed runtime VRAM/CGRAM bytes.

The images are visually coherent interior maps.

Probe outputs:

```text
data/maps/rendered/unreferenced_layout_probes/ts07/map_017.png
data/maps/rendered/unreferenced_layout_probes/ts07/map_066.png
data/maps/rendered/unreferenced_layout_probes/ts07/map_079.png
```

These are strong render candidates, but remain labelled probes because no
runtime/script selector reference has yet been recovered.

## Layouts 161 and 162

The layout-number sequence strongly suggests the otherwise missing tileset 41:

```text
TS40: layouts 157/158 and 159/160
TS41: layouts 161/162   <- missing configuration family
TS42: layouts 163/164
TS43: layouts 165/166
```

The neighboring resource sequence also suggests the candidate setup:

```text
10 13
10 14
11 27
```

Evidence for this candidate:

- TS40 uses palette operand 0x26;
- TS42 uses palette operands 0x28/0x29;
- opcode-0x11 operand 0x27 exists and covers CGRAM 0x20..0x6F;
- layouts 161/162 expanded through tileset 41 require exactly the CHR/palette
  coverage supplied by 10 13 + 10 14 + 11 27;
- both layouts pass strict resource validation;
- layout 161 renders as a large coherent map;
- layout 162 renders as a sparse secondary-like layer.

However, no actual VM setup/selector sequence:

```text
10 13 / 10 14 / 11 27
50 29 A1 ...
51 29 A2
```

has been found in parsed pack streams or raw ROM search.

Therefore TS41 is **not promoted to a canonical gameplay configuration**.
The images are retained only as structural probes:

```text
data/maps/rendered/unreferenced_layout_probes/ts41_candidate/map_161.png
data/maps/rendered/unreferenced_layout_probes/ts41_candidate/map_162.png
```

## Current CF-table accounting

- CF layout slots: 203
- primary configuration layouts: 148
- immediate secondary layouts: 49
- non-immediate proven TS42 secondary: layout 164
- remaining layouts without a recovered selector reference: 5

All five remaining layouts can now be rendered structurally without CHR/palette
coverage violations, but they are intentionally separated from canonical
reachable-map output.

## Next investigation

1. search non-standard/special VM paths for references to layouts 17/66/79/161/162;
2. inspect table-driven map setup paths outside normal 0x50/0x51;
3. if no references exist, classify these five as likely unused/orphan map data;
4. separately model normal BG1/BG2 priority to composite proven primary and
   secondary layers into final game-like maps.
