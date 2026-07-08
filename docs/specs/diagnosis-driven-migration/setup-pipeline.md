# setup-docs 파이프라인 — 증분 3 (진단 → 검증된 계획 → 승인) spec

- 상태: 제안 (브레인스토밍 완료, 사용자 4-섹션 승인)
- 날짜: 2026-07-08
- 선행: [design.md](design.md) §5·§7·§8·§10 · [doc-health.md](doc-health.md)(진단 생산자) · [render_report 계획](../../plans/2026-07-07-render-report-renderer.md)(아티팩트)

> **범위:** 증분 3 = setup-docs 본체의 **"진단 → 목표트리 → 검증된 계획 아티팩트 → 승인"**(Phase 0·1·2).
> 지금까지 만든 두 조각(doc-health 진단·render_report 렌더)을 파이프라인으로 배선한다. **실제 repo
> 마이그레이션 실행(Phase 3)·결과 재진단(Phase 4)은 증분 4로 이연.**

## 0. 사용자 합의 결정 (브레인스토밍 확정)

| # | 결정 | 근거 |
|---|---|---|
| P1 | **검증된 계획** — Phase 1b 자체검증(스크래치에 목표트리 빌드 → 두 오라클 통과 → 등급 증명)을 증분 3에 포함. 사용자에 보여주는 계획은 "이대로 하면 진짜 A" 증명된 것. | design §7 "증명 후 제시". 거짓 계획 금지 |
| P2 | **최소 코어** — 순수 이동/개명(verbatim) + 링크리라이트 + 두 오라클. **git 전제.** 정규화 transformed·비-git clone·동결역사 깊은 처리는 이연. | 유실 0 불변식 집중, 스코프 부풀림 방지(D8 opt-in) |

## 1. 아키텍처 (모듈 경계)

**통찰 — 신규는 세 조각뿐.** doc-health가 분류(`inventory`)·모순(J4)을 이미 하고, render_report는 plan 모드 UI가 완성, content_oracle·gate·scaffold도 있다. 증분 3 신규 = **배정 + 스크래치 검증 + 계획 조립.**

| 신규/수정 | 성격 | 책임 |
|---|---|---|
| `skills/setup-docs/scripts/migrate.py` (신규) | 결정론 엔진 | `plan_moves(inventory)` 타입→목적지 배정 · 스크래치에 이동+링크리라이트 · scaffold 호출(spine·loop) · gate + content_oracle → `{broken, orphan, unaccounted}` |
| `skills/setup-docs/SKILL.md` (수정) | 에이전트 절차 | MESSY 무거운 차선을 새 파이프라인으로 재배선(Phase 0·1·2) |
| 재사용(신규 아님) | — | doc-health(진단·재채점) · content_oracle · gate · scaffold · render_report · scaffold 링크리라이트 헬퍼(`_rewrite_urls`) |

**분업(doc-health 계승):** 배정의 **결정론**(type→folder)은 migrate.py. **판단**(co-change 토픽폴더·`specs/<feature>`명·동결역사 식별)은 SKILL 산문. "판단을 코드로 박제하지 말라"(§7.5 교훈).

**의존성:** migrate.py의 의존(gate·content_oracle·scaffold)은 **전부 `setup-docs/scripts` 내부** — 크로스-dir 임포트 없음. doc-health 재채점은 **SKILL이 doc-health를 호출**(migrate가 doc-health를 임포트하지 않음 → 역-의존 회피).

**(기각) 대안:** migrate 로직을 `scaffold.py`에 넣기 → scaffold="설치"·migrate="이동"으로 성격이 달라 scaffold 비대. 신규 모듈이 맞고, 증분 4가 이 migrate.py를 실제 실행에 재사용.

## 2. 데이터 흐름 (Phase 0→1→2)

