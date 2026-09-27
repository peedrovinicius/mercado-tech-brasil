from pathlib import Path
from xml.etree import ElementTree

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_dependabot_covers_python_frontend_and_actions():
    payload = yaml.safe_load(
        (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    )

    assert payload["version"] == 2
    updates = {
        (item["package-ecosystem"], item["directory"]): item
        for item in payload["updates"]
    }

    assert ("pip", "/") in updates
    assert ("npm", "/frontend") in updates
    assert ("github-actions", "/") in updates
    assert all(
        item["schedule"]["interval"] == "weekly"
        for item in updates.values()
    )
    assert all(
        item["schedule"]["timezone"] == "America/Fortaleza"
        for item in updates.values()
    )


def test_codeql_scans_backend_and_frontend():
    workflow = (
        ROOT / ".github" / "workflows" / "codeql.yml"
    ).read_text(encoding="utf-8")

    assert "security-events: write" in workflow
    assert "github/codeql-action/init@v4" in workflow
    assert "github/codeql-action/autobuild@v4" in workflow
    assert "github/codeql-action/analyze@v4" in workflow
    assert "- python" in workflow
    assert "- javascript-typescript" in workflow
    assert "queries: security-extended" in workflow


def test_production_smoke_has_daily_schedule():
    workflow = (
        ROOT / ".github" / "workflows" / "production-smoke.yml"
    ).read_text(encoding="utf-8")

    assert 'cron: "15 11 * * *"' in workflow
    assert "github.event_name == 'schedule'" in workflow
    assert "scripts/smoke_production.py" in workflow


def test_security_policy_documents_supported_release_and_private_reporting():
    policy = (ROOT / "SECURITY.md").read_text(encoding="utf-8")

    assert "0.40.x" in policy
    assert "Não abra uma issue pública" in policy
    assert "Dependabot" in policy
    assert "CodeQL" in policy
    assert "microdados brutos" in policy


def test_public_site_has_canonical_structured_metadata_and_discovery_files():
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    robots = (
        ROOT / "frontend" / "public" / "robots.txt"
    ).read_text(encoding="utf-8")
    sitemap_path = ROOT / "frontend" / "public" / "sitemap.xml"

    assert (
        '<link rel="canonical" '
        'href="https://mercado-tech-brasil.onrender.com/" />'
        in html
    )
    assert 'property="og:url"' in html
    assert 'name="twitter:card"' in html
    assert 'type="application/ld+json"' in html
    assert '"@type": "Dataset"' in html
    assert '"license"' not in html

    assert "User-agent: *" in robots
    assert "Allow: /" in robots
    assert (
        "Sitemap: https://mercado-tech-brasil.onrender.com/sitemap.xml"
        in robots
    )

    root = ElementTree.parse(sitemap_path).getroot()
    namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locations = {
        element.text
        for element in root.findall("s:url/s:loc", namespace)
    }
    assert "https://mercado-tech-brasil.onrender.com/" in locations
    assert "https://mercado-tech-brasil.onrender.com/docs" in locations
