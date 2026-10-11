# 桃太郎の生家: pack0x4D実機地名と次の洞窟候補
2026-10-11 / zin1985/shinmomo

## 実機の画面内地名

非表示BizHawkで、pack0x4D、位置(17,37)のゲーム画面に
**「桃太郎の生家」**という地名が描画されていた。
林と道の屋外マップで、世界(52,233)との往復も実機確認済み。

ローカル画像SHA-256:
336AEC83F907E31F16C10528C1F53E6999859104DA3E87CB892B8F3535CBE7E6

ROM・生画像・セーブステート・フレームログはGitに登録しない。
証拠のメタデータのみ、
data/maps/context/pack4d_runtime_location_title_20261011.json に保存。

地名は cfg_t04_l006_v2@0x4D の場面だけで確定。
同じレイアウトやタイルセットの別packに広げない。
候補CSVにパック固有の1行を追加し、Viewerでは
runtime_pack_location_contexts を使って該当packだけ表示。
NPCやストーリーフラグ、ダンジョン分類の証明ではない。

## 最も近いROM由来の洞窟系入口候補

既存の世界→洞窟系（tileset8）遷移を抽出した。
対象は世界の矩形 X=47..48 / Y=199、
静的ROM候補 CC:0B7F、catalog_transition_0750。
行先は pack0x91、cfg_t08_l092_v2、
tileset8/layout92。ROMのダンジョン系描画ファミリーで
あり、実機で洞窟に到達したことや階層移動の証明ではない。

現在の実機基準地点は世界(55,236)。
そこからのマンハッタン距離下限は44グリッド。
これは歩行可能な経路長ではない。

非表示エミュで北進したところ(55,233)で座標が停止。
東西の短い迂回を試しても、今回の経路では先へ進めなかった。
地形、イベント条件などの真因は未確定で、全ルートが不可能
という意味でもない。WRAM書換や強制ワープは不使用。

候補自動生成:
tools/python/plan_dungeon_family_entries.py
data/maps/transitions/world_dungeon_family_targets_20261011.json
scripts/test_pack4d_location_and_dungeon_targets.py

## 次回の作業

到達可能な実機ルート、別の正規ステート、
またはROMから導く階層到達条件を調べる。
pack0x91を実機で踏むまでは入口のstatic候補をruntime confirmedに昇格しない。
pack切替、$126E/$12B4収束、着地XYをフレーム別に計測する。
CPU命令アドレスも物語条件も未確定のまま維持する。

Viewerは149マップ・57接続・1296候補、全体進捗は51.4%。
