# docsherpa — STATUS & FINDINGS

## 🔜 다음 세션 시작점 (여기부터)

- **⛔ 먼저 읽어라 — 대기 중인 사용자 결정 2개(이게 없으면 진행 불가, 2026-07-09):**
  ```
  결정 A) gate.py --hook 을 배선할까, 지울까?   ← 지금 아무도 안 부르는 코드가 떠 있다
     (가) 0단계만: --hook 삭제. doc-reconcile 산문에 "검사 방법"만 적는다. 새 메커니즘 0.
     (나) 1단계까지: --hook 유지 + 커밋된 SessionStart 훅 + gate.py·contract.py를 target에 복사.
  결정 B) PR 열까? (브랜치 main 대비 38커밋, 최종리뷰 READY TO MERGE, 사용자가 "보류" 지시 중)
  ```
  **결정 A의 진짜 트레이드오프는 성능이 아니라 가시성·승인이다(실측으로 확정):**
  초대 안 한 레포에서 훅 비용 = **44ms**(그중 36ms는 python 기동, 우리 코드는 8ms) + **출력 침묵**.
  즉 "무겁다"는 논거는 죽었다. 진짜 차이는 **ADR 0007**: *커밋된* 훅은 diff에 보이고 워크스페이스마다
  사용자 승인 게이트를 타지만, **플러그인 훅은 설치 때 한 번 승인하면 모든 레포에서 보이지 않게 돈다.**
  "보조"의 실체 = 코드 줄 수가 아니라 **사용자가 보고 승인할 수 있느냐.**
  **(가)를 권한 이유:** doc-reconcile §6이 이미 "끝에 broken=0 · orphan=0 확인"이라 **시키는데
  검사기를 어디서 어떻게 부르는지 안 알려준다** — 명령은 있고 도구가 없다. 산문 몇 줄로 닫힌다.
  이 프로젝트의 병이 "메커니즘 과잉 생산"이므로 새 메커니즘 없이 먼저 닫고, 안 먹히면 (나)로.
- **🧭 전략 정렬 진단(2026-07-09, 사용자와 합의) — 다음 세션은 이 렌즈로 판단하라:**
  질문이었다: *"우리가 AI를 못 믿어 활동성을 제약하는가? 유명 스킬도 이렇게 복잡한가?"*
  **측정 결과 전제가 틀렸다.** gstack = 코드 **176,657줄**(우리 2,310줄의 75배), `gstack/spec` SKILL.md는
  **2,359줄**(우리 setup-docs 354줄). superpowers/brainstorming엔 723줄 node 서버가 있다.
  → 유명 스킬이 "확률적으로 안 느껴지는" 건 산문 덕이 아니라 **코드 덕**이다. 확률성을 없애는 건 코드다.
  **우리 코드 2,310줄의 성격:** 🛡️안전 불변식(오라클·게이트) 312줄(13%) · 🔧기계적 실행 1,200줄(52%) ·
  🎨렌더러 562줄(24%) · ⚖️**판단을 코드로 박제**(scorecard 임계값·등급) 236줄(10%).
  분류·feature명·topic·J1~J4는 **전부 AI 판단이고 코드가 안 건드린다** → "AI 제약" 진단은 틀렸다.
  **문제는 복잡도가 아니라 복잡도의 위치다.** 정체성 3축 중 비파괴·내용소실0은 **완성·실전 증명**.
  자가성장(doc-reconcile)은 **코드 0 · 테스트 0 · 산문 136줄로 방치**. 그런데 최근 40커밋의 에너지는
  렌더러(263+155줄)와 타입 분류학(계획서 578줄)에 갔다. **렌더러+테스트 903줄 = 오라클 312줄의 3배**이고,
  최근 세 세션의 버그(D4·D6·C1/C2·DF5)가 **전부 거기서** 나왔다.
  **우리는 이 교훈을 이미 적어놓고 어겼다** — 갭1: *"anchor_signals.py를 지었다가 삭제함… 판단 작업을
  코드로 박제하지 말 것."* 그런데 scorecard.py는 임계값 4개를 박고 주석에 스스로 "🔴 열린질문"이라 썼다.
  DF4(legacy가 등급 상한 D)가 그 대가다. **복잡도는 약속의 함수다** — 우리는 "파일을 옮기고 하나도 안
  잃겠다"고 약속했으니 오라클이 필요하고, 312줄로 싸게 샀다. 그 위에 올린 것들이 문제다.
- **▶️ 결정 후 순서(증거 있는 것만 — 의도적으로 짧다):**
  ```
  1. 깨진 링크에 수정안 붙이기(DF7)   ← 실측: vd-front 깨진 링크 8/8이 같은 원인
  2. 범례를 데이터에서 파생(DF5 근본) ← 실측: 오늘 사용자가 잡은 빨강 버그의 구조적 원인(증상만 고침)
  3. 등급을 안전 불변식과 분리(DF4)   ← 실측: 반증 확정 — 다른 게 다 pass여도 legacy 6건에 D
  4. PR + vd-front 랜딩 브랜치 검토(사용자)
  5. 그 뒤 = 새 기능 없음. 하드닝 루프(쓰면서 고친다).
  ```
  **의도적으로 뺀 것(관측된 필요 없음):** 안전 이동 `docsherpa mv`(아무도 요청 안 함, 새 메커니즘) ·
  DF6 절대경로 계약 정합(실사용 미관측) · ENTRY 대소문자(저확률 + 순진한 픽스는 악화) ·
  troubleshooting 실전 재검증(그런 레포를 만나면. 찾아 나서지 않는다).
  **완료 기준:** 새 레포에 돌렸을 때 **손편집 0**으로 계획이 나오고, 랜딩 후 깨진 링크가 **전부
  preexisting**이며, 그 사실을 **아무도 결심하지 않아도** 알게 된다. 앞의 둘은 vd-front에서 달성. 셋째가 결정 A.
- **🔗 링크 표기법 논쟁 — 종결(실측, 2026-07-09):** 사용자 직감 *"상대경로는 문서가 자주 바뀌니 쉽게 무너진다"*
  → **무너지는 건 맞고, 원인 진단은 틀렸다.** 랜딩 트리 92문서·문서간 링크 128개 전수 계산:
  링크 A→B 하나는 **A가 움직여도(절대경로가 막아줌) B가 움직여도(절대경로도 못 막음)** 깨진다 — 각 128건.
  실제 시뮬레이션(문서 1개 손으로 mv): 깨진 10건이 **전부 incoming** → **절대경로였다면 0건 구했다.**
  `rewrite_links`는 move_map을 알아 **양쪽 다** 고친다(vd-front 42건 이동, new_broken=0).
  **절대경로를 안 쓰는 이유**는 취향이 아니다: 마크다운/CommonMark엔 repo 루트 개념이 없고, GitHub은 선행
  `/`를 **사이트 루트**로, VSCode 프리뷰는 **FS 루트**로 읽어 사람이 클릭하는 모든 곳에서 깨진다. 게다가
  우리 `gate.resolve`도 그걸 FS 절대경로로 읽어 broken 처리한다(DF6).
  **진짜 구멍:** docsherpa **없이** 문서가 움직일 때 아무도 검사하지 않는다(손 mv 1회 → 링크 10개 침묵 파손).
  → 그래서 결정 A. **깨진 링크를 굳이 재작성하는 이유(실증):** 정체성 보존을 안 하면 `src/a/note.md`의
  `[x](README.md)`(깨짐)가 `docs/note.md`로 이사한 뒤 **실재하는 `docs/README.md`에 조용히 재결합**되고
  gate는 broken=0이라 아무도 모른다. 못생긴 이중 경로는 그 안전성의 대가다.
- **⏪ ADR 0005 위반과 되돌림(2026-07-09) — 같은 실수 반복 금지:**
  자동 gate를 `hooks/hooks.json`(플러그인 루트 active 훅)으로 배선했다가 **되돌림(47b4f97)**.
  ADR 0005(수락)는 이미 *"훅은 target repo에만 산다. 거부한 대안: user-scope 플러그인 훅 — 모든 repo에서
  전역 발동한다"* 라고 정해놨다. **정확히 그 거부된 대안을 구현했다.** "남의 레포에 코드를 안 심으니 덜
  침습적"이라 추론했으나 거꾸로였다 — 플러그인 훅은 사용자의 **모든 레포**에서 매 세션 실행되고, ADR 0007의
  워크스페이스별 승인 게이트를 **우회**한다. 침묵 가드는 증상만 없앨 뿐 메커니즘은 남는다.
  **교훈: 새 배선을 짓기 전에 `docs/decisions/`를 grep하라.**
  **같이 고친 진짜 버그 2건(유지):** ⓐ `targets_in()`이 읽기 불가 파일에서 `PermissionError` → `analyze()`
  크래시. `--hook`의 통째 except에 먹혀 **검사기가 조용히 아무 일도 안 함**(최악의 실패 모드). 비-hook CLI는
  아예 크래시했다. ⓑ `_rel()`: 라우터가 `../`로 root 밖을 링크하면 `relative_to`가 `ValueError`(선재).
  **⚠️ 구현자 서브에이전트가 "둘 다 고쳤다"고 보고했으나 ⓐ는 미수정이었다 — 재현 테스트로 잡음. 보고를 믿지 말고 재현하라.**

