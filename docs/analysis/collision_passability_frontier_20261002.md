# Collision / passability frontier audit (2026-10-02)

## Scope

This cycle intentionally leaves the opcode-0x59 `$0719` field family after the bit0 evidence was bounded as `controller_low_state_seed`. The next high-information frontier is collision/passability and event-trigger-region reconstruction because it joins the already mature canonical map/configuration, transition, actor, event, and dialogue workstreams.

## Provenance and ROM availability

The canonical ROM required for ROM-backed claims is `Shin Momotarou Densetsu (J)_original.smc`, expected size 2,097,152 bytes and SHA-256 `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`.

During this cycle Mole Remote was healthy, but the configured Google Drive path did not expose the canonical ROM (`ROM_NOT_FOUND`). No substitute ROM was used. Therefore this document contains only repository-backed planning/evidence boundaries and does not promote any new ROM semantics.

## Confirmed repository baseline

Do not redo these map layers:

- primary/secondary map reconstruction and canonical map configurations;
- Mode1/Mode7/BG-priority composition and different-size BG same-origin clipping/transparent padding;
- structural-world reconstruction;
- runtime logical/visible-object observations;
- transition extraction baseline at and after `5b5083308a02a4328ac0d70ad3e5ed3b23acc9ba`;
- opcode 0x53/0x56 transition core and 0x58 coordinate setter;
- current structural viewer/mobile packaging work.

The current main also contains the opcode59 bit0 closure and overwrite audit. Keep the conservative label `controller_low_state_seed`; do not spend the next cycle re-labelling it unless a direct pre-overwrite consumer appears incidentally.

## Collision/passability evidence boundary

A repository code search for dedicated `collision`, `passability`, `event trigger`, and Japanese `通行` artifacts did not identify a canonical collision/passability model on current main. This is a gap, not evidence that the game lacks such a table or routine.

Accordingly, collision work starts at L0: identify the movement-decision path and the map/config-dependent data it consumes before assigning any tile/region semantics.

### Confirmed

- Canonical map configuration/layout/tileset IDs and structural map output already exist and should be used as join keys.
- Transition destination/configuration and arrival-coordinate catalogs already exist and should be used as control points.
- Runtime logical/visible object work exists and should be used later to distinguish static terrain blocking from object/event blocking.

### Strong hypotheses to test, not facts

- Passability may be represented by metatile/tile attributes, a configuration-specific auxiliary table, a region grid, or a combination of these.
- Event-trigger regions may share coordinate normalization with collision or transition checks, but they must not be merged until a common reader/writer path is demonstrated.

### Unconfirmed

- collision table address/format;
- player/NPC movement collision routine;
- tile-to-world coordinate conversion used by collision;
- event-trigger-region record format;
- whether transitions are a subset of a generic trigger-region system.

## Next analysis procedure

1. With the canonical Drive ROM available and hash-verified, identify the player movement accept/reject path by tracing coordinate candidates immediately before committed movement.
2. Classify every map/config-dependent read in that bounded path. Prefer xrefs into already externalized CE/CF/configuration structures before blind ROM scans.
3. Use two control points: a known walkable neighbor pair and a known blocked neighbor pair on the same canonical configuration. Record only addresses/derived metadata, never raw ROM/VRAM/OAM/CGRAM dumps.
4. Determine whether the discriminator is tile/metatile attribute, region data, object occupancy, or a composite gate.
5. Once a static discriminator is reproduced, export a metadata-only collision/passability catalog keyed by canonical configuration + world/map coordinates.
6. Then repeat the same bounded-reader method for event activation and transition triggers, joining to the existing transition/event/dialogue catalogs.

## Rolling priority

1. collision/passability movement-decision path identification;
2. map/config -> collision-data crosslink and metadata exporter;
3. event-trigger-region reader/record format;
4. transition -> event/trigger crosslink expansion;
5. visible-object coordinate -> map-world coordinate conversion;
6. NPC/sprite/event/dialogue integrated object catalog;
7. native `$0305` writer classification;
8. rebuild-spec integration.

## Blocker

Drive指定ROMへアクセスできなかった。次のROM-backed cycleには、Google Drive上の正本ROMがMole Remote実行環境から見えることが必要。別ROMでの代用は禁止する。
