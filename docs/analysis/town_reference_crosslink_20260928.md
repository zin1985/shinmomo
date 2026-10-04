# Town reference crosslink from YMA maps and ROM dialogue

Updated: 2026-09-28

## Purpose

Bind human-facing village names to already-proven ROM map configurations without
guessing from scenery alone.

The comparison uses three independent evidence channels:

1. exact ROM/runtime map identity from the selector/configuration work,
2. derived topology from YMA's schematic town maps,
3. usage-driven static decoding of the ROM dialogue source family attached to the pack.

Reference pages:

- http://www.yma.kirara.st/data/town1.html
- http://www.yma.kirara.st/data/town2.html

Reference PNGs are not stored in Git. Only derived signatures and source hashes are
canonicalized in `data/maps/reference/yma_town_reference_signatures.json`.

## Dialogue decoder

`tools/python/decode_dialogue_source_pairs.py` reuses the already-proven readers in
`catalog_dialogue_sources.py`:

- mode 0: raw stream
- mode 1: C0:BD28 ring/back-reference reader
- mode 2: C0:BD98 tree/bitstream reader

The checked MOMO3/DICT02 rendering tables are read from the v28 dialogue Lua.
A validation run over the town-candidate families 0x50, 0x60, 0x65, 0x67, 0x82,
0x83 and 0x8E decoded 120 usage-driven source pairs with 120 successes and zero
reader errors.

Arbitrary unused subindices are deliberately not scanned because source families are
overlapping entry-point streams rather than bounded independent files.

## Static map rendering

The live tileset-4 VRAM from the runtime-confirmed 旅立ちの村 capture was checked
against the ROM-expanded map.

For field/town rendering, 4bpp CHR at VRAM character base 0x8000 reconstructs
recognizable terrain, buildings, roads and water from ROM-expanded tileset-4
tilemap entries.

This permits local-only full-map renders for unknown layouts without visiting each
map in the emulator. Render PNGs remain outside Git.

## Current bindings

### cfg_t04_l008_v2 / pack 0x50 / layout 8

**旅立ちの村**

Evidence:

- runtime-bound occurrence: pack 0x50 / CC:1C3F
- user independently recognized the visited map as 旅立ちの村
- YMA `tabidachi.png` matches the shrine, small pond, three field blocks and the
  road/building arrangement
- the YMA-derived signature has 9 buildings, one water component and three field
  components; the ROM layout reproduces the same structural fingerprint

The broad 0x50 dialogue family is not used as the naming proof because it contains
dialogue from several later locations.

### cfg_t04_l034_v2 and cfg_t04_l035_v2 / pack 0x60

**花咲かの村**

Evidence:

- YMA `hanasaka.png` has the characteristic upper special area followed by a
  repeated two-column town grid
- both ROM layouts preserve that same building topology
- family 0x60 subindex 0x04 names 花咲かじいさん and explicitly describes him
  making the cherry trees bloom in "この村"

Layouts 34 and 35 are kept as distinct ROM states but grouped under one human map
group, `hanasaka_village`.

### cfg_t04_l044_v2 / pack 0x65

**ほほえみの村**

Evidence:

- static ROM render has the left-side large/special facility, small pond and the
  lower/right shop cluster visible in YMA `hohoemi.png`
- family 0x65 is dominated by ましら, singing and だじゃれ event dialogue
- independent walkthrough evidence identifies the ましら / 天下一だじゃれ大会
  event as ほほえみの村

This is stronger than the earlier shape-only alternatives.

### cfg_t04_l059_v2 / pack 0x82

**竹取の村**

Evidence:

- family 0x82 subindex 0x06 directly says
  `この 竹取の村のある 島は...`
- subindex 0x10 independently refers to the island containing 竹取りの村
- the same family explicitly mentions さるかにの村 as a different village

Therefore the earlier shape-only guess "サルカニの村" is rejected.

### cfg_t04_l070_v2 / pack 0x83

**竹取の村 context, strong but not yet direct-current-location**

Evidence:

- the family repeatedly contains 竹取の翁, かぐや and the local 竹林
- it describes the 勇気の剣 as being near "この村"
- this is the same late-game 竹取/かぐや location context

Keep the human group as `taketori_village`, but retain a lower status than pack
0x82 until an explicit current-location sentence is found.

### cfg_t04_l060_v1 / pack 0x8E

**七夕の村**

This is direct ROM evidence.

Family 0x8E subindex 0x00 begins:

`ここは 天の川の 七夕の村...`

This overrides the earlier shape-only visual guess "豊かの村".

## Important negative result

Schematic-shape matching alone is useful for candidate generation but is not a
safe naming proof.

During this work it produced plausible but wrong provisional guesses:

- layout 59 -> サルカニの村
- layout 60 -> 豊かの村
- layout 70 -> 静かの村

ROM dialogue disproved or weakened all three. The operational rule is now:

`reference shape -> candidate -> ROM dialogue/event/runtime corroboration -> label`

Never promote a town name from schematic similarity alone.

## Remaining high-value town candidates

- pack 0x67 / layout 39: still unlabeled. Family 0x67 gives directions to
  すゞめのお宿2 and 鹿角の里 but does not yet explicitly name the current village.
- pack 0x81 / layouts 57 and 58: unusual state pair; identify from decoded family
  0x81 and event progression before applying a human name.
- remaining YMA villages such as 金太郎, 浦島, 寝太郎東西, 夢, 新しい, サルカニ,
  豊か should be matched across non-tileset-4 configurations as well; do not assume
  all town maps use tileset 4.

## Canonical evidence

- `tools/python/decode_dialogue_source_pairs.py`
- `data/maps/reference/yma_town_reference_signatures.json`
- `data/maps/context/town_reference_bindings.csv`
- `data/maps/configurations/map_configuration_index.csv`
- `data/maps/context/map_dialogue_pack_crosslink.csv`
- `data/dialogue/source_pair_usage_catalog.csv`
- `tools/python/catalog_dialogue_sources.py`
