# 新桃太郎伝説 C1:8Fxx..95xx object spawn / clone / state transfer 仕様化メモ（2026-04-25）

## 目的

前回までに、表示負荷軽減の後段は次のようにつながった。

```text
$0E27 animation state
 -> $0EA7 animation cursor
 -> $0AE7 current frame
 -> B294 sprite frame definition
 -> $0BA7/$0C67 object座標
 -> OAM piece clipping
 -> OAM DMA
```

今回はその前段である `C1:8Fxx..95xx` を、**logical object の spawn / despawn / clone / state transfer 管理層** として仕様化した。

> 表記注意: raw `0x019xxx` 領域は、過去メモに合わせて `C1:xxxx` と表記する。  
> コード内の `JSL $81:xxxx` は同一物理ROMのミラー参照として現れる箇所があるため、ここでは機能名を優先して整理する。

---

## 1. 結論

`C1:8Fxx..95xx` は、OAM builder そのものではなく、**OAM builder に渡す前の object 管理層**。

大きくは次の4層に分かれる。

```text
logical object list
  $1569[0..9]
      ↓
main object handle
  $1591[slot]
      ↓
auxiliary / clone object handles
  $159B / $15AF / $15A5 / $15C9
      ↓
object work
  $0B27, $0BA7/$0C67, $0CE7, $0E27/$0EA7/$0E67/$0AE7
      ↓
OAM builder
```

今回の仕様化で、NPC大量表示軽減に関して以下が前段から後段までつながった。

```text
spawn/despawn
 -> logical slot compact
 -> main/aux object handle allocation
 -> state/group/anchor/coords transfer
 -> draw skip bit control
 -> OAM piece clipping
 -> OAM DMA
```

---

## 2. 主要work field

| field | 役割 | メモ |
|---|---|---|
| `$1569,X` | logical object/entity id | 10本の論理slot。`0` は空き。 |
| `$1591,X` | main object handle | object work 側の本体handle。 |
| `$15B9,X` | base animation state / state seed | `C1:8F00` や `C1:9090` で `$0E27` へつながる。 |
| `$159B,X` | auxiliary handle A | `$1619` 条件で出る mirror/companion 系。 |
| `$15AF,X` | auxiliary handle B | `$1834[id-1]` 条件で出る補助object。 |
| `$15A5,X` | auxiliary handle C | `$155C` 条件で出る補助object。 |
| `$15C9` | global companion handle | semantic state `0x0C` 用の特殊clone。 |
| `$0B27,obj` | sprite group / attr / draw skip | lower4bit=group、`0x30`=attr overlay、`0x40`=draw skip。 |
| `$0BA7/$0BE7` | object X coordinate | OAM builderが読むX座標。 |
| `$0C67/$0CA7` | object Y coordinate | OAM builderが読むY座標。 |
| `$0CE7` | vertical anchor / pivot | sprite piece Y offset から引かれる基準点。 |
| `$0E27` | animation state number | B2C1 animation script state index。 |
| `$0EA7` | animation script cursor | `[frame,duration]` script内の読み位置。 |
| `$0E67` | duration / wait counter | 次frameまでの残り時間。 |
| `$0AE7` | current frame / pattern | B294 sprite frame definitionへ渡るframe番号。 |
| `$0D27/$0D67/$0DA7/$0DE7` | resource / asset handle系 | clone時にコピー、cleanup時に一部を `FF` 化。 |

---

## 3. routine 仕様表

詳細CSV: `shinmomo_C1_8Fxx_95xx_object_manager_routines_20260425.csv`

