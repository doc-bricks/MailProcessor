"""Add parent directory to sys.path for imports."""
import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def qapp():
    """Keep one Qt application alive and dispose test-owned Qt UI before shutdown."""
    from PySide6.QtCore import QCoreApplication, QEvent
    from PySide6.QtWidgets import QApplication, QSystemTrayIcon

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    assert isinstance(app, QApplication)

    yield app

    tray_icons = tuple(app.findChildren(QSystemTrayIcon))
    widgets = list(app.topLevelWidgets())
    for icon in tray_icons:
        menu = icon.contextMenu()
        if menu is not None and menu not in widgets:
            widgets.append(menu)
        icon.hide()
        icon.setContextMenu(None)

    for widget in widgets:
        widget.close()
        widget.deleteLater()
    for icon in tray_icons:
        icon.deleteLater()

    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    assert not app.topLevelWidgets(), "Qt top-level widgets remained after session cleanup"
    assert not app.findChildren(QSystemTrayIcon), "Qt tray icons remained after session cleanup"
