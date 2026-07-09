# 아티팩트 B(규모 라인)·C2(접이식 전체 스캐폴딩) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 진단 아티팩트(plan 모드)에 ① 이동 규모·고아(미도달) 감소·유실0을 한 줄로 보여주는 "규모 라인"(B)과 ② 이동되는 전체 파일을 Before→After 2단·타입색으로 펼쳐 보는 접이식 스캐폴딩(C2)을 추가한다.

**Architecture:** B는 데이터 배선(doc-health `assemble()`가 orphan 수를 구조화 방출 → `migrate.assemble_plan_data`가 orphans_before/after를 data에 실음 → `render_report._render_migration`이 `.mig-head` 렌더) + 정직성(orphans_after는 `build_and_verify`가 검증한 실제 값, 유실0은 content_oracle 불변식). C2는 순수 render 변경(before=migration src 목록, after=migration dest 목록 — 둘 다 move_plan 파생, 새 doc-health 데이터 불필요). 기존 `.tree .t-*` CSS와 `_tree_pre`를 재사용해 새 타입색 CSS·AA쌍을 만들지 않는다.

**Tech Stack:** Python 3.14, pytest(uv), 자기완결 HTML/CSS 렌더러(render_report.py 동결 품질 게이트: 인라인 style 0·div 밸런스·WCAG AA 대비 양테마).

## Global Constraints

- **정직(North Star).** 규모 라인의 모든 수치는 실측·검증값이어야 한다. `orphans_after`는 `build_and_verify` 결과의 `"orphan"`(스크래치 검증값), `orphans_before`는 Phase 0 진단의 `len(res.orphans)`. "유실 0"은 content_oracle 불변식의 표현(추측 아님).
- **impact 축 불가침.** 이 작업은 `impact`(에이전트 저작 이동-유발 위험)·`preexisting_broken`(엔진 검출) 축을 건드리지 않는다. 규모 라인은 별개 표시 요소다.
- **동결 렌더 게이트.** 추가 후에도 `test_render_report.py` 전부 green: 인라인 `style="` 0, `<div>`/`</div>` 밸런스, `test_contrast_aa_both_themes`(AA_PAIRS ≥ 명시 비율).
- **정본 리터럴 0.** render_report·migrate·scorecard 정본에 vd-front 등 특정 repo 도메인 리터럴을 넣지 않는다(표시 문자열은 범용).
- **테스트 러너:** `cd skills/setup-docs/scripts && uv run --with pytest pytest -q` · `cd skills/doc-health/scripts && uv run --with pytest pytest -q`.
- **surgical.** 데모(`render_vdfront.py`)에서 검증된 형태를 정본에 이식하되, 기존 함수/스타일 관습을 따른다. 인접 코드 리팩터 금지.

---

### Task 1: B 데이터 배선 (orphan 수치 구조화 + assemble_plan_data 전달)

**Files:**
- Modify: `skills/doc-health/scripts/scorecard.py` (assemble() out dict, ~line 196-205)
- Modify: `skills/setup-docs/scripts/migrate.py` (assemble_plan_data 시그니처·본문, ~line 539-551)
- Test: `skills/doc-health/scripts/test_scorecard.py`
- Test: `skills/setup-docs/scripts/test_migrate.py`

**Interfaces:**
- Consumes: `gate.analyze(root).orphans`(list) — Phase 0 미도달 문서. `build_and_verify(...)["orphan"]`(int) — 스크래치 검증 후 orphan 수(정상 계획이면 0).
- Produces:
  - `scorecard.assemble(...)` 반환 dict에 `"orphans": int`(= `len(res.orphans)`) 키 추가.
  - `migrate.assemble_plan_data(health, move_plan, decisions=None, preexisting_broken=None, orphans_after=None)` — 반환 data에 `data["orphans_before"] = health.get("orphans")`, `data["orphans_after"] = orphans_after` 추가. (기존 파라미터·키 전부 불변.)

- [ ] **Step 1: doc-health orphan 방출 RED 테스트**

`skills/doc-health/scripts/test_scorecard.py` 끝에 추가:

```python
def test_assemble_emits_structured_orphan_count(tmp_path):
    # 고아 문서(라우터에서 도달 불가)가 있는 repo → orphans 정수 방출
    (tmp_path / "AGENTS.md").write_text("# router\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "orphan.md").write_text("# not linked\n", encoding="utf-8")
    files = ["AGENTS.md", "docs/orphan.md"]
    d = scorecard.assemble(tmp_path, files, _judg("fail", "pass", "pass", "pass"))
    assert isinstance(d["orphans"], int)
    assert d["orphans"] == 1
```

- [ ] **Step 2: RED 확인**

Run: `cd skills/doc-health/scripts && uv run --with pytest pytest test_scorecard.py::test_assemble_emits_structured_orphan_count -q`
Expected: FAIL (`KeyError: 'orphans'`)

- [ ] **Step 3: scorecard.assemble()에 orphans 키 추가**

`skills/doc-health/scripts/scorecard.py`의 `assemble()` `out` dict에서 `"posture"` 줄 다음에 한 줄 추가:

```python
    out = {
        "repo": {"name": Path(root).resolve().name,
                 "docs_count": len(files),
                 "branch": _git_branch(root)},
        "grade": {"current": grade, "target": "A"},
        "counts": counts(mech, judgment),
        "scorecard": {"mechanical": mech, "judgment": judgment},
        "trees": {"before": _before_tree(files)},
        "posture": posture_hint(res, files, mech),
        "orphans": len(res.orphans),
    }
```

- [ ] **Step 4: GREEN 확인 (+ 회귀 없음)**

Run: `cd skills/doc-health/scripts && uv run --with pytest pytest -q`
Expected: 신규 포함 전부 PASS (기존 assemble 테스트가 `set(d) >= {...}`라 키 추가에 불변).

- [ ] **Step 5: assemble_plan_data orphan 전달 RED 테스트**

`skills/setup-docs/scripts/test_migrate.py`에 추가 (기존 assemble_plan_data 테스트 근처):

```python
def test_assemble_plan_data_carries_orphan_before_and_after():
    from migrate import assemble_plan_data
    health = {"trees": {}, "orphans": 12}
    move_plan = [{"src": "a.md", "dest": "docs/reference/a.md", "ops": ["move"], "impact": None}]
    data = assemble_plan_data(health, move_plan, orphans_after=0)
    assert data["orphans_before"] == 12
    assert data["orphans_after"] == 0

def test_assemble_plan_data_orphan_defaults_when_absent():
    from migrate import assemble_plan_data
    data = assemble_plan_data({"trees": {}}, [])
    assert data["orphans_before"] is None
    assert data["orphans_after"] is None
```

- [ ] **Step 6: RED 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_migrate.py::test_assemble_plan_data_carries_orphan_before_and_after -q`
Expected: FAIL (`TypeError: unexpected keyword argument 'orphans_after'`)

- [ ] **Step 7: assemble_plan_data 시그니처·본문 수정**

`skills/setup-docs/scripts/migrate.py`의 `assemble_plan_data`:

```python
def assemble_plan_data(health, move_plan, decisions=None, preexisting_broken=None, orphans_after=None):
    """doc-health 부분 dict → render_report plan 계약(trees.after·migration·decisions·preexisting_broken·orphans 추가).

    preexisting_broken(엔진 검출 "이동 전부터 깨져 있던 링크", [(rel,raw)])은 impact(에이전트 저작
    "이동-유발 위험")와 다른 축이라 별도 키로 둔다 — 콜아웃 아니라 _render_preexisting 섹션으로 렌더된다.
    orphans_before(health의 Phase 0 고아 수)·orphans_after(build_and_verify 검증값)는 규모 라인(.mig-head)용."""
    data = dict(health)
    data["trees"] = dict(data.get("trees", {}))
    data["trees"]["after"] = _after_tree(move_plan)
    data["migration"] = list(move_plan)
    data["decisions"] = list(decisions or [])
    data["preexisting_broken"] = list(preexisting_broken or [])
    data["orphans_before"] = health.get("orphans")
    data["orphans_after"] = orphans_after
    data.setdefault("summary", {})
    return data
```

- [ ] **Step 8: GREEN 확인 (+ 회귀 없음)**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`
Expected: 신규 2개 포함 전부 PASS.

