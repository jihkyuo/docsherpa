# setup-docs 파이프라인 (증분 3) 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **2026-07-08 계획검증 개정.** 착수 전 검증(/codex + 실측 재현)에서 6개 결함(F1~F6)이 나와 스펙([setup-pipeline.md §0a](../specs/diagnosis-driven-migration/setup-pipeline.md))과 이 계획을 소급 개정했다. 핵심 변경: **Task 0 신설**(main 잔존 잠복버그 F2·F3 픽스), **Task 4 register_in_indexes 신설**(F1 — orphan=0 실도달), plan_moves·rewrite_links·apply_moves 강화(F2·F4·F6·엣지), build_and_verify 테스트를 `broken==0`·`orphan==0` 단정으로(F5).

**Goal:** doc-health 진단 → 목표트리 배정 → 스크래치 자체검증(등급·유실0 증명) → render_report 계획 아티팩트를 잇는 setup-docs 파이프라인(Phase 0·1·2)을 만든다. 실제 repo 실행(Phase 3·4)은 증분 4로 이연.

**Architecture:** 신규 결정론 엔진 `migrate.py`(배정·링크리라이트·이동·인덱스등록·스크래치 빌드+검증) + SKILL 산문(판단·오케스트레이션). 도달성=`gate`, 무손실=`content_oracle`, spine/loop=`scaffold`, 아티팩트=`render_report`, 진단=`doc-health` **전부 재사용**. content_oracle이 링크를 정규화해 무시하므로 **내용 보존은 content_oracle, 링크 정확성·도달성은 gate(broken=0·orphan=0)** 가 각각 지킨다.

**Tech Stack:** Python 3 stdlib (`shutil`, `tempfile`, `posixpath`, `re`, `json`), pytest.

## Global Constraints

- **stdlib-only** — 외부 의존 금지(`gate.py`·`content_oracle.py` 패턴).
- **최소 코어(P2)** — 순수 이동/개명(verbatim, 내용 불변) + 링크리라이트 + 인덱스등록 + 두 오라클. **git 전제.** 정규화 transformed·비-git·동결역사 깊은 de-link·`.mdx` 이동은 증분 4 이연.
- **검증된 계획(P1)** — 스크래치에 목표트리 빌드 후 gate(broken=0·orphan=0)+content_oracle(unaccounted=0)+scaffold(spine·loop) 통과해야만 계획 제시. 미달=STOP.
- **정직성** — 1b가 증명하는 건 **기계 차원(M1~M5 via gate/scaffold/이동/등록) + 무손실**. J1~J4는 판단(스크래치 증명 대상 아님).
- **분업** — 배정 결정론(type→folder)·도달성 배선은 `migrate.py`; 판단(feature명·토픽폴더·동결역사 태깅)은 SKILL 산문. "판단을 코드로 박제 말라"(§7.5).
- **위치:** `skills/setup-docs/scripts/migrate.py` + `test_migrate.py`. 러너 `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`.
- **브랜치:** `feat/setup-pipeline-inc3`(이미 생성, 스펙 커밋됨). 커밋=gitmoji+conventional.

## 데이터 계약 (재사용 인터페이스)

```python
# doc-health가 생산(SKILL이 Phase 0에서 획득) — 분류 매니페스트:
inventory = [{"path": "api-help.md", "type": "reference",
              "coupling": "...", "summary": "..."}, ...]
# type ∈ {ADR, spec, how-to, reference, PRD, legacy}   ← doc-health SKILL.md/scoring.md 정본 어휘
# ⚠️ disposition(router/tooling/content)은 매니페스트 필드가 아니라 contract.disposition(path)로
#    경로에서 결정론 계산(F2). SKILL 판단으로 enrich: spec 문서엔 "feature", 토픽폴더면 "topic" 키 추가.

# migrate.plan_moves 산출:
move_plan = [{"src": "api-help.md", "dest": "docs/reference/api-help.md",
              "ops": ["move"], "impact": None}, ...]

# 재사용:
#   contract.disposition(rel_path) -> 'router'|'tooling'|'content'   (Task 0에서 scorecard→contract 이관)
#   gate.analyze(root)->GateResult(broken,orphans,all_docs,visited,homes,router_present,root)
#   content_oracle.collect(root)->{seg_key:{preview,locs}}   (*.md만; .mdx 미지원)
#   scaffold.scaffold(repo_root, plugin_root_dir=None)->dict
#   render_report.render_report(data, "plan")->str
```

---

### Task 0: main 잔존 잠복버그 픽스 (F2 `disposition` 이관 · F3 inject 빈 줄)

> **왜 먼저:** 두 결함은 main에 이미 머지된 코드에 있고, migrate가 그 위에 선다. `disposition`이 `contract`에 있어야 migrate가 크로스-dir 임포트 없이 쓰고(F2), inject가 빈 줄을 넣어야 1b의 content_oracle이 오탐 안 한다(F3). RED-first로 재현 테스트 먼저.

**Files:**
- Modify: `skills/setup-docs/scripts/contract.py` · `skills/setup-docs/scripts/inject_claude_md.py`
- Modify: `skills/doc-health/scripts/scorecard.py` (disposition 로컬 정의 → contract import로 교체)
- Test: `skills/setup-docs/scripts/test_contract.py` · `test_inject_claude_md.py`

- [ ] **Step 1: 실패 테스트 작성**

```python
# test_contract.py (append) — disposition이 contract로 이관됐다.
def test_disposition_router_tooling_content():
    import contract
    assert contract.disposition("AGENTS.md") == "router"
    assert contract.disposition("CLAUDE.md") == "router"
    assert contract.disposition(".github/x.md") == "tooling"
    assert contract.disposition("README.md") == "tooling"          # 루트 관례(대소문자 무시)
    assert contract.disposition("readme.md") == "tooling"
    assert contract.disposition("docs/how-to/help.md") == "content"
    assert contract.disposition("notes.md") == "content"
```

