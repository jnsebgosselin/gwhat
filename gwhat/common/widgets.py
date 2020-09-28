# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# Standard library imports :

from copy import copy

from gwhat.utils import icons

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
                 parent=None, read_only=False, show_buttons=False):
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

        if show_buttons is False:
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
