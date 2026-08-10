#!/usr/bin/env python3
"""Audit live GitHub Stars list membership drift from a local classification ledger.

This script is intentionally read-only. It helps prevent stale full-ledger
writebacks from undoing list edits made in GitHub's UI or another client.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import apply_user_lists as sync


def load_inventory_names(path: Path) -> set[str]:
    payload = sync.load_json(path)
    return {item["nameWithOwner"] for item in sync.normalize_inventory(payload)}


def ledger_memberships(assignments, managed_names: set[str], inventory_names: set[str] | None):
    memberships: dict[str, set[str]] = defaultdict(set)
    for item in assignments:
        name = item["nameWithOwner"]
        if inventory_names is not None and name not in inventory_names:
            continue
        for list_name in item.get("finalLists", []):
            if list_name in managed_names:
                memberships[name].add(list_name)
    return memberships


def live_memberships(existing_lists, managed_names: set[str], target_names: set[str] | None):
    managed_existing = [
        item for item in existing_lists
        if item.get("name") in managed_names
    ]
    live = sync.fetch_existing_memberships(managed_existing, target_names)
    memberships: dict[str, set[str]] = defaultdict(set)
    for repo_name, lists in live.items():
        for item in lists:
            if item.get("name") in managed_names:
                memberships[repo_name].add(item["name"])
    return memberships


def summarize_drift(local_by_repo, live_by_repo):
    repos = sorted(set(local_by_repo) | set(live_by_repo))
    repo_drift = []
    list_drift: dict[str, dict[str, list[str]]] = defaultdict(lambda: {
        "liveNotLocal": [],
        "localNotLive": [],
    })
    for repo in repos:
        local = set(local_by_repo.get(repo, set()))
        live = set(live_by_repo.get(repo, set()))
        live_not_local = sorted(live - local)
        local_not_live = sorted(local - live)
        if not live_not_local and not local_not_live:
            continue
        repo_drift.append({
            "nameWithOwner": repo,
            "liveLists": sorted(live),
            "localLists": sorted(local),
            "liveNotLocal": live_not_local,
            "localNotLive": local_not_live,
        })
        for list_name in live_not_local:
            list_drift[list_name]["liveNotLocal"].append(repo)
        for list_name in local_not_live:
            list_drift[list_name]["localNotLive"].append(repo)
    return repo_drift, {
        name: {
            "liveNotLocal": sorted(value["liveNotLocal"]),
            "localNotLive": sorted(value["localNotLive"]),
        }
        for name, value in sorted(list_drift.items())
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read live GitHub Stars list memberships and report drift from a local ledger."
    )
    parser.add_argument("--mapping", required=True, help="Classification ledger JSON")
    parser.add_argument("--inventory", help="GitHub stars inventory JSON; limits audit to inventory repos when provided")
    parser.add_argument("--out-dir", required=True, help="Directory for github-stars-cloud-drift-report.json")
    parser.add_argument("--taxonomy", help="Taxonomy YAML; defaults like apply_user_lists.py")
    parser.add_argument(
        "--all-inventory",
        action="store_true",
        help="Compare every repo in the inventory, treating inventory repos absent from the ledger as local empty membership.",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir).resolve()
    taxonomy_path = sync.choose_taxonomy_path(out_dir, args.taxonomy)
    taxonomy = sync.load_taxonomy(taxonomy_path)
    managed_names = set(taxonomy["names"])
    assignments = sync.load_mapping(args.mapping)
    validation = sync.validate_assignments(assignments)
    if validation:
        preview = "; ".join(
            sync.failure_label(item) + ": " + item["error"]
            for item in validation[:10]
        )
        raise ValueError(f"Invalid classification ledger: {preview}")

    inventory_names = load_inventory_names(Path(args.inventory)) if args.inventory else None
    local_by_repo = ledger_memberships(assignments, managed_names, inventory_names)
    if args.all_inventory and inventory_names is not None:
        for name in inventory_names:
            local_by_repo.setdefault(name, set())
        target_names = inventory_names
    else:
        target_names = set(local_by_repo)

    viewer_state = sync.fetch_viewer_state()
    live_by_repo = live_memberships(viewer_state["lists"], managed_names, target_names)
    if args.all_inventory and inventory_names is not None:
        for name in inventory_names:
            live_by_repo.setdefault(name, set())

    repo_drift, list_drift = summarize_drift(local_by_repo, live_by_repo)
    report = {
        "schemaVersion": 1,
        "generatedAt": sync.utc_now(),
        "viewerLogin": viewer_state["login"],
        "mappingPath": str(Path(args.mapping).resolve()),
        "inventoryPath": str(Path(args.inventory).resolve()) if args.inventory else None,
        "taxonomyPath": str(taxonomy_path),
        "managedLists": list(taxonomy["names"]),
        "auditedRepoCount": len(target_names),
        "driftRepoCount": len(repo_drift),
        "hasDrift": bool(repo_drift),
        "repoDrift": repo_drift,
        "listDrift": list_drift,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "github-stars-cloud-drift-report.json"
    sync.write_json(out_path, report)

    print(f"Audited repos: {report['auditedRepoCount']}")
    print(f"Repos with drift: {report['driftRepoCount']}")
    live_not_local = any(item["liveNotLocal"] for item in repo_drift)
    only_local_not_live = bool(repo_drift) and not live_not_local
    if only_local_not_live:
        print(
            "No liveNotLocal drift: every difference is a repo the ledger assigns "
            "to lists it is not yet in. This is the expected pre-sync state for "
            "newly classified repos (or a first full run), not a stop signal."
        )
    for item in repo_drift[:20]:
        print(
            f"{item['nameWithOwner']}: "
            f"liveNotLocal={item['liveNotLocal']} localNotLive={item['localNotLive']}"
        )
    if len(repo_drift) > 20:
        print(f"... {len(repo_drift) - 20} more drifted repos")
    print(f"Wrote: {out_path}")
    # localNotLive-only drift is the expected pre-sync state (newly
    # classified repos); only liveNotLocal is a stop-and-reconcile signal.
    return 1 if live_not_local else 0


if __name__ == "__main__":
    raise SystemExit(main())
