# 新桃太郎伝説 解析引継ぎ総覧 統合監査版（2026-03-25）

対象ROM:
- `Shin Momotarou Densetsu (J).smc`
- `Shin Momotarou Densetsu (Beta).smc`（差分参照用）

この文書は、過去の引継ぎ `.md` を**古い順に再点検**し、さらにプロジェクト内の後続スレッドで積み上がった内容を照合して、
**漏れ・重複・更新漏れを整理した統合監査版**である。

---

## 0. 今回の監査結論

### 0-1. 結論
- **3/24版は会話・token・scene再整理の主文書としてかなり強い。**
- ただし、**3/16系で一度きれいに整理されていた「表示VM / schema / DMA / 表base修正」の一部が主文から薄くなっていた**。
- また、**武器特殊能力サブシステムは本文中に名前は残っているが、独立章としての温度感が弱くなっていた**。
- よって本監査版では、**3/24版を母体にしつつ、3/13〜3/18で確立した重要事項を明示復帰**させた。

### 0-2. 重複の扱い
- 同一内容の重複ファイル
  - `shinmomo_handover_20260313_latest.md` と `shinmomo_handover_20260313_latest (1).md`
  - `shinmomo_handover_integrated_20260316.md` と `shinmomo_handover_integrated_20260316 (1).md`
  - `shinmomo_handover_integrated_20260318_updated.md` と `shinmomo_handover_integrated_20260318_updated (1).md`
- これらは**内容同一の複製**として扱い、監査対象は実質1本として数えた。

### 0-3. 今回「漏れ補完」として明示復帰した重要項目
1. `82:FD67` 汎用 field 抽出器 / `82:FE0E` selector0 special path
2. `81:DAC9` の「固定表直引きではない」認識
3. `80:A216` = WRAM -> VRAM DMA 本体、`80:A474` = HDMA更新要求 flag setter
4. `DA:3800` 22本 stream の外部デコード済み事実
5. item/equip の **schema 基準 base 修正**
   - item base `0x442AC`
   - equip base `0x449C3`
6. 武器特殊能力サブシステムを**独立系統**として保持
7. `0x41A10` first/second table と `0x41D20` / `0x41D38` の役割整理
8. 3/21〜3/24で進んだ **ED直前帯 / 避難民speaker-label / scene再整理**

---

## 1. 確認した引継ぎソース（古い順）

### 1-1. 2026-03-13 系
- `shinmomo_address_master_overview_20260313.md`
- `shinmomo_handover_20260313_latest.md`
- `shinmomo_handover_full_addresses_with_weapon_skill (1).md`
- `shinmomo_rom_handover_master_20260313.md`
- `shinmomo_selector0_decomposition_20260313.md`
- `shinmomo_text_display_deepdive_20260313.md`

### 1-2. 2026-03-14 系
- `shinmomo_da3800_streams_summary_20260314.md`

### 1-3. 2026-03-16 系
- `shinmomo_handover_integrated_20260316.md`

### 1-4. 2026-03-18 系
- `shinmomo_handover_integrated_20260318_updated.md`

### 1-5. 2026-03-24 系
- `shinmomo_handover_integrated_20260324_master.md`

### 1-6. 追加で照合したプロジェクト内スレッド由来の更新点
- `0x41D38` second-table header らしき 8byte 塊の扱い見直し
- `0x39847 / 0x39916` の 9byte 小レコード列の切り分け
- ED直前帯 entry 15/16/17 の再区切り
- `0x7D100..0x7D181` 周辺の旧「お浜/銀次5発話」読みの撤回
- 避難民 11本 macro 群の実scene対応の更新
- 雷神 token 全出現の再照合

---

## 2. いま採用する主文書と採用ルール

### 2-1. 主文書
主文書は **`shinmomo_handover_integrated_20260324_master.md`** とする。