```python
# test_inject_claude_md.py (append) — import 뒤에 빈 줄이 들어가 첫 세그먼트가 안 붙는다(F3).
def test_inject_leaves_blank_line_so_first_segment_intact():
    import content_oracle
    from inject_claude_md import inject_claude_md
    before = "# My Project\n프로젝트 설명 세그먼트.\n"
    after, changed = inject_claude_md(before)
    assert changed
    # base 세그먼트가 after에도 key 그대로 살아있어야(content_oracle 오탐 방지).
    base_keys = {content_oracle.seg_key(s) for s in content_oracle.segment(before)}
    after_keys = {content_oracle.seg_key(s) for s in content_oracle.segment(after)}
    assert base_keys <= after_keys
```

- [ ] **Step 2: 실패 확인** — `cd skills/setup-docs/scripts && uv run --with pytest pytest test_contract.py test_inject_claude_md.py -q` · Expected: FAIL(`AttributeError: disposition` · 세그먼트 key 불일치).

- [ ] **Step 3: 구현**

`contract.py`에 disposition 이관(추가):
```python
import os  # (기존 import 근처)

_TOOLING_DIRS = (".claude", ".github", ".cursor", ".gitlab")
_ROOT_CONVENTION = {"readme.md", "contributing.md", "changelog.md",
                    "security.md", "code_of_conduct.md"}


def disposition(rel_path):
    """repo-상대 경로 → 'router'|'tooling'|'content' (경로 규칙, 판단 아님).

    N11 spine·배정 엔진의 공유 단일소스(gate·scorecard·migrate). 파일 IO 없음."""
    parts = Path(rel_path).parts
    if not parts:
        return "content"
    name = parts[-1]
    if len(parts) == 1 and name in ENTRY_FILENAMES:
        return "router"
    if parts[0] in _TOOLING_DIRS:
        return "tooling"
    if len(parts) == 1 and name.lower() in _ROOT_CONVENTION:
        return "tooling"
    return "content"
```

`skills/doc-health/scripts/scorecard.py` — 로컬 disposition/상수 삭제하고 contract에서 import:
```python
from contract import disposition           # noqa: E402  (기존 `import contract` 근처)
# _TOOLING_DIRS·_ROOT_CONVENTION·def disposition(...) 로컬 정의 제거.
# outside_content 등 기존 호출부는 그대로(같은 시그니처).
```

`inject_claude_md.py` — 주입 시 빈 줄 삽입(F3). `inject_claude_md`의 두 분기:
```python
    if fm_end is not None:
        new = body[:fm_end] + IMPORT_LINE + "\n\n" + body[fm_end:]
    else:
        new = IMPORT_LINE + "\n\n" + body
```
> 주: `text is None`(파일 없음) 분기는 `IMPORT_LINE + "\n"` 그대로(내용 없어 붙을 세그먼트 없음). 기존 "이미 import" no-op도 그대로.

- [ ] **Step 4: 통과 확인** — `uv run --with pytest pytest test_contract.py test_inject_claude_md.py -q` · Expected: PASS.
- [ ] **Step 5: 회귀 확인(양 러너)** — Run:
  - `cd skills/setup-docs/scripts && uv run --with pytest pytest -q` · Expected: 109 GREEN(inject 기존 테스트가 빈 줄 반영해 갱신 필요하면 갱신).
  - `cd skills/doc-health/scripts && uv run --with pytest pytest -q` · Expected: 30 GREEN(scorecard가 contract.disposition 써도 동일 결과).
- [ ] **Step 6: 커밋**

```bash
git add skills/setup-docs/scripts/contract.py skills/setup-docs/scripts/inject_claude_md.py skills/doc-health/scripts/scorecard.py skills/setup-docs/scripts/test_contract.py skills/setup-docs/scripts/test_inject_claude_md.py
git commit -m "🐛 fix(contract/inject): disposition을 contract로 이관 + inject 빈 줄(content_oracle 오탐 제거)"
```

---

### Task 1: `plan_moves` — 결정론 배정 + skip 규칙 + 목적지 충돌 감지

**Files:**
- Create: `skills/setup-docs/scripts/migrate.py`
- Test: `skills/setup-docs/scripts/test_migrate.py`

**Interfaces:**
- Consumes: `contract.disposition`.
- Produces: `migrate.plan_moves(inventory: list[dict]) -> list[dict]` — 각 `{src, dest, ops:["move"], impact}`. **skip: router/tooling(contract.disposition) · legacy(동결역사) · `.mdx` · 이미제자리.** 계획 내 목적지 중복 시 `ValueError`.

- [ ] **Step 1: 실패 테스트 작성**

```python
# skills/setup-docs/scripts/test_migrate.py
import pytest
import migrate


def test_plan_moves_type_to_folder():
    inv = [
        {"path": "adr-1.md", "type": "ADR"},
        {"path": "help.md", "type": "how-to"},
        {"path": "why.md", "type": "PRD"},
        {"path": "notes.md", "type": "reference"},
        {"path": "concept.md", "type": "explanation"},
    ]
    dests = {p["src"]: p["dest"] for p in migrate.plan_moves(inv)}
    assert dests["adr-1.md"] == "docs/decisions/adr-1.md"
    assert dests["help.md"] == "docs/how-to/help.md"
    assert dests["why.md"] == "docs/product/why.md"
    assert dests["notes.md"] == "docs/notes.md"          # reference → 평면
    assert dests["concept.md"] == "docs/concept.md"       # explanation → 평면
    assert all(p["ops"] == ["move"] for p in migrate.plan_moves(inv))


def test_plan_moves_skips_router_tooling_legacy_mdx_inplace():
    inv = [
        {"path": "AGENTS.md", "type": "reference"},              # router → skip
        {"path": ".github/X.md", "type": "reference"},           # tooling → skip
        {"path": "README.md", "type": "reference"},              # 루트관례 tooling → skip
        {"path": "docs/decisions/a.md", "type": "ADR"},          # 이미 제자리 → skip
        {"path": "docs/specs/old/2025-01-x.md", "type": "legacy"},  # 동결역사 → skip
        {"path": "guide.mdx", "type": "how-to"},                 # .mdx → skip(증분 4)
    ]
    assert migrate.plan_moves(inv) == []


def test_plan_moves_spec_and_topic_use_judgment_fields():
    inv = [
        {"path": "func.md", "type": "spec", "feature": "billing"},
        {"path": "a.md", "type": "reference", "topic": "auth"},
    ]
    dests = {p["src"]: p["dest"] for p in migrate.plan_moves(inv)}
    assert dests["func.md"] == "docs/specs/billing/func.md"
    assert dests["a.md"] == "docs/auth/a.md"                     # topic 폴더가 type보다 우선


def test_plan_moves_collision_raises():
    inv = [
        {"path": "x/help.md", "type": "how-to"},
        {"path": "y/help.md", "type": "how-to"},                 # 둘 다 docs/how-to/help.md
    ]
    with pytest.raises(ValueError):
        migrate.plan_moves(inv)
```

