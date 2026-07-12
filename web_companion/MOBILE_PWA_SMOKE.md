# Mobile PWA Smoke - MailProcessor Companion

Stand: 2026-07-13

## Zweck

Dieser Smoke prüft den geplanten Android-/iOS-PWA-Companion mit einer echten
`mailprocessor-suite-v1.json`-Snapshot-Fixture. Er ersetzt keinen Geräte-Signoff,
aber er hält den lokalen Vertrag reproduzierbar fest: Import, redigierte
Pfadhinweise, lokale Browser-Speicherung, Offline-Assets und mobile PWA-Metadaten.

## Lokaler Contract-Smoke

```powershell
npm --prefix web_companion test
node --test web_companion/tests/mobile_pwa_smoke.test.mjs
```

Die Fixture liegt unter:

```text
web_companion/tests/mobile_smoke_snapshot.json
```

Sie enthält einen verfügbaren, einen fehlenden und einen nicht eingerichteten
Tool-Eintrag. Absolute Privatpfade, Mailinhalte, Tokens und Zugangsdaten sind
absichtlich nicht enthalten.

## Manueller Android-Chrome-Smoke

1. Companion aus einem lokalen Spiegel oder aus `web_companion/` starten:
   `npm run dev -- --host 0.0.0.0`.
2. Android Chrome im selben lokalen Netz öffnen.
3. `mobile_smoke_snapshot.json` importieren oder den JSON-Inhalt einfügen.
4. Prüfen: Statuskarten zeigen 3 Tools, 1 verfügbar und 2 mit Aufmerksamkeit.
5. PWA installieren, danach offline öffnen.
6. Prüfen: Offline-Shell lädt, gespeicherte Referenz bleibt lokal verfügbar.

## Manueller iOS-Safari-Smoke

1. Safari auf iPhone/iPad gegen denselben lokalen Dev-Server öffnen.
2. Snapshot importieren oder einfügen.
3. Über "Zum Home-Bildschirm" installieren.
4. Prüfen: App-Titel, Touch-Icon, Safe-Area-Layout und Statusansicht.
5. Gerät offline schalten und erneut starten.

## Grenzen

- Kein nativer Android-/iOS-Vollclient.
- Kein Upload, keine Server-Synchronisierung, keine Desktop-Fernsteuerung.
- Kein Transport von Maildaten, Tokens, Passwörtern oder vollständigen privaten
  Pfaden.
- Echter Geräte-/Emulator-Signoff bleibt ein separater manueller Schritt.
