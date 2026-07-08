# setup-docs 파이프라인 (증분 3) 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** doc-health 진단 → 목표트리 배정 → 스크래치 자체검증(등급·유실0 증명) → render_report 계획 아티팩트를 잇는 setup-docs 파이프라인(Phase 0·1·2)을 만든다. 실제 repo 실행(Phase 3·4)은 증분 4로 이연.

**Architecture:** 신규 결정론 엔진 `migrate.py`(배정·링크리라이트·스크래치 빌드+검증) + SKILL 산문(판단·오케스트레이션). 도달성=`gate`, 무손실=`content_oracle`, spine/loop=`scaffold`, 아티팩트=`render_report`, 진단=`doc-health` **전부 재사용**. content_oracle이 링크를 정규화해 무시하므로 **내용 보존은 content_oracle, 링크 정확성은 gate(broken=0)** 가 각각 지킨다.

**Tech Stack:** Python 3 stdlib (`shutil`, `tempfile`, `posixpath`, `re`, `json`), pytest.

## Global Constraints

- **stdlib-only** — 외부 의존 금지(`gate.py`·`content_oracle.py` 패턴).
- **최소 코어(P2)** — 순수 이동/개명(verbatim, 내용 불변) + 링크리라이트 + 두 오라클. **git 전제.** 정규화 transformed·비-git·동결역사 깊은 처리는 증분 4 이연.
- **검증된 계획(P1)** — 스크래치에 목표트리 빌드 후 gate(broken=0·orphan=0)+content_oracle(unaccounted=0)+scaffold(spine·loop) 통과해야만 계획 제시. 미달=STOP.
- **정직성** — 1b가 증명하는 건 **기계 차원(M1~M5 via gate/scaffold/이동) + 무손실**. J1~J4는 판단(스크래치 증명 대상 아님).
- **분업** — 배정 결정론(type→folder)은 `migrate.py`; 판단(feature명·토픽폴더·동결역사)은 SKILL 산문. "판단을 코드로 박제 말라"(§7.5).
- **위치:** `skills/setup-docs/scripts/migrate.py` + `test_migrate.py`. 러너 `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`.
- **브랜치:** `feat/setup-pipeline-inc3`(이미 생성, 스펙 커밋됨). 커밋=gitmoji+conventional.

## 데이터 계약 (재사용 인터페이스)

```python
# doc-health가 생산(SKILL이 Phase 0에서 획득):
inventory = [{"path": "api-help.md", "type": "reference", "disposition": "content",
              "coupling": "...", "summary": "..."}, ...]
# type ∈ {ADR, spec, how-to, troubleshooting, reference, explanation, PRD, legacy}
# disposition ∈ {router, tooling, content}  (scorecard.disposition)
# SKILL 판단으로 enrich: spec 문서엔 "feature", 토픽폴더면 "topic" 키 추가

# migrate.plan_moves 산출:
move_plan = [{"src": "api-help.md", "dest": "docs/reference/api-help.md",
              "ops": ["move"], "impact": None}, ...]

# 재사용: gate.analyze(root)->GateResult(broken,orphans,all_docs,visited,homes,router_present,root)
#         content_oracle.collect(root)->{seg_key:{preview,locs}}
#         scaffold.scaffold(repo_root, plugin_root_dir=None)->dict
#         render_report.render_report(data, "plan")->str
```

---

### Task 1: `plan_moves` — 결정론 배정 + 목적지 충돌 감지

**Files:**
- Create: `skills/setup-docs/scripts/migrate.py`
- Test: `skills/setup-docs/scripts/test_migrate.py`

**Interfaces:**
- Produces: `migrate.plan_moves(inventory: list[dict]) -> list[dict]` — 각 `{src, dest, ops:["move"], impact}`. router/tooling·이미제자리는 제외. 목적지 중복 시 `ValueError`.

- [ ] **Step 1: 실패 테스트 작성**

