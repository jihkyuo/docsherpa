# setup-docs 파이프라인 — 증분 4 (승인된 계획의 실제 랜딩 → 재진단) spec

- 상태: 제안 (브레인스토밍 완료, 사용자 5-섹션 승인)
- 날짜: 2026-07-09
- 선행: [design.md](design.md) §5·§7·§8·§10 · [setup-pipeline.md](setup-pipeline.md)(증분 3 = Phase 0·1·2, 이 엔진 재사용) · [render_report 계획](../../plans/2026-07-07-render-report-renderer.md)
- dogfood 타겟: `/Users/jiohyeon/Desktop/projects/vd-front` (git, ~70 docs, F등급 — 첫 doc-health dogfood 대상)

> **범위:** 증분 4 = **Phase 3(승인된 계획을 실 repo에 안전 적용) + Phase 4(결과 재진단)**. 증분 3이 스크래치에서
> "계획이 깨끗함"을 증명했다면, 증분 4는 그 검증된 계획을 **사용자가 검토할 실제 브랜치**로 랜딩하고, 옮긴 결과를
> 같은 채점기로 재진단한다. **배치 판단(타입 vs 기능응집)·아티팩트 UX(D3·D4·D6)는 별도 트랙**(이 스펙 밖).

## 0. 선결 (이 세션에서 닫힘)

증분 4 실행-게이트 **G1·G2 = 닫힘**(2026-07-09, RED-first, 실쓰기 전 필수 안전판):
- **G1** `inject_claude_md` frontmatter 분기가 `@AGENTS.md`를 frontmatter 세그먼트에 병합(빈 줄 없음) → false-STOP.
  닫는 `---` 뒤 빈 줄 삽입(`\n@AGENTS.md\n\n`)으로 어느 세그먼트에도 병합 안 되게 교정.
- **G2** `apply_moves`·`content_oracle`의 `errors="ignore"` → invalid UTF-8 바이트 소실 사각. 읽기/쓰기/`seg_key`
  전부 `errors="surrogateescape"`로 전환(바이트 라운드트립 = 소실 0 + 오라클이 바이트 차이 감지). preview는
  `backslashreplace`로 표시-안전화(strict stdout 크래시 방지, /code-review 후속).

## 1. 사용자 합의 결정 (브레인스토밍 확정)

| # | 결정 | 근거 |
|---|---|---|
| L1 | **격리 = 전용 git worktree + 새 브랜치.** 실 작업트리 무영향. 검증 통과 시에만 커밋 → worktree 제거·브랜치만 남김 → 검토·머지는 사용자. 실패 시 흔적 0. | 정체성(비파괴·"주인은 사용자"). M4에서 이미 쓴 방식 |
| L2 | **단일 원자 적용 + 단일 커밋.** 검증된 전체 계획을 `apply_moves`로 한 번에. 배치별 실행 안 함(계획 전체가 스크래치에서 이미 검증됨 → 배치 재검증 안전이득 0; chained-move·전역 relink는 함께 봐야 안전). "배치"는 Phase 1 분류에 속함. | 원칙 2(단순함) · apply_moves 2단계 원자성 |
| L3 | **D1 등록 = 도달성-구동.** register를 "이동 문서"가 아니라 "아직 orphan인 문서 전부"로 구동 → 이동/제자리/legacy 균일 처리. legacy는 전용 인덱스 경유(맵 척추엔 legacy 폴더 링크 1개). | 원칙 3(특수케이스 대신 일반화) · orphan=0 직접 목표 |
| L4 | **D2 = 보존+표면화.** 마이그레이션은 "새 broken 0"만 보장. 기존 broken(스테일 코드참조 등)은 원본 그대로 보존(앵커 미손) + 아티팩트에 "머지 전 결정할 것"으로 표면화(비차단). auto-de-link 금지(앵커 소실=정체성 위반). | 정체성(앵커 보존·비파괴·정직) |
| L5 | **랜드는 HEAD 커밋상태 기준.** worktree=커밋상태라 미추적/미커밋 작업(예: vd-front의 `CONTEXT.md`)은 스코프 밖(노트로 표면화, 안 건드림). | 재현성·비파괴 |

## 2. 아키텍처 (모듈 경계)

**통찰 — 증분 4는 "build_and_verify를 실 worktree에 + 커밋" + 두 정합픽스(D1·D2).** 증분 3의 엔진
(`apply_moves`·`rewrite_links`·`scaffold`·`register_in_indexes`·`content_oracle`·`gate`)을 그대로 재사용.

