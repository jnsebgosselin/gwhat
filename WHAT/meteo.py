# -*- coding: utf-8 -*-
"""
Copyright 2014-2015 Jean-Sebastien Gosselin

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

last_modification = 15/06/2015
"""
      
#----- STANDARD LIBRARY IMPORTS -----
       
import csv
from calendar import monthrange
from sys import argv
from os import path, getcwd
import time
from datetime import date

#----- THIRD PARTY IMPORTS -----

from xlrd.xldate import xldate_from_date_tuple
from xlrd import xldate_as_tuple

import numpy as np
from PySide import QtGui, QtCore

import matplotlib
matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4']='PySide'
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
import matplotlib.pyplot as plt

#---- PERSONAL IMPORTS ----

import database as db

class LabelDataBase():  
    
    
    def __init__(self, language):
        
        self.ANPRECIP = 'Annual Total Precipitation (mm)'
        self.ANTEMP = u'Average Annual Air Temperature (°C)'
        
        self.month_names = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                            "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        
        if language == 'French':
            'Option not available at the moment'
            
class Tooltips():
    
    def __init__(self, language): #------------------------------- ENGLISH -----
        
        self.save = 'Save graph'
        self.open = "Open a valid '.out' weather data file"
        self.addTitle = 'Add A Title To The Figure Here (Option not yet available)'
        
        if language == 'French': #--------------------------------- FRENCH -----
            
            pass
            
class WeatherAvgGraph(QtGui.QWidget):
    
    def __init__(self, parent=None):
        super(WeatherAvgGraph, self).__init__(parent)

        self.initUI()
        
    def initUI(self):
        
        iconDB = db.Icons()
        StyleDB = db.styleUI()
        ttipDB = Tooltips('English')
        self.station_name = []
        self.save_fig_dir = getcwd()
        self.meteo_dir = getcwd()
        
        self.setWindowTitle('Weather Averages')
        self.setFont(StyleDB.font1)
        self.setWindowIcon(iconDB.WHAT)
        
        #----------------------------------------------------- FigureCanvas ----
        
        self.fig = plt.figure()        
        self.fig.set_size_inches(8.5, 5)        
        self.fig.patch.set_facecolor('white')
        self.fig_widget = FigureCanvasQTAgg(self.fig)
        
        #---------------------------------------------------------- TOOLBAR ----
        
        self.btn_save = QtGui.QToolButton()
        self.btn_save.setAutoRaise(True)
        self.btn_save.setIcon(iconDB.save)
        self.btn_save.setToolTip(ttipDB.save)
        self.btn_save.setFocusPolicy(QtCore.Qt.NoFocus)
        
        self.btn_open = QtGui.QToolButton()
        self.btn_open.setAutoRaise(True)
        self.btn_open.setIcon(iconDB.openFile)
        self.btn_open.setToolTip(ttipDB.open)
        self.btn_open.setFocusPolicy(QtCore.Qt.NoFocus)
        
        self.graph_title = QtGui.QLineEdit()
        self.graph_title.setMaxLength(65)
        self.graph_title.setEnabled(False)
        self.graph_title.setText('Add A Title To The Figure Here')
        self.graph_title.setToolTip(ttipDB.addTitle)
        
        self.graph_status = QtGui.QCheckBox()
        self.graph_status.setEnabled(False)
        
        separator1 = QtGui.QFrame()
        separator1.setFrameStyle(StyleDB.VLine)
        
        subgrid_toolbar = QtGui.QGridLayout()
        toolbar_widget = QtGui.QWidget()
        
        row = 0
        col = 0
#        subgrid_toolbar.addWidget(self.btn_open, row, col)        
#        col += 1
        subgrid_toolbar.addWidget(self.btn_save, row, col)
        col += 1
        subgrid_toolbar.addWidget(separator1, row, col) 
#        col += 1
#        subgrid_toolbar.addWidget(graph_title_label, row, col)
        col += 1
        subgrid_toolbar.addWidget(self.graph_title, row, col)
        subgrid_toolbar.setColumnStretch(col, 4)
        col += 1
        subgrid_toolbar.addWidget(self.graph_status, row, col)
                
        subgrid_toolbar.setHorizontalSpacing(5)
        subgrid_toolbar.setContentsMargins(0, 0, 0, 0)
