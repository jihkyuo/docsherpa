# 0015. doc-health 모듈 분해

- 상태: 수락
- 날짜: 2026-07-08

## 맥락

setup-docs 재설계(진단-주도 마이그레이션, design.md §4)는 파이프라인을 6단계로 나눈다: Phase 0(전체-repo
병렬 탐색·9차원 채점·자세 판정) → Phase 1(목표트리) → Phase 2(계획 아티팩트·결정) → Phase 3(worktree 실행) →
Phase 4(결과 재진단). Phase 0(before)과 Phase 4(after)는 마이그레이션 전후 등급("F→A")을 사용자에게 보여주는데,
이 비교가 참이려면 **before와 after를 반드시 동일한 채점기로 재야 한다** — 진단 로직이 setup-docs 내부에
흩어져 있으면 두 시점의 채점 기준이 미묘하게 달라질 위험이 있고, 그 순간 "F→A" 숫자는 거짓말이 된다.
design.md §4는 이 정합성 논거로 진단을 별도 모듈로 뺄 것을 요구했고, doc-health.md §0(H1~H3)이 착수 전
사용자 합의로 그 분해 방식을 구체화했다.

## 결정

**doc-health를 독립 읽기 전용 스킬로 추출한다.** `skills/doc-health/`에 자체 SKILL.md·reference/scoring.md·
전용 `scripts/`(inventory.py·scorecard.py·test_*)를 둔다. 전체-repo 탐색 → 9차원 채점 → 등급 → 자세를
계산해 render_report가 소비할 데이터 모델의 부분집합을 반환하는 것이 유일한 책임이다. 소비·변경(목표트리·
계획·worktree 실행)은 setup-docs 몫으로 남긴다 — 진단과 실행을 깨끗이 분리한다.

- **H1 (M5 분모 = 흩어진 content 문서만):** 라우터(AGENTS/CLAUDE/GEMINI)·도구 디렉터리(`.claude/`·
  `.github/`·`.cursor/`·`.gitlab/`)·루트 관례 파일(README·CONTRIBUTING·CHANGELOG·SECURITY·CODE_OF_CONDUCT)은
  accounted-but-not-violation으로 취급하고 M5(문서 위치 위반) 분모에서 제외한다. 이들이 M5에 들어가면
  구조적으로 등급 A를 받을 수 없는 repo가 생겨 채점 자체가 거짓이 된다. README 비대 같은 문제는 M5가 아니라
  J3(판단 차원)의 몫이다.
- **H2 (전용 scripts 디렉터리):** 새 결정론 로직(`inventory.py`·`scorecard.py`)은 `skills/doc-health/
  scripts/`에 산다. `gate`·`contract`·`render_report`는 복제하지 않고 `setup-docs/scripts`에서 그대로
  재사용한다 — `conftest.py`가 `sys.path`를 부트스트랩해 `import gate`가 그대로 동작하게 한다. 스킬
  자립성(독립 실행 가능)과 단일 채점기 유지(정합성)를 동시에 만족시키는 절충이다.
- **H3 (`gate.analyze()` 외과적 추출):** `gate.main()`의 BFS 도달성 코어를 `analyze(root) →
  {broken, orphans, homes, all_docs, visited}`로 뽑아내고, `main()`은 그 결과를 호출해 기존과 바이트
  동일하게 출력만 한다. scorecard.py가 이 `analyze()`를 재사용함으로써, Phase 0과 Phase 4가 **코드
  레벨에서** 같은 도달성 엔진을 타는 것을 보장한다. 기존 gate 테스트가 이 리팩터의 회귀를 방어한다.
- **판단은 산문으로 남긴다.** J1~J4(판단 차원)는 코드화하지 않고 SKILL.md 절차 + knowledge.md 렌즈로
  에이전트가 직접 수행한다 — 휴리스틱을 억지로 결정론화하면 오히려 오탐이 늘어난다는 것이 기존 setup-docs
  경험(ADR 0014)의 교훈이다.

## 결과

- **정합성 확보:** before/after 비교가 구조적으로 참이 된다(같은 `analyze()`, 같은 M1~M5 로직).
- **스킬 자립성:** doc-health는 setup-docs 없이도 단독 실행 가능한 "수시 건강검진" 도구가 된다.
- **트레이드오프 — 크로스-디렉터리 import 부트스트랩 비용:** `conftest.py`의 `sys.path` 조작은 두 스킬의
  scripts가 물리적으로 분리된 디렉터리에 있다는 사실을 감춘다. 테스트 러너도 두 개로 늘어난다
  (`skills/setup-docs/scripts` · `skills/doc-health/scripts`) — AGENTS.md 명령어에 둘 다 병기해 회귀를
  놓치지 않게 한다.
- **이연:** `render_report.py`는 이번 분해에서 옮기지 않고 `setup-docs/scripts`에 그대로 둔다(design.md
  §4는 이를 "스킬 아님, `gate.py`류의 공유 스크립트"로 분류). doc-health·setup-docs 양쪽이 공유 소비하는
  구조라 별도 위치로의 재배치는 이번 증분 스코프 밖 — 필요해지면 후속 결정으로 다룬다.
