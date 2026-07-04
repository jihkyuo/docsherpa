# docsherpa M0 spike — FINDINGS

M0의 목적은 M1–M5 계획의 가정을 확정하는 것. 각 미지수의 결정을 여기 한 줄로 기록한다.

## 미지수 → 결정

- **① 설치 · 네임스페이스 (T1):** ✅ **확정.** 시퀀스: `/plugin marketplace add ~/Desktop/private/docsherpa`
  (로컬 경로) → `/plugin install docsherpa@docsherpa` (**user scope**) → `/docsherpa:hello` →
  `DOCSHERPA_NAMESPACE_OK`. 네임스페이스 = `/<plugin>:<skill>`(콜론). 컴포넌트는 설치 시 discover됨.
  - ⚠️ 함정: **VSCode extension 채팅에선 `/plugin` 불가** — 터미널 Claude Code에서 실행.
  - ⚠️ scope: project/local은 현재 repo `.claude/` 오염 → 테스트/개인용은 **user scope**.
- **② settings.json 포맷 (T2):** ✅ **실용 확정.** Claude Code settings는 문서상 표준 JSON →
  `merge_settings.py`의 load→dump 무손실. 병합 3-파트(보존·dedup·settings-not-local) 테스트 GREEN.
  - 남은 엣지: 사용자 settings에 주석(JSONC)이 실제로 있으면 comment-preserving 편집으로 승격(M3).
- **③ 훅-승인 게이트 (T3):** ✅ **D7 확정.** Claude Code **workspace trust 게이트**가 커밋된
  `.claude/settings.json` 훅을 신뢰 수락 전까지 차단(공식 문서 — security.md/permissions.md).
  워크스페이스 단위 1회 승인(per-hook 아님). 우리는 신뢰층 재발명 불요.
  - **보너스:** `.local.json`은 trust 스킵 → D2("settings.json, not local")가 이중으로 옳음.
  - **캐비엇(→M5 README):** `-p`(headless/CI)는 trust 스킵 → CI 사용자는 게이트 우회됨을 명시.
  - **설계 노트(→hook 명령):** trust 다이얼로그에 뜨는 hook 명령을 짧고 읽기 쉽게(무서운
    shell 메타문자 피함). 현 `cat .claude/doc-drift-prime.txt 2>/dev/null || true`는 수용 가능.
- **④ 마커 계약 (T4):** _(대기)_ — 언어-불문 마커 소비-검증 성립.

## 스펙 §14 이연 중 M0가 닫은 것

- ✅ settings 병합 코어(dedup 술어·파일 선택·기존 훅 보존) — `merge_settings.py`.
- ✅ 마커 계약 검증기 — `check_markers.py` (언어-불문, 번역 생존).
- ✅ 훅 신뢰 모델 — harness workspace-trust 게이트에 의존(D7).
- ✅ 마켓플레이스 설치·네임스페이스 형태 — 로컬 경로 + user scope + `/<plugin>:<skill>`.

## M1–M5로 넘길 남은 것 (M0 밖)

- CLAUDE.md 주입 엣지(BOM/frontmatter/다중 import) — M3.
- fixture의 구체 기대 산출물(hollow 방지 강화) — M2.
- provenance/no-placeholder 릴리스 게이트 — M5.
- settings JSONC comment-preservation(실제 필요 시) — M3.
- (검증됨) spike 중 STOP·재설계 트리거 **없음** — 순항. D7 확정으로 훅 설계 유지.

## M0 결론

**GREEN.** 가장 위험한 미지수 4개 전부 닫힘. 순수 코드 산출물(`merge_settings.py`·`check_markers.py`)은
테스트 통과. M1–M5 상세 계획을 이 FINDINGS 위에서 작성 가능.
