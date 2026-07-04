import json
import pytest
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


def test_scaffold_full_install_on_empty_repo(tmp_path):
    (tmp_path / "package.json").write_text('{"name":"demo"}', encoding="utf-8")
    result = scaffold.scaffold(tmp_path, project_name="Demo")
    # 1) 마커 게이트 PASS
    assert gate.main([str(tmp_path), "--require-markers"]) == 0
    # 2) CLAUDE.md = @AGENTS.md 주입
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n"
    # 3) settings.json에 doc-drift 훅
    data = json.loads((tmp_path / ".claude/settings.json").read_text())
    cmds = [h["command"] for e in data["hooks"]["SessionStart"] for h in e["hooks"]]
    assert any("doc-drift-prime" in c for c in cmds)
    assert not (tmp_path / ".claude/settings.local.json").exists()   # D2
    # 4) 성장 루프 파일 + version stamp
    assert (tmp_path / ".claude/doc-drift-prime.txt").is_file()
    dr = (tmp_path / ".claude/skills/doc-reconcile/SKILL.md").read_text(encoding="utf-8")
    assert "docsherpa-scaffold: v" in dr
    assert result["router"] and result["loop"]


def test_docs_skeleton_preserves_existing_howto_readme(tmp_path):
    # 사용자의 실제 how-to 인덱스가 README.md로 이미 있음 — placeholder _README.md가 그늘 지우면 고아
    howto = tmp_path / "docs" / "how-to"
    howto.mkdir(parents=True)
    (howto / "README.md").write_text("# How-To Index\n- real guide\n", encoding="utf-8")
    scaffold.scaffold(tmp_path, project_name="Demo")
    assert gate.main([str(tmp_path), "--require-markers"]) == 0          # 고아 없음
    assert "real guide" in (howto / "README.md").read_text(encoding="utf-8")  # 보존
    assert not (howto / "_README.md").exists()                          # 그늘 안 침


def test_no_orphan_template_when_decisions_readme_preexists(tmp_path):
    # 사용자의 decisions/README.md가 이미 있고 _template.md를 안 링크 → template 신설하면 고아
    dec = tmp_path / "docs" / "decisions"
    dec.mkdir(parents=True)
    (dec / "README.md").write_text("# My ADRs\n표만 있고 템플릿 링크 없음\n", encoding="utf-8")
    scaffold.scaffold(tmp_path, project_name="Demo")
    assert gate.main([str(tmp_path), "--require-markers"]) == 0          # _template 고아 없음
    assert "My ADRs" in (dec / "README.md").read_text(encoding="utf-8")  # 보존


def test_scaffold_jsonc_settings_is_atomic(tmp_path):
    # JSONC settings면 설정 병합이 던지는데, 그 전에 다른 파일을 쓰면 부분 설치가 남는다
    claude = tmp_path / ".claude"
    claude.mkdir()
    (claude / "settings.json").write_text('{\n // c\n "hooks":{}\n}\n', encoding="utf-8")
    with pytest.raises(ValueError):
        scaffold.scaffold(tmp_path, project_name="Demo")
    assert not (tmp_path / "AGENTS.md").exists()                         # 부분 설치 방지


def test_write_router_appends_only_missing_marker_section(tmp_path):
    # INDEX 마커만 있고 ROUTING 없음 — ROUTING만 추가돼야(INDEX 중복 금지)
    (tmp_path / "AGENTS.md").write_text(f"# G\n## Idx {INDEX}\n- a\n", encoding="utf-8")
    scaffold.write_router(tmp_path, "Demo")
    out = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert out.count(INDEX) == 1        # 중복 안 됨
    assert out.count(ROUTING) == 1      # 추가됨
