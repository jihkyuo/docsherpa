import html as _html

def esc(s) -> str:
    return _html.escape("" if s is None else str(s), quote=True)


# 저작 원본: ~/Downloads/docsherpa-phase2-diagnosis-mockup.html 의 <style>...</style> 내부 CSS를
# 그대로 복사한 것(이미 AA 실측·codex 검증됨). 변경 금지 — 토큰만.
TEMPLATE_CSS = r"""
  :root {
    color-scheme: light dark;
    --bg:#f6f8fa; --panel:#ffffff; --panel-2:#eef1f5;
    --ink:#161f2b; --muted:#54606f; --faint:#616d7d;
    --line:#e3e8ee; --line-strong:#ccd4de;
    --accent:#0f7a82; --accent-ink:#0b6067; --accent-soft:#d7ecec;
    --pass:#1f9d57; --pass-ink:#177544; --pass-soft:#dcefe4;
    --warn:#c48711; --warn-ink:#785200; --warn-soft:#f4ecd6;
    --fail:#cf4b4b; --fail-ink:#a82c20; --fail-soft:#f6dede;
    --shadow:0 1px 2px rgba(20,30,45,.05);
    --mono:"SF Mono","JetBrains Mono",ui-monospace,"Menlo","Consolas",monospace;
    --sans:-apple-system,"SF Pro Text","Segoe UI",system-ui,"Helvetica Neue",sans-serif;
    --s1:4px; --s2:8px; --s3:12px; --s4:16px; --s5:24px; --s6:32px;
    --r:10px; --r-sm:7px;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      color-scheme: dark;
      --bg:#0d131d; --panel:#151d29; --panel-2:#1b2431;
      --ink:#e7ecf3; --muted:#94a2b4; --faint:#8a97a9;
      --line:#26313f; --line-strong:#34414f;
      --accent:#38bcc2; --accent-ink:#57cdd2; --accent-soft:#123033;
      --pass:#3dbb77; --pass-ink:#54c98a; --pass-soft:#14291d;
      --warn:#e0a83c; --warn-ink:#e6b558; --warn-soft:#2c2612;
      --fail:#e86b6b; --fail-ink:#f08d8d; --fail-soft:#2e1919;
      --shadow:0 1px 2px rgba(0,0,0,.3),0 6px 20px rgba(0,0,0,.26);
    }
  }
  :root[data-theme="light"] {
    color-scheme: light;
    --bg:#f6f8fa; --panel:#ffffff; --panel-2:#eef1f5;
    --ink:#161f2b; --muted:#54606f; --faint:#616d7d;
    --line:#e3e8ee; --line-strong:#ccd4de;
    --accent:#0f7a82; --accent-ink:#0b6067; --accent-soft:#d7ecec;
    --pass:#1f9d57; --pass-ink:#177544; --pass-soft:#dcefe4;
    --warn:#c48711; --warn-ink:#785200; --warn-soft:#f4ecd6;
    --fail:#cf4b4b; --fail-ink:#a82c20; --fail-soft:#f6dede;
    --shadow:0 1px 2px rgba(20,30,45,.05);
  }
  :root[data-theme="dark"] {
    color-scheme: dark;
    --bg:#0d131d; --panel:#151d29; --panel-2:#1b2431;
    --ink:#e7ecf3; --muted:#94a2b4; --faint:#8a97a9;
    --line:#26313f; --line-strong:#34414f;
    --accent:#38bcc2; --accent-ink:#57cdd2; --accent-soft:#123033;
    --pass:#3dbb77; --pass-ink:#54c98a; --pass-soft:#14291d;
    --warn:#e0a83c; --warn-ink:#e6b558; --warn-soft:#2c2612;
    --fail:#e86b6b; --fail-ink:#f08d8d; --fail-soft:#2e1919;
    --shadow:0 1px 2px rgba(0,0,0,.3),0 6px 20px rgba(0,0,0,.26);
  }

  * { box-sizing: border-box; }
  .vh { position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap; border:0; }
  body { margin:0; background:var(--bg); color:var(--ink); font-family:var(--sans); line-height:1.5; -webkit-font-smoothing:antialiased; }
  main { max-width:960px; margin:0 auto; padding:var(--s6) var(--s5) 64px; }

  .mast { display:flex; align-items:flex-end; justify-content:space-between; gap:var(--s4); flex-wrap:wrap; margin-bottom:var(--s5); }
  .kicker { font-family:var(--mono); font-size:11px; letter-spacing:.14em; text-transform:uppercase; color:var(--accent-ink); font-weight:600; }
  h1 { font-size:22px; margin:var(--s1) 0 0; letter-spacing:-.01em; font-weight:640; text-wrap:balance; }
  .repo { font-family:var(--mono); font-size:12px; color:var(--muted); }
  .repo b { color:var(--ink); }

  .card { background:var(--panel); border:1px solid var(--line); border-radius:var(--r); box-shadow:var(--shadow); }
  section { margin-top:var(--s5); }
  h2.sec { font-size:14px; font-weight:640; letter-spacing:-.01em; color:var(--ink); margin:0 0 var(--s3); display:flex; align-items:center; gap:var(--s2); }
  h2.sec .n { font-family:var(--mono); font-size:11px; font-weight:600; color:var(--faint); }
  h2.sec::after { content:""; flex:1; height:1px; background:var(--line); }
  .sec-intro { font-size:12.5px; color:var(--muted); margin:0 2px var(--s3); }

  /* grade header */
  .hero { padding:var(--s5) var(--s5) var(--s4); }
  .hero-title { font-size:11px; font-family:var(--mono); letter-spacing:.08em; text-transform:uppercase; color:var(--muted); margin:0 0 var(--s5); text-align:center; }
  .scale { display:flex; align-items:center; justify-content:center; max-width:500px; margin:0 auto; padding-bottom:22px; }
  .scale .seg { flex:1; min-width:10px; height:2px; background:var(--line-strong); }
  .tick { font-family:var(--mono); font-weight:700; display:grid; place-items:center; flex:none; }
  .tick.mid { width:28px; height:28px; font-size:13px; color:var(--faint); }
  .tick.cur, .tick.tgt { width:54px; height:54px; font-size:28px; border-radius:12px; position:relative; }
  .tick.cur { color:var(--fail-ink); background:var(--fail-soft); border:2px solid var(--fail); }
  .tick.tgt { color:var(--pass-ink); background:var(--pass-soft); border:2px solid var(--pass); }
  .tick .cap { position:absolute; bottom:-20px; left:-12px; right:-12px; text-align:center; font-family:var(--mono); font-size:10px; font-weight:700; letter-spacing:.03em; }
  .tick.cur .cap { color:var(--fail-ink); }
  .tick.tgt .cap { color:var(--pass-ink); }
  .explain { max-width:660px; margin:0 auto var(--s5); text-align:center; font-size:14px; line-height:1.65; color:var(--muted); text-wrap:pretty; }
  .explain b { color:var(--ink); }
  .explain b.f { color:var(--fail-ink); }
  .explain b.a { color:var(--pass-ink); }
  .legend { display:flex; justify-content:center; flex-wrap:wrap; gap:var(--s5); border-top:1px solid var(--line); padding-top:var(--s4); }
  .lg { display:flex; align-items:center; gap:7px; font-size:12.5px; }
  .lg .cnt { font-family:var(--mono); font-weight:700; font-size:14px; }
  .lg .gl { color:var(--muted); font-size:11.5px; }
  .lg.on-fail .cnt { color:var(--fail-ink); }
  .lg.on-warn .cnt { color:var(--warn-ink); }
  .lg.on-pass .cnt { color:var(--pass-ink); }

  /* status chip — shared by legend + scorecard */
  .chip { display:inline-flex; align-items:center; font-family:var(--mono); font-size:11.5px; font-weight:600; padding:3px 10px; border-radius:99px; white-space:nowrap; }
  .chip.fail { background:var(--fail-soft); color:var(--fail-ink); }
  .chip.warn { background:var(--warn-soft); color:var(--warn-ink); }
  .chip.pass { background:var(--pass-soft); color:var(--pass-ink); }
  .c-fail { color:var(--fail-ink); }
  .c-warn { color:var(--warn-ink); }
  .c-pass { color:var(--pass-ink); }
  .htag { font-family:var(--mono); font-size:11px; font-weight:600; }
  .htag.now { color:var(--fail-ink); }
  .htag.tgt { color:var(--pass-ink); }

  /* scorecard */
  .grp { font-family:var(--mono); font-size:11px; color:var(--muted); margin:var(--s4) var(--s1) var(--s2); }
  .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:var(--s2); }
  .dim { display:grid; grid-template-columns:1fr auto; align-items:center; gap:var(--s3); min-width:0; padding:var(--s3) var(--s4); background:var(--panel); border:1px solid var(--line); border-left:3px solid var(--line-strong); border-radius:var(--r-sm); }
  .dim.d-fail { border-left-color:var(--fail); }
  .dim.d-warn { border-left-color:var(--warn); }
  .dim.d-pass { border-left-color:var(--pass); }
  .dim .name { font-size:13.5px; font-weight:560; }
  .dim .name .code { font-family:var(--mono); font-size:10.5px; color:var(--faint); margin-left:var(--s1); }
  .dim .sub { font-size:11.5px; color:var(--muted); margin-top:2px; }

  /* trees */
  .trees { display:grid; grid-template-columns:1fr 1fr; }
  .tree { padding:var(--s4); min-width:0; }
  .tree.a { border-right:1px solid var(--line); }
  .tree h3 { font-size:12.5px; font-weight:600; margin:0; color:var(--ink); }
  .tree .st { font-family:var(--mono); font-size:10.5px; color:var(--muted); margin:3px 0 var(--s3); }
  .tree pre { font-family:var(--mono); font-size:12px; line-height:1.7; margin:0; white-space:pre; overflow-x:auto; color:var(--muted); }
  .tree .new { color:var(--accent-ink); font-weight:600; }
  .tree .stray { color:var(--fail-ink); }
  .tree .grp-c { color:var(--ink); }
  .key { display:flex; justify-content:center; flex-wrap:wrap; gap:var(--s4); margin-top:var(--s2); font-family:var(--mono); font-size:11px; color:var(--muted); }
  .key span { display:inline-flex; align-items:center; gap:6px; }
  .sw { width:11px; height:11px; border-radius:3px; flex:none; }
  .sw.stray { background:var(--fail-soft); border:1.5px solid var(--fail); }
  .sw.new { background:var(--accent-soft); border:1.5px solid var(--accent); }
  .sw.grp { background:var(--panel-2); border:1.5px solid var(--line-strong); }

  /* migration table */
  .tbl-scroll { overflow-x:auto; }
  table { border-collapse:collapse; width:100%; font-size:12.5px; min-width:560px; }
  thead th { text-align:left; font-family:var(--mono); font-size:10.5px; letter-spacing:.06em; text-transform:uppercase; color:var(--muted); font-weight:600; padding:var(--s3) var(--s4); border-bottom:1px solid var(--line-strong); }
  tbody td { padding:var(--s3) var(--s4); border-bottom:1px solid var(--line); vertical-align:top; }
  tbody tr:last-child td { border-bottom:none; }
  .path { font-family:var(--mono); font-size:11.5px; color:var(--muted); word-break:break-all; }
  .path .dest { color:var(--ink); }
  .badge { display:inline-block; font-family:var(--mono); font-size:10px; letter-spacing:.03em; padding:2px 7px; border-radius:5px; text-transform:uppercase; font-weight:600; }
  .badge.move { background:var(--accent-soft); color:var(--accent-ink); }
  .badge.rename { background:var(--warn-soft); color:var(--warn-ink); }
  .badge.frozen { background:var(--panel-2); color:var(--muted); border:1px solid var(--line); }
  .impact { font-size:11.5px; color:var(--fail-ink); display:flex; gap:6px; }
  .impact .ic { flex:none; font-weight:700; }
  .muted-cell { color:var(--faint); font-family:var(--mono); font-size:11px; }
  .fnt { color:var(--faint); }
  .tbl-key { display:flex; flex-wrap:wrap; gap:var(--s2) var(--s4); padding:var(--s3) var(--s4); border-top:1px solid var(--line); font-size:11px; color:var(--muted); }
  .tbl-key b { color:var(--ink); font-weight:600; }

  /* decisions (user choices) */
  code { font-family:var(--mono); font-size:.92em; background:var(--panel-2); padding:1px 5px; border-radius:4px; color:var(--ink); }
  .dec { padding:var(--s4); }
  .dec + .dec { border-top:1px solid var(--line); }
  .dec-head { display:flex; align-items:center; gap:var(--s2); flex-wrap:wrap; margin-bottom:var(--s3); }
  .dec-no { font-family:var(--mono); font-size:10.5px; font-weight:700; letter-spacing:.03em; color:#fff; background:var(--accent); padding:3px 9px; border-radius:6px; }
  .dec-tag { font-family:var(--mono); font-size:10px; text-transform:uppercase; letter-spacing:.04em; font-weight:700; padding:3px 8px; border-radius:6px; }
  .dec-tag.warn { background:var(--warn-soft); color:var(--warn-ink); }
  .dec-tag.struct { background:var(--accent-soft); color:var(--accent-ink); }
  .dec-q { font-size:13.5px; font-weight:600; margin:0 0 var(--s3); line-height:1.5; }
  .choices { display:grid; grid-template-columns:1fr auto 1fr; gap:var(--s2); align-items:stretch; }
  .vs { align-self:center; font-family:var(--mono); font-size:11px; font-weight:700; color:var(--faint); }
  .choice { border:1px solid var(--line); border-radius:var(--r-sm); padding:var(--s3); background:var(--panel-2); display:flex; flex-direction:column; }
  .choice.rec { border-color:var(--accent); background:var(--accent-soft); }
  .choice .cl { display:flex; align-items:center; gap:6px; font-size:11px; font-family:var(--mono); text-transform:uppercase; letter-spacing:.04em; color:var(--faint); font-weight:700; margin-bottom:5px; }
  .choice .rtag { font-family:var(--mono); font-size:9px; text-transform:uppercase; letter-spacing:.04em; color:var(--accent-ink); font-weight:700; }
  .choice .cv { font-family:var(--mono); font-size:12.5px; font-weight:600; color:var(--ink); margin-bottom:4px; }
  .choice .cd { font-size:11.5px; color:var(--muted); }
  .choice .src { font-family:var(--mono); font-size:10px; color:var(--faint); margin-top:auto; padding-top:8px; }
  @media (prefers-color-scheme: dark) { .dec-no { color:#0d131d; } }
  :root[data-theme="dark"] .dec-no { color:#0d131d; }
  :root[data-theme="light"] .dec-no { color:#fff; }

  /* approval — passive, not a button */
  .approve { margin-top:var(--s5); padding:var(--s4) var(--s5); border:1px solid var(--line); border-left:3px solid var(--accent); border-radius:var(--r); background:var(--panel-2); display:flex; align-items:center; justify-content:space-between; gap:var(--s4); flex-wrap:wrap; }
  .approve .txt { font-size:13px; }
  .approve .txt b { color:var(--ink); }
  .approve .txt span { color:var(--muted); }
  kbd { font-family:var(--mono); font-size:12px; padding:6px 12px; border-radius:7px; background:var(--panel); border:1px solid var(--line-strong); border-bottom-width:2px; color:var(--ink); white-space:nowrap; }

  .foot { margin-top:var(--s4); text-align:center; font-family:var(--mono); font-size:10.5px; color:var(--faint); letter-spacing:.03em; }

  /* D4 kind tag — 필수(능력) vs 채택도(docsherpa 준수) */
  .kind { font-family:var(--mono); font-size:9px; text-transform:uppercase; letter-spacing:.04em; font-weight:700; padding:1px 6px; border-radius:5px; margin-left:6px; white-space:nowrap; }
  .kind.req { background:var(--accent-soft); color:var(--accent-ink); }
  .kind.opt { background:var(--panel-2); color:var(--faint); border:1px solid var(--line); }

  /* D6 마이그레이션 집약뷰(타입별) — 텍스트막대(인라인 style 0) */
  .mig-agg { display:grid; gap:var(--s2); padding:var(--s4); }
  .mig-grp { display:grid; grid-template-columns:minmax(130px,1.3fr) minmax(90px,auto) minmax(150px,1.4fr); gap:var(--s3); align-items:center; padding:var(--s2) var(--s3); border:1px solid var(--line); border-left:3px solid var(--line-strong); border-radius:var(--r-sm); background:var(--panel-2); }
  .mig-grp.tc-adr { border-left-color:var(--warn-ink); }
  .mig-grp.tc-spec { border-left-color:var(--accent); }
  .mig-grp.tc-howto { border-left-color:var(--pass); }
  .mig-grp.tc-prd { border-left-color:var(--accent-ink); }
  .mig-grp.tc-flat { border-left-color:var(--line-strong); }
  .mig-grp .gname { font-size:12.5px; font-weight:600; color:var(--ink); min-width:0; }
  .mig-grp .gname .gsub { font-family:var(--mono); font-size:10px; color:var(--faint); display:block; margin-top:1px; }
  .mig-grp .gbar { font-family:var(--mono); font-size:11px; letter-spacing:-1px; white-space:nowrap; color:var(--accent); }
  .mig-grp .gbar .cnt { color:var(--ink); font-weight:700; letter-spacing:0; margin-left:6px; font-size:12px; }
  .mig-grp .gdest { font-family:var(--mono); font-size:11px; color:var(--muted); word-break:break-all; }
  .mig-head { font-size:13px; margin:0 0 var(--s3); color:var(--ink); }
  .mig-head .win { color:var(--pass-ink); }
  .mig-head .ok { color:var(--muted); }
  .callout { margin:var(--s3) var(--s4) 0; padding:var(--s3) var(--s4); border:1px solid var(--fail); border-left:3px solid var(--fail); border-radius:var(--r-sm); background:var(--fail-soft); }
  .callout .ct { font-size:12px; font-weight:700; color:var(--fail-ink); margin:0 0 var(--s2); }
  .callout ul { margin:0; padding-left:18px; }
  .callout li { font-size:11.5px; color:var(--ink); margin:3px 0; }
  .callout li .path { font-family:var(--mono); color:var(--fail-ink); }

  /* D3 트리 폴더=타입색(파일 무색) + 접이식 전체보기 */
  .tree .t-adr { color:var(--warn-ink); font-weight:600; }
  .tree .t-spec { color:var(--accent-ink); font-weight:600; }
  .tree .t-howto { color:var(--pass-ink); font-weight:600; }
  .tree .t-prd { color:var(--accent); font-weight:600; }
  .tree .t-legacy { color:var(--faint); }
  .tree .t-dir { color:var(--ink); font-weight:600; }
  details.full { margin:var(--s3) var(--s4) 0; border-top:1px solid var(--line); padding-top:var(--s3); }
  details.full > summary { font-family:var(--mono); font-size:11px; color:var(--accent-ink); cursor:pointer; font-weight:600; list-style:none; }
  details.full > summary::-webkit-details-marker { display:none; }
  details.full > summary::before { content:"\25B8  "; }
  details.full[open] > summary::before { content:"\25BE  "; }
  .tkey { display:flex; flex-wrap:wrap; gap:var(--s2) var(--s4); padding:var(--s3) var(--s4) 0; font-size:11px; color:var(--muted); }
  .tkey span { display:inline-flex; align-items:center; gap:5px; }
  .tkey b { font-family:var(--mono); font-weight:700; }
  .tkey .k-adr { color:var(--warn-ink); } .tkey .k-spec { color:var(--accent-ink); }
  .tkey .k-howto { color:var(--pass-ink); } .tkey .k-prd { color:var(--accent); }
  .tkey .k-legacy { color:var(--faint); }

  @media (max-width:680px) {
    .hero { padding:var(--s4); }
    .trees { grid-template-columns:1fr; }
    .tree.a { border-right:none; border-bottom:1px solid var(--line); }
    .dim { grid-template-columns:1fr; }
    .choices { grid-template-columns:1fr; }
    .vs { display:none; }
    .mig-grp { grid-template-columns:1fr; gap:var(--s1); }
  }
"""


