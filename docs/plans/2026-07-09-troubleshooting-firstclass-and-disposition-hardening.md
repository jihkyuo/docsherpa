# Troubleshooting 1급 타입 + disposition 하드닝 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `troubleshooting`을 how-to 하위변종이 아닌 **1급 문서 타입**(전용 홈 `docs/troubleshooting/` + 독립 타입색)으로 승격하고, dogfood가 노출한 `contract.disposition` 사각(중첩 라우터·코드-인접 README)을 닫아 재실행 시 손편집 없이 옳은 계획이 나오게 한다.

**Architecture:** 두 독립 트랙을 한 배치로. **①(트랙 A) 트러블슈팅 1급** = 결정론 배정(`migrate._TYPE_DEST`) + 렌더 7번째 타입색(`render_report`/`migrate._after_tree`) + 도메인 문서(knowledge/scoring/SKILL supersede) + ADR 0017. **②(트랙 B) disposition 하드닝** = `contract.disposition`이 중첩 `CLAUDE.md/AGENTS.md`(DF2)와 코드-인접 중첩 `README.md`(DF1)를 제자리 skip으로 분류. 두 트랙은 서로 다른 함수를 건드려 독립(순서 무관).

**Tech Stack:** Python 3 stdlib(외부 의존 0), pytest(두 러너: setup-docs·doc-health), 동결 CSS + WCAG-AA 가드 테스트.

## Global Constraints

