# doc-reconcile 최신화·유연화·자가성장 재설계 (Implementation Plan) — rev4

> **For agentic workers:** REQUIRED SUB-SKILL: 승인 후 superpowers:subagent-driven-development 또는 superpowers:executing-plans로 task 단위 구현. 이 문서는 **리뷰용 설계 문서**다 — 승인 전에는 구현 금지. 승인 후 각 Task를 bite-sized TDD 스텝으로 확장한다.

**Goal:** doc-reconcile을 "특화 사본·마커-필수·전-자율" 모델에서 **"범용 임베드 + sidecar 최신화 + 아키텍처 맵 기반 3능력(UPDATE/CREATE/MAP진화) + 위험별 계층 자율"** 로 바꿔, 팀 공유(P1)·최신화(P2)·아키텍처 유연성/자가성장(P3)을 동시에 만족시킨다.

**Architecture:** ①임베드 사본은 **범용 척추**만 커밋(앵커 특화 폐기). ②갱신 판정은 **설치-시점 sidecar `{version, hash}`** 로 로컬 완결. ③프로젝트 아키텍처는 **전용 "아키텍처 맵" 문서**에 기술하고 마커를 거기 심는다(진입 파일 AGENTS.md/CLAUDE.md는 얇게 유지, 맵을 링크). ④doc-reconcile은 세 능력 — **UPDATE**(기존 문서 수리, 구조 불요) · **CREATE**(새 문서 배치, 맵 필요) · **MAP진화**(맵 자체를 성장, 고위험) — 을 갖고, **위험별 계층 자율**로 실행한다. ⑤매 실행 끝에 **항상 요약**한다.

**계층 자율 (핵심 UX):** 사용자 수동 행위는 **①플러그인 설치 ②`/docsherpa:setup-docs` 적용** 둘뿐. 이후:
- **Tier 1 (루틴: UPDATE·CREATE·refresh) = 무프롬프트 완전 자율.** 잦고 저위험, 기계 가드로 안전.
- **Tier 2 (MAP진화 = 라우팅 룰 변경) = 경량 확인.** 드물고 고위험(미래 배치 전체에 영향·발견 지연)이라 변경 순간 확인. 드물어서 안 귀찮음.
- **실행 끝 요약 = 항상.** 무엇을 했는지 계층별로 보고(맵변경·refresh 강조, 루틴 간결, 무변경도 정직히).

**Tech Stack:** Python 3 (stdlib only: `json`·`hashlib`·`pathlib`·`shutil`·`os`), pytest(`uv run --with pytest`), Markdown 산문 스킬.

**검증 이력:** rev1 `/codex` consult → rev2 `/codex` challenge + `architect` 교차 → rev3 자가 비판(자율주행 안전을 기계로) → **rev4 사용자 설계 대화(아키텍처 맵 추출 + doc-reconcile 3능력/자가성장 + 계층 자율)**. §13.

## Global Constraints

- **North Star (불가침):** 비파괴 · 사용자 내용/편집 소실 0. 모든 실패 분기는 **fail-safe = write 스킵**.
- **얇은 진입 라우터:** AGENTS.md/CLAUDE.md는 라우팅 룰을 인라인으로 담지 않고 **아키텍처 맵을 링크만** 한다(N7).
- **안전 = 기계 (N6, 하드):** 자율 작업의 무손실·오염방어는 git 리뷰가 아니라 **기계 불변식**(세그먼트-소실-0·hash-clean·provenance·릴리스 서명·별도 커밋)이 강제. 고위험(MAP진화)만 사람 확인(N5 Tier2).
- **정본 리터럴 0:** 플러그인 `skills/doc-reconcile/SKILL.md`는 프로젝트 리터럴 금지(가드 `test_doc_reconcile_portable.py`). 맵의 project-특화는 **맵 문서(사용자 repo)**에만, 척추 메타룰은 generic.
- **바이트 정규화:** 모든 hash는 단일 정규화(utf-8-sig→CRLF→LF→스탬프 1줄 제거→트레일링 LF 1개) 후 계산. stdlib only. 커밋마다 push(origin/main).

---

## 1. 문제 · 배경

