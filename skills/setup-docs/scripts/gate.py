#!/usr/bin/env python3
"""문서 도달성/링크 무결성 게이트 — setup-docs 스킬용.

루트(AGENTS.md, CLAUDE.md)에서 시작해 @import + 마크다운 링크를 따라 BFS로
모든 문서가 도달 가능한지, 깨진 링크가 없는지 검사한다.

검사 항목:
  1. broken link = 0  : 모든 ](X.md) 링크가 실제 파일로 해석된다.
  2. orphan = 0       : 모든 docs/**/*.md 가 루트에서 도달 가능하다(고아 0).

규칙:
  - 루트 = AGENTS.md(+ CLAUDE.md). CLAUDE.md 의 @AGENTS.md import 를 따라간다.
  - 링크는 그 링크를 담은 파일 기준 상대경로로 해석한다.
  - 디렉터리 링크(예: docs/how-to/)는 그 안의 _README.md/README.md 인덱스로 도달한 것으로 본다. _README.md/README.md가 없는 디렉터리 링크는 따라가지도 않고 broken으로 표시하지도 않는다.
  - http(s)/mailto/앵커-전용(#...) 링크는 무시한다.

사용:
  python3 gate.py [REPO_ROOT]    # 기본: 현재 디렉터리
종료코드: 0 = PASS, 1 = FAIL.
"""
import re
import sys
from collections import deque
from pathlib import Path

LINK_RE = re.compile(r"\]\(([^)]+)\)")           # 마크다운 링크 ](target)
IMPORT_RE = re.compile(r"(?:^|\s)@([^\s)]+\.md)")  # @path.md import


def index_of(directory: Path):
    """디렉터리의 인덱스 파일(_README.md > README.md)을 반환, 없으면 None."""
    for name in ("_README.md", "README.md"):
        cand = directory / name
        if cand.is_file():
            return cand.resolve()
    return None


def targets_in(path: Path):
    """파일 안의 모든 링크/임포트 타겟 문자열을 (raw) 리스트로 반환."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    out = [m.group(1) for m in IMPORT_RE.finditer(text)]
    out += [m.group(1) for m in LINK_RE.finditer(text)]
    return out


def resolve(base: Path, raw: str):
    """링크 타겟을 (kind, Path) 로 해석. kind: 'skip'|'file'|'dir'.

    base = 링크를 담은 파일. 반환 Path 는 절대경로(미존재여도 반환)."""
    raw = raw.strip()
    if raw.startswith(("http://", "https://", "mailto:", "tel:")):
        return ("skip", None)
    # 앵커/쿼리 제거
    raw = raw.split("#", 1)[0].split("?", 1)[0].strip()
    if not raw:
        return ("skip", None)  # 같은 파일 내 앵커
    p = (base.parent / raw).resolve()
    if raw.endswith("/"):
        return ("dir", p)
    return ("file", p)


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

    roots = [p for p in (root / "AGENTS.md", root / "CLAUDE.md") if p.is_file()]
    if not roots:
        print(f"FAIL: 진입 라우터 없음 — {root}/AGENTS.md (또는 CLAUDE.md) 가 필요하다.")
        return 1

    broken = []        # (소스파일, raw타겟)
    visited = set()    # 방문한 .md 파일(절대경로)
    queue = deque(p.resolve() for p in roots)

    while queue:
        cur = queue.popleft()
        if cur in visited:
            continue
        visited.add(cur)
        for raw in targets_in(cur):
            kind, target = resolve(cur, raw)
            if kind == "skip":
                continue
            if kind == "dir":
                if not target.is_dir():
                    broken.append((cur, raw))
                    continue
                idx = index_of(target)
                if idx:
                    queue.append(idx)
                continue
            # kind == "file"
            if not target.name.endswith(".md"):
                # 비-md 링크(이미지 등)는 broken 판정에서 제외 — 스코프 밖.
                continue
            if not target.is_file():
                broken.append((cur, raw))
                continue
            queue.append(target)

    # 도달성: 모든 docs/**/*.md 가 방문되었는가?
    docs_dir = root / "docs"
    all_docs = sorted(docs_dir.rglob("*.md")) if docs_dir.is_dir() else []
    orphans = [d for d in all_docs if d.resolve() not in visited]

    ok = not broken and not orphans
    print(f"{'PASS' if ok else 'FAIL'}: broken={len(broken)} orphan={len(orphans)} "
          f"(docs={len(all_docs)}, reachable={len(visited)})")

    if broken:
        print("\n깨진 링크:")
        for src, raw in broken:
            print(f"  {src.relative_to(root)} -> {raw}")
    if orphans:
        print("\n고아 문서(인덱스에서 도달 불가):")
        for d in orphans:
            print(f"  {d.relative_to(root)}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
