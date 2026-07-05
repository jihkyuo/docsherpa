# doc-reconcile 최신화·유연화·자가성장 재설계 (Implementation Plan) — rev8

> **For agentic workers:** REQUIRED SUB-SKILL: 승인 후 superpowers:subagent-driven-development / executing-plans. **리뷰용 설계 문서** — 승인 전 구현 금지.
> **rev8 상태:** 5라운드 교차검증(codex+architect) 수렴. **기존 코드에 대조해 검증된 것은 N8 인라인마커(gate 무변경)·N6 마이그레이션 oracle뿐이다.** sidecar/refresh(§3.1–3.4)·끝요약(N10)은 **설계·교차검증 완료이나 코드 미구현**(TDD T1–T10). rev8은 재설계가 아니라 **정직화 마감** — rev7이 남긴 자기-과장('코드 검증 완료' 오기)·refresh 트리거 부재·N1 편집 3면 중 1면 누락·N7 append 순서버그를 닫는다. **최종 검증은 새 세션에서 진행 예정.**

**Goal:** doc-reconcile을 **핵심(문서를 코드에 맞게 유지)만** 하게 쪼개고, 아키텍처 규칙 변경은 **setup-docs**로 라우팅. 임베드 최신화(sidecar)·유연성·안전한 자가성장. **안전 태세를 실제(진짜 기계 vs 에이전트 산문+커밋리뷰)에 정직히 맞춘다.**

**Architecture — 2-tool:**
```
setup-docs      아키텍처 세우기(부트스트랩) + 규칙 변경 — 승인 (규칙-텍스트=gate만 / 폴더승격=MESSY 파이프라인)
doc-reconcile   문서를 코드에 맞게 유지 — 규칙(routing) 읽기만·first-match로 배치, 목차(index) append, 규칙변경은 신고만
```
- **맵 추출·전용도구·주석포인터·맵포맷버전 폐기.** 규칙(routing)·목차(index) 마커 = **AGENTS.md 인라인 유지** → gate 도달성 BFS·자동주입 무변경.
- **소유권 = 섹션 단위:** `docsherpa:routing` = setup-docs 편집 / `docsherpa:index` = doc-reconcile append. 섹션-스코프.
- **doc-reconcile은 규칙을 절대 안 바꾼다.**

**⚠️ 안전 태세 (정직화 — rev7 핵심):**
- **기계 강제선 3개(정직 캐비엇 포함):** ①refresh(**검사·쓰기=결정론 Python**; 트리거=doc-reconcile step0; 단 릴리스 서명=OQ-d/M5 미정이라 §3.2 step4 '오염 차단'은 미완결) ②gate.py 도달성(broken=0·orphan=0) ③content_oracle(마이그레이션·폴더승격 내용보존 — **고유 세그먼트 단위**: 동일 세그먼트 중복 시 한 인스턴스 유실은 통과, 인스턴스 개수 미보존 `content_oracle.py:10`. '내용 소실 0'은 이 한도 내 기계 강제).
- **doc-reconcile 루틴 편집(UPDATE·CREATE)은 기계 보증이 아니다.** doc-reconcile엔 스크립트가 없다(전부 산문 스킬). 안전선 = **에이전트 판단 + anti-hallucination 인용(§4) + 커밋 전 git diff 사람 리뷰(끝 요약이 그 surface).** 이는 North Star와 정합 — North Star의 기계 보증(content_oracle)은 원래 **마이그레이션에만** 걸린 계약이고, 루틴 편집은 커밋 리뷰로 받는다.

**계층 자율:** 사용자 수동 = ①설치 ②setup-docs. 이후:
- **doc-reconcile 루틴 = 무프롬프트 자동**(UPDATE·CREATE). 안전선 = **커밋 리뷰**(기계 아님).
- **규칙 변경 = setup-docs + 승인.**
- **실행 끝 요약 = 항상.**

**Tech Stack:** Python 3 stdlib only, pytest, Markdown 산문.