현재 doc-reconcile은 두 벌(정본/특화 사본)이고, 세 하드 제약이 충돌한다:
- **P1 (임베드 불가침):** 루프는 target repo에 커밋 — 플러그인 미설치 collaborator(Bob)도 자동 상속.
- **P2 (최신화):** 플러그인 척추 개선 시 흩어진 임베드가 stale. 자동 cross-repo push 불가.
- **P3 (아키텍처 유연성·자가성장):** doc-reconcile이 docsherpa 아키텍처에만 딱 맞아 유연성이 없고, 아키텍처 자체는 setup-docs가 1회 짓고 얼어붙어 "자가성장"이 콘텐츠에 그친다.

**핵심 통찰 (rev4):** doc-reconcile을 하나로 보면 P3가 안 풀린다. **세 능력으로 분해하면** 아키텍처 의존도가 완전히 다르다:
- **UPDATE** (코드 변경으로 낡은 **기존 문서** 수리 = grep→편집): **구조 불요, 어디서나 동작.**
- **CREATE** (새 문서 신설 + 배치 + 인덱스 등록): **라우팅 룰(맵) 필요** — 없으면 위치 환각/고아.
- **MAP진화** (새 범주 등장 시 라우팅 룰·폴더 승격·마커 신설로 **아키텍처 맵 자체 성장**): **고위험**(미래 전 문서 배치 영향).

rev3 N4("마커 없으면 STOP")는 이 셋을 한 덩어리로 취급해 UPDATE(어디서나 가능)까지 죽였다. 그리고 마커를 AGENTS.md에 인라인으로 흩뿌려 진입 라우터를 뚱뚱하게 했고, 맵 자체의 자가성장 경로가 없었다. rev4는 이 셋을 바로잡는다.

## 2. 결정 (근거 + supersede)

| # | 결정 | 근거 | supersede |
|---|---|---|---|
| **N1** | **앵커 특화 폐기.** 임베드 = 범용 척추. | 특화 가치 marginal, P2 복잡성 제거. | D4 supersede |
| **N2** | **프라임 = 플러그인 우선, 임베드 fallback (명시).** | 특화 없으니 임베드는 옛 범용판. 최신 플러그인이 우위. | 이전 "임베드 우선" 철회 |
| **N3** | **sidecar up-only 최신화 (무프롬프트).** 설치 시 `{version,hash}` 기록. `provenance AND 내버전>임베드 AND hash==sidecar AND 서명OK`면 승인 없이 원자적 쓰기 + 별도 커밋. | 로컬 완결, 매니페스트 운영 리스크 소멸. up-only가 downgrade 차단. | R4 재정의 |
| **N4** | **능력별 graceful degrade.** 맵 있으면 UPDATE+CREATE(+MAP진화). **맵 없으면 UPDATE만 + "맵 생성(setup-docs)" 제안**(STOP 아님). | UPDATE는 구조 불요라 어디서나 값어치. CREATE만 맵 필요. rev3의 all-or-nothing 교정. | rev3 N4(STOP) 수정 |
| **N5** | **위험별 계층 자율.** Tier1(UPDATE·CREATE·refresh)=무프롬프트. **Tier2(MAP진화)=경량 확인**(드물고 고위험). | 귀찮음은 빈도 탓 — 잦은 저위험은 자동, 드문 고위험만 게이트(안 귀찮음). | rev3 N5(전-자율) 정제 |
| **N6** | **안전을 기계로.** 세그먼트-소실-0 체크·별도 툴링 커밋·릴리스 서명(refresh와 동시)·stuck-stale 가시화. | 자율은 사람 주의를 없애므로 무손실·오염방어를 기계 불변식으로. | — |
| **N7** | **아키텍처 맵 문서 신설.** 라우팅 룰·인덱스·마커를 **전용 맵 문서**(예: `docs/_doc-map.md`)로 추출, 진입(AGENTS.md/CLAUDE.md)은 링크만. | 얇은 진입 라우터 원칙 준수 + 진입-불문 + 어떤 아키텍처든 맵에 기술 가능. | 마커 AGENTS.md 인라인 폐기 |
| **N8** | **doc-reconcile MAP진화 능력.** 새 범주 반복 등장 시 맵에 라우팅 룰 추가·폴더 승격·마커 신설. **setup-docs=맵 부트스트랩(1회 승인)·doc-reconcile=맵 진화.** | North Star #3(자가성장)이 아키텍처 레벨에서 성립하려면 맵 자체가 자라야 함. 맵도 문서라 doc-reconcile이 다룸. | 아키텍처 동결 해소 |
| **N9** | **실행 끝 항상 요약.** 자율이든 아니든, 변경 있든 없든 무엇을 했는지 계층별로 보고(맵변경·refresh 강조). | 무프롬프트라도 가시성 필수. | — |

