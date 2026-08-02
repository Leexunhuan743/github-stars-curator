# Workflow

This skill works best as a repeatable maintenance loop rather than a one-off dump.

## Recommended order

1. Refresh the star inventory and compute the delta.
2. Fetch READMEs for all stars or only the new stars.
3. Read README content and enrich the per-repo metadata.
4. Refine the taxonomy only after reading real content.
5. Check `<workspace>/taxonomy.yaml` before classifying: if it exists it overrides the bundled template for all scripts — confirm the ledger's list names resolve against it, and keep it in sync when the user adds custom lists.
6. Generate a classification ledger and human-readable summary.
7. Run list sync in offline plan mode.
8. Verify GitHub access with `gh auth status`.
9. Run online plan mode to inspect existing lists, descriptions, memberships, and `planHash`.
10. Apply the sync only with the reviewed plan.
11. Report results and unresolved edge cases.

## Why this order matters

- Inventory first: otherwise you do not know which repos are new, removed, or already processed.
- README fetch before classification: repo descriptions and topics are often too shallow or misleading.
- Taxonomy after reading: category quality comes from the corpus, not from guessing up front.
- Offline plan before online plan: taxonomy and ledger mistakes should be caught without touching GitHub.
- Online plan before apply: GitHub list updates are write operations and should be reviewed once before mutation.
- Approved plan before apply: the command should apply the reviewed `planHash`, not a silently changed mapping or taxonomy.

## Incremental mode

When the user asks for "new stars only" or "just process recent additions":

1. Use the delta file from `fetch_star_inventory.py`.
2. Fetch READMEs only for `newStars`.
3. Read and classify only the new corpus entries.
4. Revisit the taxonomy only if the new repos expose a genuinely new recurring concept.
5. Merge the narrow ledger into the full ledger record with `write_classification.py --merge-into-full` once the new repos are categorized and synced.

Incremental README fetches merge into the existing corpus. They must not remove old entries from `manifest.json` or `readme-index.json`, and they must not erase already-filled classification fields. Keep README availability in `readmeStatus`/`fetchStatus` and human review progress in `classificationStatus`.

Run `fetch_readmes.py --only-new-from` immediately after the inventory refresh: `fetch_star_inventory.py` regenerates `github-stars-delta.json` on every run, so a second inventory run before the README fetch overwrites the delta and leaves you with an empty `newStars` set.

Record the new repos' classifications with `scripts/write_classification.py` and name the emitted ledger with a topic or date suffix (for example `incremental-20260801-ledger.json`) so it does not collide with the canonical record; pass that file as `--mapping` for the plan and apply steps.

After writeback, merge the narrow ledger back into the full ledger record with `write_classification.py --merge-into-full <full-ledger.json>`: the script snapshots the full ledger, then replaces same-name assignments with the narrow entries (adds the rest), so stale list assignments cannot survive a manual name-only merge.

## Cloud drift audit and reconciliation mode

Use this mode before every online writeback. The user cannot be relied on to report manual edits; check for cloud drift proactively by reading live memberships and comparing them with the local ledger.

Principle: live GitHub list membership is the newest fact when it differs from the local ledger. The local ledger is a working record, not permission to overwrite cloud edits.

Recommended order:

1. Verify `gh auth status`.
2. Run `scripts/audit_cloud_drift.py` against the canonical local ledger, or otherwise read current live list memberships before planning any writeback.
3. Compare live managed-list membership against the local ledger and summarize differences.
4. Preserve cloud edits by either:
   - merging live memberships back into the full ledger before running a full apply, or
   - creating a narrow incremental ledger that contains only the repos intentionally changed in the current task.
5. For every repo in a narrow incremental ledger, include its current live managed lists plus the new desired lists in `finalLists`.
6. Run offline plan, then online plan, and inspect every `listsToRemove`.
7. Treat removals as intentional only when they match the current request or an explicitly reviewed reconciliation decision.

When every drift entry is `localNotLive` with an empty `liveNotLocal` — the typical shape of a run that only classifies newly starred repos — that is the expected pre-sync state, not a stop signal: the online plan will show the new assignments with no `listsToRemove`, and apply is safe after plan review.

Do not apply an old full ledger without a fresh drift audit. Because GitHub's membership mutation replaces the managed-list set for each target repo, a stale full ledger can silently undo manual additions, removals, or reclassifications.

If the user intentionally removed a repo from all managed taxonomy lists, do not force it back into a fallback bucket just to satisfy a full-ledger schema. Use a narrow incremental ledger for unrelated changes, or ask before converting the cloud removal into a local `everything-else` or other fallback assignment.

Recommended command:

```bash
python scripts/audit_cloud_drift.py --mapping "<workspace>/star-readmes/complete-23bucket-ledger.json" --inventory "<workspace>/github-stars.json" --out-dir "<workspace>" --all-inventory
```

The command exits zero when there is no drift and non-zero when drift is found. A non-zero drift result is not a script failure; it is a stop-and-reconcile signal before any apply.

## Artifacts worth keeping

