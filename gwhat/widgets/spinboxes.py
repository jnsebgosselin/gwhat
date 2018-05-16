# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Imports: Standard Libraries

import sys
import os
import os.path as osp
from abc import abstractmethod

# ---- Imports: Third Parties

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QDoubleSpinBox, QFileDialog,
                             QGridLayout, QListWidget, QMenu, QMessageBox,
                             QStyle, QToolButton, QWidget, QSpinBox,
                             QLineEdit)


class StrSpinBox(QSpinBox):

    def __init__(self, model=None):
        super(StrSpinBox, self).__init__()
        self.set_model(model)
        self.setValue(0)
        self.setWrapping(True)
        self.lineEdit().setReadOnly(True)
        self.valueChanged.connect(
            self.lineEdit().deselect, Qt.QueuedConnection)

    @property
    def model(self):
        """Return the data model of the spin box."""
        return self.__model

    def set_model(self, model):
        """Set the data model of the spin box."""
        if model is None:
            self.__model = None
            self.setMaximum(0)
        else:
            if isinstance(model, list):
                self.__model = model
                self.setMaximum(len(model)-1)
            else:
                raise ValueError("The model must be a dict")
        self.setEnabled(self.__model is not None)

        # Force a refresh of the spinbox when the model changes :
        self.setValue(self.value())

    def textFromValue(self, value):
        """Qt method override."""
        if self.model is not None:
            return str(self.model[value])
        else:
            return ' '


# %% if __name__ == '__main__'

if __name__ == '__main__':
    app = QApplication(sys.argv)

    model = ['test', 'patate', 'test2', 'orange']
    text_sp = StrSpinBox(model)
    text_sp.show()

    sys.exit(app.exec_())