理由:
- 会話・文字・token・scene・ED直前帯の反映が最も新しい
- 「どこまで引き継げているか」の自己監査視点がすでに入っている
- 3/21〜3/24の会話解析結果が最もまとまっている

### 2-2. ただし主文書だけでは弱い箇所
以下は 3/24版で相対的に弱くなったため、**本監査版で明示復帰**する。
- selector / schema / field extractor の骨格
- DMA / VRAM 転送系の役割固定
- item / equip base 修正
- 武器特殊能力サブシステムの独立性
- 3/16・3/18時点の店/施設UI・ledger系の構造化説明

### 2-3. 衝突時の優先順位
1. **後発で、かつ撤回を伴う更新見解**
2. **3/24版の会話・token・scene整理**
3. **3/18版の店/施設UI・ledger・local rule engine整理**
4. **3/16版の表示VM・descriptor・DMA・base修正**
5. **3/13版のアドレス総覧・初期確定事項**

---

## 3. 現在の全体像

### 3-1. 大きな三本柱
現在の解析本線は次の三本柱で整理するのが自然。

#### A. 店 / 施設 / 分岐 / UI 系
- `0x41A10..` は **条件分岐表本命**
- `0x41A10 -> 0x39850 / 0x39993` は **target-side blob 系**
- `1D8A -> BDE7 -> C379/C931` は **bank82 local rule / membership engine**
- `19D5` は施設種別そのものより **choice layer**
- `ledger (1B15/1B25/1B35) -> bucket (BCA5/BCE1/BD06) -> choice (1D77/1D87)` の流れが見えている

#### B. 文字 / 表示 / descriptor / queue 系
- 主線は **bank89**
- `89:9D4D -> 9D91 -> 9E10 -> 9DE5 -> 9EC7 -> A5AF/A5C8`
- `09 token` は **AE3A直通 + family root fallback** の二段ディスパッチ
- `82:FD67` は **汎用 field 抽出器**
- `81:DAC9` は **固定表直引きではなく char schema + 状態依存補正**

#### C. 会話本文 / token / scene 系
- `0x70000` 台は **descriptor / pointer / page header / small dictionary 側**
- `0x30000` 台は **script / event 本体寄り**
- ED直前帯は `0x73D3B..0x7575B`
- entry 15 / 16 / 17 の切り分けと、避難民 speaker-label 群の再対応付けが進んだ

---

## 4. 監査の結果、最新版に残っていた「漏れ」と「更新漏れ」

### 4-1. 漏れではないが、本文で弱くなっていた項目

#### 表示VM / field extractor
- `82:FD67` は selector `0/1/2/3` の schema を実体付きで読める **汎用 field 抽出器**。
- selector 0 の `82:FE0E` は field `0..7` で **dynamic override** が掛かる。
- この系統は 3/24版でも断片的に残るが、主文の前半要約で強調が弱かったため復帰。

#### 表データの真の base
- item base は **`0x442AC`**
- equip base は **`0x449C3`**
- 旧 `0x442BF` / `0x449D0` は「意味ある並びの見え始め」としては有効だが、**dummy record込みの真の先頭ではない**。
- これは 3/16時点で明瞭に更新されていたため、現行統合版でも明示採用する。

#### DMA / VRAM 転送系
- `80:A216` = **WRAM -> VRAM DMA 本体**
- `80:A474` = **HDMA 更新要求 flag setter**
- `80:A151/A170/A185` = `7E:8000` 転送キュー構築側
- `7E:718B` は描画終点ではなく **operand stack / staging**

#### DA:3800 stream 群
- `DA:3800`（ROM `0x1A3800`）は asset pointer table の入口
- **22本 stream を外部デコード済み**
- `89:A963/A9AD/ABF1/AC65/AC8B/ACCA` で unpack / 再配置が見える
- `0x26A60..0x26C3F` は bitmap本体より **DMA/HDMA/表示定義寄り**

