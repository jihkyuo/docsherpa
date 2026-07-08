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


def test_list_docs_raises_on_missing_root(tmp_path):
    import pytest
    missing = tmp_path / "does-not-exist"
    with pytest.raises(FileNotFoundError):
        inventory.list_docs(missing)


def _git(root, *args):
    import subprocess
    subprocess.run(["git", "-C", str(root), *args],
                   check=True, capture_output=True, text=True)


def test_list_respects_gitignore_when_git_present(tmp_path):
    # gitignore된 외부 플러그인 스크래치는 분모에서 제외(레포 선언 존중)
    _mk(tmp_path, "docs/real.md")
    _mk(tmp_path, ".superpowers/sdd/scratch.md")
    _mk(tmp_path, ".gitignore", ".superpowers/\n")
    _git(tmp_path, "init")
    files = inventory.list_docs(tmp_path)
    assert "docs/real.md" in files
    assert ".superpowers/sdd/scratch.md" not in files


def test_list_keeps_untracked_but_not_ignored(tmp_path):
    # 커밋 안 했어도 무시 대상이 아니면 포함(새 문서 놓치지 않음)
    _mk(tmp_path, "new-uncommitted.md")
    _mk(tmp_path, ".gitignore", "*.log\n")
    _git(tmp_path, "init")
    files = inventory.list_docs(tmp_path)
    assert "new-uncommitted.md" in files


def test_list_non_git_ignores_gitignore(tmp_path):
    # 비-git 레포: git 없으면 .gitignore 무시하고 디스크 워크로 폴백
    _mk(tmp_path, "docs/real.md")
    _mk(tmp_path, "scratch/x.md")
    _mk(tmp_path, ".gitignore", "scratch/\n")
    files = inventory.list_docs(tmp_path)   # git init 안 함
    assert "docs/real.md" in files
    assert "scratch/x.md" in files


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


def test_list_respects_gitignore_nonascii_path(tmp_path):
    # 비-ASCII(한글) 경로도 gitignore되면 제외 — git check-ignore 출력 인용 이슈 가드
    _mk(tmp_path, "docs/진짜.md")
    _mk(tmp_path, "스크래치/메모.md")
    _mk(tmp_path, ".gitignore", "스크래치/\n")
    _git(tmp_path, "init")
    files = inventory.list_docs(tmp_path)
    assert "docs/진짜.md" in files
    assert "스크래치/메모.md" not in files
