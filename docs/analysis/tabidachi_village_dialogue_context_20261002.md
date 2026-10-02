# 旅立ちの村 dialogue / numbering context

Updated: 2026-10-02

## 結論

今回の比較で、**dialogue family番号は村番号ではない**ことが明確になった。

旅立ちの村では少なくとも次の番号軸を分離して扱う。

- 実機遷移で旅立ちの村外観として観測された runtime map pack: `0x50`
- 外観の共有 map config: `cfg_t04_l008_v2`
- 旅立ちの村の会話を多数含む dialogue source family: `0x4E`
- family `0x4F`: `0x4E` 会話帯の一部へ別の fresh-reader 状態から入る関連/特殊入口
- source family `0x50`: 後半地域の話題が混在し、旅立ちの村へ番号一致で結んではならない
- source family `0x51`: 海・竜宮・静かの村・梅・シャボン玉・ましら・だじゃれ・黄泉の塔などが同居する明確な multi-context family
- source family `0x52`: おむすび村を明示する会話を強く含むが、これも family ID を普遍的な「村番号」とみなす根拠にはならない

現時点では、ひえんの行き先一覧などから得られる独立した「村の通し番号 #N」は未回収である。

viewerでは無理に一つの村番号へ畳まず、**map pack / map config / dialogue family / story phase** を別フィールドで保持する。

## 旅立ちの村の内部IDとして現時点で使えるもの

場所コンテキストを指す一番安全なキーは:

`cfg_t04_l008_v2@0x50`

である。

これは「shared layout `cfg_t04_l008_v2` のうち runtime pack `0x50` として実行されているコンテキスト」を意味する。

shared layoutそのものを旅立ちの村に固定してはいけない。
`0xF0/0xF1` など別packで同じconfigが再利用されるためである。

## family 0x4E の24 logical records

canonical ROM の mode-2 readerを `C8:A717` から開始すると、`0x00..0x17` の24 logical recordsを連続して復元できる。

既存の保守的な `source_pair_usage_catalog.csv` が正式に A4 source selection として採用済みなのは `0x0C..0x17` の12本。

一方、script pack本体 `CC:18D1..CC:1B79` には、それより前にも以下の A4 byte列が存在する。

- `CC:194B A4 00`
- `CC:1951 A4 01`
- `CC:197A A4 02`
- `CC:1988 A4 03`
- `CC:198E A4 04`
- `CC:1994 A4 05`
- `CC:19B2 A4 06`
- `CC:19C0 A4 07`
- `CC:19CC A4 08`
- `CC:19E0 A4 09`
- `CC:19E9 A4 0A`
- `CC:19EF A4 0B`

この前半12本は full compact-VM CFG promotion がまだなので、既存catalogを上書きして「確定」にしない。

ただし文章は直接復元できるため、viewerの解析候補として保持する。

## 24本すべてを旅立ちの村と断定しない

他family比較により、ひとつの dialogue family が複数地点・イベントを抱えられることが判明した。

特に `0x51` には以下が同居する。

- イヌ・サル・キジの名前確認
- 海・コンブ・竜宮城
- 静かの村 / かぐや姫
- 鹿角仙人と梅
- シャボン玉で泣き止む子供
- ましら
- だじゃれ伊之助
- 黄泉の塔

したがって「family 0x4Eに入っているから旅立ちの村」という推論は禁止する。

viewerでは family 0x4E の24本を二層に分ける。

### 標準表示: 旅立ちの村との場所結合が強い16本

- `0x03`: 狛犬のヒビ
- `0x04`: 北西のおむすびころりんの穴
- `0x05`: 宿屋付近へ何か落ちた
- `0x07`: 神社の森から鳥が一斉に飛び立った
- `0x09`: ひえんの巻物を知らないという反応
- `0x0A`: おむすびころりんの穴が塞がった
- `0x0B`: おむすび村成立後
- `0x0C`: ひえんの術 / 月にも行ける巻物
- `0x0E`: 桃太郎がひえんの巻物を探している
- `0x0F`: おむすびころりんの穴が鬼に襲われた
- `0x11`: 屋根に穴がないので巻物は家の外だろう
- `0x12`: 北の山すそのきんたん仙人の庵
- `0x13`: 畑を荒らすな
- `0x14`: 神社で旅の記録をする案内
- `0x15`: 雪だるま発見・再会イベント
- `0x17`: 何か飛んできた反応

