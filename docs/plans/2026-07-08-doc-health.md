# doc-health 스킬 구현 계획 (증분 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 전체-repo 탐색 + 9차원 채점으로 문서 건강을 진단해 `render_report`가 먹는 데이터 모델 부분집합을 생산하는 읽기전용 스킬 `doc-health`를 만든다.

**Architecture:** stdlib-only Python 스크립트 2종(`inventory.py` 탐색 분모 · `scorecard.py` 기계채점+등급) + 에이전트 판단 절차(SKILL.md). 도달성은 기존 `gate.py`의 BFS 엔진을 **단일 소스로 재사용**(before/after 동일 채점기 = 정합성) — 이를 위해 `gate.analyze()`를 외과적 추출. 판단(J1~J4·분류·자세 하위)은 코드가 아니라 SKILL 산문(§7.5 anchor_signals.py 삭제 교훈).

**Tech Stack:** Python 3 stdlib (`os`, `json`, `argparse`, `pathlib`), pytest.

## Global Constraints

- **stdlib-only** — 외부 의존 금지(`gate.py`·`content_oracle.py` 패턴).
- **단일 채점기** — 도달성은 `gate.analyze` 하나만. `scorecard.py`가 BFS를 재구현하지 않는다(정합성 §0 H3).
- **doc-health 전용 scripts** — 새 스크립트는 `skills/doc-health/scripts/`. `gate`·`contract`·`render_report`는 `setup-docs/scripts`에서 `conftest.py`/자체 `sys.path` 부트스트랩으로 재사용(H2).
- **정본 리터럴 0** — doc-health 정본 산문에 프로젝트 고유 리터럴 금지. 픽스처는 test 안에서만.
- **판단은 코드 아님** — J1~J4·타입분류·MESSY 하위자세는 SKILL 산문. 스크립트는 기계 차원만.
- **경로 규칙(H1)** — disposition: router(루트 `AGENTS.md`/`CLAUDE.md`/`GEMINI.md`)·tooling(`.claude`/`.github`/`.cursor`/`.gitlab` 하위 + 루트 관례 `README.md`/`CONTRIBUTING.md`/`CHANGELOG.md`/`SECURITY.md`/`CODE_OF_CONDUCT.md`)·content(그 외). M5 = docs/ 밖 **content**만.
- **테스트 러너:** `cd skills/doc-health/scripts && uv run --with pytest pytest -q`. 기존 `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`(105 green)도 회귀 유지.
- **커밋:** gitmoji+conventional. 각 태스크 끝에 커밋. 브랜치 `feat/doc-health`(이미 생성).

---

### Task 1: `gate.analyze()` 외과적 추출 (H3)

**Files:**
- Modify: `skills/setup-docs/scripts/gate.py`
- Test: `skills/setup-docs/scripts/test_gate_analyze.py` (Create)

**Interfaces:**
- Produces: `gate.analyze(root) -> GateResult` where `GateResult = NamedTuple(root: Path, router_present: bool, broken: list[tuple[Path,str]], orphans: list[Path], all_docs: list[Path], visited: set[Path], homes: list[Path])`. `gate.main()`은 그대로 CLI(출력 바이트동일).

- [ ] **Step 1: 실패 테스트 작성** — `analyze`가 구조화 결과를 반환.

```python
# skills/setup-docs/scripts/test_gate_analyze.py
import gate


def _mk(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_analyze_healthy_repo(tmp_path):
    _mk(tmp_path, "AGENTS.md", "# R\n- [x](docs/x.md)\n")
    _mk(tmp_path, "docs/x.md", "# X\n")
    res = gate.analyze(tmp_path)
    assert res.router_present is True
    assert res.broken == []
    assert res.orphans == []
    assert len(res.all_docs) == 1
    assert (tmp_path / "docs" / "x.md").resolve() in res.visited


def test_analyze_detects_orphan_and_broken(tmp_path):
    _mk(tmp_path, "AGENTS.md", "# R\n- [x](docs/x.md)\n- [gone](docs/missing.md)\n")
    _mk(tmp_path, "docs/x.md", "# X\n")
    _mk(tmp_path, "docs/orphan.md", "# not linked\n")
    res = gate.analyze(tmp_path)
    assert len(res.broken) == 1
    assert len(res.orphans) == 1


def test_analyze_no_router(tmp_path):
    _mk(tmp_path, "docs/x.md", "# X\n")
    res = gate.analyze(tmp_path)
    assert res.router_present is False


def test_analyze_finds_marker_home(tmp_path):
    _mk(tmp_path, "AGENTS.md", "# R\n- [m](docs/_map.md)\n")
    _mk(tmp_path, "docs/_map.md",
        "# map\n## 인덱스 <!-- docsherpa:index -->\n- [x](x.md)\n"
        "## 라우팅 <!-- docsherpa:routing -->\nr\n")
    _mk(tmp_path, "docs/x.md", "# X\n")
    res = gate.analyze(tmp_path)
    assert len(res.homes) == 1
    assert res.homes[0].resolve() == (tmp_path / "docs" / "_map.md").resolve()
```

- [ ] **Step 2: 실패 확인** — Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_gate_analyze.py -q` · Expected: FAIL (`AttributeError: module 'gate' has no attribute 'analyze'`).

- [ ] **Step 3: 리팩터** — `gate.py`에 `analyze()`를 추가하고 `main()`이 그것을 쓰게 한다. `import` 줄 아래에 `from typing import NamedTuple` 추가.

```python
# gate.py — import 블록에 추가
from typing import NamedTuple


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
    all_docs = sorted(docs_dir.rglob("*.md")) if docs_dir.is_dir() else []
    orphans = [d for d in all_docs if d.resolve() not in visited]

    scanned = []
    for p in visited:
        try:
            scanned.append((p, p.read_text(encoding="utf-8", errors="ignore")))
        except OSError:
            pass
    homes = contract.find_marker_home(scanned)

    return GateResult(root, router_present, broken, orphans, all_docs, visited, homes)
