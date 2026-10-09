#!/usr/bin/env python3
"""Regression tests for evidence-backed source-map bindings."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/python"))
from crosslink_transition_sources_from_hotspots import crosslink, rows, summarize


def candidate(address="CC:1234", source="", destination="cfg_dest", x="4", y="6"):
    return {
        "trigger_addr": address, "source_config_id": source,
        "destination_config_id": destination, "destination_x": x,
        "destination_y": y, "event_record": "",
    }


def hotspot(address="CC:1234", source="cfg_source", destination="cfg_dest", x="4", y="6"):
    return {
        "hotspot_id": "example", "trigger_addr": address,
        "source_config_id": source, "destination_config_id": destination,
        "destination_x": x, "destination_y": y,
        "source_grid_x": "1", "source_grid_y": "2",
        "source_width": "1", "source_height": "1",
        "hotspot_type": "vm_opcode_0x69_exact_point",
        "confidence": "strong_candidate", "event_record": "",
    }


class CrosslinkTests(unittest.TestCase):
    def test_exact_unique_infers_source_only_and_retains_confidence(self):
        source = candidate()
        result = crosslink([source], [hotspot()])[0]
        self.assertEqual(result["binding_status"], "new_source_binding")
        self.assertEqual(result["transition_row_index"], "0")
        self.assertEqual(result["source_config_id"], "cfg_source")
        self.assertEqual(result["hotspot_confidence"], "strong_candidate")
        self.assertEqual(source["source_config_id"], "")  # never mutate canonical CSV

    def test_existing_consistent_is_not_double_promoted(self):
        outcome = crosslink([candidate(source="cfg_source")], [hotspot()])[0]
        self.assertEqual(outcome["binding_status"], "already_bound_consistent")

    def test_destination_conflict_is_rejected(self):
        for field in ("destination_config_id", "destination_x", "destination_y"):
            with self.subTest(field=field):
                src = hotspot()
                src[field] = "different"
                outcome = crosslink([candidate()], [src])[0]
                self.assertTrue(outcome["binding_status"].startswith("conflict:"))

    def test_source_conflict_is_rejected(self):
        result = crosslink([candidate(source="cfg_wrong")], [hotspot()])[0]
        self.assertTrue(result["binding_status"].startswith("conflict:"))

    def test_missing_or_ambiguous_trigger_not_bound(self):
        self.assertEqual(crosslink([candidate()], [hotspot("CC:FFFF")])[0]["binding_status"],
                         "unmatched_trigger_address")
        self.assertEqual(crosslink([candidate(), candidate()], [hotspot()])[0]["binding_status"],
                         "ambiguous_trigger_address")

    def test_multi_hotspot_same_candidate_is_not_silently_selected(self):
        a, b = hotspot(), hotspot()
        b["hotspot_id"] = "other"
        result = crosslink([candidate()], [a, b])
        self.assertEqual([r["binding_status"] for r in result], ["ambiguous_multiple_hotspots"] * 2)

    def test_unknown_destination_remains_unknown(self):
        candidate_row = candidate(destination="", x="", y="")
        result = crosslink([candidate_row], [hotspot(destination="", x="", y="")])
        report = summarize(result, [candidate_row])
        self.assertEqual(report["new_source_binding_count"], 1)
        self.assertEqual(report["new_navigable_edge_count"], 0)
        self.assertEqual(report["new_source_without_destination_count"], 1)

    def test_current_corpus_has_no_source_conflicts(self):
        candidates = rows(ROOT / "data/maps/transitions/map_transition_candidates.csv")
        hotspots = rows(ROOT / "data/maps/transitions/source_transition_hotspots.csv")
        result = crosslink(candidates, hotspots)
        for item in result:
            self.assertFalse(item["binding_status"].startswith("conflict:"), item)
        unique_index = [r["transition_row_index"] for r in result if r["binding_status"] == "new_source_binding"]
        self.assertEqual(len(unique_index), len(set(unique_index)))


if __name__ == "__main__":
    unittest.main()