#        subgrid_toolbar.setColumnMinimumWidth(col+1, 500)
                
        self.btn_save.setIconSize(StyleDB.iconSize)
        self.btn_open.setIconSize(StyleDB.iconSize)
        self.graph_title.setFixedHeight(StyleDB.size1)
        
        toolbar_widget.setLayout(subgrid_toolbar)
        
        #-------------------------------------------------------- MAIN GRID ----
        
        mainGrid = QtGui.QGridLayout()
        
        row = 0 
        mainGrid.addWidget(toolbar_widget, row, 0)
        row += 1
        mainGrid.addWidget(self.fig_widget, row, 0)
                
        mainGrid.setContentsMargins(15, 15, 15, 15) # Left, Top, Right, Bottom 
        mainGrid.setSpacing(15)
        mainGrid.setRowStretch(1, 500)
        mainGrid.setColumnStretch(0, 500)
        
        self.setLayout(mainGrid)
        
        #------------------------------------------------------------ EVENT ----
        
        self.btn_save.clicked.connect(self.save_graph)
        self.btn_open.clicked.connect(self.select_meteo_file)
        
    def generate_graph(self, filename): #=======================================
        
        METEO = MeteoObj()
        METEO.load(filename)
        
        self.station_name = METEO.station_name
        self.setWindowTitle('Weather Averages for %s' % self.station_name)
        
        YEAR = METEO.YEAR
        MONTH = METEO.MONTH
        TAVG = METEO.TAVG
        TMIN = METEO.TMIN
        TMAX = METEO.TMAX
        PTOT = METEO.PTOT
        RAIN = METEO.RAIN
        
        Tmin_norm, Tmax_norm, TNORM, PNORM, RNORM = calculate_normals(
                                      YEAR, MONTH, TMIN, TMAX, TAVG, PTOT, RAIN)
                                                  
        plot_monthly_normals(self.fig, Tmin_norm, Tmax_norm, TNORM, 
                                       PNORM, RNORM)
                
        self.fig_widget.draw()

    def save_graph(self): #=====================================================
        
        dialog_dir = self.save_fig_dir
        dialog_dir += '/WeatherAverages_%s' % self.station_name
        
        dialog = QtGui.QFileDialog()
        dialog.setConfirmOverwrite(True)
        filename, ftype = dialog.getSaveFileName(
                                          caption="Save Figure", dir=dialog_dir,
                                          filter=('*.pdf;;*.svg'))
                                  
        if filename:         
            
            if filename[-4:] != ftype[1:]:
                # Add a file extension if there is none.
                filename = filename + ftype[1:]
                
            self.save_fig_dir = path.dirname(filename)    
            self.fig.savefig(filename)   

    def select_meteo_file(self):
        dialog_dir = self.meteo_dir
        filename, _ = QtGui.QFileDialog.getOpenFileName(
                                   self, 'Select a valid weather data file', 
                                   dialog_dir, '*.out') 
                                   
        if filename:
            self.generate_graph(filename)
            self.meteo_dir = path.dirname(filename)
            
#===============================================================================        
class MeteoObj():
    """
    NaN are assigned a value of 0 for Ptot and for air Temp, the value is 
    calculated with an in-station interpolation.
    """
