# docsherpa — STATUS & FINDINGS

## 🔜 다음 세션 시작점 (여기부터)

- **🆕 setup-docs 재설계 — 진단-주도 전체-repo 마이그레이션 (2026-07-08, 브레인스토밍→스펙→증분3 완료):**
  하드닝 루프 발견(G1~G4: docs/ 중심·밖 방치·전-계정팅 부재·설치≠완료)을 재설계로 확장. **미션 = 전 프로젝트
  문서를 `docs/`로 중앙집중 + 유실 0.** 6-Phase(전체-repo 병렬 탐색 → 9차원 등급 채점 → 시각 승인
  아티팩트 → worktree 배치 실행(두 오라클) → 결과 재진단). 진단을 **`doc-health` 스킬**로 분리(before/after
  동일 채점기 = 정합성), `render_report.py` 공유 렌더러(동결 CSS + WCAG-AA 테스트로 품질 영구 고정 — 매
  실행 동일 품질). 스펙 [design.md](docs/specs/diagnosis-driven-migration/design.md), 계획
  [render-report](docs/plans/2026-07-07-render-report-renderer.md).
  **✅ 증분 1 `render_report` 완료:** 350줄 stdlib 렌더러 + 13 테스트(105 green), opus 리뷰 APPROVED(Crit/Imp 0),
  AA 가드 라이브(worst 4.78)·자기완결·동결 CSS byte-identical·전 주입점 이스케이프.
  **✅ 증분 2 `doc-health` 완료(2026-07-08):** 독립 읽기전용 스킬(`skills/doc-health/`) — `gate.analyze()`
  외과적 추출 + 전용 `inventory.py`·`scorecard.py`(disposition·M1~M5·rollup·자세·assemble) + SKILL.md·
  reference/scoring.md, 23 테스트 green(전용 러너). ADR [0015](docs/decisions/0015-doc-health-module-extraction.md)
  (H1~H3 근거 기록). 다음 = setup-docs Phase 0·1·2 배선(증분3에서 완료).
  이연: Phase 4 result-모드 CSS·repo-키 스키마 하드닝(ledger `.superpowers/sdd/progress.md`).
  **✅ 첫 실전 독푸딩(vd-front, 2026-07-08):** doc-health를 실제 레포에 적용 → **탐색이 코드 속
  `src/features/custom/shared/docs/**` ~35개 파묻힌 문서를 전부 포착(G1 갭 실증)**, 등급 **F**(정직).
  실데이터가 버그 2건 노출 → ADR [0016](docs/decisions/0016-inventory-respect-gitignore.md): **탐색 분모가
  `.gitignore` 존중**(외부 플러그인 스크래치 `.superpowers/` 등을 하드코딩 없이 자동 제외 — 레포 선언 위임,
  git-optional) + 루트 관례 대소문자 무시. vd-front M5 49(오염)→38(정직). 리뷰가 비-ASCII 경로 인용 버그도
  잡아 `-z` 픽스(한글 경로 가드 테스트). 30 테스트 green.
  참고: ADR 0010 `doc-*` 패밀리 폐기 → 새 스킬은 merit로 명명(그래서 `doc-health`).
  **📌 이연 기록(2026-07-08):** vd-front 독푸딩+설계 논의에서 표면화된 **문서 타입 템플릿·메타·트리거** 개선을
  [doc-type-templates/design.md](docs/specs/doc-type-templates/design.md)에 기록. 핵심 = doc-reconcile 트리거가
  판단-소프트(reference/explanation 트리거 없음·메타 스탬핑·게이트 부재). **심장은 템플릿 아니라 트리거.**
  합의 결정(B 스캐폴드·created/adopted 정직·타입-메타 게이트·관계메타·산업표준) 기록됨. **착수는 setup 완료 후**
  (doc-reconcile 개선 루프). ⚠️ B 착수 시 ADR 0013 supersede 필요.
