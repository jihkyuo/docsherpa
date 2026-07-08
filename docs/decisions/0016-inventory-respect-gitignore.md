# 0016. 탐색 분모는 .gitignore를 존중한다 (레포 선언에 위임)

- 상태: 수락
- 날짜: 2026-07-08
- 선행: [doc-health spec](../specs/diagnosis-driven-migration/doc-health.md) §2 · [ADR 0015](0015-doc-health-module-extraction.md)(모듈분해)

## 맥락

doc-health를 실제 레포(vd-front)에 처음 돌리자 탐색 분모가 오염됐다. `.superpowers/sdd/*.md` 9개(외부
플러그인 superpowers가 만든 **gitignore된** 작업 스크래치)가 "content 문서"로 분류돼 M5(docs/ 밖 문서)를
49건으로 부풀렸다. `.md/` 스크래치 폴더도 같은 문제.

첫 처방은 "`.superpowers`를 `_TOOLING_DIRS` 하드코딩에 추가"였으나 두 가지로 틀렸다:
1. **주제넘음·두더지잡기.** `.superpowers`는 외부 플러그인 소관이다. 우리가 그 디렉터리를 하드코딩으로
   분류하면 미래의 모든 플러그인 스크래치 디렉터리를 쫓아다녀야 하고, 그 도구의 관심사에 개입하는 꼴.
2. **카테고리 오류.** 그건 "제자리 유지할 추적된 도구"(`.claude`·`.github` = 커밋됨)가 아니라
   **"프로젝트가 아닌 untracked 스크래치"** — 분모에 들어와서도 안 되는 것.

## 결정

**탐색 분모 = "디스크의 모든 `.md`"가 아니라 "레포가 자기 것이라 선언한 문서".** `inventory.list_docs`가
`.gitignore` 대상을 분모에서 제외한다.

- **git의 무시-엔진에 위임**(`git check-ignore`) — 중첩 `.gitignore`·전역 exclude·`.git/info/exclude`까지
  정확. 우리가 gitignore 규칙을 재구현하지 않는다.
- **ignored된 것만 제외**(추적됨 + 추적안됐지만 무시대상 아닌 **새 문서**는 포함) — 아직 커밋 안 한
  진짜 문서를 진단에서 놓치지 않는다.
- **git-optional** — 비-git 레포면 폴백(기존 디스크 워크 그대로). 진단은 git 없이도 돈다.
- `EXCLUDE_DIRS`(node_modules·dist 등)는 유지 — 비-git에서도 도는 빠른 pre-filter이자 워크 가지치기.
- 별개로, 루트 관례 파일 매칭(`README`·`CHANGELOG` 등)을 **대소문자 무시**로(`readme.md`도 tooling).

## 결과

- **정체성 정합(핵심).** docsherpa는 "주인이 아니라 보조." 무엇이 프로젝트 문서인지 **우리가 판단하지
  않고**, 레포 주인이 이미 내린 선언(gitignore)에 겸손하게 따른다. 외부 도구를 방해하지 않는다.
- **일반적·자가청소.** superpowers든 미래의 어떤 플러그인 스크래치든, 우리가 그 도구를 **몰라도** 자동
  제외. 하드코딩 리스트 불필요.
- **정직한 진단.** vd-front M5 49→38(오염 11건 제거), 분모 68→58 — 남은 38이 진짜 흩어진 프로젝트 문서.
- **트레이드오프:** `git check-ignore` 서브프로세스 1회(분모당). git-optional이라 비-git 폴백 존재.
  gitignore된 디렉터리도 os.walk가 일단 훑고 사후 필터(큰 gitignore 트리에선 약간 낭비 — 실측 무해, 필요
  시 walk 중 가지치기로 최적화 가능, YAGNI).
- **불변식 유지:** 완결성 가드(unaccounted=0)는 그대로 — 분모가 정확해졌을 뿐. 새 문서(untracked·비무시)를
  포함하므로 "잊힌 문서 0"이 오히려 강화됨.
