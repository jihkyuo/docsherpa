# doc-reconcile 최신화·유연화·자가성장 재설계 (Implementation Plan) — rev6

> **For agentic workers:** REQUIRED SUB-SKILL: 승인 후 superpowers:subagent-driven-development / executing-plans. **리뷰용 설계 문서** — 승인 전 구현 금지.

**Goal:** doc-reconcile을 **핵심(문서를 코드에 맞게 유지)만** 하게 쪼개고, 아키텍처 규칙 변경은 **setup-docs의 가벼운 규칙 모드**(이미 있는 승인+two-oracle 재사용)로 라우팅. + 임베드 최신화(sidecar)·유연성·안전한 자가성장.

**Architecture — 2-tool (rev6, rev5의 3-tool 단순화):**
```
setup-docs      아키텍처 세우기(부트스트랩) + 규칙 변경(가벼운 규칙 모드) — 둘 다 승인 + two-oracle
doc-reconcile   문서를 코드에 맞게 유지 — 규칙(routing) 읽기만, 목차(index) append, 규칙변경은 신고만
```
- **맵 추출·전용 도구·주석 포인터·맵 포맷버전 전부 폐기.** 규칙(routing)·목차(index) 마커는 **AGENTS.md 인라인 유지** → gate 도달성 BFS·자동주입 컨텍스트 **무변경**(rev5 F1·F8 근본 소멸).
- **소유권 = 섹션 단위:** `docsherpa:routing` 섹션 = **setup-docs 규칙모드**가 편집. `docsherpa:index` 섹션 = **doc-reconcile이 append**. 같은 파일, 다른 섹션, 섹션-스코프 편집 → clobber 없음(F7 소멸).
- **doc-reconcile은 규칙을 절대 안 바꾼다.** 새 범주 반복 등장 = **신고만** → 사용자가 setup-docs 규칙모드 실행.

**계층 자율:** 사용자 수동 = ①설치 ②setup-docs. 이후:
- **doc-reconcile 루틴 = 자동** — 단 UPDATE 자동은 **기계로 명확한 것만**(리터럴이 문서에 **정확히 1회** 등장 + 새값==코드 실제값 + 비동결본문). 그 외(패러프레이즈·복수등장·산문)는 **확인**.
- **규칙 변경(setup-docs 규칙모드) = 항상 승인 + dry-run + two-oracle.**
- **실행 끝 요약 = 항상.**

**Tech Stack:** Python 3 stdlib only, pytest, Markdown 산문.

**검증 이력:** rev1 consult → rev2 challenge+architect → rev3 자가비판 → rev4 설계대화 → rev4 재검증(P1 다수) → rev5 3-tool 분할 → **rev5 재검증(F1 gate BFS 붕괴·과분할·동결오류 등) → rev6: 2-tool 단순화(규칙변경=setup-docs 모드) + 맵추출 폐기 + F1~F8 반영.** §13.

## Global Constraints
- **North Star (불가침):** 비파괴·내용 소실 0. 모든 실패 분기 = write 스킵. **도달성 100%(gate broken=0·orphan=0)가 내용소실 0의 기계 강제선 — 절대 훼손 금지.**
- **UPDATE 자동 = 명확한 것만:** 리터럴 정확히 1회 등장 + 새값==코드 실제값 + 비동결본문. 그 외 확인. **자동 슬라이스는 좁다**(정직히 명시). content_oracle은 **마이그레이션 oracle로 유지**(UPDATE 가드로 쓰지 않는다 — DESIGN §9).
- **동결 = 본문 단위, 상태·인덱스 예외:** accepted ADR/plan **본문**은 동결, 상태 라인·`decisions/README` 로그 행·`_template`은 편집 허용. 폴더 단위 denylist 금지.
- **규칙 변경 = doc-reconcile 밖 + 승인:** setup-docs 규칙모드(승인+two-oracle)만. doc-reconcile은 신고만.
- **맵/마커 = AGENTS.md 인라인, gate 무변경.** 정본 리터럴 0(가드). stdlib only. 커밋마다 push.

## 1. 문제·배경
P1(임베드 팀공유)·P2(최신화)·P3(유연성·자가성장) 충돌.

