# 飛燕解放・座標ワープによる「おむすびころりん」の実機入口検証

2026-10-11 / zin1985/shinmomo

## 解析方法の変更

元の世界マップ(55,236)から洞窟系の入口(47..48,199)へ徒歩で
進めなかったため、ユーザー許可に基づき、
**解析専用の非表示BizHawkで座標ワープを利用した**。
ワープするのは入口の1歩手前まで。イベント発火は原作の
SNESコントローラ入力で再現し、ワープ自体と区別する。

プロジェクトには以前から飛燕解放済みの
analysis_lv60_hien.State と作成スクリプトが存在していた。
実機WRAMを読み戻して以下の既存設定を確認済み：
- レベル60 ($1623)
- 飛燕の術 (ID 0x33、術欄 $44DA)
- 全行き先フラグ FF FF FF FF ($1931..$1934)

ただし旧ステートはpack0xF1だったため、
プレイ可能な世界pack0x4Cの既存セーブから、
analysis_world_lv60_hien_20261011.State を別名で作成した。

**飛燕行き先フラグ全開放は確認したが、画面の村名一覧の
完全な取得、術の実際の詠唱、MP無制限化はまだ未検証**。
今回の洞窟到達には飛燕術を発動せず、座標チートを使用した。

## 再利用する専用の安全なワープコマンド

PowerShell実行例：

    & .\tools\remote_lab\create_hidden_hien_warp_state.ps1 -BaseState vmtrace_world_pack4c_x55_y236_preentry_20261011 -OutputState analysis_hien_warp_near_cave -X 47 -Y 200 -Level 60 -NeutralFrames 16

このツールは専用BizHawkが非表示であること、
ソースが世界pack0x4Cであることを要求する。
ROM・通常セーブデータは書き換えず、専用のWRAM
($1623、$1931..$1934、術欄の空き1バイト、
座標$1573/$157D)だけを変更し、再読取で検証する。
別名の解析ステートに保存し、前のエミュステートへ必ず復元。
同名ステートがすでにある場合は上書き拒否。
通常の徒歩到達可能性を保証しない。

## 世界から洞窟への実機イベント

世界pack0x4Cを(47,200)に座標ワープ。
入力を16フレーム止めて位置の安定を確認した。
その後Upを30フレーム実行、120フレーム無入力で検証した。

| 実機イベント | フレーム |
| --- | --- |
| ワープ配置の確認 世界(47,200) | 663062 |
| 通常Upで入口矩形(47,199)に接触 | 663064 |
| 世界0x4C → 洞窟pack0x91切替 | 663079 |
| 生VM領域$126E/$12B4が0x91に変化 | 663116 |
| 洞窟の到着座標(71,59)を観測 | 663203 |
| 追加無入力後に洞窟画面を表示 | 663332 |

**画面内地名は「おむすびころりん」**だった。
ローカルスクリーンショットのSHA-256:
403BE0D1A45A98A513EA034F4CF7E501DE97DCD7F5A84254CF629D292EEE3825

既存の静的遷移は catalog_transition_0750、
world cfg_t01_l001_v1 の X47..48,Y199、
候補命令 CC:0B7F、
行先 cfg_t08_l092_v2、tileset8/layout92/pack0x91。
入口の実機座標と一致したが、**CPU実行PCは未観測**。
物語の全状態や通常の徒歩経路が通ることも未証明。

## データ・Viewer反映

- tools/python/verify_cheat_warp_dungeon_entry.py は
  入力ログと無入力ログの全フレームを再照合。
- data/maps/transitions/omusubi_kororin_cheat_entry_verified_20261011.json
  はローカル生キャプチャSHAを持つ派生証拠。
- tools/python/apply_cheat_positioned_dungeon_proof.py は
  既存のcatalog_transition_0750に実測到着(71,59)を結ぶ。
- data/maps/context/pack91_runtime_location_title_20261011.json は
  画面内地名をpack0x91の文脈にだけ登録。
- scripts/test_cheat_warp_dungeon_entry.py で
  誤ったワープ位置、違う到着、判定条件の過大評価を拒否。

Viewerの接続数は増やさない。strong_candidateのまま、
実機入口確認（解析用ワープ起点）と
通常の徒歩経路未確認を明確に分けて表示する。
ROM、スクリーンショット、生セーブ、キャプチャをGitに含めない。

次は洞窟内部の階層切替を調査し、飛燕行き先一覧の
村名・座標対応も実機のメニューで別途検証する。
公式全体進捗51.4%、Viewer149マップ・57接続を維持。
