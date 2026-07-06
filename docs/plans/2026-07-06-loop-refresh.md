# Loop Refresh (설치본 자동 동기화) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 플러그인이 새 버전으로 올라가면 각 target repo의 **설치본 doc-reconcile SKILL**을 안전하게 자동 갱신하는 결정론 기계(`refresh.py`)를 만든다 — 다운그레이드 차단·로컬 편집 보존·이식성, **무프롬프트 커밋 0**.

**Architecture:** 설치본 파일 끝 스탬프를 `<!-- docsherpa-scaffold: v<ver> sha=<12hex> -->` 로 확장해 **버전+해시를 파일 자체에 담는다**(별도 sidecar 파일 없음). `refresh_loop(repo_root, plugin_root)`가 provenance→스탬프파싱→version_gt→해시일치(로컬편집 가드)를 거쳐 **원자적으로 교체하고 새 스탬프를 찍되 커밋은 안 한다**. 트리거는 `/docsherpa:doc-reconcile` step0(에이전트 호출, plugin_root 확보); 에이전트가 끝 요약에 결과를 알린다. 릴리스 서명(오염 차단)은 M5로 유보.

**Tech Stack:** Python 3 stdlib only(`hashlib`·`re`·`json`·`pathlib`), pytest. 새 의존성 0.

## Global Constraints

- **stdlib only.** 새 서드파티 의존성 금지.
- **무프롬프트 커밋 0:** `refresh_loop`은 파일만 쓰고 **git 커밋을 하지 않는다**(트리거가 에이전트 호출이라 에이전트가 끝 요약으로 사용자에게 알림 — "보조 not 주인"). ADR 0012 F15 disposition을 이 방향으로 정제.
- **로컬 편집 보존:** 설치본의 canonical_hash가 스탬프에 기록된 sha와 다르면(사용자 편집) → **skip+stuck**, 안 덮음. sha 없는 구-스탬프도 검증 불가 → stuck.
- **다운그레이드 차단:** `version_gt(플러그인, 설치본)` False면 no-op.
- **이식성(provenance):** plugin_root가 target **밖** + `plugin.json` name==`docsherpa` 여야 refresh 정당. 아니면 no-op(조용). 설치본만 있는 repo(플러그인 없음)는 provenance 실패로 자동 no-op.
- **원자적 쓰기:** temp 파일 write 후 `replace`(부분 쓰기 방지).
- **스탬프 정본:** 마커 문자열 `<!-- docsherpa-scaffold: v… -->`. canonical_hash = utf-8-sig BOM 제거→CRLF/CR→LF→스탬프 제거→trailing 개행 제거→sha256[:12].
- **범위 밖:** 릴리스 서명(step4, OQ-d/M5) · Slice C sidecar home · prime/settings refresh(doc-reconcile SKILL만 동기) · docsherpa 자기 repo의 두-사본 동기(plugin==target이라 provenance no-op — 별도 관심사).
- **저작 함정(F16):** 링크 문법 `](경로)` 예시는 펜스 안에만.

---

## File Structure

- **Create `skills/setup-docs/scripts/refresh.py`** — 순수 헬퍼(`canonical_hash`·`strip_stamp`·`parse_stamp`·`make_stamp`·`version_gt`·`verify_plugin_provenance`) + `refresh_loop(repo_root, plugin_root) -> dict`. loop 버전 동기의 단일 소스.
- **Create `skills/setup-docs/scripts/test_refresh.py`** — refresh 단위·통합 테스트.
- **Modify `skills/setup-docs/scripts/scaffold.py`** — `install_loop_files`의 스탬프에 sha 추가(`refresh.make_stamp`·`refresh.canonical_hash` 사용).
- **Modify `skills/doc-reconcile/SKILL.md`·`.claude/skills/doc-reconcile/SKILL.md`** — step0 refresh 트리거 + 끝 요약에 갱신 결과 산문(정본+설치본 동기).
- **Modify `docs/decisions/0012-self-growth-open-issues.md`** — F15 disposition을 "write-and-notify(무프롬프트 커밋 0)"로 정제.
- **Modify `docs/plans/README.md`** — 이 계획 인덱스 등록.

