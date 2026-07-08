from pathlib import Path

import pytest
import migrate
import scaffold


def test_plan_moves_type_to_folder():
    inv = [
        {"path": "adr-1.md", "type": "ADR"},
        {"path": "help.md", "type": "how-to"},
        {"path": "why.md", "type": "PRD"},
        {"path": "notes.md", "type": "reference"},
        {"path": "concept.md", "type": "explanation"},
    ]
    dests = {p["src"]: p["dest"] for p in migrate.plan_moves(inv)}
    assert dests["adr-1.md"] == "docs/decisions/adr-1.md"
    assert dests["help.md"] == "docs/how-to/help.md"
    assert dests["why.md"] == "docs/product/why.md"
    assert dests["notes.md"] == "docs/notes.md"          # reference → 평면
    assert dests["concept.md"] == "docs/concept.md"       # explanation → 평면
    assert all(p["ops"] == ["move"] for p in migrate.plan_moves(inv))


def test_plan_moves_skips_router_tooling_legacy_mdx_inplace():
    inv = [
        {"path": "AGENTS.md", "type": "reference"},              # router → skip
        {"path": ".github/X.md", "type": "reference"},           # tooling → skip
        {"path": "README.md", "type": "reference"},              # 루트관례 tooling → skip
        {"path": "docs/decisions/a.md", "type": "ADR"},          # 이미 제자리 → skip
        {"path": "docs/specs/old/2025-01-x.md", "type": "legacy"},  # 동결역사 → skip
        {"path": "guide.mdx", "type": "how-to"},                 # .mdx → skip(증분 4)
    ]
    assert migrate.plan_moves(inv) == []


def test_plan_moves_spec_and_topic_use_judgment_fields():
    inv = [
        {"path": "func.md", "type": "spec", "feature": "billing"},
        {"path": "a.md", "type": "reference", "topic": "auth"},
    ]
    dests = {p["src"]: p["dest"] for p in migrate.plan_moves(inv)}
    assert dests["func.md"] == "docs/specs/billing/func.md"
    assert dests["a.md"] == "docs/auth/a.md"                     # topic 폴더가 type보다 우선


def test_plan_moves_collision_raises():
    inv = [
        {"path": "x/help.md", "type": "how-to"},
        {"path": "y/help.md", "type": "how-to"},                 # 둘 다 docs/how-to/help.md
    ]
    with pytest.raises(ValueError):
        migrate.plan_moves(inv)


def test_rewrite_links_updates_moved_target():
    mm = {"a.md": "docs/reference/a.md", "b.md": "docs/how-to/b.md"}
    out = migrate.rewrite_links("see [B](b.md)", "a.md", mm)
    assert out == "see [B](../how-to/b.md)"


def test_rewrite_links_self_moved_target_stationary():
    mm = {"a.md": "docs/reference/a.md"}
    out = migrate.rewrite_links("[R](root.md)", "a.md", mm)
    assert out == "[R](../../root.md)"


def test_rewrite_links_preserves_anchor_slash_and_skips_external_and_absolute():
    mm = {"a.md": "docs/a.md"}
    assert migrate.rewrite_links("[x](b.md#sec)", "a.md", mm) == "[x](../b.md#sec)"
    assert migrate.rewrite_links("[e](https://x.com)", "a.md", mm) == "[e](https://x.com)"
    assert migrate.rewrite_links("[a](#top)", "a.md", mm) == "[a](#top)"
    assert migrate.rewrite_links("[abs](/root/x.md)", "a.md", mm) == "[abs](/root/x.md)"  # 루트상대 skip
    # 디렉터리 링크(후행 /)는 파일화되면 안 됨 — 슬래시 보존
    assert migrate.rewrite_links("[d](sub/)", "a.md", mm) == "[d](../sub/)"


def _mk(root, rel, text=""):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text or "# doc\n", encoding="utf-8")


