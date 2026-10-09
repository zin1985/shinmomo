#!/usr/bin/env python3
"""Regression tests for context-safe saved-return edges and conservative event gate."""
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from build_native_saved_return_context import rows, match_native_boundaries, edge_activation_gate


def edge(src="cfg_a",dest="cfg_b",confidence="confirmed",type="runtime_observed_map_transition"):
    return {"transition_id":"catalog_transition_0000","source_config_id":src,
            "destination_config_id":dest,"trigger_type":type,"confidence":confidence,
            "destination_x":None,"destination_y":None}


def hotspot(src="cfg_a",dest="cfg_b",x="3",y="4",wid="1",confidence="confirmed_runtime_and_static"):
    return {"hotspot_id":"hotspot_native_example","source_config_id":src,
            "destination_config_id":dest,"trigger_addr":"C1:8955",
            "trigger_type":"native_out_of_bounds_saved_state_restore",
            "source_grid_x":"8","source_grid_y":"12","source_width":wid,"source_height":"1",
            "hotspot_type":"native_boundary_saved_return_exit",
            "destination_x":x,"destination_y":y,"confidence":confidence,
            "evidence":"runtime proof", "provenance":"data/native"}


def origin(src="cfg_a",dest="cfg_b"):
    return {"origin_hotspot_id":"hotspot_CC_FOO",
            "entered_destination_config_id":src,"saved_return_config_id":dest,
            "saved_return_x_min":"3","saved_return_y_min":"4",
            "saved_return_x_max":"3","saved_return_y_max":"4",
            "reverse_runtime_status":"confirmed_reverse_edge_and_return_coordinate",
            "provenance":"data/restore"}


class NativeReturnTests(unittest.TestCase):
    def test_attaches_same_handler_using_context(self):
        e1=edge()
        e2=edge("cfg_c","cfg_d")
        e2["transition_id"]="catalog_transition_0001"
        h1=hotspot()
        h2=hotspot("cfg_c","cfg_d")
        h2["hotspot_id"]="hotspot_native_other"
        rows_out,audit=match_native_boundaries([e1,e2],[h1,h2],[origin(),origin("cfg_c","cfg_d")])
        self.assertEqual(audit["attached_count"],2)
        self.assertEqual(rows_out[0]["native_boundary_context"]["saved_return_target_config_id"],"cfg_b")
        self.assertEqual(rows_out[1]["native_boundary_context"]["saved_return_target_config_id"],"cfg_d")
        self.assertEqual(rows_out[0]["confidence"],"confirmed")
        self.assertNotIn("native_boundary_context",e1)

    def test_ambiguous_context_fails_closed(self):
        src=edge()
        duplicates=[src,dict(src,transition_id="duplicate")]
        _,audit=match_native_boundaries(duplicates,[hotspot()],[origin()])
        self.assertEqual(audit["attached_count"],0)
        self.assertEqual(audit["rejected"][0]["reason"],"missing_or_ambiguous_source_destination_edge")

    def test_conflicting_return_coordinate_rejected(self):
        out,audit=match_native_boundaries([edge()],[hotspot(x="50")],[origin()])
        self.assertEqual(audit["attached_count"],0)
        self.assertNotIn("native_boundary_context",out[0])

    def test_candidate_corridor_not_promoted(self):
        row=hotspot(wid="3",confidence="strong_candidate")
        matched,audit=match_native_boundaries([edge()],[row],[origin()])
        self.assertEqual(audit["attached_count"],1)
        ctx=matched[0]["native_boundary_context"]
        self.assertEqual(ctx["source_region"]["evidence_status"],"candidate_corridor_not_all_cells_verified")
        self.assertEqual(ctx["current_state_evaluation"],"unknown_without_saved_state_and_position")

    def test_gate_does_not_claim_executability(self):
        cases=[edge(),edge(confidence="strong_candidate")]
        cases.append(dict(edge(),source_hotspot_binding={"hotspot_id":"h"}))
        for x in cases:
            with self.subTest(x=x):
                gate=edge_activation_gate(x)
                self.assertEqual(gate["evaluation"],"unknown")
                self.assertIs(gate["navigable_now"],False)

    def test_corpus_context_join(self):
        from crosslink_transition_sources_from_hotspots import rows as read_csv
        from crosslink_destination_bounds_for_viewer import join_destination_bounds
        import json
        world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
        native_hotspots=rows(ROOT/"data/maps/transitions/source_transition_hotspots.csv")
        origins=rows(ROOT/"data/maps/transitions/source_saved_return_origins.csv")
        matched,audit=match_native_boundaries(world["transition_edges"],native_hotspots,origins)
        self.assertEqual(audit["attached_count"],2,audit)
        self.assertFalse(audit["rejected"],audit)
        c={e["source_config_id"]:e for e in matched if e.get("native_boundary_context")}
        self.assertEqual(c["cfg_t04_l008_v2"]["native_boundary_context"]["source_region"]["evidence_status"],"confirmed_exact_cell")
        self.assertEqual(c["cfg_t07_l015_v2"]["native_boundary_context"]["source_region"]["evidence_status"],"candidate_corridor_not_all_cells_verified")


if __name__=="__main__":
    unittest.main()