```python
# skills/setup-docs/scripts/test_migrate.py
import pytest
import migrate


def test_plan_moves_type_to_folder():
    inv = [
        {"path": "adr-1.md", "type": "ADR", "disposition": "content"},
        {"path": "help.md", "type": "how-to", "disposition": "content"},
        {"path": "trouble.md", "type": "troubleshooting", "disposition": "content"},
        {"path": "why.md", "type": "PRD", "disposition": "content"},
        {"path": "notes.md", "type": "reference", "disposition": "content"},
    ]
    plan = migrate.plan_moves(inv)
    dests = {p["src"]: p["dest"] for p in plan}
    assert dests["adr-1.md"] == "docs/decisions/adr-1.md"
    assert dests["help.md"] == "docs/how-to/help.md"
    assert dests["trouble.md"] == "docs/how-to/trouble.md"   # troubleshooting → how-to/
    assert dests["why.md"] == "docs/product/why.md"
    assert dests["notes.md"] == "docs/notes.md"              # reference → 평면
    assert all(p["ops"] == ["move"] for p in plan)


def test_plan_moves_skips_router_tooling_and_inplace():
    inv = [
        {"path": "AGENTS.md", "type": "reference", "disposition": "router"},
        {"path": ".github/X.md", "type": "reference", "disposition": "tooling"},
        {"path": "docs/decisions/a.md", "type": "ADR", "disposition": "content"},  # 이미 제자리
    ]
    assert migrate.plan_moves(inv) == []


def test_plan_moves_spec_and_topic_use_judgment_fields():
    inv = [
        {"path": "func.md", "type": "spec", "disposition": "content", "feature": "billing"},
        {"path": "a.md", "type": "reference", "disposition": "content", "topic": "auth"},
    ]
    dests = {p["src"]: p["dest"] for p in migrate.plan_moves(inv)}
    assert dests["func.md"] == "docs/specs/billing/func.md"
    assert dests["a.md"] == "docs/auth/a.md"                 # topic 폴더가 type보다 우선


def test_plan_moves_collision_raises():
    inv = [
        {"path": "x/help.md", "type": "how-to", "disposition": "content"},
        {"path": "y/help.md", "type": "how-to", "disposition": "content"},  # 둘 다 how-to/help.md
    ]
    with pytest.raises(ValueError):
        migrate.plan_moves(inv)
```

- [ ] **Step 2: 실패 확인** — Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_migrate.py -q` · Expected: FAIL (`ModuleNotFoundError: migrate`).

- [ ] **Step 3: 구현**

```python
#!/usr/bin/env python3
"""setup-docs 마이그레이션 엔진 (증분 3 — Phase 1).

결정론: 배정(type→folder) · 링크리라이트 · 스크래치 빌드+검증(두 오라클).
판단(feature명·토픽폴더·동결역사)은 SKILL 산문. content_oracle이 링크를 정규화해
무시하므로 내용보존=content_oracle, 링크정확성=gate(broken=0)가 각각 담당.
"""
import posixpath
import re
import shutil
import tempfile
from pathlib import Path

import content_oracle
import gate
import scaffold

_TYPE_DEST = {
    "ADR": "docs/decisions",
    "how-to": "docs/how-to",
    "troubleshooting": "docs/how-to",   # Diátaxis: troubleshooting = how-to 변종
    "PRD": "docs/product",
    "reference": "docs",
    "explanation": "docs",
}


def plan_moves(inventory):
    """inventory(doc-health) → move_plan. 결정론(type→folder).

    router/tooling·이미제자리 제외. spec은 doc["feature"], 토픽폴더는 doc["topic"]
    (SKILL 판단으로 미리 채움)를 쓴다. 목적지 중복 → ValueError(STOP)."""
    plan = []
    for doc in inventory:
        if doc.get("disposition") in ("router", "tooling"):
            continue
        src = doc["path"]
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

- [ ] **Step 4: 통과 확인** — Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_migrate.py -q` · Expected: **4 passed**.

- [ ] **Step 5: 커밋**

```bash
git add skills/setup-docs/scripts/migrate.py skills/setup-docs/scripts/test_migrate.py
git commit -m "✨ feat(migrate): plan_moves 결정론 배정(type→folder) + 목적지 충돌 감지"
```

---

### Task 2: `rewrite_links` — 이동에 따른 링크 재작성 (양방향)

**Files:**
- Modify: `skills/setup-docs/scripts/migrate.py` · `test_migrate.py`

**Interfaces:**
- Produces: `migrate.rewrite_links(text: str, old_self: str, move_map: dict) -> str` — `old_self`=이 문서의 이동 전 repo-상대 경로, `move_map`={이동전:이동후}. 문서가 새 위치로 갈 때 링크를 (a) 자기 상대경로 재계산 + (b) 이동한 타겟은 새 경로로 갱신.

- [ ] **Step 1: 실패 테스트 작성** (append)

```python
def test_rewrite_links_updates_moved_target():
    # a.md(루트→docs/reference/)가 b.md(루트→docs/how-to/)를 가리킴
    mm = {"a.md": "docs/reference/a.md", "b.md": "docs/how-to/b.md"}
    out = migrate.rewrite_links("see [B](b.md)", "a.md", mm)
    # a는 docs/reference/, b는 docs/how-to/ → 상대경로 ../how-to/b.md
    assert out == "see [B](../how-to/b.md)"


