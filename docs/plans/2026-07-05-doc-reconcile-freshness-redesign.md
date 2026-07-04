# doc-reconcile 최신화·이식 재설계 (Implementation Plan) — rev3

> **For agentic workers:** REQUIRED SUB-SKILL: 승인 후 superpowers:subagent-driven-development 또는 superpowers:executing-plans로 task 단위 구현. 이 문서는 **리뷰용 설계 문서**다 — 승인 전에는 구현 금지. 승인 후 각 Task를 bite-sized TDD 스텝으로 확장한다.

**Goal:** doc-reconcile을 "특화 사본" 모델에서 "범용 임베드 + 버전-단조 최신화 + 마커-없으면-복구안내"로 바꿔, 팀 공유(P1)·최신화(P2)·아키텍처 의존 완화(P3)를 동시에 만족시킨다.

**Architecture:** 임베드 사본에서 **앵커 특화를 폐기**하고(범용 척추만 커밋), 갱신 판정은 **설치-시점 sidecar `{version, hash}`** 로 로컬 완결한다(과거-버전 매니페스트 불필요). 프라임은 **명시적 플러그인-우선/임베드-fallback**. 자동 실행된 최신 플러그인 스킬이 **플러그인-provenance 검증 → up-only → hash-clean → 원자적 쓰기** 게이트로 낡은 임베드를 **무프롬프트로** 끌어올린다. 마커 부재 시 스킬은 **문서를 신설하지 않고 "마커 복구 제안 후 STOP"** 한다.

**완전 자율주행 (핵심 UX 요구):** 사용자의 수동 행위는 **①플러그인 설치 ②`/docsherpa:setup-docs` 적용** 둘뿐. 그 이후 refresh·문서 갱신은 **전부 무프롬프트 자동**. "갱신할까요?"류 블로킹 프롬프트는 제거한다.

**⚠️ 안전은 사람 리뷰가 아니라 기계에 얹는다 (rev3 핵심 교정 — N6):** 자율주행은 사용자의 주의를 없애므로 "git 커밋 리뷰가 안전망"은 **자기모순**이다(자율주행이 그 주의를 제거한다). 따라서 안전을 **사람 리뷰에서 기계 불변식으로 이전**한다: ①툴링 변경은 **별도 자동 커밋**으로 분리(사용자 작업에 안 섞임) ②doc 편집 무손실을 **content_oracle류 세그먼트-소실-0 체크로 기계 강제**(anti-hallucination 산문만으로 부족) ③오염 방어 **릴리스 provenance를 refresh와 동시 착지**(M5 이연 취소) ④자동 트리거 **시점 정의** ⑤stuck-stale **가시화**. git 리뷰는 최후 보조지 주 방어선이 아니다.

**Tech Stack:** Python 3 (stdlib only: `json`, `hashlib`, `pathlib`, `shutil`, `os`), pytest (`uv run --with pytest`), Markdown 산문 스킬.

**검증 이력:** rev1 = `/codex` consult. rev2 = `/codex` challenge + `architect` 교차검증(§13). **rev3 = 자율주행 전환(N5) 후 자가 비판 리뷰** — N5가 안전을 사람 git-리뷰에 얹은 모순(C1)·doc편집 무보증(C2)·provenance 이연(C4)을 발견, **N6로 안전을 기계에 재배치**(§13 rev3).

## Global Constraints

