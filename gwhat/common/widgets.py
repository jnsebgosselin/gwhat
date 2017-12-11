# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

from __future__ import division, unicode_literals

# Standard library imports :

from copy import copy
import os

from gwhat.common import icons

from PyQt5.QtCore import Qt, QSize, QPoint, QUrl
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QGridLayout, QLabel, QFrame, QMessageBox,
                             QComboBox, QDoubleSpinBox, QAbstractSpinBox,
                             QGroupBox, QWidget, QDialog, QDesktopWidget,
                             QTextBrowser, QPushButton, QStyle, QScrollArea,
                             QToolButton)


# =============================================================================


class MyQLineLayout(QGridLayout):

    def __init__(self, widgets, parent=None):
        super(MyQLineLayout, self).__init__(parent)

        for i, widget in enumerate(widgets):
            self.addWidget(widget, 0, i)

        self.setContentsMargins(0, 0, 0, 0)  # (l, t, r, b)
        self.setColumnStretch(self.columnCount(), 100)


# ================================================================ Labels =====


class QTitle(QLabel):

    def __init__(self, text, parent=None):
        super(QTitle, self).__init__(parent)

        color = '#404040'
        text = "<font color=%s>%s</font>" % (color, text)
        self.setText(text)

        ft = self.font()
        ft.setPointSize(12)
        ft.setBold(True)
        self.setFont(ft)
        self.setAlignment(Qt.AlignLeft | Qt.AlignBottom)


class QWarningLabel(QLabel):
    def __init__(self, text, parent=None):
        super(QWarningLabel, self).__init__(text, parent)
        ft = self.font()
        ft.setPointSize(8)
        ft.setItalic(True)
        self.setFont(ft)
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)


class ModeLabel(QLabel):
    def __init__(self, label, color):
        super(ModeLabel, self).__init__()
        self.setText('<font color=%s>%s</font>' % (color, label))
        ft = self.font()
        ft.setPointSize(10)
        ft.setItalic(True)
        self.setFont(ft)
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)


class AlignHCenterLabel(QLabel):
    def __init__(self, *args, **kargs):
        super(AlignHCenterLabel, self).__init__(*args, **kargs)
        self.setAlignment(Qt.AlignHCenter |
                          Qt.AlignVCenter)


# ============================================================ Separators =====


class HSep(QFrame):                               # horizontal separators
    def __init__(self, parent=None):
        super(HSep, self).__init__(parent)
        self.setFrameStyle(52)


class VSep(QFrame):                                 # vertical separators
    def __init__(self, parent=None):
        super(VSep, self).__init__(parent)
        self.setFrameStyle(53)


# ========================================================= Messsage Box ======


class MyQErrorMessageBox(QMessageBox):
    def __init__(self, parent=None):
        super(MyQErrorMessageBox, self).__init__(parent)

#        self.setIcon(QMessageBox.Warning)
        self.setWindowTitle('Error Message')
        self.setWindowIcon(QIcon('Icons/versalogo.png'))


# ================================================================== Boxes ====


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


# ================================================================ Layout =====

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

    # -------------------------------------------------------------------------

    def rowCount(self):
        return self.layout().rowCount()

    def columnCount(self):
        return self.layout().columnCount()


class QGroupWidget(QGroupBox):
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

        self.setLayout(QGridLayout())
        self.layout().setContentsMargins(10, 25, 10, 10)  # (l, t, r, b)

    def addWidget(self, item, x, y, nx=1, ny=1):
        self.layout().addWidget(item, x, y, nx, ny)

    def addLayout(self, layout, x, y, nx=1, ny=1):
        self.layout().addLayout(layout, x, y, nx, ny)

    def rowCount(self):
        return self.layout().rowCount()


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
                                Qt.WindowMinimizeButtonHint)

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


class AboutWindow(DialogWindow):
    def __init__(self, parent=None):
        super(AboutWindow, self).__init__(parent, resizable=False)
        self.setWindowTitle('About')
        self.setWindowFlags(Qt.Window)
        self.setWindowIcon(icons.get_icon('master'))

        grid = QGridLayout()
        self.setLayout(grid)

        self.tb = QTextBrowser()
        self.tb.setOpenExternalLinks(True)
        self.tb.setMinimumSize(750, 550)

        ok = QPushButton('Ok')
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
        self.tb.setSource(QUrl.fromLocalFile(filename))


# -----------------------------------------------------------------------------


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
        self.layout().setContentsMargins(0, 0, 0, 0)

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


# =============================================================== Buttons =====


class BtnBase(QWidget):

    clicked = QSignal(bool)

    def __init__(self, parent=None):
        super(BtnBase, self).__init__(parent)

        self._btn = QToolButton()
        self._btn.setIconSize(QSize(16, 16))
        self._btn.setAutoRaise(True)
        self._btn.clicked.connect(self.btn_isClicked)

        layout = QGridLayout()
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
        self.setIcon(icons.get_icon('getfrom'))


class GuessBtn(BtnBase):
    def __init__(self, parent=None):
        super(GuessBtn, self).__init__(parent)
        self.setIcon(icons.get_icon('calcul'))
        self.setToolTip('Guesstimate values')


class InfoBtn(QToolButton):
    def __init__(self, parent=None):
        super(InfoBtn, self).__init__(parent)
        self.setIconSize(QSize(16, 16))
        self.setAutoRaise(True)
        self.setIcon(icons.get_icon('about'))

        self.infopg = AboutWindow()

        self.clicked.connect(self.show_info)

    def show_info(self):
        self.infopg.show()

    def setSource(self, filename):
        self.infopg.setSource(filename)

    def setWindowTitle(self, title):
        self.infopg.setWindowTitle(title)


class LinkBtn(QToolButton):
    def __init__(self, parent=None):
        super(LinkBtn, self).__init__(parent)
        self.setIconSize(QSize(16, 16))
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
            self.setIcon(icons.get_icon('link'))
            self.setToolTip('Link values')
        else:
            self.setIcon(icons.get_icon('notlink'))
            self.setToolTip('Unlink values')


class MyQToolButton(QToolButton):

    def __init__(self, parent=None):
        super(MyQToolButton, self).__init__(parent)
        self.setIconSize(QSize(24, 24))
        self.setAutoRaise(True)
