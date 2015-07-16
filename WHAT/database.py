# -*- coding: utf-8 -*-
"""
Copyright 2015 Jean-Sebastien Gosselin

email: jnsebgosselin@gmail.com

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

#----- STANDARD LIBRARY IMPORTS -----

import platform

#----- THIRD PARTY IMPORTS -----

from PySide.QtGui import QIcon, QFont
from PySide.QtCore import QSize

software_version = 'WHAT Beta 4.1.7'
last_modification = '07/07/2015'

class Icons():
    
    def __init__(self):
        
        self.WHAT = QIcon('Icons/WHAT.png')
        
        self.play = QIcon('Icons/start.png')
        self.forward = QIcon('Icons/start_all.png')
        self.refresh = QIcon('Icons/refresh.png')
        self.openFile = QIcon('Icons/open_file.png')
        self.openFolder = QIcon('Icons/folder')
        self.download = QIcon('Icons/download.png')
        self.stop = QIcon('Icons/process-stop.png')
        self.search = QIcon('Icons/search.png')
        self.settings = QIcon('Icons/settings.png')
        
        self.go_previous = QIcon('Icons/go-previous.png')
        self.go_next = QIcon('Icons/go-next.png')
        self.go_last = QIcon('Icons/go-last.png')
        self.go_first = QIcon('Icons/go-first.png')
        self.go_up = QIcon('Icons/go-up.png')
        
        self.staList = QIcon('Icons/note.png')
        
        #---- Menu TOOLBAR ----
        
        self.new_project = QIcon('Icons/new_project.png')
        self.open_project = QIcon('Icons/open_project.png')
        
        #----- Download Weather Data -----
        
        self.plus_sign = QIcon('Icons/plus_sign.png')
        self.add2list = QIcon('Icons/add2list.png')
        
        #---- Fill Weather Data ----
        
        self.fill_data = QIcon('Icons/fill_data.png')
        self.fill_all_data = QIcon('Icons/fill_all_data.png')
        
        self.triangle_right = QIcon('Icons/triangle_right.png')
        self.triangle_down = QIcon('Icons/triangle_down.png')
       
        #----- HYDROGRAPH TOOLBAR -----
        
        self.fit_y = QIcon('Icons/fit_y.png')
        self.fit_x = QIcon('Icons/fit_x.png')
        self.save_graph_config = QIcon('Icons/save_config.png')
        self.load_graph_config = QIcon('Icons/load_config.png')
        self.closest_meteo = QIcon('Icons/closest_meteo.png')
        self.draw_hydrograph = QIcon('Icons/stock_image.png')
        self.save = QIcon('Icons/save.png')
        self.meteo = QIcon('Icons/meteo.png')
        self.work = QIcon('Icons/work.png')
        self.toggleMode = QIcon('Icons/toggleMode2.png')
        
        #----- MRC TOOLBAR -----
        
        self.undo = QIcon('Icons/undo.png')
        self.clear_search = QIcon('Icons/clear-search.png')
        self.MRCalc = QIcon('Icons/MRCalc.png')
        self.edit = QIcon('Icons/edit.png')
        self.pan = QIcon('Icons/pan.png')
        self.home = QIcon('Icons/home.png')
        self.add_point = QIcon('Icons/add_point.png')
        self.erase = QIcon('Icons/erase.png')
        self.erase2 = QIcon('Icons/erase2.png')
        self.findPeak = QIcon('Icons/find_peak.png')
        self.findPeak2 = QIcon('Icons/find_peak2.png')
        self.showDataDots = QIcon('Icons/show_datadots.png')
        
        #---- Recharge ----
        
        self.stratigraphy = QIcon('Icons/stratigraphy.png')
        self.mrc2rechg = QIcon('Icons/recharge.png')
        
        
class Tooltips():
    
    def __init__(self, language): #================================ ENGLISH ====
        
        #--------------------------------------------------------- MENU BAR ----
        
        self.open_project = 'Open Project...'
        self.new_project = 'New Project...'
        
        #-------------------------------------------- Download Weather Data ----
        
        self.search4stations = ('Search for weather stations in the ' +
                                'Canadian Daily Climate Database (CDCD)')
        self.refresh_staList = 'Refresh the current weather station list'
        self.btn_browse_staList = 'Load an existing weather station list'
        self.btn_save_staList = 'Save current station list.'
        self.btn_delSta = 'Remove selected weather stations from the list'
        
        self.btn_GetData = 'Download data for the selected weather stations'
        
        
        self.btn_select_rawData = 'Select and format raw weather data files' 
        self.btn_save_concatenate = 'Save formated weather data in a csv file'

        #--------------------------------------------------------- FILL TAB ----
        
        self.altlimit = (
            '''<p>Altitude difference limit over which neighboring stations are
                 excluded from the gapfilling procedure.</p>
               <p>This condition is ignored if set to a value of -1.</p>''')
               
        self.distlimit = (                
            '''<p>Distance limit beyond which neighboring stations are excluded
                 from the gapfilling procedure.</p>
               <p>This condition is ignored if set to a value of -1.</p>''')
               
        self.btn_fill_all = (
        'Fill the gaps in the daily weather data for all the weather stations' +
        ' displayed in the list.')
                 
        self.btn_fill = (        
        'Fill the gaps in the daily  weather data for the selected weather ' +
        'station.')
        
        #--------------------------------------------------- HYDROGRAPH TAB ----
        
        #---- TOOLBAR ----
        
        self.loadConfig = ('Load graph layout for the current \n' +
                           'Water Level Data File if it exists')
                             
        self.saveConfig = 'Save current graph layout'
        
        self.fit_y = 'Best fit the water level scale'
        
        self.fit_x = 'Best fit the time scale'
        
        self.closest_meteo = '''<p>Search and Load the Weather Data File
        of the station located the closest from the well</p>'''
                                
        self.draw_hydrograph = 'Force a refresh of the well hydrograph'
        
        self.save_hydrograph = 'Save the well hydrograph'
        
        self.weather_normals = ('Plot the yearly and monthly averages for ' +
                                'the \n Weather Data File currently selected')
        
        self.addTitle = 'Add A Title To The Figure Here'
        
        self.work_waterlvl = ('Toggle between layout and computation ' +
                              'mode (EXPERIMENTAL FEATURE)')
        
        if language == 'French': #================================== FRENCH ====
            
            self.btn_GetData = ('Télécharger les données pour la station \n' +
                                'climatique sélectionnée')
        
    
class labels():
    
    def __init__(self, language): #================================ ENGLISH ====
        
        #-------------------------------------------------------- TAB NAMES ----
        
        self.TAB1 = 'Download Data'
        self.TAB2 = 'Fill Data'
        self.TAB3 = 'Hydrograph'
        self.TAB4 = 'About'
        
        #----------------------------------------------------- DOWNLOAD TAB ----

        self.btn_GetData = 'Get Data'
        self.title_download = ('<font size="4"><b>Download Data : </b></font>')
        self.title_concatenate = (
            '''<font size="4">
                 <b>Concatenate and Format Raw Data Files :</b>
               </font>''')
                
        self.btn_select_rawData = 'Load' 
        self.btn_save_concatenate = 'Save'
        
        self.saveMeteoAuto = "Automatically save formatted\nweather data"
        
        #--------------------------------------------------------- FILL TAB ----
        
        self.fill_station = 'Fill Data for Weather Station :'
        self.btn_fill_weather = 'Fill Station'
        self.btn_fill_all_weather = 'Fill All Stations'
        self.altlimit = 'Max. Elevation Diff. :'
        self.distlimit = 'Max. Distance :'
        self.NbrSta = 'Nbr. of stations :'
        
        if language == 'French': #================================== FRENCH ====
            
        #-------------------------------------------------------- TAB NAMES ----
        
            self.TAB1 = u'Télécharger'
            self.TAB2 = u'Combler les données'
            self.TAB3 = u'Hydrogramme'
            self.TAB4 = u'À propos'
    
class styleUI():
    
    
    def __init__(self):
        
        self.frame = 22
        self.HLine = 52
        self.VLine = 53
        
        self.size1 = 32
        
        self.iconSize = QSize(32, 32)
        self.iconSize2 = QSize(20, 20)
        
        self.sideBarWidth = 275
        
        if platform.system() == 'Windows':
            self.font1 = QFont('Segoe UI', 11) # Calibri, Cambria
            self.font_console = QFont('Segoe UI', 9)
            self.font_menubar = QFont('Segoe UI', 10) 
        elif platform.system() == 'Linux':
            self.font1 = QFont('Ubuntu', 11)
            self.font_console = QFont('Ubuntu', 9) 
            self.font_menubar = QFont('Ubuntu', 10)
    
        
#        self.fontSize1.setPointSize(11)
        
        # 17 = QtGui.QFrame.Box | QtGui.QFrame.Plain
        # 22 = QtGui.QFrame.StyledPanel | QtGui.QFrame.Plain
        # 20 = QtGui.QFrame.HLine | QtGui.QFrame.Plain
        # 52 = QtGui.QFrame.HLine | QtGui.QFrame.Sunken
        # 53 = QtGui.QFrame.VLine | QtGui.QFrame.Sunken
        
        
class FileHeaders():
    
    
    def __init__(self):
        
        #---- graph_layout.lst ----
        
        self.graph_layout = [['Name Well', 'Station Meteo', 'Min. Waterlvl',
                              'Waterlvl Scale', 'Date Start', 'Date End',
                              'Fig. Title State', 'Fig. Title Text',
                              'Precip. Scale', 'Waterlvl Ref.', 'Trend Line']]
        
        #---- weather_stations.lst ----
                 
        self.weather_stations = [['staName', 'stationId', 'StartYear',
                                  'EndYear', 'Province', 'ClimateID',
                                  'Proximity (km)']]
        
if __name__ == '__main__':
    pass
#    HeaderDB = headers()
#    StyleDB = styleUI()
    
#    style = QtGui.QFrame()
#    style.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Plain)
#    print style.frameStyle()
    
    
    
    
    
    
    
    