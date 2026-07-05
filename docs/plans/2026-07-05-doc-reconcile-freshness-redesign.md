# doc-reconcile 최신화·유연화·자가성장 재설계 (Implementation Plan) — rev5

> **For agentic workers:** REQUIRED SUB-SKILL: 승인 후 superpowers:subagent-driven-development / executing-plans로 task 단위 구현. **리뷰용 설계 문서** — 승인 전 구현 금지.

**Goal:** doc-reconcile을 **핵심 역할(문서를 코드에 맞게 유지)만** 하도록 쪼개고, 아키텍처 규칙 진화는 **전담 도구(승인제)**로 분리한다. + 임베드 최신화(sidecar)·유연성(어떤 아키텍처든)·자가성장(규칙도 자람, 단 안전하게)을 동시에 만족.

**Architecture — 3-way 도구 분할 (rev5 핵심):**
```
setup-docs      아키텍처를 처음 세운다 (설치 시 1회, 승인)
doc-reconcile   문서를 코드에 맞게 유지 (매 세션) — 기존 규칙만 따름, 규칙은 안 건드림
docsherpa:map   아키텍처 규칙을 진화시킨다 (가끔, 반드시 승인 + dry-run 리포트)   ← 신설
```
- **doc-reconcile 핵심만:** UPDATE(낡은 문서 수리) + CREATE(새 문서를 **기존 규칙대로** 배치·목차 등록) + **규칙drift 신고**(행동 아님). **규칙(라우팅) 자체는 절대 안 바꾼다.**
- **docsherpa:map(신설):** 새 범주 등장 등으로 규칙이 부족할 때 규칙 추가·폴더 승격·마커 유지보수. **자율 아님 — 항상 사용자 승인 + 영향 dry-run.**
- **맵 = 규칙 섹션(도구 소유) + 목차 섹션(doc-reconcile 추가)** 을 **분리**해 두 도구가 안 충돌.

**계층 자율 (단순화):** 사용자 수동 = ①설치 ②setup-docs. 이후:
- **doc-reconcile 루틴 = 대부분 자동** — 단 UPDATE 자동은 **기계로 검증되는 것만**(코드값 대조 리터럴 치환 + 동결문서 제외), 산문 재작성은 확인.
- **규칙 변경(docsherpa:map) = 항상 승인** (드물고 고위험이라 자율 아님).
- **실행 끝 요약 = 항상.**

**Tech Stack:** Python 3 stdlib only, pytest(`uv run --with pytest`), Markdown 산문 스킬.

**검증 이력:** rev1 consult → rev2 challenge+architect → rev3 자가비판(안전=기계) → rev4 설계대화(맵·3능력·자율) → **rev4 재검증에서 P1 다수 발견**(content_oracle 가짜안전·grep 논결정·gate.py 붕괴·N8 위험) → **rev5: 도구 3-way 분할(사용자 결정) + 검증 P1 반영.** §13.

## Global Constraints
- **North Star (불가침):** 비파괴·내용 소실 0. 모든 실패 분기 = **write 스킵**.
- **얇은 진입 라우터:** AGENTS.md/CLAUDE.md는 맵을 **링크만**.
- **UPDATE 안전 = 기계검증 가능한 것만 자동:** 코드 diff가 준 리터럴 치환(새값==코드값)만 Tier1-자동. 산문·의미 재작성은 확인. **동결문서(LICENSE·CHANGELOG·`decisions/`·`plans/`·accepted ADR 본문)는 자동 편집 금지.** ⚠️ content_oracle을 UPDATE 가드로 쓰지 않는다(§13 rev4·DESIGN §9: 재작성·모순 통과, dedup 마스킹).
- **맵 식별 = 도달성(grep 아님):** 진입→맵 링크를 따라간 그 문서의 **펜스 밖** 마커만 정본. 0/복수/언링크는 fail-closed.
- **규칙 변경 = 항상 승인.** 정본 리터럴 0(가드 유지). stdlib only. 커밋마다 push.

## 1. 문제·배경
세 하드 제약: P1(임베드 팀공유)·P2(최신화)·P3(어떤 아키텍처든 유연 + 자가성장).

