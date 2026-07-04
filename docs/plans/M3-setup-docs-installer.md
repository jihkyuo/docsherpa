# M3 — setup-docs 설치자 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **단, 이 플랜은 Task 5(SKILL.md 산문 편집)가 섞여 있어 인라인 실행을 권장한다** — 산문 편집은 subagent에 위임하지 않는다.

**Goal:** `setup-docs`를 "문서 골격 생성기"에서 "**성장 루프 설치자**"로 확장한다 — 마커 삽입 + doc-reconcile/prime/훅 스캐폴드 + `settings.json` 병합 + 기존 CLAUDE.md 안전 주입 + Phase 0 loop-presence 흡수. 데이터-유실 위험이 있는 3개 기계적 조각만 테스트된 코드로, 나머지는 SKILL.md 산문으로.

**Architecture:** 위험한 것만 코드로 격리한다. CLAUDE.md 주입(기존 파일 파괴 위험)·settings 병합(JSONC 클로버 위험)·마커 계약(drift 위험) = 테스트된 함수. 마커 *삽입*·스캐폴드 오케스트레이션·opt-in/dry-run 흐름 = SKILL.md 산문(에이전트가 실행, 게이트가 검증). "설치자다"의 정의는 산문이 아니라 **단위 테스트 3종 + 마커 게이트 GREEN**으로 고정.

**Tech Stack:** Claude Code 플러그인, Python 3(`uv run --with pytest pytest`), git. 산문 스킬 방법론은 유닛테스트 불가 → 검증은 기계적 함수 단위테스트 + 게이트.

## Global Constraints

- docsherpa repo 루트: `~/Desktop/private/docsherpa`. scripts 디렉터리: `skills/setup-docs/scripts/`.
- 테스트 실행: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q` (repo에 venv 안 만듦 — M0 확립). **현재 18 passed를 회귀 없이 유지 + 신규 추가.**
- RED-first: 동작 코드는 실패 테스트 먼저 → GREEN (spec §10, 전역 4원칙 #4).
- 커밋은 논리 단위마다. `git add -A` 금지 — 의도한 파일만 스테이지. 커밋마다 `git push`(origin/main).
- 마커 계약(spec D8): `<!-- docsherpa:routing -->` · `<!-- docsherpa:index -->` (M0 `check_markers.py`와 동일 문자열).
- settings 병합은 반드시 **`.claude/settings.json`**(공유·커밋). `settings.local.json` 금지(spec D2).
- **정본(플러그인 안) doc-reconcile은 절대 프로젝트 리터럴을 담지 않는다** — M1 가드(`test_doc_reconcile_portable.py`)가 계속 GREEN이어야 한다.
- 비대화형(headless/CI)이면 스캐폴드는 기본 **dry-run**(계획만 출력, 쓰기 없음). 실제 쓰기는 명시 승인 필요(spec §7.1).

---

### Task 1: CLAUDE.md 안전 주입 (code, RED-first)

기존 CLAUDE.md를 파괴하지 않고 `@AGENTS.md` import를 안전하게 넣는다. spec §7.3 + §14가 요구하는 엣지(없음/이미 import/다른 내용/BOM/frontmatter)를 테스트로 고정한다. gate.py 루트 탐색이 이 주입 결과에 의존하므로(§7.3) 결정론적 코드로 격리.

**Files:**
- Create: `skills/setup-docs/scripts/inject_claude_md.py`
- Test: `skills/setup-docs/scripts/test_inject_claude_md.py`

**Interfaces:**
- Produces:
  - `inject_claude_md(text: str | None) -> tuple[str, bool]` — `text=None`은 CLAUDE.md 없음. 반환 `(new_text, changed)`. 이미 `@AGENTS.md`(또는 `@./AGENTS.md`)를 import하면 `(원본, False)`.
  - `inject_claude_md_file(repo_root) -> bool` — 파일 I/O 래퍼. `repo_root/CLAUDE.md`를 읽어(없으면 None) 주입, 변경 시에만 write. `changed?` 반환.
- Consumes: 없음.

- [ ] **Step 1: 실패 테스트 작성 — 6개 엣지**

`skills/setup-docs/scripts/test_inject_claude_md.py`:
```python
from inject_claude_md import inject_claude_md, inject_claude_md_file


def test_no_file_creates_import():
    out, changed = inject_claude_md(None)
    assert out == "@AGENTS.md\n" and changed is True


def test_already_imports_left_untouched():
    src = "@AGENTS.md\n"
    out, changed = inject_claude_md(src)
    assert out == src and changed is False


def test_import_notation_variant_detected():
    src = "@./AGENTS.md\n"           # ./ 표기 변형도 이미-import로 인식
    out, changed = inject_claude_md(src)
    assert out == src and changed is False


