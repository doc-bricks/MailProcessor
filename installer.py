"""First-run installer wizard."""

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QCheckBox, QPushButton, QFileDialog,
    QLineEdit, QGroupBox, QScrollArea, QWidget, QSizePolicy,
    QProgressDialog,
)

import config as cfg_module
from config import AppConfig
from i18n import tr, set_language, get_language
from tool_manager import ToolManager, TOOL_DEFINITIONS


class _DownloadThread(QThread):
    """Background thread for GitHub downloads to keep the GUI responsive."""

    progress = Signal(int)          # 0-100
    finished_signal = Signal(str)   # empty = success, else error message

    def __init__(self, tm: ToolManager, tool_id: str, parent=None):
        super().__init__(parent)
        self._tm = tm
        self._tool_id = tool_id

    def run(self):
        err = self._tm.download_tool(self._tool_id, self.progress.emit)
        self.finished_signal.emit(err or "")


class WelcomePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)

    def _rebuild(self):
        self.setTitle(tr("page_welcome_title"))
        self.setSubTitle(tr("page_welcome_sub"))
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        text = QLabel(tr("page_welcome_text"))
        text.setWordWrap(True)
        layout.addWidget(text)

        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel(tr("page_language_label")))
        self._lang_box = QComboBox()
        self._lang_box.addItem(tr("lang_de"), "de")
        self._lang_box.addItem(tr("lang_en"), "en")
        idx = 0 if get_language() == "de" else 1
        self._lang_box.setCurrentIndex(idx)
        self._lang_box.currentIndexChanged.connect(self._on_lang_changed)
        lang_row.addWidget(self._lang_box)
        lang_row.addStretch()
        layout.addLayout(lang_row)
        layout.addStretch()

    def initializePage(self):
        # Clear and rebuild on every visit (language may have changed)
        while self.layout() and self.layout().count():
            item = self.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._rebuild()

    def _on_lang_changed(self, idx):
        lang = self._lang_box.itemData(idx)
        set_language(lang)
        # Trigger parent wizard retranslation
        wiz = self.wizard()
        if wiz:
            wiz.retranslate()


class ToolsPage(QWizardPage):
    """Scan results + tool selection checkboxes with optional GitHub download."""

    def __init__(self, tm: ToolManager, parent=None):
        super().__init__(parent)
        self._tm = tm
        self._checkboxes: dict[str, QCheckBox] = {}
        self._scan_results: dict = {}
        self._threads: list[_DownloadThread] = []  # prevent GC while running
        self._active_downloads = 0

    def isComplete(self) -> bool:
        return self._active_downloads == 0

    def _set_download_active(self, active: bool) -> None:
        previous_complete = self.isComplete()
        if active:
            self._active_downloads += 1
        else:
            self._active_downloads = max(0, self._active_downloads - 1)
        if self.isComplete() != previous_complete:
            self.completeChanged.emit()

    def initializePage(self):
        self._run_scan()
        self._rebuild_ui()

    def _run_scan(self):
        self._scan_results = self._tm.scan()

    def _rebuild_ui(self):
        previous_selection = self.selected_tools()

        # Clear existing widgets
        old = self.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            QWidget().setLayout(old)

        self.setTitle(tr("page_tools_title"))
        self.setSubTitle(tr("page_tools_sub"))

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        scan_btn = QPushButton(tr("page_tools_scan_btn"))
        scan_btn.clicked.connect(self._on_rescan)
        layout.addWidget(scan_btn)

        self._checkboxes = {}
        for tid, meta in TOOL_DEFINITIONS.items():
            found = self._scan_results.get(tid)
            cb = QCheckBox(self._tm.tool_display_name(tid))
            cb.setChecked(previous_selection.get(tid, bool(found)))
            cb.setToolTip(self._tm.tool_description(tid))

            status_label = QLabel()
            if found:
                status_label.setText(f"  ✓ {tr('detected_at')} {found[0]}")
                status_label.setStyleSheet("color: green; font-size: 11px;")
            else:
                status_label.setText(f"  {tr('not_detected')}")
                status_label.setStyleSheet("color: gray; font-size: 11px;")

            row = QVBoxLayout()
            row.setSpacing(2)

            header = QHBoxLayout()
            header.addWidget(cb)

            # Show download button when not found locally but GitHub repo is known
            if not found and meta.get("github_repo"):
                dl_btn = QPushButton(tr("btn_download"))
                dl_btn.setFixedWidth(160)
                dl_btn.setToolTip(meta["github_repo"])
                dl_btn.clicked.connect(
                    lambda _=False, t=tid, lbl=status_label, btn=dl_btn, c=cb:
                        self._start_download(t, lbl, btn, c)
                )
                header.addWidget(dl_btn)

            header.addStretch()
            row.addLayout(header)
            row.addWidget(status_label)

            box = QGroupBox()
            box.setLayout(row)
            layout.addWidget(box)
            self._checkboxes[tid] = cb

        layout.addStretch()

    def _start_download(self, tool_id: str, status_label: QLabel,
                        dl_btn: QPushButton, cb: QCheckBox) -> None:
        dl_btn.setEnabled(False)
        status_label.setText(f"  {tr('downloading')}")
        status_label.setStyleSheet("color: blue; font-size: 11px;")

        thread = _DownloadThread(self._tm, tool_id, self)
        self._threads.append(thread)
        self._set_download_active(True)

        def _on_progress(pct: int) -> None:
            status_label.setText(f"  {tr('download_pct', pct)}")

        def _on_done(err: str) -> None:
            if err:
                status_label.setText(f"  ✗ {tr('download_error', err)}")
                status_label.setStyleSheet("color: red; font-size: 11px;")
                dl_btn.setEnabled(True)
            else:
                status_label.setText(f"  ✓ {tr('download_ok')}")
                status_label.setStyleSheet("color: green; font-size: 11px;")
                cb.setChecked(True)
                # Update scan result so _on_finish can register the tool
                t = self._tm.cfg.tools.get(tool_id)
                if t and t.path and t.main_script:
                    self._scan_results[tool_id] = (t.path, t.main_script)

        thread.progress.connect(_on_progress)
        thread.finished_signal.connect(_on_done)
        thread.finished_signal.connect(lambda _err, t=thread: self._finalize_download_thread(t))
        try:
            thread.start()
        except Exception:
            self._finalize_download_thread(thread)
            raise

    def _finalize_download_thread(self, thread: _DownloadThread) -> None:
        if thread in self._threads:
            self._threads.remove(thread)
        self._set_download_active(False)

    def _on_rescan(self):
        self._run_scan()
        self._rebuild_ui()

    def selected_tools(self) -> dict[str, bool]:
        return {tid: cb.isChecked() for tid, cb in self._checkboxes.items()}