- [ ] **Step 2: 실패 확인** — `cd skills/setup-docs/scripts && uv run --with pytest pytest test_migrate.py -q` · Expected: FAIL(`ModuleNotFoundError: migrate`).

- [ ] **Step 3: 구현**

```python
#!/usr/bin/env python3
"""setup-docs 마이그레이션 엔진 (증분 3 — Phase 1).

결정론: 배정(type→folder) · 링크리라이트 · 물리이동 · 인덱스등록(도달성 배선)
· 스크래치 빌드+검증(두 오라클). 판단(feature명·토픽폴더·동결역사 태깅)은 SKILL 산문.
content_oracle이 링크를 정규화해 무시하므로 내용보존=content_oracle,
링크정확성·도달성=gate(broken=0·orphan=0)가 각각 담당. 의존은 전부 setup-docs/scripts 내부.
"""
import posixpath
import re
import shutil
import tempfile
from pathlib import Path

import content_oracle
import contract
import gate
import scaffold
from contract import ENTRY_FILENAMES, INDEX_MARKER

_TYPE_DEST = {
    "ADR": "docs/decisions",
    "how-to": "docs/how-to",
    "PRD": "docs/product",
    "reference": "docs",
    "explanation": "docs",
}


def plan_moves(inventory):
    """inventory(doc-health) → move_plan. 결정론(type→folder).

    skip: router/tooling(contract.disposition) · legacy(동결역사) · .mdx(무손실 미증명) · 이미제자리.
    spec은 doc["feature"], 토픽폴더는 doc["topic"](SKILL 판단으로 미리 채움)를 쓴다.
    계획 내 목적지 중복 → ValueError(STOP)."""
    plan = []
    for doc in inventory:
        src = doc["path"]
        if contract.disposition(src) in ("router", "tooling"):
            continue
        if doc.get("type") == "legacy" or src.endswith(".mdx"):
            continue                      # 동결역사·.mdx = 제자리(증분 4)
        name = posixpath.basename(src)
        if doc.get("topic"):
            dest = f"docs/{doc['topic']}/{name}"
        elif doc.get("type") == "spec":
            dest = f"docs/specs/{doc.get('feature') or 'misc'}/{name}"
        else:
            dest = f"{_TYPE_DEST.get(doc.get('type'), 'docs')}/{name}"
        if src == dest:
            continue
        plan.append({"src": src, "dest": dest, "ops": ["move"],
                     "impact": doc.get("impact")})
    dests = [p["dest"] for p in plan]
    dups = sorted({d for d in dests if dests.count(d) > 1})
    if dups:
        raise ValueError(f"목적지 충돌(둘 이상이 같은 경로): {dups}")
    return plan
```

- [ ] **Step 4: 통과 확인** — `uv run --with pytest pytest test_migrate.py -q` · Expected: **4 passed**.
- [ ] **Step 5: 커밋**

```bash
git add skills/setup-docs/scripts/migrate.py skills/setup-docs/scripts/test_migrate.py
git commit -m "✨ feat(migrate): plan_moves 결정론 배정 + router/tooling/legacy/.mdx skip + 충돌 감지"
```

---

### Task 2: `rewrite_links` — 이동에 따른 링크 재작성 (양방향 · 슬래시 보존)

**Files:**
- Modify: `skills/setup-docs/scripts/migrate.py` · `test_migrate.py`

**Interfaces:**
- Produces: `migrate.rewrite_links(text, old_self, move_map) -> str` — `old_self`=이 문서의 이동 전 repo-상대 경로, `move_map`={이동전:이동후}. (a) 자기 상대경로 재계산 + (b) 이동한 타겟은 새 경로로. **후행 `/`(디렉터리 링크) 보존 + 루트상대 `/…` skip**(F6, scaffold `_rewrite_urls` 계승).

- [ ] **Step 1: 실패 테스트 작성** (append)

```python
def test_rewrite_links_updates_moved_target():
    mm = {"a.md": "docs/reference/a.md", "b.md": "docs/how-to/b.md"}
    out = migrate.rewrite_links("see [B](b.md)", "a.md", mm)
    assert out == "see [B](../how-to/b.md)"


def test_rewrite_links_self_moved_target_stationary():
    mm = {"a.md": "docs/reference/a.md"}
    out = migrate.rewrite_links("[R](root.md)", "a.md", mm)
    assert out == "[R](../../root.md)"


def test_rewrite_links_preserves_anchor_slash_and_skips_external_and_absolute():
    mm = {"a.md": "docs/a.md"}
    assert migrate.rewrite_links("[x](b.md#sec)", "a.md", mm) == "[x](../b.md#sec)"
    assert migrate.rewrite_links("[e](https://x.com)", "a.md", mm) == "[e](https://x.com)"
    assert migrate.rewrite_links("[a](#top)", "a.md", mm) == "[a](#top)"
    assert migrate.rewrite_links("[abs](/root/x.md)", "a.md", mm) == "[abs](/root/x.md)"  # 루트상대 skip
    # 디렉터리 링크(후행 /)는 파일화되면 안 됨 — 슬래시 보존
    assert migrate.rewrite_links("[d](sub/)", "a.md", mm) == "[d](../sub/)"
```

