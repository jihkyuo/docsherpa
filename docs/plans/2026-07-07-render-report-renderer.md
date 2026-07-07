# render_report 렌더러 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 진단/계획 데이터(dict) → 자기완결 HTML 아티팩트를 결정론적으로 렌더하는 공유 스크립트를 만든다. 매 실행 동일 품질을 대비(WCAG AA)·구조·이스케이프 테스트로 보장한다.

**Architecture:** stdlib-only Python(`gate.py`·`content_oracle.py`와 동급). 동결 CSS 상수 + 섹션별 순수 렌더 함수 + `html.escape`. `plan`(Phase 2)·`result`(Phase 4) 모드. 저작 원본 = 이미 hand-tune + AA 실측 + codex 검증한 목업(`~/Downloads/docsherpa-phase2-diagnosis-mockup.html`).

**Tech Stack:** Python 3 stdlib (`html`, `json`), pytest.

## Global Constraints

- **stdlib-only** — jinja2 등 외부 템플릿 엔진 금지(`gate.py` 패턴).
- **자기완결 출력** — 출력 HTML에 외부 리소스 참조 0(`http`·`src=`·`@import`·웹폰트 URL 금지). Artifact 래퍼가 `<!doctype>/<head>/<body>`를 감싸므로 렌더러는 `<title>+<style>+<main>` 프래그먼트만 낸다.
- **인라인 스타일 0** — 출력에 `style="` 금지(전부 클래스).
- **테마 대응 동결 CSS** — `prefers-color-scheme` + `:root[data-theme]` 양방향. 토큰 대비 소형 텍스트 ≥4.5:1, 대형(≥24px 또는 ≥18.66px bold) ≥3:1.
- **위치:** `skills/setup-docs/scripts/render_report.py` (기존 스크립트·pytest 하니스와 동거). 테스트 `skills/setup-docs/scripts/test_render_report.py`. 논리적으로는 공유(doc-health 착수 시 위치 재고).
- **테스트 러너:** `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`.

---

## 데이터 모델 (인터페이스 — doc-health가 생산, render가 소비)

```python
# render_report(data: dict, mode: str) -> str   (mode: "plan" | "result")
DATA = {
  "repo": {"name": "vd-front", "docs_count": 69, "branch": "develop"},
  "grade": {"current": "F", "target": "A"},              # 'A'..'F'
  "counts": {"fail": 7, "warn": 2, "pass": 0},           # 현재 차원 상태 집계
  "scorecard": {
    "mechanical": [
      {"code": "M1", "name": "도달성", "sub": "broken=0·orphan=0 미달 · 고아 12", "status": "fail"},
      # ... M2..M5
    ],
    "judgment": [
      {"code": "J1", "name": "문서타입 분류", "sub": "decisions/ home 없음·root 미분류", "status": "warn"},
      # ... J2..J4
    ],
  },
  "trees": {
    "before": {"title": "산재", "tag": "지금", "sub": "docs/ 밖 흩어짐 · 고아 12", "lines": [["api-help.md", "stray"], ["docs/", None], ...]},
    "after":  {"title": "docs/ 중앙집중", "tag": "목표", "sub": "고아 0 · 도달성 100%", "lines": [["docs/", None], ["  _map.md", "new"], ...]},
  },
  "migration": [
    {"src": "api-help.md", "dest": "docs/reference/api-help.md", "ops": ["move"], "impact": None},
    {"src": "src/features/custom/shared/docs/**", "dest": "docs/specs/custom/", "ops": ["move"],
     "impact": "custom-specs-sync grep 경로·코드 상대참조 깨짐 → 승인 후 사용자 갱신 필요"},
  ],
  "decisions": [
    {"no": 1, "tag": "정합성", "tag_kind": "warn",
     "question": "tech-stack 정본 값 — 두 문서가 서로 다른 값을 주장합니다. 어느 값이 맞나요?",
     "choices": [
       {"label": "값 A", "value": "node-linker = hoisted", "detail": "hoisted 링커 사용", "src": "docs/CLAUDE.md", "recommended": False},
       {"label": "값 B", "value": "isolated", "detail": "pnpm 기본 isolated", "src": "루트 CLAUDE.md", "recommended": False},
     ]},
  ],
  "summary": {  # result 모드 전용
    "moved": 53, "orphans_before": 12, "orphans_after": 0, "outside_before": 45, "outside_after": 0,
    "loop_installed": True, "residual": [],   # residual: A 미달 시 남은 항목 리스트
  },
}
```

