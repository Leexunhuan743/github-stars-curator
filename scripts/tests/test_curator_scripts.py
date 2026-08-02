import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


SKILL_DIR = Path(__file__).resolve().parents[2]
APPLY_SCRIPT = SKILL_DIR / "scripts" / "apply_user_lists.py"
README_SCRIPT = SKILL_DIR / "scripts" / "fetch_readmes.py"
INVENTORY_SCRIPT = SKILL_DIR / "scripts" / "fetch_star_inventory.py"
TAXONOMY_PATH = SKILL_DIR / "references" / "taxonomy-template.yaml"


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_readme_meta_merge_preserves_classification_fields(tmp_path):
    readmes = load_module(README_SCRIPT, "fetch_readmes_for_test")
    readme_path = tmp_path / "raw" / "owner__repo.md"
    previous = {
        "nameWithOwner": "owner/repo",
        "summary": "Manual summary",
        "finalLists": ["downloaders"],
        "reason": "Already reviewed",
        "confidence": "high",
        "status": "reviewed",
    }
    repo_item = {
        "nameWithOwner": "owner/repo",
        "description": "New upstream description",
    }
    fetch_result = {
        "status": "ok",
        "fetchStatus": "ok",
        "bytes": 12,
        "error": None,
        "attemptedAt": "2026-01-01T00:00:00+00:00",
    }

    merged = readmes.merge_meta(repo_item, previous, readme_path, fetch_result)

    assert merged["summary"] == "Manual summary"
    assert merged["finalLists"] == ["downloaders"]
    assert merged["reason"] == "Already reviewed"
    assert merged["description"] == "New upstream description"
    assert merged["readmeStatus"] == "ok"
    assert merged["fetchStatus"] == "ok"
    assert merged["classificationStatus"] == "reviewed"
    assert "status" not in merged


def test_stale_readme_result_keeps_old_file_semantics(tmp_path):
    readmes = load_module(README_SCRIPT, "fetch_readmes_for_stale_test")
    readme_path = tmp_path / "owner__repo.md"
    readme_path.write_text("old body", encoding="utf-8")
    fetch_result = {
        "status": "stale-but-retained",
        "fetchStatus": "network_failed",
        "bytes": readme_path.stat().st_size,
        "error": "connection failed",
        "attemptedAt": "2026-01-01T00:00:00+00:00",
    }

    merged = readmes.merge_meta({"nameWithOwner": "owner/repo"}, {}, readme_path, fetch_result)

    assert merged["readmeStatus"] == "stale-but-retained"
    assert merged["fetchStatus"] == "network_failed"
    assert merged["staleReason"] == "network_failed"


def test_incremental_readme_run_preserves_full_manifest_and_enrichment(
    tmp_path, monkeypatch
):
    readmes = load_module(README_SCRIPT, "fetch_readmes_incremental_test")
    out_dir = tmp_path / "corpus"
    inventory_one = tmp_path / "inventory-one.json"
    inventory_two = tmp_path / "inventory-two.json"
    delta = tmp_path / "delta.json"
    inventory_one.write_text(
        json.dumps(
            {
                "ownerLogin": "viewer",
                "repositories": [
                    {"id": "R1", "nameWithOwner": "owner/one"}
                ],
            }
        ),
        encoding="utf-8",
    )
    inventory_two.write_text(
        json.dumps(
            {
                "ownerLogin": "viewer",
                "repositories": [
                    {"id": "R1", "nameWithOwner": "owner/one"},
                    {"id": "R2", "nameWithOwner": "owner/two"},
                ],
            }
        ),
        encoding="utf-8",
    )
    delta.write_text(json.dumps({"newStars": ["owner/two"]}), encoding="utf-8")
    monkeypatch.setattr(
        readmes, "fetch_readme", lambda owner, repo: f"# {repo}"
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "fetch_readmes.py",
            "--inventory",
            str(inventory_one),
            "--out-dir",
            str(out_dir),
        ],
    )
    readmes.main()
    first_meta_path = out_dir / "meta" / "owner__one.json"
    first_meta = json.loads(first_meta_path.read_text(encoding="utf-8"))
    first_meta["summary"] = "Manual summary"
    first_meta["classificationStatus"] = "reviewed"
    readmes.write_json(first_meta_path, first_meta)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "fetch_readmes.py",
            "--inventory",
            str(inventory_two),
            "--out-dir",
            str(out_dir),
            "--only-new-from",
            str(delta),
        ],
    )
    readmes.main()

    manifest = json.loads(
        (out_dir / "manifest.json").read_text(encoding="utf-8")
    )
    preserved = json.loads(first_meta_path.read_text(encoding="utf-8"))
    assert [item["nameWithOwner"] for item in manifest] == [
        "owner/one",
        "owner/two",
    ]
    assert preserved["summary"] == "Manual summary"
    assert preserved["classificationStatus"] == "reviewed"