#===============================================================================    

    def __init__(self):
        
        self.TIME = []  # Time in numeric format (days)
        self.TMAX = []  # Daily maximum temperature (deg C)
        self.TMIN = []  # Daily minimum temperature (deg C)
        self.TAVG = []  # Daily mean temperature (deg C)
        self.PTOT = []  # Daily total precipitation (mm)
        self.RAIN = []  # Daily total liquid precipitation (mm)
        self.ETP = []   # Daily potential evapotranspiration (mm)
        
        self.YEAR = []
        self.MONTH = []
        
        self.TIMEwk = []
        self.TMAXwk = []
        self.PTOTwk = []
        self.RAINwk = []
        
        self.info = []
        self.station_name = []
        self.LAT = []
        self.LON = []
        
        self.varnames = []
    
    def clean_endsof_file(self, DATA): #========================================
        
        """
        Remove nan values at the beginning and end of the record if any.
        """
        
        #---- Beginning ----
        
        for i in range(len(DATA[:, 0])):
            if np.all(np.isnan(DATA[i, 3:])):
                DATA = np.delete(DATA, i, axis=0)
            else:
                break
            
        #---- End ----
            
        for i in range(len(DATA[:, 0])):
            if np.all(np.isnan(DATA[-i, 3:])):
                DATA = np.delete(DATA, -i, axis=0)
            else:
                break   

        return DATA
        
        
    def load(self, fname): #====================================================
        
        with open(fname, 'rb') as f:
            reader = list(csv.reader(f, delimiter='\t'))

        for i in range(len(reader)):
            
            if len(reader[i]) > 0 :

                if reader[i][0] == 'Station Name':
                    print reader[i][0]
                    self.station_name = reader[i][1]
                elif reader[i][0] == 'Latitude':
                    self.LAT = reader[i][1]
                elif reader[i][0] == 'Longitude':
                    self.LON = reader[i][1]    
                elif reader[i][0] == 'Year':
                    self.varnames = np.array(reader[i])
                    data_indx = i + 1
                    break

        DATA = np.array(reader[data_indx:]).astype('float')
        
        #----------------------------------------------- clean ends of data ----
        
        DATA = self.clean_endsof_file(DATA)
            
        #-------------------------------------------- CHECK TIME CONTINUITY ----
        
        #Check if data are continuous over time.
        time_start = xldate_from_date_tuple((DATA[0, 0].astype('int'),
                                             DATA[0, 1].astype('int'),
                                             DATA[0, 2].astype('int')), 0)

        time_end = xldate_from_date_tuple((DATA[-1, 0].astype('int'),
                                           DATA[-1, 1].astype('int'),
                                           DATA[-1, 2].astype('int')), 0)
        
        # Check if the data series is continuous over time and 
        # correct it if not
        if time_end - time_start + 1 != len(DATA[:,0]):
            print reader[0][1], ' is not continuous, correcting...'
            DATA = make_timeserie_continuous(DATA)        
        
        #Generate a 1D array with date in numeric format
        TIME = np.arange(time_start, time_end + 1)
        
        #----------------------------------------------- REASSIGN VARIABLES ----
        
        TMAX = DATA[:, 3]
        TMIN = DATA[:, 4]
        TAVG = DATA[:, 5]
        PTOT = DATA[:, 6] 
        
        #----------------------------------------------------- ESTIMATE NAN ----

        PTOT[np.isnan(PTOT)] = 0
        
        nonanindx = np.where(~np.isnan(TMAX))[0]
        if len(nonanindx) < len(TMAX):
            TMAX = np.interp(TIME, TIME[nonanindx], TMAX[nonanindx])
            
        nonanindx = np.where(~np.isnan(TMIN))[0]
        if len(nonanindx) < len(TMIN):
            TMIN = np.interp(TIME, TIME[nonanindx], TMIN[nonanindx])
   
        #---------------------------------------------------- ESTIMATE RAIN ----
        
        RAIN = np.copy(PTOT)
        RAIN[np.where(TAVG < 0)[0]] = 0
        
        #------------------------------------------------- UPDATE CLASS VAR ----
    
        self.TIME = TIME
        self.TMAX = TMAX
        self.TAVG = TAVG
        self.TMIN = TMIN
        self.PTOT = PTOT
        self.RAIN = RAIN
        
        self.YEAR = DATA[:, 0].astype(int)
        self.MONTH = DATA[:, 1].astype(int)
        
        #-------------------------------------------------------------- ETP ----
        
        if np.any(self.varnames == 'ETP (mm)'):
            
            self.ETP = DATA[:, 7]
            
            # Estimate missing values if applicable
            
            nonanindx = np.where(~np.isnan(self.ETP))[0]
            if len(nonanindx) < len(TMAX):
                self.ETP = np.interp(TIME, TIME[nonanindx],
                                     self.ETP[nonanindx])                
                
        else:
            print('Daily ETP is not included in the file.')
            
        #--------------------------------------- DAILY TO WEEKLY CONVERSION ----        
        
        bwidth = 7.
        nbin = np.floor(len(TIME) / bwidth)
           
        #---- Alternate Method (more efficient) ----
        
        TIMEbin = TIME[:nbin*bwidth].reshape(nbin, bwidth)
        TIMEbin = np.mean(TIMEbin, axis=1)
      
        TMAXbin = TMAX[:nbin*bwidth].reshape(nbin, bwidth)
        TMAXbin = np.mean(TMAXbin, axis=1)
        
        PTOTbin = PTOT[:nbin*bwidth].reshape(nbin, bwidth)
        PTOTbin = np.sum(PTOTbin, axis=1)
        
        RAINbin = RAIN[:nbin*bwidth].reshape(nbin, bwidth)
        RAINbin = np.sum(RAINbin, axis=1)
        
        nres = len(TIME) - (nbin * bwidth)
        print 'Nbin residual =', nres
                
        #------------------------------------------------- UPDATE CLASS VAR ----

