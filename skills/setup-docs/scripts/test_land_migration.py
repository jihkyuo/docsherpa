import subprocess
from pathlib import Path

import pytest
import migrate


def _git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True)


def _init_repo(root):
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q"); _git(root, "config", "user.email", "t@t"); _git(root, "config", "user.name", "t")
    (root / "CLAUDE.md").write_text("# C\n@AGENTS.md\n", encoding="utf-8")
    (root / "AGENTS.md").write_text("# A\n<!-- docsherpa:map -->\n- [map](docs/_map.md)\n", encoding="utf-8")
    (root / "docs").mkdir(); (root / "docs/_map.md").write_text("# Map\n<!-- docsherpa:index -->\n", encoding="utf-8")
    (root / "guide.md").write_text("# Guide\n가이드 세그먼트.\n", encoding="utf-8")
    _git(root, "add", "-A"); _git(root, "commit", "-q", "-m", "init")


def test_land_migration_success_creates_branch_no_worktree_impact(tmp_path):
    repo = tmp_path / "repo"; _init_repo(repo)
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    plan = [{"src": "guide.md", "dest": "docs/how-to/guide.md", "ops": ["move"], "impact": None}]
    before = sorted(p.name for p in repo.iterdir())
    res = migrate.land_migration(repo, plan, head)
    assert res["branch"].startswith("docsherpa/migrate-")
    assert res["new_broken"] == [] and res["unaccounted"] == []
    assert sorted(p.name for p in repo.iterdir()) == before      # 실 작업트리 무영향
    branches = _git(repo, "branch").stdout
    assert res["branch"] in branches                              # 브랜치는 남음
    # 브랜치에 이동 반영 확인
    show = _git(repo, "show", f"{res['branch']}:docs/how-to/guide.md").stdout
    assert "가이드 세그먼트" in show


def test_land_migration_stale_head_stops(tmp_path):
    repo = tmp_path / "repo"; _init_repo(repo)
    stale = "0" * 40
    with pytest.raises(Exception):
        migrate.land_migration(repo, [], stale)


def test_land_migration_failure_leaves_zero_trace(tmp_path):
    repo = tmp_path / "repo"; _init_repo(repo)
    # a.md가 없는 b.md를 링크 → 이동 후에도 못 풂 → 하지만 base에서도 못 풂이면 preexisting.
    # new_broken 유발: 존재하는 타겟을 이동시키되 링크 재작성을 막을 순 없으니, 대신
    # verify를 강제 실패시키는 훅으로 흔적0만 검증(간이): 잘못된 dest 충돌로 apply STOP.
    (repo / "x.md").write_text("# X\n", encoding="utf-8")
    _git(repo, "add", "-A"); _git(repo, "commit", "-q", "-m", "x")
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    bad = [{"src": "x.md", "dest": "docs/_map.md", "ops": ["move"], "impact": None}]  # 기존 파일 충돌 → apply STOP
    with pytest.raises(Exception):
        migrate.land_migration(repo, bad, head)
    assert "docsherpa/migrate-" not in _git(repo, "branch").stdout    # 브랜치 0
    wl = _git(repo, "worktree", "list").stdout
    assert wl.count("\n") <= 1                                        # 메인 worktree만
