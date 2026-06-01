"""Tool discovery, registration and launch management."""

import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable, Optional

import config as cfg_module
from config import AppConfig, ToolConfig


# Local dir for tools downloaded from GitHub
_DOWNLOAD_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "MailProcessor" / "tools"

# Static metadata for the three supported tools
TOOL_DEFINITIONS: dict[str, dict] = {
    "universal_mail_cleaner": {
        "name_key": "tool_umc_name",
        "desc_key": "tool_umc_desc",
        "main_scripts": ["mail_imap_cleaner_v1.py", "main.py"],
        "folder_hints": ["REL-PUB_UniversalMailCleaner", "RDY_UniversalMailCleaner", "UniversalMailCleaner"],
        "github_repo": "doc-bricks/UniversalMailCleaner",
    },
    "universal_docs_grabber": {
        "name_key": "tool_udg_name",
        "desc_key": "tool_udg_desc",
        "main_scripts": ["UniversalDocsGrabberV1.py", "main.py"],
        "folder_hints": ["REL-PUB_UniversalDocsGrabber", "RDY_UniversalDocsGrabber", "UniversalDocsGrabber"],
        "github_repo": "doc-bricks/UniversalDocsGrabber",
    },
    "universal_invoice_mail": {
        "name_key": "tool_uim_name",
        "desc_key": "tool_uim_desc",
        "main_scripts": ["UniversalInvoiceMail.py", "main.py"],
        "folder_hints": ["REL-PUB_UniversalInvoiceMail", "RDY_UniversalInvoiceMail", "UniversalInvoiceMail"],
        "github_repo": "doc-bricks/UniversalInvoiceMail",
    },
}

# Where to look for tools
_SCAN_ROOTS = [
    Path(__file__).parent.parent,          # MAIL/
    Path(__file__).parent.parent.parent,   # .SOFTWARE/
    _DOWNLOAD_DIR,                         # downloaded via GitHub installer
]


