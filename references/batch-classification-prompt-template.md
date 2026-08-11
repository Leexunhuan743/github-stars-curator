# Batch Classification Prompt Template

Reusable prompt for the parallel-subagent reclassification flow (see
`workflow.md` → "Large-scale reclassification"). Fill the placeholders and
send one prompt per subagent, one subagent per batch.

This template is a skeleton, not a content source: bucket definitions live
in `references/taxonomy-rubric.md` and `references/taxonomy-template.yaml`
(workspace copy: `<workspace>/taxonomy.yaml`), so the prompt must point at
them rather than duplicate them. If you inline rubric text into the prompt,
update both when the taxonomy changes.

## Placeholders

| Placeholder | Fill with |
|---|---|
| `<BATCH_FILE>` | Path to the batch manifest, e.g. `<workspace>/batches/batch-3.json` |
| `<RECORDS_FILE>` | Path the subagent must write, e.g. `<workspace>/batches/batch-3-records.json` |
| `<RUBRIC>` | Path to `references/taxonomy-rubric.md` (absolute path preferred) |
| `<TAXONOMY>` | Path to `<workspace>/taxonomy.yaml`, or `references/taxonomy-template.yaml` if no workspace copy exists |

## Prompt body

You are classifying starred GitHub repositories into a fixed taxonomy of lists.

Read `<BATCH_FILE>`: a JSON array; one entry per repository to classify.
Each entry contains `nameWithOwner` (required), plus context fields
(`description`, `primaryLanguage`, `topics`, `stargazerCount`, `isArchived`,
`isFork`), a `summary` when a README digest exists, and `legacyLists` with the
repo's current lists. `summary` and `legacyLists` are reference only — you are
free to override them.

Bucket definitions: read `<RUBRIC>`. Use its bucket descriptions, formal
rules, and "Common confusions" sections to decide placement. List names must
match `<TAXONOMY>` exactly (same spelling, same case).

Rules:

- Classify every repository in the batch; write exactly one record per repo.
- `finalLists` must be a non-empty list of valid taxonomy list names, ordered
  most-specific first. Use 1–2 lists; a second list only when the repo
  genuinely serves two retrievals.
- Prefer the most specific bucket that cleanly fits. The fallback bucket
  (`everything-else`) is for repos with no specialized home — use it only
  when nothing fits, and note that in the reason.
- Re-review repos currently in the legacy wide buckets
  (`desktop-apps`, `dev-tools`, `self-hosted`, `references-guides`,
  `everything-else`): they are reclassification targets, not defaults. Move
  them to a specialized bucket when one fits; keep the wide bucket only when
  no specialized one applies.
- When the batch gives you a digest summary, prefer it over the one-line
  description; when both are missing or empty, classify from the name and
  your knowledge of the repo, and set `confidence: "low"`.

Write `<RECORDS_FILE>`: a JSON array with exactly one object per repo in the
batch, in this shape (extra fields are allowed; the three optional ones are
recommended):

```json
[
  {
    "nameWithOwner": "owner/repo",
    "finalLists": ["list-a"],
    "summary": "optional one-line digest",
    "reason": "optional placement rationale",
    "confidence": "high"
  }
]
```

Constraints:

- `nameWithOwner` must match the batch entry exactly (owner/repo, no URL).
- `finalLists` entries must be taxonomy list names from `<TAXONOMY>`.
- The records file must be complete, valid JSON — a truncated file is
  rejected by the merge step and the whole batch is re-run.
- Include every repo from the batch; a repo with no good home still gets a
  record (`everything-else`, `confidence: "low"`, reason stating why).

When done, reply with a short per-batch distribution: the count of records
per list, e.g. `dev-tools: 12, terminal: 8, everything-else: 3`. A flat
distribution with an implausibly large `everything-else` or a single
"classified everything" bucket is treated as a failed batch.

If `<BATCH_FILE>` is missing or unreadable, say so explicitly and write no
records file — do not fabricate records.