- [ ] **Step 2: 실패 확인** — `uv run --with pytest pytest test_migrate.py -k rewrite_links -q` · Expected: FAIL.

- [ ] **Step 3: 구현** (append to `migrate.py`)

```python
_URL_RE = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")   # [label](target)
_EXTERNAL = ("http://", "https://", "mailto:", "tel:", "#", "/")   # "/" = 루트상대(F6)


def _relpath(from_file, to_file):
    """repo-상대 POSIX 두 경로 → from_file 위치 기준 to_file 상대경로."""
    return posixpath.relpath(to_file, posixpath.dirname(from_file) or ".")


def rewrite_links(text, old_self, move_map):
    """text의 마크다운 링크를, 문서가 old_self→move_map[old_self]로 이동한다는 전제로 재작성.
    이동한 타겟은 새 경로로, 안 움직인 타겟도 새 자기위치 기준 상대경로로.
    후행 슬래시(디렉터리 링크) 보존 · 외부/앵커/루트상대 skip(F6)."""
    new_self = move_map.get(old_self, old_self)
    old_dir = posixpath.dirname(old_self)

    def repl(m):
        label, raw = m.group(1), m.group(2).strip()
        if not raw or raw.startswith(_EXTERNAL):
            return m.group(0)
        target, hashsep, anchor = raw.partition("#")
        if not target:
            return m.group(0)
        trailing = "/" if target.endswith("/") else ""
        old_target = posixpath.normpath(posixpath.join(old_dir, target))
        new_target = move_map.get(old_target, old_target)
        newrel = _relpath(new_self, new_target) + trailing
        return f"[{label}]({newrel}{hashsep}{anchor})"

    return _URL_RE.sub(repl, text)
```

- [ ] **Step 4: 통과 확인** — `uv run --with pytest pytest test_migrate.py -k rewrite_links -q` · Expected: **3 passed**.
- [ ] **Step 5: 커밋**

```bash
git add skills/setup-docs/scripts/migrate.py skills/setup-docs/scripts/test_migrate.py
git commit -m "✨ feat(migrate): rewrite_links 양방향 재작성 + 후행슬래시 보존·루트상대 skip"
```

---

### Task 3: `apply_moves` — 디렉터리에서 이동 + 전체 relink + 기존 dest 충돌 STOP

**Files:**
- Modify: `skills/setup-docs/scripts/migrate.py` · `test_migrate.py`

**Interfaces:**
- Consumes: `rewrite_links`.
- Produces: `migrate.apply_moves(root, move_plan) -> None` — `root` 트리에서 각 문서를 dest로 물리 이동하고, **트리 안 모든 `.md`의 링크를 move_map으로 재작성**. **dest가 이동 대상이 아닌 기존 파일과 충돌하면 `ValueError`(사전 STOP).**

- [ ] **Step 1: 실패 테스트 작성** (append)

```python
def _mk(root, rel, text=""):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text or "# doc\n", encoding="utf-8")


def test_apply_moves_relocates_and_relinks(tmp_path):
    _mk(tmp_path, "a.md", "# A\nsee [B](b.md)\n")
    _mk(tmp_path, "b.md", "# B\n")
    _mk(tmp_path, "keep.md", "# Keep\nlink [A](a.md)\n")   # 안 움직임, a로의 링크 갱신돼야
    plan = [
        {"src": "a.md", "dest": "docs/reference/a.md", "ops": ["move"], "impact": None},
        {"src": "b.md", "dest": "docs/how-to/b.md", "ops": ["move"], "impact": None},
    ]
    migrate.apply_moves(tmp_path, plan)
    assert (tmp_path / "docs/reference/a.md").is_file()
    assert (tmp_path / "docs/how-to/b.md").is_file()
    assert not (tmp_path / "a.md").exists()
    assert "(../how-to/b.md)" in (tmp_path / "docs/reference/a.md").read_text(encoding="utf-8")
    assert "(docs/reference/a.md)" in (tmp_path / "keep.md").read_text(encoding="utf-8")


def test_apply_moves_existing_dest_collision_raises(tmp_path):
    _mk(tmp_path, "a.md", "# A\n")
    _mk(tmp_path, "docs/x.md", "# X\n")                     # 기존 파일, 이동 대상 아님
    plan = [{"src": "a.md", "dest": "docs/x.md", "ops": ["move"], "impact": None}]
    with pytest.raises(ValueError):
        migrate.apply_moves(tmp_path, plan)
```

- [ ] **Step 2: 실패 확인** — `uv run --with pytest pytest test_migrate.py -k apply_moves -q` · Expected: FAIL.

- [ ] **Step 3: 구현** (append)

```python
def apply_moves(root, move_plan):
    """root 트리에서 move_plan대로 파일 이동 + 트리 내 전 .md 링크 재작성.
    dest가 이동 대상 아닌 기존 파일과 충돌하면 ValueError(사전 STOP, 조용한 덮어쓰기 차단).
    쓰기는 2단계(모든 목적지 기록 → 이동으로 비워진 옛 경로만 삭제)로 chained-move
    (dest==다른 src) 내용 소실을 막는다."""
    root = Path(root)
    move_map = {p["src"]: p["dest"] for p in move_plan}
    srcs = set(move_map)
    # 사전 충돌 감지: dest가 이미 있고, 그게 이동으로 비워질 src가 아니면 STOP.
    clash = sorted(p["dest"] for p in move_plan
                   if (root / p["dest"]).exists() and p["dest"] not in srcs)
    if clash:
        raise ValueError(f"기존 파일과 목적지 충돌(덮어쓰기 위험): {clash}")
    # 1) 모든 .md의 이동전 경로 → 재작성 내용 계산(이동 전 전량 메모리 확보).
    rewritten = {}
    for md in root.rglob("*.md"):
        old_rel = md.relative_to(root).as_posix()
        rewritten[old_rel] = rewrite_links(
            md.read_text(encoding="utf-8", errors="ignore"), old_rel, move_map)
    dests = {move_map.get(old_rel, old_rel) for old_rel in rewritten}
    # 2) 모든 목적지에 먼저 기록(내용은 메모리에 있어 dest==다른 src여도 안전).
    for old_rel, new_text in rewritten.items():
        dst = root / move_map.get(old_rel, old_rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(new_text, encoding="utf-8")
    # 3) 이동으로 비워진 옛 경로만 삭제(누군가의 목적지인 경로는 보존).
    for old_rel in rewritten:
        new_rel = move_map.get(old_rel, old_rel)
        if new_rel != old_rel and old_rel not in dests:
            (root / old_rel).unlink()
```

