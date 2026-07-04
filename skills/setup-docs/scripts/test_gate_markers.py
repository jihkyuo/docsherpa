import gate

ROUTING = "<!-- docsherpa:routing -->"
INDEX = "<!-- docsherpa:index -->"


def _router_without_markers(root):
    (root / "AGENTS.md").write_text(
        "# Guide\n## 문서 라우팅 룰\nrule\n## 먼저 읽기\n- x\n", encoding="utf-8"
    )


def _router_with_markers(root):
    (root / "AGENTS.md").write_text(
        f"# Guide\n## 문서 라우팅 룰 {ROUTING}\nrule\n## 먼저 읽기 {INDEX}\n- x\n",
        encoding="utf-8",
    )


def test_no_flag_ignores_markers(tmp_path):
    _router_without_markers(tmp_path)
    assert gate.main([str(tmp_path)]) == 0          # 마커 없어도 PASS(도달성만)


def test_require_markers_fails_when_absent(tmp_path):
    _router_without_markers(tmp_path)
    assert gate.main([str(tmp_path), "--require-markers"]) == 1


def test_require_markers_passes_when_present(tmp_path):
    _router_with_markers(tmp_path)
    assert gate.main([str(tmp_path), "--require-markers"]) == 0
