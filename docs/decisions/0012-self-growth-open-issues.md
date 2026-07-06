# 0012. 자가성장 열린 이슈 처리 (F11–F15)

- 상태: 수락
- 날짜: 2026-07-06

## 맥락

doc-reconcile 최신화 재설계(`plans/2026-07-05-doc-reconcile-freshness-redesign.md`) §10 자가감사가
연 F11–F15는 지금까지 미해결이었다. N11(맵 중추 문서)이 완결된 뒤 각 이슈의 실제 코드 상태를
확인하니, **F13·F14·F15·F11은 아직 존재하지 않는 기능**(N4 auto-UPDATE·N9 freeze·§3.2 refresh)에
대한 설계 주의사항이라 고칠 코드가 없고, **F12만 현재 구동 중인 doc-reconcile의 실제 갭**이었다.

## 결정

**F12(룰#4 死 — 평면-only 성장) = 지금 해결.** doc-reconcile 판정에 세 번째 질문(룰#4 트리거)을
추가: 평면 `docs/`에 같은 주제·co-change 문서가 실제로 ≥2개 뭉치면 `docs/<topic>/` 승격을
**비블로킹 제안**한다. **doc-reconcile은 파일을 옮기지 않는다**(무프롬프트 루틴에 파일 이동을 넣으면
North Star 위험) — 실제 이동·링크 리라이트는 setup-docs 폴더 승격(MESSY two-oracle, content_oracle-safe·
승인)이 담당. 이로써 "자라긴 자라는데 뭉치질 못하는" 갭을 닫되 이동 안전은 기존 기계에 위임한다.

**F11·F13·F14·F15 = 미구축 기능의 제약으로 결정·기록**(코드 없으니 지금 빌드 안 함, 실사용이
필요를 보이면 그때 아래 제약대로 구축):

- **F11 (동결 예외):** 동결 판정의 인덱스 예외는 헤딩 휴리스틱이 아니라 **`docsherpa:index` 마커
  기준**(N11 §3.8이 이미 강제). 미구축 N9 freeze도 마커 기준으로 짓는다.
- **F13 (UPDATE 앵커):** auto-UPDATE(N4) 구축 시 값("3")이 아니라 **심볼 앵커("MAX_RETRY")로 grep**한다
  (값 grep은 무의미).
- **F14 (브랜드 누출):** N9 freeze 구축 시 사용자 문서에 `docsherpa_frozen` 같은 **브랜드 키 주입 금지** —
  generic 메커니즘(마커 또는 non-brand frontmatter)으로. [0010](0010-skill-names-doc-family.md)(스킬명
  브랜드 거부)과 정합.
- **F15 (자동 커밋 posture) — 구축됨(loop-refresh):** `refresh_loop`은 **커밋을 하지 않는다**(파일만
  갱신, 트리거가 에이전트 호출이라 에이전트가 끝 요약으로 알림). 무프롬프트 커밋 0으로 "보조 not 주인"을
  지킨다 — 애초 기록한 "clean-tree+별도 커밋"보다 강한 posture로 정제.

## 결과

- 좋음: 자가성장이 "추가"뿐 아니라 "묶기"(구조화)까지 트리거 — 평면 무한증식 방지. 이동 안전은
  content_oracle에 위임(무프롬프트 파일 이동 없음).
- YAGNI: 미구축 기능(N4·N9·refresh)은 실사용 판단 전까지 빌드하지 않되, 제약을 못박아 미래 실수 방지.
  Slice C 유보([0011](0011-map-spine-document.md))와 같은 논리.
- 거부한 대안: F13·F14·F15를 위해 지금 N4·N9·refresh를 빌드(미승인 재설계·YAGNI) · doc-reconcile이
  파일을 직접 이동(무프롬프트 루틴에 내용-위험 이동 투입).
- 재설계 §10의 F11–F15는 이 ADR로 disposition됨.
