# 0018. 코드-인접 README·중첩 라우터는 "제자리(in-place)" 클래스 — 문서-건강 우주 밖

- 상태: 수락
- 날짜: 2026-07-09
- 관련: [0017](0017-troubleshooting-first-class-doc-type.md)(같은 배치)

## 맥락

vd-front dogfood에서 `contract.disposition`이 중첩 `CLAUDE.md`(서브트리 스코프 라우터)와
코드-인접 `README.md`(`src/**/mocks/`, `src/**/api/`)를 `content`로 분류했다. 그 결과 마이그레이션
엔진이 이들을 `docs/README.md`로 옮기려 했고, 여러 `README.md`가 단일 목적지에서 basename 충돌 →
`ValueError` STOP으로 이어졌다.

적대적 codex 리뷰가 [P2]로 지적: 픽스 이후 `contract.disposition()`이 중첩 라우터·코드-인접
README를 문서-건강 우주(M5 지표 + GREENFIELD/HEALTHY posture)에서 제외하고, `gate.py`는
`docs/**`만 orphan 검사한다. codex 원문: *"This is not content loss, but it is a diagnostic
honesty regression unless 'nested routers and code-adjacent READMEs are intentionally outside
the document-health universe' is the explicit product contract."* — 이것이 실제로 의도된 제품
계약이므로, 이 ADR로 명문화해 지적을 해소한다.

## 결정

`disposition()`은 세 값(`router|tooling|content`)을 유지하되:

- **(DF2)** `AGENTS.md`/`CLAUDE.md`/`GEMINI.md`는 **어느 깊이든** `router`. 중첩 라우터는 그
  서브트리의 제자리 라우터다.
- **(DF1)** 부모 경로에 `docs` 세그먼트가 **없는** 중첩 `README.md`는 `tooling`. 단 부모에
  `docs`가 있으면(대소문자 무시 — `Docs/`·`DOCS/` 포함) `content`로 남아, **파묻힌 문서 인덱스는
  내용과 함께 이주한다.**

### 명시하는 계약 (이 ADR의 핵심)

`router`·`tooling`은 **"제자리 유지 + 도달성 면제"**를 뜻한다. 이들은:

1. 이동 대상이 아니다(`migrate.py`가 `disposition in ("router", "tooling")`이면 skip).
2. `gate`의 orphan 대상이 아니다(`gate.analyze`는 `docs/**/*.md`만 orphan 검사 — disposition을
   import조차 하지 않는다).
3. M5(`scorecard.outside_content`)와 posture의 `content` 분모에서도 빠진다.

이는 루트 `README.md`가 이미 받던 대우와 동일하며, 의도된 제품 계약이다. 즉 M5의 "파묻힘 0"은
**"중앙집중 대상 문서가 모두 docs/ 아래"**를 뜻하지, "레포의 모든 `.md`가 docs/ 아래"를 뜻하지
않는다. 코드-인접 README·중첩 라우터는 애초에 중앙집중 대상이 아니다.

## 내용 소실 0 유지 근거 (교차검증으로 확증)

재분류가 `content_oracle`의 불가침 불변식(내용 소실 0)을 깨지 않는지 호출 체인을 끝까지 확인:

- `content_oracle.collect`와 `per_file_accounting`은 disposition과 무관하게 트리 전체
  `rglob("*.md")`를 훑는다 — skip된 파일도 계정에 잡힌다.
- `migrate.apply_moves`(재배선 단계)는 skip된 파일까지 포함해 모든 `*.md`의 링크를 재작성한다.
- `gate.analyze`는 `disposition`을 import하지 않는다 — orphan 판정은 `docs/**`로 독립적이다.

따라서 재분류는 파일을 삭제·덮어쓰지 않는다. 오직 **이동 계획에서 제외**할 뿐이며, 파일은 원래
자리에서 그대로 존재하고 콘텐츠 오라클이 계속 계정한다.

## 수용한 트레이드오프

루트 라우터가 없는 레포에서 중첩 라우터·코드-인접 README가 `content` 분모에서 빠지면 posture가
`GREENFIELD`로 뒤집힐 수 있다(실제 콘텐츠 문서가 있어도 분모가 작아 보임). 그러나
`scorecard.rollup()`은 `if not router_present: return "F"`이므로 **등급(grade)은 F로 정직하게
유지**된다. posture는 조언 힌트일 뿐 등급에 영향을 주지 않고, scaffold는 append-only(비파괴)이므로
오탐 posture가 있어도 실제 피해로 이어지지 않는다.

## 검증

opus 리뷰어·architect·codex(적대적) 3자 독립 교차검증에서 [P1] 0건. codex GATE PASS.
