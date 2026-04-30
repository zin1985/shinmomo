# ROMアンカー検算メモ（2026-04-30）

ROM本体は含めない。短いアンカーのみ `data/rom_anchor_checks/20260430_weapon_special_anchor_bytes.csv` に保存した。

## 目的

vol014 の Goal 7 / Goal 8 仮説が完全な空論にならないよう、少なくとも以下の raw offset に該当する byte 列が存在することを検算する。

## 検算対象

| label | raw offset | 用途 |
|---|---:|---|
| weapon_special_pointer_table_start | `0x0B01F9` | 装備ID別 pointer table 候補 |
| weapon_special_core_script_header | `0x0B03D1` | hook列候補 |
| op83_default_body | `0x0B03E1` | default op83 body候補 |
| fallback_executor_op82_default | `0x0B0408` | fallback / op82 default候補 |
| selector_dispatch_candidate_A_CA_D800_raw | `0x0AD800` | dispatch候補、未確定 |
| selector_dispatch_candidate_B_CB_D800_raw | `0x0BD800` | dispatch候補、未確定 |

## 注意

- `0x0B01F9` などは raw offset として扱う。
- `CB:03E1` 等の表記は既存メモ上のラベル。raw offset との対応は今後の runner / disassembler 環境で再確認すること。
- `CA:D800` / `CB:D800` 仮説は、現時点では「候補」であり確定ではない。
