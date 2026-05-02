# 新桃太郎伝説 vol016 戦闘時グラフィックログ解析メモ（2026-05-01）

## 入力概要
- `manifest.csv`: 866 bytes
- `frame_summary.csv`: 1008 bytes
- `visible_object_summary.csv`: 215 bytes
- `visible_objects.csv`: 434 bytes
- `bg_summary.csv`: 273 bytes
- `ppu_regs_capture.csv`: 1188 bytes
- `dma_trigger_log.csv`: 151 bytes
- `ppu_write_log.csv`: 23 bytes
- `vram.bin`: 65536 bytes

## 観測結果
- `manifest.csv` では frame `099282 -> 100500` にかけて `vram_hash` が `BBFD -> 6CF4 -> 1BF6 -> 53D3 -> FED7` と変化。戦闘突入/遷移中に VRAM は更新されている。
- `visible_object_summary.csv` では active object count が `11 -> 5 -> 7 -> 5` と変化。戦闘画面構成時に object list が再構築されている。
- `dma_trigger_log.csv` と `ppu_write_log.csv` はヘッダのみ。DMA/PPU write hook は今回も未捕捉。
- `ppu_regs_capture.csv` / `bg_summary.csv` のレジスタ値はゼロ寄り。BGMODE/BGSC/char base はログからではなく VRAM内容から推定する段階。

## 戦闘VRAMの暫定読み
- 同名 `vram.bin` 上書きのため、実体として解析できたのは最後に残ったスナップショット。manifest 上では `frame_100500` 相当とみるのが自然。
- フィールドログと同様、`VRAM 0x0000..0x7FFF` は tilemap/name table 候補として扱える。
- `char_base=0x8000` の 4bpp / 2bpp タイルシートを出力済み。戦闘は背景に加えて object/OAM 側の寄与が大きいため、背景tilemapのみでは完全再現にならない。
- 第一候補は `map_base=0x0000..0x7FFF` の比較と、`char_base=0x8000` 付近のタイル資材。

## visible object list
| slot | next | prev | sort | x16 | y16 | type_0B25 | attr_0AE5 | state_0E27 | raw0C65 | raw0BA5 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 3 | 0 | 08 | FFC0 | 0000 | 34 | 53 | 41 | 20 | E4 |
| 3 | 4 | 2 | 38 | 0400 | 0500 | 34 | 57 | 17 | D8 | 48 |
| 4 | 5 | 3 | 38 | FFD0 | 0600 | 34 | 6E | 1C | D8 | 88 |
| 5 | 1 | 4 | 3A | 0200 | 0304 | 2A | 30 | 47 | B0 | 80 |
| 1 | 255 | 5 | FF | 0000 | 0000 | 00 | 01 | 2F | 00 | 00 |

### object側の読み
- active_head は `02`。linked list は `2 -> 3 -> 4 -> 5 -> 1 -> FF`。
- slot 2/3/4 は `type_0B25=34` で同系統。戦闘中の主要表示オブジェクト群候補。
- slot 5 は `type_0B25=2A` で別系統。UI/カーソル/エフェクト/影などの候補。
- slot 1 は `type_0B25=00` だが list末尾に残る。番兵、非表示予約、親オブジェクト候補。

## 次にやること
- `frame_099282` などの各ディレクトリを丸ごと保持し、複数 `vram.bin` を比較する。
- `cgram.bin` を同時保存する。現状は疑似色/グレースケール復元のみ。
- PPU/DMA hook の domain を `BUS`, `System Bus`, `WRAM` など複数試行する Lua に修正する。
- `$0B25/$0AE5/$0E27/$0C65/$0BA5` を `C0:AF33/B03D/B100/B294` と接続し、戦闘OAM生成線へ戻す。

## 追加訂正：戦闘VRAMはフィールドと違い `0x0000..0x7FFF` がグラフィック本体寄り

フィールド時は `VRAM 0x0000..0x7FFF` を tilemap/name table として読むと自然だったが、今回の戦闘ログでは同領域を **4bpp linear tile sheet** として読むと、山・滝・地面のような戦闘背景、UI枠、数字/文字グリフがまとまって見える。

したがって戦闘画面では、少なくともこのスナップショットについては次の仮説が最有力。

- `VRAM 0x0000..0x7FFF`: 戦闘背景/戦闘UI/文字グリフの 4bpp CHR 資材本体候補
- `VRAM 0x8000..0xC000`: 会話/メッセージ/戦闘表示用の文字・記号・UI素材候補
- `VRAM 0xC000..0xE000`: 数字、状態表示、短い日本語ラベルなどのUI素材候補
- `VRAM 0xE000..0x10000`: 未整理。追加スプライト/ウィンドウ/空き領域候補

特に `battle_vram0000_8000_4bpp_linear_1x.png` は、戦闘背景復元の本命画像として扱う。
前半で出した tilemap candidate は、戦闘ログでは「候補探索の副産物」であり、今回の主線は **tilemap復元よりCHR資材復元**。
