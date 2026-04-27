# 新桃太郎伝説 Goal 7: `CB:03E1` 内 `A4 xx` / `B2 04` 追跡メモ
作成日: 2026-04-26

## 1. 結論

`A4 xx` は、固定WRAMへ直接selectorを書いている命令ではなく、  
**weapon special mini-VM の result / return selector register に即値を置く命令** と見るのが安全。

現時点で「A4 xx が直接 `STA $xxxx` するWRAMアドレス」は静的には見えない。  
実WRAMへ落ちるなら、`C0` / `B5` あるいは呼び出し元のmini-VM runner側で、VM accumulator / result registerを受け取っている可能性が高い。

---

## 2. `CB:03E1` default op83 body 再切り

```text
CB:03E1:
02 35
4F 02 23 19 08 D5 64 03 E0 1A 64 03 00
4F 02 23 19 07 D5 64 03 E0 D0 64 03 C0
EC B3 06
A4 00
B2 04
A4 01
C0
B5
```

### 命令単位

| address | bytes | 仮mnemonic | 意味 |
|---|---|---|---|
| `CB:03E1` | `02 35` | mode/guard prefix | op83 body前段の条件モード候補 |
| `CB:03E3` | `4F ...` | context/table check A | `$1923` と `CB:0364` 周辺tableを使う条件block |
| `CB:03F0` | `4F ...` | context/table check B | 2本目の条件block |
| `CB:03FD` | `EC B3 06` | predicate/helper | selector選択前の条件生成候補 |
| `CB:0400` | `A4 00` | result selector = 00 | fallback / no effect / default failure候補 |
| `CB:0402` | `B2 04` | conditional branch +4 | 条件成立時に `CB:0408` へ分岐する可能性 |
| `CB:0404` | `A4 01` | result selector = 01 | standard/default weapon effect selector |
| `CB:0406` | `C0` | commit / return-value finalize | result selectorを呼び出し元へ確定する候補 |
| `CB:0407` | `B5` | return/end | op83 body終端 |
| `CB:0408` | `B1 DB 03 CB B0` | default op82 body | `B2 04` の分岐先 |

---

## 3. `B2 04` の分岐先

`B2` は相対分岐型のbytecodeと見ると自然。

```text
CB:0402: B2 04
pc_after_operand = CB:0404
target = CB:0404 + 0x04 = CB:0408
```

`CB:0408` は default op82 body の先頭。

```text
CB:0408: B1 DB 03 CB B0
```

したがって `CB:03E1` の末尾は以下の二択に見える。

```text
A4 00
B2 04  -> 条件により CB:0408 へtail branch

A4 01
C0
B5     -> selector 01をcommitしてop83 return
```

### 機能解釈

`CB:03E1` は、

```text
共通条件check
  ↓
selector 00を仮置き
  ↓
条件次第で op82 default bodyへtail-call / tail-fall
  ↓
そうでなければ selector 01をcommitしてreturn
```

のような構造。

---

## 4. `A4 xx` の意味

`A4 xx` は、他のop83 wrapperでも以下のように頻出する。

```text
A0 E1 03 CB
A4 xx
C0
B5
```

これは、

```text
default op83 body を呼ぶ
  ↓
A4 xx で result selector を特殊効果値に差し替える
  ↓
C0 でcommit
  ↓
B5 でreturn
```

と見るのが自然。

### 代表selector

| selector | 代表装備 |
|---:|---|
| `01` | default |
| `02/04/06/08` | 四神刀 |
| `0A` | 酒呑の剣 |
| `0B/0D` | 夕凪/朝凪 |
| `0F..19` | 包丁/ドス/名刀系 |
| `1A/1C/1E/20` | 錫杖系 |
| `24` | 鬼のかぎづめ |

---

## 5. `A4 xx` が直接WRAMを書いていないと見る理由

1. bytecode上は `A4 xx` の2byte命令で、WRAM address引数がない。  
2. `A4 xx C0 B5` という「即値 -> commit -> return」形式が多数ある。  
3. special wrapperは `A0 E1 03 CB` でdefault bodyを呼んだ後、`A4 xx` でselectorだけ差し替えている。  
4. `B2` branchと組み合わされる例が多く、`A4` は分岐・return値のVM accumulatorとして振る舞っている。  
5. したがって直接WRAM書込ではなく、mini-VM runner側の内部resultに入る可能性が高い。

---

## 6. `B2` の仮仕様

多数の `A4 xx B2 dd` パターンから、`B2` は以下のような条件分岐命令と見る。

```text
B2 dd:
    if current_condition / previous_predicate indicates branch:
        pc = pc_after_operand + dd
```

`dd=04` の出現が非常に多く、典型的には「直後の `A4 next` を飛ばす」または「次blockへ進む」用途。

`CB:03E1` の `B2 04` は、分岐先が `CB:0408` にぴったり合うため、単なる偶然ではなく **default op82へのtail branch** と見るのが自然。

---

## 7. Goal 7 進捗

| Goal | 旧 | 新 | 理由 |
|---:|---:|---:|---|
| 7. 武器特殊能力サブシステムの整理 | 62% | 68% | `A4 xx` をVM result selector、`B2 04` をop82 tail branch候補として整理 |

---

## 8. 残り

1. mini-VM runnerで `A4` handlerがどの内部変数へ入れるかを探す  
2. `C0` がresult selectorをどのWRAM/呼び出し元へcommitするかを探す  
3. `B2` の分岐条件をruntimeで確認する  
4. 攻撃時に selector `01/02/04...` がどのbattle effect IDへ変換されるかを見る  

runtimeで見る場合は、武器攻撃直前に以下をwatchする。

```text
CB:03E1
CB:0400 A4 00
CB:0402 B2 04
CB:0404 A4 01
CB:0406 C0
CB:0408 default op82 body
```

そしてWRAM差分として、battle/effect work周辺の変化を取る。
