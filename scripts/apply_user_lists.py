#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError as exc:
    raise SystemExit("ERROR: PyYAML is required. Install it with: python -m pip install pyyaml") from exc


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TAXONOMY_PATH = SKILL_DIR / "references" / "taxonomy-template.yaml"
LEDGER_SCHEMA_PATH = SKILL_DIR / "references" / "classification-ledger.schema.json"
FALLBACK_LIST_DESCRIPTION = "Starred repositories curated by GitHub Stars Curator."
REPO_NAME_PATTERN = re.compile(r"^[^/]+/[^/]+$")


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


def graphql(query, fields=None, arrays=None):
    args = ["api", "graphql", "-f", f"query={query}"]
    for key, value in (fields or {}).items():
        if value is None:
            continue
        args.extend(["-F", f"{key}={value}"])
    for key, values in (arrays or {}).items():
        for value in values:
            args.extend(["-F", f"{key}[]={value}"])
    return json.loads(run_gh(args))


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    path = Path(path)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def append_jsonl(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, ensure_ascii=False, sort_keys=True) + "\n")


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(data):
    encoded = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def choose_taxonomy_path(out_dir, explicit_path=None):
    if explicit_path:
        return Path(explicit_path).resolve()
    workspace_taxonomy = Path(out_dir).resolve() / "taxonomy.yaml"
    if workspace_taxonomy.exists():
        return workspace_taxonomy
    return DEFAULT_TAXONOMY_PATH


