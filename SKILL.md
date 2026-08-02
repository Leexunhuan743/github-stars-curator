---
name: github-stars-curator
description: Curate GitHub starred repositories into stable, meaningful user lists by detecting new stars, downloading READMEs into a local corpus, enriching per-repo metadata, refining taxonomy decisions, and syncing the final mapping back to GitHub via gh or a browser fallback. Use this when a user wants their starred repos sorted into lists, a recent batch of new stars filed incrementally, or their star-list taxonomy reviewed and refined.
---

# GitHub Stars Curator

## Overview

This skill turns a pile of GitHub stars into a maintained catalog: local README corpus, enriched per-repo metadata, a curated taxonomy, and synchronized GitHub user lists.

Prefer this skill when the user says things like:

- "Sort my starred repos into lists." — full curation pass
- "Check what I starred recently and file the new ones." — incremental maintenance
- "Pull all starred repo READMEs locally, read them, and update the categories." — taxonomy and list review

Read references only when the task needs them:

- Read `references/glossary.md` for the meaning of the skill's leading words: ledger, drift, planHash, writeback, narrow incremental ledger, unmanaged list.
- Read `references/workflow.md` for inventory refreshes, README fetching, local corpus maintenance, or end-to-end runs.
- Read `references/taxonomy-rubric.md` when classifying repositories, refining buckets, or explaining list placement.
- Read `references/github-graphql-notes.md` only before online plan/apply work or browser fallback.
- Use `references/taxonomy-template.yaml` as the bundled machine-readable taxonomy. If `<workspace>/taxonomy.yaml` exists, scripts use that workspace taxonomy instead.

## Taxonomy Scope

The bundled 23-bucket taxonomy is a general-purpose classification: personal software (desktop apps, media, notes and reading, download/transfer utilities), AI and agent tooling, self-hosted services and network tooling, developer infrastructure (`frameworks-libraries`, `data-ml-tools`, `self-hosted`, `game-3d-creative`, `design-assets`, `business-apps`, `web-scraping-data-collection`, `security-pentest-tools`), reference material, and the `everything-else` fallback. A manually labeled 500-repo probe of GitHub's top-starred repositories covers ~98% of repos; the long tail (OS kernels, smart-home hubs, blockchain nodes, non-software repos) is legitimate `everything-else` material.

Classify into the most specific bucket that fits; `everything-else` exists for repos that genuinely fit none.

## Preconditions

1. Prefer `gh` first. Use the browser only if `gh` is unavailable, under-scoped, or cannot perform a required mutation.
2. Verify `gh auth status` before any writeback. For GitHub star list mutations, the token needs a scope set that includes `user`.
3. Treat the local corpus and ledger as the working memory, but treat GitHub as the final source of truth for list membership after writeback.
4. Assume classification is iterative. New or ambiguous repos can stay in the `everything-else` fallback bucket until the next pass.
5. Before any online writeback, proactively check for cloud drift even if the user did not mention manual edits. Read live GitHub memberships, compare them with the local ledger, and treat live memberships as newer when they differ. Reconcile the local plan with cloud drift, or use a narrow incremental ledger that preserves each target repo's current live lists. Do not apply an old full ledger over possible manual cloud edits.
6. If the user asks for local-only skill work, taxonomy design, or offline review, do not access GitHub or the browser.
7. `scripts/apply_user_lists.py` requires PyYAML. If it is missing, install it with `python -m pip install pyyaml`.
8. Ledger shape is validated from `references/classification-ledger.schema.json`; keep that schema as the source for assignment field rules.
9. Deleting any GitHub list is destructive and irreversible. Unmanaged lists (see `references/glossary.md`) are preserved by default; when the online plan or drift audit reveals them, ask the user whether to delete them — never delete without explicit approval (see `references/workflow.md`, Cleaning up unmanaged lists).

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
    complete-23bucket-ledger.json
  github-stars.json
  github-stars-delta.json
  taxonomy.yaml
  github-stars-sync-plan.json
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

Done when the fetch totals match its printed counts and `github-stars-delta.json` names every repo added or removed since the previous snapshot.

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

Done when every repo in scope has a `readmeStatus` — `ok`, or a documented failure with its reason — and `manifest.json` and `readme-index.json` cover it.

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

Record the results with `scripts/write_classification.py` (see Scripts). It validates every list name against the workspace taxonomy, merges the classification fields into `star-readmes/meta/*.json` without touching upstream repo metadata, and emits a ledger file that `apply_user_lists.py` can consume directly. Treat the emitted ledger as the narrow incremental ledger for this run's repos.

For a full reclassification of hundreds of repos, use parallel subagents in batches with a strict validation gate — see `references/workflow.md` (Large-scale reclassification). The aggregate validation (1:1 name coverage, bucket-name whitelist) replaces `write_classification.py` for that path.

Done when every repo in scope has non-empty `finalLists` and `classificationStatus` set to `reviewed`, and list names validated against the workspace taxonomy (via `write_classification.py` or the aggregate whitelist check).

### 4. Refine the taxonomy

Before refining, check whether `<workspace>/taxonomy.yaml` exists: it overrides the bundled template for every script (`choose_taxonomy_path` picks it up automatically when present). If the user needs custom lists, create it from `references/taxonomy-template.yaml` and add the lists there — never in the bundled file. When it exists, compare its list names with the ledger's `finalLists` before planning and flag any mismatch.

Use `references/taxonomy-template.yaml` or `<workspace>/taxonomy.yaml` as the machine source of truth for list names, order, descriptions, and max list count. Use `references/taxonomy-rubric.md` as the human decision rubric. New lists are justified only when:

- the bucket has a stable concept,
- at least a few repos belong there now or obviously soon,
- the distinction matters for later retrieval,
- the GitHub list cap still leaves room.

