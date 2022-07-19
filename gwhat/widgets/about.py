# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

# ---- Standard library imports
import platform
import os.path as osp

# ---- Third party imports
from qtpy.QtGui import QPixmap
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtCore import pyqtSlot as QSlot
from qtpy.QtWidgets import (
    QDialog, QPushButton, QGridLayout, QWidget, QApplication,
    QDesktopWidget, QLabel, QVBoxLayout, QFrame, QTabWidget)

# ---- Local imports
from gwhat import (__version__, __appname__, __date__, __project_url__,
                   __namever__, __rootdir__)
from gwhat.utils import icons
from gwhat.widgets.updates import ManagerUpdates


class AboutWhat(QDialog):

    def __init__(self, parent=None, pytesting=False):
        super(AboutWhat, self).__init__(parent)
        self._pytesting = pytesting
        self.setWindowTitle('About %s' % __appname__)
        self.setWindowIcon(icons.get_icon('information'))

        self.setMinimumSize(800, 700)
        self.setFixedWidth(850)
        self.setWindowFlags(Qt.Window |
                            Qt.CustomizeWindowHint |
                            Qt.WindowCloseButtonHint)

        self.manager_updates = ManagerUpdates(self)

        self.__initUI__()

    def __initUI__(self):
        """Initialize the GUI."""
        pixmap = QPixmap(osp.join(
            __rootdir__, 'ressources', 'WHAT_banner_750px.png'))
        label_banner = QLabel(self)
        label_banner.setPixmap(pixmap)
        label_banner.setPixmap(
            pixmap.scaledToWidth(600, Qt.SmoothTransformation))
        label_banner.setAlignment(Qt.AlignTop)

        # ---- AboutTextBox
        if platform.system() == 'Windows':
            font_family = "Segoe UI"  # "Cambria" #"Calibri" #"Segoe UI""
        elif platform.system() == 'Linux':
            font_family = "Ubuntu"
        font_size = 11

        # Setup the toolbar.
        self.ok_btn = QPushButton('OK')
        self.ok_btn.clicked.connect(self.close)

        self.btn_check_updates = QPushButton(' Check for Updates ')
        self.btn_check_updates.clicked.connect(
            self._btn_check_updates_isclicked)

        toolbar = QGridLayout()
        toolbar.addWidget(self.btn_check_updates, 0, 1)
        toolbar.addWidget(self.ok_btn, 0, 2)
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setColumnStretch(0, 100)

        label_general = QLabel(
            """
            <div style='font-family: "{font_family}";
                        font-size: {font_size}pt;
                        font-weight: normal;
                        '>
            <p>
            GWHAT version {gwhat_version}, released on {release_date}
            <br>
            Copyright &copy; 2014-2022
            <a href="https://github.com/jnsebgosselin/gwhat/graphs/contributors">
              GWHAT Project Contributors
            </a>
            <br>
            Licensed under the terms of the GNU General Public License Version 3
            <br>
            <a href="{gwhat_url}">{gwhat_url}</a>
            </p>
            <p>
            Created and maintained by Jean-S&eacute;bastien Gosselin
            <br>
            Geoscientific Developer at Géostack
            <br>
            <a href="https://www.geostack.ca/">
              https://www.geostack.ca
            </a>
            </p>
            </div>
            """.format(
                gwhat_url=__project_url__,
                gwhat_namever=__namever__,
                gwhat_version=__version__,
                release_date=__date__,
                font_family=font_family,
                font_size=font_size,
            )
        )
        label_general.setWordWrap(True)
        label_general.setAlignment(Qt.AlignTop)
        label_general.setOpenExternalLinks(True)
        label_general.setTextInteractionFlags(Qt.TextBrowserInteraction)
        label_general.setMargin(10)

        label_license = QLabel(
            """
            <div style='font-family: "{font_family}";
                        font-size: {font_size}pt;
                        font-weight: normal;
                        '>
            <p>
            {gwhat_namever} is free software: you can redistribute it and/or
            modify it under the terms
            of the GNU General Public License as published by the
            Free Software Foundation, either version 3 of the
            License, or (at your option) any later version.
            </p>
            <p>
            This program is distributed in the hope that it will be
            useful, but WITHOUT ANY WARRANTY; without even the
            implied warranty of MERCHANTABILITY or FITNESS FOR A
            PARTICULAR PURPOSE. See the GNU General Public
            License for more details.
            </p>
            <p>
            You should have received a copy of the GNU General
            Public License along with this program.  If not, see
            <a href="http://www.gnu.org/licenses">
              http://www.gnu.org/licenses
            </a>.
            </p>



            </div>
            """.format(
                gwhat_namever=__namever__,
                font_family=font_family,
                font_size=font_size,
            )
        )
        label_license.setWordWrap(True)
        label_license.setAlignment(Qt.AlignTop)
        label_license.setOpenExternalLinks(True)
        label_license.setTextInteractionFlags(Qt.TextBrowserInteraction)
        label_license.setMargin(10)

        # Setup the tabbar widget.
        tab_widget = QTabWidget()
        tab_widget.addTab(label_general, 'Overview')
        tab_widget.addTab(label_license, 'License')

        # Setup the content layout.
        content_frame = QFrame(self)
        content_frame.setStyleSheet(
            "QFrame {background-color: white}")
        content_layout = QVBoxLayout(content_frame)
        content_layout.addWidget(label_banner)
        content_layout.addWidget(tab_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)

        # Setup the main layout.
        layout = QVBoxLayout(self)
        layout.addWidget(content_frame)
        layout.addLayout(toolbar)

        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSizeConstraint(layout.SetFixedSize)

        self.ok_btn.setFocus()

    @QSlot()
    def _btn_check_updates_isclicked(self):
        """Handles when the button to check for updates is clicked."""
        self.manager_updates.start_updates_check()

    def eventFilter(self, obj, event):
        # http://stackoverflow.com/questions/13788452/
        # pyqt-how-to-handle-event-without-inheritance

        # https://srinikom.github.io/pyside-docs/PySide/QtCore/QObject.
        # html#PySide.QtCore.PySide.QtCore.QObject.installEventFilter

        if event.type() == QEvent.FontChange:
            return True  # Eat the event to disable zooming
        else:
            return QWidget.eventFilter(self, obj, event)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    instance1 = AboutWhat()
    instance1.show()

    qr = instance1.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    instance1.move(qr.topLeft())

    sys.exit(app.exec_())