def test_other_content_prepends_import():
    src = "# My Project\nsome rules\n"
    out, changed = inject_claude_md(src)
    assert out == "@AGENTS.md\n# My Project\nsome rules\n" and changed is True


def test_bom_preserved_import_after_bom():
    src = "﻿# My Project\n"      # BOM은 유지하되 import는 BOM 뒤에
    out, changed = inject_claude_md(src)
    assert out == "﻿@AGENTS.md\n# My Project\n" and changed is True


def test_frontmatter_import_after_closing_fence():
    src = "---\ntitle: x\n---\n# Body\n"
    out, changed = inject_claude_md(src)
    assert out == "---\ntitle: x\n---\n@AGENTS.md\n# Body\n" and changed is True
```

- [ ] **Step 2: 실패 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_inject_claude_md.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'inject_claude_md'`.

- [ ] **Step 3: 구현**

`skills/setup-docs/scripts/inject_claude_md.py`:
```python
"""기존 CLAUDE.md를 파괴하지 않고 @AGENTS.md import를 안전 주입.

spec §7.3 + §14 엣지: 없음(생성) / 이미 import(무변경) / 다른 내용(prepend) /
BOM(뒤에 삽입) / frontmatter(닫는 --- 뒤에 삽입). gate.py 루트 탐색이 결과에 의존.
"""
import re
from pathlib import Path

IMPORT_LINE = "@AGENTS.md"
# @AGENTS.md · @./AGENTS.md 등 표기 변형을 이미-import로 인식 (경로 앞엔 줄머리/공백)
_IMPORT_RE = re.compile(r"(?:^|\s)@\.?/?AGENTS\.md\b")


def _frontmatter_end(body: str):
    """body가 --- frontmatter로 시작하면 닫는 --- 라인 끝(문자 인덱스) 반환, 아니면 None."""
    if not body.startswith("---"):
        return None
    lines = body.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return sum(len(l) for l in lines[: i + 1])
    return None  # 미종료 frontmatter → 일반 내용으로 취급


def inject_claude_md(text):
    """(new_text, changed) 반환. text=None은 CLAUDE.md 없음."""
    if text is None:
        return IMPORT_LINE + "\n", True
    had_bom = text.startswith("﻿")
    body = text[1:] if had_bom else text
    if _IMPORT_RE.search(body):
        return text, False  # 이미 import — 손대지 않음
    prefix = "﻿" if had_bom else ""
    fm_end = _frontmatter_end(body)
    if fm_end is not None:
        new = body[:fm_end] + IMPORT_LINE + "\n" + body[fm_end:]
    else:
        new = IMPORT_LINE + "\n" + body
    return prefix + new, True


def inject_claude_md_file(repo_root) -> bool:
    """repo_root/CLAUDE.md 안전 주입. 변경 시에만 write. changed? 반환."""
    path = Path(repo_root) / "CLAUDE.md"
    text = path.read_text(encoding="utf-8") if path.exists() else None
    new, changed = inject_claude_md(text)
    if changed:
        path.write_text(new, encoding="utf-8")
    return changed
```

- [ ] **Step 4: GREEN 확인**

Run: `uv run --with pytest pytest test_inject_claude_md.py -v`
Expected: 6 passed.

- [ ] **Step 5: 파일 래퍼 테스트 추가 (기존 CLAUDE.md 보존 실증)**

`test_inject_claude_md.py`에 추가:
```python
def test_file_wrapper_preserves_existing(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Existing\nrule\n", encoding="utf-8")
    changed = inject_claude_md_file(tmp_path)
    out = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert changed is True
    assert out == "@AGENTS.md\n# Existing\nrule\n"   # 기존 보존 + prepend


def test_file_wrapper_creates_when_absent(tmp_path):
    changed = inject_claude_md_file(tmp_path)
    assert changed is True
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n"
```

- [ ] **Step 6: GREEN 확인**

Run: `uv run --with pytest pytest test_inject_claude_md.py -v`
Expected: 8 passed.

- [ ] **Step 7: 커밋 + 푸시**

```bash
cd ~/Desktop/private/docsherpa
git add skills/setup-docs/scripts/inject_claude_md.py skills/setup-docs/scripts/test_inject_claude_md.py
git commit -m "M3: safe CLAUDE.md @AGENTS.md injection (none/import/prepend/BOM/frontmatter edges)"
git push
```

---

### Task 2: settings.json JSONC 가드 (code — §14 결정 확정)

