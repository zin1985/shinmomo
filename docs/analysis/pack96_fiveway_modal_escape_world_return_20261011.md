# 新桃太郎伝説：音無しの洞窟 pack0x96 の5条件同一下降と世界帰還

2026-10-11

## 実機の検証で確定したこと

- 世界pack0x4Cの入口(50,129)から、解析用座標ワープで隣接セルに移動後、通常コントローラで洞窟pack0x96、cfg_t09_l098_v2の(39,17)へ入場した。
- 上下左右・無入力の5条件をそれぞれ保存済みの同一地点から試行し、pack/X/Yが204フレーム全一致した。いずれも(39,17)から(39,24)まで7マス下降する。1マス移動する周期は9フレーム。
- 画面には「音無しの洞窟」の地名表示があった。pack0x98でも同じ地名が表示されるが、異なるpack・異なる構造マップとして別に保持する。
- pack0x96(39,24)で、無入力72フレームの後Right72を押しても全く動かなかった。一方、通常A8フレーム・無入力64フレームの後Right72を押すと(42,24)まで歩けた。地名表示が入力を止める要因だった。
- Aを押してから通常Up96フレームで(39,14)まで移動し、フレーム663807でpack0x96から世界pack0x4Cへ切り替わった。
- 切替直後に表示された世界座標(39,7)は一時的な値。フレーム663897に世界側の(50,129)へ更新され、664216まで安定した。実際の世界地形も正常に表示され、マップ選択レジスタも0x4Cへ収束した。
- 元の世界の入口(50,129)は、既存のROMイベント catalog_transition_0756 の正確なトリガ座標と一致する。

## 実測フレーム

| 状態 | フレーム | pack・XY |
|---|---:|---|
| 5条件の共通開始 | 663329 | 0x96 (39,17) |
| 7回の下降 | 663333,342,351,360,369,378,387 | 0x96 (39,18〜24) |
| 5条件の共通終了 | 663532 | 0x96 (39,24) |
| A解除・無入力64後にUp開始 | 663640 | 0x96 (39,24) |
| Up96終了 | 663736 | 0x96 (39,14) |
| pack切替 | 663807 | 0x4C (39,7) 一時値 |
| 保存世界への座標更新 | 663897 | 0x4C (50,129) |
| 追加観測の終了 | 664216 | 0x4C (50,129) |

## Viewerに加えたもの

- 実機帰還接続 runtime_pack96_modal_Up_world_20261011 を1件追加。出発cfg_t09_l098_v2 / pack0x96 → 世界cfg_t01_l001_v1 / pack0x4C、今回のセーブに対応した到着座標(50,129)。
- pack0x96に専用の地名「音無しの洞窟」を1件追加。画面確認地名コンテキストは従来25から26件へ。pack0x98に付いている同じ地名を置換しない。
- 5条件の204フレーム完全一致、表示モーダル未解除とA解除との左右動作差、遅れて書き換わる世界XYの修正を、生ログのSHA256付き派生証拠として残した。
- マップ149、接続75、遷移候補1,312。公式全体進捗は51.4%に据え置き。

## 証拠の範囲

世界から洞窟へ最初に入場するときは、世界入口直前まで解析用座標ワープを使った。ただし、洞窟内の方向操作・モーダル解除・帰還中にはWRAM座標を書き換えていない。

正確なCPU実行命令アドレス、タイトル画面を制御するROMハンドラ、出口を発火させる正確なタイル、別セーブ・別ストーリー状態での有効性は未証明。Viewerのactivation_gateはunknown/navigable_now=falseのまま。

すべての実験で専用非表示BizHawkの元ステートを保護し、終了後に復元した。生ROM、生フレーム記録、画像、セーブステートはGitHubへ追加しない。

## 再現と追加テスト

- data/maps/transitions/pack96_5way_modal_and_world_return_20261011.json
- data/maps/context/pack96_runtime_location_title_20261011.json
- tools/python/verify_pack96_fiveway_world_return.py
- tools/python/attach_pack96_modal_world_return.py
- scripts/test_pack96_fiveway_modal_world_return.py
- tools/remote_lab/verify_pack96_neutral_no_buttons.ps1
- tools/remote_lab/probe_pack96_post_descent_directions.ps1
- tools/remote_lab/probe_pack96_title_dismissal.ps1
- tools/remote_lab/control_pack96_title_no_button.ps1
- tools/remote_lab/probe_pack96_after_title_movement.ps1
- tools/remote_lab/probe_pack96_up_black_screen_stability.ps1

## 次の課題

- 地名表示・カットシーンの解除を、残る未帰還の鬼が島pack0xBD、虹の洞窟pack0xB9、怨みの洞窟pack0xAB、村系pack0x82/0x60にも適用して再検証する。
- 9フレーム自動下降とタイトル入力待ちのROM/CPUの制御処理を特定する。
- NPCの会話・建物往復・物語フラグをさらに解析する。
- 飛燕の行き先一覧、実際の飛燕発動、MP無制限化はまだ未検証。
