---
name: github-stars-curator
description: Curate GitHub starred repositories into stable, meaningful user lists by detecting new stars, downloading READMEs into a local corpus, enriching per-repo metadata, refining taxonomy decisions, and syncing the final mapping back to GitHub via gh or a browser fallback. Use this when a user wants their starred repos reviewed, reorganized, incrementally maintained, or promoted into existing or newly created GitHub star lists.
---

# GitHub Stars Curator

## Overview

This skill turns a pile of GitHub stars into a maintained catalog: local README corpus, enriched per-repo metadata, a curated taxonomy, and synchronized GitHub user lists.

Prefer this skill when the user says things like:

- "Sort my starred repos into lists."
- "Check what I starred recently and file the new ones."
- "Pull all starred repo READMEs locally, read them, and update the categories."
- "Create or refine my GitHub star lists."

Read references only when the task needs them:

- Read `references/workflow.md` for inventory refreshes, README fetching, local corpus maintenance, or end-to-end runs.
- Read `references/taxonomy-rubric.md` when classifying repositories, refining buckets, or explaining list placement.
- Read `references/github-graphql-notes.md` only before online plan/apply work or browser fallback.
- Use `references/taxonomy-template.yaml` as the bundled machine-readable taxonomy. If `<workspace>/taxonomy.yaml` exists, scripts use that workspace taxonomy instead.

## Preconditions

1. Prefer `gh` first. Use the browser only if `gh` is unavailable, under-scoped, or cannot perform a required mutation.
2. Verify `gh auth status` before any writeback. For GitHub star list mutations, the token needs a scope set that includes `user`.
3. Treat the local corpus and ledger as the working memory, but treat GitHub as the final source of truth for list membership after writeback.
4. Assume classification is iterative. New or ambiguous repos can stay in a broad holding list such as `misc-explore` until the next pass.
5. Before any online writeback, proactively check for cloud drift even if the user did not mention manual edits. Read live GitHub memberships, compare them with the local ledger, and treat live memberships as newer when they differ. Reconcile the local plan with cloud drift, or use a narrow incremental ledger that preserves each target repo's current live lists. Do not apply an old full ledger over possible manual cloud edits.
6. If the user asks for local-only skill work, taxonomy design, or offline review, do not access GitHub or the browser.
7. `scripts/apply_user_lists.py` requires PyYAML. If it is missing, install it with `python -m pip install pyyaml`.
8. Ledger shape is validated from `references/classification-ledger.schema.json`; keep that schema as the source for assignment field rules.

## Default Workspace Layout

Unless the user specifies another path, create or reuse a workspace folder like:

```text
<cwd>/
  star-readmes/
    raw/
    meta/
    manifest.json
    summary.json
    readme-index.json
    classification-ledger.json
    final-star-taxonomy.md
  github-stars.json
  github-stars-delta.json
  taxonomy.yaml
  github-stars-writeback-summary.json
  github-stars-writeback-journal.jsonl
```

Use dated snapshots or suffixed filenames when preserving history matters.

## Workflow

### 1. Refresh the star inventory

Run `scripts/fetch_star_inventory.py` to fetch the full starred-repo inventory and compute a delta against the previous snapshot.

Recommended command:

```bash
python scripts/fetch_star_inventory.py --out-dir "<workspace>"
```

Outputs:

- `github-stars.json`
- `github-stars-delta.json`
- `github-stars-summary.json`

If the user asked for incremental maintenance, focus first on the repos in `newStars`.

The inventory records `ownerLogin`. Inventories fetched with `--login` for another account are read-only for classification; online plan/apply refuses to use them against a different authenticated viewer.

### 2. Pull README files into a local corpus

Run `scripts/fetch_readmes.py` against the inventory. This downloads the canonical GitHub README for each repo and writes a compact per-repo metadata stub.

Recommended command:

```bash
python scripts/fetch_readmes.py --inventory "<workspace>/github-stars.json" --out-dir "<workspace>/star-readmes"
```

Optional incremental command:

```bash
python scripts/fetch_readmes.py --inventory "<workspace>/github-stars.json" --out-dir "<workspace>/star-readmes" --only-new-from "<workspace>/github-stars-delta.json"
```

`readmeStatus` values can include `ok`, `missing`, `rate_limited`, `network_failed`, `api_failed`, `stale-but-retained`, or `unfetched`. `fetchStatus` records the direct outcome of the latest fetch attempt. Treat `missing` as a repo/content condition, treat `stale-but-retained` as an old local README whose refresh failed, and treat rate/network/API failures as retry or environment conditions.

### 3. Read README content and enrich metadata

Use the README corpus plus repo metadata to build or refine classification fields for each project. The agent should read the README, not just the repository description.

For each repo, enrich or confirm:

- `summary`
- `productType`
- `primaryFunction`
- `facets`
- `platforms`
- `signals`
- `candidateLists`
- `finalLists`
- `confidence`
- `reason`
- `classificationStatus`

When the README and metadata disagree, prefer the README.

### 4. Refine the taxonomy

Use `references/taxonomy-template.yaml` or `<workspace>/taxonomy.yaml` as the machine source of truth for list names, order, descriptions, and max list count. Use `references/taxonomy-rubric.md` as the human decision rubric. Do not create a new list just because one repo is slightly different. New lists are justified only when:

- the bucket has a stable concept,
- at least a few repos belong there now or obviously soon,
- the distinction matters for later retrieval,
- the GitHub list cap still leaves room.