**rev4·rev5 재검증에서 확인된 것 (rev6 근거):**
- content_oracle은 UPDATE 안전을 못 지킴(전-repo dedup·대체 self-certifying, DESIGN §9). → UPDATE 가드에서 빼되 **마이그레이션 oracle로 유지**(원래 그 용도).
- 마커 grep·주석 포인터·목차 이전은 **gate 도달성 BFS를 깨거나 논결정 재유입** → **맵 추출 자체를 폐기**, 인라인 유지가 정답.
- 규칙변경 전담 3번째 도구는 **과분할** — setup-docs가 이미 승인+two-oracle을 가짐 → **setup-docs 규칙모드로 재사용**.
- 동결을 폴더 단위로 하면 살아있는 인덱스(`decisions/README`)·plan 상태를 잘못 삼킴 → **본문 단위 동결**.
- doc-reconcile CREATE가 규칙 없는 문서를 배치하면 **조용한 아키텍처 오염** → **정확히 1규칙 매칭 시만 자동**.

## 2. 결정
| # | 결정 | 근거 | supersede |
|---|---|---|---|
| **N1** | 앵커 특화 폐기, 임베드=범용 척추 | 특화 marginal, P2 단순화 | D4 |
| **N2** | 프라임=플러그인 우선/임베드 fallback | 최신 플러그인 우위 | 이전 철회 |
| **N3** | sidecar up-only refresh(무프롬프트+별도커밋+릴리스서명) | 로컬 완결·downgrade 차단 | R4 재정의 |
| **N4** | **doc-reconcile 핵심만:** UPDATE + CREATE(**정확히 1규칙 매칭 시만 자동**, 아니면 신고+보류) + 규칙drift 신고. routing 안 씀, index append만. | 역할 과다·CREATE 오염 봉쇄. | rev5 N4 |
| **N5** | 계층 자율: 루틴 자동(UPDATE 좁게) / 규칙변경=setup-docs 규칙모드+승인 | 잦은 저위험 자동, 규칙변경만 게이트 | rev5 N5 |
| **N6** | 안전=기계. **UPDATE 자동=리터럴 1회+코드값+비동결본문**. content_oracle=마이그레이션 유지. | self-certifying·모호성 제거. | rev5 N6 |
| **N7** | **규칙 변경 = setup-docs 가벼운 규칙 모드**(독립 도구 아님). dry-run+승인+**two-oracle(gate+content_oracle) 재사용**. doc-reconcile은 신고만. | 검증된 안전기계 재사용·과분할 회피. UX(가벼움·분리)는 유지. | rev5 N8(docsherpa:map) 폐기 |
| **N8** | **맵 추출 폐기 — 규칙/목차 마커 AGENTS.md 인라인 유지.** 소유권=섹션 단위(routing=setup-docs, index=doc-reconcile append). gate·자동주입 무변경. | 주석포인터·목차이전이 gate BFS 붕괴·자동주입 손해(F1·F8). 인라인이 정답. | rev5 N7(맵 externalize) 폐기 |
| **N9** | 동결=본문 단위, 상태·인덱스·템플릿 예외 | 폴더 denylist가 살아있는 인덱스 삼킴(F3·F4) | rev5 N6 동결 |
| **N10** | 실행 끝 항상 요약 | 무프롬프트라도 가시성 | — |

## 3. 메커니즘

### 3.1 sidecar
설치 시 `.claude/skills/doc-reconcile/.docsherpa-loop.json`=`{version,hash}`. `canonical_hash`=정규화(utf-8-sig→LF→스탬프 제거→트레일링LF) 후 sha256. 부재/불일치/파싱실패 → write 스킵 + stuck 신호.

### 3.2 up-only refresh (Tier1 무프롬프트)
```
0. provenance(플러그인 root=target 밖 + plugin.json name==docsherpa) 실패→STOP·무언급
1. 임베드+sidecar 로드 (없음→setup / 파싱실패→STOP+nudge)
2. version_gt(V_p,V_e) [int-튜플,fail-closed] No→STOP(downgrade 차단)
3. hash==sidecar.hash? No→skip+stuck / 4
4. 릴리스 서명 일치? No→STOP(오염) / 5   ← 오염 주방어선
5. 재검증(unmerged 0 + git diff 빈값) → temp+atomic rename
6. 별도 툴링 커밋(그 두 파일만): chore(docsherpa): auto-refresh vX→vY
```
- **맵 포맷 커플링 없음(F2 소멸):** 규칙이 AGENTS.md 인라인 산문이라 별도 맵 포맷/버전 계약이 없다 → refresh가 척추만 올려도 맵-포맷 skew 데드락이 생길 여지 자체가 없음.