> 주(검증 중 발견·수정): 최초 안의 per-item unlink+write는 chained-move(한 이동의 dest가 다른 이동의 src와 같음 — `plan_moves`가 basename 충돌로 실제 생성)에서 순회 순서에 따라 **조용한 내용 소실**을 낸다(내용 소실 0 위반). 위 2단계(전량 읽기→전 목적지 기록→비워진 옛 경로만 삭제)로 해결. RED 테스트 `test_apply_moves_chained_dest_equals_other_src_preserves_both` 추가.

- [ ] **Step 4: 통과 확인** — `uv run --with pytest pytest test_migrate.py -k apply_moves -q` · Expected: **2 passed**.
- [ ] **Step 5: 커밋**

```bash
git add skills/setup-docs/scripts/migrate.py skills/setup-docs/scripts/test_migrate.py
git commit -m "✨ feat(migrate): apply_moves 물리이동+relink + 기존 dest 충돌 사전 STOP"
```

---

### Task 4: `register_in_indexes` — 이동 문서 도달성 배선 (F1 핵심)

> **왜 존재:** 이동만 하면 이동 문서가 어느 인덱스에도 안 붙어 **전부 orphan** → 1b가 항상 STOP(실측 orphan=1). scaffold는 스켈레톤 인덱스만 만든다. 이 단계가 이동 문서를 **폴더 인덱스(`_README`)에 링크 등록**하고 **새 폴더를 map spine에 배선**해 gate orphan=0을 실제 달성한다. design §7("폴더 계층화")·§8("orphan=0")의 명시적 전제.

**Files:**
- Modify: `skills/setup-docs/scripts/migrate.py` · `test_migrate.py`

**Interfaces:**
- Produces: `migrate.register_in_indexes(root, move_plan) -> None` — scaffold가 spine(라우터→`docs/_map.md`·`decisions/README`·`how-to/_README`)을 깐 **뒤에** 호출. 폴더 문서→그 폴더 인덱스에 링크 append(없으면 인덱스 생성) · 새 폴더는 index home(map)에 배선 · 평면 문서는 index home에 직접. 링크 타겟은 home 위치에 상대적. **멱등**(이미 있는 링크 skip).

- [ ] **Step 1: 실패 테스트 작성** (append)

```python
def test_register_makes_moved_docs_reachable(tmp_path):
    import gate
    _mk(tmp_path, "CLAUDE.md", "# C\n@AGENTS.md\n")
    _mk(tmp_path, "AGENTS.md", "# A\n- [help](help.md)\n")
    _mk(tmp_path, "help.md", "# Help\n절차.\n")
    _mk(tmp_path, "notes.md", "# Notes\n참조.\n")
    plan = [
        {"src": "help.md", "dest": "docs/how-to/help.md", "ops": ["move"], "impact": None},
        {"src": "notes.md", "dest": "docs/notes.md", "ops": ["move"], "impact": None},
    ]
    migrate.apply_moves(tmp_path, plan)
    scaffold.scaffold(tmp_path, plugin_root_dir=scaffold.plugin_root())
    # 등록 전: 이동 문서는 orphan
    assert gate.analyze(tmp_path).orphans
    migrate.register_in_indexes(tmp_path, plan)
    # 등록 후: orphan=0
    res = gate.analyze(tmp_path)
    assert res.orphans == [] and res.broken == []
```

- [ ] **Step 2: 실패 확인** — `uv run --with pytest pytest test_migrate.py -k register -q` · Expected: FAIL(`AttributeError: register_in_indexes`).

- [ ] **Step 3: 구현** (append)

```python
def _ensure_folder_index(folder):
    """폴더의 인덱스(gate.index_of 규칙: _README.md > README.md). 없으면 _README.md 생성."""
    folder = Path(folder)
    idx = gate.index_of(folder)
    if idx:
        return idx
    folder.mkdir(parents=True, exist_ok=True)
    idx = folder / "_README.md"
    idx.write_text(f"# {folder.name}\n", encoding="utf-8")
    return idx


def _home_links_index(home_text, rel):
    """home이 rel 폴더의 인덱스에 도달하는 링크(dir 링크 또는 _README/README 파일 링크)를
    이미 가졌는지. 하위 임의 파일 링크(예: rel/other.md)는 인덱스 도달을 보장 못 하므로 제외 —
    느슨한 substring 매칭이 새 중첩 폴더를 '이미 링크됨'으로 오탐해 orphan을 남기던 버그(F1) 방지."""
    return (f"]({rel}/)" in home_text
            or f"]({rel}/_README.md)" in home_text
            or f"]({rel}/README.md)" in home_text)


def _append_links(path, entries):
    """entries=[(label, target)] → '- [label](target)' 를 path에 append(멱등: 이미 있으면 skip).
    기존 내용과 빈 줄로 분리해 기존 마지막 세그먼트에 붙지 않게 한다(content_oracle false STOP 방지 —
    이미 내용 있는 인덱스에 append 시 세그먼트 key가 바뀌어 무손실인데 unaccounted로 오탐하던 버그)."""
    text = path.read_text(encoding="utf-8")
    add = [f"- [{lab}]({t})" for lab, t in entries if f"]({t})" not in text]
    if not add:
        return
    block = "\n".join(add) + "\n"
    if not text:
        path.write_text(block, encoding="utf-8")
        return
    if text.endswith("\n\n"):
        sep = ""
    elif text.endswith("\n"):
        sep = "\n"
    else:
        sep = "\n\n"
    path.write_text(text + sep + block, encoding="utf-8")


def _index_home(root):
    """INDEX_MARKER를 담은 파일(docs/_map.md 우선, 없으면 진입 라우터). 없으면 None."""
    root = Path(root)
    for c in [root / "docs" / "_map.md"] + [root / n for n in ENTRY_FILENAMES]:
        if c.is_file() and INDEX_MARKER in c.read_text(encoding="utf-8", errors="ignore"):
            return c
    return None


def register_in_indexes(root, move_plan):
    """이동 문서를 도달 가능하게 배선(orphan=0). scaffold spine 위에 얹는다.

    폴더 문서 → 폴더 인덱스에 링크(+아직 map에 안 걸린 폴더만 map에 등록) · 평면 문서 → index home에 직접.
    링크 타겟은 home 위치 기준 상대. 멱등."""
    root = Path(root)
    home = _index_home(root)
    home_dir = home.parent.relative_to(root).as_posix() if home else ""
    home_text = home.read_text(encoding="utf-8") if home else ""

    by_folder, flats = {}, []
    for p in move_plan:
        dest = p["dest"]
        folder = posixpath.dirname(dest)
        if folder == "docs":
            flats.append(dest)
        else:
            by_folder.setdefault(folder, []).append(posixpath.basename(dest))

    map_entries = []
    for folder, names in sorted(by_folder.items()):
        idx = _ensure_folder_index(root / folder)
        _append_links(idx, [(posixpath.splitext(n)[0], n) for n in sorted(names)])
        rel = posixpath.relpath(folder, home_dir or ".")   # home 기준 폴더 경로
        if not _home_links_index(home_text, rel):          # 폴더 인덱스에 도달하는 링크가 아직 없을 때만
            map_entries.append((posixpath.basename(folder), rel + "/"))
    for dest in sorted(flats):
        rel = posixpath.relpath(dest, home_dir or ".")
        map_entries.append((posixpath.splitext(posixpath.basename(dest))[0], rel))

    if home and map_entries:
        _append_links(home, map_entries)
```