**검증 이력:** rev1 consult → rev2 challenge+architect → rev3 자가비판 → rev4 설계대화+재검증 → rev5 3-tool → rev5 재검증(F1 gate BFS 붕괴 등) → rev6 2-tool 단순화 → rev6 재검증 → rev7 "기계" 과장 철회·auto-CREATE first-match 정정 → **rev8 재검증(codex+architect): refresh 트리거 부재·'코드 검증' 자기과장·N1 3면 중 1면만 편집·N7 append 死룰 봉쇄.** §13.

## Global Constraints
- **North Star (불가침):** 비파괴·내용 소실 0. 도달성 100%(gate)가 마이그레이션 내용소실 0의 **기계** 강제선. 루틴 편집은 커밋 리뷰가 net(기계 아님을 정직히).
- **UPDATE 자동은 좁은 편의:** 리터럴이 문서에 명확히 대응할 때 자동 치환(새값=코드 실제값). **패러프레이즈/단위/서술 drift는 리터럴 신호가 없어 못 잡는다(정직) — 최신화 보장 아님.** content_oracle은 UPDATE에 안 쓴다(마이그레이션 전용, DESIGN §9).
- **동결 = 산문 규칙(오라클 없음, 정직):** frontmatter `docsherpa_frozen: body|all|none` 우선, 없으면 휴리스틱(첫 `##` 이후 본문 동결·상태라인/`decisions/README` 로그행/`_template` 예외). 기계 강제 아님.
- **규칙 변경 = doc-reconcile 밖 + 승인:** setup-docs. doc-reconcile은 신고만.
- **마커 AGENTS.md 인라인, gate 무변경.** 정본 리터럴 0. stdlib only. 커밋마다 push.

## 1. 문제·배경
P1(임베드 팀공유)·P2(최신화)·P3(유연성·자가성장).

**4라운드 검증에서 확정된 것(rev7 근거):**
- content_oracle은 UPDATE 안전 못 지킴(dedup·self-cert, DESIGN §9) → 마이그레이션 전용 유지, UPDATE는 커밋리뷰 net.
- 맵 externalize(주석포인터·목차이전)는 gate 도달성 BFS 붕괴 → **인라인 유지가 정답**(F1, 코드 확인).
- 규칙변경 전담 도구는 과분할 → setup-docs로.
- **doc-reconcile은 스크립트 없는 산문 스킬** → "기계 보증" 주장은 self-cert. 안전=에이전트+인용+커밋리뷰로 정직화.
- auto-CREATE "정확히 1규칙 매칭"은 순서판정+catch-all 룰과 논리 충돌 → **first-match(디폴트 유효)로 정정.**

