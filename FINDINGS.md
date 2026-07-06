# docsherpa — STATUS & FINDINGS

## 🔜 다음 세션 시작점 (여기부터)

- **상태:** M0·M1·M3·M2 · 자기-독푸딩 · 갭1 · N11 spine · Track2/F12 · loop-refresh · PRD 1급 타입 ·
  **M5 출시 산출물 완비 + v0.1.0 발행 완료(2026-07-06).** 빌드 사실상 종료.
  다음 = **사용자 정지점만 남음**(터미널 설치 실검증 (c) · 중복 global 제거 (d) · 마켓플레이스 등록 —
  런북 `docs/plans/M4-dogfooding.md`). 새 기능 계획 없음(F13/14/15는 YAGNI 이연, ADR 0012).
- **N11 맵 중추 문서(spine) — Plan 1·2·3 완료(2026-07-06):** 마커·계약 단일 소스(`contract.py`) +
  gate 루트 일반화·단일-home locator(Plan 1) · 그린필드 맵 생성 `write_map`(Plan 2, Slice A) ·
  인라인→맵 비파괴 마이그레이션 `migrate_inline_to_map` + **docsherpa 자가적용**(Plan 3, Slice B,
  content_oracle unaccounted=0). ADR [0011](docs/decisions/0011-map-spine-document.md). SKILL·DESIGN·
  doc-reconcile 문서 정합까지 완료(f58e76f). 계획서 `docs/plans/2026-07-06-n11-*`.
- **Slice C(자가치유) 유보(YAGNI, 2026-07-06):** 맵 링크 삭제는 gate가 orphan으로 시끄럽게 잡아
  **내용 소실 0 유지**(자동 복구는 안전 아닌 편의). 실사용 필요 시 최소 `heal_map_link`(sidecar 없이)로
  착수. 근거·판단은 ADR 0011. → **N11 spine 트랙 사실상 종료.**
- **Track2/F12 + loop-refresh 완료(2026-07-06):** F12(평면-only 성장 갭)=doc-reconcile 판정에 룰#4 트리거
  (co-change 클러스터 ≥2 → 폴더 승격 **비블로킹 제안**; 이동은 안 함, content_oracle 경로에 위임).
  F11/13/14/15=미구축 기능(N4·N9) 제약을 ADR [0012](docs/decisions/0012-self-growth-open-issues.md)에 기록.
  **loop-refresh**=설치본 doc-reconcile **자동 동기**(파일 끝 스탬프에 `sha=` 심어 버전+해시; `refresh_loop`이
  provenance·다운그레이드 차단·로컬편집 보존(stuck)·**무프롬프트 커밋 0**). `skills/setup-docs/scripts/refresh.py`,
  계획서 `docs/plans/2026-07-06-loop-refresh.md`. **⚠️ 자기 repo 두-사본 동기는 여전히 수동**(plugin==target →
  provenance no-op; refresh는 배포된 사용자 repo용). **90 tests GREEN.**
