# 新桃太郎伝説解析 vol014 統合引継ぎ v2（2026-04-30）

## 0. このパッケージの目的

別スレッドで進行中の解析とマージしやすいように、以下を GitHub へそのまま配置できる構成でまとめた。

- 2026-03-13〜2026-03-18 の既存引継ぎ資料
- 既存の表ダンプ CSV / schema / selector0 / DA:3800 系資料
- C0-CF 逆アセンブル資料
- vol014 スレッド内で追加された Goal 7 / Goal 8 の作業メモ
- ROM本体を含まない再現用アンカー抽出スクリプト
- ROMから短く検算したバイトアンカー CSV

ROM本体 `.smc/.sfc` は含めていない。

## 1. 既存資料からの土台

### 1-1. 2026-03-13 時点の重要点

- `0x41A10..` は `0x41AC0` 単体ではなく、より大きい 8バイト固定長条件分岐表の途中として扱う。
- `target` は `0x30000 + target` と見ると、`0x31DDF` / `0x320A4` などへ自然につながる。
- `0x442BF` は道具表候補、`0x449D0` は装備表候補として有力。
- `$1923` は物品側レコードID、`$193B` はキャラ/主体IDとして扱うのが有力。
- `89:9A44` opcode `4F` は UI/施設画面の field 抽出命令として見る。

### 1-2. 2026-03-16〜03-18 の重要点

- `82:FD67` は汎用 field 抽出器。
- `80:A216` は WRAM -> VRAM DMA 本体、`80:A474` は HDMA 更新要求フラグ setter。
- 道具表 base は schema 基準で `0x442AC` 寄り、装備表 base は `0x449C3` 寄りと見直された。
- `19D5` は施設種別そのものではなく choice layer と見るのが自然。
- `1D8A -> BDE7 -> C379/C931` は bank82 内 local rule / membership engine 系。
- `0x41A10 -> 39850/39993` は target-side blob 系で、`C379` builder 側とは別 subsystem と切り分ける。
- 2026-03-18時点でも `0x41A10` reader 本体、会話本文、battle/weapon skill、条件 evaluator の一部は未解明として残る。

## 2. vol014 スレッドで進めた非イベント系テーマ

イベント系は別スレッドで進めている前提のため、vol014 では主に Goal 7 / Goal 8 を中心に扱った。

### 2-1. Goal 7 武器特殊能力サブシステム

このスレッドでは、以下の作業仮説が積み上がった。

#### 検算済みバイトアンカー

ROMから短く確認したもの:

| raw offset | 内容 |
|---:|---|
| `0x0B01F9` | `d1 03 0d 04 17 04 ...` と little-endian pointer らしい2バイト値が連続 |
| `0x0B03D1` | `84 db 03 83 e1 03 82 08 04 ...` で hook列らしき構造 |
| `0x0B03E1` | `02 35 4f 02 23 19 08 d5 ... a4 ...` で default op83 body候補 |
| `0x0B0408` | `b1 db 03 cb b0 ...` で fallback / op82 default body候補 |

完全な値は `data/rom_anchor_checks/20260430_weapon_special_anchor_bytes.csv` に保存。

#### 作業仮説

- `0x0B01F9..` は装備ID別 2-byte pointer table 候補。
- `CB:03D1` 以降に weapon special top-level script body がある候補。
- top-level hook command として `84 / 83 / 82 / C1 / C2 / C8` を疑う。
- `83` hook が weapon effect selector 決定の主担当候補。
- `A4 xx` は selector 一時設定候補。
- `C0` は selector commit / finalize / dispatch trigger 候補。
- `B5` は script return / end 候補。
- `B2` は条件分岐候補。
- `CB:03E1` default body の `B2 04` が `CB:0408` 相当へ抜ける流れに見える。

### 2-2. Goal 8 条件分岐ディスパッチ系

このスレッドでは、武器特殊 mini-VM の条件分岐として `B2` 系を追った。

#### 強めの仮説

- `B2` は単純 branch ではなく、VM内部条件を参照する分岐命令候補。
- `A4 -> C0` は値設定と commit の2段階処理候補。
- selector は単純な効果IDではなく、実行パスキーまたはルーティングキーの可能性がある。
- `CB:0408` は特殊効果ではなく selector 未確定時の fallback / 通常ルート候補。

#### 要注意: まだ未確定

以下はこのスレッド内で出たが、まだ runner 側のコードアドレスで固定できていない。

- `B2` が「状態消費型」かどうか。
- `B2 cc oo` のような多バイト形式かどうか。
- `VMStatusSlots[8]` や `7E:3000台` が weapon special VM 状態そのものかどうか。
- `selector = (effect_id << 1) | flag` という構造。
- `CA:D800..CA:DF00` が primary dispatch table であるかどうか。
- C1/C2/C8 の厳密タイミング。
- selector -> battle effect routine の完全対応。

