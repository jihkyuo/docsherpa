# N11 Plan 3 (Slice B) — Inline→Map Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 인라인 마커(`docsherpa:routing`·`docsherpa:index`)를 진입파일에서 `docs/_map.md`로 **비파괴 이동**하는 결정론 함수 `migrate_inline_to_map`를 만들고, **docsherpa 자신을 그 함수로 spine으로 마이그레이션**한다.

**Architecture:** 구조 고정 결정론 변환 — 임의 MESSY 트리 재편이 아니다. 두 마커 섹션을 마커 기준으로 추출해 `docs/_map.md`로 **verbatim 이동**하고, 이동한 텍스트의 **링크 URL만** `docs/` 기준 상대경로로 재작성한다(링크 텍스트는 보존). `content_oracle.normalize`가 `[text](url)→text`로 URL을 버리므로 URL만 바뀐 세그먼트는 key 불변 → **base 세그먼트 전부 보존 → content_oracle 빈 매니페스트 PASS**(내용 소실 0 기계 증명). URL 재작성 오류는 gate가 broken/orphan으로 시끄럽게 잡는다(조용한 유실 경로 없음).

**Tech Stack:** Python 3 stdlib only(`os.path.relpath`·`re`·`pathlib`), pytest. `contract.py`(Plan 1)의 `is_marker_home`·마커 상수, `content_oracle.py`(기존)의 내용보존 검증, Slice A(Plan 2)의 `_MAP_LINK_SECTION`을 소비.

## Global Constraints

- **stdlib only.** 새 서드파티 의존성 금지.
- **North Star — 내용 소실 0(불가침):** 마이그레이션 후 base(마이그레이션 전) 문서의 모든 세그먼트가 살아남는다. `content_oracle` 미분류 세그먼트 0으로 **기계 증명**. 이게 깨지면 프로젝트 끝장.
- **비파괴:** 링크 **텍스트는 verbatim 보존**(사용자 라벨을 편집하지 않음). URL만 재작성. 다른 섹션(North Star·항시룰·명령어 등)은 byte-보존. `docs/_map.md`가 이미 있으면 **STOP**(안 덮음).
- **정확히 1 home:** 마이그레이션은 `find_marker_home`이 찾은 **인라인 home이 정확히 1개**일 때만 동작(0/다수 → no-op). 마이그레이션 후 home = `docs/_map.md`, `gate.py . --require-markers` PASS.
- **도달성:** 마이그레이션 후 `gate.py .` → broken=0·orphan=0. URL 재작성이 틀리면 여기서 시끄럽게 FAIL.
- **마커 상수 단일 소스:** `contract.py`에서 import(Plan 1).
- **범위 밖(후속):** Slice C(sidecar home 기록·자가치유·커밋강제 훅) · `write_map` 헤딩-aware 가드 강화 · SKILL.md 산문 개정 · 임의 MESSY 트리 재편(기존 에이전트 파이프라인 몫). Plan 3은 **구조 고정 이동 + docsherpa 자가적용**만.
- **저작 함정(F16):** 계획/문서에 링크 문법 `](경로)`를 예시로 쓰면 gate가 실링크로 오인. 마커/링크 예시는 코드블록(펜스) 안에만.

---

## File Structure

- **Modify `skills/setup-docs/scripts/scaffold.py`** — `import os`·`import re` 추가, contract import에 `is_marker_home` 추가; `_rewrite_urls`(링크 URL 재작성 헬퍼)·`_section_span`(마커 기준 섹션 추출)·`migrate_inline_to_map`(마이그레이션 본체) 신설.
- **Modify `skills/setup-docs/scripts/test_scaffold.py`** — `_rewrite_urls` 단위 테스트 + `migrate_inline_to_map` 픽스처 테스트(spine 산출·content_oracle 무손실·엣지).
- **Modify (실제 마이그레이션) `AGENTS.md`** — docsherpa 자신의 인라인 두 섹션을 `docs/_map.md`로 이동, 라우터엔 맵 링크만(Task 3에서 함수로 수행).
- **Create (실제 마이그레이션) `docs/_map.md`** — docsherpa의 이동된 routing·index(Task 3에서 함수로 생성).
- **Modify `docs/plans/README.md`** — 이 계획을 인덱스에 등록(plan 문서 커밋 시).

Task 1(URL 헬퍼)은 순수 함수 독립. Task 2(마이그레이션 본체)는 헬퍼를 조립. Task 3은 함수를 docsherpa에 적용(실제 repo 변경 + 기계 검증).

---

### Task 1: `_rewrite_urls` — 링크 URL 재작성 헬퍼

**Files:**
- Modify: `skills/setup-docs/scripts/scaffold.py`
- Test: `skills/setup-docs/scripts/test_scaffold.py`

