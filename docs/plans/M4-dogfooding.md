# M4 — 독푸딩 (second-brain 재스캐폴드) 검증 + 커터오버 런북

> **성격:** M1–M3와 달리 M4는 **바깥 repo(second-brain)와 사용자 환경(global setup-docs)·터미널
> `/plugin`**을 건드린다. 그래서 이 문서는 (A) 이번 세션에 안전하게 끝낸 **검증**과 (B) 사용자가
> 승인/터미널에서 실행할 **게이트된 커터오버 런북**으로 나뉜다.

**Goal(§9):** docsherpa의 이식된 doc-reconcile이 second-brain 원본과 **behavioral parity**(같은 변경에
같은 신설/갱신 판정)를 가짐을 증명하고, 성장 루프를 second-brain에 **커밋 스캐폴드**(마커 주입 + 훅 보존
+ doc-reconcile 교체)한 뒤, 로컬 플러그인 경로 확인 후 중복 global setup-docs를 제거한다.

---

## A. 검증 (이번 세션 — 완료, 안전)

### A1. Behavioral parity — 이식본 ≡ 원본 (given markers)

`diff docsherpa/skills/doc-reconcile/SKILL.md  second-brain/.claude/skills/doc-reconcile/SKILL.md`가
보여주는 **유일한 차이 = M1 일반화**뿐:
- description의 phantom "pre-commit docs-impact 게이트" 트리거 제거(D9) — 그 게이트는 second-brain에도
  **없음** → 제거는 **행동적으로 inert**(트리거가 애초에 발화 안 함).
- 앵커 locator: 이식본=마커(`<!-- docsherpa:routing -->`), 원본=헤딩 문자열("문서 라우팅 룰"). **같은
  섹션**을 가리킴(D8).
- 앵커 예시: 이식본=일반형("스펙 문서(있으면)"), 원본=리터럴(`SPEC.md`·`config.py`·`ARCHITECTURE.md`).
  second-brain엔 그 대상 문서가 **전부 존재** → 일반형이 같은 구체 문서로 해석 → **같은 판정**.
- graceful degrade 명시 추가 — second-brain 대상 문서가 다 있어 **발화 안 함**(무영향).

**판정 엔진·척추(§2~§5)는 byte-identical**(양방향·spec≠ADR·"배웠나" 트리거·anti-hallucination·canonical
방향·closeout). 판정의 정본은 **AGENTS.md 자신**(둘 다 위임) → 스킬 텍스트 차이가 판정을 바꾸지 않음.

**⚠️ 유일한 전제(critical):** 이식본은 **마커로** 라우팅/인덱스 섹션을 찾는다. second-brain AGENTS.md엔
**마커가 없다(0)**. → **마커 주입이 doc-reconcile 교체보다 반드시 선행**해야 parity가 성립(D8 결합).

**결론: parity 성립 — 단, 마커 선주입 조건부.** 원본 교체 안전.

### A2. 결정론적 3-op을 second-brain 실제 파일에 dry-run(temp copy, 무-쓰기) — 통과

| op | 대상(실제 second-brain) | 결과 |
|---|---|---|
| 마커 주입 | AGENTS.md | changed=True, **markers_now=True, 기존 내용 보존=True** |
| settings 병합 | .claude/settings.json | **changed=False(dedup)** — 기존 훅이 우리 HOOK_CMD와 동일 → byte-identical 무변경 |
| CLAUDE.md 주입 | CLAUDE.md(=`@AGENTS.md`) | changed=False(이미 import) |

→ **"기존 SessionStart 훅 보존"의 최악 케이스가 실증됨**(§9): second-brain 훅 =
`cat .claude/doc-drift-prime.txt 2>/dev/null || true` = 우리 HOOK_CMD → **멱등 no-op**. 훅 유실 0.

### A3. second-brain 현재 gate 상태 — MESSY(우리 스코프 밖)

`gate.py second-brain` = **FAIL: broken=8, orphan=10**(docs=56). 원인은 second-brain **자체 문서 부채**:
- broken 8: `docs/superpowers/specs/...`가 sibling `../../../web/*`를 링크(repo 밖).
- orphan 10: `docs/superpowers/plans/*`가 인덱스 미등록.

