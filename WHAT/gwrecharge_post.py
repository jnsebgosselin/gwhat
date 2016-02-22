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
import h5py
import matplotlib as mpl
#from xlrd import xldate_as_tuple
#from xlrd.xldate import xldate_from_date_tuple
import matplotlib.pyplot as plt

#----- PERSONAL LIBRARY IMPORTS -----

from meteo import MeteoObj
from waterlvldata import WaterlvlData

def plot_rechg_GLUE(language='English'):
    
    fname = 'GLUE.h5'
    with h5py.File(fname,'r') as hf:
        data = hf.get('recharge')
        rechg = np.array(data)
        
        data = hf.get('RMSE')
        RMSE = np.array(data)
        
        data = hf.get('Time')
        TIME = np.array(data)
        
        data = hf.get('Weather')
        WEATHER = np.array(data)
        YEARS = WEATHER[:, 0].astype(int)
        MONTHS = WEATHER[:, 1].astype(int)
        PTOT = WEATHER[:, 6].astype(float)
        
        data = hf.get('Sy')
        Sy = np.array(data)
        
        data = hf.get('RASmax')
        RASmax = np.array(data)
        
        data = hf.get('Cru')
        Cru = np.array(data)
        
    print np.min(Sy), np.max(Sy) 
    print np.min(RASmax), np.max(RASmax)
    print np.min(Cru), np.max(Cru)
  
    RMSE = RMSE / np.sum(RMSE)
        
    Rbound = []
    for i in range(len(TIME)):
        isort = np.argsort(rechg[:, i])
        CDF = np.cumsum(RMSE[isort])        
        Rbound.append(np.interp([0.05, 0.5, 0.95], CDF, rechg[isort, i]))            
    Rbound = np.array(Rbound)
    
    #---- Define new variables ----

    yr2plot = np.arange(1997, 2014).astype('int')
    NYear = len(yr2plot)
    
    #---- Convert daily to hydrological year ----
    
    # the hydrological year is defined from October 1 to September 30 of the
    # next year.
    
    max_rechg_yrly = []
    min_rechg_yrly = []
    prob_rechg_yrly = []
    ptot_yrly = []
    
    for i in range(NYear):
        yr0 = yr2plot[i]
        yr1 = yr0 + 1
        
        indx0 = np.where((YEARS == yr0)&(MONTHS==10))[0][0]
        indx1 = np.where((YEARS == yr1)&(MONTHS==9))[0][-1]
                
        max_rechg_yrly.append(np.sum(Rbound[indx0:indx1+1, 2]))        
        min_rechg_yrly.append(np.sum(Rbound[indx0:indx1+1, 0]))
        prob_rechg_yrly.append(np.sum(Rbound[indx0:indx1+1, 1]))
        ptot_yrly.append(np.sum(PTOT[indx0:indx1+1]))
    
    max_rechg_yrly = np.array(max_rechg_yrly)
    min_rechg_yrly = np.array(min_rechg_yrly)
    prob_rechg_yrly = np.array(prob_rechg_yrly)
    ptot_yrly = np.array(ptot_yrly)
        

    #-------------------------------------------------------- Produce Figure --
    
    fig = plt.figure(figsize=(10, 6))
    fig.patch.set_facecolor('white')
    
    fheight = fig.get_figheight()
    fwidth = fig.get_figwidth()
    
    left_margin  = 1
    right_margin = 0.35
    bottom_margin = 1.1
    top_margin = 0.25
    
    x0 = left_margin / fwidth
    y0 = bottom_margin / fheight
    w0 = 1 - (left_margin + right_margin) / fwidth
    h0 = 1 - (bottom_margin + top_margin) / fheight
   
    #--------------------------------------------------------- AXES CREATION --

    ax0  = fig.add_axes([x0, y0, w0, h0])
    ax0.patch.set_visible(False)
    for axis in ['top','bottom','left','right']:
        ax0.spines[axis].set_linewidth(0.5)
    ax0.set_axisbelow(True)
    
    #------------------------------------------------------------ AXIS RANGE --       
    
    Ymin0 = 0
    Ymax0 = 600
    
    Xmin0 = min(yr2plot)-1
    Xmax0 = max(yr2plot)+1
    
    #------------------------------------------------------ XTICKS FORMATING -- 
    
    xtcklabl = [''] * NYear
    for i in range(NYear):        
        yr1 = str(yr2plot[i])[-2:]
        yr2 = str(yr2plot[i]+1)[-2:]
        xtcklabl[i] = "'%s - '%s" % (yr1, yr2)
                         
    ax0.xaxis.set_ticks_position('bottom')
    ax0.tick_params(axis='x',direction='out')
    ax0.set_xticks(yr2plot)
    ax0.xaxis.set_ticklabels(xtcklabl, rotation=45, ha='right')
    
    #------------------------------------------------------ YTICKS FORMATING --
 
    ax0.yaxis.set_ticks_position('left')
    ax0.set_yticks(np.arange(0, Ymax0+1, 100))
    ax0.tick_params(axis='y',direction='out', gridOn=True, labelsize=12)
    ax0.grid(axis='y', color=[0.35, 0.35, 0.35], linestyle=':',
             linewidth=0.5, dashes=[0.5, 5])
    
    ax0.set_yticks(np.arange(0, Ymax0, 50), minor=True)
    ax0.tick_params(axis='y',direction='out', which='minor', gridOn=False)
    
    #------------------------------------------------------------ AXIS RANGE --
    
    ax0.axis([Xmin0, Xmax0, Ymin0, Ymax0])

    #---------------------------------------------------------------- LABELS --
    ylabl = 'Annual Recharge (mm/y)'
    xlabl = ('Hydrological Years (October 1st of one ' +
             'year to September 30th of the next)')
    if language == 'French' :  
        ylabl = u"Colonne d'eau équivalente (mm)"
        xlabl = (u"Année Hydrologique (1er octobre d'une " +
                 u"année au 30 septembre de l'année suivante)")
                 
    ax0.set_ylabel(ylabl, fontsize=16,
                   verticalalignment='bottom')
    ax0.yaxis.set_label_coords(-0.07, 0.5)
    
    ax0.set_xlabel(xlabl, fontsize=16, verticalalignment='top')
    ax0.xaxis.set_label_coords(0.5, -0.175)
    
    #-------------------------------------------------------------- PLOTTING --
    
