#!/usr/bin/env python3
from pathlib import Path
import csv,collections,json
from PIL import Image,ImageDraw

ROOT=Path(r'C:\Users\zin\Documents\GitHub\shinmomo')
cross=list(csv.DictReader(open(ROOT/'data/npc_display/static_map_actor_selector_crosslink_20260930.csv',encoding='utf8')))
cat={int(r['selector']):r for r in csv.DictReader(open(ROOT/'data/npc_display/static_character_selector_catalog_20260930.csv',encoding='utf8'))}

stats=collections.defaultdict(lambda:{'records':set(),'configs':set(),'families':set(),'packs':set()})
for r in cross:
 s=int(r['selector_dec']);a=stats[s]
 a['records'].add(r['record_id'])
 if r['config_id']:a['configs'].add(r['config_id'])
 a['families'].add(r['family_hex']);a['packs'].add(r['pack_id_hex'])

rows=[]
for s in sorted(stats):
 a=stats[s];c=cat.get(s,{})
 rows.append({
   'selector_hex':f'0x{s:02X}','selector_dec':s,
   'unique_event_records':len(a['records']),'unique_map_configs':len(a['configs']),
   'unique_families':len(a['families']),'pack_ids':'|'.join(sorted(a['packs'])),
   'sprite_group':c.get('sprite_group',''),'animation_base_state':c.get('base_state',''),
   'chr_resource':c.get('chr_resource',''),'semantic_class':'unclassified',
   'semantic_label':''
 })
# Seed only identities already independently established.
for r in rows:
 if r['selector_hex']=='0x01':
  r['semantic_class']='party_actor';r['semantic_label']='Momotaro'
 elif r['selector_hex']=='0x0D':
  r['semantic_class']='party_actor';r['semantic_label']='Ginji'

csv_path=ROOT/'data/npc_display/static_map_bound_selector_summary_20260930.csv'
with csv_path.open('w',newline='',encoding='utf8') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)

cols=6;cw=180;ch=120
A=Image.new('RGBA',(cols*cw,((len(rows)+cols-1)//cols)*ch),(0,0,0,255));dr=ImageDraw.Draw(A)
for i,r in enumerate(rows):
 s=int(r['selector_dec']);x=(i%cols)*cw;y=(i//cols)*ch
 p=ROOT/f'graphics/static_character_reconstruction/catalog_selector_{s:02X}.png'
 if p.exists():
  im=Image.open(p).convert('RGBA')
  z=im.resize((64,64),Image.Resampling.NEAREST)
  A.alpha_composite(z,(x+6,y+25))
 dr.text((x+4,y+3),f'{r["selector_hex"]} G{r["sprite_group"]} S{r["animation_base_state"]}',fill='white')
 dr.text((x+76,y+27),f'maps {r["unique_map_configs"]}',fill=(200,200,200,255))
 dr.text((x+76,y+43),f'rec {r["unique_event_records"]}',fill=(200,200,200,255))
 dr.text((x+76,y+59),r['semantic_class'],fill=(200,200,200,255))
 if r['semantic_label']:
  dr.text((x+4,y+94),r['semantic_label'][:27],fill=(220,220,220,255))
atlas=ROOT/'graphics/static_character_reconstruction/static_map_bound_selector_atlas_20260930.png'
A.save(atlas)
print('selectors',len(rows),'atlas',atlas)
print('top by map count')
for r in sorted(rows,key=lambda x:(-int(x['unique_map_configs']),int(x['selector_dec'])))[:20]:
 print(r['selector_hex'],'maps',r['unique_map_configs'],'records',r['unique_event_records'],'packs',r['pack_ids'])
