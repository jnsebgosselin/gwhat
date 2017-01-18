"""
Copyright 2014-2016 Jean-Sebastien Gosselin
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
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# STANDARD LIBRARY IMPORTS :

from calendar import monthrange
import os
import csv
import copy
import sys
from datetime import date
# import time

# THIRD PARTY IMPORTS :

from xlrd.xldate import xldate_from_date_tuple
from xlrd import xldate_as_tuple

import numpy as np
from PySide import QtGui, QtCore

import matplotlib as mpl
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
mpl.rcParams['backend.qt4'] = 'PySide'

# PERSONAL IMPORTS :

import database as db
from colors import Colors


# =============================================================================


class LabelDataBase():

    def __init__(self, language):

        # ---- Legend ----

        self.Pyrly = 'Annual total precipitation = %0.0f mm'
        self.Tyrly = u'Average annual air temperature = %0.1f °C'
        self.rain = 'Rain'
        self.snow = 'Snow'
        self.Tmax = 'Temp. max.'
        self.Tmin = 'Temp. min.'
        self.Tavg = 'Temp. mean'

        # ---- Labels ----

        self.Tlabel = u'Monthly Air Temperature (°C)'
        self.Plabel = 'Monthly Total Precipitation (mm)'
        self.month_names = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                            "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

        if language == 'French':

            # ---- Legend ----

            self.Pyrly = u'Précipitations totales annuelles = %0.0f mm'
            self.Tyrly = u"Température moyenne annuelle = %0.1f °C"
            self.rain = 'Pluie'
            self.snow = 'Neige'
            self.Tmax = u'Températures min.'
            self.Tmin = u'Températures max.'
            self.Tavg = u'Températures moy.'

            # ---- Labels ----

            self.Tlabel = u'Températures moyennes mensuelles (°C)'
            self.Plabel = u'Précipitations totales mensuelles (mm)'
            self.month_names = ["JAN", u"FÉV", "MAR", "AVR", "MAI", "JUN",
                                "JUL", u"AOÛ", "SEP", "OCT", "NOV", u"DÉC"]


class Tooltips():

    def __init__(self, language):  # ------------------------------- ENGLISH --

        self.save = 'Save graph'
        self.open = "Open a valid '.out' weather data file"
        self.addTitle = 'Add a Title to the Figure Here.'
        self.btn_showStats = 'Show monthly weather normals data table.'

        if language == 'French':  # --------------------------------- FRENCH --

            pass


class WeatherAvgGraph(QtGui.QWidget):

    """
    GUI that allows to plot weather normals, save the graphs to file, see
    various stats about the dataset, etc...
    """

    def __init__(self, parent=None):
        super(WeatherAvgGraph, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window)
#        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.NORMALS = []  # 2D matrix holding all the weather normals
                           # [TMAX, TMIN, TMEAN, PTOT, {ETP}, {RAIN}]
        self.station_name = []
        self.save_fig_dir = os.getcwd()
        self.meteo_dir = os.getcwd()
        self.language = 'English'

        self.initUI()

    def initUI(self):  # ======================================================

        iconDB = db.Icons()
        StyleDB = db.styleUI()
        ttipDB = Tooltips('English')

        self.setWindowTitle('Weather Averages')
        self.setFont(StyleDB.font1)
        self.setWindowIcon(iconDB.WHAT)

        # ---------------------------------------------------------- TOOLBAR --

        btn_save = QtGui.QToolButton()
        btn_save.setAutoRaise(True)
        btn_save.setIcon(iconDB.save)
        btn_save.setToolTip(ttipDB.save)
        btn_save.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_save.setIconSize(StyleDB.iconSize)
        btn_save.clicked.connect(self.save_graph)

        btn_open = QtGui.QToolButton()
        btn_open.setAutoRaise(True)
        btn_open.setIcon(iconDB.openFile)
        btn_open.setToolTip(ttipDB.open)
        btn_open.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_open.setIconSize(StyleDB.iconSize)
        btn_open.clicked.connect(self.select_meteo_file)

        btn_showStats = QtGui.QToolButton()
        btn_showStats.setAutoRaise(True)
        btn_showStats.setIcon(iconDB.showGrid)
        btn_showStats.setToolTip(ttipDB.btn_showStats)
        btn_showStats.setFocusPolicy(QtCore.Qt.NoFocus)
        btn_showStats.setIconSize(StyleDB.iconSize)
        btn_showStats.clicked.connect(self.show_monthly_grid)

#        self.graph_title = QtGui.QLineEdit()
#        self.graph_title.setMaxLength(65)
#        self.graph_title.setEnabled(False)
#        self.graph_title.setText('Add A Title To The Figure Here')
#        self.graph_title.setToolTip(ttipDB.addTitle)
#        self.graph_title.setFixedHeight(StyleDB.size1)
#
#        self.graph_status = QtGui.QCheckBox()
#        self.graph_status.setEnabled(False)

#        separator1 = QtGui.QFrame()
#        separator1.setFrameStyle(StyleDB.VLine)

        subgrid_toolbar = QtGui.QGridLayout()
        toolbar_widget = QtGui.QWidget()

        row = 0
        col = 0
        subgrid_toolbar.addWidget(btn_save, row, col)
        col += 1
        subgrid_toolbar.addWidget(btn_open, row, col)
        col += 1
        subgrid_toolbar.addWidget(btn_showStats, row, col)
        col += 1
        subgrid_toolbar.setColumnStretch(col, 4)

        subgrid_toolbar.setSpacing(5)
        subgrid_toolbar.setContentsMargins(0, 0, 0, 0)

        toolbar_widget.setLayout(subgrid_toolbar)

        # -------------------------------------------------------- MAIN GRID --

        # ---- widgets ----

        self.fig_weather_normals = FigWeatherNormals()
        self.grid_weather_normals = GridWeatherNormals()
        self.grid_weather_normals.hide()

        # ---- layout ----

        mainGrid = QtGui.QGridLayout()

        row = 0
        mainGrid.addWidget(toolbar_widget, row, 0)
        row += 1
        mainGrid.addWidget(self.fig_weather_normals, row, 0)
        row += 1
        mainGrid.addWidget(self.grid_weather_normals, row, 0)

        mainGrid.setContentsMargins(10, 10, 10, 10)  # (L,T,R,B)
        mainGrid.setSpacing(10)
        mainGrid.setRowStretch(row, 500)
        mainGrid.setColumnStretch(0, 500)

        self.setLayout(mainGrid)

    def show_monthly_grid(self):  # ===========================================

        if self.grid_weather_normals.isHidden():
            self.grid_weather_normals.show()
            self.setFixedHeight(self.size().height()+250)
#            self.setFixedWidth(self.size().width()+75)
            self.sender().setAutoRaise(False)
        else:
            self.grid_weather_normals.hide()
            self.setFixedHeight(self.size().height()-250)
#            self.setFixedWidth(self.size().width()-75)
            self.sender().setAutoRaise(True)

    def set_lang(self, lang):  # ==============================================
        self.language = lang
        self.fig_weather_normals.set_lang(lang)
        self.fig_weather_normals.draw()

    def generate_graph(self, filename):  # ========= Generate and Draw Graph ==

        #------------------------------------------------------ Prepare Data --

        #---- load data from data file ----

        METEO = MeteoObj()
        METEO.load_and_format(filename)

        #---- calulate weather normals ----

        # DATA = [YEAR, MONTH, DAY, TMAX, TMIN, TMEAN, PTOT, {ETP}, {RAIN}]
        self.NORMALS, self.MTHSER = calculate_normals(METEO.DATA,
                                                      METEO.datatypes)

        #------------------------------------------------------ Plot Normals --

        self.station_name = METEO.STA
        self.fig_weather_normals.plot_monthly_normals(self.NORMALS)
        self.fig_weather_normals.draw()

        self.setWindowTitle('Weather Averages for %s' % self.station_name)

        #----------------------------------------------- Generate Data Table --

        self.grid_weather_normals.populate_table(self.NORMALS)

    def save_graph(self):  # ==================================== save_graph ==

        dialog_dir = self.save_fig_dir
        dialog_dir += '/WeatherAverages_%s' % self.station_name

        dialog = QtGui.QFileDialog()
        dialog.setConfirmOverwrite(True)
        filename, ftype = dialog.getSaveFileName(caption="Save Figure",
                                                 dir=dialog_dir,
                                                 filter=('*.pdf'))

        if filename:
            if filename[-4:] != ftype[1:]:
                # Add a file extension if there is none.
                filename = filename + ftype[1:]

            self.save_fig_dir = os.path.dirname(filename)
            self.fig_weather_normals.figure.savefig(filename)

            #---- Save Companion files ----

            filename = self.save_fig_dir
            filename += '/WeatherAverages_%s.csv' % self.station_name
            self.save_normal_table(filename)

            filename = self.save_fig_dir
            filename += '/MonthlySeries_%s.csv' % self.station_name
            self.save_monthly_series(filename)

    def save_normal_table(self, filename):  # ========= Save Normals to File ==

        NORMALS = self.NORMALS

        #--------------------------------------------- Generate File Content --

        fcontent = [['', 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL',
                     'AUG', 'SEP', 'OCT', 'NOV', 'DEC', 'YEAR']]

        #---- Air Temperature ----

        Tvar = ['Daily Tmax (degC)', 'Daily Tmin (degC)', 'Daily Tavg (degC)']
        for i in range(3):
            fcontent.append([Tvar[i]])
            # months
            for j in range(12):
                fcontent[-1].extend(['%0.1f' % NORMALS[j, i]])
            # years
            fcontent[-1].extend(['%0.1f' % np.mean(NORMALS[:, i])])

        #---- rain ----

        fcontent.append(['Rain (mm)'])
        # months
        for j in range(12):
            fcontent[-1].extend(['%0.1f' % NORMALS[j, 5]])
        # year
        fcontent[-1].extend(['%0.1f' % np.sum(NORMALS[:, 5])])

        #---- snow ----

        fcontent.append(['Snow (mm)'])
        # months
        for j in range(12):
            snowval = NORMALS[j, 3] - NORMALS[j, 5]
            fcontent[5].extend(['%0.1f' % snowval])
        # year
        fcontent[-1].extend(['%0.1f' % np.sum(NORMALS[:, 3] - NORMALS[:, 5])])

        #---- total precipitation ----

        fcontent.append(['Total Precip. (mm)'])
        for j in range(12):
            fcontent[-1].extend(['%0.1f' % NORMALS[j, 3]])
        # year
        fcontent[-1].extend(['%0.1f' % np.sum(NORMALS[:, 3])])

        #---- ETP ----

        fcontent.append(['ETP (mm)'])
        for j in range(12):
            fcontent[-1].extend(['%0.1f' % NORMALS[j, 4]])
        # year
        fcontent[-1].extend(['%0.1f' % np.sum(NORMALS[:, 4])])

        #------------------------------------------------------ Save to File --

        with open(filename, 'w')as f:
            writer = csv.writer(f, delimiter='\t', lineterminator='\n')
            writer.writerows(fcontent)

    def save_monthly_series(self, filename):  # ======== Save Monthly Series ==

        with open(filename, 'w')as f:
            writer = csv.writer(f, delimiter='\t', lineterminator='\n')
            writer.writerows(self.MTHSER)

    def select_meteo_file(self):  # ============= Select a Weather Data File ==

        filename, _ = QtGui.QFileDialog.getOpenFileName(self,
                          'Select a valid weather data file', self.meteo_dir,
                          '*.out')

        if filename:
            self.generate_graph(filename)
            self.meteo_dir = os.path.dirname(filename)

    def show(self):  # ========================================================
        super(WeatherAvgGraph, self).show()
        self.raise_()
        # self.activateWindow()

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


###############################################################################


class MeteoObj():

    """
    This is a class to load and manipulate weather data.

    nan are assigned a value of 0 for Ptot and for air Temp, the value is
    calculated with an in-station interpolation.
    """

    def __init__(self):

        self.filename = ''

        self.STA = 'Station Name'
        self.LAT = 'Latitude'
        self.LON = 'Longitude'
        self.PRO = 'Province'
        self.ALT = 'Elevation'
        self.CID = 'Climate Identifier'

        self.STADESC = [[None] * 6, [None] * 6]  # station description

        self.STADESC[0] = ['Station Name', 'Latitude', 'Longitude',
                           'Province', 'Elevation', 'Climate Identifier']

        self.INFO = []

        self.datatypes = []
        # 0 -> not cumulative data:
        #      ex.: Air Temperature
        #           Air humidity)
        # 1 -> cumulative data:
        #      ex.: Precipitation, ETP

        self.varnames = []
        self.HEADER = []
        self.DATA = []

        self.TIME = []  # Time in numeric format.

    def load_and_format(self, filename):  # ===================================

        print('Loading weather data from "%s"...' %
              os.path.basename(filename))

        # Load data from file :

        self.load(filename)
        self.build_HTML_table()

        # Clean data :

        self.clean_endsof_file()
        self.check_time_continuity()
        self.get_TIME(self.DATA[:, :3])
        self.fill_nan()

        # Add ETP and RAIN :

        self.add_ETP_to_data()
        self.add_rain_to_data()

        print('Weather data loaded.')

    def load(self, filename):  # ==============================================

        """
        Load the info related to the weather station, the date and weather
        datasets 'as is' from the file.
        """

        self.filename = filename

        labels = np.array(self.STADESC[0])

        with open(filename, 'r') as f:
            reader = list(csv.reader(f, delimiter='\t'))

        # Get info from header and find row where data starts :

        for i in range(len(reader)):

            if len(reader[i]) > 0:

                if reader[i][0] == 'Year':
                    self.varnames = reader[i]
                    data_indx = i + 1
                    self.HEADER = reader[:data_indx]
                    break

                if np.any(labels == reader[i][0]):
                    indx = np.where(labels == reader[i][0])[0][0]
                    self.STADESC[1][indx] = reader[i][1]

        # Update class variables :

        [self.STA, self.LAT, self.LON,
         self.PRO, self.ALT, self.CID] = self.STADESC[1]

        # DATA = [Year, Month, Day, Tmax, Tmin, Tmean, PTOT, {ETP}, {RAIN}]
        self.DATA = np.array(reader[data_indx:]).astype('float')

        # Assign a datatype to each variables :

        datatype0 = ['Max Temp (deg C)', 'Min Temp (deg C)',
                     'Mean Temp (deg C)']
        datatype1 = ['Total Precip (mm)', 'Rain (mm)', 'ETP (mm)']

        nvar = len(self.DATA[0, 3:])
        self.datatypes = [0] * nvar
        varname = self.varnames[3:]

        for i in range(nvar):
            if varname[i] in datatype0:
                self.datatypes[i] = 0
            elif varname[i] in datatype1:
                self.datatypes[i] = 1
            else:
                self.datatypes[i] = 0

    def clean_endsof_file(self):  # ===========================================
        """
        Remove nan values at the beginning and end of the record if any. Must
        not be run before the 'TIME' array is generated.
        """

        # Beginning :

        n = len(self.DATA[:, 0])
        for i in range(len(self.DATA[:, 0])):
            if np.all(np.isnan(self.DATA[i, 3:])):
                self.DATA = np.delete(self.DATA, i, axis=0)
            else:
                break

        if n < len(self.DATA[:, 0]):
            print('%d empty' % (n - len(self.DATA[:, 0])) +
                  ' rows of data removed at the beginning of the dataset.')

        #---- End ----

        n = len(self.DATA[:, 0])
        for i in (n - np.arange(n) - 1):
            if np.all(np.isnan(self.DATA[i, 3:])):
                self.DATA = np.delete(self.DATA, i, axis=0)
            else:
                break

        if n < len(self.DATA[:, 0]):
            print('%d empty' % (n - len(self.DATA[:, 0])) +
                  ' rows of data removed at the end of the dataset.')

    def check_time_continuity(self):  # =======================================

        #------------------------------------------ check time continuity ----

        # Check if the data series is continuous over time and
        # correct it if not

        time_start = xldate_from_date_tuple((self.DATA[0, 0].astype('int'),
                                             self.DATA[0, 1].astype('int'),
                                             self.DATA[0, 2].astype('int')), 0)

        time_end = xldate_from_date_tuple((self.DATA[-1, 0].astype('int'),
                                           self.DATA[-1, 1].astype('int'),
                                           self.DATA[-1, 2].astype('int')), 0)

        if time_end - time_start + 1 != len(self.DATA[:, 0]):
            print('%s is not continuous, correcting...' % self.STA)
            self.DATA = make_timeserie_continuous(self.DATA)

    def get_TIME(self, DATE):  # ==============================================

        # Generate a 1D array with date in numeric format because it is not
        # provided in the '.out' files.

        N = len(DATE[:, 0])
        TIME = np.zeros(N)
        for i in range(N):
            TIME[i] = xldate_from_date_tuple((DATE[i, 0].astype('int'),
                                              DATE[i, 1].astype('int'),
                                              DATE[i, 2].astype('int')), 0)
        self.TIME = TIME

        return TIME

    def fill_nan(self):  # ====================================================

        datatypes = self.datatypes
        varnames = self.varnames[3:]
        nvar = len(varnames)
        X = np.copy(self.DATA[:, 3:])
        TIME = np.copy(self.TIME)

        # preferable to be run before ETP or RAIN is estimated, So that
        # there is no missing value in both of these estimated time series.
        # However, it needs to be ran after but after 'check_time_continuity'.

        #---- Fill Temperature based variables ----

        for var in range(nvar):

            nanindx = np.where(np.isnan(X[:, var]))[0]
            if len(nanindx) > 0:

                if datatypes[var] == 0:

                    nonanindx = np.where(~np.isnan(X[:, var]))[0]
                    X[:, var] = np.interp(TIME, TIME[nonanindx],
                                          X[:, var][nonanindx])

                    print('There was %d nan values' % len(nanindx) +
                          ' in %s series.' % varnames[var]  +
                          ' Missing values estimated with a' +
                          ' linear interpolation.')

                elif datatypes[var] == 1:

                    X[:, var][nanindx] = 0

                    print('There was %d nan values' % len(nanindx) +
                          ' in %s series.' % varnames[var] +
                          ' Missing values are assigned a 0 value.')

        self.DATA[:, 3:] = X

    def add_rain_to_data(self):  # ============================================

        varnames = np.array(self.varnames)
        if np.any(varnames == 'Rain (mm)'):
            print('Already a Rain time series in the datasets.')
            return

        # Get PTOT and TAVG from data :

        indx = np.where(varnames == 'Total Precip (mm)')[0][0]
        PTOT = np.copy(self.DATA[:, indx])

        indx = np.where(varnames == 'Mean Temp (deg C)')[0][0]
        TAVG = np.copy(self.DATA[:, indx])

        # Estimate rain :

        RAIN = np.copy(PTOT)
        RAIN[np.where(TAVG < 0)[0]] = 0
        RAIN = RAIN[:, np.newaxis]

        # Extend data :

        self.DATA = np.hstack([self.DATA, RAIN])
        self.varnames.append('Rain (mm)')
        self.datatypes.append(1)

    def add_ETP_to_data(self):  # =============================================

        varnames = np.array(self.varnames)
        if np.any(varnames == 'ETP (mm)'):
            print('Already a ETP time series in the datasets.')
            return

        # Assign local variable :

        DATE = np.copy(self.DATA[:, :3])
        LAT = np.copy(float(self.LAT))

        indx = np.where(varnames == 'Mean Temp (deg C)')[0][0]
        TAVG = np.copy(self.DATA[:, indx])

        # ---- compute normals ----

        NORMALS, _ = calculate_normals(self.DATA, self.datatypes)
        Ta = NORMALS[:, 2] # monthly air temperature averages (deg Celcius)

        ETP = calculate_ETP(DATE, TAVG, LAT, Ta)
        ETP = ETP[:, np.newaxis]

        # ---- extend data ----

        self.DATA = np.hstack([self.DATA, ETP])
        self.varnames.append('ETP (mm)')
        self.datatypes.append(1)

    def build_HTML_table(self): #==============================================

        # HTML table with the info related to the weather station.

        FIELDS = self.STADESC[0]
        VALIST = self.STADESC[1]
        UNITS =  ['', '&deg;', '&deg;','', ' m', '']

        info = '<table border="0" cellpadding="2" cellspacing="0" align="left">'
        for i in range(len(FIELDS)):
            VAL = VALIST[i]
            info += '''<tr>
                         <td width=10></td>
                         <td align="left">%s</td>
                         <td align="left" width=20>:</td>
                         <td align="left">%s%s</td>
                       </tr>''' % (FIELDS[i], VAL, UNITS[i])
        info += '</table>'

        self.INFO = info

        return info


#    def daily2weekly(self): #=================================================
#
#        # THIS METHOD NEEDS UPDATING! Currently, it seems it it not used at all.
#
#        bwidth = 7.
#        nbin = np.floor(len(TIME) / bwidth)
#
#        TIMEbin = TIME[:nbin*bwidth].reshape(nbin, bwidth)
#        TIMEbin = np.mean(TIMEbin, axis=1)
#
#        TMAXbin = TMAX[:nbin*bwidth].reshape(nbin, bwidth)
#        TMAXbin = np.mean(TMAXbin, axis=1)
#
#        PTOTbin = PTOT[:nbin*bwidth].reshape(nbin, bwidth)
#        PTOTbin = np.sum(PTOTbin, axis=1)
#
#        RAINbin = RAIN[:nbin*bwidth].reshape(nbin, bwidth)
#        RAINbin = np.sum(RAINbin, axis=1)
#
#        nres = len(TIME) - (nbin * bwidth)
#        print 'Nbin residual =', nres
#
#        #---------------------------------------- update class variables ----
#
#        self.TIMEwk = TIMEbin
#        self.TMAXwk = TMAXbin
#        self.PTOTwk = PTOTbin
#        self.RAINwk = RAINbin


#==============================================================================
def add_ETP_to_weather_data_file(filename):
    """
    Load data from a weather data file, estimate the ETP and add it to
    the file.
    """
#==============================================================================

    #-- load and stock original data --

    meteoObj = MeteoObj()
    meteoObj.load(filename)

    HEADER = copy.copy(meteoObj.HEADER)
    DATAORIG = np.copy(meteoObj.DATA)
    DATE = DATAORIG[:, :3]

    #-- compute air temperature normals --

    meteoObj.clean_endsof_file()
    meteoObj.check_time_continuity()
    meteoObj.get_TIME(meteoObj.DATA[:, :3])
    meteoObj.fill_nan()

    NORMALS, _ = calculate_normals(meteoObj.DATA, meteoObj.datatypes)

    varnames = np.array(meteoObj.HEADER[-1])
    indx = np.where(varnames == 'Mean Temp (deg C)')[0][0]

    Ta = NORMALS[:, indx-3]   # monthly air temperature averages (deg C)
    LAT = float(meteoObj.LAT) # Latitude (decimal deg)

    #-- estimate ETP from original temperature time series --

    TAVG = np.copy(DATAORIG[:, indx])
    ETP = calculate_ETP(DATE, TAVG, LAT, Ta)

    #-- extend data --

    filecontent = copy.copy(HEADER)
    if np.any(varnames == 'ETP (mm)'):
        print('Already a ETP time series in the datasets. Overriding data.')

        # Override ETP in DATA:
        indx = np.where(varnames == 'ETP (mm)')[0][0]
        DATAORIG[:, indx] = ETP

    else:
        # Add new variable name to header:
        filecontent[-1].append('ETP (mm)')

        # Add ETP to DATA matrix:
        ETP = ETP[:, np.newaxis]
        DATAORIG = np.hstack([DATAORIG, ETP])

        DATAORIG.tolist()

    #-- save data --

    for i in range(len(DATAORIG[:, 0])):
        filecontent.append(DATAORIG[i, :])

    with open(filename, 'w') as f:
        writer = csv.writer(f,delimiter='\t')
        writer.writerows(filecontent)

    print('ETP time series added successfully to %s' % filename)


#==============================================================================
def make_timeserie_continuous(DATA):
    """
    This function is called when a time serie of a daily meteorological record
    is found to be discontinuous over time.

    <make_timeserie_continuous> will scan the entire time serie and will insert
    a row with nan values whenever there is a gap in the data and will return
    the continuous data set.

    DATA = [YEAR, MONTH, DAY, VAR1, VAR2 ... VARn]

           2D matrix containing the dates and the corresponding daily
           meteorological data of a given weather station arranged in
           chronological order.
    """
#==============================================================================

    nVAR = len(DATA[0,:]) - 3 # nVAR = number of meteorological variables
    nan2insert = np.zeros(nVAR) * np.nan

    i = 0
    date1 = xldate_from_date_tuple((DATA[i, 0].astype('int'),
                                    DATA[i, 1].astype('int'),
                                    DATA[i, 2].astype('int')), 0)


    while i < len(DATA[:, 0]) - 1:

        date2 = xldate_from_date_tuple((DATA[i+1, 0].astype('int'),
                                        DATA[i+1, 1].astype('int'),
                                        DATA[i+1, 2].astype('int')), 0)

        # If dates 1 and 2 are not consecutive, add a nan row to DATA
        # after date 1.
        if date2 - date1 > 1:
            date2insert = np.array(xldate_as_tuple(date1 + 1, 0))[:3]
            row2insert = np.append(date2insert, nan2insert)
            DATA = np.insert(DATA, i + 1, row2insert, 0)

        date1 += 1
        i += 1

    return DATA


#==============================================================================
def calculate_normals(DATA, datatypes):
    """
    Calculates monthly normals from daily average air temperature and
    total daily precipitation time series.

    It is assumed that the datased passed through DATA is complete, in
    chronological order, without ANY missing value.

    {2d numpy matrix} DATA = Rows are the time and columns are the variables.

                             The first three should be a time series containing
                             the year, month, an day of the month, respectively.

                             The remaining columns should contains the weather
                             data. 1 columnd -> 1 weather variable.

    {1d list} datatype = This is the type of data for which normals are being
                         calculated. It defines the operation that is goind to
                         be done to compute the normals. If this value is
                         None, all variable are assumed to be of type 0.

                         0 -> need to be averaged over a month
                              (e.g. Air Temperature, air humidity)

                         1 -> need to be summed over a month
                              (e.g. Precipitation, ETP)
    """
#==============================================================================

    print('---- calculating normals ----')

    #---- assign new variables from input ----

    nvar = len(DATA[0, 3:]) # number of weather variables

    if datatypes == None or len(datatypes) < nvar:
        print('datatype incorrect or non existent. Assuming all variables ' +
              'to be of type 0')
        datatypes = [0] * nvar

    YEAR = DATA[:, 0].astype(int)
    MONTH = DATA[:, 1].astype(int)
    X = DATA[:, 3:]

    #--------------------------------------- Do each month, for every year ----

    # Calculate the average value for each months of each year

    nyear = np.ptp(YEAR) + 1 # Range of values (max - min) along an axis
    flagIncomplete = False

    XMONTH = np.zeros((nyear, 12, nvar)) * np.nan
    for k in range(nvar):
        Xk = X[:, k]
        for j in range(nyear):
            for i in range(12):

                indx = np.where((YEAR == j+YEAR[0]) & (MONTH == i+1))[0]
                Nday = monthrange(j+YEAR[0], i+1)[1]

                if len(indx) < Nday:
                    # Default nan value will be kept in XMONTH. A flag is
                    # raised and a comment is issued afterward.

                    flagIncomplete = True

                else:

                    if datatypes[k] == 0:
                        XMONTH[j, i, k] = np.mean(Xk[indx])
                    elif datatypes[k] == 1:
                        XMONTH[j, i, k] = np.sum(Xk[indx])
    if flagIncomplete:
        print('Some months were not complete and were not considered in ' +
              'the calculation of the weather normals.')

    # Produde a monthly series for saving to a file higher up in the code
    # structure.

    MTHSER = [['Year', 'Month', 'Daily Tmax (degC)', 'Daily Tmin (degC)',
               'Daily Tavg (degC)', 'Total Precip (mm)', 'ETP (mm)']]
    for i in range(nyear):
        for j in range(12):
            MTHSER.append([i+YEAR[0], j+1])
            MTHSER[-1].extend(XMONTH[i, j, :-1])

    #----------------------------------------------- compute monthly normals --

    # Calculate the normals for each month. This is done by calculating the
    # mean of the monthly value computed in the above section.

    XNORM = np.zeros((12, nvar)) * np.nan

    for k in range(nvar):
        for i in range(12):

            indx = np.where(~np.isnan(XMONTH[:, i, k]))[0]

            if len(indx) > 0:

                XNORM[i, k] = np.mean(XMONTH[indx, i, k])

            else:

                # Default nan value is kept in the array.

                print('WARNING, some months are empty with no data.')

    return XNORM, MTHSER


#==============================================================================
def calculate_ETP(DATE, TAVG, LAT, Ta):
    """
    Daily potential evapotranspiration (mm) is calculated with a method adapted
    from Thornwaite (1948).

    Requires at least a year of data.

    #----- INPUT -----

    {1d numpy array} TIME = Numeric time in days
    {1d numpy array} TAVG = Daily temperature average (deg C)
    {float}          LAT = Latitude in degrees
    {1d numpy array} Ta = Monthly air temperature normals

    #----- OUTPUT -----

    {1d numpy array} ETP: Daily Potential Evapotranspiration (mm)

    #----- SOURCE -----

    Pereira, A.R. and W.O. Pruitt. 2004. Adaptation of the Thornthwaite scheme
        for estimating daily reference evapotranspiration. Agricultural Water
        Management, 66, 251-257.
    """
#==============================================================================

    Ta[Ta < 0] = 0

    I = np.sum((0.2 * Ta) ** 1.514) # Heat index
    a = (6.75e-7 * I**3) - (7.71e-5 * I**2) + (1.7912e-2 * I) + 0.49239

    TAVG[TAVG < 0] = 0

    DAYLEN = calculate_daylength(DATE, LAT) # Photoperiod in hr

    ETP = 16 * (10 * TAVG / I)**a * (DAYLEN / (12. * 30))

    return ETP


# =============================================================================
def calculate_daylength(DATE, LAT):
    """
    Calculate the photoperiod for the given latitude at the given time.

    #----- INPUT -----

    {1D array} TIME = Numeric time in days.
    {float}     LAT = latitude in decimal degrees.

    #----- OUTPUT -----

    {1D array} DAYLEN = photoperiod in hr.
    """
# =============================================================================

    DATE = DATE.astype(int)
    pi = np.pi
    LAT = np.radians(LAT)  # Latitude in rad

    # ----- CONVERT DAY FORMAT -----

    # http://stackoverflow.com/questions/13943062

    N = len(DATE[:, 0])
    DAY = np.zeros(N)
    for i in range(N):
        DAY[i] = int(date(DATE[i, 0], DATE[i, 1],DATE[i, 2]).timetuple().tm_yday)
        DAY[i] = int(DAY[i])

    # ----------------------------------------------- DECLINATION OF THE SUN --

    # http://en.wikipedia.org/wiki/Position_of_the_Sun#Calculations

    N = DAY - 1

    A = 2 * pi / 365.24 * (N - 2)
    B = 2 * pi / pi * 0.0167
    C = 2 * pi / 365.24 * (N + 10)

    D = -23.44 * pi / 180.

    SUNDEC = np.arcsin(np.sin(D) * np.cos(C + B * np.sin(A)))

    # ----------------------------------------------------- SUNRISE EQUATION --

    # http:/Omega/en.wikipedia.org/wiki/Sunrise_equation

    OMEGA = np.arccos(-np.tan(LAT) * np.tan(SUNDEC))

    # ------------------------------------------------------- HOURS OF LIGHT --

    # http://physics.stackexchange.com/questions/28563/
    #        hours-of-light-per-day-based-on-latitude-longitude-formula

    DAYLEN = OMEGA * 2 * 24 / (2 * np.pi)  # Day length in hours

    return DAYLEN


# =============================================================================


class FigWeatherNormals(FigureCanvasQTAgg):
    """
    This is the class that does all the plotting of the weather normals.

    ax0 is used to plot precipitation
    ax1 is used to plot air temperature
    ax3 is used to plot the legend on top of the graph.

    """

    def __init__(self, lang='English'):

        fw, fh = 8.5, 5.
        fig = mpl.figure.Figure(figsize=(fw, fh), facecolor='white')

        super(FigWeatherNormals, self).__init__(fig)

        self.lang = lang
        self.NORMALS = []

        labelDB = LabelDataBase(self.lang)
        month_names = labelDB.month_names

        # --------------------------------------------------- Define Margins --

        left_margin = 1. / fw
        right_margin = 1. / fw
        bottom_margin = 0.35 / fh
        top_margin = 0.1 / fh

        # ------------------------------------------------ Yearly Avg Labels --

        # The yearly yearly averages for the mean air temperature and
        # the total precipitation are displayed in <ax3>, which is placed on
        # top of the axes that display the data (<ax0> and <ax1>).

        ax3 = fig.add_axes([0, 0, 1, 1], zorder=1)  # temporary position
        ax3.patch.set_visible(False)
        ax3.spines['bottom'].set_visible(False)
        ax3.tick_params(axis='both', bottom='off', top='off', left='off',
                        right='off', labelbottom='off', labeltop='off',
                        labelleft='off', labelright='off')

        # ---- Mean Annual Air Temperature ----

        # Places first label at the top left corner of <ax3> with a horizontal
        # padding of 5 points and downward padding of 3 points.

        dx, dy = 5/72., -3/72.
        padding = mpl.transforms.ScaledTranslation(dx, dy, fig.dpi_scale_trans)
        transform = ax3.transAxes + padding

        ax3.text(0., 1., 'Mean Annual Air Temperature',
                 fontsize=13, va='top', transform=transform)

        # ---- Mean Annual Precipitation ----

        # Get the bounding box of the first label.

        renderer = self.get_renderer()
        bbox = ax3.texts[0].get_window_extent(renderer)
        bbox = bbox.transformed(ax3.transAxes.inverted())

        # Places second label below the first label with a horizontal
        # padding of 5 points and downward padding of 3 points.

        ax3.text(0., bbox.y0, 'Mean Annual Precipitation',
                 fontsize=13, va='top', transform=transform)

        bbox = ax3.texts[1].get_window_extent(renderer)
        bbox = bbox.transformed(fig.transFigure.inverted())

        # ---- update geometry ----

        # Updates the geometry and position of <ax3> to accomodate the text.

        x0 = left_margin
        axw = 1 - (left_margin + right_margin)
        axh = 1 - bbox.y0 - (dy / fw)
        y0 = 1 - axh - top_margin

        ax3.set_position([x0, y0, axw, axh])

        # -------------------------------------------------------- Data Axes --

        axh = y0 - bottom_margin
        y0 = y0 - axh

        # ---- Precip ----

        ax0 = fig.add_axes([x0, y0, axw, axh], zorder=1)
        ax0.patch.set_visible(False)
        ax0.spines['top'].set_visible(False)
        ax0.set_axisbelow(True)

        # ---- Air Temp. ----

        ax1 = fig.add_axes(ax0.get_position(), frameon=False, zorder=5,
                           sharex=ax0)

        # ----------------------------------------------------- INIT ARTISTS --

        # This is only to initiates the artists and to set their parameters
        # in advance. The plotting of the data is actually done by calling
        # the <plot_monthly_normals> method.

        XPOS = np.arange(-0.5, 12.51, 1)
        y = range(len(XPOS))
        colors = ['#990000', '#FF0000', '#FF6666']

        # ---- Tmax ----

        htmax, = ax1.plot(XPOS, y, color=colors[0], clip_on=True, ls='--',
                          lw=1.5, zorder=100)

        # ---- Tmean ----

        htavg, = ax1.plot(XPOS, y, color=colors[1], clip_on=True, marker='o',
                          ls='--', ms=6, zorder=100, mec=colors[1],
                          mfc='white', mew=1.5, lw=1.5)

        # ---- Tmin ----

        htmin, = ax1.plot(XPOS, y, color=colors[2], clip_on=True, ls='--',
                          lw=1.5, zorder=100)

        # ------------------------------------------------- XTICKS FORMATING --

        Xmin0 = 0
        Xmax0 = 12.001

        # ---- major ----

        ax0.xaxis.set_ticks_position('bottom')
        ax0.tick_params(axis='x', direction='out')
        ax0.xaxis.set_ticklabels([])
        ax0.set_xticks(np.arange(Xmin0, Xmax0))

        ax1.tick_params(axis='x', which='both', bottom='off', top='off',
                        labelbottom='off')

        # ---- minor ----

        ax0.set_xticks(np.arange(Xmin0+0.5, Xmax0+0.49, 1), minor=True)
        ax0.tick_params(axis='x', which='minor', direction='out',
                        length=0, labelsize=13)
        ax0.xaxis.set_ticklabels(month_names, minor=True)

        # ------------------------------------------------- Yticks Formating --

        # ---- Precipitation ----

        ax0.yaxis.set_ticks_position('right')
        ax0.tick_params(axis='y', direction='out', labelsize=13)

        ax0.tick_params(axis='y', which='minor', direction='out')
        ax0.yaxis.set_ticklabels([], minor=True)

        # ---- Air Temp. ----

        ax1.yaxis.set_ticks_position('left')
        ax1.tick_params(axis='y', direction='out', labelsize=13)

        ax1.tick_params(axis='y', which='minor', direction='out')
        ax1.yaxis.set_ticklabels([], minor=True)

        # ------------------------------------------------------------- GRID --

    #    ax0.grid(axis='y', color=[0.5, 0.5, 0.5], linestyle=':', linewidth=1,
    #             dashes=[1, 5])
    #    ax0.grid(axis='y', color=[0.75, 0.75, 0.75], linestyle='-',
#                 linewidth=0.5)

        # ------------------------------------------------------------ XLIMS --

        ax0.set_xlim(Xmin0, Xmax0)

        # ------------------------------------------------------ Plot Legend --

        self.plot_legend()

    def set_lang(self, lang):  # ============================== Set Language ==
        self.lang = lang
        if len(self.NORMALS) == 0:
            return
        self.plot_legend()
        self.set_axes_labels()
        self.update_yearly_avg()
        month_names = LabelDataBase(self.lang).month_names
        self.figure.axes[1].xaxis.set_ticklabels(month_names, minor=True)

    def plot_legend(self):  # =================================================

        ax = self.figure.axes[2]  # Axe on which the legend is hosted

        # --- bbox transform --- #

        padding = mpl.transforms.ScaledTranslation(5/72., -5/72.,
                                                   self.figure.dpi_scale_trans)
        transform = ax.transAxes + padding

        # --- proxy artists --- #

        colors = Colors()
        colors.load_colors_db()

        rec1 = mpl.patches.Rectangle((0, 0), 1, 1, fc=colors.rgb[2], ec='none')
        rec2 = mpl.patches.Rectangle((0, 0), 1, 1, fc=colors.rgb[1], ec='none')

        # --- legend entry --- #

        lines = [ax.lines[0], ax.lines[1], ax.lines[2], rec2, rec1]
        labelDB = LabelDataBase(self.lang)
        labels = [labelDB.Tmax, labelDB.Tavg, labelDB.Tmin,
                  labelDB.rain, labelDB.snow]

        # --- plot legend --- #

        leg = ax.legend(lines, labels, numpoints=1, fontsize=13,
                        borderaxespad=0, loc='upper left', borderpad=0,
                        bbox_to_anchor=(0, 1), bbox_transform=transform)
        leg.draw_frame(False)


    def plot_monthly_normals(self, NORMALS): #=================================

        self.NORMALS = NORMALS

        #-------------------------------------------- assign local variables --

        Tmax_norm = NORMALS[:, 0]
        Tmin_norm = NORMALS[:, 1]
        Tavg_norm = NORMALS[:, 2]
        Ptot_norm = NORMALS[:, 3]
        Rain_norm = NORMALS[:, -1]
        Snow_norm = Ptot_norm - Rain_norm

        print('Tmax Yearly Avg. = %0.1f' % np.mean(Tmax_norm))
        print('Tmin Yearly Avg. = %0.1f' % np.mean(Tmin_norm))
        print('Tavg Yearly Avg. = %0.1f' % np.mean(Tavg_norm))
        print('Ptot Yearly Acg. = %0.1f' % np.sum(Ptot_norm))

        #------------------------------------------------- DEFINE AXIS RANGE --

        if np.sum(Ptot_norm) < 500:
            Yscale0 = 10 # Precipitation (mm)
        else:
            Yscale0 = 20

        Yscale1 = 5 # Temperature (deg C)

        SCA0 = np.arange(0, 10000, Yscale0)
        SCA1 = np.arange(-100, 100, Yscale1)

        #---- Precipitation ----

        indx = np.where(SCA0 > np.max(Ptot_norm))[0][0]
        Ymax0 = SCA0[indx+1]

        indx = np.where(SCA0 <= np.min(Snow_norm))[0][-1]
        Ymin0 = SCA0[indx]

        NZGrid0 = (Ymax0 - Ymin0) / Yscale0

        #---- Temperature ----

        indx = np.where(SCA1 > np.max(Tmax_norm))[0][0]
        Ymax1 = SCA1[indx]

        indx = np.where(SCA1 < np.min(Tmin_norm))[0][-1]
        Ymin1 = SCA1[indx]

        NZGrid1 = (Ymax1 - Ymin1) / Yscale1

        #---- Uniformization Of The Grids ----

        if NZGrid0 > NZGrid1:
            Ymin1 = Ymax1 - NZGrid0 * Yscale1
        elif NZGrid0 < NZGrid1:
            Ymax0 = Ymin0 + NZGrid1 * Yscale0
        elif NZGrid0 == NZGrid1:
            pass

        #---- Adjust Space For Text ----

        # In case there is a need to force the value
        #----
        #Ymax0 = 200
        #Ymax1 = 30 ; Ymin1 = -20
        #----

        #-------------------------------------------------- YTICKS FORMATING --

        ax0 = self.figure.axes[1]
        ax1 = self.figure.axes[2]
        ax3 = self.figure.axes[0]

        #---- Precip (host) ----

        yticks = np.arange(Ymin0, Ymax0 + Yscale0/10., Yscale0)
        ax0.set_yticks(yticks)

        yticks_minor = np.arange(yticks[0], yticks[-1], 5)
        ax0.set_yticks(yticks_minor, minor=True)

        #---- Air Temp ----

        yticks1 = np.arange(Ymin1, Ymax1 + Yscale1/10., Yscale1)
        ax1.set_yticks(yticks1)

        yticks1_minor = np.arange(yticks1[0], yticks1[-1], Yscale1/5.)
        ax1.set_yticks(yticks1_minor, minor=True)

        #---------------------------------------------------- SET AXIS RANGE --

        ax0.set_ylim(Ymin0, Ymax0)
        ax1.set_ylim(Ymin1, Ymax1)

        #------------------------------------------------------------ LABELS --

        self.set_axes_labels()

        #---------------------------------------------------------- PLOTTING --

        self.plot_precip(Ptot_norm, Snow_norm)
        self.plot_air_temp(Tmax_norm, Tmin_norm, Tavg_norm)
        self.update_yearly_avg()

        #---------------------------------------------------------- Clipping --

        # There is currently a bug regarding this. So we need to do a
        # workaround

        x0, x1 = ax1.get_position().x0, ax1.get_position().x1
        y0, y1 = ax1.get_position().y0, ax3.get_position().y1

        dummy_ax = self.figure.add_axes([x0, y0, x1-x0, y1-y0])
        dummy_ax.patch.set_visible(False)
        dummy_ax.axis('off')

        dummy_plot, = dummy_ax.plot([], [], clip_on=True)

        clip_bbox = dummy_plot.get_clip_box()

        for line in ax1.lines:
            line.set_clip_box(clip_bbox)

    def set_axes_labels(self):
        labelDB = LabelDataBase(self.lang)

        ax0 = self.figure.axes[1]
        ax0.set_ylabel(labelDB.Plabel, va='bottom', fontsize=16, rotation=270)
        ax0.yaxis.set_label_coords(1.09, 0.5)

        ax1 = self.figure.axes[2]
        ax1.set_ylabel(labelDB.Tlabel, va='bottom', fontsize=16)
        ax1.yaxis.set_label_coords(-0.09, 0.5)

    def plot_precip(self, PNORM, SNORM):  # ===================================

        # ---- define vertices manually ----

        Xmid = np.arange(0.5, 12.5, 1)
        n = 0.5   # Controls the width of the bins
        f = 0.65  # Controls the spacing between the bins

        Xpos = np.vstack((Xmid - n * f,
                          Xmid - n * f,
                          Xmid + n * f,
                          Xmid + n * f)).transpose().flatten()

        Ptot = np.vstack((PNORM * 0,
                          PNORM,
                          PNORM,
                          PNORM * 0)).transpose().flatten()

        Snow = np.vstack((SNORM * 0,
                          SNORM,
                          SNORM,
                          SNORM * 0)).transpose().flatten()

        #-- plot data --

        ax = self.figure.axes[1]

        for collection in reversed(ax.collections):
            collection.remove()

        colors = Colors()
        colors.load_colors_db()

        ax.fill_between(Xpos, 0., Ptot, edgecolor='none',
                        color=colors.rgb[1])
        ax.fill_between(Xpos, 0., Snow, edgecolor='none',
                        color=colors.rgb[2])

    def plot_air_temp(self, Tmax_norm, Tmin_norm, Tavg_norm): #=== Air Temp. ==

        Tavg_norm = np.hstack((Tavg_norm[-1], Tavg_norm, Tavg_norm[0]))
        Tmin_norm = np.hstack((Tmin_norm[-1], Tmin_norm, Tmin_norm[0]))
        Tmax_norm = np.hstack((Tmax_norm[-1], Tmax_norm, Tmax_norm[0]))

        for i, Tnorm in enumerate([Tmax_norm, Tavg_norm, Tmin_norm]):
            self.figure.axes[2].lines[i].set_ydata(Tnorm)


    def update_yearly_avg(self): #======================= Update Yearly Avg. ==

        Tavg_norm = self.NORMALS[:, 2]
        Ptot_norm = self.NORMALS[:, 3]

        ax = self.figure.axes[0]

        #---- update position ----

        bbox = ax.texts[0].get_window_extent(self.get_renderer())
        bbox = bbox.transformed(ax.transAxes.inverted())

        ax.texts[1].set_position((0, bbox.y0))

        #---- update labels ----
        labelDB = LabelDataBase(self.lang)

        ax.texts[0].set_text(labelDB.Tyrly % np.mean(Tavg_norm))
        ax.texts[1].set_text(labelDB.Pyrly % np.sum(Ptot_norm))


# =============================================================================

class GridWeatherNormals(QtGui.QTableWidget):

# =============================================================================

    def __init__(self, parent=None):
        super(GridWeatherNormals, self).__init__(parent)

        self.initUI()

    def initUI(self): #====================================================

        StyleDB = db.styleUI()

        #--------------------------------------------------------- Style --

        fnt = StyleDB.font1
        fnt.setPointSize(10)
        self.setFont(StyleDB.font1)

        self.setFrameStyle(StyleDB.frame)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
#        self.setMinimumWidth(650)

        #-------------------------------------------------------- Header --


        HEADER = ('JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL',
                  'AUG', 'SEP', 'OCT', 'NOV', 'DEC', 'YEAR')

        self.setColumnCount(len(HEADER))
        self.setHorizontalHeaderLabels(HEADER)

        self.setRowCount(7)
        self.setVerticalHeaderLabels([u'Daily Tmax (°C)', u'Daily Tmin (°C)',
                                      u'Daily Tavg (°C)', u'Rain (mm)',
                                      u'Snow (mm)', u'Total Precip (mm)',
                                      'ETP (mm)'])

    def populate_table(self, NORMALS):

        # ---- Air Temperature ----

        for row in range(3):
            # Months
            for col in range(12):
                item = QtGui.QTableWidgetItem('%0.1f' % NORMALS[col, row])
                item.setFlags(~QtCore.Qt.ItemIsEditable)
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.setItem(row, col, item)

            # Year
            yearVal = np.mean(NORMALS[:, row])
            item = QtGui.QTableWidgetItem('%0.1f' % yearVal)
            item.setFlags(~QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.setItem(row, 12, item)

        # ---- Rain ----

        row = 3
        # Months
        for col in range(12):
            item = QtGui.QTableWidgetItem('%0.1f' % NORMALS[col, -1])
            item.setFlags(~QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.setItem(row, col, item)

        # Year
        yearVal = np.sum(NORMALS[:, -1])
        item = QtGui.QTableWidgetItem('%0.1f' % yearVal)
        item.setFlags(~QtCore.Qt.ItemIsEditable)
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.setItem(row, 12, item)

        # ---- Snow ----

        row = 4
        # Months
        for col in range(12):
            snow4cell = NORMALS[col, 3] - NORMALS[col, -1]
            item = QtGui.QTableWidgetItem('%0.1f' % snow4cell)
            item.setFlags(~QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.setItem(row, col, item)
        # Year
        yearVal = np.sum(NORMALS[:, 3] - NORMALS[:, -1])
        item = QtGui.QTableWidgetItem('%0.1f' % yearVal)
        item.setFlags(~QtCore.Qt.ItemIsEditable)
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.setItem(row, 12, item)

        # ---- Total Precip ----

        row = 5
        # Months
        for col in range(12):
            item = QtGui.QTableWidgetItem('%0.1f' % NORMALS[col, 3])
            item.setFlags(~QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.setItem(row, col, item)
        # Year
        yearVal = np.sum(NORMALS[:, 3])
        item = QtGui.QTableWidgetItem('%0.1f' % yearVal)
        item.setFlags(~QtCore.Qt.ItemIsEditable)
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.setItem(row, 12, item)

        # ---- ETP ----

        row = 6
        for col in range(12):
            item = QtGui.QTableWidgetItem('%0.1f' % NORMALS[col, 4])
            item.setFlags(~QtCore.Qt.ItemIsEditable)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.setItem(row, col, item)
        # Year
        yearVal = np.sum(NORMALS[:, 4])
        item = QtGui.QTableWidgetItem('%0.1f' % yearVal)
        item.setFlags(~QtCore.Qt.ItemIsEditable)
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.setItem(row, 12, item)

        self.resizeColumnsToContents()

if __name__ == '__main__':
#    plt.rc('font',family='Arial')

    app = QtGui.QApplication(sys.argv)

#    fmeteo = "Files4testing/Daily - SASKATOON DIEFENBAKER & RCS_1980-2014.out"
    fmeteo = "Files4testing/TORONTO LESTER B. PEARSON INT'L _1980-2010.out"
#    fmeteo = "Files4testing/BONSECOURS (7020828)_1980-2009.out"
#   fmeteo = "Files4testing/FORTIERVILLE (7022494)_2013-2015.out"

    w = WeatherAvgGraph()
    w.save_fig_dir =  '../Projects/Monteregie Est'
    w.meteo_dir = '../Projects/Monteregie Est/Meteo/Output'
    w.show()
    w.set_lang('English')
    w.generate_graph(fmeteo)
#    w.fig_weather_normals.figure.savefig('test.pdf')
#    w.save_normal_table('test.csv')
#    for i in range(250):
#        w.generate_graph(fmeteo)
#        QtCore.QCoreApplication.processEvents()
#        QtCore.QCoreApplication.processEvents()

    app.exec_()