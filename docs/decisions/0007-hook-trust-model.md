# 0007. 훅 신뢰 모델 — harness 승인 게이트에 의존

- 상태: 수락
- 날짜: 2026-07-04

## 맥락

커밋된 SessionStart 훅의 신뢰·보안이 문제였다. 설치자 opt-in만으로는 그 repo를 클론한
collaborator를 보호하지 못한다(codex #4).

## 결정

- **설치자:** opt-in + inspect-before-write + easy-disable.
- **collaborator:** 클론한 repo의 커밋된 훅은 **Claude Code 자체 훅-승인 게이트**(첫 실행 전
  승인 요청)가 safe-by-default를 제공한다 — 우리는 신뢰층을 재발명하지 않는다(M0에서 실검증).
- prime은 커밋된 신뢰 경계임을 명시한다.

## 결과

- 좋음: collaborator 보호를 harness가 담당하므로 우리가 신뢰층을 재발명할 필요가 없다.
- 거부한 대안: 조용히 훅 설치 / 자체 신뢰층 재발명.