これらは **working hypotheses** として扱い、確定資料へ昇格させるには emulator trace / runner opcode handler の発見が必要。

## 3. 13目標の進捗 v2

既存公式引継ぎでは 2026-03-18 時点で Goal 7 は未着手 18% のまま。vol014では `0x0B01F9` 系の武器特殊 pointer / script 仮説を進めたため、Goal 7/8 の内部作業進捗は上げてよい。ただし、後半ターンの dispatch table 仮説は未確定扱いに戻す。

| 目標 | 2026-03-18 | vol014 v2見立て | コメント |
|---|---:|---:|---|
| 1. スクリプトVMの値の流れ | 95% | 95% | 今回は非イベント系中心。大きな更新なし。 |
| 2. 89:9A44 -> 82:FD67 系 | 80% | 80% | 更新なし。 |
| 3. 7E:201E..2030 / 7E:3004..303C | 58% | 60% | weapon VM 状態候補の観点が追加。ただし未確定。 |
| 4. 81:8D87 戻り4値 | 30% | 30% | 更新なし。 |
| 5. 店・施設UIレコード構造 | 78% | 78% | イベント/店系は今回主対象外。 |
| 6. 道具表・装備表実用ダンプ | 76% | 78% | 装備ID別 pointer table 候補が増えたため微増。 |
| 7. 武器特殊能力サブシステム | 18% | 72% | pointer table / top-level script / op83 default body候補まで進展。ただし battle effect対応は未完。 |
| 8. 条件分岐ディスパッチ系 | 62% | 72% | B2/A4/C0 の VM命令仮説が増加。runner handler 未発見のため上げすぎ注意。 |
| 9. 会話・店・イベントスクリプト仕様書 | 58% | 60% | mini-script VM の一部仕様候補が増加。 |
| 10. 文字コード・表示系実用化 | 95% | 95% | 更新なし。 |
| 11. 外部データ化 | 62% | 64% | weapon_special anchor CSV / 再現スクリプトを追加。 |
| 12. 新桃全体構造再構成 | 75% | 78% | battle/weapon skill 側の足場が増えた。 |
| 13. NPC大量表示時処理軽減 | 28% | 28% | 更新なし。 |

## 4. 次に攻める場所

### 最優先: runner opcode handler の発見

1. `A4` handler
   - selector がどの WRAM / VM内部変数へ入るか確定する。
2. `C0` handler
   - commit / dispatch / clear の実体を確定する。
3. `B2` handler
   - 条件形式、offset形式、状態消費の有無を確定する。
4. `83` hook runner
   - `A0 E1 03 CB` のような sub-script 呼び出しがどう評価されるかを追う。

### 次点: selector -> 実効果対応

- `A4 01 / 02 / 04 / 06 ... / 24` の使用箇所を装備ID別に再集計。
- C1/C2/C8 optional hook を持つ装備と持たない装備で比較。
- battle effect / status / display routine 側の読み出し先を探す。

### 進め方

- ROM全体から `A4 ?? C0 B5`、`B2 ??`、`84 db 03 83 e1 03 82 08 04` などの byte pattern を抽出。
- それらを pointer table `0x0B01F9..` の到達先と照合。
- emulator trace が使える場合、特殊武器装備時に `0x0B03E1` 系へ入るかを確認。
- C0-CF disassembly は `data/disassembly/[L5 C0-CF] Shin Momotarou Densetsu (J) (1).txt` を参照。

## 5. このZIP内の主要ファイル

- `docs/handover/20260430_vol014_merge_handover_v2.md`
  - このファイル。次スレ再開用。
- `docs/permanent_reference/weapon_special/20260430_weapon_special_goal7_goal8_thread_findings_v2.md`
  - Goal 7 / Goal 8 の作業仮説だけを独立整理。
- `data/rom_anchor_checks/20260430_weapon_special_anchor_bytes.csv`
  - ROMから短く確認したアンカー byte。
- `scripts/analysis/extract_weapon_special_anchor_bytes.py`
  - ユーザー側ROMからアンカーを再抽出するスクリプト。
- `reference/imported_handover/`
  - 2026-03-13〜03-18 既存引継ぎ資料。
- `data/tables/`
  - 既存CSVダンプ。
- `data/disassembly/`
  - C0-CF逆アセンブル資料。

## 6. 注意

この v2 は「確定資料」と「作業仮説」を分離するためのマージ用パッケージである。特に vol014 後半の `CA:D800` dispatch table 仮説や `7E:3000台` VMStatus 仮説は、現時点では「次に検証すべき道標」であり、確定扱いしない。
