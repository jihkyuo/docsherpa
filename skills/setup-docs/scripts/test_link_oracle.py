from pathlib import Path

import migrate


def _mk(root, rel, text):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_moved_source_unrebased_link_is_new_broken(tmp_path):
    base = tmp_path / "base"
    cur = tmp_path / "cur"
    # base: guide/a.md 가 ./b.md(=guide/b.md) 링크, 둘 다 존재 → base에서 satisfiable
    _mk(base, "docs/guide/a.md", "# A\n[b](./b.md)\n")
    _mk(base, "docs/guide/b.md", "# B\n")
    # cur: a·b 둘 다 이동했으나 a의 링크가 재작성 안 됨(회귀) → how-to/b.md 없음 → broken
    _mk(cur, "docs/how-to/a.md", "# A\n[b](./b.md)\n")
    _mk(cur, "docs/reference/b.md", "# B\n")
    plan = [{"src": "docs/guide/a.md", "dest": "docs/how-to/a.md"},
            {"src": "docs/guide/b.md", "dest": "docs/reference/b.md"}]
    r = migrate.classify_links(base, cur, plan)
    assert ("docs/how-to/a.md", "./b.md") in r["new_broken"]      # 우리가 깨뜨림 → 차단
    assert not r["preexisting_broken"]


def test_stale_code_ref_is_preexisting(tmp_path):
    base = tmp_path / "base"
    cur = tmp_path / "cur"
    _mk(base, "docs/api.md", "# API\n[code](src/apis/)\n")   # src/apis/ 애초에 없음
    _mk(cur, "docs/reference/api.md", "# API\n[code](../../src/apis/)\n")  # re-base 정확, 여전히 없음
    plan = [{"src": "docs/api.md", "dest": "docs/reference/api.md"}]
    r = migrate.classify_links(base, cur, plan)
    assert r["preexisting_broken"]                    # 원래 깨짐 → 표면화만
    assert not r["new_broken"]
