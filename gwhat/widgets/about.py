# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Standard library imports

import platform
import os

# ---- Third party imports

from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import (QDialog, QTextBrowser, QPushButton, QGridLayout,
                             QWidget, QApplication, QDesktopWidget)

# ---- Local imports

from gwhat import __version__, __date__, __project_url__
from gwhat.common import icons
from gwhat import __rootdir__


class AboutWhat(QDialog):

    def __init__(self, parent=None):
        super(AboutWhat, self).__init__(parent)
        self.__initUI__()

    def __initUI__(self):

        # ----- MAIN WINDOW ----

        self.setWindowTitle('About %s' % __version__)
        self.setWindowIcon(icons.get_icon('master'))
        self.setMinimumSize(800, 700)
        self.setWindowFlags(Qt.Window |
                            Qt.CustomizeWindowHint |
                            Qt.WindowCloseButtonHint)

        # ---- AboutTextBox ----

        self.AboutTextBox = QTextBrowser()
        self.AboutTextBox.installEventFilter(self)
        self.AboutTextBox.setReadOnly(True)
        self.AboutTextBox.setFixedWidth(850)
        self.AboutTextBox.setFrameStyle(0)
        self.AboutTextBox.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.AboutTextBox.setOpenExternalLinks(True)

        self.AboutTextBox.setStyleSheet('QTextEdit {background-color:"white"}')
        self.AboutTextBox.document().setDocumentMargin(0)
        self.set_html_in_AboutTextBox()

        # ---- Ok btn ----

        self.ok_btn = QPushButton('OK')
        self.ok_btn.clicked.connect(self.close)

        # ---- Main Grid ----

        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(self.AboutTextBox, 0, 1, 1, 2)
        grid.addWidget(self.ok_btn, 1, 2)

        grid.setColumnStretch(1, 500)
        grid.setContentsMargins(10, 10, 10, 10)

        self.setLayout(grid)

    # =========================================================================

    def set_html_in_AboutTextBox(self):

        # ---- Image Logo ----

        width = 750
        version = __version__

        filename = os.path.join(
                __rootdir__, 'ressources', 'WHAT_banner_750px.png')

        # http://doc.qt.io/qt-4.8/richtext-html-subset.html

        if platform.system() == 'Windows':
            fontfamily = "Segoe UI"  # "Cambria" #"Calibri" #"Segoe UI""
        elif platform.system() == 'Linux':
            fontfamily = "Ubuntu"

        html = """
               <html>
               <head>
               <style>
               p {font-size: 16px;
                  font-family: "%s";
                  margin-right:50px;
                  margin-left:50px;
                  }
               p1 {font-size: 16px;
                   font-family: "%s";
                   margin-right:50px;
                   margin-left:50px;
                   }
               </style>
               </head>
               <body>
               """ % (fontfamily, fontfamily)

        # ---- Banner

        html += """
                <p align="left">
                  <br><img src="file:///%s" width="%d"><br>
                </p>
                """ % (filename, width)

        # ---- Copyrights

        html += """
                <br>
                <p1 align="right">
                  GWHAT version %s released on %s<br>
                  Copyright 2014-2017
                  <a href="https://github.com/jnsebgosselin/gwhat/graphs/contributors">
                    GWHAT Project Contributors
                  </a>
                  <br>
                  Licensed under the terms of the GNU General Public License Version 3
                  <br>
                  <a href="%s">%s</a>
                  <br>
                  <br>
                  Created by Jean-S&eacute;bastien Gosselin
                  <br>
                  <a href="mailto:jean-sebastien.gosselin@ete.inrs.ca">
                    jean-sebastien.gosselin@ete.inrs.ca
                  </a>
                  <br>
                  <br>
                  Developped and maintained by Jean-S&eacute;bastien Gosselin
                  <br>
                  Institut National de la Recherche Scientifique<br>
                  Research Center Eau-Terre-Environnement, Quebec City,
                  QC, Canada<br>
                  <a href="http://www.ete.inrs.ca/">
                    http://www.ete.inrs.ca
                  </a>
                  <br>
                </p1>
                """ % (version[5:].strip(), __date__,
                       __project_url__, __project_url__)

        # ---- License

        html += """
                <p align="justify">
                  %s is free software: you can redistribute it and/or
                  modify it under the terms
                  of the GNU General Public License as published by the
                  Free Software Foundation, either version 3 of the
                  License, or (at your option) any later version.
                </p>
                <p align="justify">
                  This program is distributed in the hope that it will be
                  useful, but WITHOUT ANY WARRANTY; without even the
                  implied warranty of MERCHANTABILITY or FITNESS FOR A
                  PARTICULAR PURPOSE. See the GNU General Public
                  License for more details.
                </p>
                <p align="justify">
                  You should have received a copy of the GNU General
                  Public License along with this program.  If not, see
                  <a href="http://www.gnu.org/licenses">
                    http://www.gnu.org/licenses
                  </a>.
                </p>
                </body>
                """ % version

        self.AboutTextBox.setHtml(html)

    # =========================================================================

    def eventFilter(self, obj, event):
        # http://stackoverflow.com/questions/13788452/
        # pyqt-how-to-handle-event-without-inheritance

        # https://srinikom.github.io/pyside-docs/PySide/QtCore/QObject.
        # html#PySide.QtCore.PySide.QtCore.QObject.installEventFilter

        if event.type() == QEvent.FontChange:
            return True  # Eat the event to disable zooming
        else:
            return QWidget.eventFilter(self, obj, event)

    def show(self):
        super(AboutWhat, self).show()
        self.setFixedSize(self.size())


if __name__ == '__main__':                                   # pragma: no cover
    import sys

    app = QApplication(sys.argv)

    instance1 = AboutWhat()
    instance1.show()

    qr = instance1.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    instance1.move(qr.topLeft())

    sys.exit(app.exec_())