- **North Star (불가침):** 비파괴 · 사용자 내용/편집 소실 0. **모든 분기**(hash-mismatch, no-sidecar, 최초설치, 동시 refresh, 파싱 실패)는 **fail-safe = write 스킵**으로 수렴해야 한다.
- **완전 자율주행 (하드 UX 요구):** 설치·적용 이후 **무프롬프트**. refresh·문서 갱신은 사용자 승인 없이 자동.
- **안전 = 기계 (N6, 하드):** 자율주행이 사람 주의를 없애므로 안전은 git 리뷰가 아니라 **기계 불변식**에 얹는다 — 세그먼트-소실-0 체크·hash-clean·provenance·별도 툴링 커밋·릴리스 서명. git 리뷰는 보조.
- **R4 (재정의 — 조용한 *손실* 금지, 조용한 *갱신*은 허용):** 임베드 덮어쓰기는 **hash-clean(사용자 편집 없음이 증명된) 파일에 한해 자동** 허용. **hash-dirty(hand-edit) 파일은 절대 덮지 않는다.** 즉 R4의 보호 대상은 "사용자 편집"이지 "자동 갱신 자체"가 아니다. 모든 자동 변경은 git에 노출되어 리뷰 가능해야 한다.
- **정본 리터럴 0:** 플러그인 `skills/doc-reconcile/SKILL.md`는 프로젝트 리터럴 금지. 가드 `test_doc_reconcile_portable.py`가 계속 통과해야 한다(단 §7 T3대로 앵커-존재 assert는 제거/교체).
- **바이트 정규화:** 모든 hash는 **단일 정규화 함수**(utf-8-sig 디코드 → CRLF→LF → 스탬프 1줄 제거 → 트레일링 LF 1개)를 거친 바이트로 계산. sidecar 생성과 검증이 **대칭**이어야 false-dirty를 막는다.
- **stdlib only.** 테스트: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`. 커밋마다 push(origin/main).

---

## 1. 문제 · 배경

현재 doc-reconcile은 두 벌: **정본(플러그인, 범용, 항상 최신)** + **사본(임베드, §7.5로 repo 특화, scaffold 시점 동결)**. 세 하드 제약이 충돌한다:

- **P1 (임베드 불가침):** 루프는 target repo에 커밋돼야 한다(플러그인 미설치 Bob도 자동 상속 — 팀 가치). 못 버림.
- **P2 (최신화):** 플러그인 척추 개선 시 여러 repo에 흩어진 임베드가 stale. 자동 cross-repo push 불가(각 repo 독립 git). 특화 앵커 보존 병합이 복잡 + R4 충돌.
- **P3 (아키텍처 의존 완화):** AGENTS.md 마커가 없거나 바뀌면 스킬이 거의 헛돎.

**핵심 통찰:** "임베드(P1)"와 "특화(앵커 굽기)"는 별개 축. **P2 복잡성은 전부 특화 앵커 보존에서 온다.** 실측상 특화 앵커의 고유 가치는 marginal(docsherpa 앵커 3줄 중 2.5줄이 범용 앵커 + AGENTS.md로 도달; 나머지 1줄 관례는 AGENTS.md에 이관 가능). 앵커는 "바닥이지 천장 아님"이라 에이전트가 diff로 대상을 매번 재도출한다. **특화를 폐기하면 P2가 붕괴적으로 단순해진다.**

## 2. 결정 (근거 + supersede)

| # | 결정 | 근거 | supersede/narrow |
|---|---|---|---|
| **N1** | **앵커 특화 폐기.** 임베드 = 범용 척추. repo 고유 관례는 AGENTS.md로 이관. | 특화 가치 marginal, P2 복잡성 제거. | **D4 supersede**, §6·§7.5 앵커 특화 삭제 |
| **N2** | **프라임 = 명시적 플러그인 우선, 임베드 fallback.** "또는" 동등표현 → "플러그인 있으면 반드시 `/docsherpa:doc-reconcile`, 없을 때만 `.claude/skills/...`". | 특화 없으니 임베드는 옛 범용판. 최신 플러그인이 항상 우위. "또는"은 LLM이 stale 임베드를 고를 여지(challenge #2·#8). | 이전 "임베드 우선" 권고 철회 |
| **N3** | **sidecar 기반 up-only 최신화 (무프롬프트).** 설치 시 `{version, hash}` sidecar 기록. 자동 실행 플러그인 스킬이 `provenance-verified AND 내 버전 > 임베드 버전 AND hash==sidecar.hash`일 때 **승인 없이** 원자적 덮어쓰기. | 로컬 완결(과거-버전 매니페스트 운영 리스크·KeyError·부트스트랩 버그 클래스 소멸 — challenge #5, arch #2). up-only가 downgrade 차단. 승인은 codex#3 근거로 보안 실익 없어 제거. | **R4 narrow**(hash-clean 자동, hand-edit 보호로 재정의) |
| **N4** | **마커 부재 = 문서 신설 금지, "마커 복구 제안 후 STOP".** fallback 스캔 폐기. | fallback이 taxonomy를 spine에 재복제(스킬이 금지한 안티패턴) + 신설 문서 index 집 부재 → orphan/AGENTS.md 날조 위험(challenge #8, arch #6). 마커 없는 repo = setup-docs 미실행 repo → 복구가 정답. | P3를 "복구 안내"로 축소 |
| **N5** | **완전 자율주행: doc-reconcile 편집도 무프롬프트.** "갱신할까요?" 블로킹 제거 → 자동 편집 후 **사후 요약만** 출력. | 설치·적용 후 무개입이 하드 UX 요구. | doc-reconcile 출력형태(SKILL "먼저 읽어라") 개정 |
| **N6** | **안전을 사람 리뷰 → 기계로 이전 (rev3).** ①툴링 변경 별도 자동 커밋 ②doc편집 세그먼트-소실-0 기계 체크 ③릴리스 provenance를 refresh와 동시 착지 ④자동 트리거 시점 정의 ⑤stuck-stale 가시화. | 자율주행은 사람 주의를 없애므로 "git 리뷰가 안전망"은 자기모순(C1). 무손실·오염방어를 기계 불변식으로 강제해야 성립. | OQ6 이연 취소, N5 안전 재구성 |

## 3. 메커니즘 (상세)

### 3.1 sidecar — 갱신 판정의 로컬 진실 (OQ1 해결: 매니페스트 → sidecar)

- 설치 시 임베드와 나란히 sidecar 기록: `.claude/skills/doc-reconcile/.docsherpa-loop.json` = `{"version": "0.0.1", "hash": "<canonical_hash(설치된 척추)>"}`.
- `canonical_hash(text)` = `sha256(정규화된 바이트)`. **정규화 함수(단일 정의):** utf-8-sig 디코드 → `\r\n`→`\n` → 스탬프 라인(`<!-- docsherpa-scaffold: v… -->`) 정확히 1줄 제거 → 트레일링 LF 1개 보장 → utf-8 인코드.
- **hash-clean 판정:** `canonical_hash(현재 임베드) == sidecar.hash` → 설치 이후 미수정(clean). 불일치 → hand-edit 또는 drift.
- **sidecar 부재/파싱 실패/버전 없음:** "검증 불가" → **write 스킵 + nudge**(fail-safe). 기존 특화 설치본(sidecar 없음)이 여기로 수렴해 **덮이지 않는다**(challenge #1, arch #9).
- **왜 매니페스트가 아니라 sidecar:** 매니페스트는 릴리스마다 재생성·과거버전 엔트리 관리가 필요하고, 누락 시 wild 전체가 동시에 false-dirty로 오진되며 "안 건드린 파일이 수정됐다"고 거짓 통보(두 critic이 지목한 **가장 위험한 구멍**). sidecar는 설치 시점 자기 hash를 로컬 보관 → 그 버그 클래스 전체가 소멸. 변조돼도 dirty로 읽혀 fail-safe라 안전성 동일.

### 3.2 up-only 최신화 — 체크 순서 (fail-safe로 수렴)

플러그인 doc-reconcile 실행 중 self-update 스텝이 `refresh_loop`(§3.4)를 호출:

```
0. provenance 검증: 실행 컨텍스트가 진짜 플러그인 install 경로인가?
     (플러그인 root가 target repo 밖 + .claude-plugin/plugin.json의 name==docsherpa
      + 정본 SKILL.md 경로 실재)  아니면 → STOP, 쓰기 경로 없음, 사용자에게 언급도 안 함.
