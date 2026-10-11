# 新桃太郎伝説：40か所の入口試行・37件の実機入場・25件の画面地名

2026-10-11 / zin1985/shinmomo

## 検証方法と区別

世界pack0x4CのROM由来の入口座標の南1マスへ解析専用のWRAM座標ワープを行い、16フレーム位置を安定させてから通常のSNESコントローラUpで入口へ進んだ。
マップの切替先pack、入口接触フレーム、切替フレーム、2本の無入力120フレーム後のXY、ローカル画像・フレームログSHA256を照合した。
飛燕の行き先フラグを解放したプレイ可能な世界ステートを利用したが、今回のイベント入場に飛燕術自体は詠唱していない。

実験後に専用BizHawkの元ステートへ復元。ROM、通常のゲームセーブ、原スクリーンショット、原フレームログはGitHubへ含めない。
世界の通常徒歩経路、全ストーリー条件、ROM opcodeのCPU実行PCは未証明。到着パックがROM候補に一致したことと、イベントPCが実行されたことは別。

## 結果

- 40件試行、37件で実機パック切替確認、3件は今回の接近方法では未確認。
- 36種類の異なる行先pack、32種類の異なる構造マップ設定に到達。
- 25のpack固有の実機画面地名を読み取った。宿の同一マップレイアウトの使い回しを区別している。
- 5件の既存候補で未知だった行先座標が実機判明。洞窟系pack0x96の到着は(39,17)。
- Viewerは149マップ、60接続、1297候補のまま。個別の実測属性だけを補強した。

## 37件の入場と到着

| 番号 | 画面の地名（空欄は未確認） | 行先pack | マップ構成 | 世界入口XY | 到着XY | 既存ROM候補 |
|---:|---|---|---|---|---|---|
| 1 | 桃太郎の生家 | 0x4D | cfg_t04_l006_v2 | (52,233) | (17,37) | catalog_transition_0746 |
| 2 | すずめのお宿1 | 0x5A | cfg_t04_l018_v2 | (43,162) | (24,40) | catalog_transition_0752 |
| 3 | すずめのお宿2 | 0x5B | cfg_t04_l018_v2 | (94,131) | (24,40) | catalog_transition_0762 |
| 4 | すずめのお宿5 | 0x5D | cfg_t04_l018_v2 | (209,119) | (24,40) | catalog_transition_0786 |
| 5 | すずめのお宿6 | 0x5E | cfg_t04_l018_v2 | (174,172) | (24,40) | catalog_transition_0795 |
| 6 | すずめのお宿7 | 0x5F | cfg_t06_l021_v2 | (144,184) | (24,40) | catalog_transition_0796 |
| 7 | （名称未確認） | 0x60 | cfg_t04_l035_v2 | (59,155) | (37,56) | catalog_transition_0755 |
| 8 | ほほえみの村 | 0x65 | cfg_t04_l044_v2 | (195,60) | (58,55) | catalog_transition_0773 |
| 9 | （名称未確認） | 0x68 | cfg_t06_l038_v2 | (44,115) | (36,72) | catalog_transition_0760 |
| 10 | （名称未確認） | 0x6A | cfg_t06_l040_v2 | (79,187) | (41,72) | catalog_transition_0764 |
| 11 | 寝太郎の村 | 0x6B | cfg_t05_l042_v2 | (140,33) | (24,72) | catalog_transition_0771 |
| 12 | （名称未確認） | 0x6E | cfg_t05_l043_v2 | (144,33) | (58,55) | catalog_transition_0772 |
| 13 | でか太郎の庵 | 0x7A | cfg_t05_l041_v2 | (92,48) | (15,39) | catalog_transition_0768 |
| 14 | 桃葉山 | 0x7C | cfg_t39_l156_v1 | (31,147) | (24,78) | catalog_transition_0753 |
| 15 | 桃葉山 | 0x7C | cfg_t39_l156_v1 | (31,142) | (100,70) | catalog_transition_0754 |
| 16 | すずめのお宿4 | 0x80 | cfg_t05_l020_v2 | (231,31) | (24,40) | catalog_transition_0781 |
| 17 | （名称未確認） | 0x81 | cfg_t04_l058_v2 | (192,176) | (37,15) | catalog_transition_0788 |
| 18 | （名称未確認） | 0x82 | cfg_t04_l059_v2 | (175,189) | (40,59) | catalog_transition_0791 |
| 19 | 竹取の村 | 0x83 | cfg_t04_l070_v2 | (127,195) | (33,55) | catalog_transition_0797 |
| 20 | 神々の里 | 0x87 | cfg_t44_l167_v1 | (217,35) | (30,53) | catalog_transition_0777 |
| 21 | びろーんの森 | 0x8A | cfg_t56_l194_v1 | (209,49) | (30,56) | catalog_transition_0776 |
| 22 | はらだしの里 | 0x8C | cfg_t04_l062_v2 | (199,225) | (31,48) | catalog_transition_0792 |
| 23 | 神仙郷 | 0x8E | cfg_t04_l060_v1 | (160,4) | (31,69) | catalog_transition_0801 |
| 24 | （名称未確認） | 0x90 | cfg_t04_l081_v2 | (241,244) | (23,39) | catalog_transition_0799 |
| 25 | おむすびころりん | 0x91 | cfg_t08_l092_v2 | (47,199) | (71,59) | catalog_transition_0750 |
| 26 | （名称未確認） | 0x96 | cfg_t09_l098_v2 | (50,129) | (39,17) | catalog_transition_0756 |
| 27 | 音無しの洞窟 | 0x98 | cfg_t09_l097_v2 | (51,122) | (183,29) | catalog_transition_0757 |
| 28 | 大江山 | 0x9E | cfg_t24_l125_v2 | (123,64) | (7,26) | catalog_transition_0766 |
| 29 | 氷の塔 | 0xA9 | cfg_t26_l131_v1 | (39,34) | (184,23) | catalog_transition_0770 |
| 30 | 怨みの洞窟 | 0xAB | cfg_t49_l176_v2 | (215,72) | (22,5) | catalog_transition_0774 |
| 31 | 伏龍の洞窟 | 0xAD | cfg_t34_l148_v1 | (237,37) | (7,30) | catalog_transition_0782 |
| 32 | （名称未確認） | 0xAE | cfg_t11_l101_v2 | (230,70) | (6,11) | catalog_transition_0783 |
| 33 | （名称未確認） | 0xB0 | cfg_t11_l101_v2 | (233,73) | (61,38) | catalog_transition_0784 |
| 34 | 鬼の牢獄 | 0xB1 | cfg_t29_l138_v2 | (206,182) | (224,40) | catalog_transition_0789 |
| 35 | 虹の洞窟 | 0xB9 | cfg_t25_l129_v2 | (74,141) | (68,25) | catalog_transition_0803 |
| 36 | 鬼が島 | 0xBD | cfg_t36_l150_v2 | (123,119) | (15,37) | catalog_transition_0802 |
| 37 | （名称未確認） | 0xCA | cfg_t04_l028_v2 | (25,98) | (16,24) | catalog_transition_0804 |