## 2. 결정
| # | 결정 | 근거 | supersede |
|---|---|---|---|
| **N1** | 앵커 특화 폐기, 임베드=범용 척추 | 특화 marginal, P2 단순화 | D4 |
| **N2** | 프라임=플러그인 우선/임베드 fallback | 최신 플러그인 우위 | 이전 철회 |
| **N3** | sidecar up-only refresh(별도커밋+릴리스서명) | 로컬완결·downgrade 차단. **검사·쓰기=기계(결정론 Python), 트리거=doc-reconcile step0**(plugin_root 확보). 서명 step은 M5. | R4 재정의 |
| **N4** | **doc-reconcile 핵심만:** UPDATE + CREATE(**routing 규칙 first-match로 배치**, 디폴트#5가 catch-all) + index append + 규칙drift **신고**. routing 안 씀. | 역할 과다 해소. "정확히 1규칙"이 순서판정 룰과 충돌 → first-match 정정(항상 도달가능 배치, 막다른길 없음). | rev6 N4 |
| **N5** | 계층 자율: 루틴 무프롬프트 자동(UPDATE·CREATE) / 규칙변경=setup-docs+승인. **루틴 안전선=커밋리뷰(기계 아님).** | 잦은 저위험 자동, 규칙변경만 게이트. | rev6 N5 |
| **N6** | **안전 정직화.** 진짜 기계=refresh+gate+content_oracle(마이그레이션). doc-reconcile 루틴=에이전트+인용+커밋리뷰. UPDATE 자동=명확 리터럴만(좁음). | doc-reconcile 무스크립트 → "기계" 주장은 self-cert 재발. | rev6 N6("기계" 과장) |
| **N7** | 규칙 변경=setup-docs. **(a)규칙-텍스트 추가=catch-all(#5) 앞 삽입+gate 재실행**(순수 append 금지 — first-match라 맨뒤면 #5가 선점→새 규칙 死. gate는 순서 미검증→삽입위치=에이전트). **(b)폴더 승격=기존 MESSY 파이프라인**(two-oracle·링크리라이트). | 규칙변경 무게가 케이스별 극단 → 명시 분기. 검증된 파이프라인 재사용, 전용도구 안 만듦. | rev6 N7 + rev8 append 死룰 |
| **N8** | 맵 추출 폐기 — 마커 AGENTS.md 인라인, 소유권 섹션 단위. gate·자동주입 무변경. | F1(gate BFS)·F8(자동주입) 봉쇄. 코드로 해결 확인. | rev6 N8 |
| **N9** | 동결=산문 규칙(frontmatter 우선, 오라클 없음 정직), 상태·인덱스·템플릿 예외 | 폴더 denylist가 살아있는 인덱스 삼킴(F3·F4). 단 기계 아님. | rev6 N9 |
| **N10** | 실행 끝 항상 요약(계층별 강조 + git diff 포인터=리뷰 surface) | 무프롬프트 안전선이 커밋리뷰라 가시성 필수 | — |

## 3. 메커니즘

### 3.1 sidecar (진짜 기계)
`.claude/skills/doc-reconcile/.docsherpa-loop.json`=`{version,hash}`. `canonical_hash`=정규화(utf-8-sig→LF→스탬프제거→트레일링LF) 후 sha256. 부재/불일치/파싱실패 → write 스킵 + stuck 신호.

### 3.2 up-only refresh (doc-reconcile step0 트리거 · 검사·쓰기=기계)
```
0. provenance(플러그인 root=target 밖 + plugin.json name==docsherpa) 실패→STOP·무언급
1. 임베드+sidecar 로드 (없음→setup / 파싱실패→STOP+nudge)
2. version_gt(V_p,V_e) [int-튜플,fail-closed] No→STOP(downgrade 차단)
3. hash==sidecar.hash? No→skip+stuck / 4
4. 릴리스 서명 일치? No→STOP(오염) / 5
5. 재검증(unmerged 0 + git diff 빈값) → temp+atomic rename
6. 별도 툴링 커밋(그 두 파일만): chore(docsherpa): auto-refresh vX→vY
```
**트리거 (F1 봉쇄):** `refresh_loop`는 SessionStart 훅(target 안, `cat` 산문)에서 **못 부른다** — plugin_root(=target 밖)를 넘길 수 없기 때문. 따라서 **doc-reconcile 플러그인 스킬의 step0**으로 배선한다(`/docsherpa:doc-reconcile` 실행 시 plugin_root 확보). 즉 검사·쓰기는 결정론 Python(기계)이되, **주기는 '매 세션 무조건'이 아니라 'doc-reconcile 호출 시'**(정직). '무프롬프트'=쓰기 승인이 기계검증이란 뜻이지 세션마다 자동 발화가 아니다.
**⚠️ step4 릴리스 서명:** 스펙은 OQ-d(M5). 정의 전까지 refresh는 **hash+provenance만으로 스코프**하고 step4 '오염 차단'에 '기계 강제'를 주장하지 않는다.
맵 포맷 커플링 없음(인라인 산문) → skew 데드락 여지 없음.

### 3.3 self-update 거주·이식성
척추의 "플러그인 실행 시만" 분리 부록. Alice→provenance 통과. Bob→실패·STOP·무언급. 이식성: 실패 시 no-op → portable 가드 통과.

### 3.4 scaffold.py 변경 (gate.py 무변경)
- `install_loop_files`: `not exists` 유지(R4) + sidecar 기록.
- 신규 `refresh_loop(repo_root, plugin_root)`: §3.2 기계검증+자동쓰기+별도커밋.
- `write_router`·`gate.py --require-markers` **무변경**(마커 인라인).
- 헬퍼: parse_stamp·strip_stamp·normalize·canonical_hash·version_gt·load/write_sidecar·verify_plugin_provenance·verify_release_signature. 조회 `.get()` 가드.

### 3.5 doc-reconcile 핵심 역할 (N4·N6 — 에이전트 산문, 기계 아님)
```
routing 규칙 도달 가능?
  아니오 → UPDATE 자동편집 금지, 읽기전용 stale 인벤토리 + "setup-docs로 세팅 제안"
  예     → UPDATE(자동, 커밋리뷰 net) + CREATE(first-match 배치) + 규칙drift 신고
```
- **UPDATE:** git diff→변경 리터럴 grep→기존 문서 수리. **자동=리터럴이 타겟에 명확히 대응할 때 새값(=코드 실제값)으로 치환, 비동결본문.** ⚠️ **패러프레이즈("최대 세 번")·단위·서술 drift는 리터럴 신호가 없어 자동으로도 flag로도 못 잡는다(정직) — auto-UPDATE는 최신화 보장이 아니라 좁은 편의.** 안전선=인용+커밋리뷰.
- **CREATE:** routing 규칙 **first-match**(위에서 먼저 맞는 것, 룰#5 디폴트가 catch-all)로 배치 → **항상 도달가능한 위치에 신설 + index append**(orphan 0). 막다른 길·거짓 차단 없음. 규칙 적용은 아키텍처 변경이 아니다.
- **규칙drift 신고:** 어떤 문서가 **디폴트(#5)로만 반복 흡수**되고 전용 규칙이 있으면 더 나을 때 = **"setup-docs로 규칙 추가 검토" 산문 신고**(비블로킹 제안). 문서는 이미 디폴트로 배치됨(적체·유실 없음). routing은 안 건드림.

### 3.6 setup-docs 규칙 변경 (N7)
- **트리거:** 사용자 호출 or doc-reconcile 신고 후 실행. **부트스트랩 재실행 아님** — 이미 세팅 repo면 Phase0=HEALTHY → 재-scaffold 없음.
- **(a) 규칙-텍스트 추가**(예 "runbooks → runbooks/"): routing 섹션의 **catch-all(#5 "그 외 단일") 바로 앞에 삽입**(맨 뒤 append 금지 — first-match라 #5가 먼저 걸려 새 규칙이 死) + 규칙 번호 재부여 → **gate.py 재실행**(단 gate는 링크·고아만 보고 **라우팅 순서는 검증 못 함** — 삽입 위치는 에이전트 책임). 파일 이동 없어 content_oracle 불요·내용소실 위험 0. 가벼움.
- **(b) 폴더 승격 + 링크 리라이트:** 파일 이동 → **기존 MESSY 마이그레이션 파이프라인 진입**(base 스냅샷 + two-oracle + 링크리라이트 1급 + worktree). 무게 있음, 하지만 검증된 기계 재사용.
- dry-run + 사용자 승인 필수.

### 3.7 자율 계층 + 끝 요약 (N5·N10)
- **자동(무프롬프트, net=커밋리뷰):** refresh(기계) · UPDATE(명확 리터럴) · CREATE(first-match).
- **확인/외부:** UPDATE 모호·산문(에이전트가 커밋리뷰에 노출) · **규칙 변경(setup-docs, 승인).**
- **끝 요약(항상):** 📝갱신N·🆕신설M · ⚙️refresh(있으면) · ⚠️규칙drift 신고(강조) · **→ git diff로 검토(안전 surface).** 무변경 시 `Docs-Impact: none`.

## 4. 시나리오
- **S1 refresh:** clean+서명OK+상위버전 → 무프롬프트 자동+별도커밋. ✓(진짜 기계)
- **S2~S4:** downgrade 차단 / hash-dirty 보존 / 무-sidecar 보존 = write 스킵. ✓
- **S5 UPDATE 명확:** MAX_RETRY 3→5, 문서에 그 맥락 "3" 명확 → 자동 "5"(비동결), 커밋 diff에 노출. ✓
- **S6 UPDATE 모호/패러프레이즈:** "3"이 2곳 or "세 번" → **자동 안 함.** 패러프레이즈는 신호 없어 flag도 못 냄(정직: 이 stale은 이번 세션이 못 잡음, pre-existing으로 남음 — 내용 소실 아님). ✓
- **S7 CREATE first-match:** 구조결정 → 룰#1 매칭 → decisions/ 신설 + index/README **링크** 추가. 일반 참조 → 룰#5 디폴트 → docs/ 평면. **항상 *배치*는 됨.** 단 도달성은 자동 아님 — decisions/README 로그행은 링크가 아니라, 에이전트가 신설 ADR로 가는 마크다운 링크를 안 걸면 orphan(gate가 사후 검출). ✓(배치 항상 / 도달=에이전트 링크+gate 사후)
- **S8 규칙drift 신고:** runbooks가 디폴트로 3회 흡수 → 문서는 배치됨(적체 없음) + "runbooks 규칙 추가 검토" 비블로킹 신고. ✓
- **S9 규칙 추가(setup-docs a):** 사용자 실행 → routing **catch-all #5 앞 삽입**(맨 뒤 append면 first-match로 死룰) → gate 재실행 PASS(gate는 순서 미검증 → 삽입위치=에이전트 책임). content_oracle 불요. ✓
- **S10 폴더 승격(setup-docs b):** 기존 문서 이동 → MESSY 파이프라인(two-oracle). ✓
- **S11 맵 없음:** 읽기전용 인벤토리 + setup 제안, 자동편집 0. ✓
- **S12 gate 무변경:** 마커 인라인 → `--require-markers` 현행 PASS, BFS 무변경. ✓

## 5. P3 재정리
- **유연성:** doc-reconcile은 routing 섹션(인라인)대로 동작 — 어떤 아키텍처든. 없어도 인벤토리 제공.
- **자가성장:** 콘텐츠=doc-reconcile 자동(커밋리뷰 net). 규칙=setup-docs 승인. 규칙도 자라되 안전.
- **North Star 강제기 보존:** 인라인 유지로 gate 도달성 BFS 무변경.

## 6. 트레이드오프
> **안전 태세를 정직히 계층화한다: 진짜 기계(refresh·gate·마이그레이션 oracle)는 강하게, doc-reconcile 루틴 편집은 "에이전트+인용+커밋리뷰"로 정직히. "기계 보증"을 루틴 편집에 주장하지 않는다.**
- **auto-UPDATE는 좁다:** 명확 리터럴만. 패러프레이즈 drift는 못 잡음(보조 도구의 한계, 내용 소실은 아님). 최신화를 "보장"으로 팔지 않는다.
- **2-tool·인라인 유지·전용도구 0**으로 rev5 대비 구현 표면 최소. F1~F8 봉쇄(대부분 삭제로).

## 7. 테스트
- **T1~T10** refresh(up+커밋/up-only/hash-dirty/무-sidecar/provenance/정규화/version_gt/R4/최초설치/릴리스서명) — 진짜 기계, TDD.
- **T11 UPDATE 명확 리터럴:** 문서에 대응 명확+코드값 → 자동. **T12 모호:** 복수/패러프레이즈 → 자동 0(패러프레이즈는 미탐지 정직).
- **T13 CREATE first-match:** 룰#1 → decisions/, 일반 → 디폴트 docs/. 항상 index 등록(orphan 0). **T13b 규칙drift 신고:** 디폴트 반복 흡수 → 비블로킹 신고(문서는 배치됨).
- **T14 동결(산문/frontmatter):** `docsherpa_frozen` 있으면 준수, 없으면 휴리스틱. 상태라인/decisions-README/템플릿 예외.
- **T15 setup-docs 규칙-텍스트(a):** append+gate만, content_oracle 미호출. **T15b 승격(b):** MESSY two-oracle 진입.
- **T16 gate 무변경 회귀:** `--require-markers` 현행 PASS, BFS 무변경.
- **T17 이식성:** portable 가드 통과(앵커-assert 삭제). **T18 §9 parity 재베이스.**

## 8. Task
1. 헬퍼(정규화·버전·sidecar·provenance·릴리스서명). 2. `refresh_loop` 검사·쓰기(결정론)+별도커밋+stuck(T1~T10). **트리거 배선: doc-reconcile 플러그인 step0에서 호출**(plugin_root 확보) — SessionStart `cat` 훅은 plugin_root 못 넘기므로 불가. **릴리스 서명(step4)은 OQ-d/M5 — 그전엔 refresh를 hash/provenance만으로 스코프, step4 '기계' 미주장.**
3. **N1 특화 폐기**+임베드 범용화·sidecar. **3면 모두 편집:** (i) `test_doc_reconcile_portable.py` 앵커-assert 삭제(T17) (ii) `setup-docs/SKILL.md §7.5 step5`(앵커 특화 절차) 삭제 (iii) `doc-reconcile/SKILL.md`의 `docsherpa:anchors` 경계 주석("setup-docs가 특화한다") 정정 — 블록은 범용 유지, '특화' 문구 제거.
4. **N4·N6 doc-reconcile 핵심(산문 개정):** UPDATE(명확 리터럴 자동/모호·패러프레이즈 미탐지 정직) + CREATE(first-match 배치+index) + drift 신고. **"기계 보증" 문구 제거, "커밋리뷰 net" 명시.** content_oracle을 UPDATE에서 제외(T11~T13·T18). **+ N9 동결 산문규칙**(frontmatter `docsherpa_frozen` 우선 + 휴리스틱 fallback)을 §손대지말것에 추가(T14).
5. **N7 setup-docs 규칙변경:** (a)텍스트append+gate / (b)승격=MESSY 명시 분기(T15).
6. **N8 인라인 유지 확인:** write_router·gate 무변경 회귀(T16).
7. **N5·N10 자율계층+끝요약(커밋리뷰 surface).** N2 프라임. **N5 무프롬프트 자동은 현행 doc-reconcile "먼저 요약 제안→갱신할까요?" 승인-우선 출력과 충돌 → 출력/승인 산문을 티어별로 개정**(자동=명확 리터럴 UPDATE·first-match CREATE / 확인=모호 UPDATE·규칙변경). 끝요약(N10)은 신규 산문(미구현, '코드 검증' 아님).
8. **ADR + 도달성:** D4 supersede·R4 재정의·N4/N5/N6/N7/N9 ADR + `decisions/README.md` + DESIGN §9 parity 재베이스 + 이 계획 인덱스 등록. **+ `AGENTS.md` 따름원칙(18행) 수정: "§7.5 앵커 재특화" 인용 제거**(N1이 삭제한 메커니즘) — 내용·앵커 보존을 gate+content_oracle+scaffold append-only로 재귀속, 사용자 "내용 앵커" vs doc-reconcile "드리프트 휴리스틱 앵커" 용어 분리.

## 9. 열린 질문
- **OQ-a:** 동결 판정 frontmatter 강제 vs 휴리스틱 — 추천: frontmatter 우선+휴리스틱 fallback(기계 아님 정직).
- **OQ-b:** setup-docs 규칙변경 진입 = `--rule` 플래그 vs Phase0가 신고 감지 제안 — 추천 둘 다.
- **OQ-c:** 패러프레이즈 drift 탐지 확대(심볼명 근접) 여부 — 추천: best-effort 산문으로만, 기계 보장 주장 금지.
- **OQ-d:** 릴리스 서명 강도 — M5.

## 10. 상태
- **리뷰 대기(rev8). 최종 검증은 새 세션에서 진행 예정.** 승인 전 구현 금지.
- **기존 코드에 대조해 검증된 것:** N8 인라인(gate 무변경, `gate.py`/`scaffold.py` 확인) · N6 content_oracle 마이그레이션 복귀(`content_oracle.py`). **§3.1~3.4 sidecar/refresh·N10 끝요약은 설계·교차검증 완료이나 코드 미구현(TDD T1~T10) — '코드 검증' 아님.**
- **정직화 트림 반영(rev7):** auto-CREATE first-match · "기계" 라벨 철회 · S6/S7 패러프레이즈 정직 · 규칙모드 (a)/(b) 분기.
- **정직화 마감 반영(rev8):** refresh 트리거=doc-reconcile step0 확정 · '코드 검증 완료' 오기 정정 · N1 3면 편집(setup-docs §7.5·doc-reconcile 주석·AGENTS.md) · N7(a) catch-all 앞 삽입(append 死룰 봉쇄) · content_oracle dedup·S7 도달성·N5 승인흐름·릴리스서명(M5) 캐비엇.

## 13. 검증 기록
### rev1~5 (요약)
sidecar·기계안전·3능력·자율 → 재검증 반복으로 content_oracle 가짜안전·맵 externalize의 gate BFS 붕괴·과분할·동결 폴더오류·CREATE 드리프트·self-cert를 순차 봉쇄. rev6에서 2-tool+인라인 유지로 대폭 단순화.
### rev6 재검증 (codex+architect) — rev7에 반영
- **확인 해결:** F1(gate BFS) 코드로 무변경 확인 · F2/F8(맵포맷·자동주입) 소멸 · 3번째 도구 제거 · content_oracle 마이그레이션 복귀.
- **[P1] auto-CREATE "정확히 1규칙":** 순서판정+catch-all 룰과 논리 충돌(거짓 차단→매세션 재신고) → **first-match로 정정**(항상 도달가능 배치, 막다른길 없음).
- **[P1] "안전=기계" 과장:** doc-reconcile 무스크립트=산문 → self-cert 재발 → **"기계" 철회, 에이전트+인용+커밋리뷰 net으로 정직화.**
- **[P1] S7 패러프레이즈 flag 오버클레임:** 리터럴 없으면 신호 없음 → **정직히 "미탐지, 보조 한계"**로 정정.
- **[P2] 규칙모드 무게:** (a)텍스트=gate만 / (b)승격=MESSY 분기.
### rev7 — 정직화 트림 (사용자 결정: 반영, 최종검증 새 세션)
재설계 아니라 삭제·정직화: 과장된 기계 주장 철회, auto-CREATE 술어 정정, 패러프레이즈 한계 명시, 규칙변경 무게 분기. 진짜 기계(refresh·gate·마이그레이션 oracle)와 에이전트 산문(doc-reconcile 루틴)을 정직히 구분. North Star 정합(마이그레이션만 기계 보증, 루틴은 커밋리뷰 net).
### rev8 재검증 (codex+architect 5라운드) — 반영
rev7이 정직화를 표방하고도 남긴 구멍 5개를 닫음:
- **[블로커] refresh 트리거 부재:** `refresh_loop` 호출자 없음 + SessionStart `cat` 훅이 plugin_root(target 밖) 못 넘김 → **doc-reconcile step0 배선**으로 확정, 주기='doc-reconcile 호출 시'(매 세션 아님)로 정정.
- **[정직·아이러니] '코드 검증 완료' 오기:** sidecar/refresh·N10은 레포에 코드 부재(`rg refresh_loop`=계획서에만) → '설계·교차검증, 코드 미구현(TDD)'으로 재라벨. 검증된 것은 N8/N6뿐.
- **[모순] N1 3면 중 1면만 편집:** Task 3이 portable 테스트만 삭제 → `setup-docs/SKILL.md §7.5 step5` + `doc-reconcile/SKILL.md:54` 주석 + `AGENTS.md:18`을 Task 3/8에 추가(안 하면 "특화하라"는 死지침·삭제 메커니즘 인용 잔존).
- **[버그] N7(a) append 死룰:** first-match+맨뒤 append → catch-all #5가 선점해 새 규칙 미발동, gate는 순서 미검증 → **#5 앞 삽입**으로 정정.
- **[정직] 캐비엇 추가:** content_oracle dedup(인스턴스 미보존) · S7 도달성(에이전트 링크+gate 사후) · 릴리스 서명(M5 미정) · N5 무프롬프트 vs 현행 승인-우선 출력 충돌.
- **North Star 실질 안전(architect 판정):** 진짜 내용보존은 gate+content_oracle+scaffold이지 §7.5가 아니므로 N1은 정체성 위협 아님. 단 `AGENTS.md:18`의 §7.5 인용은 원래부터 용어 오귀속 → 수정.
