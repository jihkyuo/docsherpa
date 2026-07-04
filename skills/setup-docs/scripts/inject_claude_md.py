"""기존 CLAUDE.md를 파괴하지 않고 @AGENTS.md import를 안전 주입.

spec §7.3 + §14 엣지: 없음(생성) / 이미 import(무변경) / 다른 내용(prepend) /
BOM(뒤에 삽입) / frontmatter(닫는 --- 뒤에 삽입). gate.py 루트 탐색이 결과에 의존.
"""
import re
from pathlib import Path

IMPORT_LINE = "@AGENTS.md"
# @AGENTS.md · @./AGENTS.md 등 표기 변형을 이미-import로 인식 (경로 앞엔 줄머리/공백)
_IMPORT_RE = re.compile(r"(?:^|\s)@\.?/?AGENTS\.md\b")


def _frontmatter_end(body: str):
    """body가 --- frontmatter로 시작하면 닫는 --- 라인 끝(문자 인덱스) 반환, 아니면 None."""
    if not body.startswith("---"):
        return None
    lines = body.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return sum(len(l) for l in lines[: i + 1])
    return None  # 미종료 frontmatter → 일반 내용으로 취급


def inject_claude_md(text):
    """(new_text, changed) 반환. text=None은 CLAUDE.md 없음."""
    if text is None:
        return IMPORT_LINE + "\n", True
    had_bom = text.startswith("﻿")
    body = text[1:] if had_bom else text
    if _IMPORT_RE.search(body):
        return text, False  # 이미 import — 손대지 않음
    prefix = "﻿" if had_bom else ""
    fm_end = _frontmatter_end(body)
    if fm_end is not None:
        new = body[:fm_end] + IMPORT_LINE + "\n" + body[fm_end:]
    else:
        new = IMPORT_LINE + "\n" + body
    return prefix + new, True


def inject_claude_md_file(repo_root) -> bool:
    """repo_root/CLAUDE.md 안전 주입. 변경 시에만 write. changed? 반환."""
    path = Path(repo_root) / "CLAUDE.md"
    text = path.read_text(encoding="utf-8") if path.exists() else None
    new, changed = inject_claude_md(text)
    if changed:
        path.write_text(new, encoding="utf-8")
    return changed
