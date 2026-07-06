# 0013. PRD 1급 문서 타입 (product/ 온디맨드·라우팅 #2)

- 상태: 수락
- 날짜: 2026-07-06

## 맥락

`specs/`가 온디맨드 선례다 — 라우팅 룰엔 있으나 스캐폴드/인덱스엔 없다(폴더가 생길 때 등록).
PRD(제품 요구)는 제품의 "왜 만드나·누구에게·성공/수용 기준"으로, spec("무엇을")·ADR("왜 이
기술을 골랐나")과 **다른 도달성 트리**다. 그런데 지금 그 노드가 없어 PRD 성격의 문서는 flat
catch-all(룰 #5)로 새거나 spec/ADR에 눌러 담긴다. 이미 `plans/`처럼 상류 기획을 1급으로 관리하는
마당에 PRD만 뺄 이유가 없다.

## 결정

PRD를 **라우팅 #2(ADR 바로 아래)**로 1급화한다:

- `docs/product/*.md` **폴더 카테고리**(how-to/decisions처럼 여러 개 쌓이고 여러 개면 `_README`
  인덱스화). PRD = "왜 만드나·누구에게·성공/수용 기준".
- **온디맨드** — `product/` 폴더는 지금 만들지 않는다(specs/처럼 MVD). 첫 PRD 유입 때
  doc-reconcile이 생성·등록한다. 폴더 부재 시 인덱스에 넣으면 gate broken이므로 인덱스에도 지금
  안 넣는다.
- doc-reconcile에 PRD 갱신/신설 트리거를 추가한다.
- **PRD ≠ ADR** — PRD(제품의 왜)와 ADR(기술선택의 왜)는 다른 도달성 트리다. 구조적 결정이면
  PRD가 있어도 ADR을 병렬 신설·상호링크한다.

## 결과

- 라우팅 룰이 6개화된다(PRD 삽입 후 재번호). MVD 유지 — 투기적 빈 폴더 없음.
- 첫 PRD 생성 시 doc-reconcile closeout이 `product/_README.md`(리드 인덱스) +
  `_map.md` 인덱스에 제품 요구(PRD) → `docs/product/` 링크 줄을 함께 생성해야 orphan 0이 유지된다.
- 거부한 대안: PRD를 spec/ADR에 눌러 담기(도달성 트리 혼선) · `product/` 폴더를 지금 미리 생성
  (MVD 위반·빈 폴더 orphan).
