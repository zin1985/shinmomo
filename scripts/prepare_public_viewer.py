from __future__ import annotations
import hashlib, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "viewer"
OUT = ROOT / "dist" / "viewer-site"

def copy_asset(rel: str, dest_rel: str) -> str | None:
    src = (SRC / rel).resolve()
    if not src.is_file():
        return None
    dst = OUT / dest_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return "./" + dest_rel.replace("\\", "/")

def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(SRC, OUT)
    world_path = OUT / "data" / "world.json"
    world = json.loads(world_path.read_text(encoding="utf-8-sig"))

    raw_js = (OUT / "viewer.js").read_bytes()
    raw_world = world_path.read_bytes()
    bundle_version = hashlib.sha256(raw_js + raw_world).hexdigest()[:12]

    missing_maps = []
    for m in world.get("maps", []):
        rel = m.get("canonical_image")
        if not rel:
            continue
        target = f"assets/maps/{m['config_id']}.png"
        public = copy_asset(rel, target)
        if public:
            m["canonical_image"] = public + "?v=" + bundle_version
        else:
            missing_maps.append({"config_id": m.get("config_id"), "path": rel})
            m["canonical_image"] = None

    seen = {}
    missing_sprites = []
    for e in world.get("entities", []):
        rel = e.get("sprite_asset")
        if not rel:
            continue
        if rel in seen:
            e["sprite_asset"] = seen[rel]
            continue
        src = (SRC / rel).resolve()
        suffix = src.suffix or ".png"
        target = f"assets/sprites/{len(seen):04d}{suffix}"
        public = copy_asset(rel, target)
        if public:
            public = public + "?v=" + bundle_version
            seen[rel] = public
            e["sprite_asset"] = public
        else:
            missing_sprites.append(rel)
            e["sprite_asset"] = None

    world_path.write_text(json.dumps(world, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    js_path = OUT / "viewer.js"
    js = js_path.read_text(encoding="utf-8-sig")
    for name in ("world.json", "actor_semantics.json", "actor_behavior.json"):
        js = js.replace(f"./data/{name}", f"./data/{name}?v={bundle_version}")
    hashed_js = f"viewer.{bundle_version}.js"
    (OUT / hashed_js).write_text(js, encoding="utf-8")
    js_path.unlink()

    index_path = OUT / "index.html"
    index = index_path.read_text(encoding="utf-8-sig")
    index = index.replace('src="viewer.js"', f'src="{hashed_js}"')
    index_path.write_text(index, encoding="utf-8")

    manifest = {
        "kind": "shinmomo_public_viewer_bundle",
        "bundle_version": bundle_version,
        "viewer_script": hashed_js,
        "map_count": len(world.get("maps", [])),
        "map_images_copied": sum(1 for m in world.get("maps", []) if m.get("canonical_image")),
        "sprite_assets_copied": len(seen),
        "missing_map_images": missing_maps,
        "missing_sprite_assets": sorted(set(missing_sprites)),
    }
    (OUT / "bundle-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))

if __name__ == "__main__":
    main()
