"""gate.py --hook 모드 — SessionStart 훅에서 조용히·비파괴적으로 도는 체커.

정체성 원칙(AGENTS.md): 보조 도구, 절대 세션을 막지 않는다. 초대받지 않으면(=
docsherpa-managed 아니면) 침묵. 문제 없으면 침묵. 문제 있으면 짧게 보고, 그래도
항상 return 0.
"""
import json
from pathlib import Path

import gate

ROUTING = "<!-- docsherpa:routing -->"
INDEX = "<!-- docsherpa:index -->"

REPO_ROOT = Path(__file__).resolve().parents[3]


def _map_with_markers(root, extra_links=""):
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs" / "_map.md").write_text(
        f"# 문서 지도\n## 라우팅 {ROUTING}\n설명{extra_links}\n"
        f"## 인덱스 {INDEX}\n- 목록\n",
        encoding="utf-8",
    )


def _router_linking_to_map(root):
    (root / "AGENTS.md").write_text(
        "# repo\n## 문서 지도\n- [문서 지도](docs/_map.md)\n", encoding="utf-8"
    )


def test_clean_managed_repo_is_silent(tmp_path, capsys):
    _router_linking_to_map(tmp_path)
    _map_with_markers(tmp_path)
    rc = gate.main(["--hook", str(tmp_path)])
    assert rc == 0
    assert capsys.readouterr().out == ""


def test_broken_link_reports(tmp_path, capsys):
    _router_linking_to_map(tmp_path)
    _map_with_markers(tmp_path, extra_links="\n- [죽은링크](docs/ghost.md)")
    rc = gate.main(["--hook", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "깨진 링크" in out
    assert "docs/ghost.md" in out


def test_orphan_reports(tmp_path, capsys):
    _router_linking_to_map(tmp_path)
    _map_with_markers(tmp_path)
    (tmp_path / "docs" / "orphan.md").write_text("# 고아\n", encoding="utf-8")
    rc = gate.main(["--hook", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "고아" in out
    assert "orphan.md" in out


def test_no_router_is_silent(tmp_path, capsys):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# a\n", encoding="utf-8")
    rc = gate.main(["--hook", str(tmp_path)])
    assert rc == 0
    assert capsys.readouterr().out == ""


def test_no_marker_home_anywhere_is_silent(tmp_path, capsys):
    # 라우터(CLAUDE.md)와 docs는 있지만 어디에도 마커 home이 없는 평범한 레포.
    (tmp_path / "CLAUDE.md").write_text(
        "# 아무 프로젝트\n- [노트](docs/notes.md)\n", encoding="utf-8"
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "notes.md").write_text("# notes\n", encoding="utf-8")
    # 도달 불가한 고아까지 있어도(문제가 있어도) docsherpa-managed가 아니면 침묵해야 한다.
    (tmp_path / "docs" / "orphan.md").write_text("# 고아\n", encoding="utf-8")
    rc = gate.main(["--hook", str(tmp_path)])
    assert rc == 0
    assert capsys.readouterr().out == ""


def test_unreachable_map_still_reports_regression_guard(tmp_path, capsys):
    # docs/_map.md 에 마커 둘 다 있지만(디스크상 관리됨) 라우터가 링크를 안 걸어서
    # 도달 불가 — homes(방문 기반)는 0이 되지만, 바로 그게 가장 보고가 필요한 상황이다.
    (tmp_path / "AGENTS.md").write_text("# repo\n- 없음\n", encoding="utf-8")
    _map_with_markers(tmp_path)
    rc = gate.main(["--hook", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert out != ""


def test_truncates_long_broken_link_list(tmp_path, capsys):
    _router_linking_to_map(tmp_path)
    extra = "".join(f"\n- [x{i}](docs/ghost{i}.md)" for i in range(15))
    _map_with_markers(tmp_path, extra_links=extra)
    rc = gate.main(["--hook", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "외 " in out
    assert len(out) < 2000


def test_hooks_json_wires_session_start():
    hooks_path = REPO_ROOT / "hooks" / "hooks.json"
    data = json.loads(hooks_path.read_text(encoding="utf-8"))
    command = data["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    assert "${CLAUDE_PLUGIN_ROOT}" in command
    assert "--hook" in command
    assert "${CLAUDE_PROJECT_DIR}" in command
