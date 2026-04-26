# 新桃太郎伝説 解析引継ぎ current master update（2026-04-26）

## 0. この文書の位置づけ

この文書は、2026-04-24〜2026-04-26のスレッド内で進めた解析を、漏れなく次スレ・GitHub用に統合した最新版引継ぎである。

既存GitHub構成では、リポジトリ直下に `data/` と `handover/` があり、`handover/current_master.md` が現行引継ぎの置き場である。今回の成果は以下の方針で反映する。

- 引継ぎ本体: `handover/current_master.md` を更新
- 旧current: `handover/archive/` に退避
- CSV/Lua/IPSなどの成果物: `data/` 配下へ分類配置
- ROM本体 `.smc`: コミットしない

---

## 1. 現在の13ゴール進捗

全13ゴール単純平均: **約 85.5%**

| No | ゴール | 進捗 | 状況 |
|---:|---|---:|---|
| 1 | スクリプトVMの値の流れを確定する | **96%** | bank89/C4 script VM、09 token、queue/family、C4 opcode系の主線はほぼ固い。残りは特殊枝・runtime実例の網羅。 |
| 2 | 89:9A44 -> 82:FD67 系を確定する | **82%** | selector/schema/field抽出は固い。selector0やproducer blobの全実例が残る。 |
| 3 | 7E:201E..2030 と 7E:3004..303C の正体を確定する | **64%** | 施設UI・ledger・choice層との関係は前進。全メンバ名の完全定義は未完。 |
| 4 | 81:8D87 の戻り4値の意味を確定する | **85%** | $09/$0A/$0C/$0Dがlogical object listの集計値としてほぼ確定。script wrapper文脈の細部が残る。 |
| 5 | 店・施設UIのレコード構造を確定する | **94%** | といちや/医者/宿屋/人気度/怨みの洞窟の施設文脈がかなり固定。runtime lineID取得が残る。 |
| 6 | 道具表・装備表を実用レベルでダンプする | **78%** | 道具/装備表base・主要フィールドは実用。内部フラグ・特殊効果辞書が残る。 |
| 7 | 武器特殊能力サブシステムの整理 | **42%** | 0x0B01F9を装備ID別2バイトscript pointer tableとして構造化。特殊32件を特定。hook体系の意味解読が残る。 |
| 8 | 条件分岐ディスパッチ系の確定 | **81%** | 0x41A10系、C4 predicate、C4:C8AA candidate feeder、8586AC condition 0x3Aまで整理。実script列のruntime取得が残る。 |
| 9 | 会話・店・イベントスクリプトの仕様書を作る | **95%** | 施設文・怨み入力・C4 opcode 0x18..0x1E・C7 continuation runnerを仕様化。未解決はruntime差し込み系。 |
| 10 | 文字コード・表示系の解読を実用化する | **99%** | 実用段階。02xx辞書・例外glyph・最終glyph変換の一部だけ残る。 |
| 11 | アイテム・装備・キャラ・会話の外部データ化 | **98%** | B294/B2C1/0E27/C1 object管理/Goal7 pointer table等をCSV化。完全自動抽出ツール化は未完。 |
| 12 | 新桃全体の構造を人間が読める形で再構成する | **99%** | script、施設UI、object/OAM、animation、candidate feeder、武器特殊能力まで一連の説明が可能。最終統合図が残る。 |
| 13 | NPC大量表示時の処理軽減ロジックを特定する | **98%** | candidate feeder -> $1958 -> C1:9474 -> $1569 cap -> animation state -> OAM clip/DMAまで接続。残りはruntimeラベル確定。 |


---

## 2. このスレッドで大きく進んだ点

### 2-1. Goal 13: NPC大量表示時の処理軽減ロジック

Goal 13は **42%前後から98%** まで進んだ。  
主線は以下でつながった。

```text
C4 opcode 0x1C
  candidate 0x10..0x13 を最大4本だけ走査
  $195E で消費済みcandidateをskip
  $80DA57 で relation candidate key を実entityへ解決
  $8586AC(A=0x3A, $1E=0x80) で $180A[entity-1] bit7 clear を確認
  $1958 へ出力

C4 opcode 0x18
  $1958 を C1:944B へ渡す

C1:944B / C1:9474
  $1569 logical object listへ投入
  ID < 0x17 の通常actorは slot0..3、最大4体
  ID >= 0x17 のspecial/effectは slot0..9、最大10slot

C1:8Fxx..95xx
  object spawn / clone / state transfer / slot compact
  animation state・cursor・duration・current frameまで移管

B2C1 animation script table
  group -> state -> frame/duration script

B294 sprite definition table
  group -> frame definition -> sprite piece list

OAM builder
  $0BA7/$0C67 系 object座標を読む
  $0CE5 anchor/pivot補正
  $0B25 group/attr/skip
  $0AE5 current animation frame
  OAM枠不足ならobject単位skip
  sprite片ごとに画面外clip
  stale OAMはY=E0で隠す
  dirty時だけOAM DMA
```

