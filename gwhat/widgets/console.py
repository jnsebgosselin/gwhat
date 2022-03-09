# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
#
# Copyright © 2022 SARDES Project Contributors
# https://github.com/cgq-qgc/sardes
#
# Some parts of this file is a derivative work of the Sardes project that is
# licensed under the terms of the MIT License.
# -----------------------------------------------------------------------------

# ---- Standard library imports
import sys
import os.path as osp
import datetime

# ---- Third party imports
from qtpy.QtCore import Qt
from qtpy.QtGui import QTextCursor
from qtpy.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QGridLayout, QPushButton,
    QTextBrowser, QFileDialog, QMessageBox)

# ---- Local imports
from gwhat.utils.icons import get_icon
from gwhat.config.ospath import (
    get_select_file_dialog_dir, set_select_file_dialog_dir)


class StandardStreamConsole(QTextBrowser):
    """
    A Qt text edit to hold and show the standard input and output of the
    Python interpreter.
    """

    def __init__(self, textmode='plain'):
        super().__init__()
        self.setReadOnly(True)
        self.setOpenExternalLinks(True)
        self.textmode = textmode

    def write(self, text):
        self.moveCursor(QTextCursor.End)
        if self.textmode == 'plain':
            self.insertPlainText(text)
        elif self.textmode == 'rich':
            self.insertHtml(text + '<br>')


class StreamConsole(QDialog):
    """
    A console to hold, show and manage the standard input and ouput
    of the Python interpreter.
    """

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            self.windowFlags() &
            ~Qt.WindowContextHelpButtonHint |
            Qt.WindowMinMaxButtonsHint)
        self.setWindowIcon(get_icon('console'))
        self.setWindowTitle("GWHAT Console")
        self.setMinimumSize(700, 500)

        self.std_console = StandardStreamConsole(textmode='rich')

        # Setup the dialog button box.
        self.saveas_btn = QPushButton('Save As')
        self.saveas_btn.setDefault(False)
        self.saveas_btn.clicked.connect(lambda checked: self.save_as())

        self.close_btn = QPushButton('Close')
        self.close_btn.setDefault(True)
        self.close_btn.clicked.connect(self.close)

        self.copy_btn = QPushButton('Copy')
        self.copy_btn.setDefault(False)
        self.copy_btn.clicked.connect(self.copy_to_clipboard)

        button_box = QDialogButtonBox()
        button_box.addButton(self.close_btn, button_box.AcceptRole)
        button_box.addButton(self.saveas_btn, button_box.ActionRole)
        button_box.addButton(self.copy_btn, button_box.ActionRole)

        # self.setCentralWidget(self.std_console)
        layout = QGridLayout(self)
        layout.addWidget(self.std_console, 0, 0)
        layout.addWidget(button_box, 1, 0)

    def write(self, text):
        self.std_console.write(text)

    def plain_text(self):
        """
        Return the content of the console as plain text.
        """
        return self.std_console.toPlainText()

    def save_as(self, filename=None):
        """
        Save the content of the console to a text file.
        """
        if filename is None:
            now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = osp.join(
                get_select_file_dialog_dir(), f'gwhat_log_{now}.txt')
        filename, filefilter = QFileDialog.getSaveFileName(
            self, "Save File", filename, 'Text File (*.txt)')
        if filename:
            filename = osp.abspath(filename)
            set_select_file_dialog_dir(osp.dirname(filename))
            if not filename.endswith('.txt'):
                filename += '.txt'

            QApplication.setOverrideCursor(Qt.WaitCursor)
            QApplication.processEvents()
            try:
                with open(filename, 'w') as txtfile:
                    txtfile.write(self.plain_text())
            except PermissionError:
                QApplication.restoreOverrideCursor()
                QApplication.processEvents()
                QMessageBox.warning(
                    self,
                    'File in Use',
                    ("The save file operation cannot be completed because "
                     "the file is in use by another application or user."),
                    QMessageBox.Ok)
                self.save_as(filename)
            else:
                QApplication.restoreOverrideCursor()
                QApplication.processEvents()

    def copy_to_clipboard(self):
        """
        Copy the content of the console on the clipboard.
        """
        QApplication.clipboard().clear()
        QApplication.clipboard().setText(self.plain_text())

    def show(self):
        """
        Override Qt method.
        """
        if self.windowState() == Qt.WindowMinimized:
            self.setWindowState(Qt.WindowNoState)
        super().show()
        self.activateWindow()
        self.raise_()


if __name__ == '__main__':
    from gwhat.utils.qthelpers import create_qapplication
    app = create_qapplication()

    console = StreamConsole()
    console.show()

    sys.exit(app.exec_())