`status` 값은 `"fail"|"warn"|"pass"`. `tag_kind` 는 `"warn"|"struct"`. tree `lines` 는 `[텍스트, 클래스|None]` 쌍(`"stray"|"new"|"grp"|None`).

---

### Task 1: 렌더러 골격 + 동결 CSS + 자기완결 보증

**Files:**
- Create: `skills/setup-docs/scripts/render_report.py`
- Test: `skills/setup-docs/scripts/test_render_report.py`

**Interfaces:**
- Produces: `render_report(data: dict, mode: str = "plan") -> str` — `<title>…</title><style>…</style><main>…</main>` 프래그먼트. `TEMPLATE_CSS: str` 모듈 상수.

- [ ] **Step 1: 실패 테스트 작성** — 자기완결·구조 불변식.

```python
# test_render_report.py
import re
from render_report import render_report

MIN = {"repo": {"name": "r", "docs_count": 0, "branch": "b"},
       "grade": {"current": "F", "target": "A"}, "counts": {"fail": 0, "warn": 0, "pass": 0},
       "scorecard": {"mechanical": [], "judgment": []},
       "trees": {"before": {"title": "", "tag": "지금", "sub": "", "lines": []},
                 "after": {"title": "", "tag": "목표", "sub": "", "lines": []}},
       "migration": [], "decisions": [], "summary": {}}

def test_output_is_self_contained_fragment():
    html = render_report(MIN, "plan")
    assert "<style>" in html and "<main>" in html
    assert "<title>" in html
    # 외부 리소스·인라인 스타일 0
    assert 'style="' not in html
    assert not re.search(r'src\s*=', html)
    assert "http://" not in html and "https://" not in html
    assert "@import" not in html

def test_div_balance():
    html = render_report(MIN, "plan")
    assert html.count("<div") == html.count("</div>")
```

- [ ] **Step 2: 실패 확인** — Run: `uv run --with pytest pytest test_render_report.py -q` · Expected: FAIL(`ModuleNotFoundError: render_report`).

- [ ] **Step 3: 최소 구현 + CSS 포팅.**

```python
# render_report.py
import html as _html

def esc(s) -> str:
    return _html.escape("" if s is None else str(s), quote=True)

# 저작 원본(~/Downloads/docsherpa-phase2-diagnosis-mockup.html)의 <style>…</style>
# 안쪽 CSS를 그대로 이 상수에 복사한다(이미 AA 실측·codex 검증됨). 변경 금지 — 토큰만.
TEMPLATE_CSS = r"""
:root { color-scheme: light dark; --bg:#f6f8fa; --panel:#ffffff; /* …목업의 전체 CSS… */ }
/* (목업 <style> 본문 전체를 여기에 복사) */
"""

def render_report(data: dict, mode: str = "plan") -> str:
    body = _render_main(data, mode)
    return f'<title>{esc(data["repo"]["name"])} · 문서 아키텍처 진단</title>\n<style>{TEMPLATE_CSS}</style>\n{body}'

def _render_main(data: dict, mode: str) -> str:
    return "<main></main>"  # 이후 태스크에서 섹션 채움
```

> 포팅 방법: 목업 파일을 열어 `<style>` 시작~`</style>` 직전까지를 `TEMPLATE_CSS` 삼항 따옴표 안에 붙여넣는다. 플레이스홀더 아님 — 실재하는 검증된 자산의 복사다.

- [ ] **Step 4: 통과 확인** — Run: `uv run --with pytest pytest test_render_report.py -q` · Expected: PASS(2 passed).

- [ ] **Step 5: 커밋**

