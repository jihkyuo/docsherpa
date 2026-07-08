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

- 테스트: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q` · `cd skills/doc-health/scripts && uv run --with pytest pytest -q`

## 문서 지도 <!-- docsherpa:map -->
- 라우팅·인덱스 → [문서 지도](docs/_map.md)