```

이제 `main()` 몸통을 `analyze()` 사용으로 교체(출력·종료코드 로직은 그대로):

```python
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
```

- [ ] **Step 4: 통과 + 회귀 확인** — Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q` · Expected: 105 기존 + 4 신규 = **109 passed**(기존 gate 테스트 전부 GREEN = CLI 불변 증명).

- [ ] **Step 5: docsherpa 자가 게이트 확인** — Run: `python3 skills/setup-docs/scripts/gate.py . --require-markers` · Expected: `PASS: broken=0 orphan=0 (docs=..., reachable=...) markers_ok=True` (출력 형식 불변).

- [ ] **Step 6: 커밋**

```bash
git add skills/setup-docs/scripts/gate.py skills/setup-docs/scripts/test_gate_analyze.py
git commit -m "♻️ refactor(gate): analyze() 코어 추출 — scorecard 재사용용 단일 도달성 엔진(H3)"
```

---

### Task 2: `inventory.py` — 탐색 분모 (list + check)

**Files:**
- Create: `skills/doc-health/scripts/inventory.py`
- Test: `skills/doc-health/scripts/test_inventory.py`

**Interfaces:**
- Produces: `inventory.list_docs(root) -> list[str]` (repo-상대 POSIX, 정렬). `inventory.unaccounted(root, manifest_paths) -> list[str]`. CLI `list`/`check`.

- [ ] **Step 1: 실패 테스트 작성**

```python
# skills/doc-health/scripts/test_inventory.py
import inventory


def _mk(root, rel, text="# doc\n"):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_list_finds_scattered_and_excludes_junk(tmp_path):
    _mk(tmp_path, "README.md")
    _mk(tmp_path, "docs/x.md")
    _mk(tmp_path, "src/features/a/docs/guide.md")   # 코드옆
    _mk(tmp_path, ".hidden/note.md")                # 숨은 폴더(제외 대상 아님)
    _mk(tmp_path, "page.mdx")                        # mdx도 1급
    _mk(tmp_path, "node_modules/pkg/readme.md")      # 제외
    _mk(tmp_path, "dist/out.md")                     # 제외
    _mk(tmp_path, ".git/COMMIT_EDITMSG.md")          # 제외
    files = inventory.list_docs(tmp_path)
    assert "README.md" in files
    assert "docs/x.md" in files
    assert "src/features/a/docs/guide.md" in files
    assert ".hidden/note.md" in files
    assert "page.mdx" in files
    assert "node_modules/pkg/readme.md" not in files
    assert "dist/out.md" not in files
    assert ".git/COMMIT_EDITMSG.md" not in files
    assert files == sorted(files)


def test_unaccounted_flags_missing(tmp_path):
    _mk(tmp_path, "a.md")
    _mk(tmp_path, "b.md")
    assert inventory.unaccounted(tmp_path, ["a.md"]) == ["b.md"]     # b 누락
    assert inventory.unaccounted(tmp_path, ["a.md", "b.md"]) == []


def test_check_cli_exit_code(tmp_path, capsys):
    _mk(tmp_path, "a.md")
    _mk(tmp_path, "b.md")
    import json
    mani = tmp_path / "m.json"
    mani.write_text(json.dumps([{"path": "a.md"}]), encoding="utf-8")   # b 누락
    rc = inventory.main(["check", str(tmp_path), "--manifest", str(mani)])
    assert rc == 1
    mani.write_text(json.dumps([{"path": "a.md"}, {"path": "b.md"}]), encoding="utf-8")
    assert inventory.main(["check", str(tmp_path), "--manifest", str(mani)]) == 0
```

- [ ] **Step 2: 실패 확인** — Run: `cd skills/doc-health/scripts && uv run --with pytest pytest test_inventory.py -q` · Expected: FAIL (`ModuleNotFoundError: inventory`).

- [ ] **Step 3: 구현**

