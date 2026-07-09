# doc-health 스킬 — 진단 생산자 (증분 2) spec

- 상태: 제안 (증분 1 render_report 완료 → 이 증분 착수, 사용자 합의 완료)
- 날짜: 2026-07-08
- 선행: [design.md](design.md) §4·§6(진단 상세)·§14 · [render_report 계획](../../plans/2026-07-07-render-report-renderer.md)(데이터 계약)
- 파생 ADR(구현 시 신설): 모듈 분해(doc-health 추출)

> **범위:** doc-health = **읽기 전용 진단 생산자.** 전체-repo 탐색 → 9차원 채점 → 등급 → 자세 →
> render_report가 먹는 데이터 모델 **부분집합**을 반환한다. 독립 실행(수시 건강검진) + setup-docs
> Phase 0·4가 호출. **소비·변경(목표트리·마이그레이션·결정 패널)은 setup-docs 몫이지 여기 아님.**

## 0. 사용자 합의 결정 (이 증분 착수 전 확정)

| # | 결정 | 근거 |
|---|---|---|
| H1 | **M5 분모 = 흩어진 content 문서만.** 라우터(AGENTS/CLAUDE/GEMINI)·도구(`.claude/`·`.github/`·`.cursor/`)·루트 관례(README·CONTRIBUTING·CHANGELOG·SECURITY·CODE_OF_CONDUCT)는 **accounted-but-not-violation**(제자리 유지). README 비대는 M5 아니라 J3. | 라우터·도구가 M5에 들면 등급 A 원천 불가 → 채점이 거짓말. "예외 없음 이동"은 *content 문서* 대상이지 라우터·도구·관례 파일 아님 |
| H2 | **doc-health 전용 `skills/doc-health/scripts/`.** 새 `inventory.py`·`scorecard.py`는 여기. `gate`·`contract`·`render_report`는 `setup-docs/scripts`에서 재사용(`conftest.py`가 `sys.path` 부트스트랩 → `import gate` 그대로). | 스킬 자립성. 재사용은 단일 채점기 유지(정합성) — 복제 금지 |
| H3 | **`gate.analyze()` 외과적 추출.** `gate.main()`의 BFS 코어를 `analyze(root) → {broken, orphans, homes, all_docs, visited}`로 뽑고, `main()`은 그것을 호출+출력(CLI 바이트동일). scorecard가 재사용. | before/after 동일 채점기를 **코드 레벨**에서 보장(도달성 엔진 1개). 기존 gate 테스트가 회귀 방어 |

## 1. 스킬 골격 (H2)

```
skills/doc-health/
  SKILL.md                    # 에이전트 절차(탐색 디스패치·판단 J1~J4·데이터 dict 조립)
  reference/
    scoring.md                # 9차원 루브릭·등급 산식·자세 정의(doc-health 고유)
                              #   판단 휴리스틱은 setup-docs/reference/knowledge.md 참조(단일 소스)
  scripts/
    conftest.py               # setup-docs/scripts를 sys.path에 부트스트랩(import gate/contract/render_report)
    inventory.py              # list(분모 산출) · check(매니페스트 커버 → unaccounted)
    scorecard.py              # M1~M5 기계 채점 + disposition + 등급 rollup(gate.analyze 재사용)
    test_inventory.py
    test_scorecard.py
```

- **테스트 러너 추가:** `cd skills/doc-health/scripts && uv run --with pytest pytest -q`(기존 setup-docs 러너와 별개). AGENTS.md 명령어에 병기.
- **정본 산문 무침해:** 정본 doc-reconcile 리터럴 0 가드처럼, doc-health 정본도 프로젝트 리터럴 0(픽스처는 test 안에서만).

## 2. 탐색 — 2단계 (design §6a 구체화)

### 2a. `inventory.py` (결정론 — 분모)

```
inventory.py list  [ROOT]                        # → JSON {"files": ["a.md", "docs/x.md", ...]}  (repo-상대, 정렬)
inventory.py check [ROOT] --manifest m.json      # → unaccounted(목록에 있는데 매니페스트에 없는 경로) 출력, 있으면 exit 1
```

- **list:** `ROOT` 하위 전 `*.md`·`*.mdx` 나열. 결과 = "잊힌 문서 0"의 **분모**.
  - 제외 ① 빌드 정크 `node_modules`·`.git`·`dist`·`build`·`vendor`(비-git에서도 도는 pre-filter).
  - 제외 ② **`.gitignore` 대상**([ADR 0016](../../decisions/0016-inventory-respect-gitignore.md)) — 분모 = "레포가 자기 것이라 선언한 문서". git이 있으면 `git check-ignore`에 위임(중첩·전역 gitignore까지 정확), **ignored된 것만** 제외(추적 + 무시대상 아닌 새 문서는 포함), 비-git이면 폴백. → 외부 플러그인 스크래치(`.superpowers/` 등)를 우리가 하드코딩으로 판단하지 않고 자동 제외.
