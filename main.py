"""MailProcessor – entry point."""

import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

import config as cfg_module
from i18n import set_language, tr


def _run_bundle_self_test() -> int:
    """Exercise packaged assets and the primary Qt UI without user state."""
    from PySide6.QtCore import QEvent, QEventLoop, QObject, QTimer
    from PySide6.QtGui import QIcon
    from config import AppConfig
    from settings_dialog import SettingsDialog
    from tray import MailProcessorTray, _resource_path

    app = QApplication.instance()
    owns_app = app is None
    tray = None
    dialog = None
    menu = None
    timer = None
    result = 0

    try:
        if app is None:
            QApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )
            app = QApplication([sys.argv[0]])
        app.setQuitOnLastWindowClosed(False)
        app.setApplicationName("MailProcessor")
        app.setOrganizationName("lukisch")

        # This flag is for a frozen test bundle only. It never loads or saves
        # the real profile; all UI objects receive an empty synthetic config.
        if not getattr(sys, "frozen", False) or not hasattr(sys, "_MEIPASS"):
            result = 10
        else:
            icon_path = _resource_path("resources/icon.ico")
            if not icon_path.is_file():
                result = 11
            else:
                icon = QIcon(str(icon_path))
                if icon.isNull():
                    result = 12
                else:
                    app.setWindowIcon(icon)
                    cfg = AppConfig(
                        language="en", first_run=False, start_with_windows=False
                    )
                    set_language(cfg.language)
                    tray = MailProcessorTray(cfg)
                    menu = tray.contextMenu()
                    if tray.icon().isNull() or menu is None or len(menu.actions()) < 4:
                        result = 13
                    else:
                        dialog = SettingsDialog(cfg)
                        loop = QEventLoop()
                        timer = QTimer(dialog)
                        timer.setSingleShot(True)
                        painted = False

                        class PaintProbe(QObject):
                            def eventFilter(self, watched, event):
                                nonlocal painted
                                if watched is dialog and event.type() == QEvent.Type.Paint:
                                    painted = True
                                    loop.quit()
                                return False

                        paint_probe = PaintProbe(dialog)
                        dialog.installEventFilter(paint_probe)
                        dialog.show()
                        app.processEvents()
                        if not painted:
                            timer.timeout.connect(loop.quit)
                            timer.start(1500)
                            loop.exec()
                        timer.stop()
                        if not dialog.isVisible() or not painted:
                            result = 14
    except Exception:
        result = 15
    finally:
        if timer is not None:
            try:
                timer.stop()
            except Exception:
                if result == 0:
                    result = 16
        if dialog is not None:
            try:
                dialog.close()
            except Exception:
                if result == 0:
                    result = 16
        if menu is not None:
            try:
                menu.close()
            except Exception:
                if result == 0:
                    result = 16
        if tray is not None:
            try:
                tray.hide()
            except Exception:
                if result == 0:
                    result = 16
        if app is not None:
            try:
                app.processEvents()
            except Exception:
                if result == 0:
                    result = 16
            if owns_app:
                try:
                    app.quit()
                except Exception:
                    if result == 0:
                        result = 16

    return result


def main():
    if sys.argv[1:] == ["--self-test"]:
        return _run_bundle_self_test()

    # High-DPI
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("MailProcessor")
    app.setOrganizationName("lukisch")

    from tray import get_app_icon
    app.setWindowIcon(get_app_icon())

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
        QMessageBox.critical(None, tr("app_name"), tr("tray_unavailable"))
        sys.exit(1)

    tray.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    result = main()
    if result is not None:
        sys.exit(result)