#        self.TIMEwk = TIMEwk
#        self.TMAXwk = TMAXwk
#        self.PTOTwk = PTOTwk
#        self.RAINwk = RAINwk
        self.TIMEwk = TIMEbin
        self.TMAXwk = TMAXbin
        self.PTOTwk = PTOTbin
        self.RAINwk = RAINbin
        
        #----------------------------------------------------- STATION INFO ----
        
        FIELDS = ['Station', 'Province', 'Latitude', 'Longitude', 'Altitude']
                  
        info = '<table border="0" cellpadding="2" cellspacing="0" align="left">'
        for i in range(len(FIELDS)):
            
            try:                 
                VAL = '%0.2f' % float(reader[i][1])
            except:
                VAL = reader[i][1]
                 
            info += '''<tr>
                         <td width=10></td>
                         <td align="left">%s</td>
                         <td align="left" width=20>:</td>
                         <td align="left">%s</td>
                       </tr>''' % (FIELDS[i], VAL)
        info += '</table>'
        
        self.info = info
    
    
#===============================================================================
def bin_sum(x, bwidth):
    """
    Sum data x over bins of width "bwidth" starting at indice 0 of x.
    If there is residual data at the end because of the last bin being not
    complete, data are rejected and removed from the reshaped series.
    """
#===============================================================================

    nbin = np.floor(len(x) / bwidth)
    
    bheight = x[:nbin*bwidth].reshape(nbin, bwidth)
    bheight = np.sum(bheight, axis=1)
    
#    nres = len(x) - (nbin * bwidth)
    
    return bheight

#===============================================================================
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
#===============================================================================    
    
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
    
            
#===============================================================================
def plot_monthly_normals(fig, Tmin_norm, Tmax_norm, TNORM, PNORM, RNORM,
                         COLOR=['black', 'black']):
# Plot monthly normals
#===============================================================================
    
    SNORM = PNORM - RNORM
    
    fig.clf()
    
    label_font_size = 16
    
    labelDB = LabelDataBase('English')
    
    month_names = labelDB.month_names
     
    fig.patch.set_facecolor('white')
    
    fheight = fig.get_figheight()
    fwidth = fig.get_figwidth()
    
    left_margin  = 1
    right_margin = 1
    bottom_margin = 0.5
    top_margin = 0.1
    
    x0 = left_margin / fwidth
    y0 = bottom_margin / fheight
    w0 = 1 - (left_margin + right_margin) / fwidth
    h0 = 1 - (bottom_margin + top_margin) / fheight
   
    #---------------------------------------------------------AXES CREATION-----

    ax0  = fig.add_axes([x0, y0, w0, h0])
    ax0.patch.set_visible(False)
    ax1 = fig.add_axes(ax0.get_position(), frameon=False, zorder=1)
    ax1.patch.set_visible(False)
    
    #------------------------------------------------------XTICKS FORMATING----- 
    
    Xmin0 = 0
    Xmax0 = 12.001
    
    ax0.xaxis.set_ticks_position('bottom')
    ax0.tick_params(axis='x',direction='out')
    ax0.xaxis.set_ticklabels([])
    ax0.set_xticks(np.arange(Xmin0, Xmax0))
    
    ax0.set_xticks(np.arange(Xmin0+0.5, Xmax0+0.49, 1), minor=True)
    ax0.tick_params(axis='x', which='minor', direction='out', gridOn=False,
                    length=0, labelsize=13)
    ax0.xaxis.set_ticklabels(month_names, minor=True)
    
    ax1.tick_params(axis='x', which='both', bottom='off', top='off',
                    labelbottom='off')
    
    #--------------------------------------------------- DEFINE AXIS RANGE -----
    
    if np.sum(PNORM) < 500:
        Yscale0 = 10 # Precipitation (mm)
    else:
        Yscale0 = 20
        
    Yscale1 = 5 # Temperature (deg C)
    
    SCA0 = np.arange(0, 10000, Yscale0)
    SCA1 = np.arange(-100, 100, Yscale1)
    
    #----- Precipitation -----
    
    indx = np.where(SCA0 > np.max(PNORM))[0][0]   
    Ymax0 = SCA0[indx+1]
    
    indx = np.where(SCA0 <= np.min(SNORM))[0][-1]
    Ymin0 = SCA0[indx]
    
    NZGrid0 = (Ymax0 - Ymin0) / Yscale0
    
    #----- Temperature -----
    
