# Exportformat - mailprocessor-suite-v1.json

Stand: 2026-05-30

Dieses Format ist für einen späteren Web/PWA-Companion vorgesehen. Es ist ein read-only Snapshot der MailProcessor-Launcher-Konfiguration und kein Synchronisationsformat.

## Zweck

Der Export beantwortet unterwegs oder auf einem Zweitgerät:

- Welche Universal-Mail-Tools sind in MailProcessor registriert?
- Welche Versionen wurden zuletzt erkannt?
- Welche Tools fehlen oder brauchen Wartung?
- Welche Desktop-Aktion ist als Nächstes sinnvoll?

## Datenschutzgrenze

Der Export darf keine Mailinhalte, Zugangsdaten, Tokens, Passwörter, vollständigen lokalen Pfade oder Tool-interne Datenbanken enthalten. Pfade werden höchstens als redigierte Hinweise ausgegeben, zum Beispiel `LOCALAPPDATA/MailProcessor/tools/universal_docs_grabber`.

## JSON-Skizze

```json
{
  "schema": "mailprocessor-suite-v1",
  "exported_at": "2026-05-30T12:00:00+02:00",
  "app": {
    "name": "MailProcessor",
    "version": "0.1.0",
    "platform": "windows"
  },
  "tools": [
    {
      "id": "universal_mail_cleaner",
      "display_name": "Universal Mail Cleaner",
      "enabled": true,
      "installed_by": "github",
      "version": "v1.2.0",
      "status": "available",
      "path_hint": "LOCALAPPDATA/MailProcessor/tools/universal_mail_cleaner"
    }
  ],
  "notes": [
    "Snapshot enthält keine Maildaten und keine Zugangsdaten."
  ]
}
```

## Validierungsregeln

- `schema` muss exakt `mailprocessor-suite-v1` sein.
- `tools` ist eine Liste bekannter Tool-Objekte.
- `id` ist einer der bekannten Tool-IDs aus `tool_manager.TOOL_DEFINITIONS`.
- `enabled` ist ein boolescher Wert.
- `status` ist `available`, `missing`, `not_configured` oder `unknown`.
- `path_hint` ist optional und darf keine vollständigen privaten Windows-Pfade enthalten.

## Nicht-Ziele

- Import in den Desktop als Ersatz für die lokale Konfiguration.
- Direkte Synchronisierung zwischen Geräten.
- Transport von Zugangsdaten oder Maildaten.
- Starten von Desktop-Prozessen aus Web, Android oder iOS.