#### 重要な確定・確定寄り事項

- `$0BA7/$0C67` は object/sprite/effect work の座標配列。
- OAM builder側では `X = Y + 2` ずれで `$0BA5,X/$0C65,X` として同じ座標を読む。
- `$0CE5,X` は vertical anchor / ground offset / pivot。
- `$0B25,X` は下位4bitがsprite group、`0x40`がdraw skip、`0x30`がobject-level attr overlay。
- `$0AE5,X` は1-based animation frame / pattern index。0なら描画しない。
- `C0:B294` は16本の3バイトlong pointer table。sprite definition group table。
- `C0:B2C1` はanimation script pointer tableの先頭として機能し、同時にB294 group15付近と重なるオーバーラップ構造。
- `$0E27,Y` は animation state number。`$0B27 & 0x0F` のanimation groupと組で意味が決まる。
- `80:AE88` はstate変更＋animation再始動、`80:AE79` は再生位置保持のstate差し替え、`80:AE75` はduration補助。
- `C1:94FF..958B` はlogical slot compact時に animation state/cursor/duration/current frame を完全移管する。
- `C4:C8AA` はscript opcode `0x1C` handler。
- `$195E` はcandidate `0x10..0x13` の1イベント/scene context内の消費済みmask。
- `$195E` の専用clearは静的には未発見。上位のscript/event context resetか汎用WRAM初期化依存の可能性が高い。
- `81:8D87` は `$1569` logical object list のcount feedback helper。

### 2-2. Goal 4: `81:8D87` の戻り4値

`81:8D87` は `$1569[0..9]` を走査する **object/actor count aggregator** と判明。

| 戻り先 | 意味 |
|---|---|
| `$09` | 有効通常actor数。ID `<0x17` かつ `$180A[entity-1] bit7` clear |
| `$0A` | 通常actor総数。ID `<0x17` の数 |
| `$0C` | 全logical object数。非ゼロID総数 |
| `$0D` | special object数。`$0C - $0A`、ID `>=0x17` の数 |

C4 script側には、`C4:8D50/8D60/8D6B/8D76` として4値を個別返却するwrapperがある。

### 2-3. Goal 7: 武器特殊能力サブシステム

`0x0B01F9` は **装備IDごとの2バイトscript pointer table** と見てよい。

```text
table: 0x0B01F9..0x0B03D0
entry size: 2 bytes
entry count: 236
target bank: CB local offset
first target: CB:03D1
```

デフォルト上位script:

```text
84:03DB;83:03E1;82:0408;00
```

特殊処理持ちは32件。集中箇所:

- 四神刀系: ID 16〜20周辺
- 夕凪/朝凪モリ: ID 60〜61
- 包丁/ドス/名刀系: ID 114〜130
- 錫杖系: ID 184〜187
- かぎづめ周辺: ID 207, 209
- extra/sentinel: 234, 235

現時点では「装備ID -> pointer table -> top-level effect script -> hook82/83/84 + optional C1/C2/C8」というmini-script VMとして扱う。

### 2-4. Goal 5 / 9: 店・施設UI、会話・イベントscript

文字コード解析の成果から、施設文の分類が進んだ。

#### といちや / 十一屋

`0x082E20..0x083035` は、といちや/十一屋/預かり/引き出し/金庫説明帯。

代表文:

```text
そやけど 十一屋に 3万両以上 ためてると
何べんでも おねがいしまっせ！
いくら あずけになりまっか？
もちものを えらんで くんなはれ
なんにも はいってませんよ
十一屋グループのしくみを 説明しまひょ
最高 65000両まで / 1000両ずつで...
```

#### 人気度30未満・治療費2倍

`0x0830DE..0x08310F` は人気度30未満時の治療費2倍通知。

```text
人気度が 30をわったので
いつもの 2ばいに
ちりょうひを はらうはめに
なってしまった！
```

#### 人気度80超え・宿屋半額

`0x083420..0x083458` は人気度80超え時の宿屋半額通知。

```text
人気度が 80をこえたので
半分の値段で
宿屋に とまれるようになった！
```

`02 64` は文脈上「人気」辞書候補として強い。

#### 怨みの洞窟

`0x09BF28..0x09BF5A` は名前入力3本。

```text
いちばん 嫌いな人の 名前を お聞かせください！
続いて 2番目に 嫌いな人の 名前を お聞かせください！
最後に 3番目に 嫌いな人の 名前を お聞かせください！
```

