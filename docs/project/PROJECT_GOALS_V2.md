# Shinmomo project goals v2

Updated: 2026-09-25

## Definition of Done

The project is complete only when the analysis outputs are sufficient to reconstruct Shin Momotarou Densetsu without depending on undocumented behavior from the original ROM.

The old numbered goals remain useful as analysis workstreams, but they are not top-level completion criteria.

## G1 — Program / logic complete analysis and ROM rebuild

**Goal:** fully explain the 65816 program, game logic, data flow, formats, and build layout so an equivalent ROM can be rebuilt from documented source/data/assets.

100% requires:

- complete code/data/table/pointer/bank map;
- all executable routines classified and their interfaces documented;
- Script VM, event, map, object, battle, UI, item/equipment, save and audio-side logic specified;
- all required data schemas externalized;
- reproducible build pipeline from analyzed source/data/assets;
- rebuilt output validated against known behavior, and preferably byte-identical where feasible.

A host-side C scaffold is useful evidence but is not ROM rebuild completion.

## G2 — Complete dialogue salvage

**Goal:** recover every player-visible text resource and connect it to its context.

100% requires:

- character/glyph encoding and control tokens;
- all source modes and compression/dictionary formats;
- all dialogue roots and chains enumerated;
- complete bulk extraction;
- system, shop, battle, item/equipment, NPC and event text included;
- source address, control tokens, event/location/condition and speaker/context metadata where derivable;
- validation that no reachable text corpus remains unaccounted for.

## G3 — Complete sprite salvage

**Goal:** recover all sprite/character/enemy/effect/UI graphic assets together with the metadata needed to reproduce animation and composition.

100% requires:

- sprite frame definitions and OAM piece layouts;
- CHR/tile source mapping;
- palettes/CGRAM;
- animation groups/states/timing;
- all characters, NPCs, enemies, bosses, effects and sprite-like UI assets enumerated;
- reproducible exporters producing canonical assets;
- all-scene validation.

Understanding the OAM renderer is not the same as having salvaged every sprite.

## G4 — Complete event analysis

**Goal:** enumerate and understand every event and its conditions/effects.

100% requires:

- event/script VM semantics;
- selector/condition systems;
- event resources and target tables;
- flags, actor/object actions, dialogue links, rewards, battles, joins/leaves and state changes;
- every event enumerated in a machine-readable catalog;
- an event graph covering the game from start to ending, including conditional branches.

## G5 — Complete portable specification

**Goal:** produce a specification from which the game can be reimplemented on another platform without reading the original 65816 code.

100% requires:

- architecture and memory maps;
- all table/data schemas;
- VM/event/text/graphics/map/object/battle/UI/item/equipment/save/audio specifications;
- portable reference behavior and examples;
- asset formats and extraction rules;
- deterministic verification fixtures/tests;
- enough detail for an independent implementation to reproduce behavior.

## Progress model

Top-level completion is the equal-weight mean of G1..G5.

A second layer of workstreams is retained because it is useful for deciding what to analyze next. A workstream can reach 100% without any top-level Goal reaching 100%.

Every progress change must distinguish:

1. **new analysis** completed in the current cycle;
2. **recovered evidence** from older repository material that was missing from the rolling tracker;
3. **reclassification** where old claims are narrowed or downgraded.

The canonical machine-readable source is `progress/project_progress.json`.
