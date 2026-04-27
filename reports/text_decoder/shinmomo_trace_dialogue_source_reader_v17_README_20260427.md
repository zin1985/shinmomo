# shinmomo source reader tracer v17

## 目的

v16までの `$12B2/$12C4` は表示直前の作業窓であり、かな文字は拾いやすい一方、`桃太郎`、`銀次`、`刀`、`鬼`、`穴` のような辞書語・漢字tokenが欠落しやすいです。

静的解析で、原文reader本体が見えました。

```asm
C9:9E57  LDA [$B1]
C9:9E59  INC $B1
C9:9E5D  INC $B2
C9:9E61  INC $B3
```

v17はこの `$B1/$B2/$B3` の原文source pointerをpollingし、ポインタ先24byteを直接デコードします。

## 出力

```text
TRACE_DIALOGUE_V17_SOURCE
TRACE_DIALOGUE_V17_LINE
```

見るところ:

```text
src_ptr=
src_raw=
src_decode=
source_state=
stack=
```

## 期待

`$12B2/$12C4` で欠けていた語が、`src_decode` 側に出る可能性があります。

例:

```text
02A0 -> 桃太郎
1850 1851 -> 銀次
184C -> 刀
18DB -> 鬼
19EB -> 穴
```

## 注意

Snes9x polling版なので、1フレーム内でreaderが複数token進む場合は取り逃がします。  
ただし、表示窓ではなく原文source pointerを直接見るので、欠落熟語・漢字の調査にはこちらが本命です。
