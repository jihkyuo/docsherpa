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


def test_apply_moves_preserves_invalid_utf8_bytes(tmp_path):
    # UTF-8로 디코드 안 되는 바이트(라틴1·깨진 인코딩 등)가 있어도 이동 후 소실 0
    # (정체성 불변식). errors="ignore"면 읽을 때 조용히 버려지고 오라클도 못 잡음(G2).
    raw = "# Doc\n".encode("utf-8") + b"\xff\xfe" + " tail 세그먼트.\n".encode("utf-8")
    (tmp_path / "a.md").write_bytes(raw)
    plan = [{"src": "a.md", "dest": "docs/a.md", "ops": ["move"], "impact": None}]
    migrate.apply_moves(tmp_path, plan)
    assert b"\xff\xfe" in (tmp_path / "docs/a.md").read_bytes()


def test_apply_moves_asserts_src_exists(tmp_path):
    _mk(tmp_path, "real.md", "# real\n")
    plan = [{"src": "ghost.md", "dest": "docs/ghost.md", "ops": ["move"], "impact": None}]  # 없는 src
    with pytest.raises(ValueError):
        migrate.apply_moves(tmp_path, plan)


def test_apply_moves_ignores_dir_named_dot_md(tmp_path):
    # rglob("*.md")는 이름이 .md로 끝나는 디렉터리도 매칭한다(vd-front dogfood 노출).
    # 그런 디렉터리를 read_text 하면 IsADirectoryError로 크래시 — is_file() 가드로 무시해야.
    (tmp_path / "weird.md").mkdir()
    _mk(tmp_path, "a.md", "# A\n")
    plan = [{"src": "a.md", "dest": "docs/a.md", "ops": ["move"], "impact": None}]
    migrate.apply_moves(tmp_path, plan)
    assert (tmp_path / "docs/a.md").is_file()
    assert (tmp_path / "weird.md").is_dir()


def test_prune_empty_dirs_removes_emptied_folder(tmp_path):
    _mk(tmp_path, "docs/keep.md", "# keep\n")          # docs는 비지 않음 → 보존돼야
    _mk(tmp_path, "docs/old/x.md", "# X\n")
    (tmp_path / "docs/old/x.md").unlink()              # 폴더만 빈 채 남음
    migrate.prune_empty_dirs(tmp_path)
    assert not (tmp_path / "docs/old").exists()
    assert (tmp_path / "docs").exists()                # 비지 않은 상위는 보존


def test_prune_empty_dirs_cascades_nested_emptied_folders(tmp_path):
    _mk(tmp_path, "docs/keep.md", "# keep\n")          # docs는 비지 않음 → 보존돼야
    _mk(tmp_path, "docs/old/sub/x.md", "# X\n")
    (tmp_path / "docs/old/sub/x.md").unlink()          # docs/old·docs/old/sub 둘 다 빈 채 남음
    migrate.prune_empty_dirs(tmp_path)
    assert not (tmp_path / "docs/old/sub").exists()    # 깊은 빈 폴더 제거
    assert not (tmp_path / "docs/old").exists()        # 자식 제거로 빈 부모까지 연쇄 제거(R4)
    assert (tmp_path / "docs").exists()                # 비지 않은 상위는 보존


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


def test_verify_migration_clean_all_zero(tmp_path):
    base = tmp_path / "base"; cur = tmp_path / "cur"
    _mk(base, "CLAUDE.md", "# C\n@AGENTS.md\n"); _mk(base, "AGENTS.md", "# A\n")
    _mk(base, "docs/a.md", "# A\n본문.\n")
    _mk(cur, "CLAUDE.md", "# C\n@AGENTS.md\n"); _mk(cur, "AGENTS.md", "# A\n\n<!-- docsherpa:map -->\n- [a](docs/a.md)\n")
    _mk(cur, "docs/a.md", "# A\n본문.\n")
    r = migrate.verify_migration(base, cur, [])
    assert r["unaccounted"] == [] and r["new_broken"] == [] and r["anchor_lost"] == []
    assert r["orphan"] == 0 and r["per_file"] == []


