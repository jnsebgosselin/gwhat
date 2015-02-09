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

#---- THIRD PARTY IMPORTS ----

from PySide import QtGui, QtCore

#---- PERSONAL IMPORTS ----

import database as db


#===============================================================================
class NewProject(QtGui.QWidget):
#===============================================================================

    NewProjectSignal = QtCore.Signal(str)
    
    def __init__(self, software_version, parent=None):
        super(NewProject, self).__init__(parent)
        
        self.initUI(software_version)
        
    def initUI(self, software_version):
        
        # Use this screen to name your new WHAT project, select the location
        # for your new project, and select the type of project.
        
        #---- Databases ----
        
        iconDB = db.icons()
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
        
        #----------------------------------------------------- PROJECT INFO ----
        
        #---- WIDGETS ----
        
        name_label = QtGui.QLabel('Project Name:')
        self.name = QtGui.QLineEdit()
        
        author_label = QtGui.QLabel('Author:')
        self.author = QtGui.QLineEdit()
        
        date_label = QtGui.QLabel('Created:')        
        self.date = QtGui.QLabel('%02d / %02d / %d  %02d:%02d' % now)
        
        createdby_label = QtGui.QLabel('Software:')
        self.createdby = QtGui.QLabel(software_version)
        
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
        
        #--------------------------------------------- LOCATION COORDINATES ----
        
        locaCoord_title = QtGui.QLabel('<b>Project Location Coordinates:</b>')
        locaCoord_title.setAlignment(QtCore.Qt.AlignLeft)

        label_Lat = QtGui.QLabel('Latitude :')
        label_Lat2 = QtGui.QLabel('N')
        label_Lon = QtGui.QLabel('Longitude :')
        label_Lon2 = QtGui.QLabel('W')
        
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
        
        #--------------------------------------------------------- Toolbar ----
        
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
        
        #------------------------------------------------------------- MAIN ----
        
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
        
        self.setWindowTitle('New Project')
        self.setWindowIcon(iconDB.WHAT)
        self.setFont(StyleDB.font1) 
        
        #----------------------------------------------------------- EVENTS ----

        btn_save_project.clicked.connect(self.save_project)
        btn_cancel.clicked.connect(self.cancel_save_project)
        btn_browse.clicked.connect(self.browse_saveIn_folder)
   
    def save_project(self):
        
        project_name = self.name.text()
        if project_name == '' :
            print 'Please enter a valid Project name'
            return
        
        #---- project directory ----
        
        # If directory already exist, a number is added at the end within ().
        
        project_dir = self.directory.text() + '/' + project_name
        pathExists = os.path.exists(project_dir)
        
        count = 1
        while pathExists == True:
            project_dir = self.directory.text() + '/%s (%d)' % (project_name,
                                                                     count)
            pathExists = os.path.exists(project_dir)
            count += 1
            
        print '---------------'
        print 'Creating files and folder achitecture for the new project in:'
        print project_dir
        print
            
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
            
            filecontent = [['Project name:', project_name],
                           ['Author:', self.author.text()],
                           ['Created:', self.date.text()],
                           ['Modified:', self.date.text()],
                           ['Software:', self.createdby.text()],
                           ['', ''],
                           ['Latitude (DD N):', self.Lat_SpinBox.value()],
                           ['Longitude (DD W):', self.Lon_SpinBox.value()]
                           ]
            
            print 'Creating file %s.what' % project_name 
            
            with open(fname, 'wb') as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerows(filecontent)
                
        print '---------------'
        
        self.close()
        
        self.NewProjectSignal.emit(fname)
        
    def cancel_save_project(self):
        
        self.close()
        
    def browse_saveIn_folder(self):
        
        folder = QtGui.QFileDialog.getExistingDirectory(self, 
                                                        'Save in Folder',
                                                        '../Projects')
        
        if folder:
            self.directory.setText(folder)
            
    def clear_UI(self):
        
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
        
    
if __name__ == '__main__':
    
    app = QtGui.QApplication(argv)   
    instance_1 = NewProject('WHAT')
    instance_1.show()
    instance_1.setFixedSize(instance_1.size())
    
    app.exec_() 

    