- **정체성 불가침(North Star):** 비파괴 마이그레이션 · **내용 소실 0** · 앵커 보존. 어떤 변경도 기존 내용을 이동만 하고 삭제·덮어쓰기 하지 않는다. (`content_oracle` unaccounted=0 · gate orphan=0 · scaffold append-only가 강제.)
- **정본 리터럴 0:** 정본 doc-reconcile은 프로젝트-특정 리터럴 0(가드 `test_doc_reconcile_portable.py`). 이 플랜은 doc-reconcile 정본을 건드리지 않는다.
- **RED-first:** 모든 코드 변경은 실패하는 테스트 먼저 → 최소 구현으로 green.
- **동결 CSS:** `render_report.TEMPLATE_CSS`의 `:root` 토큰 값(색 HEX)은 **변경 금지**. 새 타입색은 **기존 토큰 재사용만**. 새 클래스 추가는 D3/D6에서 이미 한 패턴(`.tree .t-*`, `.mig-grp.tc-*`, `.tkey .k-*`)을 따른다.
- **게이트:** 매 커밋 전 `python3 skills/setup-docs/scripts/gate.py . --require-markers`(self-gate PASS) + 두 러너 테스트 green.
- **커밋:** gitmoji + conventional. **커밋마다 origin push**(직전 세션이 이걸 빠뜨림). PR은 사용자 지시 전까지 보류(브랜치 누적).
- **테스트 러너:**
  - setup-docs: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`
  - doc-health: `cd skills/doc-health/scripts && uv run --with pytest pytest -q`
- **브랜치:** `fix/artifact-preexisting-label-beforetree`(현행 누적, 새 브랜치 만들지 않음).
- **결정(확정):** 트러블슈팅 전용 홈 = **`docs/troubleshooting/`**(완전 독립 최상위 폴더 — how-to 하위 아님). 사용자 채택(2026-07-09).
- **결정(확정):** 트러블슈팅 타입색 = **`--fail-ink`**(빨강). 유일하게 남은 서로 구별되는 동결 토큰이며 "깨짐·복구" 의미와 정합. AA on `--bg` 실측 = light 6.48 · dark 7.89(≥4.5 통과). `.stray`(before-트리 파일)와 토큰을 공유하나 같은 pane에서 공존하지 않고 범례가 구분한다.
- **범위 밖(미리 정하지 말 것):** 도메인 결정(org 타입-흩뿌림 vs 기능응집 · legacy 통합 · co-change topic)은 재실행 Phase 2 승인 게이트(§10 결정 표면화)에서. 이 플랜은 엔진 정확성만 고친다.

---

## File Structure

**트랙 A(트러블슈팅 1급) — 배정·렌더:**
- Modify: `skills/setup-docs/scripts/migrate.py` — `_TYPE_DEST`(배정) · `_AFTER_TYPECLS`·`_AFTER_ORDER`(후-트리 타입색)
- Modify: `skills/setup-docs/scripts/render_report.py` — CSS 3클래스(`tc-`/`t-`/`k-troubleshooting`) · `_SCAFFOLD_TYPECLS` · `_TYPE_GROUP` · `_render_migration` order · `_render_trees` 범례
- Test: `skills/setup-docs/scripts/test_migrate.py` · `skills/setup-docs/scripts/test_render_report.py`

**트랙 A — 도메인 문서(supersede) + ADR:**
- Modify: `skills/setup-docs/reference/knowledge.md` — L17·L27·L30 supersede
- Modify: `skills/setup-docs/SKILL.md` — 분류 라우팅 룰(§ line 189·194)
- Modify: `skills/doc-health/SKILL.md` — 타입 어휘(line 29)
- Modify: `skills/doc-health/reference/scoring.md` — J1 타입 어휘(line 45) + 절차성 가드
- Create: `docs/decisions/0017-troubleshooting-first-class-doc-type.md`
- Modify: `docs/decisions/README.md`(ADR 로그) — 0017 등록(orphan=0)

**트랙 B(disposition 하드닝):**
- Modify: `skills/setup-docs/scripts/contract.py` — `disposition()`
- Test: `skills/setup-docs/scripts/test_contract.py` · `skills/doc-health/scripts/test_scorecard.py` · `skills/setup-docs/scripts/test_migrate.py`

---

## Task 1: 배정 — troubleshooting → docs/troubleshooting/ (migrate._TYPE_DEST)

**Files:**
- Modify: `skills/setup-docs/scripts/migrate.py:22-28` (`_TYPE_DEST`)
- Test: `skills/setup-docs/scripts/test_migrate.py`

**Interfaces:**
- Consumes: `migrate.plan_moves(inventory)` — inventory 항목 `{"path", "type", ...}`, 결정론 type→folder.
- Produces: `type == "troubleshooting"` 인 문서 → `docs/troubleshooting/<name>`. (topic/spec/legacy/.mdx 분기는 불변.)

- [ ] **Step 1: 실패하는 테스트 작성** — `test_migrate.py` 끝에 추가:

```python
def test_plan_moves_troubleshooting_to_own_folder():
    inv = [
        {"path": "recover-db.md", "type": "troubleshooting"},
        {"path": "fix-oom.md", "type": "troubleshooting"},
    ]
    dests = {p["src"]: p["dest"] for p in migrate.plan_moves(inv)}
    assert dests["recover-db.md"] == "docs/troubleshooting/recover-db.md"
    assert dests["fix-oom.md"] == "docs/troubleshooting/fix-oom.md"
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_migrate.py::test_plan_moves_troubleshooting_to_own_folder -q`
Expected: FAIL — `docs/recover-db.md` (기본 `_TYPE_DEST.get(...,'docs')`로 떨어짐) ≠ 기대.

- [ ] **Step 3: 최소 구현** — `_TYPE_DEST`에 한 줄 추가:

```python
_TYPE_DEST = {
    "ADR": "docs/decisions",
    "how-to": "docs/how-to",
    "troubleshooting": "docs/troubleshooting",
    "PRD": "docs/product",
    "reference": "docs",
    "explanation": "docs",
}
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_migrate.py -q`
Expected: PASS(신규 포함 전부).

- [ ] **Step 5: 커밋 + push**

```bash
git add skills/setup-docs/scripts/migrate.py skills/setup-docs/scripts/test_migrate.py
git commit -m "✨ feat(migrate): troubleshooting 1급 타입 배정 — docs/troubleshooting/ (①-1)"
git push origin fix/artifact-preexisting-label-beforetree
```

---

## Task 2: 렌더 — 7번째 타입색(troubleshooting) 배선 + AA 가드

**Files:**
- Modify: `skills/setup-docs/scripts/render_report.py` — CSS(3클래스) · `_SCAFFOLD_TYPECLS`(line 327) · `_TYPE_GROUP`(line 401) · `_render_migration` order(line 423) · `_render_trees` 범례(line 381-385)
- Modify: `skills/setup-docs/scripts/migrate.py:410-412` — `_AFTER_TYPECLS`·`_AFTER_ORDER`(후-트리 타입색)
- Test: `skills/setup-docs/scripts/test_render_report.py`

**Interfaces:**
- Consumes: `migrate._after_tree(move_plan)`(폴더→타입색 클래스) · `render_report.render_report(data, mode)`.
- Produces: `docs/troubleshooting/` 폴더가 렌더 3곳(후-트리·스캐폴딩·집약뷰)에서 `tc-troubleshooting`/`t-troubleshooting` 클래스로, 범례에 `k-troubleshooting` 한 칸으로 나타난다. AA 가드에 `("--fail-ink","--bg",4.5)` 추가.

- [ ] **Step 1: 실패하는 테스트 작성** — `test_render_report.py`에 두 테스트 추가:

```python
def test_troubleshooting_type_color_in_migration_and_tree():
    d = {**MIN, "migration": [
        {"src": "recover.md", "dest": "docs/troubleshooting/recover.md", "ops": ["move"], "impact": None},
    ]}
    html = render_report(d, "plan")
    assert "tc-troubleshooting" in html      # 집약뷰 그룹 타입색
    assert "t-troubleshooting" in html       # 접이식 스캐폴딩(after) 폴더색
    assert "문제 해결" in html                # 그룹/범례 표시명
    assert "k-troubleshooting" in html        # Before→After 범례 스와치