---

### Task 1: `refresh.py` 순수 헬퍼

**Files:**
- Create: `skills/setup-docs/scripts/refresh.py`
- Test: `skills/setup-docs/scripts/test_refresh.py`

**Interfaces:**
- Produces: `canonical_hash(text) -> str`(12 hex), `strip_stamp(text) -> str`, `parse_stamp(text) -> tuple[str, str|None] | None`, `make_stamp(version, sha) -> str`, `version_gt(a, b) -> bool`, `verify_plugin_provenance(plugin_root, target) -> bool`

- [ ] **Step 1: 실패하는 테스트 작성**

`skills/setup-docs/scripts/test_refresh.py`:

```python
import json
from pathlib import Path

import refresh


def test_make_and_parse_stamp_roundtrip():
    s = refresh.make_stamp("0.0.2", "abc123def456")
    assert "docsherpa-scaffold: v0.0.2 sha=abc123def456" in s
    assert refresh.parse_stamp("body\n" + s) == ("0.0.2", "abc123def456")


def test_parse_old_stamp_without_sha():
    assert refresh.parse_stamp("x\n<!-- docsherpa-scaffold: v0.0.1 -->\n") == ("0.0.1", None)


def test_parse_stamp_none_when_absent():
    assert refresh.parse_stamp("no stamp here\n") is None


def test_strip_stamp_removes_trailing_stamp():
    body = "line1\nline2\n"
    text = body + refresh.make_stamp("0.0.2", "abc123def456")
    assert refresh.strip_stamp(text).rstrip("\n") == "line1\nline2"


def test_canonical_hash_ignores_stamp_and_crlf():
    a = "line1\nline2\n" + refresh.make_stamp("0.0.1", "old")
    b = "line1\r\nline2" + refresh.make_stamp("0.0.9", "different")
    assert refresh.canonical_hash(a) == refresh.canonical_hash(b)   # 스탬프·CRLF 무관


def test_version_gt_int_tuple():
    assert refresh.version_gt("0.0.2", "0.0.1") is True
    assert refresh.version_gt("0.1.0", "0.0.9") is True
    assert refresh.version_gt("0.0.1", "0.0.1") is False
    assert refresh.version_gt("0.0.1", "0.0.2") is False


def test_provenance_true_when_plugin_outside_and_named(tmp_path):
    plugin = tmp_path / "plugin"
    (plugin / ".claude-plugin").mkdir(parents=True)
    (plugin / ".claude-plugin" / "plugin.json").write_text('{"name":"docsherpa"}', encoding="utf-8")
    target = tmp_path / "repo"
    target.mkdir()
    assert refresh.verify_plugin_provenance(plugin, target) is True


def test_provenance_false_when_plugin_inside_target(tmp_path):
    # docsherpa 자기 repo(plugin==target) or 설치본만 있는 경우 → refresh 부정당
    target = tmp_path / "repo"
    (target / ".claude-plugin").mkdir(parents=True)
    (target / ".claude-plugin" / "plugin.json").write_text('{"name":"docsherpa"}', encoding="utf-8")
    assert refresh.verify_plugin_provenance(target, target) is False


def test_provenance_false_when_name_mismatch(tmp_path):
    plugin = tmp_path / "plugin"
    (plugin / ".claude-plugin").mkdir(parents=True)
    (plugin / ".claude-plugin" / "plugin.json").write_text('{"name":"evil"}', encoding="utf-8")
    target = tmp_path / "repo"
    target.mkdir()
    assert refresh.verify_plugin_provenance(plugin, target) is False
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_refresh.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'refresh'`

- [ ] **Step 3: 최소 구현 작성**

`skills/setup-docs/scripts/refresh.py`:

```python
"""doc-reconcile 설치본의 버전 동기(up-only refresh) — 결정론 기계.

플러그인 정본이 새 버전이면 target repo의 설치본을 안전하게 교체한다:
다운그레이드 차단·로컬 편집 보존·이식성. 커밋은 하지 않는다(에이전트가 알림).
상태는 파일 끝 스탬프(<!-- docsherpa-scaffold: v<ver> sha=<12hex> -->)에 담는다.
"""
import hashlib
import json
import re
from pathlib import Path

_STAMP_RE = re.compile(r"\s*<!-- docsherpa-scaffold:.*?-->\s*\Z")
_PARSE_RE = re.compile(r"<!-- docsherpa-scaffold: v(\S+)(?: sha=([0-9a-f]+))? -->")


def strip_stamp(text):
    """파일 끝 스캐폴드 스탬프(있으면)를 제거."""
    return _STAMP_RE.sub("", text)


def canonical_hash(text):
    """스탬프 제거 + 정규화(BOM·CRLF·trailing개행) 후 sha256[:12]. 로컬편집·버전비교 기준."""
    body = strip_stamp(text).lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]


def parse_stamp(text):
    """스탬프에서 (version, sha|None). 없으면 None. 구-스탬프(sha 없음)도 지원."""
    m = _PARSE_RE.search(text)
    if not m:
        return None
    return (m.group(1), m.group(2))


def make_stamp(version, sha):
    return f"\n<!-- docsherpa-scaffold: v{version} sha={sha} -->\n"


def version_gt(a, b):
    """a > b (점 구분 버전, int-튜플 비교; 비-정수 요소는 0)."""
    def parts(v):
        out = []
        for p in str(v).split("."):
            try:
                out.append(int(p))
            except ValueError:
                out.append(0)
        return tuple(out)
    return parts(a) > parts(b)


def verify_plugin_provenance(plugin_root, target):
    """plugin_root가 target 밖 + plugin.json name==docsherpa 여야 refresh 정당."""
    plug = Path(plugin_root).resolve()
    tgt = Path(target).resolve()
    if plug == tgt or tgt in plug.parents:      # plugin이 target 안 → 부정당
        return False
    pj = plug / ".claude-plugin" / "plugin.json"
    if not pj.is_file():
        return False
    try:
        return json.loads(pj.read_text(encoding="utf-8")).get("name") == "docsherpa"
    except (ValueError, OSError):
        return False
```

- [ ] **Step 4: 테스트가 통과하는지 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_refresh.py -q`
Expected: PASS (10 passed)

- [ ] **Step 5: 무-회귀 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`
Expected: all passed(순수 추가).

- [ ] **Step 6: 커밋**

```bash
git add skills/setup-docs/scripts/refresh.py skills/setup-docs/scripts/test_refresh.py
git commit -m "feat(refresh): 스탬프 해시·버전·provenance 순수 헬퍼 (loop-refresh T1)"
```

---

### Task 2: `install_loop_files` 스탬프에 sha 추가

**Files:**
- Modify: `skills/setup-docs/scripts/scaffold.py`
- Test: `skills/setup-docs/scripts/test_scaffold.py`

**Interfaces:**
- Consumes: `refresh.make_stamp`·`refresh.canonical_hash` (Task 1)
- Produces: 설치본 SKILL 끝 스탬프가 `sha=<12hex>` 포함 → refresh가 로컬편집을 검증 가능

- [ ] **Step 1: 실패하는 테스트 작성**

`skills/setup-docs/scripts/test_scaffold.py` 끝에 추가(파일 상단에 `import scaffold` 존재):

```python
def test_install_loop_stamp_has_sha(tmp_path):
    import refresh
    scaffold.install_loop_files(tmp_path, scaffold.plugin_root())
    installed = (tmp_path / ".claude/skills/doc-reconcile/SKILL.md").read_text(encoding="utf-8")
    parsed = refresh.parse_stamp(installed)
    assert parsed is not None
    version, sha = parsed
    assert sha is not None                                  # 해시 기록됨
    assert refresh.canonical_hash(installed) == sha         # 기록된 sha == 실제 내용 해시
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_scaffold.py::test_install_loop_stamp_has_sha -q`
Expected: FAIL — 현재 스탬프는 `v<version>`만, sha 없음 → `sha is not None` assert 깨짐