M0에서 Claude Code settings는 표준 JSON으로 확정됐다(FINDINGS ②). 그러나 사용자가 손으로 주석(JSONC)을 넣은 파일이면 `json.loads`가 던진다 → 현 `merge_settings_file`은 크래시. §14의 "JSONC 편집 전략"을 **feature가 아니라 fail-safe 가드로** 닫는다: 주석 감지 시 조용한 클로버·크래시 대신 **명확한 메시지로 거부하고 파일을 건드리지 않는다**(사용자가 수동 병합). JSONC 파서를 짓지 않는다(YAGNI).

**Files:**
- Modify: `skills/setup-docs/scripts/merge_settings.py:26-37` (merge_settings_file)
- Test: `skills/setup-docs/scripts/test_merge_settings.py` (추가)

**Interfaces:**
- Consumes: 기존 `merge_hook`.
- Produces: `merge_settings_file(claude_dir, command)` — settings.json이 표준 JSON으로 파싱 실패하면 `ValueError`(수동 병합 안내 메시지)를 던지고 **파일을 수정하지 않는다**. 성공 경로는 M0와 동일(`changed?` 반환).

- [ ] **Step 1: 실패 테스트 작성 — JSONC면 거부 + 무변경**

`test_merge_settings.py`에 추가(파일 상단 import는 이미 `json`·`merge_hook`·`merge_settings_file` 존재):
```python
import pytest


def test_jsonc_with_comments_refuses_without_clobber(tmp_path):
    claude = tmp_path / ".claude"
    claude.mkdir()
    original = '{\n  // user comment\n  "hooks": {}\n}\n'
    (claude / "settings.json").write_text(original)
    with pytest.raises(ValueError) as exc:
        merge_settings_file(claude, "cat .claude/doc-drift-prime.txt 2>/dev/null || true")
    assert "manually" in str(exc.value).lower() or "수동" in str(exc.value)
    # 파일은 절대 손상되지 않는다 (클로버 금지)
    assert (claude / "settings.json").read_text() == original
```

- [ ] **Step 2: 실패 확인**

Run: `uv run --with pytest pytest test_merge_settings.py::test_jsonc_with_comments_refuses_without_clobber -v`
Expected: FAIL — 현 구현은 `json.JSONDecodeError`(ValueError 서브클래스지만 메시지에 "manually" 없음)를 던지고, 어쨌든 assert 메시지 검사에서 실패. (핵심: 명확한 안내 없이 크래시한다는 걸 RED로 고정.)

- [ ] **Step 3: 가드 구현**

`skills/setup-docs/scripts/merge_settings.py`의 `merge_settings_file`를 교체:
```python
def merge_settings_file(claude_dir, command: str) -> bool:
    """.claude/settings.json(공유)만 대상. 없으면 생성. (.local엔 절대 안 씀.) changed? 반환.

    표준 JSON만 무손실 병합한다. 주석(JSONC) 등으로 파싱 실패하면 파일을 건드리지 않고
    ValueError로 수동 병합을 안내한다(클로버·크래시 대신 fail-safe — spec §14 JSONC 결정).
    """
    path = Path(claude_dir) / "settings.json"
    if path.exists():
        try:
            settings = json.loads(path.read_text())
        except json.JSONDecodeError:
            raise ValueError(
                f"{path} 가 표준 JSON이 아니다(주석/JSONC 추정). 자동 병합을 건너뛴다 — "
                f"SessionStart 훅을 수동으로 추가하라(merge this hook manually): {command}"
            )
    else:
        settings = {}
    settings, changed = merge_hook(settings, command)
    if changed:
        path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n")
    return changed
```

- [ ] **Step 4: GREEN 확인 (신규 + 기존 3 회귀 없음)**

Run: `uv run --with pytest pytest test_merge_settings.py -v`
Expected: 4 passed (기존 3 + JSONC 가드 1).

- [ ] **Step 5: docstring의 M3 이연 메모 갱신**

`merge_settings.py` 상단 docstring/함수 docstring에 남아 있던 "JSONC면 M3에서 comment-preserving 편집으로 승격" 문구를 실제 결정으로 교체: comment-preservation은 **의도적 미구현**(YAGNI — settings는 표준 JSON), JSONC는 fail-safe 거부로 처리함을 1줄로 명시. (spec §14 항목을 약속이 아니라 닫힌 결정으로.)

`merge_settings_file` docstring 위의 파일-레벨 docstring(라인 1-5)의 마지막 문장을 교체:
```
원래: "JSONC(주석 허용)면 M3에서 comment-preserving 편집으로 승격(spike T2 Step 11 결정)."
교체: "JSONC(주석)면 comment-preserving을 짓지 않고 fail-safe로 거부한다(M3 결정 — settings는
표준 JSON이 정상, YAGNI)."
```

- [ ] **Step 6: 커밋 + 푸시**

