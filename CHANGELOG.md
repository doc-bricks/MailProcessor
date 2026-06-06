# Changelog — MailProcessor

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

---

## [Unreleased]

### Added
- PWA installability for `web_companion/`: `manifest.webmanifest` with `id`, `scope`, brand `theme_color` `#1E78C8`, 192 and 512 icon entries; pre-build `sw.js` shell with offline fallback; `offline.html` German offline page; 15 Node.js PWA tests in `tests/pwa.test.mjs`; test script `npm test` added to `package.json`.
- Read-only Desktop-Snapshot export `mailprocessor-suite-v1.json` with redacted path hints for the companion workflow.
- Tray action to export the current MailProcessor workspace snapshot directly as JSON.
- GitHub Actions test workflow for Python 3.10, 3.11, and 3.12.
- `llms.txt` with machine-readable project context for the doc-bricks mail suite.

### Changed
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
