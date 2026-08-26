# Changelog — MailProcessor

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

---

## [Unreleased]

### Maintenance

- **Platform/status contract readback (2026-08-26)**:
  - Confirmed that Windows desktop is the only active product line and that the
    removed web/PWA/Capacitor files are historical, not open implementation gates.
  - Linked the macOS/Linux source smoke and the separate native/device and Store
    evidence required before any broader platform claim.
  - Verified 73/73 Pytest tests, source-platform smoke, Compileall, active
    documentation links, UTF-8/NUL hygiene, and whitespace consistency.
- **Fail-closed Microsoft Store readiness gate (2026-08-16)**:
  - Added `store_readiness.py` with human-readable and JSON output for release
    hashes, Store metadata, AppxManifest capabilities, privacy/support files,
    dependency licenses, MSIX presence, and WACK evidence.
  - Derived the required `runFullTrust` and `internetClient` capabilities from
    the external process/autostart and opt-in GitHub installer behavior.
  - The current v0.1.0 audit is deferred: the source ZIP hash matches, while the
    desktop EXE hash differs from `SHA256SUMS.txt`; Store metadata, manifest,
    privacy/support material, MSIX, and WACK evidence are still absent.
  - Added six regression tests for a complete fixture, tampered release,
    checksum path traversal, missing FullTrust declaration, missing
    privacy/support material, and self-exclusion during capability detection.
- **Platform scope synchronization (2026-08-14)**:
  - Aligned release, README, export-format, and LLM documentation with the intentional removal of the former web/PWA companion.
  - Kept `mailprocessor-suite-v1.json` as a redacted local-reference export; it does not establish a mobile, synchronization, Store, or native macOS/Linux release path.
- **Security & License Audit (2026-08-14)**:
  - **Security**: Added archive member path validation in `tool_manager.py` (`download_tool`) against Zip Slip path traversal (CWE-22) when downloading and extracting release archives.
  - **License & Dependency Inventory**: Synchronized `THIRD_PARTY_LICENSES.txt` and `test_third_party_licenses.py` with the current desktop runtime dependencies (`PySide6`, `PySide6_Addons`, `PySide6_Essentials`, `shiboken6`), removing legacy npm references from the previously deleted web companion. Aligned `pyproject.toml` dependencies (`PySide6>=6.6.0`) with `requirements.txt`.
  - **Git & Repository Hygiene**: Cleaned obsolete `web_companion/icons/` ignore line in `.gitignore` and registered `"license": "MIT"` in `.SOFTWARE/releases.json`.
  - **Test Suite**: Added unit tests `test_download_tool_prevents_zip_slip` and `test_download_tool_extracts_safe_archive` in `tests/test_tool_manager.py`. All 60 Pytest tests passing (100% green).
- **Discoverability, README & SEO Verification (2026-07-29)**:
  - Updated `llms.txt` Last-checked timestamp to `2026-07-29`.
  - Verified repository presentation, bilingual documentation (`README.md` / `README-DE.md`), screenshots (`README/screenshots/main.png`), and Pytest test suite (58/58 passed).
- **Discoverability, SEO & Visual Architecture Maintenance (2026-07-27)**:
  - Added Mermaid System Architecture & Data Flow Diagram to `README.md` and `README-DE.md`.
  - Updated `llms.txt` header date to `2026-07-27` with 58/58 Pytest verification status notes.
  - Formulated non-automated marketing and visibility recommendations in `MARKETING-LOG.txt`.
- **Technical Hygiene & Documentation Maintenance (2026-07-25)**:
  - Added PEP 621 `pyproject.toml` with package metadata and Pytest configuration (`pythonpath = "."`).
  - Updated `llms.txt` header date to `2026-07-25` and aligned privacy/local-first architecture descriptions.
  - Enhanced `README.md` and `README-DE.md` with Shields.io status badges and AI/LLM integration callout (`> [!NOTE]`).
  - Verified local verification suite (58/58 Pytest tests passed).

### Fixed

- `installer._DownloadThread.run()`: Unexpected exceptions from a download
  backend are now converted into a completion error and still emit
  `finished_signal`. This prevents the setup wizard from remaining locked in
  an active-download state; a regression test covers the worker failure path.
- `tool_manager.download_tool()` & `apply_scan_results()`:
  - Skript-Erkennung bei Release-Downloads unterstützt nun flache Archive (direkt in `extract_root`) sowie verschachtelte Unterverzeichnisse (z. B. `repo-tag/src/`), wodurch Fehlermeldungen `"Could not find main script in downloaded archive"` behoben werden.
  - Release-Tag-Namen mit Schrägstrichen (z. B. `release/v1.0.0`) oder Sonderzeichen werden für den ZIP-Dateinamen bereinigt (`safe_tag`), um `FileNotFoundError` beim Download zu verhindern.
  - `apply_scan_results()` heilt nun auch aktivierte Tools mit verwaistem/ungültigem Pfad (`is_path_valid == False`) automatisch bei einem erneuten Scan.
  - Vier neue Regressionstests in `tests/test_tool_manager.py` hinzugefügt.
- `tool_manager.download_tool()`: Ein durch eine Datei blockiertes Zielverzeichnis
  wird jetzt als Rückgabefehler behandelt. Zuvor propagierte `mkdir()` den Fehler
  aus dem Download-Thread, sodass der Setup-Assistent kein Abschluss-Signal erhielt
  und gesperrt blieb. Ein Regressionstest deckt den Zielkonflikt ab.
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
