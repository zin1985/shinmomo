# 新桃太郎伝説 解析引継ぎ current master merged（2026-04-26 final）

## 0. この文書

この文書は、2026-04-24〜2026-04-26スレッドで進めた解析と、同スレッド内で出力したCSV/Markdown/Lua/IPS成果物をGitHubへコミットするための最新版引継ぎである。

同梱ZIPは、GitHubリポジトリ直下へ展開してコミットできる構成にしている。

**ROM本体 `.smc` とゲーム画面スクリーンショット画像は同梱していない。**  
同梱対象は、解析メモ、CSV、Lua、IPS実験パッチ、runtimeログテキスト、manifestである。

---

## 1. 13ゴール最新進捗

全13ゴール単純平均: **約 87.5%**

| No | ゴール | 進捗 | 状況 |
|---:|---|---:|---|
| 1 | スクリプトVMの値の流れを確定する | **96%** | bank89/C4 script VM、09 token、queue/family、C4 opcode系の主線はほぼ固い。特殊枝・runtime実例の網羅が残る。 |
| 2 | 89:9A44 -> 82:FD67 系を確定する | **82%** | selector/schema/field抽出は固い。selector0やproducer blobの全実例が残る。 |
| 3 | 7E:201E..2030 と 7E:3004..303C の正体を確定する | **64%** | 施設UI・ledger・choice層との関係は前進。全メンバ名の完全定義は未完。 |
| 4 | 81:8D87 の戻り4値の意味を確定する | **85%** | $09/$0A/$0C/$0Dがlogical object listの集計値としてほぼ確定。script wrapper文脈の細部が残る。 |
| 5 | 店・施設UIのレコード構造を確定する | **94%** | といちや/医者/宿屋/人気度/怨みの洞窟の施設文脈がかなり固定。runtime lineID取得が残る。 |
| 6 | 道具表・装備表を実用レベルでダンプする | **78%** | 道具/装備表base・主要フィールドは実用。内部フラグ・特殊効果辞書が残る。 |
| 7 | 武器特殊能力サブシステムの整理 | **68%** | 0x0B01F9装備ID別pointer table、特殊32件、op83 selector体系、CB:03E1/A4/B2まで整理。runner/commit先が残る。 |
| 8 | 条件分岐ディスパッチ系の確定 | **81%** | 0x41A10系、C4 predicate、C4:C8AA candidate feeder、8586AC condition 0x3Aまで整理。実script列runtime取得が残る。 |
| 9 | 会話・店・イベントスクリプトの仕様書を作る | **95%** | 施設文・怨み入力・C4 opcode 0x18..0x1E・C7 continuation runnerを仕様化。runtime差し込み/会話staging採取が残る。 |
| 10 | 文字コード・表示系の解読を実用化する | **99%** | 実用段階。02xx辞書・例外glyph・最終glyph変換の一部だけ残る。会話Luaはstaging raw+既知デコード方式へ移行。 |
| 11 | アイテム・装備・キャラ・会話の外部データ化 | **98%** | B294/B2C1/0E27/C1 object管理/Goal7 pointer table等をCSV化。完全自動抽出ツール化は未完。 |
| 12 | 新桃全体の構造を人間が読める形で再構成する | **99%** | script、施設UI、object/OAM、animation、candidate feeder、武器特殊能力まで一連の説明が可能。最終統合図が残る。 |
| 13 | NPC大量表示時の処理軽減ロジックを特定する | **98%** | $0A61 linked list、$0A1F prev、$0AA3 sort key、AF33/AFEC/B03D/B100/B0C7まで接続。sort key全callerラベルが残る。 |

---

## 2. 今回スレッドで進んだ主要解析

### 2.1 Goal 13: NPC大量表示軽減 / visible object / OAM本線

#### 2.1.1 runtimeログでの認識更新

月の神殿と銀次加入後はじまりの村のログから、NPC表示は二層に分ける必要があると分かった。

```text
A. script/event logical actor層
   $195E/$1958 -> C1:9474 -> $1569

B. map/cutscene visible object層
   $0A61 active linked list
   -> $0B25/$0AE5/$0E27/$0BA5/$0C65
   -> OAM builder
   -> $0EE9 OAM mirror
```

月の神殿では画面上にNPCがいても `logical_1569=01 00...` のままで、実表示は `$0A61` active chain側だった。  
銀次加入後はじまりの村では `logical_1569=01 0D...` となり、`0D` が銀次/同行actor候補として出た。一方、村人や移動NPCは `$0A61` 側に出た。

