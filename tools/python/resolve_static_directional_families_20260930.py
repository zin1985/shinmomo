#!/usr/bin/env python3
from pathlib import Path
import csv, json
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
NPC = ROOT / "data/npc_display"
GFX = ROOT / "graphics/static_character_reconstruction"
DIR = GFX / "directional"
DIR.mkdir(parents=True, exist_ok=True)

DIRECT_VISUAL = {
    "0x17": ("confirmed_control_flow_plus_visual", "high", "white cat-like animal; slots visibly right/front/left/back"),
    "0x29": ("confirmed_control_flow_plus_visual", "high", "blue-clad humanoid; slots visibly right/front/left/back"),
    "0x6A": ("confirmed_control_flow_plus_visual", "high", "tall humanoid; slots visibly right/front/left/back"),
    "0x76": ("confirmed_visual_state_order", "high", "group4 wheeled/chest-like actor; slots visibly right/front/left/back"),
    "0x7F": ("confirmed_control_flow_plus_visual", "high", "robot/armored figure; slots visibly right/front/left/back"),
    "0x9E": ("confirmed_control_flow_plus_visual", "high", "humanoid with alternating-size walk frames; four directions visible"),
    "0x9F": ("confirmed_control_flow_plus_visual", "high", "red-clad humanoid with alternating-size walk frames; four directions visible"),
    "0xA3": ("confirmed_control_flow_plus_visual", "high", "blue-clad item-carrying humanoid; four directions visible"),
}

INHERITED = {
    "0x5F": ("0x17", "same G5 family S25..S28 as visually confirmed selector 0x17"),
    "0x60": ("0x6A", "same G5 family S12..S15 as visually confirmed selector 0x6A"),
    "0x83": ("0x7F", "same G7 family S29..S32 as visually confirmed selector 0x7F"),
    "0x9D": ("0x9E", "same G7 family S59..S62 as visually confirmed selector 0x9E"),
}

DIRECTION_INVARIANT = {
    "0x5C": "all four states use the same frame pair 29,30; direction has no visual effect",
    "0x5D": "all four states use the same frame pair 31,32; direction has no visual effect",
}

POSE_SEQUENCE = {
    "0x77": "four consecutive 2-frame states do not form right/front/left/back; visual pose remains essentially same-facing",
    "0x7C": "shares G7 S6..S9 with 0x7D; repeated states do not form four distinct directions",
    "0x7D": "G7 S6..S9 repeats/merges orientations; not a proven four-direction walk family",
    "0x9C": "G7 S51..S54 repeats orientations (120/121,120/122,123/124,123/124); not four-direction walk",
}

def key(value):
    value = str(value)
    return f"0x{int(value, 16):02X}" if value.lower().startswith("0x") else f"0x{int(value):02X}"

def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

fam_path = NPC / "static_actor_animation_family_catalog_20260930.csv"
families = read_csv(fam_path)
family_by_selector = {key(r["selector"]): r for r in families}

# Resolve every formerly unbound four-state family explicitly.
resolution = []
for sel, (status, confidence, note) in DIRECT_VISUAL.items():
    r = family_by_selector[sel]
    r["kind"] = "directional_4x2_confirmed_order"
    r["direction_order"] = "right,down,left,up"
    resolution.append((sel, status, confidence, note, ""))

for sel, (peer, note) in INHERITED.items():
    r = family_by_selector[sel]
    peer_row = family_by_selector[peer]
    same_family = (
        r["sprite_group"] == peer_row["sprite_group"]
        and r["family_state_start"] == peer_row["family_state_start"]
        and [r[f"slot{i}_frames"] for i in range(4)] == [peer_row[f"slot{i}_frames"] for i in range(4)]
    )
    if not same_family:
        raise RuntimeError(f"{sel} no longer shares the expected family with {peer}")
    r["kind"] = "directional_4x2_confirmed_order"
    r["direction_order"] = "right,down,left,up"
    resolution.append((sel, "confirmed_shared_state_family", "high", note, peer))

for sel, note in DIRECTION_INVARIANT.items():
    r = family_by_selector[sel]
    slots = [r[f"slot{i}_frames"] for i in range(4)]
    if len(set(slots)) != 1:
        raise RuntimeError(f"{sel} is no longer visually direction-invariant")
    r["kind"] = "direction_invariant_4state"
    r["direction_order"] = "direction_invariant"
    resolution.append((sel, "direction_invariant_4state", "high", note, ""))

