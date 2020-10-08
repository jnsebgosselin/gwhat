# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

# ---- Third party imports
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QColorDialog, QDialog, QGridLayout, QLabel, QPushButton,
    QToolButton, QWidget)


# ---- Local imports
from gwhat.config.colors import ColorsManager


class ColorsSetupDialog(QDialog):

    newColorSetupSent = QSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Colors Palette Setup')
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.__initUI__()

    def __initUI__(self):
        # Setup the colors.
        colorsDB = ColorsManager()
        colorGrid_widget = QWidget()
        self.colorGrid_layout = QGridLayout(colorGrid_widget)
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

        # Settup the buttons.
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

        # Setup the main layout.
        main_layout = QGridLayout(self)
        main_layout.addWidget(colorGrid_widget, 0, 0)
        main_layout.addWidget(toolbar_widget, 1, 0)
        main_layout.setSizeConstraint(main_layout.SetFixedSize)

    def load_colors(self):
        colors_manager = ColorsManager()
        for row, key in enumerate(colors_manager.keys()):
            item = self.colorGrid_layout.itemAtPosition(row, 3).widget()
            item.setStyleSheet(
                "background-color: rgb(%i,%i,%i)" %
                (colors_manager.RGB[key][0],
                 colors_manager.RGB[key][1],
                 colors_manager.RGB[key][2]))

    def reset_defaults(self):
        colors_manager = ColorsManager()
        colors_manager.reset_defaults()
        for row, key in enumerate(colors_manager.keys()):
            btn = self.colorGrid_layout.itemAtPosition(row, 3).widget()
            btn.setStyleSheet(
                "background-color: rgb(%i,%i,%i)" %
                (colors_manager.RGB[key][0],
                 colors_manager.RGB[key][1],
                 colors_manager.RGB[key][2]))

    def pick_color(self):
        sender = self.sender()
        color = QColorDialog.getColor(sender.palette().base().color())
        if color.isValid():
            rgb = color.getRgb()[:-1]
            sender.setStyleSheet("background-color: rgb(%i,%i,%i)" % rgb)

    def btn_OK_isClicked(self):
        self.btn_apply_isClicked()
        self.close()

    def btn_apply_isClicked(self):
        colors_manager = ColorsManager()
        for row, key in enumerate(colors_manager.keys()):
            item = self.colorGrid_layout.itemAtPosition(row, 3).widget()
            rgb = item.palette().base().color().getRgb()[:-1]
            colors_manager.RGB[key] = [rgb[0], rgb[1], rgb[2]]
        colors_manager.save_colors()
        self.newColorSetupSent.emit(True)

    def closeEvent(self, event):
        super().closeEvent(event)
        self.load_colors()

        # If cancel or X is clicked, the parameters will be reset to
        # the values they had the last time "Accept" button was
        # clicked.


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    w = ColorsSetupDialog()
    w.show()
    sys.exit(app.exec_())