- [ ] **Step 9: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add skills/doc-health/scripts/scorecard.py skills/doc-health/scripts/test_scorecard.py skills/setup-docs/scripts/migrate.py skills/setup-docs/scripts/test_migrate.py
git commit -m "✨ feat(health/migrate): orphan 수 구조화 방출 + assemble_plan_data orphans_before/after 전달(B 규모라인 데이터)"
```

---

### Task 2: B 렌더 (이동 규모 라인 `.mig-head`)

**Files:**
- Modify: `skills/setup-docs/scripts/render_report.py` (`_render_migration` ~line 366-407, TEMPLATE_CSS)
- Test: `skills/setup-docs/scripts/test_render_report.py` (신규 테스트 + AA_PAIRS)

**Interfaces:**
- Consumes: `data["migration"]`(list), `data.get("orphans_before")`(int|None), `data.get("orphans_after")`(int|None).
- Produces: migration `<section>`의 `.card` 최상단에 `<div class="mig-head">…</div>` 삽입. orphan 세그먼트는 두 값이 모두 not None일 때만.

- [ ] **Step 1: 규모 라인 RED 테스트**

`skills/setup-docs/scripts/test_render_report.py`에 추가:

```python
def test_migration_head_shows_scale_and_orphan_win():
    d = {**MIN, "migration": [
            {"src": "a.md", "dest": "docs/reference/a.md", "ops": ["move"], "impact": None},
            {"src": "b.md", "dest": "docs/how-to/b.md", "ops": ["move"], "impact": None}],
         "orphans_before": 12, "orphans_after": 0}
    html = render_report(d, "plan")
    assert 'class="mig-head"' in html
    assert "2개" in html                      # 이동 규모 = len(migration)
    assert "고아" in html and "12" in html and "0" in html   # 고아 12 → 0
    assert "유실 0" in html
    assert html.count("<div") == html.count("</div>")

def test_migration_head_omits_orphan_segment_when_absent():
    d = {**MIN, "migration": [
            {"src": "a.md", "dest": "docs/reference/a.md", "ops": ["move"], "impact": None}]}
    html = render_report(d, "plan")
    assert 'class="mig-head"' in html         # 규모 라인 자체는 나옴(이동/유실)
    assert "고아" not in html.split('class="mig-head"')[1].split("</div>")[0]  # orphan 세그먼트만 생략
    assert html.count("<div") == html.count("</div>")
```

- [ ] **Step 2: RED 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_render_report.py::test_migration_head_shows_scale_and_orphan_win -q`
Expected: FAIL (`class="mig-head"` 없음)

- [ ] **Step 3: `_render_migration`에 규모 라인 삽입**

`skills/setup-docs/scripts/render_report.py`의 `_render_migration`에서 `impacts = ...` 위에 규모 라인 조립을 추가하고, `.card` 여는 부분에 삽입한다. 기존:

```python
    impacts = [r for r in mig if r.get("impact")]
```

를 아래로 교체(규모 라인 조립을 앞에 추가):

```python
    ob, oa = data.get("orphans_before"), data.get("orphans_after")
    orphan_seg = (f' · <b class="win">고아(미도달) {esc(ob)} → {esc(oa)}</b>'
                  if ob is not None and oa is not None else "")
    mig_head = (f'<div class="mig-head"><b>{len(mig)}개 옮김</b>{orphan_seg}'
                f' · <span class="ok">전체 내용 그대로 보존(유실 0)</span></div>')
    impacts = [r for r in mig if r.get("impact")]
```

그리고 `.card` 여는 부분:

```python
            f'<div class="card"><div class="mig-agg">{"".join(rows)}</div>{callout}'
```

을:

```python
            f'<div class="card">{mig_head}<div class="mig-agg">{"".join(rows)}</div>{callout}'
```

- [ ] **Step 4: 규모 라인 CSS 추가**

`render_report.py`의 TEMPLATE_CSS에서 `.mig-agg` 관련 규칙 근처(예: `.mig-grp` 규칙들 뒤)에 추가:

```css
  .mig-head { font-size:13px; margin:0 0 var(--s3); color:var(--ink); }
  .mig-head .win { color:var(--pass-ink); }
  .mig-head .ok { color:var(--muted); }
```

- [ ] **Step 5: 새 색상쌍 AA 커버리지 추가**

