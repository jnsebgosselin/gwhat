# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# Standard library imports :

from copy import copy

from gwhat.common import icons

from PyQt5.QtCore import Qt, QSize, QPoint, QUrl
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QGridLayout, QLabel, QFrame, QMessageBox,
                             QComboBox, QDoubleSpinBox, QAbstractSpinBox,
                             QGroupBox, QWidget, QDialog, QDesktopWidget,
                             QTextBrowser, QPushButton, QStyle, QScrollArea,
                             QToolButton)


class MyQLineLayout(QGridLayout):

    def __init__(self, widgets, parent=None):
        super(MyQLineLayout, self).__init__(parent)

        for i, widget in enumerate(widgets):
            self.addWidget(widget, 0, i)

        self.setContentsMargins(0, 0, 0, 0)  # (l, t, r, b)
        self.setColumnStretch(self.columnCount(), 100)


class MyQComboBox(QComboBox):
    def __init__(self, parent=None):
        super(MyQComboBox, self).__init__(parent)

        self.__oldIndex = -1
        self.__newIndex = -1
        self.currentIndexChanged.connect(self.storeIndex)

    def storeIndex(self, index):
        self.__oldIndex = copy(self.__newIndex)
        self.__newIndex = index

    def revertToPrevIndex(self):
        self.__newIndex = copy(self.__oldIndex)
        self.setCurrentIndexSilently(self.__oldIndex)

    def setCurrentIndexSilently(self, index):
        self.blockSignals(True)
        self.setCurrentIndex(index)
        self.blockSignals(False)


class QDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, val, dec=0, step=None, units=None,
                 parent=None, read_only=False):
        super(QDoubleSpinBox, self).__init__(parent)

        self.__value = 0

        self.setKeyboardTracking(False)
        self.setAccelerated(True)
        self.setCorrectionMode(QAbstractSpinBox.CorrectToNearestValue)
        self.setFocusPolicy(Qt.ClickFocus)
        self.setAlignment(Qt.AlignCenter)

        self.setDecimals(dec)
        self.setValue(val)

        if step is not None:
            self.setSingleStep(step)
        else:
            self.setSingleStep(10**-dec)

        if units is not None:
            self.setSuffix(units)

        self.setButtonSymbols(QAbstractSpinBox.NoButtons)
        if read_only is True:
            self.setSpecialValueText('\u2014')
            self.setReadOnly(True)

        self.valueChanged.connect(self.saveNewValue)

    def saveNewValue(self, x):
        self.__value = x

    def setValueSilently(self, x):
        self.blockSignals(True)
        self.setValue(x)
        self.blockSignals(False)

    def setValue(self, x):
        super(QDoubleSpinBox, self).setValue(x)
        self.__value = x

    def value(self):
        return self.__value


