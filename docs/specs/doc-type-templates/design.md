# 문서 타입 템플릿·메타·트리거 신뢰성 — design (이연)

- 상태: **제안 (이연 — setup-docs 재설계 완료 후 착수)**
- 날짜: 2026-07-08
- 선행: [ADR 0013 PRD 1급](../../decisions/0013-prd-first-class-doc-type.md) · [ADR 0009 doc-reconcile 트리거](../../decisions/0009-narrow-doc-reconcile-triggers.md) · [knowledge.md 도메인지식](../../../skills/setup-docs/reference/knowledge.md) · [doc-reconcile SKILL](../../../skills/doc-reconcile/SKILL.md)

> **왜 이연:** 우리의 현재 목적은 **setup(진단-주도 마이그레이션)** 마무리다. 이 문서는 vd-front 첫 독푸딩 + 설계 논의에서 표면화된 **문서 타입 메타·트리거** 개선을 잃지 않게 기록한다. 착수는 setup 완료 후 — doc-reconcile 개선 루프의 일부로. **지금 손대지 않는다(방향 흔들림 방지).**

## 1. 배경 — 두 문제

### 문제 A: 문서 타입 메타 비대칭
스캐폴드가 **템플릿을 ADR에만** materialize한다(`decisions/_template.md` — 상태·날짜·Nygard 구조). 다른 1급 타입(PRD·how-to·spec)은 라우팅 룰만 받고 **템플릿·메타가 없다.** vd-front PRD엔 상태·날짜조차 없음. 절차 문서(how-to)는 신선도 신호가 없어 조용히 썩는다.

### 문제 B (진짜 심장): doc-reconcile 트리거가 소프트
"문서가 필요할 때 자동으로·정확히 작성된다"의 실제 기전은 **doc-reconcile(자가성장 North Star)**. 확인 결과:
- **있는 것:** 타입별 트리거가 실재([doc-reconcile SKILL §2](../../../skills/doc-reconcile/SKILL.md)) — 라우팅 마커 섹션을 보고 ADR/PRD/how-to/spec 신설 판정. SessionStart prime이 **매 세션 결정론적으로** 발동. troubleshooting은 "무엇이 바뀌었나(diff)"가 아니라 "무엇을 배웠나"가 트리거라고 **특별 처리**(diff-스캔만 하면 샌다고 경고).
- **한계(당신 직감):** 인식(recognition)은 **판단**이지 결정론이 아님 — 놓칠 수 있음. 리마인더는 결정론, 인식은 판단.
- **본질적 천장:** "이건 troubleshooting 문서가 필요했다"를 코드만 보고 결정론적으로 아는 건 불가능(docsherpa 자신도 인정).

**핵심:** 템플릿을 만들어도 트리거가 안 되면 무용지물. 그러니 이 작업의 **심장은 템플릿이 아니라 doc-reconcile 트리거**다. 템플릿·게이트는 "발동 뒤 정확히 쓰이게" 하는 지원.

### 구체적 빈 곳 (doc-reconcile)
1. **reference/explanation 신설 트리거가 없음** — ADR·PRD·how-to·spec·troubleshooting은 명시하는데 이 둘은 doc-reconcile에 없음.
2. **메타 스탬핑이 생성 흐름에 없음** — 신설 시 `created/adopted/status`를 박는 단계 부재.
3. **형식 강제 장치(메타 게이트)가 없음** — 만들어져도 형식 보장 안 됨.

## 2. 합의된 결정 (재논의 금지 — 착수 시 이대로)

