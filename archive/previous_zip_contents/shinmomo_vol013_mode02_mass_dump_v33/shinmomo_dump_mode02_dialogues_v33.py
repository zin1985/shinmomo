#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
shinmomo_dump_mode02_dialogues_v33.py

新桃太郎伝説 mode02 / C0:BD98 bitstream 会話ダンプ用。
- ROMからBD98 decoder tableを読み、mode02 streamを外部復元する。
- <00>後の次セリフは byte境界とは限らないため、chain state(bitbuf/bitcnt)を保持して連続出力する。
- 既知root指定、または限定範囲scanで候補抽出する。

使い方例:
  python shinmomo_dump_mode02_dialogues_v33.py --rom "Shin Momotarou Densetsu (J).smc" --roots C8:A7DD --out out.csv
  python shinmomo_dump_mode02_dialogues_v33.py --rom "Shin Momotarou Densetsu (J).smc" --roots C8:A7DD C8:F193 C9:4C7A C9:4F83 --out out.csv
  python shinmomo_dump_mode02_dialogues_v33.py --rom "Shin Momotarou Densetsu (J).smc" --scan C8:A000-C8:B200 --out scan.csv --min-score 40

注意:
  scanは候補抽出です。false positiveが混ざります。
  本命はruntimeで拾ったroot pointer、script/descriptorから逆引きしたroot pointerのchain dumpです。
