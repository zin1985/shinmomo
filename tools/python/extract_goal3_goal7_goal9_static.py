from pathlib import Path
import csv, zipfile, json, textwrap, hashlib, shutil, datetime
from collections import Counter, defaultdict

BASE = Path('/mnt/data')
ROM_PATH = BASE/'Shin Momotarou Densetsu (J)_original.smc'
EQUIP_CSV = BASE/'shinmomo_equipment_table_dump_20260313.csv'
PREV_G13_MD = BASE/'shinmomo_analysis_progress_20260527.md'
PREV_G13_CSV = BASE/'shinmomo_0799x_static_scan_20260527.csv'
OUT = BASE/'shinmomo_goal3_goal7_goal9_progress_20260527'
if OUT.exists(): shutil.rmtree(OUT)
for d in ['docs/analysis','data/static','tools/python','manifest']:
    (OUT/d).mkdir(parents=True, exist_ok=True)
rom = ROM_PATH.read_bytes()
rom_sha256 = hashlib.sha256(rom).hexdigest()

def raw_label(off, mirror='80'):
    hi = off >> 16
    lo = off & 0xFFFF
    if mirror == 'c0':
        return f"{0xC0+hi:02X}:{lo:04X}"
    return f"{0x80+hi:02X}:{lo:04X}"

def hexbytes(bs): return ' '.join(f'{b:02X}' for b in bs)

# ---------------------------------------------------------------------------
# Goal3: blind/static WRAM reference scan for 7E:201E..2030 / 7E:3004..303C
# ---------------------------------------------------------------------------
ops = {
0xAD:'LDA abs',0xBD:'LDA abs,X',0xB9:'LDA abs,Y',0xAF:'LDA long',0xBF:'LDA long,X',
0x8D:'STA abs',0x9D:'STA abs,X',0x99:'STA abs,Y',0x8F:'STA long',0x9F:'STA long,X',
0xAE:'LDX abs',0xBE:'LDX abs,Y',0x8E:'STX abs',
0xAC:'LDY abs',0xBC:'LDY abs,X',0x8C:'STY abs',
0x2D:'AND abs',0x3D:'AND abs,X',0x39:'AND abs,Y',0x0D:'ORA abs',0x1D:'ORA abs,X',0x19:'ORA abs,Y',
0x4D:'EOR abs',0x5D:'EOR abs,X',0x59:'EOR abs,Y',0x6D:'ADC abs',0x7D:'ADC abs,X',0x79:'ADC abs,Y',
0xED:'SBC abs',0xFD:'SBC abs,X',0xF9:'SBC abs,Y',0xCD:'CMP abs',0xDD:'CMP abs,X',0xD9:'CMP abs,Y',
0x2C:'BIT abs',0x3C:'BIT abs,X',0xEE:'INC abs',0xFE:'INC abs,X',0xCE:'DEC abs',0xDE:'DEC abs,X',
0x0E:'ASL abs',0x1E:'ASL abs,X',0x4E:'LSR abs',0x5E:'LSR abs,X',0x2E:'ROL abs',0x3E:'ROL abs,X',0x6E:'ROR abs',0x7E:'ROR abs,X',
0x9C:'STZ abs',0x9E:'STZ abs,X',0x1C:'TRB abs',0x0C:'TSB abs'
}
ranges=[(0x201E,0x2030,'wram_201e_2030'),(0x3004,0x303C,'wram_3004_303c')]

def bank_strength(off):
    hi = off >> 16
    if hi in (0x02,0x03,0x04,0x06):
        return 'priority_known_engine_area'
    if hi in (0x00,0x01,0x05,0x08,0x09,0x0B):
        return 'medium_needs_disasm_confirmation'
    return 'low_or_data_possible'

