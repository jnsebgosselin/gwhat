# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

from __future__ import division, unicode_literals

# ---- Standard library imports

import os
from datetime import datetime

# ---- Third party imports

from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import (QWidget, QLabel, QDesktopWidget, QPushButton,
                             QApplication, QGridLayout, QMessageBox, QDialog,
                             QLineEdit, QToolButton, QFileDialog)

# ---- Local imports

from gwhat.projet.reader_projet import ProjetReader
from gwhat.common import QToolButtonSmall
from gwhat.common import icons
from gwhat.projet.manager_data import DataManager
from gwhat.projet.reader_waterlvl import init_waterlvl_measures
import gwhat.common.widgets as myqt
from gwhat import __version__


class ProjetManager(QWidget):

    currentProjetChanged = QSignal(ProjetReader)

    def __init__(self, parent=None, projet=None):
        super(ProjetManager, self).__init__(parent)
        self.new_projet_dialog = NewProject(parent)
        self.new_projet_dialog.sig_new_project.connect(self.load_project)

        self.__projet = None
        self.__initGUI__()
        if projet:
            self.load_project(projet)

    def __initGUI__(self):
        self.project_display = QPushButton()
        self.project_display.setFocusPolicy(Qt.NoFocus)
        self.project_display.setMinimumWidth(100)
        self.project_display.clicked.connect(self.select_project)

        ft = QApplication.instance().font()
        ft.setPointSize(ft.pointSize()-1)
        self.project_display.setFont(ft)

        new_btn = QToolButtonSmall(icons.get_icon('new_project'))
        new_btn.setToolTip('Create a new project...')
        new_btn.clicked.connect(self.show_newproject_dialog)

        # ---- layout ----

        layout = QGridLayout(self)

        layout.addWidget(QLabel('Project :'), 0, 1)
        layout.addWidget(self.project_display, 0, 2)
        layout.addWidget(new_btn, 0, 3)

        layout.setSpacing(3)
        layout.setContentsMargins(0, 0, 0, 5)  # (L, T, R, B)
        layout.setColumnStretch(0, 500)
        layout.setRowMinimumHeight(0, 28)

    # =========================================================================

    @property
    def projet(self):
        return self.__projet

    def select_project(self):
        directory = os.path.abspath(os.path.join('..', 'Projects'))
        filename, _ = QFileDialog.getOpenFileName(
            self, 'Open Project', directory, '*.gwt ; *.what')

        if filename:
            self.projectfile = filename
            self.load_project(filename)

    def load_project(self, filename):
        try:
            self.__projet = projet = ProjetReader(filename)
        except:
            self.__projet = None
            msg = ('Project loading failed. <i>%s</i> is not a valid ' +
                   'WHAT project file.') % os.path.basename(filename)
            btn = QMessageBox.Ok
            QMessageBox.warning(self, 'Warning', msg, btn)
            return False
        else:
            wldir = os.path.join(projet.dirname, "Water Levels")
            init_waterlvl_measures(wldir)
            self.project_display.setText(projet.name)
            self.project_display.adjustSize()
            self.currentProjetChanged.emit(projet)

            return True

    def close_projet(self):
        self.__projet.close_projet()

    def show_newproject_dialog(self):
        self.new_projet_dialog.reset_UI()
        self.new_projet_dialog.show()


# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