def test_troubleshooting_aa_pair_registered():
    assert ("--fail-ink", "--bg", 4.5) in AA_PAIRS
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_render_report.py::test_troubleshooting_type_color_in_migration_and_tree test_render_report.py::test_troubleshooting_aa_pair_registered -q`
Expected: FAIL — 클래스/문자열/AA 페어 부재.

- [ ] **Step 3a: CSS 3클래스 추가**(동결 토큰 재사용, `render_report.py`)

`.mig-grp.tc-flat` 아래(line 207 다음)에 추가:
```python
  .mig-grp.tc-troubleshooting { border-left-color:var(--fail-ink); }
```
`.tree .t-legacy` 앞/뒤(line 227 부근)에 추가:
```python
  .tree .t-troubleshooting { color:var(--fail-ink); font-weight:600; }
```
`.tkey .k-legacy` 줄(line 239) 앞에 추가:
```python
  .tkey .k-troubleshooting { color:var(--fail-ink); }
```

- [ ] **Step 3b: 렌더 매핑 3곳 추가**(`render_report.py`)

`_SCAFFOLD_TYPECLS`(line 327):
```python
_SCAFFOLD_TYPECLS = {"product": "t-prd", "specs": "t-spec",
                     "decisions": "t-adr", "how-to": "t-howto",
                     "troubleshooting": "t-troubleshooting"}
```
`_TYPE_GROUP`(line 401):
```python
_TYPE_GROUP = {   # docs/ 아래 1단계 폴더 → (표시명, tc-클래스)
    "decisions": ("결정 기록 (ADR)", "tc-adr"),
    "specs": ("명세 (spec)", "tc-spec"),
    "how-to": ("작업 절차·복구 (how-to)", "tc-howto"),
    "troubleshooting": ("문제 해결 (troubleshooting)", "tc-troubleshooting"),
    "product": ("제품 요구 (PRD)", "tc-prd"),
}
```
`_render_migration`의 `order`(line 423):
```python
    order = ["product", "specs", "decisions", "how-to", "troubleshooting", "_flat"]
```

- [ ] **Step 3c: Before→After 범례에 troubleshooting 칸 추가**(`render_report.py` `_render_trees`, line 384 `k-howto` span 다음)

```python
            '<span><b class="k-howto">■</b> 작업 절차·복구(how-to)</span>'
            '<span><b class="k-troubleshooting">■</b> 문제 해결(troubleshooting)</span>'
            '<span><b class="k-legacy">■</b> 동결(legacy)</span></div>'
```

- [ ] **Step 3d: 후-트리 타입색 매핑 추가**(`migrate.py` line 410-412)

```python
_AFTER_TYPECLS = {"product": "t-prd", "specs": "t-spec",
                  "decisions": "t-adr", "how-to": "t-howto",
                  "troubleshooting": "t-troubleshooting"}
_AFTER_ORDER = ["product", "specs", "decisions", "how-to", "troubleshooting", "_flat"]
```

- [ ] **Step 3e: AA 가드 페어 추가**(`test_render_report.py` `AA_PAIRS`, line 43 다음)

```python
    # 트러블슈팅 1급 타입색(t-troubleshooting = fail-ink)이 --bg 위에 노출 → AA 강제
    ("--fail-ink", "--bg", 4.5),
```

- [ ] **Step 4: 테스트 통과 확인**(신규 + 기존 AA 가드 both-theme)

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_render_report.py -q`
Expected: PASS — 신규 2건 + `test_contrast_aa_both_themes`(fail-ink/bg light 6.48·dark 7.89 통과).

- [ ] **Step 5: 커밋 + push**

```bash
git add skills/setup-docs/scripts/render_report.py skills/setup-docs/scripts/migrate.py skills/setup-docs/scripts/test_render_report.py
git commit -m "🎨 feat(render): troubleshooting 7번째 타입색(fail-ink) — 집약뷰·트리·범례·AA가드 (①-2)"
git push origin fix/artifact-preexisting-label-beforetree
```

---

## Task 3: 타입 어휘 확장 + 절차성 가드 (doc-health 분류 문서)

**Files:**
- Modify: `skills/doc-health/SKILL.md:29` (`type ∈ ...`)
- Modify: `skills/doc-health/reference/scoring.md:45` (J1 타입 목록 + 절차성 가드)
- Test: gate green(문서 전용 — pytest 대상 아님, Task 6에서 통합 검증)