#    ax0.plot(yr2plot, ptot_yrly-900, marker='s', zorder=0)
    
    ax0.plot(yr2plot, prob_rechg_yrly, ls='--', color='0.35', zorder=100)    
    
    yerr = [prob_rechg_yrly-min_rechg_yrly, max_rechg_yrly-prob_rechg_yrly]
    herr = ax0.errorbar(yr2plot, prob_rechg_yrly, yerr=yerr,
                        fmt='o', capthick=1, capsize=3, ecolor='0',
                        elinewidth=1, mfc='White', mec='0', ms=5, mew=1,
                        zorder=200)
    
    #---------------------------------------------------------------- Legend --
      
    lg_handles = [herr[0], herr[1]]            
    lg_labels = ['Recharge (GLUE 50)', 'Recharge (GLUE 5/95)']
    
    ax0.legend(lg_handles, lg_labels, ncol=1, fontsize=12, frameon=False,
               numpoints=1, loc='upper left')
               
    #-------------------------------------------------------------- Averages --
    
    print('Mean annual Recharge (GLUE 95) = %0.f mm/y' % np.mean(max_rechg_yrly))
    print('Mean annual Recharge (GLUE 50)= %0.f mm/y' % np.mean(prob_rechg_yrly))
    print('Mean annual Recharge (GLUE 5) = %0.f mm/y' % np.mean(min_rechg_yrly))
    
    
    
#    (GLUE 5/50/95) = %0.f / %0.f / %0.f mm/y 
#            % (np.mean(min_rechg_yrly),
#               np.mean(prob_rechg_yrly),
#               np.mean(max_rechg_yrly)))
    
    text = (('Mean annual recharge : (GLUE 5) %d mm/y ; ' +
            '(GLUE 50) %d mm/y  ; (GLUE 95) %d mm/y')
            % (np.mean(min_rechg_yrly),
               np.mean(prob_rechg_yrly),
               np.mean(max_rechg_yrly)))
              
    
    dx, dy = 5/72., 5/72.
    padding = mpl.transforms.ScaledTranslation(dx, dy, fig.dpi_scale_trans)        
    transform = ax0.transAxes + padding
    ax0.text(0., 0., text, va='bottom', fontsize=12, transform=transform)
    
    #----- Some Calculation ----
        
    print('')
    print ('%d behavioural realizations' % len(RMSE))
    indx = np.where(prob_rechg_yrly == np.max(prob_rechg_yrly))[0][0]
    print ('Max. Recharge is %d mm/y at year %s' %
           (np.max(prob_rechg_yrly), xtcklabl[indx])            
           ) 
    indx = np.where(prob_rechg_yrly == np.min(prob_rechg_yrly))[0][0]
    print ('Min. Recharge is %d mm/y at year %s' %
           (np.min(prob_rechg_yrly), xtcklabl[indx])            
           ) 
    Runcer = max_rechg_yrly - min_rechg_yrly
    print('Max uncertainty is %d mm/y at year %s'
          % (np.max(Runcer) ,
             xtcklabl[np.where(Runcer == np.max(Runcer))[0][0]])
          )
    print('Min uncertainty is %d mm/y at year %s'
          % (np.min(Runcer) ,
             xtcklabl[np.where(Runcer == np.min(Runcer))[0][0]])
          ) 
    
    