def load_taxonomy(path):
    path = Path(path).resolve()
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Taxonomy must be a YAML object: {path}")
    lists = payload.get("lists")
    if not isinstance(lists, list) or not lists:
        raise ValueError("Taxonomy must contain a non-empty 'lists' array.")
    names = []
    descriptions = {}
    for index, item in enumerate(lists, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Taxonomy list #{index} must be an object.")
        name = item.get("name")
        description = item.get("description")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Taxonomy list #{index} is missing a valid name.")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"Taxonomy list '{name}' is missing a valid description.")
        if name in descriptions:
            raise ValueError(f"Duplicate taxonomy list name: {name}")
        names.append(name)
        descriptions[name] = description
    max_lists = int(payload.get("maxLists", 32))
    if len(names) > max_lists:
        raise ValueError(f"Taxonomy defines {len(names)} lists, exceeding maxLists={max_lists}.")
    return {
        "path": str(path),
        "version": payload.get("version", 1),
        "maxLists": max_lists,
        "names": tuple(names),
        "descriptions": descriptions,
    }


def load_mapping(path):
    payload = load_json(path)
    schema_failures = validate_mapping_payload_against_schema(payload)
    if schema_failures:
        preview = "; ".join(
            failure_label(item) + ": " + item["error"]
            for item in schema_failures[:10]
        )
        raise ValueError(f"Invalid classification ledger schema: {preview}")
    if isinstance(payload, list):
        assignments = payload
    elif isinstance(payload, dict) and "assignments" in payload:
        assignments = payload["assignments"]
    else:
        raise ValueError("Mapping file must be a list or an object with an 'assignments' field.")
    if not isinstance(assignments, list):
        raise ValueError("'assignments' must be a list.")
    return assignments


def load_ledger_schema():
    return load_json(LEDGER_SCHEMA_PATH)


def schema_type_name(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, (int, float)):
        return "number"
    return type(value).__name__


def schema_type_matches(value, expected):
    expected_types = expected if isinstance(expected, list) else [expected]
    actual = schema_type_name(value)
    return actual in expected_types


def format_schema_type(expected):
    if isinstance(expected, list):
        return " or ".join(str(item) for item in expected)
    return str(expected)


def failure_label(item):
    if item.get("nameWithOwner"):
        return item["nameWithOwner"]
    if item.get("path"):
        return item["path"]
    if item.get("index") is not None:
        return f"index {item['index']}"
    return "mapping"


def schema_field_error(field, kind, expected=None, actual=None):
    if field == "nameWithOwner":
        return "missing or invalid nameWithOwner"
    if field == "finalLists":
        if kind == "type" or kind == "minItems":
            return "finalLists must be a non-empty list"
        if kind == "uniqueItems":
            return "finalLists contains duplicate list names"
        if kind == "item":
            return "finalLists contains an invalid list name"
    if field == "readmePath" and kind == "type":
        return "readmePath must be a string"
    if field == "confidence" and kind == "enum":
        return "confidence must be high, medium, low, or null"
    if kind == "type":
        return f"expected {format_schema_type(expected)}, got {actual}"
    if kind == "enum":
        allowed = ", ".join("null" if entry is None else str(entry) for entry in expected)
        return f"expected one of: {allowed}"
    return kind


def validate_assignment_against_schema(item, assignment_schema, index):
    failures = []
    path = f"assignments[{index - 1}]"
    if not isinstance(item, dict):
        return [{"path": path, "error": "assignment must be an object"}]
    for field in assignment_schema.get("required", []):
        if field not in item:
            failures.append({"path": f"{path}.{field}", "error": "required field is missing"})
    for field, value in item.items():
        field_schema = assignment_schema.get("properties", {}).get(field)
        if field_schema is None:
            continue
        field_path = f"{path}.{field}"
        if "type" in field_schema and not schema_type_matches(value, field_schema["type"]):
            error = schema_field_error(
                field,
                "type",
                expected=field_schema["type"],
                actual=schema_type_name(value),
            )
            failures.append(
                {
                    "path": field_path,
                    "error": error,
                }
            )
            continue
        if field_schema.get("type") == "string" and "minLength" in field_schema and len(value) < field_schema["minLength"]:
            failures.append({"path": field_path, "error": f"string is shorter than minLength={field_schema['minLength']}"})
        if "pattern" in field_schema and isinstance(value, str) and not re.fullmatch(field_schema["pattern"], value):
            failures.append({"path": field_path, "error": schema_field_error(field, "pattern")})
        if "enum" in field_schema and value not in field_schema["enum"]:
            failures.append({"path": field_path, "error": schema_field_error(field, "enum", expected=field_schema["enum"])})
        if field_schema.get("type") == "array" and isinstance(value, list):
            if "minItems" in field_schema and len(value) < field_schema["minItems"]:
                failures.append({"path": field_path, "error": schema_field_error(field, "minItems")})
            if field_schema.get("uniqueItems") and len(set(json.dumps(entry, sort_keys=True) for entry in value)) != len(value):
                failures.append({"path": field_path, "error": schema_field_error(field, "uniqueItems")})
            item_schema = field_schema.get("items", {})
            if item_schema.get("type"):
                for item_index, entry in enumerate(value):
                    entry_path = f"{field_path}[{item_index}]"
                    if not schema_type_matches(entry, item_schema["type"]):
                        failures.append(
                            {
                                "path": entry_path,
                                "error": schema_field_error(field, "item"),
                            }
                        )
                        continue
                    if item_schema.get("type") == "string" and "minLength" in item_schema and len(entry) < item_schema["minLength"]:
                        failures.append({"path": entry_path, "error": schema_field_error(field, "item")})
    return failures


def validate_mapping_payload_against_schema(payload):
    schema = load_ledger_schema()
    assignment_schema = schema["$defs"]["assignment"]
    if isinstance(payload, list):
        assignments = payload
    elif isinstance(payload, dict) and isinstance(payload.get("assignments"), list):
        assignments = payload["assignments"]
    elif isinstance(payload, dict) and "assignments" not in payload:
        return [{"path": "assignments", "error": "required field is missing"}]
    elif isinstance(payload, dict):
        return [{"path": "assignments", "error": "expected array"}]
    else:
        return [{"path": "mapping", "error": "expected array or object with assignments"}]
    failures = []
    for index, item in enumerate(assignments, start=1):
        failures.extend(validate_assignment_against_schema(item, assignment_schema, index))
    return failures


def validate_assignments(assignments):
    seen = set()
    failures = validate_mapping_payload_against_schema(assignments)
    for index, item in enumerate(assignments, start=1):
        if not isinstance(item, dict):
            continue
        name = item.get("nameWithOwner")
        if not isinstance(name, str):
            continue
        if name in seen:
            failures.append({"nameWithOwner": name, "error": "duplicate assignment"})
        seen.add(name)
    return failures


def normalize_inventory(payload):
    if isinstance(payload, dict) and isinstance(payload.get("repositories"), list):
        payload = payload["repositories"]
    if not isinstance(payload, list):
        raise ValueError("Inventory must be a repo list or an object with a 'repositories' list.")
    seen = set()
    failures = []
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            failures.append({"index": index, "error": "inventory item must be an object"})
            continue
        name = item.get("nameWithOwner")
        repo_id = item.get("id")
        if not isinstance(name, str) or not REPO_NAME_PATTERN.fullmatch(name):
            failures.append({"index": index, "error": "missing or invalid nameWithOwner"})
            continue
        if name in seen:
            failures.append({"nameWithOwner": name, "error": "duplicate inventory item"})
        seen.add(name)
        if not isinstance(repo_id, str) or not repo_id:
            failures.append({"nameWithOwner": name, "error": "missing repository node id"})
    if failures:
        joined = "; ".join(item.get("nameWithOwner", f"index {item.get('index')}") + ": " + item["error"] for item in failures[:10])
        raise ValueError(f"Invalid inventory: {joined}")
    return payload


def inventory_owner_login(payload):
    if not isinstance(payload, dict):
        return None
    owner = payload.get("ownerLogin")
    return owner if isinstance(owner, str) and owner.strip() else None


def verify_inventory_owner(owner_login, viewer_login, allow_unbound=False):
    if not owner_login:
        if allow_unbound:
            return
        raise ValueError(
            "Inventory has no ownerLogin binding. Refresh it with fetch_star_inventory.py, "
            "or use --allow-unbound-inventory only for a reviewed legacy inventory."
        )
    if owner_login.casefold() != viewer_login.casefold():
        raise ValueError(
            f"Inventory owner '{owner_login}' does not match authenticated viewer '{viewer_login}'. "
            "An inventory fetched with --login for another account is read-only and cannot be applied."
        )


def fetch_viewer_state():
    query = """
query {
  viewer {
    login
    lists(first: 100) {
      nodes {
        id
        name
        description
      }
    }
  }
}
"""
    payload = graphql(query)
    viewer = payload["data"]["viewer"]
    return {"login": viewer["login"], "lists": viewer["lists"]["nodes"]}


def fetch_list_items(list_id, target_names=None):
    query = """
query($listId: ID!, $cursor: String) {
  node(id: $listId) {
    ... on UserList {
      items(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          ... on Repository {
            id
            nameWithOwner
          }
        }
      }
    }
  }
}
"""
    cursor = None
    repos = []
    remaining_targets = set(target_names or [])
    while True:
        payload = graphql(query, {"listId": list_id, "cursor": cursor})
        node = payload["data"]["node"]
        if not node:
            raise RuntimeError(f"Could not fetch list items for list id {list_id}")
        items = node["items"]
        repos.extend(
            item
            for item in items["nodes"]
            if item
            and item.get("id")
            and item.get("nameWithOwner")
            and (not remaining_targets or item["nameWithOwner"] in remaining_targets)
        )
        if remaining_targets:
            remaining_targets.difference_update(
                item["nameWithOwner"]
                for item in items["nodes"]
                if item and item.get("nameWithOwner") in remaining_targets
            )
            if not remaining_targets:
                return repos
        if not items["pageInfo"]["hasNextPage"]:
            return repos
        cursor = items["pageInfo"]["endCursor"]


def list_state_fingerprint(existing_lists):
    return stable_hash(
        [
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "description": item.get("description") or "",
            }
            for item in sorted(existing_lists, key=lambda entry: entry.get("id", ""))
        ]
    )


