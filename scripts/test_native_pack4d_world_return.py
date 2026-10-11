#!/usr/bin/env python3
"""Contract tests for new 0x4D native south-boundary saved-map return edge."""
from __future__ import annotations
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
sys.path.insert(0,str(ROOT/"scripts"))
from add_runtime_native_return_edge import inject,EDGE_ID
from verify_native_pack4d_world_return import validate
from test_vm_frame_series_replays import make_series


def fixtures():
    input_doc=make_series(663378,25,77,(17,37),76,(52,233),"Down")
    input_doc["schema_version"]=2
    for row in (input_doc["before"],*input_doc["samples"],input_doc["after"]):
        row.update(w0306=77,w126e=77,w12b4=3,w12b5=29)
    for row in input_doc["samples"]:
        if row["frame"]>=663382:
            row["w157d"]=38
        if row["frame"]>=663387:
            row["w0305"]=76
            row["w1573"],row["w157d"]=52,233
    input_doc["after"]=dict(input_doc["samples"][-1],label="after")
    neutral=make_series(663403,120,76,(52,233),76,(52,233),"")
    neutral["schema_version"]=2
    for row in (neutral["before"],*neutral["samples"],neutral["after"]):
        row.update(w0306=77,w126e=77,w12b4=3,w12b5=29)
    for row in neutral["samples"]:
        if row["frame"]>=663414:
            row["w126e"],row["w12b4"]=76,76
    neutral["after"]=dict(neutral["samples"][-1],label="after")
    proof=json.loads((ROOT/"data/maps/transitions/world_52_233_entry_verified_20261011.json").read_text(encoding="utf-8"))
    bound={"config_id":"cfg_t04_l006_v2","pack_id_hex":"0x4D",
           "min_x":"1","max_x":"46","min_y":"1","max_y":"37",
           "confidence":"confirmed_static_opcode52_bounds",
           "bounds_opcode_addr":"CC:18AB"}
    return input_doc,neutral,bound,proof


class Native4DReturnTests(unittest.TestCase):
    def test_realistic_frame_run_yields_confirmed_one_cell(self):
        a,b,bounds,incoming=fixtures()
        report=validate(a,b,bounds,incoming)
        self.assertEqual(report["first_outside_frame"],663382)
        self.assertEqual(report["switch_frame"],663387)
        self.assertEqual(report["selector_convergence_frame"],663414)
        self.assertEqual(report["settled_arrival"],{"x":52,"y":233})
        self.assertFalse(report["CPU_handler_PC_observed"])
        self.assertFalse(report["full_south_exit_width_proven"])

    def test_missing_outside_crossing_is_not_a_return_proof(self):
        a,b,bounds,inc=fixtures()
        for row in a["samples"]:
            if row["w0305"]==77:
                row["w157d"]=37
        with self.assertRaisesRegex(ValueError,"crossing"):
            validate(a,b,bounds,inc)

    def test_wrong_destination_rejected(self):
        a,b,bounds,inc=fixtures()
        for row in a["samples"]:
            if row["w0305"]==76:row["w1573"]=53
        a["after"]=dict(a["samples"][-1],label="after")
        with self.assertRaisesRegex(ValueError,"do not join"):
            validate(a,b,bounds,inc)

    def test_bad_static_native_boundary_rejected(self):
        a,b,bounds,inc=fixtures()
        bounds["max_y"]="38"
        with self.assertRaisesRegex(ValueError,"Static native bounds"):
            validate(a,b,bounds,inc)

    def test_missing_independent_world_entry_rejected(self):
        a,b,bounds,inc=fixtures()
        inc["settled_arrival"]["x"]=18
        with self.assertRaisesRegex(ValueError,"source context"):
            validate(a,b,bounds,inc)

    def test_previous_4d_byte_may_lag_and_does_not_become_a_claim(self):
        a,b,bounds,inc=fixtures()
        report=validate(a,b,bounds,inc)
        self.assertIs(report["raw_w0306_converged_to_destination"],False)

    def test_production_verified_file_adds_one_non_executable_edge(self):
        d=json.loads((ROOT/"data/maps/transitions/pack4d_south_native_return_20261011.json").read_text(encoding="utf-8"))
        world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
        originals=[x for x in world["transition_candidates"] if x.get("transition_id")!=EDGE_ID]
        added,meta=inject(originals,d)
        self.assertEqual(meta["new_runtime_native_bound_edge_count"],1)
        self.assertEqual(len(added),len(originals)+1)
        target=added[-1]
        self.assertEqual(target["confidence"],"confirmed")
        self.assertEqual(target["destination_x"],52)
        self.assertEqual(target["destination_y"],233)
        self.assertFalse(target["native_boundary_context"]["handler_CPU_PC_observed"])

    def test_double_injection_is_rejected(self):
        d=json.loads((ROOT/"data/maps/transitions/pack4d_south_native_return_20261011.json").read_text(encoding="utf-8"))
        world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ValueError,"duplicate"):
            inject(world["transition_candidates"],d)

    def test_forged_CPU_claim_is_rejected(self):
        d=json.loads((ROOT/"data/maps/transitions/pack4d_south_native_return_20261011.json").read_text(encoding="utf-8"))
        world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
        d["CPU_handler_PC_observed"]=True
        with self.assertRaisesRegex(ValueError,"Unsupported/ambiguous"):
            inject([x for x in world["transition_candidates"] if x.get("transition_id")!=EDGE_ID],d)

    def test_generated_world_has_one_new_native_return_and_unknown_gate(self):
        w=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
        e=[a for a in w["transition_edges"] if a["transition_id"]==EDGE_ID]
        self.assertEqual(len(e),1)
        self.assertEqual(len(w["maps"]),149)
        self.assertEqual(len(w["transition_edges"]),75)
        self.assertEqual(len(w["transition_candidates"]),1312)
        self.assertEqual(e[0]["activation_gate"]["evaluation"],"unknown")
        self.assertFalse(e[0]["activation_gate"]["navigable_now"])
        self.assertIsNone(e[0]["trigger_addr"])
        self.assertEqual(e[0]["trigger_type"],"native_out_of_bounds_saved_map_return")


if __name__=="__main__":unittest.main()
