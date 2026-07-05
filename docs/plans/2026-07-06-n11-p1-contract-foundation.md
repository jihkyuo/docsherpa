# N11 Plan 1 — Contract Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 마커·진입파일 계약을 단일 모듈(`contract.py`)로 중앙화하고, gate 루트를 정의된 진입파일 집합으로 일반화하며, 불린 마커 검사를 **구조화된 단일-home locator**(헤딩줄 앵커 + 펜스 제거 + 유일성)로 교체한다. 이것이 N11(맵 중추 문서)의 나머지 전부가 의존하는 토대다.

**Architecture:** 순수 리팩터 — **현재 인라인 동작을 보존**한다(이 레포는 계속 gate PASS). 마커 상수의 단일 소스를 `contract.py`로 옮기고, `check_markers`는 재-export로 하위호환 유지. gate는 하드코딩된 `AGENTS.md`/`CLAUDE.md` 대신 `contract.ENTRY_FILENAMES`에서 루트를 시드하고, `--require-markers`는 "도달 가능한 파일 중 정확히 1개가 두 마커를 헤딩줄에 가진다"로 검사한다.

**Tech Stack:** Python 3 stdlib only, pytest. 새 의존성 0. 스크립트는 `skills/setup-docs/scripts/`에 살고 서로를 모듈명으로 import(같은 디렉터리).

## Global Constraints

- **stdlib only.** 새 서드파티 의존성 금지.
- **무-회귀:** 이 레포(마커가 `AGENTS.md` 헤딩줄에 인라인)는 변경 후에도 `gate.py .` → `PASS broken=0 orphan=0`, `--require-markers`도 PASS. 기존 pytest 스위트 전부 green(변경한 테스트 제외).
- **마커 상수 단일 소스:** `ROUTING_MARKER`·`INDEX_MARKER`는 `contract.py`가 정의, 다른 모듈은 거기서 import. 중복 정의 금지.
- **locator = 헤딩줄 앵커 + 펜스 제거:** 마커가 (펜스 제거 후) ATX 헤딩(`^#{1,6}\s`) 줄에 있을 때만 home으로 센다. 본문·코드블록 속 마커 인용(예: `docs/DESIGN.md`, `docs/decisions/0008-*.md`)은 home 아님.
- **ENTRY_FILENAMES = .md만, README 제외.** `("AGENTS.md", "CLAUDE.md", "GEMINI.md")`. 비-.md 진입(.cursorrules 등)은 미지원(gate가 마크다운 링크를 파싱). README 루팅은 orphan을 가리므로 제외.
- **범위 밖(후속 Plan):** 맵 파일 생성·진입파일 링크 주입·인라인→맵 마이그레이션·sidecar·스킬 산문 개정. Plan 1은 **토대만**.
- **저작 함정(F16):** 계획/문서에 링크 문법 `](경로)`를 예시로 쓰면 인라인 백틱 안이라도 gate가 실링크로 오인한다. 이 계획서 안에서 마커/링크는 코드블록(펜스) 안에만 두거나 서술로 푼다.

---

## File Structure

- **Create `skills/setup-docs/scripts/contract.py`** — 계약의 단일 소스: 마커 상수(`ROUTING_MARKER`·`INDEX_MARKER`·`MAP_MARKER`), `ENTRY_FILENAMES`, `strip_fences`, `is_marker_home`, `find_marker_home`. 순수 함수(파일 IO 없음) — 텍스트를 받는다.
- **Create `skills/setup-docs/scripts/test_contract.py`** — contract 순수 함수 단위 테스트.
- **Modify `skills/setup-docs/scripts/check_markers.py`** — 상수를 `contract`에서 재-export(하위호환). `has_contract_markers`는 유지(기존 테스트가 씀).
- **Modify `skills/setup-docs/scripts/gate.py`** — 루트를 `contract.ENTRY_FILENAMES`로 일반화(:77); `--require-markers`를 `contract.find_marker_home`(정확히 1) 기반으로 교체(:117-123, 138).
- **Modify `skills/setup-docs/scripts/test_gate_markers.py`** — 새 계약(다중 진입 루트·헤딩 앵커·유일성)에 맞게 갱신.
- **Modify `docs/plans/README.md`** — 이 계획을 인덱스에 등록(orphan 방지).