```bash
cd ~/Desktop/private/docsherpa
git add skills/setup-docs/scripts/merge_settings.py skills/setup-docs/scripts/test_merge_settings.py
git commit -m "M3: settings.json JSONC guard — refuse+no-clobber instead of crash (§14 decision, YAGNI)"
git push
```

---

### Task 3: gate.py 마커 계약 강제 (code — spec §4/D8)

스캐폴드 후 검증에서 라우터에 마커가 실제로 있는지 게이트가 강제하게 한다(spec §4: "gate.py 마커 계약 grep 추가"). 단 Phase 0 진단(마커 없는 fresh repo)에서 false-fail하지 않도록 **opt-in `--require-markers` 플래그**로 격리한다. 스캐폴드 검증 단계에서만 켠다.

**Files:**
- Modify: `skills/setup-docs/scripts/gate.py:64-120` (main — argv 파싱 + 마커 체크 분기)
- Test: `skills/setup-docs/scripts/test_gate_markers.py` (신규)

**Interfaces:**
- Consumes: 기존 `check_markers.has_contract_markers(text) -> bool`.
- Produces: `gate.py [REPO_ROOT] [--require-markers]` — 플래그가 켜지면 broken/orphan 0에 더해 `AGENTS.md`에 라우팅·인덱스 마커 둘 다 있어야 PASS. 플래그 없으면 M0와 동일(마커 무관). 테스트용 `main(argv)` 시그니처(argv 리스트 주입 가능).

- [ ] **Step 1: 실패 테스트 작성 — 플래그 유무에 따른 마커 강제**

`skills/setup-docs/scripts/test_gate_markers.py`:
```python
import gate

ROUTING = "<!-- docsherpa:routing -->"
INDEX = "<!-- docsherpa:index -->"


def _router_without_markers(root):
    (root / "AGENTS.md").write_text(
        "# Guide\n## 문서 라우팅 룰\nrule\n## 먼저 읽기\n- x\n", encoding="utf-8"
    )


def _router_with_markers(root):
    (root / "AGENTS.md").write_text(
        f"# Guide\n## 문서 라우팅 룰 {ROUTING}\nrule\n## 먼저 읽기 {INDEX}\n- x\n",
        encoding="utf-8",
    )


def test_no_flag_ignores_markers(tmp_path):
    _router_without_markers(tmp_path)
    assert gate.main([str(tmp_path)]) == 0          # 마커 없어도 PASS(도달성만)


def test_require_markers_fails_when_absent(tmp_path):
    _router_without_markers(tmp_path)
    assert gate.main([str(tmp_path), "--require-markers"]) == 1


def test_require_markers_passes_when_present(tmp_path):
    _router_with_markers(tmp_path)
    assert gate.main([str(tmp_path), "--require-markers"]) == 0
```

- [ ] **Step 2: 실패 확인**

Run: `uv run --with pytest pytest test_gate_markers.py -v`
Expected: FAIL — 현 `main()`은 인자를 안 받고(`main()` no-arg) `sys.argv`를 읽으며 `--require-markers`를 REPO_ROOT로 오해. `TypeError: main() takes 0 positional arguments` 등.

- [ ] **Step 3: gate.py main을 argv 주입 + 플래그 분기로 수정**

`gate.py`의 `main()`을 다음으로 교체(도달성 로직 본문은 그대로, 시그니처·플래그·마커 체크만 추가). 상단에 `import check_markers` 추가:
```python
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    require_markers = "--require-markers" in argv
    argv = [a for a in argv if a != "--require-markers"]
    root = Path(argv[0] if argv else ".").resolve()

    roots = [p for p in (root / "AGENTS.md", root / "CLAUDE.md") if p.is_file()]
    if not roots:
        print(f"FAIL: 진입 라우터 없음 — {root}/AGENTS.md (또는 CLAUDE.md) 가 필요하다.")
        return 1

    broken = []        # (소스파일, raw타겟)
    visited = set()    # 방문한 .md 파일(절대경로)
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
            # kind == "file"
            if not target.name.endswith(".md"):
                continue
            if not target.is_file():
                broken.append((cur, raw))
                continue
            queue.append(target)

    docs_dir = root / "docs"
    all_docs = sorted(docs_dir.rglob("*.md")) if docs_dir.is_dir() else []
    orphans = [d for d in all_docs if d.resolve() not in visited]

    markers_ok = True
    if require_markers:
        agents = root / "AGENTS.md"
        markers_ok = agents.is_file() and check_markers.has_contract_markers(
            agents.read_text(encoding="utf-8", errors="ignore")
        )

    ok = not broken and not orphans and markers_ok
    print(f"{'PASS' if ok else 'FAIL'}: broken={len(broken)} orphan={len(orphans)} "
          f"(docs={len(all_docs)}, reachable={len(visited)})"
          + ("" if not require_markers else f" markers_ok={markers_ok}"))

    if broken:
        print("\n깨진 링크:")
        for src, raw in broken:
            print(f"  {src.relative_to(root)} -> {raw}")
    if orphans:
        print("\n고아 문서(인덱스에서 도달 불가):")
        for d in orphans:
            print(f"  {d.relative_to(root)}")
    if require_markers and not markers_ok:
        print("\n마커 누락: AGENTS.md에 <!-- docsherpa:routing -->·<!-- docsherpa:index --> 둘 다 필요.")

    return 0 if ok else 1
```
그리고 파일 하단 `sys.exit(main())`는 그대로 둔다(argv=None → sys.argv 사용).

