#!/usr/bin/env python3
"""parity 아레나 빌더 — doc-reconcile 행동 fixture의 준비 단계 (DESIGN §10.3).

어떤 git 레포의 커밋 C 하나를 "시험 문제"로 바꾼다:
C의 **부모 트리**(=코드는 착륙했고 문서는 아직 낡은 시점)를 **git 없는 평문 디렉터리**로
꺼내고, C가 만든 **코드 변경만** diff로 뽑는다.

**정답 누출이 이 도구의 유일한 치명 실패다.** 두 경로로 샌다:
  1. 트리에 `.git`이 남으면 에이전트가 `git log`로 정답 커밋을 본다. → `git archive`가 애초에 안 담는다.
  2. **diff에 문서 변경이 섞이면** 에이전트가 정답을 그대로 읽는다. → 이쪽이 실제 위험이다.
     문서 판정은 **대소문자 무시**로 하고(`README.MD`), 산출된 diff를 다시 훑어 문서가 하나라도
     들어 있으면 **RuntimeError로 멈춘다**(조용한 누출 금지).

사용:
  python3 arena.py --repo <src> --commit <sha> --out <dir>
  python3 arena.py --repo <src> --commit <sha> --out <dir> --doc-glob '*.txt'

산출:
  <dir>/control/          부모 트리(문서 낡음, .git 없음)
  <dir>/code-change.diff  C의 비-문서 변경
  <dir>/code-change.log   C의 커밋 제목들

처리군(docsherpa 설치본)은 이 control을 복제해 setup-docs를 돌려 만든다 — 그건 스킬 절차라
코드가 아니다. 절차 전체는 docs/how-to/run-parity-experiment.md.
"""
import argparse
import fnmatch
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

# 기본 문서 확장자. `.md`만 막으면 `.mdx`·`.rst` 문서 변경이 diff로 새어 정답이 노출된다.
DEFAULT_DOC_GLOBS = ("*.md", "*.mdx", "*.markdown", "*.rst", "*.adoc")

_DIFF_HEADER = "diff --git a/"


class ArenaError(RuntimeError):
    """사용자가 읽고 대응할 수 있는 아레나 오류."""


def _git(repo, *args, binary=False):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if r.returncode != 0:
        raise ArenaError(f"git {' '.join(args)} 실패:\n{r.stderr.decode('utf-8', 'replace').strip()}")
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")


def is_doc(rel_path, doc_globs):
    """경로가 문서인가. **대소문자 무시** — `README.MD`도 문서다(git pathspec은 대소문자를 가린다)."""
    p = PurePosixPath(str(rel_path)).as_posix().lower()
    name = PurePosixPath(p).name
    return any(fnmatch.fnmatch(p, g.lower()) or fnmatch.fnmatch(name, g.lower()) for g in doc_globs)


def export_tree(repo, rev, dest: Path):
    """rev 시점 트리를 dest에 평문으로 푼다(.git 없음).

    tarfile은 `filter="data"`로 푼다 — 아카이브는 우리가 만들었지만 **내용은 임의 사용자 레포**라
    신뢰 대상이 아니다(심볼릭 링크·특수 파일). 위험 멤버가 있으면 조용히 통과시키지 않고 멈춘다."""
    dest.mkdir(parents=True, exist_ok=True)
    archive = _git(repo, "archive", rev, binary=True)
    with tempfile.TemporaryDirectory() as td:
        tar_path = Path(td) / "tree.tar"
        tar_path.write_bytes(archive)
        with tarfile.open(tar_path) as tf:
            try:
                tf.extractall(dest, filter="data")
            except tarfile.TarError as e:
                raise ArenaError(f"트리 추출 거부(위험한 멤버: 심볼릭 링크 등) — {e}") from e


def changed_files(repo, parent, commit):
    out = _git(repo, "diff", "--name-only", f"{parent}..{commit}")
    return [line for line in out.splitlines() if line.strip()]


def diff_paths(diff_text):
    """diff 텍스트의 `diff --git a/<p> b/<q>` 헤더에서 경로들을 뽑는다(누출 검사용)."""
    paths = []
    for line in diff_text.splitlines():
        if not line.startswith(_DIFF_HEADER):
            continue
        body = line[len(_DIFF_HEADER):]
        a, sep, b = body.partition(" b/")
        if sep:
            paths.extend([a, b])
    return paths


def assert_no_doc_leak(diff_text, doc_globs):
    """산출된 diff에 문서가 하나라도 있으면 멈춘다(사후 조건).

    필터를 통과했더라도 rename(`a/docs/x.md b/src/x.py`)처럼 헤더 한쪽만 문서인 경우가 있다.
    필터와 별개로 **산출물 자체**를 검사해야 가드가 공허해지지 않는다."""
    leaked = sorted({p for p in diff_paths(diff_text) if is_doc(p, doc_globs)})
    if leaked:
        raise ArenaError(f"정답 누출 — 코드 diff에 문서가 들어 있다: {leaked}")