- **check:** 매니페스트(분류 결과)가 list를 **전부** 덮는지. `unaccounted > 0` → exit 1(STOP 신호). content_oracle `keys`/`check` 패턴과 동형.

### 2b. 병렬 분류 (SKILL.md 절차 — 코드 아님)

design §6a 2단계. 목록을 슬라이스로 나눠 병렬 서브에이전트가 각 문서 판정 →
`{path, type(ADR/spec/how-to/troubleshooting/reference/PRD/legacy), role, coupling(코드참조·외부싱크·동결역사), summary}`.
판단이라 **코드로 박제하지 않는다**(§7.5 anchor_signals.py 삭제 교훈과 정합).

### 2c. disposition — 결정론 (H1 강제)

각 inventory 경로를 경로 규칙으로 3분류(agent 판단 아님):

| disposition | 규칙(경로 기반) | M5 | 이동 |
|---|---|---|---|
| **router** | `AGENTS.md`·`CLAUDE.md`·`GEMINI.md`(`contract.ENTRY_FILENAMES`), **어느 깊이든** — 중첩 라우터는 그 서브트리의 제자리 라우터([0018](../../decisions/0018-disposition-in-place-classes.md)) | 제외 | 제자리(진입점 정의상) |
| **tooling** | `.claude/`·`.github/`·`.cursor/`·`.gitlab/` 하위 + 루트 관례(`README`·`CONTRIBUTING`·`CHANGELOG`·`SECURITY`·`CODE_OF_CONDUCT`, **대소문자 무시** — ADR 0016) + 코드-인접 중첩 `README.md`(부모 경로에 `docs` 세그먼트 없음, 대소문자 무시 — [0018](../../decisions/0018-disposition-in-place-classes.md)) | 제외 | 제자리 |
| **content** | 그 외 전부. `docs` 트리 안(어느 깊이든)의 `README.md`는 content로 남아 파묻힌 문서 인덱스도 내용과 함께 이주한다 | **분모** | 이동 대상(docs/ 밖이면 M5 위반) |

`scorecard.py`가 이 disposition을 계산 → M5 = `docs/` 밖 **content** 개수. **완결성 가드는 여전히 성립**: router·tooling도 매니페스트에 accounted(disposition으로), unaccounted=0.

## 3. 채점 — 9차원 (design §6b 구체화)

### 3a. 기계 차원 M1~M5 (`scorecard.py`, `gate.analyze` 재사용)

| 차원 | 판정 | 소스 |
|---|---|---|
| **M1 도달성** | `broken==0 and orphans==0` → pass, 아니면 fail | `gate.analyze` |
| **M2 라우터+마커** | 라우터 파일 존재 **and** `len(homes)==1` → pass | `gate.analyze` + `contract.find_marker_home` |
| **M3 맵 척추** | home Path == `docs/_map.md`(spine 추출, 인라인 아님) → pass; 인라인 home이면 fail | `gate.analyze.homes` 경로 |
| **M4 성장 루프** | `.claude/doc-drift-prime.txt` · settings.json SessionStart 훅 · `.claude/skills/doc-reconcile/SKILL.md` 3종 존재 → pass | `ls` 수준 |
| **M5 커버리지** | `docs/` 밖 content 수(2c) → 0=pass · `1..N_WARN`=warn · `>N_WARN`=fail | inventory disposition |

M1~M4 = 2치(pass/fail). M5 = 3치. `status ∈ {"pass","warn","fail"}`(render 계약과 동일).

**M2 vs M3 분리(design 모호점 해소):** M2 = 마커 계약 성립(home 1개). M3 = 그 home이 `docs/_map.md`(척추 분리). 인라인 마커 repo는 M2 ✅·M3 ❌ — 의미 있는 구별.

### 3b. 판단 차원 J1~J4 (SKILL.md 절차 — knowledge.md 렌즈)

design §6b + `setup-docs/reference/knowledge.md`(단일 소스) 사용. J1 타입분류 정확성 · J2 폴더승격 적정성 ·
J3 hollow·중복·bloat(README 비대 포함) · J4 정합성 플래그. 각 pass/warn/fail. 코드 아님(판단).

### 3c. 등급 rollup (`scorecard.py` — 결정론, 임계값 🔴 튜닝)

입력: `M[1..5]`·`J[1..4]` 상태 + 신호(`orphan_ratio`·`outside_count`·`router_present`).