```python
#!/usr/bin/env python3
"""문서 인벤토리 — doc-health 탐색 1단계(결정론 분모).

repo 전체 *.md·*.mdx 나열(= "잊힌 문서 0"의 분모) + 분류 매니페스트가 그 목록을
전부 덮는지 검사(unaccounted=0). 분류 자체는 병렬 서브에이전트(판단) — 여기 아님.

사용:
  inventory.py list  [ROOT]                     # → JSON {"files":[repo-상대 정렬]}
  inventory.py check [ROOT] --manifest m.json   # 매니페스트가 목록 덮나 → unaccounted, exit 1 시 STOP
"""
import argparse
import json
import os
import sys
from pathlib import Path

EXCLUDE_DIRS = {"node_modules", ".git", "dist", "build", "vendor"}
DOC_SUFFIXES = (".md", ".mdx")


def list_docs(root):
    """ROOT 하위 전 *.md·*.mdx(제외 디렉터리 밖) → repo-상대 POSIX 경로 정렬 리스트."""
    root = Path(root).resolve()
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            if fn.endswith(DOC_SUFFIXES):
                rel = Path(dirpath, fn).relative_to(root)
                out.append(rel.as_posix())
    return sorted(out)


def unaccounted(root, manifest_paths):
    """목록에 있는데 매니페스트에 없는 경로(잊힌 문서) — 정렬."""
    return sorted(set(list_docs(root)) - set(manifest_paths))


def _manifest_paths(manifest_file):
    data = json.loads(Path(manifest_file).read_text(encoding="utf-8"))
    return [e["path"] if isinstance(e, dict) else e for e in data]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    pl = sub.add_parser("list")
    pl.add_argument("root", nargs="?", default=".")
    pc = sub.add_parser("check")
    pc.add_argument("root", nargs="?", default=".")
    pc.add_argument("--manifest", required=True)
    args = ap.parse_args(argv)

    if args.cmd == "list":
        print(json.dumps({"files": list_docs(args.root)}, ensure_ascii=False, indent=2))
        return 0

    miss = unaccounted(args.root, _manifest_paths(args.manifest))
    if miss:
        print("UNACCOUNTED (잊힌 문서 — STOP):")
        for m in miss:
            print(f"  {m}")
        return 1
    print("PASS: unaccounted=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 통과 확인** — Run: `cd skills/doc-health/scripts && uv run --with pytest pytest test_inventory.py -q` · Expected: **3 passed**.

- [ ] **Step 5: 커밋**

```bash
git add skills/doc-health/scripts/inventory.py skills/doc-health/scripts/test_inventory.py
git commit -m "✨ feat(doc-health): inventory.py — 탐색 분모(list) + 완결성 가드(check)"
```

---

### Task 3: `scorecard.py` — disposition + 기계 차원 M1~M5

**Files:**
- Create: `skills/doc-health/scripts/scorecard.py`
- Create: `skills/doc-health/scripts/conftest.py`
- Test: `skills/doc-health/scripts/test_scorecard.py`

**Interfaces:**
- Consumes: `gate.analyze` (Task 1), `contract.ENTRY_FILENAMES`.
- Produces: `scorecard.disposition(rel_path) -> "router"|"tooling"|"content"`. `scorecard.outside_content(files) -> list[str]`. `scorecard.machine_dims(res, files) -> list[dict]` (M1~M5, 각 `{code,name,sub,status}`, `status∈{"pass","warn","fail"}`).

- [ ] **Step 1: conftest 부트스트랩 작성**

```python
# skills/doc-health/scripts/conftest.py
"""doc-health 테스트가 setup-docs 공유 스크립트를 import하도록 경로 부트스트랩(H2).
gate·contract·render_report는 setup-docs/scripts에 산다(단일 채점기 재사용)."""
import sys
from pathlib import Path

_SHARED = Path(__file__).resolve().parents[2] / "setup-docs" / "scripts"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))
```

- [ ] **Step 2: 실패 테스트 작성**

```python
# skills/doc-health/scripts/test_scorecard.py
import scorecard


def _mk(root, rel, text="# doc\n"):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _status(dims, code):
    return next(d["status"] for d in dims if d["code"] == code)


def test_disposition_paths():
    assert scorecard.disposition("AGENTS.md") == "router"
    assert scorecard.disposition("CLAUDE.md") == "router"
    assert scorecard.disposition(".claude/skills/doc-reconcile/SKILL.md") == "tooling"
    assert scorecard.disposition(".github/PULL_REQUEST_TEMPLATE.md") == "tooling"
    assert scorecard.disposition("README.md") == "tooling"
    assert scorecard.disposition("CHANGELOG.md") == "tooling"
    assert scorecard.disposition("docs/x.md") == "content"
    assert scorecard.disposition("src/a/docs/guide.md") == "content"
    # 하위 폴더의 AGENTS.md는 router 아님(루트만)
    assert scorecard.disposition("sub/AGENTS.md") == "content"


def test_outside_content_ignores_router_and_tooling():
    files = ["AGENTS.md", "README.md", ".github/X.md",
             "docs/a.md", "api-help.md", "src/z/docs/g.md"]
    out = scorecard.outside_content(files)
    assert out == ["api-help.md", "src/z/docs/g.md"]   # content & docs/ 밖만


def _healthy_repo(root):
    _mk(root, "AGENTS.md", "# R\n- [m](docs/_map.md)\n")
    _mk(root, "docs/_map.md",
        "# map\n## 인덱스 <!-- docsherpa:index -->\n- [a](a.md)\n"
        "## 라우팅 <!-- docsherpa:routing -->\nr\n")
    _mk(root, "docs/a.md", "# A\n")
    _mk(root, ".claude/doc-drift-prime.txt", "prime")
    _mk(root, ".claude/skills/doc-reconcile/SKILL.md", "# dr\n")
    _mk(root, ".claude/settings.json", '{"hooks":{"SessionStart":[{}]}}')


def test_m_dims_all_pass_on_healthy(tmp_path):
    import gate
    _healthy_repo(tmp_path)
    files = ["AGENTS.md", "docs/_map.md", "docs/a.md"]   # content 밖 0
    res = gate.analyze(tmp_path)
    dims = scorecard.machine_dims(res, files)
    assert [_status(dims, c) for c in ("M1", "M2", "M3", "M4", "M5")] == \
        ["pass", "pass", "pass", "pass", "pass"]


def test_m1_fail_on_orphan(tmp_path):
    import gate
    _healthy_repo(tmp_path)
    _mk(tmp_path, "docs/orphan.md", "# not linked\n")
    res = gate.analyze(tmp_path)
    dims = scorecard.machine_dims(res, ["AGENTS.md", "docs/_map.md", "docs/a.md", "docs/orphan.md"])
    assert _status(dims, "M1") == "fail"


def test_m3_fail_on_inline_marker(tmp_path):
    import gate
    # 마커가 AGENTS.md 인라인(척추 미분리) → M2 pass·M3 fail
    _mk(tmp_path, "AGENTS.md",
        "# R\n## 인덱스 <!-- docsherpa:index -->\n- [a](docs/a.md)\n"
        "## 라우팅 <!-- docsherpa:routing -->\nr\n")
    _mk(tmp_path, "docs/a.md", "# A\n")
    res = gate.analyze(tmp_path)
    dims = scorecard.machine_dims(res, ["AGENTS.md", "docs/a.md"])
    assert _status(dims, "M2") == "pass"
    assert _status(dims, "M3") == "fail"


