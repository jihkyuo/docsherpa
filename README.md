<h1 align="center">docsherpa</h1>

<p align="center">
  <strong>Build and grow an agent-readable documentation architecture.</strong><br>
  A Claude Code plugin that migrates messy docs into a clean, navigable structure —<br>
  and keeps them growing as your code changes, without ever losing a line you wrote.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/Claude%20Code-plugin-8A63D2.svg" alt="Claude Code plugin">
  <a href="https://github.com/jihkyuo/docsherpa/actions/workflows/ci.yml"><img src="https://github.com/jihkyuo/docsherpa/actions/workflows/ci.yml/badge.svg" alt="tests"></a>
</p>

---

## Why

Documentation rots. As code moves, docs drift, scatter, and go stale — until nobody
trusts them and new contributors don't know where to look.

The obvious fix is to restructure. But restructuring is *dangerous*: every repo has
hard-won notes, anchors, and landmarks buried in its docs, and a careless reorg
quietly drops some of them. So the safe move is to do nothing — and the rot wins.

**docsherpa makes the restructure safe, then keeps it from happening again.**

## What it does

docsherpa stands on three non-negotiable commitments:

1. **Non-destructive migration.** It reshapes a sprawling doc tree into a
   best-practice structure — a thin entry router plus a reachability invariant —
   while preserving the anchors and landmarks you carefully built. docsherpa is an
   assistant, not an owner.

2. **Zero content loss — the inviolable invariant.** During migration, *none* of your
   existing content is dropped or misplaced. A content oracle fails the run if a single
   segment goes unaccounted for; a reachability gate proves every doc is still reachable.
   This is the line that must never break.

3. **Self-growth.** A reconcile skill rides along so that — without you thinking about it —
   your docs follow the code: stale pages get updated, and the new documents your
   architecture calls for (decisions, how-tos, specs, PRDs) get created on their own.

## Install

docsherpa is a [Claude Code](https://claude.com/claude-code) plugin.

```
/plugin marketplace add jihkyuo/docsherpa
/plugin install docsherpa@docsherpa
```

That's it — the two skills below are now available in any project.

## Quickstart

**Set up (or clean up) a project's docs:**

```
/docsherpa:setup-docs
```

This scans your repo, then scaffolds a thin entry router (`AGENTS.md`), a docs skeleton
(`docs/decisions/`, `docs/how-to/`, a routing map), and a reachability gate — creating only
what's missing and never overwriting what you already have. For a messy existing tree, it
migrates your content into place with zero loss.

**Keep them growing — before you commit a change:**

```
/docsherpa:doc-reconcile
```

This looks at what your change actually touched and does the documentation work it left
behind: refresh the docs that drifted, and create the new ones your architecture now
requires (an ADR for a structural decision, a how-to for a recovered procedure, and so on).
A SessionStart hook nudges you toward it automatically after you've changed code.

## How it works

docsherpa's structure is deliberately small and enforceable:

| Piece | Role |
|---|---|
| **Entry router** (`AGENTS.md`) | A thin, always-current index. Points at everything; explains little. |
| **Routing rules** | Decide where a new doc belongs — see the taxonomy below. |
| **Reachability gate** | Fails if any doc is unreachable (`orphan`) or any link is dead (`broken`). The invariant is `broken=0, orphan=0`. |
| **Content oracle** | During migration, fails the run if any source segment is unaccounted for. This is what makes "zero content loss" a proof, not a promise. |
| **doc-reconcile hook** | Primes the growth loop after each change so docs never fall behind. |

New documents route by kind — each lives in its own reachability tree:

| Kind | Question it answers | Home |
|---|---|---|
| **Decision (ADR)** | *Why did we choose this?* | `docs/decisions/` |
| **PRD** | *Why build this — for whom, and what counts as done?* | `docs/product/` |
| **How-to** | *How do I do / recover this?* | `docs/how-to/` |
| **Spec** | *What does it do?* | `docs/specs/` |
| **Reference** | everything else | `docs/` (flat) |

Folders are created on demand (minimum viable docs) — docsherpa never scaffolds a
speculative empty directory.

## Hooks & transparency

The growth loop is powered by a single **opt-in** hook, installed only if you accept it
during `setup-docs`. It is deliberately trivial and auditable:

```jsonc
// .claude/settings.json
"SessionStart": [{ "hooks": [
  { "type": "command", "command": "cat .claude/doc-drift-prime.txt 2>/dev/null || true" }
]}]
```

That's the whole hook — it prints a local text file at session start. **No code runs
beyond reading that file, no network calls, no telemetry.** The reminder it prints simply
nudges you to run `doc-reconcile` before committing if you changed code, policy, or
structure this session.

- **Inspect it:** `cat .claude/doc-drift-prime.txt`
- **Disable it:** remove the `SessionStart` block from `.claude/settings.json` (or delete
  the prime file). Nothing else depends on it.

## Dogfooding

docsherpa uses its own architecture on itself. This repo's docs are structured by
docsherpa's rules, its decisions live as ADRs under [`docs/decisions/`](docs/decisions/),
and the reachability gate runs against them. The full design and rationale are in
[`docs/DESIGN.md`](docs/DESIGN.md).

## Development

The deterministic core (scaffolding, gate, content oracle, portable reconcile guard)
lives under [`skills/setup-docs/scripts/`](skills/setup-docs/scripts/) and is fully tested:

```
cd skills/setup-docs/scripts
uv run --with pytest pytest -q
```

A key contract: the canonical `doc-reconcile` skill contains **zero project-specific
literals**, so it ports cleanly into any repo — a guard test enforces this.

## License

[MIT](LICENSE) © 지오현
