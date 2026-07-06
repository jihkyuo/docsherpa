# doc-reconcile 최신화·유연화·자가성장 재설계 (Implementation Plan) — rev10

> **For agentic workers:** REQUIRED SUB-SKILL: 승인 후 superpowers:subagent-driven-development / executing-plans. **리뷰용 설계 문서** — 승인 전 구현 금지.
> **rev8 상태:** 5라운드 교차검증(codex+architect) 수렴. **기존 코드에 대조해 검증된 것은 N8 인라인마커(gate 무변경)·N6 마이그레이션 oracle뿐이다.** sidecar/refresh(§3.1–3.4)·끝요약(N10)은 **설계·교차검증 완료이나 코드 미구현**(TDD T1–T10). rev8은 재설계가 아니라 **정직화 마감** — rev7이 남긴 자기-과장('코드 검증 완료' 오기)·refresh 트리거 부재·N1 편집 3면 중 1면 누락·N7 append 순서버그를 닫는다.
> **⚠️ rev9 상태 (자가감사):** "문서 링크=주석" 진행자 오개념이 발단이 되어 전반 재감사. gate.py **실측**(얇은 CLAUDE.md → 일반 마크다운 링크 → 별도 맵 문서, AGENTS.md 없이 orphan=0 PASS)으로 **F9(맵 추출 기각 근거 거짓 — 일반 링크면 gate 통과) 판명 → N8 재오픈.** 추가 F10~F15.
> **rev10 상태 (spine 채택):** 사용자 결정 = **맵 중추 문서(N11, §3.8).** N8 뒤집힘. 패널(codex+architect)을 **올바른 프레임**(방향 확정·설계만 공격)으로 재검증 → **buildable 확인, 선결 4 blocker 도출**(커밋강제·locator·오라클·gate루트). BLOCKER-A는 **중간안 확정**(강제훅 안 넣음·sidecar 자가치유·opt-in훅·정직 라벨). **N11 초안 = 4 blocker 선결조건. 구현 승인 전 금지.**

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

**검증 이력:** rev1 consult → rev2 challenge+architect → rev3 자가비판 → rev4 설계대화+재검증 → rev5 3-tool → rev5 재검증(F1 gate BFS 붕괴 등) → rev6 2-tool 단순화 → rev6 재검증 → rev7 "기계" 과장 철회·auto-CREATE first-match 정정 → rev8 재검증(refresh 트리거·자기과장·N1·N7 死룰) → rev9 자가감사(F9 맵기각 근거거짓·F10~F15, N8 재오픈) → **rev10: 맵 중추 문서(N11) 채택 — 올바른 프레임 패널로 buildable 확인, 선결 4 blocker.** §13.

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
| **N8** ~~폐기~~ **정정→N11** | ~~맵 추출 폐기 — 인라인 유지~~ **뒤집힘.** 인라인 유지의 근거(F1 gate BFS 붕괴)가 rev9 F9로 거짓 판명(실측: 일반 링크면 gate 통과). 사용자 결정으로 **맵 중추 문서 채택**(§3.8 N11). | inline은 SPOF 없음이 장점이나, AGENTS.md 바쁜파일·없을수있음·얇은라우터 원칙이 우선. | **N11이 supersede** |
| **N9** | 동결=산문 규칙(frontmatter 우선, 오라클 없음 정직), 상태·인덱스·템플릿 예외 | 폴더 denylist가 살아있는 인덱스 삼킴(F3·F4). 단 기계 아님. | rev6 N9 |
| **N10** | 실행 끝 항상 요약(계층별 강조 + git diff 포인터=리뷰 surface) | 무프롬프트 안전선이 커밋리뷰라 가시성 필수 | — |
| **N11** | **맵 중추 문서 채택**(§3.8). routing+index를 진입파일 밖 `docs/_map.md`(중립명)로 이전, 진입파일엔 `docsherpa:map` 마커 링크 한 줄. 4 blocker 선결(§3.8). | 사용자 결정: AGENTS.md는 바쁜파일·부재가능·얇은라우터 원칙. F9로 인라인 강제 근거 소멸. **패널(codex+architect, 올바른 프레임) 재검증: buildable 확인.** | **N8** |

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