**이건 docsherpa가 고칠 대상이 아니다.** scaffold는 greenfield/healthy 전용(M2 리뷰 #3). 루프 설치
(마커+훅+doc-reconcile)와 문서-부채 청소는 **별개** — 후자는 second-brain의 독립 MESSY 마이그레이션
(추후 `/docsherpa:setup-docs` MESSY 경로로). M4 커터오버는 gate GREEN을 요구하지 않는다.

---

## B. 커터오버 런북 (게이트 — 사용자 승인/터미널)

> 순서 중요: **마커 → doc-reconcile 교체**(A1 전제). settings/CLAUDE는 이미 정상(A2) → 무작업.
> second-brain은 git repo → (a)(b)는 **git-reversible**. (c)(d)는 되돌리기 신중.

### (a) 마커 주입 — second-brain/AGENTS.md [git-reversible, 2줄 외과 편집]

기존 섹션이 이미 있으므로 **중복 append 금지** — 기존 헤딩 2개에 마커만 붙인다:
- L40 `## 먼저 읽기 (마스터 문서 인덱스)` → 끝에 ` <!-- docsherpa:index -->`
- L61 `## 문서 라우팅 룰 (새 문서가 어디로)` → 끝에 ` <!-- docsherpa:routing -->`
검증: `grep -c docsherpa: second-brain/AGENTS.md` = 2. (scaffold.write_router는 헤딩 매칭을 안 해
중복 섹션을 만들므로 second-brain엔 **직접 편집**이 맞다.)

### (b) doc-reconcile 교체 — 이식본 + version stamp [git-reversible]

```bash
cp ~/Desktop/private/docsherpa/skills/doc-reconcile/SKILL.md \
   ~/Desktop/private/second-brain/.claude/skills/doc-reconcile/SKILL.md
printf '\n<!-- docsherpa-scaffold: v0.0.1 -->\n' >> \
   ~/Desktop/private/second-brain/.claude/skills/doc-reconcile/SKILL.md
```
(R4: 원본을 의도적으로 교체하는 마이그레이션 — 승인된 행위. 롤백=git.)
검증(실전 parity): second-brain에서 실제 변경 하나에 doc-reconcile를 돌려 원본과 **같은 신설/갱신 제안**을
내는지 육안 확인.

### (c) 로컬 플러그인 설치 — **터미널 Claude Code에서만**(VSCode 채팅 불가, FINDINGS ①)

```
/plugin marketplace add ~/Desktop/private/docsherpa
/plugin install docsherpa@docsherpa      # user scope
# resolution 확인: /docsherpa:setup-docs · /docsherpa:doc-reconcile 가 스킬 목록에 노출되면 OK
```
※ (a)(b)의 커밋된 루프는 **플러그인 없이도** second-brain에서 작동(D2). (c)는 *다른* repo에서
`/docsherpa:setup-docs`를 쓰기 위한 것.

### (d) 중복 global setup-docs 제거 — **(c) 확인 후에만**(롤백 안전, codex)

```bash
# docsherpa의 setup-docs가 resolve됨을 (c)에서 확인한 뒤에만:
rm -rf ~/.claude/skills/setup-docs        # 복구원: docsherpa/skills/setup-docs
```

---

## Self-Review

**Spec coverage(§9):** 추출·일반화(M1) 완료 전제 → A1 parity(behavioral, 텍스트 superset 아님 — §9 교훈
준수). 로컬발행 → B(c). 재스캐폴드 → B(a)(b) + A2 실증. 기존 훅 보존 최악케이스 → A2(dedup). global 제거
경로확인 후 → B(d). **의도적 밖:** second-brain 문서 부채(broken/orphan) 청소는 별개 MESSY(§A3).

**안전:** 바깥/파괴 작업(second-brain 쓰기·global 삭제·터미널)은 전부 B로 게이트. 이번 세션 쓰기 0
(temp copy dry-run만). (a)(b)는 git-reversible, (d)는 (c) 확인 조건부.