1. 임베드 파일 존재 + sidecar 로드
     (임베드 없음 → 최초설치는 setup-docs 소관, 스텝 종료 / sidecar 없거나 파싱실패 → STOP+nudge)
2. version_gt(플러그인 버전 V_p, sidecar.version V_e) ?
     No  → STOP. 임베드 안 건드림. (Jack V2 vs V3: 여기서 멈춤, downgrade 차단)
     Yes → 3
3. canonical_hash(임베드) == sidecar.hash ?   (hand-edit/ drift 검사)
     No  → 덮지 말고 skip + "검증 불가(편집됐거나 개행 drift) — 자동갱신 보류" 로그. (오인 낙인 회피, hand-edit 보존)
     Yes → 4
4. 릴리스 provenance 검증(N6-③): 정본 SKILL.md가 **서명/체크섬 매니페스트와 일치**하는가?
     불일치 → STOP+경고(오염 의심). OK → 5. (이게 오염 플러그인의 주 방어선 — 사람 승인 아님)
5. 쓰기 직전 재검증(concurrency): git 인덱스에 unmerged 없음 + `git diff -- <임베드 경로>` 비어있음.
     아니면 → STOP+로그. OK → temp 파일 작성 후 atomic rename으로 임베드 교체 + sidecar 갱신.
6. **별도 툴링 커밋(N6-①):** 그 두 파일만 stage(add -A 아님) 후 **독립 커밋** 생성
     (예: `chore(docsherpa): auto-refresh doc-reconcile vV_e→vV_p`). **사용자 작업 커밋에 섞지 않는다.**
     사후 요약 로그(블로킹 아님).