def test_inventory_output_binds_owner_login(tmp_path, monkeypatch):
    inventory_module = load_module(
        INVENTORY_SCRIPT, "fetch_star_inventory_owner_test"
    )
    monkeypatch.setattr(
        inventory_module,
        "fetch_starred_repositories",
        lambda login=None: (
            "viewer",
            [
                {
                    "id": "R1",
                    "nameWithOwner": "owner/repo",
                    "starredAt": "2026-01-01T00:00:00Z",
                }
            ],
        ),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["fetch_star_inventory.py", "--out-dir", str(tmp_path)],
    )

    inventory_module.main()

    payload = json.loads(
        (tmp_path / "github-stars.json").read_text(encoding="utf-8")
    )
    assert payload["schemaVersion"] == 2
    assert payload["ownerLogin"] == "viewer"
    assert payload["repositories"][0]["id"] == "R1"


def test_unknown_lists_are_rejected_by_default():
    apply_lists = load_module(APPLY_SCRIPT, "apply_lists_unknown_test")
    taxonomy = apply_lists.load_taxonomy(TAXONOMY_PATH)

    try:
        apply_lists.ordered_list_names(["new-random-bucket"], taxonomy)
    except ValueError as exc:
        assert "Unknown list names" in str(exc)
    else:
        raise AssertionError("unknown list should be rejected")


def test_preserves_unmanaged_lists_and_skips_unchanged_repo():
    apply_lists = load_module(APPLY_SCRIPT, "apply_lists_preserve_test")
    taxonomy = apply_lists.load_taxonomy(TAXONOMY_PATH)
    description = taxonomy["descriptions"]["downloaders"]
    existing = {
        "downloaders": {"id": "L1", "name": "downloaders", "description": description},
        "custom": {"id": "L2", "name": "custom", "description": ""},
    }
    memberships = {"owner/repo": [existing["downloaders"], existing["custom"]]}

    plan = apply_lists.build_plan(
        [{"nameWithOwner": "owner/repo", "finalLists": ["downloaders"]}],
        [{"id": "R1", "nameWithOwner": "owner/repo"}],
        taxonomy,
        existing_by_name=existing,
        memberships=memberships,
    )
    repo_plan = plan["repoUpdates"][0]

    assert repo_plan["needsUpdate"] is False
    assert repo_plan["preservedUnmanagedLists"] == ["custom"]
    assert apply_lists.list_ids_for_repo(repo_plan, existing, False) == ["L2", "L1"]


def test_allowed_unknown_list_is_managed_for_current_run():
    apply_lists = load_module(APPLY_SCRIPT, "apply_lists_allowed_unknown_test")
    taxonomy = apply_lists.load_taxonomy(TAXONOMY_PATH)
    existing = {"custom": {"id": "L2", "name": "custom", "description": ""}}
    memberships = {"owner/repo": [existing["custom"]]}

    plan = apply_lists.build_plan(
        [{"nameWithOwner": "owner/repo", "finalLists": ["custom"]}],
        [{"id": "R1", "nameWithOwner": "owner/repo"}],
        taxonomy,
        existing_by_name=existing,
        memberships=memberships,
        allow_unknown=True,
    )
    repo_plan = plan["repoUpdates"][0]

    assert plan["unknownLists"] == ["custom"]
    assert repo_plan["currentManagedLists"] == ["custom"]
    assert repo_plan["preservedUnmanagedLists"] == []
    assert apply_lists.list_ids_for_repo(repo_plan, existing, False) == ["L2"]


