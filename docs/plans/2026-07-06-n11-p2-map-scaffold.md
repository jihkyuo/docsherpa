# N11 Plan 2 (Slice A) — Map Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** scaffold가 **새(greenfield) repo**를 spine 형태로 만든다 — 마커(routing·index)를 진입파일 인라인 대신 **`docs/_map.md`(중립명)** 에 두고, 진입파일엔 맵으로 가는 **링크 한 줄 + `docsherpa:map` 마커**만 남긴다.

**Architecture:** 순수 그린필드 계약 전환. `scaffold.py`가 지금까지 AGENTS.md에 인라인으로 심던 index·routing 섹션을 새 맵 문서(`docs/_map.md`)로 옮기고, 라우터엔 맵 링크만 둔다. 내용 **이동**이 아니라 그린필드 **신규 생성**이라 content_oracle 불요. gate 코드는 무변경 — Plan 1의 locator가 visited 전체를 스캔해 home(맵)을 찾고, BFS가 링크로 맵에 도달한다. docsherpa 자신의 기존 인라인 마커는 **건드리지 않는다**(그건 Slice B 마이그레이션).

**Tech Stack:** Python 3 stdlib only, pytest. 새 의존성 0. `contract.py`(Plan 1)의 `MAP_MARKER`·`is_marker_home`를 소비한다.

## Global Constraints

- **stdlib only.** 새 서드파티 의존성 금지.
- **무-회귀(이 레포):** docsherpa는 마커가 `AGENTS.md` 헤딩줄에 **인라인**인 채로 남는다(Slice A는 템플릿/scaffold만 바꿈, 이 레포의 AGENTS.md는 안 건드림). 따라서 변경 후에도 `gate.py .` → PASS, `gate.py . --require-markers` → PASS(`markers_ok=True`, home=AGENTS.md 유지). 기존 pytest 스위트 전부 green(계약 전환에 맞춰 갱신한 테스트 제외).
- **정확히 1 home 불변식:** scaffold 후 도달 가능한 문서 중 마커 home은 **정확히 1개**. 그린필드/무마커 라우터 → home=`docs/_map.md`. 기존 인라인-마커 라우터(구식 healthy) → scaffold no-op, home=AGENTS.md 유지(두 home 금지). 이 조율은 `write_map`이 라우터의 `docsherpa:map` 마커 유무로 자가 가드한다.
- **append-only·기존 보존:** `write_map`은 `docs/_map.md`가 없을 때만 생성. `write_router`는 기존 라우터 내용 전부 보존(빠진 것만 append).
- **상대경로:** 맵은 `docs/` 안에 사므로 인덱스 링크는 `docs/` 접두어 없이(`decisions/README.md`·`how-to/`). gate가 링크를 담은 파일 기준으로 해석한다.
- **마커 상수 단일 소스:** `MAP_MARKER`·`ROUTING_MARKER`·`INDEX_MARKER`는 `contract.py`에서 import(Plan 1).
- **범위 밖(후속 Plan):** 인라인→맵 마이그레이션(Slice B)·sidecar home 기록·자가치유(Slice C)·커밋시점 강제 훅. Plan 2는 **그린필드 맵 생성만**.
- **저작 함정(F16):** 계획/문서에 링크 문법 `](경로)`를 예시로 쓰면 인라인 백틱 안이라도 gate가 실링크로 오인한다. 마커/링크 예시는 코드블록(펜스) 안에만 둔다.

---

## File Structure

- **Modify `skills/setup-docs/scripts/scaffold.py`** — `MAP_MARKER` import 추가; 맵 문서 템플릿(`_MAP_DOC`)·진입측 맵 링크 섹션(`_MAP_LINK_SECTION`) 신설; `router_skeleton`이 인라인 index·routing 대신 맵 링크를 담게 교체; `write_map()` 신설(자가 가드); `write_router` 존재-라우터 경로를 맵 링크 append로 교체; `scaffold()`에 `write_map` 배선.
- **Modify `skills/setup-docs/scripts/test_scaffold.py`** — 그린필드 spine 테스트 신설 + 마커를 AGENTS.md 대신 맵에서 검사하도록 갱신 + 존재-라우터/멱등 테스트 갱신.
- **Modify `skills/setup-docs/scripts/test_fixtures_portability.py`** — `has_contract_markers`를 AGENTS.md 대신 `docs/_map.md`에서 검사.
- **Modify `docs/plans/README.md`** — 이 계획을 인덱스에 등록(orphan 방지).

