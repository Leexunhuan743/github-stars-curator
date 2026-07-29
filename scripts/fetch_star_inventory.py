#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


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


def graphql(query, fields=None):
    args = ["api", "graphql", "-f", f"query={query}"]
    for key, value in (fields or {}).items():
        if value is None:
            continue
        args.extend(["-F", f"{key}={value}"])
    return json.loads(run_gh(args))


def fetch_starred_repositories(login=None):
    if login:
        query = """
query($cursor: String, $login: String!) {
  user(login: $login) {
    login
    starredRepositories(first: 100, after: $cursor, orderBy: {field: STARRED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        nameWithOwner
        url
        description
        isArchived
        isFork
        stargazerCount
        pushedAt
        updatedAt
        primaryLanguage { name }
        repositoryTopics(first: 12) { nodes { topic { name } } }
      }
      edges {
        starredAt
      }
    }
  }
}
"""
    else:
        query = """
query($cursor: String) {
  viewer {
    login
    starredRepositories(first: 100, after: $cursor, orderBy: {field: STARRED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        nameWithOwner
        url
        description
        isArchived
        isFork
        stargazerCount
        pushedAt
        updatedAt
        primaryLanguage { name }
        repositoryTopics(first: 12) { nodes { topic { name } } }
      }
      edges {
        starredAt
      }
    }
  }
}
"""

    cursor = None
    repos = []
    owner_login = None
    while True:
        payload = graphql(query, {"cursor": cursor, "login": login})
        owner = payload["data"]["user" if login else "viewer"]
        if not owner:
            raise RuntimeError(f"Could not resolve GitHub user: {login}")
        owner_login = owner["login"]
        root = owner["starredRepositories"]
        nodes = root["nodes"]
        edges = root["edges"]
        for node, edge in zip(nodes, edges):
            repos.append(
                {
                    "id": node["id"],
                    "nameWithOwner": node["nameWithOwner"],
                    "url": node["url"],
                    "description": node.get("description"),
                    "primaryLanguage": (node.get("primaryLanguage") or {}).get("name"),
                    "topics": [
                        item["topic"]["name"]
                        for item in node.get("repositoryTopics", {}).get("nodes", [])
                        if item.get("topic") and item["topic"].get("name")
                    ],
                    "isArchived": bool(node.get("isArchived")),
                    "isFork": bool(node.get("isFork")),
                    "stargazerCount": node.get("stargazerCount"),
                    "pushedAt": node.get("pushedAt"),
                    "updatedAt": node.get("updatedAt"),
                    "starredAt": edge.get("starredAt"),
                }
            )
        if not root["pageInfo"]["hasNextPage"]:
            break
        cursor = root["pageInfo"]["endCursor"]
    return owner_login, repos


def load_previous(path):
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("repositories"), list):
        return payload["repositories"]
    raise ValueError("Previous inventory must be a repo list or an object with a 'repositories' list.")


def build_delta(previous, current):
    old_names = {item["nameWithOwner"] for item in previous}
    new_names = {item["nameWithOwner"] for item in current}
    new_stars = sorted(new_names - old_names)
    removed = sorted(old_names - new_names)
    unchanged = sorted(old_names & new_names)
    return {
        "newStars": new_stars,
        "removedStars": removed,
        "unchangedCount": len(unchanged),
        "previousCount": len(previous),
        "currentCount": len(current),
    }


def write_json(path, data):
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def main():
    parser = argparse.ArgumentParser(description="Fetch GitHub starred repositories and compute delta.")
    parser.add_argument("--out-dir", required=True, help="Directory for output JSON files")
    parser.add_argument(
        "--login",
        help="GitHub login to inspect; another user's inventory is read-only for apply",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    stars_path = out_dir / "github-stars.json"
    delta_path = out_dir / "github-stars-delta.json"
    summary_path = out_dir / "github-stars-summary.json"

    previous = load_previous(stars_path)
    owner_login, current = fetch_starred_repositories(login=args.login)
    current.sort(key=lambda item: item["starredAt"] or "", reverse=True)
    delta = build_delta(previous, current)
    generated_at = datetime.now(timezone.utc).isoformat()

    write_json(
        stars_path,
        {
            "schemaVersion": 2,
            "generatedAt": generated_at,
            "ownerLogin": owner_login,
            "repositories": current,
        },
    )
    write_json(delta_path, delta)
    write_json(
        summary_path,
        {
            "generatedAt": generated_at,
            "login": owner_login,
            "total": len(current),
            **delta,
        },
    )

    print(f"Fetched {len(current)} starred repositories.")
    print(f"New stars: {len(delta['newStars'])}")
    print(f"Removed stars: {len(delta['removedStars'])}")
    print(f"Wrote: {stars_path}")
    print(f"Wrote: {delta_path}")
    print(f"Wrote: {summary_path}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
