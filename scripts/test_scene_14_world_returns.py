#!/usr/bin/env python3
"""Guard 14 actual Down-triggered scene->saved-world transitions, not universality."""
from __future__ import annotations
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from add_14_scene_saved_world_returns import inject,PREFIX

class ReverseScene14Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof=json.loads((ROOT/"data/maps/transitions/world_14_reverse_returns_after_cheat_arrivals_20261011.json").read_text(encoding="utf-8"))
        cls.world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
        cls.entries=json.loads((ROOT/"data/maps/transitions/world_37_gamepad_entrances_after_cheat_20261011.json").read_text(encoding="utf-8"))
        cls.new=[x for x in cls.world["transition_edges"] if x["transition_id"].startswith(PREFIX)]
    def before_injection(self):
        return [copy.deepcopy(c) for c in self.world["transition_candidates"] if not c["transition_id"].startswith(PREFIX)]
    def test_20_contiguous_reverse_studies_14_confirmed(self):
        p=self.proof
        self.assertEqual(p["attempts"],20)
        self.assertEqual(p["confirmed_world_returns"],14)
        self.assertEqual(p["local_nonreturns"],6)
        self.assertEqual(len(p["verified_reverse_returns"]),14)
        self.assertEqual(len(p["unconfirmed_local_direction_returns"]),6)
        self.assertEqual(len({x["source_scene_pack"] for x in p["verified_reverse_returns"]}),14)
        self.assertEqual(len({x["source_scene_pack"] for x in p["unconfirmed_local_direction_returns"]}),6)
        self.assertTrue(p["all_batches_original_emulator_restored"])
        self.assertFalse(p["reverse_scene_controller_path_Wram_XY_cheat_used"])
        self.assertTrue(p["source_original_world_entrances_cheat_seeded"])
    def test_exact_world_coordinates_for_multiple_areas(self):
        by_pack={x["source_scene_pack"]:x for x in self.proof["verified_reverse_returns"]}
        self.assertEqual(by_pack["0x98"]["world_arrival_xy_in_this_saved_origin_context"],{"x":51,"y":122})
        self.assertEqual(by_pack["0x9E"]["world_arrival_xy_in_this_saved_origin_context"],{"x":124,"y":64})
        self.assertEqual(by_pack["0xAD"]["world_arrival_xy_in_this_saved_origin_context"],{"x":237,"y":37})
        self.assertEqual(by_pack["0xA9"]["world_arrival_xy_in_this_saved_origin_context"],{"x":39,"y":34})
        self.assertEqual(by_pack["0x65"]["world_arrival_xy_in_this_saved_origin_context"],{"x":195,"y":60})
        self.assertEqual(by_pack["0x83"]["world_arrival_xy_in_this_saved_origin_context"],{"x":127,"y":195})
        self.assertEqual(by_pack["0x8E"]["world_arrival_xy_in_this_saved_origin_context"],{"x":160,"y":4})
        self.assertEqual(by_pack["0xB1"]["world_arrival_xy_in_this_saved_origin_context"],{"x":206,"y":181})
    def test_six_unconfirmed_not_declared_no_exit(self):
        negative={x["source_scene_pack"]:x for x in self.proof["unconfirmed_local_direction_returns"]}
        self.assertEqual(set(negative),{"0x96","0xBD","0xB9","0xAB","0x82","0x60"})
        for x in negative.values():
            self.assertFalse(x["absence_of_exit_globally_proven"])
            self.assertTrue(x["other_directions_not_checked"])
            self.assertEqual(x["verified_reverse_result"],
                             "no_map_change_under_72_frame_down_then_120_neutral")
        self.assertEqual(negative["0x96"]["source_after_probe_xy"],{"x":39,"y":24})
    def test_runtime_source_tiles_not_mislabeled_exact_triggers(self):
        for edge in self.new:
            p=edge["runtime_scene_saved_world_return_proof"]
            self.assertFalse(p["exact_trigger_cell_CPU_proven"])
            self.assertIsNone(edge["source_hotspot_binding"])
            self.assertIsNone(edge["trigger_addr"])
            self.assertEqual(p["reverse_controller_input"],"Down")
            self.assertEqual(p["reverse_controller_frames"],72)
            self.assertTrue(p["observed_runtime_map_switch"])
    def test_context_scoping_unknown_story_and_pc(self):
        for edge in self.new:
            p=edge["runtime_scene_saved_world_return_proof"]
            self.assertFalse(p["return_world_xy_for_other_saves_verified"])
            self.assertFalse(p["source_world_walkability_proven"])
            self.assertFalse(p["all_story_gates_proven"])
            self.assertFalse(p["actual_native_CPU_PC_observed"])
            self.assertFalse(p["reverse_control_used_coordinate_warp"])
            self.assertTrue(p["source_reached_via_cheat_positioned_world_entrance"])
            self.assertFalse(edge["activation_gate"]["navigable_now"])
            self.assertEqual(edge["activation_gate"]["evaluation"],"unknown")
    def test_runtime_proof_matches_exact_incoming_world_pack(self):
        by_incoming={x["transition_id"]:x for x in self.entries["entries"]}
        for edge in self.new:
            incoming=by_incoming[edge["runtime_scene_saved_world_return_proof"]["incoming_world_transition_id"]]
            self.assertEqual(edge["source_config_id"],incoming["destination_config_id"])
            self.assertEqual(edge["source_pack"],incoming["destination_pack"])
            self.assertEqual(edge["destination_pack"],"0x4C")
            self.assertEqual(edge["destination_config_id"],"cfg_t01_l001_v1")
            p=edge["runtime_scene_saved_world_return_proof"]
            self.assertEqual((edge["destination_x"],edge["destination_y"]),
                              (p["return_world_xy_in_this_saved_context"]["x"],
                               p["return_world_xy_in_this_saved_context"]["y"]))
    def test_faithful_injection_adds_14_no_existing_mutation(self):
        base=self.before_injection()
        result,summary=inject(base,self.proof,self.world["maps"])
        self.assertEqual(len(result),len(base)+14)
        self.assertEqual(summary["new_confirmed_contextual_saved_world_edges"],14)
        self.assertEqual(summary["local_direction_nonreturns"],6)
        self.assertEqual(len(self.world["transition_candidates"]),len(result))
        self.assertEqual(len(self.world["transition_edges"]),77)
    def test_double_injection_rejected(self):
        with self.assertRaisesRegex(ValueError,"Duplicate injected"):
            inject(self.world["transition_candidates"],self.proof,self.world["maps"])
    def test_forged_saved_map_generality_rejected(self):
        proof=copy.deepcopy(self.proof)
        proof["verified_reverse_returns"][0]["world_arrival_same_for_other_saves_proven"]=True
        with self.assertRaisesRegex(ValueError,"lacks exact source"):
            inject(self.before_injection(),proof,self.world["maps"])
    def test_forged_cpu_pc_or_walkability_rejected(self):
        for key in ("CPU_handler_PC_observed","normal_world_route_to_original_entrance_proven"):
            proof=copy.deepcopy(self.proof)
            proof["verified_reverse_returns"][0][key]=True
            with self.assertRaises(ValueError):
                inject(self.before_injection(),proof,self.world["maps"])
    def test_corrupted_original_entry_source_rejected(self):
        proof=copy.deepcopy(self.proof)
        proof["verified_reverse_returns"][0]["source_config_id"]="cfg_unknown"
        with self.assertRaisesRegex(ValueError,"lacks exact source"):
            inject(self.before_injection(),proof,self.world["maps"])
    def test_sha_material_provenance_kept_local(self):
        for r in self.proof["verified_reverse_returns"]:
            self.assertTrue(r["frame_capture_raw_not_committed"])
            self.assertEqual(len(r["underlying_source_file_digest"]),4)
            self.assertTrue(all(len(h)==64 for h in r["underlying_source_file_digest"]))
            self.assertEqual(len(r["screenshot_sha256"]),64)
            self.assertGreaterEqual(r["world_stable_observed_frames"],8)
            self.assertTrue(r["requires_saved_world_origin_context"])
    def test_graph_counts(self):
        self.assertEqual(len(self.world["maps"]),149)
        self.assertEqual(len(self.world["transition_edges"]),77)
        self.assertEqual(len(self.world["transition_candidates"]),1314)
        self.assertEqual(self.world["transition_catalog_summary"]["bound_edge_count"],77)
        self.assertEqual(len(self.new),14)
        self.assertEqual(self.world["runtime_scene_reverse_world_14_summary"]["new_confirmed_contextual_saved_world_edges"],14)

if __name__=="__main__":unittest.main()
