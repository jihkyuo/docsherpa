# setup-docs 파이프라인 (증분 4) 구현 계획 — 승인된 계획의 실제 랜딩 → 재진단

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **선행 스펙:** [landing-migration.md](../specs/diagnosis-driven-migration/landing-migration.md) (§0b R1~R9 교차검증 개정 = codex + architect). 이 계획의 태스크는 스펙 §7 테스트 T1~T9와 대응한다.

**Goal:** 증분 3이 스크래치에서 증명한 마이그레이션 계획을, 사용자가 검토할 실제 git 브랜치로 안전하게 랜딩하고(worktree 격리·검증트리=커밋트리·통과 시에만 커밋) 결과를 재진단한다. 정체성(내용 소실 0·앵커 보존·비파괴)을 세 오라클(unaccounted·new_broken/anchor·orphan) + per-file 인스턴스 회계가 강제한다.

**Architecture:** `migrate.py`에 ① 도달성-구동 `register_all` ② 도달성-무관 링크 해석 + 소스정체성 페어링 오라클(new/preexisting/anchor) ③ per-file 인스턴스 회계 ④ 세 오라클 일원화 `verify_migration` ⑤ 실행 진입점 `land_migration`(이중 worktree·HEAD 핀·finally 흔적0)을 추가. 기존 `apply_moves`·`rewrite_links`·`scaffold`·`gate`·`content_oracle`·`doc-health`·`render_report`는 재사용. Phase 4는 doc-health 재실행 + render result 모드.

**Tech Stack:** Python 3 stdlib (`subprocess`(git worktree), `shutil`, `tempfile`, `pathlib`, `posixpath`, `re`), pytest.

## Global Constraints

- **stdlib-only** — 외부 의존 금지(`gate.py`·`content_oracle.py` 패턴).
- **정체성 불가침** — 내용 소실 0(content_oracle unaccounted=0 + per-file 회계) · 앵커 보존(anchor_lost=0) · 비파괴(worktree 격리, 실 작업트리·미커밋 무영향, 통과 시에만 커밋).
- **검증트리=커밋트리(R3)** — worktree를 그 자리에서 검증하고 그 트리를 그대로 커밋. 재실행·별도 트리 커밋 금지.
- **git 전제** — non-git repo면 STOP. worktree base·current 둘 다 커밋 HEAD 상태(copytree·ignore-list 사각 회피).
- **surrogateescape 일관** — 모든 .md 읽기/쓰기(G2). register 경로 포함(R6).
- **위치:** `skills/setup-docs/scripts/migrate.py` + `test_migrate.py`(+ 신규 링크 오라클 테스트). 러너 `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`.
- **브랜치:** `fix/incr4-exec-gates-g1-g2`(이미 생성, G1·G2·스펙 커밋됨). 커밋=gitmoji+conventional. 커밋마다 origin push.
- **RED-first** — 각 태스크 실패 테스트 먼저 → 최소 구현 → 그린 → 커밋. gate broken=0·orphan=0 유지(docsherpa 자기 dogfood).

## 데이터 계약 (신규 인터페이스)

```python
# 도달성-무관 링크 해석 — 한 문서의 링크들을 (raw, kind, resolved, anchor)로.
def doc_links(root: Path, rel: str) -> list[dict]:
    # [{"raw": "b.md#sec", "kind": "file"|"dir"|"skip", "resolved": bool, "anchor": "sec"}]

# 소스정체성 페어링 분류 → 세 리스트.
def classify_links(base_root: Path, cur_root: Path, move_plan: list) -> dict:
    # {"new_broken": [(rel, raw)], "preexisting_broken": [(rel, raw)], "anchor_lost": [(rel, raw)]}

# per-file 인스턴스 회계.
def per_file_accounting(base_root: Path, cur_root: Path, move_plan: list) -> list:
    # 위반 리스트 [] = ok. [(src, "세그먼트 dest 미도달"|"파일수 감소")]

# 세 오라클 일원화.
def verify_migration(base_root: Path, cur_root: Path, move_plan: list) -> dict:
    # {"unaccounted": [...], "new_broken": [...], "preexisting_broken": [...],
    #  "anchor_lost": [...], "orphan": int, "per_file": [...]}

# 도달성-구동 등록(무반환, 미수렴 시 raise).
def register_all(root: Path) -> None

# 실행 진입점.
def land_migration(repo, move_plan, head_sha, decisions=None, *, plugin_root=None) -> dict:
    # {"branch": str, "unaccounted": [], "new_broken": [], "anchor_lost": [],
    #  "preexisting_broken": [...], "moved": int}
```

**재사용 인터페이스(기존):** `gate.analyze(root) -> GateResult(broken, orphans, all_docs, visited, ...)` · `gate.resolve(cur_path, raw) -> (kind, target)` · `gate.targets_in(path) -> [raw]` · `gate.index_of(dir)` · `gate.LINK_RE`(fence 제거는 `targets_in`이 처리) · `content_oracle.collect(root) -> {key: {preview, locs}}` · `content_oracle.segment/seg_key` · `migrate.apply_moves(root, move_plan)` · `migrate.rewrite_links` · `scaffold.scaffold(root, plugin_root_dir=)`.

---

### Task 1: `register_all` — 도달성-구동 등록 (R5·R6, 스펙 §4·T1)

**Files:**
- Modify: `skills/setup-docs/scripts/migrate.py` (신규 `register_all` + live-link 헬퍼; `register_in_indexes`는 유지하되 `build_and_verify`/`land_migration`은 `register_all` 사용)
- Test: `skills/setup-docs/scripts/test_migrate.py`