**rev4가 과욕했고 재검증(codex+architect)이 P1 다수 발견:**
- **content_oracle는 UPDATE 안전을 못 지킴** — repo 전체 dedup이라 중복 세그먼트 삭제 불가시(A파일서 지워도 B에 남으면 통과), 대체 편집은 self-certifying(환각과 정답 동일 통과). DESIGN §9가 이미 "correctness에 쓰지 마라" 명시.
- **마커 repo-wide grep은 논결정적** — 이 repo서 17~18곳 히트, clean 유저 repo도 setup 후 ≥2히트(진짜 맵 + 설치 사본).
- **N7이 gate.py `--require-markers`(AGENTS.md 하드코딩)를 깨뜨림.**
- **N8 맵 자가진화 = 자기수정 라우팅 엔진 + 도장 게이트** — 오진화가 미래 전 문서 조용히 오배치. 둘 다 "컷" 권고.

**사용자 결정:** N8을 없애지 말고 **전담 도구로 분리 + 승인**. doc-reconcile은 역할 과다 → **핵심만.** rev5는 이 분할 + 나머지 P1 수정.

## 2. 결정
| # | 결정 | 근거 | supersede |
|---|---|---|---|
| **N1** | 앵커 특화 폐기, 임베드=범용 척추 | 특화 가치 marginal, P2 단순화 | D4 |
| **N2** | 프라임 = 플러그인 우선, 임베드 fallback | 최신 플러그인 우위 | 이전 철회 |
| **N3** | sidecar up-only refresh(무프롬프트+별도커밋+릴리스서명) | 로컬 완결, downgrade 차단 | R4 재정의 |
| **N4** | **doc-reconcile 핵심만:** UPDATE + CREATE(기존 규칙) + 규칙drift 신고. **규칙 안 바꿈.** | 역할 과다 해소(검증). 규칙 변경은 별 도구. | rev4 N4·N8 |
| **N5** | **계층 자율:** 루틴 자동(UPDATE는 기계검증분만) / 규칙 변경(docsherpa:map)=승인 | 귀찮음=빈도 탓. 잦은 저위험 자동, 규칙변경만 승인. | rev4 N5 |
| **N6** | 안전=기계. **UPDATE 가드=리터럴치환-코드대조+동결제외**(content_oracle 아님). 세그먼트-additive만 content_oracle 보조. | content_oracle가 재작성·중복삭제 못 잡음(검증 A). | rev4 N6 수정 |
| **N7** | 아키텍처 맵 = **규칙 섹션 + 목차 섹션 분리**. 식별=**도달성**(grep 아님). gate.py 마커검사를 맵으로 리다이렉트. 인라인→분리 마이그레이션 계약(포맷 버전). | 얇은 라우터 + 진입불문 + 도구 경계 청결. grep 논결정·gate 붕괴 봉쇄. | 마커 AGENTS.md 인라인 |
| **N8** | **docsherpa:map 신설 — 규칙 관리 전담 도구.** 규칙 추가·폴더 승격·마커 유지보수. **항상 승인 + dry-run 영향 리포트 + "규칙당 1문서" 검증 + 별도 커밋.** setup=부트스트랩/map=진화/reconcile=소비·신고. | 자가성장(규칙도 자람) 유지하되 안전(전담+승인). 검증의 "self-modifying 엔진" 위험 제거. | rev4 N8(자율진화) 폐기 |
| **N9** | 실행 끝 항상 요약(계층별 강조) | 무프롬프트라도 가시성 | — |

## 3. 메커니즘

### 3.1 sidecar (임베드 최신화 진실)
설치 시 `.claude/skills/doc-reconcile/.docsherpa-loop.json`=`{version,hash}`. `canonical_hash`=정규화(utf-8-sig→LF→스탬프 제거→트레일링LF) 후 sha256. hash-clean=`==sidecar.hash`. 부재/불일치/파싱실패 → write 스킵 + stuck 신호.

### 3.2 up-only refresh (Tier1 무프롬프트)
```
0. provenance(플러그인 root=target 밖 + plugin.json name==docsherpa) 실패→STOP·무언급
1. 임베드+sidecar 로드 (없음→setup / 파싱실패→STOP+nudge)
2. version_gt(V_p,V_e) [int-튜플, fail-closed] No→STOP(downgrade 차단)
3. hash==sidecar.hash? No→skip+stuck / 4
4. 릴리스 서명 일치? No→STOP(오염) / 5   ← 오염 주방어선(승인 아님)
5. 재검증(unmerged 0 + git diff 빈값) → temp+atomic rename
6. 별도 툴링 커밋(그 두 파일만): chore(docsherpa): auto-refresh vX→vY
```

### 3.3 self-update 거주·이식성
척추의 "플러그인 실행 시만" 분리 부록. Alice→provenance 통과·작동. Bob→실패·STOP·무언급. 이식성: 실패 시 no-op → portable 가드 통과.

