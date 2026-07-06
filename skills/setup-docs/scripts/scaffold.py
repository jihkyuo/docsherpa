"""setup-docs 설치자의 결정론적 코어 — 라우터/문서 골격 + 성장 루프 스캐폴드.

M3가 산문으로 남긴 결정론적 파일 작업을 호출 가능한 함수로 추출(M2). SKILL.md 산문은
opt-in/dry-run/프로젝트-특화 빈칸-채움만 담당하고 결정론적 부분은 여기 위임(단일 소스).
라우터 구조의 정본은 이 파일이다 — SKILL.md의 예시 블록은 설명용.
"""
import json
import os
import re
import shutil
from pathlib import Path

from contract import ROUTING_MARKER, INDEX_MARKER, MAP_MARKER, ENTRY_FILENAMES, is_marker_home
from inject_claude_md import inject_claude_md_file
from merge_settings import merge_settings_file

HOOK_CMD = "cat .claude/doc-drift-prime.txt 2>/dev/null || true"

# N11 spine: routing·index 마커의 home. 진입 라우터가 docsherpa:map 링크로 이 파일을 가리킨다.
# 맵이 docs/ 안에 살므로 인덱스 링크는 docs/ 접두어 없이(gate는 포함 파일 기준 해석).
_MAP_DOC = f"""# 문서 지도 (라우팅·인덱스)

> 이 저장소의 문서 지도. 진입 라우터가 이 파일을 가리킨다. 상세는 필요할 때만 읽는다.

## 먼저 읽기 (문서 인덱스 — 진입점만, 린) {INDEX_MARKER}
- 결정 기록(ADR) → [결정 기록](decisions/README.md)
- 작업 가이드 → [작업 가이드](how-to/)

## 문서 라우팅 룰 (새 문서가 어디로) {ROUTING_MARKER}
분류 순서대로 판정(위에서 먼저 맞는 것):
1. 구조적 결정(왜) → decisions/NNNN-*.md (_template 복사) + README 로그 추가
2. 절차/복구(어떻게) → how-to/*.md (3개↑면 _README 인덱스화)
3. 기능 스펙(무엇을) → specs/<feature>/ + plans/
4. 함께 읽혀야 할 문서 ≥2개(co-change) → <topic>/ 승격, 리드 문서가 인덱스
5. 그 외 단일 reference/explanation → 평면 [디폴트]
※ 증상 alias는 별도 troubleshooting 문서 말고 주인 문서(한계·개념)에 넣는다.

불변식: 새 문서는 반드시 위 인덱스에 등록(고아 방지) → broken=0·orphan=0 확인
"""

# 진입 라우터가 맵으로 가는 링크 한 줄 + docsherpa:map 마커(도구가 링크 줄을 찾/보호).
_MAP_LINK_SECTION = f"""## 문서 지도 {MAP_MARKER}
- 라우팅·인덱스 → [문서 지도](docs/_map.md)
"""

_URL_RE = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")   # [text](url)


def _rewrite_urls(block, from_dir, to_dir):
    """block 안의 링크 URL을 from_dir 기준 → to_dir 기준 상대경로로. 텍스트·외부·앵커 보존."""
    to_dir = Path(to_dir).resolve()

    def repl(m):
        text, url = m.group(1), m.group(2)
        if url.startswith(("http://", "https://", "mailto:", "tel:", "#", "/")):
            return m.group(0)
        trailing = "/" if url.endswith("/") else ""
        target = (Path(from_dir) / url).resolve()
        new = os.path.relpath(target, to_dir)
        return f"[{text}]({new}{trailing})"

    return _URL_RE.sub(repl, block)


_H12_RE = re.compile(r"^#{1,2}\s")
_H2_RE = re.compile(r"^##\s")
_MIGRATED_MAP_HEADER = (
    "# 문서 지도 (라우팅·인덱스)\n\n"
    "> 진입 라우터가 이 파일을 가리킨다. (인라인 마커에서 이관됨.)\n\n"
)


def _section_span(lines, marker):
    """marker를 담은 ## 헤딩부터 다음 # 또는 ## 헤딩(또는 EOF)까지의 (start, end). 없으면 None."""
    start = None
    for i, line in enumerate(lines):
        if _H2_RE.match(line) and marker in line:
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if _H12_RE.match(lines[j]):
            end = j
            break
    return (start, end)