- **✅ 증분 3 `migrate.py` 엔진 + Phase 0·1·2 배선 완료(2026-07-08):** 계획검증 F1~F6(F1=register_in_indexes
  substring 오탐·F2/F3=엔진 기반골격·F4=legacy skip·F5=orphan==0 단정·F6=슬래시 보존) 전부 반영해
  `skills/setup-docs/scripts/migrate.py` 신설 — `plan_moves`(결정론 type→folder·disposition/legacy/.mdx
  자동skip) · `apply_moves`+`rewrite_links`(물리이동+링크재작성, chained-move 2단계 안전) ·
  `register_in_indexes`(scaffold 위 도달성 배선, home 인덱스링크 정확매칭) · `build_and_verify`(스크래치
  복사→적용→scaffold→등록→gate+content_oracle, 실제 repo 불변) · `assemble_plan_data`(render_report plan
  계약). `skills/setup-docs/SKILL.md`의 MESSY 무거운 차선을 이 엔진 호출 Phase 0(진단 재사용)→1a(배정
  판단+plan_moves)→1b(build_and_verify 자체검증+STOP)→2(assemble_plan_data+승인 아티팩트) 절차로 재배선.
  **다음 = 증분 4**(Phase 3·4: 승인된 계획의 실제 이동 실행 — 배치·worktree·subagent-driven-development —
  및 실행결과 재진단). 128 + 30 테스트 green, gate broken=0 orphan=0 markers_ok=True.
  최종 whole-branch 리뷰(opus) READY TO MERGE — 5 정체성 불변식 전부 HOLD(scratch-only 범위), Crit/Imp 0.
  **⚠️ 증분 4 실행-게이트(실제-repo 쓰기 전 필수 차단, 둘 다 fail-safe라 증분 3은 무영향):**
  (G1) `inject_claude_md` frontmatter 분기가 `@AGENTS.md`를 frontmatter 세그먼트에 붙여(빈 줄 없음)
  build_and_verify가 false-STOP(F3 확장 — 빈 줄 앞에도 삽입 필요). (G2) `apply_moves`·`content_oracle` 둘 다
  `errors="ignore"`라 invalid UTF-8 바이트 소실이 오라클에 안 잡힘 → 실제 쓰기 전 바이트 비교/surrogateescape.
  **🧪 실전 dogfood(vd-backend, 2026-07-08):** Phase 0·1·2 파이프라인을 실 레포에 적용(스크래치, 비파괴).
  75 docs·등급 **F**(정직: 라우터 도달 orphan 67/67 + 마커·척추·성장루프 전무 → 기계 M1~M4 FAIL, M5만 PASS).
  분류 병렬 서브에이전트 4개(완결성 68/68) → plan_moves 이동 43 + legacy/제자리 등록 24 → build_and_verify
  **orphan=0·unaccounted=0(내용 소실 0)·broken=3** → render_report plan 아티팩트 산출. **증분 4 입력 3건 발굴:**
  (D1) **제자리·legacy 문서도 인덱스 등록 필요** — `plan_moves`/`register`가 이동 문서만 등록 →
  이미 올바른 위치의 docs(`docs/harness/*`·`docs/README.md`)와 legacy가 고아. 등록 대상을 docs/ 아래 전체
  content로 확장해야(이번엔 수동으로 넓혀 orphan=0). (D2) **도달성 확보가 잠복 broken 링크 노출** —
  원본 미도달이라 gate가 방문 안 해 숨겨졌던 코드-디렉터리 링크(FRONT-END_API_INVENTORY.md → `src/apis/` 등 3개)가
  이사 후 드러남 → 링크 교정(de-link) 단계 필요. (D3) **트리 시각화 생성기 스텁** — `scorecard._before_tree`는
  docs/ 밖 흩어짐만·`migrate._after_tree`는 평면 12개만 → 실제 중첩 폴더 트리 미표현. 증분 4에서 실 계층 렌더로 개선.
  (D3보강) **트리 접이식(collapsible) 전체보기** — 요약(폴더+개수)은 기본, 전체 파일 스캐폴딩은 `<details>/<summary>`
  네이티브 disclosure(JS 0·시맨틱·비버튼)로 Before→After 2열 펼침. vd-backend 아티팩트에 후처리로 프로토타입(프리즈
  테마 변수 재사용·인라인 style 0·반응형 ≤640px 1열·legacy prd/ 흐림). 정식화 = `render_report`에 트리 `collapsible`
  플래그 + 전용 프리즈 CSS + 대비/구조 게이트 테스트 추가(렌더러 확장). 프리즈 품질 게이트와 충돌 없음(외부리소스 0 유지).
  (D5) **배치는 타입 우선이어야 — 폴더명 topic 남발 금지(백엔드 개발자 검토가 실증)** — vd-backend 첫 배치에서
  분류는 내용을 읽고 정확했으나(`기획서`=PRD·`N일차_진행`=legacy 정확) 오케스트레이션이 **폴더명 기반 topic
  클러스터링**을 남발해 그 type을 배치에서 덮어씀 → PRD 기획서가 `product/` 아닌 `onboarding/`로, 결제(일본결제)
  spec이 `onboarding/`로 오배치. 도메인 전문가가 "내용 안 보고 배치했냐"고 정확히 감지. **설계 §7 "타입 먼저,
  토픽은 co-change일 때만"을 위반한 것.** 교정 v2(type 우선: PRD→product·spec→specs/<feature>·ADR→decisions,
  일본결제→specs/payment)로 재배치·재검증(orphan=0·유실0) — 두 예시 정상화. 교훈: SKILL Phase 1a enrich에서
  **topic은 co-change 클러스터에만, 배치 1순위는 분류 type**임을 산문에 강제(폴더명 승계 유혹 차단). 남은 판단:
  타입 vs 기능응집 조직(Diátaxis 흩뿌림 vs 폴더 응집)은 도메인 결정 — 결정 패널로.
  (D4) **아티팩트 은어 누출(자기설명 부재)** — 승인-대상 산출물인데 `scorecard.py`의 차원 라벨/sub가 내부 은어
  (`성장 루프 3종`·`맵 척추`·`마커 home`)라 docsherpa 개념 모르는 외부 뷰어는 이해·행동 불가(채택률 직결).
  렌더러 아닌 scorecard의 name/sub를 자기설명형(무엇을 재나+결과)으로 바꿔야. 예: M4 → "코드 변경 시 문서
  자동 갱신 장치 3종(세션 훅·알림·doc-reconcile 스킬) 미설치". vd-backend 아티팩트에 선반영해 검증(9차원 평문화).
  (D4보강) **능력 vs 준수 차원 구분 표기** — M2·M3·M4는 docsherpa 특정 부품(라우터 마커·맵 척추·doc-reconcile)
  유무를 재는 **준수(채택도) 차원**이라 사용자 자체 등가물(자작 갱신 스킬 등)을 인정 못 함(결정론 대가). 반면
  M1(도달성)·M5(커버리지)는 **능력(도구 무관) 차원** — 실제 속성이라 진짜 결함. 검사 로직은 결정론이라 그대로
  두되(자체 등가물 인정=결정론 포기), **라벨에서 "docsherpa 채택도(선택)" vs "문서 건강(필수)"를 구분**해야
  자체 체계 보유자가 오해/억울함 없이 유도 목적 유지. vd-backend 아티팩트에 선반영(M2~M4=채택도·M1/M5=필수).
