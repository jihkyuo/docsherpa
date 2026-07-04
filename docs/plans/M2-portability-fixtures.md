# M2 — 이식성 fixture + 설치자 오케스트레이터 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax. **Task 4(SKILL.md 산문 편집)가 섞여 인라인 실행 권장** — 산문은 subagent 위임 안 함.

**Goal:** M3 설치자를 4종 fixture repo에 **end-to-end로 자동 검증**한다. 이를 위해 M3가 산문으로 남긴 결정론적 스캐폴드를 **호출 가능한 `scaffold.py` 오케스트레이터**로 추출(M3 헬퍼 재사용)하고, 4종 fixture(빈 JS / 기존 AGENTS.md·번역본 / 기존 settings.json / 비영어 문서)에서 돌려 **gate `--require-markers` PASS + 구체 산출물(hollow 아님) + 마커 계약 + 기존 내용 보존**을 assert한다.

**Architecture:** M3 결정("오케스트레이터 없음, 산문")을 사용자 승인 하에 뒤집는다 — 설치자에 호출 가능한 본체가 없으면 자동 end-to-end 검증이 불가능하기 때문. `scaffold.py`가 결정론적 파일 작업(라우터 생성/마커 주입 + docs 골격 + CLAUDE.md 주입 + settings 병합 + prime/doc-reconcile 복사)을 담당하고 `inject_claude_md`·`merge_settings`(M3)를 재사용한다. SKILL.md 산문은 opt-in/dry-run/diff-preview/프로젝트-특화 빈칸-채움만 담당하고 결정론적 부분은 `scaffold.py`에 위임(단일 소스 — 라우터 구조 drift 방지). "이식성"의 정의는 산문이 아니라 **fixture 4종 × 구체-산출물 assert GREEN**으로 고정.

**Tech Stack:** Claude Code 플러그인, Python 3(`uv run --with pytest pytest`), git. 산문 방법론은 유닛테스트 불가 → 검증은 fixture+gate 행동적(spec §10 정직성).

## Global Constraints

- docsherpa repo 루트: `~/Desktop/private/docsherpa`. scripts: `skills/setup-docs/scripts/`.
- 테스트: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q` (repo에 venv 안 만듦). **현재 30 passed 회귀 없이 유지 + 신규 추가.**
- RED-first: 동작 코드는 실패 테스트 먼저 → GREEN.
- 커밋은 논리 단위마다. `git add -A` 금지. 커밋마다 `git push`(origin/main).
- 마커 계약(D8): `<!-- docsherpa:routing -->` · `<!-- docsherpa:index -->` (check_markers.py와 동일).
- settings 훅 명령: `cat .claude/doc-drift-prime.txt 2>/dev/null || true` (M3 템플릿·기존 테스트와 동일).
- settings는 반드시 **`settings.json`**(공유). `.local` 금지(D2).
- **정본 doc-reconcile은 프로젝트 리터럴 0** — `test_doc_reconcile_portable.py` GREEN 유지.
- scaffold가 만드는 라우터는 **greenfield에서 gate `--require-markers` PASS**(broken=0·orphan=0·마커 존재)여야 한다. 존재 안 하는 파일 링크(ARCHITECTURE.md 등)는 넣지 않는다.
- 기존 파일(AGENTS.md/CLAUDE.md/settings.json/docs) **절대 파괴 금지** — 병합·주입·append로만.

---

### Task 1: scaffold.py — 라우터 골격 + docs 골격 (code, RED-first)

결정론적 스캐폴드의 코어. greenfield 라우터(마커 포함, 최소 유효)와 docs 골격(decisions/how-to)을 만든다. gate `--require-markers`를 PASS하는 게 성공 기준. 기존 라우터가 있으면 마커만 append(기존 보존).

**Files:**
- Create: `skills/setup-docs/scripts/scaffold.py`
- Test: `skills/setup-docs/scripts/test_scaffold.py`

**Interfaces:**
- Consumes: `check_markers`(간접, gate 경유).
- Produces:
  - `ROUTING_MARKER`·`INDEX_MARKER` 재노출(check_markers와 동일 문자열).
  - `router_skeleton(project_name: str) -> str` — 마커 포함 최소 유효 AGENTS.md 텍스트. 인덱스는 `docs/decisions/README.md`·`docs/how-to/`만 링크(greenfield에 존재 보장되는 것만).
  - `write_router(repo_root, project_name="[프로젝트명]") -> bool` — AGENTS.md 없으면 skeleton 생성. 있고 마커 없으면 마커 붙은 인덱스+라우팅 섹션을 **append**(기존 보존). 있고 마커 있으면 no-op. changed? 반환.
  - `write_docs_skeleton(repo_root) -> bool` — `docs/decisions/_template.md`·`docs/decisions/README.md`(→_template.md 링크 포함)·`docs/how-to/_README.md`를 **없는 것만** 생성. changed? 반환.

- [ ] **Step 1: 실패 테스트 작성**

`skills/setup-docs/scripts/test_scaffold.py`:
```python
import gate
import scaffold

