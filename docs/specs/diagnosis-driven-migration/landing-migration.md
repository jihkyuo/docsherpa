# setup-docs 파이프라인 — 증분 4 (승인된 계획의 실제 랜딩 → 재진단) spec

- 상태: 제안 (브레인스토밍 5-섹션 승인 · **2026-07-09 교차검증 개정** — §0b)
- 날짜: 2026-07-09
- 선행: [design.md](design.md) §5·§7·§8·§10 · [setup-pipeline.md](setup-pipeline.md)(증분 3 = Phase 0·1·2, 이 엔진 재사용) · [render_report 계획](../../plans/2026-07-07-render-report-renderer.md)
- dogfood 타겟: `/Users/jiohyeon/Desktop/projects/vd-front` (git, ~70 docs, 다수 차원 미달 — 첫 doc-health dogfood 대상)

> **범위:** 증분 4 = **Phase 3(승인된 계획을 실 repo에 안전 적용) + Phase 4(결과 재진단)**. 증분 3이 스크래치에서
> "계획이 깨끗함"을 증명했다면, 증분 4는 그 검증된 계획을 **사용자가 검토할 실제 브랜치**로 랜딩하고, 옮긴 결과를
> 같은 채점기로 재진단한다. **배치 판단(타입 vs 기능응집, legacy 통합)·아티팩트 UX(D3·D4·D6)는 별도 트랙**(§8).

## 0. 선결 (이 세션에서 닫힘)

증분 4 실행-게이트 **G1·G2 = 닫힘**(2026-07-09, RED-first, 실쓰기 전 필수 안전판):
- **G1** `inject_claude_md` frontmatter 분기가 `@AGENTS.md`를 frontmatter 세그먼트에 병합(빈 줄 없음) → false-STOP.
  닫는 `---` 뒤 빈 줄 삽입(`\n@AGENTS.md\n\n`)으로 어느 세그먼트에도 병합 안 되게 교정.
- **G2** `apply_moves`·`content_oracle`의 `errors="ignore"` → invalid UTF-8 바이트 소실 사각. 읽기/쓰기/`seg_key`
  전부 `errors="surrogateescape"`로 전환(바이트 라운드트립 = 소실 0 + 오라클이 바이트 차이 감지). preview는
  `backslashreplace`로 표시-안전화.

## 0a. 사용자 합의 결정 (브레인스토밍 확정)

| # | 결정 | 근거 |
|---|---|---|
| L1 | **격리 = 전용 git worktree + 새 브랜치.** 실 작업트리 무영향. 검증 통과 시에만 커밋 → worktree 제거·브랜치만 남김 → 검토·머지는 사용자. 실패 시 흔적 0. | 정체성(비파괴·"주인은 사용자"). M4에서 이미 쓴 방식 |
| L2 | **단일 원자 적용 + 단일 커밋.** 검증된 전체 계획을 `apply_moves`로 한 번에. 배치별 실행 안 함. **이 구현에서 미지원**(배치-안전 정식화는 존재하나 현 apply_moves는 전역 relink·chained-move를 함께 처리하는 2단계라 배치로 쪼개면 깨짐 — §5·S6). | 원칙 2(단순함) · apply_moves 2단계 원자성 |
| L3 | **D1 등록 = 도달성-구동, 균일.** register를 "이동 문서"가 아니라 "아직 orphan인 문서 전부"로 구동 → 이동/제자리/legacy 특별취급 없이 균일 처리. | 원칙 3(특수케이스 대신 일반화) · orphan=0 직접 목표 |
| L4 | **D2 = 보존+표면화.** 마이그레이션은 "새 broken 0"만 보장. 기존 broken은 원본 그대로 보존(앵커 미손) + 아티팩트에 "머지 전 결정할 것"으로 표면화(비차단). auto-de-link 금지. | 정체성(앵커 보존·비파괴·정직) |
| L5 | **랜드는 HEAD 커밋상태 기준.** worktree=커밋상태라 미추적/미커밋 작업(예: vd-front의 `CONTEXT.md`)은 스코프 밖(안 건드림). **검증트리=커밋트리 정합·HEAD sha 핀 필수**(§0b R3). | 재현성·비파괴·정직 |

