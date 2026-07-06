# Provenance & Audit

This document records the origin of docsherpa's code and content, and the audits run
before public release. It exists to make one claim verifiable: **no third-party code is
bundled, and no private identifiers leak into the plugin canon.**

## Authored code

All executable code under [`skills/setup-docs/scripts/`](skills/setup-docs/scripts/) is
original to this project:

- `scaffold.py` — installer body (router + docs skeleton, append-only merge)
- `gate.py` — reachability gate (`broken=0, orphan=0`)
- `content_oracle.py` — zero-content-loss oracle for migrations
- `contract.py` — single source for markers and the doc contract
- `check_markers.py`, `inject_claude_md.py`, `merge_settings.py`, `refresh.py`

These depend only on the Python standard library. No third-party runtime dependency is
vendored or required. `pytest` is used for the test suite only, pulled on demand via
`uv run --with pytest` — it is never bundled.

## Pattern references (concepts, not code)

docsherpa's design is informed by established documentation and architecture patterns.
These are **conceptual influences** — no code was copied from them:

- **Architecture Decision Records** — the ADR format popularized by Michael Nygard.
- **Diátaxis** — the documentation taxonomy (decisions / how-to / reference / explanation)
  that informs the routing rules.
- **Claude Code plugin & skill conventions** — the plugin/skill structure and the
  superpowers-style skill authoring patterns.

## Identifier audit

- **Scope:** the canonical (portable) plugin sources — the skills and scripts that ship
  and install into other repositories.
- **Result:** zero personal or company identifiers leak into the plugin canon. The
  canonical `doc-reconcile` skill carries **zero project-specific literals**, enforced
  continuously by `test_doc_reconcile_portable.py`.
- **Note on scaffolded output:** documents that `setup-docs` *generates* into a user's
  repo are intentionally specific to that repo — that is the user's content, not the
  plugin canon. The invariant is one-directional: the plugin canon never absorbs a
  consumer's literals.

## License

docsherpa is released under the [MIT License](LICENSE). Copyright (c) 2026 지오현.