def test_m4_fail_without_loop(tmp_path):
    import gate
    _mk(tmp_path, "AGENTS.md", "# R\n- [a](docs/a.md)\n")
    _mk(tmp_path, "docs/a.md", "# A\n")
    res = gate.analyze(tmp_path)
    dims = scorecard.machine_dims(res, ["AGENTS.md", "docs/a.md"])
    assert _status(dims, "M4") == "fail"


def test_m5_warn_then_fail(tmp_path):
    import gate
    _healthy_repo(tmp_path)
    res = gate.analyze(tmp_path)
    # 2건 밖 → warn
    dims = scorecard.machine_dims(res, ["AGENTS.md", "docs/a.md", "stray1.md", "stray2.md"])
    assert _status(dims, "M5") == "warn"
    # 4건 밖 → fail (M5_WARN_MAX=3 초과)
    dims2 = scorecard.machine_dims(res, ["s1.md", "s2.md", "s3.md", "s4.md"])
    assert _status(dims2, "M5") == "fail"
```

- [ ] **Step 3: 실패 확인** — Run: `cd skills/doc-health/scripts && uv run --with pytest pytest test_scorecard.py -q` · Expected: FAIL (`ModuleNotFoundError: scorecard`).

- [ ] **Step 4: 구현** — `scorecard.py` 상단(부트스트랩 + disposition + M 차원).

```python
#!/usr/bin/env python3
"""문서 건강 점수표 — doc-health 채점(기계 차원 M1~M5 + 등급 rollup).

도달성은 gate.analyze 재사용(단일 엔진 = 정합성). disposition(H1)으로 M5 분모 결정.
J1~J4 판단·분류·자세 하위는 SKILL.md 절차(코드 아님).
"""
import json
import sys
from pathlib import Path

# --- 공유 스크립트 경로 부트스트랩(CLI 실행 시; 테스트는 conftest.py도) ---------
_SHARED = Path(__file__).resolve().parents[2] / "setup-docs" / "scripts"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

import contract  # noqa: E402
import gate       # noqa: E402

# --- 임계값 (🔴 열린질문 — 하드닝 루프 튜닝, spec §3c) -------------------------
M5_WARN_MAX = 3       # docs/ 밖 content 1~3 = warn, 초과 = fail
ORPHAN_MOST = 0.5     # orphan_ratio >= 이 값이면 "대부분 미도달"(F)
J_WARN_MAX = 2        # J warn 1~2 = B 유지, 초과 = C
GREENFIELD_MAX = 2    # content 문서 이하 + 라우터 없음 = GREENFIELD

# --- disposition (H1) --------------------------------------------------------
_TOOLING_DIRS = (".claude", ".github", ".cursor", ".gitlab")
_ROOT_CONVENTION = {"README.md", "CONTRIBUTING.md", "CHANGELOG.md",
                    "SECURITY.md", "CODE_OF_CONDUCT.md"}


def disposition(rel_path):
    """repo-상대 경로 → 'router'|'tooling'|'content' (경로 규칙, 판단 아님)."""
    parts = Path(rel_path).parts
    name = parts[-1]
    if len(parts) == 1 and name in contract.ENTRY_FILENAMES:
        return "router"
    if parts and parts[0] in _TOOLING_DIRS:
        return "tooling"
    if len(parts) == 1 and name in _ROOT_CONVENTION:
        return "tooling"
    return "content"


def outside_content(files):
    """docs/ 밖 content 문서 목록(M5 위반 후보) — 정렬."""
    out = [f for f in files
           if disposition(f) == "content" and Path(f).parts[0] != "docs"]
    return sorted(out)


# --- 기계 차원 M1~M5 ---------------------------------------------------------
def _has_sessionstart_hook(settings_path):
    if not settings_path.is_file():
        return False
    try:
        return "SessionStart" in settings_path.read_text(encoding="utf-8")
    except OSError:
        return False


def _m4_loop_ok(root):
    root = Path(root)
    return ((root / ".claude" / "doc-drift-prime.txt").is_file()
            and (root / ".claude" / "skills" / "doc-reconcile" / "SKILL.md").is_file()
            and _has_sessionstart_hook(root / ".claude" / "settings.json"))


def _m5_status(files):
    n = len(outside_content(files))
    if n == 0:
        return "pass"
    return "warn" if n <= M5_WARN_MAX else "fail"


def machine_dims(res, files):
    """GateResult + inventory files → [M1..M5] 차원 dict 리스트."""
    root = res.root
    n_home = len(res.homes)
    m1 = "pass" if (not res.broken and not res.orphans) else "fail"
    m2 = "pass" if (res.router_present and n_home == 1) else "fail"
    map_home = (root / "docs" / "_map.md").resolve()
    m3 = "pass" if (n_home == 1 and res.homes[0].resolve() == map_home) else "fail"
    m4 = "pass" if _m4_loop_ok(root) else "fail"
    m5 = _m5_status(files)
    outside = outside_content(files)
    return [
        {"code": "M1", "name": "도달성", "status": m1,
         "sub": f"broken={len(res.broken)} · orphan={len(res.orphans)}"},
        {"code": "M2", "name": "라우터+마커", "status": m2,
         "sub": ("라우터 없음" if not res.router_present
                 else f"마커 home {n_home}개"
                 + ("" if n_home == 1 else " (정확히 1 필요)"))},
        {"code": "M3", "name": "맵 척추", "status": m3,
         "sub": ("home=docs/_map.md" if m3 == "pass"
                 else "척추 미분리(인라인 마커 또는 home≠1)")},
        {"code": "M4", "name": "성장 루프", "status": m4,
         "sub": ("prime·hook·doc-reconcile 설치" if m4 == "pass"
                 else "성장 루프 3종 중 누락")},
        {"code": "M5", "name": "커버리지", "status": m5,
         "sub": (f"docs/ 밖 content {len(outside)}건" if outside
                 else "docs/ 밖 content 0")},
    ]