class QFrameLayout(QFrame):
    def __init__(self, parent=None):
        super(QFrameLayout, self).__init__(parent)

        self.setLayout(QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

    def addWidget(self, widget, x, y, w=1, h=1):
        self.layout().addWidget(widget, x, y, w, h)

    def addLayout(self, layout, x, y, w=1, h=1):
        self.layout().addLayout(layout, x, y, w, h)

    # -------------------------------------------------------------------------

    def setRowMinimumHeight(self, row, height):
        self.layout().setRowMinimumHeight(row, height)

    # -------------------------------------------------------------------------

    def setRowStretch(self, row, stretch):
        self.layout().setRowStretch(row, stretch)

    def setColumnStretch(self, column, stretch):
        self.layout().setColumnStretch(column, stretch)

    # -------------------------------------------------------------------------

    def setContentsMargins(self, left, top, right, bottom):
        self.layout().setContentsMargins(left, top, right, bottom)

    def setSpacing(self, spacing):
        self.layout().setSpacing(spacing)

    def setVerticalSpacing(self, spacing):
        self.layout().setVerticalSpacing(spacing)

    def setHorizontalSpacing(self, spacing):
        self.layout().setHorizontalSpacing(spacing)

    # -------------------------------------------------------------------------

    def rowCount(self):
        return self.layout().rowCount()

    def columnCount(self):
        return self.layout().columnCount()


class DialogWindow(QDialog):

    def __init__(self, parent=None, resizable=False, maximize=True):
        super(DialogWindow, self).__init__(parent)

        self.__firstshow = True
        if maximize is True:
            self.__resizable = True
            self.setWindowFlags(Qt.Window)
        else:
            self.__resizable = resizable
            self.setWindowFlags(Qt.Window |
                                Qt.WindowMinimizeButtonHint |
                                Qt.WindowCloseButtonHint)

        self.setWindowIcon(icons.get_icon('master'))

    def emit_warning(self, msg, title='Warning'):
        btn = QMessageBox.Ok
        QMessageBox.warning(self, title, msg, btn)

    def show(self):
        if self.__firstshow is True:
            self.__firstshow = False

            self.setAttribute(Qt.WA_DontShowOnScreen, True)
            super(DialogWindow, self).show()
            super(DialogWindow, self).close()
            self.setAttribute(Qt.WA_DontShowOnScreen, False)

            qr = self.frameGeometry()
            if self.parentWidget():
                parent = self.parentWidget()
                wp = parent.frameGeometry().width()
                hp = parent.frameGeometry().height()
                cp = parent.mapToGlobal(QPoint(wp/2, hp/2))
            else:
                cp = QDesktopWidget().availableGeometry().center()
            qr.moveCenter(cp)
            self.move(qr.topLeft())

            super(DialogWindow, self).show()

            if self.__resizable is False:
                self.setFixedSize(self.size())
        else:
            super(DialogWindow, self).show()

        self.raise_()


class QToolPanel(QWidget):
    """
    A custom widget that mimicks the behavior of the "Tools" sidepanel in
    Adobe Acrobat. It is derived from a QToolBox with the following variants:

    1. Only one tool can be displayed at a time.
    2. Unlike the stock QToolBox widget, it is possible to hide all the tools.
    3. It is also possible to hide the current displayed tool by clicking on
       its header.
    4. The tools that are hidden are marked by a right-arrow icon, while the
       tool that is currently displayed is marked with a down-arrow icon.
    5. Closed and Expanded arrows can be set from custom icons.
    """

    def __init__(self, parent=None):
        super(QToolPanel, self).__init__(parent)

        self.__iclosed = QWidget().style().standardIcon(
            QStyle.SP_ToolBarHorizontalExtensionButton)
        self.__iexpand = QWidget().style().standardIcon(
            QStyle.SP_ToolBarVerticalExtensionButton)

        self.setLayout(QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)  # (l, t, r, b)

        self.__currentIndex = -1

    def setIcons(self, ar_right, ar_down):  # =================================
        self.__iclosed = ar_right
        self.__iexpand = ar_down

    def addItem(self, tool, text):  # =========================================

        N = self.layout().rowCount()

        # Add Header :

        head = QPushButton(text)
        head.setIcon(self.__iclosed)
        head.clicked.connect(self.__isClicked__)
        head.setStyleSheet("QPushButton {text-align:left;}")

        self.layout().addWidget(head, N-1, 0)

        # Add Item in a ScrollArea :

        scrollarea = QScrollArea()
        scrollarea.setFrameStyle(0)
        scrollarea.hide()
        scrollarea.setStyleSheet("QScrollArea {background-color:transparent;}")
        scrollarea.setWidgetResizable(True)

        tool.setObjectName("myViewport")
        tool.setStyleSheet("#myViewport {background-color:transparent;}")
        scrollarea.setWidget(tool)

        self.layout().addWidget(scrollarea, N, 0)
        self.layout().setRowStretch(N+1, 100)

    def __isClicked__(self):  # ===============================================

        for row in range(0, self.layout().rowCount()-1, 2):

            head = self.layout().itemAtPosition(row, 0).widget()
            tool = self.layout().itemAtPosition(row+1, 0).widget()

            if head == self.sender():
                if self.__currentIndex == row:
                    # if clicked tool is open, close it
                    head.setIcon(self.__iclosed)
                    tool.hide()
                    self.__currentIndex = -1
                else:
                    # if clicked tool is closed, expand it
                    head.setIcon(self.__iexpand)
                    tool.show()
                    self.__currentIndex = row
            else:
                # close all the other tools so that only one tool can be
                # expanded at a time.
                head.setIcon(self.__iclosed)
                tool.hide()
