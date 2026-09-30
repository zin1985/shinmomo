from pathlib import Path
import csv
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "data/npc_display/static_actor_animation_family_catalog_20260930.csv"
ATLAS = ROOT / "graphics/static_character_reconstruction/static_directional_animation_atlas_20260930.png"
OUTDIR = ROOT / "graphics/static_character_reconstruction/directional"
OUTDIR.mkdir(parents=True, exist_ok=True)

BLOCK_W, BLOCK_H, COLS = 420, 126, 4

with CATALOG.open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

directional = [
    r for r in rows
    if r["kind"] in ("directional_4x2_confirmed_order", "four_state_2frame_candidate")
]
atlas = Image.open(ATLAS).convert("RGBA")

def block_for_index(index):
    x = (index % COLS) * BLOCK_W
    y = (index // COLS) * BLOCK_H
    return atlas.crop((x, y, x + BLOCK_W, y + BLOCK_H))

for group in (5, 7):
    selected = [(i, r) for i, r in enumerate(directional) if int(r["sprite_group"]) == group]
    if not selected:
        continue
    scale = 2
    gap = 8
    title_h = 36
    out = Image.new(
        "RGBA",
        (BLOCK_W * scale, title_h + len(selected) * (BLOCK_H * scale + gap)),
        (0, 0, 0, 255),
    )
    draw = ImageDraw.Draw(out)
    draw.text((8, 8), f"group {group} four-state candidate families; slots are NOT direction-bound", fill="white")
    y = title_h
    for index, row in selected:
        block = block_for_index(index).resize((BLOCK_W * scale, BLOCK_H * scale), Image.Resampling.NEAREST)
        out.alpha_composite(block, (0, y))
        y += BLOCK_H * scale + gap
    out.save(OUTDIR / f"group{group}_direction_candidates_20260930.png")

for index, row in enumerate(directional):
    if int(row["sprite_group"]) not in (5, 7):
        continue
    sel = row["selector"].replace("0x", "")
    block = block_for_index(index).resize((BLOCK_W * 3, BLOCK_H * 3), Image.Resampling.NEAREST)
    block.save(OUTDIR / f"selector_{sel}_direction_slots_candidate.png")

print("generated", sum(1 for r in directional if int(r["sprite_group"]) in (5, 7)), "candidate selector atlases")