ROUTING = "<!-- docsherpa:routing -->"
INDEX = "<!-- docsherpa:index -->"


def test_greenfield_router_and_docs_pass_marker_gate(tmp_path):
    scaffold.write_router(tmp_path, "Demo")
    scaffold.write_docs_skeleton(tmp_path)
    # 마커 계약 + 도달성(broken=0·orphan=0) 동시 통과
    assert gate.main([str(tmp_path), "--require-markers"]) == 0
    router = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert ROUTING in router and INDEX in router


def test_docs_skeleton_not_hollow(tmp_path):
    scaffold.write_docs_skeleton(tmp_path)
    readme = (tmp_path / "docs/decisions/README.md").read_text(encoding="utf-8")
    assert "](_template.md)" in readme                    # 템플릿 링크 = 고아 방지
    assert (tmp_path / "docs/decisions/_template.md").is_file()
    howto = (tmp_path / "docs/how-to/_README.md").read_text(encoding="utf-8")
    assert "PLACEHOLDER" in howto


def test_existing_router_markers_appended_preserving_content(tmp_path):
    # 마커 없는 번역본 라우터 + 사용자 커스텀 룰
    (tmp_path / "AGENTS.md").write_text(
        "# Guide\n## Always Rules\n- custom project rule XYZ\n", encoding="utf-8"
    )
    changed = scaffold.write_router(tmp_path, "Demo")
    out = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert changed is True
    assert "custom project rule XYZ" in out               # 기존 보존
    assert ROUTING in out and INDEX in out                # 마커 주입됨


def test_write_router_idempotent(tmp_path):
    scaffold.write_router(tmp_path, "Demo")
    changed2 = scaffold.write_router(tmp_path, "Demo")
    assert changed2 is False                              # 마커 있으면 no-op
```

- [ ] **Step 2: 실패 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_scaffold.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'scaffold'`.

- [ ] **Step 3: 구현**

`skills/setup-docs/scripts/scaffold.py`:
```python
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
```

- [ ] **Step 4: GREEN 확인**

Run: `uv run --with pytest pytest test_scaffold.py -q`
Expected: 4 passed.

- [ ] **Step 5: 커밋 + 푸시**

```bash
cd ~/Desktop/private/docsherpa
git add skills/setup-docs/scripts/scaffold.py skills/setup-docs/scripts/test_scaffold.py
git commit -m "M2: scaffold.py router+docs skeleton (marker gate PASS, append-preserving existing)"
git push
```

---

### Task 2: scaffold.py — 전체 설치 오케스트레이터 (code)

라우터/docs 골격에 성장 루프(prime·doc-reconcile 복사) + CLAUDE.md 주입(M3) + settings 병합(M3)을 엮어 **한 번 호출로 전체 설치**하는 `scaffold()`를 만든다. fixture가 이걸 눌러 end-to-end 검증.

**Files:**
- Modify: `skills/setup-docs/scripts/scaffold.py` (append)
- Test: `skills/setup-docs/scripts/test_scaffold.py` (추가)