각 태스크는 독립 테스트 사이클을 갖고, 리뷰어가 개별 승인/거부할 수 있는 단위다.

---

### Task 1: `contract.py` — 계약 단일 소스 + 구조화 locator

**Files:**
- Create: `skills/setup-docs/scripts/contract.py`
- Test: `skills/setup-docs/scripts/test_contract.py`

**Interfaces:**
- Produces:
  - `ROUTING_MARKER: str` = `"<!-- docsherpa:routing -->"`, `INDEX_MARKER: str` = `"<!-- docsherpa:index -->"`, `MAP_MARKER: str` = `"<!-- docsherpa:map -->"`
  - `ENTRY_FILENAMES: tuple[str, ...]` = `("AGENTS.md", "CLAUDE.md", "GEMINI.md")`
  - `strip_fences(text: str) -> str`
  - `is_marker_home(text: str) -> bool` — 두 계약 마커가 모두 (펜스 제거 후) ATX 헤딩 줄에 있으면 True
  - `find_marker_home(files: list[tuple[Path, str]]) -> list[Path]` — home인 파일들의 Path 리스트(0/1/다수 판정은 호출부)

- [ ] **Step 1: 실패하는 테스트 작성**

`skills/setup-docs/scripts/test_contract.py`:

```python
from pathlib import Path

import contract


def test_markers_are_html_comments():
    assert contract.ROUTING_MARKER == "<!-- docsherpa:routing -->"
    assert contract.INDEX_MARKER == "<!-- docsherpa:index -->"
    assert contract.MAP_MARKER == "<!-- docsherpa:map -->"


def test_entry_filenames_md_only_no_readme():
    assert contract.ENTRY_FILENAMES == ("AGENTS.md", "CLAUDE.md", "GEMINI.md")
    assert all(n.endswith(".md") for n in contract.ENTRY_FILENAMES)
    assert "README.md" not in contract.ENTRY_FILENAMES


def test_home_when_markers_on_heading_lines():
    text = (
        "# 라우터\n"
        "## 먼저 읽기 <!-- docsherpa:index -->\n- [a](docs/a.md)\n\n"
        "## 라우팅 룰 <!-- docsherpa:routing -->\n1. 결정 → decisions/\n"
    )
    assert contract.is_marker_home(text) is True


def test_not_home_when_markers_only_in_prose():
    # 마커를 '설명'하는 문서(본문 인용)는 home 아님 — false-home 방지.
    text = (
        "# 설계\n\n"
        "마커 <!-- docsherpa:routing -->·<!-- docsherpa:index -->를 헤딩에 붙인다.\n"
    )
    assert contract.is_marker_home(text) is False


def test_not_home_when_markers_inside_code_fence():
    # 템플릿 예시(펜스 안)는 home 아님.
    text = (
        "# 스킬\n\n"
        "```markdown\n"
        "## 인덱스 <!-- docsherpa:index -->\n"
        "## 라우팅 <!-- docsherpa:routing -->\n"
        "```\n"
    )
    assert contract.is_marker_home(text) is False


def test_find_marker_home_picks_only_the_home():
    home = "# r\n## i <!-- docsherpa:index -->\n## g <!-- docsherpa:routing -->\n"
    prose = "# d\n본문에 <!-- docsherpa:index --> <!-- docsherpa:routing --> 인용.\n"
    files = [(Path("AGENTS.md"), home), (Path("docs/DESIGN.md"), prose)]
    assert contract.find_marker_home(files) == [Path("AGENTS.md")]


def test_find_marker_home_reports_multiple():
    a = "# a\n## i <!-- docsherpa:index -->\n## g <!-- docsherpa:routing -->\n"
    b = "# b\n## i <!-- docsherpa:index -->\n## g <!-- docsherpa:routing -->\n"
    files = [(Path("AGENTS.md"), a), (Path("docs/_map.md"), b)]
    assert contract.find_marker_home(files) == [Path("AGENTS.md"), Path("docs/_map.md")]
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_contract.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'contract'`

- [ ] **Step 3: 최소 구현 작성**

`skills/setup-docs/scripts/contract.py`:

```python
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
```

- [ ] **Step 4: 테스트가 통과하는지 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_contract.py -q`
Expected: PASS (7 passed)

