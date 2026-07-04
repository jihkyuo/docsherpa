# 0009. doc-reconcile 트리거를 SessionStart + 수동으로 좁힘

- 상태: 수락
- 날짜: 2026-07-04

## 맥락

원본 doc-reconcile이 트리거로 "pre-commit docs-impact 게이트가 커밋을 막았을 때"를 광고했으나,
**그 게이트는 이 repo에도 없다**(의도적 보류). 광고하면 이 phantom 게이트가 소비자 repo로
복제된다(architect 최대 발견).

## 결정

doc-reconcile 트리거를 **SessionStart prime + 수동 호출**로 좁힌다. "pre-commit docs-impact
게이트" 언급을 제거한다.

## 결과

- 좋음: 미구현 phantom 게이트가 소비자로 복제되는 것을 막는다.
- 거부한 대안: 게이트 구현 — YAGNI이며, 보류 결정을 뒤집는 것.