### 3.8 맵 중추 문서 (N11 — N8 뒤집음, rev10)
**결정:** routing+index 마커를 진입파일 밖 **중립명 맵 문서**(`docs/_map.md`)로 이전. 진입파일(AGENTS/CLAUDE/GEMINI 중 primary)엔 **마크다운 링크 한 줄 + `<!-- docsherpa:map -->` 마커**만 남긴다(주석이 링크가 아니라, 링크 줄을 도구가 찾/보호하는 마커). gate는 그 링크를 재귀 BFS로 따라가 맵에 도달(rev9 F9 실측: 일반 링크면 통과). 근거: AGENTS.md는 ①바쁜 파일(중추 휩쓸림) ②부재 가능(CLAUDE-only) ③얇은 라우터 원칙 → 별도 중추가 정합. 루트 footprint "2마커+~30줄"→"1마커+1링크"로 **감소**(브랜드 누출 아님, home만 중립명).

**선결 4 blocker (패널 codex+architect 수렴, 전부 spine 유지하며 해결):**
- **A · 커밋시점 강제(identity — 확정 중간안):** 인라인은 중추가 gate 시드 안이라 *구조적으로* 도달보장이었으나, 맵은 링크 하나 뒤 → 삭제+무검사 커밋 시 조용히 orphan(파일은 남음, 연결만 끊김). **강제 pre-commit 훅 안 넣음**(보조 not 주인·무의존 원칙 위반). 대신 ①**맵 home 경로를 sidecar에 기록** → 삭제가능 링크와 독립된 설치신호 → doc-reconcile 자가치유가 진짜 작동(codex "치유근거 없음" 봉쇄) ②강한 커밋훅=**opt-in** ③**정직 라벨:** gate·oracle=진짜 기계, 도달성은 그 기계가 검사, 강제 시점=doc-reconcile/gate 실행 시(+opt-in 훅). **조용한 유실 아님 — gate가 잡아 내용소실 0 유지.**
- **B · locator 구조화:** "본문에 두 마커 문자열" 순진탐색은 마커를 *설명*하는 문서(이 레포 `docs/DESIGN.md`·`0008-*.md`)를 false-home으로 잡음. → **펜스 제거 + `##` 헤딩 줄 끝 마커만** 인정, `--require-markers`에서만, **visited 전체**(진입파일 포함) 스캔, **정확히 1 home** 강제.
- **C · 오라클 투명(우아):** relpath 리라이트가 세그먼트 key 변경→content_oracle FAIL. → 인덱스 링크의 **표시 텍스트를 "결정 기록(ADR)" 같은 사람-라벨로, 경로는 URL 자리에만** 둔다(경로를 링크 텍스트로 쓰지 않음). normalize가 URL을 제거하므로 relpath가 바뀌어도 key 불변 → 리라이트가 oracle에 투명. (⚠️ 이 계획서 자체도 인라인 백틱 속 링크 문법이 gate에 잡히니 주의.)
- **D · gate 루트:** ENTRY_FILENAMES의 **.md 부분집합만** 루트로. 비-md 진입(.cursorrules 등)은 **미지원 명시**(도달성 검사 링크 못 앵커).

**나머지(blocker 후 기계적):** 인라인→맵 마이그레이션=**기존 MESSY 두-오라클 파이프라인 재사용**(원자성·STOP-on-loss) · 동결 예외=`docsherpa:index` **마커 기준**(맵의 첫 `##`가 index라 헤딩 휴리스틱은 전체 동결) · 다중진입=우선순위 **primary 1개**만 링크(중복 map-link 금지) · gate에 **줄 단위 파싱**(Target: source_line 필요) · **contract 모듈 먼저**(안 그러면 split-brain home 정의).

