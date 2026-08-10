#!/usr/bin/env python3
"""Merge and validate per-batch classification results into one records file.

Companion to split_manifest.py for large-scale reclassification. Each
parallel subagent classifies its batch (batch-N.json) and writes
batch-N-records.json, a JSON list of classification records in the same
shape write_classification.py accepts:

    [{"nameWithOwner": "owner/repo", "finalLists": ["list-a", ...]}, ...]

This script validates every batch result before merging:

- JSON integrity: a truncated or corrupted records file is reported, not
  silently skipped (subagents writing large files can produce truncated JSON).
- 1:1 coverage: every repo in a batch has a record, and every record belongs
  to that batch. Missing and extra repos are reported per batch.
- List-name whitelist: every finalLists entry resolves against the taxonomy.
- Cross-batch duplicates: the same repo classified in two batches is an error.

Only when every check passes is the combined records file written
(default <out-dir>/records.json, pass --records-name to change the stem).
The merge report (<out-dir>/merge-summary.json) is always written so the
user can audit per-batch coverage.

Usage:

    python scripts/merge_classifications.py \
        --batches-dir <workspace>/batches \
        --out-dir <workspace> \
        --records-name records \
        [--taxonomy <taxonomy.yaml>]

Unknown list names are always rejected: add any new bucket to
<workspace>/taxonomy.yaml before running the batch pipeline.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import apply_user_lists as sync


def load_json_or_report(path):
    """Load JSON; return (None, error) on missing/truncated/malformed input."""
    if not path.exists():
        return None, f"file not found: {path}"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return None, f"invalid/truncated JSON in {path}: {exc}"


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    tmp_path.replace(path)


def validate_batch_records(batch_repos, records, batch_name, taxonomy_names):
    """Validate one batch's records. Returns (issues, normalized_records)."""
    issues = []
    batch_names = set(batch_repos)
    record_names = set()
    normalized = []
    for record in records:
        if not isinstance(record, dict):
            issues.append(f"{batch_name}: record is not an object: {record!r}")
            continue
        name = record.get("nameWithOwner")
        final_lists = record.get("finalLists")
        if not isinstance(name, str) or not name:
            issues.append(f"{batch_name}: record missing nameWithOwner: {record!r}")
            continue
        if name in record_names:
            issues.append(f"{batch_name}: duplicate record for {name}")
        record_names.add(name)
        if not isinstance(final_lists, list) or not final_lists:
            issues.append(f"{batch_name}: {name} finalLists must be a non-empty list")
            continue
        if name not in batch_names:
            issues.append(f"{batch_name}: record for {name} is not in this batch")
            continue
        if any(not isinstance(entry, str) for entry in final_lists):
            issues.append(f"{batch_name}: {name} finalLists entries must be strings")
            continue
        if len(set(final_lists)) != len(final_lists):
            issues.append(f"{batch_name}: {name} finalLists contains duplicate list names")
        unknown = sorted(list_name for list_name in final_lists if list_name not in taxonomy_names)
        if unknown:
            issues.append(f"{batch_name}: {name} unknown list names: {', '.join(unknown)}")
        normalized.append(record)
    missing = sorted(batch_names - record_names)
    if missing:
        issues.append(f"{batch_name}: missing records for {len(missing)} repos: {', '.join(missing[:10])}")
    return issues, normalized


