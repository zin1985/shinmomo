# 新桃太郎伝説解析 引継ぎ情報 2026-04-27

## 目的

このパッケージは、今回のスレッドで進んだ解析成果を GitHub にコミットしやすい形で整理したものです。

**ROM本体は含めていません。**  
IPS、Lua、CSV、Markdown、復元結果、解析メモのみを保存対象にしています。

## 今回の最重要成果

### 1. 会話 mode02 の正体が判明

これまで `$12AA=02` の会話は、`C8:A7DD` などの raw をそのまま読んでも崩れていました。  
今回のROM静的解析により、`$12AA=02` は **C0:BD98 の bitstream/tree decoder** で展開されることが判明しました。

関連テーブル:

```text
C0:BDE4  terminal bit mask 8 bytes
C0:BDEC  branch0 next-node table 255 bytes
C0:BEEB  branch0 continue-mask 32 bytes
C0:BF0B  branch1 next-node table 255 bytes
C0:C00A  branch1 continue-mask 32 bytes
```

これにより、過去に断片しか取れていなかった銀次装備会話を復元できました。

```text
「桃太郎！ 銀次の そうびを
 ととのえたか?
 銀次は 刀も そうびできる！」
「銀次の そうびは 着流しだ！
 はちまきと わらじは
 桃太郎と いっしょだがな！」
```

### 2. 小文字かな F5/F6/F7/F8 を再検証

```text
F5 = っ
F6 = ゃ
F7 = ゅ
F8 = ょ
```

特に `91 F5 9B F8 = いっしょ` であり、以前の「いっしゅ」は誤りでした。

### 3. 表示stageだけでは断片化する理由が説明可能に

`$12B2/$12B3/$12C4/$12C5` は本文そのものではなく、表示直前の作業stageです。  
そのため `桃太郎さん` や `銀次` は表示stageだけを見ると欠けます。

原因:

```text
mode02 bitstream
↓
BD98 decoderでsymbol化
↓
02辞書 / 漢字2byte / かなが展開
↓
表示stageに1〜2byteずつ流れる
↓
pollingでは途中だけ拾う
```

### 4. 移動/表示最適化パッチ

安全寄りに効果が見込めるのは **Patch B: depth_reorder_skip v2** です。

- `C1:90CE` の depth reorder routineをcustom routineへredirect
- new sort key と既存 `$0AA3[physical_slot]` が同じなら `AFEC` をskip
- profile上は `depth_same_key_slots=10` が多く、効果見込みあり

OAM/static object skip はまだ未適用推奨です。  
OAMは毎フレーム順次再構築の可能性があり、雑にskipすると残像・ちらつき・表示欠けが起きるためです。

## 推奨GitHub配置

```text
docs/
  handover/
  permanent_reference/
scripts/
  lua/
patches/
  ips/
data/
  csv/
reports/
archives/
manifest/
```

このZIP内の構成をそのままリポジトリへ展開してコミットできます。

## コミットメッセージ案

```text
docs: add 20260427 dialogue mode02 decoder and movement optimization handover
```

または分ける場合:

```text
feat: add BD98 mode02 dialogue decoder tools
docs: add permanent text decoder analysis notes
feat: add experimental depth reorder optimization IPS
docs: add movement optimization patch notes
```