def test_apply_requires_approved_plan(tmp_path):
    mapping = tmp_path / "ledger.json"
    inventory = tmp_path / "inventory.json"
    mapping.write_text('[{"nameWithOwner":"owner/repo","finalLists":["downloaders"]}]', encoding="utf-8")
    inventory.write_text('[{"id":"R1","nameWithOwner":"owner/repo"}]', encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(APPLY_SCRIPT),
            "--mapping",
            str(mapping),
            "--inventory",
            str(inventory),
            "--out-dir",
            str(tmp_path),
            "--apply",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 1
    assert "--apply requires --approved-plan" in result.stderr


def write_inventory(path, owner="viewer", repo_id="R1"):
    path.write_text(
        json.dumps(
            {
                "schemaVersion": 2,
                "ownerLogin": owner,
                "repositories": [
                    {"id": repo_id, "nameWithOwner": "owner/repo"}
                ],
            }
        ),
        encoding="utf-8",
    )


def write_mapping(path, final_lists=None):
    path.write_text(
        json.dumps(
            [
                {
                    "nameWithOwner": "owner/repo",
                    "finalLists": final_lists or ["downloaders"],
                }
            ]
        ),
        encoding="utf-8",
    )


def make_approved_plan(apply_lists, mapping, inventory, taxonomy_path, existing, memberships):
    taxonomy = apply_lists.load_taxonomy(taxonomy_path)
    inventory_payload = apply_lists.load_json(inventory)
    repos = apply_lists.normalize_inventory(inventory_payload)
    plan = apply_lists.build_plan(
        apply_lists.load_mapping(mapping),
        repos,
        taxonomy,
        existing_by_name=existing,
        memberships=memberships,
    )
    plan["inventoryOwnerLogin"] = "viewer"
    plan["viewerLogin"] = "viewer"
    apply_lists.finalize_plan(
        plan,
        "plan",
        mapping,
        inventory,
        taxonomy_path,
        True,
    )
    return plan


def test_created_list_is_used_for_repo_update(tmp_path, monkeypatch):
    apply_lists = load_module(APPLY_SCRIPT, "apply_lists_create_then_assign_test")
    mapping = tmp_path / "ledger.json"
    inventory = tmp_path / "inventory.json"
    approved_path = tmp_path / "approved.json"
    write_mapping(mapping)
    write_inventory(inventory)

    approved = make_approved_plan(
        apply_lists, mapping, inventory, TAXONOMY_PATH, {}, {}
    )
    apply_lists.write_json(approved_path, approved)
    mutations = []

    monkeypatch.setattr(
        apply_lists,
        "fetch_viewer_state",
        lambda: {"login": "viewer", "lists": []},
    )
    monkeypatch.setattr(
        apply_lists,
        "fetch_existing_memberships",
        lambda lists, target_repo_names=None: {},
    )
    monkeypatch.setattr(
        apply_lists,
        "create_list",
        lambda name, description: {
            "id": "L1",
            "name": name,
            "description": description,
        },
    )
    monkeypatch.setattr(
        apply_lists,
        "update_item_lists",
        lambda item_id, list_ids: mutations.append((item_id, list_ids)) or [],
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "apply_user_lists.py",
            "--mapping",
            str(mapping),
            "--inventory",
            str(inventory),
            "--out-dir",
            str(tmp_path),
            "--apply",
            "--approved-plan",
            str(approved_path),
        ],
    )

    apply_lists.main()

    summary = json.loads(
        (tmp_path / "github-stars-writeback-summary.json").read_text(
            encoding="utf-8"
        )
    )
    assert mutations == [("R1", ["L1"])]
    assert summary["createdLists"] == ["downloaders"]
    assert summary["updatedRepos"] == 1
    assert summary["skippedReposWithMissingLists"] == 0


