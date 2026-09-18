# MailProcessor

<p align="center">
  <img src="assets/banner.png" alt="MailProcessor Banner" width="100%" />
</p>

System tray launcher for the three Universal Mail Tools.

> **Language:** [English](README.md) · [Deutsch](README-DE.md)

[![MailProcessor tests](https://github.com/doc-bricks/MailProcessor/actions/workflows/tests.yml/badge.svg)](https://github.com/doc-bricks/MailProcessor/actions/workflows/tests.yml)
[![Version: 0.1.0](https://img.shields.io/badge/version-0.1.0-blue.svg)](CHANGELOG.md)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows%20(System%20Tray)-0078D6.svg?logo=windows&logoColor=white)](https://github.com/doc-bricks/MailProcessor)
[![GUI: PySide6 Qt](https://img.shields.io/badge/GUI-PySide6%20Qt-41CD52.svg?logo=qt&logoColor=white)](https://pypi.org/project/PySide6/)
[![Tests: 90 passed](https://img.shields.io/badge/tests-90%20passed-brightgreen.svg)](tests/)
[![Security: Policy](https://img.shields.io/badge/security-SECURITY.md-blue.svg)](SECURITY.md)
[![Security SLA: 48h Response](https://img.shields.io/badge/security%20SLA-48h%20response-blue.svg)](SECURITY.md)
[![Privacy: 100% Local--First](https://img.shields.io/badge/privacy-100%25%20Local--First-blueviolet.svg)](SECURITY.md)
[![Code Style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Umbrella: open-bricks](https://img.shields.io/badge/umbrella-open--bricks-blue.svg)](https://github.com/open-bricks)
[![LLM Ready](https://img.shields.io/badge/LLM--Ready-llms.txt-brightgreen.svg)](llms.txt)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> [!NOTE]
> For AI agents and automated tools, key architecture and interface metadata are indexed in [llms.txt](llms.txt).

---

### Quick Navigation

- [What it does](#what-it-does)
- [Features](#features)
- [System Architecture & Workflow](#system-architecture--workflow)
- [Lifecycle & Execution Sequence](#lifecycle--execution-sequence)
- [Installation](#installation)
- [Windows Release](#windows-release)
- [Platform Scope](#platform-scope)
- [Governance & Runtime Invariants](#governance--runtime-invariants)
- [Requirements](#requirements)
- [Development Checks](#development-checks)
- [Configuration](#configuration)
- [Related Tools](#related-tools)
- [License](#license)

---

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
flowchart TD
    User(["User (Desktop Interaction)"]) -->|"right-click / click"| Tray["Windows System Tray (MailProcessor)"]

    subgraph Core ["MailProcessor Desktop Core"]
        Tray -->|"reads / writes state"| Config["Config Manager<br/>(%LOCALAPPDATA%/MailProcessor/config.json)"]
        Tray -->|"opens configuration"| SettingsDialog["Settings Dialog (Paths & Autostart)"]
        Tray -->|"exports offline state"| Snapshot["Snapshot Exporter (mailprocessor-suite-v1.json)"]
        Tray -->|"first launch / missing tools"| Wizard["Setup Wizard & Local Scanner"]
        Wizard -->|"downloads releases"| Downloader["GitHub Releases Downloader (Zip-Slip Safe)"]
    end

    subgraph Tools ["Universal Mail Suite (Subprocesses)"]
        Tray -->|"launches tool (subprocess)"| Tool1["Universal Mail Cleaner<br/>(Rule-based IMAP Mailbox Cleaner)"]
        Tray -->|"launches tool (subprocess)"| Tool2["Universal Docs Grabber<br/>(Document & Attachment Grabber)"]
        Tray -->|"launches tool (subprocess)"| Tool3["Universal Invoice Mail<br/>(Automated Invoice Extractor)"]
    end

    Downloader -->|"installs archive to"| LocalTools["%LOCALAPPDATA%/MailProcessor/tools/"]
    LocalTools -.->|"provides binaries"| Tools
```

## Lifecycle & Execution Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User as "Desktop User"
    participant Tray as "Tray Application (PySide6)"
    participant Cfg as "ConfigManager"
    participant Wiz as "Setup Wizard / Downloader"
    participant GH as "GitHub Releases API"
    participant Proc as "Subprocess Runner"
    participant Tool as "Universal Mail Tool"

    User->>Tray: Launch MailProcessor (main.py / start.bat)
    Tray->>Cfg: Load settings (%LOCALAPPDATA%/MailProcessor/config.json)
    alt First Run / Unconfigured Tools
        Tray->>Wiz: Show Setup Wizard
        Wiz->>Wiz: Scan sibling folders for installed tools
        opt Download missing tools
            Wiz->>GH: Fetch latest release assets (Zip-Slip protected)
            GH-->>Wiz: Release archive ZIP
            Wiz->>Wiz: Extract to %LOCALAPPDATA%/MailProcessor/tools/
        end
        Wiz->>Cfg: Save discovered & configured tool paths
    end
    Tray-->>User: System tray icon active in notification area

    User->>Tray: Right-click tray icon & select tool
    Tray->>Proc: launch_tool(tool_id, tool_path)
    Proc->>Tool: Spawn unprivileged detached process (RunAsInvoker)
    Tool-->>User: Universal Mail Tool GUI opens (Clean / Grab / Invoice)

    opt Snapshot Export
        User->>Tray: Select "Export Snapshot"
        Tray->>Cfg: Read tool versions & metadata
        Tray->>Tray: Sanitize paths & write mailprocessor-suite-v1.json
        Tray-->>User: Confirmation notification
    end
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

## Platform Scope

MailProcessor is a Windows desktop tray launcher. The former web/PWA companion
was intentionally removed after its use-case review; the redacted snapshot is
not a synchronization interface or a mobile product. macOS and Linux retain a
source-level contract only, not a packaged end-user release; its reproducible
check and explicit non-goals are documented in
[MACOS_LINUX_SOURCE_SMOKE.md](MACOS_LINUX_SOURCE_SMOKE.md). Android/iOS,
Capacitor, and server synchronization have no active product surface. A future
native or device claim requires a new product decision plus its own build and
device/emulator acceptance. Store blockers and the next required evidence are
tracked in [RELEASES.md](RELEASES.md#current-platform-scope-2026-08-26).

## Governance & Runtime Invariants

The following invariants define the operational and security guarantees of MailProcessor:

| Invariant ID | Name | Standard / Policy | Verification & Guarantee |
|---|---|---|---|
| `INV-LOCAL-01` | **100% Local-First & Zero Egress** | Offline Privacy Standard | Operates entirely on the local machine. No telemetry, no background analytics, no cloud relay, and zero storage of email content, passwords, or credentials. |
| `INV-NOELEV-02` | **Non-Elevation & RunAsInvoker** | Windows Least Privilege | Runs exclusively as standard unprivileged user. Never requests UAC elevation (`runAsInvoker`). |
| `INV-ZIPSLIP-03` | **Zip-Slip Traversal Defense** | CWE-22 Security Standard | Tool downloads from GitHub releases validate archive member paths to prevent directory traversal attacks before extraction. |
| `INV-CFGISO-04` | **Local AppData Isolation** | Windows AppData Convention | Configuration is isolated under `%LOCALAPPDATA%\MailProcessor\config.json`. No registry pollution except optional per-user autostart entry. |
| `INV-PROCLIF-05` | **Safe Subprocess Lifecycle** | Clean Process Separation | Launches Universal Mail Tools via detached unprivileged subprocesses (`subprocess.Popen`) preventing parent tray lockups or cascaded crashes. |
| `INV-REDACT-06` | **Deterministic Snapshot Redaction** | Data Minimization | `mailprocessor-suite-v1.json` exports redact machine-specific absolute paths to protect user privacy in shared or offline bug reports. |
| `INV-OSPAR-07` | **Cross-Platform Source Smoke Contract** | Multi-OS Integrity | Primary product surface is Windows Desktop Tray; multi-platform smoke test matrix verifies source-level compatibility across Ubuntu and macOS. |
| `INV-SLA-08` | **Security Response & Triage SLA** | Responsible Disclosure | 48-hour response SLA and 5-business-day triage commitment through `security@ellmos.ai` and GitHub Security Advisories. |

## Requirements

- Python 3.10+
- PySide6 6.x
- One or more Universal Mail Tools (auto-downloaded via wizard)

## Development Checks

```bash
python -m pytest -q
python -m compileall .
```

Current local test suite: 79 Pytest tests.

## Configuration

Settings are stored in `%LOCALAPPDATA%\MailProcessor\config.json`.

Tools are installed to `%LOCALAPPDATA%\MailProcessor\tools\`.

## Related Tools

Part of the [doc-bricks](https://github.com/doc-bricks) mail suite and [open-bricks](https://github.com/open-bricks) umbrella:

| Tool | Category | Role & Description | Status | Repository |
|------|----------|-------------------|--------|------------|
| [UniversalMailCleaner](https://github.com/doc-bricks/UniversalMailCleaner) | Mail Hygiene | Rule-based IMAP mailbox cleaner with safe mode | Active / Supported | `doc-bricks/UniversalMailCleaner` |
| [UniversalDocsGrabber](https://github.com/doc-bricks/UniversalDocsGrabber) | Mail Extraction | Download documents and attachments from IMAP mail | Active / Supported | `doc-bricks/UniversalDocsGrabber` |
| [UniversalInvoiceMail](https://github.com/doc-bricks/UniversalInvoiceMail) | Mail Extraction | Extract invoices and receipts automatically from IMAP mail | Active / Supported | `doc-bricks/UniversalInvoiceMail` |
| [FormularErstellen](https://github.com/doc-bricks/FormularErstellen) | Document Tools | Interactive form generator and document template engine | Sibling Tool | `doc-bricks/FormularErstellen` |
| [PDFtoPDFocr](https://github.com/doc-bricks/PDFtoPDFocr) | Document OCR | Searchable PDF OCR pipeline and document text recognition | Sibling Tool | `doc-bricks/PDFtoPDFocr` |
| [DokuZen](https://github.com/doc-bricks/DokuZen) | Knowledge Hub | Desktop document organizer, file classifier, and knowledge hub | Sibling Tool | `doc-bricks/DokuZen` |
| [open-bricks](https://github.com/open-bricks) | Umbrella | Umbrella ecosystem, shared policies, and open-source catalog | Umbrella Hub | `open-bricks/open-bricks` |

## License

MIT License — see [LICENSE](LICENSE)
