#!/usr/bin/env python3
from pathlib import Path
import csv, json

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"data/npc_display/static_map_actor_selector_crosslink_20260930.csv"
OUT=ROOT/"data/npc_display/static_actor_spawn_conditions_20260930.csv"
SUM=ROOT/"data/npc_display/static_actor_spawn_conditions_summary_20260930.json"
TERMS=ROOT/"data/npc_display/static_actor_spawn_predicate_terms_20260930.csv"
FIELDS=["scene_id","pack_id_hex","config_id","family_hex","record_id","selector_hex","actor_command_offset","actor_command_hex","pre_actor_bytecode","guard_kind","branch_opcode","branch_rel8","branch_semantics","predicate_bytecode","producer_kind","producer_operand","condition_status","condition_expr","flag_spec_hex","flag_wram","flag_bit","state_evaluation","visibility_when_state_unknown","evidence","provenance"]

def flag_info(h):
    n=int(h,16)
    addr=0x1246+(n>>3)
    return f"0x{n:02X}", "$"+f"{addr:04X}", n&7

with SRC.open(encoding="utf-8-sig",newline="") as f:
    src=list(csv.DictReader(f))
counts={"actor_rows":len(src),"unconditional_spawn":0,"immediate_skip_guard":0,"simple_a3_flag":0,"simple_2d_condition":0,"simple_08_condition":0,"compound_predicate":0,"complex_pre_actor_control_flow":0,"b3_skip_guard":0,"b4_skip_guard":0,"decoded_compound_bitset_expression":0}
rows=[]
terms=[]
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
        if r.get("record_id")=="F50-L010" and " ".join(pred)=="3d 13 13 3d 15 13 e1 e7 17 07 13 e1 e7":
            counts["decoded_compound_bitset_expression"]+=1
            row.update({
                "producer_kind":"decoded_compound_bitset_expression",
                "producer_operand":"0x13",
                "condition_status":"confirmed_static_bitset_expression",
                "condition_expr":"bitset_test(base=$3FA1,id=0x13,wram=$3FA3,bit=2) != 0 && bitset_test(base=$3FA4,id=0x13,wram=$3FA6,bit=2) == 0 && bitset_test(base=$161D,id=0x13,wram=$161F,bit=2) != 0",
                "state_evaluation":"evaluable_if_bitset_state_available",
                "evidence":"canonical ROM: 81:A862 maps id 0x13 to bit18; C4:C705 tests $3FA1..3FA3; C4:C750 tests $3FA4..3FA6; C4:8D3B/81:A8F4 tests $161D..161F; E1/E7 compose polarity and AND",
                "provenance":"docs/analysis/family50_actor_spawn_l010_20260930.md",
            })
            terms.extend([
                {"scene_id":row["scene_id"],"pack_id_hex":row["pack_id_hex"],"config_id":row["config_id"],"record_id":row["record_id"],"selector_hex":row["selector_hex"],"term_order":1,"source_bytecode":"3D 13 13","producer":"opcode_3D_bitset_test","subtype_or_key":"0x13","operand_id_hex":"0x13","mask_bit_index":18,"bitset_base_wram":"$3FA1","resolved_wram":"$3FA3","resolved_bit":2,"expected_value":1,"term_expr":"bitset_test(base=$3FA1,id=0x13,wram=$3FA3,bit=2) != 0","condition_status":"confirmed_static","handler_chain":"C4:935C -> C4:C2CC subtype 0x13 -> C4:C705 -> 81:A862 -> C4:C353/C362","evidence":"one-hot id 0x13 maps to bit18 and is AND-tested against $3FA1..$3FA3","provenance":"docs/analysis/family50_actor_spawn_l010_20260930.md"},
                {"scene_id":row["scene_id"],"pack_id_hex":row["pack_id_hex"],"config_id":row["config_id"],"record_id":row["record_id"],"selector_hex":row["selector_hex"],"term_order":2,"source_bytecode":"3D 15 13 E1","producer":"opcode_3D_bitset_test_then_zero_test","subtype_or_key":"0x15","operand_id_hex":"0x13","mask_bit_index":18,"bitset_base_wram":"$3FA4","resolved_wram":"$3FA6","resolved_bit":2,"expected_value":0,"term_expr":"bitset_test(base=$3FA4,id=0x13,wram=$3FA6,bit=2) == 0","condition_status":"confirmed_static","handler_chain":"C4:935C -> C4:C2CC subtype 0x15 -> C4:C750 -> 81:A862 -> E1","evidence":"one-hot id 0x13 maps to bit18; subtype15 tests $3FA4..$3FA6 and E1 requires zero","provenance":"docs/analysis/family50_actor_spawn_l010_20260930.md"},
                {"scene_id":row["scene_id"],"pack_id_hex":row["pack_id_hex"],"config_id":row["config_id"],"record_id":row["record_id"],"selector_hex":row["selector_hex"],"term_order":3,"source_bytecode":"17 07 13 E1","producer":"opcode_17_key07_bitset_test_then_zero_test","subtype_or_key":"0x07","operand_id_hex":"0x13","mask_bit_index":18,"bitset_base_wram":"$161D","resolved_wram":"$161F","resolved_bit":2,"expected_value":1,"term_expr":"bitset_test(base=$161D,id=0x13,wram=$161F,bit=2) != 0","condition_status":"confirmed_static","handler_chain":"C4:8C04 key 0x07 -> C4:8D3B -> 81:A8F4 -> 81:A862 -> C4:8951 -> E1","evidence":"81:A8F4 carry reports membership; C4:8951 inverts to VM boolean and following E1 restores positive membership","provenance":"docs/analysis/family50_actor_spawn_l010_20260930.md"},
            ])
    elif not pre:
        counts["unconditional_spawn"]+=1
        row.update({"guard_kind":"no_pre_actor_guard","condition_status":"confirmed_static_unconditional","condition_expr":"always","state_evaluation":"not_required","visibility_when_state_unknown":"visible","evidence":"actor record reaches opcode59 directly with no preceding actor-local guard bytes"})
    else:
        counts["complex_pre_actor_control_flow"]+=1
        row.update({"guard_kind":"complex_pre_actor_control_flow","predicate_bytecode":" ".join(pre),"producer_kind":"nonlocal_or_multi_actor_cfg","condition_status":"unresolved_complex_control_flow","state_evaluation":"requires_record_cfg","visibility_when_state_unknown":"candidate","evidence":"actor command is preceded by nontrivial control flow not reducible to immediate B3/B4 rel8=0x08 guard; do not assume unconditional visibility"})
    rows.append(row)
with OUT.open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
TERM_FIELDS=["scene_id","pack_id_hex","config_id","record_id","selector_hex","term_order","source_bytecode","producer","subtype_or_key","operand_id_hex","mask_bit_index","bitset_base_wram","resolved_wram","resolved_bit","expected_value","term_expr","condition_status","handler_chain","evidence","provenance"]
with TERMS.open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=TERM_FIELDS); w.writeheader(); w.writerows(terms)
summary={"schema_version":2,**counts,"conditional_or_unresolved_actor_rows":counts["immediate_skip_guard"]+counts["complex_pre_actor_control_flow"],"directly_flag_evaluable_actor_rows":counts["simple_a3_flag"],"directly_state_evaluable_actor_rows":counts["simple_a3_flag"]+counts["decoded_compound_bitset_expression"],"interpretation":"pack/scene selection is necessary but insufficient for actor visibility; unknown state retains conditional actors as candidates.","binding_key":"scene_id + record_id + selector_hex","status_note":"F50-L010 compound predicate is reduced to three neutral bitset terms; semantic names of the bitsets remain unresolved."}
SUM.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(summary,ensure_ascii=False))