> 주: 폴더 인덱스 링크는 폴더 자체 기준(`name.md`)이라 home 위치와 무관. map/home 링크만 `posixpath.relpath(…, home_dir)`로 home 위치(`docs/_map.md`면 `docs/`, 인라인 라우터면 루트)에 맞춘다. decisions·how-to는 scaffold spine이 이미 map에 걸어놔 `f"]({rel}/" in home_text` 로 걸러진다(이동 ADR·how-to는 그 기존 폴더 인덱스에 append돼 도달).

- [ ] **Step 4: 통과 확인** — `uv run --with pytest pytest test_migrate.py -k register -q` · Expected: **1 passed**.
- [ ] **Step 5: 커밋**

```bash
git add skills/setup-docs/scripts/migrate.py skills/setup-docs/scripts/test_migrate.py
git commit -m "✨ feat(migrate): register_in_indexes 이동문서 도달성 배선(orphan=0 실도달)"
```

---

### Task 5: `build_and_verify` — 스크래치 자체검증 엔진

**Files:**
- Modify: `skills/setup-docs/scripts/migrate.py` · `test_migrate.py`

**Interfaces:**
- Consumes: `apply_moves`, `register_in_indexes`, `scaffold.scaffold`, `content_oracle.collect`, `gate.analyze`.
- Produces: `migrate.build_and_verify(repo, move_plan, plugin_root=None) -> dict` — 두 스크래치 사본(base·current)로 검증. 반환 `{"broken": int, "orphan": int, "unaccounted": list[str]}`. 순서: **copy → apply_moves → scaffold → register_in_indexes → gate + content_oracle.** **STOP 판정은 호출부**(셋 중 하나라도 >0이면 미달).

- [ ] **Step 1: 실패 테스트 작성** (append)

```python
def _messy_repo(root):
    _mk(root, "CLAUDE.md", "# C\n@AGENTS.md\n")
    _mk(root, "AGENTS.md", "# A\n- [help](help.md)\n")
    _mk(root, "help.md", "# Help\n순수 절차 세그먼트 하나.\n")
    _mk(root, "notes.md", "# Notes\n참조 세그먼트 하나.\n")


def test_build_and_verify_reaches_clean_and_lossless(tmp_path):
    _messy_repo(tmp_path)
    (tmp_path / ".git").mkdir()
    plan = [
        {"src": "help.md", "dest": "docs/how-to/help.md", "ops": ["move"], "impact": None},
        {"src": "notes.md", "dest": "docs/notes.md", "ops": ["move"], "impact": None},
    ]
    res = migrate.build_and_verify(tmp_path, plan)
    assert res["broken"] == 0            # 링크 무결
    assert res["orphan"] == 0            # register가 도달성 회복
    assert res["unaccounted"] == []      # 유실 0(두 세그먼트 살아남음)


def test_build_and_verify_empty_plan_verifies_spine(tmp_path):
    # 이동할 content 0(spec §3 엣지): 빈 계획 → spine/loop만 검증. 무손실·무결 당연.
    _messy_repo(tmp_path)
    (tmp_path / ".git").mkdir()
    res = migrate.build_and_verify(tmp_path, [])
    assert res["unaccounted"] == []      # 이동 없음 → 무손실
    assert res["broken"] == 0            # scaffold spine 설치 후 링크 무결
```

> 주(테스트 설계): 원안의 "덮어써서 유실" 케이스는 이제 `apply_moves`가 `ValueError`(사전 STOP)로 잡으므로 build_and_verify까지 도달 안 한다. 유실 감지(unaccounted>0)의 단위 검증은 content_oracle 자체 테스트(`test_content_oracle.py`)가 이미 커버 — build_and_verify에서 중복 증명 안 한다. 대신 여기선 **클린 도달(orphan=0·broken=0·무손실)** 과 **빈 계획 엣지**를 검증한다.

- [ ] **Step 2: 실패 확인** — `uv run --with pytest pytest test_migrate.py -k build_and_verify -q` · Expected: FAIL.

- [ ] **Step 3: 구현** (append)