## 3. 메커니즘

### 3.1 sidecar — 갱신 판정의 로컬 진실
- 설치 시 `.claude/skills/doc-reconcile/.docsherpa-loop.json` = `{"version","hash"}` 기록. `canonical_hash(text)` = `sha256(정규화 바이트)`(스탬프 라인 제외).
- **hash-clean** = `canonical_hash(현재 임베드)==sidecar.hash`. 불일치/부재/파싱실패 → **write 스킵 + stuck 신호**(fail-safe). 레거시 특화 설치본(sidecar 없음)도 여기로 안전 수렴.

### 3.2 up-only refresh — 체크 순서 (무프롬프트, Tier1)
```
0. provenance: 플러그인 root가 target 밖 + plugin.json name==docsherpa + 정본경로 실재. 아니면 STOP(무언급).
1. 임베드+sidecar 로드 (없음→setup-docs 소관 / 파싱실패→STOP+nudge)
2. version_gt(V_p, V_e)?  No→STOP(downgrade 차단, short-circuit) / Yes→3
3. canonical_hash(임베드)==sidecar.hash?  No→skip+"검증불가—stuck" 신호 / Yes→4
4. 릴리스 서명: 정본이 서명/체크섬과 일치? No→STOP(오염의심) / Yes→5   (오염 주방어선)
5. 재검증(concurrency): 인덱스 unmerged 0 + `git diff -- <임베드>` 빈값. 아니면 STOP. OK→temp+atomic rename.
6. 별도 툴링 커밋(그 두 파일만, add -A 아님): `chore(docsherpa): auto-refresh doc-reconcile vV_e→vV_p`.
```
- `version_gt` = `tuple(int(x) for x in v.split("."))`, 파싱실패 fail-closed=False. (0.0.10>0.0.9 정확)
- 별도 커밋(N6-①)으로 Alice의 작업 커밋에 안 섞임. 반환 `action`(committed/skipped-*).

### 3.3 self-update 스텝 거주 · 이식성
- 스텝은 척추의 **"플러그인 실행 시에만" 분리 부록**. 쓰기는 `refresh_loop` 위임.
- Alice(플러그인 有)→provenance 통과→작동. Bob(無)→provenance 실패→STOP·무언급. 이식성: provenance 실패 시 no-op → portable 가드 통과.

### 3.4 scaffold.py 변경
- **`install_loop_files`는 `not exists` 유지**(R4: `scaffold()` 재실행이 조용히 덮는 것 차단) + sidecar 기록 추가.
- **신규 `refresh_loop(repo_root, plugin_root)`**: §3.2 게이트 기계검증 + 자동 쓰기 + 별도 커밋. `scaffold()`는 호출 안 함.
- **신규 헬퍼:** `parse_stamp`·`strip_stamp`·`normalize`·`canonical_hash`·`version_gt`·`load/write_sidecar`·`verify_plugin_provenance`·`verify_release_signature`. 모든 조회 `.get()` 가드.
- **라우터 생성 변경(N7):** `write_router`가 진입 파일엔 **맵 링크**를, 라우팅/인덱스/마커는 **맵 문서**에 생성.

### 3.5 아키텍처 맵 문서 (N7)
- **맵 = 전용 문서**(예 `docs/_doc-map.md`): 라우팅 룰 + 인덱스 + 마커(`<!-- docsherpa:routing -->`·`<!-- docsherpa:index -->`)를 담는다. 진입 파일은 **한 줄 링크**로 연결(도달성).
- **진입 불문:** doc-reconcile은 마커를 **repo-wide grep**으로 찾으므로 맵이 어느 파일이든·진입이 AGENTS.md든 CLAUDE.md든 무관.
- **어떤 아키텍처든:** 맵은 setup 시 사용자 repo에 **핏하게** 생성 — docsherpa 권장 구조든, 사용자 고유 구조든 그 실제 레이아웃을 기술. doc-reconcile은 맵이 기술한 대로 따름.
- **부트스트랩 vs 진화:** 맵 **생성 = setup-docs(승인)**, 맵 **진화 = doc-reconcile(N8)**. 맵 없는 repo에 doc-reconcile이 맵을 무에서 강요하지 않음(보조 not 주인).

