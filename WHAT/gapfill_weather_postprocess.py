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
"""

#---- STANDARD LIBRARY IMPORTS ----

import csv, sys, os
from copy import copy

#---- THIRD PARTY IMPORTS ----

#from PySide import QtGui

import matplotlib as mpl
mpl.use('Qt4Agg')
mpl.rcParams['backend.qt4'] = 'PySide'
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
#from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

import numpy as np
import scipy.stats as stats 

from xlrd.xldate import xldate_from_date_tuple
#from xlrd import xldate_as_tuple

#---- PERSONAL IMPORTS ----

import meteo
#import database as db
#from hydrograph3 import LatLong2Dist

#==============================================================================
class PostProcessErr(object):
#==============================================================================
   
    def __init__(self, fname):
        
        self.Yp = None
        self.Ym = None 
        self.Time = None
        self.Date = None
        
        self.fname = fname
        self.dirname = os.path.dirname(self.fname)
        self.load_err_file()

        
    def load_err_file(self): #=============================== Load err. File ==
        
        with open(self.fname) as f:
            reader = list(csv.reader(f, delimiter='\t'))
        
        #---- Finds Station Info + First Row of Data ----
        
        row = 0
        while True:
            
            if row > 25:
                print('Something is wrong with the ' +
                      'formatting of the .err file')
                return
    
            try:
                if reader[row][0] == 'VARIABLE':
                    break
                elif reader[row][0] == 'Station Name':
                    self.staName = reader[row][1]
                elif reader[row][0] == 'Climate Identifier':
                    self.climID = reader[row][1]
            except IndexError: 
                pass
            
            row += 1
        row += 1
    
        #------------------------------------------------- Re-Organizes Data --
        
        # Get unique weather variable names
        
        DATA = np.array(reader[row:])   
        self.varNames = np.unique(DATA[:, 0])
        self.varTypes = ['continuous'] * (len(self.varNames))
        
        # Splits data acoording to the weather variables found.
        
        self.Yp, self.Ym, self.Time, self.Date = [], [], [], []
        for i, var in enumerate(self.varNames):
            indx = np.where(DATA[:, 0] == var)[0]
            
            self.Yp.append(DATA[indx, 7].astype(float))
            self.Ym.append(DATA[indx, 8].astype(float))
            
            y = DATA[indx, 1].astype(int)
            m = DATA[indx, 2].astype(int)
            d = DATA[indx, 3].astype(int)
            
            #---- Time ----
            
            t = np.zeros(len(y))
            for date in range(len(y)):
                t[date] = (xldate_from_date_tuple((y[date],
                                                   m[date],
                                                   d[date]), 0)
                           - xldate_from_date_tuple((y[date], 1, 1), 0))
                
            self.Time.append(t)
            self.Date.append([y, m, d])
            
            #---- Weather Variable Type ----
            
            # If the proportion of zeros in the data series is higher 
            # than 25%, the data type is set as an event-based weather
            # variable. Otherwise, default value is kept and variable is 
            # considered to be continuous in time.
            #
            # The precipitation (solid, liquid or total) is a good example of
            # an event-based variable, while air temperature (min, max or mean)
            # is a good example of a continuous variable.
          
            pc0 = len(np.where(self.Ym[i] == 0)[0]) / float(len(self.Ym[i]))
            if pc0 > 0.25:
                self.varTypes[i] = 'event-based'
            
        return
    
    def generates_graphs(self): #========================== Generates Graphs ==
        
        for i in range(len(self.Yp)):
            fname = '%s/%s.pdf' % (self.dirname, self.varNames[i])
            self.plot_est_err(self.Ym[i], self.Yp[i], self.varNames[i], fname)
            print('Generating %s.' % (os.path.basename(fname)))
            
            if self.varNames[i] == 'Total Precip (mm)':
                fname = '%s/%s.pdf' % (self.dirname, 'precip_PDF')
                self.plot_gamma_dist(self.Ym[i], self.Yp[i], fname)
                print('Generating %s.' % (os.path.basename(fname)))
                
        
    @staticmethod
    def plot_est_err(Ymes, Ypre, varName, fname): #============= Est. Errors ==
            
        Ymax = np.ceil(np.max(Ymes) / 10) * 10
        Ymin = np.floor(np.min(Ymes) / 10) * 10
        
        fw, fh = 6, 6
        fig = mpl.figure.Figure(figsize=(fw, fh))
        canvas = FigureCanvas(fig)
        
        #------------------------------------------------------- Create Axes --
        
        leftMargin  = 1. / fw
        rightMargin = 0.25 / fw
        bottomMargin = 0.8 / fh
        topMargin = 0.25 / fh
      
        x0 = leftMargin 
        y0 = bottomMargin
        w0 = 1 - (leftMargin + rightMargin)
        h0 = 1 - (bottomMargin + topMargin)
            
        ax0 = fig.add_axes([x0, y0, w0, h0])
        ax0.set_axisbelow(True)
        ax0.grid(axis='both', color='0.', linestyle='--', linewidth=0.5,
                 dashes=[0.5, 3])
        
        #-------------------------------------------------------------- Plot --
        
        #---- Estimation Error ----
        
        hscat, = ax0.plot(Ymes, Ypre, '.', mec='k', mfc='k', ms=12, alpha=0.35)
             
        #---- 1:1 Line ----
        
        dl = 12    # dashes length
        ds = 6     # spacing between dashes 
        dew = 0.5  # dashes edge width    
        dlw = 1.5  # dashes line width
        
        # Plot a white contour line
        ax0.plot([Ymin, Ymax], [Ymin, Ymax], '-w', lw=dlw + 2 * dew, alpha = 1)
        
        # Plot a black dahsed line
        hbl, = ax0.plot([Ymin, Ymax], [Ymin, Ymax], 'k', lw=dlw,
                        dashes=[dl, ds], dash_capstyle='butt')
                 
        #-------------------------------------------------------------- Text --
        
        #---- Calculate Statistics ----
        
        RMSE = (np.mean((Ypre - Ymes) ** 2)) ** 0.5
        MAE = np.mean(np.abs(Ypre - Ymes))
        ME = np.mean(Ypre - Ymes)
        r = np.corrcoef(Ypre, Ymes)[1, 0]
        
        #---- Generate and Plot Labels ----
        
        if varName in ['Max Temp (deg C)', 'Mean Temp (deg C)',
                       'Min Temp (deg C)']:
            units = u'°C'
        elif varName in ['Total Precip (mm)']:
            units = 'mm'
        else:
            units = ''
            
        tcontent = [u'RMSE = %0.1f %s' % (RMSE, units),
                    u'MAE = %0.1f %s' % (MAE, units),
                    u'ME = %0.2f %s' % (ME, units),
                    u'r = %0.3f' % (r)]
        tcontent = list(reversed(tcontent))
         
        #---- Plot Labels ----
                  
        for i in range(len(tcontent)):
            dx, dy = -10 / 72., 10 * (i+1) / 72.
            padding = mpl.transforms.ScaledTranslation(dx, dy, 
                                                       fig.dpi_scale_trans)
            transform = ax0.transAxes + padding
            ax0.text(0, 0, tcontent[i], ha='left', va='bottom', fontsize=16,
                     transform=transform)
        
        #---- Get Labels Win. Extents ----
        
        hext, vext = np.array([]), np.array([])
        renderer = canvas.get_renderer()
        for text in ax0.texts:
            bbox = text.get_window_extent(renderer)
            bbox = bbox.transformed(ax0.transAxes.inverted())
            hext = np.append(hext, bbox.width)
            vext = np.append(vext, bbox.height)
        
        #---- Position Labels in Axes ----
        
        x0 = 1 - np.max(hext)
        y0 = 0
        for i, text in enumerate(ax0.texts):
            text.set_position((x0, y0))
            y0 += vext[i]
        
        #------------------------------------------------------------ Labels --
        
        #---- Ticks ----
        
        ax0.xaxis.set_ticks_position('bottom')
        ax0.yaxis.set_ticks_position('left')
        ax0.tick_params(axis='both', direction='out', labelsize=14)
        
        #---- Axis ----
        
        if varName == 'Max Temp (deg C)':
            var = u'Daily Max Temperature (°C)'
        elif varName == 'Mean Temp (deg C)':
            var = u'Daily Mean Temperature (°C)'
        elif varName == 'Min Temp (deg C)':
            var = u'Daily Min Temperature (°C)'
        elif varName == 'Total Precip (mm)':
            var = 'Daily Total Precipitation (mm)'
        else:
            var = ''
            
        ax0.set_ylabel('Measured %s' % var, fontsize=16, labelpad=15)
        ax0.set_xlabel('Predicted %s' % var, fontsize=16, labelpad=15)
    
        #-------------------------------------------------------------- Axis --
        
        ax0.axis([Ymin, Ymax, Ymin, Ymax])
    
        #------------------------------------------------------------ Legend --       
        
        ax0.legend([hscat, hbl], ['Daily Weather Data', '1:1'],
                   loc='upper left', numpoints=1, frameon=False, fontsize=16)
        
        #-------------------------------------------------------------- Draw --
        
        fig.savefig(fname)

        return canvas
    
    
    @staticmethod
    def plot_gamma_dist(Ymes, Ypre, fname): #================ Plot Gamma PDF ==
                   
        fw, fh = 6, 6
        fig = mpl.figure.Figure(figsize=(fw, fh), facecolor='white')
        canvas = FigureCanvas(fig)
        
        #------------------------------------------------------- Create Axes --
        
        leftMargin  = 1.1 / fw
        rightMargin = 0.25 / fw
        bottomMargin = 0.85 / fh
        topMargin = 0.25 / fh
      
        x0 = leftMargin 
        y0 = bottomMargin
        w0 = 1 - (leftMargin + rightMargin)
        h0 = 1 - (bottomMargin + topMargin)
            
        ax0 = fig.add_axes([x0, y0, w0, h0])    
        ax0.set_yscale('log')
        
        Xmax = max(np.ceil(np.max(Ymes)/10.) * 10, 120)
        
        #------------------------------------------------------------- Plots --
        
        c1, c2 = '#6495ED', 'red'
        
        #---- Histogram ----
                 
        ax0.hist(Ymes, bins=20, color=c1, normed=True, histtype='stepfilled',
                 alpha=0.25, ec=c1, label='Measured Data PDF')  
                 
        #---- Measured Gamma PDF ----
        
        alpha, loc, beta = stats.gamma.fit(Ymes)
        x = np.arange(0.5, Xmax, 0.1)
        ax0.plot(x, stats.gamma.pdf(x, alpha, loc=loc, scale=beta), '-', lw=2,
                 alpha=1., color=c1, label='Gamma PDF (measured)')
        
        #---- Predicted Gamma PDF ----
        
        alpha, loc, beta = stats.gamma.fit(Ypre)
        x = np.arange(0.5, Xmax, 0.1)
        ax0.plot(x, stats.gamma.pdf(x, alpha, loc=loc, scale=beta), '--r',
                 lw=2, alpha=0.85, color=c2, label='Gamma PDF (estimated)')
        
        #------------------------------------------------------- Axis Limits --
        
#        ax0.set_xlim(0, Xmax)
        ax0.axis(xmin=0, xmax=Xmax, ymax=1)
        
        #------------------------------------------------------------ Labels --
        
        #---- axis labels ----
    
        ax0.set_xlabel('Daily Precipitation (mm)', fontsize=18, labelpad=15)
        ax0.set_ylabel('Probability', fontsize=18, labelpad=15)
        
        #---- yticks labels ----
        
        ax0.xaxis.set_ticks_position('bottom')
        ax0.yaxis.set_ticks_position('left')
        ax0.tick_params(axis='both', direction='out', labelsize=14)
        ax0.tick_params(axis='both', which='minor', direction='out',
                        labelsize=14)
        
        canvas.draw()
        ylabels = []
        for i, label in enumerate(ax0.get_yticks()):
            if label >= 1:
                ylabels.append('%d' % label)
            elif label <= 10**-3:
                ylabels.append('$\mathdefault{10^{%d}}$' % np.log10(label))
            else:
                ylabels.append(str(label))
        ax0.set_yticklabels(ylabels)
    
        #------------------------------------------------------------ Legend --
    
        lg = ax0.legend(loc='upper right', frameon=False)
        
        #----------------------------------------------- Wet Days Comparison --
        
        #---- Generate text ----
        
        preWetDays = np.where(Ypre > 0)[0]
        mesWetDays = np.where(Ymes > 0)[0]
        
        f = len(preWetDays) / float(len(mesWetDays)) * 100
        
        if f > 100:
            msg = 'Number of wet days overestimated by %0.1f%%' % f
        else:
            msg = 'Number of wet days underestimated by %0.1f%%' % f
        
        #---- Get Legend Box Position and Extent ----
        
        canvas.draw()    
        bbox = lg.get_window_extent(canvas.get_renderer())
        bbox = bbox.transformed(ax0.transAxes.inverted())
        
        dx, dy = 5/72., 5/72. 
        padding = mpl.transforms.ScaledTranslation(dx, dy, fig.dpi_scale_trans)
        transform = ax0.transAxes + padding
        
        ax0.text(0., 0., msg, transform=transform, va='bottom', ha='left')
        
        #-------------------------------------------------------------- Draw --
        
        fig.savefig(fname) # A canvas.draw() is included with this.
        return canvas
    
def plot_rmse_vs_time(Ymes, Ypre, Time, Date, name):
    
    fw, fh = 6, 6
    fig = mpl.figure.Figure(figsize=(fw, fh), facecolor='white')
    canvas = FigureCanvas(fig)
    
    #----------------------------------------------------------- Create Axes --
    
    leftMargin  = 0.75 / fw
    rightMargin = 0.75 / fw
    bottomMargin = 0.75 / fh
    topMargin = 0.75 / fh
  
    x0, y0 = leftMargin, bottomMargin
    w0 = 1 - (leftMargin + rightMargin)
    h0 = 1 - (bottomMargin + topMargin)
        
    ax0 = fig.add_axes([x0, y0, w0, h0], polar=True)    
    
    #------------------------------------------------------------- Plot Data --
    
    #---- Estimation Error ----
    
    Yerr = np.abs(Ypre - Ymes)
    Time *= 2 * np.pi / 365.
    
    c = '0.4'
    ax0.plot(Time, Yerr, '.', mec=c, mfc=c, ms=15, alpha=0.5)
    
    #---- RMSE Polygon ----
    
    Months = Date[1]
    RMSE = np.zeros(12)
    mfd = np.zeros(12) 
    for m in range(12):
        mfd[m] = (xldate_from_date_tuple((2000, m+1, 1), 0) - 
                  xldate_from_date_tuple((2000, 1, 1), 0))
        indx = np.where(Months == m+1)[0]
        RMSE[m] = (np.mean(Yerr[indx] ** 2)) ** 0.5
    
    # Transform first day of the month to radians    
    mfd = mfd * 2 * np.pi / 365.
    
    # Add first point at the end to close the polygon
    mfd = np.append(mfd, mfd[0])
    RMSE = np.append(RMSE, RMSE[0])

    RMSEscl = RMSE * np.max(Yerr) / np.max(RMSE)    
    ax0.plot(mfd, RMSE * 5, ls= '--', c='red', lw=2, mec='b', mew=3, mfc='b',
             ms=10, dash_capstyle='round', dash_joinstyle='round')
             
    
    #---- RMSE Text ----
             
    #---------------------------------------------------------------- Labels --
    
    ax0.tick_params(axis='both', direction='out', labelsize=16)
    ax0.set_xticklabels(['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 
                         'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'])    
    ax0.set_xticks(mfd)
    
    ax0.set_yticklabels([])
    ax0.set_yticks([])
    ax0.set_rmax(1.1 * np.max(Yerr))
#    ax0.set_rgrids([10,20,30,40,50,60,70,80,90], angle=345.)
    
    #------------------------------------------------------------------ Draw --
    
#    ax0.set_ylim(0, )
#    ax0.set_xlim(0, np.pi)

    #------------------------------------------------------------- Axis Lim. --
    
    fig.savefig(name + '_polar_error.pdf')
    canvas.show()
    
           
if __name__ == '__main__': #=========================================== Main ==
    
#    app = QtGui.QApplication(sys.argv)
    
    # https://www.quora.com/Whats-the-easiest-way-to-recursively-get-a-list-
    # of-all-the-files-in-a-directory-tree-in-Python
    
    dirname = '../Projects/Valcartier/Meteo/Output/'
    for root, directories, filenames in os.walk(dirname):
        for filename in filenames:            
            if os.path.splitext(filename)[1] == '.err':
                print('---- %s ----' % os.path.basename(root))
                pperr = PostProcessErr(os.path.join(root, filename))
                pperr.generates_graphs()
            elif os.path.splitext(filename)[1] == '.out':
                print('---- %s ----' % os.path.basename(root))
                w = meteo.FigWeatherNormals()
                w.plot_monthly_normals(os.path.join(root, filename))                
                savename = 'weather_normals.pdf'
                print('Generating %s.' % savename)
                w.figure.savefig(os.path.join(root, savename))


#    for i in range(4):
#        plot_rmse_vs_time(Ym[i], Yp[i], Time[i], Date[i], varNames[i])
    
#    sys.exit(app.exec_())

