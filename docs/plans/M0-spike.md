# docsherpa M0 (de-risk spike) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 가장 어려운 미지수 3개(마켓플레이스 설치·네임스페이스 resolution / settings.json 3-파트 병합 / 훅-승인 게이트 실동작)를 최소 플러그인으로 실증해, M1–M5 상세 계획의 가정을 확정한다.

**Architecture:** 새 `docsherpa` repo에 최소 플러그인(`plugin.json` + `marketplace.json` + 트리비얼 skill 하나)을 만들어 로컬 마켓플레이스로 설치한다. 그 위에 M0의 진짜 코드 산출물인 `merge_settings.py`(SessionStart 훅 멱등 병합)를 RED-first로 짓는다. 나머지 두 미지수(설치·훅 신뢰)는 실험-기록 태스크로 결정을 확정한다.

**Tech Stack:** Claude Code 플러그인(플랫폼), Python 3(스크립트·테스트, `pytest`), git.

## Global Constraints

- 새 repo 위치: `~/Desktop/private/docsherpa` (second-brain의 sibling. 변경 가능 — T1에서 확정).
- 플러그인 이름: `docsherpa` (네임스페이스 접두사 `/docsherpa:*`).
- settings 병합은 반드시 **`.claude/settings.json`**(공유·커밋). `settings.local.json` 금지(spec D2).
- RED-first: 동작 코드는 실패 테스트 먼저 → GREEN (spec §10, 전역 4원칙 #4).
- 커밋은 논리 단위마다. `git add -A` 금지 — 의도한 파일만 스테이지.
- M0는 spike다: 각 실험 태스크의 산출물은 **기록된 결정**(FINDINGS.md 한 줄)이며, 그 결정이 스펙의 D7/§7/§14를 확정하거나 갱신한다.

---

### Task 1: 최소 플러그인 스캐폴드 + 로컬 설치 + 네임스페이스 resolution

미지수 ③: 마켓플레이스가 같은 repo self-host로 실제 설치되는가? 스킬이 `/docsherpa:<name>`으로 resolve되는가?

**Files:**
- Create: `~/Desktop/private/docsherpa/.claude-plugin/plugin.json`
- Create: `~/Desktop/private/docsherpa/.claude-plugin/marketplace.json`
- Create: `~/Desktop/private/docsherpa/skills/hello/SKILL.md`
- Create: `~/Desktop/private/docsherpa/FINDINGS.md`

**Interfaces:**
- Produces: 설치 가능한 `docsherpa` 플러그인. 확인된 설치 커맨드 시퀀스(FINDINGS.md에 기록) — M3/M4가 재사용.

- [ ] **Step 1: repo 생성 + git init**

```bash
mkdir -p ~/Desktop/private/docsherpa && cd ~/Desktop/private/docsherpa && git init
```

- [ ] **Step 2: plugin.json 작성**

`.claude-plugin/plugin.json`:
```json
{
  "name": "docsherpa",
  "description": "Build and grow an agent-readable documentation architecture.",
  "version": "0.0.1",
  "author": { "name": "<이름/핸들>" },
  "license": "MIT"
}
```

- [ ] **Step 3: marketplace.json 작성 (같은 repo self-host)**

`.claude-plugin/marketplace.json`:
```json
{
  "name": "docsherpa",
  "owner": { "name": "<이름/핸들>" },
  "plugins": [
    { "name": "docsherpa", "source": "./", "description": "Agent-readable docs architecture." }
  ]
}
```

- [ ] **Step 4: 트리비얼 skill 작성 (resolution 프로브)**

`skills/hello/SKILL.md`:
```markdown
---
name: hello
description: Namespace-resolution probe for the docsherpa M0 spike. Prints a marker string.
---

# hello

Print exactly this line and nothing else: `DOCSHERPA_NAMESPACE_OK`.
```

- [ ] **Step 5: 로컬 마켓플레이스 등록 + 설치 (실험)**

Run:
```bash
# Claude Code 안에서: 로컬 경로로 마켓플레이스 추가 후 설치
/plugin marketplace add ~/Desktop/private/docsherpa
/plugin install docsherpa@docsherpa
```
Expected: 등록·설치 성공. 실패하면 에러 문구를 FINDINGS.md에 그대로 기록(경로 형식·source 형식이 원인일 수 있음 — 이게 spike가 잡을 것).

- [ ] **Step 6: 네임스페이스 resolution 검증 (실험)**

Run: `/docsherpa:hello`
Expected: `DOCSHERPA_NAMESPACE_OK` 출력. 접두사 형태(`/docsherpa:hello` vs 다른 형태)를 FINDINGS.md에 확정 기록.

- [ ] **Step 7: FINDINGS 기록 + 커밋**

FINDINGS.md에 3줄: 설치 커맨드 시퀀스(정확형) · 네임스페이스 접두사 형태 · 걸린 함정.
```bash
cd ~/Desktop/private/docsherpa
git add .claude-plugin/ skills/hello/SKILL.md FINDINGS.md
git commit -m "spike: minimal docsherpa plugin installs + namespace resolves"
```

---

### Task 2: `merge_settings.py` — SessionStart 훅 3-파트 멱등 병합 (M0의 핵심 코드 산출물)

미지수 ②·spec R1: 기존 훅 보존 + 멱등 dedup + `settings.json`(not local). 이게 유일한 진짜 데이터-유실 BREAK.

**Files:**
- Create: `~/Desktop/private/docsherpa/skills/setup-docs/scripts/merge_settings.py`
- Test: `~/Desktop/private/docsherpa/skills/setup-docs/scripts/test_merge_settings.py`

**Interfaces:**
- Produces: `merge_hook(settings: dict, command: str) -> tuple[dict, bool]` — (갱신된 settings, changed?).
  `norm(command)`으로 dedup. M3의 스캐폴더가 이 함수를 파일 I/O로 감싸 호출.

- [ ] **Step 1: 실패 테스트 작성 — 기존 훅 보존 + 새 훅 추가**

`test_merge_settings.py`:
```python
from merge_settings import merge_hook

def test_preserves_existing_sessionstart_hook():
    settings = {
        "hooks": {
            "SessionStart": [
                {"hooks": [{"type": "command", "command": "echo user-env-setup"}]}
            ]
        }
    }
    out, changed = merge_hook(settings, "cat .claude/doc-drift-prime.txt 2>/dev/null || true")
    cmds = [h["command"]
            for entry in out["hooks"]["SessionStart"]
            for h in entry["hooks"]]
    assert "echo user-env-setup" in cmds            # 기존 보존
    assert any("doc-drift-prime.txt" in c for c in cmds)  # 새 훅 추가
    assert changed is True
```

- [ ] **Step 2: 실패 확인**

Run: `cd ~/Desktop/private/docsherpa/skills/setup-docs/scripts && python3 -m pytest test_merge_settings.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'merge_settings'`.

- [ ] **Step 3: 최소 구현**

`merge_settings.py`:
```python
"""SessionStart 훅 멱등 병합 — 기존 settings.json을 보존하며 doc-drift prime 훅만 추가."""

def _norm(command: str) -> str:
    """경로·따옴표·./ 차이를 무시한 dedup 키."""
    return " ".join(command.replace("./", "").replace('"', "").split())

def merge_hook(settings: dict, command: str):
    """(갱신된 settings, changed?) 반환. 동일(정규화) 훅이 이미 있으면 changed=False."""
    hooks = settings.setdefault("hooks", {})
    sessionstart = hooks.setdefault("SessionStart", [])
    for entry in sessionstart:
        for h in entry.get("hooks", []):
            if h.get("type") == "command" and _norm(h.get("command", "")) == _norm(command):
                return settings, False
    sessionstart.append({"hooks": [{"type": "command", "command": command}]})
    return settings, True
```

- [ ] **Step 4: GREEN 확인**

Run: `python3 -m pytest test_merge_settings.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: 실패 테스트 추가 — 멱등(2회 실행 = 변경0, 경로 표기 차이도 dedup)**

`test_merge_settings.py`에 추가:
```python
def test_idempotent_across_path_notation():
    settings = {}
    cmd = "cat .claude/doc-drift-prime.txt 2>/dev/null || true"
    settings, c1 = merge_hook(settings, cmd)
    settings, c2 = merge_hook(settings, "cat ./.claude/doc-drift-prime.txt 2>/dev/null || true")  # ./ 표기차
    assert c1 is True and c2 is False               # 두 번째는 dedup
    total = sum(len(e["hooks"]) for e in settings["hooks"]["SessionStart"])
    assert total == 1                                # 중복 append 없음
```

- [ ] **Step 6: 실패 확인 → 통과 확인**

Run: `python3 -m pytest test_merge_settings.py -v`
Expected: 먼저 `test_idempotent_across_path_notation`가 통과하는지 확인(현 `_norm`이 `./`를 제거하므로 PASS해야 함). 만약 FAIL이면 `_norm`을 고쳐 GREEN. Expected 최종: 2 passed.

- [ ] **Step 7: 실패 테스트 추가 — 파일 레벨: settings.json에 쓰고 .local엔 안 씀**

`test_merge_settings.py`에 추가 (파일 I/O 래퍼를 강제):
```python
import json, pathlib
from merge_settings import merge_settings_file

def test_writes_to_settings_json_not_local(tmp_path):
    claude = tmp_path / ".claude"; claude.mkdir()
    (claude / "settings.json").write_text('{"hooks":{"SessionStart":[{"hooks":[{"type":"command","command":"echo keep"}]}]}}')
    merge_settings_file(claude, "cat .claude/doc-drift-prime.txt 2>/dev/null || true")
    data = json.loads((claude / "settings.json").read_text())
    cmds = [h["command"] for e in data["hooks"]["SessionStart"] for h in e["hooks"]]
    assert "echo keep" in cmds and any("doc-drift-prime" in c for c in cmds)
    assert not (claude / "settings.local.json").exists()   # .local 건드리지 않음
```

- [ ] **Step 8: 실패 확인**

Run: `python3 -m pytest test_merge_settings.py::test_writes_to_settings_json_not_local -v`
Expected: FAIL — `ImportError: cannot import name 'merge_settings_file'`.

- [ ] **Step 9: 파일 래퍼 구현**

`merge_settings.py`에 추가:
```python
import json
from pathlib import Path

def merge_settings_file(claude_dir, command: str) -> bool:
    """.claude/settings.json(공유)만 대상. 없으면 생성. (.local엔 절대 안 씀.) changed? 반환."""
    claude_dir = Path(claude_dir)
    path = claude_dir / "settings.json"
    settings = json.loads(path.read_text()) if path.exists() else {}
    settings, changed = merge_hook(settings, command)
    if changed:
        path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n")
    return changed
```

- [ ] **Step 10: GREEN 확인 (전체)**

Run: `python3 -m pytest test_merge_settings.py -v`
Expected: 3 passed.

- [ ] **Step 11: 포맷 보존 미지수 기록**

⚠️ 이 구현은 `json.load→dump`라 **주석·키순서를 재작성**한다. spike 결정: Claude Code `settings.json`이 표준 JSON인지 JSONC(주석 허용)인지 확인해 FINDINGS.md에 기록. **표준 JSON이면** 이 구현으로 충분(spec §14의 "JSONC 편집 전략"은 불필요로 닫힘). **JSONC면** M3에서 comment-preserving 편집으로 승격 — 결정만 여기서 확정.

- [ ] **Step 12: 커밋**

```bash
git add skills/setup-docs/scripts/merge_settings.py skills/setup-docs/scripts/test_merge_settings.py
git commit -m "spike: settings.json 3-part idempotent merge (preserve/dedup/settings-not-local)"
```

---

### Task 3: 훅-승인 게이트 실동작 검증 (D7 collaborator 보호 확정)

미지수 ①·spec D7: 커밋된 SessionStart 훅이 있는 repo를 **다른 사람이 클론**하면, Claude Code가 훅 실행 전 승인을 요구하는가? (요구하면 safe-by-default가 harness에서 제공됨 → 우리는 신뢰층 재발명 불필요.)

**Files:**
- Modify: `~/Desktop/private/docsherpa/FINDINGS.md` (결정 기록)

**Interfaces:**
- Produces: D7의 collaborator 보호 주장이 참인지 확정. M5 README 훅 투명성 문구가 이 결과에 의존.

- [ ] **Step 1: 훅 있는 target repo를 클론 시뮬레이션**

Run:
```bash
TMP=$(mktemp -d)
mkdir -p "$TMP/.claude"
printf '%s\n' '{"hooks":{"SessionStart":[{"hooks":[{"type":"command","command":"echo HOOK_FIRED_UNAPPROVED"}]}]}}' > "$TMP/.claude/settings.json"
cd "$TMP" && git init -q && git add -A && git commit -qm "repo with a committed SessionStart hook"
echo "$TMP"
```

- [ ] **Step 2: 새 신뢰 컨텍스트로 열어 승인 프롬프트 관찰 (실험)**

그 디렉터리를 Claude Code로 새로 연다(신뢰 안 된 상태). 관찰: SessionStart 훅이 **자동 실행되어 `HOOK_FIRED_UNAPPROVED`가 나오는지**, 아니면 **승인 프롬프트가 먼저 뜨는지**.
Expected(가설): 승인 프롬프트가 먼저 뜬다(harness safe-by-default). 실제 동작을 FINDINGS.md에 기록.

- [ ] **Step 3: 결정 확정 + 스펙 반영 표시**

FINDINGS.md에 기록:
- 프롬프트 뜸 → **D7 확정**: collaborator 보호는 harness 담당. README는 "훅이 뭘 하는지 + 비활성화법"만 설명하면 됨.
- 자동 실행됨 → **D7 강화 필요**: 스캐폴드를 opt-in-per-clone으로 못 함 → 대안 설계(예: 훅 대신 수동 `/docsherpa:doc-reconcile` 권장, prime을 훅에서 빼기)를 M1 전에 재설계. **이 경우 STOP·사용자 보고.**

- [ ] **Step 4: 커밋**

```bash
cd ~/Desktop/private/docsherpa
git add FINDINGS.md
git commit -m "spike: verify Claude Code hook-approval gate for cloned repos (D7)"
```

---

### Task 4: 마커 소비-증명 (D8 언어-불문 계약이 실제로 도는지)

spec D8·§6: doc-reconcile이 헤딩 문자열이 아니라 HTML 마커를 참조하고, gate가 마커 존재를 grep으로 검증하는 계약이 성립하는가?

**Files:**
- Create: `~/Desktop/private/docsherpa/skills/setup-docs/scripts/check_markers.py`
- Test: `~/Desktop/private/docsherpa/skills/setup-docs/scripts/test_check_markers.py`

**Interfaces:**
- Produces: `has_contract_markers(agents_md_text: str) -> bool` — 라우팅·인덱스 마커 둘 다 있는지. M1(doc-reconcile 마커 소비)과 M3(setup-docs 마커 삽입)이 공유하는 계약 검증기.

- [ ] **Step 1: 실패 테스트 작성 — 마커 있으면 True, 번역돼도 불변**

`test_check_markers.py`:
```python
from check_markers import has_contract_markers

ROUTING = "<!-- docsherpa:routing -->"
INDEX = "<!-- docsherpa:index -->"

def test_markers_present_survive_translation():
    # 헤딩이 영어로 번역돼도 마커가 있으면 계약 유지
    md = f"## Document Routing Rules {ROUTING}\n...\n## Read First {INDEX}\n..."
    assert has_contract_markers(md) is True

def test_missing_marker_fails():
    md = "## 문서 라우팅 룰\n...\n## 먼저 읽기\n..."   # 헤딩만, 마커 없음
    assert has_contract_markers(md) is False
```

- [ ] **Step 2: 실패 확인**

Run: `cd ~/Desktop/private/docsherpa/skills/setup-docs/scripts && python3 -m pytest test_check_markers.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'check_markers'`.

- [ ] **Step 3: 최소 구현**

`check_markers.py`:
```python
"""언어-불문 섹션 계약 검증 — doc-reconcile이 의존하는 마커가 AGENTS.md에 있는지."""

ROUTING_MARKER = "<!-- docsherpa:routing -->"
INDEX_MARKER = "<!-- docsherpa:index -->"

def has_contract_markers(agents_md_text: str) -> bool:
    return ROUTING_MARKER in agents_md_text and INDEX_MARKER in agents_md_text
```

- [ ] **Step 4: GREEN 확인**

Run: `python3 -m pytest test_check_markers.py -v`
Expected: 2 passed.

- [ ] **Step 5: 커밋**

```bash
git add skills/setup-docs/scripts/check_markers.py skills/setup-docs/scripts/test_check_markers.py
git commit -m "spike: language-agnostic marker contract check (D8)"
```

---

### Task 5: M0 종합 — FINDINGS 정리 + M1–M5 계획 갱신 지시

**Files:**
- Modify: `~/Desktop/private/docsherpa/FINDINGS.md`

- [ ] **Step 1: 확정된 미지수 요약**

FINDINGS.md 상단에 결정 표: ① 설치·네임스페이스 형태(T1) ② settings.json = 표준 JSON인가 JSONC인가(T2·포맷 전략) ③ 훅-승인 게이트 동작·D7 확정/강화(T3) ④ 마커 계약 성립(T4).

- [ ] **Step 2: 스펙 §14 이연 항목 중 M0가 닫은 것 표시**

닫힘: settings 병합 코어(dedup·파일선택) · 마커 소비 계약 · 훅 신뢰 모델. 남음(M1–M5): CLAUDE.md 엣지, fixture 구체 산출물, provenance CI 게이트.

- [ ] **Step 3: 커밋 + STOP (사용자 보고)**

```bash
git add FINDINGS.md && git commit -m "spike: M0 findings — unknowns resolved, ready to plan M1-M5"
```
M0 완료. **STOP** — FINDINGS를 사용자에게 보고하고, 그 결정으로 M1–M5 상세 계획을 별도 작성한다(특히 T3가 D7 강화를 요구하면 재설계 먼저).

---

## Self-Review

**Spec coverage:** M0 스펙 §12의 세 미지수(훅·병합·설치)를 T1(설치)·T2(병합)·T3(훅)이 커버. D8 마커는 T4. §14 이연 중 M0-닫힘 항목을 T5가 명시. M1–M5는 의도적으로 이 플랜 밖(spike-first).

**Placeholder scan:** `<이름/핸들>`은 사용자 입력(spec §11 명시) — 코드 placeholder 아님. 그 외 TBD/TODO 없음. 실험 태스크(T1·T3)는 "관찰→FINDINGS 기록"이 구체 산출물이라 placeholder 아님.

**Type consistency:** `merge_hook(settings,command)->(dict,bool)` · `merge_settings_file(claude_dir,command)->bool` · `has_contract_markers(text)->bool` — 태스크 간 시그니처 일관. `_norm`은 T2 내부 일관 사용.
