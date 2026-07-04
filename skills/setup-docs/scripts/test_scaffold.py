import json
import gate
import scaffold

ROUTING = "<!-- docsherpa:routing -->"
INDEX = "<!-- docsherpa:index -->"


def test_greenfield_router_and_docs_pass_marker_gate(tmp_path):
    scaffold.write_router(tmp_path, "Demo")
    scaffold.write_docs_skeleton(tmp_path)
    # 마커 계약 + 도달성(broken=0·orphan=0) 동시 통과
    assert gate.main([str(tmp_path), "--require-markers"]) == 0
    router = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert ROUTING in router and INDEX in router


def test_docs_skeleton_not_hollow(tmp_path):
    scaffold.write_docs_skeleton(tmp_path)
    readme = (tmp_path / "docs/decisions/README.md").read_text(encoding="utf-8")
    assert "](_template.md)" in readme                    # 템플릿 링크 = 고아 방지
    assert (tmp_path / "docs/decisions/_template.md").is_file()
    howto = (tmp_path / "docs/how-to/_README.md").read_text(encoding="utf-8")
    assert "PLACEHOLDER" in howto


def test_existing_router_markers_appended_preserving_content(tmp_path):
    # 마커 없는 번역본 라우터 + 사용자 커스텀 룰
    (tmp_path / "AGENTS.md").write_text(
        "# Guide\n## Always Rules\n- custom project rule XYZ\n", encoding="utf-8"
    )
    changed = scaffold.write_router(tmp_path, "Demo")
    out = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert changed is True
    assert "custom project rule XYZ" in out               # 기존 보존
    assert ROUTING in out and INDEX in out                # 마커 주입됨


def test_write_router_idempotent(tmp_path):
    scaffold.write_router(tmp_path, "Demo")
    changed2 = scaffold.write_router(tmp_path, "Demo")
    assert changed2 is False                              # 마커 있으면 no-op
