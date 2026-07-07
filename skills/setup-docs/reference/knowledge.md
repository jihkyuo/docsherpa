# setup-docs 도메인 지식 (on-demand 레퍼런스)

> 이 파일은 SKILL.md에서 필요할 때만 참조한다(force-load 아님). 진단·설계·설명 시 열어 읽는다.

**근거 정직성 (이 스킬의 철칙):** 아래 원칙은 근거등급을 단다 — 🟢권위 / 🟡판단 / 🔴열린질문.
진입 라우터·progressive disclosure·도달성만 🟢, 폴더화·축 선택은 🟡, 1홉·토픽vs타입은 🔴.
**표준인 척하지 마라.** 사용자에게 설명할 때도 이 등급을 보존한다.

---

## 5대 원칙

1. **Progressive disclosure**[🟢]: 진입 파일 얇게, 나머지 on-demand. 전부 미리 안 펼침. (Anthropic Claude Code/Skills, OpenAI AGENTS.md, long-context 저하 연구: Liu "lost in the middle" TACL'24, Chroma context rot)
2. **단일 정본 진입 라우터**[🟢]: `AGENTS.md` 정본(최광 호환) + `CLAUDE.md`=`@AGENTS.md`. 라우터 = 항시룰 + 린 인덱스 + 라우팅룰.
3. **도달성 불변식**[🟡]: 모든 문서가 진입→링크→도달(고아 0). **몇 홉인지는 무관**(*1홉 vs 멀티홉 최적* = 🔴).
4. **폴더 승격 규칙**[🟡]: "**함께 읽혀야 할 ≥2개**(co-change locality)"일 때만 `docs/<topic>/`. 디폴트 평면. 단순 같은 주제가 아니라 *서로 의존해 같이 봐야* 할 때. (*토픽 vs 타입* 디폴트 = 🔴)
5. **Diátaxis = 인덱스 렌즈, 폴더 아님**[🟡]: tutorial/how-to/reference/explanation은 커버리지 점검 사고틀이지 물리 폴더 아님. (사람 문서엔 권위, **Claude 공식 아님**)

---

## 문서 타입 4종 — 직교 분류 (질문어로 가른다)

| 타입 | 질문 | 핵심 | 산다 |
|---|---|---|---|
| **ADR** | **왜** 결정했나 | 근거, append-only | `decisions/` |
| **Rule/컨벤션** | **항상** 무엇을 | 선제 제약, 상시 로드 | `AGENTS.md` |
| **Troubleshooting** | 깨졌을 때 **무엇을** | **반응적 복구 — 절차(명령·진단·복구)** | `how-to/` |
| **Status/한계** | **지금** 뭐가 안 됐나 | 현황 | `ROADMAP`류 |

- ⚠️ **Troubleshooting은 절차여야 한다.** symptom→link뿐이면 Status로 붕괴 → **링크-전용 트러블슈팅 문서 만들지 마라.** 증상 alias는 주인 문서(한계 목록·개념 함정)에 넣고, `how-to/`는 실제 절차가 생길 때 졸업.
- **"Troubleshooting → Rule 졸업"** 은 *반복 + 비쌈 + 예방가능* 3조건일 때만(아니면 사후 서사).

---

## 보조 관례[🟢]

- **ADR**: 결정당 1파일 `decisions/NNNN-*.md` + 인덱스/로그 + 템플릿, append-only (Nygard·Fowler).
- **docs-as-code + MVD/bonsai**: repo 내 markdown, 코드와 같은 커밋, 얇게·자주 쳐냄, 투기 구조 금지 (Google eng-practices, Write the Docs).
- **placeholder는 싸다**: 빈 문서는 읽히기 전까지 토큰 0 → 명확히 표시한(`PLACEHOLDER`) 예약 자리는 MVD 안 깸.

---

## 안티패턴 (피한다)

타입 폴더로 결합 서브시스템 흩기 · 투기적 빈 폴더(dead-doc) · 인덱스 누락(고아) · 링크 타겟만 고치고 라벨은 옛 파일명 · 진입 파일 비대화(룰 무시됨) · 재배선 회피용 레거시 통파일 잔존 · 링크-전용 troubleshooting(Status 복제) · **비-markdown 링크 라우터**(인덱스가 평문 화살표·백틱 경로라 gate 미인식 → 트리 멀쩡해도 orphan).

---

## 진단 휴리스틱 (Phase 0 — 상태 판정)

- **진입 라우터 유무:** AGENTS.md 또는 CLAUDE.md(@import) 존재?
- **gate.py 결과:** broken·orphan 수.
- **안티패턴 적출:**
  - 타입폴더로 결합 흩기: `docs/<type>/`(guides·tutorials 등)에 서로 의존하는 문서가 흩어짐
  - 진입파일 비대화: 진입 파일이 항시룰을 넘어 상세까지 담음
  - 링크-전용 troubleshooting: 절차 없이 symptom→link만 (Status 복제)
  - ADR/how-to 오분류: "왜"문서가 decisions/ 밖, "복구절차"가 how-to/ 밖
  - 비-markdown 링크 라우터: 인덱스가 평문 화살표(`→ docs/x.md`)·백틱 경로라 gate가 링크로 미인식 → 트리 멀쩡해도 orphan
- **상태 결론:**
  - GREENFIELD: 라우터 없음 + docs 최소
  - HEALTHY: 라우터 있음 + gate PASS + 안티패턴 없음
  - MESSY: docs 있음 + (gate FAIL 또는 안티패턴 ≥1). **경량/무거움 2차선**은 SKILL.md — 옮길 문서가 없으면(링크 포맷·인덱스만) 경량, 실제 이동 필요면 무거움(ADR 0014)
