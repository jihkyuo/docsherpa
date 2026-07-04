# M1 — doc-reconcile 이식화 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 진짜 스킬(setup-docs 자산 + doc-reconcile)을 docsherpa repo로 가져오고, doc-reconcile을 **스택-불문·언어-불문**으로 이식 가능하게 만든다(phantom 트리거 제거 + 마커 계약 + 앵커 범용화). 산출물 = docsherpa 안에 사는 "이식된 doc-reconcile" + 그 이식성을 강제하는 CI 가드.

**Architecture:** setup-docs의 도메인-무관 자산(SKILL.md·knowledge.md·gate.py·content_oracle.py)은 **as-is 복사**(감사 통과분). doc-reconcile SKILL.md는 second-brain에서 baseline으로 가져와 **surgical 편집**으로 일반화한다. "이식됨"의 정의는 산문이 아니라 **가드 테스트**(도메인 리터럴 0 + phantom 문자열 0 + 마커 참조 존재)로 고정한다 — 편집이 가드를 GREEN으로 만들 때까지.

**Tech Stack:** Claude Code 플러그인, Python 3(가드 테스트, `uv run --with pytest pytest`), git. 산문 스킬은 유닛테스트 불가 → 검증은 grep 기반 가드.

## Global Constraints

- docsherpa repo 루트: `~/Desktop/private/docsherpa`.
- 테스트 실행: `uv run --with pytest pytest <file> -v` (repo에 venv 안 만듦 — M0 확립).
- RED-first: 가드 테스트를 먼저(baseline에서 FAIL) → 편집으로 GREEN.
- 커밋은 논리 단위마다. `git add -A` 금지.
- **정본(플러그인 안) doc-reconcile은 절대 프로젝트 리터럴을 담지 않는다**(spec §6 OSS 역누출 방지). 가드가 강제.
- 마커 계약(spec D8): `<!-- docsherpa:routing -->` · `<!-- docsherpa:index -->` (M0 `check_markers.py`와 동일 문자열).
- 소스 경로: setup-docs = `~/.claude/skills/setup-docs/`, doc-reconcile = `~/Desktop/private/second-brain/.claude/skills/doc-reconcile/SKILL.md`.

---

### Task 1: setup-docs 도메인-무관 자산 landing (as-is)

감사에서 도메인 무관 확인된 파일들을 docsherpa로 복사. gate.py/content_oracle는 이미 M0 scripts/에 없음 — 여기서 진짜 것을 가져온다.

**Files:**
- Create: `~/Desktop/private/docsherpa/skills/setup-docs/SKILL.md` (복사)
- Create: `~/Desktop/private/docsherpa/skills/setup-docs/reference/knowledge.md` (복사)
- Create: `~/Desktop/private/docsherpa/skills/setup-docs/scripts/gate.py` (복사)
- Create: `~/Desktop/private/docsherpa/skills/setup-docs/scripts/content_oracle.py` (복사)
- Create: `~/Desktop/private/docsherpa/skills/setup-docs/scripts/test_content_oracle.py` (복사)

**Interfaces:**
- Produces: docsherpa 안의 setup-docs 스킬 baseline(M3에서 설치자로 확장). gate.py `main()` · content_oracle CLI는 그대로.

- [ ] **Step 1: 파일 복사**

```bash
SRC=~/.claude/skills/setup-docs
DST=~/Desktop/private/docsherpa/skills/setup-docs
mkdir -p "$DST/reference" "$DST/scripts"
cp "$SRC/SKILL.md" "$DST/SKILL.md"
cp "$SRC/reference/knowledge.md" "$DST/reference/knowledge.md"
cp "$SRC/scripts/gate.py" "$DST/scripts/gate.py"
cp "$SRC/scripts/content_oracle.py" "$DST/scripts/content_oracle.py"
cp "$SRC/scripts/test_content_oracle.py" "$DST/scripts/test_content_oracle.py"
ls -R "$DST"
```

- [ ] **Step 2: content_oracle 테스트가 새 위치에서 통과 확인 (회귀 없음)**

Run: `cd ~/Desktop/private/docsherpa/skills/setup-docs/scripts && uv run --with pytest pytest test_content_oracle.py -q`
Expected: 전부 PASS (도메인 무관이라 위치 이동에 불변).

- [ ] **Step 3: 커밋**

```bash
cd ~/Desktop/private/docsherpa
git add skills/setup-docs/SKILL.md skills/setup-docs/reference/ skills/setup-docs/scripts/gate.py skills/setup-docs/scripts/content_oracle.py skills/setup-docs/scripts/test_content_oracle.py
git commit -m "M1: land domain-agnostic setup-docs assets (SKILL, knowledge, gate, content_oracle) as-is"
```

---

### Task 2: doc-reconcile baseline landing + 이식성 가드 테스트 (RED)

second-brain의 doc-reconcile을 baseline으로 가져오고, "이식됨"을 정의하는 가드 테스트를 작성한다. baseline은 도메인 리터럴·phantom을 담고 있으므로 가드는 **FAIL해야 한다**(RED).

