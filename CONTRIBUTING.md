# Contributing to docsherpa

Thanks for your interest. docsherpa is small and opinionated on purpose — a few
principles keep it that way.

## Non-negotiable principles

Before changing anything, understand what docsherpa promises. These are not style
preferences — a change that breaks one is a regression, no matter how useful:

1. **Non-destructive.** docsherpa assists, it never owns. It reshapes structure while
   preserving the user's existing content and anchors.
2. **Zero content loss.** No migration may drop or misplace a single segment. The
   content oracle enforces this — if it can't account for a segment, the run fails.
3. **The canonical skills carry zero project-specific literals.** The portable
   `doc-reconcile` skill must work in any repo, in any language. A guard test
   (`test_doc_reconcile_portable.py`) fails if a project literal leaks in. Scaffolded
   *output* is repo-specific; the *plugin canon* never is.

## Development

The deterministic core lives under `skills/setup-docs/scripts/`.

```
cd skills/setup-docs/scripts
uv run --with pytest pytest -q
```

All tests must pass before a PR is merged. CI runs the same command.

Two invariants worth knowing when you touch the core:

- **Reachability gate** (`gate.py`): `broken=0, orphan=0`. Every doc must be reachable
  from the entry router; every link must resolve.
- **Marker contract** (`contract.py`): section anchors are language-agnostic HTML
  comment markers (`<!-- docsherpa:routing -->`, `<!-- docsherpa:index -->`), never
  heading-string matches.

## Pull requests

- Keep changes surgical — touch only what the change requires.
- Match the surrounding code's style; don't refactor unrelated code.
- Add or update tests alongside behavior changes.
- If your change alters structure, policy, or a documented decision, record it: an ADR
  under `docs/decisions/` for a structural choice, and update the docs your change
  touched. (docsherpa dogfoods its own `doc-reconcile` skill for exactly this.)

## Reporting bugs

Open an issue using the templates. Because portability across diverse repos is
docsherpa's hardest problem, please include the **repo type and primary language**
where the bug appeared — that context is often the whole diagnosis.

## License

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE).
