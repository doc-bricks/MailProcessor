# macOS-/Linux-Source-Smoke

Stand: 2026-08-26

## Ziel

Dieser Smoke definiert den kleinsten sinnvollen Quellstart-Vertrag für macOS
und Linux. Er prüft keine native Endnutzerdistribution, sondern nur die
plattformnahen Kernpfade, die ohne Windows-Tray, Registry-Autostart oder
Store-Verpackung tragfähig sein müssen.

## Geprüfter Scope

- `config.app_data_dir()` fällt ohne gültiges `LOCALAPPDATA` auf
  `Path.home()/MailProcessor` zurück.
- `config.save()` und `config.load()` funktionieren mit einer temporären
  Konfigurationsdatei und manuellen Tool-Pfaden.
- `ToolManager.scan()` findet die drei unterstützten Universal-Mail-Tools
  in einer temporären Suite-Struktur über die bekannten Ordner- und
  Skriptnamen.
- `ToolManager.register_from_script_path()` akzeptiert manuelle Tool-Pfade.
- `ToolManager.launch()` setzt `PYTHONIOENCODING=utf-8` und nutzt den
  Skriptordner als Arbeitsverzeichnis; der Smoke mockt `subprocess.Popen`,
  startet also kein echtes Tool.

## Nicht-Ziele

- kein echter System-Tray-Smoke auf macOS oder Linux
- kein Autostart-/Login-Item-Test
- kein GitHub-Release-Download und kein Netzwerkzugriff
- kein Start der drei Zieltools mit echten Maildaten
- keine Prüfung von Windows Store, MSIX, WACK oder FullTrust

## Ausführung

```powershell
$env:PYTHONIOENCODING = "utf-8"
python tests\source_platform_smoke.py
python -m pytest -q tests\test_source_platform_smoke_contract.py
```

Erwartung: Beide Befehle sind grün. Der Smoke schreibt ausschließlich in ein
temporäres Verzeichnis und bereinigt dieses nach dem Lauf automatisch.

