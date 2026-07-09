import json

import pytest

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
    # 하위 폴더의 AGENTS.md도 router(DF2: 중첩 스코프 라우터, 제자리 skip)
    assert scorecard.disposition("sub/AGENTS.md") == "router"   # DF2: 중첩 라우터 제자리 skip


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


def _dims(codes_status):
    # codes_status = {"M1":"pass", ...} → [{code,name,sub,status}]
    return [{"code": c, "name": c, "sub": "", "status": s}
            for c, s in codes_status.items()]


def _mech(m1, m2, m3, m4, m5):
    return _dims({"M1": m1, "M2": m2, "M3": m3, "M4": m4, "M5": m5})


def _judg(j1, j2, j3, j4):
    return _dims({"J1": j1, "J2": j2, "J3": j3, "J4": j4})


def test_rollup_grade_A_all_pass():
    m = _mech("pass", "pass", "pass", "pass", "pass")
    j = _judg("pass", "pass", "pass", "pass")
    assert scorecard.rollup(m, j, 0.0, True) == "A"


def test_rollup_grade_B_one_j_warn():
    m = _mech("pass", "pass", "pass", "pass", "pass")
    j = _judg("warn", "pass", "pass", "pass")
    assert scorecard.rollup(m, j, 0.0, True) == "B"


def test_rollup_grade_C_j_fail_or_one_m_nonpass():
    m = _mech("pass", "pass", "pass", "pass", "pass")
    assert scorecard.rollup(m, _judg("fail", "pass", "pass", "pass"), 0.0, True) == "C"
    m2 = _mech("pass", "warn", "pass", "pass", "pass")   # M2~M5 중 1개 비-pass
    assert scorecard.rollup(m2, _judg("pass", "pass", "pass", "pass"), 0.0, True) == "C"


def test_rollup_grade_D_many_m_nonpass_or_m5_fail():
    m = _mech("pass", "fail", "fail", "fail", "pass")    # M2~M5 중 3개 비-pass
    assert scorecard.rollup(m, _judg("pass", "pass", "pass", "pass"), 0.0, True) == "D"
    m5f = _mech("pass", "pass", "pass", "pass", "fail")  # 대량 밖
    assert scorecard.rollup(m5f, _judg("pass", "pass", "pass", "pass"), 0.0, True) == "D"


def test_rollup_grade_D_and_F_on_reachability():
    m = _mech("fail", "fail", "fail", "fail", "fail")
    # 라우터 있으나 소수 고아 → D
    assert scorecard.rollup(m, _judg("fail", "fail", "fail", "fail"), 0.2, True) == "D"
    # 대부분 미도달 → F
    assert scorecard.rollup(m, _judg("fail", "fail", "fail", "fail"), 0.7, True) == "F"
    # 라우터 없음 → F
    assert scorecard.rollup(m, _judg("fail", "fail", "fail", "fail"), 0.0, False) == "F"


def test_counts_tally():
    m = _mech("pass", "fail", "warn", "pass", "pass")
    j = _judg("warn", "pass", "pass", "fail")
    assert scorecard.counts(m, j) == {"fail": 2, "warn": 2, "pass": 5}


def test_posture_hint(tmp_path):
    import gate
    # GREENFIELD: 라우터 없음 + content 최소
    _mk(tmp_path, "docs/a.md", "# A\n")
    res = gate.analyze(tmp_path)
    m = scorecard.machine_dims(res, ["docs/a.md"])
    assert scorecard.posture_hint(res, ["docs/a.md"], m) == "GREENFIELD"
    # HEALTHY
    _healthy_repo(tmp_path)
    res2 = gate.analyze(tmp_path)
    files = ["AGENTS.md", "docs/_map.md", "docs/a.md"]
    m2 = scorecard.machine_dims(res2, files)
    assert scorecard.posture_hint(res2, files, m2) == "HEALTHY"


def test_assemble_shape_and_keys(tmp_path):
    _healthy_repo(tmp_path)
    files = ["AGENTS.md", "docs/_map.md", "docs/a.md"]
    j = _judg("pass", "pass", "pass", "pass")
    d = scorecard.assemble(tmp_path, files, j)
    assert set(d) >= {"repo", "grade", "counts", "scorecard", "trees", "posture"}
    assert set(d["repo"]) == {"name", "docs_count", "branch"}
    assert d["repo"]["docs_count"] == 3
    assert d["grade"] == {"current": "A", "target": "A"}
    assert d["scorecard"]["mechanical"] and d["scorecard"]["judgment"]
    assert "before" in d["trees"]
    assert d["posture"] == "HEALTHY"


def test_assemble_before_tree_marks_stray(tmp_path):
    _healthy_repo(tmp_path)
    files = ["AGENTS.md", "docs/a.md", "api-help.md"]
    d = scorecard.assemble(tmp_path, files, _judg("warn", "pass", "pass", "pass"))
    lines = d["trees"]["before"]["lines"]
    assert ["api-help.md", "stray"] in lines


