#!/usr/bin/env python3
"""Publish a scope-accurate report of 14 verified exits, 6 local inconclusive trials."""
from pathlib import Path
import json
ROOT=Path(r'C:\Users\zin\Documents\GitHub\shinmomo')
proof=json.loads((ROOT/'data/maps/transitions/world_14_reverse_returns_after_cheat_arrivals_20261011.json').read_text(encoding='utf-8'))
names=json.loads((ROOT/'data/maps/context/world_batch_verified_onscreen_titles_20261011.json').read_text(encoding='utf-8'))
name_by_pack={x['runtime_pack_id_hex']:x['onscreen_title'] for x in names['all_25_onscreen_title_contexts']}
assert len(proof['verified_reverse_returns'])==14
assert len(proof['unconfirmed_local_direction_returns'])==6
lines=[
'# 新桃太郎伝説：14か所の村・ダンジョン内部から世界への実機帰還',
'',
'2026-10-11',
'',
'## 実験条件',
'',
'前回実機で世界入口から入場した20種類の独立シーンを保存ステートから読み込み、実際のSNESゲームパッドDownを72フレーム送信した。',
'各シーンの試験では無入力フレーム120（切替後は追加120）も採取。生フレームログのSHA256と連続性、入力状態、切替パック、座標安定性を検証した。',
'その結果、**14シーンでworld pack0x4Cへの帰還**、**6シーンは今回の一方向の試験では切替未確認**。',
'',
'元の世界から各シーンへ入場した際は、解析用座標ワープで世界の入口直前に移動している。',
'今回の**内部からの帰還操作中はWRAM座標を書き換えていない**。',
'つまり内部出口が実際に作動したことは確認できたが、自然な徒歩経路、全ストーリー状態、別セーブでの帰還先、CPU処理の実行PCは未証明。',
'生ROM・生画像・生WRAMトレース・解析用ステートはGitHubに含めない。',
'',
'## 実機帰還14シーン',
'',
'| 地名（画面表示確認分） | pack | 内部開始XY | 切替直前の内部XY | 今回の保存世界の帰還XY | pack切替フレーム | 位置安定観測数 |',
'|---|---|---|---|---|---:|---:|',
]
for x in proof['verified_reverse_returns']:
    pk=x['source_scene_pack']
    a=x['scene_spawn_xy'];b=x['last_observed_source_xy_before_switch'];c=x['world_arrival_xy_in_this_saved_origin_context']
    lines.append(f"| {name_by_pack.get(pk,'名称未確認')} | {pk} | ({a['x']},{a['y']}) | ({b['x']},{b['y']}) | ({c['x']},{c['y']}) | {x['first_world_pack_switch_frame']} | {x['world_stable_observed_frames']} |")
lines+=['',
'「切替直前の内部XY」はフレーム上で直前に見えた座標であり、正確な起動判定タイルを証明したものではない。',
'世界側の帰還先はその場の保存マップ原点に依存する可能性があるため、全セーブに同一座標とは扱わない。',
'',
'## 72フレームDownで切替しなかった6シーン',
'',
'| 地名 | pack | スタートXY | 72入力+120無入力後XY |',
'|---|---|---|---|',
]
for x in proof['unconfirmed_local_direction_returns']:
    pk=x['source_scene_pack']
    a=x['scene_spawn_xy'];b=x['source_after_probe_xy']
    lines.append(f"| {name_by_pack.get(pk,'名称未確認')} | {pk} | ({a['x']},{a['y']}) | ({b['x']},{b['y']}) |")
lines+=['',
'ここに記載した6件は別方向・他ストーリー状態での帰還不可能を示さない。',
'特に洞窟系0x96は(39,17)から(39,24)へ歩いたが切替せず、今後の内部探索が必要。',
'',
'## Viewerと再現',
'',
'新規の実測帰還経路14件をViewerに追加。149マップ、74接続、1311候補。',
'それぞれsource config + source packを維持し、destination world XYは今回の保存コンテキストのみ。',
'全件現在のactivation gateはunknown、navigable_now=falseとした。',
'',
'証拠ファイル・生成器：',
'- data/maps/transitions/world_14_reverse_returns_after_cheat_arrivals_20261011.json',
'- tools/remote_lab/batch_scene_reverse_exits.ps1',
'- tools/python/audit_scene_14_world_returns.py',
'- tools/python/add_14_scene_saved_world_returns.py',
'- scripts/test_scene_14_world_returns.py',
'',
'各バッチの元エミュ状態への復元、フレーム整合性、安定した帰還先座標、証拠SHA256を監査し、通常セーブデータは変更していない。',
'公式の全体進捗指標は51.4%のまま。',
]
dest=ROOT/'docs/analysis/world_scene_14_reverse_exits_20261011.md'
dest.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Report written',dest.name,'count',len(lines))
