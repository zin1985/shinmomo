# shinmomo source reader compact tracer v20

## 目的

v19で以下の問題が出ました。

```text
bus_domain=WRAM
Warning: attempted read of 13044978 outside the memory size of 131072
```

原因は、`$B1/$B2/$B3` が `C7:0CF2` のようなROM bankを指しているのに、v19がWRAM domainでそのまま読もうとしたためです。

v20では、ROM domain / System Bus が無い場合は読まずに `TRACE_DIALOGUE_V20_SKIP` を1回だけ出します。  
WRAM範囲外readはしません。

## 改善点

- WRAM domainでROM addressを読まない
- `System Bus` があればCPU addressで読む
- `ROM/CARTROM` domainがあればHiROM offsetへ変換して読む
- active text phaseだけ読む
- all-zero source rawは捨てる
- pointer/rawが変わった時だけ出す
- 出力長を24byteから16byteへ短縮

## 出力

```text
TRACE_DIALOGUE_V20_SOURCE
TRACE_DIALOGUE_V20_SKIP
```

見るところ:

```text
src_ptr=
source=
src_raw=
src_decode=
static_hits=
context_candidates=
```

## 重要

起動時に `ROM=` が `nil` で、`System Bus` も無い場合、ROM source bytesは読めません。  
その場合は warning の代わりに `TRACE_DIALOGUE_V20_SKIP` が出ます。

Snes9x coreでROM domainが出ない場合、BizHawkの別SNES core、またはROM domain名の確認が必要です。
