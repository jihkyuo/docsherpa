---
name: setup-docs
description: 프로젝트 문서를 일관 아키텍처(AGENTS.md 라우터 + decisions/·how-to/ + 도달성 불변식)로 세우거나 정비한다. 새 프로젝트 셋업, 또는 기존 문서가 뒤죽박죽이라 재배치가 필요할 때 사용.
---

# setup-docs

## Overview

AI 에이전트가 **진입 파일 하나에서 링크를 타고 필요한 문서에 도달**하도록 문서 골격을 세운다:
*얇은 진입 라우터 + 필요할 때 로드 + 끊김 없는 도달성*. 폴더는 "함께 읽어야 할 문서"가
생길 때만 만든다. 동작은 **외과적·멱등** — 기존 문서가 있으면 덮지 않고 병합·보존한다.

**근거 정직성 (이 스킬의 철칙):** 원칙마다 근거등급 — 🟢권위 / 🟡판단 / 🔴열린질문.
도메인 지식·진단 휴리스틱 전체: [reference/knowledge.md](reference/knowledge.md) 참조.

## When to Use

- 새 프로젝트에 문서 구조를 처음 세울 때
- 흩어진 문서(고아 markdown, 비대한 README)를 라우터+인덱스로 정비할 때
- `AGENTS.md`/`CLAUDE.md` 진입점이 없거나 라우팅 룰이 없을 때

**When NOT:** 이미 라우터+인덱스+도달성이 갖춰진 repo (게이트만 돌려 확인하면 된다).

---

## Phase 0 — 진단 (항상 먼저)

1. `python3 <skill>/scripts/gate.py <repo>` 실행 → broken/orphan 측정.
2. 진입 라우터(AGENTS.md/CLAUDE.md)·docs 트리·안티패턴 스캔 (휴리스틱은 [reference/knowledge.md](reference/knowledge.md)).
3. 상태 분류 → 분기:

| 상태 | 조건 | 동작 |
|---|---|---|
| GREENFIELD | 라우터 없음 + docs 최소 | 빠른 스캐폴드(아래 "GREENFIELD 경로") |
| HEALTHY | 라우터 + gate PASS + 안티패턴 0 | "건강함" 보고 + 소소한 것만 |
| MESSY | docs 있음 + (gate FAIL 또는 안티패턴≥1) | 마이그레이션 파이프라인 |

도메인 지식·진단 휴리스틱: [reference/knowledge.md](reference/knowledge.md) 참조.

---

## GREENFIELD 경로

> 코드 언어/스택 무관(Python·JS·Go…). 산문은 프로젝트 언어에 맞추되, 라우팅 룰·게이트 구조는 그대로.

1. **프로젝트 파악.** 스택 신호 읽기(`package.json`·`pyproject.toml`·`go.mod`·`Cargo.toml`…),
   기존 `docs/`, 기존 `AGENTS.md`/`CLAUDE.md`, 명령어(scripts·Makefile·`uv`/`pnpm` 등).
2. **진입 라우터 생성/병합.** `AGENTS.md`(정본, 최광 호환) + `CLAUDE.md`는 `@AGENTS.md` 한 줄.
   기존 AGENTS.md 있으면 **병합·기존 룰 보존**(아래 멱등·병합 규칙). 골격은 아래 템플릿.
3. **docs/ 골격 스캐폴드 — 예상되는 것만.** `docs/decisions/`(`_template.md` + `README.md` 로그표),
   `docs/how-to/_README.md`(반드시 `PLACEHOLDER` 명시). **그 외 폴더는 만들지 않는다**(MVD).
   `decisions/README.md`는 본문에 **`_template.md`로 가는 markdown 링크**를 반드시 포함한다
   (예: "결정마다 [`_template.md`](_template.md)를 복사") — 안 하면 `_template.md`가 고아가 된다.
4. **라우팅 룰 + 도달성 불변식 삽입** (아래 라우팅 룰 블록 그대로).
5. **빈칸 채움.** 명령어·스택은 코드 읽어 채운다. 못 채우면 `<!-- TODO: ... -->`로 명시.
6. **무결성 게이트.** `scripts/gate.py` 실행 → broken=0·orphan=0·도달성=100%. 실패 시 **STOP·보고**.

