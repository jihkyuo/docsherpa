# 0005. 훅은 target repo에만 산다

- 상태: 수락
- 날짜: 2026-07-04

## 맥락

SessionStart prime 훅을 어디에 둘지 정해야 했다. user-scope 플러그인 훅으로 두면 문서가 없는
repo에서도 prime이 전역 발동한다.

## 결정

훅은 **target repo에만** 산다. 플러그인은 훅 *템플릿*만 담고, active 훅은 스캐폴드된 target의
`.claude/settings.json`에만 존재한다.

## 결과

- 좋음: 문서 아키텍처가 없는 repo에서 prime이 오발동하는 것을 방지한다.
- 거부한 대안: user-scope 플러그인 훅 — 모든 repo에서 전역 발동한다.