- `github-stars.json`: latest full repo inventory
- `github-stars-delta.json`: changes since the previous scan
- `star-readmes/raw/*.md`: README corpus
- `star-readmes/meta/*.json`: per-repo metadata stubs and enrichments
- `star-readmes/manifest.json`: corpus manifest
- `star-readmes/complete-23bucket-ledger.json`: final mapping record
- `taxonomy.yaml`: optional workspace-owned taxonomy override
- `github-stars-sync-plan.json`: reviewed plan with `planHash`
- `github-stars-cloud-drift-report.json`: live-vs-ledger drift audit before writeback
- `github-stars-membership-cache.json`: optional reviewed membership cache from the latest live online plan
- `github-stars-writeback-summary.json`: list-sync result summary
- `github-stars-writeback-journal.jsonl`: per-mutation writeback journal

## List sync safety

Use `scripts/apply_user_lists.py --offline-plan` for local validation before any GitHub calls.

By default, `apply_user_lists.py` manages only the formal taxonomy lists and preserves any existing GitHub lists outside that managed set. Use `--replace-all-lists` only when the user explicitly wants the ledger to become the complete list membership for each repository.

Unknown list names are rejected by default. Add intentional new buckets to `<workspace>/taxonomy.yaml` before syncing. Keep `references/taxonomy-rubric.md` aligned when a bucket becomes part of the reusable skill.

Apply mode requires `--approved-plan <workspace>/github-stars-sync-plan.json`. The script compares the live plan hash with the reviewed plan hash, verifies the inventory owner against the authenticated viewer, creates missing lists, updates stale descriptions, skips unchanged repositories, and writes a run-scoped journal entry around every mutation. Partial failures are summarized before the command exits non-zero.

Online plan fetches memberships only for repositories present in the ledger and writes a membership cache. By default, every online plan/apply still performs a live GitHub read. Use `--use-membership-cache` only for a deliberately reviewed rerun; the cache is ignored unless its viewer login and list-state fingerprint match the current account state.

When reconciling cloud drift, prefer a fresh live read over `--use-membership-cache`. A cache is acceptable only after you have already reviewed it as the exact cloud state you intend to preserve.

## Cleaning up unmanaged lists

An **unmanaged list** (see `references/glossary.md`) is a GitHub user list outside the loaded taxonomy. `apply_user_lists.py` preserves unmanaged lists by default: it never touches their memberships, and repos in them are left alone.

Whenever the online plan or drift audit reveals unmanaged lists, report them to the user with exact list names, each list's repo count, and the consequence of deletion (memberships removed; repos keep their other lists), and ask whether they should be deleted. Deletion proceeds only on explicit user approval — it is destructive and irreversible.

Delete with the GraphQL mutation — the skill has no delete-list script:

```bash
gh api graphql -f query='mutation($id: ID!) { deleteUserList(input: {listId: $id}) { clientMutationId } }' -F id=UL_...
```

Deleting a list removes its memberships; repos stay in their other lists. After any list deletion, or after an apply interrupted mid-run, rerun the online plan: already-created lists are not re-created (missing lists = 0) and repo updates resume idempotently.

## Bucket overload review

When any managed list holds more than roughly one tenth of the total star count (with a floor of 30 repos, so small star sets do not trip it) — or clearly outgrows the rest, at roughly double the median bucket size — pause the classification flow and run this review. The `everything-else` fallback deserves the same treatment when it grows past the same threshold: that is the clearest signal that the taxonomy is missing buckets.

1. List every repo in the overloaded bucket with its summary or description.
2. Cluster them by main function or theme and count each cluster.
3. Check each cluster against the existing bucket definitions: repos that actually fit a specialized bucket were misclassified — reclassify them instead of creating anything.
4. For clusters with no existing home, evaluate the "New lists are justified only when" conditions from `references/taxonomy-rubric.md` (stable concept, a few repos now or clearly soon, retrieval value, room under the 32-list cap).
5. Present the user with: the bucket's current count, the cluster breakdown, and concrete split proposals — each with a proposed list name, definition, expected repo count, and the retrieval question it answers.
6. Ask the user which proposals to adopt (none is a valid answer).
7. Record adopted lists in `<workspace>/taxonomy.yaml` — the workspace copy is the user's own template, separate from the bundled one; if it does not exist yet, copy `references/taxonomy-template.yaml` there first. Then reclassify the affected repos into the new lists, update the ledger, and continue with the normal offline/online plan.

Propose splits only where the cluster is stable and the split serves a real retrieval question; a single lonely sub-theme stays in the parent bucket.

## Large-scale reclassification

For a full reclassification of hundreds of repos onto changed bucket definitions, run parallel subagents: split the repo list (description + meta summary + topics + legacy lists as reference-only) into batches, give each batch the bucket definitions plus explicit re-review instructions for legacy wide buckets (`desktop-apps` / `everything-else` / `self-hosted` / `dev-tools` / `references-guides`), then validate the aggregate 1:1 (name coverage, bucket-name whitelist) before writing the ledger. This path replaces `write_classification.py` — the aggregate validation is its equivalent gate, and the written ledger is the new full record (no `--merge-into-full` needed).

## Human review checkpoints

Pause for a quick review when any of these happen:

- unmanaged lists are discovered by the online plan or drift audit,
- the taxonomy would exceed 32 lists,
- the local `taxonomy.yaml` differs substantially from the bundled template,
- the cloud drift audit reports differences or the online plan shows unexpected `listsToRemove`,
- several repos do not fit existing buckets cleanly,
- a list looks too broad and should be split,
- a new list would contain only one repo with no clear future reuse,
- `gh` auth lacks the scope needed to create or update lists.
