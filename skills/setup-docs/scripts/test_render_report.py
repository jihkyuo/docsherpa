import re
from render_report import render_report, esc

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
        m = re.search(r'@media \(prefers-color-scheme: dark\)\s*\{\s*:root\s*\{(.*?)\}\s*\}', TEMPLATE_CSS, re.S)
        block = m.group(1) if m else ""
    return dict(re.findall(r'(--[\w-]+):\s*(#[0-9a-fA-F]{6})', block))

def test_contrast_aa_both_themes():
    for theme in ("light", "dark"):
        tok = _tokens_for(theme)
        for fg, bg, mn in AA_PAIRS:
            assert fg in tok and bg in tok, f"{theme}: missing {fg}/{bg}"
            r = _cr(tok[fg], tok[bg])
            assert r >= mn, f"{theme} {fg} on {bg} = {r:.2f} < {mn}"


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


def test_masthead_shows_repo_fields_escaped():
    d = {**MIN, "repo": {"name": "r&<x>", "docs_count": 69, "branch": "develop"}}
    html = render_report(d, "plan")
    assert 'class="mast"' in html
    assert "69 docs" in html and "develop" in html
    assert "r&amp;&lt;x&gt;" in html and "<x>" not in html


def test_hero_shows_current_and_target_grade():
    html = render_report({**MIN, "grade": {"current": "F", "target": "A"},
                          "counts": {"fail": 7, "warn": 2, "pass": 0}}, "plan")
    assert 'class="tick cur">F' in html and '현재' in html
    assert 'class="tick tgt">A' in html and '목표' in html
    assert "미달" in html and "7" in html   # 범례 개수


def test_scorecard_rows_and_status():
    d = {**MIN, "scorecard": {
        "mechanical": [{"code": "M1", "name": "도달성", "sub": "x", "status": "fail"}],
        "judgment":   [{"code": "J1", "name": "분류", "sub": "y", "status": "warn"}]}}
    html = render_report(d, "plan")
    assert 'class="dim d-fail"' in html and '<span class="chip fail">미달</span>' in html
    assert 'class="dim d-warn"' in html and '<span class="chip warn">부분</span>' in html
    assert "M1" in html and "도달성" in html


def test_trees_render_lines_with_classes():
    d = {**MIN, "trees": {
        "before": {"title": "산재", "tag": "지금", "sub": "고아 12", "lines": [["api-help.md", "stray"]]},
        "after":  {"title": "docs/", "tag": "목표", "sub": "고아 0", "lines": [["_map.md", "new"]]}}}
    html = render_report(d, "plan")
    assert '<span class="stray">api-help.md</span>' in html
    assert '<span class="new">_map.md</span>' in html
    assert "지금" in html and "목표" in html


def test_migration_rows_and_impact():
    d = {**MIN, "migration": [
        {"src": "a.md", "dest": "docs/reference/a.md", "ops": ["move", "rename"], "impact": None},
        {"src": "b/**", "dest": "docs/x/", "ops": ["move"], "impact": "경로 깨짐"}]}
    html = render_report(d, "plan")
    assert '<span class="badge move">move</span>' in html
    assert '<span class="badge rename">rename</span>' in html
    assert "docs/reference/a.md" in html and "경로 깨짐" in html


def test_decisions_numbered_with_choices_and_rec():
    d = {**MIN, "decisions": [{"no": 2, "tag": "구조", "tag_kind": "struct",
        "question": "라우터를 어떻게?", "choices": [
            {"label": "안 A", "value": "CLAUDE.md 유지", "detail": "맵 링크 직접", "src": None, "recommended": True},
            {"label": "안 B", "value": "AGENTS.md 승격", "detail": "라우팅만", "src": None, "recommended": False}]}]}
    html = render_report(d, "plan")
    assert "결정 2" in html and "구조" in html
    assert 'class="choice rec"' in html and "추천" in html
    assert "CLAUDE.md 유지" in html and "AGENTS.md 승격" in html and '<div class="vs"' in html


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

def test_result_mode_shows_grade_before_after_and_preexisting_broken():
    d = {**MIN, "grade": {"current": "C", "target": "B"},
         "summary": {"grade_before": "F", "grade_after": "A", "moved": 3,
                     "orphans_before": 12, "orphans_after": 0,
                     "outside_before": 45, "outside_after": 0,
                     "loop_installed": True, "residual": []},
         "preexisting_broken": [("docs/api.md", "src/x/")]}
    html = render_report(d, "result")
    assert "F" in html and "A" in html                      # before→after 등급 대비
    assert 'style="' not in html                             # 인라인 style 0(동결 품질)
    assert "머지 전" in html                                  # 기존 broken 표면화
    assert "docs/api.md" in html and "src/x/" in html
    assert html.count("<div") == html.count("</div>")


def test_result_mode_preexisting_broken_escapes_hostile_content():
    d = {**MIN, "preexisting_broken": [("<script>x</script>", "docs/a&b.md")]}
    html = render_report(d, "result")
    assert "<script>x" not in html
    assert "&lt;script&gt;" in html
    assert html.count("<div") == html.count("</div>")


def test_result_mode_without_grade_or_preexisting_still_renders():
    d = {**MIN, "summary": {"moved": 1, "orphans_before": 1, "orphans_after": 0,
                            "outside_before": 1, "outside_after": 0,
                            "loop_installed": False, "residual": []}}
    html = render_report(d, "result")
    assert "머지 전" not in html
    assert html.count("<div") == html.count("</div>")


def test_edges_do_not_crash_or_unbalance():
    for d in (MIN,  # 0 docs
              {**MIN, "scorecard": {"mechanical": [{"code": f"M{i}", "name": "n"*40,
                 "sub": "s", "status": "fail"} for i in range(200)], "judgment": []}}):  # 대량
        for mode in ("plan", "result"):
            html = render_report(d, mode)
            assert html.count("<div") == html.count("</div>")
            assert 'style="' not in html
