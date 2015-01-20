# -*- coding: utf-8 -*-
"""
Copyright 2014 Jean-Sebastien Gosselin

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
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""

#---- STANDARD LIBRARY IMPORTS ----

from sys import argv

#---- THIRD PARTY IMPORTS ----

import numpy as np
from PySide import QtGui, QtCore

import matplotlib
matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4']='PySide'
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg
import matplotlib.pyplot as plt

#class MainWindow(QtGui.QMainWindow):
#        
#    def __init__(self, parent=None):
#        super(MainWindow, self).__init__(parent)
#        
#        self.initUI()
#        
#        def initUI(self):
#                            
##        self.setGeometry(350, 75, 800, 750)
#        self.setWindowTitle('Master Recession Curve Estimation')
#        self.setWindowIcon(iconDB.WHAT)
        
class MRCalc(QtGui.QWidget):
    
    def __init__(self, parent=None):
        super(MRCalc, self).__init__(parent)

        self.initUI()
#        self.initUI_weather_normals()
        self.fig_MRC_widget.mpl_connect('button_press_event', self.onclick)
        self.fig_MRC_widget.mpl_connect('motion_notify_event', self.mouse_vguide)
        
    def initUI(self):
        
        self.setWindowTitle('Master Recession Curve Estimation')
        
        self.fig_MRC = plt.figure()        
        self.fig_MRC.set_size_inches(8.5, 5)        
        self.fig_MRC.patch.set_facecolor('white')
        self.fig_MRC_widget = FigureCanvasQTAgg(self.fig_MRC)
#    
#        self.toolbar = NavigationToolbar2QTAgg(self.fig_MRC_widget, self)
#        # https://sukhbinder.wordpress.com/2013/12/16/
#        #         simple-pyqt-and-matplotlib-example-with-zoompan/
#    
#        grid_normals = QtGui.QGridLayout()
#        self.normals_window = QtGui.QWidget()
#    
#        row = 0
#        grid_normals.addWidget(self.normals_fig_widget, row, 0)
#        row += 1
#        grid_normals.addWidget(self.toolbar, row, 0)
#        
#        self.normals_window.setLayout(grid_normals)
##   grid_normals.setContentsMargins(0, 0, 0, 0) # Left, Top, Right, Bottom 
##        grid_normals.setSpacing(15)
##        grid_normals.setColumnStretch(1, 500)
##        
##        self.normals_window.resize(250, 150)
                
    #------------------------------------------------------------ MAIN GRID ----
        
        mainGrid = QtGui.QGridLayout()
        
        row = 0 
        mainGrid.addWidget(self.fig_MRC_widget, row, 0)
              
        self.setLayout(mainGrid)
        mainGrid.setContentsMargins(10, 10, 10, 10) # Left, Top, Right, Bottom 
        mainGrid.setSpacing(15)
        mainGrid.setColumnStretch(0, 500)
        
        ########################### 4 TESTING ######################
        
        fwaterlvl = 'Files4testing/PO16A.xls'
    
        waterLvlObj = WaterlvlData()
        waterLvlObj.load(fwaterlvl)
    
        self.water_lvl = waterLvlObj.lvl
        self.water_lvl = self.water_lvl[:500]
    
        self.time = waterLvlObj.time
        self.time = self.time[:500]
        
        self.peak_indx = np.array([]).astype(int)
        
        self.plot_water_levels(self.time, self.water_lvl, self.fig_MRC)
        
    def plot_water_levels(self, t, x, fig):
        
        fheight = fig.get_figheight()
        fwidth = fig.get_figwidth()
    
    #------------------------------------------------------ FIGURE CREATION ----
        
        left_margin  = 0.65
        right_margin = 0.25
        bottom_margin = 0.65
        top_margin = 0.25
           
        x0 = left_margin / fwidth
        y0 = bottom_margin / fheight
        w = 1 - (left_margin + right_margin) / fwidth
        h = 1 - (bottom_margin + top_margin) / fheight
                        
    #-------------------------------------------------------- AXES CREATION ----        
        
        #---- Water Level (Host) ----
        
        ax0  = fig.add_axes([x0, y0, w, h], zorder=0)
        ax0.patch.set_visible(False)
        
#        #---Peaks---
#        ax1 = fig.add_axes(ax0.get_position(), frameon=False, zorder=1)
#        ax1.patch.set_visible(False)
        
    #----------------------------------------------------- XTICKS FORMATING ---- 
    
#        Xmin0 = 0
#        Xmax0 = 12.001
        
        ax0.xaxis.set_ticks_position('bottom')
        ax0.tick_params(axis='x',direction='out', gridOn=True)
#        ax0.xaxis.set_ticklabels([])
#        ax0.set_xticks(np.arange(Xmin0, Xmax0))
        
#        ax0.set_xticks(np.arange(Xmin0+0.5, Xmax0+0.49, 1), minor=True)
#        ax0.tick_params(axis='x', which='minor', direction='out', gridOn=False,
#                        length=0,)
#        ax0.xaxis.set_ticklabels(month_names, minor=True)
        
#        ax1.tick_params(axis='x', which='both', bottom='off', top='off',
#                        labelbottom='off'
    #----------------------------------------------------- YTICKS FORMATING ----
        
        ax0.yaxis.set_ticks_position('left')
        ax0.tick_params(axis='y',direction='out', gridOn=True)
                
    #------------------------------------------------------- SET AXIS RANGE ---- 
       
        delta = 0.05
        Xmin0 = np.min(t) - (np.max(t) - np.min(t)) * delta
        Xmax0 = np.max(t) + (np.max(t) - np.min(t)) * delta
    
        Ymin0 = np.min(x) - (np.max(x) - np.min(x)) * delta
        Ymax0 = np.max(x) + (np.max(x) - np.min(x)) * delta
    
        ax0.axis([Xmin0, Xmax0, Ymin0, Ymax0])
        ax0.invert_yaxis()
        
    #--------------------------------------------------------------- LABELS ----
    
#    ax0.set_ylabel('Monthly Total Precipication (mm)', fontsize=label_font_size,
#                   verticalalignment='bottom', color='blue')
#    ax0.yaxis.set_label_coords(-0.09, 0.5)
#    
#    ax1.set_ylabel(u'Monthly Mean Air Temperature (°C)', color='red',
#                   fontsize=label_font_size, verticalalignment='bottom',
#                   rotation=270)
#    ax1.yaxis.set_label_coords(1.09, 0.5)

    #------------------------------------------------------------- PLOTTING ----
    
        #---- Water Levels ----
    
        h1_ax0, = ax0.plot(t, x, color='blue', clip_on=False, zorder=100,
                           marker='None', linestyle='-')
        
        #---- Peaks ----
                 
        self.h2_ax0, = ax0.plot([], [], color='red', clip_on=False, zorder=100,
                           marker='o', linestyle='None')
                           
        self.ly = ax0.axvline(x=.5, ymin=0, ymax=1, color='red')  # Vertical guide line under cursor

    #-------------------------------------------------------- UPDATE WIDGET ----
                        
        self.fig_MRC_widget.draw()
            
    def mouse_vguide(self, event):
        # http://matplotlib.org/examples/pylab_examples/cursor_demo.html
        if event.xdata != None and event.ydata != None:
            x = event.xdata
            
            # update the line positions
            self.ly.set_xdata(x)
            
            self.fig_MRC_widget.draw()
            
    def onclick(self, event):
        # www.github.com/eliben/code-for-blog/blob/master/2009/qt_mpl_bars.py
        if event.xdata != None and event.ydata != None:
#            print(event.xdata, event.ydata)
            
            x_clic = event.xdata
            
            self.add_peak(x_clic)
                        
    def add_peak(self, xclic):
        
        # http://matplotlib.org/examples/pylab_examples/cursor_demo.html
        
        x = self.time
        y = self.water_lvl
        
        indxmin = np.where(x < xclic)[0]
        indxmax = np.where(x > xclic)[0]
        if len(indxmax) == 0:
            xclic = x[-1]
            yclic = y[-1]
            self.peak_indx = np.append(self.peak_indx, len(x)-1)
        elif len(indxmin) == 0:
            xclic = x[0]
            yclic = y[0]
            self.peak_indx = np.append(self.peak_indx, 0)
        else:
            indxmin = indxmin[-1]
            indxmax = indxmax[0]
            
            dleft = xclic - x[indxmin]
            dright = x[indxmax] - xclic
            
            if dleft < dright:
                xclic = x[indxmin]
                yclic = y[indxmin]
                self.peak_indx = np.append(self.peak_indx, indxmin)
            else:
                xclic = x[indxmax]
                yclic = y[indxmax]
                self.peak_indx = np.append(self.peak_indx, indxmax)               
        
#        yclic = np.interp(xclic, x, y)
        
#        indxmin = np.where(time < (x - Deltan/2.))[0]
#        indxmax = np.where(time > (x + Deltan/2.))[0]
#        if len(indxmin) == 0:
#            indxmin = 0
#            indxmax = np.where(time > time[0] + Deltan)[0][0]
#        elif len(indxmax) == 0:
#            indxmax = len(time) - 1
#            indxmin = np.where(time < (time[-1] - Deltan))[0][-1]
#        else:
#            indxmin = indxmin[-1]
#            indxmax = indxmax[0]
#        
#        print indxmin, indxmax
        
#        self.water_lvl = self.water_lvl[:500]
#        self.time = self.time[:500]
#        
#        self.peak_indx = []
       
#        self.h2_ax0.set_ydata(yclic)
#        self.h2_ax0.set_xdata(xclic)
        
        self.h2_ax0.set_ydata(y[self.peak_indx])
        self.h2_ax0.set_xdata(x[self.peak_indx])
                               
        self.fig_MRC_widget.draw()
            
    def del_peak(self, x, y, Deltan, fig):
        pass
    
   
#===============================================================================
def local_extrema(x, Deltan):
    """
    Code adapted from a MATLAB script at 
    www.ictp.acad.ro/vamos/trend/local_extrema.htm
    
    LOCAL_EXTREMA Determines the local extrema of a given temporal scale.
    
    ---- OUTPUT ----
    
    n_j = The positions of the local extrema of a partition of scale Deltan
          as defined at p. 82 in the book [ATE] C. Vamos and M. Craciun,
          Automatic Trend Estimation, Springer 2012.
          The positions of the maxima are positive and those of the minima
          are negative.
    kadd = n_j(kadd) are the local extrema with time scale smaller than Deltan
           which are added to the partition such that an alternation of maxima
           and minima is obtained.    
    """
#===============================================================================

    N = len(x)
    
    ni = 0
    nf = N - 1
    
#------------------------------------------------------------------ PLATEAU ----
    
    # Recognize the plateaus of the time series x defined in [ATE] p. 85
    # [n1[n], n2[n]] is the interval with the constant value equal with x[n]
    # if x[n] is not contained in a plateau, then n1[n] = n2[n] = n
    #
    # Example with a plateau between indices 5 and 8:
    #  x = [1, 2, 3, 4, 5, 6, 6, 6, 6, 7, 8,  9, 10, 11, 12]
    # n1 = [0, 1, 2, 3, 4, 5, 5, 5, 5, 9, 10, 11, 12, 13, 14]
    # n2 = [0, 1, 2, 3, 4, 8, 8, 8, 8, 9, 10, 11, 12, 13, 14]
   
    n1 = np.arange(N)
    n2 = np.arange(N)
                
    dx = np.diff(x)
    if np.any(dx == 0):
        print 'At least 1 plateau has been detected in the data'
        for i in range(N-1):            
            if x[i+1] == x[i]:                
                n1[i+1] = n1[i]
                n2[n1[i+1]:i+1] = i+1

    #-------------------------------------------------------- MAIN FUNCTION ----
    
    # the iterative algorithm presented in Appendix E of [ATE]
    
    nc = 0    # the time step up to which the time series has been
              # analyzed ([ATE] p. 127)
    Jest = 0  # number of local extrema of the partition of scale DeltaN 
    iadd = 0  # number of additional local extrema
    flagante = 0
    kadd = [] # order number of the additional local extrema between all the
              # local extrema
    n_j = []  # positions of the local extrema of a partition of scale Deltan
    
    while nc < nf:

        # the next extremum is searched within the interval [nc, nlim]
        
        nlim = min(nc + Deltan, nf)   
    
        #--------------------------------------------------- SEARCH FOR MIN ----
    
        xmin = np.min(x[nc:nlim+1])
        nmin = np.where(x[nc:nlim+1] == xmin)[0][0] + nc
       
        nlim1 = max(n1[nmin] - Deltan, ni)
        nlim2 = min(n2[nmin] + Deltan, nf)
        
        xminn = np.min(x[nlim1:nlim2+1])
        nminn = np.where(x[nlim1:nlim2+1] == xminn)[0][0] + nlim1
        
        # if flagmin = 1 then the minimum at nmin satisfies condition (6.1)
        if nminn == nmin:
            flagmin = 1
        else:
            flagmin = 0
            
        #--------------------------------------------------- SEARCH FOR MAX ----
            
        xmax = np.max(x[nc:nlim+1])
        nmax = np.where(x[nc:nlim+1] == xmax)[0][0] + nc   

        nlim1 = max(n1[nmax] - Deltan, ni)        
        nlim2 = min(n2[nmax] + Deltan, nf)
        
        xmaxx = np.max(x[nlim1:nlim2+1])
        nmaxx = np.where(x[nlim1:nlim2+1] == xmaxx)[0][0] + nlim1 
        
        # If flagmax = 1 then the maximum at nmax satisfies condition (6.1)
        if nmaxx == nmax: 
            flagmax = 1
        else: 
            flagmax=0
       
        #------------------------------------------------------- MIN or MAX ----

        # The extremum closest to nc is kept for analysis
        if flagmin == 1 and flagmax == 1:
            if nmin < nmax:
                flagmax = 0
            else:
                flagmin = 0

        #------------------------------------------------ ANTERIOR EXTREMUM ----
                
        if flagante == 0: # No ANTERIOR extremum
            
            if flagmax == 1:  # CURRENT extremum is a MAXIMUM

                nc = n1[nmax] + 1
                flagante = 1
                n_j = np.append(n_j, np.floor((n1[nmax] + n2[nmax]) / 2.))
                Jest += 1 
                
            elif flagmin == 1:  # CURRENT extremum is a MINIMUM

                nc = n1[nmin] + 1
                flagante = -1
                n_j = np.append(n_j, -np.floor((n1[nmin] + n2[nmin]) / 2.))
                Jest += 1

            else: # No extremum

                nc = nc + Deltan
                
        elif flagante == -1: # ANTERIOR extremum is an MINIMUM
            
            tminante = np.abs(n_j[-1])
            xminante = x[tminante]
            
            if flagmax == 1: # CURRENT extremum is a MAXIMUM                

                if xminante < xmax:

                    nc = n1[nmax] + 1
                    flagante = 1
                    n_j = np.append(n_j, np.floor((n1[nmax] + n2[nmax]) / 2.))
                    Jest += 1
                    
                else: 
                    
                    # CURRENT MAXIMUM is smaller than the ANTERIOR MINIMUM
                    # an additional maximum is added ([ATE] p. 82 and 83)
                    
                    xmaxx = np.max(x[tminante:nmax+1])
                    nmaxx = np.where(x[tminante:nmax+1] == xmaxx)[0][0]               
                    nmaxx += tminante
                    
                    nc = n1[nmaxx] + 1
                    flagante = 1
                    n_j = np.append(n_j, np.floor((n1[nmaxx] + n2[nmaxx]) / 2.))
                    Jest += 1
                    
                    kadd = np.append(kadd, Jest-1)
                    iadd += 1
                
            elif flagmin == 1: # CURRENT extremum is also a MINIMUM
                               # an additional maximum is added ([ATE] p. 82)

                nc = n1[nmin]
                flagante = 1
                
                xmax = np.max(x[tminante:nc+1])
                nmax = np.where(x[tminante:nc+1] == xmax)[0][0] + tminante                
                
                n_j = np.append(n_j, np.floor((n1[nmax] + n2[nmax]) / 2.))                               
                Jest += 1
                
                kadd = np.append(kadd, Jest-1)
                iadd += 1
                
            else:
                nc = nc + Deltan
                
        else: # ANTERIOR extremum is a MAXIMUM
            
            tmaxante = np.abs(n_j[-1])
            xmaxante = x[tmaxante]
            
            if flagmin == 1: # CURRENT extremum is a MINIMUM
                
                if xmaxante > xmin:
                    
                    nc = n1[nmin] + 1
                    flagante = -1
                    
                    n_j = np.append(n_j, -np.floor((n1[nmin] + n2[nmin]) / 2.))
                    Jest += 1
                    
                else: # CURRENT MINIMUM is larger than the ANTERIOR MAXIMUM:
                      # an additional minimum is added ([ATE] p. 82 and 83)
                    
                    xminn = np.min(x[tmaxante:nmin+1])  
                    nminn = np.where(x[tmaxante:nmin+1] == xminn)[0][0]
                    nminn += tmaxante
                    
                    nc = n1[nminn] + 1
                    flagante = -1
                    
                    n_j = np.append(n_j, -np.floor((n1[nminn] + n2[nminn]) / 2.))                
                    Jest = Jest + 1

                    kadd = np.append(kadd, Jest-1)                
                    iadd += 1
                    
            elif flagmax == 1: # CURRENT extremum is also an MAXIMUM:
                               # an additional minimum is added ([ATE] p. 82)
                nc = n1[nmax]
                flagante = -1
                
                xmin = np.min(x[tmaxante:nc+1])
                nmin = np.where(x[tmaxante:nc+1] == xmin)[0]            
                nmin += tmaxante
                
                n_j = np.append(n_j, -np.floor((n1[nmin] + n2[nmin]) / 2.))
                Jest += 1
                
                kadd = np.append(kadd, Jest-1)
                iadd += 1
                
            else:
                nc = nc + Deltan
            
#    # x(ni) is not included in the partition of scale Deltan 
#    nj1 = np.abs(n_j[0])
#    if nj1 > ni:
#        if n1[nj1] > ni: # the boundary ni is not included in the plateau
#                         # containing the first local extremum at n_j[1] and it
#                         # is added as an additional local extremum ([ATE] p. 83)
#            n_j = np.hstack((-np.sign(n_j[0]) * ni, n_j))
#            Jest += 1
#            
#            kadd = np.hstack((0, kadd + 1))
#            iadd += 1
#
#        else: # the boundary ni is included in the plateau containing
#              # the first local extremum at n_j(1) and then the first local
#              # extremum is moved at the boundary of the plateau
#            n_j[0] = np.sign(n_j[0]) * ni
   
   
#    # the same situation as before but for the other boundary nf
#    njJ = np.abs(n_j[Jest])
#    if njJ < nf:
#        if n2[njJ] < nf:
#            n_j = np.append(n_j, -np.sign(n_j[Jest]) * nf)
#            Jest += 1
#
#            kadd = np.append(kadd, Jest)
#            iadd += 1
#        else:
#            n_j[Jest] = np.sign(n_j[Jest]) * nf
   
    return n_j, kadd
   


if __name__ == '__main__':
    
    from matplotlib import pyplot as plt
    import xlrd
    from meteo import MeteoObj
    from hydroprint import WaterlvlData, filt_data
    
    plt.close('all')
    
    fmeteo = 'Files4testing/AUTEUIL_2000-2013.out'
    fwaterlvl = 'Files4testing/PO16A.xls'
    
    waterLvlObj = WaterlvlData()
    waterLvlObj.load(fwaterlvl)
    
    x = waterLvlObj.lvl
    x = 100-x[:500]
    
    t = waterLvlObj.time
    t = t[:500]
    
    
    app = QtGui.QApplication(argv)
    instance_1 = MRCalc()
    instance_1.show()
    app.exec_() 
    
#    # http://stackoverflow.com/questions/15721094
#    fig = plt.figure()
#    plt.plot(t, x)
#    def onclick(event):
#        if event.xdata != None and event.ydata != None:
#            print(event.xdata, event.ydata)
#            plt.plot(event.xdata, event.ydata, 'or')
#    cid = fig.canvas.mpl_connect('button_press_event', onclick)

#    plt.show()
    
    
#    # ---- Without smoothing ----
#    
#    plt.figure()
#    plt.plot(x)
#    plt.plot(x, '.')
#    
#    n_j, n_add = local_extrema(x, 4 * 2)
#    print n_j
#    
#    n_j = np.abs(n_j).astype(int)  
#    n_add = np.abs(n_add).astype(int) 
#    
#    plt.plot(n_j, x[n_j], 'or' )
#    
#    # ---- With smoothing ----
#    
#    tfilt, xfilt = filt_data(t, x, 4)
#    
#    plt.figure()
#    plt.plot(t, x)
#    plt.plot(tfilt, xfilt, 'r')
#    
#    n_j, _ = local_extrema(xfilt, 4 * 3)
#    
#    n_j = np.abs(n_j).astype(int)  
#    
#    plt.plot(tfilt[n_j], xfilt[n_j], 'or' )