**Interfaces:**
- Consumes: `write_router`·`write_docs_skeleton`(Task 1) · `inject_claude_md_file`·`merge_settings_file`(M3).
- Produces:
  - `plugin_root() -> Path` — 이 스크립트 위치에서 플러그인 루트 유도(`parents[3]`).
  - `install_loop_files(repo_root, plugin_root_dir) -> bool` — `<plugin>/skills/setup-docs/templates/doc-drift-prime.txt` → `.claude/doc-drift-prime.txt`, `<plugin>/skills/doc-reconcile/SKILL.md` → `.claude/skills/doc-reconcile/SKILL.md` + version stamp(`<!-- docsherpa-scaffold: v<version> -->`). changed? 반환.
  - `scaffold(repo_root, plugin_root_dir=None, project_name="[프로젝트명]") -> dict` — 전체 설치. `{"router":bool,"docs":bool,"claude_md":bool,"settings":bool,"loop":bool}`. plugin_root_dir 없으면 `plugin_root()` 사용.

- [ ] **Step 1: 실패 테스트 작성 — 전체 설치 end-to-end**

`test_scaffold.py`에 추가:
```python
def test_scaffold_full_install_on_empty_repo(tmp_path):
    (tmp_path / "package.json").write_text('{"name":"demo"}', encoding="utf-8")
    result = scaffold.scaffold(tmp_path, project_name="Demo")
    # 1) 마커 게이트 PASS
    assert gate.main([str(tmp_path), "--require-markers"]) == 0
    # 2) CLAUDE.md = @AGENTS.md 주입
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n"
    # 3) settings.json에 doc-drift 훅
    data = json.loads((tmp_path / ".claude/settings.json").read_text())
    cmds = [h["command"] for e in data["hooks"]["SessionStart"] for h in e["hooks"]]
    assert any("doc-drift-prime" in c for c in cmds)
    assert not (tmp_path / ".claude/settings.local.json").exists()   # D2
    # 4) 성장 루프 파일 + version stamp
    assert (tmp_path / ".claude/doc-drift-prime.txt").is_file()
    dr = (tmp_path / ".claude/skills/doc-reconcile/SKILL.md").read_text(encoding="utf-8")
    assert "docsherpa-scaffold: v" in dr
    assert result["router"] and result["loop"]
```
(주의: `json` import는 test_scaffold.py 상단에 필요 — Step에서 추가.)

- [ ] **Step 2: import 보강 + 실패 확인**

`test_scaffold.py` 상단에 `import json` 추가. 
Run: `uv run --with pytest pytest test_scaffold.py::test_scaffold_full_install_on_empty_repo -q` (node id 안 먹으면 `-k full_install`).
Expected: FAIL — `AttributeError: module 'scaffold' has no attribute 'scaffold'`.

- [ ] **Step 3: 오케스트레이터 구현**

`scaffold.py`에 append:
```python
def plugin_root() -> Path:
    # scripts/scaffold.py → setup-docs → skills → <plugin>
    return Path(__file__).resolve().parents[3]


def install_loop_files(repo_root, plugin_root_dir) -> bool:
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
        text = dr_src.read_text(encoding="utf-8")
        stamp = f"\n<!-- docsherpa-scaffold: v{version} -->\n"
        dr_dst.write_text(text + stamp, encoding="utf-8")
        changed = True
    return changed


def scaffold(repo_root, plugin_root_dir=None, project_name="[프로젝트명]") -> dict:
    """전체 결정론적 설치. SKILL.md 산문이 opt-in/dry-run 승인 후 이걸 호출한다."""
    plug = plugin_root_dir if plugin_root_dir is not None else plugin_root()
    return {
        "router": write_router(repo_root, project_name),
        "docs": write_docs_skeleton(repo_root),
        "claude_md": inject_claude_md_file(repo_root),
        "settings": merge_settings_file(Path(repo_root) / ".claude", HOOK_CMD),
        "loop": install_loop_files(repo_root, plug),
    }
```

