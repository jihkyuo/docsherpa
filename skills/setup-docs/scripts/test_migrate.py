import pytest
import migrate


def test_plan_moves_type_to_folder():
    inv = [
        {"path": "adr-1.md", "type": "ADR"},
        {"path": "help.md", "type": "how-to"},
        {"path": "why.md", "type": "PRD"},
        {"path": "notes.md", "type": "reference"},
        {"path": "concept.md", "type": "explanation"},
    ]
    dests = {p["src"]: p["dest"] for p in migrate.plan_moves(inv)}
    assert dests["adr-1.md"] == "docs/decisions/adr-1.md"
    assert dests["help.md"] == "docs/how-to/help.md"
    assert dests["why.md"] == "docs/product/why.md"
    assert dests["notes.md"] == "docs/notes.md"          # reference → 평면
    assert dests["concept.md"] == "docs/concept.md"       # explanation → 평면
    assert all(p["ops"] == ["move"] for p in migrate.plan_moves(inv))


def test_plan_moves_skips_router_tooling_legacy_mdx_inplace():
    inv = [
        {"path": "AGENTS.md", "type": "reference"},              # router → skip
        {"path": ".github/X.md", "type": "reference"},           # tooling → skip
        {"path": "README.md", "type": "reference"},              # 루트관례 tooling → skip
        {"path": "docs/decisions/a.md", "type": "ADR"},          # 이미 제자리 → skip
        {"path": "docs/specs/old/2025-01-x.md", "type": "legacy"},  # 동결역사 → skip
        {"path": "guide.mdx", "type": "how-to"},                 # .mdx → skip(증분 4)
    ]
    assert migrate.plan_moves(inv) == []


def test_plan_moves_spec_and_topic_use_judgment_fields():
    inv = [
        {"path": "func.md", "type": "spec", "feature": "billing"},
        {"path": "a.md", "type": "reference", "topic": "auth"},
    ]
    dests = {p["src"]: p["dest"] for p in migrate.plan_moves(inv)}
    assert dests["func.md"] == "docs/specs/billing/func.md"
    assert dests["a.md"] == "docs/auth/a.md"                     # topic 폴더가 type보다 우선


def test_plan_moves_collision_raises():
    inv = [
        {"path": "x/help.md", "type": "how-to"},
        {"path": "y/help.md", "type": "how-to"},                 # 둘 다 docs/how-to/help.md
    ]
    with pytest.raises(ValueError):
        migrate.plan_moves(inv)
