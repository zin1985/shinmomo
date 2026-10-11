from pathlib import Path
import json
ROOT=Path(r'C:\Users\zin\Documents\GitHub\shinmomo')
ledger=json.loads((ROOT/'data/maps/transitions/world_37_gamepad_entrances_after_cheat_20261011.json').read_text(encoding='utf-8'))
places=json.loads((ROOT/'data/maps/context/world_batch_verified_onscreen_titles_20261011.json').read_text(encoding='utf-8'))
world=json.loads((ROOT/'viewer/data/world.json').read_text(encoding='utf-8'))
names={x['runtime_pack_id_hex']:x['onscreen_title'] for x in places['all_25_onscreen_title_contexts']}
plan=json.loads((ROOT/'data/maps/transitions/world_hotspot_30scene_probe_plan_20261011.json').read_text(encoding='utf-8'))
planned={x['transition_id']:x for x in plan['targets']}
assert len(ledger['entries'])==37 and len(places['all_25_onscreen_title_contexts'])==25
lines=[
'# 新桃太郎伝説：40か所の入口試行・37件の実機入場・25件の画面地名',
'',
'2026-10-11 / zin1985/shinmomo',
'',
'## 検証方法と区別',
'',
'世界pack0x4CのROM由来の入口座標の南1マスへ解析専用のWRAM座標ワープを行い、16フレーム位置を安定させてから通常のSNESコントローラUpで入口へ進んだ。',
'マップの切替先pack、入口接触フレーム、切替フレーム、2本の無入力120フレーム後のXY、ローカル画像・フレームログSHA256を照合した。',
'飛燕の行き先フラグを解放したプレイ可能な世界ステートを利用したが、今回のイベント入場に飛燕術自体は詠唱していない。',
'',
'実験後に専用BizHawkの元ステートへ復元。ROM、通常のゲームセーブ、原スクリーンショット、原フレームログはGitHubへ含めない。',
'世界の通常徒歩経路、全ストーリー条件、ROM opcodeのCPU実行PCは未証明。到着パックがROM候補に一致したことと、イベントPCが実行されたことは別。',
'',
'## 結果',
'',
'- 40件試行、37件で実機パック切替確認、3件は今回の接近方法では未確認。',
'- 36種類の異なる行先pack、32種類の異なる構造マップ設定に到達。',
'- 25のpack固有の実機画面地名を読み取った。宿の同一マップレイアウトの使い回しを区別している。',
'- 5件の既存候補で未知だった行先座標が実機判明。洞窟系pack0x96の到着は(39,17)。',
'- Viewerは149マップ、60接続、1297候補のまま。個別の実測属性だけを補強した。',
'',
'## 37件の入場と到着',
'',
'| 番号 | 画面の地名（空欄は未確認） | 行先pack | マップ構成 | 世界入口XY | 到着XY | 既存ROM候補 |',
'|---:|---|---|---|---|---|---|',
]
for i,e in enumerate(sorted(ledger['entries'],key=lambda x:(int(x['destination_pack'],16),x['transition_id'])),1):
    sx,sy=e['source_hotspot_xy']['x'],e['source_hotspot_xy']['y']
    dx,dy=e['settled_arrival_xy']['x'],e['settled_arrival_xy']['y']
    lines.append(f"| {i} | {names.get(e['destination_pack'],'（名称未確認）')} | {e['destination_pack']} | {e['destination_config_id']} | ({sx},{sy}) | ({dx},{dy}) | {e['transition_id']} |")
lines.extend([
'',
'桃葉山pack0x7Cは2つの別の世界入口から実機到達した。入口は2件、地名packコンテキストとしては1件と数える。',
'すずめのお宿1、2、5、6は同じ構造マップ構成を共用するが、選択packにより場所名が異なる。',
'花咲かの村pack0x60、竹取の村pack0x82にはROMの会話・場所の文脈根拠があるが、今回の画像に明瞭な地名表示がなかったため画面確認地名25件には加えていない。',
'',
'## 今回は切替を確認できなかった3件',
'',
'| ROM候補 | 期待pack | 世界入口 | 座標接触の実測 | この状態での結果 |',
'|---|---|---|---|---|',
])
for e in ledger['local_no_switch_observations']:
    info=planned[e['transition_id']]
    lines.append(f"| {e['transition_id']} | {info['static_destination_pack']} | {tuple(e['source_world_hotspot'])} | {'あり' if e['source_hotspot_contact_observed'] else 'なし'} | pack切替を観測せず |")
lines.extend([
'',
'これらは今回のsouthからUpだけでの結果。別方向、他ストーリー条件、障害物等は未検証。ROM候補は無効化していない。',
'',
'## 新たに確定した5件の到着座標',
'',
'| ROM遷移候補 | pack | 到着XY |',
'|---|---|---|',
])
all_edges={x['transition_id']:x for x in world['transition_edges']}
for transition_id in world['runtime_world_entrance_37_batch_summary']['coordinate_resolved_existing_edge_ids']:
    e=all_edges[transition_id]
    lines.append(f"| {transition_id} | {e['destination_pack']} | ({e['destination_x']},{e['destination_y']}) |")
lines.extend([
'',
'## 今後の解析',
'',
'入口の確認と村内のNPC全条件、ダンジョン全階層の解析は別の作業。今後は鬼が島、鬼の牢獄、音無しの洞窟、大江山、虹の洞窟、伏龍の洞窟、怨みの洞窟、氷の塔などの内部出口・階層と、ほほえみの村、竹取の村、寝太郎の村などの会話・イベント分岐を追加していく。',
'飛燕の実機メニューの全行き先・詠唱・MP無制限化は未検証。',
'',
'### 根拠・再現の入口',
'',
'- data/maps/transitions/world_37_gamepad_entrances_after_cheat_20261011.json',
'- data/maps/context/world_batch_verified_onscreen_titles_20261011.json',
'- data/maps/transitions/world_hotspot_30scene_probe_plan_20261011.json',
'- tools/remote_lab/batch_world_hotspot_probe.ps1',
'- tools/python/compile_world_37_scene_runtime_proofs.py',
'- tools/python/attach_world_37_scene_entrance_batch.py',
'- scripts/test_world_37_scene_batch.py',
'',
'公式全体進捗は従来の指標定義に従い51.4%据え置き。',
'',
])
target=ROOT/'docs/analysis/world_37_entries_25_visible_places_20261011.md'
target.write_text('\n'.join(lines),encoding='utf-8')
print('Analysis report complete:',len(lines),'lines; table',len(ledger['entries']),'entrances.')
