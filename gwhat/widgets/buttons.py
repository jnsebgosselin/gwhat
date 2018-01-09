# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Imports: Standard Libraries

import sys

# ---- Imports: Third Parties

from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import pyqtSlot as QSlot
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (QApplication, QToolButton, QListWidget, QStyle,
                             QSpinBox, QWidget, QAbstractSpinBox)


class RangeSpinBoxes(QWidget):
    """
    Consists of two QSpinBox that are linked togheter so that one represent a
    lower boundary and the other one the upper boundary of a range.
    """
    sig_range_changed = QSignal(tuple)

    def __init__(self, min_value=0, max_value=0, orientation=Qt.Horizontal,
                 parent=None):
        super(RangeSpinBoxes, self).__init__(parent)
        self.spb_lower = QSpinBox()
        self.spb_lower.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spb_lower.setAlignment(Qt.AlignCenter)
        self.spb_lower.setRange(0, 9999)
        self.spb_lower.setKeyboardTracking(False)

        self.spb_upper = QSpinBox()
        self.spb_upper.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spb_upper.setAlignment(Qt.AlignCenter)
        self.spb_upper.setRange(0, 9999)
        self.spb_upper.setKeyboardTracking(False)

        self.spb_lower.valueChanged.connect(self.constain_bounds_to_minmax)
        self.spb_upper.valueChanged.connect(self.constain_bounds_to_minmax)

        self.set_range(1000, 9999)

    @property
    def lower_bound(self):
        return self.spb_lower.value()

    @property
    def upper_bound(self):
        return self.spb_upper.value()

    def set_range(self, min_value, max_value):
        """Set the min max values of the range for both spin boxes."""
        self.min_value = min_value
        self.max_value = max_value
        self.spb_lower.setValue(min_value)
        self.spb_upper.setValue(max_value)

    @QSlot(int)
    def constain_bounds_to_minmax(self, new_value):
        """
        Makes sure that the new value is within the min and max values that
        were set for the range. Also makes sure that the
        """
        is_range_changed = False
        corr_value = min(max(new_value, self.min_value), self.max_value)
        if corr_value != new_value:
            is_range_changed = True
            self.sender().blockSignals(True)
            self.sender().setValue(corr_value)
            self.sender().blockSignals(False)
        if corr_value > self.spb_upper.value():
            is_range_changed = True
            self.spb_upper.blockSignals(True)
            self.spb_upper.setValue(corr_value)
            self.spb_upper.blockSignals(False)
        if corr_value < self.spb_lower.value():
            is_range_changed = True
            self.spb_lower.blockSignals(True)
            self.spb_lower.setValue(corr_value)
            self.spb_lower.blockSignals(False)
        if is_range_changed is True:
            self.sig_range_changed.emit((self.lower_bound, self.upper_bound))


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


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    drop_button = DropDownButton()
    drop_button.addItems([str(i) for i in range(2017, 1899, -1)])
    drop_button.show()
    sys.exit(app.exec_())