def test_rewrite_links_self_moved_target_stationary():
    # a.md(→docs/reference/)가 안 움직인 root.md를 가리킴
    mm = {"a.md": "docs/reference/a.md"}
    out = migrate.rewrite_links("[R](root.md)", "a.md", mm)
    assert out == "[R](../../root.md)"   # docs/reference/ → 루트 root.md


def test_rewrite_links_preserves_anchor_and_skips_external():
    mm = {"a.md": "docs/a.md"}
    assert migrate.rewrite_links("[x](b.md#sec)", "a.md", mm) == "[x](../b.md#sec)"
    assert migrate.rewrite_links("[e](https://x.com)", "a.md", mm) == "[e](https://x.com)"
    assert migrate.rewrite_links("[a](#top)", "a.md", mm) == "[a](#top)"
```

- [ ] **Step 2: 실패 확인** — Run: `uv run --with pytest pytest test_migrate.py -k rewrite_links -q` · Expected: FAIL (`AttributeError: rewrite_links`).

- [ ] **Step 3: 구현** (append to `migrate.py`)

```python
_URL_RE = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")   # [label](target)
_EXTERNAL = ("http://", "https://", "mailto:", "tel:", "#")


def _relpath(from_file, to_file):
    """repo-상대 POSIX 두 경로 → from_file 위치 기준 to_file 상대경로."""
    from_dir = posixpath.dirname(from_file)
    return posixpath.relpath(to_file, from_dir or ".")


def rewrite_links(text, old_self, move_map):
    """text의 마크다운 링크를, 문서가 old_self→move_map[old_self]로 이동한다는
    전제로 재작성. 이동한 타겟은 새 경로로, 안 움직인 타겟도 새 자기위치 기준 상대경로로."""
    new_self = move_map.get(old_self, old_self)
    old_dir = posixpath.dirname(old_self)

    def repl(m):
        label, raw = m.group(1), m.group(2).strip()
        if not raw or raw.startswith(_EXTERNAL):
            return m.group(0)
        target, hashsep, anchor = raw.partition("#")
        if not target:                      # 앵커 전용
            return m.group(0)
        old_target = posixpath.normpath(posixpath.join(old_dir, target))
        new_target = move_map.get(old_target, old_target)
        newrel = _relpath(new_self, new_target)
        return f"[{label}]({newrel}{hashsep}{anchor})"

    return _URL_RE.sub(repl, text)
```

- [ ] **Step 4: 통과 확인** — Run: `uv run --with pytest pytest test_migrate.py -k rewrite_links -q` · Expected: **3 passed**.

- [ ] **Step 5: 커밋**

```bash
git add skills/setup-docs/scripts/migrate.py skills/setup-docs/scripts/test_migrate.py
git commit -m "✨ feat(migrate): rewrite_links 양방향 링크 재작성(자기상대·이동타겟)"
```

---

### Task 3: `apply_moves` — 디렉터리에서 이동 + 전체 relink

**Files:**
- Modify: `skills/setup-docs/scripts/migrate.py` · `test_migrate.py`

**Interfaces:**
- Consumes: `rewrite_links`.
- Produces: `migrate.apply_moves(root: str|Path, move_plan: list[dict]) -> None` — `root` 트리에서 각 문서를 dest로 물리 이동하고, **트리 안 모든 `.md`의 링크를 move_map으로 재작성**.

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
    # a→b 링크 갱신
    assert "(../how-to/b.md)" in (tmp_path / "docs/reference/a.md").read_text(encoding="utf-8")
    # keep.md의 a로의 링크 갱신(루트→docs/reference/a.md)
    assert "(docs/reference/a.md)" in (tmp_path / "keep.md").read_text(encoding="utf-8")
```

- [ ] **Step 2: 실패 확인** — Run: `uv run --with pytest pytest test_migrate.py -k apply_moves -q` · Expected: FAIL.

- [ ] **Step 3: 구현** (append)

