import scorecard


def _mk(root, rel, text="# doc\n"):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _status(dims, code):
    return next(d["status"] for d in dims if d["code"] == code)


def test_disposition_paths():
    assert scorecard.disposition("AGENTS.md") == "router"
    assert scorecard.disposition("CLAUDE.md") == "router"
    assert scorecard.disposition(".claude/skills/doc-reconcile/SKILL.md") == "tooling"
    assert scorecard.disposition(".github/PULL_REQUEST_TEMPLATE.md") == "tooling"
    assert scorecard.disposition("README.md") == "tooling"
    assert scorecard.disposition("CHANGELOG.md") == "tooling"
    assert scorecard.disposition("docs/x.md") == "content"
    assert scorecard.disposition("src/a/docs/guide.md") == "content"
    # 하위 폴더의 AGENTS.md는 router 아님(루트만)
    assert scorecard.disposition("sub/AGENTS.md") == "content"


def test_outside_content_ignores_router_and_tooling():
    files = ["AGENTS.md", "README.md", ".github/X.md",
             "docs/a.md", "api-help.md", "src/z/docs/g.md"]
    out = scorecard.outside_content(files)
    assert out == ["api-help.md", "src/z/docs/g.md"]   # content & docs/ 밖만


def _healthy_repo(root):
    _mk(root, "AGENTS.md", "# R\n- [m](docs/_map.md)\n")
    _mk(root, "docs/_map.md",
        "# map\n## 인덱스 <!-- docsherpa:index -->\n- [a](a.md)\n"
        "## 라우팅 <!-- docsherpa:routing -->\nr\n")
    _mk(root, "docs/a.md", "# A\n")
    _mk(root, ".claude/doc-drift-prime.txt", "prime")
    _mk(root, ".claude/skills/doc-reconcile/SKILL.md", "# dr\n")
    _mk(root, ".claude/settings.json", '{"hooks":{"SessionStart":[{}]}}')


def test_m_dims_all_pass_on_healthy(tmp_path):
    import gate
    _healthy_repo(tmp_path)
    files = ["AGENTS.md", "docs/_map.md", "docs/a.md"]   # content 밖 0
    res = gate.analyze(tmp_path)
    dims = scorecard.machine_dims(res, files)
    assert [_status(dims, c) for c in ("M1", "M2", "M3", "M4", "M5")] == \
        ["pass", "pass", "pass", "pass", "pass"]


def test_m1_fail_on_orphan(tmp_path):
    import gate
    _healthy_repo(tmp_path)
    _mk(tmp_path, "docs/orphan.md", "# not linked\n")
    res = gate.analyze(tmp_path)
    dims = scorecard.machine_dims(res, ["AGENTS.md", "docs/_map.md", "docs/a.md", "docs/orphan.md"])
    assert _status(dims, "M1") == "fail"


def test_m3_fail_on_inline_marker(tmp_path):
    import gate
    # 마커가 AGENTS.md 인라인(척추 미분리) → M2 pass·M3 fail
    _mk(tmp_path, "AGENTS.md",
        "# R\n## 인덱스 <!-- docsherpa:index -->\n- [a](docs/a.md)\n"
        "## 라우팅 <!-- docsherpa:routing -->\nr\n")
    _mk(tmp_path, "docs/a.md", "# A\n")
    res = gate.analyze(tmp_path)
    dims = scorecard.machine_dims(res, ["AGENTS.md", "docs/a.md"])
    assert _status(dims, "M2") == "pass"
    assert _status(dims, "M3") == "fail"


def test_m4_fail_without_loop(tmp_path):
    import gate
    _mk(tmp_path, "AGENTS.md", "# R\n- [a](docs/a.md)\n")
    _mk(tmp_path, "docs/a.md", "# A\n")
    res = gate.analyze(tmp_path)
    dims = scorecard.machine_dims(res, ["AGENTS.md", "docs/a.md"])
    assert _status(dims, "M4") == "fail"


def test_m5_warn_then_fail(tmp_path):
    import gate
    _healthy_repo(tmp_path)
    res = gate.analyze(tmp_path)
    # 2건 밖 → warn
    dims = scorecard.machine_dims(res, ["AGENTS.md", "docs/a.md", "stray1.md", "stray2.md"])
    assert _status(dims, "M5") == "warn"
    # 4건 밖 → fail (M5_WARN_MAX=3 초과)
    dims2 = scorecard.machine_dims(res, ["s1.md", "s2.md", "s3.md", "s4.md"])
    assert _status(dims2, "M5") == "fail"
