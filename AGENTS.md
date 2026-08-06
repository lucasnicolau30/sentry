<!-- draun:begin -->
# Draun — Spec-Driven Development

This project uses Draun (`draun`) for Spec-Driven Development. Specs are
markdown files and they are the single source of truth — the CLI parses and
edits them, never replaces them.

## Where things live

- Specs live under `.draun/specs/<spec-name>/` by default (configurable via
  `specsRoot` in `.draun/config.yaml`).
- Each spec folder has a `SPEC.md` (the functional spec), an `issues/` folder
  with one markdown file per issue, and `issues/INDEX.md` tracking issue state
  (`[ ]` todo, `[~]` in progress, `[x]` done) and dependencies (`blocked by`).

## The workflow

The cycle is spec → break → implement → archive. If the draun skills are
available to you, prefer them — each wraps a stage end to end:

1. `draun-spec` — write the `SPEC.md` for a new feature.
2. `draun-analyze` — (optional) review the spec for ambiguities, gaps, and
   risks before breaking it down.
3. `draun-break` — break the spec into issues with a dependency graph.
4. `draun-implement` — implement the ready issues, tracking each one.
5. `draun-archive` — validate and archive the finished spec.

Without them, drive the same loop with the CLI:

1. `draun new <spec-name>` — scaffold a new spec folder.
2. Write `SPEC.md` — describe components and behaviors (run
   `draun instructions spec` for the expected format).
3. `draun instructions break --spec <spec-slug>` — get instructions for
   breaking the spec into issues, then write `issues/*.md` and `issues/INDEX.md`.
4. `draun issues <spec-slug> --ready` — list issues whose blockers are all done.
5. Pick a ready issue and run `draun start <spec-slug> <issue-number>` before
   touching code, so the index reflects work in progress.
6. Implement it, then `draun done <spec-slug> <issue-number>` — the output
   lists the issues this unblocked.
7. Repeat 4–6 until every issue is done, then `draun archive <spec-slug>`.

## Useful commands

- `draun status` — progress overview across specs; `draun status <spec-slug>`
  for per-issue detail.
- `draun validate <spec-slug>` — check SPEC/issue files and INDEX.md consistency.
- `draun reopen <spec-slug> <issue-number>` — undo a `done`.

Every command supports `--json` for machine-readable output — prefer it when
driving the workflow programmatically.
<!-- draun:end -->