def render_report(data: dict, mode: str = "plan") -> str:
    body = _render_main(data, mode)
    return f'<title>{esc(data["repo"]["name"])} · 문서 아키텍처 진단</title>\n<style>{TEMPLATE_CSS}</style>\n{body}'


def _render_masthead(data: dict) -> str:
    r = data["repo"]
    return ('<div class="mast"><div>'
            '<div class="kicker">docsherpa · setup-docs</div>'
            '<h1>문서 아키텍처 진단 &amp; 마이그레이션 계획</h1></div>'
            f'<div class="repo">repo <b>{esc(r["name"])}</b> · {esc(r["docs_count"])} docs · '
            f'branch <b>{esc(r["branch"])}</b></div></div>')


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


_LABEL = {"fail": "미달", "warn": "부분", "pass": "통과"}
_KIND_CLS = {"필수": "req", "채택도": "opt"}
def _dim(d: dict) -> str:
    st = d["status"]
    kind = d.get("kind")
    kind_tag = (f'<span class="kind {_KIND_CLS.get(kind, "opt")}">{esc(kind)}</span>'
                if kind else "")
    return (f'<div class="dim d-{st}"><div><div class="name">{esc(d["name"])}'
            f'<span class="code">{esc(d["code"])}</span>{kind_tag}</div>'
            f'<div class="sub">{esc(d["sub"])}</div></div>'
            f'<span class="chip {st}">{_LABEL[st]}</span></div>')