**Interfaces:**
- Consumes: `gate.analyze(root).orphans`(list[Path]) · 기존 `_ensure_folder_index`·`_append_links`·`_index_home`·`_home_links_index`
- Produces: `register_all(root) -> None` (orphan=0 도달, 미수렴 시 `RuntimeError`)

- [ ] **Step 1: 실패 테스트 — 제자리·이동 섞여도 orphan=0 (균일)**

```python
def test_register_all_registers_inplace_and_moved_uniformly(tmp_path):
    import gate
    _mk(tmp_path, "CLAUDE.md", "# C\n@AGENTS.md\n")
    _mk(tmp_path, "AGENTS.md", "# A\n<!-- docsherpa:map -->\n- [map](docs/_map.md)\n")
    _mk(tmp_path, "docs/_map.md", "# Map\n<!-- docsherpa:index -->\n")
    _mk(tmp_path, "docs/harness/inplace.md", "# 제자리 문서\n")     # 이동 안 함 → 기존 register 누락
    _mk(tmp_path, "docs/decisions/moved.md", "# 이동된 ADR\n")
    migrate.register_all(tmp_path)
    assert not gate.analyze(tmp_path).orphans          # 제자리·이동 전부 도달
```

- [ ] **Step 2: 실패 확인** — Run: `uv run --with pytest pytest test_migrate.py::test_register_all_registers_inplace_and_moved_uniformly -v` · Expected: FAIL (`AttributeError: module 'migrate' has no attribute 'register_all'`)

- [ ] **Step 3: 실패 테스트 — 진행 가드(등록 불가 orphan은 무한루프 아닌 error)**

```python
def test_register_all_progress_guard_raises_on_stuck(tmp_path, monkeypatch):
    import gate
    _mk(tmp_path, "CLAUDE.md", "# C\n@AGENTS.md\n")
    _mk(tmp_path, "AGENTS.md", "# A\n")                # 라우터에 map 마커 없음 → home 없음
    _mk(tmp_path, "docs/x.md", "# X\n")                # 등록할 home이 없어 도달 불가
    import pytest
    with pytest.raises(RuntimeError):
        migrate.register_all(tmp_path)                  # 무한루프 대신 즉시 error
```

- [ ] **Step 4: 실패 테스트 — 펜스 속 예시링크를 "이미 링크됨"으로 오탐 안 함(R5)**

```python
def test_register_all_ignores_fenced_example_links(tmp_path):
    import gate
    _mk(tmp_path, "CLAUDE.md", "# C\n@AGENTS.md\n")
    _mk(tmp_path, "AGENTS.md", "# A\n<!-- docsherpa:map -->\n- [map](docs/_map.md)\n")
    # 폴더 인덱스에 펜스 코드블록으로 bar.md 링크가 예시로 들어있음(실링크 아님)
    _mk(tmp_path, "docs/g/_README.md", "# G\n```\n- [예시](bar.md)\n```\n")
    _mk(tmp_path, "docs/g/bar.md", "# Bar\n")
    _mk(tmp_path, "docs/_map.md", "# Map\n<!-- docsherpa:index -->\n- [g](g/)\n")
    migrate.register_all(tmp_path)
    assert not gate.analyze(tmp_path).orphans          # bar.md가 펜스오탐으로 방치되지 않음
```

- [ ] **Step 5: 실패 확인** — 3·4 테스트 FAIL 확인.

- [ ] **Step 6: 구현 — `register_all` + live-link 헬퍼**

```python
def _live_link_targets(text):
    """gate와 동일 의미론: 펜스 코드블록 제거 후 실제 ](target) 만 추출(raw substring 오탐 방지, R5)."""
    return set(gate.targets_in_text(text)) if hasattr(gate, "targets_in_text") else set(gate.LINK_RE.findall(_strip_fences(text)))

def _strip_fences(text):
    out, in_fence = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return "\n".join(out)

def _append_links_live(path, entries):
    """_append_links와 동일하나 '이미 있음' 판정을 live-link 파싱으로(R5). 반환=신규 추가 수."""
    text = path.read_text(encoding="utf-8", errors="surrogateescape") if path.exists() else ""
    have = _live_link_targets(text)
    add = [(lab, t) for lab, t in entries if t not in have]
    if not add:
        return 0
    block = "\n".join(f"- [{lab}]({t})" for lab, t in add) + "\n"
    sep = "" if text.endswith("\n\n") else ("\n" if text.endswith("\n") else ("\n\n" if text else ""))
    path.write_text(text + sep + block, encoding="utf-8", errors="surrogateescape")
    return len(add)

def register_all(root):
    """도달성-구동: gate가 orphan으로 보는 docs/**/*.md 전부를 폴더 인덱스·map에 배선.
    이동/제자리/legacy 균일(L3). 진행 가드로 미수렴 시 RuntimeError(R5)."""
    root = Path(root)
    while True:
        orphans = [p.relative_to(root).as_posix() for p in gate.analyze(root).orphans]
        if not orphans:
            return
        added = _register_orphan_rels(root, orphans)
        if added == 0:
            raise RuntimeError(f"register_all 미수렴 — 등록 불가 orphan: {orphans}")

def _register_orphan_rels(root, rels):
    """orphan 상대경로들을 폴더별로 묶어 인덱스+map에 등록. 반환=신규 링크 수(진행 측정)."""
    home = _index_home(root)
    if home is None:
        raise RuntimeError("register_all 미수렴 — index home(맵/라우터 마커) 없음")
    home_dir = home.parent.relative_to(root).as_posix()
    home_text = home.read_text(encoding="utf-8", errors="surrogateescape")
    by_folder, flats, added = {}, [], 0
    for rel in rels:
        folder = posixpath.dirname(rel)
        (flats if folder == "docs" else by_folder.setdefault(folder, [])).append(rel)
    map_entries = []
    for folder, items in sorted(by_folder.items()):
        idx = _ensure_folder_index(root / folder)
        names = sorted(posixpath.basename(r) for r in items if (root / folder / posixpath.basename(r)) != idx)
        added += _append_links_live(idx, [(posixpath.splitext(n)[0], n) for n in names])
        rel_to_home = posixpath.relpath(folder, home_dir or ".")
        if not _home_links_index(home_text, rel_to_home):
            map_entries.append((posixpath.basename(folder), rel_to_home + "/"))
    for rel in sorted(flats):
        map_entries.append((posixpath.splitext(posixpath.basename(rel))[0], posixpath.relpath(rel, home_dir or ".")))
    if map_entries:
        added += _append_links_live(home, map_entries)
    return added
```

