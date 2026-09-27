from pathlib import Path

from src.api.main import app
from src.core.settings import settings


ROOT = Path(__file__).resolve().parents[2]


def test_openapi_contract_exposes_stable_product_endpoints():
    payload = app.openapi()

    assert payload["info"]["version"] == settings.version
    paths = set(payload["paths"])
    required = {
        "/api/v1/system/health",
        "/api/v1/system/release",
        "/api/v1/indicators/overview",
        "/api/v1/provenance/release",
        "/api/v1/export/latest/{dataset}.csv",
        "/api/v1/rais/overview",
    }
    assert required <= paths


def test_accessibility_contract_keeps_skip_link_and_live_status():
    dashboard = (
        ROOT / "frontend" / "src" / "pages" / "Dashboard.tsx"
    ).read_text(encoding="utf-8")
    styles = (
        ROOT / "frontend" / "src" / "styles.css"
    ).read_text(encoding="utf-8")

    assert 'className="skip-link"' in dashboard
    assert 'href="#main-content"' in dashboard
    assert 'id="main-content"' in dashboard
    assert 'tabIndex={-1}' in dashboard
    assert 'aria-live="polite"' in dashboard
    assert 'role="status"' in dashboard
    assert "prefers-reduced-motion: reduce" in styles
    assert ".skip-link:focus" in styles


def test_openapi_export_workflow_skips_render_for_docs_only_commit():
    workflow = (
        ROOT / ".github" / "workflows" / "openapi-contract.yml"
    ).read_text(encoding="utf-8")

    assert "python scripts/export_openapi.py" in workflow
    assert "[skip render]" in workflow
    assert "docs/openapi.json" in workflow
