#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


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

README_STATUSES = {
    "ok",
    "missing",
    "rate_limited",
    "network_failed",
    "api_failed",
    "stale-but-retained",
    "unfetched",
}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def run_gh(args):
    result = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "gh failed")
    return result.stdout


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
    tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def write_text_atomic(path, body):
    path = Path(path)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(body, encoding="utf-8")
    tmp_path.replace(path)


def normalize_inventory(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("repositories"), list):
        return payload["repositories"]
    if isinstance(payload, dict) and payload.get("nameWithOwner"):
        return [payload]
    raise ValueError("Inventory must be a repo list, a repo object, or an object with a 'repositories' list.")


def load_delta_names(path):
    payload = load_json(path, {})
    return set(payload.get("newStars", []))


def fetch_readme(owner, repo):
    return run_gh(
        [
            "api",
            f"repos/{owner}/{repo}/readme",
            "-H",
            "Accept: application/vnd.github.raw+json",
        ]
    )


def classify_readme_error(message):
    normalized = message.lower()
    if "404" in normalized or "not found" in normalized:
        return "missing"
    if "rate limit" in normalized or "secondary rate" in normalized:
        return "rate_limited"
    if any(token in normalized for token in ["timed out", "timeout", "could not resolve", "connection"]):
        return "network_failed"
    return "api_failed"


def existing_meta(meta_path):
    payload = load_json(meta_path, {})
    return payload if isinstance(payload, dict) else {}


def merge_meta(repo_item, previous_meta, readme_path, fetch_result):
    merged = {**previous_meta, **repo_item}
    legacy_status = merged.pop("status", None)
    if "classificationStatus" not in merged and legacy_status not in README_STATUSES:
        merged["classificationStatus"] = legacy_status
    for key, default in CLASSIFICATION_FIELDS.items():
        if key not in merged:
            merged[key] = list(default) if isinstance(default, list) else default
    merged.update(
        {
            "readmeStatus": fetch_result["status"],
            "fetchStatus": fetch_result["fetchStatus"],
            "bytes": fetch_result["bytes"],
            "readmePath": str(readme_path),
            "error": fetch_result["error"],
            "lastFetchAttemptAt": fetch_result["attemptedAt"],
        }
    )
    if fetch_result["status"] == "ok":
        merged["lastFetchedAt"] = fetch_result["attemptedAt"]
        merged.pop("staleReason", None)
    elif fetch_result["status"] == "stale-but-retained":
        merged["staleReason"] = fetch_result["fetchStatus"]
    return merged


def load_all_meta(meta_dir):
    items = []
    for path in sorted(Path(meta_dir).glob("*.json")):
        payload = load_json(path, {})
        if isinstance(payload, dict) and payload.get("nameWithOwner"):
            items.append(payload)
    return items


def build_readme_index(manifest, raw_dir, meta_dir):
    rows = []
    for item in manifest:
        name = item["nameWithOwner"]
        slug = safe_slug(name)
        readme_path = Path(item.get("readmePath") or (raw_dir / f"{slug}.md"))
        rows.append(
            {
                "nameWithOwner": name,
                "description": item.get("description"),
                "readmeStatus": item.get("readmeStatus"),
                "fetchStatus": item.get("fetchStatus"),
                "classificationStatus": item.get("classificationStatus"),
                "readmePath": str(readme_path),
                "metaPath": str(meta_dir / f"{slug}.json"),
                "hasReadmeFile": readme_path.exists(),
            }
        )
    return rows


