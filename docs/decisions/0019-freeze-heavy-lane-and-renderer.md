# 0019. 무거운 차선·아티팩트 렌더러 기능 동결(freeze) — 자가성장으로 에너지 이전

- 상태: 수락
- 날짜: 2026-07-09
- 관련: [0020](0020-drop-letter-grade.md)(동결의 첫 집행) · [0021](0021-parity-experiment-control-group.md)(동결이 비운 자리에 갈 것)

## 맥락

220커밋 시점에 세르파와 원형 프로토타입(second-brain)을 나란히 놓고 측정했다.

- **프로토타입의 자가성장 루프 전체 = 3파일 124줄, 파이썬 0줄, 테스트 0개.** 그리고 매일 작동한다.
  (SessionStart 훅 6줄 + `doc-drift-prime.txt` 7줄 + `doc-reconcile/SKILL.md` 111줄 + 손으로 쓴 라우터)
- 세르파 = 220커밋 · 프로덕션 파이썬 ~2,300줄 · 테스트 195개. 그중 **체감 가치에 기여하는 코드는 0줄**이다.
  전부 *마이그레이션 약속*의 대가다.
- 파일별 커밋 touch: `migrate.py` 29 · `test_migrate.py` 23 · `test_render_report.py` 21 ·
  `render_report.py` 19 · … · **`doc-reconcile/SKILL.md` 9.**
- `render_report.py` 562줄 중 **252줄이 CSS**이며 소스 주석이 "변경 금지"라 못박고 있다. 최근 커밋에
  `🎨 fix(render): 타입색 on --bg AA 가드 3쌍`이 있다.
- **`troubleshooting`이라는 폴더 이름 하나를 1급 타입으로 올리는 데 8커밋·8파일이 들었다**
  (`migrate.py` → `render_report.py` → `scorecard.py` → `scaffold.py`(`_MAP_DOC`) → `SKILL.md` →
  `knowledge.md` → `doc-reconcile/SKILL.md` → ADR 0017). 문서 분류학이 코드 **4곳**에 하드코딩돼 있다:
  `migrate._TYPE_GROUP` · `render_report._SCAFFOLD_TYPECLS`/`_TYPE_GROUP` · `scorecard` 타입 어휘 ·
  `scaffold._MAP_DOC`. 프로토타입에서 같은 작업은 라우터 산문 한 줄 추가이고 코드는 0줄이다.
- 195개 테스트 중 `doc-reconcile`을 건드리는 것은 `test_doc_reconcile_portable.py` 하나이고, 내용은
  **SKILL.md 텍스트의 금지어 grep**이다. [DESIGN.md](../DESIGN.md) §10.3이 약속한 **행동 parity 테스트는
  끝내 작성되지 않았다.** 즉 제품의 유일한 가치 명제에 행동 검증이 0개이고, 리포트의 색 대비에는 341줄이 있다.

opus 리뷰어와 `/codex`(적대적 프롬프트, 반박 지시)가 **독립적으로 같은 [P1]** 을 지목했다 —
*"Zero behavioral tests for doc-reconcile is the biggest strategic risk. Using 'prose cannot be
unit-tested' to justify zero behavioral tests is a cop-out."* FINDINGS.md의 자가진단도 같다:
*"우리는 이 교훈을 이미 적어놓고 어겼다 — 판단 작업을 코드로 박제하지 말 것."*

## 결정

**무거운 차선(`migrate.py` 재배치 파이프라인)과 아티팩트 렌더러(`render_report.py`)·`doc-health`
채점기를 기능 동결한다.** 삭제가 아니다 — 이들은 작동하고 dogfood로 증명됐다(vd-front 랜딩 성공).

### 금지 (동결 대상)

1. **새 문서 타입 추가 금지.** `troubleshooting` 이후 타입 어휘는 닫혔다.
2. **새 타입색·새 CSS·새 접근성 가드 금지.** `TEMPLATE_CSS`는 정본으로 동결.
3. **새 진단 차원(M·J) 추가 금지.** 9차원에서 닫혔다.
4. **새 배정 휴리스틱·disposition 클래스 추가 금지.**

### 허용

- 회귀·정합성 버그 픽스(RED-first).
- **삭제**(동결은 성장을 막는 것이지 축소를 막지 않는다 — ADR 0020이 첫 사례).
- 불가침 불변식(내용 소실 0)을 강화하는 오라클 작업.

## 결과

- **8파일 연쇄가 오늘 멈춘다.** 분류학이 자라지 않으면 결합이 비용을 청구하지 않는다.
- 정체성 기둥은 하나도 손대지 않는다: 프로젝트별 설치형 성장 스킬 · 버전관리 업데이트 ·
  진단→승인→마이그레이션→결과 파이프라인. 전부 그대로 산다.
- **이연한 부채: writer→judge 역전.** 옳은 방향이지만 지금이 아니다. `verify_migration`의 불가침
  불변식은 `base_keys - cur_keys`(두 디렉터리 스캔)라 *누가 옮겼는지와 무관*하므로, 원리적으로 mover는
  코드일 필요가 없다. 그러나 codex 교차검증이 세 구멍을 확증했다: ①`content_oracle.normalize()`가
  링크 URL을 지워 **"존재하지만 엉뚱한 문서"를 가리키는 링크**를 통과시킨다 ②세그먼트 dedup 때문에
  **같은 내용 파일 둘 중 하나가 통째로 사라져도** `unaccounted=0`이다(그래서 `per_file_accounting`이
  존재한다) ③`.mdx`·이미지·에셋을 스캔하지 않는다. 지금 mover를 지우면 **불가침 불변식이 약해진다.**
  올바른 순서: 오라클 하드닝 → `verify_candidate(base, cand)`(move_plan 불필요) → 검증된 트리 랜딩 →
  **그 다음에** mover 삭제. 동결이 물면 이 부채는 이자를 내지 않는다.

## 수용한 트레이드오프

무거운 차선은 오늘 상태로 얼어붙는다. 사용자 레포가 우리가 예상 못 한 문서 타입을 갖고 있으면 그
문서는 평면 `docs/`로 간다(라우팅 룰 #6, 디폴트). 그 편이 8파일을 또 건드리는 것보다 싸다.

## 검증

- 동결 자체는 코드가 강제하지 않는다(정책 결정). 위반은 이 ADR을 supersede해야 한다.
- 근거 수치는 `git log --name-only --pretty=format: | sort | uniq -c | sort -rn`로 재현 가능.