- [ ] **Step 7: 그린 확인** — Run: `uv run --with pytest pytest test_migrate.py -k register_all -v` · Expected: 3 PASS. (`gate.targets_in_text` 없으면 `_strip_fences`+`LINK_RE` 경로 사용 — gate에 헬퍼 없으면 그 분기 채택.)

- [ ] **Step 8: 전체 러너 + gate** — Run: `uv run --with pytest pytest -q && cd /Users/jiohyeon/Desktop/private/docsherpa && python3 skills/setup-docs/scripts/gate.py . --require-markers` · Expected: all pass, gate PASS.

- [ ] **Step 9: 커밋**

```bash
git add skills/setup-docs/scripts/migrate.py skills/setup-docs/scripts/test_migrate.py
git commit -m "✨ feat(migrate): register_all 도달성-구동 등록(진행가드·live-link·surrogateescape) — R5·R6"
git push
```

---

### Task 2: 도달성-무관 링크 해석 + new/preexisting 분류 (R1, 스펙 §5·T2)

**Files:**
- Modify: `skills/setup-docs/scripts/migrate.py`
- Test: `skills/setup-docs/scripts/test_link_oracle.py` (신규)

**Interfaces:**
- Consumes: `gate.resolve(cur_path, raw)`(kind·target) · `gate.targets_in(path)`(raw 링크들, fence 제거됨) · `move_plan`(list of `{"src","dest",...}`)
- Produces: `doc_links(root, rel) -> list[dict]` · `classify_links(base_root, cur_root, move_plan) -> {"new_broken","preexisting_broken","anchor_lost"}`

- [ ] **Step 1: 실패 테스트 — 이동-소스 링크 미-rebase는 new_broken(R1 워크드예제)**

```python
# test_link_oracle.py
from pathlib import Path
import migrate

def _mk(root, rel, text):
    p = Path(root) / rel; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

def test_moved_source_unrebased_link_is_new_broken(tmp_path):
    base = tmp_path / "base"; cur = tmp_path / "cur"
    # base: guide/a.md 가 ./b.md(=guide/b.md) 링크, 둘 다 존재 → base에서 satisfiable
    _mk(base, "docs/guide/a.md", "# A\n[b](./b.md)\n")
    _mk(base, "docs/guide/b.md", "# B\n")
    # cur: a·b 둘 다 이동했으나 a의 링크가 재작성 안 됨(회귀) → how-to/b.md 없음 → broken
    _mk(cur, "docs/how-to/a.md", "# A\n[b](./b.md)\n")
    _mk(cur, "docs/reference/b.md", "# B\n")
    plan = [{"src": "docs/guide/a.md", "dest": "docs/how-to/a.md"},
            {"src": "docs/guide/b.md", "dest": "docs/reference/b.md"}]
    r = migrate.classify_links(base, cur, plan)
    assert ("docs/how-to/a.md", "./b.md") in r["new_broken"]      # 우리가 깨뜨림 → 차단
    assert not r["preexisting_broken"]
```

- [ ] **Step 2: 실패 테스트 — 스테일 코드참조는 preexisting(비차단)**

```python
def test_stale_code_ref_is_preexisting(tmp_path):
    base = tmp_path / "base"; cur = tmp_path / "cur"
    _mk(base, "docs/api.md", "# API\n[code](src/apis/)\n")   # src/apis/ 애초에 없음
    _mk(cur, "docs/reference/api.md", "# API\n[code](../../src/apis/)\n")  # re-base 정확, 여전히 없음
    plan = [{"src": "docs/api.md", "dest": "docs/reference/api.md"}]
    r = migrate.classify_links(base, cur, plan)
    assert r["preexisting_broken"]                    # 원래 깨짐 → 표면화만
    assert not r["new_broken"]
```

- [ ] **Step 3: 실패 확인** — Run: `uv run --with pytest pytest test_link_oracle.py -v` · Expected: FAIL (`classify_links` 없음).

- [ ] **Step 4: 구현 — `doc_links` + `classify_links`**