def test_partial_apply_writes_summary_then_exits_nonzero(tmp_path, monkeypatch):
    apply_lists = load_module(APPLY_SCRIPT, "apply_lists_partial_failure_test")
    mapping = tmp_path / "ledger.json"
    inventory = tmp_path / "inventory.json"
    approved_path = tmp_path / "approved.json"
    write_mapping(mapping)
    write_inventory(inventory)
    approved = make_approved_plan(
        apply_lists, mapping, inventory, TAXONOMY_PATH, {}, {}
    )
    apply_lists.write_json(approved_path, approved)

    monkeypatch.setattr(
        apply_lists,
        "fetch_viewer_state",
        lambda: {"login": "viewer", "lists": []},
    )
    monkeypatch.setattr(
        apply_lists,
        "fetch_existing_memberships",
        lambda lists, target_repo_names=None: {},
    )

    def fail_create(name, description):
        raise RuntimeError("creation failed")

    monkeypatch.setattr(apply_lists, "create_list", fail_create)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "apply_user_lists.py",
            "--mapping",
            str(mapping),
            "--inventory",
            str(inventory),
            "--out-dir",
            str(tmp_path),
            "--apply",
            "--approved-plan",
            str(approved_path),
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        apply_lists.main()

    assert exc_info.value.code == 2
    summary = json.loads(
        (tmp_path / "github-stars-writeback-summary.json").read_text(
            encoding="utf-8"
        )
    )
    assert summary["failedRepos"]
    assert summary["skippedReposWithMissingLists"] == 1


def test_plan_hash_binds_repo_id_and_taxonomy_bytes(tmp_path):
    apply_lists = load_module(APPLY_SCRIPT, "apply_lists_hash_integrity_test")
    mapping = tmp_path / "ledger.json"
    inventory = tmp_path / "inventory.json"
    taxonomy_path = tmp_path / "taxonomy.yaml"
    write_mapping(mapping, ["custom"])
    write_inventory(inventory, repo_id="R1")
    taxonomy_path.write_text(
        "version: 1\nmaxLists: 32\nlists:\n"
        "  - name: custom\n    description: Description A\n",
        encoding="utf-8",
    )
    plan_a = make_approved_plan(
        apply_lists, mapping, inventory, taxonomy_path, {}, {}
    )

    write_inventory(inventory, repo_id="R2")
    plan_repo_changed = make_approved_plan(
        apply_lists, mapping, inventory, taxonomy_path, {}, {}
    )
    assert plan_repo_changed["planHash"] != plan_a["planHash"]

    write_inventory(inventory, repo_id="R1")
    taxonomy_path.write_text(
        "version: 1\nmaxLists: 32\nlists:\n"
        "  - name: custom\n    description: Description B\n",
        encoding="utf-8",
    )
    plan_taxonomy_changed = make_approved_plan(
        apply_lists, mapping, inventory, taxonomy_path, {}, {}
    )
    assert plan_taxonomy_changed["planHash"] != plan_a["planHash"]


def test_approved_plan_rejects_tampered_content(tmp_path):
    apply_lists = load_module(APPLY_SCRIPT, "apply_lists_tampered_plan_test")
    mapping = tmp_path / "ledger.json"
    inventory = tmp_path / "inventory.json"
    approved_path = tmp_path / "approved.json"
    write_mapping(mapping)
    write_inventory(inventory)
    approved = make_approved_plan(
        apply_lists, mapping, inventory, TAXONOMY_PATH, {}, {}
    )
    tampered = json.loads(json.dumps(approved))
    tampered["repoUpdates"][0]["finalLists"] = ["dev-tools"]
    apply_lists.write_json(approved_path, tampered)

    with pytest.raises(ValueError, match="content does not match its planHash"):
        apply_lists.verify_approved_plan(approved, approved_path)


