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

### Laufzeitverhalten und Datenumfang

- **Daten- und Netzwerkumfang des Launchers:** MailProcessor speichert seine Launcher-Konfiguration
  lokal. Wenn Benutzer im Einrichtungsassistenten einen Werkzeug-Download starten, fragt der Launcher
  GitHub-Release-Metadaten ab und lädt das Archiv herunter. Im geprüften Launcher-Quellstand wurde
  keine Telemetrie-Implementierung gefunden. Separat gestartete Werkzeuge haben eigene Datenflüsse;
  dieser Befund beschreibt oder begrenzt deren Netzwerkverhalten nicht.
- **Unprivilegierter User-Mode (Non-Elevation):** MailProcessor benötigt und verlangt keine
  Administratorrechte. Autostart wird ausschließlich im aktuellen Benutzerkontext
  (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`) verwaltet.
- **Zip-Slip- & Pfadtraversierungs-Schutz:** Heruntergeladene Release-Archive werden vor dem
  Entpacken strikt auf Pfadtraversierung (CWE-22) validiert, sodass keine Dateien außerhalb
  des vorgesehenen Tool-Ordners abgelegt werden können.
- **Isolierte Konfiguration:** Konfigurationsdaten werden im lokalen Benutzerdatenverzeichnis
  (`%LOCALAPPDATA%\MailProcessor\config.json`) gehalten. Snapshot-Exporte ersetzen lokale
  Pfadwurzeln; andere Pfade können die letzten Ordnernamen enthalten. Vor dem Teilen prüfen.

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

### Runtime Behavior and Data Scope

- **Launcher data and network scope:** MailProcessor stores its launcher configuration locally.
  When a user starts a tool download in the setup wizard, the launcher requests GitHub release
  metadata and downloads the archive. No telemetry implementation was found in the reviewed
  launcher source. Separately launched tools have their own data flows; this finding does not
  describe or limit their network behavior.
- **Non-Elevation (User Mode):** MailProcessor runs unprivileged in standard user mode.
  Autostart entries are registered exclusively under the user scope
  (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`).
- **Zip-Slip & Path Traversal Guard:** Downloaded release archives are strictly validated
  against path traversal (CWE-22) before extraction, preventing any file writes outside the
  designated tool target directory.
- **Isolated Configuration:** Configuration data is stored in the local user directory
  (`%LOCALAPPDATA%\MailProcessor\config.json`). Snapshot exports replace local data-root paths;
  other paths may retain trailing folder names. Review an export before sharing it.

### Response Time

We aim to acknowledge vulnerability reports within 48 hours and work expeditiously to
deliver verified patches.