- [ ] **Step 4: GREEN 확인**

Run: `uv run --with pytest pytest test_gate_markers.py -v`
Expected: 3 passed.

- [ ] **Step 5: gate.py 사용법 docstring에 플래그 1줄 추가**

`gate.py` 상단 docstring "사용:" 블록에 `--require-markers`(스캐폴드 검증 시 마커 계약 강제) 1줄 추가. 그 외 문구 불변.

- [ ] **Step 6: 커밋 + 푸시**

```bash
cd ~/Desktop/private/docsherpa
git add skills/setup-docs/scripts/gate.py skills/setup-docs/scripts/test_gate_markers.py
git commit -m "M3: gate.py --require-markers flag enforces D8 marker contract (opt-in, post-scaffold verify)"
git push
```

---

### Task 4: 스캐폴드 템플릿 자산 (assets)

target repo에 커밋될 훅 프라임 + 훅 템플릿을 플러그인 안에 원본으로 둔다(spec §4 트리 `templates/`, D5: 플러그인은 훅 *템플릿*만 — active 아님). 도메인 리터럴 0(범용).

**Files:**
- Create: `skills/setup-docs/templates/doc-drift-prime.txt`
- Create: `skills/setup-docs/templates/settings-hook.json`

**Interfaces:**
- Produces: 스캐폴드 원본. Task 5의 SKILL 산문이 이 둘을 target `.claude/`로 복사·병합하라고 지시. 훅 명령 문자열은 `merge_settings`/기존 테스트와 동일: `cat .claude/doc-drift-prime.txt 2>/dev/null || true`.

- [ ] **Step 1: prime 텍스트 작성 (범용·짧게)**

`skills/setup-docs/templates/doc-drift-prime.txt`:
```
[docsherpa] 이 세션에서 코드·정책·구조를 바꿨다면, 커밋 전에 doc-reconcile을 돌려
문서를 갱신/신설하라(낡은 문서 고치기 + AGENTS.md 아키텍처가 요구하는 새 문서).
스킬: /docsherpa:doc-reconcile (또는 .claude/skills/doc-reconcile/SKILL.md).
바꾼 게 없으면 무시하라.
```

- [ ] **Step 2: 훅 템플릿 작성 (active 아님 — 참조용 스니펫)**

`skills/setup-docs/templates/settings-hook.json`:
```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          { "type": "command", "command": "cat .claude/doc-drift-prime.txt 2>/dev/null || true" }
        ]
      }
    ]
  }
}
```

