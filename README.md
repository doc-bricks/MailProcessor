# MailProcessor

<p align="center">
  <img src="assets/banner.svg" alt="MailProcessor Banner" width="100%" />
</p>

System tray launcher for the three Universal Mail Tools.

> **Deutsche Dokumentation:** [README-DE.md](README-DE.md)

[![MailProcessor tests](https://github.com/doc-bricks/MailProcessor/actions/workflows/tests.yml/badge.svg)](https://github.com/doc-bricks/MailProcessor/actions/workflows/tests.yml)

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
- Read-only snapshot export as `mailprocessor-suite-v1.json` for the companion view
- Windows autostart (registry entry)
- Bilingual: German / English

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

## Requirements

- Python 3.10+
- PySide6 6.x
- One or more Universal Mail Tools (auto-downloaded via wizard)

## Development checks

```bash
python -m pytest -q
python -m compileall .
```

Current local test suite: 53 Pytest tests.

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
