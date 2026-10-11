#!/usr/bin/env python3
"""24 genuine SNES three-turn path audits and Viewer route-overlay regression."""
from __future__ import annotations
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from attach_dungeon_controller_routes import attach,SCENES

class ThreeDungeonRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof=json.loads((ROOT/"data/maps/transitions/dungeon_three_pack_24_controller_turn_routes_20261011.json").read_text(encoding="utf-8"))
        cls.world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
    def original_maps(self):
        maps=copy.deepcopy(self.world["maps"])
        for m in maps:m.pop("runtime_controller_route_contexts",None)
        return maps
    def test_three_dungeons_and_real_24_routes(self):
        p=self.proof
        self.assertEqual(p["pack_scoped_routes"],{"0xBD":8,"0xB9":8,"0xAB":8})
        self.assertEqual(p["true_multiturn_controller_routes"],24)
        self.assertEqual(p["total_directional_gamepad_segments"],72)
        self.assertEqual(len(p["routes"]),24)
        self.assertEqual(p["real_controller_frames_per_segment"],72)
        self.assertEqual(p["neutral_frames_after_each_route"],120)
        self.assertTrue(p["created_from_hidden_lab_original_state_restored"])
    def test_exact_saved_world_entered_scene_config_and_pack(self):
        for r in self.proof["routes"]:
            cfg,xy=SCENES[r["source_scene_pack"]]
            self.assertEqual(r["source_config_id"],cfg)
            self.assertEqual(r["source_original_scene_xy"],xy)
            self.assertTrue(r["from_world_entrance_cheat_adjacent"])
            self.assertTrue(r["no_scene_xy_cheat_during_controller_path"])
            self.assertTrue(r["actual_SNES_gamepad_path"])
            self.assertTrue(r["source_pack_unchanged_in_all_observed_frames"])
    def test_exact_number_of_routes_per_map(self):
        found=[(m["config_id"],c) for m in self.world["maps"]
               for c in m.get("runtime_controller_route_contexts",[])]
        self.assertEqual(len(found),3)
        for config,ctx in found:
            self.assertEqual(ctx["route_count"],8)
            self.assertEqual(len(ctx["routes"]),8)
            self.assertEqual(config,SCENES[ctx["scene_pack"]][0])
            self.assertTrue(ctx["real_gamepad_movement_without_XY_cheat"])
            self.assertTrue(ctx["story_state_alternatives_unverified"])
    def test_every_route_was_contiguous_observed_tiles(self):
        for r in self.proof["routes"]:
            path=r["observed_position_trace_grid"]
            self.assertGreaterEqual(len(path),1)
            self.assertEqual(path[0],r["source_original_scene_xy"])
            self.assertEqual(path[-1],r["arrived_at_grid"])
            self.assertEqual(r["turn_endpoints_grid"][0],path[0])
            self.assertEqual(r["turn_endpoints_grid"][-1],path[-1])
            for a,b in zip(path,path[1:]):
                self.assertLessEqual(abs(a["x"]-b["x"])+abs(a["y"]-b["y"]),1)
    def test_known_observed_tiles_35_57_57(self):
        metrics=self.world["runtime_dungeon_turn_route_summary"]
        self.assertEqual(metrics["observed_distinct_grid_cells_by_pack"],
                         {"0xBD":35,"0xB9":57,"0xAB":57})
        for pack,expected in metrics["observed_distinct_grid_cells_by_pack"].items():
            tiles={(p["x"],p["y"]) for r in self.proof["routes"]
                   if r["source_scene_pack"]==pack
                   for p in r["observed_position_trace_grid"]}
            self.assertEqual(len(tiles),expected)
    def test_no_invented_map_edges_or_exits(self):
        self.assertEqual(self.proof["added_cross_map_transition_edges"],0)
        self.assertFalse(self.proof["other_map_exits_universally_excluded"])
        self.assertTrue(all(r["no_new_map_transition_verified_this_route"]
                            for r in self.proof["routes"]))
        self.assertTrue(all(not r["other_story_phase_or_turn_routes_excluded"]
                            for r in self.proof["routes"]))
        self.assertEqual(len(self.world["transition_edges"]),77)
        self.assertEqual(len(self.world["transition_candidates"]),1314)
    def test_source_provenance_sha256_but_no_captures_committed(self):
        self.assertTrue(self.proof["raw_ROM_screenshots_savestates_frames_not_committed"])
        for r in self.proof["routes"]:
            self.assertEqual(len(r["gamepad_frame_sha256"]),3)
            self.assertTrue(all(len(h)==64 for h in r["gamepad_frame_sha256"]))
            self.assertEqual(len(r["neutral_frame_sha256"]),64)
            self.assertEqual(len(r["final_onscreen_screenshot_sha256"]),64)
            self.assertFalse(r["raw_ROM_screenshot_and_frame_data_committed"])
            self.assertFalse(r["actual_CPU_handler_PC_observed"])
    def test_rebuild_deterministic_contexts(self):
        maps,summary=attach(self.original_maps(),self.proof,self.world["transition_edges"])
        self.assertEqual(len(maps),149)
        self.assertEqual(summary["verified_controller_route_count"],24)
        self.assertEqual(summary["new_graph_edges"],0)
        actual={m["config_id"]:m.get("runtime_controller_route_contexts")
                for m in self.world["maps"] if m.get("runtime_controller_route_contexts")}
        rebuilt={m["config_id"]:m.get("runtime_controller_route_contexts")
                 for m in maps if m.get("runtime_controller_route_contexts")}
        self.assertEqual(actual,rebuilt)
    def test_duplicate_map_context_rejected(self):
        with self.assertRaisesRegex(ValueError,"Repeated"):
            attach(self.world["maps"],self.proof,self.world["transition_edges"])
    def test_forged_map_switch_claim_rejected(self):
        bad=copy.deepcopy(self.proof)
        bad["routes"][0]["no_new_map_transition_verified_this_route"]=False
        with self.assertRaisesRegex(ValueError,"Unverified"):
            attach(self.original_maps(),bad,self.world["transition_edges"])
    def test_jump_between_nonadjacent_tiles_rejected(self):
        bad=copy.deepcopy(self.proof)
        bad["routes"][0]["observed_position_trace_grid"][1]={"x":200,"y":200}
        with self.assertRaisesRegex(ValueError,"skips tile"):
            attach(self.original_maps(),bad,self.world["transition_edges"])
    def test_forged_all_story_states_rejected(self):
        bad=copy.deepcopy(self.proof)
        bad["other_map_exits_universally_excluded"]=True
        with self.assertRaisesRegex(ValueError,"Missing protected"):
            attach(self.original_maps(),bad,self.world["transition_edges"])
    def test_invalid_pack_identity_rejected(self):
        bad=copy.deepcopy(self.proof)
        bad["routes"][0]["source_scene_pack"]="0xAB"
        with self.assertRaisesRegex(ValueError,"Unverified"):
            attach(self.original_maps(),bad,self.world["transition_edges"])
    def test_viewer_interactive_controls_and_no_edge_promotion(self):
        html=(ROOT/"viewer/index.html").read_text(encoding="utf-8")
        js=(ROOT/"viewer/viewer.js").read_text(encoding="utf-8")
        self.assertIn('id="routePanel"',html)
        self.assertIn('id="routesToggle"',html)
        self.assertIn('id="routeLayer"',html)
        self.assertIn("function renderControllerRoutes(m)",js)
        self.assertIn("function renderControllerTrail(m)",js)
        self.assertIn("selectedRouteId=r.id",js)
        self.assertIn("renderFocus(m)",js)
        self.assertIn("other_story_phase_or_turn_routes_excluded",str(self.proof["routes"][0]))
    def test_progress_remains_original_baseline(self):
        self.assertEqual(len(self.world["maps"]),149)
        self.assertEqual(self.world["runtime_location_title_attached_count"],26)
        self.assertEqual(self.world["project_progress"]["overall_percent"],51.4)
if __name__=="__main__":unittest.main()