for sel, note in POSE_SEQUENCE.items():
    r = family_by_selector[sel]
    r["kind"] = "four_state_pose_sequence"
    r["direction_order"] = "not_four_direction"
    resolution.append((sel, "four_state_pose_sequence", "medium-high", note, ""))

write_csv(fam_path, families, list(families[0].keys()))

resolution_rows = []
for sel, status, confidence, note, peer in sorted(resolution):
    r = family_by_selector[sel]
    resolution_rows.append({
        "selector_hex": sel,
        "sprite_group": r["sprite_group"],
        "base_state": r["base_state"],
        "family_state_start": r["family_state_start"],
        "family_offset": r["family_offset"],
        "slot0_frames": r["slot0_frames"],
        "slot1_frames": r["slot1_frames"],
        "slot2_frames": r["slot2_frames"],
        "slot3_frames": r["slot3_frames"],
        "resolution_status": status,
        "direction_order": r["direction_order"],
        "confidence": confidence,
        "shared_family_peer": peer,
        "reason": note,
        "provenance": (
            "static_actor_animation_family_catalog_20260930.csv;"
            "static directional candidate atlases;"
            "actor_motion_direction_pattern_table_20260930.csv"
        ),
    })
res_path = NPC / "static_directional_family_resolution_20260930.csv"
write_csv(res_path, resolution_rows, list(resolution_rows[0].keys()))

# Rebuild selector-level directional catalog without pretending non-directional families have named directions.
selectors = read_csv(NPC / "static_character_selector_catalog_20260930.csv")
family_by_sel = {key(r["selector"]): r for r in families}
status_by_sel = {r["selector_hex"]: r for r in resolution_rows}
dir_rows = []
for s in selectors:
    hexsel = f"0x{int(s['selector']):02X}"
    canonical = key(s["duplicate_of"] or hexsel)
    r = family_by_sel.get(canonical)
    if not r:
        continue
    kind = r["kind"]
    confirmed = kind == "directional_4x2_confirmed_order"
    candidate = kind == "four_state_2frame_candidate"
    invariant = kind == "direction_invariant_4state"
    pose = kind == "four_state_pose_sequence"
    frames = [r["slot0_frames"], r["slot1_frames"], r["slot2_frames"], r["slot3_frames"]]
    states = ["", "", "", ""]
    if confirmed:
        n = int(r["family_state_start"])
        states = [str(n+i) for i in range(4)]

    resolution_meta = status_by_sel.get(canonical)
    if resolution_meta:
        binding_status = resolution_meta["resolution_status"]
        confidence = resolution_meta["confidence"]
        evidence_text = resolution_meta["reason"]
        if confirmed:
            evidence_text += f"; animation state family {r['family_state_start']}..{int(r['family_state_start'])+3}; direction_order=right,down,left,up"
    elif confirmed:
        binding_status = "confirmed_state_table_order"
        confidence = "high"
        evidence_text = f"animation state family {r['family_state_start']}..{int(r['family_state_start'])+3}; direction_order={r['direction_order']}; durations={r['duration_pair']}"
    elif candidate:
        binding_status = "four_state_candidate_direction_unbound"
        confidence = "candidate"
        evidence_text = f"four consecutive 2-frame states; direction order intentionally unbound ({r['direction_order']})"
    elif invariant:
        binding_status = "direction_invariant_4state"
        confidence = "high"
        evidence_text = "four states are visually direction-invariant"
    elif pose:
        binding_status = "four_state_pose_sequence"
        confidence = "medium-high"
        evidence_text = "four-state/two-frame structure is not a four-direction walk family"
    else:
        binding_status = kind
        confidence = "high" if kind == "fixed" else "medium"
        evidence_text = f"animation kind={kind}; no 4-direction binding asserted"

    if s["duplicate_of"]:
        evidence_text += f"; selector alias of {s['duplicate_of']}"

    dir_rows.append({
        "selector_hex": hexsel,
        "sprite_group": s["sprite_group"],
        "base_state": s["base_state"],
        "right_state": states[0],
        "right_frames": frames[0] if confirmed else "",
        "front_state": states[1],
        "front_frames": frames[1] if confirmed else "",
        "left_state": states[2],
        "left_frames": frames[2] if confirmed else "",
        "back_state": states[3],
        "back_frames": frames[3] if confirmed else "",
        "walk_animation": (f"right:{frames[0]}|front:{frames[1]}|left:{frames[2]}|back:{frames[3]}" if confirmed else ""),
        "idle_state": "",
        "idle_frames": ("|".join(x.split(",")[0] for x in frames) if confirmed else ""),
        "sprite_alias": s["duplicate_of"],
        "direction_binding_status": binding_status,
        "confidence": confidence,
        "evidence": evidence_text,
        "provenance": (
            "static_character_selector_catalog_20260930.csv;"
            "static_actor_animation_family_catalog_20260930.csv;"
            "static_directional_family_resolution_20260930.csv"
        ),
    })

