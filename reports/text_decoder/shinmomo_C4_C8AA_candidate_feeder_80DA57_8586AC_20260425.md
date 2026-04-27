# 新桃太郎伝説 C4:C8AA / $80DA57 / $8586AC(A=0x3A) 解析メモ
作成日: 2026-04-25

## 0. 前提と表記補正

このメモでは、既存プロジェクトの flat ROM bank 表記に合わせる。

- `C4:C8AA` = ROM offset `0x04C8AA`
- `JSL $80:DA57` は mirror として flat `C0:DA57` を参照
- `JSL $85:86AC` は mirror として flat `C5:86AC` を参照

今回の対象は、`$1569` logical object list へ入る前段の **world/event candidate scan**。

---

## 1. C4:C8AA の結論

`C4:C8AA` は、candidate `0x10..0x13` を走査し、条件を満たしたものを `$1958` に入れる **world/event candidate feeder** と見てよい。

処理の流れ:

```text
for X in 0..3:
    bit = table_C4_C8F4[X]       # 01,02,04,08
    if $195E & bit:
        skip

    $1923 = table_C4_C8F0[X]     # 10,11,12,13
    $1924 = 1

    found = $80DA57($1923,$1924)
    if not found:
        skip

    if $192A < 0 or $192A >= 0x15:
        skip

    $1620 = $192A
    $1958 = $192A

    $1E = 0x80
    ok = $8586AC(A=0x3A)
    if ok:
        JMP C4:C357
    else:
        skip

if none:
    JMP C4:C366
```

### 1-1. data table

```text
C4:C8F0 = 10 11 12 13
C4:C8F4 = 01 02 04 08
```

| index | candidate `$1923` | bit `$195E` | 意味候補 |
|---:|---:|---:|---|
| 0 | `0x10` | `0x01` | world/event candidate 0 |
| 1 | `0x11` | `0x02` | world/event candidate 1 |
| 2 | `0x12` | `0x04` | world/event candidate 2 |
| 3 | `0x13` | `0x08` | world/event candidate 3 |

`$195E` は candidate 消費済み/処理済み bitmask と見るのが自然。

---

## 2. C4:C8AA の命令単位

| address | asm | 意味 |
|---|---|---|
| `C4:C8AA` | `LDX #$00` | candidate index 初期化 |
| `C4:C8AC` | `LDA $195E` | 処理済みbitmask |
| `C4:C8AF` | `AND $84:C8F4,X` | candidate bit を検査 |
| `C4:C8B3` | `BNE C4:C8E8` | 既処理なら次へ |
| `C4:C8B5` | `LDA $84:C8F0,X` | candidate `0x10..0x13` |
| `C4:C8B9` | `STA $1923` | candidate key |
| `C4:C8BC` | `LDA #$01` | subkey/type |
| `C4:C8BE` | `STA $1924` | subkey/type = 1 |
| `C4:C8C1` | `JSL $80:DA57` | candidate pair を実entityへ解決 |
| `C4:C8C5` | `BCS C4:C8CA` | 見つかったら続行 |
| `C4:C8C7` | `JMP C4:C8E8` | 見つからなければ次へ |
| `C4:C8CA` | `LDA $192A` | 解決後entity ID |
| `C4:C8CD` | `BMI C4:C8E8` | 負値なら却下 |
| `C4:C8CF` | `CMP #$15` | `0x15` 未満チェック |
| `C4:C8D1` | `BCS C4:C8E8` | `>=0x15` なら却下 |
| `C4:C8D3` | `STA $1620` | current entity |
| `C4:C8D6` | `STA $1958` | feeder output |
| `C4:C8D9` | `LDA #$80` | flag mask |
| `C4:C8DB` | `STA $1E` | `$8586AC` の引数 |
| `C4:C8DD` | `LDA #$3A` | condition id |
| `C4:C8DF` | `JSL $85:86AC` | condition evaluator |
| `C4:C8E3` | `BCC C4:C8E8` | 条件NGなら次へ |
| `C4:C8E5` | `JMP C4:C357` | 条件OKなら成功出口 |
| `C4:C8E8` | `INX` | 次candidate |
| `C4:C8E9` | `CPX #$04` | 4本走査 |
| `C4:C8EB` | `BCC C4:C8AA/C8AC相当` | loop |
| `C4:C8ED` | `JMP C4:C366` | 失敗出口 |

---

## 3. $80DA57 の意味

`$80DA57` = flat `C0:DA57` は、`$1923/$1924` の pair を受け取り、対応する entity / actor / fallback slot を探す resolver。

入力:

| WRAM | 内容 |
|---|---|
| `$1923` | candidate key。C4:C8AAでは `0x10..0x13` |
| `$1924` | subkey/type。C4:C8AAでは `0x01` |

出力:

| WRAM / flag | 内容 |
|---|---|
| Carry set | pair が見つかった |
| Carry clear | 見つからなかった |
| `$192A` | 解決された entity/actor ID |
| `$192B` | 対応行index / fallback index |
| `$1620` | 一時的に切り替えるが、最後に復元 |