```

- [ ] **Step 5: 통과 확인** — Run: `cd skills/doc-health/scripts && uv run --with pytest pytest test_scorecard.py -q` · Expected: **6 passed**.

- [ ] **Step 6: 커밋**

```bash
git add skills/doc-health/scripts/scorecard.py skills/doc-health/scripts/conftest.py skills/doc-health/scripts/test_scorecard.py
git commit -m "✨ feat(doc-health): scorecard disposition(H1) + 기계 차원 M1~M5(gate.analyze 재사용)"
```

---

### Task 4: `scorecard.py` — 등급 rollup + counts + posture

**Files:**
- Modify: `skills/doc-health/scripts/scorecard.py`
- Modify: `skills/doc-health/scripts/test_scorecard.py`

**Interfaces:**
- Produces: `scorecard.rollup(mech, judg, orphan_ratio, outside_count, router_present) -> "A".."F"`. `scorecard.counts(mech, judg) -> {"fail","warn","pass"}`. `scorecard.posture_hint(res, files, mech) -> "GREENFIELD"|"HEALTHY"|"MESSY"`.

- [ ] **Step 1: 실패 테스트 작성** (append to `test_scorecard.py`)

```python
def _dims(codes_status):
    # codes_status = {"M1":"pass", ...} → [{code,name,sub,status}]
    return [{"code": c, "name": c, "sub": "", "status": s}
            for c, s in codes_status.items()]


def _mech(m1, m2, m3, m4, m5):
    return _dims({"M1": m1, "M2": m2, "M3": m3, "M4": m4, "M5": m5})


def _judg(j1, j2, j3, j4):
    return _dims({"J1": j1, "J2": j2, "J3": j3, "J4": j4})


def test_rollup_grade_A_all_pass():
    m = _mech("pass", "pass", "pass", "pass", "pass")
    j = _judg("pass", "pass", "pass", "pass")
    assert scorecard.rollup(m, j, 0.0, 0, True) == "A"


def test_rollup_grade_B_one_j_warn():
    m = _mech("pass", "pass", "pass", "pass", "pass")
    j = _judg("warn", "pass", "pass", "pass")
    assert scorecard.rollup(m, j, 0.0, 0, True) == "B"


def test_rollup_grade_C_j_fail_or_one_m_nonpass():
    m = _mech("pass", "pass", "pass", "pass", "pass")
    assert scorecard.rollup(m, _judg("fail", "pass", "pass", "pass"), 0.0, 0, True) == "C"
    m2 = _mech("pass", "warn", "pass", "pass", "pass")   # M2~M5 중 1개 비-pass
    assert scorecard.rollup(m2, _judg("pass", "pass", "pass", "pass"), 0.0, 0, True) == "C"


def test_rollup_grade_D_many_m_nonpass_or_m5_fail():
    m = _mech("pass", "fail", "fail", "fail", "pass")    # M2~M5 중 3개 비-pass
    assert scorecard.rollup(m, _judg("pass", "pass", "pass", "pass"), 0.0, 0, True) == "D"
    m5f = _mech("pass", "pass", "pass", "pass", "fail")  # 대량 밖
    assert scorecard.rollup(m5f, _judg("pass", "pass", "pass", "pass"), 0.0, 8, True) == "D"


def test_rollup_grade_D_and_F_on_reachability():
    m = _mech("fail", "fail", "fail", "fail", "fail")
    # 라우터 있으나 소수 고아 → D
    assert scorecard.rollup(m, _judg("fail", "fail", "fail", "fail"), 0.2, 5, True) == "D"
    # 대부분 미도달 → F
    assert scorecard.rollup(m, _judg("fail", "fail", "fail", "fail"), 0.7, 5, True) == "F"
    # 라우터 없음 → F
    assert scorecard.rollup(m, _judg("fail", "fail", "fail", "fail"), 0.0, 0, False) == "F"


def test_counts_tally():
    m = _mech("pass", "fail", "warn", "pass", "pass")
    j = _judg("warn", "pass", "pass", "fail")
    assert scorecard.counts(m, j) == {"fail": 2, "warn": 2, "pass": 5}


def test_posture_hint(tmp_path):
    import gate
    # GREENFIELD: 라우터 없음 + content 최소
    _mk(tmp_path, "docs/a.md", "# A\n")
    res = gate.analyze(tmp_path)
    m = scorecard.machine_dims(res, ["docs/a.md"])
    assert scorecard.posture_hint(res, ["docs/a.md"], m) == "GREENFIELD"
    # HEALTHY
    _healthy_repo(tmp_path)
    res2 = gate.analyze(tmp_path)
    files = ["AGENTS.md", "docs/_map.md", "docs/a.md"]
    m2 = scorecard.machine_dims(res2, files)
    assert scorecard.posture_hint(res2, files, m2) == "HEALTHY"
```

- [ ] **Step 2: 실패 확인** — Run: `cd skills/doc-health/scripts && uv run --with pytest pytest test_scorecard.py -q` · Expected: FAIL (`AttributeError: ... 'rollup'`).

- [ ] **Step 3: 구현** (append to `scorecard.py`)

```python
# --- 등급 rollup (결정론, 임계값 🔴 튜닝) --------------------------------------
def rollup(mech, judg, orphan_ratio, outside_count, router_present):
    """9차원 상태 + 신호 → 등급 'A'..'F' (spec §3c 산식)."""
    m = {d["code"]: d["status"] for d in mech}
    if not router_present:
        return "F"
    if m["M1"] == "fail" and orphan_ratio >= ORPHAN_MOST:
        return "F"
    if m["M1"] == "fail":
        return "D"
    if m["M5"] == "fail":
        return "D"
    # 여기서 M1 == pass
    m_nonpass = sum(1 for c in ("M2", "M3", "M4", "M5") if m[c] != "pass")
    if m_nonpass >= 3:
        return "D"
    if m_nonpass >= 1:
        return "C"
    # M1~M5 전부 pass
    js = [d["status"] for d in judg]
    j_fail = sum(1 for s in js if s == "fail")
    j_warn = sum(1 for s in js if s == "warn")
    if j_fail or j_warn > J_WARN_MAX:
        return "C"
    if 1 <= j_warn <= J_WARN_MAX:
        return "B"
    return "A"