def test_assemble_feeds_render_report_without_keyerror(tmp_path):
    import render_report
    _healthy_repo(tmp_path)
    files = ["AGENTS.md", "docs/_map.md", "docs/a.md"]
    d = scorecard.assemble(tmp_path, files, _judg("pass", "pass", "pass", "pass"))
    # 독립 건강검진 렌더: migration·decisions 빈 리스트로 plan 모드
    d.setdefault("trees", {}).setdefault("after",
        {"title": "", "tag": "목표", "sub": "", "lines": []})
    d["migration"] = []
    d["decisions"] = []
    d["summary"] = {}
    html = render_report.render_report(d, "plan")
    assert html.count("<div") == html.count("</div>")
    assert 'style="' not in html
    assert d["repo"]["name"] in html


def test_main_with_judgment_and_manifest_returns_grade_json(tmp_path, capsys):
    _healthy_repo(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps([]), encoding="utf-8")
    judgment_path = tmp_path / "judgment.json"
    judgment_path.write_text(json.dumps(_judg("pass", "pass", "pass", "pass")),
                              encoding="utf-8")

    rc = scorecard.main([str(tmp_path),
                          "--manifest", str(manifest_path),
                          "--judgment", str(judgment_path)])

    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert set(data) >= {"repo", "grade", "scorecard"}
    assert data["grade"]["target"] == "A"
    j_codes = {d["code"] for d in data["scorecard"]["judgment"]}
    assert j_codes == {"J1", "J2", "J3", "J4"}


def test_main_without_judgment_exits_nonzero(tmp_path):
    _healthy_repo(tmp_path)
    with pytest.raises(SystemExit) as exc:
        scorecard.main([str(tmp_path)])
    assert exc.value.code != 0


def test_assemble_raises_on_empty_judgment(tmp_path):
    _healthy_repo(tmp_path)
    files = ["AGENTS.md", "docs/_map.md", "docs/a.md"]
    with pytest.raises(ValueError):
        scorecard.assemble(tmp_path, files, [])


def test_assemble_raises_on_short_judgment(tmp_path):
    _healthy_repo(tmp_path)
    files = ["AGENTS.md", "docs/_map.md", "docs/a.md"]
    with pytest.raises(ValueError):
        scorecard.assemble(tmp_path, files, _judg("pass", "pass", "pass", "pass")[:3])


def test_disposition_root_convention_case_insensitive():
    # 루트 관례 파일은 대소문자 무시(readme.md·README.md 둘 다 tooling)
    assert scorecard.disposition("readme.md") == "tooling"
    assert scorecard.disposition("README.md") == "tooling"
    assert scorecard.disposition("Changelog.MD") == "tooling"


def test_disposition_nested_readme_is_inplace_tooling():
    # DF1: 코드-인접 README는 outside_content(M5)에도 안 잡힌다(중앙집중 대상 아님)
    assert scorecard.disposition("src/x/mocks/README.md") == "tooling"
    assert scorecard.outside_content(["src/x/mocks/README.md", "notes.md"]) == ["notes.md"]


def test_outside_content_counts_buried_docs_index_readme():
    # 리뷰 픽스: 매몰된 docs 트리의 README(인덱스)는 content이므로 M5(outside_content)가
    # 진단상 정직하게 잡아야 한다 — tooling으로 숨어서 안 세는 건 소실 신호를 죽인다.
    assert scorecard.outside_content(
        ["src/a/docs/README.md", "src/a/mocks/README.md"]
    ) == ["src/a/docs/README.md"]


def test_before_tree_is_nested_scaffolding_not_flat():
    files = ["src/features/custom/shared/docs/a.md",
             "src/features/custom/shared/docs/b.md",
             "api-help.md"]
    t = scorecard._before_tree(files)
    texts = [line[0] for line in t["lines"]]
    # 중첩: 상위 폴더 라인(src/·features/ 등)이 개수와 함께 존재(평면이면 없음)
    assert any(s.strip().startswith("src/") and "(" in s for s in texts)
    assert any(s.strip().startswith("docs/") and "(" in s for s in texts)
    # 파일은 stray 클래스, 폴더는 무색
    assert any(cls == "stray" for _txt, cls in t["lines"])
    assert any(cls is None for _txt, cls in t["lines"])
    # 들여쓰기(중첩) 존재
    assert any(s.startswith("  ") for s in texts)


def test_assemble_emits_structured_orphan_count(tmp_path):
    # 고아 문서(라우터에서 도달 불가)가 있는 repo → orphans 정수 방출
    (tmp_path / "AGENTS.md").write_text("# router\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "orphan.md").write_text("# not linked\n", encoding="utf-8")
    files = ["AGENTS.md", "docs/orphan.md"]
    d = scorecard.assemble(tmp_path, files, _judg("fail", "pass", "pass", "pass"))
    assert isinstance(d["orphans"], int)
    assert d["orphans"] == 1