If the taxonomy would exceed 32 lists, merge the lowest-value or most overlapping buckets before writeback.

When a user's taxonomy should differ from the bundled template, copy `references/taxonomy-template.yaml` to `<workspace>/taxonomy.yaml` and edit the workspace copy. Avoid modifying the installed skill just to add a local custom list during ordinary curation.

When any bucket holds more than roughly one tenth of the total star count (floor 30) or clearly outgrows the rest — or `everything-else` crosses the same bar — run the bucket overload review before refining anything: analyze what the repos actually are, propose concrete splits, and ask the user which to adopt (see `references/workflow.md`, Bucket overload review). Adopted lists are recorded in `<workspace>/taxonomy.yaml`, the user's own template, never in the bundled one.

Done when the taxonomy stays at or under the 32-list cap and every list name the ledger uses resolves against the workspace taxonomy.

### 5. Produce the taxonomy summary

After the ledger is produced (step 3), generate a human-readable taxonomy summary so the user can audit list intent quickly.

Done when the summary reflects the current ledger, and every ledger entry matches the shape documented in `references/classification-ledger.schema.json` (offline-plan validation is step 6's first check).

### 6. Plan and sync the final mapping

Run `scripts/apply_user_lists.py` in offline plan mode first. This validates the ledger against the managed taxonomy without contacting GitHub.

```bash
python scripts/apply_user_lists.py --mapping "<workspace>/star-readmes/complete-23bucket-ledger.json" --inventory "<workspace>/github-stars.json" --out-dir "<workspace>" --offline-plan
```

Then run online plan mode. This checks existing GitHub lists, stale descriptions, missing lists, and current list membership before mutation. Review the generated `planHash`.

```bash
python scripts/apply_user_lists.py --mapping "<workspace>/star-readmes/complete-23bucket-ledger.json" --inventory "<workspace>/github-stars.json" --out-dir "<workspace>"
```

Online plan reads live GitHub data and writes a membership cache; `--use-membership-cache` is only for a deliberately reviewed rerun (details in `references/workflow.md`, List sync safety).

Before applying, run an online plan or `scripts/audit_cloud_drift.py` to compare live memberships with the local ledger. Live memberships win when they differ: reconcile via `references/workflow.md` (cloud drift audit and reconciliation mode), merging cloud edits back into the full ledger or writing a narrow incremental ledger that preserves each target repo's current live lists in `finalLists`.

Then apply the reviewed plan:

```bash
python scripts/apply_user_lists.py --mapping "<workspace>/star-readmes/complete-23bucket-ledger.json" --inventory "<workspace>/github-stars.json" --out-dir "<workspace>" --apply --approved-plan "<workspace>/github-stars-sync-plan.json"
```

Apply preserves existing GitHub lists outside the managed taxonomy by default and rejects unknown list names; `--replace-all-lists` and `--allow-unknown-lists` are deliberate opt-outs documented in `references/workflow.md` (List sync safety).

Done when the online plan shows zero unexpected `listsToRemove`, the apply exits zero, the writeback summary and journal were written, the ledger record is current (narrow runs: merged with `write_classification.py --merge-into-full`; full reclassification: the new full ledger is the record), and the plan's `taxonomyPath` points at the intended taxonomy (the workspace override when present).

### 7. Report the result cleanly

Summarize:

- how many stars were scanned,
- how many READMEs were fetched,
- what new lists were created,
- what lists were reused,
- how many repos were updated,
- any ambiguous repos left in a holding list,
- any failures that need manual follow-up.

Done when the report answers every bullet above, including an explicit "none" for empty ones.

## Classification Rules

1. Prefer function over implementation language. A Rust clipboard tool still belongs in `desktop-apps` before it belongs in a generic Rust bucket.
2. Use multiple lists when they improve retrieval, but keep them meaningful: two lists earn their place only when both names serve a future search question.
3. Favor stable user intent:
   - what the repo is for,
   - what workflow it supports,
   - what future search question it answers.
4. Use `everything-else` as the single fallback bucket for repos that fit no specialized list, whether their purpose is clear-but-unspecialized or not yet understood; record which case applies in the ledger `reason` and revisit `everything-else` entries every maintenance pass.
5. Treat `references/taxonomy-template.yaml` or `<workspace>/taxonomy.yaml` as the taxonomy source of truth. Keep `references/taxonomy-rubric.md` aligned with that machine-readable taxonomy when changing official bucket semantics.

## Browser Fallback

If `gh` cannot perform the needed operation:

1. Use the browser with an existing logged-in session.
2. Still keep the local inventory, README corpus, and ledger files as the working record.
3. Make the same taxonomy decisions locally first, then mirror them in the GitHub UI.

## Scripts

- `scripts/fetch_star_inventory.py`: fetch stars and compute delta
- `scripts/fetch_readmes.py`: pull README corpus and create per-repo metadata stubs
- `scripts/write_classification.py`: merge agent classifications into meta files and emit a ledger; validates list names against the taxonomy and makes no GitHub calls
- `scripts/audit_cloud_drift.py`: read live GitHub list memberships and report drift from a local ledger before writeback
- `scripts/apply_user_lists.py`: plan and optionally apply GitHub user list changes

## References

- `references/glossary.md`: leading-word definitions (ledger, drift, planHash, writeback, narrow incremental ledger)
- `references/workflow.md`: end-to-end operating procedure
- `references/taxonomy-rubric.md`: starter taxonomy and list-creation heuristics
- `references/taxonomy-template.yaml`: machine-readable starter taxonomy
- `references/classification-ledger.schema.json`: reviewable schema for ledger assignments
- `references/github-graphql-notes.md`: auth, API behavior, and writeback caveats
