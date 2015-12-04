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

#----- STANDARD LIBRARY IMPORTS -----
      
#from datetime import date
import csv
import datetime

#----- THIRD PARTY IMPORTS -----

import numpy as np
#from xlrd import xldate_as_tuple
#from xlrd.xldate import xldate_from_date_tuple
import matplotlib.pyplot as plt

#----- PERSONAL LIBRARY IMPORTS -----

from meteo import MeteoObj
from waterlvldata import WaterlvlData

#==============================================================================
def plot_water_budget_yearly(PRECIP, RECHG, DATE_YEAR):
#==============================================================================
   
    YEAR = np.arange(1994, 2016).astype('int')    
    NYear = len(YEAR)
    
    YEARLY_PRECIP = np.zeros(NYear) 
    YEARLY_RECHG = np.zeros(NYear) 
#    YEARLY_RUNOFF = np.zeros(NYear)
#    YEARLY_ET = np.zeros(NYear)
#    YEARLY_QWSOIL = np.zeros(NYear)
    
    #---- Convert Daily to Yearly ----
    
    for i in range(NYear):
        indexes = np.where(DATE_YEAR == YEAR[i])[0]
        
        YEARLY_PRECIP[i] = np.sum(PRECIP[indexes])
        YEARLY_RECHG[i] = np.sum(RECHG[indexes])
#        YEARLY_RUNOFF[i] = np.sum(RUNOFF[indexes])
#        YEARLY_ET[i] = np.sum(ET[indexes])
#        YEARLY_QWSOIL[i] = np.sum(QWSOIL[indexes])
    
#    print
#    print 'Mean Yearly Precip = ', np.mean(YEARLY_PRECIP), 'mm'
#    print 'Mean Yearly Recharge = ', np.mean(YEARLY_RECHG), 'mm'
#    print 'Mean Yearly Runoff = ', np.mean(YEARLY_RUNOFF), 'mm'
#    print 'Mean Yearly ET = ', np.mean(YEARLY_ET), 'mm'
#    print 'Mean Yearly Recharge @ 1m = ', np.mean(YEARLY_QWSOIL), 'mm'
                    
    fig = plt.figure(figsize=(15, 7))
    fig.patch.set_facecolor('white')
    
    fheight = fig.get_figheight()
    fwidth = fig.get_figwidth()
    
    left_margin  = 1
    right_margin = 0.35
    bottom_margin = 0.75
    top_margin = 0.25
    
    x0 = left_margin / fwidth
    y0 = bottom_margin / fheight
    w0 = 1 - (left_margin + right_margin) / fwidth
    h0 = 1 - (bottom_margin + top_margin) / fheight
   
    #--------------------------------------------------------- AXES CREATION --

    ax0  = fig.add_axes([x0, y0, w0, h0])
    ax0.patch.set_visible(False)
        
    #------------------------------------------------------------ AXIS RANGE --       
    
    Ymin0 = 0
    Ymax0 = 1800
    
    Xmin0 = YEAR[0] - 1
    Xmax0 = YEAR[-1]
    
    #------------------------------------------------------ XTICKS FORMATING -- 
   
    ax0.xaxis.set_ticks_position('bottom')
    ax0.tick_params(axis='x',direction='out', gridOn=False, labelsize=14)
    ax0.set_xticks(YEAR)
    ax0.xaxis.set_ticklabels([])
    
    ax0.set_xticks(YEAR[::2]-0.4, minor=True)
    ax0.tick_params(axis='x', which='minor', length=0, gridOn=False, pad=5,
                    labelsize=14)
    ax0.xaxis.set_ticklabels(YEAR[::2], minor=True, rotation=90,
                             horizontalalignment='center')
    
    #------------------------------------------------------ YTICKS FORMATING --
 
    ax0.yaxis.set_ticks_position('left')
    ax0.tick_params(axis='y',direction='out', gridOn=True, labelsize=14)
    
    ax0.set_yticks(np.arange(0, Ymax0, 50), minor=True)
    ax0.tick_params(axis='y',direction='out', which='minor', gridOn=False)
    
    #------------------------------------------------------------ AXIS RANGE --
    
    ax0.axis([Xmin0, Xmax0, Ymin0, Ymax0])

    #---------------------------------------------------------------- LABELS --
    
    ax0.set_ylabel('Equivalent Water (mm)', fontsize=16,
                   verticalalignment='bottom')
    ax0.yaxis.set_label_coords(-0.05, 0.5)

