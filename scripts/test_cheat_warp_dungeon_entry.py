#!/usr/bin/env python3
"""Fail-closed tests: Hien-enabled cheat travel is NOT normal walkability."""
from __future__ import annotations
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
sys.path.insert(0,str(ROOT/"scripts"))
from test_vm_frame_series_replays import make_series
from verify_cheat_warp_dungeon_entry import verify
from apply_cheat_positioned_dungeon_proof import attach,TARGET_ID


def fixtures():
    a=make_series(663062,30,76,(47,200),145,(47,199),"Up")
    b=make_series(663092,120,145,(47,199),145,(71,59),"")
    for doc in (a,b):
        doc["schema_version"]=2
        for row in (doc["before"],*doc["samples"],doc["after"]):
            row.update(w0306=80,w126e=76,w12b4=76,w12b5=3)
    for row in a["samples"]:
        if row["frame"]>=663064:row["w157d"]=199
        if row["frame"]>=663079:row["w0305"]=145
    a["after"]=dict(a["samples"][-1],label="after")
    for row in b["samples"]:
        if row["frame"]>=663116:
            row["w126e"]=145;row["w12b4"]=145
        if row["frame"]>=663203:
            row["w1573"]=71;row["w157d"]=59
    b["after"]=dict(b["samples"][-1],label="after")
    world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
    edge=next(e for e in world["transition_edges"] if e["transition_id"]==TARGET_ID)
    return a,b,edge


class CheatPositionedDungeonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof=json.loads((ROOT/"data/maps/transitions/omusubi_kororin_cheat_entry_verified_20261011.json").read_text(encoding="utf-8"))
        cls.world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))

    def test_positive_synthetic_enter_dungeon(self):
        a,b,e=fixtures()
        report=verify(a,b,e)
        self.assertEqual(report["map_pack_switch_frame"],663079)
        self.assertEqual(report["selector_convergence_frame"],663116)
        self.assertEqual(report["first_settled_coordinate_frame"],663203)
        self.assertEqual(report["destination_xy"],{"x":71,"y":59})
        self.assertEqual(report["screenshot_onscreen_title"],"おむすびころりん")
        self.assertFalse(report["source_normal_world_walk_route_proven"])
        self.assertFalse(report["hien_spell_actually_cast_for_this_transition"])

    def test_missing_source_contact_rejected(self):
        a,b,e=fixtures()
        for s in a["samples"]:
            if s["w0305"]==76:s["w157d"]=200
        with self.assertRaisesRegex(ValueError,"source hotspot"):
            verify(a,b,e)

    def test_forged_runtime_destination_rejected(self):
        a,b,e=fixtures()
        for s in b["samples"]:
            if s["w1573"]==71:s["w1573"]=72
        b["after"]["w1573"]=72
        with self.assertRaisesRegex(ValueError,"stable dungeon landing"):
            verify(a,b,e)

    def test_wrong_spatial_source_rejected(self):
        a,b,e=fixtures()
        a["before"]["w1573"]=48
        with self.assertRaisesRegex(ValueError,"Cheat start"):
            verify(a,b,e)

    def test_bad_input_device_rejected(self):
        a,b,e=fixtures()
        a["input_device"]="desktop_keyboard"
        with self.assertRaisesRegex(ValueError,"isolated SNES"):
            verify(a,b,e)

    def test_missing_selector_convergence_rejected(self):
        a,b,e=fixtures()
        for s in b["samples"]:
            s["w126e"]=76;s["w12b4"]=76
        b["after"]["w126e"]=76;b["after"]["w12b4"]=76
        with self.assertRaisesRegex(ValueError,"selectors"):
            verify(a,b,e)

    def test_production_proof_attaches_without_confidence_promotion(self):
        base=copy.deepcopy(self.world["transition_candidates"])
        for e in base:
            if e["transition_id"]==TARGET_ID:
                e["destination_x"]=None;e["destination_y"]=None
                e.pop("destination_coordinate_origin",None)
                e.pop("runtime_cheat_entry_proof",None)
        out,summary=attach(base,self.proof)
        self.assertEqual(len(out),len(base))
        self.assertEqual(summary["new_graph_edges"],0)
        e=next(e for e in out if e["transition_id"]==TARGET_ID)
        self.assertEqual((e["destination_x"],e["destination_y"]),(71,59))
        self.assertEqual(e["confidence"],"strong_candidate")
        self.assertIs(e["runtime_cheat_entry_proof"]["normal_walkable_world_route_proven"],False)
        self.assertIs(e["runtime_cheat_entry_proof"]["exact_rom_opcode_execution_proven"],False)

    def test_second_injection_rejected(self):
        with self.assertRaisesRegex(ValueError,"has earlier proof"):
            attach(self.world["transition_candidates"],self.proof)

    def test_false_story_access_assertion_rejected(self):
        fake=copy.deepcopy(self.proof)
        fake["all_story_phases_accessible_proven"]=True
        base=copy.deepcopy(self.world["transition_candidates"])
        for e in base:
            if e["transition_id"]==TARGET_ID:
                e["destination_x"]=None;e["destination_y"]=None
                e.pop("runtime_cheat_entry_proof",None)
        with self.assertRaisesRegex(ValueError,"lacks required boundaries"):
            attach(base,fake)

    def test_real_data_has_scene_scoped_title_and_unknown_gate(self):
        edge=next(e for e in self.world["transition_edges"] if e["transition_id"]==TARGET_ID)
        self.assertFalse(edge["activation_gate"]["navigable_now"])
        self.assertEqual(edge["activation_gate"]["evaluation"],"unknown")
        self.assertEqual(edge["runtime_cheat_entry_proof"]["on_screen_destination_title"],"おむすびころりん")
        self.assertEqual(self.world["runtime_cheat_dungeon_entry_summary"]["attached_count"],1)
        self.assertEqual(len(self.world["transition_edges"]),77)
        self.assertEqual(len(self.world["maps"]),149)
        self.assertEqual(self.world["runtime_location_title_attached_count"],26)
        dest=next(m for m in self.world["maps"] if m["config_id"]=="cfg_t08_l092_v2")
        self.assertEqual(dest["runtime_pack_location_contexts"][0]["pack_id_hex"],"0x91")
        self.assertFalse(dest["runtime_pack_location_contexts"][0]["story_phase_flag_binding_proven"])

    def test_title_digest_and_cheat_metadata(self):
        self.assertEqual(len(self.proof["screenshot_sha256"]),64)
        self.assertEqual(self.proof["rom_static_vm_candidate_address"],"CC:0B7F")
        self.assertEqual(self.proof["source_cheat_wram_addresses"],["0x1573","0x157D"])
        self.assertTrue(self.proof["runtime_event_triggered_by_gamepad"])
        self.assertFalse(self.proof["new_graph_edges"])

if __name__=="__main__":unittest.main()