**Interfaces:**
- Consumes: 병렬 분류 서브에이전트가 산출하는 매니페스트 `type` 필드.
- Produces: `type` 어휘에 `troubleshooting` 포함 → 분류자가 how-to와 구별해 태깅. J1이 절차성(link-only 금지)을 fail 기준으로 채점.

- [ ] **Step 1: doc-health SKILL.md 타입 어휘 확장** — line 29를 다음으로:

```markdown
   - `type` ∈ ADR/spec/how-to/troubleshooting/reference/PRD/legacy.
```

- [ ] **Step 2: scoring.md J1 타입 목록 + 절차성 가드** — line 45(J1 행)의 타입 목록에 `troubleshooting` 추가하고, "복구 절차인데 link-only면 fail" 기준을 명시:

```markdown
| **J1** | 타입분류 정확성 | 분류 매니페스트의 `type`(ADR/spec/how-to/troubleshooting/reference/PRD/legacy)이 문서 실제 내용과 맞는가. 예: "왜" 문서인데 how-to로 분류됐다면 fail. **트러블슈팅은 실제 절차(명령·진단·복구)여야 — symptom→link뿐인 링크-전용이면 troubleshooting 아님(Status로 붕괴, fail).** |
```

- [ ] **Step 3: 게이트·러너 확인**(문서만 바뀜 — 회귀 없음 확인)

Run: `cd skills/doc-health/scripts && uv run --with pytest pytest -q`
Expected: PASS(회귀 0).
Run: `python3 skills/setup-docs/scripts/gate.py . --require-markers`
Expected: `PASS: broken=0 orphan=0 ... markers_ok=True`.

- [ ] **Step 4: 커밋 + push**

```bash
git add skills/doc-health/SKILL.md skills/doc-health/reference/scoring.md
git commit -m "📝 docs(doc-health): 타입 어휘에 troubleshooting 추가 + J1 절차성 가드(link-only 금지) (①-3)"
git push origin fix/artifact-preexisting-label-beforetree
```

---

## Task 4: 분류 라우팅 룰 + knowledge.md supersede

**Files:**
- Modify: `skills/setup-docs/SKILL.md` — 분류 라우팅 룰(line 189·194 부근)
- Modify: `skills/setup-docs/reference/knowledge.md:17,27,30` — supersede

**Interfaces:**
- Consumes: Phase 1a 분류(에이전트 판단)가 이 룰을 읽어 troubleshooting 문서를 `docs/troubleshooting/`로 배정(엔진은 Task 1이 배선).
- Produces: SKILL 산문이 troubleshooting을 how-to와 분리된 1급 목적지로 안내 + knowledge.md가 옛 stance(how-to로 접음)를 supersede.

- [ ] **Step 1: setup-docs SKILL.md 분류 룰에 troubleshooting 행 추가** — line 189("절차/복구(어떻게) → how-to/*.md") 다음 줄에 삽입(번호는 기존 목록 맥락에 맞춰 조정):

```markdown
3. 절차/복구(어떻게) → how-to/*.md (3개↑면 _README 인덱스화)
   3t. 장애 복구(깨졌을 때 무엇을·어떻게) → troubleshooting/*.md — **실제 절차(명령·진단·복구)일 때만.** symptom→link뿐인 링크-전용은 만들지 말고 증상 alias를 주인 문서(한계·개념)에 넣는다(1급 승격 후에도 유지되는 가드, ADR 0017).
```

- [ ] **Step 2: line 194 가드 문구를 1급 승격과 정합하게 조정** — 기존:

```markdown
※ 증상 alias는 별도 troubleshooting 문서 말고 주인 문서(한계·개념)에 넣는다.
```
을 다음으로(troubleshooting은 이제 실절차용 1급 홈이 있고, 가드는 link-only 금지로 유지):
```markdown
※ 링크-전용(symptom→link) 증상 목록은 troubleshooting/ 문서로 만들지 말고 주인 문서(한계·개념)에 넣는다. troubleshooting/은 실제 복구 절차(명령·진단·복구)가 있을 때만(ADR 0017).
```

- [ ] **Step 3: knowledge.md L17 supersede 주석** — line 17(Diátaxis=폴더 아님) 끝에 예외 명시:

```markdown
5. **Diátaxis = 인덱스 렌즈, 폴더 아님**[🟡]: tutorial/how-to/reference/explanation은 커버리지 점검 사고틀이지 물리 폴더 아님. (사람 문서엔 권위, **Claude 공식 아님**) — **예외: troubleshooting은 1급 타입으로 전용 폴더 `docs/troubleshooting/`에 식별한다(ADR 0017 — how-to와 구별 필요).**
```

- [ ] **Step 4: knowledge.md L27 타입표 갱신** — Troubleshooting 행의 "산다" 열을 `how-to/`에서 `troubleshooting/`로, 1급임을 명시:

