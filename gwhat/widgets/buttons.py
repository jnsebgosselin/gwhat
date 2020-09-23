# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Stantard imports
import sys
from abc import abstractmethod

# ---- Third party imports
import numpy as np
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import pyqtSlot as QSlot
from PyQt5.QtCore import QSize, Qt, QEvent
from PyQt5.QtWidgets import (QApplication, QDoubleSpinBox, QGridLayout,
                             QListWidget, QMenu, QStyle, QToolButton, QWidget)

# ---- Local imports
from gwhat.utils.icons import QToolButtonBase
from gwhat.utils import icons
from gwhat.widgets.layout import VSep
from gwhat.widgets.fileio import SaveFileMixin


class ToolBarWidget(QWidget):
    """A standard toolbar with some layout specifics."""

    def __init__(self, parent=None):
        super(ToolBarWidget, self).__init__(parent)
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

    def addWidget(self, widget):
        """Add the widget to the toolbar layout."""
        lay = self.layout()
        if widget is None:
            widget = VSep()
        lay.setColumnStretch(lay.columnCount()-1, 0)
        lay.addWidget(widget, 0, lay.columnCount())
        lay.setColumnStretch(lay.columnCount(), 100)


class SmartSpinBox(QDoubleSpinBox):
    """
    A spinbox that can act as a QSpinBox or QDoubleSpinBox that stores its
    value in an internal variable so that there is no loss in precision when
    the value of the spinbox is set programatically. In addition, the
    previous value of the spinbox is stored internally.

    The signal that is emitted when the value of the spinbox changes is also
    smarter than the one implemented in the QDoubleSpinBox. The signal also
    send the previous value in addition to the new value.

    Finally, it is allowed to enter values that are above or below the range
    of the spinbox when editing the value in the line edit. The value will
    be corrected to the maximum or minimum value once the editing is finished.
    """
    sig_value_changed = QSignal(float, float)

    def __init__(self, val=0, dec=0, step=1, units=None, parent=None,
                 show_btns=True):
        super(SmartSpinBox, self).__init__(parent)
        if show_btns is False:
            self.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.setAlignment(Qt.AlignCenter)
        self.setKeyboardTracking(False)
        self.setAccelerated(True)

        self.__current_value = val
        self.__previous_value = 0
        self.setRange(0, 100)
        self.setDecimals(dec)
        self.setValue(val)
        if step is not None:
            self.setSingleStep(step)
        else:
            self.setSingleStep(10**-dec)
        if units is not None:
            self.setSuffix(units)

        self.editingFinished.connect(self.editValue)

    def keyPressEvent(self, event):
        """
        Qt method overrides to block certain key events when we want the
        spinbox to act as a QSpinBox instead of a QDoubleSpinBox.
        """
        if (event.key() in [Qt.Key_Comma, Qt.Key_Period] and
                self.decimals() == 0):
            event.accept()
        elif event.key() == Qt.Key_Minus and self.__min_value >= 0:
            event.accept()
        else:
            super(SmartSpinBox, self).keyPressEvent(event)

    def editValue(self):
        """
        Ensure that the value that was entered by editing the value of the
        spin box is within the range of values of the spinbox.
        """
        self.setValue(super(SmartSpinBox, self).value())

    def stepBy(self, n):
        """
        Qt method overrides to ensure the value remains within the
        range of values of the spinbox.
        """
        new_value = self.value() + n*self.singleStep()
        self.setValue(new_value)

    def value(self):
        """
        Qt method override that returns the value stocked in the internal
        variable instead of the one displayed in the UI.
        """
        return self.__current_value

    def previousValue(self):
        """
        Returns the previous value of the spinbox.
        """
        return self.__previous_value

    def setValue(self, new_value):
        """Qt method override to save the value in an internal variable."""
        new_value = max(min(new_value, self.__max_value), self.__min_value)
        self.blockSignals(True)
        super(SmartSpinBox, self).setValue(new_value)
        self.blockSignals(False)
        if new_value != self.__current_value:
            self.__previous_value = self.__current_value
            self.__current_value = new_value
            self.sig_value_changed.emit(
                    self.__current_value, self.__previous_value)

    def setValueSilently(self, x):
        """
        Sets the value of the spinbox silently.
        """
        self.blockSignals(True)
        self.setValue(x)
        self.blockSignals(False)

    def setDecimals(self, x):
        """Qt method override to force a reset of the displayed range."""
        super(SmartSpinBox, self).setDecimals(x)
        self.setRange(self.__min_value, self.__max_value)

    def setRange(self, xmin, xmax):
        """Qt method override to save the range in internal variables."""
        if xmin > xmax:
            raise ValueError("xmin must be <= xmax")
        self.__max_value = xmax
        self.__min_value = xmin

        # Set the range of the spinbox so that its width is adjusted
        # correctly :
        lenght_int = int(np.ceil(np.log10(max(abs(xmax), abs(xmin)))))+1
        max_edit = float('9' * lenght_int + '.' + '9' * self.decimals())
        super(SmartSpinBox, self).setRange(-max_edit, max_edit)

        self.setValue(super(SmartSpinBox, self).value())


