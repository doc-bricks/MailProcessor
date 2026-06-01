# MailProcessor — Web/PWA Companion

Vite + React + TypeScript + Tailwind + Capacitor.

## Erste Schritte

```bash
# Empfohlen: lokalen Spiegel ausserhalb OneDrive nutzen
cp -r web_companion ~/dev/mailprocessor-companion/
cd ~/dev/mailprocessor-companion/

npm install
npm run dev              # Browser-Dev-Server
npm run build            # Production-Build nach dist/

# Capacitor: native Wrapper
npx cap add android
npm run cap:sync
npm run cap:android      # oeffnet Android Studio
```

## Architektur

- **PWA** via `vite-plugin-pwa` (Service Worker, Manifest)
- **Datenformat:** Import `mailprocessor-export-v1.json` aus Desktop-Quelle
- **Lokaler Speicher:** IndexedDB (per `idb` oder `dexie`) statt SQLite
- **Capacitor:** schlanke native Wrapper fuer Android + iOS

## App-ID / Bundle

`com.lukas.mailprocessor` — wird sowohl fuer Capacitor als auch fuer Play/App Store gebraucht.

## Status

Siehe `PORTING_STATUS.md`.
