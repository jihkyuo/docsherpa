# skills/doc-health/scripts/conftest.py
"""doc-health 테스트가 setup-docs 공유 스크립트를 import하도록 경로 부트스트랩(H2).
gate·contract·render_report는 setup-docs/scripts에 산다(단일 채점기 재사용)."""
import sys
from pathlib import Path

_SHARED = Path(__file__).resolve().parents[2] / "setup-docs" / "scripts"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))
