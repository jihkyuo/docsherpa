#!/usr/bin/env python3
"""문서 인벤토리 — doc-health 탐색 1단계(결정론 분모).

repo 전체 *.md·*.mdx 나열(= "잊힌 문서 0"의 분모) + 분류 매니페스트가 그 목록을
전부 덮는지 검사(unaccounted=0). 분류 자체는 병렬 서브에이전트(판단) — 여기 아님.

사용:
  inventory.py list  [ROOT]                     # → JSON {"files":[repo-상대 정렬]}
  inventory.py check [ROOT] --manifest m.json   # 매니페스트가 목록 덮나 → unaccounted, exit 1 시 STOP
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

EXCLUDE_DIRS = {"node_modules", ".git", "dist", "build", "vendor"}
DOC_SUFFIXES = (".md", ".mdx")


def _gitignored(root, candidates):
    """candidates(repo-상대 POSIX) 중 .gitignore 대상인 것들의 집합.

    분모 = "레포가 자기 것이라 선언한 문서"(디스크의 모든 .md가 아님). git이
    있으면 git의 무시-엔진에 위임(중첩 .gitignore·전역 exclude까지 정확). git이
    없으면(비-git 레포) 빈 집합 = 폴백(디스크 워크 그대로). 우리가 특정 외부
    도구 디렉터리를 하드코딩으로 판단하지 않고, 레포 선언만 존중한다."""
    if not candidates or not (root / ".git").exists():
        return set()
    try:
        # -z: 입출력 NUL 구분 + 경로 인용 안 함(비-ASCII/한글 경로가 core.quotePath로
        # 옥탈 인용돼 문자열 매칭이 깨지는 것 방지).
        proc = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "-z", "--stdin"],
            input="\0".join(candidates), capture_output=True, text=True,
        )
    except OSError:
        return set()  # git 실행 불가 → 폴백
    if proc.returncode not in (0, 1):   # 0=일부 무시됨, 1=무시 없음, 그 외=오류
        return set()
    return set(proc.stdout.split("\0")) - {""}   # 후행 NUL → 빈 문자열 제거


def list_docs(root):
    """ROOT 하위 전 *.md·*.mdx → repo-상대 POSIX 경로 정렬 리스트.

    제외: 빌드 정크(EXCLUDE_DIRS) + .gitignore 대상(git 있을 때만 — 레포가
    "프로젝트 아님"이라 선언한 것 존중; 비-git이면 디스크 워크 폴백)."""
    root = Path(root).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"root가 디렉터리가 아님(오타·이동 의심): {root}")
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            if fn.endswith(DOC_SUFFIXES):
                rel = Path(dirpath, fn).relative_to(root)
                out.append(rel.as_posix())
    ignored = _gitignored(root, out)
    return sorted(c for c in out if c not in ignored)


def unaccounted(root, manifest_paths):
    """목록에 있는데 매니페스트에 없는 경로(잊힌 문서) — 정렬."""
    return sorted(set(list_docs(root)) - set(manifest_paths))


def _manifest_paths(manifest_file):
    data = json.loads(Path(manifest_file).read_text(encoding="utf-8"))
    return [e["path"] if isinstance(e, dict) else e for e in data]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    pl = sub.add_parser("list")
    pl.add_argument("root", nargs="?", default=".")
    pc = sub.add_parser("check")
    pc.add_argument("root", nargs="?", default=".")
    pc.add_argument("--manifest", required=True)
    args = ap.parse_args(argv)

    if args.cmd == "list":
        print(json.dumps({"files": list_docs(args.root)}, ensure_ascii=False, indent=2))
        return 0

    miss = unaccounted(args.root, _manifest_paths(args.manifest))
    if miss:
        print("UNACCOUNTED (잊힌 문서 — STOP):")
        for m in miss:
            print(f"  {m}")
        return 1
    print("PASS: unaccounted=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
