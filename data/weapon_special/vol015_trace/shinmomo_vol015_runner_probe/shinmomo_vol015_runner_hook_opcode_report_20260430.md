# 新桃太郎伝説解析 vol015: master table runner / weapon hook / mini-VM opcode length

作成日: 2026-04-30  
対象ROM: `Shin Momotarou Densetsu (J).smc`  
ROM本体は成果物に含めない。

## 1. `0x0AC03C` master table を読む runner 候補

今回の重要発見は、`0x0AC03C = CA:C03C` そのものを直接 base として読む処理よりも、**`CA:C000` を base とする 3-byte long pointer table helper** が先に見つかったこと。

### C4:8509..854F: index -> long pointer loader

この処理は概ね以下の形。

```text
incoming index -> $126A / $126E
offset = index * 3
ptr_addr = CA:C000 + offset
[$2A..$2C] = ptr_addr
$98/$99/$9A = long pointer read from CA:C000[index]
JSR C4:8554
```

該当バイト列は `runner_candidate_code_bytes_20260430.csv` に保存。

### C4:8554..858B: reverse scanner / normalizer

この処理は `$98/$99/$9A` に入った 24-bit pointer を、`CA:C000` の3バイト表から逆引きする。

```text
Y = -1
X = 0
loop:
  compare $98/$99/$9A with CA:C000+X
  if not yet past: Y++, X+=3, continue
store Y -> $126E
store Y -> $12B4
```

さらに `CPY #$14` の guard があり、**index < 0x14 は dummy/reserved 扱い** と見てよい。

## 2. `index 2 = CB:01F9` の上流値

ここは表記を分けた方が安全。

| 見方 | 値 | 内容 |
|---|---:|---|
| `CA:C03C` から数える相対index | `0x02` | `CB:01F9` |
| `CA:C000` helper から数えるglobal index | `0x16` | `CB:01F9` |
| `CA:C000` の dummy/reserved 数 | `0x14` | `CA:C000..CA:C03B` は 20件分の0埋め |

つまり、今後コード側で追うべき値は **相対 index 2** だけでなく、C4 helper 経由なら **global pack id 0x16**。

```text
CA:C000[0x14] = CA:CBC8
CA:C000[0x15] = CA:DB47
CA:C000[0x16] = CB:01F9   ; weapon special table
```

## 3. hook_id 82 / 83 / 84 / C1 / C2 / C8 の呼び分け

`CB:01F9` は装備IDごとの 16-bit pointer table。各 pointer は top-level hook list を指す。

top-level hook list は以下の反復形式。

```text
[hook_id:1][inner_ptr16:2] ... 00
```

有効装備 0..233 で確認した hook 分布:

| hook_id | 出現 | 静的な見立て |
|---:|---:|---|
| `84` | 234件中ほぼ全件 | pre/setup 系。多くは `A0 <long> B6 B5` の6バイト。 |
| `83` | 234件中ほぼ全件 | main / standard special check 系。特殊装備では `A4 xx C0 B5` 型が多い。 |
| `82` | 234件中ほぼ全件 | common fallback / footer 系。`B1 CB:03DB; B0` の5バイト。 |
| `C1` | 6件 | 玄武/白虎/朱雀/青龍系 + 凪モリ系の追加処理。 |
| `C2` | 2件 | 非常にレアな追加処理。entry 61 / 123。 |
| `C8` | 9パターン | 酒呑の剣、包丁/ドス/名刀系、錫杖系に集中。 |

注意点: top-level list の順序は実行順ではなく、**runner が要求 hook_id で検索するための辞書順リスト** と見るのが安全。  
理由は、`C8` が `82` の前に来る装備と後ろに来る装備が混在するため。順次実行ならこの順序差は不自然。

### hook selector の入口候補

`C4:A0F2..A108` が濃い。

```text
LDX $12B4
LDA $12B5
JSR $AE3A
BCC fallback
  LDA $12B4 ; JSR C4:9D4D
  LDA $12B5 ; JSR C4:9D91
```

`$12B4` は pack/root、`$12B5` は subindex / hook_id 側と見るのが自然。  
ただし **hook_id 82/83/84/C1/C2/C8 を実際にセットする caller はまだ完全未確定**。ここは次回の runner hunt 継続対象。

## 4. inner mini-VM opcode length table

今回の静的 slice 境界から、指定 opcode の長さは以下まで固めた。

| opcode | length | 確度 | 根拠 |
|---:|---:|---|---|
| `A0` | 4 | 高 | `A0 E1 03 CB` / `A0 11 DD CA` / `A0 F5 7F CB`。long pointer operand。 |
| `A4` | 2 | 高 | `A4 02 C0 B5` など。1-byte immediate。 |
| `B1` | 4 | 高 | `B1 DB 03 CB` / `B1 EF 15 CB`。long pointer operand。 |
| `B2` | 2 | 高 | `A4 00 B2 04 A4 01` で1-byte operand。 |
| `B3` | 2 | 中高 | `B3 03 B0` / `B3 0F 51`。1-byte parameter。 |
| `B4` | 2 | 高 | `B4 04 C0 B5` / `B4 06 B1...`。 |
| `B5` | 1 | 高 | short script terminator 的に機能。 |
| `C0` | 1 | 高 | `A4 xx C0 B5` の境界に一致。 |
| `D0` | 3 | 高 | `D0 64 03` / `D0 86 19`。16-bit operand。 |
| `E0` | 1 | 高 | `D5 xx xx E0` / `3B 19 E0`。 |
| `CE` | 3 | 高 | `CE 22 D5` / `CE 1B D5`。16-bit operand。 |

CSV版: `inner_mini_vm_opcode_length_table_20260430.csv`

## 5. 今回の進捗反映

- Goal 7: 72% -> **78%相当**
  - `CB:01F9` の二層構造、hook分布、inner opcode length が進んだ。
- Goal 8: 72% -> **73%相当**
  - `CA:C000` master pointer helper と `global index 0x16` の整理が進んだが、完全な caller は未確定。
- Goal 9: 60% -> **62%相当**
  - mini-script命令長表が増え、仕様書化の材料が増えた。

## 6. 次に攻める箇所

1. `C4:A0B4 / A0C0 / A0F2` の caller を opcode table 経由で追う。
2. `$12B5` に `82/83/84/C1/C2/C8` が入る瞬間を捕捉する。
3. `AE3A` direct-hit と fallback `9D4D/9D91` のどちらで weapon hook が解決されるかを切る。
4. `CB:01F9` top-level hook runner が `00`終端まで scan している本体を探す。
5. mini-VM の未定義 opcode `39/4F/5D/69/70/8D/8E/DD/EC` も長さ表に追加する。