def _render_scorecard(data: dict) -> str:
    sc = data["scorecard"]
    m = "".join(_dim(x) for x in sc["mechanical"])
    j = "".join(_dim(x) for x in sc["judgment"])
    return ('<section aria-labelledby="sc"><h2 class="sec" id="sc">진단 점수표 '
            '<span class="n">현재 상태</span></h2>'
            '<p class="sec-intro"><b>필수</b> = 도구와 무관한 실제 문서 건강(도달성·커버리지). '
            '<b>채택도</b> = docsherpa 특정 장치(라우터 마커·맵 척추·자동 갱신) 설치 여부 — '
            '자체 등가물이 있으면 “미달”이라도 실제 결함이 아닐 수 있습니다.</p>'
            f'<p class="grp">기계 채점</p><div class="grid">{m}</div>'
            f'<p class="grp">판단 채점</p><div class="grid">{j}</div></section>')


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
    after = f'{_tree(t["after"],"after")}' if t.get("after") else ""
    return ('<section aria-labelledby="tr"><h2 class="sec" id="tr">문서 구조 '
            '<span class="n">Before → After</span></h2>'
            '<p class="sec-intro">왼쪽 = 지금(산재·빨강), 오른쪽 = 정리 후. '
            '오른쪽 폴더 색 = 문서 타입(아래 범례). 파일은 무색 — 색은 “어느 타입 폴더에 모였나”를 뜻합니다.</p>'
            f'<div class="card trees">{_tree(t["before"],"before")}{after}</div>'
            '<div class="tkey"><span><b class="k-prd">■</b> 제품요구(PRD)</span>'
            '<span><b class="k-spec">■</b> 명세(spec)</span>'
            '<span><b class="k-adr">■</b> 결정(ADR)</span>'
            '<span><b class="k-howto">■</b> 작업 절차·복구(how-to)</span>'
            '<span><b class="k-legacy">■</b> 동결(legacy)</span></div></section>')


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