각 태스크는 독립 테스트 사이클을 갖는다. Task 1(맵 문서)은 기존 동작 무변경 순수 추가라 독립 green. Task 2가 그린필드 계약을 전환한다(상호의존 라우터+맵+테스트 갱신을 한 커밋에 — 중간 red 상태를 만들지 않기 위해 불가분).

---

### Task 1: 맵 문서 — `_MAP_DOC` 템플릿 + `write_map()`

**Files:**
- Modify: `skills/setup-docs/scripts/scaffold.py`
- Test: `skills/setup-docs/scripts/test_scaffold.py`

**Interfaces:**
- Consumes: `contract.MAP_MARKER`·`contract.ROUTING_MARKER`·`contract.INDEX_MARKER` (Plan 1), `contract.is_marker_home` (검증용)
- Produces: `scaffold._MAP_DOC: str`(맵 문서 텍스트, 두 마커가 `##` 헤딩줄에), `scaffold.write_map(repo_root) -> bool`

- [ ] **Step 1: 실패하는 테스트 작성**

`skills/setup-docs/scripts/test_scaffold.py` 상단 import에 `contract`를 추가하고(이미 `import scaffold` 있음), 파일 끝에 추가:

```python
import contract


def test_write_map_creates_map_with_markers_on_headings(tmp_path):
    # 라우터가 맵을 가리킬 때만 맵을 만든다 — 진입파일에 map 마커 선재.
    (tmp_path / "AGENTS.md").write_text(
        f"# R\n## 문서 지도 {contract.MAP_MARKER}\n- → [문서 지도](docs/_map.md)\n",
        encoding="utf-8")
    changed = scaffold.write_map(tmp_path)
    assert changed is True
    text = (tmp_path / "docs" / "_map.md").read_text(encoding="utf-8")
    assert contract.is_marker_home(text) is True          # 두 마커가 헤딩줄에


def test_write_map_idempotent(tmp_path):
    (tmp_path / "AGENTS.md").write_text(
        f"# R\n{contract.MAP_MARKER}\n", encoding="utf-8")
    assert scaffold.write_map(tmp_path) is True
    assert scaffold.write_map(tmp_path) is False          # 이미 있으면 no-op


def test_write_map_noop_when_router_does_not_point_to_map(tmp_path):
    # 라우터가 맵을 안 가리키면(인라인 healthy or map 마커 부재) 맵을 만들지 않는다 — 두 home 방지.
    (tmp_path / "AGENTS.md").write_text("# R\n## 인라인\nno map marker\n", encoding="utf-8")
    assert scaffold.write_map(tmp_path) is False
    assert not (tmp_path / "docs" / "_map.md").exists()
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_scaffold.py -k write_map -q`
Expected: FAIL — `AttributeError: module 'scaffold' has no attribute 'write_map'`

- [ ] **Step 3: 최소 구현 작성**

`skills/setup-docs/scripts/scaffold.py`의 import 줄을 교체(마커 정본 contract에서, `MAP_MARKER` 추가):

```python
# 변경 전:
#   from check_markers import ROUTING_MARKER, INDEX_MARKER
# 변경 후:
from contract import ROUTING_MARKER, INDEX_MARKER, MAP_MARKER
```

`_ROUTING_SECTION` 정의 아래(약 :34)에 맵 문서 템플릿을 추가. 맵은 `docs/` 안에 사므로 인덱스 링크는 `docs/` 접두어 없이:

```python
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
```

`write_docs_skeleton` 정의 위(약 :67)에 `write_map`을 추가:

```python
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
```

