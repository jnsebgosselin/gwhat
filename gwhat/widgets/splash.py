# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Third parties imports

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QSplashScreen

# ---- Local imports

SPLASH_IMG = 'ressources/splash.png'


class SplashScrn(QSplashScreen):
    def __init__(self):
        super(SplashScrn, self).__init__(QPixmap(SPLASH_IMG),
                                         Qt.WindowStaysOnTopHint)
        self.show()

    def showMessage(self, msg):
        """Override Qt method."""
        super(SplashScrn, self).showMessage(
                msg, Qt.AlignBottom | Qt.AlignCenter)
