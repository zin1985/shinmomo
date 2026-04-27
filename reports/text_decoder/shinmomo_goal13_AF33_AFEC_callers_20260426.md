# 新桃太郎伝説 Goal 13: `C0:AF33` / `C0:AFEC` caller列挙
作成日: 2026-04-26

## 1. 結論

`C0:AF33` と `C0:AFEC` は、実ROM上では主に **mirror bank `$80` への JSL** として呼ばれている。

```text
C0:AF33  = $80:AF33  object allocate + sorted insert
C0:AFEC  = $80:AFEC  existing object reorder / sort-key update
```

直接検索結果:

| target | direct JSR | JSL `$80:xxxx` | JSL `$C0:xxxx` |
|---|---:|---:|---:|
| `AF33` | 0 | 27 | 0 |
| `AFEC` | 0 | 5 | 0 |

`4C 33 AF` が `CF:C625` に1件あるが、これは現時点では code caller ではなく、data / false positive 扱いにする。

---

## 2. `C0:AF33` caller一覧

`C0:AF33` は **新規object slotを確保して、`$0AA3` sort key順に `$0A61/$0A1F` linked listへ挿入する入口**。

特に、Aレジスタが sort key / priority / depth key として渡される。

| caller | sort key source | post-call | 分類 |
|---|---|---|---|
| `C1:8E7F` | immediate #$38 | STA $1591,X | logical actor -> visible object allocation |
| `C1:917E` | A = X + #$50 when $1619 != 0 | STA $159B,X | actor-index dependent allocation |
| `C1:9258` | immediate #$2E | STA $15AF,X | event/object allocation |
| `C1:92D4` | immediate #$40 | STA $15A5,X | event/object allocation |
| `C1:93FE` | immediate #$20 | STA $15C9 | single event/display object allocation |
| `C1:AE04` | immediate #$38 | handle used immediately | effect/object allocation |
| `C1:B583` | immediate #$48 | STA $18D3,X | pooled effect/object allocation |
| `C1:B99C` | immediate #$48 | STA $1913,X | pooled effect/object allocation |
| `C1:E3A8` | immediate #$20 | STA $05D9,X | low-priority effect/object allocation |
| `C1:F459` | immediate #$08 | STA $1F9F | UI/facility/cursor-ish allocation |
| `C2:DB8A` | immediate #$3A | STA $05D9,X | effect/object allocation |
| `C2:DF96` | immediate #$28 | STA $0619,X candidate | effect/object allocation |
| `C2:DFCC` | immediate #$28 | STA $0619,X candidate | effect/object allocation |
| `C2:E0F4` | A = [$E2],Y stream/table byte | STA $0619,X candidate | data-driven effect/object allocation |
| `C2:FA23` | immediate #$28 | branch on carry | effect/object allocation |
| `C3:9259` | A = ($92) indirect stream/table byte | branch on carry | data-driven object allocation |
| `C5:9850` | immediate #$48 | STA long work candidate | event/object allocation |
| `C5:CC9A` | immediate #$20 | TAY then init work | object/effect allocation |
| `C5:CF9A` | immediate #$38 | TAY then restore/setup | object/effect allocation |
| `C5:D4AB` | immediate #$20 | TAY then setup | object/effect allocation |
| `C5:DC10` | A = long table $85:DC32,X | TAY then setup | data-driven object allocation |
| `C6:8798` | immediate #$0B | STA $05D9,X | low-priority effect/object allocation |
| `C6:8831` | immediate #$28 | STA $0619,X candidate | effect/object allocation |
| `C6:8A61` | immediate #$28 | STA $0619,X candidate | effect/object allocation |
| `C6:8EB1` | immediate #$38 | STA $0619,X candidate | effect/object allocation |
| `C6:9D9D` | immediate #$38 | STA $0619,X candidate | effect/object allocation |
| `C6:A00A` | immediate #$2C | branch on carry | effect/object allocation |

### 2-1. sort key帯の見え方

immediate keyだけで見ると、以下の優先度帯がある。

