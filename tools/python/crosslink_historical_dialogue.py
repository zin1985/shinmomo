#!/usr/bin/env python3
"""Crosslink current Shinmomo source usages to retained historical dialogue decodes.

This tool consumes metadata/token hashes from the current usage catalog plus three
historical v33 decoder CSVs. It emits metadata only and never copies decoded text.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

HISTORICAL_FILES = [
    "archive/previous_zip_contents/shinmomo_vol013_mode02_mass_dump_v33/shinmomo_mode02_chain_C8_A7DD_v33_sample.csv",
    "data/csv/shinmomo_v33_scan_C8_A7D0_A960.csv",
    "data/csv/shinmomo_v33_test_C8_A7DD.csv",
]


def _parse_historical_tokens(row: dict) -> list[int]:
    fields = (row.get("raw_tokens") or "").strip().split()
    if not fields:
        return []
    try:
        tokens = [int(x, 16) for x in fields if len(x) == 2]
    except ValueError:
        return []
    return tokens if len(tokens) == len(fields) else []


def _logical_record_complete(tokens: list[int]) -> bool:
    """True only when the final 00 is a standalone logical terminator.

    Tokens 0x18..0x1F consume the following byte even when that byte is 0x00.
    This distinction repairs retained v33 rows that split a logical record at
    an 0x18 0x00 pair.
    """
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if 0x18 <= token < 0x20:
            if i + 1 >= len(tokens):
                return False
            i += 2
            continue
        if token == 0:
            return i == len(tokens) - 1
        i += 1
    return False


def historical_hash_index(repo: Path) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for rel in HISTORICAL_FILES:
        path = repo / rel
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
            rows = list(csv.DictReader(handle))

        for row_index, row in enumerate(rows):
            tokens = _parse_historical_tokens(row)
            if not tokens or tokens[0] != 0x7D:
                continue

            joined = list(tokens)
            decoded_len = len((row.get("text") or "").strip())
            last_index = row_index

            # Retained v33 sometimes split a logical record when a paired
            # 0x18..0x1F token was followed by low byte 0x00. Stitch only
            # state-contiguous rows until a true standalone 0x00 terminator.
            while not _logical_record_complete(joined):
                next_index = last_index + 1
                if next_index >= len(rows):
                    break
                cur = rows[last_index]
                nxt = rows[next_index]
                if (cur.get("end_state") or "") != (nxt.get("start_state") or ""):
                    break
                nxt_tokens = _parse_historical_tokens(nxt)
                if not nxt_tokens:
                    break
                joined.extend(nxt_tokens)
                decoded_len += len((nxt.get("text") or "").strip())
                last_index = next_index

            if not _logical_record_complete(joined) or decoded_len <= 4:
                continue

            digest = hashlib.sha256(bytes(joined)).hexdigest()
            out[digest].append({
                "historical_file": rel,
                "historical_row": row_index + 2,
                "historical_row_end": last_index + 2,
                "historical_segments_joined": last_index - row_index + 1,
                "historical_root": row.get("root", ""),
                "historical_seg": row.get("seg", ""),
                "historical_text_len": decoded_len,
                "historical_score": row.get("score", ""),
                "historical_unknown_count": row.get("unknown", ""),
            })
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--catalog", type=Path,
                    default=Path("data/dialogue/source_pair_usage_catalog.csv"))
    ap.add_argument("--out-dir", type=Path, default=Path("data/dialogue"))
    args = ap.parse_args()

    catalog_path = args.catalog if args.catalog.is_absolute() else args.repo / args.catalog
    rows = list(csv.DictReader(catalog_path.open(encoding="utf-8-sig", newline="")))
    historical = historical_hash_index(args.repo)

    crosswalk = []
    for row in rows:
        digest = row.get("token_sha256", "")
        if not digest or digest not in historical:
            continue
        for match in historical[digest]:
            base = row.get("player_visible", "unknown")
            evidence = "strong_dialogue_historical" if base == "unknown" else base
            crosswalk.append({
                "family_id": row["family_id"],
                "family_hex": row["family_hex"],
                "subindex": row["subindex"],
                "subindex_hex": row["subindex_hex"],
                "token_sha256": digest,
                "selected_source_cpu": row.get("selected_source_cpu", ""),
                "base_player_visible": base,
                "historical_evidence_class": evidence,
                **match,
            })

    args.out_dir.mkdir(parents=True, exist_ok=True)
    fields = [
        "family_id", "family_hex", "subindex", "subindex_hex", "token_sha256",
        "selected_source_cpu", "base_player_visible", "historical_evidence_class",
        "historical_file", "historical_row", "historical_row_end",
        "historical_segments_joined", "historical_root", "historical_seg",
        "historical_text_len", "historical_score", "historical_unknown_count",
    ]
    with (args.out_dir / "historical_decode_crosswalk.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(crosswalk)

    pair_keys = {(int(r["family_id"]), int(r["subindex"])) for r in crosswalk}
    new_strong = {
        (int(r["family_id"]), int(r["subindex"])) for r in crosswalk
        if r["base_player_visible"] == "unknown"
    }
    summary = {
        "crosswalk_rows": len(crosswalk),
        "unique_usage_pairs": len(pair_keys),
        "new_strong_historical_dialogue_pairs": len(new_strong),
        "unique_token_hashes": len({r["token_sha256"] for r in crosswalk}),
        "families": sorted({f for f, _ in pair_keys}),
        "base_unknown_visibility_pairs": sum(r.get("player_visible") == "unknown" for r in rows),
        "effective_unknown_after_historical_crosslink": (
            sum(r.get("player_visible") == "unknown" for r in rows) - len(new_strong)
        ),
        "classification_rule": (
            "exact token SHA-256 match + first token 0x7D + terminator 0x00 + "
            "non-empty historical decoded text"
        ),
        "decoded_text_copied_to_crosswalk": False,
    }
    (args.out_dir / "historical_decode_crosswalk_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