- [ ] **Step 4: 테스트가 통과하는지 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_scaffold.py -k write_map -q`
Expected: PASS (3 passed)

- [ ] **Step 5: 무-회귀 확인(기존 동작 무변경)**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`
Expected: all passed — Task 1은 순수 추가라 기존 테스트 무영향. (import를 check_markers→contract로 바꿨지만 값 동일.)

Run: `python3 skills/setup-docs/scripts/gate.py . && python3 skills/setup-docs/scripts/gate.py . --require-markers`
Expected: 둘 다 PASS(이 레포 무변경).

- [ ] **Step 6: 커밋**

```bash
git add skills/setup-docs/scripts/scaffold.py skills/setup-docs/scripts/test_scaffold.py
git commit -m "feat(scaffold): 맵 문서 템플릿 + write_map (N11 P2 T1)"
```

---

### Task 2: 진입 라우터 → 맵 링크 전환 (그린필드 계약)

**Files:**
- Modify: `skills/setup-docs/scripts/scaffold.py`
- Test: `skills/setup-docs/scripts/test_scaffold.py`, `skills/setup-docs/scripts/test_fixtures_portability.py`

**Interfaces:**
- Consumes: `scaffold.write_map` (Task 1), `contract.MAP_MARKER`·`ROUTING_MARKER`·`INDEX_MARKER`
- Produces: 인라인 index·routing이 사라진 `router_skeleton`(맵 링크만), 맵 링크를 append하는 `write_router`, `write_map`을 배선한 `scaffold()`

- [ ] **Step 1: 실패하는 테스트 작성 — 그린필드 spine**

`skills/setup-docs/scripts/test_scaffold.py` 끝에 추가:

```python
def test_greenfield_scaffold_is_spine(tmp_path):
    # 진입파일엔 map 마커·링크만(인라인 routing/index 0), 맵이 home, gate 두 모드 PASS.
    scaffold.write_router(tmp_path, "Demo")
    scaffold.write_map(tmp_path)
    scaffold.write_docs_skeleton(tmp_path)
    router = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert contract.MAP_MARKER in router                      # 맵 링크 마커
    assert contract.ROUTING_MARKER not in router              # 인라인 아님
    assert contract.INDEX_MARKER not in router                # 인라인 아님
    assert gate.main([str(tmp_path)]) == 0                     # broken=0 orphan=0
    assert gate.main([str(tmp_path), "--require-markers"]) == 0  # home=맵, 정확히 1
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_scaffold.py::test_greenfield_scaffold_is_spine -q`
Expected: FAIL — 현재 `router_skeleton`이 인라인 마커를 심어 `ROUTING_MARKER not in router` assert가 깨진다.

- [ ] **Step 3: `router_skeleton`·`write_router` 교체 + `scaffold()` 배선**

`skills/setup-docs/scripts/scaffold.py`의 `_MAP_DOC` 아래에 진입측 맵 링크 섹션을 추가:

```python
# 진입 라우터가 맵으로 가는 링크 한 줄 + docsherpa:map 마커(도구가 링크 줄을 찾/보호).
_MAP_LINK_SECTION = f"""## 문서 지도 {MAP_MARKER}
- 라우팅·인덱스 → [문서 지도](docs/_map.md)
"""
```

`router_skeleton`을 교체(인라인 index·routing → 맵 링크):

```python
def router_skeleton(project_name: str) -> str:
    """마커는 docs/_map.md에 산다 — 라우터엔 맵 링크 한 줄만(N11 spine)."""
    return (
        f"# {project_name} 에이전트 가이드\n"
        "> 진입 라우터. 상세는 docs/를 필요할 때만 읽는다.\n\n"
        "## 항시 룰\n- 패키지/언어/배포: [채움]\n\n"
        "## 명령어\n- [채움: build/test/dev/lint]\n\n"
        + _MAP_LINK_SECTION
    )
```

`write_router`를 교체(존재-라우터 경로 = 맵 링크 append, 인라인/맵 이미 있으면 no-op):

```python
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
```

