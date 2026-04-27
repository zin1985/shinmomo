# 新桃太郎伝説 Goal 4: `81:8D87` 戻り4値の意味解析
作成日: 2026-04-26

## 1. 結論

`81:8D87` は、`$1569[0..9]` の logical object list を走査する **object/actor count aggregator**。

戻り4値は以下。

| 戻り先 | 意味 | 詳細 |
|---|---|---|
| `$09` | 有効通常actor数 | `$1569`内のID `<0x17` のうち、`$180A[entity-1] bit7` がclearの数 |
| `$0A` | 通常actor総数 | `$1569`内のID `<0x17` の数 |
| `$0C` | 全logical object数 | `$1569`内の非ゼロID総数 |
| `$0D` | special object数 | `$0C - $0A`。ID `>=0x17` の数 |

これにより、Goal 4「`81:8D87` の戻り4値」は大きく前進。

---

## 2. ルーチン本体

`81:8D87` = file offset `0x018D87`

```asm
81:8D87  5A             PHY
81:8D88  AD 20 16       LDA $1620
81:8D8B  48             PHA

81:8D8C  64 09          STZ $09
81:8D8E  64 0A          STZ $0A
81:8D90  64 0C          STZ $0C
81:8D92  64 0D          STZ $0D
81:8D94  A0 00          LDY #$00

loop:
81:8D96  B9 69 15       LDA $1569,Y
81:8D99  F0 1D          BEQ next

81:8D9B  E6 0C          INC $0C          ; nonzero object count
81:8D9D  85 0D          STA $0D          ; current ID temp
81:8D9F  C9 17          CMP #$17
81:8DA1  B0 15          BCS next         ; ID >= 0x17 is special

81:8DA3  E6 0A          INC $0A          ; normal actor count
81:8DA5  A5 0D          LDA $0D
81:8DA7  8D 20 16       STA $1620        ; current entity
81:8DAA  A9 80          LDA #$80
81:8DAC  85 1E          STA $1E
81:8DAE  A9 3A          LDA #$3A
81:8DB0  22 AC 86 85    JSL $85:86AC     ; test $180A[entity-1] & 0x80 == 0
81:8DB4  90 02          BCC next
81:8DB6  E6 09          INC $09          ; visible/available normal actor

next:
81:8DB8  C8             INY
81:8DB9  C0 0A          CPY #$0A
81:8DBB  90 D9          BCC loop

81:8DBD  A5 0C          LDA $0C
81:8DBF  38             SEC
81:8DC0  E5 0A          SBC $0A
81:8DC2  85 0D          STA $0D          ; special count = total - normal

81:8DC4  68             PLA
81:8DC5  8D 20 16       STA $1620
81:8DC8  7A             PLY
81:8DC9  6B             RTL
```

---

## 3. 擬似コード

```c
saved_1620 = $1620;

$09 = 0; // visible normal actor count
$0A = 0; // normal actor count
$0C = 0; // total logical object count
$0D = 0; // special object count, computed at end

for (Y = 0; Y < 10; Y++) {
    id = $1569[Y];
    if (id == 0) continue;

    $0C++;

    if (id < 0x17) {
        $0A++;

        $1620 = id;
        $1E = 0x80;
        if (condition_3A_test_clear($180A[id-1], 0x80)) {
            $09++;
        }
    }
}

$0D = $0C - $0A;
$1620 = saved_1620;
return;
```

---

## 4. 意味づけ

### `$09`: 有効通常actor数
通常actor ID `<0x17` のうち、`$180A bit7` がclearの数。  
表示可能 / hiddenでない / suppressedでない通常actorの数。

### `$0A`: 通常actor総数
`$1569`に入っている通常actor ID `<0x17` の数。  
`$180A bit7` は見ない。

### `$0C`: 全logical object数
`$1569`の非ゼロID総数。  
通常actorもspecial/effectも含む。

### `$0D`: special object数
`$0C - $0A`。  
ID `>=0x17` の special logical object / effect / companion / temporary actor 数。

---

## 5. 呼び出し元の意味

### 5-1. `C4:8D50 / 8D60 / 8D6B / 8D76`

C4 script handlerの内部で、`81:8D87` の4値を script側へ返すwrapper群がある。

| address | 返す値 | 意味 |
|---|---|---|
| `C4:8D50` | `$09` | 有効通常actor数 |
| `C4:8D60` | `$0A` | 通常actor総数 |
| `C4:8D6B` | `$0C` | 全logical object数 |
| `C4:8D76` | `$0D` | special object数 |

これにより、script VM側も logical object list の人数/特殊数を条件判定に使える。

### 5-2. `C1:D64A`

`81:8D87` 後に `$0A` を見ている。

```asm
JSL $81:8D87
LDA $1569
STA $1929
LDA $0A
CMP #$01
```

通常actorが1体だけかを見て、後続処理を変えている。  
party/follower/leader周辺の処理候補。

### 5-3. `C3:A050`

`81:8D87` 後に `$0A` を見ている。

```asm
JSL $81:8D87
LDA $1569
STA $1929
LDA $0A
CMP #$01
```

こちらも通常actor数による分岐。  
イベント/画面演出側で、単独actorか複数actorかを切り替える処理候補。

### 5-4. `C5:9C5D`

`81:8D87` 後に `$0D` を見ている。

```asm
JSL $81:8D87
LDA $0D
BEQ ...
CMP #$02
```

special object数が0か、2未満かを見ている。  
特殊object/effect/同行補助の空きや個数による分岐候補。

---

## 6. Goal 13との接続

これまでのNPC大量表示軽減は以下。

```text
C4 opcode 0x1C
  candidate 0x10..0x13を走査
  $195Eで消費済みをskip
  $80DA57でentity解決
  $180A bit7でhidden/suppressedを除外
  $1958へ出力

C1:9474
  通常actor最大4体cap
  全logical object最大10slot

81:8D87
  $1569を数え、通常/有効通常/全体/special数を返す

OAM builder
  object/piece単位でclip/skip
```

`81:8D87` は、表示系の状態をscriptやイベント側へ返す **count feedback helper** と見てよい。

---

## 7. Goal進捗更新

| Goal | 旧 | 新 | 理由 |
|---:|---:|---:|---|
| 4. `81:8D87` の戻り4値の意味を確定する | 30% | 85% | 4戻り値の意味がほぼ確定 |
| 13. NPC大量表示時の処理軽減ロジック | 97% | 98% | logical listのcount feedbackまで接続 |
| 12. 全体構造の人間可読化 | 99% | 99% | object管理層の説明が補強 |

---

## 8. 残り

Goal 4を100%へ持っていくには以下。

1. `C4:8D50/8D60/8D6B/8D76` がscript opcode上で何番のsubcommandか確定する  
2. `$09` を参照する全callerのゲーム内文脈をラベル付けする  
3. `$0D` special object数の実例をruntimeで確認する  
4. `$180A bit7` のゲーム内ラベルを確定する  

