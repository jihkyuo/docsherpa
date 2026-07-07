import inventory


def _mk(root, rel, text="# doc\n"):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_list_finds_scattered_and_excludes_junk(tmp_path):
    _mk(tmp_path, "README.md")
    _mk(tmp_path, "docs/x.md")
    _mk(tmp_path, "src/features/a/docs/guide.md")   # 코드옆
    _mk(tmp_path, ".hidden/note.md")                # 숨은 폴더(제외 대상 아님)
    _mk(tmp_path, "page.mdx")                        # mdx도 1급
    _mk(tmp_path, "node_modules/pkg/readme.md")      # 제외
    _mk(tmp_path, "dist/out.md")                     # 제외
    _mk(tmp_path, ".git/COMMIT_EDITMSG.md")          # 제외
    files = inventory.list_docs(tmp_path)
    assert "README.md" in files
    assert "docs/x.md" in files
    assert "src/features/a/docs/guide.md" in files
    assert ".hidden/note.md" in files
    assert "page.mdx" in files
    assert "node_modules/pkg/readme.md" not in files
    assert "dist/out.md" not in files
    assert ".git/COMMIT_EDITMSG.md" not in files
    assert files == sorted(files)


def test_unaccounted_flags_missing(tmp_path):
    _mk(tmp_path, "a.md")
    _mk(tmp_path, "b.md")
    assert inventory.unaccounted(tmp_path, ["a.md"]) == ["b.md"]     # b 누락
    assert inventory.unaccounted(tmp_path, ["a.md", "b.md"]) == []


def test_check_cli_exit_code(tmp_path, capsys):
    _mk(tmp_path, "a.md")
    _mk(tmp_path, "b.md")
    import json
    mani = tmp_path / "m.json"
    mani.write_text(json.dumps([{"path": "a.md"}]), encoding="utf-8")   # b 누락
    rc = inventory.main(["check", str(tmp_path), "--manifest", str(mani)])
    assert rc == 1
    mani.write_text(json.dumps([{"path": "a.md"}, {"path": "b.md"}]), encoding="utf-8")
    assert inventory.main(["check", str(tmp_path), "--manifest", str(mani)]) == 0
