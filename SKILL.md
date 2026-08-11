---
name: github-stars-curator
description: "Organize starred GitHub repos into stable, clear lists: detect new stars, download READMEs into a local corpus, classify each repo against the taxonomy, and sync the approved mapping back to GitHub via gh. Use this when a user wants their starred repos sorted into lists, a recent batch of new stars filed incrementally, or their star-list taxonomy reviewed and refined."
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
- Read `references/github-graphql-notes.md` before online plan/apply work.
- Read `references/classification-ledger.schema.json` when validating or extending the ledger shape (see step 5).
- Use `references/taxonomy-template.yaml` as the bundled machine-readable taxonomy. If `<workspace>/taxonomy.yaml` exists, scripts use that workspace taxonomy instead.

## Taxonomy Scope

The bundled 23-bucket taxonomy is a general-purpose classification: personal software, AI and agent tooling, self-hosted services and network tooling, developer infrastructure, reference material, and the `everything-else` fallback. Bucket names and definitions live in `references/taxonomy-template.yaml` and `references/taxonomy-rubric.md`.

## Preconditions

1. Use `gh` for all GitHub operations.
2. Verify `gh auth status` before any writeback. For GitHub star list mutations, the token needs a scope set that includes `user`.
3. Treat the local corpus and ledger as the working memory, but treat GitHub as the final source of truth for list membership after writeback.
4. Assume classification is iterative. New or ambiguous repos can stay in the `everything-else` fallback bucket until the next pass.
5. Before any online writeback, proactively check for cloud drift even if the user did not mention manual edits. Read live GitHub memberships, compare them with the local ledger, and treat live memberships as newer when they differ **only when the cloud edit looks deliberate** — an accidental cloud edit (repo dragged into the wrong list in the UI) should be overwritten by the ledger's intent, which apply does by setting the full desired list set (see `references/workflow.md`, Cloud drift audit and reconciliation mode). Reconcile the local plan with deliberate cloud drift, or use a narrow incremental ledger that preserves each target repo's current live lists. Do not apply an old full ledger over possible manual cloud edits.
6. For local-only work (taxonomy design, offline review), run only the offline steps: classification, ledger validation, and offline planning make no GitHub calls — skip inventory and README fetches.
7. Ledger shape is validated from `references/classification-ledger.schema.json`; keep that schema as the source for assignment field rules.
8. Deleting any GitHub list is destructive and irreversible. Unmanaged lists (see `references/glossary.md`) are preserved by default; when the online plan or drift audit reveals them, ask the user whether to delete them — never delete without explicit approval (see `references/workflow.md`, Cleaning up unmanaged lists).

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
    complete-ledger.json
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

For a full reclassification of hundreds of repos, use parallel subagents in batches with a strict validation gate — see `references/workflow.md` (Large-scale reclassification). Split the inventory with `scripts/split_manifest.py`, classify each batch in a subagent, then validate and combine the batch results with `scripts/merge_classifications.py` (JSON-integrity, 1:1 coverage, list-name whitelist, and cross-batch duplicate checks) before recording. The merge validation replaces `write_classification.py`'s validation gate for that path; recording the merged records still goes through `write_classification.py`.

Done when every repo in scope has non-empty `finalLists` and `classificationStatus` set to `reviewed`, and list names validated against the workspace taxonomy (via `write_classification.py` or the aggregate whitelist check).

### 4. Refine the taxonomy

Before refining, check whether `<workspace>/taxonomy.yaml` exists: it overrides the bundled template for every script (`choose_taxonomy_path` picks it up automatically when present), so the ledger's list names must resolve against it — flag any mismatch. When the user needs custom lists, create the workspace copy from `references/taxonomy-template.yaml` and edit it there; the workspace file is the user's own template, never the bundled one.

Use `references/taxonomy-template.yaml` or `<workspace>/taxonomy.yaml` as the machine source of truth for list names, order, descriptions, and max list count. Use `references/taxonomy-rubric.md` as the human decision rubric. New lists are justified only when:

- the bucket has a stable concept,
- at least a few repos belong there now or obviously soon,
- the distinction matters for later retrieval,
- the GitHub list cap still leaves room.

If the taxonomy would exceed 32 lists, merge the lowest-value or most overlapping buckets before writeback.

When any bucket holds more than roughly one tenth of the total star count (floor 30) or clearly outgrows the rest — or `everything-else` crosses the same bar — run the bucket overload review before refining anything: analyze what the repos actually are, propose concrete splits, and ask the user which to adopt (see `references/workflow.md`, Bucket overload review). Adopted lists are recorded in `<workspace>/taxonomy.yaml`, the user's own template.

Done when the taxonomy stays at or under the 32-list cap and every list name the ledger uses resolves against the workspace taxonomy.

### 5. Validate the ledger shape

Before planning, confirm the ledger matches `references/classification-ledger.schema.json` (required fields, list types, unique `finalLists`). There is no separate summary artifact: the schema check plus step 6's offline-plan output (desired lists, unknown lists, failed repos) is the human-readable summary — the offline plan is the validation gate.