class NewProject(QDialog):
    # Dialog window to create a new WHAT project.

    sig_new_project = QSignal(str)

    def __init__(self, parent=None):
        super(NewProject, self).__init__(parent)

        self.setWindowFlags(Qt.Window)
        self.setModal(True)

        self.setWindowTitle('New Project')
        self.setWindowIcon(icons.get_icon('master'))

        self.__initUI__()

    def __initUI__(self):

        # ---- Current Date ----

        now = datetime.now()
        now = (now.day, now.month, now.year, now.hour, now.minute)

        # ----------------------------------------------------- PROJECT INFO --

        # ---- Widgets ----

        self.name = QLineEdit()
        self.author = QLineEdit()
        self.date = QLabel('%02d/%02d/%d %02d:%02d' % now)
        self.createdby = QLabel(__version__)

        # ---- Layout ----

        projet_info = QGridLayout()

        row = 0
        projet_info.addWidget(QLabel('Project Title :'), row, 0)
        projet_info.addWidget(self.name, row, 1)
        row += 1
        projet_info.addWidget(QLabel('Author :'), row, 0)
        projet_info.addWidget(self.author, row, 1)
        row += 1
        projet_info.addWidget(QLabel('Created :'), row, 0)
        projet_info.addWidget(self.date, row, 1)
        row += 1
        projet_info.addWidget(QLabel('Software :'), row, 0)
        projet_info.addWidget(self.createdby, row, 1)

        projet_info.setSpacing(10)
        projet_info.setColumnStretch(1, 100)
        projet_info.setColumnMinimumWidth(1, 250)
        projet_info.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)

        # --------------------------------------------- LOCATION COORDINATES --

        locaCoord_title = QLabel('<b>Project Location Coordinates:</b>')
        locaCoord_title.setAlignment(Qt.AlignLeft)

        self.lat_spinbox = myqt.QDoubleSpinBox(0, 3, 0.1, ' °')
        self.lat_spinbox.setRange(0, 180)

        self.lon_spinbox = myqt.QDoubleSpinBox(0, 3, 0.1, ' °')
        self.lon_spinbox.setRange(0, 180)

        # ----- layout ----

        loc_coord = QGridLayout()

        row = 0
        loc_coord.addWidget(locaCoord_title, row, 0, 1, 11)
        row += 1
        loc_coord.setColumnStretch(0, 100)
        loc_coord.addWidget(QLabel('Latitude :'), row, 1)
        loc_coord.addWidget(self.lat_spinbox, row, 2)
        loc_coord.addWidget(QLabel('North'), row, 3)
        loc_coord.setColumnStretch(4, 100)

        loc_coord.addWidget(myqt.VSep(), row, 5)
        loc_coord.setColumnStretch(6, 100)

        loc_coord.addWidget(QLabel('Longitude :'), row, 7)
        loc_coord.addWidget(self.lon_spinbox, row, 8)
        loc_coord.addWidget(QLabel('West'), row, 9)
        loc_coord.setColumnStretch(10, 100)

        loc_coord.setSpacing(10)
        loc_coord.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)

        # --------------------------------------------------------- Browse ----

        # ---- widgets ----

        save_in_folder = os.path.abspath(os.path.join('..', 'Projects'))

        directory_label = QLabel('Save in Folder:')
        self.directory = QLineEdit()
        self.directory.setReadOnly(True)
        self.directory.setText(save_in_folder)
        self.directory.setMinimumWidth(350)

        btn_browse = QToolButton()
        btn_browse.setAutoRaise(True)
        btn_browse.setIcon(icons.get_icon('openFolder'))
        btn_browse.setIconSize(icons.get_iconsize('iconSize2'))
        btn_browse.setToolTip('Browse...')
        btn_browse.setFocusPolicy(Qt.NoFocus)
        btn_browse.clicked.connect(self.browse_saveIn_folder)

        browse = QGridLayout()

        browse.addWidget(directory_label, 0, 0)
        browse.addWidget(self.directory, 0, 1)
        browse.addWidget(btn_browse, 0, 2)

        browse.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)
        browse.setColumnStretch(1, 100)
        browse.setSpacing(10)

        # ---------------------------------------------------------- Toolbar --

        # ---- widgets ----

        btn_save = QPushButton(' Save')
        btn_save.setMinimumWidth(100)
        btn_save.clicked.connect(self.save_project)

        btn_cancel = QPushButton(' Cancel')
        btn_cancel.setMinimumWidth(100)
        btn_cancel.clicked.connect(self.close)

        # ---- layout ----

        toolbar = QGridLayout()

        toolbar.addWidget(btn_save, 0, 1)
        toolbar.addWidget(btn_cancel, 0, 2)

        toolbar.setSpacing(10)
        toolbar.setColumnStretch(0, 100)
        toolbar.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)

        # ------------------------------------------------------------- MAIN --

        main_layout = QGridLayout(self)

        main_layout.addLayout(projet_info, 0, 0)
        main_layout.addWidget(myqt.HSep(), 1, 0)
        main_layout.addLayout(loc_coord, 2, 0)
        main_layout.addWidget(myqt.HSep(), 3, 0)
        main_layout.addLayout(browse, 4, 0)
        main_layout.addLayout(toolbar, 5, 0)

        main_layout.setVerticalSpacing(25)
        main_layout.setContentsMargins(15, 15, 15, 15)  # (L, T, R, B)

    # =========================================================================

    def browse_saveIn_folder(self):
        folder = QFileDialog.getExistingDirectory(
                self, 'Save in Folder', '../Projects')
        if folder:
            self.directory.setText(folder)

    def save_project(self):
        name = self.name.text()
        if name == '':
            print('Please enter a valid Project name')
            return

        rootname = self.directory.text()
        dirname = os.path.join(rootname, name)

        # If directory already exist, a number is added at the end within ().

        count = 1
        while os.path.exists(dirname):
            dirname = os.path.join(rootname, '%s (%d)' % (name, count))
            count += 1

        print('\n---------------')
        print('Creating files and folder achitecture for the new project in:')
        print(dirname)
        print

        # ---- Create Files and Folders ----

        os.makedirs(dirname)

        # ---- folder architecture ----

        folders = [os.path.join(dirname, 'Meteo', 'Raw'),
                   os.path.join(dirname, 'Meteo', 'Input'),
                   os.path.join(dirname, 'Meteo', 'Output'),
                   os.path.join(dirname, 'Water Levels')]

        for f in folders:
            if not os.path.exists(f):
                os.makedirs(f)

        # ---- project.what ----

        fname = os.path.join(dirname, '%s.gwt' % name)

        projet = ProjetReader(fname)
        projet.name = self.name.text()
        projet.author = self.author.text()
        projet.created = self.date.text()
        projet.modified = self.date.text()
        projet.version = self.createdby.text()
        projet.lat = self.lat_spinbox.value()
        projet.lon = self.lon_spinbox.value()

        del projet

        print('Creating file %s.gwt' % name)
        print('---------------')

        self.close()
        self.sig_new_project.emit(fname)

    # =========================================================================

    def reset_UI(self):

        self.name.clear()
        self.author.clear()

        save_in_folder = os.path.abspath(os.path.join('..', 'Projects'))
        self.directory.setText(save_in_folder)

        now = datetime.now()
        now = (now.day, now.month, now.year, now.hour, now.minute)
        self.date = QLabel('%02d/%02d/%d %02d:%02d' % now)

        self.lat_spinbox.setValue(0)
        self.lon_spinbox.setValue(0)

    def show(self):
        super(NewProject, self).show()
        self.raise_()

        qr = self.frameGeometry()
        if self.parentWidget():
            wp = self.parentWidget().frameGeometry().width()
            hp = self.parentWidget().frameGeometry().height()
            cp = self.parentWidget().mapToGlobal(QPoint(wp/2., hp/2.))
        else:
            cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        self.setFixedSize(self.size())


# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


if __name__ == '__main__':                                   # pragma: no cover

    import sys

    f = 'C:/Users/jnsebgosselin/Desktop/Project4Testing/Project4Testing.what'

    app = QApplication(sys.argv)

    ft = app.font()
    ft.setFamily('Segoe UI')
    ft.setPointSize(11)
    app.setFont(ft)

    pm = ProjetManager(projet=None)
    pm.show()

    dm = DataManager(pm=pm)
    dm.show()

    app.exec_()
