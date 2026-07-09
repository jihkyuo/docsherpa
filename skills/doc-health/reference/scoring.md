# doc-health 채점 루브릭 (9차원)

> [`SKILL.md`](../SKILL.md)의 절차 4·5에서 참조한다. 판단(J1~J4)의 세부 휴리스틱 자체는
> [`../../setup-docs/reference/knowledge.md`](../../setup-docs/reference/knowledge.md)가 단일 소스다 —
> 여기서는 J1~J4가 "무엇을 pass/warn/fail로 보는가"만 정의하고 중복 서술하지 않는다.

9차원 = 기계 판정 5개(M1~M5, `scorecard.py`가 결정론 계산) + 판단 4개(J1~J4, 에이전트가 산문으로
판정). 전부 `status ∈ {"pass", "warn", "fail"}`로 정규화된다.

---

## 기계 차원 M1~M5

기계 차원은 `skills/doc-health/scripts/scorecard.py`가 `gate.analyze()`(도달성 엔진 재사용) +
inventory disposition으로 계산한다. 에이전트가 판정을 다시 내릴 필요는 없다 — 여기서는 각
차원이 **무엇을 측정하는지**만 이해하면 된다.

| 차원 | 이름 | 판정 규칙 | 2치/3치 |
|---|---|---|---|
| **M1** | 도달성 | broken link == 0 **and** orphan == 0 → pass, 아니면 fail | 2치 |
| **M2** | 라우터+마커 | 라우터 파일(AGENTS.md/CLAUDE.md 등) 존재 **and** 마커 home이 정확히 1개 → pass | 2치 |
| **M3** | 맵 척추 | M2의 home 경로가 `docs/_map.md`(인덱스/라우팅이 별도 맵 문서로 분리)면 pass, 진입 파일에 인라인이면 fail | 2치 |
| **M4** | 성장 루프 | doc-drift-prime 텍스트 · SessionStart 훅 · doc-reconcile SKILL 3종이 모두 있으면 pass | 2치 |
| **M5** | 커버리지 | `docs/` 밖에 흩어진 content 문서 수 — 0=pass, 1~경계=warn, 초과=fail | 3치 |

**M2 vs M3 구별에 유의:** M2는 "마커 계약이 성립하는가"(home이 정확히 1개), M3는 "그 home이
맵 척추 문서인가"다. 진입 파일에 라우팅/인덱스를 인라인으로 박아 넣은 repo는 M2는 통과해도
M3는 실패한다 — 계약은 있지만 척추가 분리되지 않은 상태다.

**M5의 분모는 disposition으로 결정된다.** 모든 문서는 경로 규칙으로 router(진입 라우터 파일 —
**어느 깊이든, 중첩 라우터 포함**) · tooling(`.claude/`류 도구 디렉터리 + README/CONTRIBUTING
같은 루트 관례 파일 + **코드-인접 중첩 `README.md`**) · content(그 외 전부) 3가지로 분류된다.
router·tooling은 제자리가 정상이라 M5 분모에서 제외되고, content가 `docs/` 밖에 있을 때만 M5
위반으로 센다. (완결성 가드는 여전히 성립한다 — router·tooling도 inventory 매니페스트에는
accounted로 들어간다.)

M5의 "파묻힘 0"은 **중앙집중 대상 문서가 모두 `docs/` 아래**라는 뜻이지 레포의 모든 `.md`가
`docs/` 아래라는 뜻이 아니다 — router·tooling은 제자리가 정상이라 도달성·M5 분모에서 함께
면제된다(ADR 0018).

---

## 판단 차원 J1~J4

에이전트가 실제 문서를 읽고 산문으로 판정한다. 코드로 결정론화하지 않는다 — 판단이 코드로
박제되면 문서가 실제로 어떻게 쓰이는지와 무관한 기계적 통과/실패가 되어버린다.