#### 武器特殊能力サブシステム
- 店/施設スクリプト帯とは**別VM系統**として扱うのが安全
- 現時点では
  - 武器コード
  - 特殊能力ポインタ表
  - 効果スクリプト
  という構造が有力
- ただし本格解析は未着手のまま

### 4-2. 旧認識が残りやすい箇所と、現在の正解
- **bank84 主線説** → 誤り。現在は **bank89 主線説**
- **`0x26A60..0x26C3F` bitmap本体説** → 後退。現在は **表示定義 / DMA寄り**
- **`80:A474` DMA本体説** → 誤り。DMA本体は `80:A216`
- **`19D5` 施設種別そのもの説** → 後退。現在は **choice layer**
- **`1D8A` 施設IDそのもの説** → 後退。現在は **local mode / category / subphase**
- **`0x7D100..0x7D181` お浜・銀次5発話固定説** → 撤回。現在は**複数scene連結帯**
- **`54..59 A1 00` 数字literal説** → 下げる。packet-local selector family 寄り
- **`A8 = の` 単独固定説** → 下げる。接続部品 / 助詞 / 敬称前半の可能性を残す

---

## 5. 重要確定事項の統合版

### 5-1. 施設 / 分岐 / script 側
- `0x41A10..` は 8byte 固定長条件表本命
  - 概形: `[key][c1][c2][c3][c4][c5][target_lo][target_hi]`
- `target` は `0x30000 + target` と読むのが自然
- `0x31DDF` / `0x320A4` への接続レコードあり
- `0x31DF8` は `0x31DDF` 流入後の同ストリーム途中の可能性が高い
- `0x31C68` は有力候補のまま残るが、直結は未確定
- `0x41D20` は **first/second table 間の remap / skip metadata 候補**
- `0x41D38` は **second-table header らしき独立 8byte**
- `0x39847` / `0x39916` は **A系 / B系 23件×9byte 兄弟列**
- `0x39850` は A系2件目先頭
- `0x39993` は clean record start ではなく **B系途中ラベル / 再開境界**

### 5-2. WRAM / UI / ledger 側
- `$1F9D / $1F9E` = 店/施設フェーズ値と退避
- `0x69FB6 = FF 03 00 00 01 02 01 02` は `$1F9D` の変換表候補
- `$1FAA` = サブ機能セット番号
- `$1923` = 現在選択中の物品レコードID側
- `$193B` = 現在対象のキャラ/主体ID側
- `$1936` = 所持金本体級
- `$1969/$196A` = 今回取引額ワーク
- `83:D906` = purchase commit
- `83:D8C1` = reverse transaction
- `82:B0B9` = ledger commit helper
- `82:96A0` = ledger load 本体
- `82:BCA5 / BCE1 / BD06` = raw money比較器ではなく bucket/class selector 寄り

### 5-3. local rule / membership engine 側
- `82:C4F4` = `E0 = 82:BDE7 + (1D8A * 0x0F)` を作る
- `[E0]` = 15byte 固定長 local rule-record
- `82:C379` = runtime membership table builder
- `82:C54C` = matcher
- `82:C36A` = table 初期化
- `82:CAA0` = shadow table -> active table bulk loader
- `1E11 / 1E51 / 1ED1 / 1F11` は row payload/result/control 列として読むのが自然

### 5-4. 表示 / descriptor / token 側
- `82:FD67` = 汎用 field 抽出器
- `82:FE0E` = selector0 special path
- selector 暫定ラベル
  - selector 0 = 一覧 / 基本表示系
  - selector 1 = 商品系
  - selector 2 = 装備系 / 特殊商品系
  - selector 3 = キャラ系
- `89:9A44` = opcode `0x4F` handler
- `0x4F` は会話分岐より **UI/施設画面で RAM 上の現在レコードから field を抜いて表示資材にする命令** とみるのが自然
- `89:9E10` の分類
  - `00` = 終端
  - `01..4F` = 制御
  - `50..FF` = literal raw ID