**Interfaces:**
- Produces: `scaffold._rewrite_urls(block: str, from_dir, to_dir) -> str` — `block` 안의 마크다운 링크 `](url)`의 URL을, `from_dir` 기준 상대경로를 `to_dir` 기준으로 재계산(텍스트 보존, 외부/앵커 스킵, 디렉터리 trailing slash 보존)

- [ ] **Step 1: 실패하는 테스트 작성**

`skills/setup-docs/scripts/test_scaffold.py` 끝에 추가:

```python
def test_rewrite_urls_strips_docs_prefix_preserving_text(tmp_path):
    out = scaffold._rewrite_urls(
        "- 설계 → [docs/DESIGN.md](docs/DESIGN.md)", tmp_path, tmp_path / "docs")
    assert "](DESIGN.md)" in out          # URL은 docs/ 기준
    assert "[docs/DESIGN.md]" in out       # 텍스트는 보존


def test_rewrite_urls_root_file_gets_dotdot(tmp_path):
    out = scaffold._rewrite_urls(
        "- 상태 → [FINDINGS.md](FINDINGS.md)", tmp_path, tmp_path / "docs")
    assert "](../FINDINGS.md)" in out


def test_rewrite_urls_dir_link_keeps_trailing_slash(tmp_path):
    out = scaffold._rewrite_urls(
        "- 계획 → [docs/plans/](docs/plans/)", tmp_path, tmp_path / "docs")
    assert "](plans/)" in out


def test_rewrite_urls_skips_external_and_anchor(tmp_path):
    out = scaffold._rewrite_urls(
        "[site](https://x.com) and [top](#head)", tmp_path, tmp_path / "docs")
    assert "](https://x.com)" in out and "](#head)" in out
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_scaffold.py -k rewrite_urls -q`
Expected: FAIL — `AttributeError: module 'scaffold' has no attribute '_rewrite_urls'`

- [ ] **Step 3: 최소 구현 작성**

`skills/setup-docs/scripts/scaffold.py` 상단 import에 `os`·`re` 추가(기존 `import json`·`import shutil` 옆):

```python
import json
import os
import re
import shutil
from pathlib import Path
```

`_MAP_LINK_SECTION` 정의 아래(Slice A가 추가한 곳)에 헬퍼 추가:

```python
_URL_RE = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")   # [text](url)


def _rewrite_urls(block, from_dir, to_dir):
    """block 안의 링크 URL을 from_dir 기준 → to_dir 기준 상대경로로. 텍스트·외부·앵커 보존."""
    to_dir = Path(to_dir).resolve()

    def repl(m):
        text, url = m.group(1), m.group(2)
        if url.startswith(("http://", "https://", "mailto:", "tel:", "#")):
            return m.group(0)
        trailing = "/" if url.endswith("/") else ""
        target = (Path(from_dir) / url).resolve()
        new = os.path.relpath(target, to_dir)
        return f"[{text}]({new}{trailing})"

    return _URL_RE.sub(repl, block)
```

- [ ] **Step 4: 테스트가 통과하는지 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_scaffold.py -k rewrite_urls -q`
Expected: PASS (4 passed)

- [ ] **Step 5: 무-회귀 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`
Expected: all passed (순수 추가).

- [ ] **Step 6: 커밋**

```bash
git add skills/setup-docs/scripts/scaffold.py skills/setup-docs/scripts/test_scaffold.py
git commit -m "feat(scaffold): 링크 URL 재작성 헬퍼 _rewrite_urls (N11 P3 T1)"
```

---

### Task 2: `migrate_inline_to_map` — 마이그레이션 본체

**Files:**
- Modify: `skills/setup-docs/scripts/scaffold.py`
- Test: `skills/setup-docs/scripts/test_scaffold.py`

**Interfaces:**
- Consumes: `scaffold._rewrite_urls` (Task 1), `scaffold._MAP_LINK_SECTION` (Slice A), `contract.is_marker_home`·`contract.INDEX_MARKER`·`contract.ROUTING_MARKER`, `content_oracle.collect` (검증)
- Produces: `scaffold._section_span(lines: list[str], marker: str) -> tuple[int,int] | None`, `scaffold.migrate_inline_to_map(repo_root) -> bool`

- [ ] **Step 1: 실패하는 테스트 작성**

`skills/setup-docs/scripts/test_scaffold.py`에 추가(파일 상단에 이미 `import contract`·`import scaffold`·`import gate` 있음):

