#!/usr/bin/env python3
"""Fail-closed pack96 five-way no-input and title-unlocked cave-to-world regressions."""
from __future__ import annotations
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from attach_pack96_modal_world_return import inject,EDGE_ID

class Pack96ModalReturnTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof=json.loads((ROOT/"data/maps/transitions/pack96_5way_modal_and_world_return_20261011.json").read_text(encoding="utf-8"))
        cls.title=json.loads((ROOT/"data/maps/context/pack96_runtime_location_title_20261011.json").read_text(encoding="utf-8"))
        cls.world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
        cls.edge=next(e for e in cls.world["transition_edges"] if e["transition_id"]==EDGE_ID)
    def without_new_edge(self):
        return [copy.deepcopy(c) for c in self.world["transition_candidates"] if c["transition_id"]!=EDGE_ID]
    def test_identical_five_control_conditions_204_frames(self):
        p=self.proof
        self.assertEqual(p["conditions"],["Down","Up","Left","Right","None"])
        self.assertTrue(p["five_conditions_full_204_frame_position_identity"])
        self.assertEqual(p["identical_frame_count_each"],204)
        self.assertEqual(p["same_frame_range"],[663329,663532])
        self.assertTrue(p["neutral_no_buttons_test_observed"])
        self.assertTrue(p["real_left_right_gamepad_presses_observed"])
        self.assertEqual(len(p["five_way_trace_sha256"]),5)
        self.assertTrue(all(len(a)>=3 for a in p["five_way_trace_sha256"].values()))
    def test_automated_descent_7_steps_and_9_frames(self):
        p=self.proof
        steps=p["descent_steps"]
        self.assertEqual([x["frame"] for x in steps],
                         [663333,663342,663351,663360,663369,663378,663387])
        self.assertEqual([x["y"] for x in steps],list(range(18,25)))
        self.assertEqual({x["x"] for x in steps},{39})
        self.assertEqual(p["end_of_automatic_descent_xy"],{"x":39,"y":24})
    def test_cave_name_on_exact_pack_not_layout_globally(self):
        p=self.proof
        self.assertEqual(p["location_title_onscreen"],"音無しの洞窟")
        self.assertEqual(self.title["map_config_id"],"cfg_t09_l098_v2")
        self.assertEqual(self.title["runtime_pack_id_hex"],"0x96")
        self.assertEqual(self.title["onscreen_title"],"音無しの洞窟")
        self.assertEqual(self.title["screenshot_sha256"],
                         p["display_title_at_blocked_state_screenshot_sha256"])
        self.assertFalse(self.title["applies_to_all_configs_sharing_tileset_layout"])
        self.assertFalse(self.title["screenshot_committed"])
    def test_pack96_and_pack98_both_have_local_named_contexts(self):
        found={(m["config_id"],c["pack_id_hex"]):c["label"] for m in self.world["maps"]
               for c in m.get("runtime_pack_location_contexts",[])}
        self.assertEqual(found[("cfg_t09_l098_v2","0x96")],"音無しの洞窟")
        self.assertEqual(found[("cfg_t09_l097_v2","0x98")],"音無しの洞窟")
        self.assertEqual(len(found),26)
        self.assertEqual(self.world["runtime_location_title_attached_count"],26)
    def test_modal_requires_a_then_up_true_controller(self):
        p=self.proof
        self.assertTrue(p["title_modal_blocked_directional_movement"])
        self.assertTrue(p["no_button_then_right_72_blocked_verified"])
        self.assertTrue(p["A_then_right_72_walkable_verified"])
        self.assertEqual(len(p["no_button_right_traces_sha256"]),2)
        self.assertEqual(len(p["A_then_right_traces_sha256"]),3)
        self.assertTrue(p["A_press_then_Up_world_return_observed"])
        self.assertEqual(p["post_title_A_frames"],8)
        self.assertEqual(p["post_title_neutral_frames"],64)
        self.assertEqual(p["world_return_actual_gamepad_direction"],"Up")
        self.assertEqual(p["world_return_actual_gamepad_frames"],96)
        self.assertEqual(len(p["modal_escape_full_trace_sha256"]),7)
        self.assertTrue(all(len(h)==64 for h in p["modal_escape_full_trace_sha256"]))
    def test_delayed_world_xy_not_false_transient(self):
        p=self.proof
        self.assertEqual(p["pack_switch_frame"],663807)
        self.assertEqual(p["temporary_world_pack_xy"],{"x":39,"y":7})
        self.assertEqual(p["world_arrival_first_stable_frame"],663897)
        self.assertEqual(p["world_arrival_xy"],{"x":50,"y":129})
        self.assertEqual(p["world_stable_through_frame"],664216)
        self.assertTrue(p["world_raw_selector_converged"])
        self.assertEqual((self.edge["destination_x"],self.edge["destination_y"]),(50,129))
        self.assertNotEqual((self.edge["destination_x"],self.edge["destination_y"]),(39,7))
    def test_exact_rom_proven_world_entry_matches_reverse_destination(self):
        initial=next(c for c in self.world["transition_edges"] if c["transition_id"]=="catalog_transition_0756")
        h=initial["source_hotspot_binding"]
        self.assertEqual((h["source_grid_x"],h["source_grid_y"]),(50,129))
        self.assertEqual(initial["destination_config_id"],"cfg_t09_l098_v2")
        self.assertEqual((initial["destination_x"],initial["destination_y"]),(39,17))
        self.assertEqual(self.edge["source_config_id"],"cfg_t09_l098_v2")
        self.assertEqual(self.edge["destination_config_id"],"cfg_t01_l001_v1")
        self.assertEqual(self.edge["destination_pack"],"0x4C")
    def test_saved_context_and_pc_limits_preserved(self):
        p=self.proof
        self.assertTrue(p["source_world_entry_was_cheat_seeded"])
        self.assertFalse(p["scene_controller_probe_wram_xy_cheat_used"])
        self.assertFalse(p["world_arrival_for_other_savestates_proven"])
        self.assertFalse(p["all_story_phases_verified"])
        self.assertFalse(p["exact_CPU_instruction_PC_observed"])
        self.assertFalse(p["natural_world_entry_walkability_proven"])
        self.assertFalse(p["modal_causal_code_handler_proven"])
        self.assertFalse(p["source_exit_exact_hotspot_tile_proven"])
        self.assertFalse(p["raw_traces_screens_ROM_or_states_committed"])
        live=self.edge["runtime_pack96_modal_world_return_proof"]
        self.assertFalse(live["source_normal_world_walkability_proven"])
        self.assertFalse(live["actual_CPU_instruction_PC_observed"])
        self.assertFalse(live["exact_trigger_tile_proven"])
        self.assertFalse(live["other_saved_contexts_universal"])
        self.assertFalse(self.edge["activation_gate"]["navigable_now"])
        self.assertEqual(self.edge["activation_gate"]["evaluation"],"unknown")
    def test_exact_candidate_injection_adds_one_edge(self):
        base=self.without_new_edge()
        out,summary=inject(base,self.proof,self.world["maps"])
        self.assertEqual(len(out),len(base)+1)
        self.assertEqual(summary["new_verified_modal_world_return_edge_count"],1)
        self.assertEqual(out[-1]["transition_id"],EDGE_ID)
        self.assertEqual(out[-1]["confidence"],"confirmed")
    def test_duplicate_edge_not_injected(self):
        with self.assertRaisesRegex(ValueError,"Already attached"):
            inject(self.world["transition_candidates"],self.proof,self.world["maps"])
    def test_false_story_flag_or_cpu_pc_rejected(self):
        for key in ("all_story_phases_verified","exact_CPU_instruction_PC_observed",
                    "world_arrival_for_other_savestates_proven"):
            f=copy.deepcopy(self.proof)
            f[key]=True
            with self.assertRaisesRegex(ValueError,"incomplete"):
                inject(self.without_new_edge(),f,self.world["maps"])
    def test_forged_transient_world_xy_rejected(self):
        f=copy.deepcopy(self.proof)
        f["world_arrival_xy"]={"x":39,"y":7}
        with self.assertRaisesRegex(ValueError,"incomplete"):
            inject(self.without_new_edge(),f,self.world["maps"])
    def test_graph_cardinality_and_title_count(self):
        self.assertEqual(len(self.world["maps"]),149)
        self.assertEqual(len(self.world["transition_edges"]),76)
        self.assertEqual(len(self.world["transition_candidates"]),1313)
        self.assertEqual(self.world["transition_catalog_summary"]["bound_edge_count"],76)
        self.assertEqual(self.world["runtime_pack96_modal_world_return_summary"]["new_verified_modal_world_return_edge_count"],1)
        self.assertEqual(self.world["project_progress"]["overall_percent"],51.4)

if __name__=="__main__":unittest.main()