### 3.6 doc-reconcile 3능력 + graceful degrade (N4·N8)
```
맵(마커) 있음?
  아니오 → UPDATE만 수행(있는 문서 stale 수리, 구조 불요) + "맵 생성(setup-docs) 제안". CREATE·MAP진화 안 함.
  예     → UPDATE + CREATE(맵 룰대로 배치·인덱스 등록) + MAP진화(N8, 조건부)
```
- **UPDATE:** git diff→변경 리터럴 grep→기존 문서 수리. **세그먼트-소실-0 체크(N6-②)**로 삭제·대체 편집을 기계 가드(content_oracle 재활용). 동결문서(옛 ADR·CHANGELOG) 오편집 방지 위해 범용 "동결 패턴" 휴리스틱.
- **CREATE:** 맵 라우팅 룰로 "새 문서 필요? 어디에?" 판정 → 신설 → 인덱스 마커 섹션 등록(도달성 closeout, orphan=0).
- **MAP진화(N8):** 새 범주가 **명백히 반복**(예 ≥2회, 기존 룰에 안 맞음)될 때만 맵에 룰 추가/폴더 승격. **메타룰(언제 진화)=척추(generic)**, **프로젝트 룰=맵(per-repo)** → 순환·리터럴 누출 없음.

### 3.7 계층 자율 + 실행 끝 요약 (N5·N9)
- **Tier1 (UPDATE·CREATE·refresh):** 무프롬프트 자동. 안전=기계(세그먼트체크·도달성·hash/서명).
- **Tier2 (MAP진화):** **변경 직전 경량 확인**("아키텍처 맵에 'runbooks/' 룰 추가할까요?"). 드물어서 안 귀찮음. 확인 후 **별도 라벨 커밋**. (고위험=미래 배치 전체 영향·발견 지연 → 변경 순간에 사람 확인이 그 위험을 잡음.)
- **실행 끝 요약(N9, 항상·논블로킹):**
  ```
  [docsherpa] doc-reconcile 완료
    📝 갱신 N곳 · 🆕 신설 M건(인덱스 등록됨)
    ⚙️ 임베드 refresh vX→vY (별도 커밋)            ← 있었으면
    ⚠️ 아키텍처 맵 변경: 'runbooks/' 룰 추가        ← 굵게 강조
    → git diff로 확인
  ```
  변경 없으면 `Docs-Impact: none - <이유>` 정직히 보고.

## 4. 시나리오 (step)
- **S1 refresh(무프롬프트·별도커밋):** V1 clean+서명OK, 플러그인 V2 → step2~5 통과 → step6 별도 커밋 → Bob pull. Alice 커밋과 안 섞임. ✓
- **S2 downgrade 차단:** V3 임베드, Jack V2 → step2 거짓 STOP. ✓
- **S3 수동편집 보존:** hash-dirty → skip + stuck 신호. 소실 0. ✓
- **S4 레거시/무-sidecar:** sidecar 없음 → skip+nudge. Task로 이 repo 범용화. ✓
- **S5 UPDATE-only(맵 없음):** 마커 없는 repo → 낡은 상수 수리(UPDATE)만 + "맵 만들자" 제안. CREATE·MAP 안 함 → 환각 0. ✓ (P3 유연성)
- **S6 CREATE:** 맵 있음, 구조결정 발생 → 맵 룰대로 ADR 신설 + 인덱스 등록. ✓
- **S7 MAP진화(Tier2 확인):** 'runbooks/' 3회 등장, 기존 룰 없음 → **경량 확인** → 승인 시 맵에 룰 추가 + 별도 커밋 + 요약 ⚠️강조. ✓
- **S8 doc 무손실:** 자동편집이 기존 절 삭제 시도 → 세그먼트-소실-0 실패 → 그 편집 보류. ✓
- **S9 dogfood provenance:** docsherpa 자기 repo 임베드 실행 → step0 실패(플러그인 root=target 안) → STOP. ✓
- **S10 진입 불문:** CLAUDE.md만 쓰는 repo → 맵을 CLAUDE.md에서 링크, 마커 grep으로 찾음 → 정상. ✓
- **S11 끝 요약:** 무프롬프트로 갱신 3·신설 1·맵변경 1 했어도 끝에 요약, 맵변경 ⚠️강조. 무변경이면 "none" 보고. ✓