- [ ] **Step 5: 커밋**

```bash
git add skills/setup-docs/scripts/contract.py skills/setup-docs/scripts/test_contract.py
git commit -m "feat(contract): 마커·진입파일 계약 단일 소스 + 헤딩앵커 locator (N11 P1 T1)"
```

---

### Task 2: `check_markers.py` — 상수를 contract에서 재-export

**Files:**
- Modify: `skills/setup-docs/scripts/check_markers.py`

**Interfaces:**
- Consumes: `contract.ROUTING_MARKER`, `contract.INDEX_MARKER` (Task 1)
- Produces: `check_markers.ROUTING_MARKER`·`check_markers.INDEX_MARKER`(재-export, `scaffold.py`가 계속 씀), `check_markers.has_contract_markers(text) -> bool`(유지)

- [ ] **Step 1: 재-export로 교체**

`skills/setup-docs/scripts/check_markers.py` — 상수 두 줄을 contract import로 교체(정의 중복 제거). `has_contract_markers`는 그대로 둔다:

```python
"""언어-불문 섹션 계약 검증 — doc-reconcile이 의존하는 마커가 있는지.

spec D8: 헤딩 문자열이 아니라 HTML 마커를 계약으로 삼는다.
마커 상수의 정본은 contract.py — 여기선 하위호환 재-export.
"""
from contract import ROUTING_MARKER, INDEX_MARKER


def has_contract_markers(agents_md_text: str) -> bool:
    return ROUTING_MARKER in agents_md_text and INDEX_MARKER in agents_md_text
```