- [ ] **Step 3: 템플릿이 M1 이식성 가드 금지어를 안 담는지 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_doc_reconcile_portable.py -q`
Expected: 2 passed (템플릿은 doc-reconcile SKILL이 아니지만, 이 태스크가 도메인 리터럴을 안 넣었음을 회귀로 재확인 — 전체 GREEN 유지). 추가로 육안: prime/훅에 프로젝트-특이 이름(`config.py`·`second-brain` 등) 0.

- [ ] **Step 4: 커밋 + 푸시**

```bash
cd ~/Desktop/private/docsherpa
git add skills/setup-docs/templates/doc-drift-prime.txt skills/setup-docs/templates/settings-hook.json
git commit -m "M3: add generic scaffold templates (doc-drift-prime, settings-hook — D5, active-in-target-only)"
git push
```

---

### Task 5: setup-docs SKILL.md 설치자 산문 (prose — 인라인, subagent 금지)

SKILL.md에 성장 루프 설치를 짜 넣는다. 외과적 편집: 기존 GREENFIELD 골격은 보존하고, ① AGENTS.md 템플릿에 마커 삽입 ② 라우팅 블록에 마커 ③ Phase 0에 loop-presence 1줄 ④ 새 "성장 루프 설치" 섹션(opt-in·dry-run·diff-preview·스캐폴드·merge·CLAUDE.md 주입) ⑤ 마커 삽입 규칙(기존 AGENTS.md 병합 시)만 추가한다.

**Files:**
- Modify: `skills/setup-docs/SKILL.md` (여러 지점 — 아래 각 스텝이 정확한 앵커 지정)

**Interfaces:**
- Consumes: `inject_claude_md.py`(Task 1) · `merge_settings.py`(Task 2) · `gate.py --require-markers`(Task 3) · `templates/`(Task 4) · `check_markers.py`.
- Produces: 설치자로 확장된 SKILL.md. M2 fixture가 이 산문을 end-to-end로 검증.

- [ ] **Step 1: AGENTS.md 템플릿에 마커 삽입 (라인 83·99 부근)**

SKILL.md의 "AGENTS.md 템플릿" 블록에서 인덱스 헤딩을 마커화:
```
원래: ## 먼저 읽기 (문서 인덱스 — 진입점만, 린)
교체: ## 먼저 읽기 (문서 인덱스 — 진입점만, 린) <!-- docsherpa:index -->
```
그리고 "문서 라우팅 룰 블록" 안 헤딩:
```
원래: ## 문서 라우팅 룰 (새 문서가 어디로)
교체: ## 문서 라우팅 룰 (새 문서가 어디로) <!-- docsherpa:routing -->
```
(greenfield는 템플릿을 그대로 쓰므로 마커가 자동으로 산출물에 들어간다 — doc-reconcile 소비 계약 성립.)

- [ ] **Step 2: 멱등·병합 규칙에 마커 삽입 규칙 추가 (라인 63-65 부근)**

"기존 `AGENTS.md` 있으면:" 불릿 뒤에 마커 처리 1-2줄 추가:
```markdown
- **마커 계약(D8):** 라우팅/인덱스 섹션이 있으면(헤딩이 번역/재작성됐더라도 의미로 식별)
  그 헤딩 줄 끝에 `<!-- docsherpa:routing -->`·`<!-- docsherpa:index -->`를 없을 때만 붙인다.
  섹션 자체가 없어 새로 추가하는 경우엔 위 템플릿처럼 마커를 포함해 쓴다. 헤딩을 못 찾으면
  마커를 억지로 넣지 말고 사용자에게 "라우팅/인덱스 섹션 위치 확인 필요"로 보고한다(조용한 오배치 금지).
```

- [ ] **Step 3: Phase 0에 loop-presence 체크 흡수 (라인 28-31 부근, spec §7.4)**

Phase 0 진단의 번호 리스트에 loop 3종 존재 확인 1줄 추가(별도 스크립트 안 만듦 — YAGNI):
```markdown
4. **성장 루프 존재 확인**(`ls` 수준): `.claude/doc-drift-prime.txt` · `.claude/settings.json`의
   SessionStart 훅 · `.claude/skills/doc-reconcile/SKILL.md` 3종이 있는지. 없으면 아래 "성장 루프
   설치" 대상(HEALTHY 판정도 루프 부재면 "골격은 건강, 루프 미설치"로 분리 보고).
```

- [ ] **Step 4: "성장 루프 설치" 섹션 신설 (GREENFIELD 경로 끝, 무결성 게이트 앞)**

SKILL.md의 GREENFIELD 경로 6번(무결성 게이트) 뒤, "### 멱등 · 병합 규칙" 앞에 새 섹션 삽입:
```markdown
### 성장 루프 설치 (opt-in — spec §7·D7)

문서 골격이 서면, doc-reconcile 성장 루프를 target repo에 **커밋 스캐폴드**한다(collaborator가
플러그인 없이도 규율을 얻도록 — D2). **반드시 opt-in:** 무엇을 쓸지 먼저 보여주고 승인받는다.

1. **계획 diff-preview.** 쓸 파일 목록을 먼저 보여준다:
   - `.claude/skills/doc-reconcile/SKILL.md` (플러그인 정본 복사 + version stamp)
   - `.claude/doc-drift-prime.txt` (`<skill>/templates/doc-drift-prime.txt` 복사)
   - `.claude/settings.json` (SessionStart 훅 **병합** — 덮어쓰기 아님)
   - `CLAUDE.md` (`@AGENTS.md` 안전 주입 — 기존 보존)
2. **비대화형 fallback(§7.1).** 대화형이 아니면(headless/CI) 기본 **dry-run**: 위 계획만 출력하고
   **아무것도 쓰지 않는다.** 실제 쓰기는 명시 승인(`--yes` 상당의 사용자 확정) 후에만.
3. **doc-reconcile 복사 + version stamp.** 플러그인 정본
   `<plugin>/skills/doc-reconcile/SKILL.md`를 target `.claude/skills/doc-reconcile/SKILL.md`로
   복사하고, 파일 끝에 `<!-- docsherpa-scaffold: v<plugin.version> -->` 스탬프를 붙인다.
   **재실행 정책(R4):** 이미 있고 로컬 편집이 감지되면 **기본 skip + diff 표시**, 조용한 overwrite 금지.
