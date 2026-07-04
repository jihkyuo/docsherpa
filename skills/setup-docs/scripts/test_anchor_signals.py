from anchor_signals import anchor_signals


def test_empty_repo_all_absent(tmp_path):
    sig = anchor_signals(tmp_path)
    assert sig == {"design_spec": None, "decisions": None, "codemap": None, "how_to": None}


def test_detects_design_and_decisions_and_howto(tmp_path):
    docs = tmp_path / "docs"
    (docs / "decisions").mkdir(parents=True)
    (docs / "how-to").mkdir()
    (docs / "DESIGN.md").write_text("# design\n", encoding="utf-8")
    sig = anchor_signals(tmp_path)
    assert sig["design_spec"] == "docs/DESIGN.md"
    assert sig["decisions"] == "docs/decisions"
    assert sig["how_to"] == "docs/how-to"
    assert sig["codemap"] is None                 # 없으면 None(특화 말고 일반형 유지 — hollow 방지)


def test_codemap_and_spec_variants(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "ARCHITECTURE.md").write_text("# arch\n", encoding="utf-8")
    (docs / "SPEC.md").write_text("# spec\n", encoding="utf-8")
    sig = anchor_signals(tmp_path)
    assert sig["codemap"] == "docs/ARCHITECTURE.md"
    assert sig["design_spec"] == "docs/SPEC.md"     # DESIGN 없으면 SPEC로 폴백


def test_design_preferred_over_spec(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "DESIGN.md").write_text("# d\n", encoding="utf-8")
    (docs / "SPEC.md").write_text("# s\n", encoding="utf-8")
    assert anchor_signals(tmp_path)["design_spec"] == "docs/DESIGN.md"   # 우선순위 고정