`test_render_report.py`의 `AA_PAIRS` 리스트에 `.win`(--pass-ink) on `.card`(--panel) 쌍 추가:

```python
AA_PAIRS = [
    ("--faint", "--panel", 4.5), ("--faint", "--bg", 4.5),
    ("--muted", "--panel", 4.5),
    ("--accent-ink", "--accent-soft", 4.5), ("--accent-ink", "--bg", 4.5),
    ("--warn-ink", "--warn-soft", 4.5),
    ("--fail-ink", "--fail-soft", 4.5), ("--fail-ink", "--panel", 4.5),
    ("--pass-ink", "--pass-soft", 4.5),
    ("--pass-ink", "--panel", 4.5),
]
```

- [ ] **Step 6: GREEN 확인 (규모 라인 + AA 양테마 + 회귀)**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_render_report.py -q`
Expected: 신규 2개 + `test_contrast_aa_both_themes`(새 쌍 포함) 전부 PASS. AA 실패 시 STOP — `.win` 색을 --pass-ink로 유지하되 배경 가정이 틀렸는지 확인(규모 라인은 `.card` = --panel 위).

- [ ] **Step 7: 전체 회귀 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`
Expected: 전부 PASS.

- [ ] **Step 8: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add skills/setup-docs/scripts/render_report.py skills/setup-docs/scripts/test_render_report.py
git commit -m "✨ feat(render): 이동 규모 라인(.mig-head) — 옮김수·고아 감소·유실0(B)"
```

---

### Task 3: C2 렌더 (접이식 전체 스캐폴딩 Before→After 2단)

**Files:**
- Modify: `skills/setup-docs/scripts/render_report.py` (신규 `_scaffold_lines` 헬퍼 + `_render_trees` 주입, TEMPLATE_CSS 레이아웃만)
- Test: `skills/setup-docs/scripts/test_render_report.py`

**Interfaces:**
- Consumes: `data["migration"]`(list of {src,dest,...}). before 경로 = 각 행 `src`, after 경로 = 각 행 `dest`.
- Produces: `_render_trees` 반환 `</section>` 직전에 `<details class="scaffold">…</details>` 추가. 기존 `.tree pre`·`.tree .t-*` CSS 재사용(새 타입색 CSS·AA쌍 없음).

- [ ] **Step 1: 접이식 스캐폴딩 RED 테스트**

`test_render_report.py`에 추가:

```python
def test_trees_have_collapsible_full_scaffold():
    d = {**MIN, "migration": [
            {"src": "guides/setup.md", "dest": "docs/how-to/setup.md", "ops": ["move"], "impact": None},
            {"src": "old/adr-1.md", "dest": "docs/decisions/adr-1.md", "ops": ["move"], "impact": None}]}
    html = render_report(d, "plan")
    assert 'class="full scaffold"' in html
    assert "<details" in html and "전체 파일 스캐폴딩" in html
    # before(원본 경로)·after(dest 경로) 둘 다 등장 — 트리는 폴더별 들여쓰기 라인이라
    # "docs/how-to/" 연속이 아니라 "docs/"·"how-to/"가 별도 라인으로 나온다.
    assert "guides/" in html and "setup.md" in html      # before 원본 위치
    assert "how-to/" in html                             # after 타입 폴더
    # after 타입색 클래스 재사용(how-to→t-howto)
    assert 't-howto"' in html
    assert html.count("<div") == html.count("</div>")
    assert html.count("<details") == html.count("</details>")
```

- [ ] **Step 2: RED 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_render_report.py::test_trees_have_collapsible_full_scaffold -q`
Expected: FAIL (`full scaffold` 없음)

- [ ] **Step 3: `_scaffold_lines` 헬퍼 추가**

`render_report.py`의 `_render_trees` 위에 추가:

```python
_SCAFFOLD_TYPECLS = {"product": "t-prd", "specs": "t-spec",
                     "decisions": "t-adr", "how-to": "t-howto"}
def _scaffold_lines(paths, colored):
    """flat 경로 리스트 → 중첩 트리 lines([[text, cls], ...]), 절단 없음(전체 파일).
    colored=True면 docs/<type>/ 폴더를 타입색 클래스로(after 측). 파일·기타 폴더는 무색."""
    tree = {}
    for p in paths:
        parts = p.split("/")
        node = tree
        for d in parts[:-1]:
            node = node.setdefault(d, {})
        node.setdefault("__f__", []).append(parts[-1])
    lines = []
    def walk(node, prefix, pathparts):
        for d in sorted(k for k in node if k != "__f__"):
            full = pathparts + [d]
            cls = None
            if colored and len(full) >= 2 and full[0] == "docs":
                cls = _SCAFFOLD_TYPECLS.get(full[1])
            lines.append([prefix + d + "/", cls])
            walk(node[d], prefix + "  ", full)
        for fn in sorted(node.get("__f__", [])):
            lines.append([prefix + fn, None])
    walk(tree, "", [])
    return lines
```

- [ ] **Step 4: `_render_trees`에 접이식 스캐폴딩 주입**

`render_report.py`의 `_render_trees` 반환문에서 마지막 `</section>` 직전에 스캐폴딩을 끼운다. 기존 반환문의 tkey 블록 끝:

```python
            '<span><b class="k-legacy">■</b> 동결(legacy)</span></div></section>')
```

을 아래로 교체(먼저 함수 상단에서 mig 경로 추출):

`_render_trees` 본문 시작(`t = data["trees"]`) 직후에 추가:

```python
    mig = data.get("migration") or []
    scaffold = ""
    if mig:
        before_lines = _scaffold_lines([r["src"] for r in mig], False)
        after_lines = _scaffold_lines([r["dest"] for r in mig], True)
        scaffold = (
            '<details class="full scaffold"><summary>전체 파일 스캐폴딩 펼치기 '
            '(Before → After · 타입색)</summary><div class="sc-cols">'
            '<div class="tree sc-col"><h4>현재 (원본 위치 — 파묻힘)</h4>'
            f'<pre>{_tree_pre(before_lines)}</pre></div>'
            '<div class="tree sc-col"><h4>정리 후 (타입별)</h4>'
            f'<pre>{_tree_pre(after_lines)}</pre></div>'
            '</div></details>')
```

그리고 반환문 마지막 줄 교체:

```python
            '<span><b class="k-legacy">■</b> 동결(legacy)</span></div>'
            f'{scaffold}</section>')
```

- [ ] **Step 5: 스캐폴딩 레이아웃 CSS 추가 (색상 신규 없음)**

TEMPLATE_CSS에 추가(예: `.tree .t-dir` 규칙 뒤):

```css
  details.scaffold { margin:var(--s4) 0 0; }
  details.scaffold summary { cursor:pointer; font-size:12px; color:var(--muted); }
  details.scaffold .sc-cols { display:grid; grid-template-columns:1fr 1fr; gap:var(--s3); padding:var(--s3) 0 0; }
  details.scaffold .sc-col { border:1px solid var(--line); border-radius:var(--r-sm); }
  details.scaffold .sc-col h4 { font-size:12px; font-weight:600; margin:0 0 var(--s2); color:var(--ink); }
  details.scaffold .sc-col pre { max-height:56vh; }
  @media (max-width:680px) { details.scaffold .sc-cols { grid-template-columns:1fr; } }
```

- [ ] **Step 6: GREEN 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_render_report.py::test_trees_have_collapsible_full_scaffold -q`
Expected: PASS.

- [ ] **Step 7: 전체 회귀 + 게이트 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`
Expected: 전부 PASS(인라인 style 0·div 밸런스·AA 포함).