```
Phase 0 (before 진단)
  SKILL → doc-health → { grade, scorecard, trees.before, inventory:[{path,type,disposition,coupling}], J4모순 }

Phase 1a (배정)
  migrate.plan_moves(inventory) [결정론]:
    ADR→decisions/ · how-to/troubleshooting→how-to/ · spec→specs/<feature>/ · PRD→product/
    · reference/explanation→docs/평면 · router/tooling→제자리(이동 X)
  + SKILL 판단: 토픽폴더(co-change≥2)·feature명·동결역사(인덱스만)·임팩트플래그(코드참조·외부싱크 깨짐)
    → move_plan = [{src, dest, ops:[move|rename], impact}]

Phase 1b (자체검증 = 엔진)   migrate.build_and_verify(repo, move_plan):
    ① 스크래치 사본  ② 이동+링크리라이트  ③ scaffold(스크래치: spine+성장루프)
    ④ gate → broken/orphan  ⑤ content_oracle(base=repo, current=스크래치) → unaccounted
    → {broken, orphan, unaccounted}
  SKILL: 스크래치에 doc-health 재실행 → 기계등급 확인
  ✋ STOP(§3): grade 미달·unaccounted>0·목적지충돌 → 아티팩트 안 냄

Phase 2 (계획 아티팩트 + 승인)   계획 데이터 조립:
    repo·grade(현재/목표A)·scorecard·trees.before  ← doc-health
    trees.after·migration                          ← move_plan
    decisions = 라우터결정(결정론 감지) + 내용모순(doc-health J4 재사용)
    → render_report(data,"plan") → HTML 아티팩트 → 사용자 승인
```

**증분 3 산출 = 승인된·검증된 마이그레이션 계획**(실제 실행은 증분 4).

## 3. STOP 조건 · 엣지

**STOP = 흐름 중단 + 사유 보고 + (자동수정 재시도 또는 사용자 에스컬레이션).** 조용한 멈춤도, 조용한 수정도 아님.
1b는 **스크래치**에서 도므로 STOP 시 실제 repo 무손상(공짜) — 스크래치 버리고 보고.

STOP 조건(1b):
1. `content_oracle unaccounted > 0` → 유실 위험. 미분류 세그먼트 보고.
2. gate broken≠0 또는 orphan≠0 → 도달성 미달.
3. 스크래치 재채점 후 기계등급 미달(M1~M5 not all pass) → 배정 부족(어느 차원인지).
4. 목적지 충돌(둘 → 같은 경로).

**엣지(design 계승):**
- **자세별 차등:** GREENFIELD=조용히 설치(아티팩트 X) · HEALTHY=등급 카드만 · **MESSY만 풀 파이프라인.**
- **동결 역사**(날짜박힌 specs/plans): 인덱스만·내용 verbatim·repoint 금지. 증분 3은 최소 처리(이동 대상서 "인덱스만"으로 배정, 깊은 de-link는 증분 4).
- **비-git repo:** 스코프 밖(P2). 감지 시 "git init 먼저" 안내(content_oracle 전제).
- **이동할 content 0**: move_plan 빈 계획 → 1b는 spine/loop만 검증.

## 4. 정직성 정밀화 — "등급 A 증명"의 엄밀한 의미

1b가 **결정론으로 증명**하는 것 = **M1~M5(기계 차원) pass + content_oracle unaccounted=0(무손실)**.
**J1~J4는 판단**이라 스크래치로 증명 불가 — Phase 0에서 평가되고 계획이 개선하지만, gate-증명 대상 아님.
→ 아티팩트는 **"기계 차원 A-트랙 + 내용 보존 증명"**을 정직하게 표시하고, J는 판단 평가로 별도 표기.
design §7 "등급=A 증명"의 정직한 해석(J를 결정론으로 증명하는 척하지 않음).

## 5. 테스트 계획 (RED-first — docsherpa 정책)

| 테스트 | 대상 | 기대 |
|---|---|---|
| `plan_moves` | 픽스처 inventory(타입별) | 정확 목적지 · router/tooling 이동 X |
| 링크 리라이트 | 교차링크 픽스처 → 이동 | gate broken=0(TO·FROM 링크 갱신) |
| `build_and_verify` **(핵심)** | 합성 messy repo | broken=0·orphan=0·unaccounted=0 |
| 유실 감지 | 세그먼트 빠지는 픽스처 | unaccounted>0 → STOP |
| STOP 조건 | 목적지 충돌 | 에러/STOP + 사유 |
| 계획 조립 통합 | assembled dict → render_report("plan") | div 밸런스·KeyError 0·style= 0 |

**최고 위험 = 링크 리라이트 정확성 + content_oracle 무손실 증명**(유실 0의 심장). RED-first 필수.
**판단(토픽폴더·feature명·모순 표면화·MESSY 하위) = SKILL 산문, 유닛테스트 X**(§7.5 교훈).

## 6. 스코프 밖 (증분 4 이상)

- **Phase 3 실제 실행** — worktree 격리·배치·실제 repo 이동·랜드. migrate.py 재사용.
- **Phase 4 결과 재진단** — doc-health 재실행 → render_report("result"). result-모드 CSS(증분 1 이연분) 여기서.
- 정규화 transformed(내부 포맷) · 비-git clone 경로 · 동결역사 깊은 de-link — 이연(P2).