```python
def doc_links(root, rel):
    """도달성 무관, 한 문서의 링크들을 해석. resolve는 gate.resolve(파일위치 기준)."""
    root = Path(root); path = root / rel
    out = []
    for raw in gate.targets_in(path):                 # fence 제거된 raw 링크들
        kind, target = gate.resolve(path, raw)
        anchor = raw.split("#", 1)[1] if "#" in raw else ""
        if kind == "skip":
            out.append({"raw": raw, "kind": "skip", "resolved": True, "anchor": anchor}); continue
        if kind == "dir":
            resolved = Path(target).is_dir()
        else:  # file
            resolved = (not target.name.endswith(".md")) or target.is_file()   # 비-.md는 gate가 skip(해석성공 취급)
        out.append({"raw": raw, "kind": kind, "resolved": resolved, "anchor": anchor})
    return out

def classify_links(base_root, cur_root, move_plan):
    """소스정체성 페어링(R1): base 문서 ↔ cur 문서(move_map) · 링크 index zip.
    new_broken = base-satisfiable & cur-broken. preexisting = 둘 다 broken. anchor_lost = 앵커 축소."""
    base_root, cur_root = Path(base_root), Path(cur_root)
    move_map = {p["src"]: p["dest"] for p in move_plan}
    res = {"new_broken": [], "preexisting_broken": [], "anchor_lost": []}
    for bmd in sorted(base_root.rglob("*.md")):
        old_rel = bmd.relative_to(base_root).as_posix()
        new_rel = move_map.get(old_rel, old_rel)
        if not (cur_root / new_rel).is_file():
            continue                                   # dest 부재는 per_file 회계(Task 4)가 담당
        bl = [l for l in doc_links(base_root, old_rel) if l["kind"] != "skip"]
        cl = [l for l in doc_links(cur_root, new_rel) if l["kind"] != "skip"]
        for i, b in enumerate(bl):                     # append-at-end(register)라 base index가 앞에서 정렬
            c = cl[i] if i < len(cl) else None
            if c is None:
                continue
            if b["resolved"] and not c["resolved"]:
                res["new_broken"].append((new_rel, c["raw"]))
            elif not b["resolved"] and not c["resolved"]:
                res["preexisting_broken"].append((new_rel, c["raw"]))
            if b["anchor"] and b["anchor"] != c["anchor"]:
                res["anchor_lost"].append((new_rel, c["raw"]))
    return res
```

- [ ] **Step 5: 그린 확인** — Run: `uv run --with pytest pytest test_link_oracle.py -v` · Expected: 2 PASS.

- [ ] **Step 6: 커밋**

```bash
git add skills/setup-docs/scripts/migrate.py skills/setup-docs/scripts/test_link_oracle.py
git commit -m "✨ feat(migrate): 소스정체성 페어링 링크 오라클(new vs preexisting) — R1"
git push
```

---

### Task 3: 앵커 보존 게이트 (R2, 스펙 §5·T3)

**Files:**
- Test: `skills/setup-docs/scripts/test_link_oracle.py` (Task 2 `classify_links`의 anchor_lost 검증 — 로직은 Task 2에 이미 포함)

**Interfaces:**
- Consumes: `classify_links(...)["anchor_lost"]`

- [ ] **Step 1: 실패 테스트 — base 앵커가 cur에서 사라지면 anchor_lost**

```python
def test_anchor_dropped_flagged(tmp_path):
    base = tmp_path / "base"; cur = tmp_path / "cur"
    _mk(base, "docs/a.md", "# A\n[api](guide.md#api-v1)\n")
    _mk(base, "docs/guide.md", "# G\n")
    _mk(cur, "docs/a.md", "# A\n[api](guide.md)\n")     # 앵커 소실(버그 시뮬)
    _mk(cur, "docs/guide.md", "# G\n")
    r = migrate.classify_links(base, cur, [])
    assert ("docs/a.md", "guide.md") in r["anchor_lost"]
```

- [ ] **Step 2: 실패 확인 → 그린** — Task 2에서 anchor 비교를 이미 구현했으면 PASS. 아니면 `classify_links`의 anchor 분기 추가 후 PASS. Run: `uv run --with pytest pytest test_link_oracle.py::test_anchor_dropped_flagged -v`

- [ ] **Step 3: 커밋**

```bash
git add skills/setup-docs/scripts/test_link_oracle.py
git commit -m "✅ test(migrate): 앵커 보존 게이트 검증 — R2"
git push
```

---

### Task 4: per-file 인스턴스 회계 (R7, 스펙 §5·T4)

**Files:**
- Modify: `skills/setup-docs/scripts/migrate.py`
- Test: `skills/setup-docs/scripts/test_link_oracle.py`

**Interfaces:**
- Consumes: `content_oracle.segment/seg_key` · `move_plan`
- Produces: `per_file_accounting(base_root, cur_root, move_plan) -> list`(위반; [] = ok)

- [ ] **Step 1: 실패 테스트 — 동일내용 2문서 중 1개 드롭은 content_oracle 통과해도 per_file이 잡음**

```python
import content_oracle

def test_per_file_catches_dropped_duplicate_content_doc(tmp_path):
    base = tmp_path / "base"; cur = tmp_path / "cur"
    dup = "# 공통\n동일한 보일러플레이트 세그먼트.\n"
    _mk(base, "docs/a.md", dup)
    _mk(base, "docs/b.md", dup)                        # a·b 동일내용
    _mk(cur, "docs/a.md", dup)                         # b가 통째 소실(이동 실패 시뮬)
    plan = [{"src": "docs/a.md", "dest": "docs/a.md"}, {"src": "docs/b.md", "dest": "docs/b.md"}]
    # content_oracle는 통과(고유 세그먼트 살아있음)
    assert not (set(content_oracle.collect(base)) - set(content_oracle.collect(cur)))
    # 하지만 per_file은 b의 dest 미도달을 잡아야
    viol = migrate.per_file_accounting(base, cur, plan)
    assert any("docs/b.md" in str(v) for v in viol)
```