def test_replace_all_plan_fetches_and_reports_current_memberships(
    tmp_path, monkeypatch
):
    apply_lists = load_module(APPLY_SCRIPT, "apply_lists_replace_all_test")
    mapping = tmp_path / "ledger.json"
    inventory = tmp_path / "inventory.json"
    write_mapping(mapping)
    write_inventory(inventory)
    taxonomy = apply_lists.load_taxonomy(TAXONOMY_PATH)
    downloaders = {
        "id": "L1",
        "name": "downloaders",
        "description": taxonomy["descriptions"]["downloaders"],
    }
    custom = {"id": "L2", "name": "custom", "description": "Custom"}
    membership_calls = []

    monkeypatch.setattr(
        apply_lists,
        "fetch_viewer_state",
        lambda: {"login": "viewer", "lists": [downloaders, custom]},
    )

    def fetch_memberships(lists, target_repo_names=None):
        membership_calls.append((lists, target_repo_names))
        return {"owner/repo": [custom]}

    monkeypatch.setattr(
        apply_lists, "fetch_existing_memberships", fetch_memberships
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "apply_user_lists.py",
            "--mapping",
            str(mapping),
            "--inventory",
            str(inventory),
            "--out-dir",
            str(tmp_path),
            "--replace-all-lists",
        ],
    )

    apply_lists.main()

    plan = json.loads(
        (tmp_path / "github-stars-sync-plan.json").read_text(encoding="utf-8")
    )
    assert membership_calls
    assert membership_calls[0][1] == ["owner/repo"]
    assert plan["repoUpdates"][0]["currentLists"] == ["custom"]
    assert plan["repoUpdates"][0]["listsToRemove"] == ["custom"]
    assert plan["repoUpdates"][0]["needsUpdate"] is True


def test_assignment_validation_matches_schema_invariants():
    apply_lists = load_module(APPLY_SCRIPT, "apply_lists_schema_test")
    failures = apply_lists.validate_assignments(
        [
            {
                "nameWithOwner": "owner/repo/extra",
                "finalLists": ["downloaders", "downloaders"],
                "confidence": "certain",
            }
        ]
    )
    messages = " ".join(item["error"] for item in failures)
    assert "invalid nameWithOwner" in messages

    duplicate_failures = apply_lists.validate_assignments(
        [
            {
                "nameWithOwner": "owner/repo",
                "finalLists": ["downloaders", "downloaders"],
            }
        ]
    )
    assert any("duplicate list names" in item["error"] for item in duplicate_failures)


