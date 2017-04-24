# -*- coding: utf-8 -*-
"""
copyright (C) 2016-2017 INRS
contact: jean-sebastien.gosselin@outlook.com

This is part of WHAT

WHAT is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it /will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import division, unicode_literals

# Standard library imports :

from PySide import QtGui, QtCore
from copy import copy
import os

try:
    from common import IconDB
except ImportError:  # to run this module standalone
    import sys
    import platform
    from os.path import dirname, realpath, basename
    print('Running module %s as a standalone script...' % basename(__file__))
    root = dirname(dirname(realpath(__file__)))
    sys.path.append(root)

    from common import IconDB


# =============================================================================


class MyQLineLayout(QtGui.QGridLayout):

    def __init__(self, widgets, parent=None):
        super(MyQLineLayout, self).__init__(parent)

        for i, widget in enumerate(widgets):
            self.addWidget(widget, 0, i)

        self.setContentsMargins(0, 0, 0, 0)  # (l, t, r, b)
        self.setColumnStretch(self.columnCount(), 100)


# ================================================================ Labels =====


class QTitle(QtGui.QLabel):

    def __init__(self, text, parent=None):
        super(QTitle, self).__init__(parent)

        color = '#404040'
        text = "<font color=%s>%s</font>" % (color, text)
        self.setText(text)

        ft = self.font()
        ft.setPointSize(12)
        ft.setBold(True)
        self.setFont(ft)
        self.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)


class QWarningLabel(QtGui.QLabel):
    def __init__(self, text, parent=None):
        super(QWarningLabel, self).__init__(text, parent)
        ft = self.font()
        ft.setPointSize(8)
        ft.setItalic(True)
        self.setFont(ft)
        self.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)


class ModeLabel(QtGui.QLabel):
    def __init__(self, label, color):
        super(ModeLabel, self).__init__()
        self.setText('<font color=%s>%s</font>' % (color, label))
        ft = self.font()
        ft.setPointSize(10)
        ft.setItalic(True)
        self.setFont(ft)
        self.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)


class AlignHCenterLabel(QtGui.QLabel):
    def __init__(self, *args, **kargs):
        super(AlignHCenterLabel, self).__init__(*args, **kargs)
        self.setAlignment(QtCore.Qt.AlignHCenter |
                          QtCore.Qt.AlignVCenter)


# ============================================================ Separators =====


class HSep(QtGui.QFrame):                               # horizontal separators
    def __init__(self, parent=None):
        super(HSep, self).__init__(parent)
        self.setFrameStyle(52)


class VSep(QtGui.QFrame):                                 # vertical separators
    def __init__(self, parent=None):
        super(VSep, self).__init__(parent)
        self.setFrameStyle(53)


# ========================================================= Messsage Box ======


class MyQErrorMessageBox(QtGui.QMessageBox):
    def __init__(self, parent=None):
        super(MyQErrorMessageBox, self).__init__(parent)

#        self.setIcon(QtGui.QMessageBox.Warning)
        self.setWindowTitle('Error Message')
        self.setWindowIcon(QtGui.QIcon('Icons/versalogo.png'))


# ================================================================== Boxes ====


class MyQComboBox(QtGui.QComboBox):
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


class QDoubleSpinBox(QtGui.QDoubleSpinBox):
    def __init__(self, val, dec=0, step=None, units=None,
                 parent=None, read_only=False):
        super(QDoubleSpinBox, self).__init__(parent)

        self.__value = 0

        self.setKeyboardTracking(False)
        self.setAccelerated(True)
        self.setCorrectionMode(QtGui.QAbstractSpinBox.CorrectToNearestValue)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setAlignment(QtCore.Qt.AlignCenter)

        self.setDecimals(dec)
        self.setValue(val)

        if step is not None:
            self.setSingleStep(step)
        else:
            self.setSingleStep(10**-dec)

        if units is not None:
            self.setSuffix(units)

        if read_only is True:
            self.setSpecialValueText('\u2014')
            self.setReadOnly(True)
            self.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)

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


# ================================================================ Layout =====


class QGroupWidget(QtGui.QGroupBox):
    def __init__(self, parent=None):
        super(QGroupWidget, self).__init__(parent)

        col = '#404040'
        self.setStyleSheet('QGroupBox{'
                           'font-weight: bold;'
                           'font-size: 14px;'
                           'color: %s;'
                           'border: 1.5px solid %s;'
                           'border-radius: 5px;'
                           'subcontrol-position: bottom left;'
                           'margin-top: 7px;'
                           '}'
                           'QGroupBox::title {'
                           'subcontrol-position: top left;'
                           'left: 10px; top: -10px;'
                           'padding: 0 3px 0 3px;'
                           '}' % (col, col))

        self.setLayout(QtGui.QGridLayout())
        self.layout().setContentsMargins(10, 25, 10, 10)  # (l, t, r, b)

    def addWidget(self, item, x, y, nx=1, ny=1):
        self.layout().addWidget(item, x, y, nx, ny)

    def addLayout(self, layout, x, y, nx=1, ny=1):
        self.layout().addLayout(layout, x, y, nx, ny)

    def rowCount(self):
        return self.layout().rowCount()


class DialogWindow(QtGui.QDialog):

    def __init__(self, parent=None, resizable=False):
        super(DialogWindow, self).__init__(parent)

        self.__resizable = resizable
        self.__firstshow = True

        self.setWindowIcon(IconDB().master)
        self.setWindowFlags(QtCore.Qt.Window |
                            QtCore.Qt.WindowMinimizeButtonHint)

    def show(self):
        if self.__firstshow is True:
            self.__firstshow = False

            self.setAttribute(QtCore.Qt.WA_DontShowOnScreen, True)
            super(DialogWindow, self).show()
            super(DialogWindow, self).close()
            self.setAttribute(QtCore.Qt.WA_DontShowOnScreen, False)

            qr = self.frameGeometry()
            if self.parentWidget():
                parent = self.parentWidget()
                wp = parent.frameGeometry().width()
                hp = parent.frameGeometry().height()
                cp = parent.mapToGlobal(QtCore.QPoint(wp/2, hp/2))
            else:
                cp = QtGui.QDesktopWidget().availableGeometry().center()
            qr.moveCenter(cp)
            self.move(qr.topLeft())

            super(DialogWindow, self).show()

            if self.__resizable is False:
                self.setFixedSize(self.size())
        else:
            super(DialogWindow, self).show()
        self.raise_()


class AboutWindow(DialogWindow):
    def __init__(self, parent=None):
        super(AboutWindow, self).__init__(parent, resizable=False)
        self.setWindowTitle('About')
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowIcon(IconDB().master)

        grid = QtGui.QGridLayout()
        self.setLayout(grid)

        self.tb = QtGui.QTextBrowser()
        self.tb.setOpenExternalLinks(True)
        self.tb.setMinimumSize(750, 550)

        ok = QtGui.QPushButton('Ok')
        ok.clicked.connect(self.close)

        grid.addWidget(self.tb, 0, 0, 1, 2)
        grid.addWidget(ok, 1, 1)
        grid.setColumnStretch(0, 100)
        grid.setRowStretch(0, 100)

        # ---- Add page to browser ----

        dirname = os.path.dirname(os.path.realpath(__file__))
        dirname = os.path.join(dirname, 'doc')
        self.tb.setSearchPaths(dirname)

    def setSource(self, filename):
        dirname = os.path.dirname(os.path.realpath(__file__))
        dirname = os.path.join(dirname, 'doc')
        filename = os.path.join(dirname, filename)
        self.tb.setSource(QtCore.QUrl.fromLocalFile(filename))


# =============================================================== Buttons =====


class BtnBase(QtGui.QWidget):

    clicked = QtCore.Signal(bool)

    def __init__(self, parent=None):
        super(BtnBase, self).__init__(parent)

        self._btn = QtGui.QToolButton()
        self._btn.setIconSize(QtCore.QSize(16, 16))
        self._btn.setAutoRaise(True)
        self._btn.clicked.connect(self.btn_isClicked)

        layout = QtGui.QGridLayout()
        self.setLayout(layout)
        layout.setContentsMargins(10, 0, 0, 0)  # (l, t, r, b)
        layout.addWidget(self._btn)

    def btn_isClicked(self):
        self.clicked.emit(True)

    def setIcon(self, icon):
        self._btn.setIcon(icon)

    def setToolTip(self, text):
        self._btn.setToolTip(text)


class GetBtn(BtnBase):
    def __init__(self, parent=None):
        super(GetBtn, self).__init__(parent)
        self.setIcon(QtGui.QIcon(IconDB().getfrom))


class GuessBtn(BtnBase):
    def __init__(self, parent=None):
        super(GuessBtn, self).__init__(parent)
        self.setIcon(QtGui.QIcon(IconDB().calcul))
        self.setToolTip('Guesstimate values')


class InfoBtn(QtGui.QToolButton):
    def __init__(self, parent=None):
        super(InfoBtn, self).__init__(parent)
        self.setIconSize(QtCore.QSize(16, 16))
        self.setAutoRaise(True)
        self.setIcon(QtGui.QIcon(IconDB().about))

        self.infopg = AboutWindow()

        self.clicked.connect(self.show_info)

    def show_info(self):
        self.infopg.show()

    def setSource(self, filename):
        self.infopg.setSource(filename)

    def setWindowTitle(self, title):
        self.infopg.setWindowTitle(title)


class LinkBtn(QtGui.QToolButton):
    def __init__(self, parent=None):
        super(LinkBtn, self).__init__(parent)
        self.setIconSize(QtCore.QSize(16, 16))
        self.setAutoRaise(True)
        self.set_linked_state(True)

        self.__state = True

        self.clicked.connect(self.btn_clicked)

    @property
    def linked(self):
        return self.__state

    def btn_clicked(self):
        state = not self.__state
        self.set_linked_state(state)

    def set_linked_state(self, state):
        self.__state = state
        if state is True:
            self.setIcon(QtGui.QIcon(IconDB().link))
            self.setToolTip('Link values')
        else:
            self.setIcon(QtGui.QIcon(IconDB().notlink))
            self.setToolTip('Unlink values')


class MyQToolButton(QtGui.QToolButton):

    def __init__(self, parent=None):
        super(MyQToolButton, self).__init__(parent)
        self.setIconSize(QtCore.QSize(24, 24))
        self.setAutoRaise(True)


