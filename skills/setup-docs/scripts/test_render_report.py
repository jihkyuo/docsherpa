import re
import pytest
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

@pytest.mark.xfail(reason="closed by Task 7 (migration renderer)")
def test_hostile_path_does_not_break_output():
    d = dict(MIN)
    d["migration"] = [{"src": '<script>x</script>', "dest": 'docs/a&b.md', "ops": ["move"], "impact": None}]
    html = render_report(d, "plan")
    assert "<script>x" not in html          # 원문 태그가 살아있으면 안 됨
    assert "&lt;script&gt;" in html
    assert html.count("<div") == html.count("</div>")
