# -*- coding: utf-8 -*-
"""
Copyright 2014-2017 Jean-Sebastien Gosselin
email: jean-sebastien.gosselin@ete.inrs.ca

This file is part of WHAT (Well Hydrograph Analysis Toolbox)..

WHAT is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# Standard library imports :

import sys
import platform
import os

# Third party imports :

from PySide import QtGui, QtCore

# Local imports :

try:
    import mgui
    from mgui.icons import IconDB
except ImportError:  # to run this module standalone
    print('Running module as a standalone script...')
    import sys
    import platform
    from os.path import dirname, realpath
    root = dirname(dirname(realpath(__file__)))
    sys.path.append(root)

    import mgui
    from mgui.icons import IconDB


# ==============================================================================


class AboutWhat(QtGui.QWidget):

    def __init__(self, parent=None):
        super(AboutWhat, self).__init__(parent)

        self.parent = parent
        self.initUI_About()

    def initUI_About(self):

        # ---------------------------------------------------- MAIN WINDOW ----

        self.setWindowTitle('Search for Weather Stations')
        self.setWindowIcon(IconDB().master)
#        self.setMinimumHeight(700)
#        self.setFont(styleDB.font1)

        # --------------------------------------------------- AboutTextBox ----

        self.AboutTextBox = QtGui.QTextBrowser()
        self.AboutTextBox.installEventFilter(self)
        self.AboutTextBox.setReadOnly(True)
        self.AboutTextBox.setFixedWidth(850)
        self.AboutTextBox.setFrameStyle(0)
        self.AboutTextBox.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)
        self.AboutTextBox.setOpenExternalLinks(True)

        # http://stackoverflow.com/questions/9554435/
        # qtextedit-background-color-change-also-the-color-of-scrollbar
        self.AboutTextBox.setStyleSheet('QTextEdit {background-color:"white"}')

        # http://stackoverflow.com/questions/26441999/
        # how-do-i-remove-the-space-between-qplaintextedit-and-its-contents
        self.AboutTextBox.document().setDocumentMargin(0)

        # self.AboutTextBox.setAlignment(QtCore.Qt.AlignCenter)
        # self.AboutTextBox.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)

        self.set_html_in_AboutTextBox()

        # ------------------------------------------------------ Main Grid ----

        grid = QtGui.QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(self.AboutTextBox, 0, 1)

#        grid.setColumnStretch(1, 500)
#        grid.setColumnStretch(2, 500)
        grid.setContentsMargins(10, 10, 10, 10)
#        grid.setColumnMinimumWidth(1, 850)

        self.setLayout(grid)

    # =========================================================================

    def set_html_in_AboutTextBox(self):

        # ---- Image Logo ----

        width = 750  # self.AboutTextBox.size().width()
        version = mgui.__version__
        date = mgui.__date__

        dirname = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(dirname, 'Icons', 'WHAT_banner_750px.png')

        # http://doc.qt.io/qt-4.8/richtext-html-subset.html

        if platform.system() == 'Windows':
            fontfamily = "Segoe UI"  # "Cambria" #"Calibri" #"Segoe UI""
        elif platform.system() == 'Linux':
            fontfamily = "Ubuntu"

        about_text = '''
                     <style>
                     p{font-size: 14px;
                       font-family: "%s";
                       margin-right:50px;
                       margin-left:50px}
                     p1{font-size: 16px;
                        font-family: "%s";
                        }
                     p2{font-size: 16px;
                        font-family: "%s";}
                     </style>
                     ''' % (fontfamily, fontfamily, fontfamily)

        about_text += '''
                      <p align="center"> <br>
                        <img src="%s" width="%d">
                      </p>
                      ''' % (filename, width)

#        # ---- Header ----

        about_text += '''
                      <p1 align=center>
                        <br><br>
                        Version %s<br>
                      </p1>
                      <p2 align=center>
                        Copyright 2014-2015 Jean-S&eacute;bastien Gosselin<br>
                        jean-sebastien.gosselin@ete.inrs.ca
                      <br>
                      <br>
                        Institut National de la Recherche Scientifique<br>
                        Research Center Eau Terre Environnement, Quebec City,
                        QC, Canada<br>
                        <a href="http://www.ete.inrs.ca/">
                          (http://www.ete.inrs.ca)
                        </a>
                        <br>
                      </p2>
                      ''' % (version[5:])

        # ---- License ----

        about_text += '''
                      <p align = "justify">
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
                      <p align="right">%s</p>
                      ''' % (version, date)


        self.AboutTextBox.setHtml(about_text)

    def eventFilter(self, obj, event): #========================================

        # http://stackoverflow.com/questions/13788452/
        # pyqt-how-to-handle-event-without-inheritance

        # https://srinikom.github.io/pyside-docs/PySide/QtCore/QObject.
        # html#PySide.QtCore.PySide.QtCore.QObject.installEventFilter

#        if event.type() == QtCore.QEvent.Type.Resize:
#
#            self.set_html_in_AboutTextBox() # To Keep the image logo to the
#                                            # same width as the QTextEdit box

        if event.type() == QtCore.QEvent.Type.FontChange:
            return True # Eat the event to disable zooming

        return QtGui.QWidget.eventFilter(self, obj, event)

if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)

    instance1 = AboutWhat()

    #---- SHOW ----

    instance1.show()

    qr = instance1.frameGeometry()
    cp = QtGui.QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    instance1.move(qr.topLeft())

    sys.exit(app.exec_())