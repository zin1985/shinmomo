# 新桃太郎伝説 `$1569` 上流追跡メモ  
## C1:9474 へIDを投入する world/NPC scan・script/event 経路（2026-04-25）

## 目的

前回までに、表示負荷軽減の後段は以下までつながった。

```text
$1569 logical object list
 -> $1591 main object handle
 -> $0B27 group/attr/skip
 -> $0E27 animation state
 -> $0AE7 current frame
 -> $0BA7/$0C67 object座標
 -> OAM builder
 -> piece clip / OAM skip / DMA
```

今回は `$1569` をセットする上流、特に **どの world/NPC scan が `C1:9474` にIDを投入するか** を静的に追跡した。

---

## 1. 最大の結論

`C1:9474` は **world/NPC scan本体ではなく、logical object list `$1569` への投入器**。

直接callerは2箇所だけ。

```text
C1:944C  JSR $9474
C1:9467  JSR $9474
```

どちらも `C1:944B` の内部である。

つまり、実際の投入経路は以下。

```text
script/event/world側の候補ID
  ↓
C1:944B  logical object add wrapper
  ↓
C1:9474  $1569 insertion core
  ↓
C1:8F40 / C1:900A  object rebuild + group/attr refresh
```

---

## 2. `C1:9474` の役割

`C1:9474` は、Aレジスタに渡された entity/logical object ID を `$1569[0..9]` に挿入する。

### 2-1. 重要な制限

`C1:9474` には、表示負荷軽減に直結する強い制限がある。

| ID範囲 | 挿入可能slot | 意味候補 |
|---|---|---|
| `< 0x17` | `$1569[0..3]` のみ | 通常NPC / party actor / main visible actor |
| `>= 0x17` | `$1569[0..9]` | special object / companion / effect / temporary actor |

通常IDは4本までしか入らない。  
これは **NPC大量表示軽減の前段 cap** と見てよい。

```text
通常actorは最大4体
特殊/effect込みで全体最大10slot
```

### 2-2. 重複抑制

既に同じIDが `$1569` に存在する場合は、再挿入せず成功扱いで抜ける。

```text
if id already in $1569:
    do not duplicate
```

### 2-3. 特殊ID押し出し・挿入

通常ID `<0x17` を入れたい位置に特殊ID `>=0x17` がある場合、  
slot 0..3 の範囲なら `C1:94BB` で後ろへずらして挿入する。

---

## 3. `C1:944B` の役割

`C1:944B` は `C1:9474` の上位wrapper。

主な処理は以下。

1. 渡されたIDを `C1:9474` へ投入
2. 固定表 `C1:9471 = 17 18 19` を走査
3. `17/18/19` が既にlistに存在する場合、一度 `C1:94D7` で消してから `C1:9474` で再投入
4. 特殊ID `17/18/19` の表示順・後方配置を整える

つまり `C1:944B` は単なるaddではなく、**通常ID投入後に特殊ID 17/18/19 の順序を再正規化する wrapper**。

---

## 4. `C1:94D7` と `C1:94FF`

### `C1:94D7`
指定IDを `$1569` から削除し、後続slotを詰める。

```text
find id in $1569
 -> cleanup current object via C1:8FAC
 -> C1:94FF で後続slotを左へ詰める
```

### `C1:94FF`
logical slot transfer。

`$1569` だけでなく、以下もまとめて移管する。

- `$15B9`
- `$159B`
- `$15A5`
- `$15AF`
- `$1591`
- `$0D27/$0D67/$0DA7/$0DE7`
- `$0B27`
- `$0E27/$0EA7/$0E67/$0AE7`

これにより、slot compact時にも animation state / current frame が維持される。

---

## 5. `C1:944B` へ入る上流

### add系 caller

| caller | input source | 内容 | 種別 |
|---|---|---|---|
| `C4:8C97` | script pointer `($0F)` → `$1929` | IDをpresence bitへ登録し、logical objectとしてspawn | script command |
| `C4:8D0F` | script引数 / `$07` | IDをpresence bitへ登録し、spawn | script command |
| `C4:8D8D` | `$07` | presence bit更新なしでspawn | script command |
| `C4:C85D` | `$1958` | current candidate IDをspawn | world/event candidate command |
| `C5:C9F6` | `$1929` | replacement/scene transition後にspawn | event transition |
| `C1:95C6` | `$7E3F93,X` snapshot | 保存済みlistから復元spawn | list restore |

### remove系 caller