| 차원 | 이름 | 무엇을 보는가 |
|---|---|---|
| **J1** | 타입분류 정확성 | 분류 매니페스트의 `type`(ADR/spec/how-to/troubleshooting/reference/PRD/legacy)이 문서 실제 내용과 맞는가. 예: "왜" 문서인데 how-to로 분류됐다면 fail. **트러블슈팅은 실제 절차(명령·진단·복구)여야 — symptom→link뿐인 링크-전용이면 troubleshooting 아님(Status로 붕괴, fail).** |
| **J2** | 폴더승격 적정성 | 폴더로 묶인 문서들이 실제로 함께 읽혀야 할 결합(co-change locality)인가, 아니면 같은 주제라는 이유만으로 억지로 묶였거나(타입 폴더로 결합 흩기) 반대로 흩어져야 할 게 억지로 묶였는가. |
| **J3** | hollow·중복·bloat | 내용 없이 자리만 차지하는 placeholder(명시 안 된 hollow), 같은 내용이 여러 문서에 중복, 진입 파일이나 개별 문서가 과도하게 비대해진 경우(README 비대 포함). |
| **J4** | 정합성 플래그 | 문서 간 서로 모순되는 서술, 코드와 어긋난 오래된 설명, 깨진 게 아니라 "틀린" 링크 라벨(대상은 맞지만 이름이 옛 파일명인 경우 등). |

J1~J4의 판정 기준·안티패턴 목록·"자체 루프가 드리프트된 상태" 같은 세부 판단 렌즈는
[`skills/setup-docs/reference/knowledge.md`](../../setup-docs/reference/knowledge.md)의 "안티패턴"·"진단
휴리스틱" 절을 그대로 쓴다. 이 문서는 그 지식을 doc-health의 9차원 틀에 어떻게 배치하는지만
정의한다.

---

## 등급 rollup (F ~ A)

`scorecard.py`가 M1~M5 상태 + J1~J4 상태 + 신호(`orphan_ratio`, `docs/` 밖 content 개수,
라우터 존재 여부)로 등급을 결정론 계산한다. 순서대로 첫 번째로 맞는 조건이 등급이 된다:

```
1. 라우터 없음                              → F
2. M1 fail 이고 orphan_ratio >= 임계치       → F   (대부분 미도달)
3. M1 fail                                  → D   (다수 고아, 절반 미만)
4. M5 fail                                  → D   (대량 밖 content)
   ── 여기부터는 M1 pass 확정 ──
5. M2~M5 중 non-pass 3개 이상               → D   (도달은 되나 구조 취약)
6. M2~M5 중 non-pass 1~2개                  → C
   ── 여기부터는 M1~M5 전부 pass ──
7. J 중 fail이 하나라도 있거나 warn이 임계치 초과 → C
8. J warn이 1~임계치 개                      → B
9. 그 외(전 9차원 pass)                      → A   (완료의 정의)
```

**구조(관문 순서·비-pass 카운트 로직)는 고정이다.** 각 단계에 쓰이는 구체 숫자 —
orphan_ratio 임계치, M5 warn/fail 경계, J warn 허용 개수 — 는 **🔴 튜닝값**이다. 하드닝
루프에서 실제 repo로 검증하며 조정될 수 있으므로, 이 문서에서 특정 숫자를 "정답"처럼 인용하지
않는다. 정확한 현재값은 `skills/doc-health/scripts/scorecard.py` 상단 상수를 직접 확인한다.

---

## 자세 (posture)

등급과 별개로, repo가 지금 어떤 상태인지를 3가지로 요약한다. `scorecard.py`가 결정론으로 힌트를
낸다:

- **GREENFIELD** — 라우터가 없고 content 문서도 거의 없다. 아직 문서 체계가 서기 전이다.
- **HEALTHY** — 라우터가 있고 도달성(M1)과 커버리지(M5)가 pass다. 구조가 서 있다.
- **MESSY** — 그 외 전부. 라우터는 있는데 도달성이 깨졌거나, content가 `docs/` 밖에 흩어졌거나,
  둘 다다.

**MESSY의 하위 구분(중구난방 / 자체구조 있음 / 자체 성장 루프가 있으나 드리프트된 상태)은 스크립트가 내지 않는다.**
이건 에이전트가 실제 문서 트리를 보고 내리는 판단이다 — 어떤 하위 구분이냐에 따라 이후 제안
전략(선택지 제시 vs 승인만 구함 vs 우리 것 복구)이 완전히 달라지기 때문에, 결정론 규칙 하나로
뭉뚱그리면 오판 위험이 크다. 판단 기준은 SKILL.md 절차 6과 setup-docs의 진단-주도 제안 절을
따른다.
