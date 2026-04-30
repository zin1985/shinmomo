# 新桃太郎伝説 vol013 静的解析: 0x39850 / 0x39993 の「9バイトrecord reader」探索

## 結論

`0x39847..0x399E5` の9バイト反復について、**専用の9バイト固定長reader本体は見つからず、実体は script VM の通常ディスパッチで読む bytecode macro 列**と見た方が正しいです。

つまり、前回「9バイトrecord」と呼んでいたものは、CPU側で

```text
for each 9-byte record:
    read byte0, byte1...
```

のように読む表ではなく、**script pointer `$98:$99:$9A` から1命令ずつ opcode を読み、dispatch table `0x487D4` で handler へ飛ぶVM命令列**です。

## reader本体候補

今回見つけたreader本体は以下です。

```text
PC 0x487A2  / 旧解析表記 89:87A2  VM入口
PC 0x487BD  / 旧解析表記 89:87BD  opcode -> handler pointer取得
PC 0x487CF  / 旧解析表記 89:87CF  Y=1にして handlerへ間接JMP
PC 0x487D4  / 旧解析表記 89:87D4  opcode dispatch table
PC 0x48410  / 旧解析表記 89:8410  script pointer advance helper
```

中心はここです。

```asm
89:87BD  REP #$30
89:87BF  AND #$00FF
89:87C2  ASL A
89:87C3  TAY
89:87C4  LDA $87D4,Y   ; opcode * 2 でhandler取得
89:87C7  STA $06
89:87C9  SEP #$30
89:87CB  JSR $87CF

89:87CF  LDY #$01
89:87D1  JMP ($0006)   ; handlerへ
```

## `$98/$99/$9A` と `Y`

各handlerは原則として:

```text
$98/$99/$9A = 現在のscript pointer
Y = 1 から開始、つまり opcode 直後のoperand位置
LDA [$98],Y = operand取得
```

という形で動きます。

命令長の進め方は2系統あります。

```asm
89:8410  CLC
89:8411  ADC $98
89:8413  STA $98
...
```

これは A に入っている命令長だけ `$98` を進める helper です。

また、

```asm
89:840F  TYA
89:8410  CLC
...
```

なので、handler内で `INY` しておき、最後に `JMP $840F` すると **Yの値を命令長として進める** 形になります。

## 0x38 handler

`0x39847` 系の各9バイト列はほぼ `38 05 01 ...` から始まります。

`0x38` のhandlerは:

```asm
89:97DF  LDA [$98],Y
89:97E1  STA $0F
89:97E3  INY
89:97E4  LDA [$98],Y
89:97E6  STA $10
89:97E8  INY
89:97E9  LDA ($0F)
89:97EB  JSL $858066
89:97EF  JSR $8951
89:97F2  JMP $840F
```

なので、`38 LL HH` は **2バイトpointer operandを持つ条件/predicate命令**です。  
`JSR $8951` は carry を boolean 化して `7E:718B` 側stackへ積む系統です。

## 9バイト反復の再解釈

例:

```text
0x39850:
38 05 01 02 32 10 07 9A F0
```

これは単純な固定recordではなく、少なくとも先頭は:

```text
38 05 01 = opcode 38 + pointer operand 0x0105
02 ...   = 次のVM命令
...
```

として読めます。

このため、前回の

```text
byte0 predicate
byte1 operandA
...
byte7/8 target
```

という固定recordスキーマは **観察上は便利だが、reader本体の実装とは一致しない** と修正します。

`byte7/8 = 9A F0 / DB F0 / C6 F0 ...` が分岐先らしく見えるのは引き続き有力ですが、これは9バイトreaderが末尾2バイトを読むというより、**後続VM命令またはsubhandlerがpayloadとして読む値** と見るべきです。

## 0x39993ズレ問題の修正

前回、`0x39993` が9バイトrow末尾の `F0` に着地する問題を見ました。

今回の見立てでは、これも **9バイト固定record境界にこだわりすぎた副作用** です。  
VMはbytecode pointerとして任意位置から開始できるため、`0x39993` が「row境界ではない」こと自体はあり得ます。

ただし、そこから `F0` opcodeとして実行されるか、直後 `0x39994=38` へ進む特殊入口なのかは、runtime traceで確認が必要です。

## 重要な作成ファイル

- `shinmomo_vm_dispatch_core_disasm.txt`
  - VM入口・dispatch table・advance helper・主要handlerの逆アセンブル抜粋
- `shinmomo_vm_opcode_handlers_used_by_398xx.csv`
  - 0x39847..0x399E5 で出る主要byteをdispatch tableに照合した一覧
- `shinmomo_39847_399E5_macro_rows_with_handlers.csv`
  - 9バイト反復をVM macro列として再注釈したCSV

## 今回の進捗

進んだ点:

- 9バイト列を読むreader本体候補として `0x487A2 / 0x487BD / 0x487CF / 0x487D4` を特定
- `0x38` が2バイトpointer operandを読むpredicate命令だと確定寄り
- 9バイト固定record説を「VM bytecode macro列」へ修正
- `0x39850` の先頭が script VM で読める構造であることを確認

未確定:

- `byte3` 以降のVM命令列の完全分割
- `0x02` family / `$9BEE` subhandler table の各member意味
- `9A F0 / DB F0 / C6 F0` が実際にどのhandlerでbranch targetとして扱われるか
- `0x39993` 入口が `F0` opcodeなのか、実効 `+1` なのか

## 次の静的ターゲット

次は **`opcode 0x02` family の `$9BEE` subhandler table 分解** が本命です。

`0x398xx` の9バイトmacro中で `02 32 ...` のような形が出るため、`0x02` handlerが `$9BEE + (arg-1)*3` から subhandler pointer を取り、それが残りpayloadをどう読むかを追うと、`9A F0 / DB F0` の意味がかなり固まります。