`scaffold()`의 반환 dict에 `write_map` 배선(`router` 다음 줄):

```python
        "router": write_router(repo_root, project_name),
        "map": write_map(repo_root),
        "docs": write_docs_skeleton(repo_root),
```

이제 인라인 `_INDEX_SECTION`·`_ROUTING_SECTION`은 어디서도 안 쓰인다 — 두 상수 정의(약 :18-33)를 삭제한다(내 변경이 만든 고아 제거).

- [ ] **Step 4: 그린필드 테스트 통과 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_scaffold.py::test_greenfield_scaffold_is_spine -q`
Expected: PASS

- [ ] **Step 5: 계약 전환으로 깨진 기존 테스트 갱신**

`test_scaffold.py`에서 인라인 마커를 AGENTS.md에서 검사하던 테스트 3개를 새 계약에 맞게 교체.

`test_greenfield_router_and_docs_pass_marker_gate`(약 :10-16) — 마커를 맵에서 검사:

```python
def test_greenfield_router_and_docs_pass_marker_gate(tmp_path):
    scaffold.write_router(tmp_path, "Demo")
    scaffold.write_map(tmp_path)
    scaffold.write_docs_skeleton(tmp_path)
    # 마커 계약 + 도달성(broken=0·orphan=0) 동시 통과
    assert gate.main([str(tmp_path), "--require-markers"]) == 0
    mp = (tmp_path / "docs" / "_map.md").read_text(encoding="utf-8")
    assert ROUTING in mp and INDEX in mp                  # 마커는 맵에 산다
    router = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert contract.MAP_MARKER in router                  # 라우터엔 맵 링크만
```

`test_existing_router_markers_appended_preserving_content`(약 :28-37) — 맵 링크 주입 + 맵에 마커:

```python
def test_existing_router_markers_appended_preserving_content(tmp_path):
    # 마커 없는 번역본 라우터 + 사용자 커스텀 룰
    (tmp_path / "AGENTS.md").write_text(
        "# Guide\n## Always Rules\n- custom project rule XYZ\n", encoding="utf-8"
    )
    changed = scaffold.write_router(tmp_path, "Demo")
    scaffold.write_map(tmp_path)
    out = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert changed is True
    assert "custom project rule XYZ" in out               # 기존 보존
    assert contract.MAP_MARKER in out                     # 맵 링크 주입됨
    mp = (tmp_path / "docs" / "_map.md").read_text(encoding="utf-8")
    assert ROUTING in mp and INDEX in mp                  # 마커는 맵에
```

`test_write_router_appends_only_missing_marker_section`(약 :96-102) — 인라인 섹션 append 로직이 사라졌으므로 **인라인-마커 라우터는 no-op(두 home 방지)** 테스트로 교체:

```python
def test_write_router_noop_on_existing_inline_markers(tmp_path):
    # 구식 인라인 마커 라우터 → 맵 링크를 append하지 않는다(안 그러면 두 home). Slice B 몫.
    (tmp_path / "AGENTS.md").write_text(
        f"# G\n## Idx {INDEX}\n- a\n## Rules {ROUTING}\nr\n", encoding="utf-8")
    changed = scaffold.write_router(tmp_path, "Demo")
    assert changed is False                               # no-op
    assert scaffold.write_map(tmp_path) is False          # 맵도 안 만듦
    assert not (tmp_path / "docs" / "_map.md").exists()
```

- [ ] **Step 6: 픽스처 이식성 테스트 갱신**

`test_fixtures_portability.py`의 `_assert_installed_and_reachable`(약 :12)에서 마커 검사를 맵으로 이동:

```python
# 변경 전:
#   assert has_contract_markers((repo / "AGENTS.md").read_text(encoding="utf-8"))
# 변경 후:
    assert has_contract_markers((repo / "docs/_map.md").read_text(encoding="utf-8"))
```

- [ ] **Step 7: 전체 스위트 통과 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`
Expected: all passed (그린필드 spine 신규 + 갱신 테스트 + 나머지 무-회귀).