#    indx = np.where(SCA1 > np.max(TNORM+TSTD))[0][0] 
    indx = np.where(SCA1 > np.max(Tmax_norm))[0][0]
    Ymax1 = SCA1[indx]
    
#    indx = np.where(SCA1 < np.min(TNORM-TSTD))[0][-1] 
    indx = np.where(SCA1 < np.min(Tmin_norm))[0][-1]
    Ymin1 = SCA1[indx]
    
    NZGrid1 = (Ymax1 - Ymin1) / Yscale1
    
    #----- Uniformization Of The Grids -----
    
    if NZGrid0 > NZGrid1:    
        Ymin1 = Ymax1 - NZGrid0 * Yscale1
    elif NZGrid0 < NZGrid1:
        Ymax0 = Ymin0 + NZGrid1 * Yscale0
    elif NZGrid0 == NZGrid1:
        pass
    
    #----- Adjust Space For Text -----
    
#    Ymax0 = 180 # In case there is a need to force the value
#    Ymax1 = 25 ; Ymin1 = -20
    
    reqheight = 0.15 # Height for yearly averages text on top of the graph.
    Ymax0 += (Ymax0 - Ymin0) * reqheight 
    Ymax1 += (Ymax1 - Ymin1) * reqheight
    
#    height4text = (Ymax1 - np.max(TNORM+TSTD)) / (Ymax1 - Ymin1)
        
#    Ymax0 += (Ymax0 - Ymin0) * (reqheight - height4text) 
#    Ymax1 += (Ymax1 - Ymin1) * (reqheight - height4text) 
    
#    Ymax0 += (Ymax0 - Ymin0) * (reqheight - height4text) 
#    Ymax1 += (Ymax1 - Ymin1) * (reqheight - height4text)
    
    #----------------------------------------------------- YTICKS FORMATING ----
    
    #----- Precip (host) -----
    
    ax0.yaxis.set_ticks_position('left')
    
    yticks = np.arange(Ymin0, Ymax0 - (Ymax0 - Ymin0) * 0.1, Yscale0)
    ax0.set_yticks(yticks)
    ax0.tick_params(axis='y', direction='out', labelcolor=COLOR[1],
                    labelsize=13)
    
    yticks_minor = np.arange(yticks[0], yticks[-1], 5)
    ax0.set_yticks(yticks_minor, minor=True)
    ax0.tick_params(axis='y', which='minor', direction='out')
    ax0.yaxis.set_ticklabels([], minor=True)
    
    ax0.set_axisbelow(True)
    
    #----- Air Temp -----
    
    yticks1 = np.arange(Ymin1, Ymax1 - (Ymax1 - Ymin1) * 0.1 , Yscale1)    
    ax1.yaxis.set_ticks_position('right')
    ax1.set_yticks(yticks1)
    ax1.tick_params(axis='y', direction='out', labelcolor=COLOR[0],
                    labelsize=13)
    
    yticks1_minor = np.arange(yticks1[0], yticks1[-1], Yscale1/5.)
    ax1.set_yticks(yticks1_minor, minor=True)
    ax1.tick_params(axis='y', which='minor', direction='out', gridOn=False)
    ax1.yaxis.set_ticklabels([], minor=True)
    
    #----------------------------------------------------------------- GRID ----
    
