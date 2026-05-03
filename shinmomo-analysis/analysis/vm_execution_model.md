# VM execution model

現時点の再コンパイル可能モデルでは、VMを「objectごとにスクリプトを1ステップ進めるランタイム」として実装する。

確定:
- object slotは固定意味ではなくtype依存。
- `$0759/$0799` はpointerとして使われる場面があるが、常にpointerではない。
- `$87:82C0` 周辺は pointer reader / mini-interpreter 候補。

未確定:
- 本物のTable A / command_table実アドレス。
- opcode完全対応表。
