# 新桃 DA:3800 stream 外部デコード要約（2026-03-14）

対象ROM: `Shin Momotarou Densetsu (J).smc`

## 1. 概要

- pointer table は `DA:3800`（ROM `0x1A3800`）
- 22本の 16bit little-endian pointer から各 stream 先頭へ飛ぶ
- 各 stream の先頭1byteは `x_start/x_end` を 4bit ずつ詰めた header とみなす
  - `x_start = header >> 4`
  - `x_end   = header & 0x0F`
  - `width   = x_end - x_start + 1`
- 1 record の入力長は次式で割り切れた
  - `record_input_bytes = width + ceil(width/2) + width + ceil(width/2)`
- stream 1〜21 は「次 pointer までの長さ」から件数がきれいに求まった
- stream 22 は終端 pointer が無いので、周辺 stream と同じく 64件で打ち切った

## 2. 外部デコード方針（A963 / A9AD / AA03 / AA18 相当の候補）

- record は以下の4区間で読む
  1. `seg0`: `width` bytes
  2. `seg1_packed`: `ceil(width/2)` bytes
  3. `seg2`: `width` bytes
  4. `seg3_packed`: `ceil(width/2)` bytes
- packed 部は 1byte を high nibble / low nibble に分けて 2要素化した
- 可視化では 16列固定の 4行バッファを作り、`x_start..x_end` にデータを差し込んだ
  - 行0 = `seg0`
  - 行1 = `seg1`（0..15 を見やすくするため `*17`）
  - 行2 = `seg2`
  - 行3 = `seg3`（同上）
- これは**候補ビュー**であり、実機最終VRAM配置の完全再現ではない

## 3. stream 一覧