def load_membership_cache(path, viewer_login, existing_lists, target_repo_names):
    path = Path(path)
    if not path.exists():
        return None
    payload = load_json(path)
    if payload.get("viewerLogin", "").casefold() != viewer_login.casefold():
        return None
    if payload.get("listStateFingerprint") != list_state_fingerprint(existing_lists):
        return None
    memberships = payload.get("memberships")
    if not isinstance(memberships, dict):
        return None
    target_repo_names = set(target_repo_names)
    if not target_repo_names.issubset(set(memberships)):
        return None
    return {name: memberships.get(name, []) for name in target_repo_names}


def write_membership_cache(path, viewer_login, existing_lists, target_repo_names, memberships):
    target_repo_names = sorted(set(target_repo_names))
    payload = {
        "schemaVersion": 1,
        "generatedAt": utc_now(),
        "viewerLogin": viewer_login,
        "listStateFingerprint": list_state_fingerprint(existing_lists),
        "repoNames": target_repo_names,
        "memberships": {
            name: memberships.get(name, [])
            for name in target_repo_names
        },
    }
    write_json(path, payload)


def fetch_existing_memberships(existing_lists, target_repo_names=None):
    memberships = {}
    target_repo_names = set(target_repo_names or [])
    for list_item in existing_lists:
        for repo in fetch_list_items(list_item["id"], target_repo_names or None):
            memberships.setdefault(repo["nameWithOwner"], []).append(list_item)
    for name in target_repo_names:
        memberships.setdefault(name, [])
    return memberships