| 範囲 | 役割 | 要点 |
|---|---|---|
| `C1:8F15..8F38` | all logical object refresh | `$1569[0..9]` を2pass走査。旧補助object掃除後に本体/補助を再構築。 |
| `C1:8F40..8FAB` | main object rebuild/update | 本体objectのsemantic state、group/attr、clone、補助objectをまとめて更新。 |
| `C1:8FAC..8FF6` | logical object cleanup | `$159B/$15A5/$15AF` と資源handleを解放。 |
| `C1:900A..9030` | main object group/attr refresh | `913D -> 81:B445/B477 -> $0B27`。 |
| `C1:9031..908F` | conditional state/visibility update | state=0、draw skip bit、dynamic state更新を制御。 |
| `C1:9090..90CD` | dynamic animation state calculator | direction/state seed + base stateを合成し、差分があれば `AE79`。 |
| `C1:90F7..910A` | bulk anchor initializer | 全main objectに `$0CE7=0x10`。 |
| `C1:913D..9174` | semantic actor id -> base state | `$1569,X` をイベント状態に応じて `0x1A/0x2D/0x24/0x0E` 等へ置換。 |
| `C1:9186..91E2` | `$159B` clone/mirror update | 親から座標/資源をコピーし、stateを+4派生または0へ。anchorは反転。 |
| `C1:91E3..9201` | copy position + anchor | `$0BA7/$0BE7/$0C67/$0CA7/$0CE7` をコピー。 |
| `C1:9202..920E` | copy animation cursor/wait | `$0E67/$0EA7` をコピー。 |
| `C1:920F..9227` | copy resource fields | `$0D27/$0D67/$0DA7/$0DE7` をコピー。 |
| `C1:9228..923D` | clone visibility from parent | 親stateが0なら子objectへ draw skip bit `0x40`。 |
| `C1:923E..9295` | spawn `$15AF` auxiliary | 条件付き補助object生成。stateは `1/3/4`。 |
| `C1:9296..92BA` | refresh `$15AF` auxiliary | 親attr/coordsをコピーし、親state 0なら非表示。 |
| `C1:92BB..9302` | spawn `$15A5` auxiliary | state=2の補助object。親anchorを0へ。 |
| `C1:9303..934E` | refresh `$15A5` auxiliary | anchor oscillation tableで縦基準を揺らす。 |
| `C1:9357..938B` | bulk world->screen coordinate update | world座標をobject座標へ投影。 |
| `C1:938C..93AC` | project coords into object work | `$030B/$030D/$030C/$030E` を `$0BA7/$0C67/$0BE7/$0CA7` へ。 |
| `C1:93D2..93F4` | bulk `$0B27` rebuild | 全objectのsprite group/attrを再計算。 |
| `C1:9419..944A` | refresh global companion `$15C9` | semantic state `0x0C` 用clone。親state+4、attr overlay `0x30`。 |
| `C1:9474..94BA` | ensure logical entity id | `$1569` listへIDをspawn。空きslotまたはcompact後に `8F40+900A`。 |
| `C1:94D7..94FE` | remove logical entity id | despawnして後続slotを詰める。 |
| `C1:94FF..958B` | logical slot transfer and object state migration | logical slot移動の本丸。animation state/cursor/duration/current frameまで完全移管。 |
| `C1:959F..95E0` | snapshot / restore / bulk remove | `$1569` listの退避・復元・全削除。 |

---

## 4. spawn / despawn / compact の流れ

### spawn

`C1:9474..94BA` が本命。

```text
input id
 -> 81:A91D で正規化
 -> $1569[0..9] を走査
 -> 既存なら何もしない
 -> 空きslotへ格納
 -> C1:8F40 でobject work再構築
 -> C1:900A でgroup/attr更新
```

低ID、つまり通常party/NPCに近いものは前方slot制限があり、`id < 0x17` は主に前4slotへ寄せる処理がある。  
`id >= 0x17` は後方slotまで許可される。

### despawn

`C1:94D7..94FE` が本命。

```text
input id
 -> $1569 listから一致slotを探す
 -> C1:8FAC で補助object/資源をcleanup
 -> 後続slotを C1:94FF で左詰め
```

### compact / transfer

`C1:94FF..958B` が本丸。

logical slot側:

```text
$1569
$15B9
$159B
$15A5
$15AF
```

object work側:

```text
$0B27
$0D27/$0D67/$0DA7/$0DE7
$0E27/$0EA7/$0E67/$0AE7
```

を移管する。

特に重要なのはここ。

```asm
C1:9561  LDA $0E27,Y
C1:9564  STA $0E27,X
C1:9567  LDA $0EA7,Y
C1:956A  STA $0EA7,X
C1:956D  LDA $0E67,Y
C1:9570  STA $0E67,X
C1:9573  LDA $0AE7,Y
C1:9576  STA $0AE7,X
```

これは **animation stateの完全移管**。  
単にIDを動かしているのではなく、再生中のアニメ位置まで保ったままslotを詰めている。

---

## 5. clone / auxiliary object の構造