def counts(mech, judg):
    """전 9차원 상태 tally → {fail,warn,pass}."""
    alld = list(mech) + list(judg)
    return {k: sum(1 for d in alld if d["status"] == k)
            for k in ("fail", "warn", "pass")}


def posture_hint(res, files, mech):
    """결정론 자세 힌트. MESSY 하위 구분은 에이전트 판단(SKILL)."""
    m = {d["code"]: d["status"] for d in mech}
    content = [f for f in files if disposition(f) == "content"]
    if not res.router_present and len(content) <= GREENFIELD_MAX:
        return "GREENFIELD"
    if res.router_present and m["M1"] == "pass" and m["M5"] == "pass":
        return "HEALTHY"
    return "MESSY"
```

- [ ] **Step 4: 통과 확인** — Run: `cd skills/doc-health/scripts && uv run --with pytest pytest test_scorecard.py -q` · Expected: **13 passed**.

- [ ] **Step 5: 커밋**

```bash
git add skills/doc-health/scripts/scorecard.py skills/doc-health/scripts/test_scorecard.py
git commit -m "✨ feat(doc-health): 등급 rollup(게이트형·M1 관문) + counts + posture 힌트"
```

---

### Task 5: `scorecard.py` — 데이터 dict 조립 + render_report 통합(스키마 하드닝 종결)

**Files:**
- Modify: `skills/doc-health/scripts/scorecard.py`
- Modify: `skills/doc-health/scripts/test_scorecard.py`

**Interfaces:**
- Consumes: `render_report.render_report` (통합 테스트, setup-docs/scripts).
- Produces: `scorecard.assemble(root, files, judgment, inventory=None) -> dict` (render_report 부분 데이터 모델). CLI `scorecard.py [ROOT] --manifest m.json --judgment j.json`.

- [ ] **Step 1: 실패 테스트 작성** (append to `test_scorecard.py`)

```python
def test_assemble_shape_and_keys(tmp_path):
    _healthy_repo(tmp_path)
    files = ["AGENTS.md", "docs/_map.md", "docs/a.md"]
    j = _judg("pass", "pass", "pass", "pass")
    d = scorecard.assemble(tmp_path, files, j)
    assert set(d) >= {"repo", "grade", "counts", "scorecard", "trees", "posture"}
    assert set(d["repo"]) == {"name", "docs_count", "branch"}
    assert d["repo"]["docs_count"] == 3
    assert d["grade"] == {"current": "A", "target": "A"}
    assert d["scorecard"]["mechanical"] and d["scorecard"]["judgment"]
    assert "before" in d["trees"]
    assert d["posture"] == "HEALTHY"


def test_assemble_before_tree_marks_stray(tmp_path):
    _healthy_repo(tmp_path)
    files = ["AGENTS.md", "docs/a.md", "api-help.md"]
    d = scorecard.assemble(tmp_path, files, _judg("warn", "pass", "pass", "pass"))
    lines = d["trees"]["before"]["lines"]
    assert ["api-help.md", "stray"] in lines


def test_assemble_feeds_render_report_without_keyerror(tmp_path):
    import render_report
    _healthy_repo(tmp_path)
    files = ["AGENTS.md", "docs/_map.md", "docs/a.md"]
    d = scorecard.assemble(tmp_path, files, _judg("pass", "pass", "pass", "pass"))
    # 독립 건강검진 렌더: migration·decisions 빈 리스트로 plan 모드
    d.setdefault("trees", {}).setdefault("after",
        {"title": "", "tag": "목표", "sub": "", "lines": []})
    d["migration"] = []
    d["decisions"] = []
    d["summary"] = {}
    html = render_report.render_report(d, "plan")
    assert html.count("<div") == html.count("</div>")
    assert 'style="' not in html
    assert d["repo"]["name"] in html
```

- [ ] **Step 2: 실패 확인** — Run: `cd skills/doc-health/scripts && uv run --with pytest pytest test_scorecard.py -q` · Expected: FAIL (`AttributeError: ... 'assemble'`).

- [ ] **Step 3: 구현** (append to `scorecard.py`)

```python
# --- 조립 + CLI --------------------------------------------------------------
def _git_branch(root):
    head = Path(root) / ".git" / "HEAD"
    try:
        txt = head.read_text(encoding="utf-8").strip()
    except OSError:
        return "?"
    prefix = "ref: refs/heads/"
    return txt[len(prefix):] if txt.startswith(prefix) else txt[:8]


def _before_tree(files):
    outside = outside_content(files)
    lines = []
    if any(Path(f).parts[0] == "docs" for f in files):
        lines.append(["docs/", None])
    for f in outside[:12]:
        lines.append([f, "stray"])
    sub = (f"docs/ 밖 흩어짐 · content {len(outside)}건" if outside
           else "docs/ 중심")
    return {"title": "현재 구조", "tag": "지금", "sub": sub, "lines": lines}


