import content_oracle
from inject_claude_md import inject_claude_md, inject_claude_md_file


def test_no_file_creates_import():
    out, changed = inject_claude_md(None)
    assert out == "@AGENTS.md\n" and changed is True


def test_already_imports_left_untouched():
    src = "@AGENTS.md\n"
    out, changed = inject_claude_md(src)
    assert out == src and changed is False


def test_import_notation_variant_detected():
    src = "@./AGENTS.md\n"           # ./ 표기 변형도 이미-import로 인식
    out, changed = inject_claude_md(src)
    assert out == src and changed is False


def test_other_content_prepends_import():
    src = "# My Project\nsome rules\n"
    out, changed = inject_claude_md(src)
    assert out == "@AGENTS.md\n\n# My Project\nsome rules\n" and changed is True


def test_bom_preserved_import_after_bom():
    src = "﻿# My Project\n"      # BOM은 유지하되 import는 BOM 뒤에
    out, changed = inject_claude_md(src)
    assert out == "﻿@AGENTS.md\n\n# My Project\n" and changed is True


def test_frontmatter_import_after_closing_fence():
    src = "---\ntitle: x\n---\n# Body\n"
    out, changed = inject_claude_md(src)
    # 닫는 --- 뒤 빈 줄 + @AGENTS.md + 빈 줄 — frontmatter 세그먼트와 병합 방지(G1).
    assert out == "---\ntitle: x\n---\n\n@AGENTS.md\n\n# Body\n" and changed is True


def test_file_wrapper_preserves_existing(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Existing\nrule\n", encoding="utf-8")
    changed = inject_claude_md_file(tmp_path)
    out = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert changed is True
    assert out == "@AGENTS.md\n\n# Existing\nrule\n"   # 기존 보존 + prepend


def test_file_wrapper_creates_when_absent(tmp_path):
    changed = inject_claude_md_file(tmp_path)
    assert changed is True
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n"


def test_inject_leaves_blank_line_so_first_segment_intact():
    before = "# My Project\n프로젝트 설명 세그먼트.\n"
    after, changed = inject_claude_md(before)
    assert changed
    # base 세그먼트가 after에도 key 그대로 살아있어야(content_oracle 오탐 방지).
    base_keys = {content_oracle.seg_key(s) for s in content_oracle.segment(before)}
    after_keys = {content_oracle.seg_key(s) for s in content_oracle.segment(after)}
    assert base_keys <= after_keys


def test_inject_frontmatter_preserves_frontmatter_segment_key():
    # frontmatter 뒤 빈 줄이 있는 실전 CLAUDE.md — @AGENTS.md가 frontmatter 세그먼트에
    # 병합되면(빈 줄 앞 없음) base frontmatter 세그먼트 key가 파괴돼 build_and_verify
    # false-STOP(G1). 주입은 frontmatter·본문 어느 세그먼트에도 병합되면 안 된다.
    before = "---\ntitle: x\n---\n\n# Body\n본문 세그먼트.\n"
    after, changed = inject_claude_md(before)
    assert changed
    base_keys = {content_oracle.seg_key(s) for s in content_oracle.segment(before)}
    after_keys = {content_oracle.seg_key(s) for s in content_oracle.segment(after)}
    assert base_keys <= after_keys