- [ ] **Step 2: 기존 마커 테스트가 여전히 통과하는지 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_check_markers.py -q`
Expected: PASS (변경 전과 동일 — 상수 값이 같으므로)

- [ ] **Step 3: 커밋**

```bash
git add skills/setup-docs/scripts/check_markers.py
git commit -m "refactor(check_markers): 마커 상수를 contract에서 재-export (N11 P1 T2)"
```

---

### Task 3: `gate.py` — 루트를 ENTRY_FILENAMES로 일반화 (blocker D)

**Files:**
- Modify: `skills/setup-docs/scripts/gate.py:77`
- Test: `skills/setup-docs/scripts/test_gate_markers.py`

**Interfaces:**
- Consumes: `contract.ENTRY_FILENAMES` (Task 1)
- Produces: gate가 존재하는 모든 진입파일(AGENTS/CLAUDE/GEMINI)에서 BFS 시드

- [ ] **Step 1: 실패하는 테스트 작성 — GEMINI-only repo가 도달성 통과**

`skills/setup-docs/scripts/test_gate_markers.py`에 추가:

```python
def test_gemini_only_repo_seeds_gate(tmp_path):
    # AGENTS/CLAUDE 없이 GEMINI.md만 있어도 gate가 그것을 루트로 삼아
    # 링크된 문서에 도달한다(F10 봉쇄).
    (tmp_path / "GEMINI.md").write_text(
        "# g\n- [스펙](docs/spec.md)\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "spec.md").write_text("# spec\n", encoding="utf-8")
    import gate
    rc = gate.main([str(tmp_path)])
    assert rc == 0  # broken=0 orphan=0 — GEMINI.md에서 도달
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_gate_markers.py::test_gemini_only_repo_seeds_gate -q`
Expected: FAIL — `assert 1 == 0` (gate가 GEMINI.md를 루트로 안 삼아 `진입 라우터 없음` FAIL)

- [ ] **Step 3: gate 루트 일반화**

`skills/setup-docs/scripts/gate.py` — `import check_markers` 옆에 `import contract` 추가하고, 루트 시드 줄(:77)을 교체:

```python
# 변경 전:
#   roots = [p for p in (root / "AGENTS.md", root / "CLAUDE.md") if p.is_file()]
# 변경 후:
    roots = [root / name for name in contract.ENTRY_FILENAMES
             if (root / name).is_file()]
```

`:79`의 에러 메시지도 일반화:

```python
    if not roots:
        names = " / ".join(contract.ENTRY_FILENAMES)
        print(f"FAIL: 진입 라우터 없음 — {root}에 {names} 중 하나가 필요하다.")
        return 1
```

- [ ] **Step 4: 테스트가 통과하는지 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_gate_markers.py -q`
Expected: PASS (신규 + 기존 마커 테스트 전부)

- [ ] **Step 5: 이 레포 무-회귀 확인**

Run: `python3 skills/setup-docs/scripts/gate.py .`
Expected: `PASS: broken=0 orphan=0 ...` (AGENTS.md+CLAUDE.md 존재 → 루트 동일, 회귀 없음)

- [ ] **Step 6: 커밋**

```bash
git add skills/setup-docs/scripts/gate.py skills/setup-docs/scripts/test_gate_markers.py
git commit -m "feat(gate): 루트를 ENTRY_FILENAMES로 일반화 — GEMINI 등 진입파일 시드 (N11 P1 T3, F10)"
```

---

### Task 4: `gate.py --require-markers` — 단일-home locator 기반 (blocker B)

**Files:**
- Modify: `skills/setup-docs/scripts/gate.py:117-123, 138`
- Test: `skills/setup-docs/scripts/test_gate_markers.py`

**Interfaces:**
- Consumes: `contract.find_marker_home` (Task 1), gate의 `visited` 집합(도달한 .md의 resolved Path)
- Produces: `--require-markers` = "도달 가능한 파일 중 **정확히 1개**가 두 마커를 헤딩줄에 가진다". 0개 또는 다수 → FAIL

- [ ] **Step 1: 실패하는 테스트 3개 — 정확히-1 / false-home / 다수**

`skills/setup-docs/scripts/test_gate_markers.py`에 추가:

```python
def _write_home(p):
    p.write_text(
        "# r\n## 인덱스 <!-- docsherpa:index -->\n- [a](docs/a.md)\n\n"
        "## 라우팅 <!-- docsherpa:routing -->\n1. 결정 → decisions/\n",
        encoding="utf-8")


def test_require_markers_passes_with_single_home(tmp_path):
    _write_home(tmp_path / "AGENTS.md")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# a\n", encoding="utf-8")
    import gate
    assert gate.main([str(tmp_path), "--require-markers"]) == 0


def test_require_markers_ignores_prose_quote_of_markers(tmp_path):
    # 마커를 본문에서 인용하는 문서는 home으로 세지 않는다(false-home 방지).
    _write_home(tmp_path / "AGENTS.md")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text(
        "# a\n마커 <!-- docsherpa:index --> <!-- docsherpa:routing --> 설명.\n",
        encoding="utf-8")
    import gate
    assert gate.main([str(tmp_path), "--require-markers"]) == 0  # home은 여전히 1개


def test_require_markers_fails_on_two_homes(tmp_path):
    _write_home(tmp_path / "AGENTS.md")
    (tmp_path / "docs").mkdir()
    _write_home(tmp_path / "docs" / "a.md")  # 두 번째 home(헤딩줄 마커)
    import gate
    assert gate.main([str(tmp_path), "--require-markers"]) == 1  # 다수 → FAIL
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_gate_markers.py -k require_markers -q`
Expected: `test_require_markers_fails_on_two_homes` FAIL — 현재 `--require-markers`는 `AGENTS.md`만 보고 다수를 못 잡아 PASS(0) 반환

- [ ] **Step 3: locator 기반으로 교체**

`skills/setup-docs/scripts/gate.py`의 `--require-markers` 블록(:117-123)을 교체. `visited`(도달한 .md의 resolved Path 집합)를 읽어 home을 센다:

```python
    markers_ok = True
    marker_msg = ""
    if require_markers:
        scanned = []
        for p in visited:
            try:
                scanned.append((p, p.read_text(encoding="utf-8", errors="ignore")))
            except OSError:
                pass
        homes = contract.find_marker_home(scanned)
        markers_ok = len(homes) == 1
        if len(homes) == 0:
            marker_msg = ("마커 home 없음: 도달 가능한 문서 중 "
                          f"{contract.ROUTING_MARKER}·{contract.INDEX_MARKER}를 "
                          "헤딩줄에 함께 가진 파일이 필요하다.")
        elif len(homes) > 1:
            rels = ", ".join(str(h.relative_to(root)) for h in homes)
            marker_msg = f"마커 home 중복(정확히 1개여야): {rels}"
```

그리고 `--require-markers` 실패 출력(:137-138)을 교체:

```python
    if require_markers and not markers_ok:
        print("\n" + marker_msg)
```

- [ ] **Step 4: 테스트가 통과하는지 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_gate_markers.py -q`
Expected: PASS (신규 3 + 기존 전부)

- [ ] **Step 5: 이 레포 무-회귀 확인 (인라인 home 1개)**

Run: `python3 skills/setup-docs/scripts/gate.py . --require-markers`
Expected: `PASS ... markers_ok=True` — `AGENTS.md`가 유일 home, `docs/DESIGN.md` 등의 본문 인용은 헤딩앵커로 제외

- [ ] **Step 6: 커밋**

```bash
git add skills/setup-docs/scripts/gate.py skills/setup-docs/scripts/test_gate_markers.py
git commit -m "feat(gate): --require-markers를 단일-home locator로 교체 — false-home 배제 (N11 P1 T4, B)"
```

---

### Task 5: 전체 회귀 + 계획 인덱스 등록

**Files:**
- Modify: `docs/plans/README.md`

**Interfaces:**
- Consumes: Task 1~4 전체

- [ ] **Step 1: 전체 pytest 스위트 green 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`
Expected: all passed (신규 test_contract.py + 갱신 test_gate_markers.py 포함, 기존 무-회귀)

- [ ] **Step 2: 이 레포 gate 두 모드 PASS 확인**

Run: `python3 skills/setup-docs/scripts/gate.py . && python3 skills/setup-docs/scripts/gate.py . --require-markers`
Expected: 둘 다 `PASS broken=0 orphan=0` (두 번째는 `markers_ok=True`)

- [ ] **Step 3: 이 계획을 인덱스에 등록(orphan 방지)**

`docs/plans/README.md`의 "재설계 계획" 섹션에 한 줄 추가:

```markdown
- [2026-07-06-n11-p1-contract-foundation.md](2026-07-06-n11-p1-contract-foundation.md) — N11 Plan 1: 계약 단일 소스 + gate 루트 일반화 + 단일-home locator(토대).
```

- [ ] **Step 4: gate로 등록 확인(broken=0 orphan=0)**

Run: `python3 skills/setup-docs/scripts/gate.py .`
Expected: `PASS: broken=0 orphan=0` — 이 계획이 인덱스에서 도달 가능

- [ ] **Step 5: 커밋**

```bash
git add docs/plans/README.md
git commit -m "docs(plan): N11 P1 계약 토대 계획 인덱스 등록 (N11 P1 T5)"
```

---

## Self-Review

- **Spec coverage:** blocker B(구조화 locator·false-home 배제) = Task 1·4. blocker D(gate 루트 일반화) = Task 3. contract 모듈 먼저(§3.8 전제) = Task 1. 마커 단일 소스 = Task 2. 후속 Plan(맵 생성·마이그레이션·sidecar·산문)은 명시적으로 범위 밖.
- **무-회귀 보장:** Task 3 Step5·Task 4 Step5·Task 5 Step2가 이 레포 gate 두 모드 PASS를 못박음. 마커가 `AGENTS.md` 헤딩줄에 있어 단일 home으로 잡히고, `docs/DESIGN.md`·`0008` 본문 인용은 헤딩앵커로 배제.
- **타입 일관성:** `find_marker_home(files: list[(Path, text)]) -> list[Path]`가 Task 1 정의·Task 4 소비에서 일치. `ENTRY_FILENAMES`·마커 상수 이름 일치.
- **Placeholder 스캔:** 없음 — 모든 스텝에 실제 코드/명령/기대출력.
