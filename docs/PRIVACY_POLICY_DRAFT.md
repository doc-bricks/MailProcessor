# MailProcessor Privacy Notice — review draft

**Source basis:** MailProcessor 0.1.0, reviewed at commit b5be8f20c5ec6fb519c40c4892b47f15e08c9be8 (2026-10-03).

**Review status:** This draft describes behavior found in the reviewed MailProcessor source. The repository does not identify a privacy-request contact or the legal publishing/operator entity. Those details need confirmation by the project owner before this text is published or submitted to the Microsoft Store. This is not a claim of legal compliance.

## Scope

MailProcessor is a Windows desktop tray launcher for Universal Mail Cleaner, Universal Docs Grabber, and Universal Invoice Mail. This notice covers the MailProcessor launcher only. The three separate tools are started as child processes and may access mail accounts, messages, attachments, or other services under their own behavior. Review the privacy information for each tool as well.

## Information stored on this device

MailProcessor reads and writes a JSON configuration file at %LOCALAPPDATA%\MailProcessor\config.json. If LOCALAPPDATA is missing or not an absolute path, the source falls back to a MailProcessor directory under the current user home directory.

The configuration can contain the selected language, first-run state, the start-with-Windows setting, and for each configured tool its identifier, enabled state, folder path, entry-script filename, and installation source. Folder paths can reveal local directory names.

The configuration is a UTF-8 JSON file. The reviewed source does not encrypt it; access to the file is subject to the operating system's file permissions.

Downloaded tool release ZIP files and their extracted files are stored under %LOCALAPPDATA%\MailProcessor\tools (or the same home-directory fallback). The launcher has no scheduled cleanup for its configuration or downloaded ZIP files. Removing a tool registration in Settings does not delete that tool's files. A later download replaces the extracted folder for that tool.

If start with Windows is enabled, MailProcessor maintains a per-user entry named MailProcessor under HKCU\Software\Microsoft\Windows\CurrentVersion\Run. Disabling the setting asks Windows to remove that entry. The preference is also stored in the configuration file.

## Network connections

When a user starts a tool download in the setup wizard, MailProcessor requests the latest-release metadata from the configured public GitHub repository and downloads the release archive URL returned by GitHub. The supported repositories are doc-bricks/UniversalMailCleaner, doc-bricks/UniversalDocsGrabber, and doc-bricks/UniversalInvoiceMail. The requests use the User-Agent MailProcessor/1.0 and do not add an application access token. GitHub and any server used for the archive URL may receive ordinary connection data such as the IP address and request time; GitHub describes its handling in the [GitHub General Privacy Statement](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement).

The reviewed MailProcessor source contains no telemetry, analytics, or account-sync implementation. This statement covers the launcher source only, not the separate child applications or third-party services they may use.

## Separate tools

When the user launches a configured tool, MailProcessor starts its selected script as a separate process and passes the current process environment to it. The launcher itself does not implement mailbox reading or attachment processing. The selected tool can have its own account settings, local files, and network connections; this notice does not describe or control those operations.

## Optional snapshot export

The user can choose Export Snapshot from the tray menu and select where to save a JSON file. The export contains the export time, MailProcessor name/version/platform, and each supported tool's identifier, display name, enabled state, installation source, detected version, availability status, and an optional path hint.

The exporter replaces absolute path roots under LOCALAPPDATA or the home directory with labels. For other paths it can retain the last one or two directory names, so a path hint may still reveal identifying folder names. MailProcessor writes the file to the location selected by the user and does not upload it. Review the file before sharing it; a cloud-synced destination or later sharing is controlled by the user and that service.

## Choices and removal

Tool downloads are optional. Users can change or unregister tools in Settings and can turn off start with Windows there. Before removing the configuration, turn off start with Windows in Settings and save so the per-user startup entry is removed. The configuration file can also be read directly as UTF-8 JSON; the launcher has no account portal or server-side copy of this configuration. Then close MailProcessor and remove its MailProcessor configuration and tools directory from the applicable user data location to remove the launcher configuration and downloaded copies. This does not remove separately installed tools or their data.

