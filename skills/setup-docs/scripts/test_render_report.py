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
