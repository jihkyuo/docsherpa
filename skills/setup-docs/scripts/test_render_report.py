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

def test_troubleshooting_type_color_in_migration_and_tree():
    d = {**MIN, "migration": [
        {"src": "recover.md", "dest": "docs/troubleshooting/recover.md", "ops": ["move"], "impact": None},
    ]}
    html = render_report(d, "plan")
    assert "tc-troubleshooting" in html      # 집약뷰 그룹 타입색
    assert "t-troubleshooting" in html       # 접이식 스캐폴딩(after) 폴더색
    assert "문제 해결" in html                # 그룹/범례 표시명
    assert "k-troubleshooting" in html        # Before→After 범례 스와치

def test_troubleshooting_aa_pair_registered():
    assert ("--fail-ink", "--bg", 4.5) in AA_PAIRS


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
    ("--pass-ink", "--panel", 4.5),
    # 접이식 스캐폴딩(C2)이 --bg 위에 새로 노출하는 타입색(t-adr/t-howto/t-prd; t-spec=accent-ink는 위에 이미 있음)
    ("--warn-ink", "--bg", 4.5), ("--pass-ink", "--bg", 4.5), ("--accent", "--bg", 4.5),
    # 트러블슈팅 1급 타입색(t-troubleshooting = fail-ink)이 --bg 위에 노출 → AA 강제
    ("--fail-ink", "--bg", 4.5),
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


def test_d4_scorecard_kind_and_selfexplaining_labels():
    d={**MIN,"scorecard":{"mechanical":[{"code":"M1","name":"라우터에서 모든 문서 도달","kind":"필수","status":"fail","sub":"x"},{"code":"M4","name":"코드 변경 시 문서 자동 갱신 장치 3종","kind":"채택도","status":"fail","sub":"y"}],"judgment":[]}}
    h=render_report(d,"plan")
    assert "kind req" in h and "kind opt" in h        # 필수/채택도 구분(D4보강)
    assert "자동 갱신 장치" in h                        # 자기설명 라벨(은어 아님)

def test_d6_migration_aggregated_by_type_with_bar_and_callout():
    d={**MIN,"migration":[
        {"src":"a.md","dest":"docs/specs/x/a.md","ops":["move"],"impact":None},
        {"src":"b.md","dest":"docs/specs/x/b.md","ops":["move"],"impact":None},
        {"src":"c.md","dest":"docs/decisions/c.md","ops":["move"],"impact":"옮기기 전 링크 확인"}],
       "decisions":[]}
    h=render_report(d,"plan")
    assert "mig-agg" in h and "█" in h            # 타입별 집약 + 텍스트막대
    assert "callout" in h and "옮기기 전" in h          # impact 콜아웃 격상(D6)
    assert "<details" in h                             # 전체 목록 접이식

def test_d3_after_tree_type_colored():
    import migrate
    tree=migrate._after_tree([{"src":"a.md","dest":"docs/specs/x/a.md","ops":["move"],"impact":None},
                              {"src":"p.md","dest":"docs/product/prd.md","ops":["move"],"impact":None}])
    classes={c for _,c in tree["lines"]}
    assert "t-spec" in classes and "t-prd" in classes  # 폴더=타입색(D3·D6①)


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


def test_howto_label_is_procedure_recovery_not_just_guide():
    html = render_report(MIN, "plan")
    assert "작업 절차·복구(how-to)" in html      # 트리 tkey 범례
    assert "가이드(how-to)" not in html          # 좁은 오역 제거


def test_migration_howto_group_label_aligned():
    d = {**MIN, "decisions": [],
         "migration": [{"src": "g.md", "dest": "docs/how-to/g.md", "ops": ["move"], "impact": None}]}
    html = render_report(d, "plan")
    assert "작업 절차·복구 (how-to)" in html      # mig-agg 그룹명


def test_result_mode_without_after_tree_omits_type_legend():
    # result 모드는 after 트리가 없다(t.get("after")가 falsy) → 타입색 범례를 걸 곳이 없으니
    # tkey 범례(및 k-troubleshooting 등 타입색 스와치)를 렌더하면 안 된다(D6 재발 방지: DF5).
    d = {**MIN, "trees": {"before": {"title": "", "tag": "지금", "sub": "", "lines": []}}}
    html = render_report(d, "result")
    assert 'class="tkey"' not in html
    # CSS(TEMPLATE_CSS)는 동결이라 .k-troubleshooting 규칙 자체는 항상 존재 — 마크업만 확인
    assert '<b class="k-troubleshooting">' not in html


def test_plan_mode_with_after_tree_shows_type_legend():
    html = render_report(MIN, "plan")   # MIN에는 trees.after가 있음
    assert 'class="tkey"' in html
    assert '<b class="k-troubleshooting">' in html


def test_trees_intro_does_not_claim_red_for_before_pane():
    # before 트리 파일은 이제 무색이므로(DF5) 소개문이 "산재·빨강"을 주장하면 안 된다.
    html = render_report(MIN, "plan")
    assert "빨강" not in html


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


def test_result_mode_tree_section_does_not_promise_an_after_pane():
    """after 트리가 없으면 제목이 'Before → After'라 약속하면 안 되고,
    2단 그리드(.trees)로 빈 오른쪽 절반을 남겨서도 안 된다(자기설명 결함)."""
    d = {**MIN, "trees": {"before": {"title": "현재 구조", "tag": "지금",
                                     "sub": "docs/ 밖 6건", "lines": [["a.md", None]]}},
         "migration": [], "summary": {}}
    body = render_report(d, "result").split("</style>", 1)[1]
    assert "Before → After" not in body        # after 없는데 약속하지 않는다
    assert '<div class="card trees">' not in body   # 빈 오른쪽 pane 만들지 않는다
    assert '<div class="tree a">' not in body       # 좌측 구분선(2단 전제) 없음


def test_plan_mode_tree_section_keeps_before_after_grid():
    d = {**MIN, "trees": {"before": {"title": "현재", "tag": "지금", "sub": "s", "lines": [["a.md", None]]},
                          "after": {"title": "정리 후", "tag": "목표", "sub": "s", "lines": [["docs/", "t-dir"]]}},
         "migration": [], "decisions": []}
    body = render_report(d, "plan").split("</style>", 1)[1]
    assert "Before → After" in body
    assert '<div class="card trees">' in body
    assert '<div class="tree a">' in body
