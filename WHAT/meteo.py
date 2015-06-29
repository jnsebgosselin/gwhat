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
        
        iconDB = db.icons()
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
        
    def generate_graph(self, filename):
        
        METEO = MeteoObj()
        METEO.load(filename)
        
        self.station_name = METEO.station_name
        self.setWindowTitle('Weather Averages for %s' % self.station_name)
        
        YEAR = METEO.YEAR
        MONTH = METEO.MONTH
        TAVG = METEO.TAVG
        PTOT = METEO.PTOT
        RAIN = METEO.RAIN
        
        TNORM, PNORM, RNORM, TSTD = calculate_normals(YEAR, MONTH,
                                                      TAVG, PTOT, RAIN)
                                                  
        plot_monthly_normals(self.fig, TNORM, PNORM, RNORM, TSTD)
                
        self.fig_widget.draw()

    def save_graph(self):
        
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
#===============================================================================    

    def __init__(self):
        
        self.TIME = []  # Time in numeric format (days)
        self.TMAX = []  # Daily maximum temperature (deg C)
        self.TAVG = []  # Daily mean temperature (deg C)
        self.PTOT = []  # Daily total precipitation (mm)
        self.RAIN = []  # Daily total liquid precipitation (mm)
        
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
        
    def load(self, fname):
        
        with open(fname, 'rb') as f:
            reader = list(csv.reader(f, delimiter='\t'))
        
        self.station_name = reader[0][1]
        self.LAT = reader[2][1]
        self.LON = reader[3][1]
        
        DATA = np.array(reader[11:]).astype('float')
        
        #------------------------------------------------------- REMOVE NAN ----
        
        # Remove nan rows at the beginning of the record if any
        for i in range(len(DATA[:, 0])):
            if np.all(np.isnan(DATA[i, 3:])):
                DATA = np.delete(DATA, i, axis=0)
            else:
                break
            
        # Remove nan rows at the end of the record if any
        for i in range(len(DATA[:, 0])):
            if np.all(np.isnan(DATA[-i, 3:])):
                DATA = np.delete(DATA, -i, axis=0)
            else:
                break   
            
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
        TAVG = DATA[:, 5]
        PTOT = DATA[:, 6]        

        #----------------------------------------------------- ESTIMATE NAN ----

        PTOT[np.isnan(PTOT)] = 0
        
        nonanindx = np.where(~np.isnan(TMAX))[0]
        if len(nonanindx) < len(TMAX):
            TMAX = np.interp(TIME, TIME[nonanindx], TMAX[nonanindx])
    
        #---------------------------------------------------- ESTIMATE RAIN ----
        
        RAIN = np.copy(PTOT)
        RAIN[np.where(TAVG < 0)[0]] = 0
        
        #------------------------------------------------- UPDATE CLASS VAR ----
    
        self.TIME = TIME
        self.TMAX = TMAX
        self.TAVG = TAVG
        self.PTOT = PTOT
        self.RAIN = RAIN
        
        self.YEAR = DATA[:, 0].astype(int)
        self.MONTH = DATA[:, 1].astype(int)
                
        #--------------------------------------- DAILY TO WEEKLY CONVERSION ----        
        
        bwidth = 7.
        nbin = np.floor(len(TIME) / bwidth)
        
        TIMEwk = TIME[0] + np.arange(bwidth/2. - 1,
                                     bwidth * nbin - bwidth/2.,
                                     bwidth)