```bash
git add skills/setup-docs/scripts/render_report.py skills/setup-docs/scripts/test_render_report.py
git commit -m "✨ feat(render): 렌더러 골격 + 동결 CSS + 자기완결 보증"
```

---

### Task 2: WCAG AA 대비 가드 (동결 CSS 품질 영구 고정)

**Files:**
- Modify: `skills/setup-docs/scripts/test_render_report.py`

**Interfaces:**
- Consumes: `render_report.TEMPLATE_CSS`.

- [ ] **Step 1: 실패 테스트 작성** — 토큰 쌍이 실제 AA를 만족하는지 CSS에서 파싱해 계산.

```python
def _lin(c): c/=255; return c/12.92 if c<=0.03928 else ((c+0.055)/1.055)**2.4
def _L(hexs):
    h=hexs.lstrip('#'); r,g,b=(int(h[i:i+2],16) for i in (0,2,4))
    return 0.2126*_lin(r)+0.7152*_lin(g)+0.0722*_lin(b)
def _cr(fg,bg):
    a,b=_L(fg),_L(bg); hi,lo=max(a,b),min(a,b); return (hi+0.05)/(lo+0.05)

# (fg_token, bg_token, min_ratio) — 소형 텍스트 4.5, 대형(등급 글자 등) 3.0
AA_PAIRS = [
    ("--faint", "--panel", 4.5), ("--faint", "--bg", 4.5),
    ("--muted", "--panel", 4.5),
    ("--accent-ink", "--accent-soft", 4.5), ("--accent-ink", "--bg", 4.5),
    ("--warn-ink", "--warn-soft", 4.5),
    ("--fail-ink", "--fail-soft", 4.5), ("--fail-ink", "--panel", 4.5),
    ("--pass-ink", "--pass-soft", 4.5),
]

def _tokens_for(theme: str) -> dict:
    # theme: 'light' | 'dark'. :root(라이트 기본) 또는 @media dark 블록의 --x:#hex 파싱.
    import re
    from render_report import TEMPLATE_CSS
    if theme == "light":
        block = TEMPLATE_CSS.split("@media")[0]
    else:
        m = re.search(r'@media \(prefers-color-scheme: dark\)\s*\{(.*?\})\s*\}\s*\}', TEMPLATE_CSS, re.S)
        block = m.group(1) if m else ""
    return dict(re.findall(r'(--[\w-]+):\s*(#[0-9a-fA-F]{6})', block))

def test_contrast_aa_both_themes():
    for theme in ("light", "dark"):
        tok = _tokens_for(theme)
        for fg, bg, mn in AA_PAIRS:
            assert fg in tok and bg in tok, f"{theme}: missing {fg}/{bg}"
            r = _cr(tok[fg], tok[bg])
            assert r >= mn, f"{theme} {fg} on {bg} = {r:.2f} < {mn}"
```

- [ ] **Step 2: 실패 확인** — Run: `uv run --with pytest pytest test_render_report.py::test_contrast_aa_both_themes -q` · Expected: 최초엔 FAIL 가능(정규식이 다크 블록을 못 잡거나 토큰 누락 시). 파서를 CSS 실제 형태에 맞춰 고쳐 GREEN 만든다.

- [ ] **Step 3: 파서 정합** — `_tokens_for`의 정규식을 `TEMPLATE_CSS` 실제 구조(다크 `@media` 중첩 `}}`)에 맞게 조정. 토큰 값은 목업 그대로라 대비는 이미 통과함(실측 완료). 실패 시 **CSS가 아니라 파서**를 고친다.

- [ ] **Step 4: 통과 확인** — Run: 위 명령 · Expected: PASS. 이후 누가 CSS 토큰을 낮추면 이 테스트가 빨개짐(영구 가드).

- [ ] **Step 5: 커밋**

```bash
git add skills/setup-docs/scripts/test_render_report.py
git commit -m "✅ test(render): 동결 CSS WCAG AA 대비 가드(양 테마)"
```

---

### Task 3: 이스케이프 안전성

**Files:**
- Modify: `skills/setup-docs/scripts/test_render_report.py`

**Interfaces:**
- Consumes: `render_report.esc`.

