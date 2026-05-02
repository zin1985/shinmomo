# 新桃太郎伝説 vol015: bank85 opcode 0x50 stream operand 列挙

## 対象

- bank85 mini-VM opcode `0x50`
- handler: `85:80B7`
- 処理: `LDA [$98],Y -> TAX -> JSR 85:9F4B -> JSL 84:9BC5`
- operand は `0x50` の直後1バイトで、`X = queue write index` として使われる。

## 結論

既知の CB weapon special inner script slice 内で、aligned opcode `50 xx` と見られる箇所は **3件**。

| SNES | operand | hook | equip | confidence |
|---|---:|---|---|---|
| `CB:04C1` | `00` | `C1` | `16` | high |
| `CB:04F9` | `00` | `C1` | `17` | medium-high |
| `CB:0E17` | `00` | `C8` | `187` | high |

operand summary:

| operand | count | addresses |
|---:|---:|---|
| `00` | 3 | CB:04C1 CB:04F9 CB:0E17 |

## 解釈

`opcode 0x50` の operand は、現時点で確認できる weapon special inner script ではすべて `00`。

したがって、weapon特殊能力系で `85:80B7` が呼ばれる場合は、まず `85:9F4B` に `X=0` を渡し、`$1297[0] / $129F[0]` から queue pair を構成する線が本命。

## C7側について

修正後到達点の C7 descriptor records (`C7:9EA5`, `C7:9EC3`, `C7:A566`, `C7:A57D`) には raw byte `50` が出るが、これは bank85 opcode `0x50` ではない。

理由:
- C7 descriptor stream は `84:9E10` が読む。
- `84:9E10` では `50..FF` は literal raw-id。
- したがって C7内の `50 xx` は「opcode 50 + operand xx」ではなく、「literal raw-id 50 の次に別token/byteが続いている」だけ。

C7 raw `50` occurrences: 8件。詳細は `c7_descriptor_raw50_not_opcode50_20260501.csv` を参照。

## 出力

- `cb_weapon_inner_opcode50_operands_20260501.csv`
- `opcode50_operand_summary_20260501.csv`
- `c7_descriptor_raw50_not_opcode50_20260501.csv`
