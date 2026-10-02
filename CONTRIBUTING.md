# Beitragsrichtlinie / Contributing Guide

## Deutsch

Vielen Dank für Ihr Interesse, zu diesem Projekt beizutragen.

### Wie Sie beitragen können

1. **Bug melden:** Erstellen Sie ein Issue mit klaren Schritten zur Reproduktion.
2. **Feature vorschlagen:** Beschreiben Sie den Nutzerwert und den betroffenen Workflow.
3. **Code beitragen:** Erstellen Sie einen Pull Request mit engem Scope.

### Lokales Setup

1. Python 3.10+ installieren
2. `pip install -r requirements-dev.txt`
3. App mit `start.bat` oder `python main.py` starten
4. Tests mit `python -m pytest -q` ausführen

### Pull Requests

1. Forken Sie das Repository
2. Erstellen Sie einen Branch mit klarer Absicht
3. Halten Sie Änderungen klein und nachvollziehbar
4. Aktualisieren Sie README/CHANGELOG, wenn Nutzerverhalten oder Releases betroffen sind
5. Prüfen Sie vor dem PR, dass keine lokalen Tool-Pfade, Tokens oder Release-Artefakte eingecheckt werden

### Code-Richtlinien

- Python: PEP 8 Stil
- Encoding: UTF-8 für alle Dateien
- Sprache: Code und Kommentare auf Deutsch oder Englisch
- Keine hardcoded Pfade, Secrets oder lokale Windows-spezifische Nutzerdaten committen

---

## English

Thank you for your interest in contributing to this project.

### How to Contribute

1. **Report bugs:** Open an issue with clear reproduction steps.
2. **Suggest features:** Describe the user value and affected workflow.
3. **Contribute code:** Open a pull request with a tight, reviewable scope.

### Local Setup

1. Install Python 3.10+
2. Run `pip install -r requirements-dev.txt`
3. Start the app with `start.bat` or `python main.py`
4. Run tests with `python -m pytest -q`

### Pull Requests

1. Fork the repository
2. Create a branch with a clear intent
3. Keep changes small and easy to review
4. Update README/CHANGELOG when user-visible behavior or releases change
5. Verify that no local tool paths, tokens, or release artifacts are committed

### Code Guidelines

- Python: PEP 8 style
- Encoding: UTF-8 for all files
- Language: Code and comments in German or English
- Do not commit hardcoded paths, secrets, or local Windows user data