4. **prime 복사.** `<skill>/templates/doc-drift-prime.txt` → `.claude/doc-drift-prime.txt`.
5. **settings 훅 병합.** `python3 <skill>/scripts/merge_settings.py`가 감싸는
   `merge_settings_file(target/.claude, "cat .claude/doc-drift-prime.txt 2>/dev/null || true")`로
   **`settings.json`(공유·커밋)** 에 SessionStart 훅을 멱등 병합한다. 기존 훅 보존·경로표기 dedup.
   ⚠️ `settings.json`이 표준 JSON이 아니면(주석/JSONC) 함수가 거부한다 → 사용자에게 수동 병합 안내.
   절대 `settings.local.json`에 쓰지 않는다(D2).
6. **CLAUDE.md 주입.** `inject_claude_md_file(target)`로 `@AGENTS.md`를 안전 주입한다 — 없으면 생성,
   이미 import면 무변경, 다른 내용이면 첫 줄(또는 BOM/frontmatter 뒤) prepend. 기존 내용 절대 파괴 안 함.
7. **훅 신뢰 투명성(D7).** prime은 커밋된 신뢰 경계임을 사용자에게 알린다: SessionStart에 `cat`
   한 줄이 붙고, collaborator가 clone하면 Claude Code 훅-승인 게이트가 첫 실행 전 승인을 요구한다
   (harness safe-by-default). 비활성화는 settings.json에서 그 훅 항목 삭제.
8. **스캐폴드 검증.** `python3 <skill>/scripts/gate.py <repo> --require-markers` → broken=0·orphan=0
   **+ 마커 계약 PASS**. 실패 시 STOP·보고.
```

- [ ] **Step 5: 무결성 게이트 문단에 --require-markers 언급 (라인 152-165 부근)**

GREENFIELD "무결성 게이트" 문단 끝에 1줄: 루프를 설치한 경우 `--require-markers`로 마커 계약까지 검증한다고 명시(스캐폴드 전 순수 골격 검증은 플래그 없이).

- [ ] **Step 6: Common Mistakes에 설치자 함정 2줄 추가 (라인 197-204 부근)**

```markdown
- **settings.local.json에 훅 씀** → D2 위반. 반드시 공유 `settings.json`(collaborator가 못 받음).
- **마커 없이 라우팅/인덱스 섹션 생성** → doc-reconcile이 섹션을 못 찾음(D8). 헤딩에 마커 필수.
- **기존 CLAUDE.md/settings.json 덮어씀** → 병합·주입 함수로만 건드린다(inject_claude_md/merge_settings).
```

- [ ] **Step 7: 육안 검증 — 척추 보존 + 마커 일관**

Read `skills/setup-docs/SKILL.md` 전체. 확인:
  - 기존 GREENFIELD/MESSY/멱등 규칙 문단이 훼손 없이 그대로인가(외과적 편집).
  - 삽입한 마커 문자열이 정확히 `<!-- docsherpa:routing -->`·`<!-- docsherpa:index -->`인가(check_markers와 동일).
  - "성장 루프 설치"가 opt-in·dry-run·D2·R4·D7을 모두 언급하는가.

- [ ] **Step 8: 커밋 + 푸시**

```bash
cd ~/Desktop/private/docsherpa
git add skills/setup-docs/SKILL.md
git commit -m "M3: extend setup-docs into installer — markers, loop scaffold, merge/inject, Phase0 loop-check"
git push
```

---

### Task 6: M3 종료 — 전체 GREEN + FINDINGS 갱신 + 다음(M2) 지시

**Files:**
- Modify: `FINDINGS.md` (다음 세션 시작점 + M3 완료 기록)

**Interfaces:**
- Consumes: Task 1-5 산출물.
- Produces: M3 완료 상태 + M2로의 인계.

- [ ] **Step 1: 전체 스크립트 테스트 GREEN 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`
Expected: 18(기존) + 8(inject_claude_md) + 1(JSONC 가드) + 3(gate markers) = **30 passed**. (숫자가 다르면 회귀를 조사 — 특히 기존 18이 줄었으면 STOP.)

- [ ] **Step 2: 정본 이식성 가드 재확인 (역누출 없음)**

Run: `uv run --with pytest pytest test_doc_reconcile_portable.py -q`
Expected: 2 passed — M3 편집이 정본 doc-reconcile에 프로젝트 리터럴을 안 넣었음.

- [ ] **Step 3: FINDINGS "다음 세션 시작점" 갱신**