桃葉山pack0x7Cは2つの別の世界入口から実機到達した。入口は2件、地名packコンテキストとしては1件と数える。
すずめのお宿1、2、5、6は同じ構造マップ構成を共用するが、選択packにより場所名が異なる。
花咲かの村pack0x60、竹取の村pack0x82にはROMの会話・場所の文脈根拠があるが、今回の画像に明瞭な地名表示がなかったため画面確認地名25件には加えていない。

## 今回は切替を確認できなかった3件

| ROM候補 | 期待pack | 世界入口 | 座標接触の実測 | この状態での結果 |
|---|---|---|---|---|
| catalog_transition_0787 | 0x77 | (156, 144) | なし | pack切替を観測せず |
| catalog_transition_0779 | 0x86 | (199, 38) | あり | pack切替を観測せず |
| catalog_transition_0006 | 0xC9 | (142, 34) | なし | pack切替を観測せず |

これらは今回のsouthからUpだけでの結果。別方向、他ストーリー条件、障害物等は未検証。ROM候補は無効化していない。

## 新たに確定した5件の到着座標

| ROM遷移候補 | pack | 到着XY |
|---|---|---|
| catalog_transition_0756 | 0x96 | (39,17) |
| catalog_transition_0766 | 0x9E | (7,26) |
| catalog_transition_0783 | 0xAE | (6,11) |
| catalog_transition_0802 | 0xBD | (15,37) |
| catalog_transition_0803 | 0xB9 | (68,25) |

## 今後の解析

入口の確認と村内のNPC全条件、ダンジョン全階層の解析は別の作業。今後は鬼が島、鬼の牢獄、音無しの洞窟、大江山、虹の洞窟、伏龍の洞窟、怨みの洞窟、氷の塔などの内部出口・階層と、ほほえみの村、竹取の村、寝太郎の村などの会話・イベント分岐を追加していく。
飛燕の実機メニューの全行き先・詠唱・MP無制限化は未検証。

### 根拠・再現の入口

- data/maps/transitions/world_37_gamepad_entrances_after_cheat_20261011.json
- data/maps/context/world_batch_verified_onscreen_titles_20261011.json
- data/maps/transitions/world_hotspot_30scene_probe_plan_20261011.json
- tools/remote_lab/batch_world_hotspot_probe.ps1
- tools/python/compile_world_37_scene_runtime_proofs.py
- tools/python/attach_world_37_scene_entrance_batch.py
- scripts/test_world_37_scene_batch.py

公式全体進捗は従来の指標定義に従い51.4%据え置き。
