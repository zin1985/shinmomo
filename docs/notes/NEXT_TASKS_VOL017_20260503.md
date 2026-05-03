# 次回タスク vol017差分後 (2026-05-03)

## 最優先

1. `$87:82C0` caller / entry condition特定
   - `$87:82C0` にJSR/JMPする箇所を探す
   - object type / state / routine IDを特定

2. `$87:838F` 周辺の `($2A),Y` readerを命令単位で切る
   - YがPCか、ただのtable indexかを確定
   - opcode/commandモデルを実コードで検証

3. F09A/F0DB/F0C6系blobの型分解
   - script-like stream
   - native code
   - coordinate/offset table
   - resource pointer table

4. `0x41A10 -> 0x39850/39993` reader huntへ戻る
   - 8-byte table reader
   - 9-byte row evaluator
   - target-side blob runner

5. Goal13本体
   - `$0A61` active object list
   - C0:B100
   - B294 table
   - `$0A1C/$0B27`
   - OAM runtime logとの照合

## 別スレッドへ渡す内容

```text
このスレッドでは、$0759/$0799を一律pointerではなくobject type依存fieldとして再分類した。
Goal13のOAM/active logを読む時は、slot意味をobject type別に分ける必要がある。
BG安定 + OAM変化だけでなく、同frameのobject routine/typeが必要。
```