dir_path = NPC / "static_character_directional_catalog_20260930.csv"
write_csv(dir_path, dir_rows, list(dir_rows[0].keys()))

summary_path = NPC / "static_actor_animation_family_summary_20260930.json"
summary = json.loads(summary_path.read_text(encoding="utf-8"))
summary.update({
    "four_state_2frame_detected": sum(r["kind"] in {
        "directional_4x2_confirmed_order",
        "four_state_2frame_candidate",
        "direction_invariant_4state",
        "four_state_pose_sequence",
    } for r in families),
    "directional_4x2_confirmed": sum(r["kind"] == "directional_4x2_confirmed_order" for r in families),
    "directional_4x2_candidate_unbound": sum(r["kind"] == "four_state_2frame_candidate" for r in families),
    "direction_invariant_4state": sum(r["kind"] == "direction_invariant_4state" for r in families),
    "four_state_pose_sequence": sum(r["kind"] == "four_state_pose_sequence" for r in families),
    "directional_resolution_catalog": str(res_path.relative_to(ROOT)).replace("\\", "/"),
})
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Rebuild compact evidence/final atlases from the stable four-state source atlas.
source_atlas = Image.open(GFX / "static_directional_animation_atlas_20260930.png").convert("RGBA")
four_state_kinds = {
    "directional_4x2_confirmed_order",
    "four_state_2frame_candidate",
    "direction_invariant_4state",
    "four_state_pose_sequence",
}
detected = [r for r in families if r["kind"] in four_state_kinds]
block_index = {key(r["selector"]): i for i, r in enumerate(detected)}
BLOCK_W, BLOCK_H, COLS = 420, 126, 4

def source_block(sel):
    i = block_index[sel]
    x = (i % COLS) * BLOCK_W
    y = (i // COLS) * BLOCK_H
    return source_atlas.crop((x, y, x + BLOCK_W, y + BLOCK_H))

for sel in sorted(set(DIRECT_VISUAL) | set(DIRECTION_INVARIANT) | set(POSE_SEQUENCE)):
    if sel not in block_index:
        continue
    block = source_block(sel).resize((BLOCK_W * 3, BLOCK_H * 3), Image.Resampling.NEAREST)
    block.save(DIR / f"selector_{sel[2:]}_direction_slots_candidate.png")

final_targets = ["0x40","0x24","0x59","0x5A","0x27","0x25","0x5B","0x13"] + sorted(DIRECT_VISUAL)
sel_by_hex = {f"0x{int(s['selector']):02X}": s for s in selectors}
labels = ["RIGHT", "FRONT", "LEFT", "BACK"]
for target in final_targets:
    canonical = key(sel_by_hex[target]["duplicate_of"] or target)
    if canonical not in block_index:
        continue
    fam = family_by_sel[canonical]
    i = block_index[canonical]
    bx = (i % COLS) * BLOCK_W
    by = (i // COLS) * BLOCK_H
    canvas = Image.new("RGBA", (720, 158), (0,0,0,255))
    draw = ImageDraw.Draw(canvas)
    draw.text((8, 6), f"{target} G{sel_by_hex[target]['sprite_group']} base S{sel_by_hex[target]['base_state']}  RIGHT | FRONT | LEFT | BACK", fill="white")
    pairs = [fam[f"slot{x}_frames"] for x in range(4)]
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
    "unique_directional_confirmed": summary["directional_4x2_confirmed"],
    "candidate_unbound": summary["directional_4x2_candidate_unbound"],
    "direction_invariant": summary["direction_invariant_4state"],
    "pose_sequence": summary["four_state_pose_sequence"],
    "selector_directional_confirmed": sum(r["direction_binding_status"].startswith("confirmed") for r in dir_rows),
}, ensure_ascii=False, indent=2))
