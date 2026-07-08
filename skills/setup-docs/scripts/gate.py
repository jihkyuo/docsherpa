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
  python3 gate.py [REPO_ROOT]                     # 기본: 현재 디렉터리
  python3 gate.py [REPO_ROOT] --require-markers   # 스캐폴드 검증 시 마커 계약(D8)까지 강제
종료코드: 0 = PASS, 1 = FAIL.
"""
import re
import sys
from collections import deque
from pathlib import Path
from typing import NamedTuple

import contract

LINK_RE = re.compile(r"\]\(([^)]+)\)")           # 마크다운 링크 ](target)
IMPORT_RE = re.compile(r"(?m)^[ \t]*@([^\s)]+\.md)")  # 줄-선두 @path.md import(산문 속 @언급 제외)
FENCE_RE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)  # 펜스 코드블록(예시, live 링크 아님)


def index_of(directory: Path):
    """디렉터리의 인덱스 파일(_README.md > README.md)을 반환, 없으면 None."""
    for name in ("_README.md", "README.md"):
        cand = directory / name
        if cand.is_file():
            return cand.resolve()
    return None


def targets_in(path: Path):
    """파일 안의 모든 링크/임포트 타겟 문자열을 (raw) 리스트로 반환.

    펜스 코드블록(``` … ```)은 예시라 live 링크가 아니므로 추출 전에 제거한다."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = FENCE_RE.sub("", text)
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


class GateResult(NamedTuple):
    root: object          # Path
    router_present: bool
    broken: list          # [(src Path, raw str)]
    orphans: list         # [Path]
    all_docs: list        # [Path]
    visited: set          # {Path(resolved)}
    homes: list           # [Path] — 마커 home(방문 문서 중)


def analyze(root):
    """루트에서 BFS 도달성 분석 → GateResult(출력 없음, 순수 계산)."""
    root = Path(root).resolve()
    roots = [root / name for name in contract.ENTRY_FILENAMES
             if (root / name).is_file()]
    router_present = bool(roots)

    broken = []
    visited = set()
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
            if not target.name.endswith(".md"):
                continue
            if not target.is_file():
                broken.append((cur, raw))
                continue
            queue.append(target)

    docs_dir = root / "docs"
    all_docs = sorted(p for p in docs_dir.rglob("*.md") if p.is_file()) if docs_dir.is_dir() else []
    orphans = [d for d in all_docs if d.resolve() not in visited]

    scanned = []
    for p in visited:
        try:
            scanned.append((p, p.read_text(encoding="utf-8", errors="ignore")))
        except OSError:
            pass
    homes = contract.find_marker_home(scanned)

    return GateResult(root, router_present, broken, orphans, all_docs, visited, homes)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    require_markers = "--require-markers" in argv
    argv = [a for a in argv if a != "--require-markers"]
    root = Path(argv[0] if argv else ".").resolve()

    res = analyze(root)
    if not res.router_present:
        names = " / ".join(contract.ENTRY_FILENAMES)
        print(f"FAIL: 진입 라우터 없음 — {root}에 {names} 중 하나가 필요하다.")
        return 1

    markers_ok = True
    marker_msg = ""
    if require_markers:
        markers_ok = len(res.homes) == 1
        if len(res.homes) == 0:
            marker_msg = ("마커 home 없음: 도달 가능한 문서 중 "
                          f"{contract.ROUTING_MARKER}·{contract.INDEX_MARKER}를 "
                          "헤딩줄에 함께 가진 파일이 필요하다.")
        elif len(res.homes) > 1:
            rels = ", ".join(str(h.relative_to(root)) for h in res.homes)
            marker_msg = f"마커 home 중복(정확히 1개여야): {rels}"

    ok = not res.broken and not res.orphans and markers_ok
    print(f"{'PASS' if ok else 'FAIL'}: broken={len(res.broken)} orphan={len(res.orphans)} "
          f"(docs={len(res.all_docs)}, reachable={len(res.visited)})"
          + ("" if not require_markers else f" markers_ok={markers_ok}"))

    if res.broken:
        print("\n깨진 링크:")
        for src, raw in res.broken:
            print(f"  {src.relative_to(root)} -> {raw}")
    if res.orphans:
        print("\n고아 문서(인덱스에서 도달 불가):")
        for d in res.orphans:
            print(f"  {d.relative_to(root)}")
    if require_markers and not markers_ok:
        print("\n" + marker_msg)

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
