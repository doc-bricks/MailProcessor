# Sicherer Lauf von `update_files.py`

`update_files.py` ist der wartbare, portable Nachfolger des historischen
Einmal-Skripts. Es kennt ausschließlich diese vier vorgesehenen Dateien:

- `build_exe.bat`
- `tray.py`
- `settings_dialog.py`
- `main.py`

Der Standardlauf ist immer eine schreibfreie Vorschau aus dem Projektordner:

```powershell
python update_files.py
```

Er löst den Projektbezug über den Ordner der Skriptdatei auf, liest zuerst alle
vier Ziele und gibt je Datei `would update` oder `already current` aus. Ein
fehlendes Ziel, ein unlesbares Ziel oder ein unbekannter historischer Marker
bricht verständlich ab; es wird keine Änderung geraten.

Nach der Prüfung darf die historische Wartung nur ausdrücklich ausgeführt
werden:

```powershell
python update_files.py --apply
```

`--project-dir` ist nur für den absoluten Pfad exakt dieses Projektordners
zulässig. Relative oder fremde Pfade werden abgewiesen. Für Tests wird die
Projektgrenze isoliert im Fixture nachgebildet; der produktive OneDrive-Baum
wird nicht von automatisierten Tests beschrieben.