### 2.1 산업 표준 조사 결과 (근거 정직)
- **ADR** = 🟢 Nygard 단일 표준(이미 적용).
- **how-to** = 🟢 Diátaxis(Django·GitLab·Cloudflare 채택, 장르 권위)이나 고정 템플릿은 안 박음. 구체 구조는 Good Docs Project(🟡): 개요→전제→번호절차→검증→관련.
- **troubleshooting** = 🟡 Good Docs(범위→증상→원인→해결). **how-to의 변종**(Diátaxis) — **별도 폴더 아님**, how-to/에 산다(현 knowledge.md·doc-reconcile 입장과 정합). 템플릿 shape만 다름.
- **PRD** = 🔴 Nygard급 단일 표준 없음. 수렴 구조(🟡): 문제→목표·성공기준→대상→요구사항→범위·논고울→열린질문.
- **spec** = 🟡 design-doc/RFC. 기존 손-관례(상태/날짜/선행/파생)를 형식화.
- **reference/explanation** = 🟢 Diátaxis 장르, 고정 본문 템플릿 없음. reference=lookup 최적, explanation=이해 최적. **메타만**.
- **어떤 표준도 "last-verified/freshness/created"를 형식화 안 함** → 우리 메타 추가는 전부 🟡(우리 판단, 표준인 척 금지).

### 2.2 메타 모델
- **created vs adopted 구분(정직 — codex 지적):** `created:`(우리 템플릿으로 태어난 문서만) / `adopted:`·`migrated:`(마이그레이션된 기존 문서) / `created: unknown`(모르면 안 지어냄). 마이그레이션 문서에 `created: today`를 박으면 **거짓**(도입 시점 ≠ 창작 시점).
- **타입별 메타:** ADR=상태(생애주기)+결정일 · PRD=상태(초안→검토→승인→출시→폐기)+갱신일 · how-to/troubleshooting=**최종검증일(단, 검증 명령·의미 정의될 때만** — 없으면 장식·false confidence라 안 넣음) · spec=상태+선행/파생.
- **관계 메타 > owner(codex 지적):** `related-ADR`/`implements-PRD`/`derived-from`/`supersedes` — 도달성 모델과 정합, 에이전트에 유용. **owner는 뺀다**(빨리 썩음).
- 본문 구조는 표준 **가이드**(강제 X). 메타만 강제.

### 2.3 형식 보장 = 타입-메타 게이트
- `gate.py` 확장(`--require-markers`처럼): 타입 폴더 안 문서는 **타입별 필수 메타**를 가져야 한다. 없으면 FAIL.
- **메타만 게이트, 본문은 가이드** — codex의 "폼채우기 카고컬트" 리스크 차단.

### 2.4 템플릿 스캐폴드 = B 방식 (사용자 결정)
- 스캐폴드가 **타입 폴더 + `_template.md` + 인덱스를 기본 생성**(ADR 패턴을 전 타입으로 확장) — 보이는 슬롯(발견성) + 형식 앵커.
- ⚠️ **ADR 0013을 supersede해야 함**(product/·specs 온디맨드 → 스캐폴드-기본으로 전환). 착수 시 새 ADR로 개정 기록.
- 완화(North Star "교리 설치기" 방지): 빈 슬롯엔 명확한 `PLACEHOLDER`/`_template` 마킹 · 전부 인덱스 링크(도달성) · 형식은 메타게이트가·본문은 자유.

## 3. 우선순위·시퀀싱 (착수 시)

| 순위 | 무엇 | 어디 |
|---|---|---|
| **1 (심장)** | doc-reconcile 타입별 트리거 강화 — reference/explanation 추가 + 신설 시 메타(created/adopted/status) 스탬핑 | doc-reconcile SKILL |
| 2 | 타입-메타 게이트 | gate.py |
| 3 | 템플릿 스캐폴드(B) + ADR 0013 supersede | scaffold + _template |

**정직한 최종 한계:** 인식은 판단이라 100% 자동은 불가(리마인더=결정론, 인식=판단). 문서화의 본질적 천장. 우리가 할 최대 = 리마인더 결정론 + 타입별 트리거 최대한 명시 + 발동 시 정확 생성 보장.

**착수 시점:** setup-docs 재설계(진단-주도 마이그레이션) 완료 후. 이건 doc-reconcile 개선 루프에 속한다.