### 멱등 · 병합 규칙 (다시 돌려도 안전)

**클로버 금지 — 덮지 말고 병합·보존.**

- **기존 `AGENTS.md` 있으면:** 기존 항시룰·명령어·인덱스를 **보존**한다. `## 문서 라우팅 룰`
  섹션이 **없을 때만** 추가하고, 있으면 skip. 새 인덱스 줄은 중복 없을 때만 append.
- **`CLAUDE.md`:** 없으면 `@AGENTS.md` 한 줄로 생성. 있고 이미 `@AGENTS.md`를 import하면 그대로 둔다.
- **`docs/decisions/`:** 디렉터리 있으면 `_template.md`·`README.md` 중 **없는 것만** 생성.
- **`docs/how-to/`:** `_README.md` 없을 때만 생성.
- **2회차 실행 = 변경 0.** 게이트는 항상 다시 돌려 PASS 확인.

### AGENTS.md 템플릿 (`[채움]`만 프로젝트별)

```markdown
# [프로젝트명] 에이전트 가이드
> 진입 라우터. 상세는 docs/를 필요할 때만 읽는다.

## 항시 룰
- 패키지/언어/배포: [채움]
- [프로젝트 고유 철칙: 채움, 없으면 줄 삭제]

## 명령어
- [채움: build/test/dev/lint — 못 찾으면 <!-- TODO -->]

## 먼저 읽기 (문서 인덱스 — 진입점만, 린)
- 코드 맵 → [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)            [있으면만 — 없으면 줄 삭제]
- 결정 기록(ADR) → [docs/decisions/README.md](docs/decisions/README.md)
- 작업 가이드 → [docs/how-to/](docs/how-to/)
- [프로젝트 reference 문서: 채움]

[여기에 아래 "문서 라우팅 룰" 블록 그대로 삽입]
```

⚠️ **인덱스 항목은 반드시 markdown 링크 `[라벨](경로)` 형태로 쓴다** — 게이트는 `](경로)`와
`@import`만 따라간다. 평문 화살표(`→ docs/x.md`)는 링크로 안 잡혀 **고아 판정**된다. 디렉터리는
trailing slash(`[docs/how-to/](docs/how-to/)`)로 — 게이트가 그 안 `_README.md`로 도달한다.
`[있으면]` 표시 항목은 대상 파일이 없으면 **줄을 통째로 삭제**(broken 링크 방지).

`CLAUDE.md` 전체 = `@AGENTS.md` (한 줄). 다른 에이전트 파일(`GEMINI.md` 등)도 같은 패턴.

### 문서 라우팅 룰 블록 (모든 프로젝트 동일 — 바꾸지 않음)

```markdown
## 문서 라우팅 룰 (새 문서가 어디로)
분류 순서대로 판정(위에서 먼저 맞는 것):
1. 구조적 결정(왜) → docs/decisions/NNNN-*.md (_template 복사) + README 로그 추가
2. 절차/복구(어떻게) → docs/how-to/*.md (3개↑면 _README 인덱스화)
3. 기능 스펙(무엇을) → docs/specs/<feature>/ + plans/
4. 함께 읽혀야 할 문서 ≥2개(co-change) → docs/<topic>/ 승격, 리드 문서가 인덱스
5. 그 외 단일 reference/explanation → docs/ 평면 [디폴트]
※ 증상 alias는 별도 troubleshooting 문서 말고 주인 문서(한계·개념)에 넣는다.

불변식: 새 문서는 반드시 위 인덱스에 등록(고아 방지) → broken=0·orphan=0 확인
```

### decisions/ 템플릿 (이대로 생성 — 빈칸만 채움)

`docs/decisions/_template.md`:

```markdown
# NNNN. [결정 제목]
- 상태: 제안 | 수락 | 폐기 | 대체됨(→ NNNN)
- 날짜: YYYY-MM-DD

## 맥락
[무엇이 이 결정을 강제했나 — 문제·제약]

## 결정
[무엇을 하기로 했나]

## 결과
[좋은 점·나쁜 점·트레이드오프]
```

