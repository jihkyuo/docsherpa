# 0002. target repo에 커밋 스캐폴드 (self-contained)

- 상태: 수락
- 날짜: 2026-07-04

## 맥락

성장 루프(doc-reconcile + prime + 훅)를 어떻게 배치할지 두 선택지가 있었다.
A) 순수 플러그인으로만 제공. B) target repo에 커밋되는 스캐폴드로 배치.

## 결정

**B — target repo에 커밋 스캐폴드**를 택한다. doc-reconcile·prime·훅을 target repo의
`.claude/`에 커밋해 self-contained로 만든다.

## 결과

- 좋음: public repo라 collaborator가 플러그인을 설치하지 않아도 커밋된 스캐폴드로 규율을 획득한다.
- 거부한 대안: A) 순수 플러그인 제공 — 클론한 사람이 플러그인이 없으면 규율을 잃는다.