```python
_COPY_IGNORE = shutil.ignore_patterns("node_modules", ".git", "dist", "build", "vendor")


def _copy_tree(repo, dst):
    """repo → dst 복사(제외 디렉터리 빼고). base·current가 동일 파일집합을 보게 해 content_oracle 오탐 방지."""
    shutil.copytree(repo, dst, ignore=_COPY_IGNORE, dirs_exist_ok=True)


def build_and_verify(repo, move_plan, plugin_root=None):
    """두 스크래치(base=원본 복사, current=복사+이동+scaffold+등록)로 검증 →
    {broken, orphan, unaccounted}. 실제 repo는 안 건드림."""
    repo = Path(repo).resolve()
    base = Path(tempfile.mkdtemp(prefix="docsherpa-base-"))
    current = Path(tempfile.mkdtemp(prefix="docsherpa-cur-"))
    try:
        _copy_tree(repo, base)
        _copy_tree(repo, current)
        apply_moves(current, move_plan)
        scaffold.scaffold(current, plugin_root_dir=plugin_root)
        register_in_indexes(current, move_plan)
        res = gate.analyze(current)
        base_keys = set(content_oracle.collect(base))
        cur_keys = set(content_oracle.collect(current))
        unaccounted = sorted(base_keys - cur_keys)
        return {"broken": len(res.broken), "orphan": len(res.orphans),
                "unaccounted": unaccounted}
    finally:
        shutil.rmtree(base, ignore_errors=True)
        shutil.rmtree(current, ignore_errors=True)
```

> 주: `content_oracle.collect`는 세그먼트 **key**(내용 해시) 집합. base·current 동일 제외규칙 복사(이동만 다름), 링크는 collect가 정규화로 무시, inject는 Task 0에서 빈 줄 → 이동+relink+scaffold 후에도 텍스트 세그먼트 살아있으면 unaccounted=0. scaffold가 current에만 추가하는 세그먼트(맵·스켈레톤)는 base에 없어 unaccounted(=base−current)에 안 잡힌다.

- [ ] **Step 4: 통과 확인** — `cd skills/setup-docs/scripts && uv run --with pytest pytest test_migrate.py -q` · Expected: **전체 migrate 테스트 GREEN**(Task 1~5).
- [ ] **Step 5: setup-docs 회귀 확인** — `cd skills/setup-docs/scripts && uv run --with pytest pytest -q` · Expected: 기존 + migrate 신규 전부 PASS.
- [ ] **Step 6: 커밋**

```bash
git add skills/setup-docs/scripts/migrate.py skills/setup-docs/scripts/test_migrate.py
git commit -m "✨ feat(migrate): build_and_verify 스크래치 자체검증(copy→move→scaffold→register→두 오라클)"
```

---

### Task 6: `assemble_plan_data` — Phase 2 render_report 계획 dict

**Files:**
- Modify: `skills/setup-docs/scripts/migrate.py` · `test_migrate.py`

**Interfaces:**
- Consumes: doc-health 데이터 dict, `move_plan`. `render_report.render_report`(통합 테스트).
- Produces: `migrate.assemble_plan_data(health, move_plan, decisions=None) -> dict` — doc-health 부분 dict를 render_report **plan** 계약으로 확장(`trees.after`·`migration`·`decisions` 채움).

- [ ] **Step 1: 실패 테스트 작성** (append)

```python
def _health_stub():
    return {
        "repo": {"name": "r", "docs_count": 3, "branch": "main"},
        "grade": {"current": "F", "target": "A"},
        "counts": {"fail": 5, "warn": 0, "pass": 4},
        "scorecard": {"mechanical": [], "judgment": []},
        "trees": {"before": {"title": "지금", "tag": "지금", "sub": "", "lines": []}},
        "posture": "MESSY",
    }


def test_assemble_plan_data_fills_after_and_migration():
    plan = [{"src": "help.md", "dest": "docs/how-to/help.md", "ops": ["move"],
             "impact": "custom-sync grep 경로 깨짐"}]
    d = migrate.assemble_plan_data(_health_stub(), plan)
    assert d["migration"] == [{"src": "help.md", "dest": "docs/how-to/help.md",
                               "ops": ["move"], "impact": "custom-sync grep 경로 깨짐"}]
    assert d["trees"]["after"]["tag"] == "목표"
    assert any(cls == "new" for _, cls in d["trees"]["after"]["lines"])
    assert d["decisions"] == []


def test_assemble_plan_data_renders_without_keyerror():
    import render_report
    d = migrate.assemble_plan_data(_health_stub(),
        [{"src": "a.md", "dest": "docs/a.md", "ops": ["move"], "impact": None}])
    html = render_report.render_report(d, "plan")
    assert html.count("<div") == html.count("</div>")
    assert 'style="' not in html
```

- [ ] **Step 2: 실패 확인** — `uv run --with pytest pytest test_migrate.py -k assemble_plan_data -q` · Expected: FAIL.

- [ ] **Step 3: 구현** (append)

```python
def _after_tree(move_plan):
    lines = [["docs/", None]]
    for p in move_plan[:12]:
        lines.append([p["dest"], "new"])
    sub = f"docs/ 중앙집중 · 이동 {len(move_plan)}건"
    return {"title": "docs/ 중앙집중", "tag": "목표", "sub": sub, "lines": lines}


def assemble_plan_data(health, move_plan, decisions=None):
    """doc-health 부분 dict → render_report plan 계약(trees.after·migration·decisions 추가)."""
    data = dict(health)
    data["trees"] = dict(data.get("trees", {}))
    data["trees"]["after"] = _after_tree(move_plan)
    data["migration"] = list(move_plan)
    data["decisions"] = list(decisions or [])
    data.setdefault("summary", {})
    return data
```

- [ ] **Step 4: 통과 확인** — `uv run --with pytest pytest test_migrate.py -q` · Expected: 전체 PASS.
- [ ] **Step 5: 커밋**

```bash
git add skills/setup-docs/scripts/migrate.py skills/setup-docs/scripts/test_migrate.py
git commit -m "✨ feat(migrate): assemble_plan_data — Phase 2 render_report 계획 dict 조립"
```

---

