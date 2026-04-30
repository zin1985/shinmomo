# Snes9x 実行時VRAM/CGRAM/tilemap dump手順

## 1. Snes9xでLuaを読み込む

`shinmomo_vram_cgram_tilemap_dump_v1_snes9x.lua` を読み込む。

起動すると以下が出る。

```text
TRACE_GRAPHICS_DUMP_V1_READY
```

デフォルトでは起動直後に1回dumpする設定。
出力先はSnes9xのカレントディレクトリ配下の `shinmomo_vram_dumps/`。

## 2. 出力されるもの

```text
vram_frameXXXXXX.bin          VRAM 64KB
cgram_frameXXXXXX.bin         CGRAM 512 bytes（環境にdomainがあれば）
oam_frameXXXXXX.bin           OAM 544 bytes（環境にdomainがあれば）
tilemap_pages_frameXXXXXX.csv VRAM上の0x800単位tilemap page解析
state_frameXXXXXX.txt         12AA等の状態メモ
```

## 3. PNG化

dumpフォルダをPC側に置いて、以下を実行。

```bash
python shinmomo_render_vram_dump_v1.py shinmomo_vram_dumps --bpp 4 --tile-base 0x0000
python shinmomo_render_vram_dump_v1.py shinmomo_vram_dumps --bpp 2 --tile-base 0x0000
```

`rendered/` にtile sheetとtilemap page PNGが出る。

## 4. 注意

BGごとの正しいtile base / tilemap baseはPPU設定 $2107..$210C に依存する。
Lua環境からPPU registerが読めない場合があるので、まずは全tilemap pageを出し、見えるページを絞る運用にしている。
