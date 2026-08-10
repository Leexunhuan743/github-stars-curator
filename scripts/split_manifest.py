#!/usr/bin/env python3
"""Split the starred-repo inventory into balanced batches for parallel subagents.

Large-scale reclassification (hundreds of repos) is done by parallel
subagents: one batch per subagent, each batch a self-contained JSON list of
repo objects carrying the fields the classifier needs (description, topics,
language, plus optional meta summary and legacy lists as reference-only).
This script does the split so no agent has to hand-craft batches.

Usage:

    python scripts/split_manifest.py \
        --inventory <workspace>/github-stars.json \
        --batches 5 \
        --out-dir <workspace>/batches \
        [--meta-dir <workspace>/star-readmes/meta] \
        [--ledger <workspace>/star-readmes/complete-ledger.json]

Outputs batch-1.json ... batch-<N>.json (repo-object arrays) plus
split-summary.json. A companion script, merge_classifications.py, consumes
the per-batch result files (batch-<N>-records.json) and validates them 1:1.

The optional --meta-dir merges each repo's existing `summary` into the batch
entry (reference only, never authoritative); --ledger merges each repo's
current `finalLists` as `legacyLists` (reference only). Neither is required
for a clean split.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import apply_user_lists as sync


def safe_slug(name_with_owner):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name_with_owner.replace("/", "__"))


def load_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path = Path(path)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    tmp_path.replace(path)


def batch_repo_entry(item):
    """Project an inventory item onto the classifier-facing batch fields."""
    return {
        "nameWithOwner": item["nameWithOwner"],
        "description": item.get("description"),
        "primaryLanguage": item.get("primaryLanguage"),
        "topics": list(item.get("topics") or []),
        "isArchived": bool(item.get("isArchived")),
        "isFork": bool(item.get("isFork")),
        "stargazerCount": item.get("stargazerCount"),
        "summary": None,
        "legacyLists": [],
    }


def enrich_with_meta(entries, meta_dir):
    meta_by_name = {}
    if meta_dir is not None and meta_dir.exists():
        for meta_path in sorted(meta_dir.glob("*.json")):
            payload = load_json(meta_path, {})
            if isinstance(payload, dict) and payload.get("nameWithOwner"):
                meta_by_name[payload["nameWithOwner"]] = payload
    for entry in entries:
        meta = meta_by_name.get(entry["nameWithOwner"])
        if meta and isinstance(meta.get("summary"), str):
            entry["summary"] = meta["summary"]
    return meta_by_name


def enrich_with_ledger(entries, ledger_path):
    if ledger_path is None:
        return
    payload = load_json(ledger_path, None)
    if payload is None:
        return
    if isinstance(payload, dict) and isinstance(payload.get("assignments"), list):
        assignments = payload["assignments"]
    elif isinstance(payload, list):
        assignments = payload
    else:
        raise ValueError(
            f"Ledger {ledger_path} must be a list or an object with an 'assignments' list."
        )
    by_name = {
        item["nameWithOwner"]: list(item.get("finalLists") or [])
        for item in assignments
        if isinstance(item, dict)
    }
    for entry in entries:
        if entry["nameWithOwner"] in by_name:
            entry["legacyLists"] = by_name[entry["nameWithOwner"]]


def main():
    parser = argparse.ArgumentParser(
        description="Split the starred-repo inventory into balanced classification batches."
    )
    parser.add_argument("--inventory", required=True, help="github-stars.json inventory")
    parser.add_argument("--batches", type=int, required=True, help="Number of batches")
    parser.add_argument("--out-dir", required=True, help="Directory for batch-*.json outputs")
    parser.add_argument("--meta-dir", help="star-readmes/meta; merges existing summaries (reference only)")
    parser.add_argument("--ledger", help="Full ledger; merges current finalLists as legacyLists (reference only)")
    args = parser.parse_args()

    if args.batches < 1:
        raise ValueError("--batches must be at least 1.")

    payload = load_json(args.inventory)
    inventory = sync.normalize_inventory(payload)
    entries = [batch_repo_entry(item) for item in inventory]
    enrich_with_meta(entries, Path(args.meta_dir) if args.meta_dir else None)
    enrich_with_ledger(entries, args.ledger)

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    total = len(entries)
    if total == 0:
        raise ValueError("inventory contains no repos; nothing to split. Refresh the inventory first.")
    if args.batches > total:
        print(
            f"WARNING: --batches {args.batches} exceeds the repo count {total}; "
            f"only {total} batch file(s) will be written.",
            file=sys.stderr,
        )
    effective_batches = min(args.batches, total)
    base, remainder = divmod(total, effective_batches)
    batch_sizes = [base + (1 if index < remainder else 0) for index in range(effective_batches)]

    cursor = 0
    written = []
    for index, size in enumerate(batch_sizes, start=1):
        batch = entries[cursor : cursor + size]
        cursor += size
        batch_path = out_dir / f"batch-{index}.json"
        write_json(batch_path, batch)
        written.append({"batch": index, "path": str(batch_path), "repos": len(batch)})

    # Remove stale higher-index batch files from an earlier, larger split so
    # merge_classifications' completeness check sees only the current set.
    stale = [
        path for path in out_dir.glob("batch-*.json")
        if re.fullmatch(r"batch-\d+\.json", path.name)
        and int(path.stem.split("-")[1]) > effective_batches
    ]
    for path in stale:
        path.unlink(missing_ok=True)
        print(f"Removed stale batch file: {path.name}", file=sys.stderr)

    summary = {
        "generatedAt": sync.utc_now(),
        "inventoryPath": str(Path(args.inventory).resolve()),
        "metaDir": str(Path(args.meta_dir).resolve()) if args.meta_dir else None,
        "ledgerPath": str(Path(args.ledger).resolve()) if args.ledger else None,
        "totalRepos": total,
        "batches": len(batch_sizes),
        "batchSizes": batch_sizes,
        "files": written,
    }
    write_json(out_dir / "split-summary.json", summary)

    print(f"Split {total} repos into {len(batch_sizes)} batches.")
    for item in written:
        print(f"  batch-{item['batch']}: {item['repos']} repos -> {item['path']}")
    print(f"Wrote: {out_dir / 'split-summary.json'}")
    print(
        "Each subagent classifies its batch into batch-<N>-records.json; "
        "then run merge_classifications.py to validate and combine."
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