_TYPE_GROUP = {   # docs/ 아래 1단계 폴더 → (표시명, tc-클래스)
    "decisions": ("결정 기록 (ADR)", "tc-adr"),
    "specs": ("명세 (spec)", "tc-spec"),
    "how-to": ("작업 절차·복구 (how-to)", "tc-howto"),
    "product": ("제품 요구 (PRD)", "tc-prd"),
}
def _mig_group_key(dest: str):
    parts = dest.split("/")            # docs/<folder>/... 또는 docs/<file>
    if len(parts) >= 3 and parts[0] == "docs":
        return parts[1]
    return "_flat"

def _bar(count: int, mx: int) -> str:
    n = max(1, round(count / mx * 10)) if mx else 0
    return "█" * n + "░" * (10 - n)

def _render_migration(data: dict) -> str:
    mig = data["migration"]
    groups = {}
    for r in mig:
        groups.setdefault(_mig_group_key(r["dest"]), []).append(r)
    mx = max((len(v) for v in groups.values()), default=1)
    order = ["product", "specs", "decisions", "how-to", "_flat"]
    rows = []
    for key in sorted(groups, key=lambda k: (order.index(k) if k in order else 99, k)):
        items = groups[key]
        name, tc = _TYPE_GROUP.get(key, ("조회·설명 (reference/explanation)", "tc-flat"))
        # 목적지: 공통 폴더(specs는 feature별로 여러 개일 수 있으니 접두 폴더까지)
        dests = sorted({("/".join(p["dest"].split("/")[:-1]) or "docs") for p in items})
        dest_disp = dests[0] + ("" if len(dests) == 1 else f" 외 {len(dests)-1}")
        rows.append(
            f'<div class="mig-grp {tc}"><div class="gname">{esc(name)}'
            f'<span class="gsub">{esc(key if key != "_flat" else "docs/ 직속")}</span></div>'
            f'<div class="gbar" aria-hidden="true">{_bar(len(items), mx)}'
            f'<span class="cnt">{len(items)}건</span></div>'
            f'<div class="gdest">→ {esc(dest_disp)}/</div></div>')
    ob, oa = data.get("orphans_before"), data.get("orphans_after")
    orphan_seg = (f' · <b class="win">고아(미도달) {esc(ob)} → {esc(oa)}</b>'
                  if ob is not None and oa is not None else "")
    mig_head = (f'<div class="mig-head"><b>{len(mig)}개 옮김</b>{orphan_seg}'
                f' · <span class="ok">전체 내용 그대로 보존(유실 0)</span></div>')
    impacts = [r for r in mig if r.get("impact")]
    callout = ""
    if impacts:
        lis = "".join(
            f'<li><span class="path">{esc(r["src"].split("/")[-1])}</span> — {esc(r["impact"])}</li>'
            for r in impacts)
        callout = (f'<div class="callout"><p class="ct">▲ 옮기기 전 결정·조치할 것 '
                   f'({len(impacts)}건)</p><ul>{lis}</ul></div>')
    full = "".join(_mig_row(r) for r in mig)
    return ('<section aria-labelledby="mg"><h2 class="sec" id="mg">이동 계획 '
            f'<span class="n">타입별 {len(groups)}묶음 · {len(mig)}개 문서 · 유실 0</span></h2>'
            '<p class="sec-intro">문서를 타입별로 어디로 모으는지 요약입니다. '
            '막대 = 문서 수(상대), 오른쪽 = 목적지 폴더. ▲는 옮기기 전에 당신이 정해야 할 것. '
            '문서별 전체 목록은 아래 “전체 펼치기”.</p>'
            f'<div class="card">{mig_head}<div class="mig-agg">{"".join(rows)}</div>{callout}'
            '<details class="full"><summary>문서별 전체 이동 목록 펼치기</summary>'
            '<div class="tbl-scroll"><table><caption class="vh">문서별 이동 계획</caption>'
            '<thead><tr><th scope="col">원본 → 목적지</th><th scope="col">연산</th>'
            f'<th scope="col">주의</th></tr></thead><tbody>{full}</tbody></table></div>'
            '<div class="tbl-key"><span><b>move</b> 이동</span><span><b>rename</b> 개명</span>'
            '<span><b>frozen</b> 동결</span><span><b>▲</b> 이동 시 깨짐</span></div>'
            '</details></div></section>')


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

