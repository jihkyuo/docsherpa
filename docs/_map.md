# 문서 지도 (라우팅·인덱스)

> 진입 라우터가 이 파일을 가리킨다. (인라인 마커에서 이관됨.)

## 먼저 읽기 (문서 인덱스 — 진입점만, 린) <!-- docsherpa:index -->

- 설계·전체 근거 → [docs/DESIGN.md](DESIGN.md)
- 결정 기록(ADR) → [docs/decisions/README.md](decisions/README.md)
- 제품 요구(PRD) → [docs/product/](product/)
- 상태·진행·다음 세션 시작점 → [FINDINGS.md](../FINDINGS.md)
- 마일스톤 실행 계획(M0~M4) → [docs/plans/](plans/)
- 기능 스펙(무엇을) → [docs/specs/](specs/)
- 작업 가이드 → [docs/how-to/](how-to/)

## 문서 라우팅 룰 (새 문서가 어디로) <!-- docsherpa:routing -->

분류 순서대로 판정(위에서 먼저 맞는 것):
1. 구조적 결정(왜) → docs/decisions/NNNN-*.md (_template 복사) + README 로그 추가
2. 제품 요구(왜 만드나·누구에게·성공/수용 기준) → docs/product/*.md (여러 개면 _README 인덱스화)
3. 절차/복구(어떻게) → docs/how-to/*.md (3개↑면 _README 인덱스화)
4. 기능 스펙(무엇을) → docs/specs/<feature>/ + plans/
5. 함께 읽혀야 할 문서 ≥2개(co-change) → docs/<topic>/ 승격, 리드 문서가 인덱스
6. 그 외 단일 reference/explanation → docs/ 평면 [디폴트]
※ PRD(제품의 왜)와 ADR(기술선택의 왜)는 다른 도달성 트리 — 구조적 결정은 PRD가 있어도 ADR 병렬 신설.

불변식: 새 문서는 반드시 위 인덱스에 등록(고아 방지) → broken=0·orphan=0 확인