def migrate_inline_to_map(repo_root) -> bool:
    """인라인 마커(routing·index)를 docs/_map.md로 비파괴 이동, 라우터엔 맵 링크만 남긴다.

    내용 verbatim 이동 + 링크 URL만 재작성(텍스트 보존) → content_oracle 무손실.
    인라인 home이 정확히 1개가 아니면 no-op. docs/_map.md 이미 있으면 no-op(STOP·안 덮음).
    전제: 마커 섹션은 빈 줄로 구분돼 있어야 세그먼트 경계가 보존된다. 인접(빈 줄 없음) 입력은
    content_oracle가 UNACCOUNTED로 시끄럽게 잡는다(조용한 유실 아님) — 호출부가 content_oracle를
    라이브 게이트로 돌려야 한다.
    changed? 반환."""
    root = Path(repo_root)
    entries = [(root / n, (root / n).read_text(encoding="utf-8", errors="ignore"))
               for n in ENTRY_FILENAMES if (root / n).is_file()]
    homes = [p for p, t in entries if is_marker_home(t)]
    if len(homes) != 1:
        return False
    home = homes[0]
    map_path = root / "docs" / "_map.md"
    if map_path.exists():
        return False
    lines = home.read_text(encoding="utf-8").splitlines()
    idx = _section_span(lines, INDEX_MARKER)
    rte = _section_span(lines, ROUTING_MARKER)
    if idx is None or rte is None:
        return False
    docs_dir = root / "docs"
    index_block = _rewrite_urls("\n".join(lines[idx[0]:idx[1]]).rstrip(), root, docs_dir)
    routing_block = _rewrite_urls("\n".join(lines[rte[0]:rte[1]]).rstrip(), root, docs_dir)
    docs_dir.mkdir(parents=True, exist_ok=True)
    map_path.write_text(
        _MIGRATED_MAP_HEADER + index_block + "\n\n" + routing_block + "\n",
        encoding="utf-8")
    # 두 섹션 제거 + 첫 섹션 자리에 맵 링크 삽입(섹션 순서 무관).
    spans = sorted([idx, rte])
    kept = (lines[:spans[0][0]]
            + _MAP_LINK_SECTION.rstrip("\n").splitlines()
            + lines[spans[0][1]:spans[1][0]]
            + lines[spans[1][1]:])
    home.write_text("\n".join(kept).rstrip("\n") + "\n", encoding="utf-8")
    return True


def router_skeleton(project_name: str) -> str:
    """마커는 docs/_map.md에 산다 — 라우터엔 맵 링크 한 줄만(N11 spine)."""
    return (
        f"# {project_name} 에이전트 가이드\n"
        "> 진입 라우터. 상세는 docs/를 필요할 때만 읽는다.\n\n"
        "## 항시 룰\n- 패키지/언어/배포: [채움]\n\n"
        "## 명령어\n- [채움: build/test/dev/lint]\n\n"
        + _MAP_LINK_SECTION
    )


def write_router(repo_root, project_name: str = "[프로젝트명]") -> bool:
    """AGENTS.md 없으면 skeleton(맵 링크) 생성. 있고 계약 미충족이면 맵 링크 섹션 append(기존 보존).
    이미 계약 충족(맵 링크 or 기존 인라인 마커)이면 no-op. changed? 반환."""
    path = Path(repo_root) / "AGENTS.md"
    if not path.exists():
        path.write_text(router_skeleton(project_name), encoding="utf-8")
        return True
    text = path.read_text(encoding="utf-8")
    # 이미 계약 충족 → 손대지 않음(인라인→맵 전환은 Slice B).
    if MAP_MARKER in text or (ROUTING_MARKER in text and INDEX_MARKER in text):
        return False
    suffix = "" if text.endswith("\n") else "\n"
    path.write_text(text + suffix + "\n" + _MAP_LINK_SECTION, encoding="utf-8")
    return True


def write_map(repo_root) -> bool:
    """진입 라우터가 맵을 가리킬 때만(docsherpa:map) docs/_map.md를 없으면 생성. changed? 반환.

    라우터가 맵을 안 가리키면(인라인 healthy or 부재) no-op — 두 번째 home을 만들지 않는다."""
    root = Path(repo_root)
    router = root / "AGENTS.md"
    if not router.is_file() or MAP_MARKER not in router.read_text(
            encoding="utf-8", errors="ignore"):
        return False
    path = root / "docs" / "_map.md"
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_MAP_DOC, encoding="utf-8")
    return True


