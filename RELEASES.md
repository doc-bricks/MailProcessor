# Releases

## v0.1.0 - 2026-05-02

### GitHub

- Repository: [doc-bricks/MailProcessor](https://github.com/doc-bricks/MailProcessor)
- Tag: `v0.1.0`
- Type: public Windows desktop release

### Local release artifacts

- `releases/v0.1.0/MailProcessor-0.1.0-desktop.exe`
- `releases/v0.1.0/MailProcessor-0.1.0-source.zip`
- `releases/v0.1.0/CHANGELOG.md`
- `releases/v0.1.0/SHA256SUMS.txt`

### Notes

- The binary release is built from `main.py` via `build_exe.bat`.
- The app ships as a tray launcher for Universal Mail Cleaner, Universal Docs Grabber, and Universal Invoice Mail.

### Current platform scope (2026-08-14)

- Windows desktop remains the only active product line.
- The former web/PWA companion was intentionally removed after its use-case review.
- The redacted `mailprocessor-suite-v1.json` export is local-only and does not
  establish mobile, synchronization, Store, or native macOS/Linux release readiness.

### Microsoft Store decision (2026-08-16)

- Status: **deferred / no-go for submission**.
- `store_readiness.py` now checks the immutable release bundle, SHA-256 values,
  Store metadata, AppxManifest capabilities, privacy/support material, runtime
  licenses, MSIX presence, and WACK evidence without changing the project.
- The current v0.1.0 source ZIP matches its recorded SHA-256, but the archived
  desktop EXE does not. The v0.1.0 release remains unchanged.
- MailProcessor requires `runFullTrust` for external process launch and Windows
  autostart, plus `internetClient` for its opt-in GitHub installer.
- A new versioned Windows bundle, Store metadata/manifest, live privacy and
  support routes, MSIX, and a passing elevated WACK report are required before
  the Store channel can be reconsidered.