- [ ] **Step 1: 실패 테스트 작성**

```python
from render_report import esc

def test_esc_neutralizes_html():
    assert esc('a<b>&"c') == 'a&lt;b&gt;&amp;&quot;c'
    assert esc(None) == ""

def test_hostile_path_does_not_break_output():
    d = dict(MIN)
    d["migration"] = [{"src": '<script>x</script>', "dest": 'docs/a&b.md', "ops": ["move"], "impact": None}]
    html = render_report(d, "plan")
    assert "<script>x" not in html          # 원문 태그가 살아있으면 안 됨
    assert "&lt;script&gt;" in html
    assert html.count("<div") == html.count("</div>")
```

- [ ] **Step 2: 실패 확인** — Run: `uv run --with pytest pytest test_render_report.py -k esc_or_hostile -q` · Expected: `test_esc_neutralizes_html` PASS(esc 이미 존재), `test_hostile_path` FAIL(마이그레이션 섹션 미구현 → src 미출력이라 assert 실패).

- [ ] **Step 3:** Task 7에서 마이그레이션 렌더가 `esc(row["src"])`를 쓰도록 구현하면 GREEN. 지금은 테스트만 남겨두고 Task 7에서 닫는다(순서 의존 명시). 임시로 `test_hostile_path`에 `@pytest.mark.xfail(reason="Task 7")` 부여.

```python
import pytest
@pytest.mark.xfail(reason="closed by Task 7 (migration renderer)")
def test_hostile_path_does_not_break_output():
    ...
```

- [ ] **Step 4: 확인** — Run: 위 명령 · Expected: `esc` PASS, `hostile_path` XFAIL.

- [ ] **Step 5: 커밋**

```bash
git add skills/setup-docs/scripts/test_render_report.py
git commit -m "✅ test(render): 이스케이프 + 적대적 경로 가드(Task 7에서 close)"
```

---

### Task 4: 히어로 섹션 (등급 스케일 + 범례)

**Files:**
- Modify: `render_report.py` · `test_render_report.py`

**Interfaces:**
- Produces: `_render_hero(data: dict) -> str`.

- [ ] **Step 1: 실패 테스트 작성**

```python
def test_hero_shows_current_and_target_grade():
    html = render_report({**MIN, "grade": {"current": "F", "target": "A"},
                          "counts": {"fail": 7, "warn": 2, "pass": 0}}, "plan")
    assert 'class="tick cur">F' in html and '현재' in html
    assert 'class="tick tgt">A' in html and '목표' in html
    assert "미달" in html and "7" in html   # 범례 개수
```

- [ ] **Step 2: 실패 확인** — Run: `uv run --with pytest pytest test_render_report.py::test_hero_shows_current_and_target_grade -q` · Expected: FAIL.

- [ ] **Step 3: 구현** — 목업의 히어로 마크업을 데이터 바인딩. `_render_main`이 `_render_hero(data)`를 포함하도록.

```python
def _render_hero(data: dict) -> str:
    g = data["grade"]; c = data["counts"]
    return (
      '<div class="card hero">'
      '<p class="hero-title">문서 아키텍처 건강 등급</p>'
      '<div class="scale" role="img" aria-label="등급 스케일 F부터 A까지. 현재/목표 표시.">'
      f'<span class="tick cur">{esc(g["current"])}<span class="cap">현재</span></span>'
      '<span class="seg"></span><span class="tick mid">D</span>'
      '<span class="seg"></span><span class="tick mid">C</span>'
      '<span class="seg"></span><span class="tick mid">B</span>'
      f'<span class="seg"></span><span class="tick tgt">{esc(g["target"])}<span class="cap">목표</span></span>'
      '</div>'
      f'<p class="explain">9개 진단 차원 중 <b>{c["pass"]}개</b>만 충족 → 목표 <b class="a">{esc(g["target"])}등급</b>.</p>'
      '<div class="legend">'
      f'<div class="lg on-fail"><span class="chip fail">미달</span><span class="cnt">{c["fail"]}</span><span class="gl">기준 미충족</span></div>'
      f'<div class="lg on-warn"><span class="chip warn">부분</span><span class="cnt">{c["warn"]}</span><span class="gl">일부만 충족</span></div>'
      f'<div class="lg on-pass"><span class="chip pass">통과</span><span class="cnt">{c["pass"]}</span><span class="gl">기준 충족</span></div>'
      '</div></div>'
    )
```

