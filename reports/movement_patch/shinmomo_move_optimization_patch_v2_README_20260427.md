# 新桃太郎伝説 移動/表示更新処理 最適化実験パッチ v2

## v1からの改善点

v1は「呼び出しても即returnする処理を飛ばす」方向でした。  
v2ではさらに静的解析を進め、以下を追加しました。

1. `move_projection_skip` に **DBR保護** を追加  
   - `PHB / PHK / PLB` でDBRをC1へ寄せ、最後に `PLB`
2. `$15FD,X` が非0のとき、`C1:9AFB` を呼ばずに **DEC $15FD,X をinline実行**
   - `C1:9AFB` のearly pathはほぼ `DEC $15FD,X; return`
3. `depth_reorder_skip` もDBR保護つきに変更
4. v2では `C1:F600` ではなく `C1:F620` を使用

---

## Patch A v2: move_projection_skip

### 元処理

```asm
C1:9AF1  JSR $9AFB
C1:9AF4  JSR $9F35
C1:9AF7  JSR $9031
```

### v2の考え方

- `$15FD,X != 0` の場合:
  - 元の `$9AFB` はdispatchせず、delayを1減らして戻るだけ
  - なので `DEC $15FD,X` をinline化
- `$00DF == 0` かつ `$15D5,X == 0` の場合:
  - `$9F35` はほぼ即return
  - なので呼ばない

### 期待効果

移動していないNPC/actorの毎フレーム更新で、

```text
JSR $9AFB の一部
JSR $9F35 の空振り
```

を削減。

---

## Patch B v2: depth_reorder_skip

### 元処理

`C1:90CE` は10slotぶん、毎回sort keyを作って `JSL $80:AFEC` でactive linked listを再配置する。

### v2の考え方

```text
new sort key == $0AA3[physical_slot]
```

なら表示深度キーは変わっていないため、`AFEC` を呼ばない。

### 期待効果

NPCや同行者が縦方向に動いていないフレームで、linked listの再配置処理を削減。

---

## 推奨テスト順

1. `shinmomo_exp_move_projection_skip_v2_20260427.ips` のみ適用
2. はじまりの村・月の神殿・銀次加入後の村で歩行/会話/戦闘遷移確認
3. 問題なければ `shinmomo_exp_depth_reorder_skip_v2_20260427.ips`
4. 最後に `shinmomo_exp_move_opt_combo_v2_20260427.ips`

## 効果測定Lua

`shinmomo_move_opt_profile_v1_snes9x_20260427.lua` を通常ROMで実行すると、スキップ候補数を出します。

```text
TRACE_MOVE_OPT_PROFILE
projection_skip_slots=
depth_same_key_slots=
```

見るべき値:

- `projection_skip_slots` が多いほど Patch A が効く
- `depth_same_key_slots` が多いほど Patch B が効く

## 注意

これはまだ実験パッチです。  
特に depth reorder は、重なり順の見た目バグ確認が必要です。
