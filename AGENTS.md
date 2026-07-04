# docsherpa — 에이전트 진입 라우터

> 진입 라우터. 상세는 docs/를 필요할 때만 읽는다. (docsherpa는 자기 구조를 스스로 dogfood 한다.)

## 정체성 (North Star — 절대 흔들리면 안 됨)

docsherpa는 **비파괴적 보조 도구**다. 아래 셋이 정체성이고, 하나라도 흔들리는 변경은 **방향 이탈**이다:

1. **비파괴 마이그레이션.** 사용자가 각자 레포에서 열심히 갈고닦은 **중요한 앵커·지점을 잃지 않게**
   하면서, 중구난방 문서 아키텍처를 베스트-프랙티스 구조(얇은 진입 라우터 + 도달성 불변식)로
   **마이그레이션**해 준다. docsherpa는 주인이 아니라 **보조**다.
2. **불가침 불변식 — 내용 소실 0.** 이 마이그레이션에서 사용자의 **기존 문서 내용은 절대 누락·소실되지
   않는다.** 이게 깨지는 순간 docsherpa 프로젝트는 **끝장난다.** (`content_oracle.py` 미분류 세그먼트 →
   FAIL · `gate.py` 도달성 100% · scaffold "없는 것만 생성·append-only·기존 안 덮음"이 이걸 강제한다.)
3. **자가-성장.** 거기에 **문서 자가-성장 스킬(doc-reconcile)**을 탑재해, 사용자가 신경 쓰지 않아도
   레포 문서가 변경을 따라 **자발적으로 갱신·추가되며 성장**한다.

**따름 원칙:** 사용자 repo에 적용할 때 내용·앵커 소실 0(§7.5 앵커 재특화로 사용자 고유 앵커 보존). 공개
플러그인 정본은 도메인 리터럴 0(누출 방지). 설계·근거 전체는 [docs/DESIGN.md](docs/DESIGN.md).

## 항시 룰

- 플러그인 = Claude Code. 스킬은 `skills/`(setup-docs·doc-reconcile), 테스트는 `skills/setup-docs/scripts/`.
- 정본 doc-reconcile은 프로젝트 리터럴 0(가드 `test_doc_reconcile_portable.py`가 강제).
- 커밋마다 push(origin/main). 위험·핵심 설계는 `/codex` + `architect` 교차검증.

## 명령어

- 테스트: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`

## 먼저 읽기 (문서 인덱스 — 진입점만, 린) <!-- docsherpa:index -->

- 설계·전체 근거 → [docs/DESIGN.md](docs/DESIGN.md)
- 결정 기록(ADR) → [docs/decisions/README.md](docs/decisions/README.md)
- 상태·진행·다음 세션 시작점 → [FINDINGS.md](FINDINGS.md)
- 마일스톤 실행 계획(M0~M4) → [docs/plans/](docs/plans/)
- 작업 가이드 → [docs/how-to/](docs/how-to/)

## 문서 라우팅 룰 (새 문서가 어디로) <!-- docsherpa:routing -->

분류 순서대로 판정(위에서 먼저 맞는 것):
1. 구조적 결정(왜) → docs/decisions/NNNN-*.md (_template 복사) + README 로그 추가
2. 절차/복구(어떻게) → docs/how-to/*.md (3개↑면 _README 인덱스화)
3. 기능 스펙(무엇을) → docs/specs/<feature>/ + plans/
4. 함께 읽혀야 할 문서 ≥2개(co-change) → docs/<topic>/ 승격, 리드 문서가 인덱스
5. 그 외 단일 reference/explanation → docs/ 평면 [디폴트]

불변식: 새 문서는 반드시 위 인덱스에 등록(고아 방지) → broken=0·orphan=0 확인
