# 新桃太郎伝説 vol015 追加解析: 84:A0xx / $12B5 / CB:01F9 hook path

作成日: 2026-04-30

## 要約

今回の主対象:

- `84:A0B4 / A0C0 / A0F2` の正確な caller
- `$12B5` に `82/83/84/C1/C2/C8` が入る瞬間
- `CB:01F9` top-level hook list を `00` 終端まで scan する本体
- `AE3A` direct-hit 側か、`9D4D/9D91` fallback 側か

## 1. 重要な補正: A0B4/A0C0/A0F2 は「入口そのもの」ではない

静的に見ると、アラインメント上の実入口は次のように切る方が安全。

```text
84:A0B2  STA $12B5
          LDA #$05
          BRA -> 84:A0BE

84:A0B9  STA $12B5
          LDA #$02
84:A0BE  STA $12B4
          BRA -> 84:A0C6

84:A0C3  STA $12B5
84:A0C6  LDA $12AB
          BEQ -> 84:A0CF
          BRK #$EA
          BRA -> 84:A0E4

84:A0CF  JSL $84:A0E5
          setup $0F/$0D
          JSL $80:AC1E
84:A0E4  RTL

84:A0E5  INC $12AB
          INC $12E3
          INC $12AC
84:A0EE  STZ $12C6
84:A0F1  PHX
84:A0F2  LDX $12B4
          LDA $12B5
          JSR $AE3A
          PLX
          BCS -> 84:A10C
          LDA $12B4
          JSR $9D4D
          LDA $12B5
          JSR $9D91
          BRA -> 84:A10F
84:A10C  JSR $9DD2
84:A10F  STZ $12A9
          RTL
```

したがって、ユーザー指定の `A0B4/A0C0/A0F2` は正確には以下に読み替えるのが安全。

| 指定 | 実入口/意味 |
|---|---|
| `84:A0B4` | `84:A0B2` 入口直後の中間。実入口は `A0B2` または `A0B9` |
| `84:A0C0` | `STA $12B4` のoperand途中。実入口は `A0C3` |
| `84:A0F2` | 外部入口ではなく、`A0E5/A0EE/A0F1` からの fall-through 本体 |

## 2. exact caller

### 2-1. `84:A0B9`

`JSL 84:A0B9` は 14件。

主な役割は「Aを `$12B5` に入れ、`$12B4=02` で generic descriptor evaluator へ進む」入口。

### 2-2. `84:A0C3`

`JSL 84:A0C3` は 5件。

特に重要なのは:

```text
84:8786  JSR $8554
84:8789  JSL $84:A0C3
```

`84:8554` は `$98/$99/$9A` の long pointer を `CA:C000` master table に対して reverse scan し、解決indexを `$126E` と `$12B4` に書く helper。

つまりこの経路が、

```text
master pointer解決 -> $12B4更新 -> Aを$12B5へ投入 -> evaluator
```

の最有力。

### 2-3. `84:A0EE / A0F1 / A0F2`

`84:A0EE` への JSL は3件。

```text
84:9FFE
84:A03A
85:DA3E
```

`84:A0F1` への JSL は1件。

```text
84:BEE6
```

`84:A0F2` への外部 direct call は見つからない。  
`A0F2` は、`A0E5 -> A0EE -> A0F1` から落ちてくる実処理本体。

## 3. $12B5 に hook_id が入る瞬間

`$12B5` への write は主に以下の7箇所。

```text
84:9FF5  STA $12B5 ; Aをそのまま投入
84:A02D  STA $12B5 ; Aをそのまま投入
84:A0B2  STA $12B5 ; Aをそのまま投入
84:A0B9  STA $12B5 ; Aをそのまま投入
84:A0C3  STA $12B5 ; Aをそのまま投入
84:BECE  STA $12B5 ; ($0F) から読んだ値
85:DA3B  STA $12B5 ; $036B から読んだ値
```

今回の重要点:

- `A9 82 / A9 83 / A9 84 / A9 C1 / A9 C2 / A9 C8 -> STA $12B5` のような即値直書きは見つからない。
- `82/83/84/C1/C2/C8` は ROM code の即値ではなく、`CB:xxxx` 側の top-level list data 由来と見る方が自然。
- code 側では `A` または `($0F)` / `$036B` を経由して `$12B5` に入る。

最有力経路は次の2つ。

```text
A. 84:8554 -> 84:A0C3
   $98/$99/$9A で解決済みのmaster pointerを reverse scan
   -> $12B4 に global index
   -> A を $12B5 に書く

B. 84:BECE / 85:DA3B
   data stream / work RAM から値を読んで $12B5 に書く
```

## 4. CB:01F9 top-level hook list scan本体

完全に「これ」と断定できる単独loopはまだ未確定。

ただし、今回の切り分けで候補は狭まった。

### 4-1. 違うと見てよい候補

`80:BCC3` と `86:9201` は `00` 終端scanの形は似ているが、record format が違う。

```text
80:BCC3 : key + 3-byte pointer
86:9201 : key + 3 payload bytes
```

`CB:01F9` の top-level hook list は:

```text
hook_id + ptr16
...
00
```

なので、record長は3バイト。  
このため、上記2つは「似たscan例」ではあるが、`CB:01F9` 本体runnerそのものとは言い切れない。

### 4-2. 最有力ブリッジ

現時点の最有力ブリッジは:

```text
84:8786  JSR $8554
84:8789  JSL $84:A0C3
```

`84:8554` は `CA:C000` master table reverse scanで、`CB:01F9` は `CA:C000[0x16]` にある。

したがって、`CB:01F9` の上流値は:

```text
CA:C000 global index = 0x16
local visible group index = 2
pointer = CB:01F9
```

ただし、`CB:01F9` の各装備行を

```text
[hook_id][ptr_lo][ptr_hi] ... 00
```

としてscanする実体は、まだ `84:8786` 以降の descriptor/script runner 層に埋まっている可能性が高い。

## 5. AE3A direct-hitか、9D4D/9D91 fallbackか

結論:

```text
weapon special hook path は AE3A direct-hit ではなく、
基本的に 9D4D/9D91 fallback 側に落ちる。
```

理由:

`84:A0F2` は必ず次を試す。

```text
LDX $12B4
LDA $12B5
JSR $AE3A
BCS direct-hit
fallback:
  JSR $9D4D
  JSR $9D91
```

`AE3A` の direct-hit pair は次の10件で、weapon hook系の `82/83/84/C1/C2/C8` と `global index 0x16` の組み合わせは含まれない。

```text
(19,04), (18,04), (17,04), (10,04),
(7B,06), (78,06), (A9,06),
(0C,08), (64,02), (F7,06)
```

したがって `CB:01F9` / weapon special は direct-hit対象外で、`9D4D/9D91` fallback descriptor path と見るのが安全。

## 6. 今回の進捗更新

- Goal 7 武器特殊能力サブシステム: 78% -> 82%
- Goal 8 dispatch / 条件分岐: 73% -> 74%
- Goal 9 script仕様書化: 62% -> 64%

## 7. 次に攻める場所

次はここ。

```text
1. 84:8786 -> A0C3 の A 値供給元をさらに上へ戻す
2. 84:BECE / 85:DA3B が $12B5 に入れる値の由来を実データで固定する
3. CB:01F9 の hook_id+ptr16 scan を descriptor runner命令単位で特定する
4. 9D91 -> 9DBB -> 9E34/9E10 の token skip / member select を、weapon hook index 0x16でmini traceする
```
