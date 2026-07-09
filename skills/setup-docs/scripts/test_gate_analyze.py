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
