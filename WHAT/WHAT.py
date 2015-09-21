# -*- coding: utf-8 -*-
"""
Copyright 2014-2015 Jean-Sebastien Gosselin
email: jnsebgosselin@gmail.com

WHAT is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it /will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
# Source: http://www.gnu.org/licenses/gpl-howto.html

# It is often said when developing interfaces that you need to fail fast,
# and iterate often. When creating a UI, you will make mistakes. Just keep
# moving forward, and remember to keep your UI out of the way.

# http://blog.teamtreehouse.com/10-user-interface-design-fundamentals

#---- STANDARD LIBRARY IMPORTS ----

import platform
import csv
import sys
from time import ctime
from os import makedirs, path

#---- THIRD PARTY IMPORTS ----

from PySide import QtGui, QtCore

#---- PERSONAL IMPORTS ----

import database as db
import MyQWidget
import what_project
import HydroPrint
import dwnld_weather_data
import fill_weather_data

from about_WHAT import AboutWhat

#---- DATABASES ----

labelDB = []
iconDB = []
styleDB = []
ttipDB = []
headerDB = []

# The code is segmented in two main sections: the GUI section and the
# WORKER sections.
#
# The GUI is written with the toolbox Qt using the PySide binding.
# 
# The WORKER section handles all the calculations and data manipulations of
# the program.

################################################################################
#                                                                           
#                            @SECTION GUI                               
#                                                                          
################################################################################

# The GUI is composed of a Tab area, a console terminal, and a 
# progress bar. The Tab area is where the user interacts with the
# program. It is divided in four tabs: 
#
#      (1) the "Download Data" tab, 
#      (2) the "Fill Data" tab,
#      (3) The "Hydrograph" tab
#      (4) The "About" tab.
#
# The "Download Data" tab handles the downloading of raw data files
# from http://climate.weather.gc.ca/ and the formating and concatenation
# of these raw data files into a single file.
#
# The "Fill Data" tab handles the missing data completion process.
#
# The "Hydrograph" tab is where it is possible to plot the well hydrograph
# along with the meteorological data.
#
# The "About" tabs handles Copyright, Licensing and external links information
#
# The console terminal and the progress bar are shared by all the tabs of the 
# Tab area and are only used to give information to the user about the 
# state and activities of the main program.

#==============================================================================
class MainWindow(QtGui.QMainWindow):
        
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
#==============================================================================
        
        self.initUI()
        
    def initUI(self): #========================================================
        """
        A generic widget is first set as the central widget of the
        MainWindow. Then, a QGridLayout is applied to this central
        widget. Two widgets are then added to the central widget's grid:
        (1) a Qsplitter widget on top and (2) a QProgressBar on the
        bottom.
        
        Two additional widgets are then added to the Qsplitter widget:
        (1) a QTabWidget and (2) a QTextEdit widget that is the console 
        terminal that was discussed above.
    
        The QTabWidget is composed of four tabs. Each
        tab is defined within its own class that are child classes of the
        MainWindow class. The layout of each tab is handled with a
        QGridLayout.
        """
        
        #--------------------------------------------------- CLASS INSTANCES --
        
        self.projectInfo = MyProject(self)
        self.whatPref = WHATPref(self)
        self.new_project_window = what_project.NewProject(db.software_version)
#        self.open_project_window = what_project.OpenProject()
        
        #------------------------------------------------------- PREFERENCES --
                
        self.whatPref.load_pref_file()
        
        language = self.whatPref.language
        
        self.projectfile = self.whatPref.projectfile
        self.projectdir = path.dirname(self.projectfile)
        
        style = 'Regular'
        size = self.whatPref.fontsize_general
        
        family = db.styleUI().fontfamily
        
        fontSS = ( "font-style: %s;" % style +
                   "font-size: %s;"  % size  +
                   "font-family: %s;" % family)
                    
        self.setStyleSheet("QWidget{%s}" % fontSS)
                                    
        #--------------------------------------------------------- DATABASES --
        
        # http://stackoverflow.com/questions/423379/
        # using-global-variables-in-a-function-other-
        # than-the-one-that-created-them
        
        global labelDB
        labelDB = db.labels(language)
        global iconDB
        iconDB = db.Icons()
        global styleDB
        styleDB = db.styleUI()
        global ttipDB
        ttipDB = db.Tooltips(language)
        global headerDB
        headerDB = db.FileHeaders()
        
        #------------------------------------------------- MAIN WINDOW SETUP --

#        self.setMinimumWidth(1250)
        self.setWindowTitle(db.software_version)
        self.setWindowIcon(iconDB.WHAT)
#        self.setFont(styleDB.font1)                
                        
        #------------------------------------------------------ MAIN CONSOLE --
        
        self.main_console = QtGui.QTextEdit()        
        self.main_console.setReadOnly(True)
        self.main_console.setLineWrapMode(QtGui.QTextEdit.LineWrapMode.NoWrap)
#        self.main_console.setFont(styleDB.font_console)
        
        size = self.whatPref.fontsize_console
        fontSS = ( "font-style: %s;" % style +
                    "font-size: %s;"  % size  +
                    "font-family: %s;" % family)
        self.main_console.setStyleSheet("QWidget{%s}" % fontSS)
        
        self.write2console('''<font color=black>Thanks for using %s.
        </font>''' % db.software_version)
        self.write2console(
        '''<font color=black>Please report any bug or wishful feature to 
             Jean-S&eacute;bastien Gosselin at jnsebgosselin@gmail.com.
           </font>''')
           
        #----------------------------------------------- PROJECT MENU BAR ----
                        
        project_label = QtGui.QLabel('Project :')
        project_label.setAlignment(QtCore.Qt.AlignCenter)
        
        self.project_display = QtGui.QPushButton()
        self.project_display.setFocusPolicy(QtCore.Qt.NoFocus)
        self.project_display.setFont(styleDB.font_menubar)
        self.project_display.setMinimumWidth(100)
        
        self.btn_new_project = QtGui.QToolButton()
        self.btn_new_project.setAutoRaise(True)
        self.btn_new_project.setIcon(iconDB.new_project)
        self.btn_new_project.setToolTip(ttipDB.new_project)
        self.btn_new_project.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btn_new_project.setIconSize(styleDB.iconSize2)
                          
        self.menubar_widget = QtGui.QWidget()
        subgrid_menubar = QtGui.QGridLayout()
        
        row = 0
        col = 0
        subgrid_menubar.addWidget(project_label, row, col)
        col += 1
        subgrid_menubar.addWidget(self.project_display, row, col)
        col += 1
        subgrid_menubar.addWidget(self.btn_new_project, row, col)
        
        subgrid_menubar.setSpacing(3)
        subgrid_menubar.setContentsMargins(0, 0, 0, 5) # [L, T, R, B] 
        subgrid_menubar.setColumnStretch(1, 500)
        subgrid_menubar.setRowMinimumHeight(0, 28)
        
        self.menubar_widget.setLayout(subgrid_menubar)
        
        size = self.whatPref.fontsize_menubar
        fontSS = ( "font-style: %s;" % style +
                    "font-size: %s;"  % size  +
                    "font-family: %s;" % family)
        self.menubar_widget.setStyleSheet("QWidget{%s}" % fontSS)
        
        #----------------------------------------------------- TAB WIDGET ----
           
        Tab_widget = QtGui.QTabWidget()
        
        #---- Custom TabBar Height ----
        
        # http://stackoverflow.com/questions/12428917/
        # pyqt4-set-size-of-the-tab-bar-in-qtabwidget
        
        class TabBar(QtGui.QTabBar):

           def tabSizeHint(self, index):
               width = QtGui.QTabBar.tabSizeHint(self, index).width()
               return QtCore.QSize(width, 32)
        tab_bar = TabBar()       
        Tab_widget.setTabBar(tab_bar)
        
        #---- download weather data ----
        
        self.tab_dwnld_data = dwnld_weather_data.dwnldWeather(self)
        self.tab_dwnld_data.set_workdir(self.projectdir)
        
        #---- gapfill weather data ----
        
        self.tab_fill_weather_data = fill_weather_data.GapFillWeather(self)
        self.tab_fill_weather_data.set_workdir(self.projectdir)
        
        #---- hydrograph ----
                
        self.tab_hydrograph = HydroPrint.HydroprintGUI(self)
        self.tab_hydrograph.set_workdir(self.projectdir)
        
        #---- about ----
        
        tab_about = AboutWhat(self)
        
        #---- TABS ASSEMBLY ----
        
        Tab_widget.addTab(self.tab_dwnld_data, labelDB.TAB1)        
        Tab_widget.addTab(self.tab_fill_weather_data, labelDB.TAB2) 
        Tab_widget.addTab(self.tab_hydrograph, labelDB.TAB3) 
        Tab_widget.addTab(tab_about, labelDB.TAB4)
        
        Tab_widget.setCornerWidget(self.menubar_widget)
        
        #------------------------------------------------ SPLITTER WIDGET ----
                
        splitter = QtGui.QSplitter(self)
        splitter.setOrientation(QtCore.Qt.Vertical)
        
        splitter.addWidget(Tab_widget)
        splitter.addWidget(self.main_console)
        
        splitter.setCollapsible(0, True)
        splitter.setStretchFactor(0, 100)                
        splitter.setSizes([100, 1]) # Forces initially the main_console to its
                                    # minimal height.       
       
        #------------------------------------------------------ MAIN GRID ----
        
        main_widget = QtGui.QWidget()
        self.setCentralWidget(main_widget)        
        
        mainGrid = QtGui.QGridLayout()
        
        row = 0
        mainGrid.addWidget(splitter, row, 0)
        row += 1
        mainGrid.addWidget(self.tab_fill_weather_data.pbar, row, 0)
        row += 1
        mainGrid.addWidget(self.tab_dwnld_data.pbar, row, 0)
        
        mainGrid.setSpacing(10)
        main_widget.setLayout(mainGrid)
        
        #--------------------------------------------------------- EVENTS ----
        
        self.btn_new_project.clicked.connect(self.show_new_project)
        self.project_display.clicked.connect(self.open_project)
        self.new_project_window.NewProjectSignal.connect(self.load_project)
#        self.open_project_window.OpenProjectSignal.connect(self.load_project) 

        #---- Console Signal Piping ----
        
        issuer = self.tab_dwnld_data
        issuer.ConsoleSignal.connect(self.write2console)  

        issuer = self.tab_dwnld_data.search4stations
        issuer.ConsoleSignal.connect(self.write2console)

        issuer =  self.tab_dwnld_data.dwnl_raw_datafiles 
        issuer.ConsoleSignal.connect(self.write2console)  

        issuer = self.tab_fill_weather_data
        issuer.ConsoleSignal.connect(self.write2console)

        issuer = self.tab_fill_weather_data.fillworker
        issuer.ConsoleSignal.connect(self.write2console)  
        
        issuer = self.tab_hydrograph
        issuer.ConsoleSignal.connect(self.write2console)                                                      
        
        #-------------------------------------------------- MESSAGE BOXES ----
       
        self.msgError = MyQWidget.MyQErrorMessageBox()
                   
        #----------------------------------------------------------- SHOW ----
            
        self.show()
        
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
        #----------------------------------------------- CHECK IF PROJECT ----
        
        isProjectExists = self.check_project()
        
        if isProjectExists:

            self.load_project(self.projectfile)
            
        else:
            
            self.tab_dwnld_data.setEnabled(False)    
            self.tab_fill_weather_data.setEnabled(False)     
            self.tab_hydrograph.setEnabled(False)
            
            msgtxt = '''
                     <b>Unable to read the project file.<br><br>
                     "%s" does not exist.<br><br> Please open an existing
                     project or create a new one.<b>
                     ''' % self.projectfile
            
            self.msgError.setText(msgtxt)
            self.msgError.exec_()
                
      
    def write2console(self, console_text): #=============== Write To Console ==
        
        '''
        This function is the bottle neck through which all messages writen
        in the console must go through.
        '''
            
        textime = '<font color=black>[%s] </font>' % ctime()[4:-8]
        self.main_console.append(textime + console_text)
    
        
    def show_new_project(self): #=============================== New Project ==
    
        #-- Center Widget to Main Window --
        
        # Adapted from:
        # http://zetcode.com/gui/pysidetutorial/firstprograms
                        
        self.new_project_window.clear_UI()
        
        qr = self.new_project_window.frameGeometry()
        cp = self.frameGeometry().center()
        qr.moveCenter(cp)
        self.new_project_window.move(qr.topLeft())
        
        self.new_project_window.setModal(True)
        self.new_project_window.show()
        self.new_project_window.setFixedSize(self.new_project_window.size())
            
    
    def open_project(self): #=================================================
        
        '''
        "open_project" is called by the event "self.project_display.clicked".
        It allows the user to open an already existing project.
        '''
        
#        qr = self.open_project_window.frameGeometry()
#        cp = self.frameGeometry().center()
#        qr.moveCenter(cp)
#        self.open_project_window.move(qr.topLeft())
#        
#        self.open_project_window.setModal(True)
#        self.open_project_window.show()
#        self.open_project_window.setFixedSize(self.open_project_window.size())
        
        #----------------------------------------- Custom File Dialog (1) ----
        
#        self.dialog = QtGui.QFileDialog()
#        print(self.dialog.sidebarUrls())
#        self.dialog.show()
        
#        self.dialog.setDirectory(directory)
#        self.dialog.setNameFilters(['*.what'])
#        self.dialog.setLabelText(QtGui.QFileDialog.FileName,'Open Project')
#        self.dialog.setOptions(QtGui.QFileDialog.ReadOnly)
#        self.dialog.setWindowTitle('Open Project')
#        self.dialog.setWindowIcon(iconDB.WHAT)
#        self.dialog.setFont(styleDB.font1)
#        self.dialog.setViewMode(QtGui.QFileDialog.List)
#        
#        self.dialog.fileSelected.connect(self.new_project_created)
#        
#        self.dialog.exec_()
       
        #----------------------------------------------------- Stock Dialog ----
       
        directory = path.abspath('../Projects')

        filename, _ = QtGui.QFileDialog.getOpenFileName(
                                      self, 'Open Project', directory, '*.what')
                                   
        if filename:

            self.projectfile = filename                        
            self.load_project(filename)
            
    #-------------------------------------------------------------------------
    def load_project(self, filename):
        '''
        This method is called either on startup during <initUI> or when a new
        project is chosen with <open_project>.        
        '''
    #-------------------------------------------------------------------------
        
        self.projectfile = filename 
        
        print('')
        print('---- LOADING PROJECT... ----')
        print('')
        print('Loading "%s"' % path.relpath(self.projectfile))
        
        self.projectdir = path.dirname(self.projectfile)
        
        #----Update WHAT.pref file ----
            
        self.whatPref.projectfile = self.projectfile
        self.whatPref.save_pref_file()
        
        #---- Check Project ----
        
        self.check_project()
        
        #---- Load Project Info ----
        
        self.projectInfo.load_project_info(self.projectfile)
        
        #---- Update UI ----
        
        self.tab_dwnld_data.setEnabled(True)    
        self.tab_fill_weather_data.setEnabled(True)     
        self.tab_hydrograph.setEnabled(True)
        
        self.project_display.setText(self.projectInfo.name)
        self.project_display.adjustSize()
            
        #---- Load Weather Input Files ----
        
        self.tab_fill_weather_data.load_data_dir_content()
        
        #-------------------------------------------- Update child widgets ----
        
        #---- dwnld_weather_data ----
        
        self.tab_dwnld_data.set_workdir(self.projectdir)
        self.tab_dwnld_data.search4stations.lat_spinBox.setValue(
                                                           self.projectInfo.lat)
                                                           
        self.tab_dwnld_data.search4stations.lon_spinBox.setValue(
                                                           self.projectInfo.lon)
                                                           
        #---- fill_weather_data ----
                                                           
        self.tab_fill_weather_data.set_workdir(self.projectdir)
        
        #---- hydrograph ----
        
        self.tab_hydrograph.set_workdir(self.projectdir)
        
        print('')
        print('---- PROJECT LOADED ----')
        print('')
      
    #-------------------------------------------------------------------------
    def check_project(self):
        """
        Check if all files and folders associated with the .what file are
        presents in the project folder. If some files or folders are missing,
        the program will automatically generate new ones.
        
        If the project.what file does not exist anymore, it returns a False
        answer, which should tell the code on the UI side to deactivate the  UI.
        
        This method should be run at the start of every method that needs to
        interact with resource file of the current project.
        """
    #-------------------------------------------------------------------------
        
        print('Checking project files and folders integrity')
        
        print(self.projectfile)
        if not path.exists(self.projectfile):
            print('Project file does not exist.')
            return False
            
        #---- System project folder organization ----
       
        if not path.exists(self.projectdir + '/Meteo/Raw'):
            makedirs(self.projectdir + '/Meteo/Raw')
        if not path.exists(self.projectdir + '/Meteo/Input'):
            makedirs(self.projectdir + '/Meteo/Input')
        if not path.exists(self.projectdir + '/Meteo/Output'):
            makedirs(self.projectdir + '/Meteo/Output')
        if not path.exists(self.projectdir + '/Water Levels'):
            makedirs(self.projectdir + '/Water Levels')
                
        return True
    
    def closeEvent(self,event): 
        event.accept()
        

#=============================================================================    
class WHATPref():
    """
    This class contains all the preferences relative to the WHAT interface,
    including:
    
    projectfile: It is a memory variable. It indicates upon launch to the 
                 program what was the project that was opened when last time the
                 program was closed.
                
    language: Language in which the GUI is displayed (not the labels of graphs).
    
    full_error_analysis: Option that enable when equal to 1 the error analysis
                         of the missing weather data routine. This option is
                         experimental, that is why it has not been added to the
                         UI yet.
    """
#===============================================================================

    
    def __init__(self, parent=None): #==========================================
     
        if platform.system() == 'Windows':
            self.projectfile = '..\Projects\Example\Example.what'
        elif platform.system() == 'Linux':
            self.projectfile = '../Projects/Example/Example.what'
            
        self.language = 'English'
        
        self.full_error_analysis = 0
        self.fontsize_general = '14px'
        self.fontsize_console = '10px'
        self.fontsize_menubar = '12px'
    
    def save_pref_file(self): #=================================================
            
        projectfile = path.relpath(self.projectfile).encode('utf-8')
        
        fcontent = [['Project File:', projectfile],
                    ['Language:', self.language],
                    ['Full Error Analysis:', self.full_error_analysis],
                    ['Font-Size-General:', self.fontsize_general],
                    ['Font-Size-Console:', self.fontsize_console],
                    ['Font-Size-Menubar:', self.fontsize_menubar]]
       
        with open('WHAT.pref', 'wb') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(fcontent)
    
           
    def load_pref_file(self): #===============================================
            
        if not path.exists('WHAT.pref'):
            
            # Default values will be kept and a new .pref file will be
            # generated
            
            print('No "WHAT.pref" file found. A new one has been created.')
        
            self.save_pref_file()
        
        else:
            
            with open('WHAT.pref', 'rb') as f:
                reader = list(csv.reader(f, delimiter='\t'))
            
            self.projectfile = reader[0][1].decode('utf-8')
            if platform.system() == 'Linux':
                self.projectfile = self.projectfile.replace('\\', '/')
                        
            self.language = reader[1][1]
            
            try:
                self.full_error_analysis = int(reader[2][1])
            except:
                self.full_error_analysis = 0
            try:
                self.fontsize_general = reader[3][1]
            except:
                pass # keep default value
            try:
                self.fontsize_console = reader[4][1]
            except:
                pass # keep default value
            try:
                self.fontsize_menubar = reader[5][1]
            except:
                pass # keep default value
                        
            print('self.full_error_analysis = %d' % self.full_error_analysis)
            print
        

#==============================================================================                
class MyProject():
    """
    This class contains all the info and utilities to manage the current 
    active project.
    """
#==============================================================================

    
    def __init__(self, parent=None): #=========================================
        
        self.name = ''
        self.lat = 0
        self.lon = 0
        
    
    def load_project_info(self, projectfile): #================================
            
        print('Loading project info')
        
        with open(projectfile, 'rb') as f:
            reader = list(csv.reader(f, delimiter='\t'))
            
        self.name = reader[0][1].decode('utf-8')
        self.lat = float(reader[6][1])
        self.lon = float(reader[7][1])
        
       
################################################################################
#                                                                           
#                              MAIN FUNCTION
#                                                                          
################################################################################       

        
if __name__ == '__main__':
    
    app = QtGui.QApplication(sys.argv)
    instance_1 = MainWindow()
    sys.exit(app.exec_())
