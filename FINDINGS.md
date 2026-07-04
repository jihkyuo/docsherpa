# docsherpa M0 spike — FINDINGS

M0의 목적은 M1–M5 계획의 가정을 확정하는 것. 각 미지수의 결정을 여기 한 줄로 기록한다.

## 미지수 → 결정

- **① 설치 · 네임스페이스 (T1):** _(대기)_ — 정확한 설치 커맨드 시퀀스 · `/docsherpa:hello` 접두사 형태.
- **② settings.json 포맷 (T2):** _(대기)_ — 표준 JSON인가 JSONC인가 → 병합 포맷 전략.
- **③ 훅-승인 게이트 (T3):** ✅ **D7 확정.** Claude Code **workspace trust 게이트**가 커밋된
  `.claude/settings.json` 훅을 신뢰 수락 전까지 차단(공식 문서 — security.md/permissions.md).
  워크스페이스 단위 1회 승인(per-hook 아님). 우리는 신뢰층 재발명 불요.
  - **보너스:** `.local.json`은 trust 스킵 → D2("settings.json, not local")가 이중으로 옳음.
  - **캐비엇(→M5 README):** `-p`(headless/CI)는 trust 스킵 → CI 사용자는 게이트 우회됨을 명시.
  - **설계 노트(→hook 명령):** trust 다이얼로그에 뜨는 hook 명령을 짧고 읽기 쉽게(무서운
    shell 메타문자 피함). 현 `cat .claude/doc-drift-prime.txt 2>/dev/null || true`는 수용 가능.
- **④ 마커 계약 (T4):** _(대기)_ — 언어-불문 마커 소비-검증 성립.

## 스펙 §14 이연 중 M0가 닫은 것

_(T5에서 종합)_