#### 2.1.2 `$0A61` linked list仕様

静的逆引きにより以下を確定寄りに更新。

```text
$0A61[slot] = next slot
$0A1F[slot] = previous slot
$0AA3[slot] = sort key / priority / depth key
```

主要routine:

```text
C0:AE59  active list初期化
C0:AF33  object生成 + sorted insert
C0:AFAA  object削除 + unlink
C0:AFEC  既存objectのsort key更新 + reorder
C0:B03D  active chain walk + OAM build
C0:B100  1 objectをOAM pieceへ展開
C0:B0C7  OAM DMA転送
```

OAM mirrorは `x,y,tile,attr` 形式。hidden entryは `00 E0 00 00`。

#### 2.1.3 `C0:AF33` caller

`C0:AF33` は主に `$80:AF33` へのJSLで27件。  
Aレジスタが `$0AA3` sort keyとして渡され、新規objectがlinked listへ挿入される。

sort key帯の見立て:

| sort key | 見立て |
|---:|---|
| `0x08` | UI/facility/cursor寄り |
| `0x0B` | 低優先度effect/object |
| `0x20` | 低〜中優先度object |
| `0x28` | effect/object標準帯 |
| `0x2C` | 中間帯 |
| `0x2E` | event object専用帯候補 |
| `0x38` | 人物/scene object帯候補 |
| `0x3A` | 0x38近傍 |
| `0x40` | 人物/scene objectやや奥/手前帯候補 |
| `0x48` | 高優先度/前面寄りobject帯候補 |
| `0x50 + X` | indexed actor/object帯 |
| data-driven | table/stream依存 |

#### 2.1.4 `C0:AFEC` caller

`C0:AFEC` は `$80:AFEC` へのJSLで5件。既存objectのsort key更新とlinked list再配置を行う。

最重要callerは `C1:90ED`。

```text
new_sort_key = clamp($157D - $15E9,X + 0x38, 0x38..0x48)
```

移動NPCや同行者のY/depth順ソート本線候補。

---

### 2.2 Goal 4: `81:8D87` 戻り4値

`81:8D87` は `$1569[0..9]` を走査する object/actor count aggregator。

| 戻り先 | 意味 |
|---|---|
| `$09` | 有効通常actor数。ID `<0x17` かつ `$180A[entity-1] bit7` clear |
| `$0A` | 通常actor総数。ID `<0x17` の数 |
| `$0C` | 全logical object数。非ゼロID総数 |
| `$0D` | special object数。`$0C - $0A` |

C4 script側wrapper:

```text
C4:8D50 -> $09
C4:8D60 -> $0A
C4:8D6B -> $0C
C4:8D76 -> $0D
```

---

### 2.3 Goal 7: 武器特殊能力サブシステム

`0x0B01F9` は装備IDごとの2バイトscript pointer table。

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

特殊処理持ち32件。主な集中:

```text
四神刀系: ID 16-20
夕凪/朝凪モリ: ID 60-61
包丁/ドス/名刀系: ID 114-130
錫杖系: ID 184-187
かぎづめ周辺: ID 207, 209
extra/sentinel: 234, 235
```

#### `CB:03E1` default op83 body

`CB:03E1` は共通context check + selector選択 + commit/end。

末尾:

```text
CB:0400  A4 00   ; result selector = 00
CB:0402  B2 04   ; conditional relative branch +4 -> CB:0408
CB:0404  A4 01   ; result selector = 01
CB:0406  C0      ; commit/finalize
CB:0407  B5      ; return
CB:0408  B1 DB 03 CB B0 ; default op82 body
```

`A4 xx` は固定WRAMへの直接STAではなく、mini-VM内の result / return selector register に即値を置く命令と見る。  
`B2 04` は条件付き相対分岐で、`CB:0408` default op82 bodyへのtail branch候補。

op83 selector例:

```text
01 = default
02/04/06/08 = 四神刀系
0A = 酒呑の剣
0B/0D = 夕凪/朝凪
0F..19 = 包丁/ドス/名刀系
1A/1C/1E/20 = 錫杖系
24 = 鬼のかぎづめ
```

---

### 2.4 C4 candidate / `$195E` / `$1569` logical actor系

`C4:C8AA` はC4 script VMの opcode `0x1C` handler。

