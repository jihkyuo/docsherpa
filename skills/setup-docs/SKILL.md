---
name: setup-docs
description: 프로젝트 문서를 일관 아키텍처(AGENTS.md 라우터 + decisions/·how-to/ + 도달성 불변식)로 세우거나 정비한다. 새 프로젝트 셋업, 또는 기존 문서가 뒤죽박죽이라 재배치가 필요할 때 사용.
---

# setup-docs

## Overview

AI 에이전트가 **진입 파일 하나에서 링크를 타고 필요한 문서에 도달**하도록 문서 골격을 세운다:
*얇은 진입 라우터 + 맵 중추 문서(routing·index home) + 필요할 때 로드 + 끊김 없는 도달성*. 폴더는 "함께 읽어야 할 문서"가
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
3. **성장 루프 존재 확인**(`ls` 수준, spec §7.4 — 별도 스크립트 안 만듦): `.claude/doc-drift-prime.txt` ·
   `.claude/settings.json`의 SessionStart 훅 · `.claude/skills/doc-reconcile/SKILL.md` 3종이 있는지.
   없으면 아래 "성장 루프 설치" 대상. (HEALTHY 판정도 루프 부재면 "골격은 건강, 루프 미설치"로 분리 보고.)
4. 상태 분류 → 분기:

| 상태 | 조건 | 동작 |
|---|---|---|
| GREENFIELD | 라우터 없음 + docs 최소 | 조용히 설치(아래 "GREENFIELD 경로") — 묻지 않는다 |
| HEALTHY | 라우터 + gate PASS + 안티패턴 0 | "건강함" 보고 + 우리 아키텍처 기준 개선점만 |
| MESSY | docs 있음 + (gate FAIL 또는 안티패턴≥1) | 아래 "MESSY — 진단-주도 제안 + 2차선" |

도메인 지식·진단 휴리스틱: [reference/knowledge.md](reference/knowledge.md) 참조.

### 진단-주도 제안 (자세) — ADR 0014

진단이 자세를 정한다. 경직된 게이트가 아니라 판단으로 **제안**하라 — 정본 결정(map 중추·성장 루프)을
사용자에게 위임(선택지로 나열)하지 말고, 상태에 맞는 제안을 **권장 형태로** 낸다.

- **GREENFIELD** → 조용히 설치. 질문 없음.
- **MESSY·중구난방**(보강조차 어려운 혼돈) → 선택지 **주지 마라.** "마이그레이션이 불가피한 이유"를
  쉽게 고지하고 **승인만** 구한다. migrate 적극 권장.
- **MESSY·자체구조 있음**(합리적이나 우리와 다름) → **migrate와 보강이 실제로 다른가(=이동/구조
  재편이 필요한가)로 권장을 가른다:** ①**이동 필요** → migrate vs 보강 **선택지 제시** + 트레이드오프
  쉽게 설명 + **migrate 권장**(구조 이득이 실재). ②**이동 0**(둘이 같은 경량 작업으로 붕괴) → 억지
  선택지 만들지 말고 **경량 정비 한 계획**을 제안(spine·루프 포함). **migrate를 밀지 마라** — 실익
  없이 diff·리스크만 커진다.
- **MESSY·드리프트된 docsherpa**(우리 loop·라우터는 있는데 gate FAIL·spine 없음·마커 없음) →
  migrate-vs-보강 프레이밍 **아님**(이미 우리 것). 우리 아키텍처 **복구/완성**: 인라인 인덱스면
  `migrate_inline_to_map`로 비파괴 이관 + 도달성 교정 + **기존 loop 유지**(재설치 아님). 경량 차선.
- **HEALTHY** → 우리 아키텍처 기준 개선점 리뷰. 없으면 "건강함".

**무조건(질문·스킵 대상 아님):** map 중추(spine)·성장 루프는 **어느 경로든 항상** 설치한다 —
"설치할까요"를 묻지 마라. (트러스트는 유지: 무엇을 쓸지 고지 + 훅-승인 게이트 — D7. **"필수 기능"과
"보안 투명성"은 별개 축**이다.) **보강(reinforce)** = 기존 폴더를 그대로가 아니라 *크게 벗어나지 않는
선에서 최소공수 재조정* + 트레이드오프 명시 + migrate 유도.

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
4. **맵 중추 문서 생성 + 진입파일 맵 링크** (아래 맵 문서 템플릿). routing·index는 `docs/_map.md`에,
   진입파일엔 `docsherpa:map` 링크 한 줄만(N11·ADR 0011).
