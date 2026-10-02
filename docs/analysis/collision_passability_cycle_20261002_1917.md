# Collision/passability rolling cycle 2026-10-02 19:17 JST

## Scope
Priority theme: collision/passability, specifically static provenance of the bank89 collision/edge candidate already present in canonical WRAM documentation.

## Canonical ROM status
Google Drive search for `Shin Momotarou Densetsu (J)_original.smc` returned no accessible result in this run. The expected 2,097,152-byte image and SHA-256 `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98` therefore could not be verified. No substitute ROM was used.

## Confirmed facts
- `docs/analysis/wram_object_pool.md` already records bank89 commits `$030B/$030D` into `$0919,X/$0959,X`.
- The same canonical document explicitly says later collision/edge logic reads `$0959,X` directly and probes `$0959,X + $09D9,X + 1`.
- `$07D9/$0819` remain movement-work fields for this bank89 overlay; `$0919/$0959` remain position-like, and `$09D9` behaves as a vertical span/extent in this handler family.
- `$09D9` is type-dependent elsewhere, so it must not be globally renamed as height/extent.

## New finding / reconciliation
The previous rolling plan treated the next static step as a broad search for a movement accept/reject discriminator. Re-reading the canonical WRAM evidence exposes a narrower pre-existing lead: bank89 already has a documented collision/edge consumer anchored on the position-like coordinate and an extent-adjusted probe. This does **not** prove a terrain collision table, but it materially reduces the static search frontier.

### Evidence classes
**Confirmed:** bank89 position commit and collision/edge reads described above are already canonical repository evidence.

**Strong hypothesis:** the `$0959` and `$0959+$09D9+1` consumer family is near the spatial boundary test needed for passability/edge handling and is a better breakpoint/static-xref seed than a whole-WRAM diff.

**Unconfirmed:** whether that consumer tests terrain tiles, map bounds, object occupancy, event gates, transition gates, or a mixture; exact X/Y axis assignment; map/config provenance of the tested data.

## Next cycle
1. Recover the concrete bank89 routine/caller provenance behind the documented collision/edge reads.
2. Classify every upstream data read as map/config, object occupancy, event/trigger, transition, or unknown.
3. If canonical ROM becomes accessible, verify size/hash first, then run same-savestate walkable/blocked control pairs around this narrowed candidate.
4. Promote to `terrain/passability` only after a repeatable accept/reject edge and map/config-dependent read are both demonstrated.
5. Continue to event-trigger region, transition→event crosslink, visible-object→map-world coordinates, NPC/sprite/event/dialogue integration, native `$0305` writers, then rebuild integration.

`progress/project_progress.json` is updated this cycle: WRAM track 67%→68%, with scope/evidence/updated_at refreshed and the rolling schedule replaced by the collision frontier priorities. Top-goal percentages remain unchanged, so formal overall progress remains 50.4%.
