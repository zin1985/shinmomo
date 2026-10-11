#!/usr/bin/env python3
"""ROM/scene-scoped regressions for 40 researched world entrances and 25 visible place names."""
from __future__ import annotations
import copy,csv,json,sys,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from attach_world_37_scene_entrance_batch import attach

class WorldSceneBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger=json.loads((ROOT/"data/maps/transitions/world_37_gamepad_entrances_after_cheat_20261011.json").read_text(encoding="utf-8"))
        cls.registry=json.loads((ROOT/"data/maps/context/world_batch_verified_onscreen_titles_20261011.json").read_text(encoding="utf-8"))
        cls.world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
        with (ROOT/"data/maps/context/map_location_identity_candidates_20260930.csv").open(encoding="utf-8-sig",newline="") as f:
            cls.csv_rows=list(csv.DictReader(f))

    def before_attach(self):
        original=copy.deepcopy(self.world["transition_candidates"])
        resolved=set(self.world["runtime_world_entrance_37_batch_summary"]["coordinate_resolved_existing_edge_ids"])
        for e in original:
            if e.get("runtime_world_entry_batch_probe"):
                e.pop("runtime_world_entry_batch_probe")
                if e["transition_id"] in resolved:
                    e["destination_x"]=None
                    e["destination_y"]=None
                    e.pop("destination_coordinate_origin",None)
            e.pop("runtime_world_entry_batch_negative_trial",None)
        return original

    def test_exact_40_attempt_37_success_3_local_no_switch(self):
        l=self.ledger
        self.assertEqual(l["total_attempted_hotspots"],40)
        self.assertEqual(l["successful_gamepad_world_to_ROM_pack"],37)
        self.assertEqual(l["failed_to_switch_this_local_attempt"],3)
        self.assertEqual(len(l["entries"]),37)
        self.assertEqual(len(l["local_no_switch_observations"]),3)
        self.assertEqual(len({e["transition_id"] for e in l["entries"]}),37)
        self.assertEqual(len({e["destination_pack"] for e in l["entries"]}),36)
        self.assertEqual(len({e["destination_config_id"] for e in l["entries"]}),32)

    def test_real_gamepad_not_infinite_flight_or_natural_world_reachability(self):
        l=self.ledger
        self.assertTrue(l["source_world_xy_cheat_positioned"])
        self.assertTrue(l["map_switch_triggered_by_real_controller"])
        self.assertFalse(l["normal_world_walking_routes_proven"])
        self.assertFalse(l["Hien_spell_cast_for_these_entries"])
        self.assertFalse(l["SNES_CPU_opcode_pc_observed"])
        self.assertFalse(l["all_story_states_accessible_proven"])
        self.assertTrue(l["no_raw_image_savestate_ROM_or_frame_json_committed"])
        self.assertTrue(l["underlying_emulator_restored_after_each_of_6_batches"])
        for e in l["entries"]:
            self.assertTrue(e["source_position_supplied_by_analysis_cheat"])
            self.assertFalse(e["normal_world_walking_route_to_source_proven"])
            self.assertEqual(e["real_snes_gamepad_input"],"Up")
            self.assertTrue(e["scene_pack_matches_rom_candidate"])
            self.assertFalse(e["cpu_rom_opcode_PC_observed"])
            self.assertTrue(e["source_hotspot_contact_frame"]<e["map_switch_frame"])
            self.assertEqual(e["cheat_positioned_approach_xy"]["y"],e["source_hotspot_xy"]["y"]+1)
            self.assertFalse(e["screenshot_raw_committed"])

    def test_existing_37_world_edges_have_actual_runtime_evidence(self):
        edges={e["transition_id"]:e for e in self.world["transition_edges"]}
        for item in self.ledger["entries"]:
            e=edges[item["transition_id"]]
            p=e["runtime_world_entry_batch_probe"]
            self.assertEqual(p["destination_pack"],item["destination_pack"])
            self.assertEqual(e["source_config_id"],"cfg_t01_l001_v1")
            self.assertEqual(e["destination_config_id"],item["destination_config_id"])
            self.assertEqual((e["destination_x"],e["destination_y"]),
                (item["settled_arrival_xy"]["x"],item["settled_arrival_xy"]["y"]))
            self.assertTrue(p["actual_SNES_gamepad_triggered_event"])
            self.assertFalse(p["normal_world_walking_route_proven"])
            self.assertFalse(p["ROM_opcode_CPU_executed_proven"])
            self.assertFalse(e["activation_gate"]["navigable_now"])

    def test_five_previously_unknown_arrival_coordinates_resolved(self):
        summary=self.world["runtime_world_entrance_37_batch_summary"]
        self.assertEqual(summary["coordinate_resolved_existing_edges_count"],5)
        self.assertEqual(len(summary["coordinate_resolved_existing_edge_ids"]),5)
        entry=next(e for e in self.world["transition_edges"] if e["transition_id"]=="catalog_transition_0756")
        self.assertEqual(entry["destination_pack"],"0x96")
        self.assertEqual((entry["destination_x"],entry["destination_y"]),(39,17))
        self.assertEqual(entry["destination_coordinate_origin"],
                         "runtime_arrival_after_cheat_adjacent_gamepad_world_entry")
        self.assertEqual(entry["confidence"],"strong_candidate")

    def test_negative_probe_is_not_a_universal_no_trigger_claim(self):
        bad={e["transition_id"]:e for e in self.ledger["local_no_switch_observations"]}
        self.assertEqual(set(bad),{"catalog_transition_0787",
                                  "catalog_transition_0779",
                                  "catalog_transition_0006"})
        self.assertFalse(bad["catalog_transition_0787"]["source_hotspot_contact_observed"])
        self.assertTrue(bad["catalog_transition_0779"]["source_hotspot_contact_observed"])
        for tid,v in bad.items():
            self.assertFalse(v["all_story_states_blocked_proven"])
            self.assertTrue(v["ROM_candidate_still_valid"])
            edge=next(e for e in self.world["transition_edges"] if e["transition_id"]==tid)
            self.assertFalse(edge["runtime_world_entry_batch_negative_trial"]["static_ROM_candidate_invalidated"])
            self.assertIsNone(edge.get("runtime_world_entry_batch_probe"))

    def test_reconstructed_attachment_changes_zero_edges(self):
        result,summary=attach(self.before_attach(),self.ledger)
        self.assertEqual(len(result),len(self.world["transition_candidates"]))
        self.assertEqual(summary["new_graph_edges"],0)
        self.assertEqual(summary["actual_gamepad_matched_destination_pack"],37)
        self.assertEqual(summary["coordinate_resolved_existing_edges_count"],5)
        self.assertEqual(len([e for e in result if e.get("runtime_world_entry_batch_probe")]),37)

    def test_attaching_duplicate_evidence_rejected(self):
        with self.assertRaisesRegex(ValueError,"not backed by exact ROM region|Unverified|Duplicate"):
            attach(self.world["transition_candidates"],self.ledger)

    def test_forged_cpu_opcode_proof_rejected(self):
        l=copy.deepcopy(self.ledger)
        l["entries"][0]["cpu_rom_opcode_PC_observed"]=True
        with self.assertRaisesRegex(ValueError,"World entrance event not backed"):
            attach(self.before_attach(),l)

    def test_forged_destination_xy_rejected(self):
        l=copy.deepcopy(self.ledger)
        l["entries"][0]["settled_arrival_xy"]["x"]+=1
        with self.assertRaises(ValueError):
            attach(self.before_attach(),l)

    def test_incomplete_batch_rejected(self):
        l=copy.deepcopy(self.ledger)
        l["entries"].pop()
        with self.assertRaisesRegex(ValueError,"Expected complete 37"):
            attach(self.before_attach(),l)

    def test_exact_title_registry_25_and_new_23(self):
        r=self.registry
        self.assertEqual(r["kind"],"world_gamepad_entrances_visible_title_pack_scoped")
        self.assertEqual(len(r["all_25_onscreen_title_contexts"]),25)
        self.assertEqual(len(r["new_title_proofs"]),23)
        self.assertEqual(r["existing_two_individual_title_proofs_not_duplicated"],["0x4D","0x91"])
        self.assertEqual(self.world["runtime_location_title_attached_count"],26)
        records={(e["map_config_id"],e["runtime_pack_id_hex"],e["onscreen_title"])
                 for e in r["all_25_onscreen_title_contexts"]}
        mapped={(m["config_id"],c["pack_id_hex"],c["label"])
                for m in self.world["maps"] for c in m.get("runtime_pack_location_contexts",[])}
        # World batch retains its 25 screenshot names; pack96's extra
        # title is from a later independent post-descent modal screenshot.
        self.assertEqual(mapped,records|{("cfg_t09_l098_v2","0x96","音無しの洞窟")})
        self.assertEqual(len(mapped),26)

    def test_onscreen_places_contain_more_than_ten_independent_named_places(self):
        names={e["onscreen_title"] for e in self.registry["all_25_onscreen_title_contexts"]}
        expected={"ほほえみの村","竹取の村","寝太郎の村","音無しの洞窟",
                  "神々の里","びろーんの森","桃葉山","大江山",
                  "鬼が島","鬼の牢獄","氷の塔","虹の洞窟",
                  "伏龍の洞窟","怨みの洞窟","おむすびころりん"}
        self.assertTrue(expected <= names)
        self.assertGreaterEqual(len(expected),10)
        self.assertEqual(len(names),25)

    def test_reused_layout_has_distinct_inn_scene_names(self):
        m=next(m for m in self.world["maps"] if m["config_id"]=="cfg_t04_l018_v2")
        context={p["pack_id_hex"]:p["label"] for p in m["runtime_pack_location_contexts"]}
        self.assertEqual(context,{
          "0x5A":"すずめのお宿1",
          "0x5B":"すずめのお宿2",
          "0x5D":"すずめのお宿5",
          "0x5E":"すずめのお宿6"})
        self.assertNotIn(m.get("display_name"),context.values())

    def test_csv_exact_pack_rows_no_duplicates(self):
        rows=[r for r in self.csv_rows if r["candidate_status"]=="confirmed_onscreen_pack_context"]
        self.assertEqual(len(rows),26)
        self.assertEqual(len({(r["config_id"],r["pack_id_hex"]) for r in rows}),26)
        self.assertTrue(all(r["candidate_label"] for r in rows))

    def test_graph_not_inflated_by_observation_only(self):
        self.assertEqual(len(self.world["maps"]),149)
        self.assertEqual(len(self.world["transition_edges"]),76)
        self.assertEqual(len(self.world["transition_candidates"]),1313)
        self.assertEqual(self.world["transition_catalog_summary"]["bound_edge_count"],76)
        self.assertEqual(self.world["runtime_world_entrance_37_batch_summary"]["new_graph_edges"],0)

if __name__=="__main__":unittest.main()