- [ ] **Step 2: 실패 확인** — Run: `uv run --with pytest pytest test_link_oracle.py::test_per_file_catches_dropped_duplicate_content_doc -v` · Expected: FAIL.

- [ ] **Step 3: 구현 — `per_file_accounting`**

```python
def per_file_accounting(base_root, cur_root, move_plan):
    """각 base 문서의 세그먼트 집합이 그 dest 파일에 존재하는지 + 파일수 보존(R7).
    content_oracle의 '고유 세그먼트 집합' 사각(인스턴스 소실) 보완. 반환=위반 리스트([]=ok)."""
    base_root, cur_root = Path(base_root), Path(cur_root)
    move_map = {p["src"]: p["dest"] for p in move_plan}
    viol = []
    for bmd in sorted(base_root.rglob("*.md")):
        old_rel = bmd.relative_to(base_root).as_posix()
        new_rel = move_map.get(old_rel, old_rel)
        dest = cur_root / new_rel
        if not dest.is_file():
            viol.append((new_rel, "dest 파일 미도달")); continue
        base_keys = {content_oracle.seg_key(s)
                     for s in content_oracle.segment(bmd.read_text(encoding="utf-8", errors="surrogateescape"))}
        dest_keys = {content_oracle.seg_key(s)
                     for s in content_oracle.segment(dest.read_text(encoding="utf-8", errors="surrogateescape"))}
        missing = base_keys - dest_keys
        if missing:
            viol.append((new_rel, f"세그먼트 dest 미도달 {len(missing)}건"))
    return viol
```

- [ ] **Step 4: 그린 확인** — Run: `uv run --with pytest pytest test_link_oracle.py::test_per_file_catches_dropped_duplicate_content_doc -v` · Expected: PASS.

- [ ] **Step 5: 커밋**

```bash
git add skills/setup-docs/scripts/migrate.py skills/setup-docs/scripts/test_link_oracle.py
git commit -m "✨ feat(migrate): per-file 인스턴스 회계 — content_oracle dedup 사각 보완 R7"
git push
```

---

### Task 5: `apply_moves` src 단언 + `prune_empty_dirs` (R3·R4, 스펙 §3·T8)

**Files:**
- Modify: `skills/setup-docs/scripts/migrate.py` (`apply_moves`에 src 존재 단언; 신규 `prune_empty_dirs`)
- Test: `skills/setup-docs/scripts/test_migrate.py`

**Interfaces:**
- Produces: `prune_empty_dirs(root) -> None` · `apply_moves` src 부재 시 `ValueError`

- [ ] **Step 1: 실패 테스트 — move_plan.src 부재 시 STOP(조용한 no-op 차단, R3)**

```python
def test_apply_moves_asserts_src_exists(tmp_path):
    import pytest
    _mk(tmp_path, "real.md", "# real\n")
    plan = [{"src": "ghost.md", "dest": "docs/ghost.md", "ops": ["move"], "impact": None}]  # 없는 src
    with pytest.raises(ValueError):
        migrate.apply_moves(tmp_path, plan)
```

- [ ] **Step 2: 실패 테스트 — 이동으로 빈 폴더는 제거(R4)**

```python
def test_prune_empty_dirs_removes_emptied_folder(tmp_path):
    _mk(tmp_path, "docs/old/x.md", "# X\n")
    (tmp_path / "docs/old/x.md").unlink()              # 폴더만 빈 채 남음
    migrate.prune_empty_dirs(tmp_path)
    assert not (tmp_path / "docs/old").exists()
    assert (tmp_path / "docs").exists()                # 비지 않은 상위는 보존
```

- [ ] **Step 3: 실패 확인** — 두 테스트 FAIL.

- [ ] **Step 4: 구현**

```python
# apply_moves 초입(root 계산 직후)에 추가:
    missing = [p["src"] for p in move_plan if not (root / p["src"]).exists()]
    if missing:
        raise ValueError(f"move_plan.src 부재(조용한 no-op 차단): {missing}")

def prune_empty_dirs(root):
    """이동으로 빈 디렉터리를 제거(R4: git 빈폴더 미커밋 → dir 링크 커밋후 파손 방지). 루트는 보존."""
    root = Path(root)
    for d in sorted((p for p in root.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        try:
            if d != root and not any(d.iterdir()):
                d.rmdir()
        except OSError:
            pass
```

- [ ] **Step 5: 그린 확인** — Run: `uv run --with pytest pytest test_migrate.py -k "src_exists or prune_empty" -v` · Expected: 2 PASS. 기존 apply_moves 테스트도 여전히 green(정상 plan은 src 존재).

- [ ] **Step 6: 커밋**

```bash
git add skills/setup-docs/scripts/migrate.py skills/setup-docs/scripts/test_migrate.py
git commit -m "✨ feat(migrate): apply_moves src 단언 + prune_empty_dirs — R3·R4"
git push
```

---

### Task 6: `verify_migration` 일원화 + `build_and_verify` 재배선 (스펙 §2)

**Files:**
- Modify: `skills/setup-docs/scripts/migrate.py`
- Test: `skills/setup-docs/scripts/test_migrate.py`

**Interfaces:**
- Consumes: `content_oracle.collect` · `classify_links` · `per_file_accounting` · `gate.analyze`
- Produces: `verify_migration(base_root, cur_root, move_plan) -> dict`; `build_and_verify`가 이를 호출(반환에 `new_broken`·`anchor_lost`·`per_file` 추가)

- [ ] **Step 1: 실패 테스트 — verify_migration이 clean 트리에서 전부 0**

