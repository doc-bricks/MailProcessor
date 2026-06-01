"""MailProcessor – entry point."""

import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

import config as cfg_module
from i18n import set_language


def main():
    # High-DPI
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("MailProcessor")
    app.setOrganizationName("lukisch")

    cfg = cfg_module.load()
    set_language(cfg.language)

    if cfg.first_run:
        from installer import InstallerWizard
        wizard = InstallerWizard(cfg)
        result = wizard.exec()
        if result != InstallerWizard.DialogCode.Accepted:
            sys.exit(0)
        # Reload config (wizard saved it)
        cfg = cfg_module.load()
        set_language(cfg.language)

    from settings_dialog import ensure_autostart_entry
    ensure_autostart_entry(cfg.start_with_windows)

    from tray import MailProcessorTray
    tray = MailProcessorTray(cfg)
    if not tray.isSystemTrayAvailable():
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "MailProcessor",
                             "System Tray ist auf diesem System nicht verfügbar.")
        sys.exit(1)

    tray.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
