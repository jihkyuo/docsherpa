#!/usr/bin/env python3
"""parity 채점기 — doc-reconcile의 판정을 정답지와 대조한다 (DESIGN §10.3).

에이전트는 리포트에 fenced json 판정을 **정확히 하나** 낸다:

    ```json
    {"update": ["docs/A.md"], "create": [], "no_touch": ["docs/B.md"]}
    ```

정답지(시나리오 JSON)는 그 커밋이 **실제로** 한 일이다:

    {"ground_truth": {"update": [...], "create": [...], "no_touch": [...]}}

세 축을 따로 잰다 — 하나로 합치면 무엇이 고장났는지 알 수 없다:

- **탐지(detection)**: 낡은 문서를 찾았나. `recall`. 실측상 가장 약한 축.
- **억제(suppression)**: 필요 없는 문서를 안 만들었나. `create` 집합 일치.
- **보존(preservation)**: 여전히 사실인 문서를 안 건드렸나. 정답지의 `no_touch`가
  예측의 `update`/`create`에 등장하면 위반.

**이 도구의 죄악은 크래시가 아니라 *조용히 틀린 숫자*다.** 그래서 모호하면 전부 크게 실패한다:
판정 블록이 0개거나 2개 이상이면, 원소가 문자열이 아니면, 절대경로인데 `--root`가 없으면 → 에러.
(리포트가 요구 형식을 그대로 따라 적어 판정 블록이 둘이 되는 일이 실제로 흔하다. "마지막 걸 쓴다"
같은 추측은 **틀린 채점을 조용히 만든다.**)

`extra_update`는 **감점하지 않는다.** 정답지는 그때의 사람+AI가 한 일이라 상한이 아니라 하한이다
(실측: 두 팔 모두 원본이 놓친 stale 문서를 찾아냈다). 표시만 하고 사람이 판정한다.

⚠️ **`no_touch`는 파일 *전체*가 여전히 사실일 때만 넣는다.** 한 문서에 "여전히 사실인 주장"과
"이번 변경이 거짓으로 만든 주장"이 섞이면 그 문서는 `no_touch`가 아니다 — 넣으면 **원본 루프의
맹점을 정답으로 박제**한다(첫 실측에서 실제로 밟은 함정). `validate_scenario()`는 스펙 자기모순
(`no_touch ∩ update ≠ ∅`)만 잡는다. 위 의미 오류는 **자동으로 못 잡는다 — 사람이 봐야 한다.**

사용:
  python3 score.py --scenario s.json --report r1.md [--report r2.md ...] [--root <arena>/control]
종료코드: 0 = 채점 완료(점수가 낮아도 0). 1 = 채점 불가(형식 오류·모순 시나리오).
채점기는 게이트가 아니다 — 판정 실패를 CI가 막지 않는다.
"""
import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath

_JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)
_KEYS = ("update", "create", "no_touch")


def normalize_path(raw, root=None):
    """리포트 경로 → repo-상대 posix 경로. 반환 (경로, 해석됨?).

    에이전트는 절대경로를 자주 낸다(실측). 정규화 없이 두면 정답과 매칭이 안 돼 **재현율이 조용히
    0으로 깎이고**, 존재하지 않는 문제를 고치러 가게 된다. 해석 못 하면 False를 달아 크게 알린다."""
    if not isinstance(raw, str):
        raise ValueError(f"판정 원소가 문자열이 아니다: {raw!r}")
    s = raw.strip()
    if not s:
        raise ValueError("판정에 빈 경로가 있다")
    p = Path(s)
    if p.is_absolute():
        if root is not None:
            r = Path(root).resolve()
            try:
                return PurePosixPath(p.resolve().relative_to(r)).as_posix(), True
            except ValueError:
                return s, False
        return s, False
    return PurePosixPath(s.lstrip("./")).as_posix() or s, True


def parse_report(text, root=None):
    """리포트에서 판정 블록 하나를 읽는다. 반환 (예측 dict[set], 해석 못 한 절대경로 리스트).

    블록이 0개면 못 읽는다. 2개 이상이면 **어느 것이 판정인지 추측하지 않는다** — 크게 실패한다."""
    candidates = []
    for block in _JSON_BLOCK.findall(text):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and any(k in data for k in _KEYS):
            candidates.append(data)
    if not candidates:
        raise ValueError("리포트에 판정 블록(```json, update/create/no_touch 키)이 없다")
    if len(candidates) > 1:
        raise ValueError(f"판정 블록이 {len(candidates)}개다 — 어느 것이 판정인지 모호하다. "
                         "리포트에 판정 json은 정확히 하나만 두라(형식 예시를 다시 적지 말 것)")
    data = candidates[0]
    pred, unresolved = {}, []
    for k in _KEYS:
        vals = data.get(k, [])
        if not isinstance(vals, list):
            raise ValueError(f"판정의 '{k}'가 리스트가 아니다: {vals!r}")
        acc = set()
        for raw in vals:
            norm, ok = normalize_path(raw, root)
            if not ok:
                unresolved.append(raw)
            acc.add(norm)
        pred[k] = acc
    return pred, unresolved


