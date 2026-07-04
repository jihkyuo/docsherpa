# docsherpa — 설계 (design spec) · rev3

> **에이전트-읽기용 문서 아키텍처를 세우고 스스로 자라게 하는 Claude Code 플러그인.**
> 영구 집: 이 repo `docs/DESIGN.md`. M0 spike 완료 — 실증 결과는 [FINDINGS.md](../FINDINGS.md).

- 상태: 제안 (rev3 — 이중 critic + codex 재검증 반영). M0 spike GREEN.
- 날짜: 2026-07-04
- 검증: `/codex`(외부 모델) + `architect`(인하우스 설계 critic) 교차 리뷰 1회. 수렴 이슈 5 + 각자 발견
  (phantom 게이트·훅 신뢰 모델)을 rev2에 반영. 상세 §13.

---

## 1. 배경 · 문제

second-brain repo는 강력한 문서 아키텍처를 갖고 있다: **얇은 진입 라우터(AGENTS.md) + 도달성
불변식(orphan=0) + 문서 라우팅 룰 + co-change 폴더링**. 두 스킬이 지탱한다:

- **`setup-docs`** (현재 global): 골격을 세운다 — 라우터·decisions/·how-to·게이트.
- **`doc-reconcile`** (현재 이 repo `.claude/skills/`): 매 변경 후 문서를 갱신+신설해 **자라게** 한다.
  SessionStart 훅(`doc-drift-prime.txt`)이 트리거, 게이트가 검증.

이 자산을 **공개 OSS로 발행**해 신규 프로젝트엔 보일러플레이트로, 기존 프로젝트엔
마이그레이션으로 작동시킨다(커리어 자산).

**현 걸림돌:** ① 소스가 둘로 흩어짐(global + project). ② `doc-reconcile`이 second-brain 도메인
예시로 laced돼 이식 불가. ③ `setup-docs`는 성장 루프 설치 능력 없음. ④ OSS 배포 껍데기 부재.
⑤ **doc-reconcile이 미구현 게이트를 트리거로 광고**(§6, phantom 게이트).

## 2. 목표 · 비목표

**목표**
- docsherpa 플러그인 하나로 배포: 1회 설치 → 각 프로젝트에서 `/docsherpa:setup-docs` → 문서 골격
  + 성장 루프를 target repo에 커밋 스캐폴드.
- `doc-reconcile`을 스택-불문·**언어-불문**으로 이식 가능하게.
- second-brain이 첫 고객(독푸딩): 플러그인이 단일 원본.
- OSS 자산 완비(MIT·README·CHANGELOG·provenance 감사).

**비목표**
- 멀티-플러그인 마켓플레이스(YAGNI).
- 문서 *사이트* 생성(docsify류).
- 보류된 pre-commit docs-impact 게이트 구현(§6 D9 — 의도적 보류 유지).
- 산문 스킬 방법론의 유닛테스트(불가; 검증은 fixture+gate 행동적).

## 3. 핵심 결정 (근거 포함)

