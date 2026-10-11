# 新桃太郎伝説：pack0x60の会話イベント、景観変化と世界帰還

2026-10-11

## 実機で分かったこと

pack0x60 / cfg_t04_l035_v2、座標(37,56)では、前回の12回A操作後にまだNPCの台詞が残り、通常歩行できない状態だった。

その保存ステートから、さらに実際のSNES A8フレーム＋無入力20フレームを24回実行した。元の12回を含む合計36回の操作を経て、暗転と村の景観変化が生じた。36回が最小必要回数だとは主張しない。

- 元の実機村画面は桜色の樹木が並んでいた。
- 12回目のAの後はNPCの台詞「おまえたちの 好きなように 作りかえるがいい！…」が表示されていた。
- 追加17〜21回目のA操作後には全面黒い画面が表示された。
- 追加24回目では茶色く枯れたような植物に変化し、通常歩行できる状態になった。
- 変更を引き起こした正確なCPU PC、VM命令、ストーリーフラグは未解析。

## 会話と景観変化後の通常方向入力

| 方向 | 操作後のpack | 座標 |
|---|---|---|
| Down96 | 世界0x4C | (59,155) |
| Up96 | 村0x60 | (37,40) |
| Left96 | 村0x60 | (36,56) |
| Right96 | 村0x60 | (38,56) |

下方向の帰還を独立した保存ステートから再試行。フレーム664366に村0x60から世界0x4Cへ切り替わり、後続の無入力360フレームで(59,155)が安定した。これは既存の世界→村入口catalog_transition_0755の世界X59..60 Y155に整合する。

## Viewer更新

- 新規実測帰還：runtime_pack60_A36_event_Down_saved_world_20261011
- ソース：cfg_t04_l035_v2 / pack0x60、帰還先：世界cfg_t01_l001_v1 / pack0x4C (59,155)
- pack0x60の景観が変化する実機イベントの画面証拠は、正確なsource configとpackの組にだけ結びつける。
- マップ149、接続77、遷移候補1314、画面確認パック別地名26、公式全体進捗51.4%維持。

## 証拠ファイル

- data/maps/transitions/pack60_dialogue_phase_world_return_20261011.json
- tools/python/audit_pack60_dialogue_event_return.py
- tools/python/attach_pack60_village_event_return.py
- scripts/test_pack60_dialogue_phase_world_return.py
- tools/remote_lab/probe_pack60_more_dialogue.ps1
- tools/remote_lab/verify_pack60_event_return_stability.ps1

生ROM・原スクリーンショット・rawフレーム・実験用savestateはGitHubへ入れず、派生JSONにSHA256を保存。元の世界→村への入場時は入口直前まで解析用座標ワープを使ったが、今回の村内イベント・出口調査の方向操作中にはWRAM座標を書き換えていない。

全ストーリー状態、別セーブの帰還先、正確な出口判定セル、CPU実行PCなどは未確定。ストーリーゲートはunknownで、Viewerのnavigable_now=falseを維持する。

## 次の分析

1. pack0x60の変化を起こすROMイベントとNPCフラグを特定する。
2. 鬼が島0xBD、虹の洞窟0xB9、怨みの洞窟0xABの階層・出口を実際の通路から解析する。
3. pack0x82とpack0x60の会話分岐や画面状態遷移を比較する。
4. 飛燕の実際のメニュー・詠唱・無制限化の実機検証は未完了。
