# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.


# ---- Imports: standard libraries

import os


# ---- Imports: third parties

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QSplashScreen


# ---- Imports: local

from gwhat import __rootdir__


SPLASH_IMG = os.path.join(__rootdir__, 'ressources', 'splash.png')


class SplashScrn(QSplashScreen):
    def __init__(self):
        super(SplashScrn, self).__init__(QPixmap(SPLASH_IMG),
                                         Qt.WindowStaysOnTopHint)
        self.show()

    def showMessage(self, msg):
        """Override Qt method."""
        super(SplashScrn, self).showMessage(
                msg, Qt.AlignBottom | Qt.AlignCenter)