5. **빈칸 채움.** 명령어·스택은 코드 읽어 채운다. 못 채우면 `<!-- TODO: ... -->`로 명시.
6. **무결성 게이트.** `scripts/gate.py` 실행 → broken=0·orphan=0·도달성=100%. 실패 시 **STOP·보고**.

### 성장 루프 설치 (필수 — spec §7·D7·ADR 0014)

문서 골격이 서면, doc-reconcile 성장 루프를 target repo에 **커밋 스캐폴드**한다(collaborator가
플러그인 없이도 규율을 얻도록 — D2). **필수다 — "설치할까요/스킵"을 묻지 마라(ADR 0014).** 단
무엇을 쓸지 먼저 보여주고 승인받는다(트러스트 — *스킵 선택*이 아니라 *고지·승인*; D7).

1. **계획 diff-preview.** 쓸 파일 목록을 먼저 보여준다:
   - `.claude/skills/doc-reconcile/SKILL.md` (플러그인 정본 복사 + version stamp)
   - `.claude/doc-drift-prime.txt` (`<skill>/templates/doc-drift-prime.txt` 복사)
   - `.claude/settings.json` (SessionStart 훅 **병합** — 덮어쓰기 아님)
   - `CLAUDE.md` (`@AGENTS.md` 안전 주입 — 기존 보존)
2. **비대화형 fallback(§7.1).** 대화형이 아니면(headless/CI) 기본 **dry-run**: 위 계획만 출력하고
   **아무것도 쓰지 않는다.** 실제 쓰기는 명시 승인(`--yes` 상당의 사용자 확정) 후에만.
3. **결정론적 설치 실행.** 승인(대화형) 또는 `--yes`(비대화형) 후,
   `<skill>/scripts/scaffold.py`의 `scaffold(repo_root, project_name=...)`를 호출한다. 이 함수가
   결정론적으로: 라우터 생성(맵 링크, 기존 보존·append) + **맵 중추 문서 생성**(`write_map` — `docs/_map.md`) + `docs/decisions`·`docs/how-to` 골격 +
   `inject_claude_md_file`로 CLAUDE.md 안전 주입(없음/import/prepend/BOM/frontmatter) +
   `merge_settings_file`로 **`settings.json`(공유)** 훅 멱등 병합(기존 보존·dedup, `.local` 금지 D2) +
   prime/doc-reconcile 복사(+`<!-- docsherpa-scaffold: v<version> -->` 스탬프)를 수행하고, 무엇이
   바뀌었는지 dict로 보고한다. **재실행 정책(R4):** 이미 있는 파일은 스캐폴드가 덮지 않는다(no-op/append);
   로컬 편집 감지 시 **skip + diff 표시**, 조용한 overwrite 금지. ⚠️ `settings.json`이 JSONC면
   `merge_settings_file`가 `ValueError`로 거부 → 그 메시지로 사용자에게 수동 병합을 안내한다.
4. **프로젝트 빈칸 채움(산문).** scaffold가 만든 라우터의 `[채움]`(항시룰·명령어)을 스택 신호로 채운다.
   확신되는 것만, 불확실하면 생략(hollow 방지). 기존 라우터였으면 append된 중복 섹션을 사용자와 상의해 정리.
5. **doc-reconcile 앵커 특화(§7.5 — 코드 없이 에이전트 판단).** 설치된
   `.claude/skills/doc-reconcile/SKILL.md`의 `<!-- docsherpa:anchors:start -->`~`:end` 경계 안 앵커를,
   **target repo의 실제 문서 트리(AGENTS.md·`docs/`)를 직접 보고** 특화한다:
   - 앵커 대상을 **실재하는 정확한 repo-상대 경로(대소문자까지)**로만 바꾼다 (예: `docs/DESIGN.md`,
     `docs/decisions/`). 트리에 안 보이는 경로는 절대 쓰지 마라.
   - 정확히 대응하는 문서가 없으면 그 앵커는 **일반형 그대로 둔다** — 대체 문서를 지어내지 마라(hollow 방지).
   - **뼈대(`→` 앞뒤 구조)는 유지, 대상 경로만** 갈아끼운다.
   - 특화는 **target 사본에만** — 정본 `skills/doc-reconcile`는 generic 유지(가드가 강제).
6. **훅 신뢰 투명성(D7).** prime은 커밋된 신뢰 경계임을 사용자에게 알린다: SessionStart에 `cat`
   한 줄이 붙고, collaborator가 clone하면 Claude Code 훅-승인 게이트가 첫 실행 전 승인을 요구한다
   (harness safe-by-default). 비활성화는 settings.json에서 그 훅 항목 삭제.