def test_apply_moves_relocates_and_relinks(tmp_path):
    _mk(tmp_path, "a.md", "# A\nsee [B](b.md)\n")
    _mk(tmp_path, "b.md", "# B\n")
    _mk(tmp_path, "keep.md", "# Keep\nlink [A](a.md)\n")   # 안 움직임, a로의 링크 갱신돼야
    plan = [
        {"src": "a.md", "dest": "docs/reference/a.md", "ops": ["move"], "impact": None},
        {"src": "b.md", "dest": "docs/how-to/b.md", "ops": ["move"], "impact": None},
    ]
    migrate.apply_moves(tmp_path, plan)
    assert (tmp_path / "docs/reference/a.md").is_file()
    assert (tmp_path / "docs/how-to/b.md").is_file()
    assert not (tmp_path / "a.md").exists()
    assert "(../how-to/b.md)" in (tmp_path / "docs/reference/a.md").read_text(encoding="utf-8")
    assert "(docs/reference/a.md)" in (tmp_path / "keep.md").read_text(encoding="utf-8")


def test_apply_moves_existing_dest_collision_raises(tmp_path):
    _mk(tmp_path, "a.md", "# A\n")
    _mk(tmp_path, "docs/x.md", "# X\n")                     # 기존 파일, 이동 대상 아님
    plan = [{"src": "a.md", "dest": "docs/x.md", "ops": ["move"], "impact": None}]
    with pytest.raises(ValueError):
        migrate.apply_moves(tmp_path, plan)


def test_apply_moves_chained_dest_equals_other_src_preserves_both(tmp_path):
    # A가 B의 자리로, B는 다른 곳으로(chained). 둘 다 보존돼야(내용 소실 0).
    _mk(tmp_path, "notes/s.md", "# A\nUNIQUE_A 세그먼트.\n")
    _mk(tmp_path, "docs/how-to/s.md", "# B\nUNIQUE_B 세그먼트.\n")
    plan = [
        {"src": "notes/s.md", "dest": "docs/how-to/s.md", "ops": ["move"], "impact": None},
        {"src": "docs/how-to/s.md", "dest": "docs/reference/s.md", "ops": ["move"], "impact": None},
    ]
    migrate.apply_moves(tmp_path, plan)
    assert (tmp_path / "docs/how-to/s.md").read_text(encoding="utf-8").count("UNIQUE_A") == 1
    assert (tmp_path / "docs/reference/s.md").read_text(encoding="utf-8").count("UNIQUE_B") == 1
    assert not (tmp_path / "notes/s.md").exists()


def test_register_makes_moved_docs_reachable(tmp_path):
    import gate
    _mk(tmp_path, "CLAUDE.md", "# C\n@AGENTS.md\n")
    _mk(tmp_path, "AGENTS.md", "# A\n- [help](help.md)\n")
    _mk(tmp_path, "help.md", "# Help\n절차.\n")
    _mk(tmp_path, "notes.md", "# Notes\n참조.\n")
    plan = [
        {"src": "help.md", "dest": "docs/how-to/help.md", "ops": ["move"], "impact": None},
        {"src": "notes.md", "dest": "docs/notes.md", "ops": ["move"], "impact": None},
    ]
    migrate.apply_moves(tmp_path, plan)
    scaffold.scaffold(tmp_path, plugin_root_dir=scaffold.plugin_root())
    # 등록 전: 이동 문서는 orphan
    assert gate.analyze(tmp_path).orphans
    migrate.register_in_indexes(tmp_path, plan)
    # 등록 후: orphan=0
    res = gate.analyze(tmp_path)
    assert res.orphans == [] and res.broken == []


def test_register_nested_folder_reachable_despite_preexisting_subpath_link(tmp_path):
    # 홈(맵)에 이미 폴더 하위 '파일' 링크가 있어도 새 폴더 인덱스가 도달돼야(substring 오탐 방지, F1).
    import gate
    _mk(tmp_path, "CLAUDE.md", "# C\n@AGENTS.md\n")
    _mk(tmp_path, "AGENTS.md", "# A\n")
    _mk(tmp_path, "src.md", "# S\n내용.\n")
    plan = [{"src": "src.md", "dest": "docs/specs/billing/newdoc.md", "ops": ["move"], "impact": None}]
    migrate.apply_moves(tmp_path, plan)
    scaffold.scaffold(tmp_path, plugin_root_dir=scaffold.plugin_root())
    # 맵에 이 폴더 하위 파일 링크를 심고(+타겟 실재) 그 상태로 register.
    _mk(tmp_path, "docs/specs/billing/overview.md", "# O\n개요.\n")
    m = tmp_path / "docs/_map.md"
    m.write_text(m.read_text(encoding="utf-8") + "\n- [overview](specs/billing/overview.md)\n", encoding="utf-8")
    migrate.register_in_indexes(tmp_path, plan)
    res = gate.analyze(tmp_path)
    assert res.orphans == [] and res.broken == []


