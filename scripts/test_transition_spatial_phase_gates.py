#!/usr/bin/env python3
"""Conservative spatial and unresolved story-phase transition gate tests."""
from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from transition_gate_predicates import (
    annotate_edge_gate, evaluate_inspected_position, phase_ambiguity_for, spatial_gate_for
)
from triage_unbound_transition_sources import queue


def edge():
    return {
        "transition_id":"sample",
        "source_config_id":"cfg_world",
        "destination_pack":"0xCE",
        "destination_entry_id":"0x02",
        "destination_x":22,"destination_y":28,
        "destination_config_id":None,
        "trigger_addr":"CC:1160",
        "source_hotspot_binding":{
            "hotspot_id":"hotspot_CC_1160",
            "source_grid_x":238,"source_grid_y":173,
            "source_width":1,"source_height":1,
            "provenance":"verified_point_region"
        }
    }


class SpatialGateTests(unittest.TestCase):
    def setUp(self):
        self.raw=edge()
        self.gate=annotate_edge_gate(self.raw,{"evaluation":"unknown","navigable_now":False})

    def test_coordinate_outside_proven_region_fails_closed(self):
        got=evaluate_inspected_position(self.gate,config_id="cfg_world",grid_x=237,grid_y=173)
        self.assertEqual(got["spatial"],"false")
        self.assertEqual(got["activation"],"false")

    def test_inside_does_not_prove_story_activation(self):
        got=evaluate_inspected_position(self.gate,config_id="cfg_world",grid_x=238,grid_y=173)
        self.assertEqual(got["spatial"],"true")
        self.assertEqual(got["activation"],"unknown")
        self.assertIs(self.gate["navigable_now"],False)

    def test_missing_position_or_source_map_stays_unknown(self):
        for kwargs in [{"config_id":"cfg_world"},{"config_id":None,"grid_x":238,"grid_y":173}]:
            self.assertEqual(evaluate_inspected_position(self.gate,**kwargs)["activation"],"unknown")

    def test_wrong_selected_map_is_incompatible(self):
        got=evaluate_inspected_position(self.gate,config_id="cfg_elsewhere",grid_x=238,grid_y=173)
        self.assertEqual(got["activation"],"false")

    def test_native_candidate_not_treated_as_exclusive_spatial_region(self):
        e={"source_config_id":"cfg_world","native_boundary_context":{
            "source_region":{"x":8,"y":12,"width":3,"height":1}
        }}
        self.assertIsNone(spatial_gate_for(e))
        gate=annotate_edge_gate(e,{"evaluation":"unknown","navigable_now":False})
        self.assertEqual(evaluate_inspected_position(gate,config_id="cfg_world",grid_x=7,grid_y=12)["activation"],"unknown")

    def test_phase_destination_set_retained_without_promoting(self):
        data=json.loads((ROOT/"data/events/transition_CC_1160_phase_candidates.json").read_text(encoding="utf-8"))
        e=edge()
        e["source_config_id"]=data["source_config_id"]
        phase=phase_ambiguity_for(e,data)
        self.assertEqual(len(phase["candidate_config_ids"]),5)
        self.assertFalse(phase["resolved_by_current_story_state"])
        self.assertIsNone(e["destination_config_id"])

    def test_phase_mismatch_is_rejected(self):
        data=json.loads((ROOT/"data/events/transition_CC_1160_phase_candidates.json").read_text(encoding="utf-8"))
        e=edge()
        e["source_config_id"]=data["source_config_id"]
        e["destination_x"]=999
        with self.assertRaises(ValueError):
            phase_ambiguity_for(e,data)

    def test_integrated_viewer_world_has_one_phase_family(self):
        world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
        candidates=[x for x in world["transition_candidates"] if x.get("phase_destination_ambiguity")]
        self.assertEqual(len(candidates),1)
        self.assertIsNone(candidates[0]["destination_config_id"])
        self.assertEqual(world["transition_catalog_summary"]["spatial_predicate_candidate_count"],54)
        self.assertEqual(world["transition_catalog_summary"]["bound_edge_count"],56)

    def test_unbound_queue_does_not_change_candidate_source(self):
        data={
            "transition_candidates":[
                {"transition_id":"a","trigger_type":"vm_opcode_0x56_terminal","script_pack":"0x70","source_config_id":None},
                {"transition_id":"b","trigger_type":"vm_opcode_0x56_terminal","script_pack":"0x72","source_config_id":"known"}
            ]
        }
        rows=[{"pack_id_hex":"0x70","config_id":"cfg_a"}]
        result=queue(data,rows)
        self.assertEqual(result["source_unbound_after_overlay"],1)
        self.assertEqual(result["pack_context_class_counts"]["one_pack_context_candidate_not_proof"],1)
        self.assertIsNone(data["transition_candidates"][0]["source_config_id"])


if __name__=="__main__":
    unittest.main()