```markdown
| **Troubleshooting** | 깨졌을 때 **무엇을** | **반응적 복구 — 절차(명령·진단·복구)**, 1급 타입(ADR 0017) | `troubleshooting/` |
```

- [ ] **Step 5: knowledge.md L30 가드 유지 주석** — line 30 끝에 승계 명시:

```markdown
- ⚠️ **Troubleshooting은 절차여야 한다.** symptom→link뿐이면 Status로 붕괴 → **링크-전용 트러블슈팅 문서 만들지 마라.** 증상 alias는 주인 문서(한계 목록·개념 함정)에 넣고, `troubleshooting/`은 실제 절차가 생길 때 졸업. (1급 승격 후에도 유지되는 핵심 가드 — ADR 0017.)
```

- [ ] **Step 6: 게이트 확인**(SKILL/knowledge 편집 — 마이그레이션 없음, 회귀만 확인)

Run: `python3 skills/setup-docs/scripts/gate.py . --require-markers`
Expected: `PASS: broken=0 orphan=0 ... markers_ok=True`.
Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_doc_reconcile_portable.py -q`
Expected: PASS(정본 리터럴 0 — 이 편집은 doc-reconcile 정본 아님, 회귀 0 확인).

- [ ] **Step 7: 커밋 + push**

```bash
git add skills/setup-docs/SKILL.md skills/setup-docs/reference/knowledge.md
git commit -m "📝 docs(setup-docs): troubleshooting 1급 분류 룰 + knowledge L17·L27·L30 supersede (①-4)"
git push origin fix/artifact-preexisting-label-beforetree
```

---

## Task 5: ADR 0017 신설 + 등록 (orphan=0)

**Files:**
- Create: `docs/decisions/0017-troubleshooting-first-class-doc-type.md`
- Modify: `docs/decisions/README.md`(ADR 로그 — 0017 링크 추가)

**Interfaces:**
- Consumes: `gate.analyze(.)` 도달성(신규 ADR가 로그에서 링크돼야 orphan=0).
- Produces: 결정 기록 — troubleshooting 1급 승격이 knowledge.md stance를 부분 supersede함을 append-only ADR로 고정.

- [ ] **Step 1: ADR 파일 작성** — `docs/decisions/0017-troubleshooting-first-class-doc-type.md`:

```markdown
# 0017. Troubleshooting을 1급 문서 타입으로 승격

- 상태: 채택(2026-07-09)
- 관련: [0013](0013-prd-first-class-doc-type.md)(PRD 1급 선례) · [doc-type-templates 트랙](../specs/doc-type-templates/design.md)

## 맥락

vd-front dogfood 진단서 리뷰에서 실증: 분류 type 어휘(`ADR·spec·how-to·reference·PRD·legacy`)에
**`troubleshooting` 타입 자체가 없었다.** `reference/knowledge.md`(문서타입표 L27, 가드 L30)가
Troubleshooting을 "반응적 복구 절차 → `how-to/`"로 접어, 트러블슈팅 문서가 how-to로 분류돼
**가이드와 식별 불가**하고 전용 홈이 없었다. 아티팩트 범례가 이 사실을 은폐(자기설명 실패).

## 결정 (B안 — 1급 승격)

1. **분류 어휘에 `troubleshooting` 추가** — doc-health 분류/scorecard가 how-to 하위변종이 아닌
   독립 type으로 식별. 질문어 = "깨졌을 때 무엇을·어떻게 복구".
2. **전용 홈 = `docs/troubleshooting/`** — 완전 독립 최상위 폴더(how-to 하위 아님). PRD/specs처럼
   온디맨드(첫 troubleshooting 문서 유입 시 `register`가 폴더 인덱스 생성).
3. **배정** — `migrate._TYPE_DEST["troubleshooting"] = "docs/troubleshooting"`. render 타입색·범례·
   트리에 troubleshooting 추가(6→7색, `--fail-ink` 재사용, AA on `--bg` 통과).
4. **진단 차원** — J1이 트러블슈팅 절차성을 채점(link-only면 fail).

## 승계하는 가드레일 (설계 정신 보존)

트러블슈팅은 **진짜 절차**(명령·진단·복구)여야 한다. `symptom→link`만인 **링크-전용 트러블슈팅
금지**(Status 복제·부패). 증상 alias는 주인 문서(한계·개념 함정)에. 1급 승격 후에도 유지.

## Supersede

- `reference/knowledge.md` L17(Diátaxis=폴더 아님) — troubleshooting은 **예외**로 식별 필요.
- `reference/knowledge.md` L27(타입표 how-to/ 매핑) — 산다 열 `how-to/` → `troubleshooting/`.
- `reference/knowledge.md` L30(가드) — 유지하되 홈이 `troubleshooting/`로 이동.

