from pathlib import Path
import csv, json
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
NPC = ROOT / "data/npc_display"
GFX = ROOT / "graphics/static_character_reconstruction"
DIR = GFX / "directional"
DIR.mkdir(parents=True, exist_ok=True)

PROMOTIONS = {
    "0x17": ("white cat-like animal; slots visibly right/front/left/back", "high"),
    "0x6A": ("tall humanoid; slots visibly right/front/left/back", "high"),
    "0x29": ("blue-clad humanoid; slots visibly right/front/left/back", "high"),
    "0x7F": ("robot/armored figure; slots visibly right/front/left/back", "high"),
    "0x9E": ("humanoid with alternating-size walk frames; four directions visible", "high"),
    "0x9F": ("red-clad humanoid with alternating-size walk frames; four directions visible", "high"),
    "0xA3": ("blue-clad item-carrying humanoid; four directions visible", "high"),
}
UNRESOLVED = {
    "0x5F": "selector resource does not render the candidate family",
    "0x60": "candidate frames are incomplete/magenta with this selector resource",
    "0x7C": "selector resource does not render the candidate family",
    "0x7D": "candidate frames remain same-side/repeated in visual reconstruction",
    "0x83": "selector resource does not render the candidate family",
    "0x9C": "candidate frames repeat orientations; not a proven four-direction family",
    "0x9D": "selector resource does not render the candidate family",
}

def selector_key(value):
    return f"0x{int(value, 16):02X}"

def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)

fam_path = NPC / "static_actor_animation_family_catalog_20260930.csv"
families = read_csv(fam_path)
original_kind = {r["selector"]: r["kind"] for r in families}
evidence = []
for r in families:
    sel = selector_key(r["selector"])
    if r["sprite_group"] not in ("5", "7") or sel not in (PROMOTIONS | UNRESOLVED):
        continue
    promoted = sel in PROMOTIONS
    note = PROMOTIONS[sel][0] if promoted else UNRESOLVED.get(sel, "direction semantics unresolved")
    evidence.append({
        "selector_hex": sel, "sprite_group": r["sprite_group"], "base_state": r["base_state"],
        "family_state_start": r["family_state_start"], "family_offset": r["family_offset"],
        "slot0_frames": r["slot0_frames"], "slot1_frames": r["slot1_frames"],
        "slot2_frames": r["slot2_frames"], "slot3_frames": r["slot3_frames"],
        "direction_order": "right,down/front,left,up/back" if promoted else "unbound",
        "status": "confirmed_control_flow_plus_visual" if promoted else "candidate_unresolved",
        "confidence": PROMOTIONS[sel][1] if promoted else "candidate",
        "visual_observation": note,
        "control_flow_evidence": (
            "C1:9090 maps motion pattern 1..4 to animation offsets 0..3; "
            "81:81D3/D4 deltas prove 1=right,2=down,3=left,4=up"
        ),
        "provenance": (
            "ROM C1:9090-90B9; ROM 81:81D3-81DC; "
            "reports/text_decoder/shinmomo_goal13_15F3_motion_pattern_analysis_20260426.md; "
            "graphics/static_character_reconstruction/static_directional_animation_atlas_20260930.png"
        ),
    })
    if promoted:
        r["kind"] = "directional_4x2_confirmed_order"
        r["direction_order"] = "right,down,left,up"

ev_fields = list(evidence[0].keys())
write_csv(NPC / "group5_group7_directional_family_evidence_20260930.csv", evidence, ev_fields)
write_csv(fam_path, families, list(families[0].keys()))

summary_path = NPC / "static_actor_animation_family_summary_20260930.json"
summary = json.loads(summary_path.read_text(encoding="utf-8"))
detected = sum(r["kind"] in ("directional_4x2_confirmed_order", "four_state_2frame_candidate") for r in families)
confirmed_unique = sum(r["kind"] == "directional_4x2_confirmed_order" for r in families)
candidate_unique = sum(r["kind"] == "four_state_2frame_candidate" for r in families)
summary["directional_4x2_detected"] = detected
summary["directional_4x2_confirmed"] = confirmed_unique
summary["directional_4x2_candidate_unbound"] = candidate_unique
summary["group5_group7_newly_confirmed"] = len(PROMOTIONS)
summary["group5_group7_evidence"] = "data/npc_display/group5_group7_directional_family_evidence_20260930.csv"
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
selectors = read_csv(NPC / "static_character_selector_catalog_20260930.csv")
family_by_sel = {selector_key(r["selector"]): r for r in families}
dir_rows = []
for s in selectors:
    hexsel = f"0x{int(s['selector']):02X}"
    canonical = selector_key(s["duplicate_of"] or hexsel)
    r = family_by_sel.get(canonical)
    if not r:
        continue
    confirmed = r["kind"] == "directional_4x2_confirmed_order"
    candidate = r["kind"] == "four_state_2frame_candidate"
    frames = [r["slot0_frames"], r["slot1_frames"], r["slot2_frames"], r["slot3_frames"]]
    states = ["", "", "", ""]
    if confirmed:
        n = int(r["family_state_start"])
        states = [str(n+i) for i in range(4)]
    promoted = canonical in PROMOTIONS
    evidence_text = (
        f"animation state family {r['family_state_start']}..{int(r['family_state_start'])+3}; "
        f"direction_order={r['direction_order']}; durations={r['duration_pair']}"
        if confirmed else
        (f"four consecutive 2-frame states; direction order intentionally unbound ({r['direction_order']})"
         if candidate else f"animation kind={r['kind']}; no 4-direction binding asserted")
    )
    if promoted:
        evidence_text += "; control-flow mapping C1:9090 + movement deltas 81:81D3/D4 + visual atlas"
    if s["duplicate_of"]:
        evidence_text += f"; selector alias of {s['duplicate_of']}"
    dir_rows.append({
        "selector_hex": hexsel, "sprite_group": s["sprite_group"], "base_state": s["base_state"],
        "right_state": states[0], "right_frames": frames[0] if (confirmed or candidate) else "",
        "front_state": states[1], "front_frames": frames[1] if (confirmed or candidate) else "",
        "left_state": states[2], "left_frames": frames[2] if (confirmed or candidate) else "",
        "back_state": states[3], "back_frames": frames[3] if (confirmed or candidate) else "",
        "walk_animation": (f"right:{frames[0]}|front:{frames[1]}|left:{frames[2]}|back:{frames[3]}" if confirmed else ""),
        "idle_state": "", "idle_frames": ("|".join(x.split(",")[0] for x in frames) if confirmed else ""),
        "sprite_alias": s["duplicate_of"],
        "direction_binding_status": ("confirmed_control_flow_plus_visual" if promoted else
                                     "confirmed_state_table_order" if confirmed else
                                     "four_state_candidate_direction_unbound" if candidate else r["kind"]),
        "confidence": "high" if confirmed or r["kind"] == "fixed" else ("candidate" if candidate else "medium"),
        "evidence": evidence_text,
        "provenance": ("static_character_selector_catalog_20260930.csv;"
                       "static_actor_animation_family_catalog_20260930.csv;"
                       "shinmomo_B2C1_animation_state_scripts_20260425.csv;"
                       "group5_group7_directional_family_evidence_20260930.csv"),
    })