#==============================================================================
def plot_water_budget_yearly(language = 'English'):
#==============================================================================
    
    #---- Load Results from csv ----
        
    fname = 'water_budget.csv'
    
    with open(fname, 'r') as f:
        reader = np.array(list(csv.reader(f, delimiter='\t'))[1:])
            
    DATA = np.array(reader[1:])        
        
    YEARS = DATA[:, 0].astype('int')
    MONTHS = DATA[:, 1].astype('int')
    
    PRECIP = DATA[:, 3].astype('float')  
    RU = DATA[:, 4].astype('float')
    ETR = DATA[:, 5].astype('float')
    RECHG = DATA[:, 6].astype('float')
    RAS = DATA[:, 7].astype('float')
    
    #---- Define new variables ----

    yr2plot = np.arange(1997, 2014).astype('int')
    NYear = len(yr2plot)
    
    YEARLY_PRECIP = np.zeros(NYear) 
    YEARLY_RECHG = np.zeros(NYear) 
    YEARLY_RU = np.zeros(NYear)
    YEARLY_ETR = np.zeros(NYear)
    YEARLY_dRAS = np.zeros(NYear)
    
    #---- Convert daily to hydrological year ----
    
    # the hydrological year is defined from October 1 to September 30 of the
    # next year.
    
    for i in range(NYear):
        yr0 = yr2plot[i]
        yr1 = yr0 + 1
        
        indx0 = np.where((YEARS == yr0)&(MONTHS==10))[0][0]
        indx1 = np.where((YEARS == yr1)&(MONTHS==9))[0][-1]
                
        YEARLY_PRECIP[i] = np.sum(PRECIP[indx0:indx1+1])
        YEARLY_RECHG[i] = np.sum(RECHG[indx0:indx1+1])
        YEARLY_RU[i] = np.sum(RU[indx0:indx1+1])
        YEARLY_ETR[i] = np.sum(ETR[indx0:indx1+1])
        YEARLY_dRAS[i] = RAS[indx1+1] - RAS[indx0]
        
        print(YEARLY_PRECIP[i] - YEARLY_RECHG[i] - YEARLY_RU[i] - 
              YEARLY_ETR[i] - YEARLY_dRAS[i])
        
    #---- Convert daily to calendar year ----
    