- [ ] **Step 4: GREEN 확인**

Run: `uv run --with pytest pytest test_scaffold.py -q`
Expected: 5 passed (Task 1의 4 + 전체설치 1).

- [ ] **Step 5: 커밋 + 푸시**

```bash
cd ~/Desktop/private/docsherpa
git add skills/setup-docs/scripts/scaffold.py skills/setup-docs/scripts/test_scaffold.py
git commit -m "M2: scaffold() full-install orchestrator (loop copy + version stamp, reuses inject/merge)"
git push
```

---

### Task 3: 4종 fixture end-to-end 검증 (code — spec §10.2)

spec §10.2의 4종 fixture(빈 JS / 기존 AGENTS.md·번역본 / 기존 settings.json / 비영어 문서)에서 `scaffold()`를 돌려 **gate PASS + 구체 산출물(hollow 아님) + 마커 계약 + 기존 내용 보존**을 assert한다. 이게 "설치자가 이식 가능"의 행동적 정의.

**Files:**
- Create: `skills/setup-docs/scripts/test_fixtures_portability.py`

**Interfaces:**
- Consumes: `scaffold.scaffold` · `gate.main` · `check_markers.has_contract_markers`.
- Produces: 4종 fixture end-to-end 계약. M4 독푸딩·M5 릴리스 게이트가 이 GREEN에 기댄다.

- [ ] **Step 1: 실패 테스트 작성 — 4 fixture**

`skills/setup-docs/scripts/test_fixtures_portability.py`:
```python
import json
import gate
import scaffold
from check_markers import has_contract_markers

PLUG = scaffold.plugin_root()   # 실제 플러그인 루트(prime·doc-reconcile 원본)


def _assert_installed_and_reachable(repo):
    # 마커 계약 + 도달성 동시 통과
    assert gate.main([str(repo), "--require-markers"]) == 0
    assert has_contract_markers((repo / "AGENTS.md").read_text(encoding="utf-8"))
    # hollow 아님 — 구체 산출물
    dec = (repo / "docs/decisions/README.md").read_text(encoding="utf-8")
    assert "](_template.md)" in dec
    assert (repo / "docs/decisions/_template.md").is_file()
    assert (repo / "docs/how-to/_README.md").is_file()
    # 루프 설치됨
    assert (repo / ".claude/doc-drift-prime.txt").is_file()


def test_fixture_empty_js_repo(tmp_path):
    (tmp_path / "package.json").write_text('{"name":"x"}', encoding="utf-8")
    scaffold.scaffold(tmp_path, PLUG, "EmptyJS")
    _assert_installed_and_reachable(tmp_path)


def test_fixture_existing_translated_agents_md(tmp_path):
    # 번역본(영문) 라우터 + 커스텀 룰, 마커 없음
    (tmp_path / "AGENTS.md").write_text(
        "# Project Guide\n## Always Rules\n- keep the custom rule ABC\n", encoding="utf-8")
    scaffold.scaffold(tmp_path, PLUG, "Trans")
    _assert_installed_and_reachable(tmp_path)
    out = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "keep the custom rule ABC" in out          # 기존 보존


def test_fixture_existing_settings_json(tmp_path):
    claude = tmp_path / ".claude"; claude.mkdir()
    claude.joinpath("settings.json").write_text(
        '{"hooks":{"SessionStart":[{"hooks":[{"type":"command","command":"echo keep-me"}]}]}}',
        encoding="utf-8")
    scaffold.scaffold(tmp_path, PLUG, "HasSettings")
    _assert_installed_and_reachable(tmp_path)
    data = json.loads(claude.joinpath("settings.json").read_text())
    cmds = [h["command"] for e in data["hooks"]["SessionStart"] for h in e["hooks"]]
    assert "echo keep-me" in cmds                       # 기존 훅 보존
    assert any("doc-drift-prime" in c for c in cmds)    # 새 훅 추가


def test_fixture_non_english_docs(tmp_path):
    # 기존 라우터가 자기 일본어 문서를 이미 링크(도달 가능) + 마커 없음
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/概要.md").write_text("# 概要\n本文\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text(
        "# ガイド\n## 索引\n- 概要 → [docs/概要.md](docs/概要.md)\n", encoding="utf-8")
    scaffold.scaffold(tmp_path, PLUG, "NonEng")
    _assert_installed_and_reachable(tmp_path)
    # 비영어 기존 문서 보존 + 여전히 도달 가능
    assert (tmp_path / "docs/概要.md").is_file()
```