- `09 token` は AE3A直通枝と family fallback を持つ二段構造

### 5-5. 表データ側
- 道具表本命帯: `0x442AC` 基準、旧 anchor `0x442BF`
- 装備表本命帯: `0x449C3` 基準、旧 anchor `0x449D0`
- `0x449D0..0x44A80` = 桃太郎武器帯
- `0x44B20` 周辺 = 胴装備帯
- `0x44BF0..0x44C30` = 金太郎まさかり帯（有力）
- `0x44D00..0x44D60` = 浦島モリ帯（有力）
- `0x44E50..0x44EC0` = 杖帯
- `0x44FA0..0x45020` = バラ帯

---

## 6. 会話・文字・scene 側の最新版統合

### 6-1. 会話系の大枠
- `0x70000` 台は本文直置きより **descriptor / pointer / page header / small dictionary 側**
- `0x30000` 台は **script / event 本体寄り**
- 会話本文の一括抽出は未完成で、
  - `0x41A10` reader hunt
  - `0x30000` 台 script 帯の解読
  が依然として最優先

### 6-2. ED直前帯
- 広い探索帯: `0x73D3B..0x7575B`
- entry 15 = `0x73D3B..0x746EE`
- entry 16 = `0x746EF..0x751DE`
- entry 17 = `0x751DF..0x7575B`
- 旧 handover にあった粗い読みより、**entry単位の切り分けと speaker 再配置が前進**した状態を採用

### 6-3. token 層の最新版
- `00` = 終端
- `01` = 改行 / 行区切り候補
- `50` = 行内 delimiter / 空白相当候補
- `5B` = packet 終端候補
- `7D .. 7E` = quoted speech / 発話 packet 候補
- `04 ... 03` = 小 macro / structured control / page-head template
- `18 xx` = 漢字1字または語幹が多い
- `19 xx` = 熟語 / 短句 / 敬称込み圧縮形 / 定型句
- `1A xx` = 場面依存短句・定型句
- `50..FF` = かな / 記号 literal 側

### 6-4. 固定できている主要 token 群
- `18 03 18 01 18 02` = 金太郎
- `18 04 18 05` = 浦島
- `18 06 18 01 18 02` = 桃太郎
- `18 08 18 09 18 0A` = 夜叉姫
- `19 02 A8 18 0D` = 風神
- `18 E9 18 94 18 0D` = 雷神
- `93 BD AE 19 07` = カルラ
- `18 80 18 91 18 F2 9B` = 酒呑童子
- `A3 91 A0 B3` = アジャセ
- `18 E8 18 CC 18 F3` = やまんば

### 6-5. 避難民 speaker-label 群
- 11本 macro 辞書列の対応は **3/24版の更新見解を採用**
- `0x7D100..0x7D1DC` は旧読みを破棄し、
  - お浜 scene
  - 雷神 scene
  - よしきち scene
  - 天の仙人 scene
  などの**連結帯**とみる整理を優先する

---

## 7. 13目標の統合進捗（2026-03-25採用値）

原則として**最新の3/23時点見積り**を採用し、
会話系は 3/24 の進展を反映、ただし武器特殊能力系は 3/16〜3/24を通して未着手扱いを維持する。