기존 문서 내용은 삭제하지 않는다 — stance 주석으로 supersede만 표기(append-only 정신).

## 결과

- 트러블슈팅이 가이드와 색·폴더로 구별됨(자기설명 회복).
- link-only 가드 유지로 Status 복제 부패 방지.
```

- [ ] **Step 2: ADR 로그에 0017 등록** — `docs/decisions/README.md`에서 기존 ADR 목록 형식을 따라 0017 링크 한 줄 추가(0016 다음). 먼저 기존 형식 확인:

Run: `grep -n "0016\|0015" docs/decisions/README.md`
그다음 같은 형식으로 한 줄 추가(예시 — 실제 라벨·문법은 파일의 기존 줄을 그대로 모방):
```markdown
- [0017](0017-troubleshooting-first-class-doc-type.md) — Troubleshooting 1급 문서 타입 승격
```

- [ ] **Step 3: 게이트로 orphan=0 확인**(신규 ADR가 로그에서 도달 가능)

Run: `python3 skills/setup-docs/scripts/gate.py . --require-markers`
Expected: `PASS: broken=0 orphan=0 ... markers_ok=True`.
(FAIL 시 — orphan 목록에 `docs/decisions/0017-*.md`가 있으면 Step 2 링크 누락. broken이면 ADR 본문 상대링크 오타.)

- [ ] **Step 4: 커밋 + push**

```bash
git add docs/decisions/0017-troubleshooting-first-class-doc-type.md docs/decisions/README.md
git commit -m "📝 docs(decisions): ADR 0017 — troubleshooting 1급 타입 승격(knowledge 부분 supersede) (①-5)"
git push origin fix/artifact-preexisting-label-beforetree
```

---

## Task 6: 트랙 A 통합 검증 (두 러너 + self-gate)

**Files:**
- Test: 전체 스위트(신규 코드 없음 — 통합 게이트)

**Interfaces:**
- Consumes: Task 1~5 산출물 전체.
- Produces: 트랙 A가 두 러너 + self-gate green임을 확증(재실행 전 엔진 정확성 확보).

- [ ] **Step 1: setup-docs 러너 전체**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`
Expected: 전부 PASS(직전 baseline 171 + 신규).

- [ ] **Step 2: doc-health 러너 전체**

Run: `cd skills/doc-health/scripts && uv run --with pytest pytest -q`
Expected: 전부 PASS(직전 baseline 32).

- [ ] **Step 3: self-gate**

Run: `python3 skills/setup-docs/scripts/gate.py . --require-markers`
Expected: `PASS: broken=0 orphan=0 ... markers_ok=True`.

- [ ] **Step 4: (검증-보고)** 실패 시 해당 Task로 복귀. 통과면 트랙 A 완료 — 별도 커밋 없음(코드 변경 없는 검증 단계).

---

## Task 7: disposition 하드닝 — DF2(중첩 라우터) + DF1(코드-인접 README)

**Files:**
- Modify: `skills/setup-docs/scripts/contract.py:25-39` (`disposition()`)
- Test: `skills/setup-docs/scripts/test_contract.py` · `skills/doc-health/scripts/test_scorecard.py` · `skills/setup-docs/scripts/test_migrate.py`

**Interfaces:**
- Consumes: `contract.disposition(rel_path)` — 소비자: `migrate.plan_moves`(router/tooling skip) · `scorecard.outside_content`/`posture_hint`(M5 분모).
- Produces: 중첩 `CLAUDE.md`/`AGENTS.md`/`GEMINI.md` → `"router"`(DF2, 제자리 skip) · 코드-인접 중첩 `README.md`(docs/ 밖) → `"tooling"`(DF1, 제자리 skip, basename 충돌 원천 차단). `docs/**/README.md`는 불변(`"content"`).

- [ ] **Step 1: 실패하는 테스트 작성 — contract**(`test_contract.py`, `test_disposition_router_tooling_content` 다음에 추가):

```python
def test_disposition_nested_router_and_code_adjacent_readme():
    # DF2: 중첩 라우터(스코프 CLAUDE.md/AGENTS.md)는 어느 깊이든 라우터 → 제자리 skip
    assert contract.disposition("src/features/x/CLAUDE.md") == "router"
    assert contract.disposition("sub/AGENTS.md") == "router"
    # DF1: 코드-인접 중첩 README(mocks·api)는 중앙집중 대상 아님 → tooling(제자리 skip)
    assert contract.disposition("src/features/x/mocks/README.md") == "tooling"
    assert contract.disposition("src/apis/readme.md") == "tooling"
    # docs/ 아래 README(폴더 인덱스)는 content 유지 — DF1이 과확장 안 함
    assert contract.disposition("docs/how-to/README.md") == "content"
    # 루트 관례 README는 기존대로 tooling
    assert contract.disposition("README.md") == "tooling"
```