def create_list(name, description):
    query = """
mutation($name: String!, $description: String!) {
  createUserList(input: {name: $name, description: $description}) {
    list {
      id
      name
      description
    }
  }
}
"""
    payload = graphql(query, {"name": name, "description": description})
    return payload["data"]["createUserList"]["list"]


def update_list_description(list_id, name, description):
    query = """
mutation($listId: ID!, $name: String!, $description: String!) {
  updateUserList(input: {listId: $listId, name: $name, description: $description}) {
    list {
      id
      name
      description
    }
  }
}
"""
    payload = graphql(query, {"listId": list_id, "name": name, "description": description})
    return payload["data"]["updateUserList"]["list"]


def ordered_list_names(names, taxonomy, allow_unknown=False):
    requested = []
    for name in names:
        if name not in requested:
            requested.append(name)
    taxonomy_names = set(taxonomy["names"])
    unknown = sorted(name for name in requested if name not in taxonomy_names)
    if unknown and not allow_unknown:
        joined = ", ".join(unknown)
        raise ValueError(
            f"Unknown list names are not part of the managed taxonomy: {joined}. "
            "Update taxonomy.yaml or rerun with --allow-unknown-lists for a transition-only plan."
        )
    ordered = [name for name in taxonomy["names"] if name in requested]
    return ordered + unknown


