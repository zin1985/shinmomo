# 新桃太郎伝説 Goal 7: 武器特殊能力サブシステム 初回構造化メモ
作成日: 2026-04-26

## 1. 最大の進展

`0x0B01F9` は単独の謎アドレスではなく、**装備IDごとの2バイトscript pointer table** と見てよい。

```text
table: 0x0B01F9..0x0B03D0
entry size: 2 bytes
entry count: 236
target bank: CB local offset
first target: CB:03D1
```

`0x0B03D1` が最初のscript本体なので、`0x0B01F9..0x0B03D0` までが pointer table になる。  
236本という本数は装備表のID数とほぼ一致しており、Goal 7の本命テーブルとして扱える。

---

## 2. 上位script形式

装備IDごとのentryは、まず上位scriptを持つ。

デフォルト処理は以下。

```text
84:03DB;83:03E1;82:0408;00
```

これは、装備効果処理の標準hook列と見てよい。

現時点の安全な仮ラベル:

| command | 仮ラベル | 備考 |
|---|---|---|
| `84 ptr` | hook84 / pre-main hook候補 | defaultは `03DB` |
| `83 ptr` | hook83 / effect body候補 | defaultは `03E1` |
| `82 ptr` | hook82 / post/common hook候補 | defaultは `0408` |
| `C1 ptr` | extra hook C1 | 四神刀・夕凪/朝凪など |
| `C2 ptr` | extra hook C2 | 朝凪/ドス系など |
| `C8 ptr` | extra hook C8 | 酒呑、包丁、錫杖系など |
| `00` | end | 上位script終端 |

---

## 3. 件数

| 種別 | 件数 |
|---|---:|
| 全entry | 236 |
| デフォルト上位script | 204 |
| 特殊上位script | 32 |

つまり、現時点では **204件がデフォルト、32件が特殊処理持ち**。

---

## 4. 特殊処理持ちの主な装備

特殊上位scriptは以下に集中している。

| 系統 | 装備ID |
|---|---|
| 四神刀系 | 16-20周辺 |
| 夕凪/朝凪モリ | 60-61 |
| 包丁/ドス/名刀系 | 114-130 |
| 錫杖系 | 184-187 |
| かぎづめ周辺 | 207, 209 |
| extra/sentinel | 234, 235 |

`玄武の刀 / 白虎の刀 / 朱雀の刀 / 青龍の刀 / 酒呑の剣` が明確に特殊scriptを持つこと、  
また包丁・ドス・名刀系が `83/C8` hook差替を多用していることが分かった。

---

## 5. 重要な補正

以前の装備表ダンプで見えていた `flag0/flag1/flag2` は、旧baseのずれにより誤解を生みやすい。  
Goal 7では、装備表先頭3バイトではなく、**`0x0B01F9` の装備ID別pointer table** を主線として扱う。

---

## 6. Goal 7進捗更新

| Goal | 旧 | 新 | 理由 |
|---:|---:|---:|---|
| 7. 武器特殊能力サブシステムの整理 | 18% | 42% | 装備ID別pointer table、上位script形式、特殊装備32件を特定 |

---

## 7. 次に攻める箇所

1. default hook `03DB / 03E1 / 0408` の意味を確定する  
2. `83` hook差替先を効果カテゴリ別に分類する  
3. `C1/C2/C8` extra hookの命令体系を切る  
4. 四神刀5本、夕凪/朝凪、包丁/ドス系、錫杖系を個別仕様表にする  
5. runtimeでは攻撃時に装備ID→`0x0B01F9[ID]`が引かれるかwatchする  

---

## 8. 現時点の仮説

このサブシステムは、単純な「武器ID→特殊効果番号」ではなく、

```text
装備ID
  -> 0x0B01F9 pointer table
  -> top-level effect script
  -> hook82/83/84 + optional C1/C2/C8
  -> 下位script / battle effect / 表示・状態処理
```

という **装備ID別mini-script VM** と見るのが自然。