| caller | input source | 内容 |
|---|---|---|
| `C4:8CEB` | `$07` | presence bit clear + despawn |
| `C4:8D16` | `$07` | despawn |
| `C4:8D20` | `($0F)` | despawn |
| `C4:C867` | `$1958` | current candidate despawn |
| `C5:C9ED` | `$0356[0]` | transition前のremove |
| `C1:95D8` | `$1569[9..0]` | bulk clear |

---

## 6. world/NPC scan候補

今回の静的解析では、`C1:9474` に直接入る「world/NPC scan」は見つからない。

代わりに、scan候補は **候補IDを `$1958` に入れ、後続の `C4:C85D` が `C1:944B` を呼ぶ** 形になっている。

### 6-1. `C4:C8AA` candidate scan

`C4:C8AA..C4:C8ED` は、かなり強い world/event candidate scan 候補。

```text
candidate table:
  C4:C8F0 = 10 11 12 13

bit table:
  C4:C8F4 = 01 02 04 08
```

処理概要:

```text
for candidate in [0x10,0x11,0x12,0x13]:
    if candidate bit already set in $195E:
        skip
    $1923 = candidate
    $1924 = 1
    call $80DA57
    if candidate accepted and $192A < 0x15:
        $1620 = $192A
        $1958 = $192A
        call $8586AC with A=0x3A, $1E=0x80
        if success:
            command success
```

これは直接 `$1569` に書かない。  
しかし、`$1958` を feeder とするため、後続で `C4:C85D` が走ると、

```text
C4:C8AA scan -> $1958
C4:C85D -> JSL $81944B
C1:944B -> C1:9474
```

となる。

### 6-2. `C5:C9DF` transition feeder

`C5:C9DF` は `$0356[$12E4]` を `$1958` に入れる。

`$0356` は直前の `C5:C954..C5:C97D` で `$1569[1..3]` から作られる一時list。

```text
$1569[1..3] の通常actor
 -> $0356[1..3]
 -> $0356[$12E4]
 -> $1958
 -> remove old / add new
```

これは world scan というより、**party/actor transition feeder** に近い。

---

## 7. `$1569` 直接書込

`$1569` へ直接書く箇所は少ない。

| address | 内容 | 評価 |
|---|---|---|
| `C0:CB0A` | `$1569[0] = 1` | 初期化。桃太郎/leader初期slotの可能性 |
| `C0:CB0F` | `$1569[1..9] = 0` | 初期化 |
| `C1:94AE` | insertion core | 本命 |
| `C1:9504/9509` | slot transfer | compact/shift |
| `C5:CFA3 / C5:D008` | 一時描画処理内で保存/復帰 | 本線ではない |

`C5:CFA3` は `$1569` を一時的に差し替えて、actor表示資材ルーチンを再利用し、最後に元へ戻す処理。  
したがって logical list の恒久更新ではない。

---

## 8. Goal 13への意味

今回の解析で、NPC大量表示軽減は前段でもかなり強い構造が見えた。

```text
1. 通常actor ID < 0x17 は slot0..3 に制限
2. 全logical objectは slot0..9 に制限
3. 重複IDは追加しない
4. 特殊ID 17/18/19 は add wrapper で順序再正規化
5. slot削除時はcompactし、animation stateも維持
6. OAM側ではさらに object単位skip / piece単位clip / OAM枠チェック
```

つまり新桃のNPC大量表示軽減は、後段だけではなく、

```text
logical list投入時点で数を絞る
 -> object handle数を絞る
 -> OAM出力時にさらに落とす
```

という二段構造。

---

## 9. 更新進捗

| Goal | 旧 | 新 | 理由 |
|---:|---:|---:|---|
| 13. NPC大量表示時の処理軽減ロジック | 86% | 92% | `$1569`投入cap、通常actor最大4、全体10slot、world/event候補feederが見えた |
| 12. 新桃全体の構造を人間が読める形で再構成する | 99% | 99% | object管理層の説明が完成に近い |
| 11. 外部データ化 | 98% | 98% | caller表・slot仕様表を外部化 |

---

## 10. 次に攻めるべき箇所

1. `C4:C8AA` の `$80DA57` と `$8586AC(A=0x3A)` の意味を確定する  
   - candidate `0x10..0x13` が何を表すか
   - `$192A` が最終的にどのactor/entity IDになるか

2. `$1958` の producer/consumer表を作る  
   - world/event candidate
   - party transition
   - current target selection
   を分離する

3. `C1:9474` の `<0x17` / `>=0x17` のID辞書を作る  
   - 0x01 leader/桃太郎
   - 0x10..0x13 candidate group
   - 0x17..0x19 special logical object
   までのラベル付け

4. `C4:8C85/8CFE/8D8B` がscript opcode何番かを確定する  
   - spawn/despawn commandの仕様書へ反映する
