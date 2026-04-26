# 新桃太郎伝説 C4:C8AA script opcode文脈と `$195E` のイベント単位  
作成日: 2026-04-25

## 1. 結論

`C4:C8AA` は direct call される通常サブルーチンではなく、  
C4 script VM の handler table から呼ばれる **script opcode `0x1C` のhandler**。

handler table:

```text
C4:C2DD + opcode*2 -> handler address
```

該当部分:

| opcode | handler | 役割 |
|---:|---|---|
| `0x18` | `C4:C85A` | `$1958` を logical object list へ spawn |
| `0x19` | `C4:C864` | `$1958` を logical object list から remove |
| `0x1A` | `C4:C826` | `$1958` / `$195F` 周辺を使う補助predicate |
| `0x1B` | `C4:C86E` | 現在candidateを `$195E` に消費済みset |
| `0x1C` | `C4:C8AA` | 未消費candidate `0x10..0x13` から次のentityを探し `$1958` に入れる |
| `0x1D` | `C4:C8F8` | 現在candidateが未消費ならsuccess |
| `0x1E` | `C4:C89B` | candidate4本すべて消費済みならsuccess |

これにより、`$195E` は **opcode `0x1B..0x1E` が共有する、1つのcandidate group用の消費済みmask** と見てよい。

---

## 2. dispatcher文脈

`C4:C2D0` 近辺で、script streamの現在byteを読み、handler tableに飛ぶ。

概略:

```asm
C4:C2D0  LDA [$0F]       ; script opcode
C4:C2D2  ASL A
C4:C2D3  TAX
C4:C2D4  LDY #$01
C4:C2D6  JSR $C2DA       ; stream cursor advance / arg setup
C4:C2D9  JMP ($C2DD,X)   ; handler table
```

handler tableの `opcode 0x1C` entry:

```text
table base = C4:C2DD
opcode 0x1C entry offset = C4:C2DD + 0x1C*2 = C4:C315
C4:C315 = AA C8
=> handler C4:C8AA
```

つまり `C4:C8AA` の「呼び出し元」は固定callerではなく、**script opcode byte `0x1C`**。

---

## 3. `$195E` が使われるイベント単位

### 3-1. candidate group

`C4:C8AA` が対象にするcandidateは固定4本。

```text
C4:C8F0 = 10 11 12 13
C4:C8F4 = 01 02 04 08
```

| candidate | bit in `$195E` | 内容 |
|---:|---:|---|
| `0x10` | `0x01` | candidate 0 |
| `0x11` | `0x02` | candidate 1 |
| `0x12` | `0x04` | candidate 2 |
| `0x13` | `0x08` | candidate 3 |

### 3-2. イベント単位の見立て

`$195E` はマップ全体のNPC一覧ではなく、  
**script VM上でcandidate `0x10..0x13` を順に処理する1つのイベント/scene内ローカルな候補消費mask** と見るのが最も自然。

根拠:

1. `C4:C8AA` は `0x10..0x13` だけを対象にする。
2. `$195E` の下位4bitだけを見る。
3. `0x1B` で現在candidateを消費済みにし、`0x1C` で次の未消費候補を探す。
4. `0x1D` で現在candidateが未消費か確認し、`0x1E` で全消費済みを確認する。
5. `$195E` に専用clearがないため、短い命令単位ではなく、上位のscript/event contextで維持される可能性が高い。

したがって、`$195E` のイベント単位は以下。

```text
「candidate 0x10..0x13 を扱うC4 script opcode群が走る1イベント/scene context」
```

---

## 4. opcode 0x18..0x1E の仕様案

### opcode `0x18`: spawn current candidate

```asm
C4:C85A  LDA $1958
C4:C85D  JSL $81:944B
C4:C861  JMP $C357
```

`$1958` に入っているentityを logical object list `$1569` へ投入する。

### opcode `0x19`: remove current candidate

```asm
C4:C864  LDA $1958
C4:C867  JSL $81:94D7
C4:C86B  JMP $C357
```

`$1958` のentityを logical object list から削除する。

### opcode `0x1B`: mark candidate consumed

`C4:C880` で `$1923/$1924` が candidate table に該当するか確認し、  
該当bitを `$195E` にsetする。

```text
$195E |= C4:C8F4[index]
```

### opcode `0x1C`: find next candidate

未消費candidate `0x10..0x13` を順に調べる。

1. `$195E` にbitが立っているcandidateはskip  
2. `$1923=candidate`, `$1924=1` をセット  
3. `$80DA57` で実entityへ解決  
4. `$192A < 0x15` なら `$1958=$192A`  
5. `$8586AC(A=0x3A,$1E=0x80)` で `$180A[entity-1] bit7 clear` を確認  
6. 成功なら `$1957=1` で戻る  

### opcode `0x1D`: candidate unconsumed predicate

現在の `$1923/$1924` が candidate `0x10..0x13/type1` で、  
かつ対応bitが `$195E` に立っていれば failure。

### opcode `0x1E`: all consumed predicate

```text
($195E & 0x0F) == 0x0F なら success
```

---

## 5. script上の使われ方の推定

script sequenceとしては、おそらく以下のように使う。

```text
loop:
    opcode 0x1C  ; 次の未消費candidateを探し $1958 に入れる
    if failure: end

    opcode 0x18  ; $1958 を表示/論理object listへspawn

    ...会話/移動/条件処理...

    opcode 0x1B  ; candidateを消費済みにする

    opcode 0x1E  ; 全candidate消費済みなら終了
    else loop
```

または、個別candidateに対して、

```text
opcode 0x1D  ; まだ未消費か？
opcode 0x18  ; spawn
...
opcode 0x1B  ; consumed
```

のような流れ。

---

## 6. Goal 13への意味

これで、NPC大量表示軽減の「前段イベント単位」がかなり明確になった。

```text
C4 script opcode 0x1C
  candidate 0x10..0x13 の最大4候補だけを見る
  $195Eで消費済みcandidateをskip
  $80DA57で実entityへ解決
  $180A bit7でhidden/suppressedを除外
  $1958へ出力

C4 script opcode 0x18
  $1958をC1:944Bへ渡す

C1:9474
  通常actor最大4体capで$1569へ投入

OAM builder
  object/piece単位でclip/skip
```

`$195E` は「マップ全NPC」ではなく、  
**script candidate group 4本を1イベント内で重複処理しないためのmask** と見るべき。

---

## 7. 進捗更新

Goal 13は **96% -> 97%** としてよい。

理由:

- `C4:C8AA` のopcode番号が確定寄り
- `$195E` がどの命令群で共有されるか確定寄り
- `$195E` のスコープが「candidate 0x10..0x13を扱う1イベント/scene context」と説明可能になった

残り:

1. runtimeでopcode `0x1B..0x1E` の実script列を取る
2. candidate `0x10..0x13` のゲーム内ラベルを確定
3. `$195E` が0に戻る上位context resetを実測
