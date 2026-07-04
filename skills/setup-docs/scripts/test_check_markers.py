from check_markers import has_contract_markers

ROUTING = "<!-- docsherpa:routing -->"
INDEX = "<!-- docsherpa:index -->"


def test_markers_present_survive_translation():
    # 헤딩이 영어로 번역돼도 마커가 있으면 계약 유지
    md = f"## Document Routing Rules {ROUTING}\n...\n## Read First {INDEX}\n..."
    assert has_contract_markers(md) is True


def test_missing_marker_fails():
    md = "## 문서 라우팅 룰\n...\n## 먼저 읽기\n..."   # 헤딩만, 마커 없음
    assert has_contract_markers(md) is False