| 신규/수정 | 성격 | 책임 |
|---|---|---|
| `migrate.py` `land_migration(repo, move_plan, decisions=None, *, plugin_root=None)` (신규) | 실행 진입점 | git worktree+브랜치 생성 → build_and_verify 시퀀스(apply_moves→scaffold→register_all→오라클) → **통과 시에만** 단일 커밋·worktree 제거·브랜치 반환; 실패 시 흔적 0. git 전제(non-git STOP) |
| `migrate.py` `register_all(root)` (신규, `register_in_indexes` 대체/일반화) | 도달성-구동 등록 | gate.analyze의 orphan 목록을 폴더 인덱스(`_ensure_folder_index`·`_append_links`)·map에 등록(멱등) → orphan=0. legacy는 전용 인덱스 경유. 기존 배선 헬퍼 재사용 |
| `migrate.py` 링크 오라클 (신규 헬퍼) | new-vs-preexisting 판별 | 도달성 무관하게 모든 .md 링크를 절대(레포-상대) 타겟으로 해석(gate `resolve` 재사용). base vs current diff → `new_broken`(base엔 존재했던 타겟이 current서 깨짐) · `preexisting_broken`(둘 다 없음) |
| `migrate.py` `build_and_verify` (수정) | 오라클 일원화 | raw `broken` → `new_broken`+`preexisting_broken`로 확장. Phase 1b 자체검증과 Phase 3 랜딩이 같은 오라클 공유 |
| Phase 4 재진단 (SKILL 배선 + render result 모드) | 얇은 래퍼 | doc-health를 랜딩된 worktree에 재실행 → before(Phase 0)/after 나란히 → `render_report(data, "result")` |
| `render_report.py` (수정) | result 모드 CSS | 이전 증분 **이연된 result-모드 CSS** 채움. 동결 CSS·WCAG-AA·인라인 style 0 품질 게이트 유지 |
| `SKILL.md` (수정) | 에이전트 절차 | Phase 3(land_migration·git 전제·실패 STOP)·Phase 4(재진단·result 아티팩트) 산문 |
| 재사용(신규 아님) | — | apply_moves · rewrite_links · scaffold · content_oracle · gate · doc-health · render_report |

**의존성:** land_migration의 의존(apply_moves·scaffold·gate·content_oracle)은 전부 `setup-docs/scripts` 내부.
doc-health 재진단은 **SKILL이 doc-health를 호출**(migrate가 doc-health 임포트 안 함 — 역-의존 회피, 증분 3 계승).

## 3. 데이터 흐름 (Phase 3→4)

```
[승인된 move_plan (Phase 2 아티팩트)]
        │
Phase 3 land_migration(repo=vd-front, move_plan):
   git worktree add <tmp> -b docsherpa/migrate-<stamp>   # HEAD에서 분기, 실 작업트리 무영향
   apply_moves(worktree, move_plan)          # 단일 원자(chained·전역 relink, surrogateescape)
   scaffold(worktree, plugin_root)            # 척추·성장루프
   register_all(worktree)                     # D1: orphan 전부 등록 → orphan=0
   ── 오라클 3 ──
     content_oracle: unaccounted == 0         # 내용 소실 0
     링크 오라클   : new_broken == 0          # D2: 우리가 안 깨뜨림
     gate         : orphan == 0               # 도달성 100%
   통과? ── 아니오 → worktree 제거 + 실패 리포트(부분상태 0) ── STOP
        │ 예
   git commit (단일)  →  worktree 제거, 브랜치 남김
   반환 {branch, unaccounted:0, new_broken:0, preexisting_broken:[...], moved:N}
        │
Phase 4 재진단:
   doc-health(branch의 랜딩 상태) → after 스코어
   render_report({before(Phase0), after, preexisting_broken}, "result")   # result 아티팩트
        │
[사용자: 브랜치 검토 → 머지 or 버림]   ← 우리는 머지 안 함
```

## 4. D1 — 도달성-구동 register_all

**문제(실측):** `register_in_indexes(root, move_plan)`가 이동 문서만 등록 → 제자리 docs(`docs/harness/*`·`docs/README.md`)·legacy가 orphan → gate FAIL.