```text
C4:C2DD + opcode*2 -> handler
opcode 0x1C -> C4:C8AA
```

`$195E` は candidate `0x10..0x13` の消費済みbitmask。

| opcode | handler | 役割 |
|---:|---|---|
| `0x18` | `C4:C85A` | `$1958` を logical object list へspawn |
| `0x19` | `C4:C864` | `$1958` をremove |
| `0x1B` | `C4:C86E` | 現在candidateを `$195E` に消費済みset |
| `0x1C` | `C4:C8AA` | 未消費candidateから次候補を探し `$1958` へ |
| `0x1D` | `C4:C8F8` | candidate未消費predicate |
| `0x1E` | `C4:C89B` | 4候補all consumed predicate |

candidate key:

```text
0x10 -> relation_candidate_slot_0, bit 0x01
0x11 -> relation_candidate_slot_1, bit 0x02
0x12 -> relation_candidate_slot_2, bit 0x04
0x13 -> relation_candidate_slot_3, bit 0x08
```

ただし runtimeログでは、月の神殿や村NPCの大半はこの系統ではなく `$0A61` visible object層だった。

---

### 2.5 会話テキスト採取Lua

Snes9x coreでは execute hook が使えないため、会話テキスト採取はpolling方式で複数版を作成。

作成済み:

```text
shinmomo_trace_text_polling_snes9x_20260426.lua
shinmomo_trace_text_jp_decode_snes9x_20260426.lua
shinmomo_trace_dialogue_only_jp_snes9x_20260426.lua
shinmomo_trace_dialogue_jp_v2_snes9x_20260426.lua
shinmomo_trace_dialogue_staging_v3_snes9x_20260426.lua
```

重要な認識:

- `$12B2` を1文字として積む方式は本文以外の状態値が混ざりやすく、崩れた。
- 現時点の本命は `$718B` / `$7197` 周辺の表示staging buffer。
- v3は `$718B/$7197` を中心に raw hex + 既知デコードを出す。
- 不明文字は `?` とする。

---

### 2.6 施設UI / 会話 / といちや / 怨みの洞窟

文字コード解析により、施設文の静的文脈が進んだ。

といちや/十一屋:

```text
0x082E20..0x083035
十一屋説明/預ける/引き出し/金庫/30000両関連説明帯
```

人気度30未満・治療費2倍:

```text
0x0830DE..0x08310F
人気度が 30をわったので
いつもの 2ばいに
ちりょうひを はらうはめに
なってしまった！
```

人気度80超え・宿屋半額:

```text
0x083420..0x083458
人気度が 80をこえたので
半分の値段で
宿屋に とまれるようになった！
```

怨みの洞窟:

```text
0x09BF28..0x09BF5A
嫌いな人の名前入力3本
```

ただし名前保存先と敵名差し込みはruntime差分が必要。

---

## 3. GitHub配置

ZIP内は以下のように配置済み。

```text
handover/current_master.md
handover/archive/shinmomo_thread_handover_20260426_final.md
data/manifests/
data/base_tables/
data/text_facility/
data/npc_display/
data/weapon_special/
data/runtime_hooks/
data/text_trace/
data/experimental_patches/
data/runtime_logs/
data/source_notes/
```

### コミットしないもの

```text
*.smc
Shin Momotarou Densetsu (J).smc
Shin Momotarou Densetsu (J) (1).smc
image.png
```

ROM本体とゲーム画面スクリーンショットは同梱しない。

---

## 4. 次に攻めるべき箇所

### Goal 13

1. `C1:90ED` 周辺を命令単位で完全分解
2. `$157D`, `$15E9,X`, `$6A` の意味を確定
3. `C0:AF33` callerのhandle保存先をpool別に整理
4. `C0:B100` とB294 tableを完全接続
5. `$0B27` bit定義、`$0A1C` OAM budget単位を確定

### Goal 7

1. mini-VM runner側で `A4` handlerを探す
2. `C0` commit handlerの保存先を探す
3. selectorがbattle effect IDへ落ちる経路を追う
4. `CB:0364` tableと特殊script bundleを全件整理

### Goal 5/9/10

1. dialogue staging v3で `$718B/$7197` rawを取り、文字表の不足を埋める
2. 怨みの洞窟の名前入力3本でRAM差分を取る
3. といちや説明文のruntime lineIDを取る

---

## 5. 同梱データ

全同梱ファイルは `data/manifests/manifest_all_20260426.csv` を参照。
