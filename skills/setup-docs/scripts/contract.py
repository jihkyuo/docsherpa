"""docsherpa 계약의 단일 소스 — 마커 상수·진입파일·마커 home locator.

N11(맵 중추 문서)의 토대. 마커/진입파일이 'AGENTS.md에 있다'는 하드코딩을
여기로 모은다. 순수 함수(파일 IO 없음) — 텍스트를 받는다.
"""
import re
from pathlib import Path

# 계약 마커(HTML 주석). 헤딩 줄 끝에 붙어 섹션을 표시 — 헤딩 번역에 견딘다(D8).
ROUTING_MARKER = "<!-- docsherpa:routing -->"
INDEX_MARKER = "<!-- docsherpa:index -->"
# N11: 진입파일에서 맵 중추 문서로 가는 링크 줄을 표시(후속 Plan에서 사용).
MAP_MARKER = "<!-- docsherpa:map -->"

# 진입 라우터로 인정하는 파일명. .md만(gate가 마크다운 링크를 파싱).
# README 제외: README에서만 도달 가능한 문서가 orphan을 가려버린다.
ENTRY_FILENAMES = ("AGENTS.md", "CLAUDE.md", "GEMINI.md")

_TOOLING_DIRS = (".claude", ".github", ".cursor", ".gitlab")
# 루트 관례 파일 — 소문자로 비교(README.md·readme.md 둘 다 매칭)
_ROOT_CONVENTION = {"readme.md", "contributing.md", "changelog.md",
                    "security.md", "code_of_conduct.md"}


def disposition(rel_path):
    """repo-상대 경로 → 'router'|'tooling'|'content' (경로 규칙, 판단 아님).

    N11 spine·배정 엔진의 공유 단일소스(gate·scorecard·migrate). 파일 IO 없음."""
    parts = Path(rel_path).parts
    if not parts:
        return "content"
    name = parts[-1]
    if len(parts) == 1 and name in ENTRY_FILENAMES:
        return "router"
    if parts[0] in _TOOLING_DIRS:
        return "tooling"
    if len(parts) == 1 and name.lower() in _ROOT_CONVENTION:
        return "tooling"
    return "content"


_FENCE_RE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)
_HEADING_RE = re.compile(r"^#{1,6}\s")


def strip_fences(text):
    """펜스 코드블록(``` … ```)을 제거 — 예시 속 마커를 home 판정에서 뺀다."""
    return _FENCE_RE.sub("", text)


def _has_marker_on_heading(text, marker):
    for line in strip_fences(text).splitlines():
        if _HEADING_RE.match(line) and marker in line:
            return True
    return False


def is_marker_home(text):
    """두 계약 마커가 모두 (펜스 제거 후) ATX 헤딩 줄에 있으면 True."""
    return (_has_marker_on_heading(text, ROUTING_MARKER)
            and _has_marker_on_heading(text, INDEX_MARKER))


def find_marker_home(files):
    """files = [(Path, text), ...] → home인 Path 리스트. 0/1/다수 판정은 호출부."""
    return [path for path, text in files if is_marker_home(text)]
