# shinmomo source reader static lexicon tracer v18

## 目的

v17は `$B1/$B2/$B3` が指す原文source pointerを読みました。  
v18ではさらに、原文source bytesに静的辞書を重ねて `static_hits=` を出します。

## 何が改善するか

`$12B2/$12C4` の表示作業窓では落ちがちな以下を、原文source側から拾いやすくします。

```text
桃太郎
銀次
刀
装備
鬼
穴
体
無理
旅の人
入れ
行く
```

## 出力

```text
TRACE_DIALOGUE_V18_SOURCE
TRACE_DIALOGUE_V18_LINE
```

見るところ:

```text
src_ptr=
src_raw=
src_decode=
static_hits=
source_state=
stack=
```

## static_hits の例

```text
static_hits=銀次@3/known_kanji_seq | 装備@9/known_kanji_seq | 刀@18/known_kanji
```

## 注意

Snes9x pollingなので、readerが1フレーム内で進み切ると取り逃がす可能性は残ります。  
ただし、表示窓ではなく原文source bytesを見るため、熟語・漢字欠落対策としてはこちらが本命です。
