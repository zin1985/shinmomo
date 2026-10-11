#!/usr/bin/env python3
"""Offline tests for truthful spatial runtime annotations and v2 replay joins."""
from __future__ import annotations

import copy
import csv
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
sys.path.insert(0,str(ROOT/"scripts"))
from apply_runtime_spatial_proofs import apply_runtime_spatial_proofs
from verify_spatial_event_transition import prove, unique_edge
from test_vm_frame_series_replays import corpus


def proofs():
    names=("tabidachi_shrine_entry_verified_20261011.json",
           "world_52_233_entry_verified_20261011.json")
    return [json.loads((ROOT/"data/maps/transitions"/p).read_text(encoding="utf-8")) for p in names]


def synthetic():
    data=corpus()
    first=data["world_entry"]
    second=data["world_settle"]
    for doc in (first,second):
        doc["schema_version"]=2
        for row in (doc["before"],*doc["samples"],doc["after"]):
            row.update(w0306=0x50,w126e=0x50,w12b4=0x50,w12b5=17)
    spot={"hotspot_id":"synth_world_hotspot","source_config_id":"cfg_world",
          "destination_config_id":"cfg_village","trigger_addr":"CC:0B08",
          "source_grid_x":"55","source_grid_y":"237",
          "source_width":"1","source_height":"1",
          "destination_x":"29","destination_y":"55"}
    edge={"transition_id":"synth_edge","source_config_id":"cfg_world",
          "destination_config_id":"cfg_village","trigger_addr":"CC:0B08",
          "destination_x":29,"destination_y":55,"confidence":"strong_candidate"}
    return first,second,spot,edge


class SpatialEventTests(unittest.TestCase):
    def test_real_two_proofs_have_exact_coordinates(self):
        a,b=proofs()
        self.assertEqual(a["confirmed_source_region"]["x"],29)
        self.assertEqual(a["settled_arrival"],{"x":9,"y":12})
        self.assertEqual(b["confirmed_source_region"]["x"],52)
        self.assertEqual(b["confirmed_source_region"]["y"],233)
        self.assertEqual(b["settled_arrival"],{"x":17,"y":37})
        self.assertEqual(b["pack_switch_frame"],663189)
        self.assertEqual(b["first_selector_pair_convergence_frame"],663218)
        self.assertEqual(b["first_settled_arrival_frame"],663271)
        self.assertFalse(a["static_opcode_cpu_execution_proven"])

    def test_synthetic_v2_spatial_join_proves_only_movement(self):
        f,g,hotspot,edge=synthetic()
        got=prove(f,g,hotspot,edge,
                  expected_source_pack=0x4C,expected_destination_pack=0x50)
        self.assertEqual(got["first_observed_source_contact_frame"],663047)
        self.assertFalse(got["static_opcode_cpu_execution_proven"])
        self.assertTrue(got["runtime_map_movement_proven"])
        self.assertEqual(got["new_graph_edges_promoted"],0)

    def test_wrong_hotspot_rejected(self):
        f,g,hotspot,edge=synthetic()
        hotspot["source_grid_x"]="54"
        with self.assertRaisesRegex(ValueError,"source never entered"):
            prove(f,g,hotspot,edge,expected_source_pack=0x4C,expected_destination_pack=0x50)

    def test_wrong_destination_rejected(self):
        f,g,hotspot,edge=synthetic()
        hotspot["destination_x"]="30"
        with self.assertRaisesRegex(ValueError,"Runtime arrival"):
            prove(f,g,hotspot,edge,expected_source_pack=0x4C,expected_destination_pack=0x50)

    def test_legacy_v1_not_a_v2_spatial_proof(self):
        f,g,hotspot,edge=synthetic()
        f["schema_version"]=1
        for row in (f["before"],*f["samples"],f["after"]):
            for key in ("w0306","w126e","w12b4","w12b5"):row.pop(key)
        with self.assertRaisesRegex(ValueError,"schema differ"):
            prove(f,g,hotspot,edge,expected_source_pack=0x4C,expected_destination_pack=0x50)

    def test_existing_edge_join_preserves_strong_candidate(self):
        world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
        source=copy.deepcopy(world["transition_candidates"])
        for edge in source:edge.pop("runtime_spatial_proof",None)
        out,summary=apply_runtime_spatial_proofs(source,proofs())
        self.assertEqual(summary["attached_count"],2)
        self.assertEqual(summary["new_graph_edges"],0)
        self.assertEqual(len(out),len(source))
        for edge in out:
            if edge.get("runtime_spatial_proof"):
                self.assertEqual(edge["confidence"],"strong_candidate")
                self.assertFalse(edge["runtime_spatial_proof"]["script_opcode_PC_observed"])
                self.assertFalse(edge["runtime_spatial_proof"]["story_conditions_proven"])

    def test_forged_cpu_hit_proof_rejected(self):
        p=proofs()
        p[0]["static_opcode_cpu_execution_proven"]=True
        with self.assertRaisesRegex(ValueError,"unsupported confidence"):
            apply_runtime_spatial_proofs([{}],p)

    def test_duplicate_edge_id_rejected(self):
        p=proofs()
        p[1]["existing_viewer_transition_id"]=p[0]["existing_viewer_transition_id"]
        world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
        candidates=copy.deepcopy(world["transition_candidates"])
        for edge in candidates:edge.pop("runtime_spatial_proof",None)
        with self.assertRaisesRegex(ValueError,"duplicate transition"):
            apply_runtime_spatial_proofs(candidates,p)

    def test_bad_arrival_proof_rejected(self):
        w=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
        candidates=copy.deepcopy(w["transition_candidates"])
        for edge in candidates:edge.pop("runtime_spatial_proof",None)
        ps=proofs()
        ps[1]["settled_arrival"]["x"]=99
        with self.assertRaisesRegex(ValueError,"does not match"):
            apply_runtime_spatial_proofs(candidates,ps)

    def test_viewer_retains_56_edges_with_two_runtime_proofs(self):
        w=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
        self.assertEqual(len(w["transition_edges"]),57)
        self.assertEqual(len(w["maps"]),149)
        self.assertEqual(w["runtime_spatial_proof_summary"]["attached_count"],2)
        self.assertEqual(sum(bool(e.get("runtime_spatial_proof")) for e in w["transition_edges"]),2)


if __name__=="__main__":
    unittest.main()
