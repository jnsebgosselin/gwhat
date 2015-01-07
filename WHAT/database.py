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

#----- THIRD PARTY IMPORTS -----

from PySide.QtGui import QIcon

class icons():
    
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
        
        #----- HYDROGRAPH TOOLBAR -----
        
        self.fit_y = QIcon('Icons/fit_y.png')
        self.fit_x = QIcon('Icons/fit_x.png')
        self.save_graph_config = QIcon('Icons/save_config.png')
        self.load_graph_config = QIcon('Icons/load_config.png')
        self.closest_meteo = QIcon('Icons/closest_meteo.png')
        self.draw_hydrograph = QIcon('Icons/stock_image.png')
        self.save = QIcon('Icons/save.png')
        self.meteo = QIcon('Icons/meteo.png')
        

class tooltips():
    
    def __init__(self, language): #------------------------------- ENGLISH -----
        
        #----- DOWNLOAD TAB -----        
        
        self.refresh_staList = 'Refresh the current weather station list.'
        
        self.search4stations = ('Search for weather stations on \n' +
                                'www.climate.weather.gc.ca.')
        self.btn_GetData = 'Download data for the selected weather station.'
        self.btn_browse_staList = 'Load a custom weather station list.'
        
        #----- HYDROGRAPH TOOLBAR -----
        
        self.loadConfig = ('Load graph layout for the current \n' +
                           'Water Level Data File if it exists.')
                             
        self.saveConfig = 'Save current graph layout.'
        
        self.fit_y = 'Best fit the water level scale.'
        
        self.fit_x = 'Best fit the time scale.'
        
        self.closest_meteo = '''<p>Search and Load the Weather Data File
        of the station located the closest from the well.</p>'''
                                
        self.draw_hydrograph = 'Draw the well hydrograph.'
        
        self.save_hydrograph = 'Save the well hydrograph.'
        
        self.weather_normals = '''<p>Plot the mean air temperature and 
        precipitation monthly and yearly normals calculated from the Weather
        Data File currently selected.</p>'''
        
        if language == 'French': #--------------------------------- FRENCH -----
            
            pass
        
    
class labels():
    
    def __init__(self, language):
        
        pass
    
class styleUI():
    
    
    def __init__(self):
        
        self.frame = 22
        self.HLine = 52
        self.VLine = 53
        
        # 17 = QtGui.QFrame.Box | QtGui.QFrame.Plain
        # 22 = QtGui.QFrame.StyledPanel | QtGui.QFrame.Plain
        # 20 = QtGui.QFrame.HLine | QtGui.QFrame.Plain
        # 52 = QtGui.QFrame.HLine | QtGui.QFrame.Sunken
        # 53 = QtGui.QFrame.VLine | QtGui.QFrame.Sunken

        
#        print Station_widget.frameStyle()
if __name__ == '__main__':
    pass
    
#    style = QtGui.QFrame()
#    style.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Plain)
#    print style.frameStyle()
    
    
    
    
    
    
    
    