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

상태·다음 할 일은 [FINDINGS.md](../../FINDINGS.md), 설계는 [DESIGN.md](../DESIGN.md).
