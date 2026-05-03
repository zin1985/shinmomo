# ShinVM DSL draft

このDSLは、ROM内のイベント/NPC/VM候補blobを人間が編集し、後でCランタイムへ変換するための中間表現です。

## 最小構文

```text
blob F09A_candidate @0x03F09A {
  0x0000: COMMAND 0x20 0x01
  0x0003: BRANCH_LIKE 0x80 0xFF
  0x0005: END
}
```

## 指令

- `COMMAND xx yy`: opcode `07 xx yy` 相当の作業仮説。
- `BRANCH_LIKE op arg`: `80` / `FF` 系の仮分岐。
- `BYTE xx`: 未解読バイト。
- `END`: 仮終端。

このDSLは完全仕様ではありません。Table A / command_table が確定したら `COMMAND` の意味を具体名へ置換します。
