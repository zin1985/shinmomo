#!/usr/bin/env python3
"""Regression: real cave hole drop and next map source stay evidence-scoped."""
from __future__ import annotations
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from test_vm_frame_series_replays import make_series
from verify_omusubi_hole_to_pack95 import verify
from attach_omusubi_pack95_source import attach,TARGET

def synth():
    specs={
      "hole_input":(663348,28,145,(75,54),145,(75,53),"Up"),
      "hole_idle1":(663376,120,145,(75,53),145,(70,9),""),
      "hole_idle2":(663496,120,145,(70,9),145,(70,22),""),
      "hole_idle3":(663616,120,145,(70,22),145,(70,26),""),
      "hole_idle4":(663736,120,145,(70,26),145,(70,26),""),
      "pre_right":(663856,60,145,(70,26),145,(70,26),""),
      "right_input":(663916,40,145,(70,26),149,(71,26),"Right"),
      "right_neutral":(663956,120,149,(71,26),149,(22,8),""),
    }
    items={key:make_series(*args) for key,args in specs.items()}
    for key,doc in items.items():
        doc["schema_version"]=2
        for r in (doc["before"],*doc["samples"],doc["after"]):
            r.update(w0306=80,w126e=145,w12b4=145,w12b5=3)
        for r in doc["samples"]:
            frame=r["frame"]
            if key=="hole_input" and frame>=663353:
                r["w1573"],r["w157d"]=75,53
            if key=="hole_idle1":
                if frame>=663453:r["w1573"],r["w157d"]=70,8
                if frame>=663493:r["w157d"]=9
            if key=="hole_idle2" and frame>=663600:r["w157d"]=22
            if key=="hole_idle3" and frame>=663647:r["w157d"]=26
            if key=="right_input":
                if frame>=663918:r["w1573"],r["w157d"]=71,26
                if frame>=663933:r["w0305"]=149
            if key=="right_neutral":
                if frame>=663967:r["w126e"],r["w12b4"]=149,149
                if frame>=664018:r["w1573"],r["w157d"]=22,8
        doc["after"]=dict(doc["samples"][-1],label="after")
    return items


class OmusubiHoleAndFloorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
        cls.hole=json.loads((ROOT/"data/maps/transitions/omusubi_hole_shaft_verified_20261011.json").read_text(encoding="utf-8"))
        cls.floor=json.loads((ROOT/"data/maps/transitions/omusubi_pack91_to_pack95_verified_20261011.json").read_text(encoding="utf-8"))

    def test_synthetic_real_input_drop_then_next_pack(self):
        a,b=verify(synth(),self.world)
        self.assertEqual(a["real_up_entry_frame"],663353)
        self.assertEqual(a["unmodified_event_jump_frame"],663453)
        self.assertEqual(a["final_shaft_landing_first_frame"],663647)
        self.assertTrue(a["automatic_descent_has_no_gamepad_input"])
        self.assertEqual(b["switch_frame"],663933)
        self.assertEqual(b["destination_xy"],{"x":22,"y":8})
        self.assertFalse(b["ROM_candidate_opcode_executed_PC_proven"])

    def test_wrong_hole_contact_rejected(self):
        docs=synth()
        for r in docs["hole_input"]["samples"]:
            if r["w157d"]==53:r["w157d"]=54
        docs["hole_input"]["after"]=dict(docs["hole_input"]["samples"][-1],label="after")
        docs["hole_idle1"]["before"]["w157d"]=54
        with self.assertRaisesRegex(ValueError,"Exact tile entry"):
            verify(docs,self.world)

    def test_missing_scripted_jump_rejected(self):
        docs=synth()
        for r in docs["hole_idle1"]["samples"]:
            if (r["w1573"],r["w157d"])==(70,8):r["w1573"]=71
        with self.assertRaisesRegex(ValueError,"Exact tile entry"):
            verify(docs,self.world)

    def test_hole_new_map_switch_is_invalid(self):
        docs=synth()
        docs["hole_idle1"]["samples"][20]["w0305"]=146
        with self.assertRaisesRegex(ValueError,"wholly inside"):
            verify(docs,self.world)

    def test_missing_last_120_stable_frames_rejected(self):
        docs=synth()
        docs["hole_idle4"]["samples"][-15]["w157d"]=25
        with self.assertRaisesRegex(ValueError,"Shaft landing"):
            verify(docs,self.world)

    def test_broken_consecutive_frames_rejected(self):
        docs=synth()
        docs["pre_right"]["before"]["frame"]+=1
        with self.assertRaises(ValueError):
            verify(docs,self.world)

    def test_no_0x95_arrival_rejected(self):
        docs=synth()
        for r in docs["right_neutral"]["samples"]:
            if r["w1573"]==22:r["w1573"]=23
        docs["right_neutral"]["after"]["w1573"]=23
        with self.assertRaisesRegex(ValueError,"arrival not stable"):
            verify(docs,self.world)

    def test_unknown_0x95_selector_rejected(self):
        docs=synth()
        for r in docs["right_neutral"]["samples"]:
            r["w126e"]=145;r["w12b4"]=145
        docs["right_neutral"]["after"]["w126e"]=145
        docs["right_neutral"]["after"]["w12b4"]=145
        with self.assertRaisesRegex(ValueError,"selector convergence"):
            verify(docs,self.world)

    def test_production_evidence_exact_and_scoped(self):
        self.assertEqual(self.hole["final_shaft_landing"],{"x":70,"y":26})
        self.assertEqual(self.hole["stable_neutral_end_frame"],663856)
        self.assertTrue(self.hole["hole_approach_positioned_by_cheat"])
        self.assertFalse(self.hole["normal_world_route_to_hole_proven"])
        self.assertEqual(self.floor["destination_config_id"],"cfg_t08_l096_v2")
        self.assertEqual(self.floor["destination_xy"],{"x":22,"y":8})
        self.assertEqual(self.floor["selector_convergence_frame"],663967)
        self.assertFalse(self.floor["ROM_candidate_opcode_executed_PC_proven"])
        self.assertEqual(len(self.hole["local_trace_sha256"]),5)
        self.assertEqual(len(self.floor["local_trace_sha256"]),3)

    def test_candidate_source_promoted_only_as_runtime_pair_not_opcode_pc(self):
        base=copy.deepcopy(self.world["transition_candidates"])
        for r in base:
            if r.get("transition_id")==TARGET:
                r["source_config_id"]=None
                r["source_pack"]=None
                r["source_hotspot_binding"]=None
                r.pop("runtime_floor_transition_proof",None)
        out,report=attach(base,self.floor)
        self.assertEqual(len(out),len(base))
        self.assertEqual(report["new_candidate_count"],0)
        self.assertEqual(report["new_bound_edge_count"],1)
        e=next(e for e in out if e["transition_id"]==TARGET)
        self.assertEqual(e["source_config_id"],"cfg_t08_l092_v2")
        self.assertEqual(e["confidence"],"strong_candidate")
        self.assertFalse(e["runtime_floor_transition_proof"]["script_opcode_PC_proven"])

    def test_duplicate_source_binding_rejected(self):
        with self.assertRaisesRegex(ValueError,"bound already"):
            attach(self.world["transition_candidates"],self.floor)

    def test_forged_executed_instruction_rejected(self):
        fake=copy.deepcopy(self.floor)
        fake["ROM_candidate_opcode_executed_PC_proven"]=True
        with self.assertRaisesRegex(ValueError,"invalid or overclaims"):
            attach(self.world["transition_candidates"],fake)

    def test_complete_graph_has_two_new_bindings_no_extra_candidate(self):
        self.assertEqual(len(self.world["maps"]),149)
        self.assertEqual(len(self.world["transition_edges"]),76)
        self.assertEqual(len(self.world["transition_candidates"]),1313)
        self.assertEqual(self.world["runtime_pack95_floor_source_summary"]["new_bound_edge_count"],1)
        self.assertEqual(self.world["runtime_cave_saved_origin_return_summary"]["new_graph_edge_count"],1)
        edge=next(e for e in self.world["transition_edges"] if e["transition_id"]==TARGET)
        self.assertFalse(edge["activation_gate"]["navigable_now"])
        self.assertEqual(edge["activation_gate"]["evaluation"],"unknown")

if __name__=="__main__":unittest.main()