- [ ] **Step 3: `install_loop_files` 스탬프 교체**

`skills/setup-docs/scripts/scaffold.py` 상단 import에 `import refresh` 추가(기존 `from ...` 옆). `install_loop_files`의 스탬프 생성부를 교체:

```python
# 변경 전:
#         version = json.loads(
#             (plug / ".claude-plugin" / "plugin.json").read_text()).get("version", "0")
#         stamp = f"\n<!-- docsherpa-scaffold: v{version} -->\n"
#         dr_dst.write_text(dr_src.read_text(encoding="utf-8") + stamp, encoding="utf-8")
# 변경 후:
        version = json.loads(
            (plug / ".claude-plugin" / "plugin.json").read_text()).get("version", "0")
        body = dr_src.read_text(encoding="utf-8")
        stamp = refresh.make_stamp(version, refresh.canonical_hash(body))
        dr_dst.write_text(body + stamp, encoding="utf-8")
```

- [ ] **Step 4: 테스트가 통과하는지 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_scaffold.py::test_install_loop_stamp_has_sha -q`
Expected: PASS

- [ ] **Step 5: 전체 무-회귀 + 이 레포 gate**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`
Expected: all passed(기존 스탬프 assert가 있으면 새 포맷에 맞게 통과 — 없으면 무영향).

Run: `python3 skills/setup-docs/scripts/gate.py . && python3 skills/setup-docs/scripts/gate.py . --require-markers`
Expected: 둘 다 PASS.

- [ ] **Step 6: 커밋**

```bash
git add skills/setup-docs/scripts/scaffold.py skills/setup-docs/scripts/test_scaffold.py
git commit -m "feat(scaffold): install 스탬프에 canonical_hash 기록 — refresh 로컬편집 검증용 (loop-refresh T2)"
```

---

### Task 3: `refresh_loop` — up-only refresh 기계

**Files:**
- Modify: `skills/setup-docs/scripts/refresh.py`
- Test: `skills/setup-docs/scripts/test_refresh.py`

**Interfaces:**
- Consumes: 모든 Task 1 헬퍼, `refresh.make_stamp`
- Produces: `refresh_loop(repo_root, plugin_root) -> dict` — `{"action": "refreshed"|"stuck"|"noop", "reason": str, "from": str?, "to": str?}`. 파일만 쓰고 커밋 안 함.

- [ ] **Step 1: 실패하는 테스트 작성**

`skills/setup-docs/scripts/test_refresh.py`에 추가:

```python
def _fake_plugin(tmp_path, version, skill_body):
    plugin = tmp_path / "plugin"
    (plugin / ".claude-plugin").mkdir(parents=True)
    (plugin / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "docsherpa", "version": version}), encoding="utf-8")
    dr = plugin / "skills" / "doc-reconcile"
    dr.mkdir(parents=True)
    (dr / "SKILL.md").write_text(skill_body, encoding="utf-8")
    return plugin


def _install(repo, body, version, sha):
    dst = repo / ".claude" / "skills" / "doc-reconcile" / "SKILL.md"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(body + refresh.make_stamp(version, sha), encoding="utf-8")
    return dst


def test_refresh_upgrades_installed_to_new_version(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    old = "old skill v1 body\n"
    _install(repo, old, "0.0.1", refresh.canonical_hash(old))
    new = "NEW skill v2 body\n"
    plugin = _fake_plugin(tmp_path, "0.0.2", new)
    res = refresh.refresh_loop(repo, plugin)
    assert res["action"] == "refreshed" and res["to"] == "0.0.2"
    installed = (repo / ".claude/skills/doc-reconcile/SKILL.md").read_text(encoding="utf-8")
    assert "NEW skill v2 body" in installed
    assert refresh.parse_stamp(installed) == ("0.0.2", refresh.canonical_hash(new))


def test_refresh_noop_on_downgrade(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    body = "current body\n"
    _install(repo, body, "0.0.5", refresh.canonical_hash(body))
    plugin = _fake_plugin(tmp_path, "0.0.2", "older body\n")
    assert refresh.refresh_loop(repo, plugin)["action"] == "noop"
    assert "current body" in (repo / ".claude/skills/doc-reconcile/SKILL.md").read_text(encoding="utf-8")


def test_refresh_noop_on_same_version(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    body = "body\n"
    _install(repo, body, "0.0.2", refresh.canonical_hash(body))
    plugin = _fake_plugin(tmp_path, "0.0.2", "different body\n")
    assert refresh.refresh_loop(repo, plugin)["action"] == "noop"


def test_refresh_stuck_when_locally_edited(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    body = "original body\n"
    # 설치본을 사용자가 편집: 기록된 sha는 original인데 내용은 바뀜
    _install(repo, "USER EDITED body\n", "0.0.1", refresh.canonical_hash(body))
    plugin = _fake_plugin(tmp_path, "0.0.2", "plugin new body\n")
    res = refresh.refresh_loop(repo, plugin)
    assert res["action"] == "stuck"
    assert "USER EDITED body" in (repo / ".claude/skills/doc-reconcile/SKILL.md").read_text(encoding="utf-8")


def test_refresh_noop_when_plugin_inside_target(tmp_path):
    # 설치본만 있는 repo(플러그인 없음) 시뮬 — plugin_root를 repo 자신으로 줌 → provenance no-op
    repo = tmp_path / "repo"; repo.mkdir()
    (repo / ".claude-plugin").mkdir()
    (repo / ".claude-plugin" / "plugin.json").write_text('{"name":"docsherpa","version":"9.9.9"}', encoding="utf-8")
    body = "body\n"
    _install(repo, body, "0.0.1", refresh.canonical_hash(body))
    assert refresh.refresh_loop(repo, repo)["action"] == "noop"


def test_refresh_stuck_on_old_stamp_without_sha(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    dst = repo / ".claude" / "skills" / "doc-reconcile" / "SKILL.md"
    dst.parent.mkdir(parents=True)
    dst.write_text("body\n<!-- docsherpa-scaffold: v0.0.1 -->\n", encoding="utf-8")  # sha 없음
    plugin = _fake_plugin(tmp_path, "0.0.2", "new\n")
    assert refresh.refresh_loop(repo, plugin)["action"] == "stuck"
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_refresh.py -k refresh_ -q`
Expected: FAIL — `AttributeError: module 'refresh' has no attribute 'refresh_loop'`

- [ ] **Step 3: `refresh_loop` 구현**

`skills/setup-docs/scripts/refresh.py` 끝에 추가:

```python
def refresh_loop(repo_root, plugin_root):
    """설치본 doc-reconcile을 플러그인 새 버전으로 안전 갱신. 파일만 쓰고 커밋 안 함.

    반환 dict: action=refreshed|stuck|noop, reason, (from/to 버전).
    - provenance 실패/파일부재/스탬프없음/다운그레이드 → noop
    - 로컬 편집(해시 불일치·sha 없음) → stuck(안 덮음)
    - 상위버전 + 미편집 → 원자적 교체 + 새 스탬프
    """
    root = Path(repo_root)
    plug = Path(plugin_root)
    if not verify_plugin_provenance(plug, root):
        return {"action": "noop", "reason": "provenance"}
    installed = root / ".claude" / "skills" / "doc-reconcile" / "SKILL.md"
    canonical = plug / "skills" / "doc-reconcile" / "SKILL.md"
    pj = plug / ".claude-plugin" / "plugin.json"
    if not (installed.is_file() and canonical.is_file() and pj.is_file()):
        return {"action": "noop", "reason": "missing"}
    text = installed.read_text(encoding="utf-8")
    parsed = parse_stamp(text)
    if parsed is None:
        return {"action": "noop", "reason": "no-stamp"}
    ver_e, sha_e = parsed
    ver_p = json.loads(pj.read_text(encoding="utf-8")).get("version", "0")
    if not version_gt(ver_p, ver_e):
        return {"action": "noop", "reason": "not-newer", "from": ver_e, "to": ver_p}
    if sha_e is None or canonical_hash(text) != sha_e:
        return {"action": "stuck", "reason": "local-edit", "from": ver_e}
    new_body = canonical.read_text(encoding="utf-8")
    new_text = new_body + make_stamp(ver_p, canonical_hash(new_body))
    tmp = installed.with_name(installed.name + ".tmp")
    tmp.write_text(new_text, encoding="utf-8")
    tmp.replace(installed)
    return {"action": "refreshed", "reason": "up", "from": ver_e, "to": ver_p}
```

