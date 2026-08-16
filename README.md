# MailProcessor

<p align="center">
  <img src="assets/banner.png" alt="MailProcessor Banner" width="100%" />
</p>

System tray launcher for the three Universal Mail Tools.

> **Deutsche Dokumentation:** [README-DE.md](README-DE.md)

[![MailProcessor tests](https://github.com/doc-bricks/MailProcessor/actions/workflows/tests.yml/badge.svg)](https://github.com/doc-bricks/MailProcessor/actions/workflows/tests.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![LLM Ready](https://img.shields.io/badge/LLM--Ready-llms.txt-brightgreen.svg)](llms.txt)

> [!NOTE]
> For AI agents and automated tools, key architecture and interface metadata are indexed in [llms.txt](llms.txt).

![MailProcessor Installer](README/screenshots/main.png)

## What it does

MailProcessor sits in the Windows system tray and gives you one-click access to:

- **Universal Mail Cleaner** — Clean an IMAP mailbox by rules
- **Universal Docs Grabber** — Download documents and attachments from mail
- **Universal Invoice Mail** — Extract invoices automatically from mail

## Features

- System tray icon: launch any tool via right-click at any time
- First run: setup wizard with automatic scan for installed tools
- GitHub installer: download tools directly from GitHub Releases
- Version numbers shown in tray menu (read from each tool's CHANGELOG.md)
- Settings: change paths, remove tools, add manually
- Read-only snapshot export as `mailprocessor-suite-v1.json` for local reference; no web or mobile companion is active
- Windows autostart (registry entry)
- Bilingual: German / English

## System Architecture & Workflow

```mermaid
graph TD
    Tray["Windows System Tray (MailProcessor)"] --> Wizard["Setup Wizard & Tool Scanner"]
    Tray --> Config["%LOCALAPPDATA%/MailProcessor/config.json"]
    Tray --> Snapshot["Snapshot Exporter (mailprocessor-suite-v1.json)"]
    Tray --> Tool1["Universal Mail Cleaner"]
    Tray --> Tool2["Universal Docs Grabber"]
    Tray --> Tool3["Universal Invoice Mail"]
    Wizard --> GitHub["GitHub Releases Auto-Downloader"]
```

## Installation

1. Install Python 3.10+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch:
   ```bash
   start.bat
   ```
   or
   ```bash
   python main.py
   ```
4. Select the desired tools in the setup wizard

## Windows Release

- Local release artifacts are staged in `releases/v0.1.0/`
- Rebuild the Windows executable with `build_exe.bat`
- The packaged binary is named `MailProcessor-0.1.0-desktop.exe`

### Microsoft Store readiness

The Microsoft Store is currently **deferred**. MailProcessor launches external
desktop processes, writes its per-user autostart entry, and downloads selected
GitHub release archives, so any package requires both `runFullTrust` and
`internetClient` plus a separate privacy, packaging, and certification review.

The read-only gate can be run by humans or automation and emits stable JSON:

```bash
python store_readiness.py --release-dir <existing-vX.Y.Z-release-folder>
python store_readiness.py --release-dir <existing-vX.Y.Z-release-folder> --json
```

Exit code `0` means every gate passed; exit code `2` means at least one blocker
remains. The audit never builds, signs, uploads, or submits a package.

## Platform scope

MailProcessor is a Windows desktop tray launcher. The former web/PWA companion
was intentionally removed after its use-case review; the redacted snapshot is
not a synchronization interface or a mobile product. macOS and Linux retain a
source-level contract only, not a packaged end-user release.

## Requirements

- Python 3.10+
- PySide6 6.x
- One or more Universal Mail Tools (auto-downloaded via wizard)

## Development checks

```bash
python -m pytest -q
python -m compileall .
```

Current local test suite: 66 Pytest tests.

## Configuration

Settings are stored in `%LOCALAPPDATA%\MailProcessor\config.json`.

Tools are installed to `%LOCALAPPDATA%\MailProcessor\tools\`.

## Related Tools

Part of the [doc-bricks](https://github.com/doc-bricks) mail suite:

| Tool | Description |
|------|-------------|
| [UniversalMailCleaner](https://github.com/doc-bricks/UniversalMailCleaner) | Rule-based IMAP mailbox cleaner with safe mode |
| [UniversalDocsGrabber](https://github.com/doc-bricks/UniversalDocsGrabber) | Download documents and attachments from IMAP mail |
| [UniversalInvoiceMail](https://github.com/doc-bricks/UniversalInvoiceMail) | Extract invoices and receipts from IMAP mail |

## License

MIT License — see [LICENSE](LICENSE)