- **🎯 ③④ vd-front 재실행 완료(2026-07-09) — ②가 실전 검증됨, 새 엔진 결함 DF4 발견:**
  랜딩 브랜치 **`docsherpa/migrate-e43acbcf`**(vd-front, 커밋 `39f38b0f`, 검토·머지는 사용자).
  **②는 실전 검증 성공 — 매니페스트 손편집 0건.** 직전 dogfood가 손으로 우회하던 4건을 엔진이 자동 처리:
  `src/features/custom/CLAUDE.md`·`docs/CLAUDE.md`(DF2 어느 깊이든 router) · `shared/api/README.md`·
  `src/mocks/README.md`(DF1 코드-인접). **DF1 정밀화도 실전에서 살았다** — `src/features/custom/shared/docs/README.md`가
  stranded되지 않고 이주(리뷰가 안 잡았으면 이 레포에서 그대로 터졌다).
  **결과:** 문서 65→92(스캐폴드 포함) · 이동 42 · **고아 18→0** · **순수 삭제(D) 0건**(git rename 회계로 내용소실0 증명) ·
  unaccounted 0 · new_broken 0 · anchor_lost 0 · per_file 0 · markers_ok · 성장루프 설치(M2·M3·M4 pass).
  **등급 F→D.** broken 6은 **전부 preexisting**(오라클이 `new_broken=0 ∧ unexplained_broken=0`으로 증명 — 눈으로 본 게 아님).
  **작업트리·기존 브랜치 무영향 실측:** HEAD 불변 · 현재 브랜치 불변 · dirty 0 · worktree 잔재 0 · 브랜치 diff = 신규 1개뿐
  (옛 `docsherpa/migrate-59f05e69` 보존 — 삭제 불필요했음).
  **④ 도메인 결정(사용자, Phase 2 게이트에서):** 1)조직축=**타입 우선** 2)버전쌍=**둘 다 살림(동결 없음)**
  3)dnd 토픽 승격=**안 함** 4)커스텀 인덱스=**개명 이동**(`docs/custom-docs-index.md` — 루트 인덱스 자리 회피).
  **런타임에 안전장치 2개가 실제로 발동(설계 검증):** 분류 6분 사이 사용자가 vd-front에 커밋(`e43acbcf`) →
  ① `inventory.unaccounted` 완결성 가드가 분모 64→65 변동을 잡아 **진행 거부**(잊힌 문서 0 불변식) ·
  ② `land_migration` HEAD 핀이 스테일 계획 랜딩을 막음. 둘 다 **파괴 방지가 아니라 정직성 보장** 장치다
  (워크트리 격리가 브랜치를 지키고, HEAD 핀이 "승인한 계획=랜딩된 결과"를 지킨다 — 서로 다른 축).
  **🆕 DF4(신규 엔진 결함, 다음 배치 후보) — `legacy`가 등급 상한을 D로 못박는다:**
  `plan_moves`는 `type=="legacy"`(동결역사)를 **제자리 skip**하는데, `scorecard.outside_content`는 **경로 기반
  `disposition`만 보므로 `legacy`를 모른다** → docs/ 밖 legacy를 M5 위반으로 센다 → `rollup`의
  `if m["M5"]=="fail": return "D"`로 **영구 D 상한**. 반증 시도로 확정: M1~M4 pass + J1~J4 전부 pass여도
  legacy 6건 때문에 **D**, M5만 통과시키면 **A**. **ADR 0018의 논리와 모순** — 0018은 "M5의 파묻힘 0 =
  *중앙집중 대상* 문서가 모두 docs/ 아래"라 정의했는데, legacy는 설계상 중앙집중 대상이 **아니다**(제자리 동결).
  즉 0018이 명문화한 in-place 클래스(router·tooling, 경로 기반)에 **legacy(타입 기반)가 빠져 있다.**
  후보: (a) `scorecard.assemble`이 이미 받는 `inventory` 매니페스트로 `type=="legacy"`를 M5 분모에서 제외 ·
  (b) legacy를 `docs/legacy/`로 이주 · (c) 수용. **(a)가 0018 정신과 정합**(제자리 클래스 = 도달성·M5 면제).