> 각 결정의 **정본 ADR**은 [docs/decisions/](decisions/README.md)에 있다(라우팅 룰 #1 — 구조적 결정은 ADR). 아래는 요약 인덱스.

| # | 결정 | 근거 | 거부한 대안 |
|---|---|---|---|
| [D1](decisions/0001-single-plugin-repo-self-host.md) | 단일-플러그인 repo + `marketplace.json` self-host | 마켓플레이스가 같은 repo에 `source:"./"`로 공존 | 멀티-플러그인 모노레포(YAGNI) |
| [D2](decisions/0002-committed-scaffold-in-target.md) | **B: target repo에 커밋 스캐폴드**(self-contained) | public이라 collaborator가 플러그인 없이도 규율 획득 | A: 순수 플러그인 제공(클론자 규율 소실) |
| [D3](decisions/0003-dogfooding-single-source.md) | **독푸딩: 플러그인 = 단일 원본** | drift 0 + 포트폴리오 서사 | 포크(두 원본 drift) |
| [D4](decisions/0004-doc-reconcile-one-file-two-uses.md) | doc-reconcile = **한 파일, 두 쓰임**(척추+범용앵커, 스캐폴드 시 특화) | 유지보수 단순 + B·D3 화해 | 앵커 삭제(방법론 빈약) |
| [D5](decisions/0005-hooks-live-in-target-only.md) | **훅은 target repo에만 산다**(플러그인은 훅 *템플릿*만 담음) | 문서 없는 repo에서 prime 오발동 방지 | user-scope 플러그인 훅(전역 발동) |
| [D6](decisions/0006-name-docsherpa.md) | 이름 = **docsherpa** | docs 포함 + AI-읽기 하네스 + 충돌0 | throughline·doctender·agentmap(충돌) |
| [**D7**](decisions/0007-hook-trust-model.md) | **훅 신뢰 모델**: (설치자) opt-in + inspect-before-write + easy-disable. (**collaborator**) 클론한 repo의 커밋된 훅은 **Claude Code 자체 훅-승인 게이트**(첫 실행 전 승인 요청)가 safe-by-default를 제공 — 우리는 신뢰층 재발명 안 함, M0에서 실검증. prime은 커밋된 신뢰 경계임을 명시 | opt-in은 설치자만 보호. collaborator 보호는 harness가 담당(codex #4) | 조용히 훅 설치 / 자체 신뢰층 재발명 |
| [**D8**](decisions/0008-language-agnostic-markers.md) | **섹션명 계약 = 언어-불문 마커** `<!-- docsherpa:routing -->`·`<!-- docsherpa:index -->`. 한국어 리터럴 폐기 | 소비자가 AGENTS.md를 번역하면 한국어 헤딩이 무효화 → 앵커 전멸(둘 다 지적) | 헤딩 문자열 매칭(번역·wording에 취약) |
| [**D9**](decisions/0009-narrow-doc-reconcile-triggers.md) | doc-reconcile 트리거를 **SessionStart + 수동 호출로 좁힘**. "pre-commit docs-impact 게이트" 언급 제거 | 그 게이트는 이 repo에도 없음(의도적 보류) — 광고하면 phantom이 소비자로 복제(architect) | 게이트 구현(YAGNI, 보류 결정 뒤집기) |

**감사(2026-07-04):** 개인·회사 식별자 유출 **0**. 도메인 특이성은 이식성 문제(프라이버시 아님).
**단, license/provenance 감사는 별개**(§8) — "식별자 0"이 "발행 가능"을 증명하진 않음(codex).

## 4. 아키텍처 (A: repo · 배포)

```
docsherpa/                          ← 새 public repo (GitHub)
├── .claude-plugin/
│   ├── plugin.json                 ← name:docsherpa, version, author, license:MIT
│   └── marketplace.json            ← plugins:[{name:docsherpa, source:"./"}]
├── skills/
│   ├── setup-docs/
│   │   ├── SKILL.md                ← ✏️ 설치자 확장(§7)
│   │   ├── reference/knowledge.md  ← ✅ 그대로
│   │   ├── scripts/
│   │   │   ├── gate.py             ← ✏️ 마커 계약 grep 추가(D8) — 그 외 그대로
│   │   │   ├── content_oracle.py   ← ✅ 그대로 (마이그레이션 내용보존용. parity 증명엔 안 씀 — §9)
│   │   │   ├── merge_settings.py   ← 🆕 settings.json 3-파트 병합(§7.2)
│   │   │   └── test_*.py           ← ✏️ 병합·마커 테스트 추가
│   │   └── templates/              ← 🆕 스캐폴드 원본(스킬 아님)
│   │       ├── doc-drift-prime.txt
│   │       └── settings-hook.json  ← 훅 *템플릿*(active 아님 — D5)
│   └── doc-reconcile/SKILL.md      ← ✏️ 이식화·마커화·phantom제거(§6)
├── LICENSE  ├── README.md  ├── CHANGELOG.md  ├── PROVENANCE.md
```

**흐름(2계층):** ① 설치(1회, user): `/plugin marketplace add <you>/docsherpa` → install.
② 적용(프로젝트마다): `/docsherpa:setup-docs` → 문서 골격 + 성장 루프 커밋. **opt-in**(D7):
스캐폴드 전 무엇을 쓸지 보여주고 승인받음.

## 5. 플러그인 내부물 (B) — §4 트리 상태표대로.

## 6. doc-reconcile 이식화 (C)

**`skills/doc-reconcile/SKILL.md` 하나가 정본(한 파일, 두 쓰임):**

- **척추(유지):** 양방향(갱신+신설) · **마커 위임**(D8) · spec≠ADR · "배웠나" 트리거 · 도달성
  closeout · anti-hallucination.
- **⚠️ phantom 게이트 제거(D9):** 현 description 3행의 *"pre-commit docs-impact 게이트가 막았을 때"*
  트리거를 삭제. 트리거 = **SessionStart prime + 수동 호출**로 재정의. (그 게이트는 미구현·보류.)
- **섹션명 → 언어-불문 마커(D8):** doc-reconcile은 `## 문서 라우팅 룰`·`## 먼저 읽기` **문자열이
  아니라** setup-docs가 그 헤딩 옆에 심는 HTML 마커(`<!-- docsherpa:routing -->` 등)를 참조.
  번역·wording 변경에 불변.
- **앵커 블록(범용 + graceful degrade):** second-brain 특이 예시(config.py→SPEC.md, edge type,
  ARCHITECTURE.md, CONCEPTS 3vs4, GIT.md/text-embedding-3-large, Claude/Haiku/openai 잔재)를
  일반형으로. **degrade는 조용한 no-op이 아니라 명시적**: 대상 문서 없으면 앵커를 `<!-- TODO:
  이 프로젝트엔 X 문서 없음 -->`로 남기지 말고 **그 앵커 라인 자체를 생략**(hollow 방지).
- **live 사용:** 범용 앵커. **스캐폴드:** setup-docs가 앵커만 프로젝트 특화(못 채우면 생략).

**OSS 역누출 방지(codex):** 스캐폴드 산출물(target 사본)은 target 특이 텍스트를 담지만, **플러그인
안 정본은 절대 프로젝트 리터럴을 담지 않는다** — CI 체크(정본 SKILL.md에 `config.py`·`SPEC.md` 등
금지어 grep) 1줄로 강제.

## 7. setup-docs 설치자 확장 (D)

GREENFIELD에 **"성장 루프 설치"(opt-in — D7)** 단계 추가:

1. **루프 스캐폴드(opt-in):** 무엇을 쓸지 diff-preview로 보여주고 승인 후, doc-reconcile(앵커 채워)
   + prime + 훅을 target **`.claude/settings.json`**(공유·커밋. `.local` 아님 — 정확한 경로 고정) +
   `.claude/`에 커밋 스캐폴드.
   - **비대화형 fallback(codex):** 대화형이 아니면(headless/CI) 기본 **dry-run**(쓰지 않고 계획만
     출력). 실제 쓰기는 `--yes` 명시 필요. fail-safe: 승인 없으면 아무것도 안 씀.
2. **settings.json 병합 — 3-파트 계약(R1, `merge_settings.py`):** "멱등 하나"가 아님.
   - **(a) dedup 술어:** 훅 명령을 **정규화**해 비교(경로·따옴표·`./` 차이 무시). 이미 있으면 skip.
   - **(b) 포맷 보존:** JSONC/주석/키순서 파괴 금지. 기존 파일이면 최소-침습 편집(순진한
     load→dump 금지) — setup-docs 철칙("덮지 말고 병합").
   - **(c) 파일 선택:** 반드시 **`settings.json`(공유·커밋)**. `settings.local.json`(gitignore)에
     쓰면 D2 깨짐. → RED 3개(§10).
3. **CLAUDE.md 주입(architect):** 소비자에 **내용 있는 CLAUDE.md**가 이미 있으면? 없으면
   `@AGENTS.md` 생성, `@AGENTS.md` 이미 import하면 그대로, **다른 내용 있으면 첫 줄에 `@AGENTS.md`만
   안전 prepend**(기존 보존). gate.py 루트 탐색이 이에 의존하므로 테스트로 고정.
4. **loop-presence 체크 → Phase 0 흡수(YAGNI, architect):** 별도 `loop_check` 스크립트 안 만듦.
   기존 진단에 "루프 3종 존재" `ls`-수준 확인 한 줄. HEALTHY 판정에 반영.
5. **앵커 자동 채움 — 보수적:** 스택 신호로 확신되는 것만 채우고, **불확실하면 추론 말고 생략**
   (그럴듯한 틀린 지침 방지 — codex). 채운 앵커는 실제 파일 존재 확인 후에만.

## 8. OSS 자산 (E)

- **LICENSE:** MIT (`Copyright (c) 2026 <이름/핸들>`).
- **PROVENANCE.md(codex):** 코드 출처·라이선스 감사. gate.py/content_oracle/setup-docs는 자작 확인.
  Nygard(ADR)·Diátaxis·superpowers는 **패턴 참조**(코드 복붙 아님)임을 명시. 빌려온 코드 0 증명.
- **README(얼굴):** what/why/install/30초 데모 + **훅 투명성 섹션**(prime이 뭘 주입하는지·비활성화
  방법 — D7).
- **CHANGELOG + semver `0.1.0`**("실험적" 명시).

## 9. 독푸딩 마이그레이션 (F) — parity는 behavioral (rev2)

```
1. 추출:   global setup-docs + 이 repo doc-reconcile → docsherpa
2. 일반화: 앵커 범용화 + 마커화 + phantom 제거(§6)   검증: 척추 보존 + 정본 금지어 grep=0
3. 로컬발행: /plugin marketplace add ./docsherpa
4. 재스캐폴드: second-brain에서 /docsherpa:setup-docs → doc-reconcile를 second-brain 앵커로 특화
   ⭐ 무-퇴행 = **behavioral fixture**(§10.3), 텍스트 superset 아님:
      재생성 doc-reconcile를 실제 변경 시나리오에 돌려 원본과 **같은 신설/갱신 판정**을 내는지.
      + gate broken=0·orphan=0. 통과해야 원본 교체.
   ⚠️ second-brain엔 **이미 SessionStart 훅 존재** → 이 재스캐폴드가 병합 3-파트의 **최악 케이스
      (기존 훅 보존)를 첫 실증**. M5 검증에 "기존 훅 보존 확인" 못박음.
5. 정리:   중복 global setup-docs 제거 — **단 로컬 플러그인 경로 동작 확인 후에만**(롤백 안전, codex).
```

**폐기된 주장:** "텍스트 superset이 무-퇴행을 구성상 보장"(rev1 §9)은 **거짓** — content_oracle의
`normalize()`가 링크 타겟 변경(=일반화의 핵심)을 지우고, 순서 뒤집기·모순 추가를 통과시킴. parity에
그 도구를 쓰지 않는다.

## 10. 테스트 (G)

- **기존:** `test_content_oracle.py` 그대로.
- **신규:**
  1. **settings.json 병합 RED×3:** (a) 기존 SessionStart 훅 보존+dedup (b) JSONC/포맷 보존
     (c) `settings.json`에 씀(`.local` 아님).
  2. **이식성 fixture — 확장(codex):** 단일 JS repo만 아니라 — ① 빈 JS repo ② **기존 AGENTS.md
     있는 repo**(마커 주입·번역본) ③ **기존 settings.json 있는 repo**(병합) ④ 비영어 문서 repo.
     각: gate PASS + **degrade 후에도 실제로 문서 신설을 지시**(hollow 아님) + 마커 계약 grep PASS.
  3. **독푸딩 behavioral parity:** 재생성 doc-reconcile ↔ 원본이 동일 변경 시나리오에 같은 판정.
  4. **설치-현실(codex):** 로컬 마켓플레이스 설치 → `/docsherpa:setup-docs` 네임스페이스 resolution
     → fresh-clone에서 스캐폴드된 루프가 inert 아님 확인.
- **정직성:** 산문 방법론은 유닛테스트 없음 — 검증은 fixture+gate 행동적.

## 11. 리스크 · 오픈 질문

- **R1 settings.json 병합** = 3-파트 계약(dedup·포맷·파일). RED×3로 봉쇄.
- **R2 일반화 hollow** = degrade가 조용한 no-op이면 gate 초록인데 방법론 빈약. §10.2가 "신설 지시"를
  검사해 봉쇄.
- **R3 마커 계약 drift** = D8 마커 + gate.py grep 테스트(주석 아닌 실행 검증).
- **R4 사본 drift**(정본 vs target 사본) = 스캐폴드 파일에 **version stamp**를 박음. **재실행 정책
  (codex):** 로컬 편집이 감지되면 **기본 skip + diff 표시**, 절대 조용한 overwrite 금지. 갱신은
  사용자 승인 후에만(3-way/patch-preview는 M0 spike에서 확정).
- **R5 훅 신뢰/보안**(codex) = D7(opt-in·inspect·disable) + PROVENANCE + README 투명성.
- **R6 Claude-Code 의존**(codex) = 커밋된 루프는 Claude Code 사용자에게만 작동. 타 도구엔
  inert-but-harmless임을 README에 명시.
- **OQ1** ~~doc-reconcile live 노출?~~ 해결(§4 배치로 자동 live).
- **OQ2** README 데모 자산(스크린샷/gif) 범위 → M6 시 결정.
- **사용자 입력:** `<you>`(GitHub 핸들) · `<이름/핸들>`(MIT copyright). placeholder는 이 둘뿐.

## 12. 구현 마일스톤 (writing-plans 입력) — spike 먼저 (rev2)

가장 어려운 미지수를 OSS 껍데기 전에 증명(codex·architect).

0. **M0 — spike (de-risk):** 로컬 최소 플러그인으로 ① 훅 스코프·opt-in ② settings 병합 3-파트
   ③ 마켓플레이스 설치·네임스페이스 resolution을 실증. **RED-first.** 통과해야 진행.
1. **M1 — doc-reconcile 이식화(§6):** doc-reconcile이 마커를 **소비**하도록 일반화 + phantom 제거 +
   앵커 범용화. (마커 *삽입*은 setup-docs 소관이라 M3 — codex의 소유권 지적. M1은 "마커를 참조"까지,
   M3이 "마커를 심는다".) 검증: 척추 보존 diff + 정본 금지어 grep=0.
2. **M2 — 이식성 검증(§10.2):** 4종 fixture GREENFIELD → gate + hollow-없음 + 마커 PASS.
   (M1 방향을 M2가 규정하므로 붙여 배치 — architect.)
3. **M3 — setup-docs 설치자(§7):** 루프 스캐폴드 + 병합(merge_settings.py) + CLAUDE.md 주입 +
   Phase0 loop 체크. 검증: 병합 RED×3 + 설치-현실 테스트.
4. **M4 — 독푸딩(§9):** second-brain 재스캐폴드 + behavioral parity + 기존 훅 보존 + global 제거
   (경로 확인 후).
5. **M5 — OSS 마감(§8):** README·CHANGELOG·LICENSE·PROVENANCE·훅 투명성 → public.

## 13. 검증 기록

**rev1 → rev2:** `/codex` + `architect` 교차 리뷰. **둘 다 잡음:** 병합 under-spec · parity BROKEN ·
섹션명 계약 취약 · "한 파일 두 쓰임" 취약 · 마일스톤 순서. **codex:** 훅 신뢰/보안 · provenance ·
설치-현실 테스트 · fixture 협소. **architect:** phantom pre-commit 게이트(최대 발견) · CLAUDE.md
주입 미설계 · loop-presence YAGNI. → D5·D7·D8·D9, §6·§7·§9·§10·§12 개정.

**rev2 → rev3:** codex 재검증 = 구조적 구멍 전부 닫힘(phantom·마일스톤·parity·섹션명·loop). 남은
설계급 4개 반영: D7 collaborator 보호(harness 훅-승인 게이트) · §7.1 비대화형 fallback · R4 재실행
정책(skip+diff) · M1/M3 마커 소유권 분리. 나머지는 구현 디테일 → §14 이연.

## 14. 구현 계획으로 이연 (writing-plans / M0 spike가 확정)

설계가 아니라 "정확히 어떻게"라 스펙에 안 박고 계획/spike로 넘기는 것들(codex 재검증 refinement):
- settings 병합의 정확한 hook 스키마 경로·삽입 위치·matcher별 중복·JSONC 편집 전략 (M0).
- 마커 uniqueness·블록 경계 semantics·doc-reconcile이 마커를 *소비*함을 증명하는 테스트 (M1/M3).
- CLAUDE.md 주입의 BOM/frontmatter/다중 import/의미있는 첫 줄 엣지 (M3).
- §6 "정본 금지어 grep" → 매직 워드 대신 **큐레이팅된 provenance/portability lint**로 (M1).
- §10.2 fixture의 "문서 신설 지시" → **구체 기대 산출물**로 assert(hollow 방지 강화) (M2).
- provenance/no-placeholder를 **릴리스 게이트/CI 체크**로 강제(약속 아님) — plugin.json author/license
  메타 포함 (M5).
