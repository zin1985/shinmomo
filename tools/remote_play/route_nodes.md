# Route-node extension

2026-09-27実機観測:
- ワールド長距離移動は100-220 framesが有効。
- 村内は崖・畑・階段が多く、長押しだけでは施設入口へ到達しにくい。
- 今後の施設探索は landmark -> approach node -> stairs/path node -> door node の短距離経路として記録する。
- mailbox command IDはASCIIのみを使用する。
- response ENOENTは即失敗扱いせず、同じresponseを再読する。

既知landmark:
- 兵 = 兵具屋
- 茶 = 茶店
- 宿 = 宿