|   stream_id | table_entry_rom   | pointer_lo16   | target_rom   | target_snes   | header_byte   |   x_start |   x_end |   width |   record_input_bytes |   record_count |   stream_span_bytes_used | stream_end_rom   | tail_mode                              | note                                                 |
|------------:|:------------------|:---------------|:-------------|:--------------|:--------------|----------:|--------:|--------:|---------------------:|---------------:|-------------------------:|:-----------------|:---------------------------------------|:-----------------------------------------------------|
|           1 | 0x1A3800          | 0x382C         | 0x1A382C     | DA:382C       | 0x1F          |         1 |      15 |      15 |                   46 |             62 |                     2853 | 0x1A4350         | next-pointer bounded                   |                                                      |
|           2 | 0x1A3802          | 0x4351         | 0x1A4351     | DA:4351       | 0x2F          |         2 |      15 |      14 |                   42 |             47 |                     1975 | 0x1A4B07         | next-pointer bounded                   |                                                      |
|           3 | 0x1A3804          | 0x4B08         | 0x1A4B08     | DA:4B08       | 0x07          |         0 |       7 |       8 |                   24 |             24 |                      577 | 0x1A4D48         | next-pointer bounded                   |                                                      |
|           4 | 0x1A3806          | 0x4D49         | 0x1A4D49     | DA:4D49       | 0x5F          |         5 |      15 |      11 |                   34 |             10 |                      341 | 0x1A4E9D         | next-pointer bounded                   |                                                      |
|           5 | 0x1A3808          | 0x4E9E         | 0x1A4E9E     | DA:4E9E       | 0x2F          |         2 |      15 |      14 |                   42 |             47 |                     1975 | 0x1A5654         | next-pointer bounded                   |                                                      |
|           6 | 0x1A380A          | 0x5655         | 0x1A5655     | DA:5655       | 0x07          |         0 |       7 |       8 |                   24 |             24 |                      577 | 0x1A5895         | next-pointer bounded                   |                                                      |
|           7 | 0x1A380C          | 0x5896         | 0x1A5896     | DA:5896       | 0x6F          |         6 |      15 |      10 |                   30 |              9 |                      271 | 0x1A59A4         | next-pointer bounded                   |                                                      |
|           8 | 0x1A380E          | 0x59A5         | 0x1A59A5     | DA:59A5       | 0x1F          |         1 |      15 |      15 |                   46 |             64 |                     2945 | 0x1A6525         | next-pointer bounded                   |                                                      |
|           9 | 0x1A3810          | 0x6526         | 0x1A6526     | DA:6526       | 0x1F          |         1 |      15 |      15 |                   46 |             64 |                     2945 | 0x1A70A6         | next-pointer bounded                   |                                                      |
|          10 | 0x1A3812          | 0x70A7         | 0x1A70A7     | DA:70A7       | 0x1F          |         1 |      15 |      15 |                   46 |             64 |                     2945 | 0x1A7C27         | next-pointer bounded                   |                                                      |
|          11 | 0x1A3814          | 0x7C28         | 0x1A7C28     | DA:7C28       | 0x1F          |         1 |      15 |      15 |                   46 |             64 |                     2945 | 0x1A87A8         | next-pointer bounded                   |                                                      |
|          12 | 0x1A3816          | 0x87A9         | 0x1A87A9     | DA:87A9       | 0x1F          |         1 |      15 |      15 |                   46 |             64 |                     2945 | 0x1A9329         | next-pointer bounded                   |                                                      |
|          13 | 0x1A3818          | 0x932A         | 0x1A932A     | DA:932A       | 0x1F          |         1 |      15 |      15 |                   46 |             64 |                     2945 | 0x1A9EAA         | next-pointer bounded                   |                                                      |
|          14 | 0x1A381A          | 0x9EAB         | 0x1A9EAB     | DA:9EAB       | 0x1F          |         1 |      15 |      15 |                   46 |             64 |                     2945 | 0x1AAA2B         | next-pointer bounded                   |                                                      |
|          15 | 0x1A381C          | 0xAA2C         | 0x1AAA2C     | DA:AA2C       | 0x1F          |         1 |      15 |      15 |                   46 |             64 |                     2945 | 0x1AB5AC         | next-pointer bounded                   |                                                      |
|          16 | 0x1A381E          | 0xB5AD         | 0x1AB5AD     | DA:B5AD       | 0x1F          |         1 |      15 |      15 |                   46 |             56 |                     2577 | 0x1ABFBD         | next-pointer bounded                   |                                                      |
|          17 | 0x1A3820          | 0xBFBE         | 0x1ABFBE     | DA:BFBE       | 0x1F          |         1 |      15 |      15 |                   46 |             64 |                     2945 | 0x1ACB3E         | next-pointer bounded                   |                                                      |
|          18 | 0x1A3822          | 0xCB3F         | 0x1ACB3F     | DA:CB3F       | 0x1F          |         1 |      15 |      15 |                   46 |             64 |                     2945 | 0x1AD6BF         | next-pointer bounded                   |                                                      |
|          19 | 0x1A3824          | 0xD6C0         | 0x1AD6C0     | DA:D6C0       | 0x1F          |         1 |      15 |      15 |                   46 |             64 |                     2945 | 0x1AE240         | next-pointer bounded                   |                                                      |
|          20 | 0x1A3826          | 0xE241         | 0x1AE241     | DA:E241       | 0x1F          |         1 |      15 |      15 |                   46 |             64 |                     2945 | 0x1AEDC1         | next-pointer bounded                   |                                                      |
|          21 | 0x1A3828          | 0xEDC2         | 0x1AEDC2     | DA:EDC2       | 0x1F          |         1 |      15 |      15 |                   46 |             64 |                     2945 | 0x1AF942         | next-pointer bounded                   |                                                      |
|          22 | 0x1A382A          | 0xF943         | 0x1AF943     | DA:F943       | 0x1F          |         1 |      15 |      15 |                   46 |             64 |                     2945 | 0x1B04C3         | fixed 64 records (no terminal pointer) | 0x1B04C4以降は別データっぽいため今回は64件で打ち切り |

## 4. 備考

- stream 1 は 62件、stream 17 は 56件、stream 22 は暫定64件で、それ以外は次 pointer までで自然に割り切れた
- 多くの stream は header `0x1F`（x=1..15, width=15）で、入力 record 長 46 bytes になった
- `0x1B04C4` 以降は見た目が別データ寄りで、今回は stream 22 の対象外とした
- まだ `ABF1 / AC65 / AC8C / ACCA` 相当の shuffle は外部で再現していない
- したがって今回の PNG は「入口 stream を機械的にほどいた候補ビュー」である
