# Family-0x50 verified text-token promotion

Updated: 2026-10-02

## Result

All previously unresolved token classes in the current family-0x50 canonical direct-decode set are now explained by independently retained decoder/dispatch evidence.

Verified semantics used by the promotion:

- single byte `0x5B` -> printable `?`
- recursive token `02 C5` -> `ください`
- recursive token `02 C9` -> `わたし`
- `0x04` -> switch to text table 4
- `0x03` -> switch back to text table 3

For the checked text tables, table 3 is the hiragana table and table 4 supplies the corresponding katakana glyphs. Therefore sequences such as `{04}もり{03}`, `{04}だいこん{03}`, and `{04}がんがん{03}` decode as `モリ`, `ダイコン`, and `ガンガン`.

This promotion is limited to text-token semantics. It does not infer actor identity, story meaning, event continuation, or unresolved gameplay labels.

## Canonical ROM

The ROM used for the static recursive-token check is the configured canonical ROM with SHA-256:

`F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`

## Evidence: 0x5B

The printable mapping is already present in checked text decoder tables retained in the repository:

- `data/text_trace/shinmomo_trace_text_jp_decode_snes9x_20260426.lua`
- `data/text_trace/shinmomo_trace_dialogue_jp_v2_snes9x_20260426.lua`
- `tools/lua/shinmomo_trace_dialogue_v28_mode02_bd98_decoder_smallkana_checked_snes9x_20260427.lua`

Each maps `0x5B` to `?`.

## Evidence: 02 C5 -> ください

Historical dispatch tracing already proves the token-02 path:

1. `02 C5` enters the token-02 recursive family-selection handler.
2. `C5 - A0 = 0x25`.
3. family type 01 has no `AE3A` direct hit for this selector.
4. fallback uses `C7:0000[0] = C7:02EE`.
5. after the root byte, `C4:9DBB` skips `0x25` logical zero-terminated records.
6. the selected record is `C7:0477`.
7. bytes are `97 DA 9A 91 00`.
8. checked table-3 mappings decode them as `く だ さ い`.

Primary retained evidence:

- `data/weapon_special/vol015_trace/shinmomo_vol015_dispatch_token_trace/shinmomo_vol015_dispatch_token_trace_report_20260430.md`
- `data/weapon_special/vol015_trace/shinmomo_vol015_dispatch_token_trace/token02_c5_family01_value25_landing_20260430.csv`
- `docs/analysis/dialogue_source_family_catalog.md`

The result also matches every family-0x50 sentence position where the token appears:

- `役立ててくださいね!`
- `お守りください`
- `持って でかけてくださいね!`

## Evidence: 02 C9 -> わたし

The same already-proven token-02 fallback and `C4:9DBB` logical-record skip rule applies mechanically:

1. `C9 - A0 = 0x29`.
2. family type 01 fallback root remains `C7:02EE`.
3. skipping `0x29` logical records lands at `C7:0489`.
4. bytes are `BB 9F 9B 00`.
5. checked table-3 mappings decode them as `わ た し`.

The next source token is `B2 = も`, so the family-0x50 sentence becomes:

`わたしも 一度行ってみたいな!`

No lexical guess is required for the promotion.

## Evidence: 03 / 04 text-table switching

The checked runtime-oriented decoder explicitly implements:

- `0x03 -> tableId = 3`
- `0x04 -> tableId = 4`

in:

`data/text_trace/shinmomo_trace_text_jp_decode_snes9x_20260426.lua`

The same file defines table 3 with hiragana mappings and table 4 with the corresponding katakana mappings, with fallback between the two tables where needed.

This directly explains the remaining family-0x50 markers:

- `{04}もり{03}` -> `モリ`
- `{04}だいこん{03}` -> `ダイコン`
- `{04}がんがん{03}` -> `ガンガン`

## Conservative promotion rule

The transform still promotes a source only when its complete unresolved-marker set is covered by verified rules.

Before this pass, the unresolved canonical sources were:

- `0x50:0x03`: `02C5`
- `0x50:0x04`: `02C5`
- `0x50:0x07`: `04`, `03`
- `0x50:0x0D`: `02C5`
- `0x50:0x11`: `04`, `03`, `02C9`
- `0x50:0x12`: `0x5B`, `04`, `03`

All six rows are now fully explained, so all become zero-unknown `confirmed_static_direct_decode` rows.

The earlier already-promoted `0x50:0x02`, `0x50:0x09`, and `0x50:0x0B` remain unchanged and confirmed.

## Closure impact

Strict family-0x50 actor closure rises from **5/10 to 10/10**.

Newly closed actors in this pass:

- `F50-L003`
- `F50-L005`
- `F50-L007`
- `F50-L009`
- `F50-L010`

All ten modeled family-0x50 actors now pass the same static scene-to-page closure gate.

This does not mean all higher-level semantics are solved. Speaker names, exact place naming, relation-key meaning, and post-dialogue event continuation remain outside this closure claim.

## Machine-readable outputs

- `data/dialogue/family50_verified_token_semantics_20261002.csv`
- `data/dialogue/family50_canonical_direct_decode_20260930.csv`
- `data/npc_display/static_actor_event_dialogue_binding_20260930.csv`
- `data/npc_display/static_actor_dialogue_sequences_20260930.json`
- `data/npc_display/static_actor_dialogue_sequence_pages_20260930.csv`
- `data/npc_display/static_actor_dialogue_closure_20261002.csv`
- `data/npc_display/static_actor_dialogue_closure_20261002.json`

The idempotent transform is:

`tools/python/apply_verified_dialogue_charset.py`

A second execution produces zero changes.