### analysis candidatesのみ: 同familyだが場所未確定の8本

- `0x00`: カルラ / ダイダ王子
- `0x01`: 海底 / 勇気の鎧
- `0x02`: 銀次の装備案内
- `0x06`: 鬼退治へ向かう桃太郎への忠告
- `0x08`: 井戸の水による回復
- `0x0D`: 月から飛ばされた後の反応
- `0x10`: ダイコンとお供
- `0x16`: パラメータ付き落下物取得文

この8本も旅立ちの村である可能性は残るが、内容だけでは場所を一意に固定しない。

## ひえん修行中の時期差

project gameplay sequenceとして、ひえんの術修行中にひえんの巻物が旅立ちの村へ飛来し、その前後で村人会話が変化することが確認されている。

family 0x4Eには、その時期差と非常によく対応するまとまりがある。

- `0x05`: 「さっき 宿屋のほうに 何か 落っこちてきたぞ!」
- `0x07`: 「さっき 神社の森から いっせいに 鳥が 飛びたった」
- `0x09`: 「ひえんの巻き物 ですか…?」
- `0x0C`: ひえんの術と、月にも行ける新しい巻物について話す
- `0x0E`: 桃太郎がひえんの巻物を探していることを知っている
- `0x11`: 屋根に穴がないため巻物は家の外だろう、と推測
- `0x17`: 「おや! 何か 飛んできたような……」

`0x03` の狛犬損傷も同イベントとの関係が疑われるが、現時点では「ひえん巻物が狛犬を壊した」とまでは確定しない。

各行の **exact story flag / predicate / actor binding はまだ未解決**。

そのため viewer は時期ヒントを表示するが、自動的に「現在のセリフ」へ昇格しない。

## family 0x4Fとの関係

family `0x4F` は別の村とは扱わない。

- `0x4F:0x00` は銀次装備の会話を clean fresh-reader 状態で復元する。
- `0x4F:0x01` は狛犬のヒビの会話を復元する。

これらは `0x4E:0x02/0x03` と重なる。

したがって `0x4F` は同一/関連テキスト帯の一部へ別状態から入る特殊入口として扱い、viewerで別村として重複表示しない。

## family 0x50との比較

source family `0x50` は19本が完全decode済みだが、内容は旅立ちの村に一意ではない。

代表的な話題:

- 浦島
- 乙姫
- 養老の滝
- 寝太郎
- 氷の塔
- 希望の都

runtime exterior map packが `0x50` であることを理由に、dialogue family `0x50` を同じ場所へ結ぶことは禁止する。

## family 0x51 / 0x52との比較

`0x51` は明確な multi-context familyであり、「family番号 = 村番号」を否定する強い対照例。

`0x52` では複数行が明示的に「おむすび村」と発話する。

したがって場所同定は番号ではなく、**文章・event context・transition・runtime packを横断して行う**。

## Viewer policy

`cfg_t04_l008_v2@0x50` では `data/dialogue/location_dialogue_context_20261002.csv` を「場所会話 / 時期別アーカイブ」として表示する。

標準では旅立ちの村との場所結合が強い16本だけを表示する。

既存の `analysis dialogue candidates` をONにすると、同familyだが場所未確定の8本も表示する。

各行には:

- dialogue family / subindex
- source pointer
- script callsite
- source selection の証拠レベル
- 時期ヒント
- exact story flag が未解決であること
- decode status
- location binding status

を保持する。

actor-bound current dialogueとは完全に別表示にする。
exact flagが取れるまでは、どのフェーズも自動選択しない。

## 再生成

canonical ROMから24本を再生成する:

```
python tools/python/build_tabidachi_location_dialogue.py --rom <canonical-rom>
```

canonical ROM SHA-256:

`F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`