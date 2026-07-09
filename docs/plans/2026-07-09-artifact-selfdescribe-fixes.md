# 아티팩트 자기설명 보정 (A·라벨·C1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** vd-front dogfood·UX 피드백에서 드러난 진단서 아티팩트 3결함을 파이프라인에서 고친다 — (A) 플랜 모드에 기존 깨진 링크(preexisting_broken) 표면화, (라벨) how-to를 "작업 절차·복구"로 정직화, (C1) before 트리를 평면→중첩 스캐폴딩.

**Architecture:** 아티팩트 = `render_report.render_report(data,"plan")` ∘ `migrate.assemble_plan_data(...)`. 데이터 생산(migrate·scorecard)과 렌더(render_report)를 각각 최소 수정한다. **architect 교차검증(2026-07-09) 결론 반영:** A는 콜아웃/impact가 아니라 기존 `_render_preexisting` 컴포넌트를 plan 모드에도 렌더(impact=이동유발 vs preexisting=이동무관, 의미 분리). B(규모라인)·C2(트리 접이식)는 §2 단순함/중복으로 defer.

**Tech Stack:** Python 3 stdlib, pytest. render_report는 동결 품질 렌더러(인라인 style 0·AA 대비·div 밸런스 게이트 유지).

## Global Constraints

- **stdlib-only.** RED-first(실패 테스트 먼저).
- **render_report 품질 게이트 불변:** 인라인 `style=` 0 · `<div>` 밸런스 · AA 대비 · 기존 D3/D4/D6 테스트 GREEN 유지. 새 색/토큰 추가 시 AA_PAIRS 갱신.
- **impact 필드 불가침:** `impact`는 에이전트-저작 "이동-유발 위험" 단일 소스. preexisting_broken을 impact에 매핑하지 말 것(의미 충돌 + `test_assemble_plan_data_fills_after_and_migration`가 impact 보존을 assert).
- **하위호환:** `assemble_plan_data` 신규 파라미터는 선택(default None) — 기존 positional 호출부 안전.
- **위치:** `skills/setup-docs/scripts/`(migrate.py·render_report.py·test_*) + `skills/doc-health/scripts/`(scorecard.py·test_scorecard.py) + `skills/setup-docs/SKILL.md`.
- **브랜치:** 현재 `feat/artifact-ux-d3d4d6`(증분 4 활성본)에서 **피처브랜치 신설**(예: `fix/artifact-preexisting-label-beforetree`). 커밋=gitmoji+conventional.
- **러너:** `cd skills/setup-docs/scripts && uv run --with pytest pytest -q` · `cd skills/doc-health/scripts && uv run --with pytest pytest -q`.

---

### Task 1: `build_and_verify`가 `preexisting_broken` 반환 + `assemble_plan_data`가 전달

**Files:**
- Modify: `skills/setup-docs/scripts/migrate.py` (`build_and_verify` 반환 dict · `assemble_plan_data` 시그니처)
- Test: `skills/setup-docs/scripts/test_migrate.py`

**Interfaces:**
- Produces: `build_and_verify(...) -> {..., "preexisting_broken": list[(rel,raw)]}` (기존 키 유지 + 추가). `assemble_plan_data(health, move_plan, decisions=None, preexisting_broken=None) -> dict`에 `data["preexisting_broken"]` 키 추가.

- [ ] **Step 1: 실패 테스트 작성** (append to test_migrate.py)

