# -*- coding: utf-8 -*-
"""
Copyright 2014-2017 Jean-Sebastien Gosselin
email: jean-sebastien.gosselin@ete.inrs.ca

This file is part of WHAT (Well Hydrograph Analysis Toolbox).

WHAT is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# Standard library imports :
import os

# Third party imports :
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QDialog, QApplication, QGridLayout,
                             QLabel, QPushButton, QCheckBox, QLineEdit,
                             QFileDialog)

# Local imports :

from common import IconDB, QToolButtonSmall
from meteo.weather_reader import WXDataFrame


class WXDataMerger(QDialog):

    def __init__(self, wxdset=None, parent=None):
        super(WXDataMerger, self).__init__(parent)

        self.setModal(False)
        self.setWindowFlags(Qt.CustomizeWindowHint |
                            Qt.WindowCloseButtonHint)

        self.setWindowTitle('Merge dataset')
        self.setWindowIcon(IconDB().master)
        self._workdir = os.getcwd()
        self.wxdsets = {}

        self.__initUI__()

    def __initUI__(self):

        # ---- Toolbar ----

        btn_merge = QPushButton('Merge')
        btn_merge.clicked.connect(self.btn_merge_isClicked)
        btn_cancel = QPushButton('Close')
        btn_cancel.clicked.connect(self.close)

        toolbar = QGridLayout()
        toolbar.addWidget(btn_merge, 0, 1)
        toolbar.addWidget(btn_cancel, 0, 2)
        toolbar.setColumnStretch(0, 100)
        toolbar.setContentsMargins(0, 25, 0, 0)  # (L, T, R, B)

        # ---- Central Widget ----

        btn_wxdset1 = QToolButtonSmall(IconDB().openFile)
        btn_wxdset1.line_edit = QLineEdit()
        btn_wxdset1.line_edit.setReadOnly(True)
        btn_wxdset1.label = QLabel("Select a first dataset :")
        btn_wxdset1.clicked.connect(self.btn_get_file_isClicked)

        btn_wxdset2 = QToolButtonSmall(IconDB().openFile)
        btn_wxdset2.line_edit = QLineEdit()
        btn_wxdset2.line_edit.setReadOnly(True)
        btn_wxdset2.label = QLabel("Select a second dataset :")
        btn_wxdset2.clicked.connect(self.btn_get_file_isClicked)

        lbl_wxdset3 = QLabel("Enter a name for the resulting dataset :")
        wxdset3 = QLineEdit()

        qchckbox = QCheckBox(
                "Delete both original input datafiles after merging.")
        qchckbox.setCheckState(Qt.Checked)

        central_layout = QGridLayout()
        row = 0
        for btn in [btn_wxdset1, btn_wxdset2]:
            central_layout.addWidget(btn.label, row, 0, 1, 2)
            row += 1
            central_layout.addWidget(btn.line_edit, row, 0)
            central_layout.addWidget(btn, row, 1)
            row += 1
            central_layout.setRowMinimumHeight(row, 15)
            row += 1
        central_layout.addWidget(lbl_wxdset3, row, 0, 1, 2)
        row += 1
        central_layout.addWidget(wxdset3, row, 0, 1, 2)
        row += 1
        central_layout.setRowMinimumHeight(row, 15)
        row += 1
        central_layout.addWidget(qchckbox, row, 0, 1, 2)
        central_layout.setColumnStretch(1, 100)

        # ---- Self Layout ----

        layout = QGridLayout(self)
        layout.addLayout(central_layout, 0, 0)
        layout.addLayout(toolbar, 1, 0)

    def set_workdir(self, dirname):
        if os.path.exists(dirname):
            self._workdir = dirname

    def btn_merge_isClicked(self):
        print(len(self.wxdsets))
        self.close()

    def btn_get_file_isClicked(self):
        fname, ftype = QFileDialog.getOpenFileName(
                self, 'Select a valid weather data file', self._workdir,
                '*.csv')
        if fname:
            self.sender().line_edit.setText(fname)
            self.wxdsets[self.sender()] = WXDataFrame(fname)

    def show(self):
        super(WXDataMerger, self).show()
        self.setFixedSize(self.size())


if __name__ == '__main__':                                   # pragma: no cover
    import platform
    import sys

    app = QApplication(sys.argv)

    if platform.system() == 'Windows':
        app.setFont(QFont('Segoe UI', 11))
    elif platform.system() == 'Linux':
        app.setFont(QFont('Ubuntu', 11))

    wxdata_merger = WXDataMerger()
    wxdata_merger.show()

    workdir = os.path.join("..", "tests", "@ new-prô'jèt!", "Meteo", "Input")
    wxdata_merger.set_workdir(workdir)

    sys.exit(app.exec_())