`docs/decisions/README.md` (ADR 로그 — **반드시 `_template.md` 링크 포함**, 안 하면 고아):

```markdown
# 결정 기록 (ADR)
구조적 결정은 결정당 1파일 `NNNN-*.md`로 남긴다(append-only). 새 결정은
[`_template.md`](_template.md)를 복사해 만들고 아래 표에 한 줄 추가한다.

| # | 결정 | 상태 | 날짜 |
|---|------|------|------|
| — | (아직 없음) | — | — |
```

`docs/how-to/_README.md`:

```markdown
# 작업 가이드 (how-to)
<!-- PLACEHOLDER: 실제 절차(명령·진단·복구)가 생기면 *.md로 추가하고 여기 링크. 3개↑면 이 파일을 목록 인덱스로 전환. -->
```

### 무결성 게이트

`scripts/gate.py`를 repo 루트에서 실행한다:

```bash
python3 ~/.claude/skills/setup-docs/scripts/gate.py [REPO_ROOT]   # 기본: 현재 디렉터리
```

루트(`AGENTS.md`+`CLAUDE.md`)에서 `@import`와 `](X.md)` 링크를 BFS로 따라가:
- **broken link = 0** — 모든 `.md` 링크가 실제 파일로 해석.
- **orphan = 0 / 도달성 100%** — 모든 `docs/**/*.md`가 루트에서 도달 가능.

디렉터리 링크(`docs/how-to/`)는 그 안의 `_README.md`/`README.md`로 도달한 것으로 본다.
종료코드 0=PASS. **FAIL이면 멈추고 보고** — 조용히 고치지 않는다.

---

## 마이그레이션 파이프라인 (MESSY)

1. **진단 보고** — gate.py 출력 + 안티패턴 + 현재 트리를 아티팩트로 제시.
2. **목표 구조 제안 (자체검증 후)** — 제안 트리를 임시로 빌드해 gate.py + content_oracle 둘 다
   PASS함을 먼저 증명한 뒤 before/after + 이동 delta + 스코프(전면 재배치로 기울임) 제시.
3. **사용자 승인 게이트** — 스코프 조정 가능.
4. **계획 정식화** — superpowers:writing-plans 위임. 배치=독립 doc-group, 링크 리라이트 1급,
   worktree 여부(이동 있음 또는 ~10파일↑ → worktree) + 머지 타이밍 합의.
5. **사용자 계획 승인.**
6. **자율 실행** — superpowers:using-git-worktrees(필요 시) + superpowers:subagent-driven-development.
   배치마다: 이동+링크리라이트 → 두 oracle PASS → 다음. 실패=fix 루프. 유실위험=STOP.

### 두 oracle (배치 전진 = 둘 다 PASS)

- **도달성:** `python3 <skill>/scripts/gate.py <repo>` → broken=0·orphan=0.
- **내용보존:** base 스냅샷을 만들고(`git worktree add` 또는 마이그레이션 base 커밋을 별 디렉터리로
  `git --work-tree`로 체크아웃) `python3 <skill>/scripts/content_oracle.py check --base <base> --current <repo> --manifest <manifest.json>`.
  미분류 세그먼트 → FAIL. 매니페스트는 dropped(+사유)/transformed로 의도적 변경을 명시.

### STOP 조건 (자율 루프 멈추고 보고)

- content_oracle 미분류 세그먼트(유실 위험)
- gate.py가 2회 fix 후에도 0 못 만듦
- 이동이 기존 목적지 파일 덮어씀 / 매핑 모호(다중 후보)
- 승인된 계획 밖 범위 발견

---

## Common Mistakes

- **기존 AGENTS.md를 덮어씀** → 병합·보존 규칙 위반. 항시룰·명령어는 반드시 보존.
- **투기적 빈 폴더 생성**(`specs/`, `tutorials/`…) → MVD 위반. 예상되는 것(decisions·how-to)만.
- **새 문서를 인덱스에 등록 안 함** → 고아. 게이트 orphan>0로 잡힘.
- **근거등급 누락** → 🟡/🔴를 🟢인 척. 폴더화·1홉은 정설 아님을 명시.
- **게이트 FAIL을 조용히 우회** → STOP·보고가 원칙.