```python
def test_build_and_verify_returns_preexisting_broken(tmp_path):
    # 기존부터 깨진 링크(nowhere.md)가 있는 repo → build_and_verify가 preexisting_broken을 반환(드롭 안 함)
    _mk(tmp_path, "CLAUDE.md", "# C\n@AGENTS.md\n")
    _mk(tmp_path, "AGENTS.md", "# A\n- [x](docs/x.md)\n")
    _mk(tmp_path, "docs/x.md", "# X\n본문. [dead](nowhere.md)\n")   # nowhere.md 없음 = 기존 broken
    (tmp_path / ".git").mkdir()
    res = migrate.build_and_verify(tmp_path, [])
    assert "preexisting_broken" in res
    assert any("nowhere.md" in raw for _rel, raw in res["preexisting_broken"])


def test_assemble_plan_data_threads_preexisting_broken():
    pre = [("docs/x.md", "nowhere.md")]
    d = migrate.assemble_plan_data(
        _health_stub(),
        [{"src": "a.md", "dest": "docs/a.md", "ops": ["move"], "impact": "이동시 grep 깨짐"}],
        preexisting_broken=pre)
    assert d["preexisting_broken"] == pre
    # impact는 에이전트 소스 그대로(preexisting이 덮지 않음)
    assert d["migration"][0]["impact"] == "이동시 grep 깨짐"
```

- [ ] **Step 2: 실패 확인** — `cd skills/setup-docs/scripts && uv run --with pytest pytest test_migrate.py -k "preexisting_broken or threads_preexisting" -q` · Expected: FAIL(`KeyError: 'preexisting_broken'` · `TypeError: unexpected keyword argument`).

- [ ] **Step 3: 구현** — `migrate.py` `build_and_verify` 반환 dict에 한 줄 추가(현재 `"per_file": v["per_file"]}` 줄):

```python
        return {"broken": len(v["new_broken"]), "orphan": v["orphan"],
                "unaccounted": v["unaccounted"], "new_broken": v["new_broken"],
                "anchor_lost": v["anchor_lost"], "unexplained_broken": v["unexplained_broken"],
                "preexisting_broken": v["preexisting_broken"],
                "per_file": v["per_file"]}
```

`assemble_plan_data` 시그니처·본문 수정:

```python
def assemble_plan_data(health, move_plan, decisions=None, preexisting_broken=None):
    """doc-health 부분 dict → render_report plan 계약(trees.after·migration·decisions·preexisting_broken 추가).

    preexisting_broken(엔진 검출 "이동 전부터 깨져 있던 링크", [(rel,raw)])은 impact(에이전트 저작
    "이동-유발 위험")와 다른 축이라 별도 키로 둔다 — 콜아웃 아니라 _render_preexisting 섹션으로 렌더된다."""
    data = dict(health)
    data["trees"] = dict(data.get("trees", {}))
    data["trees"]["after"] = _after_tree(move_plan)
    data["migration"] = list(move_plan)
    data["decisions"] = list(decisions or [])
    data["preexisting_broken"] = list(preexisting_broken or [])
    data.setdefault("summary", {})
    return data
```

- [ ] **Step 4: 통과 확인** — `uv run --with pytest pytest test_migrate.py -k "preexisting_broken or threads_preexisting" -q` · Expected: **2 passed**. 그리고 기존 assemble 테스트 유지: `uv run --with pytest pytest test_migrate.py -k assemble -q` · Expected: 전부 PASS.

- [ ] **Step 5: 커밋**

```bash
git add skills/setup-docs/scripts/migrate.py skills/setup-docs/scripts/test_migrate.py
git commit -m "✨ feat(migrate): build_and_verify preexisting_broken 반환 복원 + assemble_plan_data 전달"
```

---

### Task 2: `render_report`가 plan 모드에도 `_render_preexisting` 렌더 (A)

**Files:**
- Modify: `skills/setup-docs/scripts/render_report.py` (`_render_main`)
- Test: `skills/setup-docs/scripts/test_render_report.py`

**Interfaces:**
- Consumes: `data["preexisting_broken"]`(Task 1). 기존 `_render_preexisting(items)`(무수정) 재사용.

- [ ] **Step 1: 실패 테스트 작성** (append to test_render_report.py)

```python
def test_plan_mode_surfaces_preexisting_broken():
    d = {**MIN,
         "migration": [{"src": "a.md", "dest": "docs/a.md", "ops": ["move"], "impact": None}],
         "decisions": [],
         "preexisting_broken": [("docs/x.md", "nowhere.md")]}
    html = render_report(d, "plan")
    assert "기존에 깨져 있던 링크" in html and "머지 전" in html   # _render_preexisting 헤더
    assert "docs/x.md" in html and "nowhere.md" in html
    assert 'style="' not in html
    assert html.count("<div") == html.count("</div>")


def test_plan_mode_no_preexisting_section_when_empty():
    d = {**MIN, "migration": [], "decisions": [], "preexisting_broken": []}
    html = render_report(d, "plan")
    assert "기존에 깨져 있던 링크" not in html      # 빈 리스트면 섹션 없음
```

