#!/usr/bin/env python3
"""Validate reverse cave stair from exact pack95 landing with fail-closed tests."""
from __future__ import annotations
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from test_vm_frame_series_replays import make_series
from verify_pack95_reverse_stair import verify
from attach_pack95_reverse_stair import attach,TARGET


def synthetic():
    down=make_series(664076,11,149,(22,8),149,(22,9),"Down")
    up=make_series(664087,20,149,(22,9),149,(22,8),"Up")
    first=make_series(664107,120,149,(22,8),145,(71,26),"")
    second=make_series(664227,120,145,(71,26),145,(71,26),"")
    for doc in (down,up,first,second):
        doc["schema_version"]=2
        for r in (doc["before"],*doc["samples"],doc["after"]):
            r.update(w0306=80,w126e=149,w12b4=149,w12b5=3)
    for row in down["samples"]:
        if row["frame"]>=664080:row["w157d"]=9
    down["after"]=dict(down["samples"][-1],label="after")
    for row in up["samples"]:
        if row["frame"]>=664095:row["w157d"]=8
    up["after"]=dict(up["samples"][-1],label="after")
    for row in first["samples"]:
        if row["frame"]>=664110:row["w0305"]=145
        if row["frame"]>=664145:row["w126e"]=145;row["w12b4"]=145
        if row["frame"]>=664196:row["w1573"],row["w157d"]=71,26
    first["after"]=dict(first["samples"][-1],label="after")
    for row in (second["before"],*second["samples"],second["after"]):
        row["w126e"]=145;row["w12b4"]=145
    return down,up,first,second