def main():
    parser = argparse.ArgumentParser(description="Fetch GitHub README files for starred repositories.")
    parser.add_argument("--inventory", required=True, help="Path to github-stars.json")
    parser.add_argument("--out-dir", required=True, help="Output directory for the README corpus")
    parser.add_argument("--only-new-from", help="Optional delta file; fetch only repos in newStars")
    args = parser.parse_args()

    inventory = normalize_inventory(load_json(args.inventory))
    selected = inventory
    if args.only_new_from:
        wanted = load_delta_names(args.only_new_from)
        selected = [item for item in inventory if item["nameWithOwner"] in wanted]

    out_dir = Path(args.out_dir).resolve()
    raw_dir = out_dir / "raw"
    meta_dir = out_dir / "meta"
    raw_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    fetched = 0
    missing = 0
    stale_retained = 0
    failed = []
    selected_names = {item["nameWithOwner"] for item in selected}

    for item in selected:
        owner, repo = item["nameWithOwner"].split("/", 1)
        slug = safe_slug(item["nameWithOwner"])
        readme_path = raw_dir / f"{slug}.md"
        meta_path = meta_dir / f"{slug}.json"
        previous = existing_meta(meta_path)

        attempted_at = utc_now()
        fetch_result = {
            "status": "ok",
            "fetchStatus": "ok",
            "bytes": 0,
            "error": None,
            "attemptedAt": attempted_at,
        }
        try:
            body = fetch_readme(owner, repo)
            write_text_atomic(readme_path, body)
            fetch_result["bytes"] = len(body.encode("utf-8"))
            fetched += 1
        except Exception as exc:
            error = str(exc)
            failure_status = classify_readme_error(error)
            has_existing_readme = readme_path.exists()
            fetch_result.update(
                {
                    "status": "stale-but-retained" if has_existing_readme else failure_status,
                    "fetchStatus": failure_status,
                    "bytes": readme_path.stat().st_size if has_existing_readme else 0,
                    "error": error,
                }
            )
            if has_existing_readme:
                stale_retained += 1
            elif failure_status == "missing":
                missing += 1
            else:
                failed.append({"nameWithOwner": item["nameWithOwner"], "status": failure_status, "error": error})

        meta = merge_meta(item, previous, readme_path, fetch_result)
        write_json(meta_path, meta)

    # Rebuild the corpus-wide manifest/index from all meta files, so incremental
    # fetches keep already-classified repositories visible in the working memory.
    manifest_by_name = {item["nameWithOwner"]: item for item in load_all_meta(meta_dir)}
    for item in inventory:
        name = item["nameWithOwner"]
        if name not in manifest_by_name and name not in selected_names:
            slug = safe_slug(name)
            meta_path = meta_dir / f"{slug}.json"
            readme_path = raw_dir / f"{slug}.md"
            fetch_result = {
                "status": "unfetched",
                "fetchStatus": "unfetched",
                "bytes": readme_path.stat().st_size if readme_path.exists() else 0,
                "error": None,
                "attemptedAt": None,
            }
            meta = merge_meta(item, {}, readme_path, fetch_result)
            write_json(meta_path, meta)
            manifest_by_name[name] = meta

    manifest = [manifest_by_name[item["nameWithOwner"]] for item in inventory if item["nameWithOwner"] in manifest_by_name]
    readme_index = build_readme_index(manifest, raw_dir, meta_dir)

    summary = {
        "generatedAt": utc_now(),
        "inventoryTotal": len(inventory),
        "selected": len(selected),
        "corpusTotal": len(manifest),
        "fetched": fetched,
        "missing": missing,
        "staleRetained": stale_retained,
        "failed": len(failed),
        "failedRepos": failed,
    }

    write_json(out_dir / "manifest.json", manifest)
    write_json(out_dir / "summary.json", summary)
    write_json(out_dir / "readme-index.json", readme_index)

    print(f"Inventory: {len(inventory)} repos")
    print(f"Selected: {len(selected)} repos")
    print(f"Fetched: {fetched}")
    print(f"Missing: {missing}")
    print(f"Stale retained: {stale_retained}")
    print(f"Failed: {len(failed)}")
    print(f"Wrote: {out_dir / 'manifest.json'}")
    print(f"Wrote: {out_dir / 'summary.json'}")
    print(f"Wrote: {out_dir / 'readme-index.json'}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
