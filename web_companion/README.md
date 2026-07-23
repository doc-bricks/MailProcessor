# MailProcessor — Web/PWA Companion

Vite + React + TypeScript + Tailwind + Capacitor.

## Erste Schritte

```bash
# Empfohlen: lokalen Spiegel außerhalb OneDrive nutzen
cp -r web_companion ~/dev/mailprocessor-companion/
cd ~/dev/mailprocessor-companion/

npm install
npm run dev              # Browser-Dev-Server
npm run build            # Production-Build nach dist/

# Capacitor: native Wrapper
npx cap add android
npm run cap:sync
npm run cap:android      # öffnet Android Studio
```

## Architektur

- **PWA** via `vite-plugin-pwa` (Service Worker, Manifest)
- **Datenformat:** Import `mailprocessor-suite-v1.json` aus Desktop-Quelle
- **Statussicht:** lokale read-only Referenzansicht mit Tool-Status, Versionen, Pfad-Hinweisen und Desktop-Aktionshinweisen
- **Lokaler Speicher:** IndexedDB (per `idb` oder `dexie`) statt SQLite
- **Capacitor:** schlanke native Wrapper für Android + iOS

## App-ID / Bundle

`com.lukas.mailprocessor` — wird sowohl für Capacitor als auch für Play/App Store gebraucht.

## Aktueller Companion-Stand

- JSON-Datei oder eingefügten Snapshot `mailprocessor-suite-v1.json` importieren
- Snapshot nur lokal im Browser/PWA halten
- Keine Maildaten, Tokens oder absoluten Privatpfade akzeptieren
- Read-only Referenz für spätere Desktop-Wartung

## Status

Siehe `PORTING_STATUS.md`.