def test_mapping_loader_uses_bundled_json_schema(tmp_path):
    apply_lists = load_module(APPLY_SCRIPT, "apply_lists_schema_loader_test")
    mapping = tmp_path / "ledger.json"
    mapping.write_text(
        json.dumps(
            [
                {
                    "nameWithOwner": "owner/repo",
                    "finalLists": [],
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid classification ledger schema"):
        apply_lists.load_mapping(mapping)


def test_membership_cache_requires_matching_viewer_and_list_state(tmp_path):
    apply_lists = load_module(APPLY_SCRIPT, "apply_lists_membership_cache_test")
    cache = tmp_path / "membership-cache.json"
    existing = [{"id": "L1", "name": "downloaders", "description": "A"}]
    memberships = {
        "owner/repo": [
            {"id": "L1", "name": "downloaders", "description": "A"}
        ]
    }

    apply_lists.write_membership_cache(
        cache,
        "viewer",
        existing,
        ["owner/repo"],
        memberships,
    )

    assert apply_lists.load_membership_cache(
        cache,
        "viewer",
        existing,
        ["owner/repo"],
    ) == memberships
    assert apply_lists.load_membership_cache(
        cache,
        "someone-else",
        existing,
        ["owner/repo"],
    ) is None
    assert apply_lists.load_membership_cache(
        cache,
        "viewer",
        [{"id": "L1", "name": "downloaders", "description": "B"}],
        ["owner/repo"],
    ) is None


def test_inventory_owner_mismatch_is_rejected():
    apply_lists = load_module(APPLY_SCRIPT, "apply_lists_owner_test")
    with pytest.raises(ValueError, match="does not match authenticated viewer"):
        apply_lists.verify_inventory_owner("someone-else", "viewer")


WRITE_CLASS_SCRIPT = SKILL_DIR / "scripts" / "write_classification.py"


def test_write_classification_merges_meta_and_emits_ledger(tmp_path):
    writer = load_module(WRITE_CLASS_SCRIPT, "write_classification_merge_test")
    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    meta_dir.joinpath("owner__repo.json").write_text(
        json.dumps(
            {
                "nameWithOwner": "owner/repo",
                "description": "A download manager",
                "readmeStatus": "ok",
                "fetchStatus": "ok",
                "classificationStatus": None,
            }
        ),
        encoding="utf-8",
    )
    apply_lists = load_module(APPLY_SCRIPT, "apply_lists_wc_support_test")
    taxonomy = apply_lists.load_taxonomy(TAXONOMY_PATH)
    ledger_path = tmp_path / "ledger" / "incremental-ledger.json"

    ledger = writer.apply_classifications(
        [
            {
                "nameWithOwner": "owner/repo",
                "finalLists": ["downloaders"],
                "summary": "Multi-threaded download manager.",
                "reason": "README describes queues and resume.",
                "confidence": "high",
            }
        ],
        meta_dir,
        taxonomy,
        ledger_path,
        product_type="test-run",
    )

    assert len(ledger) == 1
    assert ledger[0]["nameWithOwner"] == "owner/repo"
    assert ledger[0]["finalLists"] == ["downloaders"]
    assert ledger[0]["readmePath"] == "star-readmes/raw/owner__repo.md"
    assert ledger[0]["description"] == "A download manager"
    assert ledger[0]["productType"] == "test-run"
    assert ledger[0]["primaryFunction"] == "downloaders"
    assert ledger[0]["classificationStatus"] == "reviewed"
    meta = json.loads(meta_dir.joinpath("owner__repo.json").read_text(encoding="utf-8"))
    assert meta["summary"] == "Multi-threaded download manager."
    assert meta["finalLists"] == ["downloaders"]
    assert meta["reason"] == "README describes queues and resume."
    assert meta["confidence"] == "high"
    assert meta["description"] == "A download manager"
    assert meta["readmeStatus"] == "ok"
    assert meta["facets"] == []


def test_write_classification_rejects_unknown_list(tmp_path):
    writer = load_module(WRITE_CLASS_SCRIPT, "write_classification_unknown_test")
    apply_lists = load_module(APPLY_SCRIPT, "apply_lists_wc_unknown_test")
    taxonomy = apply_lists.load_taxonomy(TAXONOMY_PATH)
    with pytest.raises(ValueError, match="Unknown list names"):
        writer.apply_classifications(
            [{"nameWithOwner": "owner/repo", "finalLists": ["no-such-bucket"]}],
            tmp_path / "meta",
            taxonomy,
            tmp_path / "ledger.json",
        )


def test_write_classification_requires_existing_meta(tmp_path):
    writer = load_module(WRITE_CLASS_SCRIPT, "write_classification_meta_test")
    apply_lists = load_module(APPLY_SCRIPT, "apply_lists_wc_meta_test")
    taxonomy = apply_lists.load_taxonomy(TAXONOMY_PATH)
    with pytest.raises(ValueError, match="Run fetch_readmes.py first"):
        writer.apply_classifications(
            [{"nameWithOwner": "owner/repo", "finalLists": ["downloaders"]}],
            tmp_path / "meta",
            taxonomy,
            tmp_path / "ledger.json",
        )


def test_write_classification_refuses_overwrite_of_different_ledger(tmp_path):
    writer = load_module(WRITE_CLASS_SCRIPT, "write_classification_overwrite_test")
    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    meta_dir.joinpath("owner__repo.json").write_text(
        json.dumps({"nameWithOwner": "owner/repo"}),
        encoding="utf-8",
    )
    apply_lists = load_module(APPLY_SCRIPT, "apply_lists_wc_overwrite_test")
    taxonomy = apply_lists.load_taxonomy(TAXONOMY_PATH)
    records = [{"nameWithOwner": "owner/repo", "finalLists": ["downloaders"]}]
    ledger_path = tmp_path / "ledger.json"
    writer.apply_classifications(records, meta_dir, taxonomy, ledger_path)
    with pytest.raises(ValueError, match="already exists with different content"):
        writer.apply_classifications(
            [{"nameWithOwner": "owner/repo", "finalLists": ["terminal"]}],
            meta_dir,
            taxonomy,
            ledger_path,
        )
    # identical re-run is allowed and stays idempotent
    writer.apply_classifications(records, meta_dir, taxonomy, ledger_path)
    assert len(json.loads(ledger_path.read_text(encoding="utf-8"))) == 1


def test_write_classification_rejects_repo_missing_from_inventory(tmp_path):
    writer = load_module(WRITE_CLASS_SCRIPT, "write_classification_inventory_test")
    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    meta_dir.joinpath("ghost__repo.json").write_text(
        json.dumps({"nameWithOwner": "ghost/repo"}),
        encoding="utf-8",
    )
    apply_lists = load_module(APPLY_SCRIPT, "apply_lists_wc_inventory_test")
    taxonomy = apply_lists.load_taxonomy(TAXONOMY_PATH)
    with pytest.raises(ValueError, match="Refresh the inventory first"):
        writer.apply_classifications(
            [{"nameWithOwner": "ghost/repo", "finalLists": ["downloaders"]}],
            meta_dir,
            taxonomy,
            tmp_path / "ledger.json",
            inventory_names={"owner/repo"},
        )


def test_write_classification_main_writes_ledger_and_meta(tmp_path, monkeypatch):
    writer = load_module(WRITE_CLASS_SCRIPT, "write_classification_main_test")
    meta_dir = tmp_path / "star-readmes" / "meta"
    meta_dir.mkdir(parents=True)
    meta_dir.joinpath("owner__repo.json").write_text(
        json.dumps({"nameWithOwner": "owner/repo", "description": "D"}),
        encoding="utf-8",
    )
    records = tmp_path / "records.json"
    records.write_text(
        json.dumps([{"nameWithOwner": "owner/repo", "finalLists": ["downloaders"]}]),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "write_classification.py",
            "--classifications",
            str(records),
            "--out-dir",
            str(tmp_path),
            "--ledger-name",
            "my-ledger",
        ],
    )
    writer.main()
    ledger = json.loads(
        (tmp_path / "star-readmes" / "my-ledger.json").read_text(encoding="utf-8")
    )
    assert ledger[0]["nameWithOwner"] == "owner/repo"
    assert ledger[0]["finalLists"] == ["downloaders"]
    assert ledger[0]["productType"] == "agent-classified"


def test_write_classification_merge_into_full_replaces_same_name(tmp_path):
    writer = load_module(WRITE_CLASS_SCRIPT, "write_classification_merge_full_test")
    apply_lists = load_module(APPLY_SCRIPT, "apply_lists_wc_merge_full_test")
    taxonomy = apply_lists.load_taxonomy(TAXONOMY_PATH)
    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    for slug in ("owner__repo", "other__repo"):
        meta_dir.joinpath(f"{slug}.json").write_text(
            json.dumps({"nameWithOwner": slug.replace("__", "/")}),
            encoding="utf-8",
        )
    ledger_path = tmp_path / "incremental-ledger.json"
    ledger = writer.apply_classifications(
        [
            {
                "nameWithOwner": "owner/repo",
                "finalLists": ["downloaders"],
                "summary": "New summary",
                "reason": "Reclassified",
            },
            {"nameWithOwner": "other/repo", "finalLists": ["terminal"]},
        ],
        meta_dir,
        taxonomy,
        ledger_path,
    )
    full_path = tmp_path / "complete-classification-ledger.json"
    full_path.write_text(
        json.dumps(
            {
                "assignments": [
                    {
                        "nameWithOwner": "owner/repo",
                        "finalLists": ["terminal"],
                        "summary": "Old summary",
                        "reason": "Old reason",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    replaced, added, total, snapshot_path = writer.merge_into_full(
        full_path, ledger, "incremental-ledger"
    )

    assert (replaced, added, total) == (1, 1, 2)
    assert snapshot_path.exists()
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert snapshot["assignments"][0]["finalLists"] == ["terminal"]
    assert snapshot["assignments"][0]["summary"] == "Old summary"
    merged = json.loads(full_path.read_text(encoding="utf-8"))
    by_name = {item["nameWithOwner"]: item for item in merged["assignments"]}
    assert by_name["owner/repo"]["finalLists"] == ["downloaders"]
    assert by_name["owner/repo"]["summary"] == "New summary"
    assert by_name["owner/repo"]["reason"] == "Reclassified"
    assert by_name["other/repo"]["finalLists"] == ["terminal"]


def test_write_classification_merge_into_full_requires_existing_full(tmp_path):
    writer = load_module(WRITE_CLASS_SCRIPT, "write_classification_merge_missing_test")
    with pytest.raises(ValueError, match="Full ledger not found"):
        writer.merge_into_full(tmp_path / "nope.json", [], "incremental-ledger")