goal3_rows=[]
for i,b in enumerate(rom[:-4]):
    if b not in ops: continue
    m=ops[b]
    insn_len = 4 if 'long' in m else 3
    addr=rom[i+1] | (rom[i+2]<<8)
    if 'long' in m:
        if rom[i+3] != 0x7E: continue
    for lo,hi,label in ranges:
        if lo <= addr <= hi:
            ctx_start=max(0,i-8); ctx_end=min(len(rom),i+insn_len+8)
            goal3_rows.append({
                'raw_offset':f'0x{i:06X}',
                'label_80_mirror':raw_label(i,'80'),
                'label_c0_mirror':raw_label(i,'c0'),
                'opcode':f'0x{b:02X}',
                'mnemonic':m,
                'operand':f'$7E:{addr:04X}' if 'long' in m else f'${addr:04X}',
                'goal3_range':label,
                'raw_bank_hi':f'0x{i>>16:02X}',
                'candidate_strength':bank_strength(i),
                'bytes':hexbytes(rom[i:i+insn_len]),
                'context_bytes':hexbytes(rom[ctx_start:ctx_end]),
            })
            break
with (OUT/'data/static/goal3_wram_refs_20260527.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f, fieldnames=list(goal3_rows[0].keys()))
    w.writeheader(); w.writerows(goal3_rows)
addr_counter=Counter(r['operand'] for r in goal3_rows)
bank_counter=Counter(r['raw_bank_hi'] for r in goal3_rows)
mn_counter=Counter(r['mnemonic'] for r in goal3_rows)
with (OUT/'data/static/goal3_wram_ref_summary_20260527.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['summary_type','key','count'])
    for k,v in addr_counter.most_common(): w.writerow(['operand',k,v])
    for k,v in bank_counter.most_common(): w.writerow(['raw_bank_hi',k,v])
    for k,v in mn_counter.most_common(): w.writerow(['mnemonic',k,v])

# ---------------------------------------------------------------------------
# Goal7: parse equipment-id script-pack pointer table at raw 0x0B01F9
# Table is treated as zero-based: entry 0 dummy/default, equipment ID N uses entry N.
# ---------------------------------------------------------------------------
import pandas as pd
equip = pd.read_csv(EQUIP_CSV)
pack_table_base = 0x0B01F9
pack_bank_base = 0x0B0000

def parse_pack_by_table_index(idx):
    pos = pack_table_base + idx*2
    ptr = rom[pos] | (rom[pos+1]<<8)
    off = pack_bank_base + ptr
    hooks=[]; p=off
    for guard in range(24):
        if p>=len(rom): break
        h=rom[p]
        if h==0: break
        tgt=rom[p+1] | (rom[p+2]<<8)
        hooks.append((h,tgt))
        p += 3
    term_off = p if p < len(rom) else None
    return ptr,off,hooks,term_off

def hooks_sig(hooks): return ' '.join(f'{h:02X}->{t:04X}' for h,t in hooks)
def hooks_ids(hooks): return ' '.join(f'{h:02X}' for h,t in hooks)
base_ptr,base_off,default_hooks,_ = parse_pack_by_table_index(0)

g7_rows=[]
all_hook_targets=[]
for _,r in equip.iterrows():
    eid=int(r['id_dec'])
    ptr,off,hooks,term = parse_pack_by_table_index(eid)
    is_default = hooks == default_hooks
    has_special = any(h in (0xC1,0xC2,0xC8) for h,t in hooks)
    changed_83_84 = any((h,t) not in default_hooks for h,t in hooks if h in (0x83,0x84))
    row={
        'equipment_id_dec':eid,
        'equipment_id_hex':f'0x{eid:02X}',
        'name':str(r['name']),
        'group':str(r['group']),
        'slot_label':str(r['slot_label']),
        'stat_value':int(r['stat_value']),
        'pack_table_index':'same_as_equipment_id_zero_based_table',
        'pack_pointer_16':f'0x{ptr:04X}',
        'pack_raw_offset':f'0x{off:06X}',
        'pack_label_c0_mirror':raw_label(off,'c0'),
        'hook_count':len(hooks),
        'hook_ids':hooks_ids(hooks),
        'hook_signature':hooks_sig(hooks),
        'is_default_pack':is_default,
        'has_c1_c2_c8_special_hook':has_special,
        'changed_83_or_84_target':changed_83_84,
        'classification': 'non_default_special' if not is_default else 'default',
    }
    g7_rows.append(row)
    for order,(h,t) in enumerate(hooks):
        all_hook_targets.append({
            'equipment_id_dec':eid,
            'equipment_id_hex':f'0x{eid:02X}',
            'name':str(r['name']),
            'hook_order':order,
            'hook_id':f'0x{h:02X}',
            'hook_target_16':f'0x{t:04X}',
            'hook_target_raw_offset':f'0x{pack_bank_base+t:06X}',
            'hook_target_label_c0_mirror':raw_label(pack_bank_base+t,'c0'),
            'is_special_hook_id':h in (0xC1,0xC2,0xC8),
        })
with (OUT/'data/static/goal7_weapon_script_pack_by_equipment_20260527.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f, fieldnames=list(g7_rows[0].keys()))
    w.writeheader(); w.writerows(g7_rows)
with (OUT/'data/static/goal7_weapon_hook_targets_20260527.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f, fieldnames=list(all_hook_targets[0].keys()))
    w.writeheader(); w.writerows(all_hook_targets)
nondefault=[r for r in g7_rows if not r['is_default_pack']]
hook_counts=Counter()
special_hook_counts=Counter()
for row in all_hook_targets:
    hook_counts[row['hook_id']]+=1
    if row['is_special_hook_id']: special_hook_counts[row['hook_id']]+=1
unique_targets = sorted({(row['hook_id'], row['hook_target_16'], row['hook_target_raw_offset']) for row in all_hook_targets})
# body snippets for non-default unique targets
body_rows=[]
for hid,t16,raws in unique_targets:
    off=int(raws,16)
    used_by=[x for x in all_hook_targets if x['hook_id']==hid and x['hook_target_raw_offset']==raws]
    if any(int(x['equipment_id_dec']) in [int(r['equipment_id_dec']) for r in nondefault] for x in used_by):
        body_rows.append({
            'hook_id':hid,
            'hook_target_16':t16,
            'hook_target_raw_offset':raws,
            'hook_target_label_c0_mirror':raw_label(off,'c0'),
            'used_by_equipment_ids':' '.join(str(x['equipment_id_dec']) for x in used_by[:40]),
            'used_by_names':' / '.join(str(x['name']) for x in used_by[:20]),
            'first_32_bytes':hexbytes(rom[off:off+32])
        })
with (OUT/'data/static/goal7_hook_body_windows_20260527.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f, fieldnames=list(body_rows[0].keys()))
    w.writeheader(); w.writerows(body_rows)

# ---------------------------------------------------------------------------
# Goal9: 0x41A10 records, 398xx 9-byte rows, selected script windows
# ---------------------------------------------------------------------------
# 0x41A10 8-byte condition/target table candidates
rows41=[]
for idx in range(0,160):
    off=0x041A10 + idx*8
    rec=rom[off:off+8]
    if len(rec)<8: break
    target = rec[6] | (rec[7]<<8)
    target_file = 0x30000 + target
    note=''
    if target_file in (0x39850,0x39993): note='known_398xx_anchor'
    if target_file in (0x31C68,0x31DDF,0x31DF8,0x320A4,0x320C8): note='known_shop_facility_script_candidate'
    rows41.append({
        'record_index_from_0x41A10':idx,
        'record_raw_offset':f'0x{off:06X}',
        'key':f'0x{rec[0]:02X}',
        'c1':f'0x{rec[1]:02X}',
        'c2':f'0x{rec[2]:02X}',
        'c3':f'0x{rec[3]:02X}',
        'c4':f'0x{rec[4]:02X}',
        'c5':f'0x{rec[5]:02X}',
        'target_16':f'0x{target:04X}',
        'target_file_offset_assuming_0x30000_base':f'0x{target_file:06X}',
        'target_bytes_preview':hexbytes(rom[target_file:target_file+16]) if target_file < len(rom) else '',
        'note':note,
        'raw_hex':hexbytes(rec)
    })
with (OUT/'data/static/goal9_41a10_target_records_20260527.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f, fieldnames=list(rows41[0].keys()))
    w.writeheader(); w.writerows(rows41)
# 398xx 9-byte rows
rows398=[]
for p in range(0x39800,0x39A80):
    if rom[p:p+2] == bytes([0x38,0x05]):
        row=rom[p:p+9]
        runner=row[7] | (row[8]<<8)
        rows398.append({
            'row_raw_offset':f'0x{p:06X}',
            'series':'A_F09A' if row[7:9]==bytes([0x9A,0xF0]) else ('B_F0DB' if row[7:9]==bytes([0xDB,0xF0]) else 'other'),
            'b0':f'0x{row[0]:02X}','b1':f'0x{row[1]:02X}','b2':f'0x{row[2]:02X}','b3':f'0x{row[3]:02X}',
            'b4':f'0x{row[4]:02X}','b5':f'0x{row[5]:02X}','b6':f'0x{row[6]:02X}',
            'runner_ptr16':f'0x{runner:04X}',
            'raw_hex':hexbytes(row),
        })
with (OUT/'data/static/goal9_398xx_9byte_rows_20260527.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f, fieldnames=list(rows398[0].keys()))
    w.writeheader(); w.writerows(rows398)
# selected script/data windows
windows=[0x31C68,0x31DDF,0x31DF8,0x320A4,0x320C8,0x39847,0x39850,0x39916,0x39993]
winrows=[]
for off in windows:
    bs=rom[off:off+96]
    winrows.append({
        'raw_offset':f'0x{off:06X}',
        'label_80_mirror':raw_label(off,'80'),
        'label_c0_mirror':raw_label(off,'c0'),
        'first_32_bytes':hexbytes(bs[:32]),
        'first_96_bytes':hexbytes(bs),
        'ascii_safe':'' .join(chr(b) if 32<=b<127 else '.' for b in bs[:96]),
    })
with (OUT/'data/static/goal9_script_blob_windows_20260527.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f, fieldnames=list(winrows[0].keys()))
    w.writeheader(); w.writerows(winrows)

# Copy previous Goal13 note for continuity, if present
if PREV_G13_MD.exists(): shutil.copy(PREV_G13_MD, OUT/'docs/analysis/goal13_0799x_progress_20260527.md')
if PREV_G13_CSV.exists(): shutil.copy(PREV_G13_CSV, OUT/'data/static/goal13_0799x_static_scan_20260527.csv')

# Tool script for reproducibility
script_text = Path(__file__).read_text(encoding='utf-8')
(OUT/'tools/python/extract_goal3_goal7_goal9_static.py').write_text(script_text, encoding='utf-8')

# Docs
now='2026-05-27'
progress_md = f"""# Goal3 / Goal7 / Goal9 解析進捗更新（{now}）

## 目的

ユーザー指定の低進捗領域 Goal3 / Goal7 / Goal9 を、GitHub にそのまま配置できる形で追加解析した。
ROM 本体や raw copyrighted assets は含めない。

## 入力

- ROM: `Shin Momotarou Densetsu (J)_original.smc`
- ROM size: {len(rom):,} bytes
- SHA256: `{rom_sha256}`
- 既存資料: 2026-03-13 / 2026-03-18 handoff、260510Y handoff

## 進捗更新サマリ

| Goal | 旧見立て | 今回更新 | 更新理由 |
|---|---:|---:|---|
| Goal3 | 58% | 60〜62% | `7E:201E..2030` / `7E:3004..303C` への絶対参照候補を機械抽出し、次に読むべき bank/operand を CSV 化した。まだ blind scan のため確定ではなく、伸び幅は控えめ。 |
| Goal7 | 45〜50%相当 | 60〜62% | `0x0B01F9` の equipment-id script-pack pointer table を zero-based entry として読み、230装備に対して hook pack を展開。30件の non-default pack を確定候補として表化した。 |
| Goal9 | 58% | 62〜64% | `0x41A10` 8-byte target table を160件展開し、`0x39850` / `0x39993` anchor と `398xx` 9-byte row series をCSV化。script/data blob 仕様書化の足場が増えた。 |

## 今回作成した成果物

```text
docs/analysis/goal3_wram_struct_progress_20260527.md
docs/analysis/goal7_weapon_special_progress_20260527.md
docs/analysis/goal9_script_spec_progress_20260527.md
docs/analysis/goal_progress_update_20260527.md
data/static/goal3_wram_refs_20260527.csv
data/static/goal3_wram_ref_summary_20260527.csv
data/static/goal7_weapon_script_pack_by_equipment_20260527.csv
data/static/goal7_weapon_hook_targets_20260527.csv
data/static/goal7_hook_body_windows_20260527.csv
data/static/goal9_41a10_target_records_20260527.csv
data/static/goal9_398xx_9byte_rows_20260527.csv
data/static/goal9_script_blob_windows_20260527.csv
tools/python/extract_goal3_goal7_goal9_static.py
```

## 注意

- Goal3 の static scan は opcode-like bytes を拾うため、data area の false positive を含む。
- Goal7 はかなり強い。table entry 0 を dummy/default と見て、装備ID `N` は pointer table entry `N` を使う形が、玄武の刀以降の特殊packと整合する。
- Goal9 は reader 本体発見ではない。今回は target table / target-side blob の仕様書化を進めた。
"""
(OUT/'docs/analysis/goal_progress_update_20260527.md').write_text(progress_md,encoding='utf-8')

# Goal3 doc
prio_addrs = ', '.join(f'{k}({v})' for k,v in addr_counter.most_common(12))
prio_banks = ', '.join(f'{k}({v})' for k,v in bank_counter.most_common(8))
goal3_md=f"""# Goal3 WRAM構造体解析進捗（2026-05-27）

## Goal3の対象

Goal3 は `7E:201E..2030` と `7E:3004..303C` の正体を確定すること。
既存引継ぎでは、施設UI / ledger / choice 層に関わる中間構造体として 58% まで進んでいた。

## 今回の追加解析

ROM全体に対し、65816 の absolute / absolute indexed / long address 形式で以下を参照する候補を抽出した。

- `$201E..$2030`
- `$3004..$303C`
- `$7E:201E..$7E:2030`
- `$7E:3004..$7E:303C`

抽出件数: **{len(goal3_rows)} 件**。

多く出た operand:

```text
{prio_addrs}
```

raw bank high byte 別件数:

```text
{prio_banks}
```

## 解釈

今回の結果だけで各フィールド名を確定するにはまだ早い。
ただし、`$201E..$2030` と `$3004..$303C` が孤立した一時領域ではなく、複数の engine / UI / script 周辺から参照される中間構造体群であることは再確認できた。

特に次は、CSV の `candidate_strength=priority_known_engine_area` を起点に読む。
これは raw bank high byte `0x02/0x03/0x04/0x06` 周辺にあり、既存解析で bank82/83/84/86 の UI・local rule・descriptor 系と結びついていた領域に相当する。

## 進捗更新

- 旧見立て: 58%
- 今回更新: **60〜62%**

## 次に読む場所

1. `data/static/goal3_wram_refs_20260527.csv` の `priority_known_engine_area` 行。
2. `$3014/$3015`、`$301C/$301D`、`$201E/$201F/$2020` を優先。
3. `read/write` の実行順を runtime trace で取る。
4. `Goal9` の target-side script と join し、D系 opcode の `($9C)` 書込先と対応づける。
"""
(OUT/'docs/analysis/goal3_wram_struct_progress_20260527.md').write_text(goal3_md,encoding='utf-8')

# Goal7 doc
special_names='、'.join(f"{r['equipment_id_dec']}:{r['name']}" for r in nondefault[:18])
goal7_md=f"""# Goal7 武器特殊能力解析進捗（2026-05-27）

## Goal7の対象

武器・装備の特殊能力サブシステムを整理する。
既存引継ぎでは、武器特殊は弱点領域として残っていたが、`CB:01F9 / raw 0x0B01F9` が equipment-id based script-pack pointer table である見立てが出ていた。

## 今回の追加解析

`raw 0x0B01F9` を 16-bit pointer table として読み直した。
この table は **entry 0 が dummy/default** で、装備ID `N` は table entry `N` を使う形が自然。

default pack は以下。

```text
{hooks_sig(default_hooks)}
```

全230装備を展開した結果、default と異なる pack は **{len(nondefault)} 件**。
この30件を `data/static/goal7_weapon_script_pack_by_equipment_20260527.csv` に保存した。

代表的な non-default 装備:

```text
{special_names}
```

hook出現数:

```text
{', '.join(f'{k}:{v}' for k,v in hook_counts.most_common())}
```

特殊hook出現数:

```text
{', '.join(f'{k}:{v}' for k,v in special_hook_counts.most_common())}
```

## 今回強くなったこと

- `0x0B01F9` は装備ID別 script-pack pointer table として扱える。
- `84/83/82` はdefault packの基本hook。
- `C1/C2/C8` が追加される装備、または `83/84` target が差し替わる装備が特殊処理候補。
- 玄武・白虎・朱雀・青龍・酒呑、浦島モリ系、包丁/ドス/村雨/村正/孫六/菊一文字、錫杖系、鬼のかぎづめが non-default 側にまとまる。

## 進捗更新

- 旧見立て: 45〜50%相当
- 今回更新: **60〜62%**

## 残課題

1. `C1/C2/C8` の hook class 意味を battle routine 側へ接続する。
2. `data/static/goal7_hook_body_windows_20260527.csv` の body bytes から、damage/status/stat/回復/消費などの効果カテゴリを割る。
3. `83` hook target の差し替えが、表示文・命中判定・対象条件のどれかを判定する。
4. 30件の non-default 装備を効果カテゴリ付きCSVへ拡張する。
"""
(OUT/'docs/analysis/goal7_weapon_special_progress_20260527.md').write_text(goal7_md,encoding='utf-8')

# Goal9 doc
series_counts=Counter(r['series'] for r in rows398)
goal9_md=f"""# Goal9 会話・店・イベントスクリプト仕様解析進捗（2026-05-27）

## Goal9の対象

会話・店・イベントスクリプトの仕様書を作ること。
既存引継ぎでは、`31DE0/320A4` の2バイト命令列化、`39850/39993` blob兄弟性、local runner 理解が前進し、58%程度とされていた。

## 今回の追加解析

### 1. `0x41A10` target table 展開

`raw 0x41A10` から 8-byte record を160件展開した。
形式は既存仮説どおり、以下で扱える。

```text
[key][c1][c2][c3][c4][c5][target_lo][target_hi]
```

`target_file_offset = 0x30000 + target_16` として展開し、preview bytes を保存した。

重要anchor:

- record 68: `target=0x39850`
- record 107: `target=0x39993`

### 2. `398xx` 9-byte row series

`0x39800..0x39A80` で `38 05` から始まる 9-byte row を抽出した。
抽出件数: **{len(rows398)} 件**。

series counts:

```text
{', '.join(f'{k}:{v}' for k,v in series_counts.items())}
```

A系は末尾 `9A F0`、B系は末尾 `DB F0` を持つ。
これは 260510Y 側の `$83:F09A / $83:F0DB` terminal runner 説と整合する。

### 3. script / blob window 保存

以下の候補帯を96 bytes窓として保存した。

```text
0x31C68, 0x31DDF, 0x31DF8, 0x320A4, 0x320C8, 0x39847, 0x39850, 0x39916, 0x39993
```

## 進捗更新

- 旧見立て: 58%
- 今回更新: **62〜64%**

## 残課題

1. `0x41A10` reader 本体はまだ未発見。
2. `398xx/399xx` row が命令なのか、runner用 compact data なのかを runtime で判定する。
3. `0x31C68/0x31DDF/0x320A4/0x320C8` を opcode/data/text reference に分割する。
4. Goal3 の WRAM 作業領域と `0x30000` 台 script の書込先を join する。
"""
(OUT/'docs/analysis/goal9_script_spec_progress_20260527.md').write_text(goal9_md,encoding='utf-8')

# Manifest, README, excluded, commit commands
readme=f"""# Shinmomo Goal3/Goal7/Goal9 progress package 20260527

This package contains commit-ready text/data/tool outputs for the Shin Momotarou Densetsu analysis project.

Focus:

- Goal3: `7E:201E..2030` / `7E:3004..303C` WRAM structure candidate references
- Goal7: equipment script-pack / special weapon hook table
- Goal9: `0x41A10` target table and `398xx/399xx` script/blob row series

No ROM images, savestates, raw VRAM/OAM/CGRAM dumps, or nested ZIPs are included.

Start here:

1. `docs/analysis/goal_progress_update_20260527.md`
2. `docs/analysis/goal7_weapon_special_progress_20260527.md`
3. `docs/analysis/goal3_wram_struct_progress_20260527.md`
4. `docs/analysis/goal9_script_spec_progress_20260527.md`
5. `manifest/MANIFEST.md`

"""
(OUT/'README_GOAL3_7_9_20260527.md').write_text(readme,encoding='utf-8')
(OUT/'NOT_INCLUDED_ROM.txt').write_text('ROM files (.smc/.sfc), savestates, raw VRAM/OAM/CGRAM dumps, and nested ZIP archives are intentionally excluded.\n',encoding='utf-8')
(OUT/'manifest/EXCLUDED.md').write_text('# Excluded files\n\n- ROM binaries: `.smc`, `.sfc`\n- Savestates\n- Raw VRAM/OAM/CGRAM dumps\n- Nested ZIP archives\n- Any copyrighted raw asset dumps\n',encoding='utf-8')
# manifest list
files=[]
for p in sorted(OUT.rglob('*')):
    if p.is_file():
        rel=p.relative_to(OUT).as_posix()
        files.append((rel,p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest()))
with (OUT/'manifest/MANIFEST.md').open('w',encoding='utf-8') as f:
    f.write('# Manifest\n\n')
    f.write('| file | bytes | sha256 |\n|---|---:|---|\n')
    for rel,size,sha in files:
        f.write(f'| `{rel}` | {size} | `{sha}` |\n')
commit='''#!/usr/bin/env bash
set -euo pipefail

# Run from repository root after copying this package into zin1985/shinmomo.

git add README_GOAL3_7_9_20260527.md NOT_INCLUDED_ROM.txt \
  docs/analysis/goal_progress_update_20260527.md \
  docs/analysis/goal3_wram_struct_progress_20260527.md \
  docs/analysis/goal7_weapon_special_progress_20260527.md \
  docs/analysis/goal9_script_spec_progress_20260527.md \
  docs/analysis/goal13_0799x_progress_20260527.md \
  data/static/goal3_wram_refs_20260527.csv \
  data/static/goal3_wram_ref_summary_20260527.csv \
  data/static/goal7_weapon_script_pack_by_equipment_20260527.csv \
  data/static/goal7_weapon_hook_targets_20260527.csv \
  data/static/goal7_hook_body_windows_20260527.csv \
  data/static/goal9_41a10_target_records_20260527.csv \
  data/static/goal9_398xx_9byte_rows_20260527.csv \
  data/static/goal9_script_blob_windows_20260527.csv \
  data/static/goal13_0799x_static_scan_20260527.csv \
  tools/python/extract_goal3_goal7_goal9_static.py \
  manifest/MANIFEST.md manifest/EXCLUDED.md

git commit -m "analysis: progress Goal3 Goal7 Goal9 static findings 20260527"
'''
(OUT/'COMMIT_COMMANDS_GOAL3_7_9_20260527.sh').write_text(commit,encoding='utf-8')

# Refresh manifest after adding commit commands
files=[]
for p in sorted(OUT.rglob('*')):
    if p.is_file():
        rel=p.relative_to(OUT).as_posix()
        if rel == 'manifest/MANIFEST.md': continue
        files.append((rel,p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest()))
with (OUT/'manifest/MANIFEST.md').open('w',encoding='utf-8') as f:
    f.write('# Manifest\n\n')
    f.write('This package is intended to be copied into the root of `zin1985/shinmomo`.\n\n')
    f.write('| file | bytes | sha256 |\n|---|---:|---|\n')
    for rel,size,sha in files:
        f.write(f'| `{rel}` | {size} | `{sha}` |\n')

# Zip
zip_path=BASE/'shinmomo_goal3_goal7_goal9_progress_20260527.zip'
if zip_path.exists(): zip_path.unlink()
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.rglob('*')):
        if p.is_file():
            z.write(p, p.relative_to(OUT.parent))
print(zip_path)
print('Goal3 refs',len(goal3_rows),'Goal7 nondefault',len(nondefault),'Goal9 rows398',len(rows398))
