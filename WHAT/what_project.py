# -*- coding: utf-8 -*-
"""
Copyright 2015 Jean-Sebastien Gosselin

email: jnsebgosselin@gmail.com

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
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

#---- STANDARD LIBRARY IMPORTS ----

from sys import argv
import platform
import os
import csv
from datetime import datetime
import re

#---- THIRD PARTY IMPORTS ----

from PySide import QtGui, QtCore

#---- PERSONAL IMPORTS ----

import database as db


#==============================================================================
class NewProject(QtGui.QDialog):
    """
    Dialog window to create a new WHAT project.
    """
#==============================================================================

    NewProjectSignal = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(NewProject, self).__init__(parent)

        self.setWindowFlags(QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.setWindowTitle('New Project')
        self.setWindowIcon(db.Icons().WHAT)
        self.setFont(db.styleUI().font1)

        self.initUI()

    def initUI(self):

        # Use this screen to name your new WHAT project, select the location
        # for your new project, and select the type of project.

        #---- Databases ----

        iconDB = db.Icons()
        StyleDB = db.styleUI()

        #---- Save In Folder ----

        if platform.system() == 'Windows':
            save_in_folder = '..\Projects'
        elif platform.system() == 'Linux':
            save_in_folder = '../Projects'

        save_in_folder = os.path.abspath(save_in_folder)

        #---- Current Date ----

        now = datetime.now()
        now = (now.day, now.month, now.year, now.hour, now.minute)

        #------------------------------------------------------ PROJECT INFO --

        #---- WIDGETS ----

        name_label = QtGui.QLabel('Project Title:')
        self.name = QtGui.QLineEdit()

        author_label = QtGui.QLabel('Author:')
        self.author = QtGui.QLineEdit()

        date_label = QtGui.QLabel('Created:')
        self.date = QtGui.QLabel('%02d / %02d / %d  %02d:%02d' % now)

        createdby_label = QtGui.QLabel('Software:')
        self.createdby = QtGui.QLabel(db.software_version)

        #---- GRID ----

        proINfo_widget = QtGui.QFrame()
        proInfo_grid = QtGui.QGridLayout()

        row = 0
        proInfo_grid.addWidget(name_label, row, 0)
        proInfo_grid.addWidget(self.name, row, 1)
        row += 1
        proInfo_grid.addWidget(author_label, row, 0)
        proInfo_grid.addWidget(self.author, row, 1)
        row += 1
        proInfo_grid.addWidget(date_label, row, 0)
        proInfo_grid.addWidget(self.date, row, 1)
        row += 1
        proInfo_grid.addWidget(createdby_label, row, 0)
        proInfo_grid.addWidget(self.createdby, row, 1)

        proInfo_grid.setSpacing(10)
        proInfo_grid.setColumnStretch(1, 100)
        proInfo_grid.setColumnMinimumWidth(1, 250)
        proInfo_grid.setContentsMargins(0, 0, 0, 0) # (L, T, R, B)

        proINfo_widget.setLayout(proInfo_grid)

        #---------------------------------------------- LOCATION COORDINATES --

        locaCoord_title = QtGui.QLabel('<b>Project Location Coordinates:</b>')
        locaCoord_title.setAlignment(QtCore.Qt.AlignLeft)

        label_Lat = QtGui.QLabel('Latitude :')
        label_Lat2 = QtGui.QLabel('North')
        label_Lon = QtGui.QLabel('Longitude :')
        label_Lon2 = QtGui.QLabel('West')

        self.Lat_SpinBox = QtGui.QDoubleSpinBox()
        self.Lat_SpinBox.setAlignment(QtCore.Qt.AlignCenter)
        self.Lat_SpinBox.setSingleStep(0.1)
        self.Lat_SpinBox.setValue(0)
        self.Lat_SpinBox.setMinimum(0)
        self.Lat_SpinBox.setMaximum(180)
        self.Lat_SpinBox.setSuffix(u' °')

        self.Lon_SpinBox = QtGui.QDoubleSpinBox()
        self.Lon_SpinBox.setAlignment(QtCore.Qt.AlignCenter)
        self.Lon_SpinBox.setSingleStep(0.1)
        self.Lon_SpinBox.setValue(0)
        self.Lon_SpinBox.setMinimum(0)
        self.Lon_SpinBox.setMaximum(180)
        self.Lon_SpinBox.setSuffix(u' °')

        VLine1 = QtGui.QFrame()
        VLine1.setFrameStyle(StyleDB.VLine)
        HLine1 = QtGui.QFrame()
        HLine1.setFrameStyle(StyleDB.HLine)
        HLine2 = QtGui.QFrame()
        HLine2.setFrameStyle(StyleDB.HLine)

        locaCoord_widget = QtGui.QFrame()
        locaCoord_grid = QtGui.QGridLayout()

        row = 0
        locaCoord_grid.addWidget(HLine1, row, 0, 1, 11)
        row += 1
        locaCoord_grid.addWidget(locaCoord_title, row, 0, 1, 11)
        row += 1
        locaCoord_grid.setColumnStretch(0, 100)
        locaCoord_grid.addWidget(label_Lat, row, 1)
        locaCoord_grid.addWidget(self.Lat_SpinBox, row, 2)
        locaCoord_grid.addWidget(label_Lat2, row, 3)
        locaCoord_grid.setColumnStretch(4, 100)
        locaCoord_grid.addWidget(VLine1, row, 5)
        locaCoord_grid.setColumnStretch(6, 100)
        locaCoord_grid.addWidget(label_Lon, row, 7)
        locaCoord_grid.addWidget(self.Lon_SpinBox, row, 8)
        locaCoord_grid.addWidget(label_Lon2, row, 9)
        locaCoord_grid.setColumnStretch(10, 100)
        row += 1
        locaCoord_grid.addWidget(HLine2, row, 0, 1, 11)

        locaCoord_grid.setSpacing(10)
        locaCoord_grid.setContentsMargins(0, 0, 0, 0) # (L, T, R, B)

        locaCoord_widget.setLayout(locaCoord_grid)

        #----------------------------------------------------------- Toolbar --

        btn_save_project = QtGui.QPushButton(' Save')
        btn_save_project.setIcon(iconDB.new_project)
        btn_save_project.setIconSize(StyleDB.iconSize2)
        btn_save_project.setMinimumWidth(100)

        btn_cancel = QtGui.QPushButton(' Cancel')
        btn_cancel.setIcon(iconDB.clear_search)
        btn_cancel.setIconSize(StyleDB.iconSize2)
        btn_cancel.setMinimumWidth(100)

        toolbar_widget = QtGui.QFrame()
        toolbar_grid = QtGui.QGridLayout()

        row = 0
        col = 1
        toolbar_grid.addWidget(btn_cancel, row, col)
        col += 1
        toolbar_grid.addWidget(btn_save_project, row, col)

        toolbar_grid.setSpacing(10)
        toolbar_grid.setColumnStretch(col+1, 100)
        toolbar_grid.setContentsMargins(0, 0, 0, 0) # (L, T, R, B)

        toolbar_widget.setLayout(toolbar_grid)

        #-------------------------------------------------------------- MAIN --

        directory_label = QtGui.QLabel('Save in Folder:')
        self.directory = QtGui.QLineEdit()
        self.directory.setReadOnly(True)
        self.directory.setText(save_in_folder)

        btn_browse = QtGui.QToolButton()
        btn_browse.setAutoRaise(True)
        btn_browse.setIcon(iconDB.openFolder)
        btn_browse.setIconSize(StyleDB.iconSize2)
        btn_browse.setToolTip('Browse...')
        btn_browse.setFocusPolicy(QtCore.Qt.NoFocus)

        newProject_grid = QtGui.QGridLayout()

        row = 0
        newProject_grid.addWidget(proINfo_widget, row, 0, 1, 3)
        row += 1
        newProject_grid.addWidget(locaCoord_widget, row, 0, 1, 3)
        row += 1
        newProject_grid.addWidget(directory_label, row, 0)
        newProject_grid.addWidget(self.directory, row, 1)
        newProject_grid.addWidget(btn_browse, row, 2)
        row += 1
        newProject_grid.addWidget(toolbar_widget, row, 0, 1, 2)

        newProject_grid.setVerticalSpacing(25)
        newProject_grid.setColumnMinimumWidth(1, 350)
        newProject_grid.setContentsMargins(15, 15, 15, 15) # (L, T, R, B)

        self.setLayout(newProject_grid)

        #---------------------------------------------------------- EVENTS ----

        btn_save_project.clicked.connect(self.save_project)
        btn_cancel.clicked.connect(self.close)
        btn_browse.clicked.connect(self.browse_saveIn_folder)

    def save_project(self):  # ================================================

        project_name = self.name.text()
        if project_name == '':
            print('Please enter a valid Project name')
            return

        #---- Project Directory Name ----

        # If directory already exist, a number is added at the end within ().

        project_dir = self.directory.text() + '/' + project_name
        pathExists = os.path.exists(project_dir)

        count = 1
        while pathExists == True:
            project_dir = self.directory.text() + '/%s (%d)' % (project_name,
                                                                count)
            pathExists = os.path.exists(project_dir)
            count += 1

        print('\n---------------')
        print('Creating files and folder achitecture for the new project in:')
        print(project_dir)
        print

        #---- Create Files and Folders ----

        try:

            os.makedirs(project_dir)

            #---- folder architecture ----

            if not os.path.exists(project_dir + '/Meteo/Raw'):
                os.makedirs(project_dir + '/Meteo/Raw')
            if not os.path.exists(project_dir + '/Meteo/Input'):
                os.makedirs(project_dir + '/Meteo/Input')
            if not os.path.exists(project_dir + '/Meteo/Output'):
                os.makedirs(project_dir + '/Meteo/Output')
            if not os.path.exists(project_dir + '/Water Levels'):
                os.makedirs(project_dir + '/Water Levels')

            #---- project.what ----

            fname = project_dir + '/%s.what' % project_name
            if not os.path.exists(fname):

                project_name = project_name
                author = self.author.text()

                filecontent = [['Project name:', project_name],
                               ['Author:', author],
                               ['Created:', self.date.text()],
                               ['Modified:', self.date.text()],
                               ['Software:', self.createdby.text()],
                               ['', ''],
                               ['Latitude (DD N):', self.Lat_SpinBox.value()],
                               ['Longitude (DD W):', self.Lon_SpinBox.value()]
                               ]

                print('Creating file %s.what' % project_name)

                with open(fname, 'w', encoding='utf-8') as f:
                    writer = csv.writer(f, delimiter='\t')
                    writer.writerows(filecontent)

            self.close()

            print('---------------')

            self.NewProjectSignal.emit(fname)

        except Exception as e:
            raise e
#            print('There was a problem creating the project. '
#                  'Project not saved.')
#            print('---------------')

    def browse_saveIn_folder(self):

        folder = QtGui.QFileDialog.getExistingDirectory(self,
                                                        'Save in Folder',
                                                        '../Projects')

        if folder:
            self.directory.setText(folder)

    def reset_UI(self):

        self.name.clear()
        self.author.clear()

        if platform.system() == 'Windows':
            save_in_folder = '..\Projects'
        elif platform.system() == 'Linux':
            save_in_folder = '../Projects'
        save_in_folder = os.path.abspath(save_in_folder)
        self.directory.setText(save_in_folder)

        now = datetime.now()
        now = (now.day, now.month, now.year, now.hour, now.minute)
        self.date = QtGui.QLabel('%02d / %02d / %d %02d:%02d' % now)

        self.Lat_SpinBox.setValue(0)
        self.Lon_SpinBox.setValue(0)

    def show(self): #================================================== show ==
        super(NewProject, self).show()
        self.raise_()

        # Adapted from:
        # http://zetcode.com/gui/pysidetutorial/firstprograms

        qr = self.frameGeometry()
        if self.parentWidget():
            print('coucou')
            wp = self.parentWidget().frameGeometry().width()
            hp = self.parentWidget().frameGeometry().height()
            cp = self.parentWidget().mapToGlobal(QtCore.QPoint(wp/2., hp/2.))
        else:
            cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        self.setFixedSize(self.size())


#===============================================================================
class OpenProject(QtGui.QDialog):
    """
    Dialog window to browse and select already existing WHAT project.
    """
#===============================================================================

    OpenProjectSignal = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(OpenProject, self).__init__(parent)

        self.home = os.path.abspath('../Projects')
        self.projectfile = []
        self.pathMemory = [self.home]
        self.memoryIndx = 0

        self.initUI()

    def initUI(self):

        iconDB = db.Icons()
        styleDB = db.styleUI()

        #--------------------------------------------------- WINDOW SETUP ----

        self.setWindowTitle('Open Project')
        self.setWindowIcon(iconDB.WHAT)
        self.setFont(styleDB.font1)

        #---------------------------------------------- File System Model ----

        self.model = SeFileSystemModel(self.home)

        #------------------------------------------------- Tree File View ----

        self.centralPanel =  QtGui.QListView()
        self.centralPanel.setModel(self.model)
        self.centralPanel.setRootIndex(self.model.index(self.home))

        self.leftPanel =  QtGui.QTreeView()
        self.leftPanel.setModel(self.model)
        self.leftPanel.setColumnHidden(1, True)
        self.leftPanel.setColumnHidden(2, True)
        self.leftPanel.setColumnHidden(3, True)
        self.leftPanel.setHeaderHidden(True)
        self.leftPanel.setRootIndex(self.model.index(''))

        self.centralPanel.setMinimumWidth(350)

        #---- Events ----

        # http://stackoverflow.com/questions/4511908/
        # connect-double-click-event-of-qlistview-with-method-in-pyqt4
        self.centralPanel.doubleClicked.connect(self.item_ddclick)

        # http://stackoverflow.com/questions/23993895/
        # python-pyqt-qtreeview-example-selection

        signal = 'selectionChanged(QItemSelection, QItemSelection)'
        QtCore.QObject.connect(self.centralPanel.selectionModel(),
                               QtCore.SIGNAL(signal),
                               self.new_item_selected)

        #------------------------------------------------ Central QSplitter ----

        self.project_details = QtGui.QTextEdit()
        self.project_details.setReadOnly(True)
        linewrapmode = QtGui.QTextEdit.LineWrapMode.NoWrap
        self.project_details.setLineWrapMode(linewrapmode)
        self.project_details.setMaximumWidth(250)

        splitter = QtGui.QSplitter()

        splitter.addWidget(self.leftPanel)
        splitter.addWidget(self.centralPanel)
        splitter.addWidget(self.project_details)

#        splitter.setStretchFactor(0, 100)
        splitter.setCollapsible(1, False)

        #------------------------------------------------------ TOP TOOLBAR ----

        #---- WIDGETS ----

        self.btn_goPrevious = QtGui.QToolButton()
        self.btn_goPrevious.setAutoRaise(True)
        self.btn_goPrevious.setIcon(iconDB.go_previous)
        self.btn_goPrevious.setToolTip('Go to the previous visited location')
        self.btn_goPrevious.setIconSize(styleDB.iconSize2)
        self.btn_goPrevious.setEnabled(False)

        self.btn_goNext = QtGui.QToolButton()
        self.btn_goNext.setAutoRaise(True)
        self.btn_goNext.setIcon(iconDB.go_next)
        self.btn_goNext.setToolTip('Go to the next visited location')
        self.btn_goNext.setIconSize(styleDB.iconSize2)
        self.btn_goNext.setEnabled(False)

        self.btn_goUp = QtGui.QToolButton()
        self.btn_goUp.setAutoRaise(True)
        self.btn_goUp.setIcon(iconDB.go_up)
        self.btn_goUp.setToolTip('Go up one directory')
        self.btn_goUp.setIconSize(styleDB.iconSize2)

        btn_goHome = QtGui.QToolButton()
        btn_goHome.setAutoRaise(True)
        btn_goHome.setIcon(iconDB.home)
        btn_goHome.setToolTip('Go to <i>Projects</i> folder')
        btn_goHome.setIconSize(styleDB.iconSize2)

#        directory_label = QtGui.QLabel('Look in:')

        self.dir_menu = QtGui.QComboBox()
        self.populate_dir_menu(self.home)

        #---- LAYOUT ----

        topTbar_widget = QtGui.QFrame()
        topTbar_grid = QtGui.QGridLayout()

        row = 0
        col = 0
        topTbar_grid.addWidget(self.btn_goPrevious, row, col)
        col += 1
        topTbar_grid.addWidget(self.btn_goNext, row, col)
        col += 1
        topTbar_grid.addWidget(self.btn_goUp, row, col)
        col += 1
        topTbar_grid.addWidget(btn_goHome, row, col)
        col += 1
        topTbar_grid.setColumnMinimumWidth(col, 15)
        col += 1
        topTbar_grid.addWidget(self.dir_menu, row, col)

        topTbar_grid.setSpacing(0)
        topTbar_grid.setColumnStretch(col, 100)
        topTbar_grid.setContentsMargins(0, 0, 0, 0) # (L, T, R, B)

        topTbar_widget.setLayout(topTbar_grid)

        #--------------------------------------------------- BOTTOM TOOLBAR ----

        btn_open_project = QtGui.QPushButton(' Open')
        btn_open_project.setIcon(iconDB.open_project)
        btn_open_project.setIconSize(styleDB.iconSize2)
        btn_open_project.setMinimumWidth(100)

        btn_cancel = QtGui.QPushButton(' Cancel')
        btn_cancel.setIcon(iconDB.clear_search)
        btn_cancel.setIconSize(styleDB.iconSize2)
        btn_cancel.setMinimumWidth(100)

        toolbar_widget = QtGui.QFrame()
        toolbar_grid = QtGui.QGridLayout()

        row = 0
        col = 1
        toolbar_grid.addWidget(btn_cancel, row, col)
        col += 1
        toolbar_grid.addWidget(btn_open_project, row, col)

        toolbar_grid.setSpacing(5)
        toolbar_grid.setColumnStretch(col+1, 100)
        toolbar_grid.setContentsMargins(0, 0, 0, 0) # (L, T, R, B)

        toolbar_widget.setLayout(toolbar_grid)

        #------------------------------------------------------ MAIN LAYOUT ----

        projectname_label = QtGui.QLabel('Project Name:')
        self.projectname_display = QtGui.QLineEdit()
        self.projectname_display.setReadOnly(True)

        main_grid = QtGui.QGridLayout()

        row = 0
        main_grid.addWidget(topTbar_widget, row, 0, 1, 2)
        row += 1
        main_grid.addWidget(splitter, row, 0, 1, 2)
        row += 1
        main_grid.addWidget(projectname_label, row, 0)
        main_grid.addWidget(self.projectname_display, row, 1)
        row += 1
        main_grid.addWidget(toolbar_widget, row, 0, 1, 2)

        main_grid.setVerticalSpacing(10)
#        main_grid.setColumnMinimumWidth(1, 350)
        main_grid.setRowMinimumHeight(1, 350)
        main_grid.setRowStretch(1, 100)
        main_grid.setColumnStretch(1, 100)
        main_grid.setContentsMargins(15, 15, 15, 15) # (L, T, R, B)

        self.setLayout(main_grid)

        #----------------------------------------------------------- EVENTS ----

        self.btn_goPrevious.clicked.connect(self.goPrevious)
        self.btn_goNext.clicked.connect(self.goNext)
        self.btn_goUp.clicked.connect(self.goUP)
        btn_goHome.clicked.connect(self.goHOME)
        self.dir_menu.currentIndexChanged.connect(self.dir_menu_changed)
        btn_open_project.clicked.connect(self.open_project)
        btn_cancel.clicked.connect(self.cancel_open_project)

    def open_project(self):

        if self.projectfile:
            print('Project Select. Sending signal to load the project.')
            self.OpenProjectSignal.emit(self.projectfile)
            self.close()

    def cancel_open_project(self):

        self.close()

    def goUP(self):

        filepath = self.dir_menu.currentText()
        filepath2 = os.path.dirname(filepath)

#        Qdir = QtCore.QDir(self.home)
#        print(Qdir.path())
#        import win32api
#        for i in range(len(Qdir.drives())):
#            print(Qdir.drives()[i].path())
#            print(win32api.GetVolumeInformation(Qdir.drives()[i].path()))
#        print Qdir.homePath()

        if filepath == filepath2:
            print('Already to the top buddy...')
            return

        self.update_directory(filepath2)

    def goPrevious(self):

        self.memoryIndx = max(self.memoryIndx - 1, 0)

        print(self.memoryIndx)

        dirname = self.pathMemory[self.memoryIndx]

        self.populate_dir_menu(dirname)
        self.centralPanel.setRootIndex(self.model.index(dirname))

        self.btn_goNext.setEnabled(True)
        if self.memoryIndx == 0:
            self.btn_goPrevious.setEnabled(False)

    def goNext(self):

        self.memoryIndx = min(self.memoryIndx + 1, len(self.pathMemory) - 1)

        print(self.memoryIndx)

        dirname = self.pathMemory[self.memoryIndx]

        self.populate_dir_menu(dirname)
        self.centralPanel.setRootIndex(self.model.index(dirname))

        self.btn_goPrevious.setEnabled(True)
        if self.memoryIndx == len(self.pathMemory) - 1:
            self.btn_goNext.setEnabled(False)

    def goHOME(self):

        if self.dir_menu.currentText() == self.home:
            print('Already at home men...')
            return

        filepath = self.home
        self.update_directory(filepath)

    def item_ddclick(self, signal):

        print('ddclick well received')

        filepath = self.model.filePath(signal)

        if not os.path.isfile(filepath):

            self.update_directory(filepath)

        else:

            self.open_project()

    def dir_menu_changed(self):

        if self.NOMENU == True:

            filepath = self.dir_menu.currentText()
            self.update_directory(filepath)

    def new_item_selected(self, selected, deselected):

        print('selection changed')

        itemIndx = selected.indexes()

        if len(itemIndx) == 0:
            self.projectfile = []
            self.projectname_display.clear()
            self.project_details.clear()
            return

        filepath = self.model.filePath(itemIndx[0])

        if os.path.splitext(filepath)[-1] == '.what':

            self.projectfile = filepath
            self.projectname_display.setText(os.path.basename(filepath))

            #---- Reading Project File ----

            reader = open(filepath, 'rb')
            reader = csv.reader(reader, delimiter='\t')
            reader = list(reader)

#            name = reader[0][1].decode('utf-8')
#            author = reader[1][1].decode('utf-8')
#            lat = float(reader[6][1])
#            lon = float(reader[7][1])

#            table = '''<table border="0" cellpadding="1" cellspacing="0"
#                       align="left">'''
#
#            for i in range(len(reader)):
#                self.project_details.append
#
#                table += '<tr>' # + <td width=10></td>'
#                table +=   '<td align="left">%s</td>' % reader[i][0].decode('utf-8')
##                table +=   '<td align="left">&nbsp;:&nbsp;</td>'
#                table +=   '<td align="left">%s</td>' % reader[i][1].decode('utf-8')
#                table += '</tr>'
#
#            table +=  '</table>'
#
#            self.project_details.clear()
#            self.project_details.setText(table)

            self.project_details.clear()

            header = ['Project: ', 'Author: ', 'Created: ', 'Modified: ',
                       'Software: ', '----------', 'Latitude: ', 'Longitude: ']

            table1 = '''<table border="0" cellpadding="1" cellspacing="0"
                        align="left">'''
            for i in range(len(header)):

                table1 += '<tr>' # + <td width=10></td>'
                table1 +=   '<td align="left">%s</td>' % header[i]
                table1 +=   '<td align="left">%s</td>' % reader[i][1].decode('utf-8')
                table1 += '</tr>'

            table1 += '</table>'

#            table2 = '''<table border="0" cellpadding="1" cellspacing="0"
#                        align="left">'''
#            for i in range(6, 8):
#
#                table2 += '<tr>' # + <td width=10></td>'
#                table2 +=   '<td align="left">%s</td>' % header[i]
#                table2 +=   '<td align="left">%s</td>' % reader[i][1].decode('utf-8')
#                table2 += '</tr>'
#
#            table2 += '</table>'

            self.project_details.append(table1)
#            self.project_details.append(table2)


#            for i in range(len(reader)):
#                info = reader[i][1].decode('utf-8')
#                self.project_details.append('%s%s' % (header[i], info))

        else:

            self.projectfile = []
            self.projectname_display.clear()
            self.project_details.clear()

    def update_directory(self, filepath):

        self.populate_dir_menu(filepath)
        self.centralPanel.setRootIndex(self.model.index(filepath))

        self.memoryIndx += 1
        self.pathMemory = self.pathMemory[:self.memoryIndx]
        self.pathMemory.append(filepath)
        self.btn_goPrevious.setEnabled(True)
        self.btn_goNext.setEnabled(False)

    def populate_dir_menu(self, path):

        self.NOMENU = False

        if os.path.isfile(path):
            dirlist = [os.path.dirname(path)]
        else:
            dirlist = [path]

        i = 0
        while 1:
            path = os.path.dirname(dirlist[i])
            if path == dirlist[i] or i>10:
                 break
            else:
                i += 1
                dirlist.append(path)

        self.dir_menu.clear()
        self.dir_menu.addItems(dirlist)

        self.NOMENU = True

class SeFileSystemModel(QtGui.QFileSystemModel):

    # http://stackoverflow.com/questions/18106074/
    # python-pyside-own-qfileiconprovider-implementation-fails-
    # with-no-exceptions-thr

    def __init__(self, directory):

        QtGui.QFileSystemModel.__init__(self)
#        self.fileEndPattern = re.compile("^.*\.(\w{2,4})$")

        self.setRootPath(directory)
        self.setNameFilters(['*.what'])
        self.setNameFilterDisables(False)
        self.setReadOnly(True)

    def data(self, index, role):

        iconDB = db.Icons()

        if index.column() == 0 and role == QtCore.Qt.DecorationRole:
            if os.path.splitext(index.data())[-1] == '.what':
                return iconDB.WHAT
            elif os.path.splitext(index.data())[-1] == '':
                pass
#                return iconDB.openFolder

        return super(SeFileSystemModel, self).data(index, role)


if __name__ == '__main__':

    app = QtGui.QApplication(argv)

    instance_2 = OpenProject()
    instance_2.show()

    instance_1 = NewProject()
    instance_1.show()

    app.exec_()