**Files:**
- Create: `~/Desktop/private/docsherpa/skills/doc-reconcile/SKILL.md` (복사 baseline)
- Create: `~/Desktop/private/docsherpa/skills/setup-docs/scripts/test_doc_reconcile_portable.py`

**Interfaces:**
- Produces: `test_doc_reconcile_portable.py` — 이식성 계약. Task 3이 이걸 GREEN으로 만든다. M2/M3도 이 가드에 의존.

- [ ] **Step 1: baseline 복사**

```bash
mkdir -p ~/Desktop/private/docsherpa/skills/doc-reconcile
cp ~/Desktop/private/second-brain/.claude/skills/doc-reconcile/SKILL.md \
   ~/Desktop/private/docsherpa/skills/doc-reconcile/SKILL.md
```

- [ ] **Step 2: 이식성 가드 테스트 작성**

`~/Desktop/private/docsherpa/skills/setup-docs/scripts/test_doc_reconcile_portable.py`:
```python
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent.parent / "doc-reconcile" / "SKILL.md"

# 명백한 second-brain 도메인 리터럴 + phantom 트리거 문자열 (큐레이팅 — 일반 doc명 SPEC.md 등은 제외)
FORBIDDEN = [
    "bge-m3", "edge type", "config.py", "text-embedding-3-large",
    "confidentiality", "second-brain", "pre-commit docs-impact",
    "voice firewall", "synthesized thought",
]

def test_no_domain_literals():
    text = SKILL.read_text(encoding="utf-8")
    hits = [w for w in FORBIDDEN if w in text]
    assert hits == [], f"정본 doc-reconcile에 도메인 리터럴 누출: {hits}"

def test_references_language_agnostic_markers():
    text = SKILL.read_text(encoding="utf-8")
    assert "docsherpa:routing" in text, "라우팅 마커 참조 없음(헤딩 문자열 의존 의심)"
    assert "docsherpa:index" in text, "인덱스 마커 참조 없음"
```

- [ ] **Step 3: RED 확인 (baseline은 이식 불가)**

Run: `cd ~/Desktop/private/docsherpa/skills/setup-docs/scripts && uv run --with pytest pytest test_doc_reconcile_portable.py -v`
Expected: 둘 다 FAIL — `test_no_domain_literals`는 `edge type`·`config.py`·`pre-commit docs-impact` 등 검출, `test_references_...markers`는 마커 없음.

- [ ] **Step 4: 커밋 (RED 상태 고정)**

```bash
cd ~/Desktop/private/docsherpa
git add skills/doc-reconcile/SKILL.md skills/setup-docs/scripts/test_doc_reconcile_portable.py
git commit -m "M1: land doc-reconcile baseline + portability guard (RED — baseline not yet portable)"
```

---

### Task 3: doc-reconcile 일반화 — 가드를 GREEN으로

baseline SKILL.md를 surgical 편집해 (a) phantom 트리거 제거 (b) 앵커 범용화 (c) 마커 참조로 전환. 가드가 GREEN이면 이식 완료.

**Files:**
- Modify: `~/Desktop/private/docsherpa/skills/doc-reconcile/SKILL.md`

**Interfaces:**
- Consumes: Task 2의 가드 테스트.
- Produces: 이식된 doc-reconcile SKILL.md — M3(설치자가 스캐폴드)·M2(fixture 검증)가 사용.

- [ ] **Step 1: phantom 트리거 제거 (spec D9)**

`description` frontmatter에서 phantom 게이트 언급 삭제. 원문:
> `... pre-commit docs-impact 게이트가 커밋을 막았을 때, 또는 SessionStart doc-drift prime이 이 스킬을 가리킬 때도 사용. ...`
로 시작하는 문장을 → 다음으로 교체:
> `... SessionStart doc-drift prime이 이 스킬을 가리킬 때, 또는 변경을 마무리·커밋하기 전에 수동으로 사용. ...`
그리고 본문에서 "pre-commit docs-impact 게이트"를 언급하는 다른 라인도 SessionStart+수동 트리거로 좁힌다. (그 게이트는 미구현·보류 — spec §6/D9.)

- [ ] **Step 2: 섹션명 참조 → 마커 (spec D8)**

doc-reconcile이 AGENTS.md의 `## 문서 라우팅 룰`·`## 먼저 읽기` **헤딩 문자열**을 자연어로 참조하는 곳(예: "AGENTS.md '문서 라우팅 룰'·'먼저 읽기 인덱스'")을, **마커 참조**로 바꾼다:
> `AGENTS.md의 라우팅 마커(<!-- docsherpa:routing -->)와 인덱스 마커(<!-- docsherpa:index -->)가 가리키는 섹션 — 헤딩이 번역/재작성돼도 마커로 찾는다.`
(setup-docs가 그 마커를 헤딩 옆에 심는다 — M3.)

- [ ] **Step 3: 앵커 범용화 (spec §6 목록)**