- [ ] **Step 2: 실패/통과 확인 (진단)**

Run: `uv run --with pytest pytest test_fixtures_portability.py -v`
Expected: 대부분 통과할 수 있으나 — **비영어 fixture(④)에서 orphan 위험 점검**: scaffold가 append한 인덱스가 `docs/decisions/README.md`·`docs/how-to/`를 링크하고 그 파일들이 생성되므로 도달 가능. 기존 `docs/概要.md`는 기존 라우터가 이미 링크 → 도달 가능. 만약 orphan/broken으로 FAIL하면 원인(어떤 문서가 도달 불가)을 gate 출력에서 확인하고 fixture를 "기존 문서가 라우터에 링크된 상태"로 교정(스캐폴드는 기존 미인덱스 문서를 자동 인덱싱하지 않음 — 그건 MESSY 경로/에이전트 몫). 교정 후 재실행.

- [ ] **Step 3: 4 fixture GREEN 확인**

Run: `uv run --with pytest pytest test_fixtures_portability.py -q`
Expected: 4 passed.

- [ ] **Step 4: 커밋 + 푸시**

```bash
cd ~/Desktop/private/docsherpa
git add skills/setup-docs/scripts/test_fixtures_portability.py
git commit -m "M2: 4 portability fixtures end-to-end (gate+markers+no-hollow+preservation, §10.2)"
git push
```

---

### Task 4: SKILL.md 산문 — scaffold.py 위임으로 개정 (prose — 인라인, subagent 금지)

"성장 루프 설치" 섹션의 결정론적 단계(라우터 생성·docs 골격·복사·병합·주입)를 **`scaffold.py` 호출로 위임**한다. opt-in·dry-run·diff-preview·프로젝트 빈칸-채움·D7 투명성 산문은 유지. AGENTS.md 템플릿 블록엔 "정본은 scaffold.py, 이 블록은 설명용" 주석 1줄.

**Files:**
- Modify: `skills/setup-docs/SKILL.md`

**Interfaces:**
- Consumes: `scaffold.py`(Task 1-2).
- Produces: 개정된 SKILL.md — 결정론적 부분은 scaffold.py 단일 소스, 산문은 대화/판단만.

- [ ] **Step 1: "성장 루프 설치" 섹션의 3-6 단계를 scaffold 호출로 교체**

현재 SKILL.md "성장 루프 설치" 섹션의 3~6번(doc-reconcile 복사 / prime 복사 / settings 병합 / CLAUDE.md 주입)을 다음 한 단계로 축약(1 계획-preview, 2 비대화형 dry-run, 7 D7 투명성, 8 검증은 유지):
```markdown
3. **결정론적 설치 실행.** 승인(대화형) 또는 `--yes`(비대화형) 후,
   `<skill>/scripts/scaffold.py`의 `scaffold(repo_root, project_name=...)`를 호출한다. 이 함수가
   결정론적으로: 라우터 생성/마커 주입(기존 보존·append) + `docs/decisions`·`docs/how-to` 골격 +
   `inject_claude_md_file`로 CLAUDE.md 안전 주입 + `merge_settings_file`로 `settings.json`(공유) 훅
   멱등 병합 + prime/doc-reconcile 복사(+version stamp)를 수행한다. 반환 dict로 무엇이 바뀌었는지 보고.
   ⚠️ `settings.json`이 JSONC면 `merge_settings_file`가 `ValueError`로 거부 → 사용자에게 수동 병합 안내.
4. **프로젝트 빈칸 채움(산문).** scaffold가 만든 라우터의 `[채움]`(항시룰·명령어)을 스택 신호로 채운다.
   확신되는 것만, 불확실하면 생략(hollow 방지). 기존 라우터였으면 append된 중복 섹션을 사용자와 상의해 정리.
```
(기존 5~8번 중 D7 투명성·스캐폴드 검증은 번호만 밀려 유지.)

