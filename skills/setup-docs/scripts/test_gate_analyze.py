import gate


def _mk(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_analyze_healthy_repo(tmp_path):
    _mk(tmp_path, "AGENTS.md", "# R\n- [x](docs/x.md)\n")
    _mk(tmp_path, "docs/x.md", "# X\n")
    res = gate.analyze(tmp_path)
    assert res.router_present is True
    assert res.broken == []
    assert res.orphans == []
    assert len(res.all_docs) == 1
    assert (tmp_path / "docs" / "x.md").resolve() in res.visited


def test_analyze_detects_orphan_and_broken(tmp_path):
    _mk(tmp_path, "AGENTS.md", "# R\n- [x](docs/x.md)\n- [gone](docs/missing.md)\n")
    _mk(tmp_path, "docs/x.md", "# X\n")
    _mk(tmp_path, "docs/orphan.md", "# not linked\n")
    res = gate.analyze(tmp_path)
    assert len(res.broken) == 1
    assert len(res.orphans) == 1


def test_analyze_no_router(tmp_path):
    _mk(tmp_path, "docs/x.md", "# X\n")
    res = gate.analyze(tmp_path)
    assert res.router_present is False


def test_inline_code_span_is_not_a_live_link(tmp_path):
    # 인라인 코드스팬(`...`)은 펜스 코드블록과 같은 이유로 live 링크가 아니다 — 렌더러가
    # 링크로 만들지 않는다. 링크 문법을 *논하는* 문서(마이그레이션 계획·게이트 스펙·
    # find/replace 표)가 broken으로 잡히면, setup-docs SKILL이 처방하는 de-link(백틱화)가
    # no-op이 되고 사용자는 동결 역사를 falsify해야만 게이트를 통과한다.
    _mk(tmp_path, "AGENTS.md", "# R\n- [m](docs/x.md)\n")
    _mk(tmp_path, "docs/x.md",
        "# X\n\n"
        "게이트 스펙 인용: 모든 `](GHOST.md)` 가 실제 파일로 해석돼야 한다.\n\n"
        "재작성 표: | `[ADR-9](DECISIONS.md)` | `[ADR-9](decisions/0009-x.md)` |\n")
    res = gate.analyze(tmp_path)
    assert res.broken == []


def test_unmatched_backtick_runs_do_not_swallow_a_live_link(tmp_path):
    # 거짓 음성 가드(적대적 리뷰). CommonMark: 코드스팬은 여는/닫는 백틱 런의 **길이가 같아야**
    # 성립한다. 짝 없는 런은 문자 그대로 렌더되고 그 뒤 링크는 **살아 있다**. 런 길이를 안 보면
    # 게이트가 진짜 깨진 링크를 조용히 삼킨다 — 거짓 양성보다 나쁘다.
    _mk(tmp_path, "AGENTS.md", "# R\n- [m](docs/x.md)\n")
    _mk(tmp_path, "docs/x.md",
        "# X\n\n"
        "코드는 ``` 펜스로 감싼다, 예: [안내](gone1.md)`\n\n"      # 열림3 / 닫힘1
        "참고 ``[사라짐](gone2.md)` 여기.\n\n"                      # 열림2 / 닫힘1
        "참고 `[사라짐](gone3.md)`` 여기.\n")                       # 열림1 / 닫힘2
    res = gate.analyze(tmp_path)
    assert sorted(raw for _, raw in res.broken) == ["gone1.md", "gone2.md", "gone3.md"]


def test_code_span_inside_link_text_still_resolves(tmp_path):
    # 반대 방향 가드: 링크 *텍스트*에 코드스팬이 있는 흔한 형태는 여전히 live 링크다.
    _mk(tmp_path, "AGENTS.md", "# R\n- [`docs/x.py` 코드맵](docs/x.md)\n")
    _mk(tmp_path, "docs/x.md", "# X\n")
    res = gate.analyze(tmp_path)
    assert res.broken == []
    assert res.orphans == []


def test_main_reports_broken_link_outside_root(tmp_path, capsys):
    # 회귀 가드(test_gate_hook.py 삭제로 유실된 커버리지 복원): 라우터가 `../`로 root 밖 문서를
    # 링크하고 그 문서에 깨진 링크가 있으면 `_rel`의 relative_to가 ValueError를 던진다.
    # 크래시·침묵 없이 절대경로로라도 보고해야 한다(gate.py `_rel` 계약).
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "o.md").write_text("# o\n- [죽음](./ghost.md)\n", encoding="utf-8")
    repo = tmp_path / "repo"
    _mk(repo, "AGENTS.md", "# R\n- [외부](../outside/o.md)\n")
    rc = gate.main([str(repo)])
    out = capsys.readouterr().out
    assert rc == 1
    assert "ghost.md" in out


def test_analyze_finds_marker_home(tmp_path):
    _mk(tmp_path, "AGENTS.md", "# R\n- [m](docs/_map.md)\n")
    _mk(tmp_path, "docs/_map.md",
        "# map\n## 인덱스 <!-- docsherpa:index -->\n- [x](x.md)\n"
        "## 라우팅 <!-- docsherpa:routing -->\nr\n")
    _mk(tmp_path, "docs/x.md", "# X\n")
    res = gate.analyze(tmp_path)
    assert len(res.homes) == 1
    assert res.homes[0].resolve() == (tmp_path / "docs" / "_map.md").resolve()