"자주 새는 앵커"·"손대지 말 것"·"Common Mistakes"의 second-brain 예시를 일반형으로 교체:
- `config.py 상수 → SPEC.md의 그 수치` → `상수/설정 파일 변경 → 그 수치를 담은 스펙 문서(있으면)`
- `provider/model/tier·edge type 등 구조 변경 → 관련 ADR` → `구조 상수/타입 변경 → 관련 ADR`
- `새 prod 모듈 → ARCHITECTURE.md 코드맵 행` → `새 모듈 → 코드맵 문서(있으면)의 행`
- `CONCEPTS "complex 3개" ← config는 4개` 예시 → `[프로젝트 예시: 편집하는 줄의 숫자를 코드/설정에 대조]`(구체 수치 제거)
- 손대지 말 것의 `GIT.md Co-Authored-By`·`text-embedding-3-large`·`edge 엔티티` → 원칙만 남기고 예시 삭제 또는 `[예시]` 마킹
- Common Mistakes의 `Claude/Haiku/Sonnet 잔재`·openai 예시 → `provider 이름 잔재(예: 모델명)`
- **graceful degrade 명시:** 대상 문서가 없으면 앵커 라인을 `<!-- TODO -->`로 남기지 말고 **생략**(hollow 방지, spec §6).

- [ ] **Step 4: GREEN 확인**

Run: `cd ~/Desktop/private/docsherpa/skills/setup-docs/scripts && uv run --with pytest pytest test_doc_reconcile_portable.py -v`
Expected: 2 passed — 도메인 리터럴 0, 마커 참조 존재. FAIL이면 검출된 리터럴을 마저 제거/일반화.

- [ ] **Step 5: 척추 보존 육안 확인 (회귀 방지)**

Read `skills/doc-reconcile/SKILL.md`. 확인: 양방향(갱신+신설) · spec≠ADR · "배웠나" 트리거 · 도달성 closeout · anti-hallucination **6개 척추가 그대로 있는가**. 하나라도 편집 중 사라졌으면 복원. (가드는 리터럴만 보지 척추 존재는 안 봄 — 이 육안 체크가 그 갭을 메움.)

- [ ] **Step 6: 커밋**

```bash
cd ~/Desktop/private/docsherpa
git add skills/doc-reconcile/SKILL.md
git commit -m "M1: generalize doc-reconcile — remove phantom trigger, marker refs, generic anchors (guard GREEN)"
```

---

### Task 4: M1 종료 — 전체 가드 통과 확인 + 다음(M3) 지시

**Files:**
- Modify: `~/Desktop/private/docsherpa/FINDINGS.md` (M1 완료 기록)

- [ ] **Step 1: 전체 스크립트 테스트 GREEN 확인**

Run: `cd ~/Desktop/private/docsherpa/skills/setup-docs/scripts && uv run --with pytest pytest -q`
Expected: merge_settings(3) + check_markers(2) + content_oracle(N) + doc_reconcile_portable(2) 전부 PASS.

- [ ] **Step 2: FINDINGS에 M1 완료 한 줄 + 다음 단계**

FINDINGS.md 하단에: "M1 완료 — doc-reconcile 이식됨(가드 GREEN), setup-docs 자산 landing. 다음 = **M3 설치자**(setup-docs가 마커 삽입 + 루프 스캐폴드 + merge_settings 통합 + CLAUDE.md 주입). 그 다음 M2(end-to-end fixture, 설치자 필요)."

- [ ] **Step 3: 커밋**

```bash
cd ~/Desktop/private/docsherpa
git add FINDINGS.md
git commit -m "M1: complete — doc-reconcile portable, ready for M3 installer"
```

---

## Self-Review

**Spec coverage:** spec §6(doc-reconcile 이식화: phantom제거 D9 · 마커 D8 · 앵커 범용화 · graceful degrade · OSS 역누출 가드) → Task 2-3. setup-docs 자산 landing(§4 트리 as-is) → Task 1. M2(fixture)·M3(설치자)·M4·M5는 의도적으로 이 플랜 밖(재-시퀀싱: M1→M3→M2→M4→M5).

**Placeholder scan:** `<!-- TODO -->`는 doc-reconcile의 graceful-degrade **금지 패턴 예시**로 언급된 것(플랜 placeholder 아님). `[프로젝트 예시]`·`[예시]`는 일반화 산출물의 의도된 자리표시(생성 산문). 그 외 TBD/미완 없음. 편집 대상 문자열은 spec §6에서 그대로 인용.

**Type consistency:** 가드 마커 문자열 `docsherpa:routing`·`docsherpa:index`는 M0 `check_markers.py`(`<!-- docsherpa:routing -->`)와 동일. `test_doc_reconcile_portable.py`의 SKILL 경로(`../../doc-reconcile/SKILL.md` = scripts→setup-docs→skills→doc-reconcile)는 Task 1/2가 만든 트리와 일치.

**주의(구현자에게):** Task 3은 산문 편집이라 가드(리터럴 grep)만으론 척추 손실을 못 잡는다 → Step 5 육안 체크가 필수 게이트. 가드 GREEN ≠ 방법론 온전. (spec §9 parity 교훈의 축소판.)
