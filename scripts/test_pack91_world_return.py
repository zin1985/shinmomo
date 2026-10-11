#!/usr/bin/env python3
"""Synthetic and metadata regressions for cave saved-origin return."""
from __future__ import annotations
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from audit_transition_phases import collect
from add_runtime_cave_world_return_edge import inject,ID
from verify_pack91_world_return import verify
from test_vm_frame_series_replays import make_series


def fixtures():
    down=make_series(663332,50,145,(71,59),145,(71,61),"Down")
    up=make_series(663382,35,145,(71,61),76,(71,59),"Up")
    n1=make_series(663417,120,76,(71,59),76,(47,199),"")
    n2=make_series(663537,120,76,(47,199),76,(47,199),"")
    for obj in (down,up,n1,n2):
        obj["schema_version"]=2
        for row in (obj["before"],*obj["samples"],obj["after"]):
            row.update(w0306=80,w126e=145,w12b4=145,w12b5=3)
    for r in down["samples"]:
        if r["frame"]>=663350:r["w157d"]=60
        if r["frame"]>=663366:r["w157d"]=61
    down["after"]=dict(down["samples"][-1],label="after")
    for r in up["samples"]:
        if r["frame"]>=663385:r["w157d"]=60
        if r["frame"]>=663402:r["w157d"]=59
    up["after"]=dict(up["samples"][-1],label="after")
    for r in n1["samples"]:
        if r["frame"]>=663451:r["w126e"]=76;r["w12b4"]=76
        if r["frame"]>=663532:r["w1573"],r["w157d"]=47,199
    n1["after"]=dict(n1["samples"][-1],label="after")
    for r in (n2["before"],*n2["samples"],n2["after"]):
        r["w126e"]=76;r["w12b4"]=76
    incoming=json.loads((ROOT/"data/maps/transitions/omusubi_kororin_cheat_entry_verified_20261011.json").read_text(encoding="utf-8"))
    return down,up,n1,n2,incoming


class Pack91WorldReturnTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof=json.loads((ROOT/"data/maps/transitions/omusubi_cave_world_return_verified_20261011.json").read_text(encoding="utf-8"))
        cls.world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))

    def test_extended_neutral_proves_delayed_arrival(self):
        down,up,n1,n2,inc=fixtures()
        with self.assertRaisesRegex(ValueError,"Could not prove"):
            collect(up,n1,stability_frames=8)
        report=collect(up,n1,stability_frames=8,extra_neutral_trace=n2)
        self.assertEqual(report["source_pack"],145)
        self.assertEqual(report["destination_pack"],76)
        self.assertEqual(report["pack_switch_frame"],663417)
        self.assertEqual(report["first_settled_arrival_frame"],663532)
        self.assertEqual(report["settled_arrival"],{"x":47,"y":199})
        self.assertEqual(report["neutral_capture_chunk_count"],2)
        self.assertTrue(report["extended_neutral_capture_verified"])

    def test_positive_synthetic_validates_conditional_return(self):
        report=verify(*fixtures())
        self.assertEqual(report["contact_frame"],663402)
        self.assertEqual(report["first_settled_arrival_frame"],663532)
        self.assertGreaterEqual(report["stable_observed_frames"],120)
        self.assertFalse(report["return_world_xy_for_other_saves_verified"])
        self.assertFalse(report["floor_to_floor_transition_verified"])

    def test_missing_exact_cave_tile_rejected(self):
        a,b,c,d,inc=fixtures()
        for row in b["samples"]:
            if row["w0305"]==145 and row["w157d"]==59:row["w157d"]=60
        with self.assertRaisesRegex(ValueError,"Return floor tile"):
            verify(a,b,c,d,inc)

    def test_wrong_arrival_rejected(self):
        a,b,c,d,inc=fixtures()
        for row in c["samples"]:
            if row["w1573"]==47:row["w1573"]=48
        c["after"]["w1573"]=48
        for row in (d["before"],*d["samples"],d["after"]):
            row["w1573"]=48
        with self.assertRaisesRegex(ValueError,"landing"):
            verify(a,b,c,d,inc)

    def test_missing_extra_neutral_continuity_rejected(self):
        a,b,c,d,inc=fixtures()
        d["before"]["frame"]+=1
        with self.assertRaises(ValueError):
            verify(a,b,c,d,inc)

    def test_fake_controller_input_rejected(self):
        a,b,c,d,inc=fixtures()
        b["buttons"]="A"
        with self.assertRaisesRegex(ValueError,"bounded controller"):
            verify(a,b,c,d,inc)

    def test_false_independent_entry_context_rejected(self):
        a,b,c,d,inc=fixtures()
        inc["source_normal_world_walk_route_proven"]=True
        with self.assertRaisesRegex(ValueError,"Independent"):
            verify(a,b,c,d,inc)

    def test_wrong_selector_convergence_rejected(self):
        a,b,c,d,inc=fixtures()
        for row in c["samples"]:
            row["w126e"]=145;row["w12b4"]=145
        c["after"]["w126e"]=145;c["after"]["w12b4"]=145
        d["before"]["w126e"]=145;d["before"]["w12b4"]=145
        with self.assertRaisesRegex(ValueError,"Selector convergence"):
            verify(a,b,c,d,inc)

    def test_injection_produces_only_one_new_context_bound_edge(self):
        original=[e for e in self.world["transition_candidates"] if e["transition_id"]!=ID]
        generated,summary=inject(original,self.proof)
        self.assertEqual(len(generated),len(original)+1)
        self.assertEqual(summary["new_runtime_cave_saved_return_edge_count"],1)
        e=generated[-1]
        self.assertEqual(e["source_config_id"],"cfg_t08_l092_v2")
        self.assertEqual(e["destination_config_id"],"cfg_t01_l001_v1")
        self.assertEqual((e["destination_x"],e["destination_y"]),(47,199))
        self.assertFalse(e["runtime_saved_origin_context"]["destination_for_other_saved_states_proven"])
        self.assertFalse(e["runtime_saved_origin_context"]["return_handler_CPU_PC_observed"])

    def test_duplicate_injection_rejected(self):
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            inject(self.world["transition_candidates"],self.proof)

    def test_forged_saved_state_generality_rejected(self):
        fake=copy.deepcopy(self.proof)
        fake["return_world_xy_for_other_saves_verified"]=True
        with self.assertRaisesRegex(ValueError,"Return proof lacks"):
            inject([e for e in self.world["transition_candidates"] if e["transition_id"]!=ID],fake)

    def test_checked_in_proof_and_viewer_counts(self):
        self.assertTrue(self.proof["entry_origin_supplied_by_analysis_coordinate_cheat"])
        self.assertEqual(self.proof["neutral_capture_count"],2)
        self.assertEqual(self.proof["observed_stable_through_frame"],663657)
        self.assertEqual(len(self.proof["local_raw_trace_sha256"]),4)
        self.assertEqual(len(self.world["maps"]),149)
        self.assertEqual(len(self.world["transition_edges"]),74)
        self.assertEqual(len(self.world["transition_candidates"]),1311)
        edges=[e for e in self.world["transition_edges"] if e["transition_id"]==ID]
        self.assertEqual(len(edges),1)
        self.assertFalse(edges[0]["activation_gate"]["navigable_now"])
        self.assertEqual(edges[0]["activation_gate"]["evaluation"],"unknown")

if __name__=="__main__":unittest.main()