def _render_grade_compare(before: str, after: str) -> str:
    return (
      '<div class="card hero">'
      '<p class="hero-title">재진단 등급 변화 <span class="n">Phase 0 → Phase 4</span></p>'
      '<div class="scale" role="img" aria-label="마이그레이션 전후 등급 대비.">'
      f'<span class="tick cur">{esc(before)}<span class="cap">이전</span></span>'
      '<span class="seg"></span>'
      f'<span class="tick tgt">{esc(after)}<span class="cap">이후</span></span>'
      '</div></div>'
    )


def _render_preexisting(items) -> str:
    rows = "".join(
        f'<li><span class="path">{esc(rel)}</span> → <span class="fnt">{esc(raw)}</span></li>'
        for rel, raw in items)
    return (
      f'<section aria-labelledby="pe"><h2 class="sec" id="pe">기존에 깨져 있던 링크 '
      f'<span class="n">{len(items)}건 · 머지 전 결정 필요</span></h2>'
      '<p class="sec-intro">마이그레이션 이전부터 깨져 있던 링크입니다 — 이번 변경이 만든 게 아니니 '
      '머지 전 처리 여부를 따로 판단하세요.</p>'
      f'<div class="card"><ul>{rows}</ul></div></section>'
    )


def _render_main(data: dict, mode: str) -> str:
    parts = [_render_masthead(data), _render_hero(data), _render_scorecard(data), _render_trees(data)]
    if mode == "plan":
        parts += [_render_migration(data), _render_decisions(data)]
    else:
        parts.append(_render_summary(data))
        s = data.get("summary") or {}
        if "grade_before" in s and "grade_after" in s:
            parts.append(_render_grade_compare(s["grade_before"], s["grade_after"]))
    pre = data.get("preexisting_broken")
    if pre:
        parts.append(_render_preexisting(pre))
    parts.append('<p class="foot">docsherpa · setup-docs</p>')
    return "<main>" + "".join(parts) + "</main>"
