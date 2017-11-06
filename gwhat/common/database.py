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


class Tooltipsblabla():

    def __init__(self, language):  # ============================= ENGLISH ====

        # ------------------------------------------------------- MENU BAR ----

        self.open_project = 'Open Project...'
        self.new_project = 'New Project...'

        # ------------------------------------------ Download Weather Data ----

        self.search4stations = ('Search for weather stations in the ' +
                                'Canadian Daily Climate Database (CDCD)')
        self.refresh_staList = 'Refresh the current weather station list'
        self.btn_browse_staList = 'Load an existing weather station list'
        self.btn_save_staList = 'Save current station list.'
        self.btn_delSta = 'Remove selected weather stations from the list'

        self.btn_GetData = 'Download data for the selected weather stations'


class labels():

    def __init__(self, language): #================================ ENGLISH ====

        #----------------------------------------------------- DOWNLOAD TAB ----

        self.btn_GetData = 'Get Data'
        self.title_download = ('<font size="4"><b>Download Data : </b></font>')
        self.title_concatenate = (
            '''<font size="4">
                 <b>Concatenate and Format Raw Data Files :</b>
               </font>''')

        self.btn_select_rawData = 'Load'
        self.btn_save_concatenate = 'Save'

        #--------------------------------------------------------- FILL TAB ----


class FileHeaders():


    def __init__(self):

        #---- graph_layout.lst ----

        self.graph_layout = [['Name Well', 'Station Meteo', 'Min. Waterlvl',
                              'Waterlvl Scale', 'Date Start', 'Date End',
                              'Show Graph Title', 'Show Legend',
                              'Precip. Scale', 'Waterlvl Ref.', 'Trend Line',
                              'Fig. Width', 'Fig. Height', 'Color Palette',
                              'Label Lang.', 'Date mode', 'Date Disp. Pattern',
                              'Weather Bin Width', 'Top/Bottom Axes Ratio',
                              'Bottom Grid Div.', 'Top Grid Div.']]

        #---- weather_stations.lst ----

        self.weather_stations = [['staName', 'stationId', 'StartYear',
                                  'EndYear', 'Province', 'ClimateID',
                                  'Proximity (km)']]

        #---- weather data (*.out) ----

if __name__ == '__main__':
    pass
#    HeaderDB = headers()
#    StyleDB = styleUI()

#    style = QtGui.QFrame()
#    style.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Plain)
#    print style.frameStyle()