def assemble(root, files, judgment, inventory=None):
    """root + inventory files + 에이전트 판단 J차원 → render_report 부분 데이터 모델."""
    res = gate.analyze(root)
    mech = machine_dims(res, files)
    orphan_ratio = (len(res.orphans) / len(res.all_docs)) if res.all_docs else 0.0
    grade = rollup(mech, judgment, orphan_ratio,
                   len(outside_content(files)), res.router_present)
    out = {
        "repo": {"name": Path(root).resolve().name,
                 "docs_count": len(files),
                 "branch": _git_branch(root)},
        "grade": {"current": grade, "target": "A"},
        "counts": counts(mech, judgment),
        "scorecard": {"mechanical": mech, "judgment": judgment},
        "trees": {"before": _before_tree(files)},
        "posture": posture_hint(res, files, mech),
    }
    if inventory is not None:
        out["inventory"] = inventory
    return out


def main(argv=None):
    import argparse
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--manifest", help="분류 매니페스트 JSON([{path,type,...}])")
    ap.add_argument("--judgment", help="J1~J4 판단 차원 JSON([{code,name,sub,status}])")
    args = ap.parse_args(argv)

    import inventory as _inv
    files = _inv.list_docs(args.root)
    manifest = None
    if args.manifest:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    judgment = []
    if args.judgment:
        judgment = json.loads(Path(args.judgment).read_text(encoding="utf-8"))
    data = assemble(args.root, files, judgment, inventory=manifest)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

> `main`은 `inventory.list_docs`로 파일 목록을 직접 뽑는다(에이전트가 `--manifest`로 분류를, `--judgment`로 J차원을 넘긴다). `import inventory`는 같은 디렉터리라 CLI에서 해석됨.

- [ ] **Step 4: 통과 확인** — Run: `cd skills/doc-health/scripts && uv run --with pytest pytest -q` · Expected: **전체 doc-health 스위트 GREEN** (inventory 3 + scorecard 16 = 19 passed).

- [ ] **Step 5: setup-docs 회귀 확인** — Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q` · Expected: **109 passed**(Task 1 이후 불변).

- [ ] **Step 6: 커밋**

```bash
git add skills/doc-health/scripts/scorecard.py skills/doc-health/scripts/test_scorecard.py
git commit -m "✨ feat(doc-health): 데이터 dict 조립 + render_report 통합(스키마 하드닝 종결)"
```

---

### Task 6: `SKILL.md` + `reference/scoring.md` (에이전트 절차 + 루브릭)

**Files:**
- Create: `skills/doc-health/SKILL.md`
- Create: `skills/doc-health/reference/scoring.md`

**Interfaces:** 없음(산문). 스크립트를 경로로 호출하는 절차 + 9차원 루브릭.

- [ ] **Step 1: `SKILL.md` 작성** — 다음 요건을 담는다(정본 리터럴 0 — 픽스처·프로젝트명 금지):
  - **frontmatter:** `name: doc-health` · `description: 문서 건강을 전체-repo 탐색+9차원 채점으로 진단(읽기전용). 수시 건강검진 또는 setup-docs Phase 0·4가 호출.`
  - **Overview:** 읽기전용 진단 생산자. 산출 = render_report 부분 데이터 모델. 변경 안 함.
  - **When to Use:** 수시 "문서 건강검진" · setup-docs Phase 0(before)·4(after) 호출.
  - **절차:**
    1. `python3 skills/doc-health/scripts/inventory.py list <repo>` → 분모(files).
    2. **병렬 분류(판단):** files를 슬라이스로 나눠 서브에이전트 동시 판정 → 매니페스트 `[{path, type(ADR/spec/how-to/reference/PRD/legacy), role, coupling, summary}]`. 판단 휴리스틱 = `skills/setup-docs/reference/knowledge.md`(단일 소스). disposition(router/tooling/content)은 스크립트가 계산하므로 분류는 **content 타입 판정**에 집중.
    3. `inventory.py check <repo> --manifest manifest.json` → **unaccounted=0 아니면 STOP**(완결성 가드).
    4. **J1~J4 판단** → `judgment.json = [{code,name,sub,status}]`(J1 타입분류 정확성·J2 폴더승격·J3 hollow/dup/bloat[README 비대 포함]·J4 정합성 플래그). 루브릭 = `reference/scoring.md`.
    5. `scorecard.py <repo> --manifest manifest.json --judgment judgment.json` → 데이터 dict(기계 M1~M5 + rollup 등급 + 자세 힌트 포함).
    6. **자세 판정:** 스크립트 `posture` 힌트 + MESSY면 하위(중구난방/자체구조/드리프트된-docsherpa) 판단(ADR 0014).
    7. **(독립 실행 시) 렌더:** dict에 `trees.after={...빈...}`·`migration=[]`·`decisions=[]`·`summary={}` 채워 `render_report(dict, "plan")` → 아티팩트. (setup-docs 연동 시엔 dict를 그대로 넘김.)
  - **Common Mistakes:** unaccounted STOP 무시 · 판단을 코드로 박제 · router/tooling을 M5 위반으로 오인 · 정본에 프로젝트 리터럴 삽입.
- [ ] **Step 2: `reference/scoring.md` 작성** — 9차원 루브릭(M1~M5 기계 판정 규칙 + J1~J4 판단 기준) · 등급 산식(spec §3c 표) · 자세 정의 · 임계값이 🔴 튜닝임을 명시. 판단 휴리스틱 상세는 `../../setup-docs/reference/knowledge.md` 참조(중복 금지).
- [ ] **Step 3: 정본 리터럴 0 확인** — Run: `grep -rn -iE "docsherpa|vd-front|jio" skills/doc-health/SKILL.md skills/doc-health/reference/scoring.md | grep -v "docsherpa:" | grep -vi "skills/setup-docs"` · Expected: 아키텍처 참조(마커·경로) 외 프로젝트 고유 리터럴 없음. (마커 `docsherpa:` 접두어·스킬 경로는 아키텍처 계약이라 허용.)
- [ ] **Step 4: 게이트 확인(스킬은 docs/ 밖 → orphan 무관, 회귀만)** — Run: `python3 skills/setup-docs/scripts/gate.py . --require-markers` · Expected: `PASS ... markers_ok=True`.
- [ ] **Step 5: 커밋**

```bash
git add skills/doc-health/SKILL.md skills/doc-health/reference/scoring.md
git commit -m "✨ feat(doc-health): SKILL 절차 + 9차원 루브릭(scoring.md) — 판단은 산문"
```

---

### Task 7: ADR(모듈 분해) + 배선(테스트 러너·인덱스·ledger)

**Files:**
- Create: `docs/decisions/0015-doc-health-module-extraction.md`
- Modify: `docs/decisions/README.md` (로그 표 한 줄)
- Modify: `AGENTS.md` (테스트 명령어에 doc-health 러너 병기)
- Modify: `docs/plans/README.md` (이 계획 등록)
- Modify: `FINDINGS.md` · `.superpowers/sdd/progress.md` (증분 2 완료 기록)

**Interfaces:** 없음(문서·배선).

- [ ] **Step 1: ADR 0015 작성** — `docs/decisions/_template.md` 복사. 맥락(design §4 모듈 분해 + before/after 동일 채점기 정합성) · 결정(doc-health 독립 스킬 추출, 전용 scripts, gate.analyze 재사용, 판단은 산문 — H1~H3) · 결과(정합성·자립성 vs 크로스-dir import 부트스트랩 비용; render_report 위치는 setup-docs/scripts 유지 = 이연).
- [ ] **Step 2: 로그 등록** — `docs/decisions/README.md` 표에 추가:

```markdown
| [0015](0015-doc-health-module-extraction.md) | doc-health 독립 스킬 추출 — 전용 scripts·gate.analyze 재사용·판단은 산문(H1~H3) | 수락 | 2026-07-08 |
```

- [ ] **Step 3: AGENTS.md 명령어 병기** — `## 명령어` 아래 테스트 줄을 두 러너로:

```markdown
- 테스트: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q` · `cd skills/doc-health/scripts && uv run --with pytest pytest -q`
```

- [ ] **Step 4: 계획 인덱스 등록** — `docs/plans/README.md`에 이 계획 한 줄 추가:

```markdown
- [2026-07-08-doc-health.md](2026-07-08-doc-health.md) — 증분 2: `doc-health` 진단 생산자 스킬(전체-repo 탐색 + 9차원 채점 → render_report 부분 데이터 모델). 후속: setup-docs Phase 0·4 배선.
```

- [ ] **Step 5: 게이트 + 전체 회귀 확인** — Run:
  - `python3 skills/setup-docs/scripts/gate.py . --require-markers` · Expected: `PASS broken=0 orphan=0 ... markers_ok=True` (ADR·계획 등록으로 orphan 0 유지).
  - `cd skills/setup-docs/scripts && uv run --with pytest pytest -q` · Expected: 109 passed.
  - `cd skills/doc-health/scripts && uv run --with pytest pytest -q` · Expected: 19 passed.
- [ ] **Step 6: ledger·FINDINGS 갱신** — `.superpowers/sdd/progress.md`에 "doc-health — SDD progress" 섹션(태스크별 완료·리뷰 결과) + `FINDINGS.md` 최상단 "다음 세션 시작점"을 증분 2 완료·다음=setup-docs Phase 0·4 배선으로 갱신.
- [ ] **Step 7: 커밋**

```bash
git add docs/decisions/0015-doc-health-module-extraction.md docs/decisions/README.md AGENTS.md docs/plans/README.md FINDINGS.md .superpowers/sdd/progress.md
git commit -m "📝 docs(doc-health): ADR 0015 모듈분해 + 러너·인덱스·ledger 배선"
```

---

## Self-Review (작성자 체크)

**1. 스펙 커버리지** (spec `doc-health.md` 각 절 → 태스크):
- §1 스킬 골격 → Task 2·3·6(scripts·conftest·SKILL·reference 전부 생성).
- §2 탐색(inventory list/check + 분류 절차 + disposition) → Task 2(스크립트) + Task 6(분류 산문) + Task 3(disposition).
- §3 채점(M1~M5·J1~J4·rollup·자세) → Task 3(M dims)·Task 4(rollup/counts/posture)·Task 6(J 산문·루브릭).
- §4 데이터 계약(부분집합 + 스키마 하드닝) → Task 5(assemble + render 통합 테스트).
- §5 테스트 계획 → Task 1~5 RED-first 전 항목 매핑(inventory·disposition·M dims·gate.analyze 패리티·rollup·통합).
- §6 호출 기전 → Task 6 SKILL 절차(독립 + 절차 참조).
- §0 H1(M5 분모)·H2(전용 scripts)·H3(gate.analyze) → Task 3(disposition)·Task 2·3(scripts+conftest)·Task 1.
- ADR(모듈 분해) → Task 7.

**2. 플레이스홀더 스캔:** 코드 스텝 전부 실제 코드. 산문 스텝(Task 6·7)은 "무엇을 담을지" 요건을 구체 열거(정본 리터럴 0 grep 가드 포함). TBD 없음.

**3. 타입 정합성:** `machine_dims`가 내는 dim dict `{code,name,sub,status}` ↔ `rollup`/`counts`가 `d["code"]`·`d["status"]`로 소비 ↔ render_report 계약 `{code,name,sub,status}`·`status∈{pass,warn,fail}` 일치. `GateResult` 필드(Task 1) ↔ `machine_dims`·`assemble`·`posture_hint` 소비(`res.broken`·`res.orphans`·`res.homes`·`res.router_present`·`res.all_docs`·`res.root`) 일치. `assemble` 반환 키 ↔ render 계약 부분집합 일치.

## Execution Handoff

**Plan complete and saved to `docs/plans/2026-07-08-doc-health.md`.**