- [ ] **Step 8: 이 레포 무-회귀 확인(docsherpa는 인라인 유지)**

Run: `python3 skills/setup-docs/scripts/gate.py . && python3 skills/setup-docs/scripts/gate.py . --require-markers`
Expected: 둘 다 PASS(`markers_ok=True`). 이 레포 AGENTS.md는 인라인 마커 유지 — Slice A는 이 파일을 안 건드린다.

- [ ] **Step 9: 커밋**

```bash
git add skills/setup-docs/scripts/scaffold.py skills/setup-docs/scripts/test_scaffold.py skills/setup-docs/scripts/test_fixtures_portability.py
git commit -m "feat(scaffold): 그린필드 라우터를 맵 링크로 전환 — spine (N11 P2 T2)"
```

---

### Task 3: 계획 인덱스 등록 + 전체 회귀

**Files:**
- Modify: `docs/plans/README.md`

**Interfaces:**
- Consumes: Task 1~2 전체

- [ ] **Step 1: 전체 pytest 스위트 green 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`
Expected: all passed.

- [ ] **Step 2: 이 레포 gate 두 모드 PASS 확인**

Run: `python3 skills/setup-docs/scripts/gate.py . && python3 skills/setup-docs/scripts/gate.py . --require-markers`
Expected: 둘 다 `PASS broken=0 orphan=0`(두 번째는 `markers_ok=True`, home=AGENTS.md 인라인 유지).

- [ ] **Step 3: 이 계획을 인덱스에 등록(orphan 방지)**

`docs/plans/README.md`의 "재설계 계획" 섹션에 한 줄 추가:

```markdown
- [2026-07-06-n11-p2-map-scaffold.md](2026-07-06-n11-p2-map-scaffold.md) — N11 Plan 2(Slice A): 그린필드 맵 생성 + 진입파일 맵 링크(spine 계약, 마이그레이션은 후속).
```

- [ ] **Step 4: gate로 등록 확인(broken=0 orphan=0)**

Run: `python3 skills/setup-docs/scripts/gate.py .`
Expected: `PASS: broken=0 orphan=0` — 이 계획이 인덱스에서 도달 가능.

- [ ] **Step 5: 커밋**

```bash
git add docs/plans/README.md
git commit -m "docs(plan): N11 P2 맵 스캐폴드 계획 인덱스 등록 (N11 P2 T3)"
```

---

## Self-Review

- **Spec coverage:** Slice A 승인 설계 전부 = Task 1(맵 문서 템플릿·`write_map` 자가가드) + Task 2(라우터 맵 링크 전환·`scaffold` 배선·테스트 갱신). blocker C 선행 정합(맵 인덱스 링크=사람-라벨 텍스트) = Task 1 `_MAP_DOC`. 인라인→맵 마이그레이션(B)·sidecar/자가치유(C)·커밋강제는 명시적 범위 밖.
- **정확히-1-home 불변식:** `write_map`이 라우터 `docsherpa:map` 유무로 가드 → 그린필드/무마커=home 맵(1), 인라인 healthy=no-op(home AGENTS.md 유지, 1). `test_write_router_noop_on_existing_inline_markers`가 두-home 회귀를 못박음.
- **무-회귀 보장:** Task 1 Step5·Task 2 Step8·Task 3 Step2가 이 레포 gate 두 모드 PASS를 못박음(docsherpa AGENTS.md 인라인 유지, Slice A 무접촉). 계약 전환에 깨지는 테스트는 Task 2 Step5-6에서 같은 커밋에 갱신 — 중간 red 없음.
- **타입 일관성:** `write_map(repo_root) -> bool`·`write_router(repo_root, project_name) -> bool` 시그니처가 Task 1·2에서 일치. `_MAP_DOC`·`_MAP_LINK_SECTION`·`MAP_MARKER` 이름 일치. 고아 제거(`_INDEX_SECTION`·`_ROUTING_SECTION` 삭제)는 Task 2 Step3에 명시.
- **Placeholder 스캔:** 없음 — 모든 스텝에 실제 코드/명령/기대출력.