### 3.4 scaffold.py + gate.py 변경
- `install_loop_files`: `not exists` 유지(R4) + sidecar 기록.
- 신규 `refresh_loop(repo_root, plugin_root)`: §3.2 기계검증+자동쓰기+별도커밋. `scaffold()`는 호출 안 함.
- **`write_router`(N7):** 진입 파일엔 **맵 링크** `<!-- docsherpa:map <path> -->` 1개 + 맵 문서에 규칙/목차 섹션·마커 생성.
- **`gate.py --require-markers`(N7 수정):** AGENTS.md 하드코딩 폐기 → **진입의 map 포인터를 따라가 맵에서** 마커 확인(도달성 BFS·`FENCE_RE` 재사용). 맵 0/복수/언링크 → FAIL.
- 헬퍼: parse_stamp·strip_stamp·normalize·canonical_hash·version_gt·load/write_sidecar·verify_plugin_provenance·verify_release_signature·resolve_map(도달성). 모든 조회 `.get()` 가드.

### 3.5 아키텍처 맵 (N7)
- **맵 = 전용 문서**(예 `docs/_doc-map.md`), 진입에서 **`<!-- docsherpa:map <path> -->` 포인터 1개**로 지목(도달성). doc-reconcile/map은 **grep 아니라 포인터→맵**으로 식별. 0/복수/언링크 fail-closed.
- **두 섹션 분리(다른 write-path·다른 소유자):**
  - **규칙 섹션**(`docsherpa:routing`) = **docsherpa:map 소유.** "어떤 문서를 어디에."
  - **목차 섹션**(`docsherpa:index`) = **doc-reconcile이 append**(도달성 closeout). 규칙 아님.
- **맵 포맷 버전:** 맵 frontmatter `docsherpa_map_format: N`. 척추/도구가 호환 포맷 선언, skew면 STOP+nudge(refresh가 척추만 갱신하는 데서 오는 drift 봉쇄).
- **어떤 아키텍처든:** 맵은 setup 시 사용자 repo에 핏하게 생성(권장구조든 사용자 고유구조든 실제 레이아웃 기술).
- **마이그레이션(인라인→분리):** 이 repo 등 기존 AGENTS.md 인라인 마커 → map이 규칙/목차를 맵 문서로 이전 + 진입에 포인터 + **인라인 마커 제거**를 한 단계로. 마커 소스 이중 존재는 hard fail.

### 3.6 doc-reconcile 핵심 역할 (N4)
```
맵(도달 가능) 있음?
  아니오 → UPDATE는 자동편집 금지, 읽기전용 stale 인벤토리 + "setup-docs로 맵 생성 제안"(제안-only)
  예     → UPDATE + CREATE(규칙대로) + 규칙drift 신고
```
- **UPDATE(N6):** git diff→변경 리터럴 grep. **Tier1-자동 = 코드값 대조 리터럴 치환(새값==코드 실제 새값) + 동결문서 제외.** 산문·의미 재작성은 **확인**(사람이 충실성 판단, content_oracle 못함).
- **CREATE:** 규칙대로 새 문서 배치 + **목차 섹션에 append**(도달성, orphan=0). 규칙 섹션은 안 건드림.
- **규칙drift 신고:** 기존 규칙에 안 맞는 문서가 반복(≥2회)되면 편집 말고 **"docsherpa:map 돌려 규칙 추가 검토" 신고**만.

