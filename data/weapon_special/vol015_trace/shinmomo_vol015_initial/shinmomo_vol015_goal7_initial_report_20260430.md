# 新桃太郎伝説解析 vol015 初回メモ（2026-04-30）

## 対象
- GitHub current master と 2026-04-30 goals v2 を踏まえ、今回は Goal 7（武器特殊能力サブシステム）を主対象にした。
- ローカルROM: `Shin Momotarou Densetsu (J).smc`
- ROM size: `2,097,152` bytes

## 1. 今回の確認結果

### 1.1 `0x0B01F9` は装備ID別 script-pack pointer table と見てよい
- table base: `0x0B01F9`
- entry size: 2 bytes
- entry count: 236
- ただし実装備表は 234件側なので、entry 234/235 は sentinel / table boundary spill として扱うのが安全。
- 各 entry は CB bank local offset を指す。

### 1.2 top-level script-pack は `hook_id + ptr16` 反復、`00`終端
デフォルト entry:
```text
84 -> 03DB
83 -> 03E1
82 -> 0408
00
```

意味の仮置き:
- `84`: 常時/前処理 hook 候補
- `83`: 攻撃・発動判定 hook 候補
- `82`: default tail / 共通 fallback hook 候補
- `C1/C2/C8`: 特殊武器だけが持つ追加 hook。単なる op83 selector ではなく、top-level hook class として扱うべき。

### 1.3 特殊処理持ちは 32 entries。ただし実装備として読むなら 30 entries + sentinel 2
実装備側の特殊処理:
30 entries

hook ID パターン別:
- `84 83 82`: 5件 / 117:牛切り包丁, 121:骨切り包丁, 130:菊一文字, 207:なし, 209:鬼のかぎづめ
- `84 83 82 C1`: 5件 / 16:玄武の刀, 17:白虎の刀, 18:朱雀の刀, 19:青龍の刀, 60:夕凪のモリ
- `84 83 82 C1 C2`: 1件 / 61:朝凪のモリ
- `84 83 82 C8`: 5件 / 20:酒呑の剣, 184:きんたんの錫杖, 185:稲妻の錫杖, 186:魔よけの錫杖, 187:鹿角の錫杖
- `84 83 C8 82`: 13件 / 114:出刃包丁, 115:小出刃包丁, 116:薄切り包丁, 118:葉切り包丁, 119:合出刃包丁, 120:柳刃包丁, 122:切り出し包丁, 124:長ドス, 125:隼のドス, 126:団十郎, 127:村雨, 128:村正, 129:孫六
- `84 83 C8 C2 82`: 1件 / 123:ドス

### 1.4 master long pointer table側の位置
`0x0AC03C` 付近に long pointer table があり、その index 2 が `CB:01F9`。
```text
index 0: CACBC8
index 1: CADB47
index 2: CB01F9  <- weapon special pointer table
index 3: CB0FFC
index 4: CB28B2
index 5: CB6BAB
index 6: CB82F1
index 7: CBA668
```
これにより、武器特殊能力 table は孤立した単体表ではなく、CA/CB系の大きな battle/effect script-pack master table の一要素と見た方が自然。

## 2. 重要サンプル bytes

```json
{
  "default_top_03D1": "84 db 03 83 e1 03 82 08 04 00 a0 e2 dc ca b6 b5",
  "default_84_body_03DB": "a0 e2 dc ca b6 b5 02 35 4f 02 23 19 08 d5 64 03 e0 1a 64 03 00 4f 02 23 19 07 d5 64 03 e0 d0 64",
  "default_83_body_03E1": "02 35 4f 02 23 19 08 d5 64 03 e0 1a 64 03 00 4f 02 23 19 07 d5 64 03 e0 d0 64 03 c0 ec b3 06 a4 00 b2 04 a4 01 c0 b5 b1",
  "default_82_body_0408": "b1 db 03 cb b0 84 db 03 83 e1 03 82",
  "genbu_83_04B0": "a0 e1 03 cb a4 02 c0 b5 a0 11 dd ca b6 b4 04 c0 b5 50 00 a4 03 69 46 ce 22 d5 3b 19 e0 d0 86 19 d5 8b 19 e0 a0 a4 1a cb",
  "suzaku_84_051C": "a0 4e fb ca b6 b5 a0 e1 03 cb a4 06 c0 b5 5d 03 b4 06 b1 34 85 cb a0 11 dd ca b6 b4 04 c0 b5 a4 07 69 41 ce 15 d5 3b 19",
  "deba_83_09DF": "a0 e1 03 cb a4 0f c0 b5 39 03 b3 03 b0 4f 02 23 19 02 dd 6e 1d e0 69 2f 5d 09 e0 2e 01 51 00 a4 10 a0 f5 7f cb b0 84 db",
  "shakujo_83_0D74": "a0 e1 03 cb a4 1a c0 b5 39 07 b3 03 b0 4f 02 23 19 02 dd 6e 1d e0 69 2f 5d 09 e0 2e 01 a4 1b 8d 1a a0 f5 7f cb 8e b0 84"
}
```

## 3. 認識更新

### 更新1
前回の「op83 selector体系」だけで見ると狭い。  
今回の構造上、まず top-level hook class `82/83/84/C1/C2/C8` があり、その先の subscript 内に `A4/B2/C0/B5/B1/A0...` などの mini-VM 命令がある二層構造。

### 更新2
`A4 xx` は引き続き result/return selector 即値セット候補だが、`C1/C2/C8` が top-level hookとして出るため、`C8` を「op83 selector」と混ぜない方がよい。

### 更新3
ID 234/235 は旧メモ通り extra/sentinel でよいが、実装備表CSV側の件数と照合すると、通常の武器特殊能力リストからは除外した方が安全。

## 4. 次回の攻め筋

1. `0x0AC03C` master table を読む CPU側/VM側 runner を探す。
2. index 2 = `CB:01F9` を選ぶ上流値が「装備特殊能力」なのか「battle effect category」なのかを確定する。
3. top-level hook `82/83/84/C1/C2/C8` の呼び分けタイミングを探す。
4. inner mini-VM opcode `A4/B2/C0/B5/B1/A0/B3/B4/D0/E0/CE` の長さ表を作る。
5. 特殊30装備について「hook class -> subscript ptr -> selector/effect候補」をCSV化する。

## 5. 出力
- `goal7_weapon_hook_special_entries_20260430.csv`