### `$159B` clone

`C1:9186..91E2`

- 条件: `$1619 != 0` で `C1:9175` がhandle確保
- 親から座標・duration/cursor・資源をコピー
- 親stateが有効なら `state + 4`
- anchor `$0CE7` は符号反転
- `$0B27` は親group lower4bitを継承し、frame counterにより `0x40` を混ぜる場合あり

候補役割:

```text
mirror / shadow / companion / overlay
```

### `$15AF` auxiliary

`C1:923E..9295`

- 条件: `$1834[id-1] != 0`
- group/attr: `$0B27 = 0x24`
- state:
  - semantic state `0x0C` -> `4`
  - semantic state `0x0B` or `0x09` -> `3`
  - otherwise -> `1`

### `$15A5` auxiliary

`C1:92BB..934E`

- 条件: `$155C != 0` and semantic state != `0x19`
- group/attr: `$0B27 = 0x24`
- state: `2`
- parent anchorを0へ
- 補助object側のanchorは `C1:934F` tableで周期的に変わる

`C1:934F` table:

```text
04 05 06 07 08 07 06 05
```

### `$15C9` global companion

`C1:93F5..9418` で確保/解放、`C1:9419..944A` で更新。

- semantic state `0x0C` 専用
- 親objectからgroup/coords/cursor/resourceをコピー
- `$0B27 |= 0x30`
- state = parent state + 4

---

## 6. draw skip と表示負荷軽減への接続

C1側でも draw skip bit `0x40` が複数箇所で操作される。

| 箇所 | 操作 | 意味 |
|---|---|---|
| `C1:9058..905D` | `$0B27 |= 0x40` | 条件付きで本体objectを非表示化 |
| `C1:9062..9067` | `$0B27 &= 0xBF` | 本体objectを表示可能へ戻す |
| `C1:9228..923D` | 親stateが0なら子に`0x40` | clone/auxiliaryを親stateに連動して非表示 |
| `C1:91C2..91C9` | group lower4bit + optional `0x40` | `$159B` clone側の表示/非表示・group設定 |

後段の OAM builder では `$0B25/$0B27 bit6` が立つと object単位でOAM出力されない。  
したがってC1側は **OAMに行く前の表示抑制レイヤー** を担っている。

NPC大量表示軽減の前段としてはかなり強い。

```text
logical slotが空なら走査しない
despawn時はslotを詰める
補助objectは親stateが0ならskip
条件付きで本体objectもskip
後段OAM builderでpiece単位clip
```

---

## 7. Goal 13への反映

前回まで:

```text
object state -> animation frame -> sprite definition -> OAM clipping
```

今回追加:

```text
logical object spawn/despawn
 -> slot compact
 -> clone/auxiliary object
 -> state/current frame transfer
 -> pre-OAM draw skip
```

よって Goal 13 は次のように更新してよい。

| Goal | 旧 | 新 |
|---:|---:|---:|
| 13. NPC大量表示時の処理軽減ロジック | 80% | **86%** |
| 11. 外部データ化 | 97% | **98%** |
| 12. 全体構造の人間可読化 | 98% | **99%** |

Goal 13 は、後段だけでなく前段のobject list管理まで見えたため、かなり完成に近づいた。  
残りは「どのlogicが `$1569` にNPCを追加するか」と「画面内NPC候補をどう選別しているか」。

---

## 8. 次に攻めるべき箇所

1. `$1569` をセットする上流をさらに逆引きする  
   `C1:9474` だけでなく、どのworld/NPC scanがここへIDを投入するかを見る。

2. `C1:9357..938C` の座標投影を深掘りする  
   `$1573/$157D` と `$030B/$030D` の関係を詰めると、画面内候補化の前段が見える。

3. `80:AF33 / 80:AFAA` allocator を仕様化する  
   object handleの確保・解放・active list接続の正体を固める。

4. `$1587` flag bit定義を進める  
   `0x10/0x20/0x40/0x08` がC1側でstate/skip/transformに関与している。

---

## 9. 出力ファイル

- `shinmomo_C1_8Fxx_95xx_object_manager_routines_20260425.csv`
- `shinmomo_C1_8Fxx_95xx_object_work_fields_20260425.csv`
- `shinmomo_C1_8Fxx_95xx_key_accesses_20260425.csv`
