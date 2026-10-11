#!/usr/bin/env python3
"""Five scene modal A actions, 20 real direction tests, and pack82 saved world return."""
from __future__ import annotations
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from attach_five_scene_A_pack82_return import attach,EDGE,PACKS,DIRECTIONS

class FiveScenesAndPack82Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
        cls.proof=json.loads((ROOT/"data/maps/transitions/five_scene_modal_tests_and_pack82_world_return_20261011.json").read_text(encoding="utf-8"))
        cls.edge=next(e for e in cls.world["transition_edges"] if e["transition_id"]==EDGE)
    def base_candidates(self):
        return [copy.deepcopy(c) for c in self.world["transition_candidates"] if c["transition_id"]!=EDGE]
    def base_maps(self):
        original=copy.deepcopy(self.world["maps"])
        for m in original:m.pop("runtime_five_scene_A_directional_contexts",None)
        return original
    def test_exact_five_packs_twenty_directions(self):
        p=self.proof
        self.assertEqual(p["five_scene_pack_contexts"],list(PACKS))
        self.assertEqual(p["five_scene_actual_A8_plus_four_direction_tests"],5)
        self.assertEqual(p["total_real_direction_probes"],20)
        self.assertEqual(len(p["scene_trials"]),5)
        for row in p["scene_trials"]:
            self.assertEqual({d["direction"] for d in row["directions"]},DIRECTIONS)
            self.assertTrue(row["real_A8_followed_by_neutral64"])
            self.assertFalse(row["actual_scene_probe_wram_xy_cheat_used"])
            self.assertFalse(row["scene_A_interaction_cause_of_walking_proven"])
            self.assertTrue(all(d["did_not_switch_pack_in_this_probe"] for d in row["directions"]))
            self.assertTrue(all(d["input_frames"]==96 and d["neutral_frames"]==120 for d in row["directions"]))
    def test_dungeon_local_walk_without_claimed_exit(self):
        by={s["source_scene_pack"]:s for s in self.proof["scene_trials"]}
        locations={
           "0xBD":{"Down":[15,38],"Up":[15,36],"Left":[14,37],"Right":[16,37]},
           "0xB9":{"Down":[68,31],"Up":[68,23],"Left":[62,25],"Right":[74,25]},
           "0xAB":{"Down":[22,11],"Up":[22,3],"Left":[16,5],"Right":[26,5]}
        }
        for pack,target in locations.items():
            self.assertEqual({d["direction"]:d["after_neutral_xy"] for d in by[pack]["directions"]},target)
            self.assertFalse(by[pack]["no_exit_other_stories_or_directions_proven"])
    def test_villages_remain_stationary_after_single_A(self):
        by={s["source_scene_pack"]:s for s in self.proof["scene_trials"]}
        for pack,xy in (("0x82",[40,59]),("0x60",[37,56])):
            self.assertEqual({tuple(d["after_neutral_xy"]) for d in by[pack]["directions"]},{tuple(xy)})
            self.assertFalse(by[pack]["all_story_states_reachable_proven"])
    def test_dialogue_A_count_12_both_villages(self):
        self.assertEqual(self.proof["village_twelve_A_dialogue_trials"],["0x82","0x60"])
        for row in self.proof["dialogue_sequences"]:
            self.assertEqual(row["actual_A_button_presses"],12)
            self.assertEqual(row["per_press_held_frames"],8)
            self.assertEqual(row["neutral_frames_between_presses"],20)
            self.assertTrue(row["scene_xy_unchanged_during_all_twelve_A_presses"])
            self.assertEqual(len(row["per_step"]),14)
            self.assertFalse(row["universal_story_state_proven"])
    def test_one_village_returns_the_other_does_not(self):
        by={x["pack"]:x for x in self.proof["dialogue_sequences"]}
        self.assertEqual(by["0x82"]["followup_destination_pack"],"0x4C")
        self.assertEqual(by["0x82"]["followup_destination_xy"],[175,189])
        self.assertEqual(by["0x60"]["followup_destination_pack"],"0x60")
        self.assertEqual(by["0x60"]["followup_destination_xy"],[37,56])
        self.assertTrue(self.proof["village_pack82_saved_world_return_reproduced"])
        self.assertFalse(self.proof["village_pack60_world_return_observed"])
    def test_world_return_is_real_direct_and_stable(self):
        p=self.proof["pack82_confirmed_world_return"]
        self.assertEqual(p["source_world_transition_id"],"catalog_transition_0791")
        self.assertEqual(p["world_switch_frame"],663683)
        self.assertEqual(p["world_destination_pack"],"0x4C")
        self.assertEqual(p["world_destination_xy_for_original_saved_world_context"],{"x":175,"y":189})
        self.assertEqual(p["world_arrival_stable_neutral_frames"],360)
        self.assertEqual(p["last_observed_world_frame"],664132)
        self.assertEqual(len(p["raw_frame_sha256"]),4)
        self.assertEqual(len(p["screenshot_sha256"]),4)
    def test_new_graph_edge_ties_to_exact_real_world_entry(self):
        e=self.edge
        inc=next(x for x in self.world["transition_edges"] if x["transition_id"]=="catalog_transition_0791")
        self.assertEqual(e["source_pack"],inc["destination_pack"])
        self.assertEqual(e["source_config_id"],inc["destination_config_id"])
        self.assertEqual(e["destination_pack"],"0x4C")
        self.assertEqual((e["destination_x"],e["destination_y"]),(175,189))
        self.assertEqual((inc["source_hotspot_binding"]["source_grid_x"],
                          inc["source_hotspot_binding"]["source_grid_y"]),(175,189))
        self.assertEqual(e["confidence"],"confirmed")
    def test_source_cpu_pc_story_and_walkability_never_forged(self):
        p=self.edge["runtime_pack82_dialogue_saved_world_return_proof"]
        self.assertTrue(p["observed_runtime_map_switch"])
        self.assertTrue(p["original_world_entrance_cheat_seeded"])
        self.assertFalse(p["reverse_gamepad_coordinate_cheat_used"])
        self.assertFalse(p["world_destination_in_other_saves_verified"])
        self.assertFalse(p["exact_source_event_trigger_tile_proven"])
        self.assertFalse(p["CPU_handler_PC_observed"])
        self.assertFalse(p["story_activation_gates_proven"])
        self.assertFalse(p["normal_world_access_proven"])
        self.assertIsNone(self.edge["source_hotspot_binding"])
        self.assertFalse(self.edge["activation_gate"]["navigable_now"])
        self.assertEqual(self.edge["activation_gate"]["evaluation"],"unknown")
    def test_all_five_contexts_bound_only_to_exact_map(self):
        contexts=[(m["config_id"],x) for m in self.world["maps"]
                  for x in m.get("runtime_five_scene_A_directional_contexts",[])]
        self.assertEqual(len(contexts),5)
        self.assertEqual({x["source_pack"] for _,x in contexts},set(PACKS))
        by_entry={c["transition_id"]:c for c in self.world["transition_edges"]}
        for cfg,row in contexts:
            self.assertEqual(by_entry[row["source_transition_id"]]["destination_config_id"],cfg)
            self.assertFalse(row["A_input_caused_walking_unlock_proven"])
            self.assertFalse(row["all_story_phases_and_exits_proven"])
    def test_faithful_injection_one_new_edge(self):
        maps,edges,summary=attach(self.base_maps(),self.base_candidates(),self.proof)
        self.assertEqual(len(edges),len(self.base_candidates())+1)
        self.assertEqual(len(maps),149)
        self.assertEqual(summary["new_verified_pack82_world_return_edges"],1)
        self.assertEqual(summary["actual_directional_scene_trials"],20)
        self.assertTrue(summary["unresolved_pack60_return"])
    def test_double_attach_rejected(self):
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            attach(self.world["maps"],self.world["transition_candidates"],self.proof)
    def test_forged_world_return_coordinate_rejected(self):
        x=copy.deepcopy(self.proof)
        x["pack82_confirmed_world_return"]["world_destination_xy_for_original_saved_world_context"]={"x":40,"y":59}
        with self.assertRaisesRegex(ValueError,"mismatch"):
            attach(self.base_maps(),self.base_candidates(),x)
    def test_false_claim_about_universal_walkability_rejected(self):
        x=copy.deepcopy(self.proof)
        x["scene_trials"][0]["all_story_states_reachable_proven"]=True
        with self.assertRaisesRegex(ValueError,"Unverified"):
            attach(self.base_maps(),self.base_candidates(),x)
    def test_graph_counts_and_unmodified_named_locations(self):
        self.assertEqual(len(self.world["maps"]),149)
        self.assertEqual(len(self.world["transition_edges"]),77)
        self.assertEqual(len(self.world["transition_candidates"]),1314)
        self.assertEqual(self.world["transition_catalog_summary"]["bound_edge_count"],77)
        self.assertEqual(self.world["runtime_location_title_attached_count"],26)
        self.assertEqual(self.world["runtime_five_scene_A_pack82_world_return_summary"]["new_verified_pack82_world_return_edges"],1)
        self.assertEqual(self.world["project_progress"]["overall_percent"],51.4)
if __name__=="__main__":unittest.main()
