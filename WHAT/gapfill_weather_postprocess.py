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

#-- STANDARD LIBRARY IMPORTS --

import csv
import sys
from time import strftime, sleep
import os
from copy import copy
from time import clock

#-- THIRD PARTY IMPORTS --

import matplotlib as mpl
mpl.use('Qt4Agg')
mpl.rcParams['backend.qt4'] = 'PySide'
#from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

import numpy as np
from numpy.linalg import lstsq as linalg_lstsq
from xlrd.xldate import xldate_from_date_tuple
from xlrd import xldate_as_tuple
from PySide import QtCore, QtGui

#-- PERSONAL IMPORTS --

import meteo
import database as db
from hydrograph3 import LatLong2Dist


def load_err_file(fname):
    
    with open(fname) as f:
        reader = list(csv.reader(f, delimiter='\t'))
    
    #---- First Row ----
    
    row = 0
    while True:
        
        if row > 25:
            print('Something is wrong with the formatting of the .err file')
            return

        try:
            if reader[row][0] == 'VARIABLE':
                break             
        except IndexError: 
            pass
        
        row += 1
    row += 1

    #---- Organize data ----

    DATA = np.array(reader[row:])   
    VARNAMES = np.unique(DATA[:, 0])
    print VARNAMES
    
    err, Yp, Ym = [], [], []
    for i, var in enumerate(VARNAMES):
        indx = np.where(DATA[:, 0] == var)[0]
        
        err.append(DATA[indx, 4])
        Yp.append(DATA[indx, 5])
        Ym.append(DATA[indx, 6])
        
    return(Yp, Ym, VARNAMES)
        
def plot_est_err(Yp, Ym, name):
    
    Ypre = np.array(Yp).astype(float)
    Ymes = np.array(Ym).astype(float)
    
    Ymax = np.max(Ymes)
    Ymin = np.min(Ymes)
    dYmax = np.max(Ypre - Ymes)
    dYmin = np.min(Ypre - Ymes)
    
    fig = mpl.figure.Figure(figsize=(6, 6))
    canvas = FigureCanvas(fig)
    
    ax0 = fig.add_axes([0.12, 0.1, 0.8, 0.85])
    mc = 'k'
    ax0.plot(Ymes, Ypre, '.', mec=mc, mfc=mc, ms=12, alpha=0.35)
    
    ax0.grid(axis='both', color='0.', linestyle='--', linewidth=0.5,
             dashes=[0.5, 3])
    ax0.set_axisbelow(True)
         
    #-------------------------------------------------------------- 1:1 Line --
    
    dl = 12     # dashes length
    ds = 6     # spacing between dashes 
    dew = 0.5    # dashes edge width    
    dlw = 1.5  # dashes line width
    
    shift = dew / 2. / 72. / np.sin(np.radians(45)) 
    offset = mpl.transforms.ScaledTranslation(shift, shift, fig.dpi_scale_trans)
    transform = ax0.transData + offset
    
    #---- White Line ----

    ax0.plot([Ymin, Ymax], [Ymin, Ymax], '-w', lw=dlw + 2 * dew, alpha = 1)
    
    #---- Black Line ----

    ax0.plot([Ymin, Ymax], [Ymin, Ymax], 'k', lw=dlw, dashes=[dl, ds],
             dash_capstyle='butt', transform=transform)

    #------------------------------------------------------------------ Axis --
    
    ax0.axis([Ymin, Ymax, Ymin, Ymax])    
    ax0.set_ylabel('Measured')
    ax0.set_xlabel('Predicted')
        
    canvas.draw()
    canvas.show()
    canvas.setFixedSize(canvas.size())
    fig.savefig(name + '.pdf')
    
        
if __name__ == '__main__':
    
    app = QtGui.QApplication(sys.argv)
    
    fname = ('../Projects/Monteregie Est/Meteo/Output/' +
             'AUTEUIL (7020392)_1980-2009.err')
    Yp, Ym, varNames = load_err_file(fname)
    
    for i in range(4):
        plot_est_err(Yp[i], Ym[i], varNames[i])
    
    sys.exit(app.exec_())

