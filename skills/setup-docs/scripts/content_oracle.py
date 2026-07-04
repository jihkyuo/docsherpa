#!/usr/bin/env python3
"""내용보존 oracle — setup-docs 마이그레이션 안전망 (oracle 2).

마이그레이션 전(base) 문서 본문의 모든 세그먼트가 마이그레이션 후(current)에
(a) 어딘가 그대로 존재 / (b) 매니페스트에 dropped+사유 / (c) transformed 로
명시돼 있는지 검사. 미분류 세그먼트가 하나라도 있으면 FAIL → 조용한 유실 차단.

세그먼트 = 빈 줄로 나뉜 블록(펜스 코드블록은 통째 유지).
정규화 = strip + 공백 축약 + [text](url) → text (이동+relink 후에도 매칭).
매칭은 정규화된 고유 세그먼트 key 집합 기준 — 동일 텍스트 중복 세그먼트는 dedup되며, 불변식은 "모든 고유 세그먼트가 살아남는다"이다(인스턴스 개수 보존이 아님).

사용:
  content_oracle.py keys  --base DIR
  content_oracle.py check --base DIR --current DIR --manifest manifest.json
종료코드: check 0=PASS, 1=FAIL.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")   # [text](url) -> text
_WS = re.compile(r"\s+")
_FENCE = re.compile(r"^```")


def segment(text):
    """본문 → 세그먼트 리스트. 펜스 코드블록 통째, 나머지는 빈 줄 분리."""
    segs, buf, in_fence = [], [], False

    def flush():
        block = "\n".join(buf).strip()
        if block:
            segs.append(block)
        buf.clear()

    for line in text.splitlines():
        if _FENCE.match(line):
            if in_fence:
                buf.append(line)
                flush()
                in_fence = False
            else:
                flush()
                in_fence = True
                buf.append(line)
            continue
        if in_fence:
            buf.append(line)
        elif line.strip() == "":
            flush()
        else:
            buf.append(line)
    flush()
    return segs


def normalize(seg):
    return _WS.sub(" ", _LINK.sub(r"\1", seg)).strip()


def seg_key(seg):
    return hashlib.sha1(normalize(seg).encode("utf-8")).hexdigest()[:12]


def collect(root):
    """dir 내 모든 *.md 의 {key: {"preview", "locs": [...]}}."""
    out = {}
    for md in sorted(Path(root).rglob("*.md")):
        for seg in segment(md.read_text(encoding="utf-8", errors="ignore")):
            k = seg_key(seg)
            e = out.setdefault(k, {"preview": normalize(seg)[:70], "locs": []})
            e["locs"].append(str(md.relative_to(root)))
    return out


def cmd_keys(args):
    for k, e in collect(args.base).items():
        print(f"{k}  {e['locs'][0]:30}  {e['preview']}")
    return 0


def cmd_check(args):
    base = collect(args.base)
    current = set(collect(args.current))
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8")) if args.manifest else {}
    dropped = {d["key"] for d in manifest.get("dropped", [])}
    bad_drops = [d for d in manifest.get("dropped", []) if not str(d.get("reason", "")).strip()]

    # transformed 항목은 `to` 목적지가 실제 current에 존재해야만 유효하다.
    # `to`가 비어 있거나, seg_key(to)가 current에 없으면 bad_transform으로 처리.
    valid_transformed = set()
    bad_transforms = []
    for t in manifest.get("transformed", []):
        to_val = str(t.get("to", "")).strip()
        if to_val and seg_key(to_val) in current:
            valid_transformed.add(t["key"])
        else:
            bad_transforms.append(t)

    unaccounted = [(k, e) for k, e in base.items()
                   if k not in current and k not in dropped and k not in valid_transformed]

    ok = not unaccounted and not bad_drops and not bad_transforms
    print(f"{'PASS' if ok else 'FAIL'}: base_segments={len(base)} "
          f"unaccounted={len(unaccounted)} dropped_no_reason={len(bad_drops)} "
          f"transform_unverified={len(bad_transforms)}")
    for k, e in unaccounted:
        print(f"  UNACCOUNTED {k}  {e['locs'][0]}  {e['preview']}")
    for d in bad_drops:
        print(f"  DROPPED-NO-REASON {d.get('key')}")
    for t in bad_transforms:
        print(f"  TRANSFORM-UNVERIFIED {t.get('key')}  to={t.get('to')!r}")
    return 0 if ok else 1


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    pk = sub.add_parser("keys")
    pk.add_argument("--base", required=True)
    pc = sub.add_parser("check")
    pc.add_argument("--base", required=True)
    pc.add_argument("--current", required=True)
    pc.add_argument("--manifest")
    args = p.parse_args()
    return cmd_keys(args) if args.cmd == "keys" else cmd_check(args)


if __name__ == "__main__":
    sys.exit(main())
