# 永久保存版: 移動/表示最適化パッチ関係まとめ 2026-04-27

## 1. 今回作成した主なIPS

### move_projection_skip v2

```text
patches/ips/shinmomo_exp_move_projection_skip_v2_20260427.ips
```

対象:

```text
C1:9AF1
```

元処理:

```asm
C1:9AF1  JSR $9AFB
C1:9AF4  JSR $9F35
C1:9AF7  JSR $9031
```

最適化:

- `$15FD,X != 0` の場合、`C1:9AFB` のdelay pathをinline化
- `$00DF == 0` かつ `$15D5,X == 0` の場合、`JSR $9F35` をskip
- DBR保護として `PHB / PHK / PLB` を追加

評価:

```text
今回ログでは projection_skip_slots=0 が多く、大効果ではない。
副次効果扱い。
```

### depth_reorder_skip v2

```text
patches/ips/shinmomo_exp_depth_reorder_skip_v2_20260427.ips
patches/ips/shinmomo_apply_depth_reorder_skip_v2_ONLY_recommended_20260427.ips
```

対象:

```text
C1:90CE
```

狙い:

```text
new sort key == $0AA3[physical_slot]
```

なら、`JSL $80:AFEC` のlinked-list再配置をskip。

評価:

```text
profile上、depth_same_key_slots=10 が多く、効果見込みが高い。
ただし表示順に関わるため、NPCが重なる場面で目視テスト必須。
```

### combo v2

```text
patches/ips/shinmomo_exp_move_opt_combo_v2_20260427.ips
```

注意:

```text
comboは元ROMへ直接適用する。
個別パッチ適用済みROMへ重ねない。
```

## 2. OAM/static object skip

現時点では **未適用推奨**。

理由:

```text
C0:B03D/B100 付近ではOAMを毎フレーム順番に再構築している可能性が高い。
object単位でskipすると、OAM index更新がずれて残像・ちらつき・表示欠けの危険がある。
```

安全にやるなら、per-object skipではなく full-frame OAM build skip が候補。

条件案:

```text
全object snapshotが前回と完全一致
OAM index / pack count も一致
画面切替・会話・戦闘遷移中ではない
```

## 3. 効果測定Lua

```text
scripts/lua/movement/shinmomo_move_opt_profile_v1_snes9x_20260427.lua
scripts/lua/movement/shinmomo_move_opt_profile_v2_snes9x_20260427.lua
scripts/lua/movement/shinmomo_oam_static_guard_probe_v1_snes9x_20260427.lua
```

見る値:

```text
projection_skip_slots
depth_same_key_slots
object_static_slots
object_draw_skip_slots
offscreen_like_slots
actor_empty_slots
all_static
stable_run_samples
```

## 4. 推奨テスト順

1. 元ROMをバックアップ
2. `depth_reorder_skip v2 ONLY recommended` を適用
3. はじまりの村、月の神殿、銀次加入後の村で確認
4. NPC重なり、上下移動、会話開始/終了、戦闘遷移を確認
5. 問題なければcombo v2を元ROMに別名で適用して比較

## 5. IPS適用ツール

推奨:

```text
Floating IPS / FLIPS
```

注意:

```text
combo IPSは個別IPS適用済みROMへ重ねない。
必ず元ROMへ直接適用する。
```