| sort key | 主なcaller | 見立て |
|---:|---|---|
| `0x08` | `C1:F459` | UI/facility/cursor寄りの低い帯 |
| `0x0B` | `C6:8798` | 低優先度effect/object |
| `0x20` | `C1:93FE`, `C1:E3A8`, `C5:CC9A`, `C5:D4AB` | 低〜中優先度object |
| `0x28` | `C2:DF96`, `C2:DFCC`, `C2:FA23`, `C6:8831`, `C6:8A61` | effect/object標準帯その1 |
| `0x2C` | `C6:A00A` | 0x28と0x38の中間帯 |
| `0x2E` | `C1:9258` | event object専用帯候補 |
| `0x38` | `C1:8E7F`, `C1:AE04`, `C5:CF9A`, `C6:8EB1`, `C6:9D9D` | 人物/scene object帯候補 |
| `0x3A` | `C2:DB8A` | 0x38近傍のeffect/object |
| `0x40` | `C1:92D4` | 人物/scene objectのやや奥/手前帯候補 |
| `0x48` | `C1:B583`, `C1:B99C`, `C5:9850` | 高優先度/前面寄りobject帯候補 |
| `0x50 + X` | `C1:917E` | indexed actor/object帯 |
| data-driven | `C2:E0F4`, `C3:9259`, `C5:DC10` | table/streamがsort keyを決める |

この時点で、`$0AA3` は単純なY座標だけではなく、**深度/優先度/描画帯を混ぜたsort key** と見るのが安全。

---

## 3. `C0:AFEC` caller一覧

`C0:AFEC` は **既存objectのsort keyを更新して、linked list上で並べ替える入口**。

| caller | new sort key source | slot source | 分類 |
|---|---|---|---|
| `C1:90ED` | A = clamp($157D - $15E9,X + #$38, #$38..#$48) | STY $6A before call | main depth/Y-sort reorder |
| `C1:BD37` | immediate #$2C | STY $6A before call | fixed-priority reorder |
| `C3:9B96` | A = ($94) stream/table byte | implicit current $6A | data-driven reorder command |
| `C3:F1B2` | A = table C3:F1CB,X | implicit current $6A | table-driven cutscene/object reorder |
| `C5:E8EF` | A = long table $85:E8F8,X | implicit/current $6A | table-driven reorder |

### 3-1. 最重要caller: `C1:90ED`

`C1:90ED` は今回のNPCログと最も強くつながるcaller。

周辺は概ね以下。

```asm
LDA $157D
SEC
SBC $15E9,X
CLC
ADC #$38
CMP #$30
BCS ok_low
LDA #$38
CMP #$40
BCC ok_high
LDA #$48
STY $6A
JSL $80:AFEC
```

意味は、

```text
new_sort_key = clamp($157D - $15E9,X + 0x38, 0x38..0x48)
```

に近い。

これは **Y座標/相対縦位置から描画順sort keyを作り、移動中objectをactive chain内で並べ替える処理** と見てよい。

はじまりの村ログで `active_chain` が移動中に揺れていた理由は、このcallerが走っているためと見るのが自然。

---

## 4. Goal 13への反映

今回で、NPC大量表示軽減のうち「active linked listの生成・並べ替え」がかなり固まった。

```text
C0:AF33
  new objectを確保
  Aのsort keyで$0AA3順にinsert

C0:AFEC
  既存objectのsort keyを更新
  $0A61/$0A1F linked listを並べ替え

C0:B03D
  $0A61 head.nextからchain walk
  slot>=2だけOAM buildへ渡す

C0:B100
  B294 sprite group/frameからOAM mirrorへpiece出力
```

これにより、Goal 13は **98%据え置き**。

上げない理由:

- caller一覧は取れたが、各callerのゲーム内ラベルは未確定
- `$0AA3` sort keyが「Y座標だけ」か「優先度帯 + Y補正」かを100%までは言い切れない
- `C1:90ED` はかなり本命だが、全移動NPCがここを通るかはruntime確認が必要

---

## 5. 次に攻めるべき箇所

1. `C1:90ED` 周辺を命令単位で完全分解  
   - `$157D`, `$15E9,X`, `$6A` の意味を確定する
2. `C0:AF33` callerの post-call handle保存先を分類  
   - `$1591/$159B/$15AF/$15A5/$05D9/$0619/...` が何のobject poolか整理
3. `C0:B100` とB294 tableを接続  
   - `b25=22/23`, `ae5=07/08/22/23/...` がどのframe/pieceへ落ちるか確認
4. compact v2 Luaで `active_chain` と `visible_slots` を数場面採取  
   - sort key帯のゲーム内意味をラベル化する

---

## 6. データ成果物

- `shinmomo_AF33_callers_20260426.csv`
- `shinmomo_AFEC_callers_20260426.csv`