7. **스캐폴드 검증.** `python3 <skill>/scripts/gate.py <repo> --require-markers` → broken=0·orphan=0
   **+ 마커 계약 PASS**. 실패 시 STOP·보고.

### 멱등 · 병합 규칙 (다시 돌려도 안전)

**클로버 금지 — 덮지 말고 병합·보존.**

- **기존 `AGENTS.md` 있으면:** 기존 항시룰·명령어를 **보존**한다. 맵 링크(`<!-- docsherpa:map -->`)
  섹션이 **없을 때만** 추가하고, 이미 계약(맵 링크 or 기존 인라인 마커)이 있으면 skip.
- **마커 계약(D8·ADR 0011):** routing·index 마커는 **맵 중추 문서 `docs/_map.md`** 에 산다(진입파일
  인라인 아님). 진입파일엔 맵으로 가는 링크 한 줄 + `<!-- docsherpa:map -->` 마커만. **그린필드**는
  `scaffold`(`write_router`+`write_map`)가 맵을 만들고, **기존 인라인-마커 repo**는
  `scaffold.migrate_inline_to_map`이 비파괴로(내용 verbatim 이동·링크 URL만 재작성, content_oracle
  무손실) 맵으로 이관한다. home(두 마커를 헤딩 줄에 함께 가진 문서)은 도달 가능 문서 중 **정확히
  1개**여야 하며 `gate.py --require-markers`가 강제한다.
- **`CLAUDE.md`:** 없으면 `@AGENTS.md` 한 줄로 생성. 있고 이미 `@AGENTS.md`를 import하면 그대로 둔다.
- **`docs/decisions/`:** 디렉터리 있으면 `_template.md`·`README.md` 중 **없는 것만** 생성.
- **`docs/how-to/`:** `_README.md` 없을 때만 생성.
- **2회차 실행 = 변경 0.** 게이트는 항상 다시 돌려 PASS 확인.

### AGENTS.md 템플릿 (`[채움]`만 프로젝트별)

> **정본은 `scripts/scaffold.py`의 `router_skeleton()`** — 아래 블록은 구조 설명용. 실제 생성은 scaffold가 한다. routing·index 마커는 진입파일이 아니라 아래 **맵 중추 문서**에 산다(N11·ADR 0011).

```markdown
# [프로젝트명] 에이전트 가이드
> 진입 라우터. 상세는 docs/를 필요할 때만 읽는다.

## 항시 룰
- 패키지/언어/배포: [채움]
- [프로젝트 고유 철칙: 채움, 없으면 줄 삭제]

## 명령어
- [채움: build/test/dev/lint — 못 찾으면 <!-- TODO -->]

## 문서 지도 <!-- docsherpa:map -->
- 라우팅·인덱스 → [문서 지도](docs/_map.md)
```

⚠️ **인덱스 항목은 반드시 markdown 링크 `[라벨](경로)` 형태로 쓴다** — 게이트는 `](경로)`와
`@import`만 따라간다. 평문 화살표(`→ docs/x.md`)는 링크로 안 잡혀 **고아 판정**된다. 디렉터리는
trailing slash(`[docs/how-to/](docs/how-to/)`)로 — 게이트가 그 안 `_README.md`로 도달한다.
`[있으면]` 표시 항목은 대상 파일이 없으면 **줄을 통째로 삭제**(broken 링크 방지).

`CLAUDE.md` 전체 = `@AGENTS.md` (한 줄). 다른 에이전트 파일(`GEMINI.md` 등)도 같은 패턴.

### 맵 중추 문서 템플릿 (`docs/_map.md`)

> **결정론 코어**(index의 decisions·how-to 링크 + routing 룰 전체)의 정본은 `scripts/scaffold.py`의 `_MAP_DOC` — scaffold가 생성한다. 아래 예시의 `[있으면만]`·`[채움]` 인덱스 줄(코드 맵·reference 문서)은 **에이전트가 프로젝트에 맞게 추가**한다(hollow 방지 — 확신되는 것만). 진입파일이 `docsherpa:map` 링크로 이 파일을 가리킨다. 맵이 `docs/` 안에 사므로 인덱스 링크는 `docs/` 접두어 없이 쓴다(gate는 링크 담은 파일 기준 해석; 루트 파일은 `../`).

