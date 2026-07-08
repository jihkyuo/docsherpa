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


def test_analyze_finds_marker_home(tmp_path):
    _mk(tmp_path, "AGENTS.md", "# R\n- [m](docs/_map.md)\n")
    _mk(tmp_path, "docs/_map.md",
        "# map\n## 인덱스 <!-- docsherpa:index -->\n- [x](x.md)\n"
        "## 라우팅 <!-- docsherpa:routing -->\nr\n")
    _mk(tmp_path, "docs/x.md", "# X\n")
    res = gate.analyze(tmp_path)
    assert len(res.homes) == 1
    assert res.homes[0].resolve() == (tmp_path / "docs" / "_map.md").resolve()
