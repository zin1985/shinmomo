# 新桃太郎伝説 移動/表示更新処理 最適化実験パッチ v1

## 注意

これは実験IPSです。ROM本体は同梱していません。  
必ずバックアップROMに当ててください。  
まず `move_projection_skip` 単体から試すのが安全です。

---

## Patch A: move_projection_skip

### 目的

`C1:9AF1` の actor update pipeline は毎回以下を呼びます。

```asm
C1:9AF1  JSR $9AFB
C1:9AF4  JSR $9F35
C1:9AF7  JSR $9031
```

`C1:9F35` は `$00DF == 0` かつ `$15D5,X == 0` の場合、ほぼ何もせずreturnします。  
そこで、呼び出し前にこの条件を見て、不要な `JSR $9F35` を避けます。

### 変更

```asm
; C1:9AF1
JSR $F5E7
NOP
NOP
NOP
NOP
NOP
NOP

; C1:F5E7 free space
JSR $9AFB
LDA $00DF
BNE do_move
LDA $15D5,X
BEQ skip_move
do_move:
JSR $9F35
skip_move:
JSR $9031
RTS
```

### 安全度

比較的高め。  
`$00DF/$15D5,X` が0なら、元の `$9F35` も即returnするため、結果はほぼ同じ想定。

---

## Patch B: depth_reorder_skip

### 目的

`C1:90CE` は logical actor 10本に対し、毎回 `AFEC` を呼んで active linked listの並べ替えを行います。

```text
sort key = $157D - $15E9,X + 0x38
```

しかし、既存の `$0AA3[physical_slot]` と新しいsort keyが同じなら、再配置は不要なはずです。

### 変更

`C1:90CE` の入口を `JMP $F600` に差し替え、free spaceに同等処理＋same-key skipを置きます。

```asm
; if $0AA3[external_handle+2] == new_sort_key:
;     skip JSL $80:AFEC
; else:
;     JSL $80:AFEC
```

### 安全度

中程度。  
表示順が激しく入れ替わる場面、重なり順が重要なイベントでテストが必要です。

---

## 推奨テスト順

1. `shinmomo_exp_move_projection_skip_v1_20260427.ips` だけ適用
2. はじまりの村、月の神殿、銀次加入後の村を歩く
3. 会話、戦闘遷移、NPC重なり、画面切替を確認
4. 問題がなければ `shinmomo_exp_move_opt_combo_v1_20260427.ips` を試す

## 生成物

- `shinmomo_exp_move_projection_skip_v1_20260427.ips`
- `shinmomo_exp_depth_reorder_skip_v1_20260427.ips`
- `shinmomo_exp_move_opt_combo_v1_20260427.ips`
- `shinmomo_move_optimization_patch_v1_records_20260427.csv`