def build_plan(assignments, inventory, taxonomy, existing_by_name=None, memberships=None, allow_unknown=False, replace_all_lists=False):
    validation_failures = validate_assignments(assignments)
    if validation_failures:
        preview = "; ".join(
            failure_label(item) + ": " + item["error"]
            for item in validation_failures[:10]
        )
        raise ValueError(f"Invalid classification ledger: {preview}")

    repo_ids = {item["nameWithOwner"]: item["id"] for item in inventory}
    raw_desired_lists = {name for item in assignments for name in item.get("finalLists", [])}
    desired_lists = ordered_list_names(raw_desired_lists, taxonomy, allow_unknown=allow_unknown)
    if len(desired_lists) > taxonomy["maxLists"]:
        raise ValueError(f"Refusing to continue: {len(desired_lists)} lists exceed maxLists={taxonomy['maxLists']}.")

    has_online_list_state = existing_by_name is not None
    existing_by_name = existing_by_name or {}
    memberships = memberships or {}
    unknown_lists = [name for name in desired_lists if name not in taxonomy["descriptions"]]
    effective_managed_names = tuple(dict.fromkeys([*taxonomy["names"], *unknown_lists]))
    effective_managed_set = set(effective_managed_names)
    missing_lists = [name for name in desired_lists if name not in existing_by_name] if has_online_list_state else []
    projected_list_count = len(existing_by_name) + len(missing_lists) if has_online_list_state else None
    if (
        has_online_list_state
        and missing_lists
        and projected_list_count > taxonomy["maxLists"]
    ):
        raise ValueError(
            "Refusing to create lists: "
            f"{len(existing_by_name)} existing + {len(missing_lists)} missing "
            f"would exceed maxLists={taxonomy['maxLists']}."
        )
    description_updates = [
        {
            "id": existing_by_name[name]["id"],
            "name": name,
            "currentDescription": existing_by_name[name].get("description") or "",
            "desiredDescription": taxonomy["descriptions"][name],
        }
        for name in desired_lists
        if name in taxonomy["descriptions"]
        and name in existing_by_name
        and (existing_by_name[name].get("description") or "") != taxonomy["descriptions"][name]
    ] if has_online_list_state else []

    plan = {
        "taxonomyPath": taxonomy["path"],
        "taxonomyVersion": taxonomy["version"],
        "taxonomyMaxLists": taxonomy["maxLists"],
        "managedLists": list(taxonomy["names"]),
        "managedListDescriptions": {
            name: taxonomy["descriptions"][name] for name in taxonomy["names"]
        },
        "effectiveManagedLists": list(effective_managed_names),
        "desiredLists": desired_lists,
        "desiredListCount": len(desired_lists),
        "unknownLists": unknown_lists,
        "missingLists": missing_lists,
        "missingListDefinitions": [
            {
                "name": name,
                "description": taxonomy["descriptions"].get(
                    name, FALLBACK_LIST_DESCRIPTION
                ),
            }
            for name in missing_lists
        ],
        "existingListCount": len(existing_by_name) if has_online_list_state else None,
        "projectedListCount": projected_list_count,
        "descriptionUpdates": description_updates,
        "repoUpdates": [],
        "failedRepos": [],
    }

    for item in assignments:
        name = item["nameWithOwner"]
        final_lists = ordered_list_names(item.get("finalLists", []), taxonomy, allow_unknown=allow_unknown)
        current_lists = memberships.get(name, [])
        current_list_names = [entry["name"] for entry in current_lists]
        current_managed = [entry["name"] for entry in current_lists if entry["name"] in effective_managed_set]
        preserved_unmanaged = [] if replace_all_lists else [entry["name"] for entry in current_lists if entry["name"] not in effective_managed_set]
        missing_for_repo = [list_name for list_name in final_lists if list_name not in existing_by_name] if has_online_list_state else []
        managed_to_add = [list_name for list_name in final_lists if list_name not in current_managed]
        managed_to_remove = [list_name for list_name in current_managed if list_name not in final_lists]
        lists_to_remove = (
            [list_name for list_name in current_list_names if list_name not in final_lists]
            if replace_all_lists
            else managed_to_remove
        )
        needs_update = bool(managed_to_add or managed_to_remove or (replace_all_lists and set(current_list_names) != set(final_lists)))
        repo_plan = {
            "nameWithOwner": name,
            "repoId": repo_ids.get(name),
            "repoIdFound": name in repo_ids,
            "finalLists": final_lists,
            "currentLists": current_list_names,
            "currentManagedLists": current_managed,
            "preservedUnmanagedLists": preserved_unmanaged,
            "missingListNames": missing_for_repo,
            "managedListsToAdd": managed_to_add,
            "managedListsToRemove": managed_to_remove,
            "listsToRemove": lists_to_remove,
            "needsUpdate": needs_update,
        }
        plan["repoUpdates"].append(repo_plan)
        if not repo_plan["repoIdFound"]:
            plan["failedRepos"].append({"nameWithOwner": name, "error": "missing repo id in inventory"})
    return plan


def plan_hash_payload(plan):
    return {
        "taxonomyPath": plan.get("taxonomyPath"),
        "taxonomyVersion": plan.get("taxonomyVersion"),
        "taxonomyMaxLists": plan.get("taxonomyMaxLists"),
        "inventoryOwnerLogin": plan.get("inventoryOwnerLogin"),
        "viewerLogin": plan.get("viewerLogin"),
        "managedListDescriptions": plan.get("managedListDescriptions"),
        "managedLists": plan.get("managedLists"),
        "desiredLists": plan.get("desiredLists"),
        "unknownLists": plan.get("unknownLists"),
        "missingLists": plan.get("missingLists"),
        "missingListDefinitions": plan.get("missingListDefinitions"),
        "existingListCount": plan.get("existingListCount"),
        "projectedListCount": plan.get("projectedListCount"),
        "descriptionUpdates": plan.get("descriptionUpdates"),
        "mappingSha256": plan.get("mappingSha256"),
        "inventorySha256": plan.get("inventorySha256"),
        "taxonomySha256": plan.get("taxonomySha256"),
        "preserveUnmanagedLists": plan.get("preserveUnmanagedLists"),
        "repoUpdates": [
            {
                "nameWithOwner": item["nameWithOwner"],
                "repoId": item["repoId"],
                "repoIdFound": item["repoIdFound"],
                "finalLists": item["finalLists"],
                "currentManagedLists": item["currentManagedLists"],
                "preservedUnmanagedLists": item["preservedUnmanagedLists"],
                "missingListNames": item["missingListNames"],
                "managedListsToAdd": item["managedListsToAdd"],
                "managedListsToRemove": item["managedListsToRemove"],
                "listsToRemove": item["listsToRemove"],
                "needsUpdate": item["needsUpdate"],
            }
            for item in plan.get("repoUpdates", [])
        ],
        "failedRepos": plan.get("failedRepos", []),
    }