## Privacy contact

The reviewed source and public project metadata do not specify a verified contact for privacy requests or identify the legal operator of MailProcessor. Do not post personal information in a public issue. The project owner must provide a private, verified privacy-contact route before this draft is published as a final policy.

---

## Deutsch

### Datenschutzhinweise für MailProcessor — Prüfentwurf

**Quellgrundlage:** MailProcessor 0.1.0, geprüft auf Commit b5be8f20c5ec6fb519c40c4892b47f15e08c9be8 (2026-10-03).

**Prüfstatus:** Dieser Entwurf beschreibt Verhalten, das im geprüften MailProcessor-Quellstand gefunden wurde. Das Repository benennt weder eine Ansprechstelle für Datenschutzanfragen noch eine rechtlich verantwortliche Veröffentlichungs- oder Betreiberstelle. Diese Angaben muss die Projektverantwortung vor einer Veröffentlichung oder Store-Einreichung bestätigen. Dies ist keine Zusicherung rechtlicher Konformität.

### Geltungsbereich

MailProcessor ist ein Windows-Desktopprogramm im Infobereich der Taskleiste und startet Universal Mail Cleaner, Universal Docs Grabber und Universal Invoice Mail. Diese Hinweise gelten nur für den MailProcessor-Launcher. Die drei separaten Werkzeuge werden als eigene Prozesse gestartet und können nach ihrem jeweiligen Verhalten auf E-Mail-Konten, Nachrichten, Anhänge oder weitere Dienste zugreifen. Bitte prüfe auch die Datenschutzhinweise der jeweiligen Werkzeuge.

### Auf diesem Gerät gespeicherte Informationen

MailProcessor liest und schreibt eine JSON-Konfigurationsdatei unter %LOCALAPPDATA%\MailProcessor\config.json. Wenn LOCALAPPDATA fehlt oder kein absoluter Pfad ist, verwendet der Quellstand stattdessen ein MailProcessor-Verzeichnis im Home-Verzeichnis des aktuellen Benutzers.

Die Konfiguration kann die ausgewählte Sprache, den Ersteinrichtungsstatus, die Einstellung für den Windows-Start sowie für jedes eingerichtete Werkzeug dessen Kennung, Aktivierungsstatus, Verzeichnispfad, Dateinamen des Einstiegsskripts und Installationsherkunft enthalten. Verzeichnispfade können lokale Ordnernamen erkennen lassen.

Die Konfiguration ist eine UTF-8-JSON-Datei. Der geprüfte Quellstand verschlüsselt sie nicht; der Zugriff richtet sich nach den Dateiberechtigungen des Betriebssystems.

Heruntergeladene Release-ZIP-Dateien der Werkzeuge und deren entpackte Dateien liegen unter %LOCALAPPDATA%\MailProcessor\tools oder im entsprechenden Fallback-Verzeichnis im Home-Verzeichnis. Der Launcher hat keine zeitgesteuerte Bereinigung für Konfiguration oder heruntergeladene ZIP-Dateien. Wenn ein Werkzeug in den Einstellungen abgemeldet wird, löscht das seine Dateien nicht. Ein späterer Download ersetzt das entpackte Verzeichnis dieses Werkzeugs.

Wenn Windows-Start aktiviert ist, verwaltet MailProcessor im aktuellen Benutzerkontext einen Eintrag namens MailProcessor unter HKCU\Software\Microsoft\Windows\CurrentVersion\Run. Beim Deaktivieren der Einstellung versucht das Programm, diesen Eintrag zu entfernen. Die Einstellung steht außerdem in der Konfigurationsdatei.

### Netzwerkverbindungen