```python
def apply_moves(root, move_plan):
    """root 트리에서 move_plan대로 파일 이동 + 트리 내 전 .md 링크 재작성."""
    root = Path(root)
    move_map = {p["src"]: p["dest"] for p in move_plan}
    # 1) 모든 .md의 이동전 경로 → 새 내용(링크 재작성) 계산
    rewritten = {}   # old_rel(POSIX) -> new text
    for md in root.rglob("*.md"):
        old_rel = md.relative_to(root).as_posix()
        text = md.read_text(encoding="utf-8", errors="ignore")
        rewritten[old_rel] = rewrite_links(text, old_rel, move_map)
    # 2) 물리 이동(+ 재작성 내용 기록). 이동 안 한 문서도 재작성 내용 반영.
    for old_rel, new_text in rewritten.items():
        new_rel = move_map.get(old_rel, old_rel)
        dst = root / new_rel
        src = root / old_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if new_rel != old_rel and src.exists():
            src.unlink()
        dst.write_text(new_text, encoding="utf-8")
```

- [ ] **Step 4: 통과 확인** — Run: `uv run --with pytest pytest test_migrate.py -k apply_moves -q` · Expected: **1 passed**.

- [ ] **Step 5: 커밋**

```bash
git add skills/setup-docs/scripts/migrate.py skills/setup-docs/scripts/test_migrate.py
git commit -m "✨ feat(migrate): apply_moves 물리이동 + 트리 전체 relink"
```

---

### Task 4: `build_and_verify` — 스크래치 자체검증 엔진 (핵심)

**Files:**
- Modify: `skills/setup-docs/scripts/migrate.py` · `test_migrate.py`

**Interfaces:**
- Consumes: `apply_moves`, `content_oracle.collect`, `gate.analyze`, `scaffold.scaffold`.
- Produces: `migrate.build_and_verify(repo, move_plan, plugin_root=None) -> dict` — 두 스크래치 사본(base·current)로 검증. 반환 `{"broken": int, "orphan": int, "unaccounted": list[str]}`. **STOP 판정은 호출부**(broken/orphan/unaccounted 중 하나라도 >0이면 미달).

- [ ] **Step 1: 실패 테스트 작성** (append)

```python
def _messy_repo(root):
    # 라우터 없음 + docs/ 밖 흩어진 content 2개 + 교차링크
    _mk(root, "CLAUDE.md", "# C\n@AGENTS.md\n")     # 라우터(제자리)
    _mk(root, "AGENTS.md", "# A\n- [help](help.md)\n")
    _mk(root, "help.md", "# Help\n순수 절차 세그먼트 하나.\n")
    _mk(root, "notes.md", "# Notes\n참조 세그먼트 하나.\n")


def test_build_and_verify_reaches_clean_and_lossless(tmp_path):
    _messy_repo(tmp_path)
    (tmp_path / ".git").mkdir()   # git 전제 흉내(content_oracle는 .md만 봄)
    plan = [
        {"src": "help.md", "dest": "docs/how-to/help.md", "ops": ["move"], "impact": None},
        {"src": "notes.md", "dest": "docs/notes.md", "ops": ["move"], "impact": None},
    ]
    res = migrate.build_and_verify(tmp_path, plan)
    assert res["unaccounted"] == []          # 유실 0(두 세그먼트 살아남음)
    # 이동 후 gate가 도달성 회복(scaffold가 spine·loop·인덱스 설치)
    assert isinstance(res["broken"], int) and isinstance(res["orphan"], int)


def test_build_and_verify_detects_content_loss(tmp_path):
    # move_plan이 notes.md를 누락(이동 안 함) → 여전히 있으니 유실 아님.
    # 유실은 "세그먼트가 사라질 때". 여기선 apply가 파일을 지우는 버그를 시뮬레이션 대신
    # base에만 있고 current에 없는 세그먼트를 만들기 위해, dest 충돌로 덮이는 케이스를 쓴다.
    _mk(tmp_path, "a.md", "# A\n고유 세그먼트 A.\n")
    _mk(tmp_path, "AGENTS.md", "# R\n- [a](a.md)\n")
    (tmp_path / ".git").mkdir()
    # a.md를 docs/x.md로 옮기되, 별도로 docs/x.md가 이미 존재(다른 내용)해 덮음 → A 세그먼트 유실
    _mk(tmp_path, "docs/x.md", "# X\n다른 내용.\n")
    plan = [{"src": "a.md", "dest": "docs/x.md", "ops": ["move"], "impact": None}]
    res = migrate.build_and_verify(tmp_path, plan)
    assert res["unaccounted"]                 # A 세그먼트가 사라짐 → 감지
```

