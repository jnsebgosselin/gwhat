# -*- coding: utf-8 -*-
"""
Copyright 2014-2016 Jean-Sebastien Gosselin
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

import os
import csv
from PySide import QtCore, QtGui

# =============================================================================


class Colors():

    def __init__(self):

        self.RGB = [[255, 212, 212],  # Air Temperature
                    [ 23,  52,  88],  # Rain
                    [165, 165, 165],  # Snow
                    [ 45, 100, 167],  # Water Level (solid line)
                    [204, 204, 204],  # Water Level (data dots)
                    [255,   0,   0]]  # Water Level (measures)

        self.rgb = [[255./255, 212./255, 212./255],  # Air Temperature
                    [ 23./255,  52./255,  88./255],  # Rain
                    [165./255, 165./255, 165./255],  # Snow
                    [ 45./255, 100./255, 167./255],  # Water Level (solid line)
                    [0.8, 0.8, 1],                   # Water Level (data dots)
                    [255./255,   0./255,   0./255]]  # Water Level (measures)

        self.labels = ['Air Temperature', 'Rain', 'Snow',
                       'Water Level (solid line)',
                       'Water Level (data dots)',
                       'Water Level (man. obs.)']

    def load_colors_db(self):  # ==============================================

        fname = 'Colors.db'
        if not os.path.exists(fname):
            print('No color database file exists, creating a new one...')
            self.save_colors_db()

        else:
            print('Loading colors database...')
            with open(fname, 'r') as f:
                reader = list(csv.reader(f, delimiter='\t'))

            for row in range(len(reader)):
                self.RGB[row] = [int(i) for i in reader[row][1:]]
                self.rgb[row] = [(int(i)/255.) for i in reader[row][1:]]

        print('Colors database loaded sucessfully.')

    def save_colors_db(self):  # ==============================================

        fname = 'Colors.db'
        fcontent = []
        for i in range(len(self.labels)):
            fcontent.append([self.labels[i]])
            fcontent[-1].extend(self.RGB[i])

        with open(fname, 'w') as f:
            writer = csv.writer(f, delimiter='\t', lineterminator='\n')
            writer.writerows(fcontent)

        print('Color database saved successfully')


# =============================================================================


class ColorsSetupWin(QtGui.QWidget):                         # ColorsSetupWin #

    newColorSetupSent = QtCore.Signal(bool)

    def __init__(self, parent=None):
        super(ColorsSetupWin, self).__init__(parent)

        self.setWindowTitle('Colors Palette Setup')
        self.setWindowFlags(QtCore.Qt.Window)

        self.__initUI__()

    def __initUI__(self):  # ==================================================

        # ---- Toolbar ----

        toolbar_widget = QtGui.QWidget()

        btn_apply = QtGui.QPushButton('Apply')
        btn_apply.clicked.connect(self.btn_apply_isClicked)
        btn_cancel = QtGui.QPushButton('Cancel')
        btn_cancel.clicked.connect(self.close)
        btn_OK = QtGui.QPushButton('OK')
        btn_OK.clicked.connect(self.btn_OK_isClicked)
        btn_reset = QtGui.QPushButton('Reset Defaults')
        btn_reset.clicked.connect(self.reset_defaults)

        toolbar_layout = QtGui.QGridLayout()
        toolbar_layout.addWidget(btn_reset, 1, 0, 1, 3)
        toolbar_layout.addWidget(btn_OK, 2, 0)
        toolbar_layout.addWidget(btn_cancel, 2, 1)
        toolbar_layout.addWidget(btn_apply, 2, 2)

        toolbar_layout.setColumnStretch(3, 100)
        toolbar_layout.setRowStretch(0, 100)

        toolbar_widget.setLayout(toolbar_layout)

        # ---- Color Grid ----

        colorsDB = Colors()
        colorsDB.load_colors_db()

        colorGrid_widget = QtGui.QWidget()

        self.colorGrid_layout = QtGui.QGridLayout()
        for i in range(len(colorsDB.rgb)):
            self.colorGrid_layout.addWidget(
                QtGui.QLabel('%s :' % colorsDB.labels[i]), i, 0)

            btn = QtGui.QToolButton()
            btn.setAutoRaise(True)
            btn.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            btn.clicked.connect(self.pick_color)

            self.colorGrid_layout.addWidget(btn, i, 3)
        self.load_colors()
        self.colorGrid_layout.setColumnStretch(2, 100)

        colorGrid_widget.setLayout(self.colorGrid_layout)

        # ---- Main Layout ----

        main_layout = QtGui.QGridLayout()
        main_layout.addWidget(colorGrid_widget, 0, 0)
        main_layout.addWidget(toolbar_widget, 1, 0)
        self.setLayout(main_layout)

    def load_colors(self):  # =================================================

        colorsDB = Colors()
        colorsDB.load_colors_db()

        nrow = self.colorGrid_layout.rowCount()
        for row in range(nrow):
            item = self.colorGrid_layout.itemAtPosition(row, 3).widget()
            item.setStyleSheet("background-color: rgb(%i,%i,%i)" %
                               (colorsDB.RGB[row][0],
                                colorsDB.RGB[row][1],
                                colorsDB.RGB[row][2])
                               )

    def reset_defaults(self):  # =========================== Reset Deafaults ==

        colorsDB = Colors()

        nrow = self.colorGrid_layout.rowCount()
        for row in range(nrow):
            btn = self.colorGrid_layout.itemAtPosition(row, 3).widget()
            btn.setStyleSheet("background-color: rgb(%i,%i,%i)" %
                              (colorsDB.RGB[row][0],
                               colorsDB.RGB[row][1],
                               colorsDB.RGB[row][2])
                              )

    def pick_color(self):  # =============================== Pick New Colors ==

        sender = self.sender()
        color = QtGui.QColorDialog.getColor(sender.palette().base().color())
        if color.isValid():
            rgb = color.getRgb()[:-1]
            sender.setStyleSheet("background-color: rgb(%i,%i,%i)" % rgb)

    def btn_OK_isClicked(self):  # ====================================== OK ==
        self.btn_apply_isClicked()
        self.close()

    def btn_apply_isClicked(self):  # ================================ Apply ==

        colorsDB = Colors()
        colorsDB.load_colors_db()

        nrow = self.colorGrid_layout.rowCount()
        for row in range(nrow):
            item = self.colorGrid_layout.itemAtPosition(row, 3).widget()
            rgb = item.palette().base().color().getRgb()[:-1]

            colorsDB.RGB[row] = [rgb[0], rgb[1], rgb[2]]
            colorsDB.rgb[row] = [rgb[0]/255., rgb[1]/255., rgb[2]/255.]

        colorsDB.save_colors_db()
        self.newColorSetupSent.emit(True)

    def closeEvent(self, event):  # ================================== Close ==
        super(ColorsSetupWin, self).closeEvent(event)

        # ---- Refresh UI ----

        # If cancel or X is clicked, the parameters will be reset to
        # the values they had the last time "Accept" button was
        # clicked.

        self.load_colors()

    def show(self):  # ================================================ Show ==

        self.activateWindow()
        self.raise_()

        qr = self.frameGeometry()
        if self.parentWidget():
            parent = self.parentWidget()

            wp = parent.frameGeometry().width()
            hp = parent.frameGeometry().height()
            cp = parent.mapToGlobal(QtCore.QPoint(wp/2., hp/2.))
        else:
            cp = QtGui.QDesktopWidget().availableGeometry().center()

        qr.moveCenter(cp)
        self.move(qr.topLeft())

        super(ColorsSetupWin, self).show()
        self.setFixedSize(self.size())

if __name__ == '__main__':
    import sys

    app = QtGui.QApplication(sys.argv)

    w = ColorsSetupWin()
    w.show()

    sys.exit(app.exec_())
