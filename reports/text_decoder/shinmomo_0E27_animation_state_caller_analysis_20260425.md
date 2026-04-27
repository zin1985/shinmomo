# 新桃太郎伝説 `$0E27,Y` animation state caller 解析メモ（2026-04-25）

## 目的

前回までに、`C0:B2C1` 系を

```text
animation group -> state -> [frame,duration] script -> $0AE7 current frame -> B294 sprite definition -> OAM
```

として外部化した。

今回は、その **state番号をセットする側** を静的に列挙し、`$0E27,Y` の意味を割り当てる。

---

## 1. 結論

`$0E27,Y` は **animation state number**。

ただし単独では意味が決まらない。  
必ず次の組で読む必要がある。

```text
animation group = $0B27,Y & 0x0F
animation state = $0E27,Y
```

つまり同じ `state=03` でも、group 0 / group 4 / group 5 では参照するscript tableが違う。

---

## 2. setter 系ルーチン

### `80:AE88`

```asm
80:AE88  STA $0E27,Y
80:AE8B  LDA #$00
80:AE8D  STA $0EA7,Y
80:AE90  JSR $AE94
80:AE93  RTL
```

役割:

```text
stateをセット
animation cursor $0EA7 を 0 に戻す
state scriptを先頭から読み直す
```

**状態変更 + アニメ再始動** の入口。

---

### `80:AE79`

```asm
80:AE79  STA $0E27,Y
80:AE7C  LDA $0E67,Y
80:AE7F  PHA
80:AE80  JSR $AE94
80:AE83  PLA
80:AE84  STA $0E67,Y
80:AE87  RTL
```

役割:

```text
stateをセット
ただし duration / wait counter $0E67 は保存して戻す
cursor $0EA7 もクリアしない
```

**再生位置・残り時間を保ったまま、stateだけ差し替える** 入口。  
歩行中の向き差し替え、同じphaseのまま絵柄だけ変える処理に使われる可能性が高い。

---

### `80:AE75`

```asm
80:AE75  STA $0E67,Y
80:AE78  RTL
```

durationだけを外からセットする入口。  
`$0E27` 本体ではないが、animation state制御の補助。

---

## 3. 直接write箇所

ROM全体で `$0E27` へ直接writeする箇所は少ない。

| SNES | 命令 | 役割 |
|---|---|---|
| `C0:AE79` | `STA $0E27,Y` | state変更、cursor維持 |
| `C0:AE88` | `STA $0E27,Y` | state変更、cursor reset |
| `C0:AF7C` | `STZ $0E27,X` | object slot確保時の初期化。新規objectはstate 0から始まる |
| `C1:904E` | `STA $0E27,Y` with `A=00` | 条件付きでstate 0へ落とす。表示/アニメ停止系 |
| `C1:9564` | `LDA $0E27,Y -> STA $0E27,X` | object slot複製/移管時にanimation stateをコピー |
| `C1:9583` | `A=00 -> STA $0E27,Y` | 複製元/旧slot側をstate 0へ落とす |

### 重要

`C1:9564..9586` は、stateだけでなく以下をまとめてコピーしている。

```asm
$0E27  state
$0EA7  cursor
$0E67  duration
$0AE7  current frame
```

したがってここは **object animation stateの完全移管処理** と見てよい。

---

## 4. caller数

| callee | 件数 | 意味 |
|---|---:|---|
| `JSL $80:AE88` | 55 | stateをセットしてアニメを先頭から再生 |
| `JSL $80:AE79` | 11 | stateをセットするが、cursor/durationを維持 |
| direct `STA/STZ/COPY` | 4本質箇所 | 初期化・停止・slot移管 |

---

## 5. state 0 の意味

`80:AE94` 内では、`$0E27,Y == 0` の場合、

```asm
$0AE7,Y = 0
$0E67,Y = 0
```

へ落ちる。

よって **state 0 は全group共通で「アニメなし / 表示frameなし / inactive」** と見てよい。

これはかなり確定。

---

## 6. low state の意味候補

`state 1..4` はよく使われるが、意味は group 依存。

例:

| group | state | script | 解釈候補 |
|---:|---:|---|---|
| 4 | 2 | `C1:2FBB frame_seq=10 dur=255` | group4の静止pose |
| 4 | 4 | `C1:2FE1 frame_seq=24,20,21,22,23,26,27,28,27,26,23,25,23,22,21,20` | group4の長いモーション |
| 5 | 3 | `C1:4206 frame_seq=7 dur=255` | group5の静止pose A |
| 5 | 4 | `C1:420A frame_seq=8 dur=255` | group5の静止pose B |
| 8 | 1 | `C2:53C9 frame_seq=5,2,1,6...` | group8の複合ループ/演出初期状態 |

つまり `state=3` や `state=4` を「歩き」などとグローバル名で固定してはいけない。  
**groupごとのstate label** が必要。

---

## 7. high state の意味候補

