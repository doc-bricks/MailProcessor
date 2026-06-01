# MailProcessor Web/PWA-Portierung — Status

**Quelle:** `../` (Python, PySide6/PyQt6)
**Ziel:** Web/PWA mit Capacitor-Wrapper (Android + iOS)
**App-ID:** `com.lukas.mailprocessor`
**Erstellt:** 2026-05-25 (Mac Studio Scaffold-Run)

## Status

| Schritt | Status | Dateien |
|---------|--------|---------|
| 1. Projektstruktur | GERUEST | Vite+React+TS+Tailwind+Capacitor, kein `npm install` ausgefuehrt |
| 2. Austauschformat | OFFEN | `mailprocessor-export-v1.json` aus Desktop importieren |
| 3. Lokaler Speicher | OFFEN | IndexedDB (idb/dexie) statt SQLite |
| 4. UI-Screens | OFFEN | Mobile Workflows priorisieren |
| 5. PWA-Manifest + Icons | OFFEN | manifest.webmanifest + Icons in public/ |
| 6. Capacitor-Wrapper | OFFEN | `npx cap add android` (Xcode fuer iOS noch nicht da) |
| 7. Build verifizieren | OFFEN | `npm run build && npx cap sync` |

## Naechste Schritte

1. `web_companion` nach `~/dev/mailprocessor-companion/` spiegeln (OneDrive ist langsam fuer node_modules).
2. `npm install` ausfuehren.
3. `npm run dev` starten, Browser auf `http://localhost:5173`.
4. Desktop-Exportformat definieren oder uebernehmen (`../../GUIDE.md` -> `mediplaner-export-v1.json`-Vorbild).
5. Import-View fuer Exportdatei bauen.
6. P1-Screens als Mobile-Prototyp bauen.
7. `npx cap add android`, dann `cap sync` + Android Studio fuer ersten APK-Build.

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
- Eine Codebasis fuer Browser + Android + iOS
- Desktop bleibt autoritative Quelle, Mobile ist Companion
- Geringere Wartungslast als getrennte native Apps
- Bessere Eignung fuer datensensitive Inhalte ohne komplexen App-Store-Review

## iOS-Status

iOS-Wrapper kann erst gebaut werden, wenn Xcode auf dem Mac Studio installiert ist
(siehe `.SYNC/_onboarding/00_OVERVIEW.md`). Bis dahin: PWA testbar im Mobile-Safari.

## Wichtig: node_modules NICHT in OneDrive

`node_modules` enthaelt zigtausende kleiner Dateien — OneDrive-Sync wuerde
nicht hinterherkommen. Daher entweder per Spiegel arbeiten oder `node_modules`
streng ausschliessen.
