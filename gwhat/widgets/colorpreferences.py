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

    sig_color_preferences_changed = QSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Colors Palette Setup')
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.__initUI__()

    def __initUI__(self):
        # Setup the colors.
        colors_manager = ColorsManager()
        colorGrid_widget = QWidget()
        self.colorGrid_layout = QGridLayout(colorGrid_widget)
        self._color_buttons = []
        for i, key in enumerate(colors_manager.keys()):
            self.colorGrid_layout.addWidget(
                QLabel('{} :'.format(colors_manager.labels[key])), i, 0)

            btn = QToolButton()
            btn.setAutoRaise(True)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.clicked.connect(self.pick_color)
            btn.setToolTip('Click to select a new color.')
            btn.color_key = key
            self.colorGrid_layout.addWidget(btn, i, 1)
            self._color_buttons.append(btn)
        self.colorGrid_layout.setColumnStretch(0, 100)
        self.load_colors()

        # Settup the buttons.
        btn_apply = QPushButton('Apply')
        btn_apply.clicked.connect(self.btn_apply_isClicked)
        btn_cancel = QPushButton('Cancel')
        btn_cancel.clicked.connect(self.close)
        btn_OK = QPushButton('OK')
        btn_OK.clicked.connect(self.btn_OK_isClicked)
        btn_reset = QPushButton('Reset Defaults')
        btn_reset.clicked.connect(self.reset_defaults)

        toolbar_widget = QWidget()
        toolbar_layout = QGridLayout(toolbar_widget)
        toolbar_layout.addWidget(btn_reset, 1, 0, 1, 3)
        toolbar_layout.addWidget(btn_OK, 2, 0)
        toolbar_layout.addWidget(btn_cancel, 2, 1)
        toolbar_layout.addWidget(btn_apply, 2, 2)
        toolbar_layout.setColumnStretch(3, 100)
        toolbar_layout.setRowStretch(0, 100)

        # Setup the main layout.
        main_layout = QGridLayout(self)
        main_layout.addWidget(colorGrid_widget, 1, 0)
        main_layout.addWidget(toolbar_widget, 2, 0)
        main_layout.setSizeConstraint(main_layout.SetFixedSize)

    def load_colors(self):
        colors_manager = ColorsManager()
        for button in self._color_buttons:
            button.setStyleSheet(
                "background-color: rgb(%i,%i,%i)" %
                tuple(colors_manager.RGB[button.color_key]))

    def reset_defaults(self):
        colors_manager = ColorsManager()
        colors_manager.reset_defaults()
        for button in self._color_buttons:
            button.setStyleSheet(
                "background-color: rgb(%i,%i,%i)" %
                tuple(colors_manager.RGB[button.color_key]))

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
        for button in self._color_buttons:
            rgb = button.palette().base().color().getRgb()[:-1]
            colors_manager.RGB[button.color_key] = [rgb[0], rgb[1], rgb[2]]
        colors_manager.save_colors()
        self.sig_color_preferences_changed.emit(True)

    def showEvent(self, event):
        self.load_colors()
        super().showEvent(event)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    w = ColorsSetupDialog()
    w.show()
    sys.exit(app.exec_())
