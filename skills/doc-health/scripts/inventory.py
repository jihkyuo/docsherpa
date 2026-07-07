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
import sys
from pathlib import Path

EXCLUDE_DIRS = {"node_modules", ".git", "dist", "build", "vendor"}
DOC_SUFFIXES = (".md", ".mdx")


def list_docs(root):
    """ROOT 하위 전 *.md·*.mdx(제외 디렉터리 밖) → repo-상대 POSIX 경로 정렬 리스트."""
    root = Path(root).resolve()
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            if fn.endswith(DOC_SUFFIXES):
                rel = Path(dirpath, fn).relative_to(root)
                out.append(rel.as_posix())
    return sorted(out)


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
