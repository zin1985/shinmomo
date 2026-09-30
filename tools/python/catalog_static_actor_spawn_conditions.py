#!/usr/bin/env python3
from pathlib import Path
import csv, json

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"data/npc_display/static_map_actor_selector_crosslink_20260930.csv"
OUT=ROOT/"data/npc_display/static_actor_spawn_conditions_20260930.csv"
SUM=ROOT/"data/npc_display/static_actor_spawn_conditions_summary_20260930.json"
FIELDS=["scene_id","pack_id_hex","config_id","family_hex","record_id","selector_hex","actor_command_offset","actor_command_hex","pre_actor_bytecode","guard_kind","branch_opcode","branch_rel8","branch_semantics","predicate_bytecode","producer_kind","producer_operand","condition_status","condition_expr","flag_spec_hex","flag_wram","flag_bit","state_evaluation","visibility_when_state_unknown","evidence","provenance"]

def flag_info(h):
    n=int(h,16)
    addr=0x1246+(n>>3)
    return f"0x{n:02X}", "$"+f"{addr:04X}", n&7

with SRC.open(encoding="utf-8-sig",newline="") as f:
    src=list(csv.DictReader(f))
counts={"actor_rows":len(src),"unconditional_spawn":0,"immediate_skip_guard":0,"simple_a3_flag":0,"simple_2d_condition":0,"simple_08_condition":0,"compound_predicate":0,"complex_pre_actor_control_flow":0,"b3_skip_guard":0,"b4_skip_guard":0}
rows=[]
for r in src:
    toks=(r.get("body_hex") or "").strip().split()
    ai=int(r.get("actor_command_offset") or 0)
    pre=toks[:ai]
    branch=pre[-2:] if len(pre)>=2 else []
    guarded=len(branch)==2 and branch[0] in {"b3","b4"} and branch[1]=="08"
    row={k:"" for k in FIELDS}
    row.update({"scene_id":r["config_id"]+"@"+r["pack_id_hex"],"pack_id_hex":r["pack_id_hex"],"config_id":r["config_id"],"family_hex":r["family_hex"],"record_id":r["record_id"],"selector_hex":r["selector_hex"],"actor_command_offset":r["actor_command_offset"],"actor_command_hex":r["actor_command_hex"],"pre_actor_bytecode":" ".join(pre),"provenance":"docs/analysis/map_selector_upper_vm_cfg_promotion_20260928.md"})
    if guarded:
        counts["immediate_skip_guard"]+=1
        counts["b3_skip_guard" if branch[0]=="b3" else "b4_skip_guard"]+=1
        pred=pre[:-2]; want="!= 0" if branch[0]=="b3" else "== 0"
        row.update({"guard_kind":"immediate_skip_actor_0x59","branch_opcode":branch[0].upper(),"branch_rel8":"0x08","branch_semantics":"predicate_zero_skips_actor; spawn_when_nonzero" if branch[0]=="b3" else "predicate_nonzero_skips_actor; spawn_when_zero","predicate_bytecode":" ".join(pred),"visibility_when_state_unknown":"candidate","evidence":"B3/B4 rel8=0x08 branches over the following 6-byte opcode59 actor command; branch outcome is confirmed, predicate semantics preserved at available confidence"})
        if len(pred)==2 and pred[0]=="a3":
            counts["simple_a3_flag"]+=1
            spec,wram,bit=flag_info(pred[1])
            row.update({"producer_kind":"A3_flag_test","producer_operand":spec,"condition_status":"confirmed_static_flag","condition_expr":f"flag_test(spec={spec},wram={wram},bit={bit}) {want}","flag_spec_hex":spec,"flag_wram":wram,"flag_bit":str(bit),"state_evaluation":"evaluable_if_flag_state_available"})
        elif len(pred)==2 and pred[0]=="2d":
            counts["simple_2d_condition"]+=1
            op="0x"+pred[1].upper()
            row.update({"producer_kind":"0x2D_condition_compare_0306","producer_operand":op,"condition_status":"confirmed_static_control_partial_predicate","condition_expr":f"predicate_2D(operand={op},compare_target=$0306) {want}","state_evaluation":"requires_2D_predicate_semantics_or_runtime_value"})
        elif len(pred)==4 and pred[0]=="08":
            counts["simple_08_condition"]+=1
            row.update({"producer_kind":"0x08_condition","producer_operand":"0x"+"".join(pred[1:]).upper(),"condition_status":"confirmed_static_control_partial_predicate","condition_expr":"predicate_08(bytes="+" ".join(pred).upper()+") "+want,"state_evaluation":"requires_08_predicate_semantics_or_runtime_value"})
        else:
            counts["compound_predicate"]+=1
            row.update({"producer_kind":"compound_vm_expression","condition_status":"confirmed_static_branch_unresolved_predicate","condition_expr":"vm_expression("+" ".join(pred).upper()+") "+want,"state_evaluation":"requires_compound_vm_expression_evaluation"})
    elif not pre:
        counts["unconditional_spawn"]+=1
        row.update({"guard_kind":"no_pre_actor_guard","condition_status":"confirmed_static_unconditional","condition_expr":"always","state_evaluation":"not_required","visibility_when_state_unknown":"visible","evidence":"actor record reaches opcode59 directly with no preceding actor-local guard bytes"})
    else:
        counts["complex_pre_actor_control_flow"]+=1
        row.update({"guard_kind":"complex_pre_actor_control_flow","predicate_bytecode":" ".join(pre),"producer_kind":"nonlocal_or_multi_actor_cfg","condition_status":"unresolved_complex_control_flow","state_evaluation":"requires_record_cfg","visibility_when_state_unknown":"candidate","evidence":"actor command is preceded by nontrivial control flow not reducible to immediate B3/B4 rel8=0x08 guard; do not assume unconditional visibility"})
    rows.append(row)
with OUT.open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
summary={"schema_version":1,**counts,"conditional_or_unresolved_actor_rows":counts["immediate_skip_guard"]+counts["complex_pre_actor_control_flow"],"directly_flag_evaluable_actor_rows":counts["simple_a3_flag"],"interpretation":"pack/scene selection is necessary but insufficient for actor visibility; unknown state retains conditional actors as candidates.","binding_key":"scene_id + record_id + selector_hex"}
SUM.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(summary,ensure_ascii=False))