- **🎨 DF5 픽스 완료 + DF6·DF7 발견(2026-07-09, 사용자가 렌더된 아티팩트를 보고 잡음 — 리뷰어 3명 다 놓침):**
  **DF5(픽스됨, 32d5ec7·9151d8e) — 타입색 `--fail-ink`가 `.stray`와 충돌해 범례가 거짓말했다.**
  `.tree .stray`(before 트리 파일, 선재)와 `.tree .t-troubleshooting`(이번 배치 추가)이 **같은 토큰**.
  result 모드는 after 트리를 안 그리는데(`t.get("after")` 없음) **타입색 범례는 무조건 렌더**돼,
  사용자가 본 화면은 "빨강 파일 + 바로 아래 '빨강=문제 해결(troubleshooting)'" — 그 repo엔 트러블슈팅 0건.
  intro의 "파일은 무색"도 자기 그림과 모순. **내 계획서가 스스로 경고했다가("stray와 토큰 공유하나 같은
  pane에서 공존하지 않고 범례가 구분한다") 무시한 지점 — 둘 다 틀렸다.**
  **픽스 방향(중요):** 동결 팔레트엔 트러블슈팅에 줄 새 색이 **없다**(AA on `--bg` 통과 + 미사용 =
  `--muted`·`--ink` 무채색뿐. `--warn` 2.89 · `--pass` 3.28 · `--fail` 4.14 = 라이트 AA 미달).
  그래서 "빨강을 stray에서 회수" — ⓐ `_nested_lines` 파일 클래스 `stray`→`None`(before 트리 무색).
  이건 **기록된 설계 의도 D6①("before=회색투성이/after=타입별 컬러")의 복원**이고, before 트리는 정의상
  전부 stray(`outside_content`만 나열)라 빨강이 **정보량 0**이었다. ⓑ after 트리 없으면 타입 범례 미렌더.
  ⓒ result 모드 제목 `Before → After`→`잔여`, 2단 그리드 해제(빈 오른쪽 절반 제거). 동결 CSS 토큰 무변경.
  **DF6(신규) — 절대(루트-상대) 링크에서 두 엔진의 계약이 어긋난다.**
  `migrate._EXTERNAL`은 `"/"`를 skip(F6 결정: 재작성 안 함)하는데, `gate.resolve`는 `(base.parent / "/src/x.md")`로
  **파일시스템 절대경로**로 해석 → 없는 파일 → **broken**. 즉 사용자가 절대경로를 쓰면 재작성은 안 되는데
  gate가 깨졌다고 한다. (실증: 합성 fixture로 확인.) 애초에 절대경로를 정본으로 못 쓰는 이유 = 마크다운/
  CommonMark엔 repo 루트 개념이 없고, GitHub은 선행 `/`를 사이트 루트로, VSCode 프리뷰는 FS 루트로 해석해
  **사람이 클릭하는 모든 경로에서 깨진다.** doc-상대만 GitHub·IDE·에이전트 셋 다에서 산다. 대가는 이사 시
  재작성 필요 → 그게 `rewrite_links` + 두 오라클의 존재 이유.
  **DF7(신규, 진단 실행가능성) — "repo-상대로 쓴 링크"를 별도 카테고리로.**
  vd-front preexisting_broken 8건은 전부 저자가 repo-상대로 쓴 것이고, 타겟 5개 중 **4개가 repo 루트 기준으론
  실재**한다. 지금 gate는 그냥 "broken"이라 말할 뿐이다. `doc-상대로는 깨짐 ∧ repo-루트 기준 실재` →
  "저자가 repo-상대로 씀" 힌트 + 정확한 수정안(`../../src/...`) 제시. **고치지 않고 제안만**(비파괴).
  **왜 깨진 링크를 굳이 재작성하나(설계 근거, 실증됨):** `rewrite_links`가 타겟 정체성을 보존하지 않으면,
  `src/a/note.md`의 `[x](README.md)`(깨짐)가 `docs/note.md`로 이사한 뒤 **실재하는 `docs/README.md`에 조용히
  재결합**되고 gate는 `broken=0`이라 아무도 모른다. 정체성 보존은 틀린 걸 틀린 채로 시끄럽게 남긴다 —
  이중 경로(`../../src/.../work-plans/src/.../c00-gate.md`)의 못생김은 그 안전성의 대가다.
- **✅ ①②③④ 완료 기록(2026-07-09) — 다음 순서는 위 ▶️ 블록을 따르라(이 블록은 이력):**
  아티팩트 자기설명 트랙 **완료**. 증분 4 land_migration 엔진 **origin/main 머지됨**(PR#10).
  **①트러블슈팅 1급 + ②disposition 하드닝 + ③④ vd-front 재실행**까지 이번 배치로 완료.
  현재 작업 브랜치 = `fix/artifact-preexisting-label-beforetree`
  (**195 setup-docs + 34 doc-health green · self-gate PASS · main 대비 38커밋 · PR은 사용자 지시 대기**).
  **① 트러블슈팅은 실전 미검증:** vd-front엔 troubleshooting 문서가 **0건**이라 1급 타입이 배치를 타지 않았다
  (범례·CSS만 존재). 트러블슈팅 문서가 있는 레포에서 재검증 필요 — 숨기지 말 것.
  **③ 재실행 기술 주의(2026-07-09 실측으로 정정):** land_migration은 브랜치명을 `docsherpa/migrate-<head_sha[:8]>`로
  결정론 생성. ~~vd-front HEAD가 `59f05e69`라 재실행 시 브랜치 충돌 STOP → `git branch -D` 선행 필요~~ →
  **틀림. vd-front HEAD가 `b6329632`로 이동함**(`59f05e69`는 그 조상). 새 브랜치명 = `docsherpa/migrate-b6329632`라
  **충돌 없음** → 옛 브랜치 `docsherpa/migrate-59f05e69`는 **삭제하지 말고 비교 기준선으로 보존**(비파괴 원칙:
  안 지워도 되는 걸 지우지 않는다). 재실행 전 확인할 것: 작업트리 clean(dirty=0) · gitignored `.md`=0 —
  이 둘이 성립해야 Phase 1b 스크래치 복사본(`.git` 제외)과 Phase 3 워크트리(추적 파일만)의 트리가 같아
  **1b가 3의 충실한 리허설**이 된다(어긋나면 3에서 `apply_moves` "src 부재" STOP).
  **워크트리 격리는 엔진이 이미 한다:** `land_migration`이 이중 worktree(`tempfile.mkdtemp`)로 격리 —
  `feat/VDS-892`·작업트리는 checkout조차 안 됨. Phase 0~2는 `build_and_verify`가 tempdir 복사만 쓰므로 **변형 0**.
  **③에서 검증할 것(②가 갚은 빚):** 직전 dogfood는 DF1/DF2를 **매니페스트 손편집으로 우회**했다. 이제 disposition이
  중첩 라우터·코드-인접 README를 자동 skip하므로 **손수정 0으로 계획이 나와야** 한다. 특히 vd-front의
  `src/features/custom/shared/docs/**`는 그 폴더의 `README.md`(문서 인덱스)까지 **함께 이주**해야 한다(DF1 정밀화).
- **🧭 ①트러블슈팅 1급 + ②disposition 하드닝 완료(2026-07-09, subagent-driven 8태스크 + 3자 교차검증):**
  계획 [2026-07-09-troubleshooting-firstclass-and-disposition-hardening.md](docs/plans/2026-07-09-troubleshooting-firstclass-and-disposition-hardening.md).
  **① troubleshooting 1급화:** 전용 홈 **`docs/troubleshooting/`**(사용자 확정 — how-to 하위 아님, 완전 독립 최상위)
  · `migrate._TYPE_DEST` 배정 · **7번째 타입색**(동결 토큰 `--fail-ink` 재사용, AA on `--bg` light 6.48/dark 7.89
  실측, AA 가드 페어 추가) · 집약뷰·트리·스캐폴딩·범례 전 렌더지점 배선 · doc-health 타입 어휘 +
  **J1 절차성 가드**(symptom→link-only = troubleshooting 아님 = fail) · knowledge.md L17·L27·L30 **주석 supersede
  (원문 삭제 0)** · **ADR [0017](docs/decisions/0017-troubleshooting-first-class-doc-type.md)**.
  ⚠️ **리뷰가 잡은 갭:** 라우팅 룰 **정본은 `scaffold._MAP_DOC`**(사용자 프로젝트로 생성됨)인데 SKILL.md 미러만
  고쳐 신규 스캐폴드는 옛 룰을 받을 뻔함 → `_MAP_DOC` + 자기 `docs/_map.md` 동기(f1ebddd). 템플릿엔 ADR 번호
  미표기(**도메인 리터럴 0** — 누출 방지). troubleshooting/은 PRD·specs처럼 **온디맨드**(인덱스 선등록 안 함).
  **② `contract.disposition` 하드닝(엔진 핵심 단일소스 — gate·scorecard·migrate 공유):**
  (DF2) `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` = **어느 깊이든 `router`**(중첩 = 그 서브트리의 제자리 라우터).
  (DF1) 부모 경로에 `docs` 세그먼트가 **없는** 중첩 `README.md` = `tooling`(제자리) → basename 충돌
  `ValueError` STOP 원천 차단. 부모에 `docs`가 있으면(**대소문자 무시** — `Docs/`·`DOCS/`) `content` 유지 →
  **파묻힌 문서 인덱스는 내용과 함께 이주**. 반환값 3종 불변. **ADR [0018](docs/decisions/0018-disposition-in-place-classes.md)**
  = "router·tooling = 제자리 + 도달성 면제"를 **명시 계약**으로 기록(M5의 "파묻힘 0" = *중앙집중 대상* 문서가 모두
  docs/ 아래라는 뜻이지, 레포의 모든 .md가 아님).
  **🔍 3자 독립 교차검증(opus 리뷰어 · architect · codex 적대적) — [P1] 0건:**
  내용소실0 확증 — `content_oracle.collect`·`per_file_accounting`은 disposition **무관** 전-트리 `rglob("*.md")`,
  `apply_moves`는 skip 파일까지 링크 재작성, `gate.analyze`는 disposition을 **import하지 않음**(orphan 우주 = `docs/**`).
  → 재분류는 삭제·덮어쓰기가 아니라 **이동 계획 제외**일 뿐(루트 README가 이미 받던 대우).
  **리뷰가 잡은 실결함 2건(둘 다 수정):** (a) DF1이 `parts[0]!="docs"`라 **파묻힌 docs 트리의 README가
  stranded**되고 M5가 그걸 안 세던 사각 → `"docs" not in parts[:-1]`로 정밀화(a45afc7, 사용자 승인).
  (b) 그 부모 검사가 **대소문자 민감**이라 `Docs/`가 같은 결함을 재현 → 소문자 정규화(f2da2f1, codex 적발).
  **의식적 수용:** 루트 라우터 없는 레포에서 posture가 GREENFIELD로 뒤집힐 수 있으나 `rollup()`의
  `if not router_present: return "F"`로 **등급은 F로 정직 유지**(posture는 조언 힌트, scaffold는 append-only).
  **최종 whole-branch 리뷰(opus): READY TO MERGE** — Critical·Important 0, 정체성 4불변식 전부 HOLD
  (비파괴·내용소실0·자가성장·도메인리터럴0), 동결 CSS `:root` 토큰 무변경 확인.
  **잔여 Minor 3건(전부 비블로킹 follow-up):**
  - **(M1) `name in ENTRY_FILENAMES` 대소문자 민감** — 선재. macOS에서 루트 `Claude.md`면 content로 떨어져
    이동 → 라우터 소실 → gate orphan → **거짓 STOP(시끄러움, 소실 아님)**. ⚠️ **순진한 소문자 픽스는 오히려
    악화**: Linux repo의 정당한 문서 `docs/agents.md`(에이전트를 *다루는* 문서)가 `router`로 오분류돼
    **조용히 이동 제외 + M5 면제**된다 — 정직한 진단이 정체성인 도구에서 "시끄러운 실패 → 조용한 오면제"는
    나쁜 교환. **올바른 픽스는 비대칭**: 루트는 대소문자 무시(FS 현실), 중첩은 대소문자 민감(정확한
    `CLAUDE.md`가 곧 라우터 계약). 설계 작업이므로 별도 처리. (architect·최종리뷰 둘 다 defer 동의.)
  - **(M2) `_MAP_DOC` 정본 가드 테스트 없음** — 이번 드리프트가 부재의 실증. 단 유용한 불변식은
    "SKILL.md와 byte-identical"이 **아니다**(정본=간결·리터럴0, SKILL.md=상세·ADR 주석 — 의도적 차이).
    올바른 가드 = "정본이 라우팅 룰을 담고 있고 **ADR 리터럴 0**".
  - **(M3) `posture_hint`가 GREENFIELD로 뒤집힐 수 있음** — `rollup()`의 `if not router_present: return "F"`로
    **등급은 F 유지**, posture는 조언·scaffold는 append-only → 파괴적 동작 없음. ADR 0018에 수용 기록.
  - **(M4, 최종리뷰 신규) DF1은 리터럴 `docs` 세그먼트만 인식** — `documentation/README.md`·`guides/README.md`
    같은 다른 이름의 문서 인덱스는 제자리에 남고 형제 content만 이주. **소실 아님**(파일 잔존 + `apply_moves`가
    링크 재작성 + 오라클 회계). 직전 대안(basename 충돌 STOP)보다 낫다 — 경계 있는 트레이드오프.
- **✅ 아티팩트 자기설명 보정(A·라벨·C1) 완료(2026-07-09, subagent-driven 5태스크):**
  vd-front dogfood·UX 피드백에서 드러난 진단서 아티팩트 결함 3건을 고침. **(A) 플랜 표면화** —
  `build_and_verify`가 `preexisting_broken`을 반환 → `assemble_plan_data(..., preexisting_broken=...)`가
  전달 → `render_report`가 plan·result 양 모드에서 기존 `_render_preexisting`으로 렌더(콜아웃/impact
  아님 — 이동유발 위험은 이미 `new_broken=0` 게이트로 차단, preexisting은 별도 축). SKILL.md Phase 2
  산문에 배선 명시. **(라벨) how-to 정직화** — tkey·`_TYPE_GROUP` 두 곳 모두 "가이드(how-to)"→"작업
  절차·복구(how-to)"로 변경(트러블슈팅 은폐 방지, 위 트러블슈팅 1급 승격 결정과 정합). **(C1) before 트리
  중첩** — `scorecard._before_tree`를 평면 나열에서 `_nested_lines` 기반 중첩 스캐폴딩으로(파묻힌 구조
  가시화, `_after_tree`와 표현 일관). **B·C2 구현 완료(사용자 명시 요청으로 architect defer 해제):**
  B는 orphan 데이터 배선(doc-health orphans 방출 → `assemble_plan_data(..., orphans_after=...)` →
  `.mig-head` 규모 라인 "고아 N→0"), C2는 순수 render(기존 `.tree` CSS 재사용, 이동 src/dest에서 파생) —
  정직성은 `orphans_after`=`build_and_verify` 검증값, 유실0은 `content_oracle` 불변식이 각각 담보.
  트러블슈팅 1급 승격(doc-type 트랙, 아래 항목)은 이 작업 범위 밖 유지. 브랜치
  `fix/artifact-preexisting-label-beforetree`, 계획
  [2026-07-09-artifact-selfdescribe-fixes.md](docs/plans/2026-07-09-artifact-selfdescribe-fixes.md).
- **✅ 증분 4 `land_migration` 완료 + vd-front 실 dogfood 성공(2026-07-09, subagent-driven 9태스크):**
  승인된 계획을 git worktree 격리로 실 브랜치에 랜딩 + 재진단. 신규 `land_migration`(이중 worktree·HEAD sha 핀·
  **검증트리=커밋트리**·통과 시에만 커밋·`finally` 흔적0) · `register_all`(도달성-구동·진행가드·live-link) ·
  링크 오라클 `classify_links`/`doc_links`(**소스정체성 페어링** — new_broken vs preexisting, 앵커 보존) ·
  `per_file_accounting`(content_oracle dedup 사각 보완) · `verify_migration`(5-체크 일원화:
  unaccounted·new_broken·anchor_lost·**unexplained_broken**·orphan·per_file) + build_and_verify 재배선 +
  render result 모드 + SKILL Phase 3·4. **157 setup-docs + 30 doc-health green, self-gate PASS.**
  스펙 [landing-migration.md](docs/specs/diagnosis-driven-migration/landing-migration.md)(§0b R1~R9 교차검증=codex+architect),
  계획 [2026-07-09-increment4-landing-migration.md](docs/plans/2026-07-09-increment4-landing-migration.md). 브랜치 `fix/incr4-exec-gates-g1-g2`.
  **구현자≠검증자가 잡은 실결함:** Critical(재호출 시 이전 성공 브랜치 force-delete=내용소실0 위반) · HIGH(doc_links가
  `@import`를 링크로 세어 zip 정렬붕괴 오분류) · 최종리뷰 Important(cur-only 파일 broken 안전망 회귀) · MEDIUM 다수 — 전부 수정·재리뷰.
  **🎯 vd-front 실 dogfood 성공:** Phase0 진단(58 커밋 docs·등급 F·~35 buried in `src/features/custom/shared/docs/**`)
  → 병렬 분류 2서브(type우선 D5: project-meta spec폴더→reference 교정·버전쌍 legacy·dnd co-change) → 26 이동
  → build_and_verify 전부 0 → **land_migration → 실 브랜치 `docsherpa/migrate-59f05e69`(vd-front에 존재, 검토·머지는 사용자)**:
  unaccounted0·new_broken0·anchor_lost0·**preexisting_broken8(표면화)**·작업트리 무영향·worktree잔재0. Phase4 재진단:
  **orphan 67→0·markers_ok·docs 48**. broken 6은 전부 **preexisting 검증**(원본이 repo-상대를 doc-상대로 오작성한 부채가
  도달성 확보로 드러남=D2 실증) — 마이그레이션이 만들지·숨기지·고치지 않고 표면화만(L4/정체성 교과서 준수).
  **증분 4 = origin/main 머지됨(PR#10, 9b84d51).**
  **dogfood 발견 → ②로 승격(재실행 전 엔진 하드닝) — ✅ 전부 완료(위 🧭 블록·ADR 0018):** DF1 코드-인접 nested README(mocks·api)는
  중앙집중 대상 아님 → `contract.disposition`이 in-place로 skip(basename 충돌 원천 차단). DF2 nested CLAUDE.md도 router-skip 확장.
  DF3(수정됨, a0a9587) `rglob("*.md")` is_file() 가드(`.md`로 끝나는 디렉터리 크래시).
  **도메인 결정(org type-scatter vs 기능응집 · legacy 통합 · co-change topic)은 §10 결정 표면화 = 재실행 Phase 2 승인에서**
  (최상단 ▶️ 블록 ④ — 미리 정하지 말 것). vd-front 시험 브랜치 `docsherpa/migrate-59f05e69`는 ③에서 폐기 후 재실행.
- **🩺 트러블슈팅 1급 승격 결정(B안, 2026-07-09 사용자 채택) — ✅ 구현 완료(위 🧭 블록·ADR 0017). 아래는 결정 근거 기록:**
  **문제 실증(vd-front 진단서 리뷰):** 현재 분류 type 어휘 = `ADR·spec·how-to·reference·PRD·legacy` — **`troubleshooting`
  타입 자체가 없다.** knowledge.md(§문서타입4종, L27·L30)가 Troubleshooting을 "반응적 복구 절차(명령·진단·복구) →
  `how-to/`"로 **접어버려**, 트러블슈팅 문서가 how-to로 분류돼 **가이드와 식별 불가** + 전용 홈 없음. 아티팩트 범례
  "가이드(how-to)"가 이 사실을 **은폐**(자기설명 실패, D4류) → 라벨은 "작업 절차·복구(how-to)"로 이미 선반영.
  **결정 B(1급 승격):**
  (1) **분류 type 어휘에 `troubleshooting` 추가** — doc-health 분류(inventory 병렬분류) + scorecard가 독립 type으로
  식별(how-to 하위변종 아님). 질문어 = "깨졌을 때 무엇을·어떻게 복구".
  (2) **전용 홈** — 권장 `docs/how-to/troubleshooting/`(Diátaxis how-to 계열 응집 유지 + 식별성 확보) vs 대안
  `docs/troubleshooting/`(완전 독립). ← 둘 중 최종 폴더는 착수 시 확정(권장=how-to/troubleshooting/).
  (3) migrate `plan_moves`에 troubleshooting→그 폴더 배정. render 타입색·범례·트리에 troubleshooting 추가(6→7색).
  (4) **진단 차원** — 트러블슈팅 절차성(link-only 아님) 품질 차원 유지/강화.
  **승계할 가드레일(설계 정신 보존):** 트러블슈팅은 **진짜 절차**여야(명령·진단·복구). `symptom→link`만인 링크-전용
  트러블슈팅 금지(Status 복제·부패). 증상 alias는 주인 문서(한계·개념 함정)에. → B 승격 후에도 이 가드는 유지.
  **supersede 대상:** knowledge.md L17(Diátaxis=폴더 아님 — troubleshooting은 예외로 식별 필요)·L27(타입표 how-to/
  매핑)·L30(가드). **ADR 신설 필요**(현 stance 부분 supersede; 이연 [doc-type-templates](docs/specs/doc-type-templates/design.md)
  트랙과 묶음). **착수 시점:** 증분 4 마무리 후 doc-type 개선 트랙.
- **🆕 setup-docs 재설계 — 진단-주도 전체-repo 마이그레이션 (2026-07-08, 브레인스토밍→스펙→증분3 완료):**
  하드닝 루프 발견(G1~G4: docs/ 중심·밖 방치·전-계정팅 부재·설치≠완료)을 재설계로 확장. **미션 = 전 프로젝트
  문서를 `docs/`로 중앙집중 + 유실 0.** 6-Phase(전체-repo 병렬 탐색 → 9차원 등급 채점 → 시각 승인
  아티팩트 → worktree 배치 실행(두 오라클) → 결과 재진단). 진단을 **`doc-health` 스킬**로 분리(before/after
  동일 채점기 = 정합성), `render_report.py` 공유 렌더러(동결 CSS + WCAG-AA 테스트로 품질 영구 고정 — 매
  실행 동일 품질). 스펙 [design.md](docs/specs/diagnosis-driven-migration/design.md), 계획
  [render-report](docs/plans/2026-07-07-render-report-renderer.md).
  **✅ 증분 1 `render_report` 완료:** 350줄 stdlib 렌더러 + 13 테스트(105 green), opus 리뷰 APPROVED(Crit/Imp 0),
  AA 가드 라이브(worst 4.78)·자기완결·동결 CSS byte-identical·전 주입점 이스케이프.
  **✅ 증분 2 `doc-health` 완료(2026-07-08):** 독립 읽기전용 스킬(`skills/doc-health/`) — `gate.analyze()`
  외과적 추출 + 전용 `inventory.py`·`scorecard.py`(disposition·M1~M5·rollup·자세·assemble) + SKILL.md·
  reference/scoring.md, 23 테스트 green(전용 러너). ADR [0015](docs/decisions/0015-doc-health-module-extraction.md)
  (H1~H3 근거 기록). 다음 = setup-docs Phase 0·1·2 배선(증분3에서 완료).
  이연: Phase 4 result-모드 CSS·repo-키 스키마 하드닝(ledger `.superpowers/sdd/progress.md`).
  **✅ 첫 실전 독푸딩(vd-front, 2026-07-08):** doc-health를 실제 레포에 적용 → **탐색이 코드 속
  `src/features/custom/shared/docs/**` ~35개 파묻힌 문서를 전부 포착(G1 갭 실증)**, 등급 **F**(정직).
  실데이터가 버그 2건 노출 → ADR [0016](docs/decisions/0016-inventory-respect-gitignore.md): **탐색 분모가
  `.gitignore` 존중**(외부 플러그인 스크래치 `.superpowers/` 등을 하드코딩 없이 자동 제외 — 레포 선언 위임,
  git-optional) + 루트 관례 대소문자 무시. vd-front M5 49(오염)→38(정직). 리뷰가 비-ASCII 경로 인용 버그도
  잡아 `-z` 픽스(한글 경로 가드 테스트). 30 테스트 green.
  참고: ADR 0010 `doc-*` 패밀리 폐기 → 새 스킬은 merit로 명명(그래서 `doc-health`).
  **📌 이연 기록(2026-07-08):** vd-front 독푸딩+설계 논의에서 표면화된 **문서 타입 템플릿·메타·트리거** 개선을
  [doc-type-templates/design.md](docs/specs/doc-type-templates/design.md)에 기록. 핵심 = doc-reconcile 트리거가
  판단-소프트(reference/explanation 트리거 없음·메타 스탬핑·게이트 부재). **심장은 템플릿 아니라 트리거.**
  합의 결정(B 스캐폴드·created/adopted 정직·타입-메타 게이트·관계메타·산업표준) 기록됨. **착수는 setup 완료 후**
  (doc-reconcile 개선 루프). ⚠️ B 착수 시 ADR 0013 supersede 필요.
- **✅ 증분 3 `migrate.py` 엔진 + Phase 0·1·2 배선 완료(2026-07-08):** 계획검증 F1~F6(F1=register_in_indexes
  substring 오탐·F2/F3=엔진 기반골격·F4=legacy skip·F5=orphan==0 단정·F6=슬래시 보존) 전부 반영해
  `skills/setup-docs/scripts/migrate.py` 신설 — `plan_moves`(결정론 type→folder·disposition/legacy/.mdx
  자동skip) · `apply_moves`+`rewrite_links`(물리이동+링크재작성, chained-move 2단계 안전) ·
  `register_in_indexes`(scaffold 위 도달성 배선, home 인덱스링크 정확매칭) · `build_and_verify`(스크래치
  복사→적용→scaffold→등록→gate+content_oracle, 실제 repo 불변) · `assemble_plan_data`(render_report plan
  계약). `skills/setup-docs/SKILL.md`의 MESSY 무거운 차선을 이 엔진 호출 Phase 0(진단 재사용)→1a(배정
  판단+plan_moves)→1b(build_and_verify 자체검증+STOP)→2(assemble_plan_data+승인 아티팩트) 절차로 재배선.
  **다음 = 증분 4**(Phase 3·4: 승인된 계획의 실제 이동 실행 — 배치·worktree·subagent-driven-development —
  및 실행결과 재진단). 128 + 30 테스트 green, gate broken=0 orphan=0 markers_ok=True.
  최종 whole-branch 리뷰(opus) READY TO MERGE — 5 정체성 불변식 전부 HOLD(scratch-only 범위), Crit/Imp 0.
  **✅ 증분 4 실행-게이트 G1·G2 닫힘(2026-07-09, RED-first):** 실제-repo 쓰기 전 필수 안전 게이트 2건 해소.
  (G1) `inject_claude_md` frontmatter 분기가 `@AGENTS.md`를 frontmatter 세그먼트에 붙여(빈 줄 없음)
  build_and_verify가 false-STOP → **닫는 `---` 뒤 빈 줄 삽입**(`\n@AGENTS.md\n\n`)으로 어느 세그먼트에도
  병합 안 되게 교정(RED 테스트 = frontmatter 세그먼트 key 보존). (G2) `apply_moves`·`content_oracle` 둘 다
  `errors="ignore"`라 invalid UTF-8 바이트 소실이 오라클에 안 잡히던 사각 → **읽기/쓰기/seg_key 전부
  `errors="surrogateescape"`**로 전환(apply_moves 바이트 라운드트립 = 소실 0 + 오라클이 바이트 차이를 key에
  반영해 감지). RED 테스트 2건(apply_moves 바이트 보존 · collect가 바이트 소실 unaccounted 감지). 131 setup-docs
  + 30 doc-health green, gate PASS. **→ 실제 파일 쓰기 안전판 확보(증분 4 Phase 3 진입 가능).**
  **🧪 실전 dogfood(vd-backend, 2026-07-08):** Phase 0·1·2 파이프라인을 실 레포에 적용(스크래치, 비파괴).
  75 docs·등급 **F**(정직: 라우터 도달 orphan 67/67 + 마커·척추·성장루프 전무 → 기계 M1~M4 FAIL, M5만 PASS).
  분류 병렬 서브에이전트 4개(완결성 68/68) → plan_moves 이동 43 + legacy/제자리 등록 24 → build_and_verify
  **orphan=0·unaccounted=0(내용 소실 0)·broken=3** → render_report plan 아티팩트 산출. **증분 4 입력 3건 발굴:**
  (D1) **제자리·legacy 문서도 인덱스 등록 필요** — `plan_moves`/`register`가 이동 문서만 등록 →
  이미 올바른 위치의 docs(`docs/harness/*`·`docs/README.md`)와 legacy가 고아. 등록 대상을 docs/ 아래 전체
  content로 확장해야(이번엔 수동으로 넓혀 orphan=0). (D2) **도달성 확보가 잠복 broken 링크 노출** —
  원본 미도달이라 gate가 방문 안 해 숨겨졌던 코드-디렉터리 링크(FRONT-END_API_INVENTORY.md → `src/apis/` 등 3개)가
  이사 후 드러남 → 링크 교정(de-link) 단계 필요. (D3) **트리 시각화 생성기 스텁** — `scorecard._before_tree`는
  docs/ 밖 흩어짐만·`migrate._after_tree`는 평면 12개만 → 실제 중첩 폴더 트리 미표현. 증분 4에서 실 계층 렌더로 개선.
  (D3보강) **트리 접이식(collapsible) 전체보기** — 요약(폴더+개수)은 기본, 전체 파일 스캐폴딩은 `<details>/<summary>`
  네이티브 disclosure(JS 0·시맨틱·비버튼)로 Before→After 2열 펼침. vd-backend 아티팩트에 후처리로 프로토타입(프리즈
  테마 변수 재사용·인라인 style 0·반응형 ≤640px 1열·legacy prd/ 흐림). 정식화 = `render_report`에 트리 `collapsible`
  플래그 + 전용 프리즈 CSS + 대비/구조 게이트 테스트 추가(렌더러 확장). 프리즈 품질 게이트와 충돌 없음(외부리소스 0 유지).
  (D5) **배치는 타입 우선이어야 — 폴더명 topic 남발 금지(백엔드 개발자 검토가 실증)** — vd-backend 첫 배치에서
  분류는 내용을 읽고 정확했으나(`기획서`=PRD·`N일차_진행`=legacy 정확) 오케스트레이션이 **폴더명 기반 topic
  클러스터링**을 남발해 그 type을 배치에서 덮어씀 → PRD 기획서가 `product/` 아닌 `onboarding/`로, 결제(일본결제)
  spec이 `onboarding/`로 오배치. 도메인 전문가가 "내용 안 보고 배치했냐"고 정확히 감지. **설계 §7 "타입 먼저,
  토픽은 co-change일 때만"을 위반한 것.** 교정 v2(type 우선: PRD→product·spec→specs/<feature>·ADR→decisions,
  일본결제→specs/payment)로 재배치·재검증(orphan=0·유실0) — 두 예시 정상화. 교훈: SKILL Phase 1a enrich에서
  **topic은 co-change 클러스터에만, 배치 1순위는 분류 type**임을 산문에 강제(폴더명 승계 유혹 차단). 남은 판단:
  타입 vs 기능응집 조직(Diátaxis 흩뿌림 vs 폴더 응집)은 도메인 결정 — 결정 패널로.
  (D4) **아티팩트 은어 누출(자기설명 부재)** — 승인-대상 산출물인데 `scorecard.py`의 차원 라벨/sub가 내부 은어
  (`성장 루프 3종`·`맵 척추`·`마커 home`)라 docsherpa 개념 모르는 외부 뷰어는 이해·행동 불가(채택률 직결).
  렌더러 아닌 scorecard의 name/sub를 자기설명형(무엇을 재나+결과)으로 바꿔야. 예: M4 → "코드 변경 시 문서
  자동 갱신 장치 3종(세션 훅·알림·doc-reconcile 스킬) 미설치". vd-backend 아티팩트에 선반영해 검증(9차원 평문화).
  (D4보강) **능력 vs 준수 차원 구분 표기** — M2·M3·M4는 docsherpa 특정 부품(라우터 마커·맵 척추·doc-reconcile)
  유무를 재는 **준수(채택도) 차원**이라 사용자 자체 등가물(자작 갱신 스킬 등)을 인정 못 함(결정론 대가). 반면
  M1(도달성)·M5(커버리지)는 **능력(도구 무관) 차원** — 실제 속성이라 진짜 결함. 검사 로직은 결정론이라 그대로
  두되(자체 등가물 인정=결정론 포기), **라벨에서 "docsherpa 채택도(선택)" vs "문서 건강(필수)"를 구분**해야
  자체 체계 보유자가 오해/억울함 없이 유도 목적 유지. vd-backend 아티팩트에 선반영(M2~M4=채택도·M1/M5=필수).
  (D6) **아티팩트는 내레이션 없이 스스로 의도를 말해야 — 자기설명 섹션 + 시각 인코딩 라벨링(vd-backend UX 반복
  개선으로 도출)**. render_report 여러 섹션이 "만든 사람만 아는" 상태였음. 발견·교정 항목:
  ① **트리 폴더=타입색**(파일 무색·폴더에 색): 폴더 하위 문서가 단일 타입이면 타입색, 섞이면 회색 →
  before=회색투성이(혼합)/after=타입별 컬러 대비가 "정리 전후"를 색으로 전달. 하단 범례를 "폴더 색=타입"으로 교체.
  ② **이동 계획 = 나열 아닌 정보전달 구조**: per-doc 43행(정보 0) → **타입별 6행 집약**(규모 한 줄 + 문서수 +
  텍스트막대(크기,인라인 style 0) + 목적지) + **"▲ 옮기기 전 결정·조치할 것" 별도 콜아웃**(impact를 셀에 파묻지 말고
  격상). 상세는 접이식 스캐폴딩이 담당(역할 분담: 요약=형태, 펼침=상세). ③ **자기설명 필수**: 섹션마다
  (a)무엇을 보여주나 (b)어떻게 읽나(막대=문서 수·▲=결정) (c)뭘 하란건가 를 intro/컬럼헤더/범례로 명시 —
  내레이션 의존=실패. ④ **컬럼 헤더 + 가로 스크롤**: 표에 열 제목 필수, 긴 셀은 `overflow-x:auto`+`nowrap`로
  잘림 대신 스크롤. → 정식화 = render_report에 (트리 타입색·이동 집약뷰·섹션 intro/범례 강제·가로스크롤) 반영 +
  각각 대비/구조 게이트 테스트. 프리즈 품질(인라인 style 0·외부리소스 0·라이트/다크) 유지하며 프로토타입 검증 완료.
  참고: vd-backend 아티팩트 렌더 프로토타입은 세션 스크래치(`render_vdb.py`)에만 존재(프로젝트 리터럴 有 → 정본 커밋 X).
- **상태:** M0·M1·M3·M2 · 자기-독푸딩 · 갭1 · N11 spine · Track2/F12 · loop-refresh · PRD 1급 타입 ·
  **M5 출시 산출물 완비 + v0.1.0 발행 완료(2026-07-06).** 빌드 사실상 종료.
  다음 = **사용자 정지점만 남음**(터미널 설치 실검증 (c) · 중복 global 제거 (d) · 마켓플레이스 등록 —
  런북 `docs/plans/M4-dogfooding.md`). 새 기능 계획 없음(F13/14/15는 YAGNI 이연, ADR 0012).
- **setup-docs 진단-주도 제안 — ADR [0014](docs/decisions/0014-setup-docs-diagnosis-driven-proposal.md) 완료(2026-07-07):**
  e2e 독푸딩(jio.dev)에서 setup-docs가 정본 결정 위임·무거운 경로 강요·루프 스킵유도를 재현 →
  SKILL·knowledge 수정(**4자세 진단-주도 제안 · 성장 루프 필수화 · MESSY 경량/무거움 2차선**).
  fresh 베이스라인 대비 행동 4항목 FAIL→PASS(독립 판정자 확인) + jio.dev 실행 M1~M4
  (gate broken=0·orphan=0 · 마커 · content_oracle 무손실 unaccounted=0 · 멱등/HEALTHY 재진단) 전부 PASS.
  **gate.py `@import` 오탐 = 해결(2026-07-07):** 산문 속 `@AGENTS.md`를 import로 오인하던 `IMPORT_RE`를
  **줄-선두 매칭**(`(?m)^[ \t]*@…`)으로 좁힘. RED-first 재현 테스트 2건 추가(92 GREEN).
  **4자세 전부 검증 완료(2026-07-07):** 자세3(jio.dev, 8/8 루브릭) + GREENFIELD(조용히 설치)·
  중구난방(선택지 없이 migrate 강권)·HEALTHY(무변경) 합성 fixture로 확인 — **라우터 없는 GREENFIELD
  vs 중구난방 구분**(docs 최소 vs chaotic)까지 통과. **→ setup-docs 진단-주도 개선 = 완결.**
  관찰: 무거운 차선의 content_oracle/worktree는 git 전제(non-git repo면 `git init` 선행). (jio.dev
  마이그레이션은 여전히 **미적용** — 적용은 사용자 판단; gate 버그 해결로 이제 백틱 우회 없이 깨끗함.)
- **N11 맵 중추 문서(spine) — Plan 1·2·3 완료(2026-07-06):** 마커·계약 단일 소스(`contract.py`) +
  gate 루트 일반화·단일-home locator(Plan 1) · 그린필드 맵 생성 `write_map`(Plan 2, Slice A) ·
  인라인→맵 비파괴 마이그레이션 `migrate_inline_to_map` + **docsherpa 자가적용**(Plan 3, Slice B,
  content_oracle unaccounted=0). ADR [0011](docs/decisions/0011-map-spine-document.md). SKILL·DESIGN·
  doc-reconcile 문서 정합까지 완료(f58e76f). 계획서 `docs/plans/2026-07-06-n11-*`.
- **Slice C(자가치유) 유보(YAGNI, 2026-07-06):** 맵 링크 삭제는 gate가 orphan으로 시끄럽게 잡아
  **내용 소실 0 유지**(자동 복구는 안전 아닌 편의). 실사용 필요 시 최소 `heal_map_link`(sidecar 없이)로
  착수. 근거·판단은 ADR 0011. → **N11 spine 트랙 사실상 종료.**
- **Track2/F12 + loop-refresh 완료(2026-07-06):** F12(평면-only 성장 갭)=doc-reconcile 판정에 룰#4 트리거
  (co-change 클러스터 ≥2 → 폴더 승격 **비블로킹 제안**; 이동은 안 함, content_oracle 경로에 위임).
  F11/13/14/15=미구축 기능(N4·N9) 제약을 ADR [0012](docs/decisions/0012-self-growth-open-issues.md)에 기록.
  **loop-refresh**=설치본 doc-reconcile **자동 동기**(파일 끝 스탬프에 `sha=` 심어 버전+해시; `refresh_loop`이
  provenance·다운그레이드 차단·로컬편집 보존(stuck)·**무프롬프트 커밋 0**). `skills/setup-docs/scripts/refresh.py`,
  계획서 `docs/plans/2026-07-06-loop-refresh.md`. **⚠️ 자기 repo 두-사본 동기는 여전히 수동**(plugin==target →
  provenance no-op; refresh는 배포된 사용자 repo용). **90 tests GREEN.**
- **PRD 1급 문서 타입 완료(2026-07-06):** PRD(제품의 "왜 만드나·누구·성공기준")를 spec(무엇)·ADR(왜 이 기술)과
  **다른 도달성 트리**로 라우팅 **#2**(ADR 바로 아래)에 1급화. `docs/product/*.md` 폴더 카테고리, **온디맨드**
  (specs/처럼 스캐폴드 X·MVD — 첫 PRD 유입 때 생성). 정본 3곳 동기(`_map.md` 라이브 · `scaffold.py` `_MAP_DOC`
  그린필드 · `setup-docs/SKILL.md` 예시) + doc-reconcile에 PRD 트리거·"PRD 있어도 ADR 병렬 신설" 함정.
  재번호(#3~#6)로 낡은 룰 참조 2곳 정정. ADR [0013](docs/decisions/0013-prd-first-class-doc-type.md).
  **첫 PRD dogfood**: `docs/product/`가 온디맨드로 실제 생성됨(`PRD-nondestructive-migration.md` +
  `_README` 리드 인덱스 + `_map.md` 등록, gate broken=0 orphan=0, docs 29→31).
  ⚠️ **정본 doc-reconcile 편집 → `refresh.canonical_hash` 변경. 설치본 전파는 `plugin.json` version 범프 필요 = M5 릴리즈 스텝.**
- **✅ M5 출시 산출물 완비 + v0.1.0 발행(2026-07-06):** `README.md`(오픈소스 퀄리티 — 훅 투명성 섹션 포함) ·
  `LICENSE`(MIT, plugin.json 선언과 정합) · `CHANGELOG.md`(0.1.0) · `PROVENANCE.md`(자작 코드·패턴 참조·빌린
  코드 0·식별자 감사 누출 0) 신설. `hello` 프로브 제거(ADR 0010 실행분). `plugin.json` **0.0.1 → 0.1.0**.
  **git 태그 `v0.1.0` + GitHub Release 발행**(https://github.com/jihkyuo/docsherpa/releases/tag/v0.1.0).
  검증: 90 tests GREEN · gate broken=0 orphan=0 · 릴리즈 게이트(JSON·링크·placeholder·버전 정합) 통과.
  **남은 사용자 정지점(M4 런북, 터미널 Claude Code):** (c) `/plugin install docsherpa@docsherpa` 실검증 ·
  (d) 중복 global `~/.claude/skills/setup-docs` 제거(c 확인 후) · (선택) 마켓플레이스 공식 등록.
- **ADR 0010 폐기 — `doc-*` 패밀리 미채택(2026-07-07):** `setup-docs → doc-setup` 개명은 **하지 않음**(v0.1.0이
  `setup-docs` 커맨드 표면으로 이미 발행 → 개명은 breaking). flagship이 안 따라 `doc-*` "패밀리"는 실현된 적
  없음 → **폐기.** 실제 규칙 = **혼합**(`setup-docs`+`doc-reconcile`), 새 스킬은 `doc-*` 강제 없이 **merit(명료함
  + 네임스페이스 없이 홀로 불릴 때 자명)**로 명명. `hello` 삭제·브랜드 미표기(`docsherpa-*` 거부)는 유효.
  ADR [0010](docs/decisions/0010-skill-names-doc-family.md) 상태 = 폐기.
- **순서(재-시퀀싱):** M1 → M3 → M2 → M4 → 자기-독푸딩 → **갭1** → M5.
- **갭1(재사용 §7.5) 완료 — 산문+마커, 코드 없음:** ① 정본 doc-reconcile 앵커 블록을
  `<!-- docsherpa:anchors:start/end -->`로 구분(가드가 강제 — 특화 대상 명확). ② SKILL 5단계에 "§7.5 특화"
  **에이전트 절차**: target `docs/`·AGENTS.md를 직접 보고 **실재하는 정확 경로(대소문자)로만** 특화,
  없으면 일반형 유지(대체 문서 지어내기 금지), 정본은 generic. **45 tests GREEN.**
  - **⚠️ 리뷰 교훈(/code-review + /codex 합치):** 처음엔 `anchor_signals.py`(탐지 헬퍼)를 지었다가
    **삭제함.** 이유: M3 계획의 "§7.5 추가 코드 불요" 결정을 뒤집었고(YAGNI), 대소문자-무시 FS에서 잘못된
    경로 반환, `.claude` 사본이 `docs/` 접두어 빠진 경로를 가리켜 **일반본보다 나쁜 특화**(hollow). §7.5는
    본질이 판단이라 산문이 정답 — 코드로 굳히면 오히려 해로움. (교훈: 판단 작업을 코드로 박제하지 말 것.)
- **자기-독푸딩(정체성 자기모순 해소):** "문서 아키텍처를 세워주는 도구가 정작 자기 repo엔 없다"를 해소.
  ① docsherpa에 자기 라우터(`AGENTS.md` North Star 정체성 + 마커) + `CLAUDE.md` 생성 → self-gate PASS.
  ② `scaffold()`를 docsherpa 자신에 실행 → 성장 루프 설치(SessionStart 훅·prime·커밋 doc-reconcile+stamp).
  ③ §7.5 실전: 설치된 doc-reconcile 앵커를 docsherpa용으로 특화(정본은 generic 유지, 가드 GREEN).
  ④ **D1~D9 결정을 `docs/decisions/` ADR 9개로 마이그레이션**(자기 라우팅 룰 #1) — **content_oracle로
  내용 소실 0 증명**(base_segments=43 unaccounted=0) + gate PASS. **핵심가치(내용 보존 마이그레이션)를
  우리 repo에서 실증함.** ⑤ gate.py 코드펜스 false-positive 버그 수정.
- **정체성(불가침):** `AGENTS.md` 최상단 North Star = 비파괴 마이그레이션 · **내용 소실 0(깨지면 끝장)** ·
  자가성장. 흔들리면 방향 이탈. (메모리 `docsherpa-identity`에도 기록.)
- **M4 상태(중요):** 검증(A) + **격리 워크트리 실동작 확인 완료.** behavioral parity 성립(이식본≡원본,
  **마커 선주입 조건부**). **(a)(b) 커터오버를 second-brain 격리 워크트리에서 실제 적용·검증함**:
  워크트리 `~/Desktop/private/second-brain-dogfood`, 브랜치 `docsherpa-dogfood`(커밋 55f407c) —
  메인 `feat/ask-deploy` 무영향. 실동작 결과: 마커 2개(중복 섹션 0)·`has_contract_markers=True`·
  gate `markers_ok=True`·이식본 doc-reconcile 리터럴 0. broken=8/orphan=9는 second-brain **자체 문서부채**
  (MESSY, docsherpa 스코프 밖). **메인 브랜치 반영·(c) 터미널 `/plugin install`·(d) global 제거는 여전히
  게이트**(사용자가 깨끗한 정지점에 실행). 런북 = `docs/plans/M4-dogfooding.md`.
- **M2가 닫은 것:** ① `scaffold.py` — 호출 가능한 설치자 본체(라우터/docs 골격 + inject/merge 재사용 +
  prime/doc-reconcile 복사+stamp). M3의 "산문만" 결정을 사용자 승인 하에 뒤집음(자동 end-to-end 위해).
  ② 4종 fixture end-to-end GREEN(gate `--require-markers` + no-hollow 구체 산출물 + 마커 + 기존 보존).
  ③ SKILL 산문을 scaffold 위임으로 개정(결정론 부분 단일 소스). ④ 리뷰 발견 4버그 수정(howto-shadow ·
  orphan-template · JSONC-atomicity · dup-marker).
- **scaffold 스코프(중요, M4 주의):** `scaffold()`는 **greenfield/healthy 전용**. 기존에 라우터에 안 걸린
  `docs/**` 문서가 있으면(MESSY) scaffold가 자동 인덱싱 안 함 → orphan으로 gate FAIL. MESSY는 마이그레이션
  파이프라인(에이전트 discovery) 몫. **second-brain은 성숙한 docs → M4는 loop-install만 하되, 기존 docs가
  라우터에 도달 가능한지(HEALTHY) 먼저 확인**하고 scaffold를 돌려야 한다.
- **M4가 할 일(§9):** second-brain 재스캐폴드 + **behavioral parity**(재생성 doc-reconcile ↔ 원본이 동일
  변경 시나리오에 같은 신설/갱신 판정) + **기존 SessionStart 훅 보존 첫 실증** + 로컬 플러그인 경로 동작
  확인 후 중복 global setup-docs 제거. **먼저 writing-plans로 M4 계획 작성.**
- **이어가려면 이 순서로 읽어라:** ① 이 파일 → ② `docs/DESIGN.md` §9(독푸딩·behavioral parity)·§10.3 →
  ③ `docs/plans/M2-portability-fixtures.md`(scaffold가 무엇을 하는지).
- **테스트 러너:** `cd skills/setup-docs/scripts && uv run --with pytest pytest -q` (현재 **90 passed**).
- **핵심 계약:** doc-reconcile은 헤딩이 아니라 **마커**를 소비한다(D8) → M3의 마커 삽입과 맞물림.
  정본 doc-reconcile은 도메인 리터럴 0(가드 `test_doc_reconcile_portable.py`가 강제 — M3 후에도 GREEN).

---

## 미지수 → 결정 (M0)

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

## M1 완료 (doc-reconcile 이식화)

**GREEN.** doc-reconcile 이식됨 — phantom 트리거 제거(D9) + 언어-불문 마커 참조(D8) + 앵커 범용화
+ graceful degrade 명시. 이식성 가드(`test_doc_reconcile_portable.py`) GREEN, 척추 6개 보존.
setup-docs 도메인-무관 자산(SKILL·knowledge·gate·content_oracle) as-is landing. 전체 18 tests GREEN.

**다음 = M3 설치자** (setup-docs가 마커 삽입 + 루프 스캐폴드 + `merge_settings` 통합 + CLAUDE.md 주입 +
Phase0 loop 체크). 그 다음 **M2** (end-to-end fixture — 설치자 필요), **M4** 독푸딩, **M5** 공개.
(재-시퀀싱: M1→M3→M2→M4→M5. spec §12의 M2-before-M3를 codex 지적대로 뒤집음.)

## M3 완료 (setup-docs 설치자)

**GREEN.** setup-docs가 골격 생성기 → **성장 루프 설치자**로 확장됨. 위험한 것만 테스트된 코드로 격리:
- **`inject_claude_md.py`** — 기존 CLAUDE.md에 `@AGENTS.md` 안전 주입(없음/이미-import/prepend/BOM/
  frontmatter 엣지, §14). 8 tests. gate 루트 탐색이 의존.
- **`merge_settings.py` JSONC 가드** — 주석/JSONC면 크래시·클로버 대신 `ValueError`로 거부+수동 병합 안내
  (§14 결정: comment-preserving 안 지음, settings는 표준 JSON이 정상 — YAGNI). +1 test.
- **`gate.py --require-markers`** — 스캐폴드 검증에서만 D8 마커 계약 강제(opt-in — Phase0 진단 false-fail 방지).
  +3 tests. 도달성 본문은 byte-identical 보존.
- **`templates/`** — 범용 prime + 훅 템플릿(D5: 플러그인은 active 아닌 템플릿만, 도메인 리터럴 0).
- **SKILL.md 산문** — "성장 루프 설치" 섹션(opt-in·dry-run·diff-preview·D2·R4·R7), AGENTS.md 템플릿에 마커
  인라인, 기존 병합 규칙에 마커 삽입 규칙, Phase0 loop-presence 1줄. 척추(GREENFIELD/MESSY/멱등/게이트)
  외과적 보존.

전체 **30 tests GREEN**(18→30), 이식성 가드 GREEN(역누출 0). /code-review(high, 분석적) = 0 findings.
**설치-현실 테스트(§10.4)는 이연** — VSCode 채팅에서 `/plugin` 불가 → M4 독푸딩에서 실제 설치·스캐폴드 검증.

**다음 = M2 이식성 fixture**(§10.2 4종): 설치자 산문을 end-to-end로 돌려 gate PASS + hollow-없음 + 마커 grep.

## M2 완료 (이식성 fixture + scaffold 오케스트레이터)

**GREEN.** M3가 산문으로 남긴 결정론적 스캐폴드를 **호출 가능한 `scaffold.py`로 추출**(사용자 승인 하에
M3의 "산문만" 결정 뒤집음 — 자동 end-to-end 검증엔 호출 가능한 본체가 필수). `scaffold()`는 라우터/docs
골격 + `inject_claude_md_file`·`merge_settings_file`(M3 재사용) + prime/doc-reconcile 복사(+version stamp)를
한 번에 수행. SKILL 산문은 opt-in/dry-run/빈칸-채움만 담당하도록 개정(결정론 부분 단일 소스, drift 방지).

- **4종 fixture end-to-end GREEN**(§10.2): 빈 JS / 기존 AGENTS.md·번역본 / 기존 settings.json / 비영어 문서.
  각: gate `--require-markers` PASS + **hollow 아님**(`_template.md` 링크 등 구체 산출물 assert, §14) +
  마커 계약(`has_contract_markers`) + 기존 내용(커스텀 룰·훅·비영어 문서) 보존.
- **리뷰 발견 4버그 수정**(subagent code-review): ① how-to 기존 `README.md`를 placeholder `_README.md`가
  그늘 져 고아 만듦 → 인덱스 있으면 placeholder 안 만듦 ② `decisions/README.md` 기존이면 `_template.md`
  신설이 고아 → README 신설 시에만 template를 쌍으로 ③ JSONC settings가 병합 중간에 던져 부분 설치 →
  settings를 **먼저** 돌려 실패 시 다른 파일 안 씀(atomic-ish) ④ 마커 하나만 있으면 둘 다 append해 중복 →
  빠진 섹션만 append.
- **scaffold 스코프 = greenfield/healthy 전용**(리뷰 #3): 기존 미인덱스 `docs/**`가 있으면 orphan으로 gate
  FAIL(MESSY는 마이그레이션 파이프라인 몫). **M4가 second-brain에 적용 전 HEALTHY 확인 필수.**

전체 **43 tests GREEN**(30→43), 이식성 가드 GREEN. **다음 = M4 독푸딩**(behavioral parity + 기존 훅 보존
실증 + 설치-현실 + global 제거).