def validate_scenario(truth):
    """정답지 자기모순 검사. 같은 파일이 update/create와 no_touch에 동시에 있으면 스펙 오류다
    (파일 단위 no_touch는 '파일 전체가 여전히 사실'을 뜻한다)."""
    both = truth["update"] & truth["no_touch"]
    if both:
        raise ValueError(f"시나리오 모순 — update이면서 no_touch: {sorted(both)}")
    both = truth["create"] & truth["no_touch"]
    if both:
        raise ValueError(f"시나리오 모순 — create이면서 no_touch: {sorted(both)}")


def score_one(pred, truth):
    """예측 dict(set) × 정답 dict(set) → 축별 결과."""
    validate_scenario(truth)
    gt_u, gt_c, gt_n = truth["update"], truth["create"], truth["no_touch"]
    hit = pred["update"] & gt_u
    violated = gt_n & (pred["update"] | pred["create"])
    return {
        "detected": sorted(hit),
        "missed": sorted(gt_u - pred["update"]),
        "extra_update": sorted(pred["update"] - gt_u),      # 감점 아님
        "recall": (len(hit) / len(gt_u)) if gt_u else None,  # 정답 update가 없으면 잴 게 없다
        "suppression_ok": pred["create"] == gt_c,
        "created": sorted(pred["create"]),
        "preservation_ok": not violated,
        "preservation_violations": sorted(violated),
    }


def aggregate(rows):
    """여러 실행 → 축별 집계. LLM은 확률적이라 n=1로 단정하면 안 된다."""
    n = len(rows)
    scored = [r["recall"] for r in rows if r["recall"] is not None]
    return {
        "runs": n,
        "recall_mean": (sum(scored) / len(scored)) if scored else None,
        "suppression_pass": sum(r["suppression_ok"] for r in rows),
        "preservation_pass": sum(r["preservation_ok"] for r in rows),
    }


def _fmt(scenario_id, rows, agg):
    out = [f"시나리오: {scenario_id}  (실행 {agg['runs']}회)"]
    for i, r in enumerate(rows, 1):
        flags = ("억제 ✅" if r["suppression_ok"] else f"억제 ❌ {r['created']}",
                 "보존 ✅" if r["preservation_ok"] else f"보존 ❌ {r['preservation_violations']}")
        total = len(r["detected"]) + len(r["missed"])
        det = f"탐지 {len(r['detected'])}/{total}" if total else "탐지 —(정답 update 없음)"
        out.append(f"  #{i} {det}  {'  '.join(flags)}")
        if r["missed"]:
            out.append(f"      놓침: {', '.join(r['missed'])}")
        if r["extra_update"]:
            out.append(f"      추가발견(감점 아님, 사람이 판정): {', '.join(r['extra_update'])}")
    rm = "—" if agg["recall_mean"] is None else f"{agg['recall_mean']:.0%}"
    out.append(f"  ── 탐지 재현율 평균 {rm}"
               f" · 억제 {agg['suppression_pass']}/{agg['runs']}"
               f" · 보존 {agg['preservation_pass']}/{agg['runs']}")
    return "\n".join(out)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--scenario", required=True)
    p.add_argument("--report", action="append", required=True, help="에이전트 리포트(반복 가능)")
    p.add_argument("--root", default=None,
                   help="아레나 루트(예: <out>/control). 리포트가 절대경로를 낼 때 필요하다.")
    a = p.parse_args(argv)
    try:
        scenario = json.loads(Path(a.scenario).read_text(encoding="utf-8"))
        truth = {k: set(scenario["ground_truth"].get(k, [])) for k in _KEYS}
        validate_scenario(truth)
        rows, unresolved = [], []
        for rp in a.report:
            pred, unres = parse_report(Path(rp).read_text(encoding="utf-8"), a.root)
            unresolved += [(rp, u) for u in unres]
            rows.append(score_one(pred, truth))
        if unresolved:
            listed = "\n".join(f"    {rp}: {u}" for rp, u in unresolved)
            raise ValueError("리포트에 repo-상대로 해석 못 한 절대경로가 있다 — `--root <arena>/control` "
                             f"를 주거나 프롬프트에서 repo-상대 경로를 요구하라:\n{listed}")
    except (ValueError, KeyError, OSError) as e:
        print(f"STOP: {e}", file=sys.stderr)
        return 1
    print(_fmt(scenario.get("id", a.scenario), rows, aggregate(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