- [ ] **Step 2: AGENTS.md 템플릿 블록에 정본 주석 추가**

"### AGENTS.md 템플릿" 헤딩 바로 아래에 1줄:
```markdown
> **정본은 `scripts/scaffold.py`의 `router_skeleton()`** — 아래 블록은 구조 설명용. 실제 생성은 scaffold가 한다.
```

- [ ] **Step 3: 육안 검증 — 척추 + 위임 일관**

Read `skills/setup-docs/SKILL.md`. 확인:
  - GREENFIELD/MESSY/멱등 규칙 문단 훼손 없음.
  - "성장 루프 설치"가 이제 scaffold 호출 + opt-in/dry-run/D7/검증을 담고, 결정론적 파일작업을 손으로 나열하지 않음.
  - 마커 문자열 정확(`<!-- docsherpa:routing -->`·`<!-- docsherpa:index -->`).

- [ ] **Step 4: 커밋 + 푸시**

```bash
cd ~/Desktop/private/docsherpa
git add skills/setup-docs/SKILL.md
git commit -m "M2: delegate deterministic scaffold to scaffold.py in SKILL prose (single source, anti-drift)"
git push
```

---

### Task 5: M2 종료 — 전체 GREEN + /code-review + FINDINGS + 다음(M4) 지시

**Files:**
- Modify: `FINDINGS.md`

