# 新桃太郎伝説 Goal 7 武器特殊能力サブシステム 第2解析  
## default hook / effect selector / extra hook 分類（2026-04-26）

## 1. 今回の結論

`0x0B01F9` からの装備ID別script tableは、単なるpointer表ではなく、上位script opcode `82/83/84/C1/C2/C8` によって複数hookを呼び分ける **装備特殊能力mini-script VM** と見てよい。

特に大きい進展は、`op83` hook が **特殊効果selector** としてかなり読めるようになったこと。

多くの特殊装備の `op83` hook は、以下の定型形になっている。

```text
A0 E1 03 CB   ; default op83 body CB:03E1 を呼ぶ
A4 xx         ; effect selector xx
C0 B5         ; return / commit
```

つまり、

```text
op83 = default effect body + effect selector
```

の可能性が高い。

---

## 2. default hook

デフォルト上位script:

```text
84:03DB;83:03E1;82:0408;00
```

各hookのchunkは以下。

| hook | ptr | length | bytes | 解釈 |
|---|---|---:|---|---|
| `84` | `CB:03DB` | 6 | `A0 E2 DC CA B6 B5` | 共通pre hook。`CA:DCE2` らしき共通処理を呼ぶ |
| `83` | `CB:03E1` | 39 | 長い | 共通effect body。最後に `A4 01 C0 B5` |
| `82` | `CB:0408` | 5 | `B1 DB 03 CB B0` | 共通post/finalize hook候補 |

`op83 default` の末尾に `A4 01 C0 B5` があるため、標準武器は selector `01` と見られる。

---

## 3. op83 effect selector

### 3-1. selectorの読み方

`op83` hook内の `A4 xx C0 B5` を effect selector と見る。

| selector | 主な装備 |
|---:|---|
| `01` | デフォルト武器/防具など204件 |
| `02` | 玄武の刀 |
| `04` | 白虎の刀 |
| `06` | 朱雀の刀 |
| `08` | 青龍の刀 |
| `0A` | 酒呑の剣 |
| `0B` | 夕凪のモリ |
| `0D` | 朝凪のモリ |
| `0F` | 出刃包丁 / 葉切り包丁 |
| `11` | 小出刃包丁 / 合出刃包丁 / 隼のドス / 村正 |
| `12` | 薄切り包丁 / 柳刃包丁 / 長ドス / 孫六 |
| `14` | 牛切り包丁 / 骨切り包丁 / 菊一文字 |
| `15` | 切り出し包丁 |
| `16` | ドス |
| `18` | 団十郎 |
| `19` | 村雨 |
| `1A` | きんたんの錫杖 |
| `1C` | 稲妻の錫杖 |
| `1E` | 魔よけの錫杖 |
| `20` | 鹿角の錫杖 |
| `23` | ID207 なし |
| `24` | 鬼のかぎづめ |

偶数/奇数が混じるが、四神刀は `02/04/06/08`、包丁/ドス系は `0F..19`、錫杖系は `1A/1C/1E/20` に集中する。

### 3-2. 重要な特徴

- 玄武/白虎/朱雀/青龍/酒呑は、`op83` selectorだけでなく `C1` や `C8` extra hookも持つ。
- 包丁/ドス/名刀系は `op83 selector` と `C8` hookの組み合わせで分類される。
- 錫杖系も `op83 selector` と `C8` hookの組み合わせで分類される。
- 鹿角の錫杖 `op83 CB:0E04` は `A4 20 C0 B5` の4byteだけで、default body呼び出しを含まない。特殊扱い。

---

## 4. op84 hook

`op84` は共通pre hook候補。

| ptr | 対象 | embedded pointer |
|---|---|---|
| `CB:03DB` | default 231件 | `CA:DCE2` |
| `CB:051C` | 朱雀の刀 | `CA:FB4E` |
| `CB:074B` | 夕凪のモリ | `CA:DDE9` |
| `CB:078F` | 朝凪のモリ | `CA:E364` |

`op84` は「装備効果本体」ではなく、前段条件・属性付与・攻撃前補助などのpre hookである可能性が高い。

---

## 5. opC1 / opC2 / opC8 extra hook

### C1
主に四神刀と夕凪/朝凪が持つ。

- 四神刀は `C1` extra hookで個別の演出/属性/追加効果を持つ可能性。
- 夕凪/朝凪も `C1` extra hookを持ち、モリ固有効果を扱う可能性。

### C2
現時点では2件。

| ptr | 対象 |
|---|---|
| `CB:07C2` | 朝凪のモリ |
| `CB:0AE8` | ドス |

`C2` は非常に少なく、追加後処理または例外効果候補。

### C8
包丁/ドス/錫杖系に多い。  
特に `C8` hookには条件・判定・追加処理らしき長いscriptが多く、実効果の条件判定側と見られる。

代表例:

- 酒呑の剣: `CB:0594`
- 包丁/ドス系: `CB:09E7 / 0A1A / 0A38 / 0AC0`
- 錫杖系: `CB:0D7C / 0DB0 / 0DE3 / 0E08`

---

## 6. Goal 7進捗更新

| Goal | 旧 | 新 | 理由 |
|---:|---:|---:|---|
| 7. 武器特殊能力サブシステムの整理 | 42% | 55% | op83 selector、default hook、extra hook分類が進んだ |

---

## 7. 次に攻めるべき箇所

1. `CB:03E1` default op83 bodyを命令単位で切る  
2. `A4 xx` が実際にどのWRAM/効果IDへ落ちるかを追う  
3. `C8` hookの共通命令列を分類する  
4. 四神刀の `C1` hookを比較し、属性/効果差分を抽出する  
5. runtimeで攻撃時に `op83 selector` とダメージ/状態異常/演出が一致するか確認する  

---

## 8. ROM修正観点

`op83 selector` が効くなら、IPSで特殊効果selectorを差し替える実験が可能になる。

例:

- 木刀のtop scriptを特殊selectorに差し替える
- 特定武器の `A4 xx` を別selectorへ変える

ただし、現時点では `C1/C8` extra hookとの組み合わせ依存があるため、`A4 xx` だけの差し替えは効果不完全・副作用の可能性がある。  
まずはruntimeでselectorと実効果の対応を取るべき。