**설계:** 등록을 **orphan 목록으로 구동**한다.
```
register_all(root):
  gate.analyze(root).orphans 로 도달 안 되는 docs/**/*.md 전부 수집
  각 orphan → 자기 폴더 인덱스(_ensure_folder_index)에 링크(_append_links) + 폴더를 map에 배선(멱등)
  → orphan == 0
```
- **균일**: 이동/제자리/legacy 구분 없이 "orphan인가"만 본다.
- **자기교정**: 간접(move_plan 신뢰) 대신 불변식(도달성 100%)을 직접 목표.
- **legacy**: 도달은 되게 하되 메인 맵 직접 링크 대신 **전용 인덱스**(예: `docs/specs/old/_README.md`) 경유 →
  맵 척추엔 legacy 폴더 링크 1개, 개별 legacy는 그 인덱스 안에서 도달. 아티팩트(D3)는 legacy 흐리게 표시.

## 5. D2 — new vs preexisting 링크 판별

**판별 규칙:** 링크를 문서 위치 기준 **절대(레포-상대) 타겟**으로 해석(`rewrite_links`가 옳으면 이동 전/후가
같은 실제 타겟). 그러면:

> **new_broken = current(이사 후)서 깨졌는데, 그 타겟이 base(원본)엔 존재했던 링크** (= 우리가 깨뜨림 → 차단)
> **preexisting_broken = current·base 둘 다 없음** (= 원래 깨져 있던 것 → 보존·표면화, 비차단)

- 예① 이동 문서 링크 미-rebase → 현재 옛경로 비어 broken, 타겟은 base엔 있었음 → **new(우리 버그) → 차단.**
- 예② 스테일 코드참조 `src/apis/`(re-base 정확) → 현재·base 둘 다 없음 → **preexisting → 표면화만.**

**새 헬퍼 필요:** gate.analyze는 **도달 문서만** 링크 검사(BFS). base는 대부분 orphan이라 안 봄 → **도달성 무관
전-문서 링크 해석 함수**(gate `resolve` 의미론 재사용)로 base·current를 diff. scaffold/register가 얹는 링크는
실재 인덱스/문서라 new_broken 유발 0.

**오라클 일원화:** 이 계산을 `build_and_verify`에 얹어 Phase 1b(스크래치)와 Phase 3(랜딩)이 같은 정의 공유.

## 6. Phase 4 — 재진단(결과 아티팩트)

- doc-health를 **랜딩된 worktree(옮긴·커밋 상태)**에 재실행 → after 스코어.
- Phase 0 before와 나란히 → `render_report(data, "result")`. before→after 대비(등급 F→?·orphan→0·마커/척추/
  성장루프 설치)를 시각화.
- **result 모드 CSS는 이전 증분 이연분** — 이번에 채움. 동결 CSS·WCAG-AA·인라인 style 0 유지.
- before/after가 같은 채점기(doc-health)라 등급 비교 공정 — doc-health 분리의 원래 취지 실현.

## 7. 테스트 & 롤아웃 (RED-first)

| # | 조각 | RED-first 검증 |
|---|---|---|
| T1 | `register_all` | in-place·legacy 섞인 fixture에서 orphan=0(이동 안 한 문서·legacy도 등록). legacy는 전용 인덱스 경유 |
| T2 | 링크 오라클 | "이동 문서 링크 미-rebase"→new_broken 검출; "스테일 코드참조"→preexisting 분류 |
| T3 | `land_migration` 통과 | 브랜치 생성·단일 커밋·worktree 제거·실 작업트리 무영향 |
| T4 | `land_migration` 실패 | new_broken 주입 시 커밋 0·브랜치 0·흔적 0 |
| T5 | Phase 4 result 모드 | 이연 CSS 존재·AA 대비·인라인 style 0 게이트 |

**e2e 순서:** 합성 fixture(제자리 docs + legacy + 스테일 코드링크 + 이동-문서 링크)로 end-to-end GREEN **먼저**
→ **그다음 vd-front 실 dogfood**(브랜치 산출, 검토·머지는 사용자).

**정체성 게이트(불가침):** 매 조각이 내용 소실 0·앵커 보존·비파괴를 지키는지 각 테스트가 강제.

## 8. 스코프 밖 (별도 트랙)

- **배치 판단** — 타입 vs 기능응집 조직(Diátaxis 흩뿌림 vs 폴더 응집). 도메인 결정 패널 필요(D5 포함).
  Phase 3 실행 메커니즘과 분리(엔진은 승인된 move_plan을 그대로 실행).
- **아티팩트 UX** — D3(트리 접이식·타입색)·D4(은어 제거)·D6(이동 집약뷰·자기설명). render_report 병렬 트랙.
- **깊은 처리** — .mdx content_oracle 지원 · 정규화 transformed · non-git clone (증분 3서 이연된 것들 유지).