#    for i in range(NYear):
#        
#        indexes = np.where(YEARS == yr2plot[i])[0]
#        
#        YEARLY_PRECIP[i] = np.sum(PRECIP[indexes])
#        YEARLY_RECHG[i] = np.sum(RECHG[indexes])
#        YEARLY_RU[i] = np.sum(RU[indexes])
#        YEARLY_ETR[i] = np.sum(ETR[indexes])
        
    #---- Save Results in a csv ----
    
    fname = 'water_budget_yearly.csv'
    fcontent = [['From', 'To', 'PRECIP(mm)', 'RU(mm)',
                     'ETR(mm)', 'RECHG(mm)', 'dRAS(mm)']]
    for i in range(NYear):      
        fcontent.append(['01/10/%d' % yr2plot[i], 
                         '30/09/%d' % (yr2plot[i]+1),
                         '%0.1f' % YEARLY_PRECIP[i],
                         '%0.1f' % YEARLY_RU[i],
                         '%0.1f' % YEARLY_ETR[i],
                         '%0.1f' % YEARLY_RECHG[i],
                         '%0.1f' % YEARLY_dRAS[i]])
                                
    with open(fname, 'w') as f:
        writer = csv.writer(f, delimiter='\t', lineterminator='\n')
        writer.writerows(fcontent)
    
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
    
    Ymin0 = 200
    Ymax0 = 1600
    
    Xmin0 = yr2plot[0] - 0.5
    Xmax0 = yr2plot[-1] + 0.5
    
    #------------------------------------------------------ XTICKS FORMATING -- 
    
    tcklabl = [''] * NYear
    for i in range(NYear):
        if yr2plot[i] >= 2000:
            tcklabl[i] = "'%02d" % (yr2plot[i] - 2000)
        else:
            tcklabl[i] = "'%02d" % (yr2plot[i] - 1900)
        
    ax0.xaxis.set_ticks_position('bottom')
    ax0.tick_params(axis='x',direction='out', gridOn=False, labelsize=14)
    ax0.set_xticks(yr2plot)
    
    #------------------------------------------------------ YTICKS FORMATING --
 
    ax0.yaxis.set_ticks_position('left')
    ax0.tick_params(axis='y',direction='out', gridOn=True, labelsize=14)
    
    ax0.set_yticks(np.arange(0, Ymax0, 50), minor=True)
    ax0.tick_params(axis='y',direction='out', which='minor', gridOn=False)
    
    #------------------------------------------------------------ AXIS RANGE --
    
    ax0.axis([Xmin0, Xmax0, Ymin0, Ymax0])

    #---------------------------------------------------------------- LABELS --
    ylabl = 'Equivalent Water (mm)'
    xlabl = ('Hydrological Years (October 1st of one ' +
             'year to September 30th of the next)')
    if language == 'French' :  
        ylabl = u"Colonne d'eau équivalente (mm)"
        xlabl = (u"Année Hydrologique (1er octobre d'une " +
                 u"année au 30 septembre de l'année suivante)")
                 
    ax0.set_ylabel(ylabl, fontsize=16,
                   verticalalignment='bottom')
    ax0.yaxis.set_label_coords(-0.05, 0.5)

    ax0.set_xlabel(xlabl, fontsize=16, verticalalignment='top')
    ax0.xaxis.set_label_coords(0.5, -0.075)
    
    #-------------------------------------------------------------- PLOTTING --
    
    COLOR = [[0./255, 128./255, 255./255],
             [0./255, 76./255, 153./255],
             [0./255, 25./255, 51./255],              
             [102./255, 178./255, 255./255]]
    LABEL = ['Total Precipitation', 'Recharge', 'Runoff',
             'Real Evapotranspiration']
    if language == 'French' :        
        LABEL = [u'Précipitations Totales', 'Recharge', 'Ruissellement',
                 u'Évapotranspiration Réelle']      
             
    MARKER = ['o', 'h', 's', 'D']
    DATA = [YEARLY_PRECIP, YEARLY_RECHG, YEARLY_RU, YEARLY_ETR]
    lspoint = '-'
#    lstrend = '--'
    
    for i in range(4):
        ax0.plot(yr2plot, DATA[i], color=COLOR[i], markeredgecolor='white',
                 marker=MARKER[i], markersize=9, linestyle=lspoint,
                 label=LABEL[i], clip_on=False, zorder=100, alpha=0.85)
             
#    A = np.polyfit(YEAR-0.5, YEARLY_PRECIP, 1)
#    print 'Trend Precip =', A[0], ' mm/y'
#    TREND1 = A[0]*(YEAR-0.5) + A[1]
#    ax0.plot(YEAR-0.5, TREND1, color='blue', linestyle=lstrend,
#             marker='None', label='Trend Line Precipitation', clip_on=False,
    
    #------------------------------------------------------- YEARLY AVERAGES -- 
    
#    ax0.text(YEAR[0] - 1 + 0.1, 40,
#         'Mean Yearly Precipitation = %d mm' % np.mean(YEARLY_PRECIP),
#         color='b', fontsize=14)
#             
#    ax0.text(YEAR[0] - 1 + 0.1, 130,
#             'Mean Yearly Recharge = %d mm' % np.mean(YEARLY_RECHG),
#             color='orange', fontsize=14)
             
    #---------------------------------------------------------------- LEGEND --   
    
    ax0.legend(loc=2, ncol=3, numpoints=1, fontsize=14, frameon=False)
    
    fig.savefig('yearly_budget.pdf')

