# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# Standard library imports :

import platform

# Third party imports :

from PyQt5.QtGui import QIcon, QFont, QFontDatabase
from PyQt5.QtCore import QSize


class StyleDB(object):
    def __init__(self):

        # ---- frame

        self.frame = 22
        self.HLine = 52
        self.VLine = 53
        self.sideBarWidth = 275

        # ----- colors

        self.red = '#C83737'
        self.lightgray = '#E6E6E6'
        self.rain = '#0000CC'
        self.snow = '0.7'
        self.wlvl = '#0000CC'  # '#000099'

        if platform.system() == 'Windows':
            self.font1 = QFont('Segoe UI', 11)  # Calibri, Cambria
            self.font_console = QFont('Segoe UI', 9)
            self.font_menubar = QFont('Segoe UI', 10)
        elif platform.system() == 'Linux':
            self.font1 = QFont('Ubuntu', 11)
            self.font_console = QFont('Ubuntu', 9)
            self.font_menubar = QFont('Ubuntu', 10)

#        database = QFontDatabase()
#        print database.families()

        if platform.system() == 'Windows':
            self.fontfamily = "Segoe UI"  # "Cambria" #"Calibri" #"Segoe UI""
        elif platform.system() == 'Linux':
            self.fontfamily =  "Ubuntu"

#        self.fontSize1.setPointSize(11)

        # 17 = QtGui.QFrame.Box | QtGui.QFrame.Plain
        # 22 = QtGui.QFrame.StyledPanel | QtGui.QFrame.Plain
        # 20 = QtGui.QFrame.HLine | QtGui.QFrame.Plain
        # 52 = QtGui.QFrame.HLine | QtGui.QFrame.Sunken
        # 53 = QtGui.QFrame.VLine | QtGui.QFrame.Sunken