### 3.3 self-update 거주·이식성
척추의 "플러그인 실행 시만" 분리 부록. Alice→provenance 통과·작동. Bob→실패·STOP·무언급. 이식성: 실패 시 no-op → portable 가드 통과.

### 3.4 scaffold.py 변경 (gate.py는 무변경 — F1·F6 소멸)
- `install_loop_files`: `not exists` 유지(R4) + sidecar 기록.
- 신규 `refresh_loop(repo_root, plugin_root)`: §3.2 기계검증+자동쓰기+별도커밋.
- **`write_router`는 현행 유지**(라우팅/인덱스 마커 인라인 생성). 맵 externalize 없음.
- **`gate.py --require-markers` 변경 없음** — 마커가 AGENTS.md 인라인이라 현행 검사 그대로.
- 헬퍼: parse_stamp·strip_stamp·normalize·canonical_hash·version_gt·load/write_sidecar·verify_plugin_provenance·verify_release_signature. 조회 `.get()` 가드.

### 3.5 doc-reconcile 핵심 역할 (N4)
```
규칙(routing 섹션) 도달 가능?
  아니오 → UPDATE 자동편집 금지, 읽기전용 stale 인벤토리 + "setup-docs로 세팅 제안"(제안-only)
  예     → UPDATE + CREATE(정확히 1규칙 매칭 시만 자동) + 규칙drift 신고
```
- **UPDATE(N6):** git diff→변경 리터럴 grep. **자동 = 타겟 문서에 그 리터럴이 정확히 1회 + 새값==코드 실제값 + 비동결본문.** 복수등장·패러프레이즈·산문 재작성 = **확인**. content_oracle는 안 씀(마이그레이션 전용).
- **CREATE:** routing 섹션의 **정확히 1개 규칙에 매칭**되면 그 규칙대로 신설 + **index 섹션에 append**(도달성 closeout, orphan=0). **매칭 규칙 0개 or 승격(룰#4) or 복수 규칙 = write 안 함 + 규칙변경 신고·보류.**
- **규칙drift 신고:** 규칙 없는 문서가 반복 등장 = 편집·배치 말고 **"setup-docs 규칙모드로 규칙 추가 검토" 신고**만. routing 섹션은 절대 안 건드림.

### 3.6 setup-docs 규칙 모드 (N7)
- **트리거:** 사용자 호출(가벼운 규칙모드) or doc-reconcile 신고 후 사용자 실행. **부트스트랩 재실행 아님** — 이미 세팅된 repo면 Phase0 진단이 HEALTHY → 재-scaffold 없이 규칙 변경만.
- **동작:** ①dry-run 영향 리포트(새 규칙에 걸리는 기존 문서·before/after 라우팅·**"각 문서가 정확히 1규칙 매칭" 결정론 검증**) ②승인 ③routing 섹션만 편집(폴더 승격 시 링크 리라이트) ④**two-oracle(gate 도달성 + content_oracle 내용보존) 재사용** ⑤별도 커밋.
- **재사용:** 이 안전기계는 setup-docs MESSY 마이그레이션 파이프라인이 이미 보유 — 규칙모드는 그 focused 진입점.

### 3.7 자율 계층 + 끝 요약 (N5·N10)
- **자동:** refresh · CREATE(1규칙 매칭) · UPDATE(리터럴 1회 명확).
- **확인:** UPDATE 모호/산문 · **규칙 변경(setup-docs 규칙모드, 항상)**.
- **끝 요약(항상):** 📝갱신N·🆕신설M · ⚙️refresh(있으면) · ⚠️규칙drift 신고/규칙변경(강조) · git diff 포인터. 무변경 시 `Docs-Impact: none`.

## 4. 시나리오
- **S1 refresh:** clean+서명OK+상위버전 → 무프롬프트 자동+별도커밋. ✓
- **S2~S4:** downgrade 차단 / hash-dirty 보존 / 무-sidecar 보존 = write 스킵. ✓
- **S5 UPDATE 명확:** MAX_RETRY 3→5, 문서에 "3"이 그 맥락 1회 → 자동 "5"(비동결). ✓
- **S6 UPDATE 모호:** "3"이 문서에 2곳("3 retries"·"3 phases") → 자동 안 함, 확인. ✓
- **S7 UPDATE 패러프레이즈:** "최대 세 번" → 리터럴 없음 → 자동 미히트, **확인 경로로 flag**(침묵 누락 방지). ✓
- **S8 동결본문:** 옛 ADR 본문의 옛 값 → 본문 동결 → 안 건드림. 단 `decisions/README` 로그 행 append는 **허용**. ✓
- **S9 CREATE 1규칙:** 구조결정 → routing 규칙 1개 매칭 → ADR 신설 + index append. ✓
- **S10 CREATE 무규칙/승격:** runbooks(규칙 없음) or 룰#4 승격 대상 → **write 안 함 + 규칙변경 신고**. 사용자가 setup-docs 규칙모드 → dry-run+승인+two-oracle → 규칙 추가·배치. ✓
- **S11 맵 없음:** routing 섹션 없는 repo → 읽기전용 인벤토리 + setup 제안. 자동편집 0. ✓
- **S12 gate 무변경:** 마커 인라인 유지 → `--require-markers` 현행대로 PASS, 도달성 BFS 무변경. ✓
- **S13 끝 요약:** 무프롬프트 작업도 끝에 요약, 규칙 관련 강조. ✓

## 5. P3 재정리
- **유연성:** doc-reconcile은 routing 섹션(인라인)이 기술한 대로 동작 — 어떤 아키텍처든. 없어도 UPDATE 인벤토리 제공.
- **자가성장:** 콘텐츠=doc-reconcile 자동. 규칙=setup-docs 규칙모드(승인) → 규칙도 자라되 안전.
- **North Star 강제기 보존:** 마커·목차 인라인 유지로 gate 도달성 BFS 무변경 → 내용소실 0 기계 강제선 그대로.

## 6. 트레이드오프
> **2-tool로 "역할 하나씩"(문서 유지 vs 아키텍처 세우기·규칙변경)을 얻되 도구 수 증가 0. 안전은 기계(UPDATE 리터럴대조·refresh hash/서명·규칙 two-oracle)에 얹고, 규칙변경만 승인. 맵 추출·전용도구·포맷버전을 폐기해 rev5보다 단순 + gate/자동주입 무변경.**
대가: UPDATE 자동 슬라이스가 좁음(모호·패러프레이즈는 확인). 이득: 유연성·안전한 자가성장·역할 명료·rev5 F1~F8 봉쇄·구현 표면 최소.

## 7. 테스트
- **T1~T10** refresh(up+커밋/up-only/hash-dirty/무-sidecar/provenance/정규화/version_gt/R4/최초설치/릴리스서명).
- **T11 UPDATE 1회 자동:** 리터럴 정확히 1회+코드값 → 자동. **T12 복수등장:** 2곳 → 확인(자동 0). **T13 패러프레이즈:** 리터럴 없음 → 확인 경로 flag.
- **T14 동결본문:** ADR/plan 본문 옛 값 → 편집 0. **T14b 인덱스 예외:** `decisions/README` 로그·plan 상태 라인 → 편집 허용.
- **T15 CREATE 1규칙:** 1개 매칭 → 신설+index append. **T16 CREATE 무규칙/승격:** 0개 or 승격 or 복수 → write 0 + 신고.
- **T17 규칙 섹션 불변:** doc-reconcile은 routing 섹션 해시 불변(index만 append).
- **T18 setup-docs 규칙모드:** dry-run+승인+two-oracle+"1규칙 매칭" 검증. 승인 없이 규칙 미변경.
- **T19 gate 무변경:** `--require-markers` 현행 PASS, 도달성 BFS 무변경(회귀 없음).
- **T20 맵 없음:** 인벤토리+제안, 자동편집 0.
- **T21 이식성:** portable 가드 통과(앵커-assert 삭제). **T22 §9 parity 재베이스.**

## 8. Task
1. 헬퍼(정규화·버전·sidecar·provenance·릴리스서명). 2. `refresh_loop` 무프롬프트+별도커밋+stuck(T1~T10).
3. **N1 특화 폐기** + 임베드 범용화·sidecar. 앵커-assert 삭제(T21).
4. **N4·N6 doc-reconcile 핵심:** 척추를 UPDATE(리터럴 1회 자동/모호·산문 확인/본문동결·인덱스예외) + CREATE(1규칙만 자동, 아니면 신고) + drift 신고로 재작성. content_oracle을 UPDATE 가드에서 제외(마이그레이션 유지)(T11~T17·T20·T22).
5. **N7 setup-docs 규칙모드:** MESSY 파이프라인의 승인+two-oracle을 focused "규칙 추가/승격" 진입점으로 노출. dry-run+승인+"1규칙" 검증(T18).
6. **N8 인라인 유지 확인:** write_router·gate 무변경 회귀 테스트(T19). 소유권 섹션 계약(routing=setup, index=reconcile) 문서화.
7. **N5·N10 자율계층+끝요약.** N2 프라임.
8. **ADR + 도달성:** D4 supersede·R4 재정의·N4/N5/N7/N9 ADR + `decisions/README.md` + DESIGN §9 parity 재베이스 + 이 계획 인덱스 등록.

## 9. 열린 질문
- **OQ (해결):** sidecar / version_gt int-튜플 / UPDATE=리터럴 1회(content_oracle 아님) / 규칙변경=setup-docs 모드+승인 / 맵 인라인 유지.
- **OQ-a:** 동결 판정 = frontmatter `docsherpa_frozen: body|all|none` vs 경로+상태 휴리스틱. 추천: frontmatter 우선 + 휴리스틱 fallback.
- **OQ-b:** setup-docs 규칙모드 진입 = 별도 플래그(`--rule`) vs Phase0가 신고를 감지해 제안. 추천: 둘 다.
- **OQ-c:** UPDATE 패러프레이즈 drift(리터럴 없음)를 어디까지 탐지 — 코드 심볼명 기반 근접 탐색 vs 확인-only. 추천: 심볼명 근접 + 확인.
- **OQ-d:** 릴리스 서명 강도 — M5.

## 10. 상태
- **리뷰 대기(rev6).** 승인 전 구현 금지.
- 검증: consult(rev1)+challenge+architect(rev2)+자가비판(rev3)+설계대화(rev4)+재검증(rev4·rev5)+**rev6 재검증 예정.**

## 13. 검증 기록
### rev1~4 (요약)
sidecar·기계안전·3능력·자율 → rev4 재검증에서 content_oracle 가짜안전·grep 논결정·gate 붕괴·N8 위험.
### rev5 재검증 (codex+architect) — rev6에 반영
- **F1(최고위험) 주석포인터+목차이전이 gate 도달성 BFS 붕괴:** BFS는 링크·import만 따라감, 주석 미포함 → 맵 orphan → 전문서 도달불가. → **맵 추출 폐기, 인라인 유지(N8), gate 무변경.**
- **과분할(docsherpa:map):** setup-docs가 이미 승인+two-oracle 보유 → **규칙변경=setup-docs 규칙모드(N7), 3-tool→2-tool.**
- **CREATE 규칙드리프트 오염:** → **정확히 1규칙 매칭 시만 자동(N4), 아니면 신고+보류.**
- **동결 폴더단위 오류:** `decisions/README`·plan 상태 삼킴, SKILL §3와 충돌 → **본문 동결·상태/인덱스 예외(N9).**
- **UPDATE self-certifying:** 새값==코드값은 삽입에 의해 항상 참, occurrence 미검증 → **리터럴 정확히 1회일 때만 자동(N6).** content_oracle는 마이그레이션 유지("제거" 프레이밍 오류 정정).
- **맵 포맷 skew 데드락 / 자동주입 손해(F2·F8):** 맵 externalize 폐기로 **동시 소멸.**
### rev6 — 2-tool 단순화
규칙변경을 전용 도구 아니라 setup-docs 규칙모드로, 맵 추출 폐기(인라인 유지)로 gate·자동주입 보존. 사용자의 "규칙변경 분리·가볍게" 목표는 유지(setup-docs focused 모드), 검증의 "안전기계 재사용·gate 불변식 보존"도 충족.
