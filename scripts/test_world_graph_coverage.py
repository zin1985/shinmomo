#!/usr/bin/env python3
"""Unit tests for non-assertive world graph coverage reporting."""
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from audit_world_graph_coverage import audit


def sample():
    return {
        "maps":[{"config_id":x} for x in ("A","B","C")],
        "transition_candidates":[
            {"source_config_id":"A","destination_config_id":"B"},
            {"source_config_id":None,"destination_config_id":"C"}],
        "transition_edges":[
            {"source_config_id":"A","destination_config_id":"B",
             "confidence":"confirmed","activation_gate":{"evaluation":"unknown"}}]
    }


class WorldGraphAuditTests(unittest.TestCase):
    def test_reports_disconnected_without_inventing_reverse_edges(self):
        d=audit(sample())
        self.assertEqual(d["map_count"],3)
        self.assertEqual(d["maps_with_at_least_one_outgoing"],1)
        self.assertEqual(d["maps_with_no_bound_outgoing"],["B","C"])
        self.assertEqual(d["weak_component_sizes"],[2,1])
        self.assertEqual(d["one_way_pair_count"],1)
        self.assertEqual(d["confirmed_runtime_edge_count"],1)

    def test_true_reverse_clears_one_way_report(self):
        d=sample()
        d["transition_edges"].append({
            "source_config_id":"B","destination_config_id":"A",
            "confidence":"strong_candidate","activation_gate":{"evaluation":"unknown"}})
        out=audit(d)
        self.assertEqual(out["one_way_pair_count"],0)
        self.assertEqual(out["bound_edge_count"],2)

    def test_edge_gate_unknown_not_claimed_traversable(self):
        self.assertEqual(audit(sample())["edges_with_unknown_current_activation"],1)

    def test_integrated_corpus_preserves_edge_gate(self):
        world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
        d=audit(world)
        self.assertEqual(d["bound_edge_count"],len(world["transition_edges"]))
        self.assertEqual(d["native_boundary_context_count"],2)
        self.assertEqual(d["edges_with_unknown_current_activation"],d["bound_edge_count"])
        self.assertEqual(d["map_count"],len(world["maps"]))


if __name__=="__main__":
    unittest.main()