- [ ] **Step 4: 통과 확인** — Run: 위 명령 · Expected: PASS.

- [ ] **Step 5: 커밋** — `git commit -m "✨ feat(render): 히어로(등급 스케일·범례)"`

---

### Task 5: 점수표 섹션 (현재 상태만 · 칩 + 심각도 스트라이프)

**Files:** Modify `render_report.py` · `test_render_report.py`
**Interfaces:** Produces `_render_scorecard(data: dict) -> str`. `_dim(d) -> str` 헬퍼.

- [ ] **Step 1: 실패 테스트**

```python
def test_scorecard_rows_and_status():
    d = {**MIN, "scorecard": {
        "mechanical": [{"code": "M1", "name": "도달성", "sub": "x", "status": "fail"}],
        "judgment":   [{"code": "J1", "name": "분류", "sub": "y", "status": "warn"}]}}
    html = render_report(d, "plan")
    assert 'class="dim d-fail"' in html and '<span class="chip fail">미달</span>' in html
    assert 'class="dim d-warn"' in html and '<span class="chip warn">부분</span>' in html
    assert "M1" in html and "도달성" in html
```

- [ ] **Step 2: 실패 확인** — Expected: FAIL.
- [ ] **Step 3: 구현**

```python
_LABEL = {"fail": "미달", "warn": "부분", "pass": "통과"}
def _dim(d: dict) -> str:
    st = d["status"]
    return (f'<div class="dim d-{st}"><div><div class="name">{esc(d["name"])}'
            f'<span class="code">{esc(d["code"])}</span></div>'
            f'<div class="sub">{esc(d["sub"])}</div></div>'
            f'<span class="chip {st}">{_LABEL[st]}</span></div>')

def _render_scorecard(data: dict) -> str:
    sc = data["scorecard"]
    m = "".join(_dim(x) for x in sc["mechanical"])
    j = "".join(_dim(x) for x in sc["judgment"])
    return ('<section aria-labelledby="sc"><h2 class="sec" id="sc">진단 점수표 '
            '<span class="n">현재 상태</span></h2>'
            f'<p class="grp">기계 채점</p><div class="grid">{m}</div>'
            f'<p class="grp">판단 채점</p><div class="grid">{j}</div></section>')
```

- [ ] **Step 4: 통과 확인** — Expected: PASS.
- [ ] **Step 5: 커밋** — `git commit -m "✨ feat(render): 점수표(현재상태·칩·스트라이프)"`

---

### Task 6: Before/After 트리

**Files:** Modify `render_report.py` · `test_render_report.py`
**Interfaces:** Produces `_render_trees(data: dict) -> str`.

- [ ] **Step 1: 실패 테스트**

```python
def test_trees_render_lines_with_classes():
    d = {**MIN, "trees": {
        "before": {"title": "산재", "tag": "지금", "sub": "고아 12", "lines": [["api-help.md", "stray"]]},
        "after":  {"title": "docs/", "tag": "목표", "sub": "고아 0", "lines": [["_map.md", "new"]]}}}
    html = render_report(d, "plan")
    assert '<span class="stray">api-help.md</span>' in html
    assert '<span class="new">_map.md</span>' in html
    assert "지금" in html and "목표" in html
```

- [ ] **Step 2: 실패 확인** — Expected: FAIL.
- [ ] **Step 3: 구현**