```python
def test_verify_migration_clean_all_zero(tmp_path):
    base = tmp_path / "base"; cur = tmp_path / "cur"
    _mk(base, "CLAUDE.md", "# C\n@AGENTS.md\n"); _mk(base, "AGENTS.md", "# A\n")
    _mk(base, "docs/a.md", "# A\n본문.\n")
    _mk(cur, "CLAUDE.md", "# C\n@AGENTS.md\n"); _mk(cur, "AGENTS.md", "# A\n<!-- docsherpa:map -->\n- [a](docs/a.md)\n")
    _mk(cur, "docs/a.md", "# A\n본문.\n")
    r = migrate.verify_migration(base, cur, [])
    assert r["unaccounted"] == [] and r["new_broken"] == [] and r["anchor_lost"] == []
    assert r["orphan"] == 0 and r["per_file"] == []
```

- [ ] **Step 2: 실패 확인 → 구현**

```python
def verify_migration(base_root, cur_root, move_plan):
    """세 오라클 + per-file 일원화(Phase 1b·Phase 3 공유). 반환 dict."""
    base_keys = set(content_oracle.collect(base_root))
    cur_keys = set(content_oracle.collect(cur_root))
    links = classify_links(base_root, cur_root, move_plan)
    return {
        "unaccounted": sorted(base_keys - cur_keys),
        "new_broken": links["new_broken"],
        "preexisting_broken": links["preexisting_broken"],
        "anchor_lost": links["anchor_lost"],
        "orphan": len(gate.analyze(cur_root).orphans),
        "per_file": per_file_accounting(base_root, cur_root, move_plan),
    }
```

- [ ] **Step 3: `build_and_verify` 재배선** — 기존 검증부(content_oracle diff)를 `verify_migration` 호출로 교체. `register_in_indexes` → `register_all`. 기존 테스트(`test_build_and_verify_*`)가 반환 키 이름 바뀌면 그에 맞춰 갱신(예: `res["orphan"]`, 통과 판정 = `unaccounted==[] and new_broken==[] and anchor_lost==[] and orphan==0 and per_file==[]`).

```python
# build_and_verify 내부 검증부 교체:
        apply_moves(current, move_plan)
        prune_empty_dirs(current)
        scaffold.scaffold(current, plugin_root_dir=plugin_root)
        register_all(current)
        v = verify_migration(base, current, move_plan)
        return {"broken": len(v["new_broken"]), "orphan": v["orphan"],
                "unaccounted": v["unaccounted"], "new_broken": v["new_broken"],
                "anchor_lost": v["anchor_lost"], "per_file": v["per_file"]}
```

- [ ] **Step 4: 그린 확인** — Run: `uv run --with pytest pytest test_migrate.py -q` · Expected: 전부 PASS(기존 build_and_verify 테스트 갱신 포함).

- [ ] **Step 5: 커밋**

```bash
git add skills/setup-docs/scripts/migrate.py skills/setup-docs/scripts/test_migrate.py
git commit -m "✨ feat(migrate): verify_migration 오라클 일원화 + build_and_verify 재배선"
git push
```

---

### Task 7: `land_migration` — worktree 생애주기 (R3·R8, 스펙 §2·§3·T5·T6·T7)

**Files:**
- Modify: `skills/setup-docs/scripts/migrate.py`
- Test: `skills/setup-docs/scripts/test_land_migration.py` (신규 — 실제 git repo fixture)

**Interfaces:**
- Consumes: `apply_moves`·`prune_empty_dirs`·`scaffold`·`register_all`·`verify_migration` · `subprocess`(git worktree)
- Produces: `land_migration(repo, move_plan, head_sha, decisions=None, *, plugin_root=None) -> dict`

- [ ] **Step 1: 실패 테스트 — 통과 시 브랜치 생성·실 작업트리 무영향(T5)**

```python
# test_land_migration.py
import subprocess
from pathlib import Path
import migrate

def _git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True)

def _init_repo(root):
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q"); _git(root, "config", "user.email", "t@t"); _git(root, "config", "user.name", "t")
    (root / "CLAUDE.md").write_text("# C\n@AGENTS.md\n", encoding="utf-8")
    (root / "AGENTS.md").write_text("# A\n<!-- docsherpa:map -->\n- [map](docs/_map.md)\n", encoding="utf-8")
    (root / "docs").mkdir(); (root / "docs/_map.md").write_text("# Map\n<!-- docsherpa:index -->\n", encoding="utf-8")
    (root / "guide.md").write_text("# Guide\n가이드 세그먼트.\n", encoding="utf-8")
    _git(root, "add", "-A"); _git(root, "commit", "-q", "-m", "init")

def test_land_migration_success_creates_branch_no_worktree_impact(tmp_path):
    repo = tmp_path / "repo"; _init_repo(repo)
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    plan = [{"src": "guide.md", "dest": "docs/how-to/guide.md", "ops": ["move"], "impact": None}]
    before = sorted(p.name for p in repo.iterdir())
    res = migrate.land_migration(repo, plan, head)
    assert res["branch"].startswith("docsherpa/migrate-")
    assert res["new_broken"] == [] and res["unaccounted"] == []
    assert sorted(p.name for p in repo.iterdir()) == before      # 실 작업트리 무영향
    branches = _git(repo, "branch").stdout
    assert res["branch"] in branches                              # 브랜치는 남음
    # 브랜치에 이동 반영 확인
    show = _git(repo, "show", f"{res['branch']}:docs/how-to/guide.md").stdout
    assert "가이드 세그먼트" in show
```

- [ ] **Step 2: 실패 테스트 — HEAD 스테일이면 STOP(T7)**

