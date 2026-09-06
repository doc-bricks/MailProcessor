# Sicherheitsrichtlinie / Security Policy

## Deutsch

### Unterstützte Versionen

Sicherheitsupdates werden für folgende Versionen bereitgestellt:

| Version | Unterstützt |
|---------|-------------|
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x: |

### Sicherheitslücken melden

Wenn Sie eine Sicherheitslücke oder ein Sicherheitsrisiko in MailProcessor finden,
melden Sie diese bitte verantwortungsvoll:

1. **Kein öffentliches Issue eröffnen.**
2. **GitHub Private Vulnerability Reporting verwenden:**
   [Security Advisories](https://github.com/doc-bricks/MailProcessor/security/advisories/new)
3. Alternativ per E-Mail an das Sicherheitsteam:
   - `security@ellmos.ai`
   - `support@lukasgeiger.com`
   - `lukas@open-bricks.org`

### Verbindliche Sicherheitsgarantien (Invarianten)

- **Local-First & Zero-Egress:** MailProcessor speichert keine E-Mail-Inhalte, Passwörter,
  Tokens oder IMAP-Zugangsdaten. Alle Operationen laufen lokal auf dem Rechner des Nutzers.
- **Unprivilegierter User-Mode (Non-Elevation):** MailProcessor benötigt und verlangt keine
  Administratorrechte. Autostart wird ausschließlich im aktuellen Benutzerkontext
  (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`) verwaltet.
- **Zip-Slip- & Pfadtraversierungs-Schutz:** Heruntergeladene Release-Archive werden vor dem
  Entpacken strikt auf Pfadtraversierung (CWE-22) validiert, sodass keine Dateien außerhalb
  des vorgesehenen Tool-Ordners abgelegt werden können.
- **Isolierte Konfiguration:** Konfigurationsdaten werden im lokalen Benutzerdatenverzeichnis
  (`%LOCALAPPDATA%\MailProcessor\config.json`) gehalten. Snapshot-Exporte redigieren lokale
  Pfade und enthalten keinerlei geheime Informationen.

### Reaktionszeit

Wir bestätigen den Empfang von Sicherheitsmeldungen in der Regel innerhalb von 48 Stunden
und stellen zeitnah qualifizierte Fehlerbehebungen bereit.

---

## English

### Supported Versions

Security updates are provided for the following versions:

| Version | Supported |
|---------|-----------|
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x: |

### Reporting a Vulnerability

If you discover a security vulnerability or concern in MailProcessor, please report it responsibly:

1. **Do not open a public issue.**
2. **Use GitHub Private Vulnerability Reporting:**
   [Security Advisories](https://github.com/doc-bricks/MailProcessor/security/advisories/new)
3. Or email our security contacts directly:
   - `security@ellmos.ai`
   - `support@lukasgeiger.com`
   - `lukas@open-bricks.org`

### Core Security Invariants

- **Local-First & Zero-Egress:** MailProcessor does not store email contents, passwords,
  tokens, or IMAP credentials. It operates 100% locally with zero cloud telemetry.
- **Non-Elevation (User Mode):** MailProcessor runs unprivileged in standard user mode.
  Autostart entries are registered exclusively under the user scope
  (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`).
- **Zip-Slip & Path Traversal Guard:** Downloaded release archives are strictly validated
  against path traversal (CWE-22) before extraction, preventing any file writes outside the
  designated tool target directory.
- **Isolated Configuration:** Configuration data is stored in the local user directory
  (`%LOCALAPPDATA%\MailProcessor\config.json`). Snapshot exports redact local paths and
  contain zero secrets.

### Response Time

We aim to acknowledge vulnerability reports within 48 hours and work expeditiously to
deliver verified patches.