def _python_interpreter() -> Optional[str]:
    """Return an interpreter that can execute tool scripts."""
    if not getattr(sys, "frozen", False):
        return sys.executable

    for candidate in ("pythonw", "python", "py"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved

    return None


class ToolManager:
    def __init__(self, app_config: AppConfig):
        self.cfg = app_config

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def scan(self) -> dict[str, Optional[tuple[str, str]]]:
        """Scan for installed tools. Returns {tool_id: (folder, script) | None}."""
        results: dict[str, Optional[tuple[str, str]]] = {}
        for tool_id, meta in TOOL_DEFINITIONS.items():
            found = self._find_tool(meta["folder_hints"], meta["main_scripts"])
            results[tool_id] = found
        return results

    def _find_tool(self, folder_hints: list[str], scripts: list[str]) -> Optional[tuple[str, str]]:
        for root in _SCAN_ROOTS:
            if not root.exists():
                continue
            for folder_name in folder_hints:
                candidate = root / folder_name
                if candidate.is_dir():
                    for script in scripts:
                        script_path = candidate / script
                        if script_path.exists():
                            return str(candidate), script
        return None

    def apply_scan_results(self, results: dict[str, Optional[tuple[str, str]]]) -> list[str]:
        """Register newly discovered tools. Returns list of newly found tool IDs."""
        added = []
        for tool_id, found in results.items():
            if found is None:
                continue
            folder, script = found
            tool_cfg = self.cfg.get_tool(tool_id)
            if not tool_cfg.enabled:
                tool_cfg.enabled = True
                tool_cfg.path = folder
                tool_cfg.main_script = script
                tool_cfg.installed_by = "scan"
                added.append(tool_id)
        return added

    # ------------------------------------------------------------------
    # Registration (manual)
    # ------------------------------------------------------------------

    def register(self, tool_id: str, folder: str, script_name: str,
                 installed_by: str = "manual") -> bool:
        """Register a tool by explicit path. Returns False if script not found."""
        script_path = Path(folder) / script_name
        if not script_path.exists():
            return False
        t = self.cfg.get_tool(tool_id)
        t.enabled = True
        t.path = folder
        t.main_script = script_name
        t.installed_by = installed_by
        return True

    def register_from_script_path(self, tool_id: str, script_path: str,
                                  installed_by: str = "manual") -> bool:
        p = Path(script_path)
        if not p.exists():
            return False
        return self.register(tool_id, str(p.parent), p.name, installed_by)

    def unregister(self, tool_id: str) -> None:
        """Remove a tool registration (does NOT delete any files)."""
        if tool_id in self.cfg.tools:
            self.cfg.tools[tool_id] = ToolConfig()

    # ------------------------------------------------------------------
    # Launch
    # ------------------------------------------------------------------

    def launch(self, tool_id: str) -> Optional[str]:
        """Start a tool in a new process. Returns error message or None."""
        t = self.cfg.tools.get(tool_id)
        if not t or not t.enabled or not t.path or not t.main_script:
            return "Tool not configured"
        script = Path(t.path) / t.main_script
        if not script.exists():
            return f"Script not found: {script}"
        interpreter = _python_interpreter()
        if not interpreter:
            return "Python interpreter not found"
        try:
            subprocess.Popen(
                [interpreter, str(script)],
                cwd=str(script.parent),
            )
            return None
        except Exception as e:
            return str(e)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def active_tools(self) -> list[str]:
        return [tid for tid, t in self.cfg.tools.items() if t.enabled and t.path]

    def tool_display_name(self, tool_id: str) -> str:
        from i18n import tr
        meta = TOOL_DEFINITIONS.get(tool_id, {})
        return tr(meta.get("name_key", tool_id))

    def tool_description(self, tool_id: str) -> str:
        from i18n import tr
        meta = TOOL_DEFINITIONS.get(tool_id, {})
        return tr(meta.get("desc_key", ""))

    def is_path_valid(self, tool_id: str) -> bool:
        t = self.cfg.tools.get(tool_id)
        if not t or not t.path or not t.main_script:
            return False
        return (Path(t.path) / t.main_script).exists()

    @staticmethod
    def find_script_in_folder(folder: str, tool_id: str) -> Optional[str]:
        """Given a folder, try to find the main script for tool_id."""
        meta = TOOL_DEFINITIONS.get(tool_id)
        if not meta:
            return None
        p = Path(folder)
        for script in meta["main_scripts"]:
            if (p / script).exists():
                return script
        return None

    # ------------------------------------------------------------------
    # GitHub installer
    # ------------------------------------------------------------------

    def fetch_latest_version(self, tool_id: str) -> Optional[str]:
        """Query GitHub API for the latest release tag. Returns e.g. 'v1.2.0' or None."""
        meta = TOOL_DEFINITIONS.get(tool_id)
        if not meta or not meta.get("github_repo"):
            return None
        url = f"https://api.github.com/repos/{meta['github_repo']}/releases/latest"
        try:
            req = urllib.request.Request(
                url,
                headers={"Accept": "application/vnd.github+json", "User-Agent": "MailProcessor/1.0"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode()).get("tag_name")
        except Exception:
            return None

    def download_tool(self, tool_id: str,
                      progress_cb: Optional[Callable[[int], None]] = None) -> Optional[str]:
        """Download latest release ZIP from GitHub, extract, and register.

        Returns None on success or an error message string.
        progress_cb receives integer 0-100 during download.
        """
        meta = TOOL_DEFINITIONS.get(tool_id)
        if not meta or not meta.get("github_repo"):
            return "No GitHub repo configured for this tool"
        repo = meta["github_repo"]

        # Fetch release metadata
        api_url = f"https://api.github.com/repos/{repo}/releases/latest"
        try:
            req = urllib.request.Request(
                api_url,
                headers={"Accept": "application/vnd.github+json", "User-Agent": "MailProcessor/1.0"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                release = json.loads(resp.read().decode())
        except Exception as exc:
            return f"GitHub API error: {exc}"

        zipball_url: Optional[str] = release.get("zipball_url")
        tag: str = release.get("tag_name", "latest")
        if not zipball_url:
            return "No zipball_url in release info"

        # Prepare download directory
        dest_dir = _DOWNLOAD_DIR / tool_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        zip_path = dest_dir / f"{tag}.zip"

        # Stream download with progress
        try:
            req = urllib.request.Request(zipball_url, headers={"User-Agent": "MailProcessor/1.0"})
            with urllib.request.urlopen(req, timeout=120) as resp, open(zip_path, "wb") as fh:
                total = int(resp.headers.get("Content-Length") or 0)
                downloaded = 0
                while chunk := resp.read(8192):
                    fh.write(chunk)
                    downloaded += len(chunk)
                    if progress_cb and total > 0:
                        progress_cb(min(99, int(downloaded * 100 / total)))
        except Exception as exc:
            return f"Download error: {exc}"

        # Extract archive
        extract_root = dest_dir / "extracted"
        if extract_root.exists():
            import shutil
            shutil.rmtree(extract_root, ignore_errors=True)
        extract_root.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_root)
        except Exception as exc:
            return f"Extract error: {exc}"

        # Find main script inside the extracted folder (GitHub adds a prefix dir)
        for child in extract_root.iterdir():
            if not child.is_dir():
                continue
            script = self.find_script_in_folder(str(child), tool_id)
            if script:
                self.register(tool_id, str(child), script, installed_by="github")
                if progress_cb:
                    progress_cb(100)
                return None

        return "Could not find main script in downloaded archive"

    # ------------------------------------------------------------------
    # Version helper
    # ------------------------------------------------------------------

    def tool_version(self, tool_id: str) -> str:
        """Read the latest version from the tool's CHANGELOG.md.

        Returns e.g. 'v1.2.0' or empty string if not found.
        """
        t = self.cfg.tools.get(tool_id)
        if not t or not t.path:
            return ""
        changelog = Path(t.path) / "CHANGELOG.md"
        if not changelog.exists():
            return ""
        try:
            text = changelog.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"##\s*\[?(\d+\.\d+\.\d+)\]?", text)
            return f"v{m.group(1)}" if m else ""
        except Exception:
            return ""