探索順:

1. `$81:D5E4` の special check  
2. active logical object `$1569[0..3]` の通常actor `<0x17`
3. actor ID `1..0x15`
4. actor ID `0x81..0x95` 相当の派生/alternate check
5. fallback table `$7E:4472 / $7E:4492` 32本

### 3-1. C0:DADF の下請け

`C0:DADF` は、`$192A` を指定して、そのactor/entityが持つ parallel table に `$1923/$1924` pair があるかを見る。

重要なポインタ:

```text
$2A = $7E:406D + (($192A - 1) * 0x10)
$2D = $2A + 0x0150
$30 = $2D + 0x0150
$1927 = 8
```

つまり、`$80DA57` は **candidate key/subkey を実entity IDへ解決する関係表検索器** と見てよい。

---

## 4. $8586AC(A=0x3A) の意味

`$8586AC` = flat `C5:86AC` は汎用 condition evaluator。

Aに condition id を渡し、dispatch table でhandlerへ飛ぶ。

`A=0x3A` の場合:

```text
A=0x3A
DEC A -> 0x39
ASL -> index 0x72
jump table -> C5:8952
```

### 4-1. C5:8952 handler

```asm
C5:8952  LDX #$01E7
C5:8955  JSR $89E2
C5:8958  LDA $1623,X
C5:895B  BIT $1E
C5:895D  BEQ carry_set
C5:895F  CLC
C5:8960  BRA end
C5:8962  SEC
C5:8963  RTS
```

`C5:89E2` は `X = base + ($1620 - 1)` に変換する helper。

したがって、`A=0x3A, $1E=0x80` は、

```text
target = $1623 + 0x01E7 + ($1620 - 1)
       = $180A + ($1620 - 1)

if target & 0x80 == 0:
    Carry set
else:
    Carry clear
```

### 4-2. 意味

C4:C8AAでは `BCC` なら候補を捨てるため、

```text
$180A[entity-1] の bit7 が clear のときだけ candidate 採用
```

という条件になる。

`$8586AC(A=0x3A)` は、candidate entity の **bit7未設定チェック / event flag clear check / availability check** と見てよい。

---

## 5. C4:C8AA の最終仕様

```text
未処理candidate 0x10..0x13を順番に見る
  ↓
candidate pair ($1923=candidate, $1924=1) を $80DA57 で実entityへ解決
  ↓
解決entityが 0x00..0x14 の範囲なら採用候補
  ↓
$180A[entity-1] bit7 が clear ならOK
  ↓
$1958 = entity
  ↓
成功出口 C4:C357
```

これは、`$1569` へ直接入れるscanではなく、`$1958` に「次にspawn/addすべきentity候補」を置く feeder。

後続で `C4:C85D -> C1:944B -> C1:9474` が走ると、`$1958` が logical object list `$1569` に投入される。

---

## 6. Goal 13への反映

今回で、NPC大量表示軽減の前段がさらに明確になった。

```text
candidate 0x10..0x13 4本だけ走査
  ↓
$195E bitmaskで既処理candidateを除外
  ↓
$80DA57で実entityに解決できないものを除外
  ↓
entity ID 0x15以上を除外
  ↓
$180A bit7が立っているentityを除外
  ↓
$1958へ投入
  ↓
C1:9474で通常actor最大4体へcap
  ↓
OAM builderでさらにpiece clip
```

つまり、新桃のNPC大量表示軽減は、

1. candidate scan段階で候補を4本に限定  
2. 処理済みbitmaskで重複/再処理を抑制  
3. relation resolverで存在しないentityを捨てる  
4. per-entity flag bitで表示不可を捨てる  
5. logical listで通常actor最大4体にcap  
6. OAM段でobject/pieceをさらに捨てる  

という多段構造。

---

## 7. 進捗更新案

| Goal | 旧 | 新 | 理由 |
|---:|---:|---:|---|
| 13. NPC大量表示時の処理軽減ロジック | 92% | 95% | candidate feeder、resolver、per-entity bit7 check まで接続 |
| 8. 条件分岐ディスパッチ系 | 80% | 81% | `$8586AC` の condition id 0x3A handler を確定寄りに整理 |
| 12. 全体構造の人間可読化 | 99% | 99% | 表示前段の説明がさらに補強 |

---

## 8. 次に攻めるべき箇所

1. `$195E` をセット/クリアするcallerを列挙する  
   - candidate `0x10..0x13` の消費済み管理を確定する

2. `$180A + entity` の bit7 をセット/クリアするcallerを列挙する  
   - `A=0x3A` 条件の実ラベルを確定する

3. `$1923/$1924` pair table `$7E:406D / $7E:41BD` のproducerを追う  
   - candidate key `0x10..0x13` がどのイベント/NPC定義由来かを確定する

4. `C4:C357 / C4:C366` の成功/失敗出口を仕様化する  
   - `C4:C8AA` がscript opcode上で何を返すかを確定する