- [ ] **Step 2: 실패 확인** — Run: `uv run --with pytest pytest test_migrate.py -k build_and_verify -q` · Expected: FAIL.

- [ ] **Step 3: 구현** (append)

```python
_COPY_IGNORE = shutil.ignore_patterns("node_modules", ".git", "dist", "build", "vendor")


def _copy_tree(repo, dst):
    """repo → dst 복사(제외 디렉터리 빼고). base·current 스크래치가 동일 파일집합을
    보게 해 content_oracle 오탐 방지."""
    shutil.copytree(repo, dst, ignore=_COPY_IGNORE, dirs_exist_ok=True)


def build_and_verify(repo, move_plan, plugin_root=None):
    """두 스크래치(base=원본 복사, current=복사+이동+scaffold)로 검증 →
    {broken, orphan, unaccounted}. 실제 repo는 안 건드림."""
    repo = Path(repo).resolve()
    base = Path(tempfile.mkdtemp(prefix="docsherpa-base-"))
    current = Path(tempfile.mkdtemp(prefix="docsherpa-cur-"))
    try:
        _copy_tree(repo, base)
        _copy_tree(repo, current)
        apply_moves(current, move_plan)
        scaffold.scaffold(current, plugin_root_dir=plugin_root)
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

> 주: `content_oracle.collect`는 세그먼트 **key**(내용 해시) 집합을 준다. base·current 둘 다 동일 제외규칙으로 복사하므로 파일집합이 같고(이동만 다름), 링크는 collect가 정규화로 무시 → 이동+relink 후에도 텍스트 세그먼트가 살아있으면 unaccounted=0.

- [ ] **Step 4: 통과 확인** — Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_migrate.py -q` · Expected: **전체 migrate 테스트 GREEN**(1~4 태스크).

- [ ] **Step 5: setup-docs 회귀 확인** — Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q` · Expected: 기존 109 + migrate 신규 전부 PASS.

- [ ] **Step 6: 커밋**

```bash
git add skills/setup-docs/scripts/migrate.py skills/setup-docs/scripts/test_migrate.py
git commit -m "✨ feat(migrate): build_and_verify 스크래치 자체검증(두 오라클·유실0 증명)"
```

---

### Task 5: `assemble_plan_data` — Phase 2 render_report 계획 dict

**Files:**
- Modify: `skills/setup-docs/scripts/migrate.py` · `test_migrate.py`

**Interfaces:**
- Consumes: doc-health 데이터 dict, `move_plan`. `render_report.render_report`(통합 테스트).
- Produces: `migrate.assemble_plan_data(health: dict, move_plan: list[dict], decisions: list=None) -> dict` — doc-health 부분 dict를 render_report **plan** 계약으로 확장(`trees.after`·`migration`·`decisions` 채움).

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

- [ ] **Step 2: 실패 확인** — Run: `uv run --with pytest pytest test_migrate.py -k assemble_plan_data -q` · Expected: FAIL.

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
    data.setdefault("trees", {})
    data["trees"] = dict(data["trees"])
    data["trees"]["after"] = _after_tree(move_plan)
    data["migration"] = list(move_plan)
    data["decisions"] = list(decisions or [])
    data.setdefault("summary", {})
    return data
```

- [ ] **Step 4: 통과 확인** — Run: `uv run --with pytest pytest test_migrate.py -q` · Expected: 전체 PASS.

- [ ] **Step 5: 커밋**

```bash
git add skills/setup-docs/scripts/migrate.py skills/setup-docs/scripts/test_migrate.py
git commit -m "✨ feat(migrate): assemble_plan_data — Phase 2 render_report 계획 dict 조립"
```

---

### Task 6: SKILL.md 재배선 (Phase 0·1·2 절차) + 배선

**Files:**
- Modify: `skills/setup-docs/SKILL.md`
- Modify: `FINDINGS.md`

**Interfaces:** 없음(산문·오케스트레이션).