Wenn ein Benutzer im Einrichtungsassistenten einen Werkzeug-Download startet, fragt MailProcessor die Metadaten des neuesten Releases beim festgelegten öffentlichen GitHub-Repository ab und lädt anschließend die von GitHub gelieferte Release-Archivadresse herunter. Unterstützt werden die Repositories doc-bricks/UniversalMailCleaner, doc-bricks/UniversalDocsGrabber und doc-bricks/UniversalInvoiceMail. Die Anfragen verwenden den User-Agent MailProcessor/1.0 und fügen kein Anwendungszugangstoken hinzu. GitHub und ein Server, der für die Archivadresse verwendet wird, können übliche Verbindungsdaten wie IP-Adresse und Anfragezeit erhalten. GitHub beschreibt seine Verarbeitung in der [allgemeinen GitHub-Datenschutzerklärung](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement).

Im geprüften MailProcessor-Quellstand wurde keine Implementierung für Telemetrie, Analyse oder Kontosynchronisierung gefunden. Diese Aussage betrifft nur den Launcher und nicht die separat gestarteten Anwendungen oder von ihnen genutzten Drittanbieterdienste.

### Separate Werkzeuge

Wenn der Benutzer ein eingerichtetes Werkzeug startet, führt MailProcessor dessen ausgewähltes Skript als eigenen Prozess aus und übergibt ihm die aktuelle Prozessumgebung. Der Launcher selbst implementiert weder das Lesen von Postfächern noch die Verarbeitung von Anhängen. Das gestartete Werkzeug kann eigene Kontoeinstellungen, lokale Dateien und Netzwerkverbindungen haben. Diese Hinweise beschreiben oder steuern diese Vorgänge nicht.

### Optionaler Snapshot-Export

Über den Menüpunkt „Snapshot exportieren“ kann der Benutzer einen Speicherort wählen und eine JSON-Datei schreiben. Der Export enthält Exportzeitpunkt, MailProcessor-Name, Version und Plattform sowie für jedes unterstützte Werkzeug Kennung, Anzeigename, Aktivierungsstatus, Installationsherkunft, erkannte Version, Verfügbarkeitsstatus und gegebenenfalls einen Pfadhinweis.

Der Export ersetzt absolute Pfadwurzeln unter LOCALAPPDATA oder im Home-Verzeichnis durch Bezeichnungen. Bei anderen Pfaden kann er die letzten ein oder zwei Ordnernamen behalten. Ein Pfadhinweis kann deshalb weiterhin identifizierende Ordnernamen offenbaren. MailProcessor schreibt die Datei an den ausgewählten Speicherort und lädt sie nicht selbst hoch. Bitte prüfe die Datei vor dem Teilen. Eine Cloud-Synchronisierung des ausgewählten Zielordners oder eine spätere Weitergabe wird durch den Benutzer oder den jeweiligen Dienst gesteuert.

### Auswahl und Entfernen

Werkzeug-Downloads sind optional. Benutzer können Werkzeuge in den Einstellungen ändern oder abmelden und dort auch den Windows-Start deaktivieren. Die Konfigurationsdatei lässt sich außerdem direkt als UTF-8-JSON lesen. Der Launcher hat kein Benutzerkonto-Portal und keine serverseitige Kopie dieser Konfiguration.

Vor dem Entfernen der Konfiguration sollte der Benutzer in den Einstellungen den Windows-Start deaktivieren und speichern, damit der Autostarteintrag für den aktuellen Benutzer entfernt wird. Anschließend kann MailProcessor geschlossen und die MailProcessor-Konfiguration samt Werkzeugverzeichnis am zutreffenden Benutzerdatenort entfernt werden. Dadurch werden Launcher-Konfiguration und heruntergeladene Kopien entfernt, jedoch keine separat installierten Werkzeuge oder deren Daten.

### Kontakt für Datenschutzanfragen

Der geprüfte Quellstand und die öffentlichen Projektmetadaten nennen keinen bestätigten Kontakt für Datenschutzanfragen und keine rechtliche Betreiberstelle von MailProcessor. Bitte veröffentliche personenbezogene Informationen nicht in öffentlichen Issues. Die Projektverantwortung muss vor der Veröffentlichung dieses Entwurfs als endgültige Datenschutzerklärung einen privaten, bestätigten Kontaktweg angeben.