ただし順位・名前入力UI・保存先・敵名差し込みが混じるため、静的だけでは完全確定不可。runtime hookが必要。

### 2-5. `0x398xx/0x399xx` target-side blob / C7 continuation runner

`0x39839` の `30 75` は、当初 `0x7530=30000` と見たが、9バイトrecord境界で見ると撤回寄り。

```text
0x039835: 48 00 3E 42 30 75 00 70 F0
0x03983E: 48 00 3E 42 30 76 00 22 E8
```

自然な読み:

```text
[op][p1][p2][p3][cmd][val_lo][val_hi][next_lo][next_hi]
```

つまり `30 75` は金額30000ではなく、`cmd=0x30 / val=0x0075` と見る方が安全。

`0x39847..0x399E4` はA/B兄弟record列。  
`0x39850` / `0x39993` は表先頭ではなく途中ラベル。

C7 continuation runner:

- `C7:F09A` = A系 common continuation
- `C7:F0DB` = B系 common postlude
- `C7:F0C6/F0CD/F0D4` = 階段型continuation入口
- `35 F9 F0`, `35 50 F1`, `35 07 F2` はC7内native helper call形式として有力

`C7:F106 = 48 68 88 A8` は32刻みの4列X座標table。  
`C7:F0F9` helperは `X & 3` でこのtableを引き `$0BA7,Y` へ書く。

---

## 3. ROM修正・IPS実験パッチ

作成済み実験IPS:

| IPS | 内容 | 安全度 |
|---|---|---|
| `shinmomo_experimental_normal_actor_cap3_lighten.ips` | 通常actor cap 4 -> 3。処理軽減テスト | 中 |
| `shinmomo_experimental_normal_actor_cap6_expand.ips` | 通常actor cap 4 -> 6。表示増加テスト | 低〜中 |
| `shinmomo_experimental_candidate_scan_4_to_2_full_20260425.ips` | candidate scan 4 -> 2。候補0x12/0x13を無視 | 低 |

まだ避けるべき修正:

- candidate table `10 11 12 13` の拡張
- `$195E` の強制初期化
- `$180A bit7` 判定無効化
- OAM clipping条件緩和
- `$80DA57` 探索順変更

---

## 4. 次にやるべきこと

### runtimeでやる

1. `shinmomo_trace_C4_opcode_1B_1E_bizhawk_20260426.lua` をBizHawkで実行
2. `opcode 0x1B..0x1E` の実script列を取る
3. candidate `0x10..0x13 -> $192A/$1958` の実entity対応を取得
4. `$195E` が0へ戻る上位context resetをwatch
5. 怨みの洞窟の名前入力RAM差分を取る

### 静的で続ける

1. Goal 7: default hook `03DB / 03E1 / 0408` の意味を確定
2. Goal 7: `83/C1/C2/C8` hook先の命令体系を切る
3. Goal 4: `C4:8D50/8D60/8D6B/8D76` のopcode番号を確定
4. Goal 5/9: といちや・医者・宿屋帯のruntime lineID取得に備え、静的本文表を作る
5. Goal 8: `0x41A10` reader本体とC4 predicate群の接点を探す

---

## 5. GitHub反映方針

### handover側

- `handover/current_master.md`
  - この文書を最新版として上書き
- `handover/archive/shinmomo_thread_handover_20260426.md`
  - 同内容を履歴として保存

### data側

新規ディレクトリを切ることを推奨。

```text
data/npc_display/
data/weapon_special/
data/runtime_hooks/
data/experimental_patches/
```

ROM本体 `.smc` はGitHubにコミットしない。

---

## 6. 変更した箇所 / 変更していない箇所

### 変更・追加した成果物

- NPC表示軽減系CSV/Markdown/Lua/IPS
- B294 sprite group / frame sample
- B2C1 animation script table
- `$0E27` animation state caller table
- C1 object manager tables
- `$1569` upstream / C1:9474 caller tables
- C4:C8AA / `$195E` / `$180A`関連 tables
- `81:8D87` return value tables
- Goal 7 weapon special pointer tables

### 変更していないもの

- ROM本体 `.smc`
- 既存GitHub上のファイル
- 実機/エミュレータruntimeログ
- 既存の旧引継ぎアーカイブ

---

## 7. 不確定点

- `$195E` の初期化タイミング
- `$180A bit7` のゲーム内ラベル
- candidate `0x10..0x13` のマップ/イベント上の具体名
- 怨みの洞窟の名前保存先RAM
- 0x0B01F9 weapon scriptの下位hook命令体系
- default hook `84:03DB / 83:03E1 / 82:0408` の機能名
- `0x41A10` reader本体