- [ ] **Step 4: 테스트가 통과하는지 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_refresh.py -q`
Expected: PASS (전체 refresh 테스트).

- [ ] **Step 5: 무-회귀 + gate**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`
Expected: all passed.

Run: `python3 skills/setup-docs/scripts/gate.py . && python3 skills/setup-docs/scripts/gate.py . --require-markers`
Expected: 둘 다 PASS.

- [ ] **Step 6: 커밋**

```bash
git add skills/setup-docs/scripts/refresh.py skills/setup-docs/scripts/test_refresh.py
git commit -m "feat(refresh): refresh_loop 업-온리 안전 갱신(다운그레이드 차단·로컬편집 보존) (loop-refresh T3)"
```

---

### Task 4: doc-reconcile 트리거 산문 + F15 정제 + 인덱스

**Files:**
- Modify: `skills/doc-reconcile/SKILL.md`, `.claude/skills/doc-reconcile/SKILL.md`
- Modify: `docs/decisions/0012-self-growth-open-issues.md`
- Modify: `docs/plans/README.md`

**Interfaces:**
- Consumes: `refresh.refresh_loop` (Task 3)

- [ ] **Step 1: doc-reconcile 산문에 step0 refresh 트리거 추가**

`skills/doc-reconcile/SKILL.md`의 `## 절차` 헤딩(그 아래 `### 1. 변경 수집` 앞)에 step0 섹션을 삽입. 정본과 `.claude/skills/doc-reconcile/SKILL.md` **둘 다 동일 편집**:

`### 1. 변경 수집 (결정론적)` 바로 위에 삽입:

```markdown
### 0. 설치본 refresh (플러그인 실행 시만 — 결정론)

`/docsherpa:doc-reconcile`로 실행돼 plugin_root를 확보할 수 있을 때, 시작 전 설치본 갱신을 시도한다:
`python3 <plugin>/skills/setup-docs/scripts/refresh.py`의 `refresh_loop(repo_root, plugin_root)`를
호출(또는 동등 조회). 이 기계는 다운그레이드를 차단하고, 사용자가 설치본을 직접 고쳤으면 안 덮으며
(stuck), provenance 실패(설치본만 있는 repo) 시 조용히 no-op한다. **커밋하지 않는다** — 결과는
아래 끝 요약으로 사용자에게 알린다. plugin_root가 없으면(설치본에서 실행) 이 단계는 건너뛴다.
```

- [ ] **Step 2: 끝 요약에 refresh 결과 산문 추가**

두 사본 모두, `## 절차`의 마지막(`### 6. 도달성 closeout` 뒤, `## 손대지 말 것` 앞)에 삽입:

```markdown
### 7. 끝 요약 (refresh 결과 포함)

실행 끝에 사용자에게 요약한다: 📝갱신 N · 🆕신설 M · ⚙️refresh(했으면 "설치본 vX→vY 갱신됨 —
`git diff .claude/` 확인 후 커밋" / stuck이면 "설치본이 로컬 편집돼 자동갱신 skip — 수동 확인 필요").
무변경이면 `Docs-Impact: none`.
```

- [ ] **Step 3: 두 사본 동기 확인**