```python
def _tree_pre(lines) -> str:
    out = []
    for text, cls in lines:
        out.append(f'<span class="{cls}">{esc(text)}</span>' if cls else esc(text))
    return "\n".join(out)

def _tree(side: dict, which: str) -> str:
    tagcls = "now" if which == "before" else "tgt"
    return (f'<div class="tree {"a" if which=="before" else "b"}">'
            f'<h3>{esc(side["title"])} <span class="htag {tagcls}">{esc(side["tag"])}</span></h3>'
            f'<div class="st">{esc(side["sub"])}</div>'
            f'<pre>{_tree_pre(side["lines"])}</pre></div>')

def _render_trees(data: dict) -> str:
    t = data["trees"]
    return ('<section aria-labelledby="tr"><h2 class="sec" id="tr">문서 구조 '
            '<span class="n">Before → After</span></h2>'
            f'<div class="card trees">{_tree(t["before"],"before")}{_tree(t["after"],"after")}</div>'
            '<div class="key"><span><span class="sw stray"></span>산재·문제</span>'
            '<span><span class="sw new"></span>신설</span>'
            '<span><span class="sw grp"></span>폴더</span></div></section>')
```

- [ ] **Step 4: 통과 확인** — Expected: PASS.
- [ ] **Step 5: 커밋** — `git commit -m "✨ feat(render): Before/After 트리 + 색 키"`

---

### Task 7: 마이그레이션 표 (+ Task 3 xfail close)

**Files:** Modify `render_report.py` · `test_render_report.py`
**Interfaces:** Produces `_render_migration(data: dict) -> str` (plan 모드 전용).

- [ ] **Step 1: 실패 테스트**

```python
def test_migration_rows_and_impact():
    d = {**MIN, "migration": [
        {"src": "a.md", "dest": "docs/reference/a.md", "ops": ["move", "rename"], "impact": None},
        {"src": "b/**", "dest": "docs/x/", "ops": ["move"], "impact": "경로 깨짐"}]}
    html = render_report(d, "plan")
    assert '<span class="badge move">move</span>' in html
    assert '<span class="badge rename">rename</span>' in html
    assert "docs/reference/a.md" in html and "경로 깨짐" in html
```

- [ ] **Step 2: 실패 확인** — Expected: `test_migration_rows_and_impact` FAIL; `test_hostile_path`는 아직 XFAIL.
- [ ] **Step 3: 구현**

```python
_BADGE = {"move": '<span class="badge move">move</span>',
          "rename": '<span class="badge rename">rename</span>',
          "frozen": '<span class="badge frozen">frozen</span>'}
def _mig_row(r: dict) -> str:
    ops = " ".join(_BADGE[o] for o in r["ops"])
    if r.get("impact"):
        imp = f'<td class="impact"><span class="ic" aria-hidden="true">▲</span><span>{esc(r["impact"])}</span></td>'
    else:
        imp = '<td class="muted-cell">—</td>'
    return (f'<tr><td class="path">{esc(r["src"])}<br>→ '
            f'<span class="dest">{esc(r["dest"])}</span></td><td>{ops}</td>{imp}</tr>')

def _render_migration(data: dict) -> str:
    rows = "".join(_mig_row(r) for r in data["migration"])
    return ('<section aria-labelledby="mg"><h2 class="sec" id="mg">이동 계획 '
            '<span class="n">per-doc · 유실 0</span></h2><div class="card"><div class="tbl-scroll">'
            '<table><caption class="vh">문서별 이동 계획</caption>'
            '<thead><tr><th scope="col">원본 → 목적지</th><th scope="col">연산</th>'
            f'<th scope="col">주의</th></tr></thead><tbody>{rows}</tbody></table></div>'
            '<div class="tbl-key"><span><b>move</b> 이동</span><span><b>rename</b> 개명</span>'
            '<span><b>frozen</b> 동결</span><span><b>▲</b> 이동 시 깨짐</span></div></div></section>')
```

- [ ] **Step 4: xfail 제거** — `test_hostile_path_does_not_break_output`에서 `@pytest.mark.xfail` 데코레이터 삭제(이제 GREEN이어야 함).
- [ ] **Step 5: 통과 확인** — Run: `uv run --with pytest pytest test_render_report.py -q` · Expected: migration·hostile_path 모두 PASS.
- [ ] **Step 6: 커밋** — `git commit -m "✨ feat(render): 마이그레이션 표 + 적대적 경로 close"`

---

