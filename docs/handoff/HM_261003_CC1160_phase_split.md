# Handoff: CC:1160 phase-dependent destination set

Date: 2026-10-03

The last destination-config-only trigger gap is no longer an ordinary missing-join case. Canonical Drive ROM was obtained and verified at 2,097,152 bytes / SHA-256 `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`.

`CC:1160` is `53 CE 02`, so the transition targets pack `0xCE`, entry `0x02`; committed arrival is `(22,28)`. Pack 0xCE exposes five canonical configs in the relevant destination family (`cfg_t04_l085_v2`, `cfg_t04_l086_v2`, `cfg_t05_l087_v2`, `cfg_t04_l088_v2`, `cfg_t04_l089_v2`). All five share native bounds X=16..31/Y=16..28, so bounds cannot disambiguate the arrival. This explains why the generic bounds resolver intentionally produced no unique row.

Next priority: recover the destination-side phase/state discriminator around the pack-0xCE entry-0x02 control flow (`CD:9140..91DC`) and determine the reachable subset for `CC:1160`. Do not guess a single config from layout proximity. After this selector is understood, continue with the ten arrival-XY-only trigger gaps.

Evidence: `docs/analysis/event_trigger_CC_1160_phase_split_20261003.md`, `data/events/transition_CC_1160_phase_candidates.json`, committed map configuration index/native bounds, canonical ROM static inspection. No ROM/raw copyrighted dump is committed.
