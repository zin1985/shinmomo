# VM time slicing

作業仮説:
- NPC/event objectは全フレームで重い処理を行わず、waitにより実行頻度を下げる。
- これはGoal13本体側の「処理軽減」候補として扱う。

注意:
- これはロジックモデルであり、実コードの距離判定・culling本体は未確定。