- **상태:** M0·M1·M3·M2 · 자기-독푸딩 · 갭1 · N11 spine · Track2/F12 · loop-refresh · PRD 1급 타입 ·
  **M5 출시 산출물 완비 + v0.1.0 발행 완료(2026-07-06).** 빌드 사실상 종료.
  다음 = **사용자 정지점만 남음**(터미널 설치 실검증 (c) · 중복 global 제거 (d) · 마켓플레이스 등록 —
  런북 `docs/plans/M4-dogfooding.md`). 새 기능 계획 없음(F13/14/15는 YAGNI 이연, ADR 0012).
- **setup-docs 진단-주도 제안 — ADR [0014](docs/decisions/0014-setup-docs-diagnosis-driven-proposal.md) 완료(2026-07-07):**
  e2e 독푸딩(jio.dev)에서 setup-docs가 정본 결정 위임·무거운 경로 강요·루프 스킵유도를 재현 →
  SKILL·knowledge 수정(**4자세 진단-주도 제안 · 성장 루프 필수화 · MESSY 경량/무거움 2차선**).
  fresh 베이스라인 대비 행동 4항목 FAIL→PASS(독립 판정자 확인) + jio.dev 실행 M1~M4
  (gate broken=0·orphan=0 · 마커 · content_oracle 무손실 unaccounted=0 · 멱등/HEALTHY 재진단) 전부 PASS.
  **gate.py `@import` 오탐 = 해결(2026-07-07):** 산문 속 `@AGENTS.md`를 import로 오인하던 `IMPORT_RE`를
  **줄-선두 매칭**(`(?m)^[ \t]*@…`)으로 좁힘. RED-first 재현 테스트 2건 추가(92 GREEN).
  **4자세 전부 검증 완료(2026-07-07):** 자세3(jio.dev, 8/8 루브릭) + GREENFIELD(조용히 설치)·
  중구난방(선택지 없이 migrate 강권)·HEALTHY(무변경) 합성 fixture로 확인 — **라우터 없는 GREENFIELD
  vs 중구난방 구분**(docs 최소 vs chaotic)까지 통과. **→ setup-docs 진단-주도 개선 = 완결.**
  관찰: 무거운 차선의 content_oracle/worktree는 git 전제(non-git repo면 `git init` 선행). (jio.dev
  마이그레이션은 여전히 **미적용** — 적용은 사용자 판단; gate 버그 해결로 이제 백틱 우회 없이 깨끗함.)
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
- **ADR 0010 폐기 — `doc-*` 패밀리 미채택(2026-07-07):** `setup-docs → doc-setup` 개명은 **하지 않음**(v0.1.0이
  `setup-docs` 커맨드 표면으로 이미 발행 → 개명은 breaking). flagship이 안 따라 `doc-*` "패밀리"는 실현된 적
  없음 → **폐기.** 실제 규칙 = **혼합**(`setup-docs`+`doc-reconcile`), 새 스킬은 `doc-*` 강제 없이 **merit(명료함
  + 네임스페이스 없이 홀로 불릴 때 자명)**로 명명. `hello` 삭제·브랜드 미표기(`docsherpa-*` 거부)는 유효.
  ADR [0010](docs/decisions/0010-skill-names-doc-family.md) 상태 = 폐기.
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