#==============================================================================
def plot_water_budget_yearly2(language='English'):
#==============================================================================
    
    #---- Load Results from csv ----
        
    fname = 'water_budget.csv'
    
    with open(fname, 'r') as f:
        reader = np.array(list(csv.reader(f, delimiter='\t'))[1:])
            
    DATA = np.array(reader[1:])        
        
    YEARS = DATA[:, 0].astype('int')
    MONTHS = DATA[:, 1].astype('int')
    
    PRECIP = DATA[:, 3].astype('float')  
    RU = DATA[:, 4].astype('float')
    ETR = DATA[:, 5].astype('float')
    RECHG = DATA[:, 6].astype('float')
    RAS = DATA[:, 7].astype('float')
    
    #---- Define new variables ----

    yr2plot = np.arange(1997, 2014).astype('int')
    NYear = len(yr2plot)
    
    YEARLY_PRECIP = np.zeros(NYear) 
    YEARLY_RECHG = np.zeros(NYear) 
    YEARLY_RU = np.zeros(NYear)
    YEARLY_ETR = np.zeros(NYear)
    YEARLY_dRAS = np.zeros(NYear)
    
    #---- Convert daily to hydrological year ----
    
    # the hydrological year is defined from October 1 to September 30 of the
    # next year.
    
    for i in range(NYear):
        yr0 = yr2plot[i]
        yr1 = yr0 + 1
        
        indx0 = np.where((YEARS == yr0)&(MONTHS==10))[0][0]
        indx1 = np.where((YEARS == yr1)&(MONTHS==9))[0][-1]
                
        YEARLY_PRECIP[i] = np.sum(PRECIP[indx0:indx1+1])
        YEARLY_RECHG[i] = np.sum(RECHG[indx0:indx1+1])
        YEARLY_RU[i] = np.sum(RU[indx0:indx1+1])
        YEARLY_ETR[i] = np.sum(ETR[indx0:indx1+1])
        YEARLY_dRAS[i] = RAS[indx1+1] - RAS[indx0]
        
        print(YEARLY_PRECIP[i] - YEARLY_RECHG[i] - YEARLY_RU[i] - 
              YEARLY_ETR[i] - YEARLY_dRAS[i])

    #---- Save Results in a csv ----
    
    fname = 'water_budget_yearly.csv'
    fcontent = [['From', 'To', 'PRECIP(mm)', 'RU(mm)',
                     'ETR(mm)', 'RECHG(mm)', 'dRAS(mm)']]
    for i in range(NYear):      
        fcontent.append(['01/10/%d' % yr2plot[i], 
                         '30/09/%d' % (yr2plot[i]+1),
                         '%0.1f' % YEARLY_PRECIP[i],
                         '%0.1f' % YEARLY_RU[i],
                         '%0.1f' % YEARLY_ETR[i],
                         '%0.1f' % YEARLY_RECHG[i],
                         '%0.1f' % YEARLY_dRAS[i]])
                                
    with open(fname, 'w') as f:
        writer = csv.writer(f, delimiter='\t', lineterminator='\n')
        writer.writerows(fcontent)
        
    #---- Produce Figure ----
    
    fig = plt.figure(figsize=(15, 7))
    fig.patch.set_facecolor('white')
    
    fheight = fig.get_figheight()
    fwidth = fig.get_figwidth()
    
    left_margin  = 1
    right_margin = 0.35
    bottom_margin = 1.
    top_margin = 0.25
    
    x0 = left_margin / fwidth
    y0 = bottom_margin / fheight
    w0 = 1 - (left_margin + right_margin) / fwidth
    h0 = 1 - (bottom_margin + top_margin) / fheight
   
    #--------------------------------------------------------- AXES CREATION --

    ax0  = fig.add_axes([x0, y0, w0, h0])
    ax0.patch.set_visible(False)
    for axis in ['top','bottom','left','right']:
        ax0.spines[axis].set_linewidth(0.5)
        
    #------------------------------------------------------------ AXIS RANGE --       
    
    Ymin0 = 0
    Ymax0 = 1700
    
    Xmin0 = 0
    Xmax0 = NYear * 3
    
    #------------------------------------------------------ XTICKS FORMATING -- 
    
    xtcklabl = [''] * NYear
    for i in range(NYear):
        
        yr1 = str(yr2plot[i])[-2:]
        yr2 = str(yr2plot[i]+1)[-2:]
        xtcklabl[i] = "'%s - '%s" % (yr1, yr2)
        
    xtckpos = np.arange(NYear * 3 + 1)
                         
    ax0.xaxis.set_ticks_position('bottom')
    ax0.tick_params(axis='x',direction='out')
    ax0.xaxis.set_ticklabels([])
    ax0.set_xticks(xtckpos[::3])
    
    ax0.set_xticks(xtckpos[::3] + 1.5, minor=True)        
    ax0.tick_params(axis='x', which='minor', length=0, labelsize=12, pad=2)
    ax0.xaxis.set_ticklabels(xtcklabl, minor=True, rotation=45, ha='right')
    
    #------------------------------------------------------ YTICKS FORMATING --
 
    ax0.yaxis.set_ticks_position('left')
    ax0.set_yticks(np.arange(0, Ymax0, 500))
    ax0.tick_params(axis='y',direction='out', gridOn=False, labelsize=14)
    
    ax0.set_yticks(np.arange(0, Ymax0, 50), minor=True)
    ax0.tick_params(axis='y',direction='out', which='minor', gridOn=False)
    
    #------------------------------------------------------------ AXIS RANGE --
    
    ax0.axis([Xmin0, Xmax0, Ymin0, Ymax0])

    #---------------------------------------------------------------- LABELS --
    ylabl = 'Equivalent Water (mm)'
    xlabl = ('Hydrological Years (October 1st of one ' +
             'year to September 30th of the next)')
    if language == 'French' :  
        ylabl = u"Colonne d'eau équivalente (mm)"
        xlabl = (u"Année Hydrologique (1er octobre d'une " +
                 u"année au 30 septembre de l'année suivante)")
                 
    ax0.set_ylabel(ylabl, fontsize=16,
                   verticalalignment='bottom')
    ax0.yaxis.set_label_coords(-0.05, 0.5)
    
    ax0.set_xlabel(xlabl, fontsize=16, verticalalignment='top')
    ax0.xaxis.set_label_coords(0.5, -0.125)
    
    #-------------------------------------------------------------- PLOTTING --
    
    COLOR = [[0./255, 25./255, 51./255],
             [0./255, 76./255, 153./255],
             [0./255, 128./255, 255./255],              
             [102./255, 178./255, 255./255]]
             
    LABEL = ['Total Precipitation', 'Recharge', 'Runoff',
             'Real Evapotranspiration']
    if language == 'French' :       
        LABEL = [u'Précipitations Totales', 'Recharge', 'Ruissellement',
                 u'Évapotranspiration Réelle']

    bar_width = 0.85

    ax0.bar(xtckpos[1::3], YEARLY_PRECIP, align='center', width=bar_width,
            color=COLOR[0], edgecolor='None', label=LABEL[0])
    
    var2plot = YEARLY_RECHG + YEARLY_ETR + YEARLY_RU
    ax0.bar(xtckpos[2::3], var2plot, align='center', width=bar_width,
            color=COLOR[3], edgecolor='None', label=LABEL[2])
            
    var2plot = YEARLY_RECHG + YEARLY_ETR
    ax0.bar(xtckpos[2::3], var2plot, align='center', width=bar_width,
            color=COLOR[2], edgecolor='None', label=LABEL[3])
    
    var2plot = YEARLY_RECHG
    ax0.bar(xtckpos[2::3], var2plot, align='center', width=bar_width,
            color=COLOR[1], edgecolor='None', label=LABEL[1])

    #--------------------------------------------------------- PLOTTING TEXT --
    
    for i in range(NYear):
        y = YEARLY_PRECIP[i] / 2.
        x = 1 + 3 * i
        txt = '%0.1f' % YEARLY_PRECIP[i]
        ax0.text(x, y, txt, color='white', va='center', ha='center',
                 rotation=90, fontsize=10)
                 
        y = YEARLY_RECHG[i] / 2.
        x = 2 + 3 * i
        txt = '%0.1f' % YEARLY_RECHG[i]
        ax0.text(x, y, txt, color='white', va='center', ha='center',
                 rotation=90, fontsize=10)
                 
        y = YEARLY_ETR[i] / 2. + YEARLY_RECHG[i]
        x = 2 + 3 * i
        txt = '%0.1f' % YEARLY_ETR[i]
        ax0.text(x, y, txt, color='black', va='center', ha='center',
                 rotation=90, fontsize=10)
                 
        y = YEARLY_RU[i] / 2. + YEARLY_RECHG[i] + YEARLY_ETR[i]
        x = 2 + 3 * i
        txt = '%0.1f' % YEARLY_RU[i]
        ax0.text(x, y, txt, color='black', va='center', ha='center',
                 rotation=90, fontsize=10)
    #---------------------------------------------------------------- LEGEND --   
    
    ax0.legend(loc=2, ncol=2, numpoints=1, fontsize=14, frameon=False)
    
    fig.savefig('yearly_budget2.pdf')
    
if __name__ == '__main__':
    
    plt.close('all')
#    plot_water_budget_yearly(language='French')
#    plot_water_budget_yearly2(language='French')
    
    plot_rechg_GLUE()
    plt.show()


