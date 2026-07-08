from pathlib import Path

import content_oracle
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


def test_cur_link_loss_falls_back_to_new_broken(tmp_path):
    # 정체성 fail-safe: cur가 링크를 잃으면(삭제/재정렬) zip 정렬이 붕괴해 자가유발 broken을
    # preexisting로 은폐할 수 있다. 이때는 차단 방향(new_broken)으로 폴백해야 한다.
    base = tmp_path / "base"
    cur = tmp_path / "cur"
    # base g.md: [./missing.md](broken=preexisting), [./real.md](sat) — 링크 2개
    _mk(base, "docs/g.md", "# G\n[x](./missing.md)\n[y](./real.md)\n")
    _mk(base, "docs/real.md", "# R\n")
    # cur 같은 g.md: 링크 1개, 그것도 broken(자가유발) — 링크 수 감소
    _mk(cur, "docs/g.md", "# G\n[z](./gone.md)\n")
    plan = []                                            # 이동 없음(정체성 페어링은 같은 경로)
    r = migrate.classify_links(base, cur, plan)
    assert ("docs/g.md", "./gone.md") in r["new_broken"]   # 은폐 차단 → new_broken
    assert not r["preexisting_broken"]


def test_anchor_dropped_flagged(tmp_path):
    base = tmp_path / "base"
    cur = tmp_path / "cur"
    _mk(base, "docs/a.md", "# A\n[api](guide.md#api-v1)\n")
    _mk(base, "docs/guide.md", "# G\n")
    _mk(cur, "docs/a.md", "# A\n[api](guide.md)\n")     # 앵커 소실(버그 시뮬)
    _mk(cur, "docs/guide.md", "# G\n")
    r = migrate.classify_links(base, cur, [])
    assert ("docs/a.md", "guide.md") in r["anchor_lost"]


def test_import_prepend_does_not_shift_link_pairing(tmp_path):
    # 정체성 직결: scaffold의 inject_claude_md가 @AGENTS.md를 CLAUDE.md 맨 앞에 prepend하면
    # doc_links가 import를 링크로 세어 zip 인덱스가 밀려 무손실 마이그레이션이 오분류된다.
    # classify_links는 본문 링크(](target))만 봐야 한다 — import는 gate가 별도로 본다.
    base = tmp_path / "base"; cur = tmp_path / "cur"
    _mk(base, "SETUP.md", "# S\n")                 # setup 링크는 실재(satisfiable)
    _mk(base, "CLAUDE.md", "# P\n\n[ghost](ghost.md) [setup](SETUP.md)\n")  # ghost=없음(preexisting)
    _mk(cur, "SETUP.md", "# S\n")
    _mk(cur, "CLAUDE.md", "@AGENTS.md\n\n# P\n\n[ghost](ghost.md) [setup](SETUP.md)\n")  # import prepend
    r = migrate.classify_links(base, cur, [])
    assert not any(f == "CLAUDE.md" for f, _ in r["new_broken"])   # 무손실 → 거짓 new_broken 없음
    assert ("CLAUDE.md", "ghost.md") in r["preexisting_broken"]    # ghost는 원래 깨짐(정확 페어링)


def test_per_file_catches_dropped_duplicate_content_doc(tmp_path):
    base = tmp_path / "base"; cur = tmp_path / "cur"
    dup = "# 공통\n동일한 보일러플레이트 세그먼트.\n"
    _mk(base, "docs/a.md", dup)
    _mk(base, "docs/b.md", dup)                        # a·b 동일내용
    _mk(cur, "docs/a.md", dup)                         # b가 통째 소실(이동 실패 시뮬)
    plan = [{"src": "docs/a.md", "dest": "docs/a.md"}, {"src": "docs/b.md", "dest": "docs/b.md"}]
    # content_oracle는 통과(고유 세그먼트 살아있음)
    assert not (set(content_oracle.collect(base)) - set(content_oracle.collect(cur)))
    # 하지만 per_file은 b의 dest 미도달을 잡아야
    viol = migrate.per_file_accounting(base, cur, plan)
    assert any("docs/b.md" in str(v) for v in viol)
