# Changelog — MailProcessor

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

---

## [Unreleased]

### Fixed

- Streunende Bugsweep-Backup-Ordner (`MailProcessor_BUGSWEEP_*_20260621.bak/`),
  verwaiste Scaffold-Icons ohne Codebezug (`assets/android-icon-*`,
  `assets/splash-icon.png`, doppelte `web_companion/apple-touch-icon*.png` und
  `web_companion/favicon.png` außerhalb von `public/`) sowie vier
  `*_BUGSWEEP_*.bak`-Dateien in `web_companion/` nach `_archive/` verschoben
  (neu gitignored). Keine dieser Dateien wurde von Code, Tests oder Doku
  referenziert.
- README/README-DE: veraltete Testzahl (53) auf die tatsächliche lokale
  Pytest-Anzahl (58) korrigiert.
- `update_files.py`: Der historische harte Benutzerpfad ist durch den aufgelösten
  Skript-Projektordner ersetzt. Der Standardlauf ist ein Dry-Run für genau vier
  dokumentierte Dateien; ein optionaler Zielpfad muss absolut sein und exakt
  zum Projektordner auflösen, bevor `--apply` schreiben darf.
- `installer.PathsPage`: Manuelle Pfadfelder und `Durchsuchen …`-Buttons im
  Einrichtungs-Wizard exponieren jetzt pro Tool sprechende Accessible Names,
  Descriptions und Tooltips statt sich fast nur auf Gruppenüberschrift und
  Position zu verlassen.
- `tool_manager._iter_scan_candidates()`: `iterdir()` auf dem Download-Ordner und auf
  `extracted/`-Unterordnern wird jetzt in `try/except (PermissionError, OSError)` gefangen.
  Bislang konnte ein gesperrter OneDrive-Pfad den gesamten Tool-Scan zum Absturz bringen.
- `tool_manager.ToolManager.launch()`: Sub-Skripte erhalten jetzt explizit
  `PYTHONIOENCODING=utf-8` in ihrer Prozess-Umgebung. Verhindert cp1252-Encoding-Fehler
  bei nicht-ASCII-Ausgaben auf Windows-Systemen ohne englische Systemsprache.
- `tool_manager.download_tool()`: redundantes lokales `import shutil` entfernt
  (bereits auf Modulebene importiert).
- 2 neue Regressionstests in `tests/test_tool_manager.py`:
  `test_scan_handles_permission_error_in_download_dir` und
  `test_launch_sets_pythonioencoding_in_subprocess_env`;
  Testsuite gesamt: 50 Pytest-Tests (alle grün).
- Neuer Installer-Regressionscheck deckt den zugänglichen Kontext der manuellen
  Pfadsteuerung im Wizard ab.

### Security

- Raised the MailProcessor companion Vite dev-server dependency from `^6.0.3` to `^6.4.3` to pick up the Windows dev-server path and editor middleware security fixes.

### Documentation

- Added `MACOS_LINUX_SOURCE_SMOKE.md` plus an executable source-platform smoke
  for config fallback, suite scanning and manual tool-path registration.
- Standardized `llms.txt`: `## Last-checked:` header at line 1, `## Search Phrases` as fenced code block.
- Updated README test count to 53 Pytest tests.
- Added `web_companion/icons/` to `.gitignore` (PWA source icon copies; tracked copies live in `web_companion/public/`).

### Added
- PWA installability for `web_companion/`: `manifest.webmanifest` with `id`, `scope`, brand `theme_color` `#1E78C8`, 192 and 512 icon entries; pre-build `sw.js` shell with offline fallback; `offline.html` German offline page; 15 Node.js PWA tests in `tests/pwa.test.mjs`; test script `npm test` added to `package.json`.
- Read-only Desktop-Snapshot export `mailprocessor-suite-v1.json` with redacted path hints for the companion workflow.
- Tray action to export the current MailProcessor workspace snapshot directly as JSON.
- Companion-Importansicht für echte `mailprocessor-suite-v1.json`-Snapshots mit lokaler read-only Referenzansicht, Statuskarten, Tool-Aktionshinweisen und Validierung gegen absolute Privatpfade.
- GitHub Actions test workflow for Python 3.10, 3.11, and 3.12.
- `llms.txt` with machine-readable project context for the doc-bricks mail suite.

### Changed
- `web_companion` ist nicht mehr nur Scaffold: Snapshot-Import per Datei oder Paste, lokale `localStorage`-Referenz und kompakte Statusoberfläche für die drei Universal-Mail-Tools.
- Node-Testlauf für `web_companion` deckt jetzt auch den Snapshot-Importvertrag ab.
- Fallback für `LOCALAPPDATA` gehärtet: Leere oder relative Werte schreiben Konfiguration und GitHub-Tool-Downloads nicht mehr relativ zum Arbeitsordner, sondern sauber unter `Path.home()/MailProcessor`; neue Regressionstests decken beide Fehlkonfigurationen ab.
- MailProcessor nutzt jetzt ein verifiziertes eigenes Tray-/Build-Icon statt still auf das generische Fallback zu rutschen; neue Regressionstests sichern Dateiladung, ICO-Größen und Gleichstand von `resources/icon.ico` und `MailProcessor.ico`.
- Load tray icon from `resources/icon.ico` with a fallback to the existing generated envelope icon.
- Regenerate `resources/icon.ico` in 16x16, 32x32, and 256x256 sizes via Pillow.
- Validate and repair Windows autostart registry entry during startup so it points to the current executable.
- Use a real Python interpreter when launching tools from a frozen MailProcessor build.
- Preserve installer wizard selections across page rebuilds and keep the wizard blocked while GitHub downloads are still running.
- Align companion documentation on the final snapshot name `mailprocessor-suite-v1.json`.
- Document the local 32-test verification command in both READMEs.
- Rescan logic now rediscovers GitHub-installed tools from the extracted installer layout under `%LOCALAPPDATA%\\MailProcessor\\tools\\<tool_id>\\extracted\\...`.

## [0.1.0] - 2026-05-02

### Added
- System tray launcher with right-click context menu to start any registered Mail Tool
- First-run installer wizard with language selection (DE/EN) and automatic tool scan
- Manual path configuration for tools not auto-detected
- Settings dialog with tool management (add, remove, change path) and autostart option
- GitHub installer: download tools directly from GitHub releases (with progress display)
- Version display in tray menu (reads from each tool's CHANGELOG.md)
- Autostart support via Windows Registry (HKCU\...\Run)
- DE/EN localization via `i18n.py`
- Supports: Universal Mail Cleaner, Universal Docs Grabber, Universal Invoice Mail

---

*Alle Versionen | All versions: see this file*
