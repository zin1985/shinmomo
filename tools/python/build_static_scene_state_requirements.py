#!/usr/bin/env python3
from pathlib import Path
import csv,json
ROOT=Path(__file__).resolve().parents[2]
SPAWN=ROOT/"data/npc_display/static_actor_spawn_conditions_20260930.csv"
DIALOGUE=ROOT/"data/npc_display/static_actor_dialogue_conditions_20260930.csv"
OUT=ROOT/"data/npc_display/static_scene_state_requirements_20260930.json"
def rows(p):
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def add_unique(a,o,key):
    if not any(key(x)==key(o) for x in a):a.append(o)
scenes={}
def get_scene(sid,config,pack):
    return scenes.setdefault(sid,{"scene_id":sid,"config_id":config,"pack_id_hex":pack,"spawn_actor_count":0,"conditional_spawn_actor_count":0,"dialogue_variant_count":0,"state_inputs":[],"unresolved_predicates":[]})
for r in rows(SPAWN):
    s=get_scene(r["scene_id"],r["config_id"],r["pack_id_hex"]);s["spawn_actor_count"]+=1
    if r.get("visibility_when_state_unknown")=="candidate":s["conditional_spawn_actor_count"]+=1
    if r.get("flag_wram"):
        o={"kind":"flag","source":"actor_spawn","spec":r.get("flag_spec_hex"),"wram":r["flag_wram"],"bit":int(r["flag_bit"]),"status":"confirmed_static"}
        add_unique(s["state_inputs"],o,lambda x:(x["kind"],x.get("wram"),x.get("bit"),x["source"]))
    elif r.get("visibility_when_state_unknown")=="candidate":
        o={"kind":"predicate","source":"actor_spawn","producer_kind":r.get("producer_kind") or None,"operand":r.get("producer_operand") or None,"bytecode":r.get("predicate_bytecode") or None,"status":r.get("condition_status") or "unresolved"}
        add_unique(s["unresolved_predicates"],o,lambda x:(x["kind"],x.get("producer_kind"),x.get("operand"),x.get("bytecode")))
for r in rows(DIALOGUE):
    pack="0x"+r["record_id"][1:3].upper();sid=r["config_id"]+"@"+pack;s=get_scene(sid,r["config_id"],pack);s["dialogue_variant_count"]+=1
    if r.get("flag_0x65_wram"):
        o={"kind":"flag","source":"dialogue","spec":"0x65","wram":r["flag_0x65_wram"],"bit":int(r["flag_0x65_bit"]),"status":"confirmed_static"}
        add_unique(s["state_inputs"],o,lambda x:(x["kind"],x.get("wram"),x.get("bit"),x["source"]))
    if r.get("secondary_flag_wram"):
        o={"kind":"flag","source":"dialogue","spec":r.get("secondary_flag_spec"),"wram":r["secondary_flag_wram"],"bit":int(r["secondary_flag_bit"]),"status":"confirmed_static"}
        add_unique(s["state_inputs"],o,lambda x:(x["kind"],x.get("wram"),x.get("bit"),x["source"]))
    if r.get("relation_key"):
        o={"kind":"relation_resolver_condition","source":"dialogue","key":r["relation_key"],"subkey":r.get("relation_subkey"),"resolver":"80:DA57","status":"confirmed_static_structure","semantic_identity":"unresolved_relation_key"}
        add_unique(s["state_inputs"],o,lambda x:(x["kind"],x.get("key"),x.get("subkey"),x["source"]))
arr=sorted(scenes.values(),key=lambda x:x["scene_id"])
for s in arr:
    s["state_evaluation_status"]="required_or_partial" if s["state_inputs"] or s["unresolved_predicates"] else "not_required_by_current_catalog"
    s["known_state_input_count"]=len(s["state_inputs"]);s["unresolved_predicate_count"]=len(s["unresolved_predicates"])
obj={"schema_version":1,"scene_count":len(arr),"scenes":arr,"policy":{"unknown_state":"do not choose a current dialogue branch; render conditional spawn actors as candidates","evaluation_order":["select scene by config_id + active pack","evaluate actor spawn predicates","show active actors","evaluate selected actor dialogue predicates","play chosen dialogue pages"],"shared_state_object":True}}
OUT.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"scene_count":len(arr)},ensure_ascii=False))
