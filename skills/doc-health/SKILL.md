---
name: doc-health
description: 문서 건강을 전체-repo 탐색+9차원 채점으로 진단(읽기전용). 수시 건강검진 또는 setup-docs Phase 0·4가 호출.
---

# doc-health

## Overview

**읽기전용 진단 생산자.** repo 전체를 탐색해 9차원(기계 M1~M5 + 판단 J1~J4)으로 채점하고,
등급(F~A)·자세(GREENFIELD/HEALTHY/MESSY)를 매긴다. 산출물은 render_report 데이터 모델의
**부분집합**이다 — doc-health는 목표 트리를 그리지 않고, 마이그레이션을 계획하지 않고, 결정
패널을 만들지 않는다. **아무것도 바꾸지 않는다.** 소비·변경(목표트리·마이그레이션·결정 패널)은
setup-docs 몫이다.

## When to Use

- 수시 "문서 건강검진" — 사용자가 지금 상태만 알고 싶을 때(독립 실행).
- setup-docs Phase 0(마이그레이션 전 진단)·Phase 4(마이그레이션 후 재채점)에서 호출.

## 절차

1. **분모 산출.** `python3 skills/doc-health/scripts/inventory.py list <repo>` → repo 전체
   `*.md`·`*.mdx`(제외: `node_modules`·`.git`·`dist`·`build`·`vendor`) 목록. 이게 "잊힌 문서 0"의
   분모다.

2. **병렬 분류 — 판단, 코드 아님.** 목록을 슬라이스로 나눠 서브에이전트를 동시에 띄워 각 문서를
   판정한다. 산출 매니페스트 형태: `[{path, type, role, coupling, summary}, ...]`.
   - `type` ∈ ADR/spec/how-to/reference/PRD/legacy.
   - `coupling` = 코드참조·외부싱크·동결역사 같은 결합 신호.
   - **판단 휴리스틱의 단일 소스는 [`skills/setup-docs/reference/knowledge.md`](../setup-docs/reference/knowledge.md)** — 여기서 중복 서술하지 않는다.
   - disposition(router/tooling/content)은 `scorecard.py`가 경로 규칙으로 결정론 계산하므로,
     분류는 **content 타입 판정**에만 집중한다.

3. **완결성 가드.** `python3 skills/doc-health/scripts/inventory.py check <repo> --manifest <manifest.json>`
   → `unaccounted`(목록엔 있는데 매니페스트에 없는 경로)가 하나라도 있으면 **STOP** — 잊힌 문서가
   있다는 뜻이니 분류를 다시 돌지 다음 단계로 넘어가지 않는다. `unaccounted=0`이면 진행.

4. **J1~J4 판단.** 아래 산출을 `judgment.json = [{code, name, sub, status}, ...]`로 만든다
   (`status` ∈ pass/warn/fail).
   - **J1** 타입분류 정확성 — 매니페스트의 `type`이 실제 문서 내용과 맞는가.
   - **J2** 폴더승격 적정성 — 폴더화된 곳이 실제 co-change 결합인가, 흩어짐인가.
   - **J3** hollow·중복·bloat — 빈 placeholder 남용, 같은 내용 중복, README 비대 포함.
   - **J4** 정합성 플래그 — 문서 간 모순·오래된 서술.
   - 판단 기준(루브릭)은 [`reference/scoring.md`](reference/scoring.md)를 따른다.

5. **채점.** `python3 skills/doc-health/scripts/scorecard.py <repo> --manifest manifest.json --judgment judgment.json`
   → 기계 차원(M1~M5) + 앞서 만든 판단 차원(J1~J4) + 등급 rollup + 자세 힌트가 담긴 데이터 dict를
   stdout에 JSON으로 낸다. **`--judgment`는 필수 인자다** — 9차원(M+J)을 전부 평가해야 등급이
   정직해지므로, 판단을 건너뛰고 기계 차원만으로 채점을 시도할 수 없다. `--manifest`는 선택(주면
   결과 dict의 `inventory` 키로 그대로 들어간다).

6. **자세 판정.** dict의 `posture` 힌트(GREENFIELD/HEALTHY/MESSY)를 받는다. `MESSY`면 그 하위
   구분(중구난방 / 자체구조 있음 / 자체 성장 루프가 있으나 드리프트된 상태)은 스크립트가 아니라
   에이전트 판단이다 — ADR 0014의 진단-주도 제안 기준을 그대로 쓴다.

7. **(독립 실행 시) 렌더.** setup-docs에 연동되지 않고 doc-health만 단독으로 돌린 경우, 5번의
   dict에 doc-health가 채우지 않는 키를 빈 값으로 채워 넣고 `render_report(dict, "plan")`을 호출해
   아티팩트를 만든다:
   - `trees.after = {"title": "", "tag": "목표", "sub": "", "lines": []}`
   - `migration = []`
   - `decisions = []`
   - `summary = {}`

   결과는 히어로+점수표+현재(before) 트리만 채워지고 목표 트리·마이그레이션 표·결정 패널은 빈
   채로 렌더된다 — 빈 섹션 헤더가 보이는 건 의도된 동작이다(doc-health가 아직 안 정한 것이므로).
   setup-docs와 연동될 때는 이 빈칸을 setup-docs가 직접 채우므로, doc-health는 5번의 dict를
   그대로 넘기면 된다.

## 산출 데이터 계약

doc-health가 채우는 키(render_report 데이터 모델의 부분집합):

```
repo(name·docs_count·branch) · grade(current·target) · counts(fail·warn·pass) ·
scorecard(mechanical·judgment) · trees.before · posture · inventory(선택)
```

`trees.after`·`migration`·`decisions`·`summary`는 doc-health가 **채우지 않는다** — setup-docs가
확장하는 몫이다.

## Common Mistakes

- **unaccounted STOP을 무시하고 진행** — 잊힌 문서가 있는 채로 채점하면 등급이 거짓말이 된다.
- **판단(J1~J4·타입분류·MESSY 하위자세)을 코드로 박제하려는 시도** — 이 스킬의 판단 차원은
  산문 절차다. 결정론화하면 §7.5 앵커 특화 교훈(코드가 아니라 에이전트가 실제 문서를 보고
  판정해야 한다)을 반복하게 된다.
- **router/tooling을 M5 위반으로 오인** — `AGENTS.md`/`CLAUDE.md` 같은 라우터, `.claude/`·README
  같은 도구/관례 파일은 disposition이 router/tooling이라 M5 분모에서 제외된다(제자리가 정상).
  M5는 `docs/` 밖에 흩어진 **content** 문서만 센다.
- **`--judgment` 없이 scorecard.py를 돌리려는 시도** — 필수 인자다. 생략하면 실행 자체가 안 된다.
- **정본 산문에 프로젝트 고유 리터럴 삽입** — 이 SKILL.md·reference/scoring.md는 어떤 repo에도
  적용되는 정본이다. 픽스처·특정 프로젝트명은 스크립트의 테스트 파일 안에만 산다.