- [ ] **Step 1: 전체 스크립트 테스트 GREEN**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`
Expected: 30(M3) + scaffold(5) + fixtures(4) = **39 passed**. 다르면 회귀 조사(기존 30 줄면 STOP).

- [ ] **Step 2: 이식성 가드 재확인**

Run: `uv run --with pytest pytest test_doc_reconcile_portable.py -q`
Expected: 2 passed — 정본 doc-reconcile에 프로젝트 리터럴 없음.

- [ ] **Step 3: /code-review (설치자 오케스트레이터는 핵심 변경)**

`scaffold.py`는 파일을 쓰는 오케스트레이터라 위험도 있음 → `/code-review high`로 자가검증. 발견 시 RED-first로 픽스.

- [ ] **Step 4: FINDINGS 갱신**

FINDINGS.md 맨 위 "다음 세션 시작점"을 M2 완료 → **M4 독푸딩**으로:
  - 상태: M0·M1·M3·**M2 완료.** 다음 = **M4 독푸딩**(second-brain 재스캐폴드 + behavioral parity + 기존 훅 보존 + global 제거).
  - 순서: M1→M3→M2→**M4**→M5.
  - M2가 닫은 것: scaffold.py 오케스트레이터(호출 가능 설치자 본체) + 4종 fixture end-to-end GREEN(gate+markers+no-hollow+preservation) + SKILL 산문을 scaffold 위임으로 개정.
  - 테스트 러너 "30 passed" → "39 passed".
  - 이어읽기: DESIGN §9(독푸딩 마이그레이션·behavioral parity)·§10.3.
  하단에 M2 완료 문단(GREEN, 무엇을 닫았나, 남은 것: M4가 실제 설치·parity로 검증).

- [ ] **Step 5: 커밋 + 푸시**

```bash
cd ~/Desktop/private/docsherpa
git add FINDINGS.md docs/plans/M2-portability-fixtures.md
git commit -m "M2: complete — scaffold orchestrator + 4 fixtures GREEN (39 tests), ready for M4"
git push
```

---

## Self-Review

**Spec coverage:**
- §10.2 4종 fixture(빈 JS / 기존 AGENTS.md·번역본 / 기존 settings.json / 비영어) → Task 3.
- §10.2 각 fixture "gate PASS + degrade 후 문서 신설 지시(hollow 아님) + 마커 grep PASS" → Task 3 `_assert_installed_and_reachable`(gate --require-markers + `](_template.md)` 구체 산출물 + has_contract_markers).
- §14 "fixture의 문서 신설 지시 → 구체 기대 산출물 assert" → Task 1 `test_docs_skeleton_not_hollow` + Task 3 구체 링크/파일 assert.
- §7.1 opt-in + 비대화형 dry-run → Task 4(산문 유지). §7.2 settings 병합·§7.3 CLAUDE.md 주입 → scaffold가 M3 함수 재사용(Task 2).
- R4 version stamp → Task 2 `install_loop_files`. D2 settings.json → Task 2·3 assert(`.local` 없음). D8 마커 → 전 fixture assert.
- **의도적 밖:** §9 behavioral parity(재생성 doc-reconcile ↔ 원본 동일 판정) + 기존 훅 보존 첫 실증 + global 제거는 **M4**(second-brain 실제 repo 필요). 설치-현실 테스트(§10.4 실제 `/plugin install`)도 M4. M5 릴리스 게이트는 그 다음.

**Placeholder scan:** `[채움]`·`[프로젝트명]`·`<skill>`·`<plugin>`은 scaffold 산출물/SKILL 산문의 의도된 자리표시(에이전트가 채움 — 기존 SKILL도 사용). `<!-- PLACEHOLDER -->`(how-to/_README)·`<!-- docsherpa-scaffold: v.. -->`는 의도된 산출 마커. `NNNN`·`YYYY-MM-DD`는 ADR 템플릿의 관례적 자리표시. 그 외 TBD/미완 없음.

**Type consistency:**
- `router_skeleton(project_name)->str` · `write_router(repo_root,project_name)->bool` · `write_docs_skeleton(repo_root)->bool` · `install_loop_files(repo_root,plugin_root_dir)->bool` · `plugin_root()->Path` · `scaffold(repo_root,plugin_root_dir=None,project_name)->dict` — Task 1/2 정의, Task 3/4에서 동일 시그니처로 호출. 일치.
- 재사용: `inject_claude_md_file(repo_root)->bool` · `merge_settings_file(claude_dir,command)->bool`(JSONC면 ValueError) — M3 정의, scaffold가 `merge_settings_file(repo_root/.claude, HOOK_CMD)`로 호출(claude_dir 경로 주의 — .claude 하위). 일치.
- 마커 문자열 `ROUTING_MARKER`·`INDEX_MARKER`는 check_markers에서 import(단일 소스) — scaffold/test 전부 동일. 일치.
- `HOOK_CMD` = `cat .claude/doc-drift-prime.txt 2>/dev/null || true` — M3 템플릿·test_merge_settings와 동일. 일치.

**구현자 주의:**
- scaffold `merge_settings_file`는 **`repo_root/.claude`**를 claude_dir로 받는다(M3 시그니처). `.claude` 디렉터리가 없으면 merge_settings_file가 생성하는지 확인 — M3 구현은 `path = Path(claude_dir)/"settings.json"`이고 부모 생성 안 함. **fixture ③ 외엔 `.claude`가 없을 수 있음** → scaffold가 `install_loop_files`에서 `.claude`를 mkdir하지만 순서상 merge_settings가 먼저 호출됨(scaffold dict 순서). **버그 위험**: merge_settings_file가 `.claude` 없으면 write 시 FileNotFoundError. → Task 2 Step 3에서 `scaffold()`가 merge_settings 호출 전에 `(Path(repo_root)/".claude").mkdir(exist_ok=True)`를 보장하거나, merge_settings_file가 부모를 mkdir하도록. **구현 시 이 순서 버그를 반드시 처리**(RED로 잡히면 scaffold에 mkdir 추가).
- Task 4는 산문 편집 — 육안 체크(Step 3)가 필수 게이트.
- Task 3 fixture ④ orphan 위험은 Step 2에서 진단 후 교정.
