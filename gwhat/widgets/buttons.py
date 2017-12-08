# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Imports: standard libraries

import sys

# ---- Imports: third parties

from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QApplication, QToolButton, QListWidget, QStyle


class DropDownButton(QToolButton):
    """QToolButton with QComboBox dropdown-like capability."""
    sig_year_selected = QSignal(int)

    def __init__(self, parent=None, icon=None, icon_size=QSize(28, 28)):
        super(QToolButton, self).__init__(parent=None)
        if icon:
            self.setIcon(icon)
        self.setIconSize(icon_size)
        self.setAutoRaise(True)
        self.setFocusPolicy(Qt.NoFocus)

        self.droplist = DropDownList(self)

        self.clicked.connect(self.show_dropdown)
        self.sig_year_selected = self.droplist.sig_year_selected

    def addItems(self, items):
        """Clear and add items to the button dropdown list."""
        self.droplist.clear()
        self.droplist.addItems(items)

    def show_dropdown(self):
        """Show and set focus on the dropdown list."""
        self.droplist.show()
        self.droplist.setFocus()


class DropDownList(QListWidget):
    sig_year_selected = QSignal(int)

    def __init__(self, parent):
        super(DropDownList, self).__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.hide()

    def show(self):
        """
        Qt method override to show the dropdown list under its parent,
        aligned to its left edge.
        """
        point = self.parent().rect().bottomLeft()
        global_point = self.parent().mapToGlobal(point)
        self.move(global_point)
        self.resizeColumnsToContents()
        super(DropDownList, self).show()

    def resizeColumnsToContents(self):
        """Adjust the width of the list to its content."""
        self.setFixedWidth(
                self.sizeHintForColumn(0) + 2*self.frameWidth() +
                QApplication.style().pixelMetric(QStyle.PM_ScrollBarExtent))

    def keyPressEvent(self, event):
        """
        Qt method override to select the highlighted item and hide the list
        if the Enter key is pressed.
        """
        super(DropDownList, self).keyPressEvent(event)
        if event.key() == Qt.Key_Return:
            self.sig_year_selected.emit(int(self.currentItem().text()))
            self.hide()

    def mousePressEvent(self, event):
        """
        Qt method override to select and hide the list if an item is clicked
        with the left button of the mouse.
        """
        super(DropDownList, self).mousePressEvent(event)
        if event.button() == 1:
            self.sig_year_selected.emit(int(self.currentItem().text()))
            self.hide()

    def focusOutEvent(self, event):
        """Qt method override to hide the list when focus is lost."""
        event.ignore()
        # Don't hide it on Mac when main window loses focus because
        # keyboard input is lost
        if sys.platform == "darwin":
            if event.reason() != Qt.ActiveWindowFocusReason:
                self.hide()
        else:
            self.hide()


if __name__ == '__main__':                                   # pragma: no cover
    import sys

    app = QApplication(sys.argv)
    drop_button = DropDownButton()
    drop_button.addItems([str(i) for i in range(2017, 1899, -1)])
    drop_button.show()
    sys.exit(app.exec_())
