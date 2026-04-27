# Patch B + OAM/static object skip 適用判断パック

## 結論

この段階で **適用してよいのは Patch B(depth_reorder_skip v2)** です。

一方、**OAM/static object skip は、現時点ではIPS化して適用しない方が安全**です。

理由は、C0:B03D/B100の構造上、OAMは毎フレーム順番に再構築されています。  
per-object単位で「変わっていないから飛ばす」を入れると、OAM bufferの書き込み順・index更新・前フレーム残骸が崩れて、sprite消え残り/ちらつき/表示欠けが起きる可能性が高いです。

## 今回同梱したもの

### 適用用IPS

```text
shinmomo_apply_depth_reorder_skip_v2_ONLY_recommended_20260427.ips
```

これは既存の `depth_reorder_skip v2` と同じ内容です。  
今回のログでは `depth_same_key_slots=10` がほぼ連続しており、効果見込みが高いです。

### OAM/static確認Lua

```text
shinmomo_oam_static_guard_probe_v1_snes9x_20260427.lua
```

これはOAM/static skipを本当にパッチ化できるか確認するための測定Luaです。

見る行:

```text
TRACE_OAM_STATIC_GUARD
```

見る値:

```text
all_static=
stable_run_samples=
active_like_slots=
oam_index_1109=
oam_pack_count_110C=
```

## OAM/static skip を安全にやるなら

per-object skipではなく、まずは **full-frame OAM build skip** だけが候補です。

条件イメージ:

```text
全object snapshotが前回と完全一致
かつ
OAM pack count/indexも前回と一致
かつ
画面切替/会話/戦闘遷移中ではない
```

この条件なら「OAM bufferを前回のまま使う」方向なので、per-object skipより安全です。

ただし、まだIPS化はしません。  
まず `TRACE_OAM_STATIC_GUARD` で `all_static=1` が長く続くかを見る必要があります。