Done when every ledger entry passes the schema check (step 6's offline plan enforces this as its first check and prints the summary counts).

### 6. Plan and sync the final mapping

Run `scripts/apply_user_lists.py` in offline plan mode first. This validates the ledger against the managed taxonomy without contacting GitHub.

```bash
python scripts/apply_user_lists.py --mapping "<workspace>/star-readmes/complete-ledger.json" --inventory "<workspace>/github-stars.json" --out-dir "<workspace>" --offline-plan
```

Then run online plan mode. This checks existing GitHub lists, stale descriptions, missing lists, and current list membership before mutation. Review the generated `planHash`.

The `--mapping` file is the ledger to sync. For a narrow run, pass the step-3 narrow ledger (e.g. `star-readmes/incremental-20260802-ledger.json`); the `complete-ledger.json` in the commands below is the full-record form used for full reclassifications or after merging the narrow ledger back (`--merge-into-full`).

```bash
python scripts/apply_user_lists.py --mapping "<workspace>/star-readmes/complete-ledger.json" --inventory "<workspace>/github-stars.json" --out-dir "<workspace>"
```

Online plan reads live GitHub data and writes a membership cache; `--use-membership-cache` is only for a deliberately reviewed rerun (details in `references/workflow.md`, List sync safety).

Before applying, run an online plan or `scripts/audit_cloud_drift.py` to compare live memberships with the local ledger. Deliberate cloud edits win and are reconciled via `references/workflow.md` (cloud drift audit and reconciliation mode) — merging cloud edits back into the full ledger or writing a narrow incremental ledger that preserves each target repo's current live lists in `finalLists`. An accidental cloud edit (repo dragged into the wrong list) is not an intent: the ledger is the target and apply overwrites it (see Precondition 5).

Then apply the reviewed plan:

```bash
python scripts/apply_user_lists.py --mapping "<workspace>/star-readmes/complete-ledger.json" --inventory "<workspace>/github-stars.json" --out-dir "<workspace>" --apply --approved-plan "<workspace>/github-stars-sync-plan.json"
```

Apply preserves existing GitHub lists outside the managed taxonomy by default and rejects unknown list names; `--replace-all-lists` and `--allow-unknown-lists` are deliberate opt-outs documented in `references/workflow.md` (List sync safety). Apply is idempotent: a failed or interrupted run can be re-planned and re-applied without manual cleanup, and `--retry N` makes transient network errors (timeout/TLS/EOF) retry per mutation. Repos in the ledger but absent from the inventory (e.g. unstarred) are reported as `absentRepos` and never mutated; handle their cloud memberships per `references/workflow.md` (Handling removed stars).

Done when the online plan shows zero unexpected `listsToRemove`, the apply exits zero, the writeback summary and journal were written, the ledger record is current (narrow runs: merged with `write_classification.py --merge-into-full`; full reclassification: the new full ledger is the record), and the plan's `taxonomyPath` points at the intended taxonomy (the workspace override when present).

### 7. Report the result cleanly

Summarize:

- how many stars were scanned,
- how many READMEs were fetched,
- what new lists were created,
- what lists were reused,
- how many repos were updated,
- any ambiguous repos left in `everything-else`,
- any failures that need manual follow-up.

Done when the report answers every bullet above, including an explicit "none" for empty ones.

## Classification Rules

1. Prefer function over implementation language, and classify into the most specific bucket that fits. A Rust clipboard tool belongs in `clipboard-tools`, not in a generic Rust bucket.
2. Use multiple lists when they improve retrieval, but keep them meaningful: two lists earn their place only when both names serve a future search question.
3. Favor stable user intent:
   - what the repo is for,
   - what workflow it supports,
   - what future search question it answers.
4. Use `everything-else` as the single fallback bucket for repos that fit no specialized list, whether their purpose is clear-but-unspecialized or not yet understood; record which case applies in the ledger `reason` and revisit `everything-else` entries every maintenance pass.
5. Treat `references/taxonomy-template.yaml` or `<workspace>/taxonomy.yaml` as the taxonomy source of truth. Keep `references/taxonomy-rubric.md` aligned with that machine-readable taxonomy when changing official bucket semantics.

## Scripts

- `scripts/fetch_star_inventory.py`: fetch stars and compute delta
- `scripts/fetch_readmes.py`: pull README corpus and create per-repo metadata stubs
- `scripts/split_manifest.py`: split the inventory into balanced batches for parallel subagent classification
- `scripts/merge_classifications.py`: validate and merge per-batch classification results into one records file (JSON-integrity, 1:1 coverage, list-name whitelist, cross-batch duplicate checks)
- `scripts/write_classification.py`: merge agent classifications into meta files and emit a ledger; validates list names against the taxonomy and makes no GitHub calls; `--merge-into-full` also accepts `--prune-removed <inventory>` to drop unstarred repos from the full ledger
- `scripts/audit_cloud_drift.py`: read live GitHub list memberships and report drift from a local ledger before writeback
- `scripts/apply_user_lists.py`: plan and optionally apply GitHub user list changes; `--retry N` retries transient network errors (timeout/TLS/EOF) per mutation

## References

See the Overview pointers above for when each file is reached; this is the index of what exists.

- `references/glossary.md`
- `references/workflow.md`
- `references/taxonomy-rubric.md`
- `references/taxonomy-template.yaml`
- `references/classification-ledger.schema.json`
- `references/github-graphql-notes.md`
