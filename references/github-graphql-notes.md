# GitHub GraphQL Notes

## Preferred tooling

Use `gh` for this skill because it is more scriptable, easier to diff, and easier to rerun safely.

## Auth checks

Before writeback, verify:

```bash
gh auth status
```

For list creation and mutation on user star lists, the token needs access that includes the `user` scope.

## Current writeback caveats

These are practical lessons from a working run:

1. GitHub user star lists are a public-preview surface. Treat the 32-list cap as the current defensive planning limit and validate it at runtime.
2. The mutation used for syncing memberships is `updateUserListsForItem`.
3. When passing GraphQL array variables through `gh api graphql`, repeated `-F listIds[]=...` flags are the reliable way to send the list.
4. List creation can be done with `createUserList`.
5. List description updates can be done with `updateUserList`.
6. A clean source-of-truth ledger makes reruns much safer than editing lists ad hoc in the UI.
7. Treat `updateUserListsForItem` as a complete list-membership update for the item. Preserve non-taxonomy list IDs unless the user explicitly requests replacement.
8. The agent must not depend on the user to report manual GitHub edits. Before writeback, perform a fresh live membership read or drift audit. When a deliberate live edit differs from the local ledger, the local ledger is stale until reconciled; an accidental live edit (repo in the wrong list) is not intent and apply overwrites it with the ledger.

## Operational guidance

- Fetch first, mutate later.
- Keep repo IDs in the inventory because writeback uses repository node IDs.
- Keep list names stable once published; renames are possible but cost mental continuity.
- Avoid creating one-off novelty lists.
- Save a writeback summary so the user can audit what changed.
- Run `apply_user_lists.py --offline-plan` before any networked plan.
- Let the managed taxonomy replace only managed taxonomy lists. Existing GitHub lists outside the loaded taxonomy should stay attached to repos.
- Before writeback, read live memberships first and preserve cloud drift in the plan. Prefer a narrow incremental ledger for unrelated changes so stale full-ledger entries do not undo the user's cloud edits.
- Run online plan, review `planHash`, then apply with `--approved-plan`.
- Bind the plan hash to the mapping, inventory, taxonomy, repository node IDs, target descriptions, and preservation mode.
- Refuse online plan/apply when the inventory owner does not match the authenticated viewer. Treat another user's `--login` inventory as read-only.
- Apply mode should skip repos whose managed list membership is already correct.
- Even in `--replace-all-lists` mode, fetch current memberships so the reviewed plan shows every removal.
- Prefer live membership reads. The script can write and explicitly reuse a membership cache, but it must be bound to the viewer and list-state fingerprint and should be used only for reviewed reruns.
- Consider any unexpected `listsToRemove` a stop-and-review signal. Removals caused only by local ledger drift should be fixed by reconciling with live GitHub state before applying.
- Keep `github-stars-writeback-journal.jsonl` so partial failures can be audited and resumed deliberately.
- Write the summary and journal before returning a non-zero exit code for incomplete mutations.
- Review and apply `descriptionUpdates` when list descriptions drift from the loaded taxonomy.