| No | 目標 | 採用進捗 | メモ |
|---|---|---:|---|
| 1 | スクリプトVMの値の流れを確定する | **95** | bank89主線はかなり固い。reader本体と一部特殊枝の網羅が残る。 |
| 2 | `89:9A44 -> 82:FD67` 系を確定する | **82** | schema / wrapper / selectorの理解は強い。selector0全実例は未完。 |
| 3 | `7E:201E..2030` と `7E:3004..303C` の正体を確定する | **60** | 施設UI / ledger / choice の意味づけは前進。各メンバ定義は残る。 |
| 4 | `81:8D87` の戻り4値の意味を確定する | **30** | 依然として未解読寄り。 |
| 5 | 店・施設UIのレコード構造を確定する | **80** | choice layer / row buffer / ledger / transaction core までかなり見えた。 |
| 6 | 道具表・装備表を実用レベルでダンプする | **70** | 実用維持。true base 修正済み。内部フラグ辞書は未完。 |
| 7 | 武器特殊能力サブシステムの整理 | **18** | 独立系統の認識は保持、実解析は未着手。 |
| 8 | 条件分岐ディスパッチ系の確定 | **58** | `41A10` / `41D38` / A-B blob 理解は進んだが reader 本体未発見。 |
| 9 | 会話・店・イベントスクリプトの仕様書を作る | **63** | ED直前帯 / entry15-17 / speaker-label 群の整理が前進。 |
| 10 | 文字コード・表示系の解読を実用化する | **96** | 実用上かなり強い。全文自動抽出と最終glyph変換は未完。 |
| 11 | アイテム・装備・キャラ・会話の外部データ化 | **68** | 表・descriptor・token辞書・scene整理は進んだが、会話本文自動化は未完。 |
| 12 | 新桃全体の構造を人間可読で再構成する | **78** | 三本柱の整理がかなり進んだ。 |
| 13 | NPC大量表示時の処理軽減ロジックを特定する | **28** | VRAM転送・UI周辺の足場はあるが本体未到達。 |

### 7-1. 総合所感
- **会話・文字・scene側は 3/24時点でかなり前進**
- **表示VM / schema / DMA / 表base修正は 3/16時点の理解を保持すべき**
- **店/施設UI・ledger・local rule は 3/18時点の整理が依然として重要**
- よって、今後は「3/24だけ見る」のではなく、**3/16・3/18の核心を取り込んだこの監査版を見るのが最も安全**

---

## 8. 次回の優先タスク

### 最優先
1. **`0x41A10` reader hunt の続行**
   - direct call ではなく indirect dispatcher / script VM / embedded pointer 側の探索を継続
2. **`0x39847 / 0x39916` 9byte 小レコード列のレコード単位分解**
3. **`0x41D38` second-table header と `0x41D20` metadata の意味確定**
4. **`0x31DDF / 0x31DF8 / 0x320A4 / 0x320C8` の script 帯仕様化**

### 会話・文字側
5. **ED直前帯 entry 15/16/17 の quoted packet 切り出しをさらに進める**
6. **避難民11本 macro と scene の最終固定**
7. **glyph 最終変換表の仕上げと本文自動抽出への接続**

### 店・施設UI側
8. **`1E11 / 1E51 / 1ED1 / 1F11` 列定義の完成**
9. **purchase / money / ledger から実価格比較ルートを捕捉**

### 未着手の別系統
10. **武器特殊能力サブシステムを独立トラックで再開**

---

## 9. 再開時の最短メモ

- 主文書は 3/24版でよいが、**それだけでは 3/16系の表示VM / DMA / true base 修正が薄い**。
- 今後は **この 2026-03-25 監査版を最上位 handover** として使う。
- 最重要本線は次の4本。
  1. `0x41A10` 条件表
  2. `0x39847 / 0x39916` target-side blob
  3. bank82 local rule / membership engine (`1D8A -> BDE7 -> C379/C931`)
  4. bank89 文字表示主線 (`9D4D -> 9D91 -> 9E10 -> 9EC7 -> A5AF/A5C8`)
- 会話本文の一括抽出はまだ未完で、**reader本体と script 帯解読が最優先**。
- `82:FD67` / `81:DAC9` / `80:A216` / `80:A474` / `DA:3800` / `0x442AC` / `0x449C3` は、今後も**確定寄り前提で扱ってよい**。

---

## 10. ひとことで言うと

**3/24版は優秀だが、3/16と3/18で固めた土台を数個落としていた。**
本監査版ではその落ちた部品を拾い直し、さらに 3/21〜3/24 の会話側更新を上に被せて、
**再開時にいちばん事故りにくい一本**にしてある。