### 3.7 docsherpa:map (신설, N8)
- **트리거:** 사용자 호출 or doc-reconcile 신고.
- **동작:** ①영향 dry-run 리포트(어떤 기존 문서가 새 규칙에 걸리는지·before/after 라우팅·**"각 문서가 정확히 1규칙에 매칭" 결정론 검증**) ②**사용자 승인** ③규칙 섹션만 write + 마커 유지보수 ④gate(도달성) 검증 ⑤별도 라벨 커밋.
- **추론·소비 분리(검증 codex#4):** 규칙을 넣는 실행과 그 규칙으로 배치하는 실행을 섞지 않는다(map은 규칙만, 배치는 다음 reconcile).
- **부트스트랩 아님:** 맵이 아예 없으면 map이 무에서 강요 안 함 → setup-docs 소관.

### 3.8 자율 계층 + 끝 요약 (N5·N9)
- **자동(무프롬프트):** refresh · CREATE · UPDATE(기계검증분).
- **확인:** UPDATE 산문 재작성 · **docsherpa:map 규칙 변경(항상)**.
- **끝 요약(항상):** 📝갱신N·🆕신설M · ⚙️refresh(있으면) · ⚠️규칙drift 신고/규칙 변경(강조) · git diff 포인터. 무변경 시 `Docs-Impact: none`.

## 4. 시나리오
- **S1 refresh:** clean+서명OK+상위버전 → 무프롬프트 자동 + 별도 커밋. ✓
- **S2 downgrade 차단 / S3 hash-dirty 보존 / S4 무-sidecar 보존:** 전부 write 스킵. ✓
- **S5 UPDATE 기계치환:** MAX_RETRY 3→5(코드값 5) → 문서 "3"을 "5"로 자동(비동결 문서만, 새값=코드값 검증). ✓
- **S6 UPDATE 산문:** "동작 방식이 바뀜"류 → 자동 안 함, **확인.** ✓
- **S7 동결문서:** grep이 CHANGELOG/옛 ADR의 옛 값 히트 → 동결 제외 → 안 건드림. ✓ (rev4 위험 봉쇄)
- **S8 맵 없음:** 읽기전용 인벤토리 + 맵 생성 제안. 자동편집 0. ✓
- **S9 CREATE:** 규칙대로 ADR 신설 + 목차 append(규칙 섹션 불변). ✓
- **S10 규칙drift → map:** runbooks 2회 → doc-reconcile **신고** → 사용자가 docsherpa:map 호출 → dry-run+승인 → 규칙 추가. **doc-reconcile은 규칙 안 건드림.** ✓
- **S11 맵 식별:** 진입 포인터 따라 맵 1개 특정(설치 사본·펜스 마커 무시). 복수/언링크 → fail-closed. ✓
- **S12 gate:** N7 후에도 `--require-markers`가 포인터 따라 맵서 마커 확인 → PASS. ✓
- **S13 끝 요약:** 무프롬프트 작업도 끝에 요약, 규칙 관련 강조. ✓

## 5. P3 재정리
- **유연성:** doc-reconcile은 레이아웃 아니라 "맵(규칙+도달성)"에만 의존. 어떤 구조든 맵이 기술하면 동작. 맵 없어도 UPDATE 인벤토리는 제공.
- **자가성장:** 콘텐츠(문서)=doc-reconcile 자동. **아키텍처(규칙)=docsherpa:map 승인제** → 규칙도 자라되 안전.
- single-source: taxonomy는 맵 규칙 섹션 한 곳. 척추엔 generic 메타룰만.

## 6. 트레이드오프
> **3-way 분할로 "역할 하나씩"을 얻는 대신 도구 1개 증가. 안전은 사람 리뷰가 아니라 기계(UPDATE 리터럴대조·refresh hash/서명·맵 dry-run/승인)에 얹고, 규칙 변경만 사람 승인. 자가성장은 유지하되 위험(규칙)은 게이트.**
대가: 도구·계약(맵 포맷·map 포인터) 증가. 이득: 유연성·안전한 자가성장·역할 명료·rev4 P1 봉쇄.

## 7. 테스트
- **T1~T4** refresh: up+커밋 / up-only / hash-dirty 보존 / sidecar부재 보존.
- **T5 provenance · T6 정규화대칭 · T7 version_gt(0.0.10>0.0.9, malformed fail-closed) · T8 R4 · T9 최초설치+sidecar · T10 릴리스서명.**
- **T11 UPDATE 기계치환:** 새값==코드값이면 자동, ≠면 안 함.
- **T12 UPDATE 산문 확인:** 재작성 편집 → 자동 안 하고 확인 경로.
- **T13 동결 제외:** CHANGELOG/`decisions/`/`plans/`/LICENSE → 자동 편집 0.
- **T14 맵 없음:** 인벤토리+제안, 자동편집 0.
- **T15 맵 식별 도달성:** 진입 포인터→맵 1개. 설치 사본·펜스 마커 무시. 복수/언링크 → fail(T15b).
- **T16 gate.py 맵 리다이렉트:** `--require-markers`가 맵서 마커 확인, AGENTS.md 인라인 없어도 PASS. 기존 마커 테스트 갱신.
- **T17 규칙/목차 분리:** doc-reconcile CREATE는 목차만 append, 규칙 섹션 불변(해시 동일).
- **T18 docsherpa:map:** dry-run 리포트 + 승인 없이는 규칙 미변경 + "규칙당 1문서" 검증 + 추론/소비 분리.
- **T19 규칙drift 신고:** ≥2회 미매칭 → doc-reconcile이 신고만(규칙 미변경).
- **T20 맵 포맷 skew:** 척추 포맷!=맵 포맷 → STOP+nudge.
- **T21 마이그레이션:** 인라인→분리, 마커 이중 존재 hard fail.
- **T22 이식성:** portable 가드 통과(앵커-assert 삭제). **T23 §9 parity 재베이스.**

## 8. Task
1. 헬퍼(정규화·버전·sidecar·provenance·릴리스서명). 2. `refresh_loop` 무프롬프트+별도커밋+stuck(T1~T10).
3. **N7 맵 추출:** `write_router` 진입=map 포인터·맵=규칙/목차 분리 섹션·포맷버전. `resolve_map`(도달성). **gate.py `--require-markers` 맵 리다이렉트**(T15·T16·T20). 이 repo(dogfood) 인라인→분리 마이그레이션(T21).
4. **N1 특화 폐기** + 임베드 범용화·sidecar. 앵커-assert 삭제(T22).
5. **N4 doc-reconcile 핵심:** 척추를 UPDATE(기계치환-자동/산문-확인/동결제외) + CREATE(목차만) + drift 신고로 재작성. **content_oracle을 UPDATE 가드에서 제거**(T11~T14·T17·T19·T23).
6. **N8 docsherpa:map 신설:** 새 스킬. dry-run+승인+규칙섹션 write+gate+별도커밋+추론/소비 분리(T18).
7. **N5·N9 자율계층+끝요약.** N2 프라임.
8. **ADR + 도달성:** D4 supersede·R4 재정의·N4/N5/N7/N8 ADR + `decisions/README.md` + DESIGN §9 parity 재베이스 + 이 계획 인덱스 등록.

## 9. 열린 질문
- **OQ (해결):** sidecar / version_gt int-튜플 / UPDATE 가드=리터럴대조(content_oracle 아님) / 맵 식별=도달성 / 규칙변경=승인.
- **OQ-a:** 맵 파일 단일 vs 규칙·목차 **파일 분리**. 추천: 최소 **섹션 분리**(다른 write-path), 파일 분리는 구현 시.
- **OQ-b:** docsherpa:map 트리거 — 사용자 호출만 vs doc-reconcile 신고 자동 제안. 추천: **둘 다**(신고→사용자 호출).
- **OQ-c:** 새 도구 이름(`docsherpa:map` 가칭). M5 확정.
- **OQ-d:** 릴리스 서명 강도(체크섬 최소 vs 서명) — M5.

## 10. 상태
- **리뷰 대기(rev5).** 승인 전 구현 금지. 승인 시 TDD 확장 + 인덱스 등록.
- 검증: consult(rev1)+challenge+architect(rev2)+자가비판(rev3)+설계대화(rev4)+재검증(rev4)+**rev5 재검증 예정.**

## 13. 검증 기록
### rev1~3 (요약)
consult→sidecar/fallback. challenge+architect→sidecar확정·R4봉쇄·정규화·provenance·fallback폐기. 자가비판→안전을 기계로(N6).
### rev4 재검증 (codex+architect) — P1 다수, rev5에 반영
- **content_oracle 가짜안전(최고위험):** repo 전체 dedup(중복 세그먼트 삭제 불가시) + 대체 self-certifying + DESIGN §9 자기위반 → **UPDATE 가드에서 제거, 리터럴-코드대조+동결제외로 대체(N6).**
- **마커 grep 논결정(최고위험):** 17~18곳 히트·clean repo도 ≥2 → **도달성 포인터 식별(N7).**
- **gate.py `--require-markers` 붕괴:** AGENTS.md 하드코딩 → **맵 리다이렉트(N7·Task3).**
- **N8 자율진화 위험 / Tier 경계 흐림:** self-modifying 라우팅 엔진 → **전담 도구 분리+승인(N8), 규칙/목차 섹션 분리(N7).**
- **UPDATE-only가 STOP보다 위험:** 동결문서 재작성 → **맵 없으면 인벤토리+제안(자동편집 0).**
- refresh↔맵 포맷 skew → **맵 포맷 버전(N7).**
### rev5 — 사용자 결정: 3-way 도구 분할
규칙 변경을 "없애기(검증안)"가 아니라 **전담 도구(docsherpa:map)+승인**으로 분리. doc-reconcile은 **핵심(문서 유지)만**, 규칙은 소비·신고만. 자가성장 유지 + 위험 게이트 + 역할 명료. + 나머지 P1(content_oracle·grep·gate.py) 반영.
