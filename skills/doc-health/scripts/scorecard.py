#!/usr/bin/env python3
"""문서 건강 점수표 — doc-health 채점(기계 차원 M1~M5).

도달성은 gate.analyze 재사용(단일 엔진 = 정합성). disposition(H1)으로 M5 분모 결정.
J1~J4 판단·분류·자세 하위는 SKILL.md 절차(코드 아님).
"""
import json
import sys
from pathlib import Path

# --- 공유 스크립트 경로 부트스트랩(CLI 실행 시; 테스트는 conftest.py도) ---------
_SHARED = Path(__file__).resolve().parents[2] / "setup-docs" / "scripts"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

import gate                        # noqa: E402
from contract import disposition   # noqa: E402

# --- 임계값 -------------------------------------------------------------------
M5_WARN_MAX = 3       # docs/ 밖 content 1~3 = warn, 초과 = fail
GREENFIELD_MAX = 2    # content 문서 이하 + 라우터 없음 = GREENFIELD


def outside_content(files):
    """docs/ 밖 content 문서 목록(M5 위반 후보) — 정렬."""
    out = [f for f in files
           if disposition(f) == "content" and Path(f).parts[0] != "docs"]
    return sorted(out)


# --- 기계 차원 M1~M5 ---------------------------------------------------------
def _has_sessionstart_hook(settings_path):
    if not settings_path.is_file():
        return False
    try:
        return "SessionStart" in settings_path.read_text(encoding="utf-8")
    except OSError:
        return False


def _m4_loop_ok(root):
    root = Path(root)
    return ((root / ".claude" / "doc-drift-prime.txt").is_file()
            and (root / ".claude" / "skills" / "doc-reconcile" / "SKILL.md").is_file()
            and _has_sessionstart_hook(root / ".claude" / "settings.json"))


def _m5_status(files):
    n = len(outside_content(files))
    if n == 0:
        return "pass"
    return "warn" if n <= M5_WARN_MAX else "fail"


def machine_dims(res, files):
    """GateResult + inventory files → [M1..M5] 차원 dict 리스트."""
    root = res.root
    n_home = len(res.homes)
    m1 = "pass" if (not res.broken and not res.orphans) else "fail"
    m2 = "pass" if (res.router_present and n_home == 1) else "fail"
    map_home = (root / "docs" / "_map.md").resolve()
    m3 = "pass" if (n_home == 1 and res.homes[0].resolve() == map_home) else "fail"
    m4 = "pass" if _m4_loop_ok(root) else "fail"
    m5 = _m5_status(files)
    outside = outside_content(files)
    # kind: "필수"=능력(도구 무관 실제 문서 건강) · "채택도"=docsherpa 특정 부품 설치 여부(선택).
    # (D4보강: 자체 등가물 보유자가 오해 없게 라벨로 구분.)
    return [
        {"code": "M1", "name": "라우터에서 모든 문서 도달", "kind": "필수", "status": m1,
         "sub": (f"깨진 링크 {len(res.broken)}개 · 어디서도 안 걸리는 문서 {len(res.orphans)}개"
                 if (res.broken or res.orphans) else "깨진 링크 0 · 고아 문서 0")},
        {"code": "M2", "name": "진입 라우터 + 계약 마커 설치", "kind": "채택도", "status": m2,
         "sub": ("진입 라우터(AGENTS.md/CLAUDE.md) 없음" if not res.router_present
                 else f"마커 담은 인덱스 {n_home}개"
                 + ("" if n_home == 1 else " (정확히 1개여야)"))},
        {"code": "M3", "name": "문서 지도(맵)를 중추 문서로 분리", "kind": "채택도", "status": m3,
         "sub": ("지도 = docs/_map.md (단일 소스)" if m3 == "pass"
                 else "맵이 라우터에 인라인이거나 인덱스 home이 1개가 아님")},
        {"code": "M4", "name": "코드 변경 시 문서 자동 갱신 장치 3종", "kind": "채택도", "status": m4,
         "sub": ("세션 훅·prime·doc-reconcile 스킬 설치됨" if m4 == "pass"
                 else "자동 갱신 3종(세션 훅·prime·doc-reconcile) 중 누락")},
        {"code": "M5", "name": "모든 문서가 docs/ 아래(파묻힘 0)", "kind": "필수", "status": m5,
         "sub": (f"docs/ 밖에 흩어진 content {len(outside)}건" if outside
                 else "docs/ 밖 content 0")},
    ]