If the taxonomy would exceed 32 lists, merge the lowest-value or most overlapping buckets before writeback.

When a user's taxonomy should differ from the bundled template, copy `references/taxonomy-template.yaml` to `<workspace>/taxonomy.yaml` and edit the workspace copy. Avoid modifying the installed skill just to add a local custom list during ordinary curation.

### 5. Produce a classification ledger

Maintain a JSON ledger that can be reviewed and diffed. A good record shape is:

```json
{
  "nameWithOwner": "owner/repo",
  "finalLists": ["list-a", "list-b"],
  "readmePath": "C:\\path\\to\\README.md",
  "description": "Short repo description",
  "summary": "1-3 sentence summary based on the README",
  "primaryFunction": "download",
  "facets": ["windows", "self-hosted"],
  "reason": "Why these lists fit",
  "confidence": "high",
  "classificationStatus": "reviewed"
}
```

Also generate a human-readable taxonomy summary so the user can audit list intent quickly.

### 6. Plan and sync the final mapping

Run `scripts/apply_user_lists.py` in offline plan mode first. This validates the ledger against the managed taxonomy without contacting GitHub.

```bash
python scripts/apply_user_lists.py --mapping "<workspace>/star-readmes/classification-ledger.json" --inventory "<workspace>/github-stars.json" --out-dir "<workspace>" --offline-plan
```

Then run online plan mode. This checks existing GitHub lists, stale descriptions, missing lists, and current list membership before mutation. Review the generated `planHash`.

```bash
python scripts/apply_user_lists.py --mapping "<workspace>/star-readmes/classification-ledger.json" --inventory "<workspace>/github-stars.json" --out-dir "<workspace>"
```

Online plan writes `<workspace>/github-stars-membership-cache.json` after a live membership read. It uses live GitHub data by default on each run. Use `--use-membership-cache` only for a reviewed rerun when the cache viewer and list-state fingerprint still match; this avoids accidentally preserving stale list memberships.

Before applying, do not jump from a local full ledger straight to writeback. Run an online plan or `scripts/audit_cloud_drift.py` to compare live memberships with the local ledger. If drift exists, decide whether to (a) merge the cloud edits back into the full ledger or (b) create a narrow incremental ledger containing only the repos you intend to change, with each target repo's current live lists included in `finalLists`.

Then apply the reviewed plan:

```bash
python scripts/apply_user_lists.py --mapping "<workspace>/star-readmes/classification-ledger.json" --inventory "<workspace>/github-stars.json" --out-dir "<workspace>" --apply --approved-plan "<workspace>/github-stars-sync-plan.json"
```

This script manages only the formal taxonomy lists from `references/taxonomy-template.yaml` or `<workspace>/taxonomy.yaml` by default. It preserves any existing GitHub lists that are not part of the managed taxonomy. Use `--replace-all-lists` only when the user explicitly wants the ledger to replace every list membership for each repo.

Unknown list names are rejected by default. Update `<workspace>/taxonomy.yaml` first, then rerun the plan. Use `--allow-unknown-lists` only as a transition aid; it does not replace a real taxonomy entry.

Apply mode only mutates repositories whose managed list membership differs from the reviewed plan. It writes `github-stars-writeback-journal.jsonl` before and after each mutation so partial failures can be audited.

The reviewed `planHash` binds the mapping, inventory, taxonomy, repository node IDs, descriptions, and preservation mode. Apply writes its summary and journal first, then exits non-zero when any requested mutation remains incomplete.

### 7. Report the result cleanly

Summarize:

- how many stars were scanned,
- how many READMEs were fetched,
- what new lists were created,
- what lists were reused,
- how many repos were updated,
- any ambiguous repos left in a holding list,
- any failures that need manual follow-up.

## Classification Rules

1. Prefer function over implementation language. A Rust clipboard tool still belongs in `desktop-apps` before it belongs in a generic Rust bucket.
2. Use multiple lists when they improve retrieval, but keep them meaningful. Do not spray every repo across many adjacent buckets.
3. Favor stable user intent:
   - what the repo is for,
   - what workflow it supports,
   - what future search question it answers.
4. Keep at least one broad fallback list for unresolved repos.
5. Treat `references/taxonomy-template.yaml` or `<workspace>/taxonomy.yaml` as the taxonomy source of truth. Keep `references/taxonomy-rubric.md` aligned with that machine-readable taxonomy when changing official bucket semantics.

## Browser Fallback

If `gh` cannot perform the needed operation:

1. Use the browser with an existing logged-in session.
2. Still keep the local inventory, README corpus, and ledger files as the working record.
3. Make the same taxonomy decisions locally first, then mirror them in the GitHub UI.

Do not use the browser as the first choice when `gh` can do the job more reliably.

## Scripts

- `scripts/fetch_star_inventory.py`: fetch stars and compute delta
- `scripts/fetch_readmes.py`: pull README corpus and create per-repo metadata stubs
- `scripts/audit_cloud_drift.py`: read live GitHub list memberships and report drift from a local ledger before writeback
- `scripts/apply_user_lists.py`: plan and optionally apply GitHub user list changes

## References

- `references/workflow.md`: end-to-end operating procedure
- `references/taxonomy-rubric.md`: starter taxonomy and list-creation heuristics
- `references/taxonomy-template.yaml`: machine-readable starter taxonomy
- `references/classification-ledger.schema.json`: reviewable schema for ledger assignments
- `references/github-graphql-notes.md`: auth, API behavior, and writeback caveats
