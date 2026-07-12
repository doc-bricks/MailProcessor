# MailProcessor Web/PWA-Portierung — Status

**Quelle:** `../` (Python, PySide6/PyQt6)
**Ziel:** Web/PWA mit Capacitor-Wrapper (Android + iOS)
**App-ID:** `com.lukas.mailprocessor`
**Erstellt:** 2026-05-25 (Mac Studio Scaffold-Run)

## Status

| Schritt | Status | Dateien |
|---------|--------|---------|
| 1. Projektstruktur | GERÜST | Vite+React+TS+Tailwind+Capacitor, kein `npm install` ausgeführt |
| 2. Austauschformat | DONE | Import-View + Validierung für `mailprocessor-suite-v1.json`, lokale Read-only-Referenz via `localStorage` |
| 3. Lokaler Speicher | DONE | Read-only Referenz via `localStorage`; `diffSnapshots()` in snapshot.js ermöglicht Vergleich beim erneuten Import (Statusänderungen, hinzugekommene/entfernte Tools); IndexedDB bleibt Nicht-Ziel (PWA braucht nur einen lokalen Referenz-Snapshot) |
| 4. UI-Screens | IN ARBEIT | Import-/Statussicht + Diff-Anzeige umgesetzt (2026-06-28); Android-/iOS-PWA-Smoke-Contract mit echter Snapshot-Fixture ergänzt (2026-07-13); echter Geräte-Signoff offen |
| 5. PWA-Manifest + Icons | DONE | manifest.webmanifest + sw.js + offline.html in public/; 15/15 Tests grün |
| 6. Capacitor-Wrapper | OFFEN | `npx cap add android` (Xcode für iOS noch nicht da) |
| 7. Build verifizieren | OFFEN | `npm run build && npx cap sync` |

## Nächste Schritte

1. `web_companion` nach `~/dev/mailprocessor-companion/` spiegeln (OneDrive ist langsam für node_modules).
2. `npm install` ausführen.
3. `npm run dev` starten, Browser auf `http://localhost:5173`.
4. IndexedDB-Modell am read-only Snapshot ausrichten, sobald mehr als eine lokale Referenz nötig ist.
5. P1-Screens als Mobile-Prototyp um die bestehende Import-/Statussicht herum bauen.
6. `npx cap add android`, dann `cap sync` + Android Studio für ersten APK-Build.

## Mobile-Smoke-Contract

Lokaler Contract:

```bash
node --test tests/mobile_pwa_smoke.test.mjs
```

Die Fixture `tests/mobile_smoke_snapshot.json` bildet einen echten
`mailprocessor-suite-v1`-Desktop-Export mit redigierten Pfadhinweisen ab. Der
Smoke deckt Android-Chrome- und iOS-Safari-PWA-Metadaten, Offline-Assets,
lokale Browser-Speicherung und Snapshot-Diff ab. Ein echter Geräte- oder
Emulator-Signoff bleibt offen und ist in `MOBILE_PWA_SMOKE.md` beschrieben.

## Voraussetzung Mac Studio

```zsh
# Node + npm
node --version    # >=20
npm --version

# Capacitor CLI (global installiert: 7.6.5)
cap --version

# Android Toolchain (in ~/.zshrc gesetzt)
export JAVA_HOME=/opt/homebrew/opt/openjdk@17
export ANDROID_HOME=/opt/homebrew/share/android-commandlinetools
```

## Warum PWA statt nativ?

Diese Entscheidung folgt der bestehenden `../PORTIERUNGSPLAN.md` (Stand 2026-05-24).
Kernpunkte:
- Eine Codebasis für Browser + Android + iOS
- Desktop bleibt autoritative Quelle, Mobile ist Companion
- Geringere Wartungslast als getrennte native Apps
- Bessere Eignung für datensensitive Inhalte ohne komplexen App-Store-Review

## iOS-Status

iOS-Wrapper kann erst gebaut werden, wenn Xcode auf dem Mac Studio installiert ist
(siehe `.SYNC/_onboarding/00_OVERVIEW.md`). Bis dahin: PWA testbar im Mobile-Safari.

## Wichtig: node_modules NICHT in OneDrive

`node_modules` enthält zigtausende kleiner Dateien — OneDrive-Sync würde
nicht hinterherkommen. Daher entweder per Spiegel arbeiten oder `node_modules`
streng ausschließen.