#    ax0.grid(axis='y', color=[0.5, 0.5, 0.5], linestyle=':', linewidth=1,
#             dashes=[1, 5])
#    ax0.grid(axis='y', color=[0.75, 0.75, 0.75], linestyle='-', linewidth=0.5)

    #------------------------------------------------------- SET AXIS RANGE ---- 

    ax0.axis([Xmin0, Xmax0, Ymin0, Ymax0])
    ax1.axis([Xmin0, Xmax0, Ymin1, Ymax1])
    
    #--------------------------------------------------------------- LABELS ----
    
    ax0.set_ylabel('Monthly Total Precipication (mm)', fontsize=label_font_size,
                   verticalalignment='bottom', color=COLOR[1])
    ax0.yaxis.set_label_coords(-0.09, 0.5)
    
    ax1.set_ylabel(u'Monthly Mean Air Temperature (°C)', color=COLOR[0],
                   fontsize=label_font_size, verticalalignment='bottom',
                   rotation=270)
    ax1.yaxis.set_label_coords(1.09, 0.5)

    #------------------------------------------------------------- PLOTTING ----
    
    SNOWcolor = [0.85, 0.85, 0.85]
    RAINcolor = [0, 0, 1]
            
    XPOS = np.arange(0.5, 12.5, 1)
    
    ax0.bar(XPOS, PNORM, align='center', width=0.5, color=RAINcolor,
            edgecolor='k', linewidth=0.5)            
    ax0.bar(XPOS, SNORM, align='center', width=0.5, color=SNOWcolor,
            edgecolor='k', linewidth=0.5)    
    
    #---- Air Temperature ----
    
    colors = ['#990000', '#FF0000', '#FF6666']
    
    TNORM = np.hstack((TNORM[-1], TNORM, TNORM[0]))
    Tmin_norm = np.hstack((Tmin_norm[-1], Tmin_norm, Tmin_norm[0]))
    Tmax_norm = np.hstack((Tmax_norm[-1], Tmax_norm, Tmax_norm[0]))
#    TSTD = np.hstack((TSTD[-1], TSTD, TSTD[0])) 
    
    XPOS = np.arange(-0.5, Xmax0+0.5) 
    
    h1_ax1, = ax1.plot(XPOS, TNORM, color=colors[1], clip_on=True,
                       marker='o', ls='--', ms=6, zorder=100,
                       mec=colors[1], mfc='white', mew=1.5, lw=1.5)
    
    h2_ax1, = ax1.plot(XPOS, Tmax_norm, color=colors[0], clip_on=True,
                       marker='o', ls='--', ms=0, zorder=100,
                       mec=colors[0], mfc='white', mew=1.5, lw=1.)
                       
    h3_ax1, = ax1.plot(XPOS, Tmin_norm, color=colors[2], clip_on=True,
                       marker='o', ls='--', ms=0, zorder=100,
                       mec=colors[2], mfc='white', mew=1.5, lw=1.)
                         
#    ax1.errorbar(XPOS, TNORM, yerr=TSTD, color='red', fmt='o', ecolor='black',
#                 capthick=1.2, elinewidth=1.2, clip_on=True, zorder=100)
    
    #---- Yearly Averages Labels ----
            
    ax1.text(0.02, 0.94, 
             u'Mean Annual Air Temperature = %0.1f °C' % np.mean(TNORM[1:-1]),
             fontsize=13, verticalalignment='bottom', transform=ax1.transAxes)
    ax1.text(0.02, 0.88,
             u'Mean Annual Precipitation = %0.1f mm' % np.sum(PNORM),
             fontsize=13, verticalalignment='bottom', transform=ax1.transAxes)
             
    #--------------------------------------------------------------- LEGEND ----        

    rec1 = plt.Rectangle((0, 0), 1, 1, fc=SNOWcolor)
    rec2 = plt.Rectangle((0, 0), 1, 1, fc=RAINcolor)
    
    lines = [h2_ax1, h1_ax1, h3_ax1, rec1, rec2]
   
    labels = ['Max Temp.', 'Mean Temp.', 'Min. Temp.', 'Snow', 'Rain']
    
    # Get the bounding box of the original legend