- [ ] **Step 2: 실패하는 테스트 작성 — scorecard**(`test_scorecard.py`, line 28 근처의 기존 `sub/AGENTS.md == "content"` 단정을 **새 동작으로 갱신** + 중첩 README 케이스 추가). 먼저 line 28을 교체:

```python
    assert scorecard.disposition("sub/AGENTS.md") == "router"   # DF2: 중첩 라우터 제자리 skip
```
그리고 `test_disposition_root_convention_case_insensitive`(line 253) 다음에 추가:
```python
def test_disposition_nested_readme_is_inplace_tooling():
    # DF1: 코드-인접 README는 outside_content(M5)에도 안 잡힌다(중앙집중 대상 아님)
    assert scorecard.disposition("src/x/mocks/README.md") == "tooling"
    assert scorecard.outside_content(["src/x/mocks/README.md", "notes.md"]) == ["notes.md"]
```

- [ ] **Step 3: 실패하는 테스트 작성 — plan_moves 통합**(`test_migrate.py`, `test_plan_moves_collision_raises` 뒤에 추가) — 중첩 README/CLAUDE.md가 이동에서 빠져 basename 충돌이 안 남을 실증:

```python
def test_plan_moves_skips_nested_router_and_readme_no_collision():
    inv = [
        {"path": "src/a/mocks/README.md", "type": "reference"},   # DF1 → skip
        {"path": "src/b/api/README.md", "type": "reference"},     # DF1 → skip(둘 다면 예전엔 docs/README.md 충돌)
        {"path": "src/a/CLAUDE.md", "type": "reference"},         # DF2 → skip
        {"path": "guide.md", "type": "how-to"},                   # 정상 이동
    ]
    plan = migrate.plan_moves(inv)                                # 충돌 ValueError 안 남
    dests = {p["src"]: p["dest"] for p in plan}
    assert "src/a/mocks/README.md" not in dests
    assert "src/b/api/README.md" not in dests
    assert "src/a/CLAUDE.md" not in dests
    assert dests["guide.md"] == "docs/how-to/guide.md"
```

- [ ] **Step 4: 세 테스트 실패 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest test_contract.py::test_disposition_nested_router_and_code_adjacent_readme test_migrate.py::test_plan_moves_skips_nested_router_and_readme_no_collision -q`
Run: `cd skills/doc-health/scripts && uv run --with pytest pytest test_scorecard.py::test_disposition_nested_readme_is_inplace_tooling -q`
Expected: 모두 FAIL — 중첩 라우터=content(현행) · 중첩 README=content(현행, plan_moves 충돌).

- [ ] **Step 5: 최소 구현** — `contract.py`의 `disposition()`을 다음으로:

```python
def disposition(rel_path):
    """repo-상대 경로 → 'router'|'tooling'|'content' (경로 규칙, 판단 아님).

    N11 spine·배정 엔진의 공유 단일소스(gate·scorecard·migrate). 파일 IO 없음."""
    parts = Path(rel_path).parts
    if not parts:
        return "content"
    name = parts[-1]
    if name in ENTRY_FILENAMES:                 # DF2: 라우터는 어느 깊이든 라우터(중첩 CLAUDE.md 제자리 skip)
        return "router"
    if parts[0] in _TOOLING_DIRS:
        return "tooling"
    if len(parts) == 1 and name.lower() in _ROOT_CONVENTION:
        return "tooling"
    if name.lower() == "readme.md" and parts[0] != "docs":   # DF1: 코드-인접 중첩 README = 제자리(중앙집중 대상 아님, basename 충돌 차단)
        return "tooling"
    return "content"
```

주의: DF2 분기(`if name in ENTRY_FILENAMES`)에서 기존 `len(parts) == 1` 가드를 제거한 것이 핵심. DF1 분기는 루트 README(기존 `_ROOT_CONVENTION` 분기가 이미 처리) 뒤에 두어 **중첩** README만 새로 잡는다.

- [ ] **Step 6: 세 테스트 통과 + 전체 회귀 확인**

Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q`
Expected: PASS(신규 + 기존 `test_disposition_router_tooling_content` 불변).
Run: `cd skills/doc-health/scripts && uv run --with pytest pytest -q`
Expected: PASS(갱신된 `sub/AGENTS.md == "router"` 포함).

- [ ] **Step 7: self-gate**(docsherpa 자체 repo에 중첩 라우터/README가 있으면 disposition 변화가 self-gate에 영향 없는지 확인)

Run: `python3 skills/setup-docs/scripts/gate.py . --require-markers`
Expected: `PASS: broken=0 orphan=0 ... markers_ok=True`.
(gate.py는 disposition을 import하지 않고 루트 ENTRY_FILENAMES만 roots로 쓰므로 영향 없음 — 확증용.)

