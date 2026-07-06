# 결정 기록 (ADR)

구조적 결정은 결정당 1파일 `NNNN-*.md`로 남긴다(append-only). 새 결정은
[`_template.md`](_template.md)를 복사해 만들고 아래 표에 한 줄 추가한다.
전체 설계 맥락은 [DESIGN.md](../DESIGN.md) — 이 로그가 결정의 **정본**이다.

| # | 결정 | 상태 | 날짜 |
|---|------|------|------|
| [0001](0001-single-plugin-repo-self-host.md) | 단일-플러그인 repo + marketplace self-host | 수락 | 2026-07-04 |
| [0002](0002-committed-scaffold-in-target.md) | target repo에 커밋 스캐폴드(self-contained) | 수락 | 2026-07-04 |
| [0003](0003-dogfooding-single-source.md) | 독푸딩 — 플러그인 = 단일 원본 | 수락 | 2026-07-04 |
| [0004](0004-doc-reconcile-one-file-two-uses.md) | doc-reconcile = 한 파일, 두 쓰임 | 수락 | 2026-07-04 |
| [0005](0005-hooks-live-in-target-only.md) | 훅은 target repo에만 산다 | 수락 | 2026-07-04 |
| [0006](0006-name-docsherpa.md) | 이름 = docsherpa | 수락 | 2026-07-04 |
| [0007](0007-hook-trust-model.md) | 훅 신뢰 모델(harness 승인 게이트 의존) | 수락 | 2026-07-04 |
| [0008](0008-language-agnostic-markers.md) | 섹션명 계약 = 언어-불문 마커 | 수락 | 2026-07-04 |
| [0009](0009-narrow-doc-reconcile-triggers.md) | doc-reconcile 트리거를 SessionStart+수동으로 좁힘 | 수락 | 2026-07-04 |
| [0010](0010-skill-names-doc-family.md) | 스킬 이름 = `doc-*` 패밀리(`doc-setup`+`doc-reconcile`, 구현 이연) | 수락 | 2026-07-05 |
| [0011](0011-map-spine-document.md) | 맵 중추 문서 — routing·index를 진입파일 밖 `docs/_map.md`로(N8 supersede) | 수락 | 2026-07-06 |
