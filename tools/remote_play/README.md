# Remote Play Action Modules

BizHawk remote lab を安全かつ効率的に長時間操作するための再利用可能な行動単位。

## 原則
- 各モジュール開始前に SCREENSHOT で状態確認する。
- GAMEPAD / STEP は mailbox へ1命令ずつ発行し、OK確認後に次へ進む。
- モジュール終了時に SCREENSHOT で postcondition を確認する。
- 予期しない画面、HP危険域、不可逆な選択では即停止する。
- 「探索」と「位置合わせ」と「入店」を分離する。ランドマーク確認後に粗い移動を継続しない。
- フレーム数は固定値ではなく初期値。実測結果を蓄積して調整する。

## Navigation state machine

移動は次の3段階で扱う。

1. **SEARCH**: 目的地が画面にない間だけ粗い移動を使う。
2. **APPROACH**: 目的ランドマークを確認したら粗い移動を禁止し、短い fine_move に切り替える。
3. **ENTER**: 入口直前では1方向ずつ短く入力し、画面遷移または店内表示を確認する。

### anti-oscillation
- 同じ2画面間を往復した場合は探索方向を変える。
- 同一ランドマークが2回以上確認できたら「発見済み」として探索を終了する。
- 入口付近で 100 frames 超の入力は禁止する。
- 建物前で位置がほぼ変わらない場合は、別軸へ1回だけ微調整して再確認する。

## Modules

### advance_dialogue
pre: 会話・敗北演出など文字表示中
action: STEP 120-240 -> A 30 frames -> SCREENSHOT。変化がなければ最大数回反復。
post: 次の台詞または画面遷移。
observed: 敗北後「カエルを もう一度 こらしめてみよ！」は短いAでは進まず、待機を挟んだA 30 framesで進行した。

### load_save_slot_1
pre: セーブデータ選択画面、1段目に有効データ。
action: A 30 -> SCREENSHOT。黒画面なら STEP 240-600 -> SCREENSHOT。
post: プレイヤー操作可能なマップ。

### traverse_direction
用途: SEARCHフェーズのみ。
pre: 一本道または安全な移動方向をSCREENSHOTで確認済み。
action: direction 100-220 frames -> SCREENSHOT。
post: 目的地点、ランドマーク、障害物、またはマップ遷移。
stop: 目的ランドマークが画面に入った時点で終了し、approach_landmarkへ移行。

### fine_move
用途: APPROACH / ENTERフェーズ。
pre: 目的地または入口が画面内に見えている。
action: 方向入力 12-60 frames -> SCREENSHOT。
post: 目的地との相対位置が改善。
stop: 位置が悪化、画面外へ目的地が消える、遷移発生。

### approach_landmark
pre: 目的ランドマークが画面内。
action: ランドマークと主人公の相対位置から、fine_move を1回ずつ実行。
post: 入口隣接または入口正面。
rule: traverse_directionへの逆戻りは禁止。目的地が画面外へ消えた場合のみSEARCHへ戻す。

### enter_building
pre: 入口隣接または入口正面。
action: 入口方向へ 12-45 frames -> SCREENSHOT。黒画面なら wait_transition。
post: 建物内部または店内UI。
max_retries: 3。失敗時は1軸だけfine_moveして再試行。

### wait_transition
pre: 移動直後の黒画面。
action: STEP 120-600 -> SCREENSHOT。必要時のみ反復。
post: 新マップ表示。
note: 黒画面を即異常扱いしない。

### find_weapon_shop
pre: 旅立ちの村内。
landmark: 看板「兵」= 武器屋。「茶」は武器屋ではない。
action:
1. SEARCHで「兵」を探す。
2. 「兵」を確認した瞬間に traverse_direction を終了。
3. approach_landmark で入口へ寄せる。
4. enter_building で入店。
post: 武器屋内部。
important: 「兵」を見つけた後は100 frames超の移動を禁止。

### shop_purchase
pre: 店内・商品一覧。
action: SCREENSHOTで所持金/商品/価格/装備差を確認 -> 明確に有利で資金内なら選択 -> 購入確認前後をSCREENSHOT。
post: 所持金と装備変更を確認。
stop: 高額消費、性能不明、不可逆な売却。

### field_one_battle
pre: 村外、HPが安全域。
action: encounterまで短距離移動。戦闘開始SCREENSHOT。敵とHPを確認し1ターン単位で攻撃。各ターン後SCREENSHOT。
post: 勝利してフィールド復帰。
stop: 主人公HPが危険域、未知の特殊選択、逃走不能リスク。

### return_and_save
pre: 戦闘終了・帰路が既知。
action: 村/神社へ戻る -> セーブ担当NPC/地点へ移動 -> 会話を進めセーブ -> SCREENSHOT。
post: ゲーム内セーブ完了を確認。

## Composite task example
equip_then_win_one:
1. load_save_slot_1
2. find_weapon_shop
3. shop_purchase
4. 村外へ traverse_direction
5. field_one_battle
6. return_and_save

## 観測知識
- 武器屋の看板は「兵」。
- 「茶」は別施設。
- GAMEPADは短い1-frame入力ではUIが反応しない場合があり、会話送りではA 30 framesが有効だった。
- マップ遷移の黒画面はSTEPで十分なフレームを進める必要がある。
- 建物の入口周辺で100-200 frames移動すると通り過ぎや往復が起きやすい。入口付近は12-60 framesへ縮小する。
- 銀次の包丁選択は通常戦闘コマンドとは別段階。初見時はSCREENSHOT確認を必須とする。