`state >= 0x40` は、通常歩行というより **イベント専用・演出専用の状態番号** に見える。

代表例:

| caller | group | state | script / 内容 |
|---|---:|---:|---|
| `C1:91CD` | 0 | `0x40` | `C5:28AE frame_seq=121 dur=16` |
| `C5:CCB2` | 0 | `0x71` | `C5:315E frame_seq=191 dur=255` |
| `C5:D4CB` | 0 | `0x72` | `C5:3162 frame_seq=192 dur=255` |
| `C1:B9DA` | 2 | `0xDC` | `C1:1931 frame_seq=98 dur=255` |
| `C1:B9EC` | 2 | `0xDE` | `C1:194D frame_seq=249 dur=255` |
| `C1:E3C1` | 3 | `0x86` | `C1:22FF frame_seq=29,70 dur=16,16` |
| `C5:9874` | 5 | `0x25` | `C1:51DA frame_seq=76 dur=16` |
| `C5:CFC7` | 8 | `0x38` | `C2:55FF frame_seq=61 dur=240` |

この層は、個別scene/イベントごとにラベル化するのがよい。

---

## 8. callerの分類

### A. reset型: `AE88`

- 新規stateへ切り替えて、scriptを先頭から再生する。
- 多くのspawn/init/イベント開始処理がこれを使う。
- immediate stateが多い。
- table/WRAM由来のdynamic stateも存在する。

代表:

| caller | state source | 補足 |
|---|---|---|
| `C1:8F60` | `#00` | state 0、アニメ停止 |
| `C1:9290` | `#01/#03/#04` | 条件でlow state切替 |
| `C1:92F5` | group4 / state2 | group4静止pose |
| `C1:B5CD` | group5 / state4 | group5静止pose B |
| `C1:B5E0` | group5 / state3 | group5静止pose A |
| `C1:B9DA` | group2 / stateDC | イベント/特殊pose |
| `C1:B9EC` | group2 / stateDE | イベント/特殊pose |
| `C5:CCB2` | group0 / state71 | イベント/特殊pose |
| `C5:D4CB` | group0 / state72 | イベント/特殊pose |

### B. preserve型: `AE79`

- stateだけ変える。
- `$0E67` durationを復帰するため、時間経過は途切れない。
- 方向差し替え、バリエーション切替、phase維持に使われる。

代表:

| caller | state source | 補足 |
|---|---|---|
| `C1:9444` | `$0E27,X + 4` | 親/元objectのstateに+4した派生state |
| `C3:EF03` | `$15C7 + 0x38` | base index + offset 系 |
| `C3:EF88` | `$15C7 + 0x18` | base index + offset 系 |
| `C3:EFBF` | `$15C7 + 0x20` | base index + offset 系 |
| `C3:F00F` | `$15C7 + 0x27` | base index + offset 系 |

`$15C7` は、この周辺では **event/effect base animation state** のように働く。

---

## 9. 現時点のstate number割当方針

### 確定

| state | 意味 |
|---:|---|
| 0 | animation off / current frame 0 / duration 0 |

### 確定寄り

| state帯 | 意味 |
|---|---|
| 1..4 | low/common state。ただし意味はgroup依存 |
| `0x40+` | event/special pose stateが多い |
| `0xDC..0xF0` | group2など大型tableの特殊state。scene固有の可能性大 |

### 注意

`state=1` を「idle」、`state=2` を「walk」などと全group共通で命名するのは危険。  
必ず `group:state` 形式で管理する。

例:

```text
anim_g4_s02 = group4 静止pose frame10
anim_g4_s04 = group4 長いモーション
anim_g5_s03 = group5 静止pose A
anim_g5_s04 = group5 静止pose B
```

---

## 10. Goal 13への反映

これで、NPC/obj大量表示軽減の後段は以下まで接続済み。

```text
object slot
  -> active list
  -> $0B27 group
  -> $0E27 animation state
  -> $0EA7 cursor
  -> $0AE7 current frame
  -> B294 sprite frame definition
  -> $0BA7/$0C67 object座標
  -> piece単位clip
  -> OAM出力
```

表示負荷軽減の観点では、

- state 0 なら frame 0 で描画なし
- `$0B25 bit6` でobject単位skip
- OAM残枠不足ならobject単位skip
- piece単位で画面外clip
- active listで巡回対象を限定

まで見えている。

---

## 11. 次に静的で伸ばす場所

1. `C1:8Fxx..95xx` を object spawn / clone / state transfer 管理として仕様化する。
2. `C1:9090 / 913D / 9202 / 920F / 91E3` を追い、low state `1/3/4` の分岐条件を確定する。
3. `$15B9 / $15C7` のproducerを追い、dynamic state sourceを意味付ける。
4. high state `0x5B..0x72` と `0xDC..0xF0` を、scene/イベント単位にラベル化する。
5. `group:state -> script -> frame definition -> OAM piece` の統合CSVを作る。