class RangeSpinBoxes(QWidget):
    """
    Consists of two spinboxes that are linked togheter so that one represent a
    lower boundary and the other one the upper boundary of a range.
    """
    sig_range_changed = QSignal(tuple)

    def __init__(self, min_value=0, max_value=100, orientation=Qt.Horizontal,
                 parent=None):
        super(RangeSpinBoxes, self).__init__(parent)
        self.spb_lower = SmartSpinBox()
        self.spb_upper = SmartSpinBox()

        self.spb_lower.sig_value_changed.connect(
                self.constrain_bounds_to_minmax)
        self.spb_upper.sig_value_changed.connect(
                self.constrain_bounds_to_minmax)

        self.setRange(min_value, max_value)

    @property
    def lower_bound(self):
        return self.spb_lower.value()

    @property
    def upper_bound(self):
        return self.spb_upper.value()

    def setRange(self, min_value, max_value):
        """Set the min max values of the range for both spin boxes."""
        if min_value > max_value:
            raise ValueError("min_value > max_value")
        self.spb_lower.setRange(min_value, max_value)
        self.spb_upper.setRange(min_value, max_value)
        self.spb_lower.setValueSilently(min_value)
        self.spb_upper.setValueSilently(max_value)

    @QSlot(float, float)
    def constrain_bounds_to_minmax(self, new_value, old_value):
        """
        Makes sure that the new value is within the min and max values that
        were set for the range. Also makes sure that the
        """
        if new_value > self.spb_upper.value():
            self.spb_upper.setValueSilently(new_value)
        if new_value < self.spb_lower.value():
            self.spb_lower.setValueSilently(new_value)
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


class DropdownToolButton(QToolButtonBase):
    """A toolbutton with a dropdown menu."""
    TOOLTIP = ''

    def __init__(self, icon, parent=None):
        super(DropdownToolButton, self).__init__(icon, parent)
        self.setToolTip(self.TOOLTIP)
        self.setPopupMode(QToolButtonBase.InstantPopup)
        self.setStyleSheet("QToolButton::menu-indicator {image: none;}")
        self.setup_menu()

    @abstractmethod
    def setup_menu(self):
        """Setup the menu of the button."""
        menu = QMenu()
        self.setMenu(menu)


class LangToolButton(DropdownToolButton):
    """A toolbutton that allow language selection."""
    TOOLTIP = ""
    LANGUAGES = {'french': 'FR',
                 'english': 'EN'}
    sig_lang_changed = QSignal(str)

    def __init__(self, parent=None):
        DropdownToolButton.__init__(self, 'language', parent)
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.__language = 'english'
        self.setText(self.LANGUAGES[self.language])

    def setup_menu(self):
        """Setup the languages in the menu."""
        super(LangToolButton, self).setup_menu()
        self.menu().addAction('English', lambda: self.set_language('english'))
        self.menu().addAction('French', lambda: self.set_language('french'))

    @property
    def language(self):
        """Return the current language."""
        return self.__language

    def set_language(self, lang):
        """Set the namespace for the language."""
        lang = lang.lower()
        lang = lang if lang in list(self.LANGUAGES.keys()) else 'english'
        if lang != self.__language:
            self.__language = lang
            self.setText(self.LANGUAGES[lang])
            self.sig_lang_changed.emit(lang)


class ExportDataButton(DropdownToolButton, SaveFileMixin):
    """
    A toolbutton with a dropdown menu that handles the export of data
    in various format.
    """
    MODELCLS = object

    def __init__(self, model=None, parent=None):
        DropdownToolButton.__init__(self, 'export_data', parent)
        SaveFileMixin.__init__(self)
        self.set_model(model)

    @property
    def model(self):
        return self.__model

    def set_model(self, model):
        """Set the data model of the button."""
        if model is None:
            self.__model = None
        else:
            if isinstance(model, self.MODELCLS):
                self.__model = model
            else:
                raise ValueError("The model must be an instance of %s" %
                                 str(type(self.MODELCLS)))
        self.setEnabled(self.__model is not None)


class OnOffToolButton(QToolButtonBase):
    """A tool button that can be toggled on or off by clicking on it."""
    sig_value_changed = QSignal(bool)

    def __init__(self, icon, icon_raised=None, size=None, parent=None):
        self._icon = icons.get_icon(icon) if isinstance(icon, str) else icon
        self._icon_raised = (icons.get_icon(icon_raised) if
                             isinstance(icon_raised, str) else icon_raised)
        super(OnOffToolButton, self).__init__(self._icon, parent)
        self.installEventFilter(self)
        if size is not None:
            self.setIconSize(icons.get_iconsize(size))

    def eventFilter(self, widget, event):
        if event.type() == QEvent.MouseButtonPress and self.isEnabled():
            self.setValue(not self.value())
        return super(OnOffToolButton, self).eventFilter(widget, event)

    def value(self):
        """Return True if autoRaise is False and False if True."""
        return not self.autoRaise()

    def setValue(self, value, silent=False):
        """Set autoRaise to False if value is True and to True if False."""
        if value != self.value():
            self.setAutoRaise(not bool(value))
            self._setup_icon()
            if not silent:
                self.sig_value_changed.emit(self.value())

    def _setup_icon(self):
        """Setup the icon of the button according to its auto raise state."""
        if self._icon_raised is None:
            return
        icon = self._icon_raised if self.value() else self._icon
        self.setIcon(icon)


# %% if __name__ == '__main__'

if __name__ == '__main__':
    app = QApplication(sys.argv)

    drop_button = DropDownButton(icon=icons.get_icon('todate'))
    drop_button.addItems([str(i) for i in range(2017, 1899, -1)])

    onoff_button = OnOffToolButton('play', 'stop')
    onoff_button.setIconSize(icons.get_iconsize('normal'))

    lang_button = LangToolButton()
    lang_button.setIconSize(icons.get_iconsize('normal'))

    toolbar = ToolBarWidget()
    toolbar.addWidget(onoff_button)
    toolbar.addWidget(drop_button)
    toolbar.addWidget(lang_button)
    toolbar.show()

    sys.exit(app.exec_())