- **PRD 1급 문서 타입 완료(2026-07-06):** PRD(제품의 "왜 만드나·누구·성공기준")를 spec(무엇)·ADR(왜 이 기술)과
  **다른 도달성 트리**로 라우팅 **#2**(ADR 바로 아래)에 1급화. `docs/product/*.md` 폴더 카테고리, **온디맨드**
  (specs/처럼 스캐폴드 X·MVD — 첫 PRD 유입 때 생성). 정본 3곳 동기(`_map.md` 라이브 · `scaffold.py` `_MAP_DOC`
  그린필드 · `setup-docs/SKILL.md` 예시) + doc-reconcile에 PRD 트리거·"PRD 있어도 ADR 병렬 신설" 함정.
  재번호(#3~#6)로 낡은 룰 참조 2곳 정정. ADR [0013](docs/decisions/0013-prd-first-class-doc-type.md).
  **첫 PRD dogfood**: `docs/product/`가 온디맨드로 실제 생성됨(`PRD-nondestructive-migration.md` +
  `_README` 리드 인덱스 + `_map.md` 등록, gate broken=0 orphan=0, docs 29→31).
  ⚠️ **정본 doc-reconcile 편집 → `refresh.canonical_hash` 변경. 설치본 전파는 `plugin.json` version 범프 필요 = M5 릴리즈 스텝.**
- **✅ M5 출시 산출물 완비 + v0.1.0 발행(2026-07-06):** `README.md`(오픈소스 퀄리티 — 훅 투명성 섹션 포함) ·
  `LICENSE`(MIT, plugin.json 선언과 정합) · `CHANGELOG.md`(0.1.0) · `PROVENANCE.md`(자작 코드·패턴 참조·빌린
  코드 0·식별자 감사 누출 0) 신설. `hello` 프로브 제거(ADR 0010 실행분). `plugin.json` **0.0.1 → 0.1.0**.
  **git 태그 `v0.1.0` + GitHub Release 발행**(https://github.com/jihkyuo/docsherpa/releases/tag/v0.1.0).
  검증: 90 tests GREEN · gate broken=0 orphan=0 · 릴리즈 게이트(JSON·링크·placeholder·버전 정합) 통과.
  **남은 사용자 정지점(M4 런북, 터미널 Claude Code):** (c) `/plugin install docsherpa@docsherpa` 실검증 ·
  (d) 중복 global `~/.claude/skills/setup-docs` 제거(c 확인 후) · (선택) 마켓플레이스 공식 등록.
- **ADR 0010 개명 부분 철회(2026-07-06):** `setup-docs → doc-setup` 개명은 **하지 않기로 확정**(v0.1.0이
  `setup-docs` 커맨드 표면으로 이미 발행 → 개명은 breaking). `hello` 삭제·브랜드 미표기는 유효. `setup-docs`
  이름 영구 유지. ADR [0010](docs/decisions/0010-skill-names-doc-family.md) 상태 = 부분 철회.
- **순서(재-시퀀싱):** M1 → M3 → M2 → M4 → 자기-독푸딩 → **갭1** → M5.
- **갭1(재사용 §7.5) 완료 — 산문+마커, 코드 없음:** ① 정본 doc-reconcile 앵커 블록을
  `<!-- docsherpa:anchors:start/end -->`로 구분(가드가 강제 — 특화 대상 명확). ② SKILL 5단계에 "§7.5 특화"
  **에이전트 절차**: target `docs/`·AGENTS.md를 직접 보고 **실재하는 정확 경로(대소문자)로만** 특화,
  없으면 일반형 유지(대체 문서 지어내기 금지), 정본은 generic. **45 tests GREEN.**
  - **⚠️ 리뷰 교훈(/code-review + /codex 합치):** 처음엔 `anchor_signals.py`(탐지 헬퍼)를 지었다가
    **삭제함.** 이유: M3 계획의 "§7.5 추가 코드 불요" 결정을 뒤집었고(YAGNI), 대소문자-무시 FS에서 잘못된
    경로 반환, `.claude` 사본이 `docs/` 접두어 빠진 경로를 가리켜 **일반본보다 나쁜 특화**(hollow). §7.5는
    본질이 판단이라 산문이 정답 — 코드로 굳히면 오히려 해로움. (교훈: 판단 작업을 코드로 박제하지 말 것.)
- **자기-독푸딩(정체성 자기모순 해소):** "문서 아키텍처를 세워주는 도구가 정작 자기 repo엔 없다"를 해소.
  ① docsherpa에 자기 라우터(`AGENTS.md` North Star 정체성 + 마커) + `CLAUDE.md` 생성 → self-gate PASS.
  ② `scaffold()`를 docsherpa 자신에 실행 → 성장 루프 설치(SessionStart 훅·prime·커밋 doc-reconcile+stamp).
  ③ §7.5 실전: 설치된 doc-reconcile 앵커를 docsherpa용으로 특화(정본은 generic 유지, 가드 GREEN).
  ④ **D1~D9 결정을 `docs/decisions/` ADR 9개로 마이그레이션**(자기 라우팅 룰 #1) — **content_oracle로
  내용 소실 0 증명**(base_segments=43 unaccounted=0) + gate PASS. **핵심가치(내용 보존 마이그레이션)를
  우리 repo에서 실증함.** ⑤ gate.py 코드펜스 false-positive 버그 수정.
- **정체성(불가침):** `AGENTS.md` 최상단 North Star = 비파괴 마이그레이션 · **내용 소실 0(깨지면 끝장)** ·
  자가성장. 흔들리면 방향 이탈. (메모리 `docsherpa-identity`에도 기록.)
- **M4 상태(중요):** 검증(A) + **격리 워크트리 실동작 확인 완료.** behavioral parity 성립(이식본≡원본,
  **마커 선주입 조건부**). **(a)(b) 커터오버를 second-brain 격리 워크트리에서 실제 적용·검증함**:
  워크트리 `~/Desktop/private/second-brain-dogfood`, 브랜치 `docsherpa-dogfood`(커밋 55f407c) —
  메인 `feat/ask-deploy` 무영향. 실동작 결과: 마커 2개(중복 섹션 0)·`has_contract_markers=True`·
  gate `markers_ok=True`·이식본 doc-reconcile 리터럴 0. broken=8/orphan=9는 second-brain **자체 문서부채**
  (MESSY, docsherpa 스코프 밖). **메인 브랜치 반영·(c) 터미널 `/plugin install`·(d) global 제거는 여전히
  게이트**(사용자가 깨끗한 정지점에 실행). 런북 = `docs/plans/M4-dogfooding.md`.
- **M2가 닫은 것:** ① `scaffold.py` — 호출 가능한 설치자 본체(라우터/docs 골격 + inject/merge 재사용 +
  prime/doc-reconcile 복사+stamp). M3의 "산문만" 결정을 사용자 승인 하에 뒤집음(자동 end-to-end 위해).
  ② 4종 fixture end-to-end GREEN(gate `--require-markers` + no-hollow 구체 산출물 + 마커 + 기존 보존).
  ③ SKILL 산문을 scaffold 위임으로 개정(결정론 부분 단일 소스). ④ 리뷰 발견 4버그 수정(howto-shadow ·
  orphan-template · JSONC-atomicity · dup-marker).
- **scaffold 스코프(중요, M4 주의):** `scaffold()`는 **greenfield/healthy 전용**. 기존에 라우터에 안 걸린
  `docs/**` 문서가 있으면(MESSY) scaffold가 자동 인덱싱 안 함 → orphan으로 gate FAIL. MESSY는 마이그레이션
  파이프라인(에이전트 discovery) 몫. **second-brain은 성숙한 docs → M4는 loop-install만 하되, 기존 docs가
  라우터에 도달 가능한지(HEALTHY) 먼저 확인**하고 scaffold를 돌려야 한다.
- **M4가 할 일(§9):** second-brain 재스캐폴드 + **behavioral parity**(재생성 doc-reconcile ↔ 원본이 동일
  변경 시나리오에 같은 신설/갱신 판정) + **기존 SessionStart 훅 보존 첫 실증** + 로컬 플러그인 경로 동작
  확인 후 중복 global setup-docs 제거. **먼저 writing-plans로 M4 계획 작성.**
- **이어가려면 이 순서로 읽어라:** ① 이 파일 → ② `docs/DESIGN.md` §9(독푸딩·behavioral parity)·§10.3 →
  ③ `docs/plans/M2-portability-fixtures.md`(scaffold가 무엇을 하는지).
- **테스트 러너:** `cd skills/setup-docs/scripts && uv run --with pytest pytest -q` (현재 **90 passed**).
- **핵심 계약:** doc-reconcile은 헤딩이 아니라 **마커**를 소비한다(D8) → M3의 마커 삽입과 맞물림.
  정본 doc-reconcile은 도메인 리터럴 0(가드 `test_doc_reconcile_portable.py`가 강제 — M3 후에도 GREEN).

---

## 미지수 → 결정 (M0)

- **① 설치 · 네임스페이스 (T1):** ✅ **확정.** 시퀀스: `/plugin marketplace add ~/Desktop/private/docsherpa`
  (로컬 경로) → `/plugin install docsherpa@docsherpa` (**user scope**) → `/docsherpa:hello` →
  `DOCSHERPA_NAMESPACE_OK`. 네임스페이스 = `/<plugin>:<skill>`(콜론). 컴포넌트는 설치 시 discover됨.
  - ⚠️ 함정: **VSCode extension 채팅에선 `/plugin` 불가** — 터미널 Claude Code에서 실행.
  - ⚠️ scope: project/local은 현재 repo `.claude/` 오염 → 테스트/개인용은 **user scope**.
- **② settings.json 포맷 (T2):** ✅ **실용 확정.** Claude Code settings는 문서상 표준 JSON →
  `merge_settings.py`의 load→dump 무손실. 병합 3-파트(보존·dedup·settings-not-local) 테스트 GREEN.
  - 남은 엣지: 사용자 settings에 주석(JSONC)이 실제로 있으면 comment-preserving 편집으로 승격(M3).
- **③ 훅-승인 게이트 (T3):** ✅ **D7 확정.** Claude Code **workspace trust 게이트**가 커밋된
  `.claude/settings.json` 훅을 신뢰 수락 전까지 차단(공식 문서 — security.md/permissions.md).
  워크스페이스 단위 1회 승인(per-hook 아님). 우리는 신뢰층 재발명 불요.
  - **보너스:** `.local.json`은 trust 스킵 → D2("settings.json, not local")가 이중으로 옳음.
  - **캐비엇(→M5 README):** `-p`(headless/CI)는 trust 스킵 → CI 사용자는 게이트 우회됨을 명시.
  - **설계 노트(→hook 명령):** trust 다이얼로그에 뜨는 hook 명령을 짧고 읽기 쉽게(무서운
    shell 메타문자 피함). 현 `cat .claude/doc-drift-prime.txt 2>/dev/null || true`는 수용 가능.
- **④ 마커 계약 (T4):** _(대기)_ — 언어-불문 마커 소비-검증 성립.

## 스펙 §14 이연 중 M0가 닫은 것

- ✅ settings 병합 코어(dedup 술어·파일 선택·기존 훅 보존) — `merge_settings.py`.
- ✅ 마커 계약 검증기 — `check_markers.py` (언어-불문, 번역 생존).
- ✅ 훅 신뢰 모델 — harness workspace-trust 게이트에 의존(D7).
- ✅ 마켓플레이스 설치·네임스페이스 형태 — 로컬 경로 + user scope + `/<plugin>:<skill>`.

## M1–M5로 넘길 남은 것 (M0 밖)

- CLAUDE.md 주입 엣지(BOM/frontmatter/다중 import) — M3.
- fixture의 구체 기대 산출물(hollow 방지 강화) — M2.
- provenance/no-placeholder 릴리스 게이트 — M5.
- settings JSONC comment-preservation(실제 필요 시) — M3.
- (검증됨) spike 중 STOP·재설계 트리거 **없음** — 순항. D7 확정으로 훅 설계 유지.

## M0 결론

**GREEN.** 가장 위험한 미지수 4개 전부 닫힘. 순수 코드 산출물(`merge_settings.py`·`check_markers.py`)은
테스트 통과. M1–M5 상세 계획을 이 FINDINGS 위에서 작성 가능.

## M1 완료 (doc-reconcile 이식화)

**GREEN.** doc-reconcile 이식됨 — phantom 트리거 제거(D9) + 언어-불문 마커 참조(D8) + 앵커 범용화
+ graceful degrade 명시. 이식성 가드(`test_doc_reconcile_portable.py`) GREEN, 척추 6개 보존.
setup-docs 도메인-무관 자산(SKILL·knowledge·gate·content_oracle) as-is landing. 전체 18 tests GREEN.

**다음 = M3 설치자** (setup-docs가 마커 삽입 + 루프 스캐폴드 + `merge_settings` 통합 + CLAUDE.md 주입 +
Phase0 loop 체크). 그 다음 **M2** (end-to-end fixture — 설치자 필요), **M4** 독푸딩, **M5** 공개.
(재-시퀀싱: M1→M3→M2→M4→M5. spec §12의 M2-before-M3를 codex 지적대로 뒤집음.)

## M3 완료 (setup-docs 설치자)

**GREEN.** setup-docs가 골격 생성기 → **성장 루프 설치자**로 확장됨. 위험한 것만 테스트된 코드로 격리:
- **`inject_claude_md.py`** — 기존 CLAUDE.md에 `@AGENTS.md` 안전 주입(없음/이미-import/prepend/BOM/
  frontmatter 엣지, §14). 8 tests. gate 루트 탐색이 의존.
- **`merge_settings.py` JSONC 가드** — 주석/JSONC면 크래시·클로버 대신 `ValueError`로 거부+수동 병합 안내
  (§14 결정: comment-preserving 안 지음, settings는 표준 JSON이 정상 — YAGNI). +1 test.
- **`gate.py --require-markers`** — 스캐폴드 검증에서만 D8 마커 계약 강제(opt-in — Phase0 진단 false-fail 방지).
  +3 tests. 도달성 본문은 byte-identical 보존.
- **`templates/`** — 범용 prime + 훅 템플릿(D5: 플러그인은 active 아닌 템플릿만, 도메인 리터럴 0).
- **SKILL.md 산문** — "성장 루프 설치" 섹션(opt-in·dry-run·diff-preview·D2·R4·R7), AGENTS.md 템플릿에 마커
  인라인, 기존 병합 규칙에 마커 삽입 규칙, Phase0 loop-presence 1줄. 척추(GREENFIELD/MESSY/멱등/게이트)
  외과적 보존.

전체 **30 tests GREEN**(18→30), 이식성 가드 GREEN(역누출 0). /code-review(high, 분석적) = 0 findings.
**설치-현실 테스트(§10.4)는 이연** — VSCode 채팅에서 `/plugin` 불가 → M4 독푸딩에서 실제 설치·스캐폴드 검증.

**다음 = M2 이식성 fixture**(§10.2 4종): 설치자 산문을 end-to-end로 돌려 gate PASS + hollow-없음 + 마커 grep.

## M2 완료 (이식성 fixture + scaffold 오케스트레이터)

**GREEN.** M3가 산문으로 남긴 결정론적 스캐폴드를 **호출 가능한 `scaffold.py`로 추출**(사용자 승인 하에
M3의 "산문만" 결정 뒤집음 — 자동 end-to-end 검증엔 호출 가능한 본체가 필수). `scaffold()`는 라우터/docs
골격 + `inject_claude_md_file`·`merge_settings_file`(M3 재사용) + prime/doc-reconcile 복사(+version stamp)를
한 번에 수행. SKILL 산문은 opt-in/dry-run/빈칸-채움만 담당하도록 개정(결정론 부분 단일 소스, drift 방지).

- **4종 fixture end-to-end GREEN**(§10.2): 빈 JS / 기존 AGENTS.md·번역본 / 기존 settings.json / 비영어 문서.
  각: gate `--require-markers` PASS + **hollow 아님**(`_template.md` 링크 등 구체 산출물 assert, §14) +
  마커 계약(`has_contract_markers`) + 기존 내용(커스텀 룰·훅·비영어 문서) 보존.
- **리뷰 발견 4버그 수정**(subagent code-review): ① how-to 기존 `README.md`를 placeholder `_README.md`가
  그늘 져 고아 만듦 → 인덱스 있으면 placeholder 안 만듦 ② `decisions/README.md` 기존이면 `_template.md`
  신설이 고아 → README 신설 시에만 template를 쌍으로 ③ JSONC settings가 병합 중간에 던져 부분 설치 →
  settings를 **먼저** 돌려 실패 시 다른 파일 안 씀(atomic-ish) ④ 마커 하나만 있으면 둘 다 append해 중복 →
  빠진 섹션만 append.
- **scaffold 스코프 = greenfield/healthy 전용**(리뷰 #3): 기존 미인덱스 `docs/**`가 있으면 orphan으로 gate
  FAIL(MESSY는 마이그레이션 파이프라인 몫). **M4가 second-brain에 적용 전 HEALTHY 확인 필수.**

전체 **43 tests GREEN**(30→43), 이식성 가드 GREEN. **다음 = M4 독푸딩**(behavioral parity + 기존 훅 보존
실증 + 설치-현실 + global 제거).
