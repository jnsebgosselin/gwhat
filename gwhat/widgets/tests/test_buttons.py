# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# Standard library imports
import sys
import os

# Third party imports
import pytest
from PyQt5.QtCore import Qt

# Local imports
from gwhat.widgets.buttons import SmartSpinBox, RangeSpinBoxes


# ---- Test SmartSpinBox


def test_smartspinbox_prog(qtbot):
    """Tests the interface of the SmartSpinBox when used programatically."""
    spinbox = SmartSpinBox(3.1298739862187356123)
    qtbot.addWidget(spinbox)

    # Assert the default state :

    assert spinbox.maximum() == 999
    assert spinbox.minimum() == -999
    assert spinbox.decimals() == 0
    assert spinbox.value() == 3.1298739862187356123
    assert spinbox.previousValue() == 0

    # Test when setting the value below the minimum :

    spinbox.setValue(-1.5)
    assert spinbox.value() == 0
    assert spinbox.previousValue() == 3.1298739862187356123

    # Test when setting the value above the maximum :

    spinbox.setValue(135)
    assert spinbox.value() == 100
    assert spinbox.previousValue() == 0


def test_smartspinbox_gui(qtbot):
    """Tests the interface of the SmartSpinBox when used from the GUI."""
    spinbox = SmartSpinBox()
    qtbot.addWidget(spinbox)

    # Test when entering a value above the maximum :

    spinbox.clear()
    qtbot.keyClicks(spinbox, '120')
    qtbot.keyClick(spinbox, Qt.Key_Enter)
    assert spinbox.value() == 100
    assert spinbox.previousValue() == 0

    # Test when entering a value below the minimum :

    spinbox.clear()
    qtbot.keyClicks(spinbox, '-1.5')
    qtbot.keyPress(spinbox, Qt.Key_Enter)
    # The - and . are not registered since the minimum value is 0 and the
    # precision is 0. Therefore, the number entered is 15.
    assert spinbox.value() == 15
    assert spinbox.previousValue() == 100

    # Test when entering a valid value :

    spinbox.clear()
    qtbot.keyClicks(spinbox, '15')
    qtbot.keyPress(spinbox, Qt.Key_Enter)
    assert spinbox.value() == 15
    assert spinbox.previousValue() == 100

    # Test when changing the decimals and range and entering a valid value,
    # but with more decimals than what the edit box is accepting :

    spinbox.setDecimals(2)
    spinbox.setRange(-100, 100)
    assert spinbox.decimals() == 2
    assert spinbox.maximum() == 999.99
    assert spinbox.minimum() == -999.99

    spinbox.clear()
    qtbot.keyClicks(spinbox, '-6.5342435234')
    qtbot.keyPress(spinbox, Qt.Key_Enter)
    assert spinbox.value() == -6.53
    assert spinbox.previousValue() == 15


# ---- Test RangeSpinBoxes

def test_rangespinbox(qtbot):
    """Tests the interface of the RangeSpinBoxes when used from the GUI."""
    rangespinbox = RangeSpinBoxes(1800, 2010)
    qtbot.addWidget(rangespinbox)

    assert rangespinbox.lower_bound == 1800
    assert rangespinbox.upper_bound == 2010

    # Test if setting a non valide range :

    with pytest.raises(ValueError):
        rangespinbox.setRange(2010, 2000)
    assert rangespinbox.lower_bound == 1800
    assert rangespinbox.upper_bound == 2010

    # Test the link between the smartspinboxes min and max values :

    rangespinbox.spb_lower.clear()
    qtbot.keyClicks(rangespinbox.spb_lower, '2009')
    qtbot.keyPress(rangespinbox.spb_lower, Qt.Key_Enter)
    assert rangespinbox.lower_bound == 2009

    rangespinbox.spb_upper.clear()
    qtbot.keyClicks(rangespinbox.spb_upper, '2005')
    qtbot.keyPress(rangespinbox.spb_upper, Qt.Key_Enter)
    assert rangespinbox.lower_bound == 2005
    assert rangespinbox.upper_bound == 2005

    rangespinbox.spb_lower.clear()
    qtbot.keyClicks(rangespinbox.spb_lower, '2015')
    qtbot.keyPress(rangespinbox.spb_lower, Qt.Key_Enter)
    assert rangespinbox.lower_bound == 2010
    assert rangespinbox.upper_bound == 2010

    # Test when navigating with the up and down keys :

    qtbot.keyClick(rangespinbox.spb_lower, Qt.Key_Down)
    qtbot.keyClick(rangespinbox.spb_upper, Qt.Key_Down)
    assert rangespinbox.lower_bound == 2009
    assert rangespinbox.upper_bound == 2009

    qtbot.keyClick(rangespinbox.spb_upper, Qt.Key_Up)
    qtbot.keyClick(rangespinbox.spb_lower, Qt.Key_Up)
    assert rangespinbox.lower_bound == 2010
    assert rangespinbox.upper_bound == 2010

    # Test the link between the smartspinboxes when using the
    # up and down keys :

    nclick = 5
    for i in range(nclick):
        qtbot.keyClick(rangespinbox.spb_upper, Qt.Key_Down)
    assert rangespinbox.lower_bound == 2010-nclick
    assert rangespinbox.upper_bound == 2010-nclick

    for i in range(nclick+3):
        qtbot.keyClick(rangespinbox.spb_lower, Qt.Key_Up)
    assert rangespinbox.lower_bound == 2010
    assert rangespinbox.upper_bound == 2010


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