class Pack95ReverseStairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
        cls.proof=json.loads((ROOT/"data/maps/transitions/omusubi_pack95_reverse_stair_verified_20261011.json").read_text(encoding="utf-8"))

    def test_synthetic_return_contact_and_delayed_arrival(self):
        doc=verify(*synthetic(),self.world)
        self.assertEqual(doc["pack_switch_frame"],664110)
        self.assertEqual(doc["return_contact_frame"],664095)
        self.assertEqual(doc["selector_convergence_frame"],664145)
        self.assertEqual(doc["first_settled_arrival_frame"],664196)
        self.assertEqual(doc["settled_arrival_xy"],{"x":71,"y":26})
        self.assertFalse(doc["actual_opcode_CPU_PC_observed"])

    def test_missing_controller_return_tile_rejected(self):
        d,u,n1,n2=synthetic()
        for row in u["samples"]:
            row["w157d"]=9
        u["after"]=dict(u["samples"][-1],label="after")
        n1["before"]["w157d"]=9
        with self.assertRaisesRegex(ValueError,"reenter exact stair"):
            verify(d,u,n1,n2,self.world)

    def test_wrong_return_pack_rejected(self):
        d,u,n1,n2=synthetic()
        for row in n1["samples"]:
            if row["w0305"]==145:row["w0305"]=148
        n1["after"]["w0305"]=148
        n2["before"]["w0305"]=148
        with self.assertRaisesRegex(ValueError,"exactly one pack switch"):
            verify(d,u,n1,n2,self.world)

    def test_wrong_settled_coordinates_rejected(self):
        d,u,n1,n2=synthetic()
        for row in n1["samples"]:
            if (row["w1573"],row["w157d"])==(71,26):
                row["w1573"]=70
        n1["after"]["w1573"]=70
        for row in (n2["before"],*n2["samples"],n2["after"]):
            row["w1573"]=70
        with self.assertRaisesRegex(ValueError,"Stable reverse"):
            verify(d,u,n1,n2,self.world)

    def test_fake_input_device_rejected(self):
        d,u,n1,n2=synthetic()
        u["input_device"]="desktop_keyboard"
        with self.assertRaisesRegex(ValueError,"isolated SNES buttons"):
            verify(d,u,n1,n2,self.world)

    def test_noncontiguous_extra_neutral_rejected(self):
        d,u,n1,n2=synthetic()
        n2["before"]["frame"]+=1
        with self.assertRaises(ValueError):
            verify(d,u,n1,n2,self.world)

    def test_proof_provenance_does_not_claim_flight_or_walkability(self):
        self.assertEqual(self.proof["source_config_id"],"cfg_t08_l096_v2")
        self.assertEqual(self.proof["destination_config_id"],"cfg_t08_l092_v2")
        self.assertFalse(self.proof["normal_world_walk_to_cave_proven"])
        self.assertTrue(self.proof["source_reached_via_cheat_origin_cave_route"])
        self.assertFalse(self.proof["actual_opcode_CPU_PC_observed"])
        self.assertFalse(self.proof["pack95_stair_at_22_31_proven_as_exit"])
        self.assertEqual(len(self.proof["local_trace_sha256"]),4)

    def test_unique_preexisting_rom_candidate_source_binding(self):
        base=copy.deepcopy(self.world["transition_candidates"])
        for e in base:
            if e["transition_id"]==TARGET:
                e["source_config_id"]=None
                e["source_pack"]=None
                e["destination_x"]=None
                e["destination_y"]=None
                e.pop("runtime_reverse_stair_proof",None)
        new,summary=attach(base,self.proof)
        self.assertEqual(len(new),len(base))
        self.assertEqual(summary["new_bound_edge_count"],1)
        e=next(e for e in new if e["transition_id"]==TARGET)
        self.assertEqual(e["source_config_id"],"cfg_t08_l096_v2")
        self.assertEqual(e["destination_config_id"],"cfg_t08_l092_v2")
        self.assertEqual((e["destination_x"],e["destination_y"]),(71,26))
        self.assertEqual(e["confidence"],"strong_candidate")
        self.assertFalse(e["runtime_reverse_stair_proof"]["ROM_opcode_CPU_executed_proven"])

    def test_duplicate_binding_rejected(self):
        with self.assertRaisesRegex(ValueError,"source was already bound"):
            attach(self.world["transition_candidates"],self.proof)

    def test_forged_cpu_instruction_claim_rejected(self):
        fake=copy.deepcopy(self.proof)
        fake["actual_opcode_CPU_PC_observed"]=True
        with self.assertRaisesRegex(ValueError,"Missing or overclaimed"):
            attach(self.world["transition_candidates"],fake)

    def test_second_ladder_local_probe_not_promoted_to_universal_exit(self):
        p=ROOT/"data/maps/transitions/pack95_ladder22_31_no_switch_probe_20261011.json"
        doc=json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(doc["config_id"],"cfg_t08_l096_v2")
        self.assertEqual(doc["pack_id"],"0x95")
        self.assertEqual(doc["ladder_tile_xy"],[22,31])
        self.assertEqual(doc["ROM_catalog_transition_0183_destination_xy"],[22,31])
        self.assertFalse(doc["ROM_catalog_transition_0183_is_source_exit_proven"])
        self.assertFalse(doc["all_story_phases_excluded"])
        self.assertFalse(doc["universal_trigger_absence_proven"])
        self.assertEqual(len(doc["probes"]),2)
        self.assertEqual(
            {v["direction"] for v in doc["probes"]},
            {"from_south_up","from_north_down"})
        for entry in doc["probes"]:
            self.assertEqual(entry["pack_before"],"0x95")
            self.assertEqual(entry["pack_after"],"0x95")
            self.assertEqual(entry["tile31_contact_xy"],[22,31])
            self.assertTrue(entry["no_map_switch_within_observed_window"])
            self.assertFalse(entry["source_walkable_path_without_cheat_proven"])
            self.assertEqual(len(entry["local_input_capture_sha256"]),64)
            self.assertEqual(len(entry["local_neutral_capture_sha256"]),64)

    def test_viewer_has_exact_reverse_edge_and_unknown_gate(self):
        self.assertEqual(len(self.world["maps"]),149)
        self.assertEqual(len(self.world["transition_edges"]),60)
        self.assertEqual(len(self.world["transition_candidates"]),1297)
        edges=[e for e in self.world["transition_edges"] if e["transition_id"]==TARGET]
        self.assertEqual(len(edges),1)
        self.assertFalse(edges[0]["activation_gate"]["navigable_now"])
        self.assertEqual(edges[0]["activation_gate"]["evaluation"],"unknown")
        self.assertEqual(self.world["runtime_pack95_reverse_stair_summary"]["new_bound_edge_count"],1)


if __name__=="__main__":unittest.main()
