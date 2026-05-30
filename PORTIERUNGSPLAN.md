# Portierungsplan - MailProcessor

Stand: 2026-05-30

## Bedingungsprüfung

Es gab vor diesem Check keinen zentralen `PORTIERUNGSPLAN.md`. Vorhanden war ein grobes, ungetracktes `web_companion/PORTING_STATUS.md` aus einem Scaffold-Lauf vom 2026-05-25. Dieses Dokument ist deshalb Pfad B: Der Plan wird aus den vorhandenen Features, Nutzergruppen und Usecases neu abgeleitet.

## Beste Version: Features

MailProcessor ist kein eigenes Mail-Verarbeitungswerkzeug, sondern ein lokaler Hub für die drei Universal-Mail-Tools:

- System-Tray-Launcher für Universal Mail Cleaner, Universal Docs Grabber und Universal Invoice Mail.
- First-Run-Wizard mit automatischem Scan nach Geschwisterprojekten und manuell gesetzten Tool-Pfaden.
- GitHub-Installer für die drei Tool-Releases.
- Versionsanzeige im Tray-Menü über die `CHANGELOG.md` der installierten Tools.
- Einstellungen für Tool-Pfade, Entfernen, manuelles Hinzufügen, Sprache und Windows-Autostart.
- Lokale Konfiguration unter `%LOCALAPPDATA%\MailProcessor\config.json`.
- Windows-Release als PySide6-Desktop-App.

## Usecases aus den Features

### Usecase-Setting 1: Windows-Arbeitsplatz mit Mail-Automation

Nutzer: Eine Person, die die drei Mail-Tools im Arbeitsalltag nutzt und sie nicht einzeln suchen, installieren oder starten will.

Usecases:

- Nach Windows-Start steht der Tray-Hub bereit.
- Neue oder vorhandene Mail-Tools werden einmalig gefunden, registriert oder per GitHub-Release installiert.
- Nutzer startet das passende Spezialtool aus einem einzigen Tray-Menü.
- Defekte oder verschobene Tool-Pfade werden in den Einstellungen repariert.
- Versionsstände der drei Tools sind schnell sichtbar.

Dieses Setting ist die Vollversion und entscheidet die Hauptplattform.

### Usecase-Setting 2: macOS/Linux-Quellstart für Entwickler und Power-User

Nutzer: Entwickler oder technisch starke Nutzer, die die Suite aus dem Quellcode starten.

Usecases:

- Tool-Scan und manuelle Pfade funktionieren ohne Windows-spezifische Store-Verpackung.
- Tray-Verhalten und Autostart werden pro Plattform nur als Smoke-Test bewertet.
- GitHub-Installer bleibt nutzbar, sofern die drei Zieltools dort ebenfalls lauffähig sind.

Dieses Setting ist nicht identisch mit dem Windows-Endnutzerfall, aber nah genug für Quell-Smokes.

### Usecase-Setting 3: Web/Mobile-Companion für Status und Referenz

Nutzer: Dieselbe Person, aber unterwegs oder auf einem Zweitgerät.

Usecases:

- Import eines Desktop-Snapshots mit Toolliste, Versionen, Pfaden ohne private absolute Details und Installationsstatus.
- Nachschlagen, welche Mail-Tools installiert sind und welche Aufgaben sie übernehmen.
- Optional: Checkliste oder Linkliste für spätere Desktop-Wartung.

Dieses Setting kann die Hauptapp nicht ersetzen, weil Browser, Android und iOS keine lokalen Windows-Tray-Prozesse starten und keine Desktop-Python-Tools in `%LOCALAPPDATA%` verwalten sollen.

## Plattformentscheidung

| Plattform | Entscheidung | Begründung |
|---|---|---|
| Windows Desktop | Hauptplattform | Tray, Autostart, lokale Tool-Pfade und Desktop-Prozessstart sind der Kernnutzen. |
| Windows Store | Kein aktueller Zielkanal | Die App ist ein Launcher/Downloader für lokale Tools und externe Prozesse. GitHub-Release bleibt risikoärmer; Store nur nach separatem FullTrust-, Datenschutz- und Installer-Review erneut prüfen. |
| macOS | P2 Source-Smoke | Grundlogik ist Python/PySide6, aber Tray, Autostart und Tool-Start brauchen plattformspezifische Prüfung. |
| Linux | P2 Source-Smoke | Wie macOS; sinnvoll für Entwickler, nicht als erste Endnutzerlinie. |
| Web/PWA | P3 Companion | Nur Status-/Referenz-Companion mit `mailprocessor-suite-v1.json`, keine Voll-App. |
| Android | P3 PWA-Smoke | Nur über Web/PWA-Companion; native Android-App ist kein belegter Usecase. |
| iOS | P3 PWA-Smoke | Nur über Web/PWA-Companion; native iOS-App ist kein belegter Usecase. |

## Synchronisations- und Austauschmodell

Direkte Synchronisation ist kein Ziel. MailProcessor selbst hält nur lokale Launcher-Konfigurationen und keine fachlichen Maildaten. Ein dateibasierter Export reicht für den Companion-Fall:

- Geplantes Format: `mailprocessor-suite-v1.json`.
- Inhalt: App-Version, Exportzeitpunkt, Tool-IDs, Anzeigenamen, erkannte Versionen, Installationsstatus und optional redigierte Pfadhinweise.
- Nicht enthalten: Mail-Inhalte, Zugangsdaten, Tokens, Passwörter, komplette private absolute Pfade oder Tool-interne Datenbanken.

## Entwicklungsplan

### P0 - Desktop-Plan absichern

- `mailprocessor-suite-v1.json` als Exportformat definieren.
- Desktop-Export als read-only Snapshot ergänzen.
- Konfigurationsprüfung so erweitern, dass fehlende Tools im Snapshot klar markiert werden.

### P1 - Windows-Release stabilisieren

- EXE-Build und `start.bat` gegen den aktuellen dirty Worktree nachziehen, sobald die offenen Codeänderungen abgeschlossen sind.
- GitHub-Release-Flow dokumentieren: MailProcessor selbst plus die drei Zieltools.
- Privacy-Hinweis ergänzen: MailProcessor speichert keine Mailinhalte und keine Zugangsdaten.

### P2 - macOS/Linux-Smokes

- Headless-/offscreen Smoke für `config`, `tool_manager.scan()` und manuelle Tool-Pfade.
- Plattformnotiz zu Tray und Autostart: unterstützt, eingeschränkt oder Nicht-Ziel.

### P3 - Web/PWA-Companion

- Bestehenden `web_companion/`-Scaffold nur als Companion weiterführen.
- Importansicht für `mailprocessor-suite-v1.json` bauen.
- Android/iOS nur als PWA-Installations- und Import-Smoke prüfen.

## Nicht-Ziele

- Native Android- oder iOS-Voll-App.
- Öffentliche Server-Synchronisierung.
- Starten oder Steuern der Desktop-Tools aus einer mobilen App.
- Speichern oder Übertragen von Mailzugängen, Tokens oder Mailinhalten.
- Windows-Store-Einreichung ohne separaten Policy- und FullTrust-Review.