### Task 8: 결정 패널 (A vs B)

**Files:** Modify `render_report.py` · `test_render_report.py`
**Interfaces:** Produces `_render_decisions(data: dict) -> str` (plan 모드 전용).

- [ ] **Step 1: 실패 테스트**

```python
def test_decisions_numbered_with_choices_and_rec():
    d = {**MIN, "decisions": [{"no": 2, "tag": "구조", "tag_kind": "struct",
        "question": "라우터를 어떻게?", "choices": [
            {"label": "안 A", "value": "CLAUDE.md 유지", "detail": "맵 링크 직접", "src": None, "recommended": True},
            {"label": "안 B", "value": "AGENTS.md 승격", "detail": "라우팅만", "src": None, "recommended": False}]}]}
    html = render_report(d, "plan")
    assert "결정 2" in html and "구조" in html
    assert 'class="choice rec"' in html and "추천" in html
    assert "CLAUDE.md 유지" in html and "AGENTS.md 승격" in html and '<div class="vs"' in html
```

- [ ] **Step 2: 실패 확인** — Expected: FAIL.
- [ ] **Step 3: 구현**

```python
def _choice(c: dict) -> str:
    rec = ' rec' if c.get("recommended") else ''
    tag = '<span class="rtag">추천</span>' if c.get("recommended") else ''
    src = f'<div class="src">출처 · {esc(c["src"])}</div>' if c.get("src") else ''
    return (f'<div class="choice{rec}"><div class="cl">{esc(c["label"])} {tag}</div>'
            f'<div class="cv">{esc(c["value"])}</div><div class="cd">{esc(c["detail"])}</div>{src}</div>')

def _decision(d: dict) -> str:
    a, b = d["choices"][0], d["choices"][1]
    return (f'<div class="dec"><div class="dec-head"><span class="dec-no">결정 {esc(d["no"])}</span>'
            f'<span class="dec-tag {esc(d["tag_kind"])}">{esc(d["tag"])}</span></div>'
            f'<p class="dec-q">{esc(d["question"])}</p>'
            f'<div class="choices">{_choice(a)}<div class="vs" aria-hidden="true">vs</div>{_choice(b)}</div></div>')

def _render_decisions(data: dict) -> str:
    if not data["decisions"]:
        return ""
    decs = "".join(_decision(d) for d in data["decisions"])
    n = len(data["decisions"])
    return (f'<section aria-labelledby="fl"><h2 class="sec" id="fl">당신의 결정 '
            f'<span class="n">{n}건 · 채팅에서 선택</span></h2>'
            '<p class="sec-intro">자동으로 고치지 않습니다 — 채팅으로 선택을 알려주세요.</p>'
            f'<div class="card">{decs}</div></section>')
```

- [ ] **Step 4: 통과 확인** — Expected: PASS.
- [ ] **Step 5: 커밋** — `git commit -m "✨ feat(render): 결정 패널(A vs B·추천)"`

---

### Task 9: 조립(plan/result) + 픽스처 엣지

**Files:** Modify `render_report.py` · `test_render_report.py`
**Interfaces:** `_render_main` 완성. `_render_summary(data) -> str`(result 모드).

- [ ] **Step 1: 실패 테스트** — 두 모드 + 엣지.

```python
def test_plan_mode_has_migration_and_decisions_but_result_does_not():
    d = {**MIN,
         "migration": [{"src": "a.md", "dest": "docs/a.md", "ops": ["move"], "impact": None}],
         "decisions": [{"no": 1, "tag": "구조", "tag_kind": "struct", "question": "?",
                        "choices": [{"label": "A", "value": "x", "detail": "", "src": None, "recommended": True},
                                    {"label": "B", "value": "y", "detail": "", "src": None, "recommended": False}]}],
         "summary": {"moved": 3, "orphans_before": 12, "orphans_after": 0,
                     "outside_before": 45, "outside_after": 0, "loop_installed": True, "residual": []}}
    plan = render_report(d, "plan")
    assert "이동 계획" in plan and "당신의 결정" in plan
    result = render_report(d, "result")
    assert "이동 계획" not in result and "당신의 결정" not in result
    assert "완료" in result and "12" in result and "0" in result   # 요약 수치

def test_edges_do_not_crash_or_unbalance():
    for d in (MIN,  # 0 docs
              {**MIN, "scorecard": {"mechanical": [{"code": f"M{i}", "name": "n"*40,
                 "sub": "s", "status": "fail"} for i in range(200)], "judgment": []}}):  # 대량
        for mode in ("plan", "result"):
            html = render_report(d, mode)
            assert html.count("<div") == html.count("</div>")
            assert 'style="' not in html
```