- [ ] **Step 2: 실패 확인** — `uv run --with pytest pytest test_render_report.py -k "plan_mode_surfaces_preexisting or no_preexisting_section" -q` · Expected: FAIL(첫 테스트: 섹션 부재).

- [ ] **Step 3: 구현** — `_render_main`에서 preexisting 렌더를 `else`(result) 안에서 **밖으로** 빼 양 모드 공통으로:

```python
def _render_main(data: dict, mode: str) -> str:
    parts = [_render_masthead(data), _render_hero(data), _render_scorecard(data), _render_trees(data)]
    if mode == "plan":
        parts += [_render_migration(data), _render_decisions(data)]
    else:
        parts.append(_render_summary(data))
        s = data.get("summary") or {}
        if "grade_before" in s and "grade_after" in s:
            parts.append(_render_grade_compare(s["grade_before"], s["grade_after"]))
    pre = data.get("preexisting_broken")          # 양 모드(plan·result) 공통 표면화
    if pre:
        parts.append(_render_preexisting(pre))
    parts.append('<p class="foot">docsherpa · setup-docs</p>')
    return "<main>" + "".join(parts) + "</main>"
```

- [ ] **Step 4: 통과 확인** — Run:
  - `uv run --with pytest pytest test_render_report.py -k "plan_mode_surfaces_preexisting or no_preexisting_section" -q` · Expected: **2 passed**.
  - 회귀(result 모드 preexisting·품질게이트 유지): `uv run --with pytest pytest test_render_report.py -q` · Expected: 전부 PASS(기존 result preexisting 테스트 그대로).

- [ ] **Step 5: 커밋**

```bash
git add skills/setup-docs/scripts/render_report.py skills/setup-docs/scripts/test_render_report.py
git commit -m "✨ feat(render): plan 모드에도 preexisting_broken 표면화(_render_preexisting 공통 렌더)"
```

---

### Task 3: how-to 라벨 정직화 — "가이드" → "작업 절차·복구" (라벨)

**Files:**
- Modify: `skills/setup-docs/scripts/render_report.py` (`_render_trees` tkey · `_TYPE_GROUP`)
- Test: `skills/setup-docs/scripts/test_render_report.py`

**Interfaces:** 없음(표시 문자열).

- [ ] **Step 1: 실패 테스트 작성** (append)

```python
def test_howto_label_is_procedure_recovery_not_just_guide():
    html = render_report(MIN, "plan")
    assert "작업 절차·복구(how-to)" in html      # 트리 tkey 범례
    assert "가이드(how-to)" not in html          # 좁은 오역 제거


def test_migration_howto_group_label_aligned():
    d = {**MIN, "decisions": [],
         "migration": [{"src": "g.md", "dest": "docs/how-to/g.md", "ops": ["move"], "impact": None}]}
    html = render_report(d, "plan")
    assert "작업 절차·복구 (how-to)" in html      # mig-agg 그룹명
```

- [ ] **Step 2: 실패 확인** — `uv run --with pytest pytest test_render_report.py -k "howto_label or howto_group_label" -q` · Expected: FAIL.

- [ ] **Step 3: 구현** — `render_report.py` 두 곳:
  - `_render_trees`의 tkey 줄: `'<span><b class="k-howto">■</b> 가이드(how-to)</span>'` → `'<span><b class="k-howto">■</b> 작업 절차·복구(how-to)</span>'`.
  - `_TYPE_GROUP`의 how-to: `"how-to": ("가이드·절차 (how-to)", "tc-howto"),` → `"how-to": ("작업 절차·복구 (how-to)", "tc-howto"),`.

