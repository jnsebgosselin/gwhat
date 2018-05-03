# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.


# ---- Third party imports

from PyQt5.QtWidgets import QGridLayout, QLabel, QWidget, QRadioButton


class OnOffToggleWidget(QWidget):
    """
    A widget that contains a label and two 'On'/'Off' radio buttons on a
    single horizontal row.
    """

    def __init__(self, label='', toggle=True, parent=None):
        super(OnOffToggleWidget, self).__init__(parent)
        self.setup(label, toggle)

    def setup(self, label, toggle):
        """Setup the widget with the provided options."""
        self.toggle_on = QRadioButton('On')
        self.toggle_off = QRadioButton('Off')
        self.set_toggle(toggle)

        layout = QGridLayout(self)
        layout.addWidget(QLabel(label + ' :'), 0, 0)
        layout.addWidget(self.toggle_on, 0, 2)
        layout.addWidget(self.toggle_off, 0, 3)
        layout.setColumnStretch(1, 100)
        layout.setContentsMargins(0, 0, 0, 0)

    @property
    def toggle(self):
        """Return True if the toggle is 'On' and False if it is 'Off'."""
        return self.toggle_on.isChecked()

    def set_toggle(self, toggle):
        """Set to 'On' if toggle is True and set to 'Off' if it is False."""
        if toggle:
            self.toggle_on.toggle()
        else:
            self.toggle_off.toggle()
