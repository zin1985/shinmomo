# shinmomo vol013 mode02 mass dump v33

## 目的
ROM上の `$12AA=02` 系会話、つまり `C0:BD98` bitstream/tree decoder で読まれる mode02 会話を、外部CSVへ大量出力するためのオフラインダンパです。

## 重要な考え方
- mode02 は plain text ではありません。
- `C0:BD98` の tree decoder で 1 symbol ずつ復元します。
- `<00>` で1セリフが終わっても、次セリフは **byte境界から始まるとは限りません**。
- そのため `bank:addr` だけでなく、`bitcnt / bitbuf` を含む chain state を保持して連続デコードします。
- 今回の実例では `C8:A7DD` の chain seg2 が、画面に出ていた「北西のおむすびころりんの穴は…」に対応しました。

## 同梱物
- `shinmomo_dump_mode02_dialogues_v33.py`
  - mode02 / BD98 オフラインダンパ本体
- `shinmomo_mode02_chain_C8_A7DD_v33_sample.csv`
  - `C8:A7DD` root のサンプルCSV
- `shinmomo_mode02_chain_C8_A7DD_v33_sample.md`
  - 同サンプルのMarkdown表示版

## 使い方
```bash
python shinmomo_dump_mode02_dialogues_v33.py ^
  --rom "Shin Momotarou Densetsu (J).smc" ^
  --lua shinmomo_trace_dialogue_v28_mode02_bd98_decoder_smallkana_checked_snes9x_20260427.lua ^
  --roots C8:A7DD ^
  --out mode02_C8_A7DD.csv
```

複数rootを指定する例:

```bash
python shinmomo_dump_mode02_dialogues_v33.py ^
  --rom "Shin Momotarou Densetsu (J).smc" ^
  --lua shinmomo_trace_dialogue_v28_mode02_bd98_decoder_smallkana_checked_snes9x_20260427.lua ^
  --roots C8:A7DD C8:F193 C9:4C7A C9:4F83 ^
  --out mode02_roots.csv
```

限定範囲scanの例:

```bash
python shinmomo_dump_mode02_dialogues_v33.py ^
  --rom "Shin Momotarou Densetsu (J).smc" ^
  --lua shinmomo_trace_dialogue_v28_mode02_bd98_decoder_smallkana_checked_snes9x_20260427.lua ^
  --scan C8:A000-C8:B200 ^
  --out scan_C8_A000_B200.csv ^
  --min-score 40
```

## CSV列
- `root`: 入力root
- `seg`: chain内のセリフ番号
- `start_state`: `bank:addr/bitcnt/bitbuf`
- `end_state`: セリフ終端後のstate
- `score`: 日本語らしさの仮スコア
- `raw_tokens`: 復元後の内部token列
- `text`: 復元本文
- `events`: tokenごとの対応

## 注意
scanは候補抽出です。false positiveが混ざります。
本命は、runtime Luaで拾ったroot pointer、またはscript/descriptor解析から逆引きしたroot pointerを入力する方法です。
