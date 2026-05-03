# `$87:82C0` VM reader候補とF09A系blobモデル（2026-05-03）

## 現時点の安全な結論

- `$87:82C0..83xx` は object-slot pointer reader 候補として強い
- ただし全object共通ではない
- `$87:F09A / F0DB / F0C6 / F0CD / F0D4` は target-side blob label候補
- `0x39850 / 0x39993` row末尾wordが直接 `$0759/$0799` に入る証拠は未発見

## F09A周辺

`data/hexdumps/vm_blob_f09a.hex.txt` に抽出済み。

F09A直後は、単純な固定長テーブルというより、script/data/native helperが混在している可能性がある。
そのため、まず以下に分ける必要がある。

```text
1. script-like byte stream
2. native code
3. offset / coordinate / resource table
```

## 後半RunのVM/command仮説について

このスレッド後半では、VMをAI step scheduler / command dispatcherとしてモデル化した。
ただし、以下は未検証である。

- Table A実体
- command_table実体
- opcode 0x07のdispatch確定
- `$0799` wait完全固定

したがって、現時点では「今後検証する作業仮説」として扱う。