- [ ] **Step 1: SKILL.md "무거운 차선"을 새 파이프라인으로 교체** — 기존 `## MESSY — 진단-주도 제안 + 2차선`의 **무거운 차선(재배치 파이프라인)** 절을 아래 절차로 재작성(경량 차선·자세 분기·두 oracle 설명은 유지):
  1. **Phase 0 (before 진단):** `doc-health` 실행 → 데이터 dict(grade·scorecard·trees.before·inventory·J4). 자세=MESSY일 때만 아래 진행(GREENFIELD=조용히 설치·HEALTHY=등급 카드만).
  2. **Phase 1a (배정):** inventory를 **판단으로 enrich**(spec→`feature`명·co-change≥2→`topic`·동결역사 식별) 후 `python3 <skill>/scripts/migrate.py`의 `plan_moves(inventory)` → move_plan. 코드참조·외부싱크 깨짐은 `impact`로.
  3. **Phase 1b (자체검증):** `build_and_verify(repo, move_plan)` → `{broken, orphan, unaccounted}`. **STOP 판정:** 셋 중 하나라도 >0이면 아티팩트 안 냄 — 사유 보고 후 자동수정 재시도(목적지 개명 등) 또는 사용자 에스컬레이션. 통과 시 스크래치에 doc-health 재실행해 기계등급 확인.
  4. **Phase 2 (계획 아티팩트):** `assemble_plan_data(health, move_plan, decisions)` → `render_report(data, "plan")` 아티팩트. `decisions`=라우터결정(리치 CLAUDE.md+AGENTS 없음)·내용모순(doc-health J4)에서 조립. 사용자 승인.
  5. **정직성:** 아티팩트는 "기계 차원 A-트랙 + 내용보존 증명(unaccounted=0)"을 표시. J는 판단 평가로 별도. 증명 못 하면 계획 제시 안 함.
  6. **증분 3 경계:** 여기까지(승인). **실제 이동 실행·결과 재진단은 증분 4**(별도).
- [ ] **Step 2: 판단은 코드 아님 명시** — SKILL에 "배정 결정론=migrate.plan_moves, feature명·토픽폴더·동결역사=에이전트 판단(§7.5 교훈)" 한 줄.
- [ ] **Step 3: FINDINGS 갱신** — 최상단 "다음 세션 시작점"을 증분 3 완료·다음=증분 4(Phase 3·4 실행)로 갱신.
- [ ] **Step 4: 게이트 + 전체 회귀** — Run:
  - `python3 skills/setup-docs/scripts/gate.py . --require-markers` · Expected: `PASS broken=0 orphan=0 ... markers_ok=True`.
  - `cd skills/setup-docs/scripts && uv run --with pytest pytest -q` · Expected: 109 + migrate 신규 GREEN.
- [ ] **Step 5: 커밋**

```bash
git add skills/setup-docs/SKILL.md FINDINGS.md
git commit -m "📝 docs(setup-docs): MESSY 무거운 차선을 Phase 0·1·2 파이프라인으로 재배선"
```

---

## Self-Review (작성자 체크)

**1. 스펙 커버리지** (spec `setup-pipeline.md` → 태스크):
- §1 아키텍처(migrate.py 신규·재사용) → Task 1~5(migrate) + Task 6(SKILL).
- §2 데이터흐름 Phase 0(doc-health 호출)→Task 6 · 1a(plan_moves)→Task 1 · 1b(build_and_verify)→Task 4 · 2(assemble+render)→Task 5.
- §3 STOP/엣지 → Task 1(충돌 ValueError)·Task 4(unaccounted/broken/orphan)·Task 6(자세 분기·STOP 절차).
- §4 정직성(기계 M1~M5+무손실, J 판단) → Task 6 Step 5 명시 + Task 4가 gate/oracle만 반환(J 증명 안 함).
- §5 테스트(RED-first) → Task 1~5 전부 RED-first. 링크리라이트(Task 2)·content_oracle 무손실(Task 4)=최고위험 커버.
- §6 이연 → Task 6 Step 6(증분 4 경계) 명시.

**2. 플레이스홀더 스캔:** 코드 스텝 전부 실제 코드. 산문 스텝(Task 6)은 절차 항목 구체 열거. TBD 없음.

**3. 타입 정합성:** `plan_moves`→`move_plan[{src,dest,ops,impact}]` ↔ `apply_moves`(move_map={src:dest})·`build_and_verify`·`assemble_plan_data`(migration=move_plan) 일치. `rewrite_links(text, old_self, move_map)` ↔ `apply_moves`가 old_rel·move_map으로 호출 일치. `build_and_verify`→`{broken,orphan,unaccounted}` ↔ Task 6 STOP 판정 소비 일치. `assemble_plan_data`→render_report plan 계약(trees.after·migration·decisions) 일치.

## Execution Handoff

**Plan complete and saved to `docs/plans/2026-07-08-setup-pipeline-inc3.md`.**