```python
def _inline_router_repo(root):
    (root / "AGENTS.md").write_text(
        "# R\n> entry\n\n## 항시\n- keep me\n\n"
        f"## 먼저 읽기 {INDEX}\n\n"
        "- 설계 → [docs/DESIGN.md](docs/DESIGN.md)\n"
        "- 상태 → [FINDINGS.md](FINDINGS.md)\n"
        "- 가이드 → [docs/how-to/](docs/how-to/)\n\n"
        f"## 라우팅 {ROUTING}\n\n분류:\n1. 결정 → docs/decisions/\n",
        encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "DESIGN.md").write_text("# design\n", encoding="utf-8")
    (root / "FINDINGS.md").write_text("# findings\n", encoding="utf-8")
    (root / "docs" / "how-to").mkdir()
    (root / "docs" / "how-to" / "_README.md").write_text("# how-to\n", encoding="utf-8")


def test_migrate_inline_to_map_produces_spine(tmp_path):
    _inline_router_repo(tmp_path)
    assert scaffold.migrate_inline_to_map(tmp_path) is True
    router = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert contract.MAP_MARKER in router
    assert contract.INDEX_MARKER not in router
    assert contract.ROUTING_MARKER not in router
    assert "keep me" in router                          # 다른 섹션 보존
    mp = (tmp_path / "docs" / "_map.md").read_text(encoding="utf-8")
    assert contract.is_marker_home(mp) is True           # home = map
    assert "](DESIGN.md)" in mp                            # docs/ 접두어 제거
    assert "](../FINDINGS.md)" in mp                        # 루트 파일 ../
    assert gate.main([str(tmp_path)]) == 0                 # broken=0 orphan=0
    assert gate.main([str(tmp_path), "--require-markers"]) == 0


def test_migrate_no_content_loss_via_oracle(tmp_path):
    import shutil
    import content_oracle
    _inline_router_repo(tmp_path)
    base = tmp_path.parent / "base"
    base.mkdir()
    shutil.copy(tmp_path / "AGENTS.md", base / "AGENTS.md")   # 마이그레이션 전 스냅샷
    assert scaffold.migrate_inline_to_map(tmp_path) is True
    base_keys = set(content_oracle.collect(base))
    cur_keys = set(content_oracle.collect(tmp_path))
    assert base_keys <= cur_keys           # 모든 base 세그먼트 생존(빈 매니페스트)


def test_migrate_noop_when_already_spine(tmp_path):
    scaffold.write_router(tmp_path, "D")
    scaffold.write_map(tmp_path)
    assert scaffold.migrate_inline_to_map(tmp_path) is False   # 인라인 home 없음


def test_migrate_stops_when_map_exists(tmp_path):
    _inline_router_repo(tmp_path)
    (tmp_path / "docs" / "_map.md").write_text("# pre-existing\n", encoding="utf-8")
    assert scaffold.migrate_inline_to_map(tmp_path) is False    # 안 덮음
    assert (tmp_path / "docs" / "_map.md").read_text(encoding="utf-8") == "# pre-existing\n"
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_scaffold.py -k migrate -q`
Expected: FAIL — `AttributeError: module 'scaffold' has no attribute 'migrate_inline_to_map'`

- [ ] **Step 3: 최소 구현 작성**

`skills/setup-docs/scripts/scaffold.py`의 contract import에 `is_marker_home`을 추가:

```python
from contract import ROUTING_MARKER, INDEX_MARKER, MAP_MARKER, is_marker_home
```

`_rewrite_urls`(Task 1) 아래에 추가:

```python
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
```

- [ ] **Step 4: 테스트가 통과하는지 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_scaffold.py -k migrate -q`
Expected: PASS (4 passed)

- [ ] **Step 5: 전체 무-회귀 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`
Expected: all passed.

Run: `python3 skills/setup-docs/scripts/gate.py . && python3 skills/setup-docs/scripts/gate.py . --require-markers`
Expected: 둘 다 PASS(이 레포는 아직 인라인 — Task 3에서 마이그레이션. 함수 추가만으론 무변경).

- [ ] **Step 6: 커밋**

```bash
git add skills/setup-docs/scripts/scaffold.py skills/setup-docs/scripts/test_scaffold.py
git commit -m "feat(scaffold): migrate_inline_to_map 결정론 마이그레이션 (N11 P3 T2)"
```

---

### Task 3: docsherpa 자가 마이그레이션 (dogfood)

**Files:**
- Modify: `AGENTS.md` (함수가 수행 — 인라인 두 섹션 제거, 맵 링크 삽입)
- Create: `docs/_map.md` (함수가 수행 — 이동된 routing·index)

**Interfaces:**
- Consumes: `scaffold.migrate_inline_to_map` (Task 2), `content_oracle.py` (검증), `gate.py` (검증)

- [ ] **Step 1: 마이그레이션 전 base 스냅샷 + 함수 실행**

