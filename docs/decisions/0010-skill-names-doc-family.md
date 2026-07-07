# 0010. 스킬 이름 = `doc-*` 패밀리 (`doc-setup` + `doc-reconcile`)

- 상태: 폐기 (2026-07-07) — 개명·`doc-*` 패밀리 컨벤션 **미채택 확정**. `hello` 삭제·브랜드 미표기(별개 축)는 유효.
- 날짜: 2026-07-05 (개명 철회: 2026-07-06 · 패밀리 폐기: 2026-07-07)

> **갱신 (2026-07-07) — 패밀리 컨벤션 폐기.** `doc-*` 단수 동사 패밀리는 **살아있는 컨벤션이 아니다.**
> flagship `setup-docs`가 (발행 후 개명 불가로) 끝내 안 따랐으므로 "패밀리"는 실현된 적이 없다. 관찰되는
> 실제 규칙은 **혼합**(`setup-docs` + `doc-reconcile`)이다. 따라서 **새 스킬을 `doc-*`에 억지로 맞추지
> 않는다** — 이름은 (1) 그 자체로 명료하고 (2) 커밋되어 네임스페이스 없이 홀로 불릴 때 자명하면 된다.
> 정체성 정렬은 네임스페이스 `docsherpa:`가 한다. 여전히 유효: 브랜드 미박기(`docsherpa-*` 거부)·`hello` 삭제.

> **갱신 (2026-07-06) — 개명 철회.** `setup-docs → doc-setup` 개명은 **실행하지 않기로 확정**했다.
> v0.1.0이 `setup-docs`·`/docsherpa:setup-docs` 커맨드 표면으로 이미 공개 발행됐고, 이 시점의 개명은
> 발행된 커맨드 표면을 깨는 breaking 변경이라 코히런스 이득보다 비용이 크다. 아래 "결정 1(개명)"은
> **무효**, "결정 3(`hello` 삭제)·결정 4(브랜드 미표기)"는 그대로 유효(이미 실행됨). 개명 관련 후속
> 참조(plans·본문)는 역사로 보존한다.

## 맥락

스킬 이름(`setup-docs`·`doc-reconcile`)은 플러그인 이름([0006](0006-name-docsherpa.md)=docsherpa) 결정
**전에** 지어졌다. 그래서 두 문제가 남았다:

1. **패턴 불일치:** `setup-docs`=[동사][명사] vs `doc-reconcile`=[명사][동사] — 순서가 어긋나 한
   세트로 안 읽힌다.
2. **"플러그인 이름에 맞춰야 하나?"의 오해:** 정체성 정렬은 이미 **네임스페이스 `docsherpa:`**가
   한다(`docsherpa:setup-docs`). 스킬 토큰에 `docsherpa`를 박으면 `docsherpa:docsherpa-setup`
   말더듬 + 사용자 레포 브랜드 누출.

결정적 비대칭: `setup-docs`는 플러그인 안에만 살아 **항상 네임스페이스와 함께** 불리지만,
`doc-reconcile`은 [0002](0002-committed-scaffold-in-target.md)대로 **target repo에 커밋**되어
(`.claude/skills/doc-reconcile/`, scaffold가 그 경로를 물고 있음) **네임스페이스 없이 홀로** 불린다.

## 결정

- **`setup-docs` → `doc-setup`으로 개명.** `doc-<동사>` 단수 패밀리로 짝을 맞춘다.
- **`doc-reconcile`은 그대로 둔다.** 개명 비용이 큰 쪽(ADR 파일명 `0004`·`0009`, prime 템플릿,
  scaffold 하드코딩 타겟 경로, 커밋되는 스킬 폴더)을 건드리지 않고, 남의 레포에서 홀로 불려도
  자명한 이름을 보존한다.
- **`hello` 스킬 삭제** — M0 스파이크의 네임스페이스 확인용 프로브라 제품 자산이 아니다.
- **브랜드를 이름에 박지 않는다**(`docsherpa-*` 거부) — "docsherpa는 주인이 아니라 보조 +
  누출 방지"([AGENTS.md] North Star)와 정합.

## 결과

- 좋음: `docsherpa:doc-setup` + `docsherpa:doc-reconcile`로 한 세트처럼 읽히고, 커밋/ADR-바인딩된
  `doc-reconcile`은 무변경이라 개명 blast radius가 절반으로 준다.
- 거부한 대안:
  - `docs-setup` + `docs-reconcile`(복수, 둘 다 개명) — 코히런스는 같은데 커밋/ADR 쪽까지 흔들어 비용 2배.
  - `setup` + `reconcile`(docs 생략) — 플러그인 호출은 깔끔하나 `doc-reconcile`이 홀로 불릴 때 `reconcile`이 "뭘?"로 모호.
  - `docsherpa-*` 브랜딩 — 말더듬 + 사용자 레포 누출.
- 비용(구현 이연): `skills/setup-docs/` 폴더 이동(그 아래 `scripts/`·`templates/`·`reference/` 전체) +
  scaffold.py 경로 상수 + 내부 문서 참조 교정. self-contained(target 커밋·ADR 파일명에 안 박힘)라
  외과적으로 끝난다.

관련: [0006](0006-name-docsherpa.md)(이름=docsherpa) · [0004](0004-doc-reconcile-one-file-two-uses.md)(doc-reconcile 정본).