```python
def test_land_migration_stale_head_stops(tmp_path):
    import pytest
    repo = tmp_path / "repo"; _init_repo(repo)
    stale = "0" * 40
    with pytest.raises(Exception):
        migrate.land_migration(repo, [], stale)
```

- [ ] **Step 3: 실패 테스트 — new_broken 주입 시 커밋 0·브랜치 0·worktree 0(T6·R8)**

```python
def test_land_migration_failure_leaves_zero_trace(tmp_path):
    import pytest
    repo = tmp_path / "repo"; _init_repo(repo)
    # a.md가 없는 b.md를 링크 → 이동 후에도 못 풂 → 하지만 base에서도 못 풂이면 preexisting.
    # new_broken 유발: 존재하는 타겟을 이동시키되 링크 재작성을 막을 순 없으니, 대신
    # verify를 강제 실패시키는 훅으로 흔적0만 검증(간이): 잘못된 dest 충돌로 apply STOP.
    (repo / "x.md").write_text("# X\n", encoding="utf-8")
    _git(repo, "add", "-A"); _git(repo, "commit", "-q", "-m", "x")
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    bad = [{"src": "x.md", "dest": "docs/_map.md", "ops": ["move"], "impact": None}]  # 기존 파일 충돌 → apply STOP
    with pytest.raises(Exception):
        migrate.land_migration(repo, bad, head)
    assert "docsherpa/migrate-" not in _git(repo, "branch").stdout    # 브랜치 0
    wl = _git(repo, "worktree", "list").stdout
    assert wl.count("\n") <= 1                                        # 메인 worktree만
```

- [ ] **Step 4: 실패 확인** — 3 테스트 FAIL (`land_migration` 없음).

- [ ] **Step 5: 구현 — `land_migration`**

```python
import subprocess

def _git_out(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True).stdout

def land_migration(repo, move_plan, head_sha, decisions=None, *, plugin_root=None):
    """검증된 계획을 worktree 격리로 실 브랜치에 랜딩(R3·R8). 통과 시에만 커밋, 실패/크래시 흔적0."""
    repo = Path(repo).resolve()
    if not (repo / ".git").exists():
        raise RuntimeError("git repo 아님 — land_migration은 git 전제(git init 선행).")
    cur_head = _git_out(repo, "rev-parse", "HEAD").strip()
    if cur_head != head_sha:
        raise RuntimeError(f"HEAD 스테일(계획 시 {head_sha[:8]} ≠ 현재 {cur_head[:8]}) — 재진단 필요.")
    stamp = head_sha[:8]
    branch = f"docsherpa/migrate-{stamp}"
    wt_cur = Path(tempfile.mkdtemp(prefix="docsherpa-land-"))
    wt_base = Path(tempfile.mkdtemp(prefix="docsherpa-base-"))
    committed = False
    try:
        subprocess.run(["git", "-C", str(repo), "worktree", "add", "-q", "-b", branch, str(wt_cur), head_sha], check=True)
        subprocess.run(["git", "-C", str(repo), "worktree", "add", "-q", "--detach", str(wt_base), head_sha], check=True)
        apply_moves(wt_cur, move_plan)
        prune_empty_dirs(wt_cur)
        scaffold.scaffold(wt_cur, plugin_root_dir=plugin_root)
        register_all(wt_cur)
        v = verify_migration(wt_base, wt_cur, move_plan)
        ok = (not v["unaccounted"] and not v["new_broken"] and not v["anchor_lost"]
              and v["orphan"] == 0 and not v["per_file"])
        if not ok:
            raise RuntimeError(f"랜딩 오라클 실패 → 흔적0 STOP: { {k: v[k] for k in ('unaccounted','new_broken','anchor_lost','orphan','per_file')} }")
        subprocess.run(["git", "-C", str(wt_cur), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(wt_cur), "commit", "-q", "-m",
                        f"📦 docs: docsherpa 마이그레이션(이동 {len(move_plan)}건, 검증트리=커밋트리)"], check=True)
        committed = True
        return {"branch": branch, "unaccounted": [], "new_broken": [], "anchor_lost": [],
                "preexisting_broken": v["preexisting_broken"], "moved": len(move_plan)}
    finally:
        subprocess.run(["git", "-C", str(repo), "worktree", "remove", "--force", str(wt_cur)],
                       capture_output=True)
        subprocess.run(["git", "-C", str(repo), "worktree", "remove", "--force", str(wt_base)],
                       capture_output=True)
        shutil.rmtree(wt_cur, ignore_errors=True); shutil.rmtree(wt_base, ignore_errors=True)
        if not committed:
            subprocess.run(["git", "-C", str(repo), "branch", "-D", branch], capture_output=True)  # 흔적0(R8)
```

- [ ] **Step 6: 그린 확인** — Run: `uv run --with pytest pytest test_land_migration.py -v` · Expected: 3 PASS.

- [ ] **Step 7: 전체 러너 + gate + 커밋**

```bash
uv run --with pytest pytest -q
cd /Users/jiohyeon/Desktop/private/docsherpa && python3 skills/setup-docs/scripts/gate.py . --require-markers
git add skills/setup-docs/scripts/migrate.py skills/setup-docs/scripts/test_land_migration.py
git commit -m "✨ feat(migrate): land_migration worktree 생애주기(HEAD핀·검증=커밋·finally 흔적0) — R3·R8"
git push
```

---

### Task 8: Phase 4 재진단 — `render_report` result 모드 (스펙 §6·T9)