## 5. P3 재정리 (유연성 + 자가성장)
- **유연성:** doc-reconcile은 특정 레이아웃이 아니라 **"맵(마커+도달성)"에만** 의존. 맵이 어떤 구조를 기술하든 그대로 동작. 맵 없어도 UPDATE는 됨.
- **자가성장:** 맵도 문서라 doc-reconcile이 **진화**(N8) → 아키텍처가 setup 시점에 얼지 않고 코드/문서 성장을 따라 자람.
- single-source 유지: 프로젝트 taxonomy는 **맵 한 곳**, 척추엔 메타룰(generic)만. rev3 fallback의 taxonomy 복제 문제 없음.

## 6. 근본 트레이드오프
> **P1+P2+P3를 동시에 만족하려면 "단일하고 우아한 판단 소스"를 포기하고 계층 시스템 — 범용 척추(방법론·메타룰) + 아키텍처 맵(per-repo, 자가진화) + sidecar(로컬 최신화 진실) — 을 받아들여야 한다. 안전은 사람 리뷰가 아니라 기계 불변식에 얹고, 위험이 높은 맵진화만 사람 확인.**

대가: 구현 복잡도↑(3능력·계층자율·세그먼트체크·서명·맵 추출). 이득: 유연성(어떤 아키텍처든)·진짜 자가성장(맵 진화)·귀찮음 0(루틴 자동)·안전(기계+드문 확인).

## 7. 테스트 (behavioral, RED-first) — `skills/setup-docs/scripts/test_*.py`
- **T1 refresh up+커밋:** V1 clean+서명OK+V2 → V2 덮고 sidecar 갱신 + 별도 커밋.
- **T2 up-only:** V3+V2 → write 0. **T3 hash-dirty 보존:** write 0 + stuck. **T4 sidecar부재:** write 0+nudge.
- **T5 provenance:** target 안 scaffold.py 있어도 provenance 실패 시 no-op. **T6 정규화 대칭:** CRLF/BOM/개행 변형 → 일치.
- **T7 version_gt:** 0.0.10>0.0.9 참, 역 거짓, malformed fail-closed. **T8 R4:** `install_loop_files` 기존 덮지 않음.
- **T9 최초설치:** 정본+스탬프+sidecar. **T10 릴리스 서명:** 변조 정본 → skipped-bad-signature.
- **T11 UPDATE-only(맵 없음):** 마커 없는 fixture → 상수 수리(UPDATE) 하되 문서 신설(CREATE) 안 함 + 맵 제안.
- **T12 CREATE:** 맵 있는 fixture + 구조결정 → ADR 신설 + 인덱스 등록(orphan=0).
- **T13 MAP진화 확인:** 새 범주 ≥2회 → Tier2 **확인 프롬프트** 방출(승인 전 맵 미변경).
- **T14 세그먼트-소실-0:** 기존 절 삭제 편집 → 보류(write 0). 추가-only는 통과.
- **T15 별도 커밋 격리:** refresh가 사용자 인덱스와 안 섞임. **T16 stuck 노출:** hash-dirty → 가시 신호.
- **T17 맵 링크·grep:** 맵이 CLAUDE.md에서 링크되고 마커 grep으로 발견. 진입 파일 불문.
- **T18 끝 요약 항상:** 변경 有 → 계층별 요약(맵변경 강조). 무변경 → "Docs-Impact: none".
- **T19 이식성:** `test_doc_reconcile_portable.py` 통과(앵커-assert 삭제·리터럴 0). 맵 진화 메타룰은 generic.
- **T20 §9 parity 재베이스:** behavioral parity를 범용 판정 기준으로 갱신.

