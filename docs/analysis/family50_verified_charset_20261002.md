# Family-0x50 verified charset promotion

Updated: 2026-10-02

## Result

Single-byte text token `0x5B` is promoted from an unknown marker to the literal printable glyph `?`.

This is a charset correction only. It does not infer actor identity, event meaning, story state, or branch semantics.

## Evidence

The same mapping is present in the checked text decoder tables already retained in the repository:

- `data/text_trace/shinmomo_trace_text_jp_decode_snes9x_20260426.lua`: `["5B"] = "?"`
- `data/text_trace/shinmomo_trace_dialogue_jp_v2_snes9x_20260426.lua`: `["5B"] = "?"`
- `tools/lua/shinmomo_trace_dialogue_v28_mode02_bd98_decoder_smallkana_checked_snes9x_20260427.lua`: `["5B"] = "?"`

The family-0x50 canonical streams also place `0x5B` in ordinary printable-text positions, including question-shaped sentence endings. No control-flow interpretation is required for this promotion.

## Mechanical effect

Before promotion, the following canonical sources contained unresolved `0x5B` markers:

- `0x50:0x02`: 1 unknown, all attributable to `0x5B`
- `0x50:0x09`: 1 unknown, all attributable to `0x5B`
- `0x50:0x0B`: 4 unknowns, all attributable to `0x5B`
- `0x50:0x12`: 3 unknowns total, one attributable to `0x5B`

After promotion:

- `0x50:0x02`, `0x50:0x09`, and `0x50:0x0B` become zero-unknown confirmed static direct decodes.
- `0x50:0x12` remains unresolved because two non-`0x5B` tokens remain.
- strict family-0x50 actor closure increases from 3/10 to 5/10.
- newly closed actors are `F50-L002` and `F50-L006`.

Remaining incomplete actors are `F50-L003`, `F50-L005`, `F50-L007`, `F50-L009`, and `F50-L010`.

## Reproducible transform

`tools/python/apply_verified_dialogue_charset.py` applies the verified charset mapping to:

- `data/dialogue/family50_canonical_direct_decode_20260930.csv`
- `data/npc_display/static_actor_event_dialogue_binding_20260930.csv`
- `data/npc_display/static_actor_dialogue_sequences_20260930.json`
- `data/npc_display/static_actor_dialogue_sequence_pages_20260930.csv`

The script is idempotent and preserves unresolved non-`0x5B` tokens.
