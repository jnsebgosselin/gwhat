# -*- coding: utf-8 -*-
"""
Copyright 2014-2017 Jean-Sebastien Gosselin
email: jean-sebastien.gosselin@ete.inrs.ca

This file is part of WHAT (Well Hydrograph Analysis Toolbox).

WHAT is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""

from __future__ import division, unicode_literals

# Standard library imports :

from sys import argv
import platform
import os
import csv
from datetime import datetime
import re

# Third party imports :

from PySide import QtGui, QtCore
import h5py

# Local imports :

import database as db
from icons import IconDB
from database import styleUI
import my_widgets as myqt


class Projet(h5py.File):
    def __init__(self, name, mode='a'):
        super(Projet, self).__init__(name, mode)

        keys = list(self.attrs.keys())
        attrs = ['name', 'author', 'created', 'modified', 'version',
                 'latitude', 'longitude']

        for attr in attrs:
            if attr not in keys:
                self.attrs[attr] = 'None'

    # =========================================================================

    @property
    def name(self):
        return self.attrs['name']

    @name.setter
    def name(self, x):
        self.attrs['name'] = x

    @property
    def author(self):
        return self.attrs['author']

    @author.setter
    def author(self, x):
        self.attrs['author'] = x

    # -------------------------------------------------------------------------

    @property
    def created(self):
        return self.attrs['created']

    @created.setter
    def created(self, x):
        self.attrs['created'] = x

    @property
    def modified(self):
        return self.attrs['modified']

    @modified.setter
    def modified(self, x):
        self.attrs['modified'] = x

    @property
    def version(self):
        return self.attrs['version']

    @version.setter
    def version(self, x):
        self.attrs['version'] = x

    # -------------------------------------------------------------------------

    @property
    def lat(self):
        return self.attrs['latitude']

    @lat.setter
    def lat(self, x):
        self.attrs['latitude'] = x

    @property
    def lon(self):
        return self.attrs['longitude']

    @lon.setter
    def lon(self, x):
        self.attrs['longitude'] = x

    # =========================================================================

    def create_WL_dataset(self):
        pass


# =============================================================================
# =============================================================================


class ProjetManager(QtGui.QWidget):

    currentProjetChanged = QtCore.Signal(bool)

    def __init__(self, parent=None):
        super(ProjetManager, self).__init__(parent)

        self.__projet = None
        self.filename = None
        self.dirname = None

        self.__initGUI__()

    def __initGUI__(self):
        project_label = QtGui.QLabel('Project :')
        project_label.setAlignment(QtCore.Qt.AlignCenter)

        self.project_display = QtGui.QPushButton()
        self.project_display.setFocusPolicy(QtCore.Qt.NoFocus)
        self.project_display.setFont(styleUI().font_menubar)
        self.project_display.setMinimumWidth(100)
        self.project_display.clicked.connect(self.select_project)

        new_btn = QtGui.QToolButton()
        new_btn.setAutoRaise(True)
        new_btn.setIcon(IconDB().new_project)
        new_btn.setToolTip('Create a new project...')
        new_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        new_btn.setIconSize(styleUI().iconSize2)
        new_btn.clicked.connect(self.show_newproject_dialog)

        layout = QtGui.QGridLayout(self)

        layout.addWidget(project_label, 0, 1)
        layout.addWidget(self.project_display, 0, 2)
        layout.addWidget(new_btn, 0, 3)

        layout.setSpacing(3)
        layout.setContentsMargins(0, 0, 0, 5)  # (L, T, R, B)
        layout.setColumnStretch(0, 500)
        layout.setRowMinimumHeight(0, 28)

    # =========================================================================

    def currentProjet(self):
        return self.__projet

    # =========================================================================

    def show_newproject_dialog(self):
        if self.parent():
            new_project_window = NewProject(self.parent())
        else:
            new_project_window = NewProject(self)
        new_project_window.show()

    def select_project(self):
        directory = os.path.abspath(os.path.join('..', 'Projects'))
        filename, _ = QtGui.QFileDialog.getOpenFileName(
            self, 'Open Project', directory, '*.what')

        if filename:
            self.projectfile = filename
            self.load_project(filename)

    def load_project(self, filename):
        self.filename = filename
        self.dirname = os.path.dirname(filename)

        print('\n-------------------------------')
        print('LOADING PROJECT...')
        print('-------------------------------\n')
        print('Loading "%s"' % os.path.relpath(filename))

        try:
            if self.__projet:
                self.__projet.close()
            self.__projet = Projet(filename)
        except OSError:
            print('Old file format. Converting to the new format.')

            # ---- reading old project file ----

            with open(filename, 'r', encoding='utf-8') as f:
                reader = list(csv.reader(f, delimiter='\t'))

            name = reader[0][1]
            author = reader[1][1]
            created = reader[2][1]
            modified = reader[3][1]
            version = reader[4][1]
            lat = float(reader[6][1])
            lon = float(reader[7][1])

            os.remove(filename)

            # ---- creating new project file ----

            if self.__projet:
                self.__projet.close()

            self.__projet = Projet(filename)
            self.__projet.name = name
            self.__projet.author = author
            self.__projet.created = created
            self.__projet.modified = modified
            self.__projet.version = version
            self.__projet.lat = lat
            self.__projet.lon = lon

            print('Projet converted to the new format successfully.')
        except:
            print('!Not working! Project file not valid.')
            raise
            return False

        # ---- Update UI ----

        self.project_display.setText(self.__projet.name)
        self.project_display.adjustSize()

        print('')
        print('---- PROJECT LOADED ----')
        print('')

        self.currentProjetChanged.emit(True)

        return True


# =============================================================================
# =============================================================================


class NewProject(QtGui.QDialog):
    # Dialog window to create a new WHAT project.

    NewProjectSignal = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(NewProject, self).__init__(parent)

        self.setWindowFlags(QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.setWindowTitle('New Project')
        self.setWindowIcon(IconDB().master)
        self.setFont(db.styleUI().font1)

        self.__initUI__()

    def __initUI__(self):

        # ---- Current Date ----

        now = datetime.now()
        now = (now.day, now.month, now.year, now.hour, now.minute)

        # ----------------------------------------------------- PROJECT INFO --

        # ---- Widgets ----

        self.name = QtGui.QLineEdit()
        self.author = QtGui.QLineEdit()
        self.date = QtGui.QLabel('%02d/%02d/%d  %02d:%02d' % now)
        self.createdby = QtGui.QLabel(db.software_version)

        # ---- Layout ----

        projet_info = QtGui.QGridLayout()

        row = 0
        projet_info.addWidget(QtGui.QLabel('Project Title :'), row, 0)
        projet_info.addWidget(self.name, row, 1)
        row += 1
        projet_info.addWidget(QtGui.QLabel('Author :'), row, 0)
        projet_info.addWidget(self.author, row, 1)
        row += 1
        projet_info.addWidget(QtGui.QLabel('Created :'), row, 0)
        projet_info.addWidget(self.date, row, 1)
        row += 1
        projet_info.addWidget(QtGui.QLabel('Software :'), row, 0)
        projet_info.addWidget(self.createdby, row, 1)

        projet_info.setSpacing(10)
        projet_info.setColumnStretch(1, 100)
        projet_info.setColumnMinimumWidth(1, 250)
        projet_info.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)

        # --------------------------------------------- LOCATION COORDINATES --

        locaCoord_title = QtGui.QLabel('<b>Project Location Coordinates:</b>')
        locaCoord_title.setAlignment(QtCore.Qt.AlignLeft)

        label_Lon2 = QtGui.QLabel('West')

        self.Lat_SpinBox = QtGui.QDoubleSpinBox()
        self.Lat_SpinBox.setAlignment(QtCore.Qt.AlignCenter)
        self.Lat_SpinBox.setSingleStep(0.1)
        self.Lat_SpinBox.setDecimals(3)
        self.Lat_SpinBox.setValue(0)
        self.Lat_SpinBox.setMinimum(0)
        self.Lat_SpinBox.setMaximum(180)
        self.Lat_SpinBox.setSuffix(u' °')

        self.Lon_SpinBox = QtGui.QDoubleSpinBox()
        self.Lon_SpinBox.setAlignment(QtCore.Qt.AlignCenter)
        self.Lon_SpinBox.setSingleStep(0.1)
        self.Lon_SpinBox.setDecimals(3)
        self.Lon_SpinBox.setValue(0)
        self.Lon_SpinBox.setMinimum(0)
        self.Lon_SpinBox.setMaximum(180)
        self.Lon_SpinBox.setSuffix(u' °')

        loc_coord = QtGui.QGridLayout()

        row = 0
        loc_coord.addWidget(locaCoord_title, row, 0, 1, 11)
        row += 1
        loc_coord.setColumnStretch(0, 100)
        loc_coord.addWidget(QtGui.QLabel('Latitude :'), row, 1)
        loc_coord.addWidget(self.Lat_SpinBox, row, 2)
        loc_coord.addWidget(QtGui.QLabel('North'), row, 3)
        loc_coord.setColumnStretch(4, 100)

        loc_coord.addWidget(myqt.VSep(), row, 5)
        loc_coord.setColumnStretch(6, 100)

        loc_coord.addWidget(QtGui.QLabel('Longitude :'), row, 7)
        loc_coord.addWidget(self.Lon_SpinBox, row, 8)
        loc_coord.addWidget(QtGui.QLabel('West'), row, 9)
        loc_coord.setColumnStretch(10, 100)

        loc_coord.setSpacing(10)
        loc_coord.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)

        # --------------------------------------------------------- Browse ----

        # ---- widgets ----

        save_in_folder = os.path.abspath(os.path.join('..', 'Projects'))

        directory_label = QtGui.QLabel('Save in Folder:')
        self.directory = QtGui.QLineEdit()
        self.directory.setReadOnly(True)
        self.directory.setText(save_in_folder)
        self.directory.setMinimumWidth(350)

        btn_browse = QtGui.QToolButton()
        btn_browse.setAutoRaise(True)
        btn_browse.setIcon(IconDB().openFolder)
        btn_browse.setIconSize(db.styleUI().iconSize2)
        btn_browse.setToolTip('Browse...')
        btn_browse.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_browse.clicked.connect(self.browse_saveIn_folder)

        browse = QtGui.QGridLayout()

        browse.addWidget(directory_label, 0, 0)
        browse.addWidget(self.directory, 0, 1)
        browse.addWidget(btn_browse, 0, 2)

        browse.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)
        browse.setColumnStretch(1, 100)
        browse.setSpacing(10)

        # ---------------------------------------------------------- Toolbar --

        # ---- widgets ----

        btn_save = QtGui.QPushButton(' Save')
        btn_save.setMinimumWidth(100)
        btn_save.clicked.connect(self.save_project)

        btn_cancel = QtGui.QPushButton(' Cancel')
        btn_cancel.setMinimumWidth(100)
        btn_cancel.clicked.connect(self.close)

        # ---- layout ----

        toolbar = QtGui.QGridLayout()

        toolbar.addWidget(btn_save, 0, 1)
        toolbar.addWidget(btn_cancel, 0, 2)

        toolbar.setSpacing(10)
        toolbar.setColumnStretch(0, 100)
        toolbar.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)

        # ------------------------------------------------------------- MAIN --

        main_layout = QtGui.QGridLayout(self)

        main_layout.addLayout(projet_info, 0, 0)
        main_layout.addWidget(myqt.HSep(), 1, 0)
        main_layout.addLayout(loc_coord, 2, 0)
        main_layout.addWidget(myqt.HSep(), 3, 0)
        main_layout.addLayout(browse, 4, 0)
        main_layout.addLayout(toolbar, 5, 0)

        main_layout.setVerticalSpacing(25)
        main_layout.setContentsMargins(15, 15, 15, 15)  # (L, T, R, B)

    # =========================================================================

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

        try:
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

            fname = os.path.join(dirname, '%s.what' % name)
            projet = Projet(fname, 'w')

            projet.name = self.name.text()
            projet.author = self.author.text()
            projet.created = self.date.text()
            projet.modified = self.date.text()
            projet.version = self.createdby.text()
            projet.lat = self.Lat_SpinBox.value()
            projet.lon = self.Lon_SpinBox.value()

            projet.close()

            print('Creating file %s.what' % name)
            print('---------------')

            self.close()
            self.NewProjectSignal.emit(fname)
        except:
            raise

    def browse_saveIn_folder(self):
        folder = QtGui.QFileDialog.getExistingDirectory(
                self, 'Save in Folder', '../Projects')

        if folder:
            self.directory.setText(folder)

    # =========================================================================

    def reset_UI(self):

        self.name.clear()
        self.author.clear()

        save_in_folder = os.path.abspath(os.path.join('..', 'Projects'))
        self.directory.setText(save_in_folder)

        now = datetime.now()
        now = (now.day, now.month, now.year, now.hour, now.minute)
        self.date = QtGui.QLabel('%02d/%02d/%d %02d:%02d' % now)

        self.Lat_SpinBox.setValue(0)
        self.Lon_SpinBox.setValue(0)

    def show(self):
        super(NewProject, self).show()
        self.raise_()

        qr = self.frameGeometry()
        if self.parentWidget():
            wp = self.parentWidget().frameGeometry().width()
            hp = self.parentWidget().frameGeometry().height()
            cp = self.parentWidget().mapToGlobal(QtCore.QPoint(wp/2., hp/2.))
        else:
            cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        self.setFixedSize(self.size())


# =============================================================================
# =============================================================================


if __name__ == '__main__':

    app = QtGui.QApplication(argv)

    pm = ProjetManager()
    pm.show()

    app.exec_()
