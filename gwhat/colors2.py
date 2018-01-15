# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

from __future__ import division, unicode_literals

# Standard library imports :

import os
import csv
from collections import OrderedDict

# Third party imports :

from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QPushButton, QGridLayout, QLabel,
                             QToolButton, QColorDialog, QApplication)

import numpy as np

# Local imports :

import gwhat.common.widgets as myqt
from gwhat.common.utils import save_content_to_csv


class ColorsReader(object):
    def __init__(self):
        self.RGB = OrderedDict()
        self.RGB['Tair'] = [255, 212, 212]
        self.RGB['Rain'] = [23, 52, 88]
        self.RGB['Snow'] = [165, 165, 165]
        self.RGB['WL solid'] = [45, 100, 167]
        self.RGB['WL data'] = [204, 204, 204]
        self.RGB['WL obs'] = [255, 0, 0]

        self.labels = OrderedDict()
        self.labels['Tair'] = 'Air Temperature'
        self.labels['Rain'] = 'Rain'
        self.labels['Snow'] = 'Snow'
        self.labels['WL solid'] = 'Water Level (solid line)'
        self.labels['WL data'] = 'Water Level (data dots)'
        self.labels['WL obs'] = 'Water Level (man. obs.)'

    @property
    def rgb(self):
        rgb = OrderedDict()
        for key in self.RGB.keys():
            rgb[key] = [x/255 for x in self.RGB[key]]
        return rgb

    def keys(self):
        return list(self.RGB.keys())

    def load_colors_db(self):
        """Load the color settings from Colors.db."""
        fname = 'Colors.db'
        if not os.path.exists(fname):
            self.save_colors_db()

        else:
            with open(fname, 'r') as f:
                reader = list(csv.reader(f, delimiter=','))

            for row in reader:
                self.RGB[row[0]] = [int(x) for x in row[1:]]

    def save_colors_db(self):
        """Save the color settings to Colors.db."""
        fname = 'Colors.db'
        fcontent = []
        for key in self.RGB.keys():
            fcontent.append([key])
            fcontent[-1].extend(self.RGB[key])
        save_content_to_csv(fname, fcontent)


class ColorsSetupWin(myqt.DialogWindow):

    newColorSetupSent = QSignal(bool)

    def __init__(self, parent=None):
        super(ColorsSetupWin, self).__init__(parent)

        self.setWindowTitle('Colors Palette Setup')
        self.setWindowFlags(Qt.Window)

        self.__initUI__()

    def __initUI__(self):  # ==================================================

        # ---- Toolbar ----

        toolbar_widget = QWidget()

        btn_apply = QPushButton('Apply')
        btn_apply.clicked.connect(self.btn_apply_isClicked)
        btn_cancel = QPushButton('Cancel')
        btn_cancel.clicked.connect(self.close)
        btn_OK = QPushButton('OK')
        btn_OK.clicked.connect(self.btn_OK_isClicked)
        btn_reset = QPushButton('Reset Defaults')
        btn_reset.clicked.connect(self.reset_defaults)

        toolbar_layout = QGridLayout()
        toolbar_layout.addWidget(btn_reset, 1, 0, 1, 3)
        toolbar_layout.addWidget(btn_OK, 2, 0)
        toolbar_layout.addWidget(btn_cancel, 2, 1)
        toolbar_layout.addWidget(btn_apply, 2, 2)

        toolbar_layout.setColumnStretch(3, 100)
        toolbar_layout.setRowStretch(0, 100)

        toolbar_widget.setLayout(toolbar_layout)

        # ---- Color Grid ----

        colorsDB = ColorsReader()
        colorsDB.load_colors_db()

        colorGrid_widget = QWidget()

        self.colorGrid_layout = QGridLayout()
        for i, key in enumerate(colorsDB.keys()):
            self.colorGrid_layout.addWidget(
                QLabel('%s :' % colorsDB.labels[key]), i, 0)

            btn = QToolButton()
            btn.setAutoRaise(True)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.clicked.connect(self.pick_color)

            self.colorGrid_layout.addWidget(btn, i, 3)
        self.load_colors()
        self.colorGrid_layout.setColumnStretch(2, 100)

        colorGrid_widget.setLayout(self.colorGrid_layout)

        # ---- Main Layout ----

        main_layout = QGridLayout()
        main_layout.addWidget(colorGrid_widget, 0, 0)
        main_layout.addWidget(toolbar_widget, 1, 0)
        self.setLayout(main_layout)

    # =========================================================================

    def load_colors(self):

        colorsDB = ColorsReader()
        colorsDB.load_colors_db()

        nrow = self.colorGrid_layout.rowCount()
        for row, key in enumerate(colorsDB.keys()):
            item = self.colorGrid_layout.itemAtPosition(row, 3).widget()
            item.setStyleSheet("background-color: rgb(%i,%i,%i)" %
                               (colorsDB.RGB[key][0],
                                colorsDB.RGB[key][1],
                                colorsDB.RGB[key][2])
                               )

    def reset_defaults(self):

        colorsDB = ColorsReader()

        nrow = self.colorGrid_layout.rowCount()
        for row, key in enumerate(colorsDB.keys()):
            btn = self.colorGrid_layout.itemAtPosition(row, 3).widget()
            btn.setStyleSheet("background-color: rgb(%i,%i,%i)" %
                              (colorsDB.RGB[key][0],
                               colorsDB.RGB[key][1],
                               colorsDB.RGB[key][2])
                              )

    def pick_color(self):
        sender = self.sender()
        color = QColorDialog.getColor(sender.palette().base().color())
        if color.isValid():
            rgb = color.getRgb()[:-1]
            sender.setStyleSheet("background-color: rgb(%i,%i,%i)" % rgb)

    # =========================================================================

    def btn_OK_isClicked(self):
        self.btn_apply_isClicked()
        self.close()

    def btn_apply_isClicked(self):

        colorsDB = ColorsReader()

        nrow = self.colorGrid_layout.rowCount()
        for row, key in enumerate(colorsDB.keys()):
            item = self.colorGrid_layout.itemAtPosition(row, 3).widget()
            rgb = item.palette().base().color().getRgb()[:-1]

            colorsDB.RGB[key] = np.array([rgb[0], rgb[1], rgb[2]])

        colorsDB.save_colors_db()
        self.newColorSetupSent.emit(True)

    # =========================================================================

    def closeEvent(self, event):
        super(ColorsSetupWin, self).closeEvent(event)
        self.load_colors()

        # If cancel or X is clicked, the parameters will be reset to
        # the values they had the last time "Accept" button was
        # clicked.


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    w = ColorsSetupWin()
    w.show()

    sys.exit(app.exec_())