- [ ] **Step 8: 커밋 + push**

```bash
git add skills/setup-docs/scripts/contract.py skills/setup-docs/scripts/test_contract.py skills/setup-docs/scripts/test_migrate.py skills/doc-health/scripts/test_scorecard.py
git commit -m "🐛 fix(contract): disposition 하드닝 — 중첩 라우터(DF2)·코드-인접 README(DF1) 제자리 skip (②)"
git push origin fix/artifact-preexisting-label-beforetree
```

---

## Task 8: doc-reconcile + FINDINGS 갱신 (배치 마무리)

**Files:**
- Modify: `FINDINGS.md` — ▶️ 다음 작업 블록 갱신(①② 완료 → ③ vd-front 재실행 대기)
- (조건부) doc-reconcile 스킬이 요구하는 추가 문서

**Interfaces:**
- Consumes: Task 1~7 산출물.
- Produces: 상태 문서가 실제와 정합 — 다음 세션이 ③(재실행)부터 이어감.

- [ ] **Step 1: doc-reconcile 실행**(코드·정책·구조 변경 마무리 — SessionStart prime 요구)

Skill 호출: `docsherpa:doc-reconcile`. 이 배치가 낡게 만든 문서(있으면) 갱신 + AGENTS.md 아키텍처가 요구하는 신규 문서 확인. ADR 0017은 Task 5에서 이미 신설했으므로 중복 생성 금지 — reconcile이 추가로 요구하는 것만.

- [ ] **Step 2: FINDINGS.md ▶️ 블록 갱신** — ①② 완료 표시, ③(vd-front 재실행: 시험 브랜치 `docsherpa/migrate-59f05e69` 폐기 후 재진단)·④(재실행 Phase 2에서 도메인 결정)를 다음 작업으로. ②가 disposition에 반영됐으므로 "매니페스트 손편집 우회"가 이제 자동 처리됨을 명시(재실행이 검증).

- [ ] **Step 3: 최종 게이트 + 두 러너**

Run: `python3 skills/setup-docs/scripts/gate.py . --require-markers` → PASS
Run: `cd skills/setup-docs/scripts && uv run --with pytest pytest -q` → PASS
Run: `cd skills/doc-health/scripts && uv run --with pytest pytest -q` → PASS

- [ ] **Step 4: 커밋 + push**

```bash
git add FINDINGS.md docs/
git commit -m "📝 docs(findings): ①트러블슈팅 1급 + ②disposition 하드닝 완료 → ③ vd-front 재실행 대기"
git push origin fix/artifact-preexisting-label-beforetree
```

---

## 위험·핵심 교차검증 (권장)

Task 7(disposition)은 **엔진 핵심 단일소스** 변경(gate·scorecard·migrate 공유)이라 위험도 높음.
Task 7 완료 후 `/code-review`(high) + `/codex`(다른 모델 critic) 교차검증 권장. 특히:
- DF1이 `docs/**/README.md`(폴더 인덱스)를 tooling으로 과확장하지 않는지(테스트가 커버하나 재확인).
- DF2가 gate의 루트-only roots 가정과 충돌 없는지(gate는 disposition 미사용 — 확증).
- 중첩 라우터를 skip해 제자리에 두면 그 문서가 orphan/내용소실로 이어지지 않는지(tooling = 도달성 면제, 내용 보존).

## Self-Review (작성자 체크)

- **스펙 커버리지:** ①(1)어휘=Task3 · ①(2)전용홈 docs/troubleshooting/=Task1 확정 · ①(3)plan_moves 배정=Task1, render 6→7색=Task2 · ①(4)절차성 차원=Task3 · supersede knowledge L17·L27·L30=Task4 · ADR 신설=Task5. ②DF1/DF2=Task7(RED-first 합성 fixture: 중첩 README·CLAUDE.md). ③④는 이 플랜 범위 밖(재실행·도메인 결정) — 의도적 제외.
- **Placeholder 스캔:** 코드 스텝 전부 실제 코드 포함. Task5 Step2·Task8은 기존 파일 형식 모방(grep으로 확인 후) — "형식 그대로 모방"은 파일별 문법이 달라 명시적으로 grep 선행을 지시(placeholder 아님).
- **타입 정합성:** `troubleshooting` type 문자열·`docs/troubleshooting` 경로·`t-troubleshooting`/`tc-troubleshooting`/`k-troubleshooting` 클래스명·`--fail-ink` 토큰이 Task 1·2·4·5 전반에서 일관. disposition 반환값 `"router"|"tooling"|"content"` 3값 계약 불변(신규 카테고리 없음 — 소비자 안전).