**Files:**
- Modify: `skills/setup-docs/scripts/render_report.py` (result 모드 CSS 이연분)
- Test: 해당 스킬 러너의 render_report 테스트(대비·구조·인라인 style 0)

**Interfaces:**
- Consumes: `render_report(data, mode="result")` · doc-health 재채점 결과(before/after)

- [ ] **Step 1: result 모드 현황 확인** — Run: `grep -n "result" skills/setup-docs/scripts/render_report.py skills/*/scripts/render_report.py` · result 분기·CSS 존재 여부·이연분 식별.

- [ ] **Step 2: 실패 테스트 — result 모드 렌더가 before→after 대비 + AA + 인라인 style 0**

```python
def test_render_result_mode_before_after_and_quality():
    data = {"summary": {"grade_before": "F", "grade_after": "A"},
            "trees": {}, "preexisting_broken": [("docs/api.md", "src/x/")]}
    html = render_report.render(data, "result")
    assert "F" in html and "A" in html                 # before→after 대비
    assert "style=" not in html                          # 인라인 style 0(동결 품질)
    assert "머지 전" in html or "preexisting" in html.lower()   # 기존 broken 표면화
    # AA 대비 가드는 기존 게이트 테스트가 커버(토큰 쌍 검사)
```

- [ ] **Step 3: 실패 확인 → 구현** — result 모드 분기에 이연된 CSS/섹션(before→after 등급 카드·preexisting_broken 콜아웃) 추가. 동결 CSS·WCAG-AA·외부리소스 0·인라인 style 0 유지(기존 품질 게이트 통과).

- [ ] **Step 4: 그린 확인** — Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest -k render -q`(+ doc-health 러너의 render 테스트) · Expected: PASS, AA 가드 green.

- [ ] **Step 5: 커밋**

```bash
git add skills/setup-docs/scripts/render_report.py skills/setup-docs/scripts/test_render_report.py
git commit -m "✨ feat(render): result 모드 이연 CSS — before→after 등급 + preexisting 콜아웃 T9"
git push
```

---

### Task 9: SKILL.md Phase 3·4 배선 (산문)

**Files:**
- Modify: `skills/setup-docs/SKILL.md` (Phase 3·4 절차)

**Interfaces:**
- Consumes: `land_migration`·doc-health 재진단·`render_report(…, "result")`

- [ ] **Step 1: SKILL.md 현 Phase 0·1·2 절차 확인** — Run: `grep -n "Phase" skills/setup-docs/SKILL.md`

- [ ] **Step 2: Phase 3·4 산문 추가** — Phase 2(승인) 뒤에:
  - Phase 3: 승인된 move_plan + Phase 0 기록 HEAD sha로 `land_migration(repo, move_plan, head_sha)` 호출. **git 전제**(non-git STOP). 실패(오라클 미통과) 시 흔적0 STOP + 사용자에 실패 리포트. 성공 시 브랜치명·preexisting_broken 안내. **머지는 사용자**(우리가 안 함).
  - Phase 4: 랜딩 브랜치에 doc-health 재실행 → before/after로 `render_report(data, "result")` 아티팩트. preexisting_broken을 "머지 전 결정할 것"으로 표면화.
  - **배치 판단·legacy 통합·타입 vs 기능응집은 이 절차 밖**(§8 별도 트랙) 명시.

- [ ] **Step 3: 정합 확인 + gate** — Run: `cd /Users/jiohyeon/Desktop/private/docsherpa && python3 skills/setup-docs/scripts/gate.py . --require-markers` · Expected: PASS.

- [ ] **Step 4: 커밋**

```bash
git add skills/setup-docs/SKILL.md
git commit -m "📝 docs(skill): setup-docs Phase 3·4 배선(land_migration·재진단·result 아티팩트)"
git push
```

---

## e2e 롤아웃 (전 태스크 후)

- [ ] **합성 fixture e2e** — 제자리 docs + legacy + 스테일 코드링크 + 이동-소스 링크 + 앵커링크 + 빈-폴더유발을 담은 git fixture에서 `land_migration` end-to-end GREEN(브랜치 산출·세 오라클 0·per_file ok).
- [ ] **vd-front 실 dogfood** — `/Users/jiohyeon/Desktop/projects/vd-front`(feat/VDS-892 HEAD)에 Phase 0~4 실제 적용. `docsherpa/migrate-<sha>` 브랜치 산출 → **검토·머지는 사용자**. 미추적 `CONTEXT.md`는 스코프 밖(무영향 확인). preexisting_broken 리포트 확인.
- [ ] **FINDINGS.md 갱신** — 증분 4 완료 블록(랜딩 라이브·오라클 확장·vd-front dogfood 결과) 기록.
- [ ] **whole-branch 리뷰** — `/code-review` + `/codex`(위험·핵심) → 5 정체성 불변식 HOLD 확인 → PR(마지막 한 번에).

## Self-Review 체크

- **스펙 커버리지:** R1(Task2)·R2(Task3)·R3(Task5·7)·R4(Task5)·R5·R6(Task1)·R7(Task4)·R8(Task7)·R9(스펙/design 이미 반영). T1~T9 전부 태스크 대응. ✓
- **타입 정합:** `classify_links`/`per_file_accounting`/`verify_migration`/`register_all`/`land_migration` 시그니처가 데이터 계약과 태스크 간 일치. ✓
- **placeholder:** 각 스텝에 실제 테스트·구현 코드 포함(구현 세부는 RED 테스트가 강제). ⚠️ Task8 result 모드는 기존 render_report 구조 확인 후 이연분 채움(Step 1에서 현황 파악).