#        TMAXwk = np.zeros(nbin)
#        PTOTwk = np.zeros(nbin)
#        RAINwk = np.zeros(nbin)
#        for i in range(7):   
#            TMAXwk = TMAXwk + TMAX[i:bwidth*nbin + i:bwidth] / bwidth
#            PTOTwk = PTOTwk + PTOT[i:bwidth*nbin + i:bwidth]
#            RAINwk = RAINwk + RAIN[i:bwidth*nbin + i:bwidth]
            
        #---- Alternate Method ----
        
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

        self.TIMEwk = TIMEwk
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
#
# This function is called when a time serie of a daily meteorological record
# is found to be discontinuous over time.
#
# <make_timeserie_continuous> will scan the entire time serie and will insert
# a row with nan values whenever there is a gap in the data and will return
# the continuous data set.
#
# DATA = [YEAR, MONTH, DAY, VAR1, VAR2 ... VARn]
#
#        2D matrix containing the dates and the corresponding daily 
#        meteorological data of a given weather station arranged in 
#        chronological order. 
#
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
def plot_monthly_normals(fig, TNORM, PNORM, RNORM, TSTD,
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
    
    indx = np.where(SCA1 > np.max(TNORM+TSTD))[0][0] 
    Ymax1 = SCA1[indx]
    
    indx = np.where(SCA1 < np.min(TNORM-TSTD))[0][-1] 
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
    
    #------------------------------------------------------YTICKS FORMATING-----
    
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

    #------------------------------------------------------ SET AXIS RANGE ----- 

    ax0.axis([Xmin0, Xmax0, Ymin0, Ymax0])
    ax1.axis([Xmin0, Xmax0, Ymin1, Ymax1])
    
    #----------------------------------------------------------------LABELS-----
    
    ax0.set_ylabel('Monthly Total Precipication (mm)', fontsize=label_font_size,
                   verticalalignment='bottom', color=COLOR[1])
    ax0.yaxis.set_label_coords(-0.09, 0.5)
    
    ax1.set_ylabel(u'Monthly Mean Air Temperature (°C)', color=COLOR[0],
                   fontsize=label_font_size, verticalalignment='bottom',
                   rotation=270)
    ax1.yaxis.set_label_coords(1.09, 0.5)

    #------------------------------------------------------------ PLOTTING -----
    
    SNOWcolor = [0.85, 0.85, 0.85]
    RAINcolor = [0, 0, 1]
    
    TNORM = np.hstack((TNORM[-1], TNORM, TNORM[0]))
    TSTD = np.hstack((TSTD[-1], TSTD, TSTD[0]))    
            
    XPOS = np.arange(0.5, 12.5, 1)
    
    ax0.bar(XPOS, PNORM, align='center', width=0.5, color=RAINcolor,
            edgecolor='k', linewidth=0.5)            
    ax0.bar(XPOS, SNORM, align='center', width=0.5, color=SNOWcolor,
            edgecolor='k', linewidth=0.5)    

    XPOS = np.arange(-0.5, Xmax0+0.5) 
    h1_ax1, = ax1.plot(XPOS, TNORM, color='red', clip_on=True, zorder=100,
                       marker='o', linestyle='--')
                         
    ax1.errorbar(XPOS, TNORM, yerr=TSTD, color='red', fmt='o', ecolor='black',
                 capthick=1.2, elinewidth=1.2, clip_on=True, zorder=100)
                 
    ax1.text(0.02, 0.94, 
             u'Mean Annual Air Temperature = %0.1f °C' % np.mean(TNORM[1:-1]),
             fontsize=13, verticalalignment='bottom', transform=ax1.transAxes)
    ax1.text(0.02, 0.88,
             u'Mean Annual Precipitation = %0.1f mm' % np.sum(PNORM),
             fontsize=13, verticalalignment='bottom', transform=ax1.transAxes)
             
#------------------------------------------------------------------ LEGEND -----        

    rec1 = plt.Rectangle((0, 0), 1, 1, fc=SNOWcolor)
    rec2 = plt.Rectangle((0, 0), 1, 1, fc=RAINcolor)
   
    labels = ['Air Temperature', 'Snow', 'Rain']
    
    legend = ax1.legend([h1_ax1, rec1, rec2], labels, loc=[0.01, 0.65],
                        numpoints=1, fontsize=13, borderaxespad=0.)
               
    legend.draw_frame(False)
    
#===============================================================================    
def calculate_normals(YEAR, MONTH, TAVG, PTOT, RAIN):
#===============================================================================
    
#---------------------------------------------------------- MONTHLY VALUES -----
    
    nYEAR = YEAR[-1] - YEAR[0] + 1
   
    TMONTH = np.zeros((nYEAR, 12))
    PMONTH = np.zeros((nYEAR, 12))
    RMONTH = np.zeros((nYEAR, 12))
    for j in range(nYEAR):
        for i in range(12):
            
            indx = np.where((YEAR == j+YEAR[0]) & (MONTH == i+1))[0]
            Nday = monthrange(j+YEAR[0], i+1)[1] 
            
            if len(indx) < Nday:
                print 'Month', i+1, 'of year', j+YEAR[0], 'is imcomplete'
                TMONTH[j, i] = np.nan
                PMONTH[j, i] = np.nan
                RMONTH[j, i] = np.nan
            else:
                TMONTH[j, i] = np.mean(TAVG[indx])
                PMONTH[j, i] = np.sum(PTOT[indx])
                RMONTH[j, i] = np.sum(RAIN[indx])

#--------------------------------------------------------- MONTHLY NORMALS -----
    
    TNORM = np.zeros(12)
    PNORM = np.zeros(12)
    RNORM = np.zeros(12)
    TSTD = np.zeros(12)
    for i in range(12):
        indx = np.where(~np.isnan(TMONTH[:, i]))[0]
        
        if len(indx) > 0:
            TNORM[i] = np.mean(TMONTH[indx, i])
            PNORM[i] = np.mean(PMONTH[indx, i])
            RNORM[i] = np.mean(RMONTH[indx, i])            
            TSTD[i] = (np.mean((TMONTH[indx, i] - TNORM[i])**2))**0.5            
        else:
            
            print 'WARNING, some months are empty because of lack of data'
            
            TNORM[i] = np.nan
            PNORM[i] = np.nan
            RNORM[i] = np.nan
            TSTD[i] = np.nan
    
    return TNORM, PNORM, RNORM, TSTD

if __name__ == '__main__':
#    plt.rc('font',family='Arial')
#    global label_font_size
#    label_font_size = 14
#    
#    global labelDB
#    labelDB = LabelDataBase('English')
#                
#    plt.close("all")
#    
#    fmeteo = 'Files4testing/AUTEUIL_2000-2013.out'
#    TNORM, PNORM, RNORM, TSTD = calculate_normals(fmeteo)
#    
#    fig = plt.figure(figsize=(8.5, 5))        
##    fig.set_size_inches(8.5, 5)
#    plot_monthly_normals(fig, TNORM, PNORM, RNORM, TSTD)
#    
    
    app = QtGui.QApplication(argv)   
    instance_1 = WeatherAvgGraph()
            
    fmeteo = "Files4testing/Daily - SASKATOON DIEFENBAKER & RCS_1980-2014.out"
#    fmeteo = "Files4testing/TORONTO LESTER B. PEARSON INT'L _1980-2010.out"
#    fmeteo = "Files4testing/QUEBEC-JEAN LESAGE INTL A_1985-2005.out"
    
    instance_1.generate_graph(fmeteo)
    
    instance_1.show()
    instance_1.setFixedSize(instance_1.size());
    app.exec_()