# vol014 スレッド要約 v2（2026-04-30）

## 作業対象

イベント系を避け、非イベント系で伸びやすい Goal 7 / Goal 8 を中心に進めた。

## 進んだ点

- `0x0B01F9` 付近に装備ID別 2-byte pointer table 候補を確認。
- `0x0B03D1` 付近に `84 / 83 / 82` hook列らしき構造を確認。
- `0x0B03E1` 付近を default op83 body候補として整理。
- `0x0B0408` 付近を fallback / op82 default body候補として整理。
- `A4 / C0 / B2 / B5` を mini-VM命令候補として整理。
- ただし、後半で出た `CA:D800` dispatch table / `7E:3000台` VMStatus 仮説は未検証扱いに戻した。

## 次にやること

1. A4 handler を探す。
2. C0 handler を探す。
3. B2 handler を探す。
4. selector値と装備ID・実効果の対応をCSV化する。