- [ ] **Step 4: 통과 확인** — `uv run --with pytest pytest test_render_report.py -k "howto_label or howto_group_label" -q` · Expected: **2 passed**.

- [ ] **Step 5: 커밋**

```bash
git add skills/setup-docs/scripts/render_report.py skills/setup-docs/scripts/test_render_report.py
git commit -m "📝 fix(render): how-to 라벨을 '작업 절차·복구'로 정직화(트러블슈팅 은폐 방지)"
```

---

### Task 4: before 트리를 중첩 스캐폴딩으로 (C1)

**Files:**
- Modify: `skills/doc-health/scripts/scorecard.py` (`_before_tree` + 신규 `_nested_lines`)
- Test: `skills/doc-health/scripts/test_scorecard.py`

**Interfaces:**
- Produces: `_before_tree(files) -> {..., "lines":[[text,cls],...]}` — flat stray 리스트가 아니라 중첩 폴더(폴더=`[text,None]`+개수, 파일=`[text,"stray"]`).

- [ ] **Step 1: 실패 테스트 작성** (append to test_scorecard.py)

```python
def test_before_tree_is_nested_scaffolding_not_flat():
    files = ["src/features/custom/shared/docs/a.md",
             "src/features/custom/shared/docs/b.md",
             "api-help.md"]
    t = scorecard._before_tree(files)
    texts = [line[0] for line in t["lines"]]
    # 중첩: 상위 폴더 라인(src/·features/ 등)이 개수와 함께 존재(평면이면 없음)
    assert any(s.strip().startswith("src/") and "(" in s for s in texts)
    assert any(s.strip().startswith("docs/") and "(" in s for s in texts)
    # 파일은 stray 클래스, 폴더는 무색
    assert any(cls == "stray" for _txt, cls in t["lines"])
    assert any(cls is None for _txt, cls in t["lines"])
    # 들여쓰기(중첩) 존재
    assert any(s.startswith("  ") for s in texts)
```

- [ ] **Step 2: 실패 확인** — `cd skills/doc-health/scripts && uv run --with pytest pytest test_scorecard.py -k before_tree_is_nested -q` · Expected: FAIL(현재 평면이라 폴더+개수·들여쓰기 없음).

- [ ] **Step 3: 구현** — `scorecard.py`에 `_nested_lines` 추가 + `_before_tree` 수정:

```python
def _nested_lines(paths):
    """repo-상대 경로들 → 중첩 폴더 트리 lines. 폴더=[text(개수),None]·파일=[text,'stray']."""
    root = {}
    for p in sorted(paths):
        parts = p.split("/")
        node = root
        for seg in parts[:-1]:
            node = node.setdefault(seg, {})
        node.setdefault("__f__", []).append(parts[-1])

    def count(n):
        c = len(n.get("__f__", []))
        for k, v in n.items():
            if k != "__f__":
                c += count(v)
        return c

    lines = []

    def walk(node, pre):
        for d in sorted(k for k in node if k != "__f__"):
            lines.append([f"{pre}{d}/  ({count(node[d])})", None])
            walk(node[d], pre + "  ")
        for fn in sorted(node.get("__f__", [])):
            lines.append([f"{pre}{fn}", "stray"])

    walk(root, "")
    return lines


def _before_tree(files):
    outside = outside_content(files)
    lines = _nested_lines(outside)          # 평면 stray 리스트 → 중첩 스캐폴딩(파묻힘 가시화)
    sub = (f"docs/ 밖 흩어짐 · content {len(outside)}건" if outside
           else "docs/ 중심")
    return {"title": "현재 구조", "tag": "지금", "sub": sub, "lines": lines}
```

- [ ] **Step 4: 통과 확인** — Run:
  - `uv run --with pytest pytest test_scorecard.py -k before_tree_is_nested -q` · Expected: **1 passed**.
  - 전체 회귀: `cd skills/doc-health/scripts && uv run --with pytest pytest -q` · Expected: 30(+신규) GREEN.

- [ ] **Step 5: 커밋**