```

- **완전 자율(N5):** step4~6은 승인 없이 자동 실행. hash-clean(step3)이 내용 소실 0을 보증.
- **C1 해소(N6-①):** 툴링 변경을 **자기 커밋으로 분리** → Alice의 hotfix 커밋에 안 쓸려 들어감. 사람이 매 커밋 정독 안 해도 추적 가능(git log에 명확).
- **North Star:** hand-edit은 step3에서 걸려 절대 안 덮음. 모든 실패 분기가 write-skip.
- **downgrade 차단:** step2 short-circuit(Jack은 V3 hash 조회 불필요).
- **provenance(step0):** dogfood repo(docsherpa 자신)엔 `scaffold.py`가 repo 안에 실재 → "스크립트 있으면 실행"은 fail-open(arch #7). plugin.json name + 경로 검증으로 배제.
- **오염 플러그인 방어(step4, C4/N6-③):** 자동 refresh라 사람 승인이 방어선이 될 수 없음(승인은 보안 리뷰 아님 — challenge #3). **릴리스 provenance(서명/체크섬)가 주 방어선이고, 이건 refresh와 동시 착지**(M5 이연 취소). git 리뷰는 최후 보조.

### 3.3 self-update 스텝의 거주지 · 이식성

- 스텝은 **척추 산문의 분리된 "플러그인 실행 시에만" 부록**에 둔다(본문에 섞지 않음). 실제 쓰기는 `refresh_loop`에 위임.
- **Alice(플러그인 有):** 자동 실행 = 플러그인 사본 → provenance 통과 → 작동.
- **Bob(플러그인 無):** 자동 실행 = 임베드 사본 → provenance 실패(플러그인 root 없음) → **STOP, 언급 안 함**. Bob은 커밋된 임베드 소비.
- **이식성:** 스텝은 플러그인-상대 경로만 참조(리터럴 0). provenance 실패 시 no-op → `test_doc_reconcile_portable.py` 통과.

### 3.4 scaffold.py 변경 (핵심 코드) — R4 위반 봉쇄(arch #1)

- **`install_loop_files`는 `not exists` 게이트 유지(현행).** `scaffold()`(setup-docs 재실행)가 승인 없이 덮는 R4 위반을 원천 차단. 단 sidecar 기록은 최초설치에 추가.
- **신규 `refresh_loop(repo_root, plugin_root_dir) -> dict`:** §3.2 게이트(provenance·up-only·hash-clean·릴리스서명·재검증·atomic)를 **전부 기계 검증으로** 구현하고 통과 시 **승인 없이 자동 쓰기 + 별도 툴링 커밋**(N6-①). 반환 dict에 `action`(committed/skipped-dirty/skipped-uptodate/skipped-no-provenance/skipped-bad-signature) 기록. `skipped-dirty`는 **stuck-stale 신호로 상위(프라임/다이제스트)에 노출**(N6-⑤). `scaffold()`는 이걸 호출하지 않는다(자동 스텝만 호출).
- **신규 헬퍼:** `parse_stamp`, `strip_stamp`, `normalize(text)->bytes`, `canonical_hash`, `version_gt` (strict `tuple(int(x) for x in v.split("."))`, 파싱 실패 시 fail-closed=False), `load_sidecar`, `write_sidecar`, `verify_plugin_provenance`.
- **모든 조회 `.get()` 가드 + 파일 부재 no-op** — KeyError/FileNotFound로 인한 부분 설치 크래시 방지(arch #2).

### 3.5 graceful degrade (P3) — fallback 스캔 폐기(N4)

- **마커 있으면:** 현행대로 AGENTS.md 마커로 판정(권위).
- **마커 없으면:** **문서 신설·라우팅 결정 금지.** "이 repo는 docsherpa 마커가 없음 → `/docsherpa:setup-docs`로 구조 설치를 제안" + (선택) 읽기전용 stale 인벤토리만. **새 문서·index 변경은 사용자가 setup-docs로 opt-in할 때만.**
- 근거: fallback 스캔은 taxonomy를 spine에 재복제(single-source 위반) + 신설 문서의 도달성 집이 없어 orphan/날조 유발. 마커 없는 repo는 setup 미실행 repo이므로 복구 안내가 정답.

### 3.6 doc-reconcile 출력형태 개정 — 무프롬프트 자동 (N5)

현 doc-reconcile SKILL.md의 "출력 형태(먼저 읽어라)"는 **"요약 제안 → 사용자 승인 → 편집"** 이다. N5로 이를 **무프롬프트 자동**으로 바꾼다:

- **판정 → 편집 → 스테이징을 승인 없이 자동 수행.** 블로킹 "갱신할까요?" 제거.
- **사후 요약만 출력:** "갱신 N곳·신설 M건 완료. git diff로 확인." (정보 제공, 블로킹 아님)
- **트리거 시점 정의(C3/N6-④):** SessionStart 프라임은 "**직전 세션의 미반영 변경**"만 대상(현재 세션 코드가 반쯤 바뀐 상태를 문서화하지 않음). 현재 세션 변경의 반영은 **에이전트가 그 변경을 완료(커밋 직전)로 판단한 시점**에만. pre-commit 훅은 도입 안 함(D9 유지) — 트리거는 SessionStart(과거분) + 에이전트의 커밋-직전 판단.
- **무손실 기계 강제(C2/N6-②):** 자동 doc 편집은 **추가(additive) 우선**. 기존 사용자 산문의 **삭제·대체가 포함된 편집은 content_oracle류 "세그먼트-소실-0" 체크를 통과할 때만** 적용(편집 전 세그먼트가 편집 후에도 전부 매핑되는지 기계 검증). 통과 못 하면 그 편집은 보류 + stuck 신호. anti-hallucination 산문은 하한선일 뿐, **무손실은 기계가 보증**한다.
- **안전 불변식 유지:** §4 anti-hallucination + "손대지 말 것"(역사 동결 문서·pre-existing 버그) 그대로. 자동이라고 스코프가 넓어지지 않는다.
- **척추 전파 인지(C6):** 이 무프롬프트 출력형태는 척추에 있으므로 **Bob의 임베드 사본에도 담긴다** → Bob 에이전트도 무프롬프트 자동편집. 의도된 팀 일관성이나, 세그먼트-소실-0 체크가 Bob 쪽에서도 무손실을 보증해야 안전(N6-②가 Bob에도 적용됨).

## 4. 시나리오 검증 (step으로)

**S1 정상 최신화(무프롬프트, 별도 커밋):** 임베드 V1(clean). Alice(V3) → step0 provenance → step2 V3>V1 → step3 hash 일치 → step4 릴리스서명 OK → step5 재검증·atomic write → step6 **별도 툴링 커밋**(승인 없이) → Bob pull로 V3. Alice의 hotfix 커밋과 안 섞임. ✓
**S2 downgrade 차단:** 임베드 V3. Jack(V2) → step2 V2>V3 거짓 → STOP. ✓
**S3 수동편집 보존:** 임베드 hand-edit → step3 hash 불일치 → skip + diff, "검증 불가" 표기. 소실 0. ✓
**S4 기존 특화/무-sidecar 설치본:** sidecar 없음 → step1 STOP+nudge. **덮지 않음**(North Star). Task3이 이 repo 임베드를 범용화+sidecar 부여로 정상화. ✓
**S5 바이트 drift(CRLF):** Windows 체크아웃 임베드가 CRLF → 정규화 함수가 LF로 통일 후 hash → sidecar와 일치 → clean 유지(false-dirty 아님). ✓
**S6 매니페스트 크래시 부재:** 과거-버전 조회 자체가 없음(sidecar 로컬) → KeyError·부분설치 소멸. ✓
**S7 dogfood provenance:** docsherpa 자기 repo에서 임베드 실행 → step0에서 플러그인 root가 target 안이라 provenance 실패 → STOP(자기수정 안 함). ✓
**S8 동시 refresh:** 판정~쓰기 사이 파일 변경 → step5 재검증에서 `git diff` 비어있지 않음 감지 → STOP. ✓
**S9 마커 없는 repo:** fallback 신설 없이 "마커 복구(setup-docs) 제안"만. 환각 문서 0. ✓
**S10 프라임 우선순위:** 프라임이 "플러그인 있으면 반드시…"로 명시 → Alice가 stale 임베드 오선택 안 함. ✓
**S11 자동변경 격리(C1):** Alice가 hotfix + `git commit -am` → refresh는 이미 **별도 툴링 커밋**으로 착지했고, doc 편집은 별도 스테이징이라 hotfix 커밋에 섞이지 않음. 사람이 정독 안 해도 툴링 변경이 git log에 분리 추적. ✓
**S12 doc 무손실(C2):** 자동편집이 기존 산문 절을 지우려 함 → 세그먼트-소실-0 체크 실패 → 그 편집 보류 + stuck 신호. 승인 없이도 **내용 소실 0 기계 보증**. ✓
**S13 stuck-stale 가시화(C7):** 임베드가 hash-dirty로 굳음 → `skipped-dirty`가 조용한 로그가 아니라 **프라임/다이제스트에 "임베드 고착, 확인 요망" 노출** → 사람이 인지. ✓
**S14 오염 플러그인(C4):** 악성 정본 + 일치 hash → step4 릴리스서명 검증 실패 → STOP. 사람 승인이 아니라 **서명이 방어**(refresh와 동시 착지). ✓

## 5. P3 경계 (fallback 폐기 후)

- **마커 존재:** 마커가 유일 권위.
- **마커 부재:** 읽기전용 인벤토리 + setup-docs 복구 제안. **신설/라우팅/인덱스 변경 금지.**
- 결과: spine에 taxonomy 복제 없음(single-source 유지) → arch #6·challenge #8 소멸.

## 6. 근본 트레이드오프

> **P1+P2+P3를 동시에 만족하려면 "단일하고 우아한 판단 소스"를 포기하고 2계층(sidecar 폐기 후) — 커밋된 범용 방법론(척추) + repo 소유 로컬 지식(AGENTS.md) — 을 받아들여야 한다.** fallback을 폐기해 3계층에서 2계층으로 줄였다(rev1 대비 단순화).

부수 트레이드오프: 특화 폐기 → repo 고유 리마인더를 AGENTS.md로 이관(1회 소량). sidecar → 파일 1개 추가(매니페스트 운영 리스크와 맞바꿈, 유리한 교환). **완전 자율주행(N5) → 안전을 사람 리뷰가 아니라 기계에 얹음(N6): 세그먼트-소실-0 체크·별도 툴링 커밋·릴리스 서명. 대가 = 구현 복잡도↑(오라클류 체크·서명 인프라)이지만, 이게 "자율주행인데 안전"의 유일한 성립 경로.** 승인 프롬프트는 codex#3 근거로 보안 실익 없어 제거.

## 7. 테스트 (behavioral, RED-first) — 정본 `skills/setup-docs/scripts/test_*.py`

- **T1 stale+clean → refresh(up):** V1 sidecar 임베드(정본 내용) + 서명 유효 + 플러그인 V2 → `refresh_loop`가 V2로 덮고 sidecar 갱신 + **별도 커밋** 생성.
- **T2 up-only:** V3 sidecar + 플러그인 V2 → **write 안 함**.
- **T3 hash-dirty 보존:** 내용 수정된 임베드 → **write 안 함**, "검증 불가" 신호.
- **T4 sidecar 부재 보존:** sidecar 없는(레거시) 임베드 → **write 안 함** + nudge.
- **T5 provenance:** target repo 안에 scaffold.py가 있어도(dogfood 모사) provenance 실패 시 no-op.
- **T6 정규화 대칭:** CRLF/ BOM/트레일링개행 변형 임베드가 `normalize` 후 sidecar와 일치(false-dirty 방지).
- **T7 version_gt:** `0.0.10 > 0.0.9` 참, `0.0.9 > 0.0.10` 거짓, 4-컴포넌트·suffix·malformed → fail-closed(False).
- **T8 R4 불변:** `install_loop_files`는 기존 임베드를 **절대 덮지 않음**(`not exists` 유지). `scaffold()` 재실행이 clean·stale 임베드를 조용히 덮지 않음.
- **T9 최초설치:** 임베드 없음 → 정본+스탬프+sidecar 설치.
- **T10 무프롬프트 자동:** 게이트 전부 통과(provenance·up-only·clean·서명·재검증) → `refresh_loop`가 **승인 인자 없이** 자동 write + sidecar 갱신 + `action="committed"` 반환.
- **T10b 자동편집 무프롬프트:** doc-reconcile 출력형태가 블로킹 승인 없이 편집·스테이징 후 사후 요약을 냄(산문 계약 — fixture로 "갱신할까요?" 문자열 부재 확인).
- **T11 이식성 유지 + 앵커 assert 교체:** `test_doc_reconcile_portable.py`의 `test_anchor_block_is_delimited_for_specialization`를 **삭제**(N1이 블록 제거)하고, 리터럴 0 assert는 유지·통과.
- **T12 마커 부재 = 신설 금지:** 마커 없는 fixture repo → 스킬이 문서 신설을 지시하지 **않고** setup-docs 복구를 제안(hollow 아닌 "복구 안내").
- **T13 프라임 우선순위:** 프라임 텍스트가 "플러그인 우선/임베드 fallback" 관계를 명시(단순 "또는" 아님).
- **T14 §9 parity 재베이스:** behavioral parity fixture를 **범용 판정** 기준으로 갱신(특화 앵커 제거로 인한 판정 변화 반영, arch #9).
- **T15 별도 툴링 커밋(C1/N6-①):** refresh 성공 시 임베드·sidecar가 **독립 커밋**으로 착지, 사용자 스테이징 인덱스에 섞이지 않음(add -A 미사용 확인).
- **T16 세그먼트-소실-0(C2/N6-②):** 기존 산문 절을 삭제하는 자동 편집 시나리오 → 소실 체크가 그 편집을 **보류**시키고 write 0. 추가-only 편집은 통과.
- **T17 릴리스 서명(C4/N6-③):** 정본 SKILL.md 변조(서명 불일치) → `refresh_loop` `skipped-bad-signature`, write 0.
- **T18 stuck-stale 노출(C7/N6-⑤):** hash-dirty 임베드 → refresh가 조용히 skip만 하지 않고 **가시 신호**(다이제스트/프라임 문자열)를 방출.

## 8. Task 개요 (승인 후 TDD로 확장)

1. **정규화·버전·sidecar 헬퍼:** `normalize`/`parse_stamp`/`strip_stamp`/`canonical_hash`/`version_gt`/`load_sidecar`/`write_sidecar` (T6·T7).
2. **provenance 검증:** `verify_plugin_provenance(plugin_root, repo_root)` (T5).
3. **install에 sidecar 부여 + R4 유지:** `install_loop_files`에 sidecar 기록 추가, `not exists` 게이트 불변 (T8·T9).
4. **`refresh_loop`(무프롬프트 + 별도 커밋, N6-①):** §3.2 게이트를 기계검증·원자쓰기·재검증까지 구현, 승인 없이 자동 write **후 독립 툴링 커밋** 생성 (T1·T2·T3·T4·T10·T15).
5. **릴리스 서명 검증(N6-③, C4):** `verify_release_signature(canonical, plugin_root)` — refresh step4에 편입. 서명/체크섬 매니페스트를 플러그인에 포함. **refresh와 동시 착지(M5 이연 안 함)** (T17).
6. **N1 특화 폐기:** 정본·이 repo 임베드에서 §7.5 앵커 블록 제거, 범용 확정 + sidecar 부여. 앵커-assert 테스트 삭제 (T11).
7. **N4 P3:** 척추에서 fallback 스캔 삭제 → "마커 복구 제안 후 STOP" (T12).
8. **N3 자동 스텝 + stuck-stale(N6-⑤):** 척추 부록 self-update(provenance 有→refresh_loop, 無→STOP). `skipped-dirty`를 가시 신호로 노출 (T5·T18).
9. **N5 doc-reconcile 무프롬프트 + 무손실(N6-②):** 출력형태를 "자동 편집→사후 요약"으로 개정 + **세그먼트-소실-0 체크**(content_oracle 재활용)로 삭제·대체 편집 기계 가드 + **트리거 시점 정의**(SessionStart=과거분/커밋직전=현재분) (T10b·T16).
10. **N2 프라임:** 프라임 우선순위 문구(플러그인 우선/임베드 fallback) (T13).
11. **ADR + 도달성:** D4 supersede + R4 재정의 + N5·N6 자율주행/기계안전 ADR 신설 + `decisions/README.md` 로그 + DESIGN.md §9 parity 재베이스 + 이 계획 문서 인덱스 등록 (T14).

## 9. 열린 질문 (OQ)

- **OQ1 (해결):** 매니페스트 → **sidecar** 확정(challenge/arch 합의, §3.1).
- **OQ2 (해결):** self-update = doc-reconcile 스텝이 `refresh_loop` 호출. **무프롬프트 자동** — 안전은 provenance + hash-clean + 릴리스 서명 + 별도 커밋(N6), git 리뷰는 보조.
- **OQ3 (해결):** 특화 관례는 **전부 AGENTS.md** 이관(임베드 anchors 잔존 없음).
- **OQ4 (해결):** `version_gt`는 **int-튜플 비교 + fail-closed** 필수(T7).
- **OQ5 (신규, 리뷰어 판단):** 마커 부재 시 "읽기전용 stale 인벤토리"를 제공할지, 순수 "복구 제안 후 STOP"만 할지. 추천: **인벤토리는 읽기전용 한정**(쓰기 0이면 무해).
- **OQ6 (해결 방향, C4):** 릴리스 provenance는 **자동 refresh의 주 방어선**이므로 M5 이연 취소 — **refresh와 동시 착지**(Task5). 강도(서명 vs 체크섬)는 구현 시 결정하되, 최소 "정본 변조 감지 체크섬"은 필수. 미결: 서명 키 관리 범위.
- **OQ7 (신규, 리뷰어 판단):** 세그먼트-소실-0 체크에 content_oracle을 그대로 재활용할지, 경량 버전을 새로 둘지. 추천: **재활용**(이미 검증된 무손실 오라클, 마이그레이션과 동일 불변식).

## 10. 이 문서의 상태

- **리뷰 대기(rev3).** 승인 전 구현 금지. 승인 시 Task를 bite-sized TDD로 확장 + 이 문서를 인덱스에 등록(도달성 불변식).
- 검증: `/codex` consult(rev1) + `/codex` challenge + `architect`(rev2) + 자가 비판 리뷰(rev3). 다음: 사용자 리뷰.

## 13. 검증 기록

### rev2 — `/codex` challenge + `architect` 병렬 교차검증
강하게 수렴. 반영한 P1/P2 (아래 일부는 rev3에서 재조정 — §rev3 참조):

- **매니페스트 → sidecar (가장 위험한 구멍):** 두 critic 공통 — 매니페스트 단일 오라클이 릴리스 실수·개행 drift 시 wild 전체를 false-dirty로 오진하며 거짓 통보. sidecar로 로컬 완결. (N3·§3.1)
- **R4 정면 위반(arch #1):** `install_loop_files` 게이트 변경이 승인 없는 `scaffold()` 재실행 경로를 조용히 덮게 함. → `not exists` 유지 + 별도 `refresh_loop(approved)`. (§3.4)
- **바이트 drift false-dirty(둘 다):** 단일 정규화 함수로 대칭 보장. (§3.1)
- **version_gt 함정(둘 다):** int-튜플 + fail-closed. (T7)
- **self-update fail-open / dogfood(arch #7, challenge #7):** provenance 검증(plugin.json + 경로). (§3.2 step0)
- **fallback 스캔 폐기(challenge #8, arch #6):** taxonomy 재복제·orphan·환각 게이트 제거. (N4)
- **레거시 특화 임베드 영구 dirty(challenge #1, arch #9):** sidecar 부재 = write-skip으로 안전 수렴 + 이 repo는 Task5에서 범용화. §9 parity 재베이스(T14).
- **프라임 rot / 비결정 선택(challenge #2, arch #8):** 명시적 우선순위 문구. (N2·T13)
- **승인 ≠ 보안 경계(challenge #3):** full diff + 도구-업데이트 승인 분리 + 릴리스 provenance(OQ6). (§3.2 step4)
- **동시 refresh race(challenge #10):** 쓰기 직전 재검증 + atomic rename. (§3.2 step4)

### rev3 — 사용자 결정(완전 자율주행) + 자가 비판 리뷰

**사용자 결정:** "설치·적용 후 무개입"이 하드 UX 요구 → **N5**: refresh·doc 편집 모두 **무프롬프트 자동**. 승인 프롬프트 제거(codex#3: 승인은 보안 경계가 아님).

**자가 비판 리뷰가 N5의 미검증 구멍 발견 → N6로 봉쇄:**
- **C1 [P1] 안전 스토리 자기모순:** "git 커밋 리뷰가 안전망"인데 자율주행이 그 주의를 없앰. → **툴링 변경 별도 자동 커밋**(사용자 커밋에 안 섞임). (N6-①·§3.2 step6)
- **C2 [P1] doc편집 무보증:** refresh는 hash-clean이지만 자동 doc 편집엔 기계 가드 0(North Star 유일 노출). → **세그먼트-소실-0 체크로 기계 강제**(content_oracle 재활용). (N6-②·§3.6)
- **C3 [P1] 트리거 시점 미정의:** SessionStart(너무 이름) vs "커밋 전"(트리거 없음). → **SessionStart=과거분/커밋직전=현재분** 정의. (N6-④·§3.6)
- **C4 [P1] provenance 순서 역전:** 오염 방어가 자동 refresh의 주 방어선인데 M5 이연. → **릴리스 서명을 refresh와 동시 착지**. (N6-③·§3.2 step4·Task5)
- **C5/C6/C7 [P2]:** 스테이징 미정의(→별도 커밋), 척추 전파로 Bob도 자동편집(→세그먼트체크가 Bob도 보증), stuck-stale 침묵(→가시화). (N6-⑤)

**핵심 교정:** 완전 자율주행은 사람 주의를 없애므로 **안전을 사람 리뷰 → 기계 불변식으로 이전**해야 성립. git 리뷰는 최후 보조. rev2의 "승인 분리/full diff"(승인 전제) 항목은 N5로 무효화되고 기계 방어로 대체됨.