## 8. Task 개요 (승인 후 TDD)
1. 정규화·버전·sidecar 헬퍼(T6·T7). 2. provenance + 릴리스 서명 검증(T5·T10). 3. `install_loop_files` sidecar+R4 유지(T8·T9). 4. `refresh_loop` 무프롬프트+별도커밋+stuck(T1~T4·T15·T16).
5. **N7 맵 추출:** `write_router`가 진입=링크·맵=라우팅/인덱스/마커 생성. doc-reconcile 마커 조회를 repo-wide grep으로(T17). 이 repo(dogfood) AGENTS.md도 맵 패턴으로 마이그레이트.
6. **N1 특화 폐기:** 정본·이 repo 임베드 앵커 블록 제거+범용화+sidecar. 앵커-assert 삭제(T19).
7. **N4·N8 3능력:** 척추를 UPDATE(구조불요)/CREATE(맵필요)/MAP진화(조건부)로 재작성. 맵 없으면 UPDATE만+제안(T11·T12·T13).
8. **N6-② 세그먼트-소실-0:** content_oracle 재활용해 UPDATE 삭제·대체 가드 + 동결패턴 휴리스틱(T14).
9. **N5·N9 계층 자율+요약:** Tier1 무프롬프트/Tier2 맵변경 확인 + 실행 끝 항상 요약(T13·T18).
10. **N2 프라임 우선순위.** 
11. **ADR + 도달성:** D4 supersede·R4 재정의·N5~N9 ADR 신설 + `decisions/README.md` 로그 + DESIGN.md §9 parity 재베이스 + 이 계획 인덱스 등록(T20).

## 9. 열린 질문 (OQ)
- **OQ1~4 (해결):** sidecar(§3.1)·refresh_loop 무프롬프트(§3.2)·특화 전부 맵/AGENTS.md 이관·version_gt int-튜플.
- **OQ5 (해결 방향):** 맵 없는 repo에서 UPDATE는 하되 CREATE·MAP 안 함(N4). 읽기전용 stale 인벤토리는 UPDATE에 포함.
- **OQ6 (해결 방향):** 릴리스 서명 = 자동 refresh 주방어선 → refresh와 동시 착지(Task2). 서명 키 관리 범위는 M5.
- **OQ7 (해결 방향):** 세그먼트-소실-0 = content_oracle 재활용(Task8).
- **OQ8 (신규):** 맵 문서 파일명·위치(`docs/_doc-map.md` vs AGENTS.md 내 링크 섹션)·아주 작은 repo에서 별도 파일이 과한지 — 구현 시 결정. 추천: 전용 파일 + 진입 링크(원칙 일관).
- **OQ9 (신규):** MAP진화 발동 임계(반복 ≥2회? 신뢰도?) + Tier2 확인을 매번 vs 세션당 배치. 추천: ≥2회 + 배치 확인.

## 10. 상태
- **리뷰 대기(rev4).** 승인 전 구현 금지. 승인 시 Task를 TDD로 확장 + 이 문서 인덱스 등록.
- 검증: consult(rev1)+challenge+architect(rev2)+자가비판(rev3)+설계대화(rev4). 다음: 사용자 리뷰 / 필요 시 codex·architect 재교차.

## 13. 검증 기록
### rev1~rev3 (요약)
- rev1: consult → sidecar/fallback 방향. rev2: challenge+architect → sidecar 확정·R4 봉쇄·정규화·version_gt·provenance·fallback 폐기. rev3: 자율주행 전환 후 자가비판 → 안전을 사람 리뷰→기계로(N6: 세그먼트체크·별도커밋·릴리스서명·stuck 가시화).
### rev4 — 사용자 설계 대화
- **아키텍처 맵 추출(N7):** 마커를 AGENTS.md 인라인 → 전용 맵 문서(진입 불문 링크). 얇은 라우터 원칙 준수 + 어떤 아키텍처든 기술.
- **doc-reconcile 3능력 분해(N4·N8):** UPDATE(구조불요)/CREATE(맵필요)/MAP진화(고위험). rev3 "마커없으면 STOP"을 "UPDATE만+제안"으로 교정 → 유연성 확보하되 환각(CREATE without 맵) 안 엶.
- **자가성장 완성(N8):** 맵도 문서 → doc-reconcile이 맵 진화 → 아키텍처 레벨 자가성장(North Star #3). setup=부트스트랩/reconcile=진화 분리(보조 not 주인).
- **계층 자율(N5):** 전-자율(rev3) → 위험별 2계층. 귀찮음은 빈도 탓이므로 잦은 저위험(UPDATE·CREATE·refresh)=자동, 드문 고위험(MAP진화)=확인. 맵 오판은 "발견 지연"이 위험이라 변경 순간 확인이 잡음.
- **실행 끝 항상 요약(N9):** 무프롬프트라도 계층별 요약(맵변경·refresh 강조, 무변경 정직 보고).
