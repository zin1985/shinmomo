#!/usr/bin/env python3
"""Join confirmed map-selector occurrences to same-index dialogue source families."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


def cfg_id(row: dict) -> str:
    return (
        f"cfg_t{int(row['primary_tileset_id']):02d}"
        f"_l{int(row['primary_layout_id']):03d}"
        f"_v{int(row['map_variant'])}"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    args = ap.parse_args()
    root = args.repo_root

    def load(rel: str) -> list[dict]:
        with (root / rel).open(encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    primary = load("data/maps/selectors/primary_map_selector_catalog.csv")
    crosswalk = load("data/dialogue/source_family_script_pack_crosswalk.csv")
    usage = load("data/dialogue/source_pair_usage_catalog.csv")
    semantic = load("data/dialogue/historical_dialogue_semantic_context.csv")

    family_meta = {
        int(r["family_id_dec"]): r
        for r in crosswalk
        if r["relation_status"] == "confirmed_index_key"
    }
    usage_by_family: dict[int, list[dict]] = defaultdict(list)
    for row in usage:
        usage_by_family[int(row["family_id"])].append(row)

    semantic_by_family: dict[int, list[dict]] = defaultdict(list)
    for row in semantic:
        semantic_by_family[int(row["family_hex"], 16)].append(row)

    out = []
    for row in primary:
        pack = int(row["pack_id_dec"])
        meta = family_meta.get(pack)
        if meta is None:
            raise SystemExit(f"missing source-family crosswalk for pack {pack:02X}")
        family_usage = usage_by_family.get(pack, [])
        family_semantic = semantic_by_family.get(pack, [])
        visible = [
            u for u in family_usage
            if u["player_visible"] in {"strong_visible_text", "strong_dialogue_historical"}
        ]
        contexts = sorted({s["semantic_context"] for s in family_semantic})
        out.append(
            {
                "config_id": cfg_id(row),
                "pack_id_hex": row["pack_id_hex"],
                "record_index": row["record_index"],
                "entry_id_hex": row["entry_id_hex"],
                "map_command_addr": row["command_addr"],
                "source_family_hex": row["pack_id_hex"],
                "source_root": meta["source_root"],
                "source_mode": meta["source_mode"],
                "source_pair_usage_rows": len(family_usage),
                "player_visible_source_rows": len(visible),
                "script_callsite_count_sum": sum(
                    int(u["script_callsite_count"] or 0) for u in family_usage
                ),
                "direct_callsite_count_sum": sum(
                    int(u["direct_callsite_count"] or 0) for u in family_usage
                ),
                "known_semantic_context_count": len(contexts),
                "known_semantic_contexts": " | ".join(contexts),
                "location_label_status": (
                    "context_only" if contexts else "unlabeled"
                ),
            }
        )
    out_dir = root / "data/maps/context"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / "map_dialogue_pack_crosslink.csv"
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        writer.writeheader()
        writer.writerows(out)

    config_contexts: dict[str, set[str]] = defaultdict(set)
    for row in out:
        if row["known_semantic_contexts"]:
            config_contexts[row["config_id"]].add(row["known_semantic_contexts"])

    status_counts = Counter(r["location_label_status"] for r in out)
    summary = {
        "schema_version": 1,
        "kind": "map_dialogue_pack_context_crosslink",
        "join_rule": (
            "for valid CA packs 0x14..0xF9, script-pack interval index equals "
            "C7 source-family index"
        ),
        "map_occurrence_count": len(out),
        "map_pack_family_joined_count": sum(bool(r["source_root"]) for r in out),
        "distinct_map_packs": len({r["pack_id_hex"] for r in out}),
        "occurrences_with_known_semantic_context": sum(
            r["known_semantic_context_count"] > 0 for r in out
        ),
        "configurations_with_known_semantic_context": len(config_contexts),
        "location_label_status_counts": dict(sorted(status_counts.items())),
        "semantic_configuration_ids": sorted(config_contexts),
        "interpretation": (
            "Pack-level dialogue context is provenance, not a map-name proof. "
            "Human-facing display_name stays unset until independent location "
            "evidence ties a semantic context to the selected map."
        ),
        "outputs": ["map_dialogue_pack_crosslink.csv", "map_dialogue_pack_crosslink_summary.json"],
    }
    (out_dir / "map_dialogue_pack_crosslink_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
