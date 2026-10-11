#!/usr/bin/env python3
"""Pack60 continuing NPC A dialogue, dark transition, changed village + real return."""
from __future__ import annotations
from pathlib import Path
import copy,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from attach_pack60_village_event_return import attach,EDGE_ID

class Pack60ExtendedEventTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof=json.loads((ROOT/"data/maps/transitions/pack60_dialogue_phase_world_return_20261011.json").read_text(encoding="utf-8"))
        cls.world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
        cls.edge=next(x for x in cls.world["transition_edges"] if x["transition_id"]==EDGE_ID)
    def origin_maps(self):
        maps=copy.deepcopy(self.world["maps"])
        for m in maps:m.pop("runtime_pack60_village_visual_event_contexts",None)
        return maps
    def origin_candidates(self):
        return [copy.deepcopy(x) for x in self.world["transition_candidates"] if x["transition_id"]!=EDGE_ID]
    def test_saved_world_entry_and_actual_A_sequence(self):
        p=self.proof
        self.assertEqual(p["source_world_transition_id"],"catalog_transition_0755")
        self.assertEqual(p["source_config_id"],"cfg_t04_l035_v2")
        self.assertEqual(p["source_arrival_xy"],{"x":37,"y":56})
        self.assertEqual(p["A_presses_in_initial_village_study"],12)
        self.assertEqual(p["additional_A_presses_in_extension"],24)
        self.assertEqual(p["all_real_SNES_A_presses"],36)
        self.assertEqual(len(p["recorded_A_screen_phases"]),24)
        self.assertEqual([x["absolute_ordinal_A"] for x in p["recorded_A_screen_phases"]],list(range(13,37)))
    def test_visual_event_dark_to_transformed_scene(self):
        p=self.proof
        self.assertTrue(p["A17_to_A21_additional_black_screenshot_identical"])
        self.assertEqual(p["black_screenshot_sha256"],
                         "6BE1250C4F701AA84D921C77F05D8F95753B441F06F39E55D233D4DE0EE9FBC0")
        self.assertEqual(p["visual_transformation_described_from_local_screenshots"],
                         "pink_flowery_village_to_brown_withered_vegetation")
        self.assertNotEqual(p["original_pre_event_screenshot_sha256"],
                            p["transformed_village_onscreen_sha256"])
        self.assertEqual(len(p["transformed_village_onscreen_sha256"]),64)
        self.assertFalse(p["exact_visual_event_trigger_A_count_proven"])
    def test_world_return_after_event_not_at_initial_dialogue_12(self):
        self.assertEqual(self.proof["return_after_A36_controller"],"Down")
        self.assertEqual(self.proof["return_after_A36_controller_frames"],96)
        self.assertEqual(self.proof["return_world_pack"],"0x4C")
        self.assertEqual(self.proof["return_world_xy_this_saved_context"],{"x":59,"y":155})
        self.assertEqual(self.proof["world_scene_switch_frame"],664366)
        self.assertEqual(self.proof["world_stable_neutral_frames"],360)
        self.assertEqual(len(self.proof["long_return_frame_sha256"]),4)
    def test_four_walk_results_after_visual_event(self):
        expect={"Down":("0x4C",[59,155]),"Up":("0x60",[37,40]),
                "Left":("0x60",[36,56]),"Right":("0x60",[38,56])}
        actual=self.proof["after_A36_four_direction_real_controller_results"]
        self.assertEqual(set(actual),set(expect))
        for d,(pack,xy) in expect.items():
            self.assertEqual(actual[d]["scene_pack_after"],pack)
            self.assertEqual(actual[d]["xy"],xy)
            self.assertEqual(len(actual[d]["controller_sha256"]),64)
            self.assertEqual(len(actual[d]["neutral_sha256"]),64)
    def test_correct_pack_and_saved_world_xy_against_rom_source(self):
        source=next(e for e in self.world["transition_edges"]
                    if e["transition_id"]=="catalog_transition_0755")
        self.assertEqual(source["destination_pack"],"0x60")
        self.assertEqual(source["destination_config_id"],"cfg_t04_l035_v2")
        h=source["source_hotspot_binding"]
        self.assertEqual((h["source_grid_x"],h["source_grid_y"]),(59,155))
        self.assertEqual(self.edge["source_config_id"],"cfg_t04_l035_v2")
        self.assertEqual(self.edge["destination_config_id"],"cfg_t01_l001_v1")
        self.assertEqual((self.edge["destination_x"],self.edge["destination_y"]),(59,155))
    def test_context_is_not_assigned_to_all_village_maps(self):
        contexts=[(m["config_id"],c) for m in self.world["maps"]
                 for c in m.get("runtime_pack60_village_visual_event_contexts",[])]
        self.assertEqual(len(contexts),1)
        cfg,context=contexts[0]
        self.assertEqual(cfg,"cfg_t04_l035_v2")
        self.assertEqual(context["source_pack"],"0x60")
        self.assertTrue(context["onscreen_pink_flowers_to_brown_withered_village"])
        self.assertFalse(context["event_exact_minimal_A_count_proven"])
        self.assertTrue(context["story_gates_unknown"])
    def test_event_discovery_not_presented_as_unconditional_route(self):
        p=self.proof
        self.assertTrue(p["original_world_entry_cheat_seeded"])
        self.assertFalse(p["scene_controller_XY_coordinate_cheat_used"])
        self.assertFalse(p["exact_story_gates_proven"])
        self.assertFalse(p["dialogue_event_cpu_handler_pc_observed"])
        self.assertFalse(p["return_destination_for_other_saves_proven"])
        self.assertFalse(p["source_exact_return_trigger_cell_proven"])
        self.assertFalse(p["original_world_access_without_cheat_proven"])
        pr=self.edge["runtime_pack60_village_phase_world_return_proof"]
        self.assertFalse(pr["CPU_handler_PC_observed"])
        self.assertFalse(pr["story_activation_gates_proven"])
        self.assertFalse(pr["normal_world_access_proven"])
        self.assertFalse(pr["exact_source_trigger_cell_proven"])
        self.assertEqual(self.edge["activation_gate"]["evaluation"],"unknown")
        self.assertFalse(self.edge["activation_gate"]["navigable_now"])
    def test_deterministic_attachment_one_new_edge(self):
        maps,edges,summary=attach(self.origin_maps(),self.origin_candidates(),self.proof)
        self.assertEqual(len(maps),149)
        self.assertEqual(len(edges),len(self.origin_candidates())+1)
        self.assertEqual(summary["new_verified_pack60_saved_world_return"],1)
        self.assertTrue(summary["confirmed_visual_transformation_in_one_scene_state"])
        self.assertEqual(edges[-1]["transition_id"],EDGE_ID)
    def test_double_attachment_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            attach(self.world["maps"],self.world["transition_candidates"],self.proof)
    def test_forged_universal_story_state_rejected(self):
        x=copy.deepcopy(self.proof)
        x["exact_story_gates_proven"]=True
        with self.assertRaisesRegex(ValueError,"incomplete"):
            attach(self.origin_maps(),self.origin_candidates(),x)
    def test_forged_early_return_was_not_proven(self):
        x=copy.deepcopy(self.proof)
        x["all_real_SNES_A_presses"]=12
        with self.assertRaisesRegex(ValueError,"incomplete"):
            attach(self.origin_maps(),self.origin_candidates(),x)
    def test_forged_world_return_position_rejected(self):
        x=copy.deepcopy(self.proof)
        x["return_world_xy_this_saved_context"]={"x":37,"y":56}
        with self.assertRaisesRegex(ValueError,"incomplete"):
            attach(self.origin_maps(),self.origin_candidates(),x)
    def test_no_rom_or_screens_uploaded(self):
        self.assertTrue(self.proof["runtime_source_emulator_restored_after_probes"])
        self.assertFalse(self.proof["raw_ROM_screenshots_traces_savestates_committed"])
        self.assertTrue(all(len(x["gamepad_trace_sha256"])==64
                            for x in self.proof["recorded_A_screen_phases"]))
    def test_graph_and_titles_keep_progress_consistent(self):
        self.assertEqual(len(self.world["maps"]),149)
        self.assertEqual(len(self.world["transition_edges"]),77)
        self.assertEqual(len(self.world["transition_candidates"]),1314)
        self.assertEqual(self.world["transition_catalog_summary"]["bound_edge_count"],77)
        self.assertEqual(self.world["runtime_location_title_attached_count"],26)
        self.assertEqual(self.world["runtime_pack60_village_event_world_return_summary"]["new_verified_pack60_saved_world_return"],1)
        self.assertEqual(self.world["project_progress"]["overall_percent"],51.4)
if __name__=="__main__":unittest.main()
