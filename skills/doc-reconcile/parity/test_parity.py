"""parity 하네스 테스트 — 합성 fixture만 사용(도메인 리터럴 0, 이식성 유지).

측정 도구가 틀리면 이후의 모든 결정이 틀린다. 그래서 여기 테스트는 대부분 **조용히 틀린 숫자**를
막는 가드다(적대적 리뷰가 잡은 C1~C8). 크래시는 괜찮다. 침묵이 죄악이다.
"""
import json
import subprocess

import pytest

import arena
import score


# --- arena -------------------------------------------------------------------

def _run(repo, *a):
    subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)


def _head(repo):
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()


def _repo(tmp_path, extra=()):
    """base → (코드 착륙 커밋) → (문서 정리 커밋=시험문제). extra=(경로, 내용) 을 마지막 커밋에 얹는다."""
    r = tmp_path / "src"
    r.mkdir()
    _run(r, "init", "-q", "-b", "main")
    _run(r, "config", "user.email", "t@t.t")
    _run(r, "config", "user.name", "t")
    (r / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    (r / "docs").mkdir()
    (r / "docs" / "spec.md").write_text("# spec\nVALUE 는 1 이다.\n", encoding="utf-8")
    _run(r, "add", "-A"); _run(r, "commit", "-qm", "base")
    (r / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    _run(r, "add", "-A"); _run(r, "commit", "-qm", "feat: VALUE 2")
    (r / "docs" / "spec.md").write_text("# spec\nVALUE 는 2 이다.\n", encoding="utf-8")
    (r / "app.py").write_text("VALUE = 2\nEXTRA = 0\n", encoding="utf-8")
    for rel, body in extra:
        p = r / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    _run(r, "add", "-A"); _run(r, "commit", "-qm", "docs: spec 갱신")
    return r, _head(r)


def test_build_exports_parent_tree_without_git(tmp_path):
    r, sha = _repo(tmp_path)
    control = arena.build(r, sha, tmp_path / "out")["control"]
    assert not (control / ".git").exists(), "정답 누출 — 아레나에 히스토리가 남았다"
    assert "VALUE = 2" in (control / "app.py").read_text(encoding="utf-8")
    assert "1 이다" in (control / "docs" / "spec.md").read_text(encoding="utf-8")


def _docs_only_repo(tmp_path):
    """코드 착륙 → 문서만 정리(가장 좋은 시나리오 유형). 마지막 커밋에 코드 변경이 없다."""
    r = tmp_path / "src"
    r.mkdir()
    _run(r, "init", "-q", "-b", "main")
    _run(r, "config", "user.email", "t@t.t"); _run(r, "config", "user.name", "t")
    (r / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    (r / "docs").mkdir()
    (r / "docs" / "spec.md").write_text("# spec\nVALUE 는 1 이다.\n", encoding="utf-8")
    _run(r, "add", "-A"); _run(r, "commit", "-qm", "base")
    base = _head(r)
    (r / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    _run(r, "add", "-A"); _run(r, "commit", "-qm", "feat: VALUE 2")
    (r / "docs" / "spec.md").write_text("# spec\nVALUE 는 2 이다.\n", encoding="utf-8")
    _run(r, "add", "-A"); _run(r, "commit", "-qm", "docs(reconcile): spec 갱신")
    return r, _head(r), base


def test_docs_only_commit_without_code_base_stops_loudly(tmp_path):
    # 최고의 시나리오 유형인데 diff가 비면 에이전트가 '방금 뭘 했는지'를 못 본다.
    r, sha, _ = _docs_only_repo(tmp_path)
    with pytest.raises(arena.ArenaError, match="code-base"):
        arena.build(r, sha, tmp_path / "out")


def test_docs_only_commit_with_code_base_yields_the_landed_code(tmp_path):
    r, sha, base = _docs_only_repo(tmp_path)
    res = arena.build(r, sha, tmp_path / "out", code_base=base)
    diff = res["diff"].read_text(encoding="utf-8")
    assert "VALUE = 2" in diff, "코드 착륙분이 diff에 있어야 한다"
    assert "spec.md" not in diff, "정답 누출"
    # 트리는 언제나 부모 = 코드는 새것, 문서는 낡음
    assert "1 이다" in (res["control"] / "docs" / "spec.md").read_text(encoding="utf-8")


def test_code_diff_excludes_docs_nested_and_toplevel(tmp_path):
    r, sha = _repo(tmp_path, extra=[("README.md", "top\n"), ("docs/a/b.md", "nested\n")])
    diff = arena.build(r, sha, tmp_path / "out")["diff"].read_text(encoding="utf-8")
    assert "EXTRA = 0" in diff
    for leak in ("spec.md", "README.md", "b.md"):
        assert leak not in diff, f"정답 누출: {leak}"


def test_doc_match_is_case_insensitive(tmp_path):
    # C2: git pathspec은 대소문자를 가린다 → `README.MD` 문서 변경이 diff로 샜다.
    r, sha = _repo(tmp_path, extra=[("CHANGELOG.MD", "대문자 확장자\n")])
    diff = arena.build(r, sha, tmp_path / "out")["diff"].read_text(encoding="utf-8")
    assert "CHANGELOG.MD" not in diff, "대문자 확장자 문서가 diff로 샜다"


def test_default_globs_cover_mdx_and_rst(tmp_path):
    # C2: 기본값이 `*.md`뿐이면 .mdx/.rst 문서 변경이 정답 누출이 된다.
    r, sha = _repo(tmp_path, extra=[("notes.mdx", "x\n"), ("guide.rst", "y\n")])
    diff = arena.build(r, sha, tmp_path / "out")["diff"].read_text(encoding="utf-8")
    assert "notes.mdx" not in diff and "guide.rst" not in diff


def test_leak_guard_catches_a_doc_in_the_diff_text():
    # 사후 조건은 필터와 **독립**이어야 한다. rename처럼 헤더 한쪽만 문서인 경우를 잡는다.
    text = ("diff --git a/docs/spec.md b/src/spec_data.py\n"
            "similarity index 100%\nrename from docs/spec.md\nrename to src/spec_data.py\n")
    with pytest.raises(arena.ArenaError, match="정답 누출"):
        arena.assert_no_doc_leak(text, arena.DEFAULT_DOC_GLOBS)


def test_leak_guard_passes_on_pure_code_diff():
    arena.assert_no_doc_leak("diff --git a/app.py b/app.py\n+x\n", arena.DEFAULT_DOC_GLOBS)


def test_user_globs_can_only_widen_never_narrow(tmp_path):
    # 좁히기를 허용하면 정답이 샌다. `--doc-glob '*.rst'` 를 줘도 `*.md`는 계속 문서다.
    assert set(arena.DEFAULT_DOC_GLOBS) <= set(arena.doc_globs_for(("*.rst",)))
    assert "*.txt" in arena.doc_globs_for(("*.txt",))
    r, sha = _repo(tmp_path)
    diff = arena.build(r, sha, tmp_path / "out", doc_globs=("*.rst",))["diff"].read_text(encoding="utf-8")
    assert "spec.md" not in diff, "글롭을 좁혔더니 문서가 샜다"


def test_root_commit_gives_legible_error(tmp_path):
    r = tmp_path / "root"
    r.mkdir()
    _run(r, "init", "-q", "-b", "main")
    _run(r, "config", "user.email", "t@t.t"); _run(r, "config", "user.name", "t")
    (r / "a.py").write_text("x\n", encoding="utf-8")
    _run(r, "add", "-A"); _run(r, "commit", "-qm", "root")
    with pytest.raises(arena.ArenaError, match="루트 커밋"):
        arena.build(r, _head(r), tmp_path / "out")


def test_merge_commit_is_rejected(tmp_path):
    r, _ = _repo(tmp_path)
    _run(r, "checkout", "-q", "-b", "side", "HEAD~2")
    (r / "side.py").write_text("s\n", encoding="utf-8")
    _run(r, "add", "-A"); _run(r, "commit", "-qm", "side")
    _run(r, "checkout", "-q", "main")
    _run(r, "merge", "-q", "--no-ff", "side", "-m", "merge")
    with pytest.raises(arena.ArenaError, match="머지 커밋"):
        arena.build(r, _head(r), tmp_path / "out")


def test_is_doc_matches_basename_and_path():
    assert arena.is_doc("docs/a/b.MD", arena.DEFAULT_DOC_GLOBS)
    assert arena.is_doc("README.markdown", arena.DEFAULT_DOC_GLOBS)
    assert not arena.is_doc("src/mdx_parser.py", arena.DEFAULT_DOC_GLOBS)


# --- score -------------------------------------------------------------------

TRUTH = {"update": {"docs/a.md", "docs/b.md"}, "create": set(), "no_touch": {"docs/keep.md"}}


def _report(update, create, no_touch, tail=""):
    return ("설명 산문...\n\n```json\n"
            + json.dumps({"update": update, "create": create, "no_touch": no_touch})
            + "\n```\n" + tail)


def _pred(*a, **kw):
    pred, unresolved = score.parse_report(_report(*a), kw.get("root"))
    assert not unresolved
    return pred


def test_perfect_run():
    r = score.score_one(_pred(["docs/a.md", "docs/b.md"], [], ["docs/keep.md"]), TRUTH)
    assert r["recall"] == 1.0 and r["suppression_ok"] and r["preservation_ok"]


def test_missed_detection_lowers_recall_only():
    r = score.score_one(_pred(["docs/a.md"], [], ["docs/keep.md"]), TRUTH)
    assert r["recall"] == 0.5 and r["missed"] == ["docs/b.md"]
    assert r["suppression_ok"] and r["preservation_ok"], "탐지 실패가 다른 축을 오염시키면 안 된다"


def test_extra_update_is_not_penalized():
    r = score.score_one(_pred(["docs/a.md", "docs/b.md", "docs/z.md"], [], []), TRUTH)
    assert r["recall"] == 1.0, "정답지는 상한이 아니라 하한 — 추가발견은 감점 아님"
    assert r["extra_update"] == ["docs/z.md"]


def test_suppression_violation():
    r = score.score_one(_pred(["docs/a.md", "docs/b.md"], ["docs/decisions/0001-x.md"], []), TRUTH)
    assert not r["suppression_ok"] and r["created"] == ["docs/decisions/0001-x.md"]


def test_preservation_violation_via_update_and_via_create():
    r1 = score.score_one(_pred(["docs/a.md", "docs/keep.md"], [], []), TRUTH)
    r2 = score.score_one(_pred([], ["docs/keep.md"], []), TRUTH)
    assert not r1["preservation_ok"] and r1["preservation_violations"] == ["docs/keep.md"]
    assert not r2["preservation_ok"]


# C1 — 조용한 재현율 0
def test_dot_slash_prefix_is_normalized():
    r = score.score_one(_pred(["./docs/a.md", "docs/b.md"], [], []), TRUTH)
    assert r["recall"] == 1.0, "'./' 접두사로 재현율이 조용히 깎이면 안 된다"


def test_absolute_path_resolves_against_root(tmp_path):
    root = tmp_path / "arena" / "control"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "a.md").write_text("x", encoding="utf-8")
    pred, unresolved = score.parse_report(
        _report([str(root / "docs" / "a.md"), "docs/b.md"], [], []), root)
    assert not unresolved
    assert score.score_one(pred, TRUTH)["recall"] == 1.0


def test_absolute_path_without_root_is_reported_not_silently_missed():
    _, unresolved = score.parse_report(_report(["/tmp/x/docs/a.md"], [], []))
    assert unresolved == ["/tmp/x/docs/a.md"], "해석 못 한 절대경로는 크게 알려야 한다"


def test_main_stops_on_unresolved_absolute_path(tmp_path, capsys):
    s = tmp_path / "s.json"
    s.write_text(json.dumps({"id": "t", "ground_truth": {
        "update": ["docs/a.md"], "create": [], "no_touch": []}}), encoding="utf-8")
    rep = tmp_path / "r.md"
    rep.write_text(_report(["/abs/docs/a.md"], [], []), encoding="utf-8")
    assert score.main(["--scenario", str(s), "--report", str(rep)]) == 1
    assert "절대경로" in capsys.readouterr().err


# C3 — 판정 블록 모호성
def test_two_json_blocks_raise_instead_of_guessing():
    text = _report(["docs/a.md"], [], []) + '\n형식 예시:\n```json\n{"update": ["docs/z.md"]}\n```\n'
    with pytest.raises(ValueError, match="판정 블록이 2개"):
        score.parse_report(text)


def test_no_json_block_raises():
    with pytest.raises(ValueError, match="판정 블록"):
        score.parse_report("판정 블록 없음")


def test_non_verdict_json_block_is_ignored():
    text = '```json\n{"unrelated": 1}\n```\n' + _report(["docs/a.md"], [], [])
    assert score.parse_report(text)[0]["update"] == {"docs/a.md"}


# C4/C5 — 원소 타입 · 펜스 대소문자
def test_non_string_element_raises():
    text = '```json\n{"update": [{"path": "docs/a.md"}]}\n```'
    with pytest.raises(ValueError, match="문자열이 아니다"):
        score.parse_report(text)


def test_non_list_value_raises():
    with pytest.raises(ValueError, match="리스트가 아니다"):
        score.parse_report('```json\n{"update": "docs/a.md"}\n```')


def test_uppercase_fence_info_string_is_accepted():
    text = '```JSON\n{"update": ["docs/a.md"], "create": [], "no_touch": []}\n```'
    assert score.parse_report(text)[0]["update"] == {"docs/a.md"}


# C8 — 시나리오 모순은 어느 진입점에서도 잡힌다
def test_validate_rejects_contradictory_scenario():
    with pytest.raises(ValueError, match="update이면서 no_touch"):
        score.validate_scenario({"update": {"docs/a.md"}, "create": set(), "no_touch": {"docs/a.md"}})
    with pytest.raises(ValueError, match="create이면서 no_touch"):
        score.validate_scenario({"update": set(), "create": {"docs/a.md"}, "no_touch": {"docs/a.md"}})


def test_score_one_validates_even_when_called_directly():
    bad = {"update": {"docs/a.md"}, "create": set(), "no_touch": {"docs/a.md"}}
    with pytest.raises(ValueError):
        score.score_one(_pred(["docs/a.md"], [], []), bad)


# L4 — 정답 update가 없으면 재현율은 잴 게 없다(1.0으로 부풀리지 않는다)
def test_empty_ground_truth_update_yields_none_recall():
    truth = {"update": set(), "create": set(), "no_touch": {"docs/keep.md"}}
    r = score.score_one(_pred([], [], ["docs/keep.md"]), truth)
    assert r["recall"] is None
    assert score.aggregate([r])["recall_mean"] is None


def test_aggregate_averages_only_scored_runs():
    rows = [score.score_one(_pred(u, [], ["docs/keep.md"]), TRUTH)
            for u in (["docs/a.md", "docs/b.md"], ["docs/a.md"], [])]
    agg = score.aggregate(rows)
    assert agg["runs"] == 3
    assert agg["recall_mean"] == pytest.approx((1.0 + 0.5 + 0.0) / 3)
    assert agg["suppression_pass"] == 3 and agg["preservation_pass"] == 3
