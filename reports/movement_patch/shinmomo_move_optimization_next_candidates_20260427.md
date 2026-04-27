# 新桃太郎伝説 移動/表示処理 最適化 次候補メモ

## 結論

v2の次に処理アップへ貢献しそうな候補はまだある。  
ただし、v2より先は **描画/OAM/通行判定に近づくためリスクが上がる**。

現時点の優先順位は以下。

1. OAM/object static-frame skip
2. offscreen object早期skip強化
3. animation unchanged skip
4. inactive actor slot full skip
5. collision/probe frequency削減

このうち、すぐIPS化してよいのはまだ少ない。  
次は効果測定Luaで「本当に削れる余地があるか」を見るのが安全。

---

## 1. OAM/object static-frame skip

### 狙い

座標、sprite group、animation frame、flagsが前フレームと同じobjectは、OAM構築を再実行しなくてもよい可能性がある。

### 見るWRAM

```text
$0BA7/$0BE7 = screen X
$0C67/$0CA7 = screen Y
$0AE5       = animation frame / pattern
$0B25       = sprite group / flags
```

### リスク

SFCのOAMは毎フレーム再構築前提のことが多い。  
不用意にskipすると、消え残り、ちらつき、優先順位崩れが起きる可能性がある。

### 状態

まだパッチ化しない。  
`object_static_slots` が多いかを測る。

---

## 2. offscreen object早期skip強化

### 狙い

画面外objectをpiece loop前に落とす。

### リスク

画面端、影、上下半身piece、登場/退場演出で欠ける可能性。

### 状態

C0:B03D/B100の完全分解後なら候補。

---

## 3. animation unchanged skip

### 狙い

`$0AE5` が変わっていない待機NPCのanimation処理を軽くする。

### リスク

足踏み/瞬き/イベント演出が止まる可能性。

---

## 4. inactive actor slot full skip

### 狙い

`$1569,X == 0` や `$180A bit7 hidden` のactorについて、visible object更新をもっと早く抜ける。

### リスク

非表示でも内部タイマーやイベント判定が進んでいる可能性がある。

---

## 5. collision/probe frequency削減

### 狙い

`C1:9EAD` の6連probeを減らす。

### リスク

高い。NPCすり抜け、イベント衝突、不正移動につながる。

現時点ではパッチ非推奨。

---

## 効果測定Lua

`shinmomo_move_opt_profile_v2_snes9x_20260427.lua` を通常ROMで走らせる。

見る値:

```text
projection_skip_slots
depth_same_key_slots
object_static_slots
object_draw_skip_slots
offscreen_like_slots
```

目安:

- `object_static_slots` が高い → OAM/object static skipに価値あり
- `offscreen_like_slots` が高い → offscreen早期skipに価値あり
- `actor_empty_slots` が高い → inactive actor skipに価値あり
- `depth_same_key_slots` が高い → v2 depth patchに価値あり

---

## 次の判断

v2 IPSを当てる前に、まず通常ROMで profile_v2 を取り、  
NPCが多い場面、銀次加入後、月の神殿でログを比較するのが安全。