def write_docs_skeleton(repo_root) -> bool:
    """decisions/_template.md·decisions/README.md·how-to/_README.md를 없는 것만 생성."""
    root = Path(repo_root)
    changed = False
    dec = root / "docs" / "decisions"
    howto = root / "docs" / "how-to"
    dec.mkdir(parents=True, exist_ok=True)
    howto.mkdir(parents=True, exist_ok=True)

    # decisions README와 _template.md는 한 쌍 — README가 _template.md를 링크하므로, README를
    # 새로 만들 때만 template도 만든다. 기존 README가 있으면 둘 다 건드리지 않는다(template만
    # 신설하면 기존 README가 링크 안 해 고아가 됨).
    readme = dec / "README.md"
    if not readme.exists():
        readme.write_text(
            "# 결정 기록 (ADR)\n구조적 결정은 결정당 1파일 `NNNN-*.md`로 남긴다(append-only).\n"
            "새 결정은 [`_template.md`](_template.md)를 복사해 만들고 아래 표에 한 줄 추가한다.\n\n"
            "| # | 결정 | 상태 | 날짜 |\n|---|------|------|------|\n| — | (아직 없음) | — | — |\n",
            encoding="utf-8")
        changed = True
        tmpl = dec / "_template.md"
        if not tmpl.exists():
            tmpl.write_text(
                "# NNNN. [결정 제목]\n- 상태: 제안 | 수락 | 폐기 | 대체됨(→ NNNN)\n"
                "- 날짜: YYYY-MM-DD\n\n## 맥락\n[무엇이 이 결정을 강제했나]\n\n"
                "## 결정\n[무엇을 하기로 했나]\n\n## 결과\n[트레이드오프]\n",
                encoding="utf-8")

    # how-to 인덱스가 이미 있으면(README.md 또는 _README.md) placeholder를 만들지 않는다 —
    # gate가 _README.md를 우선하므로 placeholder가 기존 README.md를 그늘 지워 고아로 만든다.
    if not (howto / "_README.md").exists() and not (howto / "README.md").exists():
        (howto / "_README.md").write_text(
            "# 작업 가이드 (how-to)\n<!-- PLACEHOLDER: 실제 절차(명령·진단·복구)가 생기면 *.md로 "
            "추가하고 여기 링크. 3개↑면 이 파일을 목록 인덱스로 전환. -->\n",
            encoding="utf-8")
        changed = True
    return changed


def plugin_root() -> Path:
    # scripts/scaffold.py → setup-docs → skills → <plugin>
    return Path(__file__).resolve().parents[3]


def install_loop_files(repo_root, plugin_root_dir) -> bool:
    """prime 텍스트 + doc-reconcile 정본 복사(+version stamp)를 target .claude/에. changed? 반환."""
    root = Path(repo_root)
    plug = Path(plugin_root_dir)
    changed = False
    claude = root / ".claude"
    claude.mkdir(exist_ok=True)

    prime_src = plug / "skills" / "setup-docs" / "templates" / "doc-drift-prime.txt"
    prime_dst = claude / "doc-drift-prime.txt"
    if prime_src.is_file() and not prime_dst.exists():
        shutil.copyfile(prime_src, prime_dst)
        changed = True

    dr_src = plug / "skills" / "doc-reconcile" / "SKILL.md"
    dr_dst = claude / "skills" / "doc-reconcile" / "SKILL.md"
    if dr_src.is_file() and not dr_dst.exists():
        dr_dst.parent.mkdir(parents=True, exist_ok=True)
        version = json.loads(
            (plug / ".claude-plugin" / "plugin.json").read_text()).get("version", "0")
        stamp = f"\n<!-- docsherpa-scaffold: v{version} -->\n"
        dr_dst.write_text(dr_src.read_text(encoding="utf-8") + stamp, encoding="utf-8")
        changed = True
    return changed


def scaffold(repo_root, plugin_root_dir=None, project_name="[프로젝트명]") -> dict:
    """전체 결정론적 설치. SKILL.md 산문이 opt-in/dry-run 승인 후 이걸 호출한다."""
    plug = plugin_root_dir if plugin_root_dir is not None else plugin_root()
    # settings 병합이 유일하게 던지는 단계(JSONC 거부)다 — 다른 파일을 쓰기 전에 먼저 돌려
    # 실패하면 부분 설치를 남기지 않는다(atomic-ish). merge_settings_file은 .claude 존재를 가정.
    (Path(repo_root) / ".claude").mkdir(exist_ok=True)
    settings = merge_settings_file(Path(repo_root) / ".claude", HOOK_CMD)
    return {
        "settings": settings,
        "router": write_router(repo_root, project_name),
        "map": write_map(repo_root),
        "docs": write_docs_skeleton(repo_root),
        "claude_md": inject_claude_md_file(repo_root),
        "loop": install_loop_files(repo_root, plug),
    }
