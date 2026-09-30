from pathlib import Path
import csv,json,collections,importlib.util
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('sc',ROOT/'tools/python/render_static_character_selectors.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

seq={};dur={}
with open(ROOT/'data/npc_display/shinmomo_B2C1_animation_state_scripts_20260425.csv',encoding='utf-8-sig') as f:
 for r in csv.DictReader(f):
  k=(int(r['group']),int(r['state_no_1_based']))
  seq[k]=[int(x) for x in r['frame_sequence_dec'].split(',') if x.strip().isdigit()]
  dur[k]=[int(x) for x in r['duration_sequence_dec'].split(',') if x.strip().isdigit()]

cat=[r for r in csv.DictReader(open(ROOT/'data/npc_display/static_character_selector_catalog_20260930.csv',encoding='utf8')) if not r['duplicate_of']]
evidence_path=ROOT/'data/npc_display/group5_group7_directional_family_evidence_20260930.csv'
extra_directional=set()
if evidence_path.exists():
 with evidence_path.open(encoding='utf-8-sig') as f:
  extra_directional={r['selector_hex'] for r in csv.DictReader(f) if r['status'].startswith('confirmed_')}
rows=[];directional=[];special=[]
for r in cat:
 sel=int(r['selector']);g=int(r['sprite_group']);base=int(r['base_state']);hit=None
 for off in range(8):
  qs=[seq.get((g,base+off+i),[]) for i in range(4)]
  ds=[dur.get((g,base+off+i),[]) for i in range(4)]
  if all(len(x)==2 for x in qs) and all(len(x)==2 for x in ds) and len({tuple(x) for x in ds})==1:
   hit=(off,qs,ds[0]);break
 if hit:
  off,qs,dd=hit
  selector_hex=f'0x{sel:02X}'
  direction_confirmed=(g in (2,3) or selector_hex in extra_directional)
  row={'selector':selector_hex,'sprite_group':g,'base_state':base,'kind':('directional_4x2_confirmed_order' if direction_confirmed else 'four_state_2frame_candidate'),
       'family_state_start':base+off,'family_offset':off,
       'slot0_frames':','.join(map(str,qs[0])),'slot1_frames':','.join(map(str,qs[1])),
       'slot2_frames':','.join(map(str,qs[2])),'slot3_frames':','.join(map(str,qs[3])),
       'duration_pair':','.join(map(str,dd)),
       'direction_order':'right,down,left,up' if direction_confirmed else 'unverified_slot0,slot1,slot2,slot3'}
  directional.append((r,row,qs))
 else:
  q=seq.get((g,base),[]);d=dur.get((g,base),[])
  kind='fixed' if len(q)==1 else ('two_frame' if len(q)==2 else 'special_sequence')
  row={'selector':f'0x{sel:02X}','sprite_group':g,'base_state':base,'kind':kind,
       'family_state_start':'','family_offset':'','slot0_frames':','.join(map(str,q)),
       'slot1_frames':'','slot2_frames':'','slot3_frames':'','duration_pair':','.join(map(str,d)),
       'direction_order':''}
  special.append((r,row,q))
 rows.append(row)

outcsv=ROOT/'data/npc_display/static_actor_animation_family_catalog_20260930.csv'
fields=list(rows[0].keys())
with outcsv.open('w',newline='',encoding='utf8') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def render_thumb(sel,fr,w=48,h=48):
 rec=m.selector_record(sel);im,_,_=m.render_frame(rec,fr)
 zf=max(1,min(3,min(w//max(1,im.width),h//max(1,im.height))))
 z=im.resize((im.width*zf,im.height*zf),Image.Resampling.NEAREST)
 t=Image.new('RGBA',(w,h),(0,0,0,255));t.alpha_composite(z,((w-z.width)//2,(h-z.height)//2));return t

# Directional atlas: each selector is one compact block with 8 frame thumbnails.
cols=4;bw=420;bh=126
A=Image.new('RGBA',(cols*bw,((len(directional)+cols-1)//cols)*bh),(0,0,0,255));dr=ImageDraw.Draw(A)
for i,(r,row,qs) in enumerate(directional):
 sel=int(r['selector']);x=(i%cols)*bw;y=(i//cols)*bh
 dr.text((x+4,y+3),f'{sel:02X} G{row["sprite_group"]} base S{row["base_state"]} -> S{row["family_state_start"]} (+{row["family_offset"]})',fill='white')
 labels=['0','1','2','3']
 if row['direction_order'].startswith('right'):labels=['R','D','L','U']
 for di,pair in enumerate(qs):
  for fi,fr in enumerate(pair):
   t=render_thumb(sel,fr);px=x+56+(di*2+fi)*44;py=y+30;A.alpha_composite(t.resize((40,40),Image.Resampling.NEAREST),(px,py))
   dr.text((px+2,py+42),f'{labels[di]}{fi}:F{fr}',fill=(190,190,190,255))
 dr.text((x+4,y+92),f'dur {row["duration_pair"]}',fill=(160,160,160,255))
dirpath=ROOT/'graphics/static_character_reconstruction/static_directional_animation_atlas_20260930.png';A.save(dirpath)

# Non-directional atlas: show every position in base-state sequence, preserving repeats; max 25 seen.
cols=3;bw=520;bh=250
B=Image.new('RGBA',(cols*bw,((len(special)+cols-1)//cols)*bh),(0,0,0,255));dr=ImageDraw.Draw(B)
for i,(r,row,q) in enumerate(special):
 sel=int(r['selector']);x=(i%cols)*bw;y=(i//cols)*bh
 dr.text((x+4,y+3),f'{sel:02X} G{row["sprite_group"]} S{row["base_state"]} {row["kind"]} N={len(q)}',fill='white')
 for j,fr in enumerate(q[:30]):
  t=render_thumb(sel,fr,40,40);px=x+4+(j%10)*50;py=y+28+(j//10)*65;B.alpha_composite(t,(px,py));dr.text((px,py+42),f'F{fr}',fill=(190,190,190,255))
specialpath=ROOT/'graphics/static_character_reconstruction/static_special_animation_atlas_20260930.png';B.save(specialpath)

confirmed_count=sum(x[1]['kind']=='directional_4x2_confirmed_order' for x in directional)
candidate_count=sum(x[1]['kind']=='four_state_2frame_candidate' for x in directional)
summary={'unique_graphics_signatures':len(cat),'directional_4x2':len(directional),'non_directional':len(special),
         'directional_4x2_detected':len(directional),'directional_4x2_confirmed':confirmed_count,
         'directional_4x2_candidate_unbound':candidate_count,
         'group5_group7_newly_confirmed':len(extra_directional),
         'group5_group7_evidence':'data/npc_display/group5_group7_directional_family_evidence_20260930.csv',
         'directional_family_offsets':dict(collections.Counter(str(x[1]['family_offset']) for x in directional)),
         'non_directional_kinds':dict(collections.Counter(x[1]['kind'] for x in special)),
         'directional_atlas':str(dirpath.relative_to(ROOT)),'special_atlas':str(specialpath.relative_to(ROOT)),
         'catalog':str(outcsv.relative_to(ROOT))}
(ROOT/'data/npc_display/static_actor_animation_family_summary_20260930.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
