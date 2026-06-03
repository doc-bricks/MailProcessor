# MailProcessor Web/PWA-Portierung — Status

**Quelle:** `../` (Python, PySide6/PyQt6)
**Ziel:** Web/PWA mit Capacitor-Wrapper (Android + iOS)
**App-ID:** `com.lukas.mailprocessor`
**Erstellt:** 2026-05-25 (Mac Studio Scaffold-Run)

## Status

| Schritt | Status | Dateien |
|---------|--------|---------|
| 1. Projektstruktur | GERÜST | Vite+React+TS+Tailwind+Capacitor, kein `npm install` ausgeführt |
| 2. Austauschformat | IN ARBEIT | `mailprocessor-suite-v1.json` aus Desktop importieren |
| 3. Lokaler Speicher | OFFEN | IndexedDB (idb/dexie) statt SQLite |
| 4. UI-Screens | OFFEN | Mobile Workflows priorisieren |
| 5. PWA-Manifest + Icons | OFFEN | manifest.webmanifest + Icons in public/ |
| 6. Capacitor-Wrapper | OFFEN | `npx cap add android` (Xcode für iOS noch nicht da) |
| 7. Build verifizieren | OFFEN | `npm run build && npx cap sync` |

## Nächste Schritte

1. `web_companion` nach `~/dev/mailprocessor-companion/` spiegeln (OneDrive ist langsam für node_modules).
2. `npm install` ausführen.
3. `npm run dev` starten, Browser auf `http://localhost:5173`.
4. Import-View für `mailprocessor-suite-v1.json` bauen.
5. IndexedDB-Modell am read-only Snapshot ausrichten.
6. P1-Screens als Mobile-Prototyp bauen.
7. `npx cap add android`, dann `cap sync` + Android Studio für ersten APK-Build.

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
