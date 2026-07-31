#!/usr/bin/env python3
"""Record agent classifications into the README corpus and emit a ledger file.

This script turns the human/agent classification step into a scripted,
reviewable operation. It merges classification fields into the per-repo meta
files produced by fetch_readmes.py (preserving upstream repo metadata and
readmeStatus/fetchStatus), validates every list name against the workspace
taxonomy, and emits a ledger JSON that apply_user_lists.py can consume
directly in offline-plan / online-plan / apply mode.

It never calls GitHub. Run it after fetch_readmes.py and before the offline
plan, and treat the emitted ledger as the narrow incremental ledger for the
repos listed in the classification file.

Usage:

    python write_classification.py \\
        --classifications classifications.json \\
        --inventory <workspace>/github-stars.json \\
        --out-dir <workspace> \\
        --ledger-name incremental-20260801-ledger

The --classifications file is a JSON list of objects. Each object requires:

    {
      "nameWithOwner": "owner/repo",
      "finalLists": ["list-a", "list-b"]
    }

Optional fields: summary, reason, confidence, facets, platforms,
candidateLists, signals, classificationStatus, productType.
Unknown list names and repos missing from the inventory are rejected.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import apply_user_lists as sync

CLASSIFICATION_FIELDS = {
    "summary": None,
    "productType": None,
    "primaryFunction": None,
    "facets": [],
    "platforms": [],
    "signals": [],
    "candidateLists": [],
    "finalLists": [],
    "confidence": None,
    "reason": None,
    "classificationStatus": None,
}

DEFAULT_PRODUCT_TYPE = "agent-classified"
DEFAULT_CLASSIFICATION_STATUS = "reviewed"


def safe_slug(name_with_owner):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name_with_owner.replace("/", "__"))


def load_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    tmp_path.replace(path)


def normalize_classifications(records, product_type, taxonomy_names):
    unknown = set()
    normalized = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Each classification entry must be an object.")
        name = record.get("nameWithOwner")
        final_lists = record.get("finalLists")
        if not isinstance(name, str) or not name:
            raise ValueError(f"Classification entry missing nameWithOwner: {record!r}")
        if not isinstance(final_lists, list) or not final_lists:
            raise ValueError(f"{name}: finalLists must be a non-empty list.")
        unknown.update(list_name for list_name in final_lists if list_name not in taxonomy_names)
        candidate = record.get("candidateLists")
        if isinstance(candidate, list):
            unknown.update(list_name for list_name in candidate if list_name not in taxonomy_names)
        entry = {
            "nameWithOwner": name,
            "finalLists": list(final_lists),
            "productType": record.get("productType") or product_type,
            "classificationStatus": record.get("classificationStatus")
            or DEFAULT_CLASSIFICATION_STATUS,
        }
        for key in ("summary", "reason", "confidence"):
            if record.get(key) is not None:
                entry[key] = record[key]
        for key in ("facets", "platforms", "signals", "candidateLists"):
            value = record.get(key)
            if isinstance(value, list):
                entry[key] = list(value)
        normalized.append(entry)
    if unknown:
        raise ValueError(
            "Unknown list names: "
            + ", ".join(sorted(unknown))
            + ". Add them to <workspace>/taxonomy.yaml first."
        )
    return normalized


def apply_classifications(records, meta_dir, taxonomy, ledger_path, product_type=DEFAULT_PRODUCT_TYPE, inventory_names=None):
    """Merge classification fields into meta files and emit a ledger.

    Returns the emitted ledger list. Raises ValueError on unknown lists,
    repos missing from the inventory, missing meta files, or a ledger path
    that already holds different content.
    """
    meta_dir = Path(meta_dir)
    taxonomy_names = set(taxonomy["names"])
    normalized = normalize_classifications(records, product_type, taxonomy_names)

    failures = sync.validate_assignments(normalized)
    if failures:
        preview = "; ".join(
            sync.failure_label(item) + ": " + item["error"]
            for item in failures[:10]
        )
        raise ValueError(f"Invalid classifications: {preview}")

    if inventory_names is not None:
        missing_repos = sorted(
            item["nameWithOwner"]
            for item in normalized
            if item["nameWithOwner"] not in inventory_names
        )
        if missing_repos:
            raise ValueError(
                "Repos not present in inventory: "
                + ", ".join(missing_repos)
                + ". Refresh the inventory first."
            )

    ledger = []
    for entry in normalized:
        name = entry["nameWithOwner"]
        slug = safe_slug(name)
        meta_path = meta_dir / f"{slug}.json"
        if not meta_path.exists():
            raise ValueError(
                f"{name}: meta file {meta_path} not found. Run fetch_readmes.py first."
            )
        meta = load_json(meta_path, {})
        if not isinstance(meta, dict):
            raise ValueError(f"{name}: meta file {meta_path} is not a JSON object.")
        merged = {**meta}
        for key, default in CLASSIFICATION_FIELDS.items():
            if key in entry:
                merged[key] = entry[key]
            elif key not in merged:
                merged[key] = list(default) if isinstance(default, list) else default
        write_json(meta_path, merged)
        ledger.append(
            {
                "nameWithOwner": name,
                "finalLists": list(entry["finalLists"]),
                "readmePath": f"star-readmes/raw/{slug}.md",
                "description": merged.get("description"),
                "summary": merged.get("summary"),
                "productType": merged.get("productType"),
                "primaryFunction": "; ".join(entry["finalLists"]),
                "facets": list(merged.get("facets") or []),
                "platforms": list(merged.get("platforms") or []),
                "signals": list(merged.get("signals") or []),
                "candidateLists": list(merged.get("candidateLists") or []),
                "confidence": merged.get("confidence"),
                "reason": merged.get("reason"),
                "classificationStatus": merged.get("classificationStatus"),
            }
        )

    ledger.sort(key=lambda item: item["nameWithOwner"].casefold())
    ledger_path = Path(ledger_path)
    if ledger_path.exists():
        existing = load_json(ledger_path)
        if existing != ledger:
            raise ValueError(
                f"{ledger_path} already exists with different content; "
                "pass --ledger-name <name> to write a new file instead of overwriting."
            )
    write_json(ledger_path, ledger)
    return ledger


def main():
    parser = argparse.ArgumentParser(
        description="Record classifications into meta files and emit a ledger."
    )
    parser.add_argument("--classifications", required=True, help="JSON list of classification records")
    parser.add_argument("--out-dir", required=True, help="Workspace directory")
    parser.add_argument("--meta-dir", help="Meta directory; defaults to <out-dir>/star-readmes/meta")
    parser.add_argument("--inventory", help="Inventory JSON; repos not in it are rejected")
    parser.add_argument("--taxonomy", help="Taxonomy YAML; defaults like apply_user_lists.py")
    parser.add_argument("--ledger-name", default="classification-ledger", help="Ledger file name without .json; default 'classification-ledger'")
    parser.add_argument("--product-type", default=DEFAULT_PRODUCT_TYPE, help="productType label for entries without one")
    args = parser.parse_args()

    out_dir = Path(args.out_dir).resolve()
    taxonomy_path = sync.choose_taxonomy_path(out_dir, args.taxonomy)
    taxonomy = sync.load_taxonomy(taxonomy_path)
    meta_dir = Path(args.meta_dir).resolve() if args.meta_dir else (out_dir / "star-readmes" / "meta")

    records = load_json(args.classifications)
    if not isinstance(records, list):
        raise ValueError("--classifications must be a JSON list.")

    inventory_names = None
    if args.inventory:
        payload = sync.load_json(args.inventory)
        inventory_names = {
            item["nameWithOwner"] for item in sync.normalize_inventory(payload)
        }

    ledger_path = out_dir / "star-readmes" / f"{args.ledger_name}.json"
    ledger = apply_classifications(
        records,
        meta_dir,
        taxonomy,
        ledger_path,
        product_type=args.product_type,
        inventory_names=inventory_names,
    )

    print(f"Recorded {len(ledger)} classifications into meta files.")
    print(f"Wrote: {ledger_path}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