- [ ] **Step 8: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add skills/setup-docs/scripts/render_report.py skills/setup-docs/scripts/test_render_report.py
git commit -m "✨ feat(render): 접이식 전체 스캐폴딩 Before→After 2단·타입색(C2) — 기존 .tree CSS 재사용"
```

---

### Task 4: SKILL 배선 + 문서 갱신 (orphans_after 전달 · defer 해제 기록)

**Files:**
- Modify: `skills/setup-docs/SKILL.md` (Phase 2 assemble_plan_data 호출 산문)
- Modify: `FINDINGS.md` (B·C2 구현 완료로 defer 기록 supersede)
- Modify: `docs/plans/README.md` (본 계획 등록)

**Interfaces:**
- Consumes: Task 1의 `assemble_plan_data(..., orphans_after=...)` 시그니처.
- Produces: SKILL Phase 2 산문이 `orphans_after=<Phase 1b build_and_verify 결과>["orphan"]`를 넘기도록 서술.

- [ ] **Step 1: SKILL.md Phase 2 산문에 orphans_after 배선 추가**

`skills/setup-docs/SKILL.md`에서 `assemble_plan_data(...)`를 서술하는 Phase 2 문단을 찾아, `preexisting_broken=` 인자 옆에 `orphans_after=` 배선을 추가한다(기존 preexisting_broken 서술과 동일한 위치·톤). 예시 문구:

```markdown
`assemble_plan_data(health, move_plan, decisions=..., preexisting_broken=<Phase 1b 결과>, orphans_after=<Phase 1b build_and_verify 결과>["orphan"])`로 조립한다.
`orphans_after`는 스크래치 검증된 이동 후 고아 수(정상 계획이면 0)로, health의 orphans_before(Phase 0 진단)와 함께 규모 라인에 "고아 N→0"으로 표시된다 — 이동-유발 위험 콜아웃이 아니라 도달성 개선의 실측 표시다.
```

- [ ] **Step 2: SKILL 게이트 확인(회귀 없음)**

Run: `cd "$(git rev-parse --show-toplevel)" && cd skills/setup-docs/scripts && uv run --with pytest pytest -q && cd ../../doc-health/scripts && uv run --with pytest pytest -q`
Expected: 두 러너 전부 PASS(산문 변경이라 코드 회귀 없음).

- [ ] **Step 3: 셀프-게이트(도달성·마커) 확인**

Run: `cd "$(git rev-parse --show-toplevel)" && uv run --with pytest skills/setup-docs/scripts/gate.py . 2>/dev/null || python3 skills/setup-docs/scripts/gate.py .`
Expected: broken=0 · orphan=0 · markers_ok=True (본 변경은 문서/코드 추가라 도달성 불변).

- [ ] **Step 4: FINDINGS.md defer 기록 supersede**

`FINDINGS.md` 최상단의 아티팩트 보정 항목에서 "B(규모라인)·C2(트리접이식) defer" 기록을, "B·C2 구현 완료(사용자 명시 요청으로 architect defer 해제)"로 갱신. 근거 한 줄: B는 orphan 데이터 배선(doc-health orphans 방출 → assemble_plan_data → .mig-head), C2는 순수 render(migration src/dest 파생, 기존 .tree CSS 재사용). 정직성: orphans_after=검증값, 유실0=content_oracle 불변식.

- [ ] **Step 5: docs/plans/README.md에 본 계획 등록**

`docs/plans/README.md`의 "진단-주도 마이그레이션" 섹션 아래(2026-07-09-artifact-selfdescribe-fixes.md 항목 다음)에 한 줄 추가:

```markdown
- [2026-07-09-artifact-magnitude-scaffold.md](2026-07-09-artifact-magnitude-scaffold.md) — 아티팩트 B(이동 규모 라인 .mig-head: 옮김수·고아 N→0·유실0)·C2(접이식 전체 스캐폴딩 Before→After 2단·타입색). architect defer를 사용자 명시 요청으로 해제. orphan 데이터 배선(doc-health orphans 방출) + 순수 render(기존 .tree CSS 재사용).
```

- [ ] **Step 6: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add skills/setup-docs/SKILL.md FINDINGS.md docs/plans/README.md
git commit -m "📝 docs(skill/findings): orphans_after 배선 산문 + B·C2 defer 해제 기록 + 계획 등록"
```

---

## 완료 기준

- doc-health `assemble()`가 `orphans`(int) 방출, `assemble_plan_data`가 `orphans_before`/`orphans_after` 실음.
- plan 모드 아티팩트에 `.mig-head` 규모 라인(옮김수·고아 N→0·유실0)과 접이식 `<details class="scaffold">` 2단 스캐폴딩이 렌더됨.
- `test_render_report.py` 전 게이트 green(인라인 style 0·div/details 밸런스·AA 양테마), setup-docs·doc-health 두 러너 green, 셀프-게이트 PASS.
- SKILL Phase 2가 orphans_after 배선을 서술, FINDINGS가 defer 해제를 기록.
