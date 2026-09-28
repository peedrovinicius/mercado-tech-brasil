from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_community_policy_documents_are_present_and_linked():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    expected = {
        "CODE_OF_CONDUCT.md": "evidências",
        "SUPPORT.md": "O que não é suporte",
        "ACCESSIBILITY.md": "prefers-reduced-motion",
    }
    for filename, marker in expected.items():
        path = ROOT / filename
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert marker in content
        assert f"]({filename})" in readme


def test_accessibility_policy_does_not_claim_formal_certification():
    policy = (ROOT / "ACCESSIBILITY.md").read_text(encoding="utf-8")

    assert "não representa certificação formal" in policy
    assert "WCAG" in policy


def test_support_routes_security_reports_to_private_policy():
    support = (ROOT / "SUPPORT.md").read_text(encoding="utf-8")

    assert "[SECURITY.md](SECURITY.md)" in support
    assert "Não publique vulnerabilidades" in support