**과설계 금지(architect 기각):** ①ordering 데드락 **없음**(BFS는 home-무관, visited 먼저 생성 후 locator 사후스캔; 링크끊긴 맵은 docs/ orphan으로 구분됨) — 부트스트랩 기계 만들지 마라. ②브랜드 누출 **감소지 regression 아님**(ADR 0010은 스킬*이름* 브랜드 거부, HTML 마커는 D8로 수용) — 누출 고치는 코드 만들지 마라.

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
6. ~~**N8 인라인 유지 확인**~~ **→ N11 대체(rev10):** 인라인 유지 폐기. 대신 **맵 중추 문서(§3.8)** 구현 — contract 모듈 먼저 → locator(헤딩줄·유일성)·gate 루트(.md ENTRY_FILENAMES)·사람-라벨 인덱스·sidecar home 기록·인라인→맵 마이그레이션(MESSY 파이프라인). **4 blocker 선결 후 착수.** (T16은 spine 회귀 테스트로 재작성.)
7. **N5·N10 자율계층+끝요약(커밋리뷰 surface).** N2 프라임. **N5 무프롬프트 자동은 현행 doc-reconcile "먼저 요약 제안→갱신할까요?" 승인-우선 출력과 충돌 → 출력/승인 산문을 티어별로 개정**(자동=명확 리터럴 UPDATE·first-match CREATE / 확인=모호 UPDATE·규칙변경). 끝요약(N10)은 신규 산문(미구현, '코드 검증' 아님).
8. **ADR + 도달성:** D4 supersede·R4 재정의·N4/N5/N6/N7/N9 ADR + `decisions/README.md` + DESIGN §9 parity 재베이스 + 이 계획 인덱스 등록. **+ `AGENTS.md` 따름원칙(18행) 수정: "§7.5 앵커 재특화" 인용 제거**(N1이 삭제한 메커니즘) — 내용·앵커 보존을 gate+content_oracle+scaffold append-only로 재귀속, 사용자 "내용 앵커" vs doc-reconcile "드리프트 휴리스틱 앵커" 용어 분리.

## 9. 열린 질문
- **OQ-a:** 동결 판정 frontmatter 강제 vs 휴리스틱 — 추천: frontmatter 우선+휴리스틱 fallback(기계 아님 정직).
- **OQ-b:** setup-docs 규칙변경 진입 = `--rule` 플래그 vs Phase0가 신고 감지 제안 — 추천 둘 다.
- **OQ-c:** 패러프레이즈 drift 탐지 확대(심볼명 근접) 여부 — 추천: best-effort 산문으로만, 기계 보장 주장 금지.
- **OQ-d:** 릴리스 서명 강도 — M5.

