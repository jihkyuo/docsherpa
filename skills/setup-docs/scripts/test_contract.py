from pathlib import Path

import contract


def test_markers_are_html_comments():
    assert contract.ROUTING_MARKER == "<!-- docsherpa:routing -->"
    assert contract.INDEX_MARKER == "<!-- docsherpa:index -->"
    assert contract.MAP_MARKER == "<!-- docsherpa:map -->"


def test_entry_filenames_md_only_no_readme():
    assert contract.ENTRY_FILENAMES == ("AGENTS.md", "CLAUDE.md", "GEMINI.md")
    assert all(n.endswith(".md") for n in contract.ENTRY_FILENAMES)
    assert "README.md" not in contract.ENTRY_FILENAMES


def test_home_when_markers_on_heading_lines():
    text = (
        "# 라우터\n"
        "## 먼저 읽기 <!-- docsherpa:index -->\n- [a](docs/a.md)\n\n"
        "## 라우팅 룰 <!-- docsherpa:routing -->\n1. 결정 → decisions/\n"
    )
    assert contract.is_marker_home(text) is True


def test_not_home_when_markers_only_in_prose():
    # 마커를 '설명'하는 문서(본문 인용)는 home 아님 — false-home 방지.
    text = (
        "# 설계\n\n"
        "마커 <!-- docsherpa:routing -->·<!-- docsherpa:index -->를 헤딩에 붙인다.\n"
    )
    assert contract.is_marker_home(text) is False


def test_not_home_when_markers_inside_code_fence():
    # 템플릿 예시(펜스 안)는 home 아님.
    text = (
        "# 스킬\n\n"
        "```markdown\n"
        "## 인덱스 <!-- docsherpa:index -->\n"
        "## 라우팅 <!-- docsherpa:routing -->\n"
        "```\n"
    )
    assert contract.is_marker_home(text) is False


def test_find_marker_home_picks_only_the_home():
    home = "# r\n## i <!-- docsherpa:index -->\n## g <!-- docsherpa:routing -->\n"
    prose = "# d\n본문에 <!-- docsherpa:index --> <!-- docsherpa:routing --> 인용.\n"
    files = [(Path("AGENTS.md"), home), (Path("docs/DESIGN.md"), prose)]
    assert contract.find_marker_home(files) == [Path("AGENTS.md")]


def test_find_marker_home_reports_multiple():
    a = "# a\n## i <!-- docsherpa:index -->\n## g <!-- docsherpa:routing -->\n"
    b = "# b\n## i <!-- docsherpa:index -->\n## g <!-- docsherpa:routing -->\n"
    files = [(Path("AGENTS.md"), a), (Path("docs/_map.md"), b)]
    assert contract.find_marker_home(files) == [Path("AGENTS.md"), Path("docs/_map.md")]


def test_disposition_router_tooling_content():
    assert contract.disposition("AGENTS.md") == "router"
    assert contract.disposition("CLAUDE.md") == "router"
    assert contract.disposition(".github/x.md") == "tooling"
    assert contract.disposition("README.md") == "tooling"          # 루트 관례(대소문자 무시)
    assert contract.disposition("readme.md") == "tooling"
    assert contract.disposition("docs/how-to/help.md") == "content"
    assert contract.disposition("notes.md") == "content"


def test_disposition_nested_router_and_code_adjacent_readme():
    # DF2: 중첩 라우터(스코프 CLAUDE.md/AGENTS.md)는 어느 깊이든 라우터 → 제자리 skip
    assert contract.disposition("src/features/x/CLAUDE.md") == "router"
    assert contract.disposition("sub/AGENTS.md") == "router"
    # DF1: 코드-인접 중첩 README(mocks·api)는 중앙집중 대상 아님 → tooling(제자리 skip)
    assert contract.disposition("src/features/x/mocks/README.md") == "tooling"
    assert contract.disposition("src/apis/readme.md") == "tooling"
    # docs/ 아래 README(폴더 인덱스)는 content 유지 — DF1이 과확장 안 함
    assert contract.disposition("docs/how-to/README.md") == "content"
    assert contract.disposition("docs/README.md") == "content"
    # 루트 관례 README는 기존대로 tooling
    assert contract.disposition("README.md") == "tooling"


def test_disposition_buried_docs_index_readme_is_content():
    # 리뷰 픽스: parts[0] != "docs"는 최상위만 봐서 매몰된 docs 트리의 인덱스를
    # tooling(제자리)로 잘못 분류했다. "docs"가 부모 어디든 있으면 content로 이동.
    assert contract.disposition("src/features/custom/shared/docs/README.md") == "content"
    assert contract.disposition("src/a/docs/README.md") == "content"
    # 코드-인접(부모에 docs 없음)은 여전히 tooling
    assert contract.disposition("src/a/mocks/README.md") == "tooling"
    assert contract.disposition("src/apis/readme.md") == "tooling"