def test_verify_migration_flags_cur_only_broken_as_unexplained(tmp_path):
    # 정체성 안전망: cur에만 있는 파일(scaffold/register가 만든 인덱스 등)의 broken 파일-링크는
    # classify_links(base만 페어링)의 new_broken에 안 잡히고 orphan도 아니다. gate 전체 broken을
    # new_broken∪preexisting로 설명 못 하는 잔여를 unexplained_broken으로 잡아 랜딩을 STOP해야 한다.
    base = tmp_path / "base"; cur = tmp_path / "cur"
    _mk(base, "CLAUDE.md", "# C\n@AGENTS.md\n")
    _mk(base, "AGENTS.md", "# A\n\n<!-- docsherpa:map -->\n- [map](docs/_map.md)\n")
    _mk(base, "docs/_map.md", "# M\n\n<!-- docsherpa:index -->\n- [howto](how-to/)\n")
    _mk(cur, "CLAUDE.md", "# C\n@AGENTS.md\n")
    _mk(cur, "AGENTS.md", "# A\n\n<!-- docsherpa:map -->\n- [map](docs/_map.md)\n")
    _mk(cur, "docs/_map.md", "# M\n\n<!-- docsherpa:index -->\n- [howto](how-to/)\n")
    _mk(cur, "docs/how-to/_README.md", "# H\n- [gone](gone.md)\n")   # cur-only, 없는 .md 가리킴
    r = migrate.verify_migration(base, cur, [])
    assert ("docs/how-to/_README.md", "gone.md") in r["unexplained_broken"]
    assert r["new_broken"] == []          # base엔 이 파일 없어 new_broken엔 안 잡히던 gap
    assert r["orphan"] == 0               # 미도달 아님 — broken이지 orphan 아님


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
    # after 트리는 타입-색 폴더(파일 무색) 중첩 — how-to dest → t-howto 폴더 클래스(D3·D6①)
    assert any(cls == "t-howto" for _, cls in d["trees"]["after"]["lines"])
    assert d["decisions"] == []


def test_assemble_plan_data_renders_without_keyerror():
    import render_report
    d = migrate.assemble_plan_data(_health_stub(),
        [{"src": "a.md", "dest": "docs/a.md", "ops": ["move"], "impact": None}])
    html = render_report.render_report(d, "plan")
    assert html.count("<div") == html.count("</div>")
    assert 'style="' not in html


def test_register_all_registers_inplace_and_moved_uniformly(tmp_path):
    import gate
    _mk(tmp_path, "CLAUDE.md", "# C\n@AGENTS.md\n")
    _mk(tmp_path, "AGENTS.md", "# A\n<!-- docsherpa:map -->\n- [map](docs/_map.md)\n")
    _mk(tmp_path, "docs/_map.md", "# Map\n<!-- docsherpa:index -->\n")
    _mk(tmp_path, "docs/harness/inplace.md", "# 제자리 문서\n")     # 이동 안 함 → 기존 register 누락
    _mk(tmp_path, "docs/decisions/moved.md", "# 이동된 ADR\n")
    migrate.register_all(tmp_path)
    assert not gate.analyze(tmp_path).orphans          # 제자리·이동 전부 도달


def test_register_all_progress_guard_raises_on_stuck(tmp_path, monkeypatch):
    import gate
    _mk(tmp_path, "CLAUDE.md", "# C\n@AGENTS.md\n")
    _mk(tmp_path, "AGENTS.md", "# A\n")                # 라우터에 map 마커 없음 → home 없음
    _mk(tmp_path, "docs/x.md", "# X\n")                # 등록할 home이 없어 도달 불가
    import pytest
    with pytest.raises(RuntimeError):
        migrate.register_all(tmp_path)                  # 무한루프 대신 즉시 error


def test_register_all_ignores_fenced_example_links(tmp_path):
    import gate
    _mk(tmp_path, "CLAUDE.md", "# C\n@AGENTS.md\n")
    _mk(tmp_path, "AGENTS.md", "# A\n<!-- docsherpa:map -->\n- [map](docs/_map.md)\n")
    # 폴더 인덱스에 펜스 코드블록으로 bar.md 링크가 예시로 들어있음(실링크 아님)
    _mk(tmp_path, "docs/g/_README.md", "# G\n```\n- [예시](bar.md)\n```\n")
    _mk(tmp_path, "docs/g/bar.md", "# Bar\n")
    _mk(tmp_path, "docs/_map.md", "# Map\n<!-- docsherpa:index -->\n- [g](g/)\n")
    migrate.register_all(tmp_path)
    assert not gate.analyze(tmp_path).orphans          # bar.md가 펜스오탐으로 방치되지 않음


def test_register_all_ignores_fenced_example_link_in_home_file(tmp_path):
    """home(map) 파일 자체의 펜스 예시가 실링크로 오탐되면 진짜 등록이 skip되고
    진행가드가 (해결 가능한데도) 거짓 RuntimeError를 낸다 — code-review에서 발견."""
    import gate
    _mk(tmp_path, "CLAUDE.md", "# C\n@AGENTS.md\n")
    _mk(tmp_path, "AGENTS.md", "# A\n<!-- docsherpa:map -->\n- [map](docs/_map.md)\n")
    # home(docs/_map.md) 자체가 펜스 안에 실링크와 똑같은 문법을 예시로 담고 있음
    _mk(tmp_path, "docs/_map.md",
        "# Map\n<!-- docsherpa:index -->\n\n예시 문법:\n```\n- [decisions](decisions/)\n```\n")
    _mk(tmp_path, "docs/decisions/moved.md", "# 이동된 ADR\n")
    migrate.register_all(tmp_path)                      # RuntimeError 없이 실제로 배선돼야
    assert not gate.analyze(tmp_path).orphans
