# 마일스톤 실행 계획 (M0~M4)

docsherpa는 spike-first로 진행한다(가장 위험한 미지수를 껍데기 전에 증명). 재-시퀀싱 순서:
M1 → M3 → M2 → M4 → M5. 각 계획은 writing-plans로 작성하고 RED-first로 실행했다.

| # | 계획 | 요지 |
|---|------|------|
| M0 | [M0-spike.md](M0-spike.md) | 4 미지수 실증(설치·네임스페이스·settings 병합·훅 신뢰·마커 계약) |
| M1 | [M1-doc-reconcile-portability.md](M1-doc-reconcile-portability.md) | doc-reconcile 이식화(phantom 제거·마커 참조·앵커 범용화) |
| M2 | [M2-portability-fixtures.md](M2-portability-fixtures.md) | scaffold.py 오케스트레이터 + 4종 이식성 fixture |
| M3 | [M3-setup-docs-installer.md](M3-setup-docs-installer.md) | setup-docs 설치자(마커 삽입·CLAUDE.md 주입·settings 병합·gate 마커) |
| M4 | [M4-dogfooding.md](M4-dogfooding.md) | second-brain 독푸딩(behavioral parity + 커터오버 런북) |

## 재설계 계획

- [2026-07-05-doc-reconcile-freshness-redesign.md](2026-07-05-doc-reconcile-freshness-redesign.md) — doc-reconcile 최신화·유연화·자가성장 재설계(sidecar/refresh·2-tool·정직화). 리뷰 대기(rev10, N11 맵 중추 문서 채택).
- [2026-07-06-n11-p1-contract-foundation.md](2026-07-06-n11-p1-contract-foundation.md) — N11 Plan 1: 계약 단일 소스(contract.py) + gate 루트 일반화 + 단일-home locator (구현 토대).
- [2026-07-06-n11-p2-map-scaffold.md](2026-07-06-n11-p2-map-scaffold.md) — N11 Plan 2(Slice A): 그린필드 맵 생성 + 진입파일 맵 링크(spine 계약, 마이그레이션은 후속).
- [2026-07-06-n11-p3-inline-map-migration.md](2026-07-06-n11-p3-inline-map-migration.md) — N11 Plan 3(Slice B): 인라인→맵 비파괴 마이그레이션(content_oracle 무손실) + docsherpa 자가적용.
- [2026-07-06-loop-refresh.md](2026-07-06-loop-refresh.md) — 설치본 doc-reconcile 자동 동기(up-only refresh, 스탬프 해시·provenance·로컬편집 보존·무프롬프트 커밋 0).

## 하드닝 루프 (진행 중)

- [2026-07-07-setup-docs-hardening-loop.md](2026-07-07-setup-docs-hardening-loop.md) — setup-docs를 실제 프로젝트에 독푸딩하며 하드닝하는 반복 루프의 **방법론·현재 상태·라운드 이력**. 다음 세션 진입점.

## 진단-주도 마이그레이션 (재설계 구현 — 스펙 [design.md](../specs/diagnosis-driven-migration/design.md))

- [2026-07-07-render-report-renderer.md](2026-07-07-render-report-renderer.md) — 증분 1: `render_report` 동결 렌더러(데이터 모델 → 자기완결 HTML 아티팩트, 대비/구조/이스케이프/픽스처 테스트). 후속: `doc-health` 스킬 → setup-docs 리팩터 → 마이그레이션 실행.
- [2026-07-08-doc-health.md](2026-07-08-doc-health.md) — 증분 2: `doc-health` 진단 생산자 스킬(전체-repo 탐색 + 9차원 채점 → render_report 부분 데이터 모델). 스펙 [doc-health.md](../specs/diagnosis-driven-migration/doc-health.md). 후속: setup-docs Phase 0·4 배선.
- [2026-07-08-setup-pipeline-inc3.md](2026-07-08-setup-pipeline-inc3.md) — 증분 3: setup-docs 파이프라인(Phase 0·1·2 진단→목표트리→검증된 계획→승인). 신규 `migrate.py`(배정·relink·스크래치 자체검증) + 재사용. 스펙 [setup-pipeline.md](../specs/diagnosis-driven-migration/setup-pipeline.md). 후속: 증분 4(Phase 3·4 실행·결과).
- [2026-07-09-increment4-landing-migration.md](2026-07-09-increment4-landing-migration.md) — 증분 4: 승인된 계획의 실제 랜딩(Phase 3 worktree 격리·검증트리=커밋트리) → 재진단(Phase 4). 신규 `land_migration`·`register_all`·링크 오라클(new/preexisting/anchor)·per-file 회계. 스펙 [landing-migration.md](../specs/diagnosis-driven-migration/landing-migration.md)(§0b R1~R9 교차검증). dogfood=vd-front.

상태·다음 할 일은 [FINDINGS.md](../../FINDINGS.md), 설계는 [DESIGN.md](../DESIGN.md).
