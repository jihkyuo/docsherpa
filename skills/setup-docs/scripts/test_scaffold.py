import json
import pytest
import gate
import scaffold
import contract

ROUTING = "<!-- docsherpa:routing -->"
INDEX = "<!-- docsherpa:index -->"


def test_greenfield_router_and_docs_pass_marker_gate(tmp_path):
    scaffold.write_router(tmp_path, "Demo")
    scaffold.write_map(tmp_path)
    scaffold.write_docs_skeleton(tmp_path)
    # 마커 계약 + 도달성(broken=0·orphan=0) 동시 통과
    assert gate.main([str(tmp_path), "--require-markers"]) == 0
    mp = (tmp_path / "docs" / "_map.md").read_text(encoding="utf-8")
    assert ROUTING in mp and INDEX in mp                  # 마커는 맵에 산다
    router = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert contract.MAP_MARKER in router                  # 라우터엔 맵 링크만


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
    scaffold.write_map(tmp_path)
    out = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert changed is True
    assert "custom project rule XYZ" in out               # 기존 보존
    assert contract.MAP_MARKER in out                     # 맵 링크 주입됨
    mp = (tmp_path / "docs" / "_map.md").read_text(encoding="utf-8")
    assert ROUTING in mp and INDEX in mp                  # 마커는 맵에


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


def test_write_router_noop_on_existing_inline_markers(tmp_path):
    # 구식 인라인 마커 라우터 → 맵 링크를 append하지 않는다(안 그러면 두 home). Slice B 몫.
    (tmp_path / "AGENTS.md").write_text(
        f"# G\n## Idx {INDEX}\n- a\n## Rules {ROUTING}\nr\n", encoding="utf-8")
    changed = scaffold.write_router(tmp_path, "Demo")
    assert changed is False                               # no-op
    assert scaffold.write_map(tmp_path) is False          # 맵도 안 만듦
    assert not (tmp_path / "docs" / "_map.md").exists()


def test_write_map_creates_map_with_markers_on_headings(tmp_path):
    # 라우터가 맵을 가리킬 때만 맵을 만든다 — 진입파일에 map 마커 선재.
    (tmp_path / "AGENTS.md").write_text(
        f"# R\n## 문서 지도 {contract.MAP_MARKER}\n- → [문서 지도](docs/_map.md)\n",
        encoding="utf-8")
    changed = scaffold.write_map(tmp_path)
    assert changed is True
    text = (tmp_path / "docs" / "_map.md").read_text(encoding="utf-8")
    assert contract.is_marker_home(text) is True          # 두 마커가 헤딩줄에


def test_write_map_idempotent(tmp_path):
    (tmp_path / "AGENTS.md").write_text(
        f"# R\n{contract.MAP_MARKER}\n", encoding="utf-8")
    assert scaffold.write_map(tmp_path) is True
    assert scaffold.write_map(tmp_path) is False          # 이미 있으면 no-op


def test_write_map_noop_when_router_does_not_point_to_map(tmp_path):
    # 라우터가 맵을 안 가리키면(인라인 healthy or map 마커 부재) 맵을 만들지 않는다 — 두 home 방지.
    (tmp_path / "AGENTS.md").write_text("# R\n## 인라인\nno map marker\n", encoding="utf-8")
    assert scaffold.write_map(tmp_path) is False
    assert not (tmp_path / "docs" / "_map.md").exists()


def test_greenfield_scaffold_is_spine(tmp_path):
    # 진입파일엔 map 마커·링크만(인라인 routing/index 0), 맵이 home, gate 두 모드 PASS.
    scaffold.write_router(tmp_path, "Demo")
    scaffold.write_map(tmp_path)
    scaffold.write_docs_skeleton(tmp_path)
    router = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert contract.MAP_MARKER in router                      # 맵 링크 마커
    assert contract.ROUTING_MARKER not in router              # 인라인 아님
    assert contract.INDEX_MARKER not in router                # 인라인 아님
    assert gate.main([str(tmp_path)]) == 0                     # broken=0 orphan=0
    assert gate.main([str(tmp_path), "--require-markers"]) == 0  # home=맵, 정확히 1


def test_rewrite_urls_strips_docs_prefix_preserving_text(tmp_path):
    out = scaffold._rewrite_urls(
        "- 설계 → [docs/DESIGN.md](docs/DESIGN.md)", tmp_path, tmp_path / "docs")
    assert "](DESIGN.md)" in out          # URL은 docs/ 기준
    assert "[docs/DESIGN.md]" in out       # 텍스트는 보존


def test_rewrite_urls_root_file_gets_dotdot(tmp_path):
    out = scaffold._rewrite_urls(
        "- 상태 → [FINDINGS.md](FINDINGS.md)", tmp_path, tmp_path / "docs")
    assert "](../FINDINGS.md)" in out


def test_rewrite_urls_dir_link_keeps_trailing_slash(tmp_path):
    out = scaffold._rewrite_urls(
        "- 계획 → [docs/plans/](docs/plans/)", tmp_path, tmp_path / "docs")
    assert "](plans/)" in out


def test_rewrite_urls_skips_external_and_anchor(tmp_path):
    out = scaffold._rewrite_urls(
        "[site](https://x.com) and [top](#head)", tmp_path, tmp_path / "docs")
    assert "](https://x.com)" in out and "](#head)" in out


def test_rewrite_urls_skips_root_relative(tmp_path):
    out = scaffold._rewrite_urls(
        "[abs](/docs/page.md)", tmp_path, tmp_path / "docs")
    assert "](/docs/page.md)" in out   # 루트-상대 링크는 그대로(가르지 않음)