#    renderer = fig.canvas.get_renderer()
#     bb = leg.legendPatch.get_bbox().inverse_transformed(ax.transAxes)
    
    pos = ax1.transData.transform((0., np.max(yticks1)))
    pos = ax1.transAxes.inverted().transform(pos)
    pos[0] = 0.01
    
    legend = ax1.legend(lines, labels,
                        numpoints=1, fontsize=13, borderaxespad=0.,
                        bbox_to_anchor=pos, loc='upper left')
               
    legend.draw_frame(False)
    
      
#===============================================================================    
def calculate_normals(YEAR, MONTH, TMIN, TMAX, TAVG, PTOT, RAIN):
    """
    Calculates monthly normals from daily average air temperature and
    total daily precipitation time series. Won't return a value if 
    there is NaN in any of the input time series.
    
    #---- INPUT ----
    
    {1D array} YEAR = Year for each data in the time series.
    {1D array} MONTH = Month (1-12) for each data in the time series.
    {1D array} PTOT = Daily total precipitation in mm
    {1D array} TAVG = Daily average air temperature in deg. C.
    
    #---- OUTPUT ----
    
    {1D array} TNORM = Monthly normals for air temperature in deg C.
    {1D array} PNORM = Monthly normals for total precipitation in mm.
    {1D array} RNORM = Monthly normals for rain in mm.
    {1D array} TSTD = Monthly standard deviation for air temperature in deg C.    
    """
#===============================================================================
   
    #------------------------------------------------------ MONTHLY VALUES -----
    
    # Calculate the average value for each months of each year.
    
    nYEAR = YEAR[-1] - YEAR[0] + 1
   
    TMONTH = np.zeros((nYEAR, 12)) * np.nan
    Tmin_mth = np.zeros((nYEAR, 12)) * np.nan
    Tmax_mth = np.zeros((nYEAR, 12)) * np.nan
    PMONTH = np.zeros((nYEAR, 12)) * np.nan
    RMONTH = np.zeros((nYEAR, 12)) * np.nan
    for j in range(nYEAR):
        for i in range(12):
            
            indx = np.where((YEAR == j+YEAR[0]) & (MONTH == i+1))[0]
            Nday = monthrange(j+YEAR[0], i+1)[1] 
            
            if len(indx) < Nday:
                print 'Month', i+1, 'of year', j+YEAR[0], 'is imcomplete'
                
                # Do nothing. Default nan value will be kept.                
                
            else:                
                TMONTH[j, i] = np.mean(TAVG[indx])
                PMONTH[j, i] = np.sum(PTOT[indx])
                RMONTH[j, i] = np.sum(RAIN[indx])
                Tmin_mth[j, i] = np.mean(TMIN[indx])
                Tmax_mth[j, i] = np.mean(TMAX[indx])

    #------------------------------------------------------ MONTHLY NORMALS ----
    
    # Calculate the normals for each month.
    
    TNORM = np.zeros(12) * np.nan
    PNORM = np.zeros(12) * np.nan
    RNORM = np.zeros(12) * np.nan
    TSTD = np.zeros(12) * np.nan
    
    Tmin_norm = np.zeros(12)
    Tmax_norm = np.zeros(12)
    
    for i in range(12):
        
        indx = np.where(~np.isnan(TMONTH[:, i]))[0]
        
        if len(indx) > 0:
            
            TNORM[i] = np.mean(TMONTH[indx, i])
            PNORM[i] = np.mean(PMONTH[indx, i])
            RNORM[i] = np.mean(RMONTH[indx, i])            
            TSTD[i] = (np.mean((TMONTH[indx, i] - TNORM[i])**2))**0.5

            Tmin_norm[i] = np.mean(Tmin_mth[indx, i]) 
            Tmax_norm[i] = np.mean(Tmax_mth[indx, i])
            
        else:
            
            print 'WARNING, some months are empty because of lack of data'
            
            # Default nan value is kept in the array.

    return Tmin_norm, Tmax_norm, TNORM, PNORM, RNORM


