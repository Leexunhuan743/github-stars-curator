#!/usr/bin/env python3
"""Apply a bucket-split reclassification to the full ledger.

Companion to the bucket-overload flow in references/workflow.md. After the
user adopts a split proposal, this script takes a mapping of repos to their
new lists and reclassifies them end to end:

- reuses write_classification.apply_classifications (validates list names,
  writes the new finalLists into the per-repo meta files, emits a narrow
  ledger),
- reuses write_classification.merge_into_full (snapshots the full ledger,
  then replaces same-name assignments) — the single merge path, no manual
  ledger surgery,
- reports replaced/added/total and the snapshot path.

The mapping file is a JSON object {"owner/repo": ["list-a", ...], ...}, or
a JSON list of {"nameWithOwner": "owner/repo", "finalLists": [...], ...}
records (extra fields such as reason are carried through).

Usage:

    python scripts/reclassify_bucket.py \
        --ledger "<workspace>/star-readmes/complete-ledger.json" \
        --mapping reclassify-mapping.json \
        --out-dir "<workspace>"

The full ledger is both the source of current assignments and the merge
target; pass --out-ledger to write the merged result elsewhere.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import apply_user_lists as sync
import write_classification as writer

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def parse_mapping(payload):
    """Normalize the mapping file into [(name, final_lists, extra), ...]."""
    if isinstance(payload, dict):
        entries = []
        for name, final_lists in payload.items():
            if not isinstance(name, str) or not name:
                raise ValueError(f"Mapping key must be a repo name: {name!r}")
            if not isinstance(final_lists, list) or not final_lists:
                raise ValueError(f"{name}: mapped value must be a non-empty list of list names")
            entries.append((name, list(final_lists), {}))
        return entries
    if isinstance(payload, list):
        entries = []
        for record in payload:
            if not isinstance(record, dict):
                raise ValueError("Each mapping record must be an object.")
            name = record.get("nameWithOwner")
            final_lists = record.get("finalLists")
            if not isinstance(name, str) or not name:
                raise ValueError(f"Mapping record missing nameWithOwner: {record!r}")
            if not isinstance(final_lists, list) or not final_lists:
                raise ValueError(f"{name}: finalLists must be a non-empty list")
            extra = {k: v for k, v in record.items() if k not in ("nameWithOwner", "finalLists")}
            entries.append((name, list(final_lists), extra))
        return entries
    raise ValueError("Mapping must be a JSON object or a JSON list.")


def main():
    parser = argparse.ArgumentParser(
        description="Reclassify repos into new lists and merge into the full ledger."
    )
    parser.add_argument("--ledger", required=True, help="Full ledger JSON (source of current assignments and merge target)")
    parser.add_argument("--mapping", required=True, help="JSON mapping: {repo: [lists]} or [{nameWithOwner, finalLists}]")
    parser.add_argument("--out-dir", required=True, help="Workspace directory (holds taxonomy.yaml and star-readmes/)")
    parser.add_argument("--out-ledger", help="Merge target; defaults to --ledger")
    parser.add_argument("--meta-dir", help="Meta directory; defaults to <out-dir>/star-readmes/meta")
    parser.add_argument("--taxonomy", help="Taxonomy YAML; defaults like apply_user_lists.py")
    parser.add_argument("--ledger-name", default="reclassified", help="Narrow ledger file name without .json; default 'reclassified'")
    args = parser.parse_args()

    out_dir = Path(args.out_dir).resolve()
    taxonomy_path = sync.choose_taxonomy_path(out_dir, args.taxonomy)
    taxonomy = sync.load_taxonomy(taxonomy_path)
    taxonomy_names = set(taxonomy["names"])
    meta_dir = Path(args.meta_dir).resolve() if args.meta_dir else (out_dir / "star-readmes" / "meta")

    mapping = parse_mapping(load_json(args.mapping))
    unknown = sorted(
        list_name for _, final_lists, _ in mapping for list_name in final_lists
        if list_name not in taxonomy_names
    )
    if unknown:
        raise ValueError(
            "Unknown list names: "
            + ", ".join(unknown)
            + ". Add them to <workspace>/taxonomy.yaml first."
        )

    ledger_payload = load_json(args.ledger)
    if isinstance(ledger_payload, dict) and isinstance(ledger_payload.get("assignments"), list):
        assignments = ledger_payload["assignments"]
    elif isinstance(ledger_payload, list):
        assignments = ledger_payload
    else:
        raise ValueError(
            f"Ledger {args.ledger} must be a list or an object with an 'assignments' list."
        )
    by_name = {item.get("nameWithOwner"): item for item in assignments if isinstance(item, dict)}
    missing = sorted(name for name, _, _ in mapping if name not in by_name)
    if missing:
        raise ValueError(
            "Repos not present in the ledger: "
            + ", ".join(missing)
            + ". Refresh or re-record the ledger first."
        )

    records = []
    for name, final_lists, extra in mapping:
        current = by_name[name]
        record = {
            "nameWithOwner": name,
            "finalLists": final_lists,
        }
        for key in ("summary", "productType", "primaryFunction", "facets", "platforms",
                    "signals", "candidateLists", "confidence", "reason", "classificationStatus"):
            if key in extra:
                record[key] = extra[key]
            elif key in current and current[key] is not None:
                record[key] = current[key]
        records.append(record)

    ledger_path = out_dir / "star-readmes" / f"{args.ledger_name}.json"
    ledger = writer.apply_classifications(
        records,
        meta_dir,
        taxonomy,
        ledger_path,
        product_type=writer.DEFAULT_PRODUCT_TYPE,
    )

    target = args.out_ledger or args.ledger
    replaced, added, removed, total, snapshot_path = writer.merge_into_full(
        target, ledger, args.ledger_name
    )
    print(f"Reclassified {len(records)} repos; wrote narrow ledger: {ledger_path}")
    print(f"Merged into full ledger: {replaced} replaced, {added} added ({total} total).")
    print(f"Snapshot: {snapshot_path}")
    print(
        "Next: run scripts/audit_cloud_drift.py to see how the new lists differ "
        "from live memberships, then the normal offline/online plan + apply."
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
