#!/usr/bin/env python3
"""Six direction-specific nonreturns and exact independent Up/Down drift in pack96."""
from __future__ import annotations
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from attach_six_scene_directional_probes import attach,EXPECTED

class SceneSixUpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
        cls.up=json.loads((ROOT/"data/maps/transitions/six_scene_up_no_pack_switch_20261011.json").read_text(encoding="utf-8"))
        cls.down=json.loads((ROOT/"data/maps/transitions/world_14_reverse_returns_after_cheat_arrivals_20261011.json").read_text(encoding="utf-8"))
        cls.forced=json.loads((ROOT/"data/maps/transitions/pack96_up_down_identical_forced_movement_20261011.json").read_text(encoding="utf-8"))
    def test_six_real_up_trials_no_scene_switch(self):
        d=self.up
        self.assertEqual(set(d["six_exact_scopes"]),EXPECTED)
        self.assertEqual(len(d["probes"]),6)
        self.assertTrue(d["Up_trial_no_coordinate_cheat"])
        self.assertTrue(d["all_original_hidden_emulator_states_restored"])
        self.assertFalse(d["universal_no_exit_claim"])
        for p in d["probes"]:
            self.assertEqual(p["controller"],"Up")
            self.assertEqual(p["controller_frames"],72)
            self.assertEqual(p["neutral_frames"],120)
            self.assertTrue(p["no_pack_switch_in_observation"])
            self.assertFalse(p["other_direction_or_story_state_exits_proven_absent"])
            self.assertFalse(p["raw_frame_capture_committed"])
            self.assertEqual(len(p["trace_sha256"]),3)
            self.assertTrue(all(len(h)==64 for h in p["trace_sha256"]))
    def test_pack96_opposing_buttons_same_204_frame_positions(self):
        f=self.forced
        self.assertEqual(f["source_config_id"],"cfg_t09_l098_v2")
        self.assertEqual(f["pack"],"0x96")
        self.assertEqual(f["compared_actual_buttons"],["Down","Up"])
        self.assertEqual(f["same_game_frame_range"],[663329,663532])
        self.assertEqual(f["both_direction_position_series_identical_frame_count"],204)
        self.assertTrue(f["downward_every_nine_frames"])
        self.assertTrue(f["same_pack_during_entire_span"])
        self.assertEqual(f["last_xy"],{"x":39,"y":24})
        self.assertFalse(f["generalizes_to_other_savestates"])
        self.assertFalse(f["actual_CPU_opcode_PC_proven"])
    def test_seven_downward_steps_at_nine_frame_intervals(self):
        f=self.forced
        self.assertEqual([p["frame"] for p in f["observed_positions"]],
                         [663333,663342,663351,663360,663369,663378,663387])
        self.assertEqual([p["y"] for p in f["observed_positions"]],[18,19,20,21,22,23,24])
        self.assertEqual({p["x"] for p in f["observed_positions"]},{39})
        self.assertEqual(len(f["down_trace_sha256"]),3)
        self.assertEqual(len(f["up_trace_sha256"]),3)
    def test_all_six_scoped_map_records_attached_once(self):
        matches=[(m["config_id"],c) for m in self.world["maps"]
                 for c in m.get("runtime_scene_directional_probe_contexts",[])]
        self.assertEqual(len(matches),6)
        self.assertEqual({x["source_pack"] for _,x in matches},EXPECTED)
        for mapid,c in matches:
            self.assertEqual(mapid,c["source_config_id"])
            self.assertEqual(c["scope"],"this_runtime_pack_and_save_state_only")
            self.assertTrue(c["local_down_no_map_switch"])
            self.assertTrue(c["local_up_no_map_switch"])
            self.assertFalse(c["other_stories_or_directions_excluded"])
            self.assertTrue(c["original_world_entrance_cheat_seeded"])
    def test_pack96_motion_propagated_to_only_its_exact_map(self):
        matches=[(m["config_id"],c) for m in self.world["maps"]
                 for c in m.get("runtime_scene_directional_probe_contexts",[])
                 if c["source_pack"]=="0x96"]
        self.assertEqual(len(matches),1)
        config,context=matches[0]
        self.assertEqual(config,"cfg_t09_l098_v2")
        motion=context["controller_direction_independent_movement"]
        self.assertEqual(motion["position_trace_identical_frame_count"],204)
        self.assertEqual(motion["forced_path_to"],{"x":39,"y":24})
        self.assertTrue(motion["specific_native_handler_unknown"])
    def test_faithful_reconstruction_and_no_new_graph_edges(self):
        source=copy.deepcopy(self.world["maps"])
        for m in source:m.pop("runtime_scene_directional_probe_contexts",None)
        new,summary=attach(source,self.up,self.down,self.forced)
        self.assertEqual(len(new),len(source))
        self.assertEqual(summary["world_transition_edges_created"],0)
        self.assertEqual(summary["up_local_trials_without_switch"],6)
        self.assertEqual(summary["pack96_identical_directional_motion_frames"],204)
        self.assertEqual(len(self.world["transition_edges"]),77)
        self.assertEqual(len(self.world["transition_candidates"]),1314)
    def test_forged_general_no_exit_claim_rejected(self):
        bad=copy.deepcopy(self.up)
        bad["universal_no_exit_claim"]=True
        with self.assertRaisesRegex(ValueError,"Incomplete six-scene"):
            attach(self.world["maps"],bad,self.down,self.forced)
    def test_forged_exact_frame_identity_rejected(self):
        bad=copy.deepcopy(self.forced)
        bad["both_direction_position_series_identical_frame_count"]=203
        with self.assertRaisesRegex(ValueError,"exact independent proof"):
            attach(self.world["maps"],self.up,self.down,bad)
    def test_duplicate_attach_rejected(self):
        with self.assertRaisesRegex(ValueError,"Duplicate local scene"):
            attach(self.world["maps"],self.up,self.down,self.forced)
    def test_scoped_replay_does_not_change_public_progress(self):
        self.assertEqual(len(self.world["maps"]),149)
        self.assertEqual(self.world["runtime_scene_directional_six_up_summary"]["up_local_trials_without_switch"],6)
        self.assertEqual(self.world["runtime_scene_directional_six_up_summary"]["world_transition_edges_created"],0)
        self.assertEqual(self.world["project_progress"]["overall_percent"],51.4)

if __name__=="__main__":unittest.main()
