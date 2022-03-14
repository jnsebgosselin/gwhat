# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

# ---- Standard library imports
import copy

# ---- Third party imports
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import (QApplication, QTabWidget, QWidget, QTabBar,
                             QDesktopWidget, QHBoxLayout)

# ---- Local imports
from gwhat.utils import icons


class TabWidget(QTabWidget):
    def __init__(self, parent=None):
        super(TabWidget, self).__init__(parent=None)

        self._buttons = []
        self._button_box = QWidget(self)
        layout = QHBoxLayout(self._button_box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)

        tab_bar = TabBar(self, parent)
        self.setTabBar(tab_bar)
        tab_bar.sig_resized.connect(self._move_about_btn)
        tab_bar.sig_tab_layout_changed.connect(self._move_about_btn)

    def add_button(self, button):
        """Add the provided button to the tab bar."""
        button.setIconSize(icons.get_iconsize('small'))
        button.setFixedSize(32, 32)
        self._button_box.layout().addWidget(button)
        self._buttons.append(button)

    def resizeEvent(self, event):
        """Qt method override."""
        super().resizeEvent(event)
        self._move_about_btn()

    def _move_about_btn(self):
        """
        Move the buton to show the About dialog window to the right
        side of the tab bar.
        """
        x = 0
        for i in range(self.count()):
            x += self.tabBar().tabRect(i).width()
        self._button_box.move(x, 0)


class TabBar(QTabBar):

    sig_resized = QSignal()
    sig_tab_layout_changed = QSignal()

    def __init__(self, tab_widget, parent=None):
        super(TabBar, self).__init__(parent=None)

        self.__tab_widget = tab_widget

        self.__oldIndex = -1
        self.__newIndex = -1
        self.currentChanged.connect(self.storeIndex)

    def tabWidget(self):
        return self.__tab_widget

    def tabSizeHint(self, index):
        width = QTabBar.tabSizeHint(self, index).width()
        return QSize(width, 32)

    def sizeHint(self):
        sizeHint = QTabBar.sizeHint(self)
        w = sizeHint.width()
        for button in self.tabWidget()._buttons:
            w += button.size().width()
        return QSize(w, 32)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.sig_resized.emit()

    def tabLayoutChange(self):
        super().tabLayoutChange()
        self.sig_resized.emit()

    def storeIndex(self, index):
        self.__oldIndex = copy.copy(self.__newIndex)
        self.__newIndex = index

    def previousIndex(self):
        return self.__oldIndex


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    tabwidget = TabWidget()
    tabwidget.addTab(QWidget(), 'Tab#1')
    tabwidget.addTab(QWidget(), 'Tab#2')
    tabwidget.addTab(QWidget(), 'Tab#3')
    tabwidget.show()

    qr = tabwidget.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    tabwidget.move(qr.topLeft())

    sys.exit(app.exec_())