dir_fields = list(dir_rows[0].keys())
write_csv(NPC / "static_character_directional_catalog_20260930.csv", dir_rows, dir_fields)

pattern_rows = [
    {"motion_pattern": 0, "dx": 0, "dy": 0, "animation_offset": "", "direction": "idle/special"},
    {"motion_pattern": 1, "dx": 1, "dy": 0, "animation_offset": 0, "direction": "right"},
    {"motion_pattern": 2, "dx": 0, "dy": 1, "animation_offset": 1, "direction": "down/front"},
    {"motion_pattern": 3, "dx": -1, "dy": 0, "animation_offset": 2, "direction": "left"},
    {"motion_pattern": 4, "dx": 0, "dy": -1, "animation_offset": 3, "direction": "up/back"},
]
for r in pattern_rows:
    r["evidence"] = "81:81D3-81DC movement delta table; C1:9090 AND #07, DEC A, then add to animation base"
    r["confidence"] = "high"
write_csv(NPC / "actor_motion_direction_pattern_table_20260930.csv", pattern_rows, list(pattern_rows[0].keys()))
# Build compact finalized RIGHT | FRONT | LEFT | BACK atlases from the existing source atlas.
source_atlas = Image.open(GFX / "static_directional_animation_atlas_20260930.png").convert("RGBA")
detected_before = [r for r in families if original_kind[r["selector"]] in ("directional_4x2_confirmed_order", "four_state_2frame_candidate")]
block_index = {selector_key(r["selector"]): i for i, r in enumerate(detected_before)}
BLOCK_W, BLOCK_H, COLS = 420, 126, 4
targets = ["0x40","0x24","0x59","0x5A","0x27","0x25","0x5B","0x13"] + list(PROMOTIONS)
sel_by_hex = {f"0x{int(s['selector']):02X}": s for s in selectors}
labels = ["RIGHT", "FRONT", "LEFT", "BACK"]

for target in targets:
    s = sel_by_hex[target]
    canonical = selector_key(s["duplicate_of"] or target)
    idx = block_index[canonical]
    bx = (idx % COLS) * BLOCK_W
    by = (idx // COLS) * BLOCK_H
    fam = family_by_sel[canonical]
    canvas = Image.new("RGBA", (720, 158), (0,0,0,255))
    draw = ImageDraw.Draw(canvas)
    draw.text((8, 6), f"{target} G{s['sprite_group']} base S{s['base_state']}  RIGHT | FRONT | LEFT | BACK", fill="white")
    if s["duplicate_of"]:
        draw.text((8, 20), f"alias {s['duplicate_of']}", fill=(180,180,180,255))
    pairs = [fam["slot0_frames"], fam["slot1_frames"], fam["slot2_frames"], fam["slot3_frames"]]
    for di in range(4):
        x0 = di * 180
        draw.text((x0+8, 38), labels[di], fill="white")
        for fi in range(2):
            sx = bx + 56 + (di*2+fi)*44
            thumb = source_atlas.crop((sx, by+30, sx+40, by+70)).resize((80,80), Image.Resampling.NEAREST)
            canvas.alpha_composite(thumb, (x0+5+fi*86, 55))
        draw.text((x0+8, 138), "F" + " / F".join(pairs[di].split(",")), fill=(180,180,180,255))
    canvas.save(DIR / f"selector_{target[2:]}_directions.png")

print(json.dumps({
    "unique_confirmed": confirmed_unique,
    "candidate_unbound": candidate_unique,
    "selector_confirmed": sum(r["direction_binding_status"].startswith("confirmed") for r in dir_rows),
    "final_atlases": len(targets),
    "promoted": list(PROMOTIONS),
}, ensure_ascii=False))