"""

from __future__ import annotations
import argparse, csv, re, sys
from pathlib import Path

# v28から移植した暫定文字表。完全版が欲しい場合は --lua で v28 Luaを渡す。
MOMO3 = {
"50":" ","51":"0","52":"1","53":"2","54":"3","55":"4","56":"5","57":"6","58":"7","59":"8","5A":"9","5B":"{5B}","5C":"!","5D":"、","5E":"。","5F":"…","60":"·","61":"A","62":"B","63":"C","64":"D","65":"E","66":"F","67":"G","68":"H","69":"I","6A":"J","6B":"K","6C":"L","6D":"M","6E":"N","6F":"O","70":"P","71":"Q","72":"R","73":"S","74":"T","75":"U","76":"V","77":"W","78":"X","79":"Y","7A":"Z","7B":"(","7C":")","7D":"「","7E":"」","7F":"〜","80":"ー","82":"c","83":"+","84":"-","85":"/","86":"㎏","87":"->","88":"<-","89":"<","8A":">","8B":"『","8C":"』",
"90":"あ","91":"い","92":"う","93":"え","94":"お","95":"か","96":"き","97":"く","98":"け","99":"こ","9A":"さ","9B":"し","9C":"す","9D":"せ","9E":"そ","9F":"た","A0":"ち","A1":"つ","A2":"て","A3":"と","A4":"な","A5":"に","A6":"ぬ","A7":"ね","A8":"の","A9":"は","AA":"ひ","AB":"ふ","AC":"へ","AD":"ほ","AE":"ま","AF":"み","B0":"む","B1":"め","B2":"も","B3":"や","B4":"ゆ","B5":"よ","B6":"ら","B7":"り","B8":"る","B9":"れ","BA":"ろ","BB":"わ","BC":"を","BD":"ん","BE":"で",
"D0":"が","D1":"ぎ","D2":"ぐ","D3":"げ","D4":"ご","D5":"ざ","D6":"じ","D7":"ず","D8":"ぜ","D9":"ぞ","DA":"だ","DB":"ぢ","DC":"づ","DD":"ど","DE":"ば","DF":"び","E0":"ぶ","E1":"べ","E2":"ぼ","E3":"ぱ","E4":"ぴ","E5":"ぷ","E6":"ぺ","E7":"ぽ","F0":"ぁ","F1":"ぃ","F2":"ぅ","F3":"ぇ","F4":"ぉ","F5":"っ","F6":"ゃ","F7":"ゅ","F8":"ょ","F9":"ゎ",
}
DICT02 = {"64":"人気","A0":"桃太郎","AC":"オニ","B0":"きんたん","B9":"ゆうき","C0":"おにぎり","CD":"ちから","CE":"あしゅら"}

TERM=0xBDE4
T0=0xBDEC
M0=0xBEEB
T1=0xBF0B
M1=0xC00A

def load_lua_tables(path: str|None):
    """v28 Luaを渡された場合、MOMO3/DICT02を完全版へ上書きする。"""
    global MOMO3, DICT02
    if not path:
        return
    text=Path(path).read_text(encoding="utf-8")
    pre=text.split("local DICT02")[0]
    m3={}
    for k,v in re.findall(r'\["([0-9A-F]+)"\]\s*=\s*"([^"]*)"', pre):
        m3[k]=v
    m3.update({"F5":"っ","F6":"ゃ","F7":"ゅ","F8":"ょ"})
    if m3:
        MOMO3=m3
    m=re.search(r'local DICT02 = \{(.*?)\n\}', text, re.S)
    d={}
    if m:
        for k,v in re.findall(r'\["([0-9A-F]+)"\]\s*=\s*"([^"]*)"', m.group(1)):
            d[k]=v
    if d:
        DICT02=d

class Decoder:
    def __init__(self, rom: bytes):
        self.rom=rom
    def hirom_offset(self, bank:int, addr:int)->int:
        b=bank
        if b>=0xC0:
            b-=0xC0
        elif b>=0x80:
            b-=0x80
        return b*0x10000 + addr
    def rom8(self, bank:int, addr:int):
        off=self.hirom_offset(bank, addr)
        if 0 <= off < len(self.rom):
            return self.rom[off]
        return None
    def tb(self, snes_addr:int)->int:
        v=self.rom8(0xC0, snes_addr)
        return 0 if v is None else v
    def next_symbol(self, st):
        node=0
        for _ in range(80):
            old=node
            low=old & 7
            hi=old >> 3
            st["bitcnt"]=(st["bitcnt"]-1) & 0xff
            if st["bitcnt"]>=0x80:
                b=self.rom8(st["bank"], st["addr"])
                if b is None:
                    return None, "source_oob"
                st["bitbuf"]=b
                st["bitcnt"]=7
                st["addr"]=(st["addr"]+1)&0xffff
                if st["addr"]==0:
                    st["bank"]=(st["bank"]+1)&0xff
            carry = 1 if (st["bitbuf"] & 0x80) else 0
            st["bitbuf"]=(st["bitbuf"]*2)&0xff
            if carry==0:
                node=self.tb(T0+old)
                mask=self.tb(M0+hi)
            else:
                node=self.tb(T1+old)
                mask=self.tb(M1+hi)
            term=self.tb(TERM+low)
            if (mask & term)==0:
                return node, None
        return None, "tree_depth_guard"
    def decode_segment(self, st, max_symbols:int):
        start=st.copy()
        syms=[]
        err=""
        for _ in range(max_symbols):
            sym,e=self.next_symbol(st)
            if sym is None:
                err=e or "decode_error"
                break
            syms.append(sym)
            if sym==0x00:
                break
        return start, syms, err, st.copy()

def render(syms):
    out=[]
    events=[]
    unknown=0
    i=0
    while i<len(syms):
        b=syms[i]
        if b==0:
            out.append("<00>")
            events.append(f"{i+1}:00:<00>")
            i+=1
        elif b==1:
            out.append("\n")
            events.append(f"{i+1}:01:<NL>")
            i+=1
        elif b==2 and i+1<len(syms):
            low=syms[i+1]
            s=DICT02.get(f"{low:02X}", f"{{02{low:02X}}}")
            if s.startswith("{"):
                unknown+=1
            out.append(s)
            events.append(f"{i+1}:02{low:02X}:{s}")
            i+=2
        elif 0x18<=b<0x20 and i+1<len(syms):
            low=syms[i+1]
            key=f"{b:02X}{low:02X}"
            s=MOMO3.get(key, "?")
            if s=="?":
                s=f"{{K{key}}}"
                unknown+=1
            out.append(s)
            events.append(f"{i+1}:{key}:{s}")
            i+=2
        else:
            key=f"{b:02X}"
            s=MOMO3.get(key, "?")
            if s=="?":
                s=f"{{{key}}}"
                unknown+=1
            out.append(s)
            events.append(f"{i+1}:{key}:{s}")
            i+=1
    return "".join(out), " | ".join(events), unknown

def score_text(text, syms, unknown):
    if not syms or syms[-1]!=0:
        return -999
    t=text.replace("<00>","")
    if len(t)<8:
        return -50
    jp=sum(1 for ch in t if ("ぁ"<=ch<="ん") or ("ァ"<=ch<="ン") or ("一"<=ch<="龯"))
    score=jp*2 + text.count("「")*8 + text.count("」")*8 + text.count("\n")*3 + text.count("!")*2 + text.count("。")*2
    score-=unknown*14 + text.count("{")*8 + text.count("?")*5
    for w in ("桃太郎","銀次","おむすび","金太郎","浦島","夜叉姫","オニ"):
        if w in text:
            score+=10
    ascii_count=sum(1 for ch in t if ch.isascii() and ch not in "<>0123456789{}:")
    score-=ascii_count*3
    return score

def parse_ptr(s):
    m=re.fullmatch(r"([0-9A-Fa-f]{2}):([0-9A-Fa-f]{4})", s)
    if not m:
        raise ValueError(f"bad pointer: {s}")
    return int(m.group(1),16), int(m.group(2),16)

def parse_scan(s):
    # C8:A000-C8:B200
    left,right=s.split("-")
    b1,a1=parse_ptr(left)
    b2,a2=parse_ptr(right)
    if b1!=b2:
        raise ValueError("scan currently supports one bank only")
    return b1,a1,a2

def dump_chain(dec, root_label, bank, addr, max_segments, max_symbols):
    st={"bank":bank,"addr":addr,"bitbuf":0,"bitcnt":0}
    rows=[]
    for seg in range(max_segments):
        start,syms,err,end=dec.decode_segment(st, max_symbols)
        text,events,unknown=render(syms)
        row={
            "root":root_label,
            "seg":seg,
            "start_state":f'{start["bank"]:02X}:{start["addr"]:04X}/bitcnt{start["bitcnt"]:02X}/bitbuf{start["bitbuf"]:02X}',
            "start_bank":f'{start["bank"]:02X}',
            "start_addr":f'{start["addr"]:04X}',
            "start_bitcnt":f'{start["bitcnt"]:02X}',
            "start_bitbuf":f'{start["bitbuf"]:02X}',
            "end_state":f'{end["bank"]:02X}:{end["addr"]:04X}/bitcnt{end["bitcnt"]:02X}/bitbuf{end["bitbuf"]:02X}',
            "end_bank":f'{end["bank"]:02X}',
            "end_addr":f'{end["addr"]:04X}',
            "end_bitcnt":f'{end["bitcnt"]:02X}',
            "end_bitbuf":f'{end["bitbuf"]:02X}',
            "score":score_text(text, syms, unknown),
            "sym_count":len(syms),
            "unknown":unknown,
            "err":err,
            "raw_tokens":" ".join(f"{b:02X}" for b in syms),
            "text":text,
            "events":events,
        }
        rows.append(row)
        if err or not syms or syms[-1]!=0:
            break
        st=end
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--rom", required=True)
    ap.add_argument("--lua", help="v28 Lua path. If given, use its full MOMO3 table.")
    ap.add_argument("--roots", nargs="*", default=[])
    ap.add_argument("--scan", help="candidate scan range, e.g. C8:A000-C8:B200")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-segments", type=int, default=80)
    ap.add_argument("--max-symbols", type=int, default=260)
    ap.add_argument("--min-score", type=int, default=40)
    args=ap.parse_args()

    load_lua_tables(args.lua)
    rom=Path(args.rom).read_bytes()
    dec=Decoder(rom)
    out_rows=[]

    for ptr in args.roots:
        bank,addr=parse_ptr(ptr)
        out_rows.extend(dump_chain(dec, ptr.upper(), bank, addr, args.max_segments, args.max_symbols))

    if args.scan:
        bank,start,end=parse_scan(args.scan)
        # scanは先頭segだけを評価して、良さそうなrootだけchain展開
        for addr in range(start,end):
            rows=dump_chain(dec, f"{bank:02X}:{addr:04X}", bank, addr, 1, min(args.max_symbols,180))
            if rows and rows[0]["score"]>=args.min_score:
                out_rows.extend(dump_chain(dec, f"{bank:02X}:{addr:04X}", bank, addr, min(args.max_segments,8), args.max_symbols))

    fieldnames=["root","seg","start_state","start_bank","start_addr","start_bitcnt","start_bitbuf",
                "end_state","end_bank","end_addr","end_bitcnt","end_bitbuf",
                "score","sym_count","unknown","err","raw_tokens","text","events"]
    with open(args.out,"w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in out_rows:
            w.writerow(row)
    print(f"wrote {len(out_rows)} rows -> {args.out}")

if __name__ == "__main__":
    main()