#===============================================================================
def calculate_ETP(TIME, TAVG, LAT, Ta):
    """
    Daily potential evapotranspiration (mm) is calculated with a method adapted
    from Thornwaite (1948).
    
    Requires at least a year of data.
    
    #----- INPUT -----
    
    TIME = Numeric time in days
    TAVG = Daily temperature average (deg C)
    LAT = Latitude in degrees
    Ta = Monthly air temperature normals
    
    #----- OUTPUT -----

    ETP: Daily Potential Evapotranspiration (mm)    
    
    #----- SOURCE -----
    
    Pereira, A.R. and W.O. Pruitt. 2004. Adaptation of the Thornthwaite scheme
        for estimating daily reference evapotranspiration. Agricultural Water
        Management, 66, 251-257.
    """
#===============================================================================
        
    Ta[Ta < 0] = 0    
    
    I = np.sum((0.2 * Ta) ** 1.514) # Heat index
    a = (6.75e-7 * I**3) - (7.71e-5 * I**2) + (1.7912e-2 * I) + 0.49239
    
    TAVG[TAVG < 0] = 0
    
    DAYLEN = calculate_daylength(TIME, LAT) # Photoperiod in hr
    
    ETP = 16 * (10 * TAVG / I)**a * (DAYLEN / (12. * 30))
        
    return ETP
    
    
#===============================================================================   
def calculate_daylength(TIME, LAT):
    """
    Calculate the photoperiod for the given latitude at the given time.
    
    #----- INPUT -----
    
    {1D array} TIME = Numeric time in days.
    {float}     LAT = latitude in decimal degrees.
    
    #----- OUTPUT -----
    
    {1D array} DAYLEN = photoperiod in hr.    
    """
#===============================================================================
    
    pi = np.pi
    
    LAT = np.radians(LAT) # Latitude in rad
    
    #----- CONVERT DAY FORMAT -----
    
    # http://stackoverflow.com/questions/13943062
    
    DAY = np.zeros(len(TIME))
    
    for i in range(len(DAY)):
        DATE = xldate_as_tuple(TIME[i], 0)
        DAY[i] = int(date(DATE[0], DATE[1], DATE[2]).timetuple().tm_yday)
    
    #---------------------------------------------- DECLINATION OF THE SUN -----    
    
    # http://en.wikipedia.org/wiki/Position_of_the_Sun#Calculations

    N = DAY - 1
    
    A = 2 * pi / 365.24 * (N - 2)
    B = 2 * pi / pi * 0.0167
    C = 2 * pi / 365.24 * (N + 10)
    
    D = -23.44 * pi / 180.
            
    SUNDEC = np.arcsin(np.sin(D) * np.cos(C + B * np.sin(A)))
    
    #---------------------------------------------------- SUNRISE EQUATION -----    

    # http:/Omega/en.wikipedia.org/wiki/Sunrise_equation

    OMEGA = np.arccos(-np.tan(LAT) * np.tan(SUNDEC))
    
    #------------------------------------------------------ HOURS OF LIGHT -----
    
    # http://physics.stackexchange.com/questions/28563/
    #        hours-of-light-per-day-based-on-latitude-longitude-formula
    
    DAYLEN = OMEGA * 2 * 24 / (2 * np.pi) # Day length in hours
    
    return DAYLEN

if __name__ == '__main__':
#    plt.rc('font',family='Arial')
    
    app = QtGui.QApplication(argv)   
    instance_1 = WeatherAvgGraph()
            
    fmeteo = "Files4testing/Daily - SASKATOON DIEFENBAKER & RCS_1980-2014.out"
#    fmeteo = "Files4testing/TORONTO LESTER B. PEARSON INT'L _1980-2010.out"
#    fmeteo = "Files4testing/QUEBEC-JEAN LESAGE INTL A_1985-2005.out"
    instance_1.save_fig_dir =  '../Projects/Project4Testing'
    instance_1.generate_graph(fmeteo)
    
    instance_1.show()
    instance_1.setFixedSize(instance_1.size());
    app.exec_()