def counts(mech, judg):
    """전 9차원 상태 tally → {fail,warn,pass}."""
    alld = list(mech) + list(judg)
    return {k: sum(1 for d in alld if d["status"] == k)
            for k in ("fail", "warn", "pass")}


def posture_hint(res, files, mech):
    """결정론 자세 힌트. MESSY 하위 구분은 에이전트 판단(SKILL)."""
    m = {d["code"]: d["status"] for d in mech}
    content = [f for f in files if disposition(f) == "content"]
    if not res.router_present and len(content) <= GREENFIELD_MAX:
        return "GREENFIELD"
    if res.router_present and m["M1"] == "pass" and m["M5"] == "pass":
        return "HEALTHY"
    return "MESSY"


# --- 조립 + CLI --------------------------------------------------------------
def _git_branch(root):
    head = Path(root) / ".git" / "HEAD"
    try:
        txt = head.read_text(encoding="utf-8").strip()
    except OSError:
        return "?"
    prefix = "ref: refs/heads/"
    return txt[len(prefix):] if txt.startswith(prefix) else txt[:8]


def _nested_lines(paths):
    """repo-상대 경로들 → 중첩 폴더 트리 lines. 폴더=[text(개수),None]·파일=[text,None].
    파일 무색: 색은 타입 인코딩 전용으로 예약(범례 fail-ink=troubleshooting과 충돌 방지)."""
    root = {}
    for p in sorted(paths):
        parts = p.split("/")
        node = root
        for seg in parts[:-1]:
            node = node.setdefault(seg, {})
        node.setdefault("__f__", []).append(parts[-1])

    def count(n):
        c = len(n.get("__f__", []))
        for k, v in n.items():
            if k != "__f__":
                c += count(v)
        return c

    lines = []

    def walk(node, pre):
        for d in sorted(k for k in node if k != "__f__"):
            lines.append([f"{pre}{d}/  ({count(node[d])})", None])
            walk(node[d], pre + "  ")
        for fn in sorted(node.get("__f__", [])):
            lines.append([f"{pre}{fn}", None])

    walk(root, "")
    return lines


def _before_tree(files):
    outside = outside_content(files)
    lines = _nested_lines(outside)
    sub = (f"docs/ 밖 흩어짐 · content {len(outside)}건" if outside
           else "docs/ 중심")
    return {"title": "현재 구조", "tag": "지금", "sub": sub, "lines": lines}


def assemble(root, files, judgment, inventory=None):
    """root + inventory files + 에이전트 판단 J차원 → render_report 부분 데이터 모델."""
    j_codes = {d["code"] for d in judgment}
    if j_codes != {"J1", "J2", "J3", "J4"}:
        raise ValueError(
            f"judgment must assess all 4 dims (J1-J4); got codes {sorted(j_codes)}")
    res = gate.analyze(root)
    mech = machine_dims(res, files)
    out = {
        "repo": {"name": Path(root).resolve().name,
                 "docs_count": len(files),
                 "branch": _git_branch(root)},
        "counts": counts(mech, judgment),
        "scorecard": {"mechanical": mech, "judgment": judgment},
        "trees": {"before": _before_tree(files)},
        "posture": posture_hint(res, files, mech),
        "orphans": len(res.orphans),
    }
    if inventory is not None:
        out["inventory"] = inventory
    return out


def main(argv=None):
    import argparse
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--manifest", help="분류 매니페스트 JSON([{path,type,...}])")
    ap.add_argument("--judgment", required=True,
                     help="J1~J4 판단 차원 JSON([{code,name,sub,status}]) — "
                          "9차원(M1~M5+J1~J4)을 전부 평가해야 점수표가 정직하므로 필수")
    args = ap.parse_args(argv)

    import inventory as _inv
    files = _inv.list_docs(args.root)
    manifest = None
    if args.manifest:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    judgment = json.loads(Path(args.judgment).read_text(encoding="utf-8"))
    data = assemble(args.root, files, judgment, inventory=manifest)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