def main():
    parser = argparse.ArgumentParser(
        description="Validate and merge batch classification results into a records file."
    )
    parser.add_argument("--batches-dir", required=True, help="Directory containing batch-<N>.json and batch-<N>-records.json")
    parser.add_argument("--out-dir", required=True, help="Workspace directory for records.json and merge-summary.json")
    parser.add_argument("--records-name", default="records", help="Output records file stem (default 'records')")
    parser.add_argument("--taxonomy", help="Taxonomy YAML; defaults like apply_user_lists.py")
    args = parser.parse_args()

    out_dir = Path(args.out_dir).resolve()
    taxonomy = sync.load_taxonomy(sync.choose_taxonomy_path(out_dir, args.taxonomy))
    taxonomy_names = set(taxonomy["names"])

    batches_dir = Path(args.batches_dir).resolve()
    batch_files = sorted(
        path for path in batches_dir.glob("batch-*.json")
        if re.fullmatch(r"batch-\d+\.json", path.name)
    )
    if not batch_files:
        raise ValueError(f"No batch-<N>.json files found in {batches_dir}")

    # Validate the batch set is complete: split_manifest.py writes
    # split-summary.json naming exactly which batches it produced. A missing
    # batch would silently under-cover; a stale higher-index file from an
    # earlier, larger split would be merged as if current.
    expected_count = None
    split_summary_path = batches_dir / "split-summary.json"
    if split_summary_path.exists():
        try:
            split_summary = json.loads(split_summary_path.read_text(encoding="utf-8"))
            expected_count = split_summary.get("batches")
        except (json.JSONDecodeError, UnicodeDecodeError):
            split_summary = None
            print(
                f"WARNING: {split_summary_path} is unreadable; batch-set completeness not verified",
                file=sys.stderr,
            )
    else:
        print(
            "WARNING: split-summary.json not found; batch-set completeness not verified "
            "(missing batches would silently under-cover). Run split_manifest.py first.",
            file=sys.stderr,
        )
    batch_indexes = sorted(int(path.stem.split("-")[1]) for path in batch_files)
    if expected_count is not None and batch_indexes != list(range(1, expected_count + 1)):
        raise ValueError(
            f"Batch set is incomplete or has stale files: found {batch_indexes}, "
            f"split-summary.json expects 1..{expected_count}. "
            "Re-run split_manifest.py or remove stale batch-*.json files."
        )

    all_issues = []
    per_batch = []
    merged = []
    seen_names = set()
    cross_batch_duplicates = []

    for batch_path in sorted(batch_files, key=lambda p: int(p.stem.split("-")[1])):
        batch_index = int(batch_path.stem.split("-")[1])
        batch_repos, batch_error = load_json_or_report(batch_path)
        if batch_error:
            all_issues.append(batch_error)
            per_batch.append({"batch": batch_index, "path": str(batch_path), "error": batch_error})
            continue
        if not isinstance(batch_repos, list):
            all_issues.append(f"batch-{batch_index}: expected a JSON list of repos")
            per_batch.append({"batch": batch_index, "path": str(batch_path), "error": "not a JSON list"})
            continue

        records_path = batches_dir / f"batch-{batch_index}-records.json"
        records, records_error = load_json_or_report(records_path)
        if records_error:
            all_issues.append(records_error)
            per_batch.append({"batch": batch_index, "path": str(records_path), "error": records_error, "expected": len(batch_repos)})
            continue
        # A records file older than its batch manifest is a leftover from a
        # previous split/reclassification run; merging it silently would
        # propagate stale classifications.
        if records_path.stat().st_mtime < batch_path.stat().st_mtime:
            issue = (
                f"{records_path.name} is older than {batch_path.name}; "
                "delete stale batch-*-records.json files and re-run the subagents"
            )
            all_issues.append(issue)
            per_batch.append({"batch": batch_index, "path": str(records_path), "error": issue, "expected": len(batch_repos)})
            continue
        if not isinstance(records, list):
            all_issues.append(f"batch-{batch_index}: batch-{batch_index}-records.json must be a JSON list")
            per_batch.append({"batch": batch_index, "path": str(records_path), "error": "not a JSON list", "expected": len(batch_repos)})
            continue

        batch_names = {item["nameWithOwner"] for item in batch_repos if isinstance(item, dict) and item.get("nameWithOwner")}
        issues, normalized = validate_batch_records(
            batch_names, records, f"batch-{batch_index}", taxonomy_names
        )
        all_issues.extend(issues)
        per_batch.append(
            {
                "batch": batch_index,
                "path": str(records_path),
                "expected": len(batch_repos),
                "covered": len(normalized),
                "missing": sorted(batch_names - {r["nameWithOwner"] for r in normalized}),
                "issues": issues,
            }
        )
        for record in normalized:
            name = record["nameWithOwner"]
            if name in seen_names:
                cross_batch_duplicates.append(name)
            seen_names.add(name)
            merged.append(record)

    if cross_batch_duplicates:
        all_issues.append(
            "cross-batch duplicate classifications: "
            + ", ".join(sorted(cross_batch_duplicates))
        )

    merge_report = {
        "generatedAt": sync.utc_now(),
        "taxonomyPath": taxonomy["path"],
        "batchesDir": str(batches_dir),
        "perBatch": per_batch,
        "crossBatchDuplicates": sorted(cross_batch_duplicates),
        "issues": all_issues,
        "ok": not all_issues,
    }
    write_json(out_dir / "merge-summary.json", merge_report)

    if all_issues:
        print(f"Merge failed with {len(all_issues)} issue(s); records.json was NOT written.")
        for issue in all_issues[:20]:
            print(f"  - {issue}")
        if len(all_issues) > 20:
            print(f"  ... and {len(all_issues) - 20} more")
        print(f"Wrote: {out_dir / 'merge-summary.json'}")
        raise SystemExit(1)

    records_path = out_dir / f"{args.records_name}.json"
    write_json(records_path, merged)
    print(f"Validated {len(batch_files)} batches, {len(merged)} records, no issues.")
    print(f"Wrote: {records_path}")
    print(f"Wrote: {out_dir / 'merge-summary.json'}")
    print(f"Next: python scripts/write_classification.py --classifications {records_path} ...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