def finalize_plan(plan, mode, mapping_path, inventory_path, taxonomy_path, preserve_unmanaged_lists):
    plan["mode"] = mode
    plan["generatedAt"] = utc_now()
    plan["mappingPath"] = str(Path(mapping_path).resolve())
    plan["inventoryPath"] = str(Path(inventory_path).resolve())
    plan["taxonomyPath"] = str(Path(taxonomy_path).resolve())
    plan["mappingSha256"] = sha256_file(mapping_path)
    plan["inventorySha256"] = sha256_file(inventory_path)
    plan["taxonomySha256"] = sha256_file(taxonomy_path)
    plan["preserveUnmanagedLists"] = preserve_unmanaged_lists
    plan["planHash"] = stable_hash(plan_hash_payload(plan))
    return plan


def verify_approved_plan(current_plan, approved_plan_path):
    approved = load_json(approved_plan_path)
    if approved.get("mode") != "plan":
        raise ValueError("Approved plan must be an online plan generated without --apply.")
    approved_hash = approved.get("planHash")
    current_hash = current_plan.get("planHash")
    if not approved_hash:
        raise ValueError("Approved plan has no planHash. Regenerate the online plan first.")
    recomputed_approved_hash = stable_hash(plan_hash_payload(approved))
    if approved_hash != recomputed_approved_hash:
        raise ValueError(
            "Approved plan content does not match its planHash. "
            "The plan file may have been edited after review."
        )
    if approved_hash != current_hash:
        raise ValueError(
            "Current plan does not match the approved plan hash. "
            f"approved={approved_hash} current={current_hash}"
        )
    return approved_hash


def update_item_lists(item_id, list_ids):
    query = """
mutation($itemId: ID!, $listIds: [ID!]!) {
  updateUserListsForItem(input: {itemId: $itemId, listIds: $listIds}) {
    lists {
      id
      name
    }
  }
}
"""
    payload = graphql(query, {"itemId": item_id}, {"listIds": list_ids})
    return payload["data"]["updateUserListsForItem"]["lists"]


def list_ids_for_repo(repo_plan, existing_by_name, replace_all_lists):
    list_ids = []
    if not replace_all_lists:
        for list_name in repo_plan["preservedUnmanagedLists"]:
            found = existing_by_name.get(list_name)
            if found and found["id"] not in list_ids:
                list_ids.append(found["id"])
    for list_name in repo_plan["finalLists"]:
        found = existing_by_name.get(list_name)
        if found and found["id"] not in list_ids:
            list_ids.append(found["id"])
    return list_ids