```bash
git add skills/doc-health/scripts/scorecard.py skills/doc-health/scripts/test_scorecard.py
git commit -m "✨ feat(scorecard): before 트리를 중첩 스캐폴딩으로(파묻힌 구조 가시화, C1)"
```

---

### Task 5: SKILL 산문 배선 + FINDINGS + 전체 게이트/회귀

**Files:**
- Modify: `skills/setup-docs/SKILL.md` (Phase 2 산문)
- Modify: `FINDINGS.md`

**Interfaces:** 없음(산문).

- [ ] **Step 1: SKILL.md Phase 2 산문에 preexisting_broken 배선 명시** — 현재 "Phase 2(계획 아티팩트)" 항목에 한 줄 추가: `assemble_plan_data(health, move_plan, decisions, preexisting_broken=build_and_verify 결과의 preexisting_broken)`로 호출해 **플랜 아티팩트가 "기존에 깨져 있던 링크"를 승인 전 표면화**(콜아웃 아님 — 이동-유발 위험은 new_broken=0 게이트로 이미 차단). how-to 라벨은 "작업 절차·복구".
- [ ] **Step 2: FINDINGS 갱신** — 아티팩트 보정(A preexisting plan 표면화·라벨·C1 before 중첩) 완료 기록. B(규모)·C2(트리접이식)는 architect 검증으로 defer(중복/저부가) 명시. 트러블슈팅 B는 doc-type 트랙 유지.
- [ ] **Step 3: 게이트 + 양 러너 회귀** — Run:
  - `python3 skills/setup-docs/scripts/gate.py . --require-markers` · Expected: `PASS broken=0 orphan=0 ... markers_ok=True`.
  - `cd skills/setup-docs/scripts && uv run --with pytest pytest -q` · Expected: 기존 + 신규 GREEN.
  - `cd skills/doc-health/scripts && uv run --with pytest pytest -q` · Expected: 기존 + 신규 GREEN.
- [ ] **Step 4: 신규 계획서·문서 인덱스 등록 확인** — 이 계획서(`docs/plans/2026-07-09-artifact-selfdescribe-fixes.md`)를 `docs/plans/`(README/인덱스)에 등록(고아 방지). gate orphan=0 재확인.
- [ ] **Step 5: 커밋**

```bash
git add skills/setup-docs/SKILL.md FINDINGS.md docs/plans/
git commit -m "📝 docs(skill/findings): 아티팩트 보정 배선(preexisting plan 표면화·라벨·before중첩) + defer 기록"
```

---

## Self-Review (작성자 체크)

**1. 스코프 커버리지:**
- A(플랜 preexisting 표면화) → Task 1(데이터: build_and_verify 반환+assemble 전달) + Task 2(렌더: _render_preexisting 공통) + Task 5(SKILL 배선). **impact/콜아웃 무수정**(architect 지적 반영).
- 라벨(how-to 정직화) → Task 3(tkey + _TYPE_GROUP 둘 다).
- C1(before 중첩) → Task 4(scorecard._before_tree + _nested_lines).
- Defer(B 규모라인·C2 트리접이식) → Task 5 FINDINGS에 근거와 함께 명시(구현 안 함).

**2. 플레이스홀더 스캔:** 코드 스텝 전부 실제 코드. 산문 스텝(Task 5)은 항목 구체 열거. TBD 없음.

**3. 타입 정합성:** `build_and_verify`→`{...,preexisting_broken:[(rel,raw)]}` ↔ `assemble_plan_data(preexisting_broken=...)`→`data["preexisting_broken"]` ↔ `render_report._render_main`이 `data.get("preexisting_broken")`→`_render_preexisting(items=[(rel,raw)])` 소비 일치. `_nested_lines(paths)`→lines[[text,cls]] ↔ `_before_tree`가 render_report `_tree_pre`가 소비하는 `[[text,cls]]` 형식과 일치. impact 필드는 어느 태스크도 안 건드림(불가침 준수).

## Execution Handoff

**Plan complete and saved to `docs/plans/2026-07-09-artifact-selfdescribe-fixes.md`.**
