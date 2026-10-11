#!/usr/bin/env python3
"""Guard pack-scoped onscreen name and evidence-limited dungeon shortlist."""
from __future__ import annotations
import csv,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from plan_dungeon_family_entries import catalog_targets


class MapIdentityAndDungeonQueueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
        cls.proof=json.loads((ROOT/"data/maps/context/pack4d_runtime_location_title_20261011.json").read_text(encoding="utf-8"))
        with (ROOT/"data/maps/context/map_location_identity_candidates_20260930.csv").open(encoding="utf-8-sig",newline="") as f:
            cls.rows=list(csv.DictReader(f))

    def test_title_exact_runtime_pack(self):
        p=self.proof
        self.assertEqual(p["map_config_id"],"cfg_t04_l006_v2")
        self.assertEqual(p["runtime_pack_id_hex"],"0x4D")
        self.assertEqual(p["onscreen_title"],"桃太郎の生家")
        self.assertEqual(len(p["screenshot_sha256"]),64)
        self.assertFalse(p["screenshot_committed"])
        self.assertFalse(p["applies_to_all_configs_sharing_tileset_layout"])
        self.assertFalse(p["dungeon_or_staircase_evidence"])

    def test_location_csv_has_unique_pack_scoped_evidence(self):
        candidates=[r for r in self.rows if r["candidate_status"]=="confirmed_onscreen_pack_context"]
        self.assertEqual(len(candidates),2)
        by_pack={c["pack_id_hex"]:c for c in candidates}
        self.assertEqual(by_pack["0x4D"]["config_id"],"cfg_t04_l006_v2")
        self.assertEqual(by_pack["0x4D"]["candidate_label"],"桃太郎の生家")
        self.assertEqual(by_pack["0x91"]["config_id"],"cfg_t08_l092_v2")
        self.assertEqual(by_pack["0x91"]["candidate_label"],"おむすびころりん")

    def test_viewer_propagates_title_only_in_exact_context(self):
        maps=self.world["maps"]
        chosen=[m for m in maps if m["config_id"]=="cfg_t04_l006_v2"]
        self.assertEqual(len(chosen),1)
        c=chosen[0].get("runtime_pack_location_contexts")
        self.assertEqual(len(c),1)
        self.assertEqual(c[0]["pack_id_hex"],"0x4D")
        self.assertEqual(c[0]["label"],"桃太郎の生家")
        self.assertEqual(c[0]["scope"],"exact_config_and_runtime_pack_only")
        self.assertEqual(self.world["runtime_location_title_attached_count"],2)
        for m in maps:
            if m["config_id"] not in ("cfg_t04_l006_v2","cfg_t08_l092_v2"):
                self.assertFalse(m.get("runtime_pack_location_contexts"))
        self.assertNotEqual(chosen[0].get("display_name"),"桃太郎の生家")

    def test_viewer_js_title_checks_requested_pack(self):
        code=(ROOT/"viewer/viewer.js").read_text(encoding="utf-8")
        self.assertIn("c.pack_id_hex===pack&&c.identity_status==='confirmed_onscreen_title_runtime_scene'",code)
        self.assertIn("...(m.runtime_pack_location_contexts||[]).map(c=>c.pack_id_hex)",code)
        self.assertNotIn("if(m.config_id==='cfg_t04_l006_v2')return '桃太郎の生家'",code)

    def test_actual_closest_tileset8_cave_family_candidate(self):
        report=catalog_targets(self.world)
        self.assertEqual(report["candidate_count"],1)
        target=report["targets"][0]
        self.assertEqual(target["transition_id"],"catalog_transition_0750")
        self.assertEqual(target["source_region"],{"x":47,"y":199,"width":2,"height":1})
        self.assertEqual(target["destination_config_id"],"cfg_t08_l092_v2")
        self.assertEqual(target["destination_pack"],"0x91")
        self.assertEqual(target["static_opcode_candidate"],"CC:0B7F")
        self.assertEqual(target["distance_lower_bound_world_grid_cells"],44)
        self.assertFalse(target["distance_is_walkable_route"])
        self.assertTrue(target["observed_runtime_transition"])
        self.assertTrue(target["runtime_origin_positioned_by_cheat"])
        self.assertFalse(target["normal_world_route_walkable_proven"])
        self.assertTrue(target["destination_arrival_xy_confirmed"])
        self.assertEqual(target["destination_arrival_xy"],[71,59])

    def test_closest_candidate_does_not_claim_route(self):
        doc=json.loads((ROOT/"data/maps/transitions/world_dungeon_family_targets_20261011.json").read_text(encoding="utf-8"))
        self.assertFalse(doc["accessible_from_origin_current_story_proven"])
        self.assertFalse(doc["recorded_navigation_probe"]["entire_region_or_all_possible_routes_blocked_proven"])
        self.assertTrue(doc["no_edges_promoted"])
        self.assertEqual(doc["recorded_navigation_probe"]["direct_north_result_xy"],[55,233])

    def test_only_tileset8_known_hotspots_selected(self):
        synthetic={"transition_edges":[
            {"transition_id":"valid","source_config_id":"cfg_t01_l001_v1","destination_tileset":8,
             "destination_config_id":"cave","destination_pack":"0x91","source_hotspot_binding":
                {"source_grid_x":10,"source_grid_y":20,"source_width":1,"source_height":1}},
            {"transition_id":"other","source_config_id":"cfg_t01_l001_v1","destination_tileset":4,
             "destination_config_id":"town","source_hotspot_binding":
                {"source_grid_x":11,"source_grid_y":20,"source_width":1,"source_height":1}},
            {"transition_id":"another_map","source_config_id":"somewhere_else","destination_tileset":8,
             "destination_config_id":"cave2","source_hotspot_binding":
                {"source_grid_x":0,"source_grid_y":0,"source_width":1,"source_height":1}},
        ]}
        report=catalog_targets(synthetic)
        self.assertEqual(report["candidate_count"],1)
        self.assertEqual(report["targets"][0]["transition_id"],"valid")

    def test_proven_world_graph_count_unmodified(self):
        self.assertEqual(len(self.world["maps"]),149)
        self.assertEqual(len(self.world["transition_edges"]),57)
        self.assertEqual(len(self.world["transition_candidates"]),1296)
        self.assertEqual(self.world["transition_catalog_summary"]["bound_edge_count"],57)


if __name__=="__main__":unittest.main()