- [ ] **Step 2: 실패 확인** — Expected: FAIL(result 요약 미구현, `_render_main`이 섹션 조립 안 함).
- [ ] **Step 3: 구현**

```python
def _render_summary(data: dict) -> str:
    s = data.get("summary") or {}
    residual = s.get("residual") or []
    res_html = ("<b>완료 — 전 차원 충족.</b>" if not residual
                else "<b>완료(잔여 있음):</b> " + esc(", ".join(residual)))
    return ('<section aria-labelledby="sm"><h2 class="sec" id="sm">마이그레이션 완료 '
            '<span class="n">실제 결과</span></h2><div class="card"><div class="flag"><div>'
            f'<div class="t">{res_html}</div>'
            f'<div class="d">이동 {esc(s.get("moved",0))}개 · 고아 {esc(s.get("orphans_before",0))}→{esc(s.get("orphans_after",0))} · '
            f'docs/ 밖 {esc(s.get("outside_before",0))}→{esc(s.get("outside_after",0))} · '
            f'성장 루프 {"설치" if s.get("loop_installed") else "미설치"}</div>'
            '</div></div></div></section>')

def _render_main(data: dict, mode: str) -> str:
    parts = [_render_hero(data), _render_scorecard(data), _render_trees(data)]
    if mode == "plan":
        parts += [_render_migration(data), _render_decisions(data)]
    else:
        parts.append(_render_summary(data))
    parts.append('<p class="foot">docsherpa · setup-docs</p>')
    return "<main>" + "".join(parts) + "</main>"
```

- [ ] **Step 4: 통과 확인** — Run: `uv run --with pytest pytest test_render_report.py -q` · Expected: 전체 PASS.
- [ ] **Step 5: 전체 스위트 회귀 확인** — Run: `uv run --with pytest pytest -q` (scripts 전체) · Expected: 기존 90 + 신규 전부 PASS.
- [ ] **Step 6: 커밋** — `git commit -m "✨ feat(render): plan/result 조립 + 픽스처 엣지 가드"`

---

## Self-Review (작성자 체크)

- **스펙 커버리지:** design.md §9(동결 렌더러) 전 요구 — 대비 테스트(Task 2)·구조/인라인0/자기완결(Task 1)·이스케이프(Task 3,7)·픽스처 엣지(Task 9)·plan/result 모드(Task 9) 모두 태스크 있음. §5 파이프라인의 "붕어빵 틀 재사용"은 이 렌더러가 실현.
- **범위:** 이 계획은 `render_report`만(첫 증분). `doc-health` 스킬·탐색·마이그레이션 실행·setup-docs 리팩터는 **후속 별도 계획**(각자 spec→plan). 렌더러는 픽스처 데이터로 독립 검증되므로 doc-health 없이도 완결.
- **인터페이스 정합:** 데이터 모델(위)이 단일 소스. `_render_*` 함수 시그니처·`status`/`tag_kind` 값이 태스크 간 일치.
- **미해결:** CSS 포팅(Task 1 Step 3)은 목업 자산 복사 — 실행자가 파일을 열어 붙여야 함(자산 경로 명시).

## 후속 (이 증분 이후)

1. `doc-health` 스킬(탐색 2단계 + 채점 + 등급) — 이 렌더러의 데이터 모델을 생산.
2. setup-docs 리팩터(Phase 0·4에서 doc-health 호출 + Phase 2 계획 데이터 조립 → render_report).
3. 마이그레이션 실행(worktree·두 오라클) + Phase 4 결과.
