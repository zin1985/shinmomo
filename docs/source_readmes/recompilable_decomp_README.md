# Shin Momotarou Densetsu recompilable decomp scaffold 2026-05-03

このパッケージは、現時点で解析済みの領域を **再コンパイル可能なC99プロジェクト + ShinVM DSL/IR** に落としたものです。

重要:

- ROM本体は含めていません。
- これは「全ゲームを完全にCへ戻したもの」ではなく、**既知テーブルとVM仮説をC/DSL化した再コンパイル可能な足場**です。
- 既知の道具表・装備表・`0x41A10` 条件表候補・`0x398xx/0x399xx` 9-byte row候補はC構造体として生成済みです。
- 未確定のVM command table / Table A / opcode意味は、Cランタイム上では `UNKNOWN_*` として安全に表現します。

## すぐ試す

```bash
cd recompilable_c
make
./build/shinmomo_decomp_demo
```

## ROMから再生成する

```bash
python3 tools/decompile_rom_to_c.py '/path/to/Shin Momotarou Densetsu (J).smc' --out recompilable_c/generated
make -C recompilable_c
```

## 収録範囲

- C99で再コンパイルできるデータ構造とVMランタイム骨格
- ShinVM DSLの暫定仕様
- 既知テーブルのC initializer
- `opcode -> behavior` を埋めていくためのCSVテンプレート
- ROMから同じC/DSLを再生成するPythonツール

## 現時点でC/DSL化済み

- `0x442AC/0x442BF` 系 道具表候補
- `0x449C3/0x449D0` 系 装備表候補
- `0x41A10` 系 8-byte条件分岐表候補
- `0x39847`, `0x39916` 系 9-byte macro row候補
- `0x03F09A` などVM/blob entry候補のカタログ

## まだ未確定

- `0x41A10` reader本体
- `F09A/F0DB`系blobの命令体系
- Table A / command_table の実アドレス
- 全イベント本文の完全逆コンパイル
- ROM全体を再生成できる完全ビルドシステム