## 10. 상태
- **리뷰 대기(rev10). 구현 승인 전 금지.**
- **rev10 결정(spine 채택):** N8 뒤집힘 → **N11 맵 중추 문서(§3.8).** 올바른-프레임 패널로 buildable 확인. **선결 4 blocker**(A 커밋강제=중간안 확정 / B locator 헤딩줄·유일성 / C 사람-라벨 인덱스 / D gate루트 .md ENTRY_FILENAMES). contract 모듈 먼저, 인라인→맵 마이그레이션=MESSY 파이프라인.
- **F11–F15 disposition됨([ADR 0012](../decisions/0012-self-growth-open-issues.md), 2026-07-06):** F12(룰#4 co-change 死)=doc-reconcile 판정에 룰#4 트리거(클러스터→폴더 승격 비블로킹 제안) **구축**. F11(동결 예외=마커)·F13(UPDATE 심볼앵커)·F14(docsherpa_frozen 브랜드 금지)·F15(refresh clean-tree 커밋)=미구축 기능(N4·N9·refresh)의 제약으로 **결정·기록**(실사용 시 그 제약대로 구축).
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
### rev9 자가감사 — "문서링크=주석" 오개념이 드러낸 추가 구멍 (F9~F15, 미해결)
계기: 진행자가 문서 링크를 HTML 주석으로 오인해온 게 드러나, gate.py를 **실측**(얇은 CLAUDE.md → 일반 마크다운 링크 → 별도 맵 문서, AGENTS.md 없이 `orphan=0 PASS`)하며 계획 전반 재감사.
- **[근거 거짓] F9 — 맵 추출 기각:** "맵 externalize → gate BFS 붕괴"는 **주석-포인터 strawman에만 참.** 일반 마크다운 링크면 gate가 재귀적으로 따라가 통과(실측). 이 전제가 계획 10곳에 전파, N8이 부분적으로 이 근거로 rev5를 supersede → **N8 재오픈.** 인라인 결정은 다른 근거(구현표면·파일수·브랜드 누출)로 **재도출 필요.** rev4-5의 맵은 전용도구+커스텀포맷+주석포인터 **묶음**으로 왔고, rev6이 통째로 버리며 경량 마크다운 중추(정상 링크)까지 함께 버림 — 그 형태는 독립 평가된 적 없음.
- **[범위 모순] F10 — gate 루트:** `gate.py:77`이 AGENTS.md·CLAUDE.md만 루트. 그러나 setup-docs가 GEMINI.md 등 "같은 패턴" 지원 주장(`setup-docs/SKILL.md:143`) → GEMINI-only repo는 진입점 못 찾아 전 문서 orphan. **주장 지원범위 > 기계 실지원.**
- **[과장] F11 — 규칙 불변·동결 충돌:** "doc-reconcile은 규칙 절대 안 바꾼다"는 **산문 규율뿐**(두 마커 동일 파일, 기계강제 0). + N9 동결 휴리스틱("첫 `##` 이후 본문")이 doc-reconcile이 반드시 append하는 index 섹션과 겹침 — "인덱스 예외"가 `docsherpa:index` 마커 기준(안전)인지 헤딩 기준(취약)인지 **미명시.**
- **[자가성장 구멍] F12 — 룰#4 死:** 라우팅 룰#4(co-change ≥2 → 폴더 승격)는 first-match+단건 CREATE에선 영영 안 걸림. 규칙drift 신고는 "없는 규칙 추가"용이지 "기존 평면문서 묶기"(룰#4) 트리거가 아님 → **콘텐츠가 평면으로만 자라고 절대 안 뭉침.**
- **[일관성] F14 — 브랜드 누출:** N9의 `docsherpa_frozen` frontmatter = 사용자 문서에 우리 브랜드 키 주입 → **ADR 0010**(docsherpa-* 스킬명 거부)과 모순.
- **[posture] F15 — 자동 커밋:** refresh §3.2 step6이 사용자 git 히스토리에 무프롬프트 커밋 → "보조 not 주인"과 긴장(clean tree 조건이 막긴 함).
- **[명확화] F13 — grep 앵커:** UPDATE는 값이 아니라 **심볼 앵커**로 grep해야 작동("3" grep 무의미, "MAX_RETRY" 유효) — 미명시.
- **관통 패턴:** ①기계 주장 vs 실제 산문/휴리스틱 ②주장 지원범위 > 실지원 ③브랜드·주인 vs 보조 정체성.
### rev10 — 맵 중추 문서(N11) 채택 + 올바른-프레임 재검증
**교훈(먼저):** rev9까지의 검증이 "inline으로 수렴"한 건 부분적으로 **프레이밍 편향**이었다 — "inline→spine 변경안을 적대적으로 검증하라"는 틀이 구조적으로 현상유지(inline)를 방어하게 만들었다(변경 비용만 세고 inline 자체 비용은 안 셈). 사용자가 이를 지적, 방향을 spine으로 확정하고 **프레임을 뒤집어**(방향 확정·설계만 공격) 재검증.
- **패널 수렴(codex+architect):** spine은 **buildable**, 방향 부정 0. 선결 **4 blocker** 도출 → §3.8 N11에 반영. 전부 spine 유지하며 해결 가능.
  - **A(identity):** 인라인은 중추가 gate 시드라 구조적 도달보장 / 맵은 링크 하나 뒤 → 도달성이 "구조보증→규율"로 강등 위험. **확정 중간안:** 강제훅 X · sidecar에 home 기록해 자가치유 실작동 · opt-in 훅 · 정직 라벨(조용한 유실 아님, gate가 잡음).
  - **B:** 순진 마커탐색이 이 레포 `DESIGN.md`·`0008`을 false-home으로 잡음 → 헤딩줄 마커만·펜스제거·유일성.
  - **C:** relpath가 oracle FAIL → 인덱스 링크를 사람-라벨 텍스트로(normalize가 URL제거→key 불변).
  - **D:** gate 루트=ENTRY_FILENAMES의 .md만, 비-md 미지원 명시.
- **architect 기각(과설계 방지):** ordering 데드락 없음(BFS home-무관) · 브랜드 누출은 감소지 regression 아님(footprint↓). → 부트스트랩·누출 기계 만들지 마라.
- **미해결(이월):** F11(동결 예외 마커기준으로 §3.8이 답 강제)·F12(룰#4 死)·F13·F14·F15는 N11과 독립, 순차 처리. **N11 구현은 4 blocker 선결 후 승인.**
- **F16(신규·저작 함정):** gate.py의 `LINK_RE`는 **삼중 펜스만** 벗기고 **인라인 백틱(`` `…` ``) 속 `](경로)`는 실링크로 오인**한다. 그래서 문서에 링크 문법을 *예시로* 쓰면 broken link로 잡힌다(이 계획서에서 2회 재현: NNNN·decisions/README). 저작 시 링크 문법을 서술로 풀거나, **gate에 인라인-코드 스트립 추가**를 검토(별개 개선). 이 계획서 예시는 전부 서술로 우회함.