```markdown
# 문서 지도 (라우팅·인덱스)

> 진입 라우터가 이 파일을 가리킨다. 상세는 필요할 때만 읽는다.

## 먼저 읽기 (문서 인덱스 — 진입점만, 린) <!-- docsherpa:index -->
- 코드 맵 → [코드 맵](ARCHITECTURE.md)            [있으면만 — 없으면 줄 삭제]
- 결정 기록(ADR) → [결정 기록](decisions/README.md)
- 작업 가이드 → [작업 가이드](how-to/)
- [프로젝트 reference 문서: 채움]

## 문서 라우팅 룰 (새 문서가 어디로) <!-- docsherpa:routing -->
분류 순서대로 판정(위에서 먼저 맞는 것):
1. 구조적 결정(왜) → decisions/NNNN-*.md (_template 복사) + README 로그 추가
2. 제품 요구(왜 만드나·누구에게·성공/수용 기준) → product/*.md (여러 개면 _README 인덱스화)
3. 절차/복구(어떻게) → how-to/*.md (3개↑면 _README 인덱스화)
4. 기능 스펙(무엇을) → specs/<feature>/ + plans/
5. 함께 읽혀야 할 문서 ≥2개(co-change) → <topic>/ 승격, 리드 문서가 인덱스
6. 그 외 단일 reference/explanation → 평면 [디폴트]
※ PRD(제품의 왜)와 ADR(기술선택의 왜)는 다른 도달성 트리 — 구조적 결정은 PRD가 있어도 ADR 병렬 신설.
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

성장 루프를 설치한 경우 `--require-markers`를 붙여 마커 계약(D8)까지 검증한다
(`gate.py <repo> --require-markers`). 스캐폴드 전 순수 골격 검증은 플래그 없이 돌린다.

---

## MESSY — 진단-주도 제안 + 2차선 (ADR 0014)

> **인라인→맵 spine 이관은 별도 경로**: 기존 인라인 마커 repo(gate는 통과하는 HEALTHY)를 맵 구조로
> 옮기는 건 `scaffold.migrate_inline_to_map`(결정론·비파괴·content_oracle 무손실)이 처리한다 —
> 아래 재편 파이프라인과 구분(N11·ADR 0011).

먼저 **자세**(위 "진단-주도 제안")로 *무엇을 제안할지* 정하고, **차선**으로 *어떻게 실행할지* 정한다.

### 차선 선택 — 옮길 게 있나?

**판정 룰: 파일을 실제로 *옮겨야* 하나?**
- **아니오 → 경량 차선.** 실패가 링크 포맷(평문 화살표·비-markdown 링크) 또는 인덱스 미등록뿐이고
  문서 오분류·결합 흩기가 없으면: **worktree·content_oracle 불필요.** 링크를 markdown으로 교정 +
  누락 인덱스 체인/README 신설(고아 제거) + map 중추·성장 루프 설치 + `gate --require-markers`. 끝.
- **예 → 무거운 차선.** 문서가 실제로 이동/승격해야 하면(결합 흩기·타입폴더 분산): 아래 재배치 파이프라인.

⚠️ **잘 정리된 트리인데 링크만 깨진 흔한 케이스를 무거운 차선으로 끌고 가지 마라** — 인덱스 파일
*추가*(이동 0)로 도달성이 복구된다. (fresh 베이스라인이 정확히 이 과오를 범했다 — ADR 0014.)

**링크 교정 — 실패 유형을 가려라(broken link):**
- **포맷-깨짐**(평문 화살표·백틱, 타겟은 존재) → markdown 링크로 교정.
- **타겟-소실**(링크 대상이 삭제/이동됨): ①현행 문서 + 살아있는 등가물 존재 → repoint. ②**동결 역사
  문서**(날짜박힌 `specs/`·`plans/`)의 타겟-소실 → **de-link**(`[라벨](경로)` → 백틱 텍스트; 기록은
  보존, gate는 통과). **repoint·삭제 금지** — 그 문서는 *당시 상태*를 기록한 것이라 고치면 역사를
  falsify한다(doc-reconcile "역사 동결 문서 손대지 마라"와 정합).

### 무거운 차선 — 재배치 파이프라인 (이동 있을 때만)

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
- **settings.local.json에 훅 씀** → D2 위반. 반드시 공유 `settings.json`(collaborator가 못 받음).
- **마커 없이 라우팅/인덱스 섹션 생성** → doc-reconcile이 섹션을 못 찾음(D8). 헤딩에 마커 필수.
- **기존 CLAUDE.md/settings.json 덮어씀** → 병합·주입 함수로만 건드린다(inject_claude_md/merge_settings).
