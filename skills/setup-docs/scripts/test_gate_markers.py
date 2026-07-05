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


def _write_home(p):
    p.write_text(
        "# r\n## 인덱스 <!-- docsherpa:index -->\n- [a](docs/a.md)\n\n"
        "## 라우팅 <!-- docsherpa:routing -->\n1. 결정 → decisions/\n",
        encoding="utf-8")


def test_require_markers_passes_with_single_home(tmp_path):
    _write_home(tmp_path / "AGENTS.md")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# a\n", encoding="utf-8")
    import gate
    assert gate.main([str(tmp_path), "--require-markers"]) == 0


def test_require_markers_ignores_prose_quote_of_markers(tmp_path):
    # 마커를 본문에서 인용하는 문서는 home으로 세지 않는다(false-home 방지).
    _write_home(tmp_path / "AGENTS.md")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text(
        "# a\n마커 <!-- docsherpa:index --> <!-- docsherpa:routing --> 설명.\n",
        encoding="utf-8")
    import gate
    assert gate.main([str(tmp_path), "--require-markers"]) == 0  # home은 여전히 1개


def test_require_markers_fails_on_two_homes(tmp_path):
    _write_home(tmp_path / "AGENTS.md")
    (tmp_path / "docs").mkdir()
    # 두 번째 home(헤딩줄 마커). 깨진 링크 없이 써서 rc=1이 오직 두-home 감지에서 나오게 한다.
    (tmp_path / "docs" / "a.md").write_text(
        "# a\n## i <!-- docsherpa:index -->\n## g <!-- docsherpa:routing -->\n",
        encoding="utf-8")
    import gate
    assert gate.main([str(tmp_path), "--require-markers"]) == 1  # 다수 → FAIL


def test_gemini_only_repo_seeds_gate(tmp_path):
    # AGENTS/CLAUDE 없이 GEMINI.md만 있어도 gate가 그것을 루트로 삼아
    # 링크된 문서에 도달한다(F10 봉쇄).
    (tmp_path / "GEMINI.md").write_text(
        "# g\n- [스펙](docs/spec.md)\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "spec.md").write_text("# spec\n", encoding="utf-8")
    import gate
    rc = gate.main([str(tmp_path)])
    assert rc == 0  # broken=0 orphan=0 — GEMINI.md에서 도달


def test_links_inside_code_fences_are_not_broken(tmp_path):
    # 코드 펜스 안 링크는 예시일 뿐 — live 링크 아님(고아/broken으로 세면 안 됨).
    (tmp_path / "AGENTS.md").write_text(
        "# R\n## 먼저 읽기\n- real → [docs/real.md](docs/real.md)\n\n"
        "```\nexample: [nope](does-not-exist.md) and @ghost.md\n```\n",
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/real.md").write_text("# real\n", encoding="utf-8")
    assert gate.main([str(tmp_path)]) == 0   # 펜스 안 does-not-exist.md 무시 → broken=0