class PathsPage(QWizardPage):
    """Manual path entry for tools that weren't auto-detected."""

    def __init__(self, tools_page: ToolsPage, tm: ToolManager, parent=None):
        super().__init__(parent)
        self._tools_page = tools_page
        self._tm = tm
        self._path_edits: dict[str, QLineEdit] = {}

    def initializePage(self):
        self.setTitle(tr("page_paths_title"))
        self.setSubTitle(tr("page_paths_sub"))

        old = self.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            QWidget().setLayout(old)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        hint = QLabel(tr("page_paths_hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(hint)

        selected = self._tools_page.selected_tools()
        scan = self._tools_page._scan_results
        self._path_edits = {}

        has_manual = False
        for tid, checked in selected.items():
            if not checked or scan.get(tid):
                continue
            has_manual = True
            name = self._tm.tool_display_name(tid)
            row_lbl = QLabel(f"<b>{name}</b>")
            edit = QLineEdit()
            edit.setPlaceholderText(tr("page_paths_hint"))
            browse_btn = QPushButton(tr("browse"))
            browse_btn.setFixedWidth(120)

            def _make_browse(e=edit, t=tid):
                def _browse():
                    path, _ = QFileDialog.getOpenFileName(
                        self, tr("select_script"), "",
                        "Python Scripts (*.py)"
                    )
                    if path:
                        e.setText(path)
                return _browse

            browse_btn.clicked.connect(_make_browse())
            edit.textChanged.connect(lambda *_: self.completeChanged.emit())
            row = QHBoxLayout()
            row.addWidget(edit)
            row.addWidget(browse_btn)

            box = QGroupBox()
            vl = QVBoxLayout(box)
            vl.addWidget(row_lbl)
            vl.addLayout(row)
            layout.addWidget(box)
            self._path_edits[tid] = edit

        if not has_manual:
            lbl = QLabel("✓  " + tr("page_tools_found") + " " + ", ".join(
                self._tm.tool_display_name(t) for t, c in selected.items() if c
            ))
            lbl.setWordWrap(True)
            layout.addWidget(lbl)

        layout.addStretch()
        self.completeChanged.emit()

    def isComplete(self) -> bool:
        selected = self._tools_page.selected_tools()
        scan = self._tools_page._scan_results
        for tid, checked in selected.items():
            if not checked or scan.get(tid):
                continue
            edit = self._path_edits.get(tid)
            if not edit:
                return False
            path = edit.text().strip()
            if not path or not Path(path).exists():
                return False
        return True

    def manual_paths(self) -> dict[str, str]:
        return {tid: edit.text().strip() for tid, edit in self._path_edits.items()}


class DonePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFinalPage(True)

    def initializePage(self):
        self.setTitle(tr("page_done_title"))
        self.setSubTitle(tr("page_done_sub"))
        old = self.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            QWidget().setLayout(old)
        layout = QVBoxLayout(self)
        lbl = QLabel(tr("page_done_text"))
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
        layout.addStretch()


class InstallerWizard(QWizard):
    def __init__(self, app_cfg: AppConfig, parent=None):
        super().__init__(parent)
        self._cfg = app_cfg
        self._tm = ToolManager(app_cfg)

        self.setWindowTitle(tr("wizard_title"))
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.resize(580, 460)

        self._welcome = WelcomePage(self)
        self._tools = ToolsPage(self._tm, self)
        self._paths = PathsPage(self._tools, self._tm, self)
        self._done = DonePage(self)

        self.addPage(self._welcome)
        self.addPage(self._tools)
        self.addPage(self._paths)
        self.addPage(self._done)

        self.accepted.connect(self._on_finish)

    def retranslate(self):
        self.setWindowTitle(tr("wizard_title"))
        self.currentPage().initializePage()

    def _on_finish(self):
        selected = self._tools.selected_tools()
        scan = self._tools._scan_results
        manual = self._paths.manual_paths()

        for tid, checked in selected.items():
            if not checked:
                continue
            found = scan.get(tid)
            if found:
                self._tm.register(tid, found[0], found[1], "installer")
            elif tid in manual and manual[tid]:
                self._tm.register_from_script_path(tid, manual[tid], "manual")

        self._cfg.first_run = False
        self._cfg.language = get_language()
        cfg_module.save(self._cfg)