> **legacy 처리(S2 해소, 결정 A):** register_all은 legacy도 다른 orphan처럼 **제자리 폴더 인덱스에 균일 등록**(L3 순수·F4 "legacy 제자리" 유지). legacy를 `docs/legacy/`로 통합하거나 흐리게 표시하는 것은 **배치-판단/아티팩트 트랙(§8)**. 실행 엔진은 legacy 배치를 결정하지 않는다.

## 0b. 교차검증 개정 (2026-07-09 — /codex + architect 교차)

스펙을 착수 전 교차검증(codex consult + architect, 각기 5파일 호출체인 추적)했더니 **§5 D2 판별규칙 결함**과
정합/커버리지 구멍 다수 발견. 특히 **"3게이트 다 통과인데 내용/앵커/문서 소실"** 사각이 실재. 아래 반영:

| # | 결함 (발견자) | 개정 |
|---|---|---|
| R1 | **D2 fail-open — 이동-소스 링크 오분류(codex C1 · architect S1, 교차).** §5의 "current 깨진 링크의 절대타겟이 base에 있었나"는 소스문서가 이동하면 틀림: `rewrite_links`가 타겟을 새 경로로 re-base → base엔 없던 경로 → **우리가 만든 broken을 preexisting로 오분류 → 비차단 → 자가유발 broken이 브랜치에 실려 나감**(오라클이 자기 목적=rewrite버그 캐치를 못 함). content-중복 문서면 소실도 미검출. | §5 재기술: **역-move_map으로 소스문서 정체성 페어링 → base에서 링크 재해석**. `new_broken` = "base에서 풀렸었는데 current에서 깨짐"(위치-매칭, 절대타겟 존재여부 아님). 도달성-무관 재해석 헬퍼는 **base 쪽에만**(current는 register 후 orphan=0이라 gate.analyze가 이미 전 링크 커버). |
| R2 | **앵커 보존을 게이트가 안 잼(codex C3).** content_oracle는 URL 통째 strip, gate.resolve는 앵커 strip → 링크 앵커가 `guide.md#v1`에서 (버그로) `guide.md#v2`로 바뀌어도 3게이트 통과 → 앵커 조용히 소실(정체성 "앵커 보존" 위반). | §5에 **앵커-보존 체크** 추가: 페어링된 각 링크의 base 앵커(#frag) ⊆ current 앵커. 현 `rewrite_links`는 앵커 보존하나 *강제*가 없던 것을 게이트화. |
| R3 | **검증트리 ≠ 커밋트리(codex C5 · architect S3, 교차).** `build_and_verify`는 tmpdir copytree(워킹디렉터리)를 검증 후 rmtree, 랜딩은 worktree(커밋HEAD)에 **재실행분 커밋** → 검증한 트리와 다른 트리 커밋. + 미추적 파일로 **승인계획 X ≠ 실행계획 X′("아티팩트 거짓말")**. `_COPY_IGNORE`가 `build`/`vendor` 폴더명 제외 → `docs/build/` 문서 오라클 사각. | §2/§3: **worktree 그 자리에서 검증하고 그 트리를 커밋**(재실행 금지). base = **두번째 worktree@핀HEAD**(copytree·ignore-list 회피). **HEAD sha 핀**(Phase 0 기록→랜딩 불변 단정, 스테일 STOP). `apply_moves`가 **move_plan.src 존재 단언**(미추적 유입 시 조용한 no-op 차단). |
| R4 | **이동 후 빈 디렉터리 → dir 링크 커밋 후 깨짐(codex C2).** `apply_moves`는 파일만 삭제, 빈 폴더 잔존. gate는 "dir 존재+무인덱스"를 broken도 traverse도 안 함(통과) — 근데 **git은 빈 폴더 미커밋** → fresh checkout서 dir 링크 broken. "통과 시에만 커밋" 위반. | §3: apply_moves 후 **빈 디렉터리 제거**를 검증 전에. |
| R5 | **register_all 미수렴/오탐(codex C4).** `_append_links`는 raw 링크-substring 매칭으로 "이미 링크됨" 판단하나 gate는 펜스 코드블록 링크 무시 → `_README`에 예시 펜스 링크 있으면 register skip·gate orphan → "orphan==0까지 루프"면 무한 no-op. | §4: **진행 가드**(한 바퀴 신규등록 0인데 orphan 잔존 → error) + **gate와 같은 live-link 파싱**(펜스 제거 후 LINK_RE), substring 아님. |
| R6 | **G2 하드닝 비대칭(architect S4).** register 경로(`_append_links`:150·register home:184)는 여전히 strict UTF-8, `_index_home`:171은 ignore → vd-front 인덱스에 비-UTF8 1개만 있어도 **랜딩 전체 abort**(G2가 막으려던 클래스). | §2: register 경로 읽기 `surrogateescape`로 하드닝. |
| R7 | **content_oracle dedup 사각(codex C7 · architect S5, 교차).** 고유 세그먼트 생존만 증명, 문서 인스턴스 아님 → 동일내용 2문서 중 1개 소실 시 unaccounted=0. 증분4는 실브랜치 커밋이라 실질. | §5에 **per-file 목적지 회계** 추가: 각 move_plan.src의 세그먼트가 *그 dest*에 존재 + 파일수 보존(scaffold 신설 제외) 단언. content_oracle 집합-의미론 보완. |
| R8 | **크래시 흔적(architect S7).** worktree-add와 cleanup 사이 크래시 시 댕글링 worktree/브랜치. "흔적0"은 정상 STOP만 성립. | §3: cleanup을 `finally` + 부분 worktree/브랜치 방어 삭제. |
| R9 | **L2 문구 과장(codex C6 · architect S6, 교차).** "배치 안전이득 0"은 부정확(배치-안전 정식화 존재). design §8이 "배치마다 오라클"로 남아 드리프트. | L2를 "이 구현 미지원"으로 정직화(위 표) + [design.md](design.md) §8 드리프트 갱신. |

## 1. 아키텍처 (모듈 경계)

**통찰 — 증분 4 신규 = ① 랜딩 생애주기 ② 도달성-구동 등록 ③ new-vs-preexisting 링크+앵커+인스턴스 오라클.**
증분 3 엔진(`apply_moves`·`rewrite_links`·`scaffold`·`content_oracle`·`gate`)은 재사용.

| 신규/수정 | 성격 | 책임 |
|---|---|---|
| `migrate.py` `land_migration(repo, move_plan, head_sha, decisions=None, *, plugin_root=None)` (신규) | 실행 진입점 | HEAD sha 핀 검증 → git worktree(current)+새 브랜치 & 두번째 worktree(base@핀HEAD) → apply_moves(src존재 단언)→빈디렉터리 제거→scaffold→register_all → `verify_migration` → **통과 시 그 current worktree를 커밋**(재실행 없음)·worktree들 제거·브랜치 반환; 실패/크래시 시 `finally`로 흔적 0. git 전제(non-git STOP) |
| `migrate.py` `verify_migration(base_root, current_root, move_plan)` (신규, `build_and_verify` 검증부 추출) | 오라클 일원화 | 세 판정을 한 곳에: `unaccounted`(content_oracle) · `new_broken`+`preexisting_broken`+`anchor_lost`(링크 오라클, §5) · `orphan`(gate) + `per_file`(§5 인스턴스 회계). Phase 1b(스크래치)·Phase 3(worktree)가 **동일 함수** 호출 |
| `migrate.py` `register_all(root)` (신규, `register_in_indexes` 대체) | 도달성-구동 등록 | gate.analyze의 orphan을 폴더 인덱스·map에 등록(멱등, **진행 가드** + gate live-link 파싱). legacy 특별취급 없음(L3). 읽기 `surrogateescape`(R6) |
| `migrate.py` 링크 오라클 헬퍼 (신규) | new/preexisting/anchor 판별 | 도달성-무관 전-문서 링크 해석(base 쪽) + **역-move_map 소스정체성 페어링** → base-satisfiable & current-broken = new_broken; 앵커 diff(§5) |
| `migrate.py` `build_and_verify` (수정) | Phase 1b | 검증부를 `verify_migration` 호출로 교체(반환 확장). `apply_moves` src 단언·빈디렉터리 제거 공유 |
| Phase 4 재진단 (SKILL 배선 + render result 모드) | 얇은 래퍼 | doc-health를 랜딩 브랜치에 재실행 → before(Phase 0)/after → `render_report(data, "result")` |
| `render_report.py` (수정) | result 모드 CSS | 이연된 result-모드 CSS 채움. 동결 CSS·WCAG-AA·인라인 style 0 유지 |
| `SKILL.md` (수정) | 에이전트 절차 | Phase 3(land_migration·HEAD핀·git 전제·실패 STOP)·Phase 4 산문 |
| 재사용(신규 아님) | — | apply_moves · rewrite_links · scaffold · content_oracle · gate · doc-health · render_report |

**의존성:** land_migration 의존은 전부 `setup-docs/scripts` 내부. doc-health 재진단은 **SKILL이 doc-health 호출**(migrate가 doc-health 임포트 안 함 — 역-의존 회피, 증분 3 계승).

## 2. 데이터 흐름 (Phase 3→4)

```
[승인된 move_plan (Phase 2) + Phase 0 기록 HEAD sha]
        │
Phase 3 land_migration(repo=vd-front, move_plan, head_sha):
   assert repo HEAD == head_sha           # 스테일 STOP(진단~랜딩 사이 변경 차단)
   wt_cur  = git worktree add -b docsherpa/migrate-<stamp> <head_sha>   # 실 작업트리 무영향
   wt_base = git worktree add --detach <head_sha>                        # 오라클 base(동일 커밋)
   apply_moves(wt_cur, move_plan)          # 단일 원자, src 존재 단언(R3), surrogateescape
   prune_empty_dirs(wt_cur)                # R4: 이동으로 빈 폴더 제거(dir 링크 커밋후 파손 방지)
   scaffold(wt_cur, plugin_root)           # 척추·성장루프
   register_all(wt_cur)                    # 도달성-구동 등록(진행가드·live-link) → orphan=0
   ── verify_migration(wt_base, wt_cur, move_plan) ──
     unaccounted   == 0    (content_oracle 세그먼트)
     per_file       ok      (R7: 각 src 세그먼트가 그 dest에 · 파일수 보존)
     new_broken    == 0    (R1: base-satisfiable & current-broken)
     anchor_lost   == 0    (R2: base 앵커 ⊆ current 앵커)
     orphan        == 0    (gate)
   통과? ── 아니오 → (finally) worktree 2개 제거·브랜치 -D · 실패 리포트 ── STOP
        │ 예
   git -C wt_cur commit (단일)   # ← 검증한 바로 그 트리를 커밋(재실행 없음, R3)
   worktree 2개 제거(브랜치 보존)
   반환 {branch, unaccounted:0, new_broken:0, anchor_lost:0, preexisting_broken:[...], moved:N}
        │
Phase 4 재진단:  doc-health(branch) → after → render_report({before, after, preexisting_broken}, "result")
        │
[사용자: 브랜치 검토 → 머지 or 버림]   ← 우리는 머지 안 함
```

크래시 안전(R8): worktree add~commit 사이 예외는 `finally`가 두 worktree + (미커밋)브랜치를 방어 삭제.

## 3. 랜딩 생애주기 상세 (§0b R3·R4·R8 반영)

1. **HEAD 핀:** Phase 0 진단 시 `repo` HEAD sha 기록 → land_migration 진입에서 불변 단정. 다르면 계획 스테일 → STOP(재진단 유도).
2. **이중 worktree:** `wt_cur`(새 브랜치, 적용 대상) + `wt_base`(detached @핀HEAD, 오라클 base). 둘 다 **커밋상태**라 파일집합 동일(copytree·ignore-list 사각 없음). 미추적/미커밋은 애초에 안 들어옴(L5).
3. **적용:** apply_moves가 각 `move_plan.src` 존재를 단언(없으면 STOP — 미추적 유입 방지). 이동 후 빈 디렉터리 제거(git 빈폴더 미커밋 → dir 링크 파손 방지).
4. **검증=커밋 정합:** `wt_cur`를 **그 자리에서** 검증하고, 통과 시 **그 트리를 그대로 커밋**한다(별도 트리 재빌드·재실행 없음). 승인 아티팩트가 증명한 것과 커밋되는 것이 동일 트리임을 보장.
5. **정리:** 성공·실패·크래시 모두 `finally`에서 두 worktree 제거. 실패/크래시 시 브랜치도 `-D`(흔적 0). 성공 시 브랜치만 남김.

## 4. D1 — 도달성-구동 register_all (§0b R5·R6)

**문제(실측):** `register_in_indexes(root, move_plan)`가 이동 문서만 등록 → 제자리 docs·legacy가 orphan → gate FAIL.

**설계:** 등록을 **orphan 목록으로 구동**(이동/제자리/legacy 균일, L3).
```
register_all(root):
  반복:
    orphans = gate.analyze(root).orphans        # 도달 안 되는 docs/**/*.md
    orphans 비면 종료
    각 orphan → 자기 폴더 인덱스(_ensure_folder_index)에 링크 + 폴더를 map에 배선(멱등)
    이번 바퀴에 신규 등록 0인데 orphan 잔존 → error(진행 가드, R5) — 무한 no-op 차단
```
- **멱등 판정은 gate와 같은 live-link 파싱**(펜스 코드블록 제거 후 `LINK_RE`)을 쓴다 — `_append_links`의 raw substring이 펜스 속 예시 링크를 "이미 있음"으로 오탐하던 것 차단(R5).
- **읽기 `surrogateescape`**(R6): `_append_links`·home 읽기가 strict라 비-UTF8 인덱스에서 abort하던 사각 제거.
- **legacy 균일(결정 A):** legacy도 제자리 폴더 인덱스에 등록. 통합·흐리게는 §8 트랙.

## 5. D2 — 링크 오라클: new vs preexisting + 앵커 + 인스턴스 (§0b R1·R2·R7)

**핵심 교정(R1):** 판별은 **해석된 절대-타겟의 집합 diff가 아니라, 소스문서 정체성 기준 페어링**이다.
소스가 이동하면 base·current에서 링크가 서로 다른 위치 기준으로 해석되므로, 집합 멤버십은 페어링을 잃는다.

```
링크 오라클(base_root, cur_root, move_plan):
  move_map = {src: dest}
  각 base 문서 D_base (경로 old_rel):
    D_cur = cur_root / move_map.get(old_rel, old_rel)      # 역/순 move_map으로 페어링
    base 링크 L_base[i] ↔ cur 링크 L_cur[i]  (rewrite는 순서·개수 보존 → 인덱스 zip)
    각 i:
      sat_base = resolve(D_base, L_base[i]) 존재?     # ← 도달성-무관 재해석(base는 orphan이라 gate 미검사)
      sat_cur  = resolve(D_cur,  L_cur[i]) 존재?      # (cur는 register 후 orphan=0라 gate와 일치)
      sat_base and not sat_cur   → new_broken         # 우리가 깨뜨림 → 차단
      not sat_base and not sat_cur → preexisting      # 원래 깨짐 → 표면화(비차단)
      anchor(L_base[i]) ⊄ anchor(L_cur[i])  → anchor_lost   # R2: 앵커 소실 → 차단
```
- **도달성-무관 헬퍼는 base 쪽에만 필요**(architect S1): base 문서 대부분 orphan이라 `gate.analyze(base)`는 링크를 거의 안 본다. current는 register_all 후 orphan=0이라 `gate.analyze(cur).broken`이 이미 전 링크 커버(중복 회피 가능).
- **워크드 예제 = 이동-소스(어려운 케이스):** `docs/guide/a.md → docs/how-to/a.md`, 링크 `./b.md`(→`docs/guide/b.md`). rewrite 회귀로 a의 링크 미재작성 시 current `docs/how-to/b.md`(없음)=broken인데, 절대-집합 모델은 "how-to/b.md가 base에 없었으니 preexisting"으로 **오분류**. 페어링 모델은 "base의 a→b가 base에서 satisfiable(`docs/guide/b.md` 존재)했는데 current 깨짐 → **new_broken → 차단**". scaffold 자기 dir 링크(빈 타입폴더)도 같은 원리로 우리 것을 preexisting로 숨기지 않게.

**per-file 인스턴스 회계(R7):** content_oracle는 *고유 세그먼트* 생존만 증명(동일내용 2문서 중 1개 소실 미검출). 보완:
각 `move_plan.src`의 세그먼트가 **그 dest 파일에** 존재하는지 + docs 파일수 보존(scaffold 신설분 제외)을 단언 → 문서-인스턴스 소실 차단.

## 6. Phase 4 — 재진단(결과 아티팩트)

- doc-health를 **랜딩 브랜치(옮긴·커밋 상태)**에 재실행 → after 스코어.
- Phase 0 before와 나란히 → `render_report(data, "result")`. before→after 대비(차원 충족·orphan→0·마커/척추/성장루프)를 시각화. `preexisting_broken`을 "머지 전 결정할 것"으로 표면화(L4).
- **result 모드 CSS = 이전 증분 이연분** — 이번에 채움. 동결 CSS·WCAG-AA·인라인 style 0 유지.
- before/after 동일 채점기(doc-health)라 차원 비교 공정 — doc-health 분리 취지 실현.

## 7. 테스트 & 롤아웃 (RED-first)

| # | 조각 | RED-first 검증 |
|---|---|---|
| T1 | `register_all` 균일 | in-place·legacy·이동 섞인 fixture에서 orphan=0. **진행 가드**(등록 불가 orphan → error) · **펜스 예시링크** 오탐 안 함(R5) |
| T2 | 링크 오라클 new vs preexisting | **이동-소스 링크 미-rebase → new_broken 검출**(R1 워크드예제) · 스테일 코드참조 → preexisting · scaffold 빈-폴더 dir링크 오분류 안 함 |
| T3 | 앵커 보존(R2) | base `#frag`가 current서 사라지면 `anchor_lost` 차단 |
| T4 | per-file 인스턴스(R7) | 동일내용 2문서 중 1개 드롭 시 검출(content_oracle 통과해도 per_file fail) |
| T5 | `land_migration` 통과 | 브랜치 생성·**검증트리=커밋트리**·단일커밋·worktree 제거·실 작업트리 무영향 |
| T6 | `land_migration` 실패/크래시 | new_broken 주입 시 커밋 0·브랜치 0·worktree 0(`finally` 흔적0, R8) |
| T7 | HEAD 핀(R3) | 진단~랜딩 사이 HEAD 변경 시 스테일 STOP |
| T8 | 빈 디렉터리(R4) | 폴더 비우는 이동 후 그 dir 링크가 커밋트리에서 broken 아님 |
| T9 | Phase 4 result 모드 | 이연 CSS 존재·AA 대비·인라인 style 0 |

**e2e 순서:** 합성 fixture(제자리 docs + legacy + 스테일 코드링크 + 이동-소스 링크 + 앵커링크 + 빈-폴더유발)로 end-to-end GREEN **먼저** → **그다음 vd-front 실 dogfood**(브랜치 산출, 검토·머지는 사용자).

**정체성 게이트(불가침):** 매 조각이 내용 소실 0·앵커 보존·비파괴를 지키는지 각 테스트가 강제.

## 8. 스코프 밖 (별도 트랙)

- **배치 판단** — 타입 vs 기능응집 조직(Diátaxis 흩뿌림 vs 폴더 응집), **legacy 통합(`docs/legacy/`)** 여부. 도메인 결정 패널(D5 포함). Phase 3 실행 메커니즘과 분리(엔진은 승인된 move_plan을 그대로 실행).
- **아티팩트 UX** — D3(트리 접이식·타입색·**legacy 흐리게**)·D4(은어 제거)·D6(이동 집약뷰·자기설명). render_report 병렬 트랙.
- **깊은 처리** — .mdx content_oracle 지원 · 정규화 transformed · non-git clone · 서브모듈(증분 3서 이연분 유지).