def code_diff(repo, parent, commit, doc_globs):
    """부모→커밋 diff에서 문서를 제외한 것. = '방금 끝낸 코드 변경'.

    git pathspec `:(exclude)`는 대소문자를 가리므로 파이썬에서 직접 거른다. 산출물은 다시 검사한다."""
    code = [f for f in changed_files(repo, parent, commit) if not is_doc(f, doc_globs)]
    text = _git(repo, "diff", f"{parent}..{commit}", "--", *code) if code else ""
    assert_no_doc_leak(text, doc_globs)
    return text


def doc_globs_for(user_globs):
    """사용자 글롭은 기본 문서 확장자에 **더할 수만** 있다. 좁히면 정답이 새므로 허용하지 않는다."""
    return tuple(sorted(set(DEFAULT_DOC_GLOBS) | set(user_globs or ())))


def resolve_parent(repo, commit):
    """C의 단일 부모. 루트 커밋·머지 커밋은 시나리오로 부적합하므로 읽히는 오류로 거절한다."""
    parents = _git(repo, "rev-list", "--parents", "-n", "1", commit).split()[1:]
    if not parents:
        raise ArenaError(f"{commit[:8]}은 루트 커밋이라 부모 트리가 없다 — 다른 커밋을 고르라")
    if len(parents) > 1:
        raise ArenaError(f"{commit[:8]}은 머지 커밋({len(parents)} 부모)이라 '직전 상태'가 모호하다 "
                         "— 문서만 정리한 일반 커밋을 고르라")
    return parents[0]


def build(repo, commit, out: Path, doc_globs=(), code_base=None):
    """아레나 생성. 반환: {"control", "diff", "log", "parent"}. doc_globs는 기본값에 **추가**된다.

    두 시나리오 유형을 구분한다 — 에이전트가 보는 트리는 **언제나 부모**다:

    - **문서-정리 전용 커밋**(가장 좋은 재료): 코드는 그 전 커밋들에서 착륙했다. `code_base`를 주면
      diff는 `code_base..parent`가 된다. 안 주면 diff가 비어 "방금 뭘 했는지"를 못 보여준다 → STOP.
    - **코드+문서 혼합 커밋**: diff는 `parent..commit`의 비-문서 변경.
    """
    doc_globs = doc_globs_for(doc_globs)
    parent = resolve_parent(repo, commit)
    lo, hi = (code_base, parent) if code_base else (parent, commit)
    diff_text = code_diff(repo, lo, hi, doc_globs)
    if not diff_text.strip():
        raise ArenaError(
            f"코드 변경이 비어 있다({lo[:8]}..{hi[:8]}). "
            f"{commit[:8]}이 문서-정리 전용 커밋이면 `--code-base <코드 작업 직전 rev>`를 줘라 "
            "— 그러면 diff가 `code_base..parent`가 된다.")
    out.mkdir(parents=True, exist_ok=True)
    control = out / "control"
    export_tree(repo, parent, control)
    if (control / ".git").exists():                      # git archive는 안 담지만 방어(사후 손댐)
        raise ArenaError("아레나에 .git이 남았다 — 정답 누출 위험")
    diff_path = out / "code-change.diff"
    diff_path.write_text(diff_text, encoding="utf-8")
    log_path = out / "code-change.log"
    log_path.write_text(_git(repo, "log", "--oneline", f"{lo}..{hi}"), encoding="utf-8")
    return {"control": control, "diff": diff_path, "log": log_path, "parent": parent}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo", required=True)
    p.add_argument("--commit", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--doc-glob", action="append", default=None,
                   help=f"문서로 간주해 코드 diff에서 제외할 glob(대소문자 무시). 기본값 "
                        f"{DEFAULT_DOC_GLOBS} 에 **추가**된다(좁힐 수는 없다 — 좁히면 정답이 샌다). 반복 가능.")
    p.add_argument("--code-base", default=None,
                   help="문서-정리 전용 커밋일 때, 코드 작업 직전 rev. diff가 `code_base..parent`가 된다.")
    a = p.parse_args(argv)
    try:
        res = build(Path(a.repo), a.commit, Path(a.out), tuple(a.doc_glob or ()), a.code_base)
    except ArenaError as e:
        print(f"STOP: {e}", file=sys.stderr)
        return 1
    print(f"parent={res['parent'][:8]}")
    print(f"control={res['control']}")
    print(f"diff={res['diff']} ({res['diff'].stat().st_size}B)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
