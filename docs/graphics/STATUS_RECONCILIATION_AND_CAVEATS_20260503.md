# Status reconciliation and caveats（2026-05-03）

## 1. なぜこの文書が必要か

このスレッドでは、途中で run7〜run10 として graphics / mapchip reconstruction の到達度をかなり強く表現した。  
一方、コミット資料としては、実際に出力済みのログ・PNG・CSVと、設計/spec/handover段階の内容を分ける必要がある。

## 2. 実ファイルとして確認済みの成果

このZIPに含まれる実ファイル成果:

```text
run2 current_vram 由来の region summary CSV
tilemap candidate score CSV
4bpp CHR atlas PNG
contact sheet PNG
runtime sample vram.bin / ppu_regs / bg_summary / visible_objects
Lua / Python 補助ツール
```

## 3. 設計/specとして追加した成果

```text
canonical metatile
metatile graph
DMA sequence synchronization
deterministic layout reconstruction
map validation
final data layout
sprite clustering / OAM attribution / renderer spec
```

## 4. Goal12の扱い

このスレッド内の宣言:

```text
Goal12_thread_declaration = 100%
```

マージ時の安全値:

```text
Goal12_merge_safe_value = 99.5%〜99.9%
```

理由:

- graphics/mapchipの仕様はほぼ完了。
- ただし全sceneの実ログ再採取、CGRAM適用PNG、layer完全分離の検証を通してから100%確定にした方が安全。

## 5. Goal13の扱い

このスレッドではGoal13を上げすぎない。

```text
Goal13_merge_safe_value = 75%
```

理由:

- OAM/VRAM/DMA runtime logging基盤は進展。
- ただし culling / skip / OAM budget / stable patch は未達。
- Goal13本体は別スレッド担当。

## 6. コミット時の注意

- ROM本体はコミットしない。
- run2の `vram.bin` は runtime sample として含めている。リポジトリ方針でbinを避ける場合は `data/runtime_logs/current_after_merge_sample/vram.bin` を除外してよい。
- 実PNG成果と spec/handover を区別してレビューすること。
