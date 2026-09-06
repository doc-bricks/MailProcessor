"""Metadata, CI matrix, security and parity contract tests for MailProcessor."""

from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read_file(relative_path: str) -> str:
    path = ROOT / relative_path
    assert path.exists(), f"File {relative_path} does not exist"
    return path.read_text(encoding="utf-8")


def test_ci_workflow_integrity():
    """Verify GitHub Actions CI workflow adheres to security and matrix standards."""
    workflow_content = _read_file(".github/workflows/tests.yml")

    assert "permissions:" in workflow_content
    assert "contents: read" in workflow_content
    assert "concurrency:" in workflow_content
    assert "cancel-in-progress: true" in workflow_content

    # Action versions must be modern and stable
    assert "actions/checkout@v4" in workflow_content
    assert "actions/setup-python@v5" in workflow_content
    assert "@v6" not in workflow_content

    # Matrix configuration
    assert "windows-latest" in workflow_content
    assert "ubuntu-latest" in workflow_content
    assert "macos-latest" in workflow_content
    assert '"3.10"' in workflow_content
    assert '"3.11"' in workflow_content
    assert '"3.12"' in workflow_content

    # Quality and test steps
    assert "ruff check ." in workflow_content
    assert "pytest" in workflow_content
    assert "source_platform_smoke.py" in workflow_content


def test_pyproject_pep621_metadata():
    """Verify pyproject.toml PEP 621 compliance, classifiers, and ecosystem URLs."""
    raw_toml = _read_file("pyproject.toml")
    data = tomllib.loads(raw_toml)

    project = data.get("project", {})
    assert project.get("name") == "doc-bricks-mailprocessor"
    assert project.get("version") == "0.1.0"
    assert project.get("license", {}).get("text") == "MIT"

    classifiers = project.get("classifiers", [])
    expected_classifiers = [
        "Development Status :: 4 - Beta",
        "Environment :: Win32 (MS Windows)",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications :: Email",
        "Topic :: Desktop Environment",
        "Topic :: Utilities",
    ]
    for clf in expected_classifiers:
        assert clf in classifiers, f"Classifier '{clf}' missing from pyproject.toml"

    urls = project.get("urls", {})
    expected_urls = {
        "Homepage": "https://github.com/doc-bricks/MailProcessor",
        "Repository": "https://github.com/doc-bricks/MailProcessor",
        "Bug Tracker": "https://github.com/doc-bricks/MailProcessor/issues",
        "Changelog": "https://github.com/doc-bricks/MailProcessor/blob/main/CHANGELOG.md",
        "Documentation": "https://github.com/doc-bricks/MailProcessor#readme",
        "Security": "https://github.com/doc-bricks/MailProcessor/blob/main/SECURITY.md",
        "Parent Organization": "https://github.com/doc-bricks",
        "Umbrella Ecosystem": "https://github.com/open-bricks",
    }
    for key, expected_val in expected_urls.items():
        assert key in urls, f"URL key '{key}' missing from project.urls"
        assert urls[key] == expected_val, f"URL '{key}' value mismatch: {urls[key]} != {expected_val}"

    # Tool configs
    tool = data.get("tool", {})
    assert "pytest" in tool
    assert "ruff" in tool


def test_security_policy_and_invariants():
    """Verify bilingual SECURITY.md structure, contacts, and core invariants."""
    security_content = _read_file("SECURITY.md")

    # Bilingual presence
    assert "## Deutsch" in security_content
    assert "## English" in security_content
    assert "Unterstützte Versionen" in security_content
    assert "Supported Versions" in security_content
    assert "0.1.x" in security_content

    # Official contacts & advisories
    assert "security@ellmos.ai" in security_content
    assert "support@lukasgeiger.com" in security_content
    assert "lukas@open-bricks.org" in security_content
    assert "https://github.com/doc-bricks/MailProcessor/security/advisories/new" in security_content
    assert "48" in security_content

    # Core invariants
    assert "Local-First" in security_content
    assert "Zero-Egress" in security_content
    assert "Non-Elevation" in security_content
    assert "Zip-Slip" in security_content
    assert "%LOCALAPPDATA%\\MailProcessor\\config.json" in security_content


def test_gitignore_integrity():
    """Verify .gitignore contains cache, lock files, and conflict patterns."""
    gitignore_content = _read_file(".gitignore")

    required_entries = [
        "__pycache__/",
        ".pytest_cache/",
        ".ruff_cache/",
        ".coverage",
        "htmlcov/",
        "*.sync-conflict-*",
        "*.conflict",
        "*-CONFLIT-*",
        "LOCK*.txt",
    ]
    for entry in required_entries:
        assert entry in gitignore_content, f"Entry '{entry}' missing from .gitignore"


def test_readme_bilingual_parity():
    """Verify README.md and README-DE.md cross-linking, badges, and structure."""
    readme_en = _read_file("README.md")
    readme_de = _read_file("README-DE.md")

    # Cross links
    assert "README-DE.md" in readme_en
    assert "README.md" in readme_de

    # Architecture diagram in both
    assert "```mermaid" in readme_en
    assert "```mermaid" in readme_de
    assert "Universal Mail Cleaner" in readme_en
    assert "Universal Mail Cleaner" in readme_de

    # LLM readiness
    assert "llms.txt" in readme_en
    assert "llms.txt" in readme_de

    # Sibling tools
    for tool_name in ("UniversalMailCleaner", "UniversalDocsGrabber", "UniversalInvoiceMail"):
        assert tool_name in readme_en
        assert tool_name in readme_de


def test_llms_txt_integrity():
    """Verify llms.txt metadata and alignment with repository state."""
    llms_content = _read_file("llms.txt")

    assert "https://github.com/doc-bricks/MailProcessor" in llms_content
    assert "doc-bricks" in llms_content
    assert "PySide6 desktop tray application" in llms_content
    assert "UniversalMailCleaner" in llms_content
    assert "UniversalDocsGrabber" in llms_content
    assert "UniversalInvoiceMail" in llms_content
    assert "source-platform smoke PASS" in llms_content
    assert "%LOCALAPPDATA%\\MailProcessor\\config.json" in llms_content
