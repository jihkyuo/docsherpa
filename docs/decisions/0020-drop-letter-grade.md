# 0020. A~F 등급 폐기 — 판단을 코드로 박제하지 않는다

- 상태: 수락
- 날짜: 2026-07-09
- 관련: [0019](0019-freeze-heavy-lane-and-renderer.md)(동결의 첫 집행) · [0018](0018-disposition-in-place-classes.md)(부분 supersede — 아래)

## 맥락

`scorecard.rollup()`은 9차원 상태를 `A`~`F` 한 글자로 접는다. 그 산식은 임계값 4개
(`M5_WARN_MAX`·`ORPHAN_MOST`·`J_WARN_MAX`·`GREENFIELD_MAX`)에 의존하고, **소스 주석이 스스로
`🔴 열린질문 — 하드닝 루프 튜닝`이라 쓰고 있다.**

그 대가가 실측됐다(FINDINGS DF4): `if m["M5"] == "fail": return "D"` 때문에 **다른 차원이 전부
`pass`여도 동결 역사 문서 6건이 `docs/` 밖에 있으면 등급이 `D`로 떨어진다.** 그리고 이 등급은
승인 아티팩트의 **히어로 카드 최상단** — 사용자가 마이그레이션을 승인할지 결정하며 보는 첫 숫자다.

`/codex` 적대적 교차검증도 [P1]로 같은 결론을 냈다: *"the A-F grade and hardcoded taxonomy are not
load-bearing. Thresholds are admitted 'open question' constants."* 반면 9차원 자체는 *"turns gate
state, router state, loop installation, and outside-doc drift into legible dimensions — that supports
approval trust"* 로 유지 가치를 인정했다.

FINDINGS의 자가진단이 이 병을 이미 명명해뒀다: *"갭1 — `anchor_signals.py`를 지었다가 삭제함…
**판단 작업을 코드로 박제하지 말 것.** 그런데 `scorecard.py`는 임계값 4개를 박고 주석에 스스로
🔴 열린질문이라 썼다. DF4가 그 대가다."*

## 결정

**등급(`A`~`F`)과 그 임계값을 삭제한다. 9차원의 `pass`/`warn`/`fail`과 그 합계만 남긴다.**

- `scorecard.rollup()` 삭제. `ORPHAN_MOST`·`J_WARN_MAX` 삭제(rollup 전용).
  `M5_WARN_MAX`(M5 상태 판정)·`GREENFIELD_MAX`(posture 힌트)는 **차원/자세 판정에 계속 쓰이므로 잔존.**
- `assemble()`의 `"grade"` 키 삭제. `counts`(fail/warn/pass tally)와 `dims`는 유지.
- `render_report._render_hero`: 등급 스케일(F→A 눈금·현재/목표) 제거. 이미 있던
  **"9개 진단 차원 중 N개 충족"** 문장과 범례가 히어로를 대신한다.
- `render_report._render_grade_compare`(result 모드 등급 비교) 삭제. **대체 배선을 새로 깔지 않는다**
  ([0019](0019-freeze-heavy-lane-and-renderer.md) 동결 — 삭제는 허용, 신설은 금지). result 모드의
  개선 증명은 이미 있는 **규모 라인**(고아 N→0 · 유실 0)과 **after 차원표**가 맡는다.
- 위 삭제로 고아가 된 CSS 규칙(`.scale`·`.tick`·`.cap`·`.seg` 등 등급 전용)만 제거한다. 나머지
  `TEMPLATE_CSS`는 동결 유지.

### 정보 손실 0 근거

등급이 운반하던 신호는 전부 차원에 이미 있다.

| rollup 분기 | 대체 |
|---|---|
| `not router_present → F` | `M2` = fail ("진입 라우터 없음") |
| `M1 fail + orphan_ratio ≥ 0.5 → F` | `M1` = fail + `sub`에 깨진 링크·고아 실수 |
| `M5 fail → D` | `M5` = fail ("docs/ 밖 content N건") |
| `m_nonpass ≥ 1 → C` | `counts.fail`/`counts.warn` |
| J 상태 접기 | J 차원 각각의 상태 |

즉 등급은 **정보를 더하지 않고 임계값이라는 의견을 더했다.**

## ADR 0018 부분 supersede

[0018](0018-disposition-in-place-classes.md) "수용한 트레이드오프"는 posture가 GREENFIELD로 오탐돼도
*"`scorecard.rollup()`은 `if not router_present: return 'F'`이므로 **등급은 F로 정직하게 유지**된다"*
를 안전망으로 들었다. 등급이 사라지므로 그 문장은 무효다. **대체 안전망: `M2`(진입 라우터 + 계약
마커) = `fail`.** `machine_dims`가 `m2 = "pass" if (res.router_present and n_home == 1) else "fail"`로
이미 계산하고 있어 정직성은 동일하게 유지된다. 0018의 나머지 결정(제자리 클래스 계약)은 유효하다.

## 결과

- 승인 아티팩트가 사용자에게 **거짓말을 하지 않는다.** 동결 역사 문서를 가진 건강한 레포가 `D`를
  받지 않는다.
- 임계값 튜닝 루프(`🔴 열린질문`)가 소멸한다. 튜닝할 상수가 없다.
- 등급 비교(`before → after`)가 사라지므로 result 아티팩트의 "개선 증명"은 **차원 충족 수와
  실측치**(고아 N→0, 깨진 링크 N→0)로만 말한다. 이 편이 더 강한 증거다.

## 수용한 트레이드오프

한 글자 요약은 스캔하기 쉬웠다. 이제 사용자는 차원 표를 봐야 한다. 그러나 그 한 글자가 **틀렸으므로**
스캔 편의는 신뢰의 대가로 지불할 값이 아니다.