Run:
```bash
BASE=$(mktemp -d) && cp AGENTS.md "$BASE/AGENTS.md" && echo "BASE=$BASE"
python3 -c "import sys; sys.path.insert(0, 'skills/setup-docs/scripts'); import scaffold; print('changed=', scaffold.migrate_inline_to_map('.'))"
```
Expected: `changed= True` — `AGENTS.md`의 인라인 두 섹션이 `docs/_map.md`로 이동, 라우터엔 `docsherpa:map` 링크만.
(`$BASE` 경로를 Step 2에서 쓴다 — 같은 셸에서 이어 실행하거나 경로를 기록.)

- [ ] **Step 2: 내용 소실 0 기계 증명(content_oracle) — 필수 게이트**

Run: `python3 skills/setup-docs/scripts/content_oracle.py check --base "$BASE" --current .`
Expected: `PASS: base_segments=... unaccounted=0 dropped_no_reason=0 transform_unverified=0`
(마이그레이션 전 AGENTS.md의 모든 세그먼트가 현재 repo에 살아있다 — 빈 매니페스트로 통과. **unaccounted가 0이 아니면 STOP·보고**: 마이그레이션이 내용을 잃었다는 뜻, North Star 위반.)

- [ ] **Step 3: 도달성·마커 게이트**

Run: `python3 skills/setup-docs/scripts/gate.py . && python3 skills/setup-docs/scripts/gate.py . --require-markers`
Expected: 둘 다 `PASS broken=0 orphan=0`. 두 번째는 `markers_ok=True` — home이 이제 `docs/_map.md`(정확히 1). AGENTS.md엔 인라인 마커 없음.

- [ ] **Step 4: 전체 테스트 스위트 green**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`
Expected: all passed.

- [ ] **Step 5: 마이그레이션 결과 육안 확인**

Run: `git diff --stat && echo "---" && cat docs/_map.md`
Expected: `AGENTS.md` 변경 + `docs/_map.md` 신규. `docs/_map.md`에 index·routing 섹션(링크 URL이 `DESIGN.md`·`../FINDINGS.md`·`plans/` 등으로 재작성, 텍스트 보존). `AGENTS.md`엔 North Star·항시룰·명령어 보존 + `## 문서 지도 <!-- docsherpa:map -->` 링크.

- [ ] **Step 6: 이 계획을 인덱스에 등록 확인(plan 커밋 시 이미 등록 — no-op 검증)**

Run: `grep -c "n11-p3-inline-map-migration" docs/plans/README.md`
Expected: `1` (plan 문서 커밋 때 등록됨). 0이면 아래 줄을 `docs/plans/README.md` "재설계 계획"에 추가:

```markdown
- [2026-07-06-n11-p3-inline-map-migration.md](2026-07-06-n11-p3-inline-map-migration.md) — N11 Plan 3(Slice B): 인라인→맵 비파괴 마이그레이션(content_oracle 무손실) + docsherpa 자가적용.
```

- [ ] **Step 7: 커밋**

```bash
git add AGENTS.md docs/_map.md
git commit -m "feat(dogfood): docsherpa 자신을 인라인→맵 spine으로 마이그레이션 (N11 P3 T3)"
```

---

## Self-Review

- **Spec coverage:** 승인 설계 전부 = Task 1(`_rewrite_urls` URL 재작성) + Task 2(`_section_span`+`migrate_inline_to_map` 결정론 이동·엣지) + Task 3(docsherpa 자가적용·content_oracle 무손실 증명). blocker C 정합(URL만 재작성→key 불변) = Task 1·2. CLAUDE.md-only 엣지 커버(`find_marker_home`으로 home 탐색, AGENTS.md 하드코딩 아님) = Task 2. Slice C·write_map 가드·SKILL 산문·임의 MESSY는 명시적 범위 밖.
- **내용 소실 0 보장:** Task 2 `test_migrate_no_content_loss_via_oracle`(base⊆current) + Task 3 Step2(실제 repo content_oracle PASS)가 기계 증명. URL만 재작성해 세그먼트 key 불변 — verbatim 이동.
- **무-회귀:** Task 1·2는 함수 추가만(이 레포 무변경, gate 두 모드 PASS 유지). Task 3에서 비로소 이 레포를 마이그레이션 — content_oracle+gate 두 모드로 무손실·도달성 못박음.
- **타입 일관성:** `_rewrite_urls(block, from_dir, to_dir) -> str`·`_section_span(lines, marker) -> tuple|None`·`migrate_inline_to_map(repo_root) -> bool` 시그니처가 Task 정의·소비에서 일치. `_MAP_LINK_SECTION`(Slice A)·`is_marker_home`(Plan 1)·`content_oracle.collect`(기존) 이름 일치.
- **Placeholder 스캔:** 없음 — 모든 스텝에 실제 코드/명령/기대출력.