Run: `diff <(grep -v "docsherpa-scaffold: v" skills/doc-reconcile/SKILL.md) <(grep -v "docsherpa-scaffold: v" .claude/skills/doc-reconcile/SKILL.md)`
Expected: `<!-- docsherpa:anchors -->` 블록만 차이(정본=generic / 설치본=docsherpa 특화). step0·끝요약 산문은 양쪽 동일.

- [ ] **Step 4: ADR 0012 F15 disposition 정제**

`docs/decisions/0012-self-growth-open-issues.md`의 F15 줄을 교체:

```markdown
# 변경 전:
# - **F15 (자동 커밋 posture):** refresh(§3.2) 구축 시 무프롬프트 커밋은 **clean-tree 조건 + 별도 툴링
#   커밋**으로 스코프해 "보조 not 주인" 원칙을 지킨다.
# 변경 후:
- **F15 (자동 커밋 posture) — 구축됨(loop-refresh):** `refresh_loop`은 **커밋을 하지 않는다**(파일만
  갱신, 트리거가 에이전트 호출이라 에이전트가 끝 요약으로 알림). 무프롬프트 커밋 0으로 "보조 not 주인"을
  지킨다 — 애초 기록한 "clean-tree+별도 커밋"보다 강한 posture로 정제.
```

- [ ] **Step 5: 이 계획 인덱스 등록**

`docs/plans/README.md`의 "재설계 계획" 섹션에 한 줄 추가:

```markdown
- [2026-07-06-loop-refresh.md](2026-07-06-loop-refresh.md) — 설치본 doc-reconcile 자동 동기(up-only refresh, 스탬프 해시·provenance·로컬편집 보존·무프롬프트 커밋 0).
```

- [ ] **Step 6: gate + 전체 테스트 확인**

Run: `python3 skills/setup-docs/scripts/gate.py . && python3 skills/setup-docs/scripts/gate.py . --require-markers`
Expected: 둘 다 `PASS broken=0 orphan=0`(계획 인덱스 등록으로 orphan 0), 이식성 가드 대상 아님 확인은 아래.

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_doc_reconcile_portable.py -q`
Expected: PASS(정본 doc-reconcile에 step0 산문 추가가 도메인 리터럴 누출 아님 — `<plugin>`·`refresh_loop` 등 generic).

- [ ] **Step 7: 커밋**

```bash
git add skills/doc-reconcile/SKILL.md .claude/skills/doc-reconcile/SKILL.md docs/decisions/0012-self-growth-open-issues.md docs/plans/README.md
git commit -m "feat(doc-reconcile): step0 refresh 트리거 + 끝요약, F15 write-and-notify 정제 (loop-refresh T4)"
```

---

## Self-Review

- **Spec coverage:** 승인 설계 전부 = Task 1(스탬프/해시/버전/provenance 헬퍼) + Task 2(install 스탬프 sha) + Task 3(refresh_loop 업-온리·다운그레이드 차단·로컬편집 stuck·provenance 이식성·무커밋) + Task 4(트리거 산문·끝요약·F15 정제·인덱스). 릴리스 서명(M5)·Slice C·prime refresh·docsherpa 자기 두-사본 동기는 명시적 범위 밖.
- **무-회귀:** Task 2 Step5·Task 3 Step5·Task 4 Step6이 이 레포 gate 두 모드 PASS·전체 테스트 green을 못박음. 새 파일은 순수 추가라 기존 코드 무변경(install 스탬프 포맷만 확장).
- **타입 일관성:** `canonical_hash(text)->str`·`parse_stamp(text)->tuple|None`·`make_stamp(version,sha)->str`·`version_gt(a,b)->bool`·`verify_plugin_provenance(plugin_root,target)->bool`·`refresh_loop(repo_root,plugin_root)->dict` 시그니처가 Task 1 정의·Task 2/3 소비에서 일치. 스탬프 문자열 포맷(`v<ver> sha=<hex>`)이 make/parse/install에서 일치.
- **Placeholder 스캔:** 없음 — 모든 스텝에 실제 코드/명령/기대출력.
