# 0017. Troubleshooting을 1급 문서 타입으로 승격

- 상태: 수락
- 날짜: 2026-07-09
- 관련: [0013](0013-prd-first-class-doc-type.md)(PRD 1급 선례) · [doc-type-templates 트랙](../specs/doc-type-templates/design.md)

## 맥락

vd-front dogfood 진단서 리뷰에서 실증: 분류 type 어휘(`ADR·spec·how-to·reference·PRD·legacy`)에
**`troubleshooting` 타입 자체가 없었다.** `reference/knowledge.md`(문서타입표 L27, 가드 L30)가
Troubleshooting을 "반응적 복구 절차 → `how-to/`"로 접어, 트러블슈팅 문서가 how-to로 분류돼
**가이드와 식별 불가**하고 전용 홈이 없었다. 아티팩트 범례가 이 사실을 은폐(자기설명 실패).

## 결정 (B안 — 1급 승격)

1. **분류 어휘에 `troubleshooting` 추가** — doc-health 분류/scorecard가 how-to 하위변종이 아닌
   독립 type으로 식별. 질문어 = "깨졌을 때 무엇을·어떻게 복구".
2. **전용 홈 = `docs/troubleshooting/`** — 완전 독립 최상위 폴더(how-to 하위 아님). PRD/specs처럼
   온디맨드(첫 troubleshooting 문서 유입 시 `register`가 폴더 인덱스 생성).
3. **배정** — `migrate._TYPE_DEST["troubleshooting"] = "docs/troubleshooting"`. render 타입색·범례·
   트리에 troubleshooting 추가(6→7색, `--fail-ink` 재사용, AA on `--bg` 통과).
4. **진단 차원** — J1이 트러블슈팅 절차성을 채점(link-only면 fail).

## 승계하는 가드레일 (설계 정신 보존)

트러블슈팅은 **진짜 절차**(명령·진단·복구)여야 한다. `symptom→link`만인 **링크-전용 트러블슈팅
금지**(Status 복제·부패). 증상 alias는 주인 문서(한계·개념 함정)에. 1급 승격 후에도 유지.

## Supersede

- `reference/knowledge.md` L17(Diátaxis=폴더 아님) — troubleshooting은 **예외**로 식별 필요.
- `reference/knowledge.md` L27(타입표 how-to/ 매핑) — 산다 열 `how-to/` → `troubleshooting/`.
- `reference/knowledge.md` L30(가드) — 유지하되 홈이 `troubleshooting/`로 이동.

기존 문서 내용은 삭제하지 않는다 — stance 주석으로 supersede만 표기(append-only 정신).

## 결과

- 트러블슈팅이 가이드와 색·폴더로 구별됨(자기설명 회복).
- link-only 가드 유지로 Status 복제 부패 방지.
