"""setup-docs 설치자의 결정론적 코어 — 라우터/문서 골격 + 성장 루프 스캐폴드.

M3가 산문으로 남긴 결정론적 파일 작업을 호출 가능한 함수로 추출(M2). SKILL.md 산문은
opt-in/dry-run/프로젝트-특화 빈칸-채움만 담당하고 결정론적 부분은 여기 위임(단일 소스).
라우터 구조의 정본은 이 파일이다 — SKILL.md의 예시 블록은 설명용.
"""
import json
import shutil
from pathlib import Path

from check_markers import ROUTING_MARKER, INDEX_MARKER
from inject_claude_md import inject_claude_md_file
from merge_settings import merge_settings_file

HOOK_CMD = "cat .claude/doc-drift-prime.txt 2>/dev/null || true"

# greenfield에 존재가 보장되는 링크만(ARCHITECTURE.md 등 조건부 링크는 넣지 않음 — broken 방지).
_INDEX_SECTION = f"""## 먼저 읽기 (문서 인덱스 — 진입점만, 린) {INDEX_MARKER}
- 결정 기록(ADR) → [docs/decisions/README.md](docs/decisions/README.md)
- 작업 가이드 → [docs/how-to/](docs/how-to/)
"""

_ROUTING_SECTION = f"""## 문서 라우팅 룰 (새 문서가 어디로) {ROUTING_MARKER}
분류 순서대로 판정(위에서 먼저 맞는 것):
1. 구조적 결정(왜) → docs/decisions/NNNN-*.md (_template 복사) + README 로그 추가
2. 절차/복구(어떻게) → docs/how-to/*.md (3개↑면 _README 인덱스화)
3. 기능 스펙(무엇을) → docs/specs/<feature>/ + plans/
4. 함께 읽혀야 할 문서 ≥2개(co-change) → docs/<topic>/ 승격, 리드 문서가 인덱스
5. 그 외 단일 reference/explanation → docs/ 평면 [디폴트]
※ 증상 alias는 별도 troubleshooting 문서 말고 주인 문서(한계·개념)에 넣는다.

불변식: 새 문서는 반드시 위 인덱스에 등록(고아 방지) → broken=0·orphan=0 확인
"""


def router_skeleton(project_name: str) -> str:
    """마커 포함 최소 유효 AGENTS.md 텍스트."""
    return (
        f"# {project_name} 에이전트 가이드\n"
        "> 진입 라우터. 상세는 docs/를 필요할 때만 읽는다.\n\n"
        "## 항시 룰\n- 패키지/언어/배포: [채움]\n\n"
        "## 명령어\n- [채움: build/test/dev/lint]\n\n"
        + _INDEX_SECTION + "\n" + _ROUTING_SECTION
    )


def write_router(repo_root, project_name: str = "[프로젝트명]") -> bool:
    """AGENTS.md 없으면 skeleton 생성. 있고 마커 없으면 마커 섹션 append(기존 보존).
    있고 마커 있으면 no-op. changed? 반환."""
    path = Path(repo_root) / "AGENTS.md"
    if not path.exists():
        path.write_text(router_skeleton(project_name), encoding="utf-8")
        return True
    text = path.read_text(encoding="utf-8")
    if ROUTING_MARKER in text and INDEX_MARKER in text:
        return False
    # 번역/재작성된 기존 라우터 — 헤딩 매칭 대신 마커 섹션을 append(기존 전부 보존).
    suffix = "" if text.endswith("\n") else "\n"
    path.write_text(text + suffix + "\n" + _INDEX_SECTION + "\n" + _ROUTING_SECTION,
                    encoding="utf-8")
    return True


def write_docs_skeleton(repo_root) -> bool:
    """decisions/_template.md·decisions/README.md·how-to/_README.md를 없는 것만 생성."""
    root = Path(repo_root)
    changed = False
    dec = root / "docs" / "decisions"
    howto = root / "docs" / "how-to"
    dec.mkdir(parents=True, exist_ok=True)
    howto.mkdir(parents=True, exist_ok=True)

    tmpl = dec / "_template.md"
    if not tmpl.exists():
        tmpl.write_text(
            "# NNNN. [결정 제목]\n- 상태: 제안 | 수락 | 폐기 | 대체됨(→ NNNN)\n"
            "- 날짜: YYYY-MM-DD\n\n## 맥락\n[무엇이 이 결정을 강제했나]\n\n"
            "## 결정\n[무엇을 하기로 했나]\n\n## 결과\n[트레이드오프]\n",
            encoding="utf-8")
        changed = True

    readme = dec / "README.md"
    if not readme.exists():
        readme.write_text(
            "# 결정 기록 (ADR)\n구조적 결정은 결정당 1파일 `NNNN-*.md`로 남긴다(append-only).\n"
            "새 결정은 [`_template.md`](_template.md)를 복사해 만들고 아래 표에 한 줄 추가한다.\n\n"
            "| # | 결정 | 상태 | 날짜 |\n|---|------|------|------|\n| — | (아직 없음) | — | — |\n",
            encoding="utf-8")
        changed = True

    howto_readme = howto / "_README.md"
    if not howto_readme.exists():
        howto_readme.write_text(
            "# 작업 가이드 (how-to)\n<!-- PLACEHOLDER: 실제 절차(명령·진단·복구)가 생기면 *.md로 "
            "추가하고 여기 링크. 3개↑면 이 파일을 목록 인덱스로 전환. -->\n",
            encoding="utf-8")
        changed = True
    return changed
