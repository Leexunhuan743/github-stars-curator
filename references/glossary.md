# Glossary — GitHub Stars Curator

Leading words used throughout this skill. Each anchors a meaning in one place so the same word always means the same thing; lookup by bold term.

## Ledger

The local JSON record of repo-to-list assignments (`star-readmes/*-ledger.json`). A working record, never authority over live GitHub state.

## Drift

Any difference between live GitHub list membership and the local ledger. Live membership is the newest fact. `localNotLive`-only drift is the expected pre-sync state of newly classified repos; `liveNotLocal` is a stop-and-reconcile signal.

## PlanHash

SHA-256 binding of the reviewed sync plan to the mapping, inventory, taxonomy, repository node IDs, descriptions, and preservation mode. Apply refuses any plan whose hash does not match the approved file.

## Writeback

Any mutation of GitHub star lists, gated behind offline plan, then online plan, then an approved plan.

## Narrow Incremental Ledger

A ledger containing only the repos intentionally changed in the current run, each with its current live lists plus desired lists in `finalLists`. The drift-safe alternative to re-applying an old full ledger.
