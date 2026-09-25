# Historical dialogue crosslink handoff — 2026-09-26

## Scope

Priority 1 continued for G2/G4/G5 by reconnecting retained decoder results to the current usage-driven source model.

The pinned Drive ROM folder was checked again. The canonical file is `Shin Momotarou Densetsu (J)_original.smc`, Drive id `1pl41WGRSac6kqBLzTtAtx_peeIe6jqpq`, size 2,097,152 bytes.

The analysis ROM available in this chat was also checked directly: size 2,097,152 bytes and SHA-256 `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`. This matches the established canonical analysis hash.

## New result

`tools/python/crosslink_historical_dialogue.py` joins the current usage catalog to retained v33 decoder outputs by exact token SHA-256, requiring first token `0x7D`, terminator `0x00`, and non-empty historical decoded output.

Result:

- 76 historical evidence rows
- 21 unique current usage pairs
- families `0x4E`, `0x4F`, `0x50`
- 2 pairs already known dialogue: `0x4F:00`, `0x4F:01`
- 19 previously visibility-unknown pairs gain `strong_dialogue_historical` evidence
- unresolved visibility set becomes 2,206 when the overlay is applied, versus 2,225 in the unchanged base usage catalog

No historical decoded dialogue body is copied into the new crosswalk. Only source/hash/evidence metadata is emitted.

## Progress impact

- G1: 47% unchanged
- G2: 62% -> 63%
- G3: 49% unchanged
- G4: 44% unchanged
- G5: 48% unchanged
- overall: 50.0% -> 50.2%

Legacy workstreams:

- Dialogue: 74% -> 76%
- Externalization: 72% -> 73%
- weighted local maturity: 76.2% -> 76.4%

## Next target

1. classify the remaining 2,206 unknown pairs through display/event/runtime provenance;
2. attach event/script-pack context to the 19 recovered strong dialogue pairs;
3. render only the player-visible subset;
4. keep UI/system/descriptor/internal resources separate;
5. reuse the same evidence key in the future event catalog.

## Canonical outputs

- `docs/analysis/historical_dialogue_crosslink.md`
- `data/dialogue/historical_decode_crosswalk.csv`
- `data/dialogue/historical_decode_crosswalk_summary.json`
- `tools/python/crosslink_historical_dialogue.py`
- `progress/project_progress.json`

Drive `Projects/shinmomo/latest` is promoted only after the final GitHub Actions run succeeds.