### Task 7: SKILL.md 재배선 (Phase 0·1·2 절차) + FINDINGS 갱신

**Files:**
- Modify: `skills/setup-docs/SKILL.md`
- Modify: `FINDINGS.md`

**Interfaces:** 없음(산문·오케스트레이션).

- [ ] **Step 1: SKILL.md "무거운 차선"을 새 파이프라인으로 교체** — 기존 `## MESSY — 진단-주도 제안 + 2차선`의 **무거운 차선(재배치 파이프라인)** 절을 아래 절차로 재작성(경량 차선·자세 분기·두 oracle 설명은 유지):
  1. **Phase 0 (before 진단):** `doc-health` 실행 → 데이터 dict(grade·scorecard·trees.before·inventory·J4). 자세=MESSY일 때만 진행(GREENFIELD=조용히 설치·HEALTHY=등급 카드만).
  2. **Phase 1a (배정):** inventory를 **판단으로 enrich**(spec→`feature`명·co-change≥2→`topic`·동결역사→`type:legacy` 태깅) 후 `plan_moves(inventory)` → move_plan. **disposition(router/tooling)·legacy·`.mdx` skip은 엔진이 자동**(판단 아님). 코드참조·외부싱크 깨짐은 `impact`로.
  3. **Phase 1b (자체검증):** `build_and_verify(repo, move_plan)` → `{broken, orphan, unaccounted}`. **STOP 판정:** 셋 중 하나라도 >0이면 아티팩트 안 냄 — 사유 보고 후 자동수정 재시도(목적지 개명·배정 조정 등) 또는 사용자 에스컬레이션. 통과 시 스크래치에 doc-health 재실행해 기계등급 확인.
  4. **Phase 2 (계획 아티팩트):** `assemble_plan_data(health, move_plan, decisions)` → `render_report(data, "plan")` 아티팩트. `decisions`=라우터결정(리치 CLAUDE.md+AGENTS 없음)·내용모순(doc-health J4)에서 조립. 사용자 승인.
  5. **정직성:** 아티팩트는 "기계 차원 A-트랙 + 내용보존 증명(unaccounted=0)"을 표시. J는 판단 평가로 별도. 증명 못 하면 계획 제시 안 함.
  6. **증분 3 경계:** 여기까지(승인). **실제 이동 실행·결과 재진단은 증분 4**(별도).
- [ ] **Step 2: 판단 vs 코드 경계 명시** — SKILL에 "배정 결정론·skip(disposition/legacy/.mdx)·도달성 배선=migrate 엔진, feature명·토픽폴더·동결역사 태깅=에이전트 판단(§7.5 교훈)" 한 줄.
- [ ] **Step 3: FINDINGS 갱신** — 최상단 "다음 세션 시작점"을 증분 3 완료(계획검증 F1~F6 반영)·다음=증분 4(Phase 3·4 실행)로 갱신.
- [ ] **Step 4: 게이트 + 전체 회귀** — Run:
  - `python3 skills/setup-docs/scripts/gate.py . --require-markers` · Expected: `PASS broken=0 orphan=0 ... markers_ok=True`.
  - `cd skills/setup-docs/scripts && uv run --with pytest pytest -q` · Expected: 기존 + migrate 신규 GREEN.
  - `cd skills/doc-health/scripts && uv run --with pytest pytest -q` · Expected: 30 GREEN.
- [ ] **Step 5: 커밋**

```bash
git add skills/setup-docs/SKILL.md FINDINGS.md
git commit -m "📝 docs(setup-docs): MESSY 무거운 차선을 Phase 0·1·2 파이프라인으로 재배선"
```

---

## Self-Review (작성자 체크)

**1. 스펙 커버리지** (spec `setup-pipeline.md` → 태스크):
- §0a 개정(F1~F6) → **F2·F3=Task 0 · F1=Task 4(register) · F4=Task 1(legacy skip) · F5=Task 5(orphan==0 단정) · F6=Task 2(슬래시 보존).** 엣지(기존 dest 충돌·.mdx)=Task 3·Task 1.
- §1 아키텍처(migrate.py·contract 이관·inject·재사용) → Task 0~6(엔진) + Task 7(SKILL).
- §2 데이터흐름 Phase 0→Task 7 · 1a(plan_moves)→Task 1 · 1b(build_and_verify: copy→apply→scaffold→register→오라클)→Task 3·4·5 · 2(assemble+render)→Task 6.
- §3 STOP/엣지 → Task 1(계획충돌 ValueError)·Task 3(기존 dest 충돌)·Task 5(unaccounted/broken/orphan)·Task 7(자세 분기·STOP 절차).
- §4 정직성(기계 M1~M5+무손실, J 판단) → Task 7 Step 5 + Task 5가 gate/oracle만 반환(J 증명 안 함).
- §5 테스트(RED-first) → Task 0~6 전부 RED-first. 링크리라이트(Task 2)·도달성 배선(Task 4)·content_oracle 무손실(Task 5)=최고위험 커버.
- §6 이연 → Task 7 Step 6 + .mdx/legacy 깊은 처리 이연 명시.

**2. 플레이스홀더 스캔:** 코드 스텝 전부 실제 코드. 산문 스텝(Task 7)은 절차 항목 구체 열거. TBD 없음.

**3. 타입 정합성:** `contract.disposition(path)`→`plan_moves` skip · `plan_moves`→`move_plan[{src,dest,ops,impact}]` ↔ `apply_moves`(move_map={src:dest})·`register_in_indexes`(dest 파싱)·`build_and_verify`·`assemble_plan_data`(migration=move_plan) 일치. `rewrite_links(text, old_self, move_map)` ↔ `apply_moves` 호출 일치. `register_in_indexes`가 scaffold 뒤 실행(home=`docs/_map.md`) 순서 명시. `build_and_verify`→`{broken,orphan,unaccounted}` ↔ Task 7 STOP 소비 일치. `assemble_plan_data`→render_report plan 계약 일치.

## Execution Handoff

**Plan complete and saved to `docs/plans/2026-07-08-setup-pipeline-inc3.md`.**