def main():
    parser = argparse.ArgumentParser(description="Plan or apply GitHub user list assignments.")
    parser.add_argument("--mapping", required=True, help="Classification ledger JSON path")
    parser.add_argument("--inventory", required=True, help="Inventory JSON path with repo node IDs")
    parser.add_argument("--out-dir", required=True, help="Directory for plan/apply summaries")
    parser.add_argument("--taxonomy", help="Taxonomy YAML path; defaults to <out-dir>/taxonomy.yaml if present, else bundled template")
    parser.add_argument("--apply", action="store_true", help="Actually create/update GitHub lists")
    parser.add_argument("--offline-plan", action="store_true", help="Write a local validation plan without calling GitHub")
    parser.add_argument("--approved-plan", help="Required with --apply; path to the reviewed online plan JSON")
    parser.add_argument("--allow-unknown-lists", action="store_true", help="Allow lists outside the managed taxonomy for a transition-only run")
    parser.add_argument(
        "--allow-unbound-inventory",
        action="store_true",
        help="Allow a legacy inventory without ownerLogin; never bypasses an explicit owner mismatch",
    )
    parser.add_argument(
        "--replace-all-lists",
        action="store_true",
        help="Replace every list membership for each repo instead of preserving unmanaged lists",
    )
    parser.add_argument(
        "--membership-cache",
        help="Membership cache JSON path; defaults to <out-dir>/github-stars-membership-cache.json",
    )
    parser.add_argument(
        "--use-membership-cache",
        action="store_true",
        help="Use a reviewed membership cache when its viewer and list-state fingerprint still match",
    )
    args = parser.parse_args()

    if args.apply and args.offline_plan:
        raise ValueError("--offline-plan cannot be combined with --apply.")
    if args.apply and not args.approved_plan:
        raise ValueError("--apply requires --approved-plan pointing at a reviewed online plan.")

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    taxonomy_path = choose_taxonomy_path(out_dir, args.taxonomy)
    taxonomy = load_taxonomy(taxonomy_path)
    assignments = load_mapping(args.mapping)
    inventory_payload = load_json(args.inventory)
    inventory_owner = inventory_owner_login(inventory_payload)
    inventory = normalize_inventory(inventory_payload)

    if args.offline_plan:
        plan = build_plan(
            assignments,
            inventory,
            taxonomy,
            allow_unknown=args.allow_unknown_lists,
            replace_all_lists=args.replace_all_lists,
        )
        plan["inventoryOwnerLogin"] = inventory_owner
        plan["viewerLogin"] = None
        finalize_plan(plan, "offline-plan", args.mapping, args.inventory, taxonomy_path, not args.replace_all_lists)
        write_json(out_dir / "github-stars-sync-plan.json", plan)
        print(f"Validated {len(plan['repoUpdates'])} repo assignments without calling GitHub.")
        print(f"Desired lists: {plan['desiredListCount']}")
        print(f"Unknown lists: {len(plan['unknownLists'])}")
        print(f"Failed repos: {len(plan['failedRepos'])}")
        print(f"Plan hash: {plan['planHash']}")
        print(f"Wrote: {out_dir / 'github-stars-sync-plan.json'}")
        return

    viewer_state = fetch_viewer_state()
    verify_inventory_owner(
        inventory_owner,
        viewer_state["login"],
        allow_unbound=args.allow_unbound_inventory,
    )
    existing_lists = viewer_state["lists"]
    existing_by_name = {item["name"]: item for item in existing_lists}
    target_repo_names = [item["nameWithOwner"] for item in assignments]
    membership_cache_path = Path(args.membership_cache).resolve() if args.membership_cache else out_dir / "github-stars-membership-cache.json"
    memberships = None
    if args.use_membership_cache:
        memberships = load_membership_cache(
            membership_cache_path,
            viewer_state["login"],
            existing_lists,
            target_repo_names,
        )
    if memberships is None:
        memberships = fetch_existing_memberships(existing_lists, target_repo_names)
        write_membership_cache(
            membership_cache_path,
            viewer_state["login"],
            existing_lists,
            target_repo_names,
            memberships,
        )
    plan = build_plan(
        assignments,
        inventory,
        taxonomy,
        existing_by_name=existing_by_name,
        memberships=memberships,
        allow_unknown=args.allow_unknown_lists,
        replace_all_lists=args.replace_all_lists,
    )
    plan["inventoryOwnerLogin"] = inventory_owner
    plan["viewerLogin"] = viewer_state["login"]
    finalize_plan(plan, "apply" if args.apply else "plan", args.mapping, args.inventory, taxonomy_path, not args.replace_all_lists)

    if not args.apply:
        write_json(out_dir / "github-stars-sync-plan.json", plan)
        print(f"Planned {len(plan['repoUpdates'])} repo assignments.")
        print(f"Repos needing update: {sum(1 for item in plan['repoUpdates'] if item['needsUpdate'])}")
        print(f"Missing lists: {len(plan['missingLists'])}")
        print(f"Description updates: {len(plan['descriptionUpdates'])}")
        print(f"Plan hash: {plan['planHash']}")
        print(f"Wrote: {out_dir / 'github-stars-sync-plan.json'}")
        return

    approved_hash = verify_approved_plan(plan, args.approved_plan)
    journal_path = out_dir / "github-stars-writeback-journal.jsonl"
    run_id = f"{utc_now()}-{uuid.uuid4().hex[:12]}"
    journal_context = {"runId": run_id, "planHash": approved_hash}
    created_lists = []
    description_updates = []
    failures = list(plan["failedRepos"])

    for list_name in plan["missingLists"]:
        event = {
            **journal_context,
            "time": utc_now(),
            "operation": "createList",
            "name": list_name,
            "status": "started",
        }
        append_jsonl(journal_path, event)
        try:
            created = create_list(list_name, taxonomy["descriptions"].get(list_name, FALLBACK_LIST_DESCRIPTION))
            existing_by_name[list_name] = created
            created_lists.append(list_name)
            append_jsonl(journal_path, {**event, "time": utc_now(), "status": "ok", "created": created})
        except Exception as exc:
            failure = {"name": list_name, "error": str(exc)}
            failures.append({"list": failure, "error": "create list failed"})
            append_jsonl(journal_path, {**event, "time": utc_now(), "status": "failed", "error": str(exc)})

    for update in plan["descriptionUpdates"]:
        event = {
            **journal_context,
            "time": utc_now(),
            "operation": "updateDescription",
            "name": update["name"],
            "status": "started",
            "before": update["currentDescription"],
            "after": update["desiredDescription"],
        }
        append_jsonl(journal_path, event)
        try:
            updated_list = update_list_description(update["id"], update["name"], update["desiredDescription"])
            existing_by_name[update["name"]] = updated_list
            description_updates.append(update["name"])
            append_jsonl(journal_path, {**event, "time": utc_now(), "status": "ok", "updated": updated_list})
        except Exception as exc:
            failures.append({"list": update["name"], "error": str(exc)})
            append_jsonl(journal_path, {**event, "time": utc_now(), "status": "failed", "error": str(exc)})

    repo_ids = {item["nameWithOwner"]: item["id"] for item in inventory}
    updated = 0
    skipped_unchanged = 0
    skipped_missing = 0
    for repo_plan in plan["repoUpdates"]:
        name = repo_plan["nameWithOwner"]
        repo_id = repo_ids.get(name)
        if not repo_id:
            continue
        unresolved_lists = [
            list_name
            for list_name in repo_plan["finalLists"]
            if list_name not in existing_by_name
        ]
        if unresolved_lists:
            skipped_missing += 1
            failures.append(
                {
                    "nameWithOwner": name,
                    "error": "required lists could not be created",
                    "missingLists": unresolved_lists,
                }
            )
            continue
        if not repo_plan["needsUpdate"]:
            skipped_unchanged += 1
            continue
        list_ids = list_ids_for_repo(repo_plan, existing_by_name, args.replace_all_lists)
        event = {
            **journal_context,
            "time": utc_now(),
            "operation": "updateRepoLists",
            "nameWithOwner": name,
            "status": "started",
            "before": repo_plan["currentLists"],
            "after": [*repo_plan["preservedUnmanagedLists"], *repo_plan["finalLists"]],
            "listIds": list_ids,
        }
        append_jsonl(journal_path, event)
        try:
            result_lists = update_item_lists(repo_id, list_ids)
            updated += 1
            append_jsonl(journal_path, {**event, "time": utc_now(), "status": "ok", "resultLists": result_lists})
        except Exception as exc:
            failures.append({"nameWithOwner": name, "error": str(exc)})
            append_jsonl(journal_path, {**event, "time": utc_now(), "status": "failed", "error": str(exc)})

    summary = {
        "generatedAt": utc_now(),
        "runId": run_id,
        "approvedPlanPath": str(Path(args.approved_plan).resolve()),
        "approvedPlanHash": approved_hash,
        "inventoryOwnerLogin": inventory_owner,
        "viewerLogin": viewer_state["login"],
        "desiredListCount": plan["desiredListCount"],
        "createdLists": created_lists,
        "descriptionUpdates": description_updates,
        "preserveUnmanagedLists": not args.replace_all_lists,
        "updatedRepos": updated,
        "skippedUnchangedRepos": skipped_unchanged,
        "skippedReposWithMissingLists": skipped_missing,
        "failedRepos": failures,
        "journalPath": str(journal_path),
    }
    write_json(out_dir / "github-stars-writeback-summary.json", summary)
    print(f"Updated repos: {updated}")
    print(f"Skipped unchanged repos: {skipped_unchanged}")
    print(f"Failures: {len(failures)}")
    print(f"Wrote: {out_dir / 'github-stars-writeback-summary.json'}")
    print(f"Journal: {journal_path}")
    if failures or skipped_missing:
        raise SystemExit(2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
