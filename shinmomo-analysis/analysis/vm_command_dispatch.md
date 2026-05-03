# VM command dispatch

後半Runでは `opcode 0x07 = command呼び出し` と仮定した。

本パッケージではこの仮説をCランタイムで再現するが、確定とはしない。
Table A / command_tableが未特定なので、`0x07` は `EVENT` placeholderとして処理する。
