# 新桃太郎伝説 Goal 7: `CB:03E1` default op83 body 命令単位分解

作成日: 2026-04-26

## 1. 対象

`CB:03E1` は、装備特殊能力mini-script VMにおける **default op83 body**。

上位scriptのデフォルト形:

```text
84:03DB;83:03E1;82:0408;00
```

特殊武器の多くは次の形で `CB:03E1` を呼んだ後、`A4 xx` でselectorを上書きする。

```text
A0 E1 03 CB   ; call default op83 body CB:03E1
A4 xx         ; selector override
C0 B5         ; commit/end
```

したがって、`CB:03E1` は単なる効果ID `01` ではなく、**op83共通処理 + default selector設定** と見る。

---

## 2. raw bytes

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

全長: **39 bytes**

---

## 3. 命令単位分解

| address | bytes | 仮mnemonic | 意味 |
|---|---|---|---|
| `CB:03E1` | `02 35` | prefix/guard | 後続 `4F` blockのモード/条件prefix候補。単独mnemonicは未確定。 |
| `CB:03E3` | `4F 02 23 19 08 D5 64 03 E0 1A 64 03 00` | condition/table block A | `$1923` と table `CB:0364` を使う条件/表参照block。 |
| `CB:03F0` | `4F 02 23 19 07 D5 64 03 E0 D0 64 03 C0` | condition/table block B | 同じく `$1923` と `CB:0364` を使う2本目の条件/表参照block。 |
| `CB:03FD` | `EC B3 06` | predicate/helper | `A4 selector` 前に頻出する helper。効果適用可否/条件正規化候補。 |
| `CB:0400` | `A4 00` | set selector 00 | selector/resultを0へ設定。no-effect/fallback候補。 |
| `CB:0402` | `B2 04` | conditional branch/skip | selector 00 と selector 01 の選択分岐候補。 |
| `CB:0404` | `A4 01` | set selector 01 | default weapon effect selectorを1へ設定。 |
| `CB:0406` | `C0` | commit/control return | selector commitまたはblock return候補。 |
| `CB:0407` | `B5` | end/return | op83 body終端。 |

---

## 4. 現時点の擬似コード

正確な分岐条件は未確定だが、機能的には次の形が最も自然。

```c
// CB:03E1 default op83 body

run_common_context_check_A($1923, table_CB0364);
run_common_context_check_B($1923, table_CB0364);

predicate = helper_EC_B3_06();

selector = 0x00;       // fallback / no-effect
if (predicate_allows_default_selector) {
    selector = 0x01;   // standard/default weapon effect
}

commit_selector(selector);
return;
```

特殊武器側は、この後に `A4 xx` でselectorを上書きする。

```text
A0 E1 03 CB  ; default bodyを呼ぶ
A4 xx        ; selector xx に上書き
C0 B5
```

---

## 5. `CB:0364` tableとの関係

`CB:03E1` 内の2本の `4F` blockは、どちらも `64 03`、つまり `CB:0364` を参照しているように見える。

`CB:0364` は2バイトpointer tableで、先頭は以下。

| index | ptr |
|---:|---|
| 0 | `CB:0D53` |
| 1 | `CB:0D5D` |
| 2 | `CB:0D67` |
| 3 | `CB:0D9B` |
| 4 | `CB:0DCE` |
| 5 | `CB:0DF7` |
| 6 | `CB:0E20` |
| 7 | `CB:0E2A` |

これらのptr先には、`84/83/82/C8` を含む装備特殊script bundleが並ぶ。  
そのため、`CB:03E1` は **selectorや現在の装備状態から、特殊script bundle tableを参照する共通dispatch前段** を持つ可能性がある。

---

## 6. `A4 01` の意味

特殊op83 wrapperのほとんどは、

```text
A0 E1 03 CB
A4 xx
C0 B5
```

の形をしている。

例:

| selector | 主な対象 |
|---:|---|
| `01` | default武器 |
| `02/04/06/08` | 四神刀 |
| `0A` | 酒呑の剣 |
| `0B/0D` | 夕凪/朝凪 |
| `0F..19` | 包丁/ドス/名刀系 |
| `1A/1C/1E/20` | 錫杖系 |
| `24` | 鬼のかぎづめ |

したがって、`CB:03E1` 末尾の `A4 01` は **標準武器用selector 01** と見てよい。

ただし直前に `A4 00; B2 04` があるため、条件によって `selector=00` のまま終わる fallback/no-effect path が存在する可能性がある。

---

## 7. 認識更新

前回まで:

```text
op83 default body = selector 01を置くだけ
```

今回更新:

```text
op83 default body =
  共通context check / table dispatch前段
  + predicate
  + selector 00/01 選択
  + commit/end
```

つまり `CB:03E1` は、武器特殊能力処理の **共通効果selector body**。

---

## 8. Goal 7進捗

| Goal | 旧 | 新 | 理由 |
|---:|---:|---:|---|
| 7. 武器特殊能力サブシステムの整理 | 55% | 62% | `CB:03E1` default op83 bodyを命令単位で分解し、selector 00/01分岐とCB:0364 table参照を確認 |

---

## 9. 次に攻めるべき箇所

1. `A4 xx` がどのWRAMにselectorを書いているかを追う  
2. `B2 04` の分岐条件を確定する  
3. `EC B3 06` helperの意味を、他140出現から分類する  
4. `CB:0364` tableの全entryを、selector/effect bundle tableとして外部化する  
5. `C0/B5/B0` の終端・commit・return差を整理する  

