import json
import gate
import scaffold
from check_markers import has_contract_markers

PLUG = scaffold.plugin_root()   # 실제 플러그인 루트(prime·doc-reconcile 원본)


def _assert_installed_and_reachable(repo):
    # 마커 계약 + 도달성 동시 통과
    assert gate.main([str(repo), "--require-markers"]) == 0
    assert has_contract_markers((repo / "AGENTS.md").read_text(encoding="utf-8"))
    # hollow 아님 — 구체 산출물
    dec = (repo / "docs/decisions/README.md").read_text(encoding="utf-8")
    assert "](_template.md)" in dec
    assert (repo / "docs/decisions/_template.md").is_file()
    assert (repo / "docs/how-to/_README.md").is_file()
    # 루프 설치됨
    assert (repo / ".claude/doc-drift-prime.txt").is_file()


def test_fixture_empty_js_repo(tmp_path):
    (tmp_path / "package.json").write_text('{"name":"x"}', encoding="utf-8")
    scaffold.scaffold(tmp_path, PLUG, "EmptyJS")
    _assert_installed_and_reachable(tmp_path)


def test_fixture_existing_translated_agents_md(tmp_path):
    # 번역본(영문) 라우터 + 커스텀 룰, 마커 없음
    (tmp_path / "AGENTS.md").write_text(
        "# Project Guide\n## Always Rules\n- keep the custom rule ABC\n", encoding="utf-8")
    scaffold.scaffold(tmp_path, PLUG, "Trans")
    _assert_installed_and_reachable(tmp_path)
    out = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "keep the custom rule ABC" in out          # 기존 보존


def test_fixture_existing_settings_json(tmp_path):
    claude = tmp_path / ".claude"
    claude.mkdir()
    claude.joinpath("settings.json").write_text(
        '{"hooks":{"SessionStart":[{"hooks":[{"type":"command","command":"echo keep-me"}]}]}}',
        encoding="utf-8")
    scaffold.scaffold(tmp_path, PLUG, "HasSettings")
    _assert_installed_and_reachable(tmp_path)
    data = json.loads(claude.joinpath("settings.json").read_text())
    cmds = [h["command"] for e in data["hooks"]["SessionStart"] for h in e["hooks"]]
    assert "echo keep-me" in cmds                       # 기존 훅 보존
    assert any("doc-drift-prime" in c for c in cmds)    # 새 훅 추가


def test_fixture_non_english_docs(tmp_path):
    # 기존 라우터가 자기 일본어 문서를 이미 링크(도달 가능) + 마커 없음
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/概要.md").write_text("# 概要\n本文\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text(
        "# ガイド\n## 索引\n- 概要 → [docs/概要.md](docs/概要.md)\n", encoding="utf-8")
    scaffold.scaffold(tmp_path, PLUG, "NonEng")
    _assert_installed_and_reachable(tmp_path)
    # 비영어 기존 문서 보존 + 여전히 도달 가능
    assert (tmp_path / "docs/概要.md").is_file()