FINDINGS.md 맨 위 블록을 M3 완료 → M2 시작으로 갱신:
  - 상태: M0·M1·**M3 완료.** 다음 = **M2 이식성 fixture**(설치자 end-to-end 검증).
  - M3이 닫은 것: CLAUDE.md 주입(§14 엣지) · settings JSONC 결정(fail-safe 거부) · gate 마커 강제(--require-markers) · 스캐폴드 산문(opt-in/dry-run/D2/R4/D7) · Phase0 loop 흡수.
  - 테스트 러너 줄의 "18 passed"를 "30 passed"로 갱신.
  - 이어읽기: DESIGN §10.2(4종 fixture) → M2 계획을 writing-plans로.

- [ ] **Step 4: FINDINGS 하단에 M3 완료 문단 추가**

M1 완료 문단 아래에 M3 완료 문단(GREEN, 무엇을 닫았나, 남은 것: M2 fixture가 설치-현실·hollow-없음을 검증).

- [ ] **Step 5: 커밋 + 푸시**

```bash
cd ~/Desktop/private/docsherpa
git add FINDINGS.md docs/plans/M3-setup-docs-installer.md
git commit -m "M3: complete — installer built (inject/merge/gate/scaffold), 30 tests GREEN, ready for M2"
git push
```

---

## Self-Review

**Spec coverage:**
- §7.1 루프 스캐폴드 opt-in + 비대화형 dry-run fallback → Task 5 Step 4 (항목 1·2).
- §7.2 settings 3-파트 병합(dedup·포맷·파일선택) → merge_settings(M0 완료) + Task 2 JSONC 가드 + Task 5 Step 4 항목 5.
- §7.3 CLAUDE.md 주입(없음/import/prepend) → Task 1 + Task 5 Step 4 항목 6.
- §7.4 loop-presence → Phase 0 흡수(별도 스크립트 없음) → Task 5 Step 3.
- §7.5 앵커 보수적 채움 → doc-reconcile 정본이 이미 graceful degrade(M1). 스캐폴드는 정본 복사(Task 5 Step 4 항목 3). 추가 코드 불요.
- §4 gate.py 마커 grep(D8) → Task 3.
- §14 CLAUDE.md BOM/frontmatter/import 엣지 → Task 1 테스트. JSONC 전략 결정 → Task 2(fail-safe 거부, YAGNI). R4 재실행 skip+diff → Task 5 Step 4 항목 3.
- D5 훅 템플릿(active 아님) → Task 4. D7 훅 투명성 → Task 5 Step 4 항목 7. D2 settings.json → Task 2·5 + Common Mistakes.
- **의도적 밖:** §10.4 설치-현실 테스트(실제 `/plugin install`)는 VSCode 채팅에서 `/plugin` 불가(FINDINGS ①) → M2/M4의 수동 검증으로 이연. M2 fixture(§10.2)는 이 플랜 밖(재-시퀀싱 M3→M2).

**Placeholder scan:** `<plugin>`·`<skill>`·`<repo>`·`v<plugin.version>`는 SKILL.md 산문의 의도된 경로 자리표시(에이전트가 실행 시 해석 — 기존 SKILL.md도 `<skill>` 사용). `<!-- TODO -->`는 doc-reconcile graceful-degrade 금지 패턴 예시로만 언급, 플랜 placeholder 아님. `--yes 상당`은 대화형 승인 개념 설명이지 미구현 플래그 요구 아님(코드로 안 만듦 — 에이전트 판단). 그 외 TBD/미완 없음.

**Type consistency:**
- `inject_claude_md(text|None)->(str,bool)` · `inject_claude_md_file(repo_root)->bool` — Task 1 정의, Task 5 Step 4 항목 6에서 `inject_claude_md_file(target)`로 호출. 일치.
- `merge_settings_file(claude_dir,command)->bool` (JSONC면 ValueError) — Task 2, Task 5 항목 5 호출. 일치.
- `gate.main(argv=None)->int` + `--require-markers` — Task 3 정의, Task 5 Step 8·Step 5에서 CLI로 사용. 일치.
- 마커 문자열 `<!-- docsherpa:routing -->`·`<!-- docsherpa:index -->` — check_markers(M0)·Task 1 테스트 아님·Task 3·Task 4 훅 아님·Task 5 전부 동일 리터럴. 일치.
- 훅 명령 `cat .claude/doc-drift-prime.txt 2>/dev/null || true` — Task 4 템플릿·Task 5 항목 5·기존 test_merge_settings 동일. 일치.

**구현자 주의:** Task 5는 산문 편집이라 단위 테스트로 척추 손실을 못 잡는다 → Step 7 육안 체크가 필수 게이트(M1 Task 3 Step 5 교훈의 반복). Task 3 gate.py 수정은 도달성 로직 본문을 **그대로** 옮기고 시그니처·플래그·마커 분기만 더하는 것 — 본문 로직을 바꾸지 말 것(회귀 위험).
```