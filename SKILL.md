---
name: mailprocessor
version: 0.1.0
description: "Headless CLI and Windows system-tray launcher hub for doc-bricks Universal Mail Tools (UniversalMailCleaner, UniversalDocsGrabber, UniversalInvoiceMail)."
---

# MailProcessor — Product Skill (Human & LLM Usage)

MailProcessor is a local-first Windows system-tray hub and headless CLI for the three `doc-bricks` Universal Mail Tools:

- `universal_mail_cleaner` — Universal Mail Cleaner (`mail_imap_cleaner_v1.py`)
- `universal_docs_grabber` — Universal Docs Grabber (`UniversalDocsGrabberV1.py`)
- `universal_invoice_mail` — Universal Invoice Mail (`UniversalInvoiceMail.py`)

## When to use

Use MailProcessor when you need to:

1. Inspect which Universal Mail Tools are configured, valid, or installed on the host.
2. Scan sibling directories or `%LOCALAPPDATA%\MailProcessor\tools\` for supported mail tools.
3. Export a redacted `mailprocessor-suite-v1.json` status snapshot without credentials or mail data.
4. Register, unregister, dry-run validate, or launch one of the three mail tools from a script or assistant.
5. Audit Microsoft Store readiness (`store-readiness`) in strict read-only mode.

## Boundaries & Non-Goals

- MailProcessor is a **launcher and configuration manager**, not an IMAP/SMTP client itself.
- It never stores mailbox passwords, OAuth tokens, or email contents.
- Tool downloads from GitHub Releases happen **only** when explicitly initiated by a human in the GUI setup wizard (never automatically in headless CLI commands).
- No web/PWA companion or mobile app exists.

## Prerequisites & Configuration

- Python `>= 3.10`
- `PySide6 >= 6.6.0, != 6.12.0` is required only for the GUI tray/wizard (`python main.py`).
- Headless CLI commands (`status`, `scan`, `snapshot`, `register`, `unregister`, `launch`, `store-readiness`) run with the Python standard library alone.
- Configuration file: `%LOCALAPPDATA%\MailProcessor\config.json` (or `~/MailProcessor/config.json` fallback when `LOCALAPPDATA` is unset or relative).

## Human & LLM Entry Points

### GUI (Desktop User)

```bash
start.bat
# or
python main.py
```

### Headless CLI (Human & LLM Assistant)

All commands work via `python main.py <command>`, `python mailprocessor_cli.py <command>`, or the console script `mailprocessor <command>`:

| Action | Command | Side Effects |
|---|---|---|
| Show version | `python main.py --version --json` | None (read-only) |
| Inspect tool status | `python main.py status --json` | None (read-only, redacted path hints) |
| Dry-run tool discovery | `python main.py scan --json` | None (read-only) |
| Apply tool discovery | `python main.py scan --apply --json` | Updates `config.json` with discovered tools |
| Print redacted snapshot | `python main.py snapshot` | None (stdout JSON `mailprocessor-suite-v1`) |
| Write redacted snapshot | `python main.py snapshot --out path/to/snapshot.json --json` | Atomic write to target path |
| Register tool path | `python main.py register <tool_id> <path> --json` | Validates script file and updates `config.json` |
| Preview unregister | `python main.py unregister <tool_id> --dry-run --json` | None (read-only) |
| Unregister tool | `python main.py unregister <tool_id> --yes --json` | Clears tool entry in `config.json` (files kept) |
| Dry-run launch check | `python main.py launch <tool_id> --dry-run --json` | None (validates script + Python interpreter) |
| Launch configured tool | `python main.py launch <tool_id> --json` | Spawns detached subprocess with `PYTHONIOENCODING=utf-8` |
| Store readiness audit | `python main.py store-readiness --json` | None (read-only) |

Valid `<tool_id>` values: `universal_mail_cleaner`, `universal_docs_grabber`, `universal_invoice_mail`.

## Exit Codes & Result Verification

- `0`: Command succeeded (or `store-readiness` passed all gates).
- `1`: Runtime launch failure (e.g., `launch` failed to spawn process).
- `2`: Validation error, missing confirmation (`--yes` required for `unregister`), unknown `tool_id`, invalid path, or `store-readiness` blockers remain.

Always pass `--json` for deterministic machine parsing and check `"ok": true` before assuming a mutation or validation succeeded.