```
if not router_present:                    F      # 라우터 없음
if M1==fail and orphan_ratio >= 0.5:      F      # 대부분 미도달
if M1==fail:                              D      # 다수 고아(<0.5)
if M5==fail:                              D      # 대량 밖
# 여기서 M1==pass 확정
m_nonpass = count(M2..M5 not pass)
if m_nonpass >= 3:                        D      # 도달되나 구조 취약
if m_nonpass >= 1:                        C      # M2~M5 중 1~2개
# M1~M5 전부 pass
if any(J fail) or count(J warn) >= 3:     C
if 1 <= count(J warn) <= 2:               B
                                          A      # 전 차원 pass = 완료 정의
```

임계값(`orphan_ratio 0.5`·`N_WARN`·`J warn 2`) = 🔴 열린질문(design §14, 하드닝 루프 튜닝). **구조**(M1 관문·비-pass 카운트)는 고정. 픽스처(알려진 상태)→기대 등급으로 테스트(F/D/C/B/A).

### 3d. 자세 (design §6c)

`posture_hint()`(결정론): 라우터 없음+content 최소 → GREENFIELD · 라우터+M1 pass+안티패턴 0 → HEALTHY ·
그 외 → MESSY. **MESSY 하위(중구난방·자체구조·드리프트된-docsherpa) = 에이전트 판단**(ADR 0014 계승, SKILL 산문).

## 4. 출력 데이터 계약 (render_report 부분집합)

doc-health가 **생산**하는 키(render_report 데이터 모델의 부분집합):

```python
{
  "repo":      {"name", "docs_count", "branch"},   # inventory + git(브랜치·이름)
  "grade":     {"current", "target": "A"},          # rollup
  "counts":    {"fail", "warn", "pass"},            # 9차원 tally
  "scorecard": {"mechanical": [M1..M5], "judgment": [J1..J4]},  # 각 {code,name,sub,status}
  "trees":     {"before": {...}},                   # 현재 구조(읽기전용 기술) — after는 setup-docs
  "posture":   "GREENFIELD|HEALTHY|MESSY",
  "inventory": [{path, type, disposition, coupling, summary}, ...],  # 분류 매니페스트(setup-docs Phase 1 입력)
}
```

**setup-docs가 확장**(doc-health 아님): `trees.after`·`migration`·`decisions`·`summary`.

**스키마 하드닝(이연분 종결):** doc-health가 `repo.docs_count`·`branch`를 **항상** 채워 render_report의
KeyError 경로를 닫는다. 통합 테스트로 `doc-health dict → render_report("plan")` KeyError 0 + div 밸런스 검증.

**독립 실행 렌더:** 수시 건강검진은 render_report `plan` 모드에 `migration=[]`·`decisions=[]`로 넘겨
히어로+점수표+before 트리만 렌더(빈 섹션 헤더는 표시됨 — 허용). 전용 `diagnosis` 모드는 YAGNI 이연.

## 5. 테스트 계획 (RED-first)

| 테스트 | 대상 | 기대 |
|---|---|---|
| inventory list | 합성 fixture(숨은 폴더·코드옆·루트 산재·node_modules) | 정확 목록, 제외 디렉터리 빠짐 |
| inventory check | 매니페스트에서 1개 누락 | unaccounted=[그 경로], exit 1 |
| disposition | router·tooling·content 경로 샘플 | 정확 3분류, M5 = content-outside 카운트 |
| scorecard M1~M5 | 상태별 fixture(broken·orphan·인라인마커·루프없음·docs밖) | 각 차원 pass/warn/fail 정확 |
| gate.analyze 패리티 | 추출 전후 | CLI 출력 불변 + analyze 반환이 CLI와 일치 |
| grade rollup | 알려진 차원상태 세트 | F/D/C/B/A 각각 |
| 통합 | doc-health dict → render_report("plan") | KeyError 0, div 밸런스, style= 0 |

판단(J1~J4·분류·MESSY 하위자세) = 테스트 안 함(산문 절차, §7.5 교훈).

## 6. 호출 기전 (design §14 종결)

- **독립:** doc-health 스킬 인보크 → 진단 + (선택) render_report 렌더 아티팩트.
- **setup-docs 연동:** setup-docs SKILL.md Phase 0·4가 doc-health **절차 참조**("doc-health 진단 실행 — `skills/doc-health/SKILL.md`"). 새 인보크 기계장치 없음 — repo가 이미 SKILL↔스크립트를 경로로 조립하는 방식과 정합.

## 7. 스코프 밖 (이 증분 아님)

- setup-docs 리팩터(Phase 0·4 실제 배선)·목표트리(Phase 1)·마이그레이션 실행(Phase 3)·결정 패널 데이터 = **후속 증분**.
- render_report result-모드 CSS(이연) — Phase 4 설계 시.
- 임계값 정밀 튜닝 — 하드닝 루프.
