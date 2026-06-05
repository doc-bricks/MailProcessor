"""Translations DE/EN for MailProcessor."""

_STRINGS: dict[str, dict[str, str]] = {
    # General
    "app_name":              {"de": "MailProcessor",                        "en": "MailProcessor"},
    "tray_tooltip":          {"de": "MailProcessor – Mail-Tools Launcher",  "en": "MailProcessor – Mail Tools Launcher"},
    "menu_settings":         {"de": "Einstellungen",                        "en": "Settings"},
    "menu_export_snapshot":  {"de": "Arbeitsstand exportieren …",           "en": "Export snapshot…"},
    "menu_quit":             {"de": "Beenden",                              "en": "Quit"},
    "no_tools":              {"de": "Keine Tools konfiguriert",             "en": "No tools configured"},
    "start_tool":            {"de": "Starten",                              "en": "Start"},
    "ok":                    {"de": "OK",                                   "en": "OK"},
    "cancel":                {"de": "Abbrechen",                            "en": "Cancel"},
    "save":                  {"de": "Speichern",                            "en": "Save"},
    "browse":                {"de": "Durchsuchen …",                        "en": "Browse …"},
    "error":                 {"de": "Fehler",                               "en": "Error"},
    "warning":               {"de": "Hinweis",                              "en": "Warning"},

    # Tool names / descriptions
    "tool_umc_name":         {"de": "Universal Mail Cleaner",               "en": "Universal Mail Cleaner"},
    "tool_umc_desc":         {"de": "IMAP-Postfach nach Regeln bereinigen", "en": "Clean IMAP mailbox by rules"},
    "tool_udg_name":         {"de": "Universal Docs Grabber",               "en": "Universal Docs Grabber"},
    "tool_udg_desc":         {"de": "Dokumente und Anhänge aus Mails laden","en": "Download documents and attachments from mails"},
    "tool_uim_name":         {"de": "Universal Invoice Mail",               "en": "Universal Invoice Mail"},
    "tool_uim_desc":         {"de": "Rechnungen automatisch aus Mails extrahieren","en": "Extract invoices automatically from mails"},

    # Installer wizard
    "wizard_title":          {"de": "MailProcessor – Einrichtung",          "en": "MailProcessor – Setup"},
    "page_welcome_title":    {"de": "Willkommen",                           "en": "Welcome"},
    "page_welcome_sub":      {"de": "Richte MailProcessor ein",             "en": "Set up MailProcessor"},
    "page_welcome_text":     {"de": "MailProcessor startet als System-Tray-Icon und ermöglicht den schnellen Start der Mail-Tools per Rechtsklick.\n\nWähle im nächsten Schritt, welche Tools du einrichten möchtest.",
                              "en": "MailProcessor runs as a system tray icon and lets you launch Mail Tools quickly via right-click.\n\nIn the next step, choose which tools you want to set up."},
    "page_language_label":   {"de": "Sprache / Language:",                  "en": "Sprache / Language:"},
    "page_tools_title":      {"de": "Tools auswählen",                      "en": "Select Tools"},
    "page_tools_sub":        {"de": "Gefundene und verfügbare Tools",       "en": "Detected and available tools"},
    "page_tools_found":      {"de": "Automatisch gefunden:",                "en": "Automatically detected:"},
    "page_tools_scan_btn":   {"de": "Erneut scannen",                       "en": "Scan again"},
    "page_paths_title":      {"de": "Pfade konfigurieren",                  "en": "Configure paths"},
    "page_paths_sub":        {"de": "Pfad zu nicht gefundenen Tools angeben","en": "Specify path to undetected tools"},
    "page_paths_hint":       {"de": "Leer lassen = Tool nicht einrichten",  "en": "Leave empty = skip this tool"},
    "page_done_title":       {"de": "Fertig",                               "en": "Done"},
    "page_done_sub":         {"de": "MailProcessor ist eingerichtet",       "en": "MailProcessor is set up"},
    "page_done_text":        {"de": "MailProcessor läuft jetzt im System-Tray.\nRechtsklick auf das Symbol zum Starten der Tools.",
                              "en": "MailProcessor is now running in the system tray.\nRight-click the icon to launch tools."},
    "not_detected":          {"de": "Nicht gefunden – Pfad manuell eingeben","en": "Not detected – enter path manually"},
    "detected_at":           {"de": "Gefunden:",                            "en": "Detected at:"},

    # Settings dialog
    "settings_title":        {"de": "MailProcessor – Einstellungen",        "en": "MailProcessor – Settings"},
    "tab_tools":             {"de": "Tools",                                "en": "Tools"},
    "tab_general":           {"de": "Allgemein",                            "en": "General"},
    "col_tool":              {"de": "Tool",                                 "en": "Tool"},
    "col_status":            {"de": "Status",                               "en": "Status"},
    "col_path":              {"de": "Pfad",                                 "en": "Path"},
    "status_active":         {"de": "Aktiv",                                "en": "Active"},
    "status_inactive":       {"de": "Inaktiv",                              "en": "Inactive"},
    "status_missing":        {"de": "Pfad fehlt",                           "en": "Path missing"},
    "btn_change_path":       {"de": "Pfad ändern",                          "en": "Change path"},
    "btn_remove_tool":       {"de": "Entfernen",                            "en": "Remove"},
    "btn_add_tool":          {"de": "Manuell hinzufügen",                   "en": "Add manually"},
    "btn_rescan":            {"de": "Erneut scannen",                       "en": "Scan again"},
    "label_language":        {"de": "Sprache:",                             "en": "Language:"},
    "label_autostart":       {"de": "Mit Windows starten",                  "en": "Start with Windows"},
    "autostart_note":        {"de": "(Startet MailProcessor beim Windows-Login automatisch)",
                              "en": "(Launches MailProcessor automatically on Windows login)"},
    "rescan_done":           {"de": "Scan abgeschlossen. Gefundene Tools wurden hinzugefügt.", "en": "Scan complete. Detected tools have been added."},
    "rescan_none":           {"de": "Scan abgeschlossen. Keine neuen Tools gefunden.", "en": "Scan complete. No new tools found."},
    "remove_confirm":        {"de": "Tool aus MailProcessor entfernen? Die Tool-Dateien werden NICHT gelöscht.",
                              "en": "Remove tool from MailProcessor? The tool files will NOT be deleted."},
    "path_not_found":        {"de": "Kein gültiges Skript an diesem Pfad gefunden.",
                              "en": "No valid script found at this path."},
    "select_script":         {"de": "Python-Skript auswählen",              "en": "Select Python script"},
    "launch_error":          {"de": "Tool konnte nicht gestartet werden:\n{}", "en": "Could not launch tool:\n{}"},
    "lang_de":               {"de": "Deutsch",                              "en": "German"},
    "lang_en":               {"de": "Englisch",                             "en": "English"},

    # Download / GitHub installer
    "btn_download":          {"de": "Von GitHub laden",                    "en": "Download from GitHub"},
    "downloading":           {"de": "Wird heruntergeladen …",              "en": "Downloading …"},
    "download_pct":          {"de": "Herunterladen … {}%",                 "en": "Downloading … {}%"},
    "download_ok":           {"de": "Heruntergeladen. Fertig.",            "en": "Downloaded successfully."},
    "download_error":        {"de": "Download fehlgeschlagen:\n{}",        "en": "Download failed:\n{}"},
    "download_title":        {"de": "Download läuft",                      "en": "Downloading"},
    "download_cancel":       {"de": "Abbrechen",                           "en": "Cancel"},
    "export_dialog_title":   {"de": "Arbeitsstand exportieren",            "en": "Export snapshot"},
    "export_file_filter":    {"de": "JSON-Dateien (*.json)",               "en": "JSON files (*.json)"},
    "export_ok":             {"de": "Arbeitsstand exportiert:\n{}",        "en": "Snapshot exported:\n{}"},
    "export_error":          {"de": "Export fehlgeschlagen:\n{}",          "en": "Export failed:\n{}"},
}

_lang: str = "de"


def set_language(lang: str) -> None:
    global _lang
    _lang = lang if lang in ("de", "en") else "de"


def get_language() -> str:
    return _lang


def tr(key: str, *args) -> str:
    entry = _STRINGS.get(key, {})
    text = entry.get(_lang) or entry.get("en") or key
    if args:
        text = text.format(*args)
    return text
