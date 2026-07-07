# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-07-07

### Changed

- **`setup-docs` — migrate-vs-reinforce recommendation is now conditional** on
  whether files actually need to move. For a "자체구조 있음" repo where migrate and
  reinforce collapse to the same no-move work, the skill no longer pushes migrate —
  it recommends the minimal light reinforce and proposes one plan instead of forcing
  a choice. (Variance testing showed fresh agents split three ways when migrate was
  recommended unconditionally; the conditional makes the recommendation converge.) (ADR 0014)

## [0.2.0] - 2026-07-07

### Changed

- **`setup-docs` — diagnosis-driven proposal model** (ADR 0014). Diagnosis now selects
  a posture (silent install / migrate-only for chaotic trees / migrate-vs-reinforce
  choice for reasonable-but-different trees / review for healthy) and *proposes* rather
  than delegating canonical decisions. The growth loop and map spine are now mandatory
  (not an opt-in-skip choice; the trust ceremony of announce-before-write is preserved).
  MESSY is split into a light lane (link/index fixes, no file moves) and the heavy
  relayout lane, so well-organized trees with only broken links stay light.

### Fixed

- **`gate.py` `@import` false positive** — a prose mention of `@AGENTS.md`
  mid-line was parsed as a live import and reported as a broken link. Now only a
  line-leading `@path.md` is treated as an import.

## [0.1.0] - 2026-07-06

First public release.

### Added

- **`setup-docs` skill** — scaffolds a thin entry router (`AGENTS.md`), a docs
  skeleton (`decisions/`, `how-to/`, routing map), and a reachability gate. Creates
  only what's missing, append-only, never overwriting existing content.
- **`doc-reconcile` skill** — the self-growth loop. After a change, refreshes drifted
  docs and creates the new documents the architecture requires (ADR, how-to, spec, PRD).
  The canonical skill carries zero project-specific literals, enforced by a guard test.
- **Reachability gate** (`gate.py`) — enforces the `broken=0, orphan=0` invariant.
- **Content oracle** (`content_oracle.py`) — fails a migration if any source segment
  goes unaccounted for, making zero content loss a proof rather than a promise.
- **Map spine document** — routing rules and index live in `docs/_map.md`, generated
  from a single canonical source; non-destructive inline-to-map migration.
- **PRD as a first-class doc type** — product requirements route to `docs/product/`
  (on-demand, a distinct reachability tree from specs and ADRs).
- **loop-refresh** — installed copies of `doc-reconcile` stay in sync via a version+hash
  stamp, with downgrade protection, local-edit preservation, and zero unprompted commits.
- **SessionStart doc-drift prime** — nudges toward `doc-reconcile` after code changes.
- MIT license, README, and release/provenance documentation.

[0.1.0]: https://github.com/jihkyuo/docsherpa/releases/tag/v0.1.0