def _messy_repo(root):
    _mk(root, "CLAUDE.md", "# C\n@AGENTS.md\n")
    _mk(root, "AGENTS.md", "# A\n- [help](help.md)\n")
    _mk(root, "help.md", "# Help\n순수 절차 세그먼트 하나.\n")
    _mk(root, "notes.md", "# Notes\n참조 세그먼트 하나.\n")


def test_build_and_verify_reaches_clean_and_lossless(tmp_path):
    _messy_repo(tmp_path)
    (tmp_path / ".git").mkdir()
    plan = [
        {"src": "help.md", "dest": "docs/how-to/help.md", "ops": ["move"], "impact": None},
        {"src": "notes.md", "dest": "docs/notes.md", "ops": ["move"], "impact": None},
    ]
    res = migrate.build_and_verify(tmp_path, plan)
    assert res["broken"] == 0            # 링크 무결
    assert res["orphan"] == 0            # register가 도달성 회복
    assert res["unaccounted"] == []      # 유실 0(두 세그먼트 살아남음)


def test_build_and_verify_empty_plan_verifies_spine(tmp_path):
    # 이동할 content 0(spec §3 엣지): 빈 계획 → spine/loop만 검증. 무손실·무결 당연.
    _messy_repo(tmp_path)
    (tmp_path / ".git").mkdir()
    res = migrate.build_and_verify(tmp_path, [])
    assert res["unaccounted"] == []      # 이동 없음 → 무손실
    assert res["broken"] == 0            # scaffold spine 설치 후 링크 무결


def test_build_and_verify_no_false_loss_on_preexisting_index(tmp_path):
    # 이미 내용 있는 index 파일을 가진 repo(부분 마이그레이션)에 문서 추가 → register의 append가
    # 기존 세그먼트에 안 붙어야(content_oracle 오탐 = false STOP 방지).
    _mk(tmp_path, "CLAUDE.md", "# C\n@AGENTS.md\n")
    _mk(tmp_path, "AGENTS.md", "# A\n- [map](docs/_map.md)\n")
    _mk(tmp_path, "docs/_map.md",
        "# 지도\n\n## 먼저 읽기 <!-- docsherpa:index -->\n- [기존](existing.md)\n")
    _mk(tmp_path, "docs/existing.md", "# 기존\n기존 세그먼트.\n")
    _mk(tmp_path, "notes.md", "# Notes\n새 참조 세그먼트.\n")
    (tmp_path / ".git").mkdir()
    plan = [{"src": "notes.md", "dest": "docs/notes.md", "ops": ["move"], "impact": None}]
    res = migrate.build_and_verify(tmp_path, plan)
    assert res["unaccounted"] == []      # 기존 index 세그먼트 보존
    assert res["broken"] == 0


def _health_stub():
    return {
        "repo": {"name": "r", "docs_count": 3, "branch": "main"},
        "grade": {"current": "F", "target": "A"},
        "counts": {"fail": 5, "warn": 0, "pass": 4},
        "scorecard": {"mechanical": [], "judgment": []},
        "trees": {"before": {"title": "지금", "tag": "지금", "sub": "", "lines": []}},
        "posture": "MESSY",
    }


def test_assemble_plan_data_fills_after_and_migration():
    plan = [{"src": "help.md", "dest": "docs/how-to/help.md", "ops": ["move"],
             "impact": "custom-sync grep 경로 깨짐"}]
    d = migrate.assemble_plan_data(_health_stub(), plan)
    assert d["migration"] == [{"src": "help.md", "dest": "docs/how-to/help.md",
                               "ops": ["move"], "impact": "custom-sync grep 경로 깨짐"}]
    assert d["trees"]["after"]["tag"] == "목표"
    assert any(cls == "new" for _, cls in d["trees"]["after"]["lines"])
    assert d["decisions"] == []


def test_assemble_plan_data_renders_without_keyerror():
    import render_report
    d = migrate.assemble_plan_data(_health_stub(),
        [{"src": "a.md", "dest": "docs/a.md", "ops": ["move"], "impact": None}])
    html = render_report.render_report(d, "plan")
    assert html.count("<div") == html.count("</div>")
    assert 'style="' not in html