#    
#    ax0.set_xlabel(LabelDB.years, fontsize=label_font_size,
#                   verticalalignment='top')
#    ax0.xaxis.set_label_coords(0.5, -0.075)
    
    #-------------------------------------------------------------- PLOTTING --
                         
    lspoint = '-'
    lstrend = '--'
    
    #----- PRECIP -----
    
    ax0.plot(YEAR-0.5, YEARLY_PRECIP,
             color='blue', markeredgecolor='None', marker='o',
             markersize=5, linestyle=lspoint, label='Precipitation',
             clip_on=False, zorder=100)
             
    A = np.polyfit(YEAR-0.5, YEARLY_PRECIP, 1)
    print 'Trend Precip =', A[0], ' mm/y'
    TREND1 = A[0]*(YEAR-0.5) + A[1]
    ax0.plot(YEAR-0.5, TREND1, color='blue', linestyle=lstrend,
             marker='None', label='Trend Line Precipitation', clip_on=False,
             zorder=100)
    
    #----- RECHG -----
    
    ax0.plot(YEAR-0.5, YEARLY_RECHG,
             color='orange', markeredgecolor='None', marker='^',
             markersize=8, linestyle=lspoint, label='Recharge',
             clip_on=False, zorder=100)  
             
    A = np.polyfit(YEAR-0.5, YEARLY_RECHG, 1)
    print 'Trend Rechg =', A[0], ' mm/y'
    TREND1 = A[0]*(YEAR-0.5) + A[1]
    ax0.plot(YEAR-0.5, TREND1, color='orange', linestyle=lstrend,
             marker='None', label='Trend Line Recharge', clip_on=False,
             zorder=100)             
    
#    #----- RUNOF -----    
#    
#    ax0.plot(YEAR-0.5, YEARLY_RUNOFF,
#             color='red', markeredgecolor='None', marker='s',
#             markersize=5, linestyle=lspoint, label='Runoff',
#             clip_on=False, zorder=100)
#             
#    A = np.polyfit(YEAR-0.5, YEARLY_RUNOFF, 1)
#    print 'Trend Runoff =', A[0], ' mm/y'
#    TREND1 = A[0]*(YEAR-0.5) + A[1]
#    ax0.plot(YEAR-0.5, TREND1, color='red', linestyle=lstrend,
#             marker='None', label='Trend Line Runoff', clip_on=False,
#             zorder=100) 
#    
#    #----- ETP -----
#        
#    ax0.plot(YEAR-0.5, YEARLY_ET,
#             color='green', markeredgecolor='None', marker='D',
#             markersize=5, linestyle=lspoint, label='ETP',
#             clip_on=False, zorder=100)
#             
#    A = np.polyfit(YEAR-0.5, YEARLY_ET, 1)
#    print 'Trend ETP =', A[0], ' mm/y'
#    TREND1 = A[0]*(YEAR-0.5) + A[1]
#    ax0.plot(YEAR-0.5, TREND1, color='green', linestyle=lstrend,
#             marker='None', label='Trend Line ETP', clip_on=False,
#             zorder=100) 

    #------------------------------------------------------- YEARLY AVERAGES -- 
    
    ax0.text(YEAR[0] - 1 + 0.1, 40,
         'Mean Yearly Precipitation = %d mm' % np.mean(YEARLY_PRECIP),
         color='b', fontsize=14)
             
    ax0.text(YEAR[0] - 1 + 0.1, 130,
             'Mean Yearly Recharge = %d mm' % np.mean(YEARLY_RECHG),
             color='orange', fontsize=14)
             
    #---------------------------------------------------------------- LEGEND --   
    
    ax0.legend(loc=2, ncol=2, numpoints=1, fontsize=14)
    
    fig.savefig('yearly_budget.pdf')






