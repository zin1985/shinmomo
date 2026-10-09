#!/usr/bin/env python3
"""Fail-closed native-bounds destination overlay tests."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from crosslink_destination_bounds_for_viewer import join_destination_bounds, read_csv


def candidate(addr="CC:1234",pack="0x60",x="37",y="56",cfg=""):
    return {"trigger_addr":addr,"destination_pack":pack,"destination_x":x,
            "destination_y":y,"destination_config_id":cfg}


def bounds(addr="CC:1234",pack="0x60",x="37",y="56",cfg="cfg_t04_l035_v2",count="1"):
    return {"trigger_addr":addr,"destination_pack":pack,"destination_x":x,
            "destination_y":y,"resolved_config_id":cfg,"candidate_count":count,
            "evidence":"verified native bounds", "provenance":"independent analyzer"}


class NativeBoundsOverlayTests(unittest.TestCase):
    def test_exact_unique_binding_and_input_immutability(self):
        entry=candidate()
        matched,audit=join_destination_bounds([entry],[bounds()])
        self.assertEqual(matched[0]["resolved_config_id"],"cfg_t04_l035_v2")
        self.assertEqual(audit[0]["status"],"new_destination_binding")
        self.assertEqual(entry["destination_config_id"],"")

    def test_rejects_ambiguity_and_nonunique_bounds(self):
        self.assertEqual(len(join_destination_bounds([candidate(),candidate()],[bounds()])[0]),0)
        self.assertEqual(len(join_destination_bounds([candidate()],[bounds(count="2")])[0]),0)
        self.assertEqual(len(join_destination_bounds([candidate()],[bounds(addr="CC:9999")])[0]),0)

    def test_rejects_conflicting_pack_coordinate_or_existing_config(self):
        for field,invalid in [("destination_pack","0x61"),("destination_x","38"),("destination_y","57")]:
            with self.subTest(field=field):
                b=bounds()
                b[field]=invalid
                accepted,audit=join_destination_bounds([candidate()],[b])
                self.assertFalse(accepted)
                self.assertEqual(audit[0]["status"],"pack_or_arrival_mismatch")
        accepted,audit=join_destination_bounds([candidate(cfg="cfg_other")],[bounds()])
        self.assertFalse(accepted)
        self.assertEqual(audit[0]["status"],"existing_config_conflict")

    def test_does_not_infer_arrival_or_config(self):
        for c in [candidate(x=""),candidate(y="")]:
            accepted,_=join_destination_bounds([c],[bounds()])
            self.assertFalse(accepted)

    def test_duplicate_resolution_is_not_adopted(self):
        accepted,audit=join_destination_bounds([candidate()],[bounds(),bounds()])
        self.assertFalse(accepted)
        self.assertEqual(audit[0]["status"],"duplicate_resolution")

    def test_current_corpus_only_unique_conflict_free_matches(self):
        candidates=read_csv(ROOT/"data/maps/transitions/map_transition_candidates.csv")
        resolutions=read_csv(ROOT/"data/maps/transitions/destination_config_bounds_resolution.csv")
        accepted,audit=join_destination_bounds(candidates,resolutions)
        self.assertEqual(len(accepted),len(set(accepted)))
        self.assertEqual(len(accepted),len([a for a in audit if a["status"]=="new_destination_binding"]))
        self.assertFalse([a for a in audit if a["status"] not in ("new_destination_binding","already_bound_consistent")])


if __name__=="__main__":
    unittest.main()
