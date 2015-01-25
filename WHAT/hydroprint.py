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

#----- STANDARD LIBRARY IMPORTS -----

from os import path
from calendar import monthrange
import csv
from math import sin, cos, sqrt, atan2, radians

#----- THIRD PARTY IMPORTS -----

import numpy as np
import matplotlib.pyplot as plt
from xlrd.xldate import xldate_from_date_tuple
from xlrd import xldate_as_tuple
from xlrd import open_workbook

class LabelDatabase():
    
    def __init__(self, language): #------------------------------- English -----
        
        self.temperature = u'Tmax weekly (°C)'
        self.mbgs = 'Water Level at Well %s (mbgs)'
        self.masl = 'Water Level at Well %s (masl)'
        self.precip = 'Ptot weekly (mm)'
        self.station_meteo = 'Climatological Station = %s (located %0.1f km from the well)'
        self.month_names = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                            "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
                            
        if language == 'French': #--------------------------------- French -----
            
            self.mbgs = "Niveau d'eau au puits %s (mbgs)"
            self.masl = "Niveau d'eau au puits %s (masl)"
            self.precip = 'Ptot hebdo (mm)'
            self.temperature = u'Tmax hebdo (°C)'
            self.station_meteo = u'Station climatologique = %s (située à %0.1f km du puits)'
            self.month_names = ["JAN", u"FÉV", "MAR", "AVR", "MAI", "JUN",
                                "JUL", u"AOÛ", "SEP", "OCT", "NOV", u"DÉC"]

class Hydrograph():
    
    def __init__(self, parent=None):
        
        'Do Nothing'
        
        self.fig = plt.figure()
        self.fig.patch.set_facecolor('white')
        self.fig.set_size_inches(11, 8.5)
        
    def generare_hydrograph(self, WaterLvlObj, MeteoObj, GraphParamObj):
        
        self.fig.clf()
    
        self.fig.patch.set_facecolor('white')
        
        fheight = GraphParamObj.fheight # Figure height in inches
        fwidth = GraphParamObj.fwidth   # Figure width in inches

        self.fig.set_size_inches(fwidth, fheight, forward=True)
       
        self.name_well = WaterLvlObj.name_well          
                
        fname_info = GraphParamObj.finfo
        
        self.TIMEmin = GraphParamObj.TIMEmin
        self.TIMEmax = GraphParamObj.TIMEmax
        
        isTitle = GraphParamObj.title_state # 1 -> title ; 0 -> no title
        graph_title = GraphParamObj.title_text
       
        language = GraphParamObj.language
        labelDB = LabelDatabase(language)
        
        self.date_labels_display_pattern = 2
        self.NZGrid = GraphParamObj.ygrid_divnumber            
        RAINscale = GraphParamObj.RAINscale
        
        self.WLref = GraphParamObj.WLref
        
        # Font size is multiplied by a ratio in order to keep the preview
        # and the final saved figure to the same scale. The preview
        # figure's size is modified when the UI is generated and depends
        # on the screen resolution.
        
        self.label_font_size = 14 * fheight / 8.5
            
        #-------------------------------------------------- FIGURE CREATION ----
        
        #---- MARGINS (Inches) ----
        
        left_margin  = 0.85 
        right_margin = 0.85
        bottom_margin = 0.75  
        if isTitle == 1:
            top_margin = 0.75
        else:
            top_margin = 0.25
        
        #---- MARGINS (% of figure) ----
        
        x0 = left_margin / fwidth
        y0 = bottom_margin / fheight
        w = 1 - (left_margin + right_margin) / fwidth
        h = 1 - (bottom_margin + top_margin) / fheight
            
        #-------------------------------------------------------- AXES CREATION ----        
        
        # http://stackoverflow.com/questions/15303284/
        # multiple-y-scales-but-only-one-enabled-for-pan-and-zoom
        
        # http://matplotlib.1069221.n5.nabble.com/Control-twinx-series-zorder-
        #        ax2-series-behind-ax1-series-or-place-ax2-on-left-ax1-on-right-
        #        td12994.html
        
        #---Time (host)---
        self.ax1  = self.fig.add_axes([x0, y0, w, h], zorder=0)
        self.ax1.axis([self.TIMEmin, self.TIMEmax, 0, self.NZGrid])
        
        #---Water Levels---
        self.ax2 = self.fig.add_axes(self.ax1.get_position(), frameon=False, zorder=1)
        
        #---Precipitation---
    #    ax3 = fig.add_axes(ax1.get_position(), frameon=False, zorder=2)
        self.ax3 = self.ax2.twinx()
        self.ax3.set_zorder(self.ax2.get_zorder()+1)
        self.ax3.set_navigate(False)
        
        #---Air Temperature---
    #    ax4 = fig.add_axes(ax1.get_position(), frameon=False, zorder=3)
        self.ax4 = self.ax2.twinx()
        self.ax4.set_zorder(self.ax3.get_zorder()+1)
        self.ax4.set_navigate(False)
            
        #------------------------------------------------------------- TIME ----            
        
        xticks_position, xticks_labels_position, xticks_labels = \
                    generate_xticks_informations(
                            self.TIMEmin, self.TIMEmax,
                            self.date_labels_display_pattern, 0,
                            labelDB.month_names)
                            
        self.ax1.set_xticks(xticks_position)
        self.ax1.xaxis.set_ticklabels([])
        self.ax1.xaxis.set_ticks_position('bottom')
        self.ax1.tick_params(axis='both',direction='out', gridOn=True)
        
        self.ax1.set_yticks(np.arange(0, self.NZGrid, 1))
        self.ax1.yaxis.set_ticklabels([])
        self.ax1.tick_params(axis='y', length=0)
        self.ax1.patch.set_facecolor('none')
                         
        #====================================================== WATER LEVEL ====
            
        time = WaterLvlObj.time   
        
        if GraphParamObj.WLref == 1:   # masl
        
            water_lvl = WaterLvlObj.ALT - WaterLvlObj.lvl
            
            WLmin = GraphParamObj.WLmin
            WLscale = GraphParamObj.WLscale
            WLmax = WLmin + self.NZGrid * WLscale
            
            yticks_position = np.arange(WLmin,
                                        WLmin + (self.NZGrid - 8) * WLscale,
                                        WLscale * 2)
                                        
        else: # mbgs: Y axis is inverted
        
            water_lvl = WaterLvlObj.lvl
        
            WLmax = GraphParamObj.WLmin
            WLscale = GraphParamObj.WLscale    
            WLmin = WLmax - self.NZGrid * WLscale
            
            yticks_position = np.arange(WLmax, 
                                        WLmax - (self.NZGrid - 8) * WLscale,
                                        WLscale * -2)
        
        self.ax2.axis([self.TIMEmin, self.TIMEmax, WLmin, WLmax])
        
        self.ax2.set_xticks(xticks_position)
        self.ax2.xaxis.set_ticklabels([])
        self.ax2.tick_params(axis='x', length=0, direction='out')
        
        self.ax2.set_yticks(yticks_position)
        self.ax2.yaxis.set_ticks_position('left')
        self.ax2.tick_params(axis='y', direction='out', labelsize=10)            
        if GraphParamObj.WLref != 1:
            self.ax2.invert_yaxis()
        
        #--------------------------------------------------------- PLOTTING ----
        
        #---- Water Levels ----
        
        if GraphParamObj.trend_line == 1:
            tfilt, wlfilt = filt_data(time, water_lvl, 7)
        
            self.ax2.plot(tfilt, wlfilt, '-', zorder = 10, linewidth=1,
                          label='WL Trend Line')
            self.ax2.plot(time, water_lvl, '.', color=[0.65, 0.65, 1.],
                          markersize=5, label='WL Data Point')
        else:
            self.ax2.plot(time, water_lvl, '-', zorder = 10, linewidth=1, 
                          label='Water Level')                
        
        #---- Manual Measures ----
           
        TIMEmes = WaterLvlObj.TIMEmes
        WLmes = WaterLvlObj.WLmes
        
        h_WLmes = self.ax2.plot(TIMEmes, WLmes, 'o', zorder = 15,
                                label='Manual measures')
                                            
        plt.setp(h_WLmes, markerfacecolor='none', markersize=5,
                 markeredgecolor=(1, 0.25, 0.25), markeredgewidth=1.5)
                     
        #---- Recession ----
            
    #    # Plot a Recession line for Dundurn Report
    #    trecess = np.arange(41548, 41760)
    #    hrecess = 0.69 * (trecess - 41548) / 1000. + 6.225
    #
    #    ax2.plot(trecess, hrecess, '--r', zorder = 10, linewidth=1.5,
    #             label='Water Level Recession')
                         
        #--------------------------------------------------------------- LEGEND ----
        
        if GraphParamObj.isLegend == True:
            self.ax2.legend(loc=4, numpoints=1, fontsize=10, ncol=2)    
                         
        #=============================================== PLOT PRECIPITATION ====
            
        time = MeteoObj.TIMEwk
        Tmax = MeteoObj.TMAXwk
        Ptot = MeteoObj.PTOTwk
        Rain = MeteoObj.RAINwk
        self.name_meteo = MeteoObj.station_name
                        
        istart = np.where(time > self.TIMEmin)[0]
        if len(istart) == 0:
            istart = 0
        else:
            istart = istart[0]
            if istart > 0:
                istart -= 1
        
        iend = np.where(time < self.TIMEmax)[0]
        if len(iend) == 0:
            iend = 0
        else:
            iend = iend[-1]
            if iend < len(time):
                iend += 1
        
        time = time[istart:iend]
        Tmax = Tmax[istart:iend]
        Ptot = Ptot[istart:iend]
        Rain = Rain[istart:iend]
        
        RAINmin = 0
        RAINmax = RAINmin + RAINscale * 6
        
        self.ax3.axis([self.TIMEmin, self.TIMEmax, 
                       RAINmin - (RAINscale*4), 
                       RAINmin - (RAINscale*4) + self.NZGrid*RAINscale])    
        yticks_position = np.arange(0, RAINmax + RAINscale, RAINscale)
        
        self.ax3.set_xticks(xticks_position)
        self.ax3.xaxis.set_ticklabels([])
        self.ax3.tick_params(axis='x', length=0, direction='out')    
        
        self.ax3.set_yticks(yticks_position)
        self.ax3.yaxis.set_ticks_position('right')
        self.ax3.tick_params(axis='y', direction='out', labelsize=10)
        self.ax3.invert_yaxis()
        self.ax3.yaxis.set_label_position('right')
        
            
        #------------------------------------------------------- PLOT DATA -----
            
        bar1 = self.ax3.bar(time, Ptot, align='center', width=7-1)
        plt.setp(bar1, color=(0.65,0.65,0.65), edgecolor='none')
        
        bar2 = self.ax3.bar(time, Rain, align='center', width=7-1)
        plt.setp(bar2, color=(0,0,1), edgecolor='none')
        
        self.ax3.plot([self.TIMEmin, self.TIMEmax],[0, 0],'k')
        
        if fname_info:
            Ptot_missing_time, _ = load_weather_log(fname_info,
                                                    'Total Precip (mm)', 
                                                    time, Ptot)
        
            line_missing_Ptot = self.ax3.plot(
                Ptot_missing_time, 
                np.ones(len(Ptot_missing_time)) * -5 * RAINscale / 20., '.')
            plt.setp(line_missing_Ptot, markerfacecolor=(1, 0.25, 0.25),
                     markeredgecolor='none', markersize=5)
    
        #============================================ PLOT AIR TEMPERATURE =====
            
        TEMPmin = -40
        TEMPscale = 20
        TEMPmax = 40
        
        self.ax4.axis([self.TIMEmin, self.TIMEmax, TEMPmax-TEMPscale*self.NZGrid, TEMPmax])    
        yticks_position = np.arange(TEMPmin, TEMPmax + TEMPscale, TEMPscale)
        
        self.ax4.set_xticks(xticks_position)
        self.ax4.xaxis.set_ticklabels([])
        self.ax4.tick_params(axis='x', length=0, direction='out')
        
        self.ax4.set_yticks(yticks_position)
        self.ax4.yaxis.set_ticks_position('left')
        self.ax4.tick_params(axis='y', direction='out', labelsize=10)
        self.ax4.yaxis.set_label_position('left')
        
        TIME2X = np.zeros(len(time)*2)
        Tmax2X = np.zeros(len(time)*2)
        
        n = 3.5
        TIME2X[0:2*len(time)-1:2] = time - n
        TIME2X[1:2*len(time):2] = time + n
        Tmax2X[0:2*len(time)-1:2] = Tmax
        Tmax2X[1:2*len(time):2] = Tmax
            
        #------------------------------------------------------- PLOT DATA -----
            
        self.ax4.fill_between(TIME2X, 0.1, Tmax2X, color='red', alpha=0.25,
                         edgecolor='none')
        self.ax4.plot(TIME2X, Tmax2X, 'k')
        
        if fname_info:
            Temp_missing_time, Temp_missing_value = load_weather_log(
                                   fname_info, 'Max Temp (deg C)',
                                   time, Tmax)
            
            h1_ax4, = self.ax4.plot(Temp_missing_time, 
                              np.ones(len(Temp_missing_time)) * 35, '.')
            plt.setp(h1_ax4, markerfacecolor=(1, 0.25, 0.25),
                     markeredgecolor='none', markersize=5)
                     
        if GraphParamObj.isLegend == True:
    
            rec1 = plt.Rectangle((0, 0), 1, 1, fc=[0.65,0.65,0.65])
            rec2 = plt.Rectangle((0, 0), 1, 1, fc=[0, 0, 1])
            rec3 = plt.Rectangle((0, 0), 1, 1, fc=[1, 0.65, 0.65])
           
            labels = ['Snow', 'Rain', 'Air Temperature', 'Missing Data']
            self.ax4.legend([rec1, rec2, rec3, h1_ax4], labels, loc=[0.01, 0.45],
                       numpoints=1, fontsize=10)
                         
        #----------------------------------------------------- FIGURE TITLE ----
           
        self.dZGrid_inch = (fheight - bottom_margin - top_margin) / self.NZGrid
        if isTitle == 1:
            
            xTitle = (self.TIMEmin + self.TIMEmax) / 2.
            
            ytitle = self.NZGrid + (top_margin / 1.7 / self.dZGrid_inch)
            
            self.ax1.text(xTitle, ytitle, graph_title,
                     fontsize=18 * fheight / 8.5,
                     horizontalalignment='center', 
                     verticalalignment='center')
                     
        #--------------------------------------------- WEATHER STATION TEXT ----
        
        # Calculate horizontal distance between weather station and
        # observation well.

        LAT1 = float(WaterLvlObj.LAT)
        LON1 = float(WaterLvlObj.LON)
        LAT2 = float(MeteoObj.LAT)
        LON2 = float(MeteoObj.LON)
            
        self.dist = LatLong2Dist(LAT1, LON1, LAT2, LON2)
         
        text1_ypos = self.NZGrid + 0.025 / self.dZGrid_inch
       
        self.text1 = self.ax1.text(self.TIMEmax, text1_ypos, '',
                                   rotation=0, verticalalignment='bottom',
                                   horizontalalignment='right', fontsize=10)                 
        
        #---------------------------------------------------- xlabel (Time) ----
        
        self.xlab = []
        for i in range(len(xticks_labels)) : 
            xlab = self.ax1.text(xticks_labels_position[i], -0.15,
                           xticks_labels[i], rotation=45, 
                           verticalalignment='top', horizontalalignment='right',
                           fontsize=10)
                           
            self.xlab.append(xlab)
                
        #------------------------------------------------------ DRAW LABELS ----
                                                 
        self.draw_ylabels(language)
        self.draw_xlabels(language)
        
    def draw_xlabels(self, language):
       
        labelDB = LabelDatabase(language)
        
        _, _, xticks_labels = generate_xticks_informations(
                                            self.TIMEmin, self.TIMEmax,
                                            self.date_labels_display_pattern, 0,
                                            labelDB.month_names)
                                            
        for i in range(len(self.xlab)):
            self.xlab[i].set_text(xticks_labels[i])
    
    def draw_ylabels(self, language):

        labelDB = LabelDatabase(language)
        
        #---------------------------------- YLABELS LEFT (Temp. & Waterlvl) ----
        
        if self.WLref == 0:       
            lab_ax2 = labelDB.mbgs % self.name_well
        elif self.WLref == 1:
            lab_ax2 = labelDB.masl % self.name_well
            
        self.ax2.set_ylabel(lab_ax2,rotation=90,
                            fontsize=self.label_font_size,
                            verticalalignment='top',
                            horizontalalignment='center')
                       
        self.ax4.set_ylabel(labelDB.temperature, rotation=90,
                            fontsize=self.label_font_size,
                            verticalalignment='top',
                            horizontalalignment='center')
                       
        # Get bounding box dimensions of yaxis ticklabels for ax2 and ax4
        renderer = self.fig.canvas.get_renderer()            
        bbox2_left, bbox2_right = self.ax2.yaxis.get_ticklabel_extents(renderer)
        bbox4_left, bbox4_right = self.ax4.yaxis.get_ticklabel_extents(renderer)
        
        # Transform coordinates in ax2 and ax4 coordinate system and
        # calculate the labels positions in x and y.
        bbox2_left = self.ax2.transAxes.inverted().transform(bbox2_left)
        bbox4_left = self.ax4.transAxes.inverted().transform(bbox4_left)
        
        ylabel2_xpos = - (bbox2_left[1, 0] - bbox2_left[0, 0])
        ylabel2_ypos = (bbox2_left[1, 1] + bbox2_left[0, 1]) / 2.
        
        ylabel4_xpos = - (bbox4_left[1, 0] - bbox4_left[0, 0])
        ylabel4_ypos = (bbox4_left[1, 1] + bbox4_left[0, 1]) / 2.
        
        # Take the position which is farthest from the left y axis in order
        # to have both labels on the left aligned.
        ylabel_xpos = min(ylabel2_xpos, ylabel4_xpos)

        self.ax2.yaxis.set_label_coords(ylabel_xpos - 0.04, ylabel2_ypos)
        self.ax4.yaxis.set_label_coords(ylabel_xpos - 0.04, ylabel4_ypos)
        
        #  Old way I was doing it before. Position of the labels were
        #  fixed, indepently of the ticks labels format.
            
        #  ax4.yaxis.set_label_coords(-.07, (NZGrid - 2.) / NZGrid)
            
        
        #------------------------------------ YLABELS RIGHT (Precipitation) ----
            
        self.ax3.set_ylabel(labelDB.precip, rotation=270,
                            fontsize=self.label_font_size,
                            verticalalignment='top',
                            horizontalalignment='center')
                            
        # Get bounding box dimensions of yaxis ticklabels for ax3
        bbox3_left, bbox3_right = self.ax3.yaxis.get_ticklabel_extents(renderer)
        
        # Transform coordinates in ax3 coordinate system and
        # calculate the labels positions in x and y.
        bbox3_right = self.ax3.transAxes.inverted().transform(bbox3_right)
        
        ylabel3_xpos = (bbox3_right[1, 0] - bbox3_right[0, 0])
        ylabel3_ypos = (bbox3_right[1, 1] + bbox3_right[0, 1]) / 2.
        
        # Take the position which is farthest from the left y axis in order
        # to have both labels on the left aligned.

        self.ax3.yaxis.set_label_coords(1 + ylabel3_xpos + 0.04, ylabel3_ypos)
        
        #-------------------------------------------- WEATHER STATION LABEL ----
        
        text_top_margin = labelDB.station_meteo % (self.name_meteo, self.dist)
        
        self.text1.set_text(text_top_margin)
            
#===============================================================================        
def generate_hydrograph(fig, WaterLvlObj, MeteoObj, GraphParamObj):
# This method generate the figure with the parameters that are entered in
# the UI.
#===============================================================================
                    
    fig.clf()
    
    fig.patch.set_facecolor('white')
    
    fheight = fig.get_figheight() # Height of the figure in inches
    fwidth = fig.get_figwidth()   # Width of the figure in inches
   
    name_well = WaterLvlObj.name_well          
            
    fname_info = GraphParamObj.finfo
    
    TIMEmin = GraphParamObj.TIMEmin
    TIMEmax = GraphParamObj.TIMEmax
    
    isTitle = GraphParamObj.title_state # 1 -> title ; 0 -> no title
    graph_title = GraphParamObj.title_text
   
    language = GraphParamObj.language
    labelDB = LabelDatabase(language)
    
    date_labels_display_pattern = 2
    NZGrid = GraphParamObj.ygrid_divnumber            
    RAINscale = GraphParamObj.RAINscale
    
    # Font size is multiplied by a ratio in order to keep the preview
    # and the final saved figure to the same scale. The preview
    # figure's size is modified when the UI is generated and depends
    # on the screen resolution.
    
    label_font_size = 14 * fheight / 8.5
        
    #------------------------------------------------------ FIGURE CREATION ----
    
    #---- MARGINS (Inches) ----
    
    left_margin  = 0.85 
    right_margin = 0.85
    bottom_margin = 0.75  
    if isTitle == 1:
        top_margin = 0.75
    else:
        top_margin = 0.25
    
    #---- MARGINS (% of figure) ----
    
    x0 = left_margin / fwidth
    y0 = bottom_margin / fheight
    w = 1 - (left_margin + right_margin) / fwidth
    h = 1 - (bottom_margin + top_margin) / fheight
        
    #-------------------------------------------------------- AXES CREATION ----        
    
    # http://stackoverflow.com/questions/15303284/
    # multiple-y-scales-but-only-one-enabled-for-pan-and-zoom
    
    # http://matplotlib.1069221.n5.nabble.com/Control-twinx-series-zorder-
    #        ax2-series-behind-ax1-series-or-place-ax2-on-left-ax1-on-right-
    #        td12994.html
    
    #---Time (host)---
    ax1  = fig.add_axes([x0, y0, w, h], zorder=0)
    ax1.axis([TIMEmin, TIMEmax, 0, NZGrid])
    
    #---Water Levels---
    ax2 = fig.add_axes(ax1.get_position(), frameon=False, zorder=1)
    
    #---Precipitation---
#    ax3 = fig.add_axes(ax1.get_position(), frameon=False, zorder=2)
    ax3 = ax2.twinx()
    ax3.set_zorder(ax2.get_zorder()+1)
    ax3.set_navigate(False)
    
    #---Air Temperature---
#    ax4 = fig.add_axes(ax1.get_position(), frameon=False, zorder=3)
    ax4 = ax2.twinx()
    ax4.set_zorder(ax3.get_zorder()+1)
    ax4.set_navigate(False)
        
    #----------------------------------------------------------------- TIME ----            
    
    xticks_position, xticks_labels_position, xticks_labels = \
                generate_xticks_informations(
                        TIMEmin, TIMEmax,date_labels_display_pattern, 0,
                        labelDB.month_names)
                        
    ax1.set_xticks(xticks_position)
    ax1.xaxis.set_ticklabels([])
    ax1.xaxis.set_ticks_position('bottom')
    ax1.tick_params(axis='both',direction='out', gridOn=True)
    
    ax1.set_yticks(np.arange(0, NZGrid, 1))
    ax1.yaxis.set_ticklabels([])
    ax1.tick_params(axis='y', length=0)
    ax1.patch.set_facecolor('none')
                     
    #========================================================== WATER LEVEL ====
        
    time = WaterLvlObj.time   
    
    if GraphParamObj.WLref == 1:   # masl
    
        water_lvl = WaterLvlObj.ALT - WaterLvlObj.lvl
        
        WLmin = GraphParamObj.WLmin
        WLscale = GraphParamObj.WLscale
        WLmax = WLmin + NZGrid * WLscale
        
        yticks_position = np.arange(WLmin,
                                    WLmin + (NZGrid - 8) * WLscale,
                                    WLscale * 2)
                                    
    else: # mbgs: Y axis is inverted
    
        water_lvl = WaterLvlObj.lvl
    
        WLmax = GraphParamObj.WLmin
        WLscale = GraphParamObj.WLscale    
        WLmin = WLmax - NZGrid * WLscale
        
        yticks_position = np.arange(WLmax, 
                                    WLmax - (NZGrid - 8) * WLscale,
                                    WLscale * -2)
    
    ax2.axis([TIMEmin, TIMEmax, WLmin, WLmax])
    
    ax2.set_xticks(xticks_position)
    ax2.xaxis.set_ticklabels([])
    ax2.tick_params(axis='x', length=0, direction='out')
    
    ax2.set_yticks(yticks_position)
    ax2.yaxis.set_ticks_position('left')
    ax2.tick_params(axis='y', direction='out', labelsize=10)            
    if GraphParamObj.WLref != 1:
        ax2.invert_yaxis()
    
    #------------------------------------------------------------- PLOTTING ----
    
    #---- Water Levels ----
    
    if GraphParamObj.trend_line == 1:
        tfilt, wlfilt = filt_data(time, water_lvl, 7)
    
        ax2.plot(tfilt, wlfilt, '-', zorder = 10, linewidth=1,
                 label='WL Trend Line')
        ax2.plot(time, water_lvl, '.', color=[0.65, 0.65, 1.],
                        markersize=5, label='WL Data Point')
    else:
        ax2.plot(time, water_lvl, '-', zorder = 10, linewidth=1, 
                 label='Water Level')                
    
    #---- Manual Measures ----
       
    TIMEmes = WaterLvlObj.TIMEmes
    WLmes = WaterLvlObj.WLmes
    
    h_WLmes = ax2.plot(TIMEmes, WLmes, 'o', zorder = 15,
                       label='Manual measures')
                                        
    plt.setp(h_WLmes, markerfacecolor='none', markersize=5,
             markeredgecolor=(1, 0.25, 0.25), markeredgewidth=1.5)
                 
    #---- Recession ----
        
#    # Plot a Recession line for Dundurn Report
#    trecess = np.arange(41548, 41760)
#    hrecess = 0.69 * (trecess - 41548) / 1000. + 6.225
#
#    ax2.plot(trecess, hrecess, '--r', zorder = 10, linewidth=1.5,
#             label='Water Level Recession')
                     
    #--------------------------------------------------------------- LEGEND ----
    
    if GraphParamObj.isLegend == True:
        ax2.legend(loc=4, numpoints=1, fontsize=10, ncol=2)    
                     
    #=================================================== PLOT PRECIPITATION ====
        
    time = MeteoObj.TIMEwk
    Tmax = MeteoObj.TMAXwk
    Ptot = MeteoObj.PTOTwk
    Rain = MeteoObj.RAINwk
    name_meteo = MeteoObj.station_name
                    
    istart = np.where(time > TIMEmin)[0]
    if len(istart) == 0:
        istart = 0
    else:
        istart = istart[0]
        if istart > 0:
            istart -= 1
    
    iend = np.where(time < TIMEmax)[0]
    if len(iend) == 0:
        iend = 0
    else:
        iend = iend[-1]
        if iend < len(time):
            iend += 1
    
    time = time[istart:iend]
    Tmax = Tmax[istart:iend]
    Ptot = Ptot[istart:iend]
    Rain = Rain[istart:iend]
    
    RAINmin = 0
    RAINmax = RAINmin + RAINscale * 6
    
    ax3.axis([TIMEmin, TIMEmax, 
              RAINmin - (RAINscale*4), 
              RAINmin - (RAINscale*4) + NZGrid*RAINscale])    
    yticks_position = np.arange(0, RAINmax + RAINscale, RAINscale)
    
    ax3.set_xticks(xticks_position)
    ax3.xaxis.set_ticklabels([])
    ax3.tick_params(axis='x', length=0, direction='out')    
    
    ax3.set_yticks(yticks_position)
    ax3.yaxis.set_ticks_position('right')
    ax3.tick_params(axis='y', direction='out', labelsize=10)
    ax3.invert_yaxis()
    ax3.yaxis.set_label_position('right')
    ax3.set_ylabel(labelDB.precip, rotation=270,
                   fontsize=label_font_size, verticalalignment='bottom')
    ax3.yaxis.set_label_coords(1.06, 1.-7./NZGrid) 
        
    #----------------------------------------------------------- PLOT DATA -----
        
    bar1 = ax3.bar(time, Ptot, align='center', width=7-1)
    plt.setp(bar1, color=(0.65,0.65,0.65), edgecolor='none')
    
    bar2 = ax3.bar(time, Rain, align='center', width=7-1)
    plt.setp(bar2, color=(0,0,1), edgecolor='none')
    
    ax3.plot([TIMEmin, TIMEmax],[0, 0],'k')
    
    if fname_info:
        Ptot_missing_time, _ = load_weather_log(fname_info,
                                                'Total Precip (mm)', 
                                                time, Ptot)
    
        line_missing_Ptot = ax3.plot(
            Ptot_missing_time, 
            np.ones(len(Ptot_missing_time)) * -5 * RAINscale / 20., '.')
        plt.setp(line_missing_Ptot, markerfacecolor=(1, 0.25, 0.25),
                 markeredgecolor='none', markersize=5)
    
    # Calculate horizontal distance between weather station and
    # observation well.
    LAT1 = float(WaterLvlObj.LAT)
    LON1 = float(WaterLvlObj.LON)
    LAT2 = float(MeteoObj.LAT)
    LON2 = float(MeteoObj.LON)
        
    dist = round(LatLong2Dist(LAT1, LON1, LAT2, LON2), 1)
     
    text_top_margin_yposition = RAINmin - (RAINscale*4) - 1.5 * RAINscale / 20.  
    text_top_margin = labelDB.station_meteo % (name_meteo,
                                                       str(dist))
        
    ax3.text(TIMEmax, text_top_margin_yposition , text_top_margin,
             rotation=0, verticalalignment='bottom',
             horizontalalignment='right', fontsize=10)

    #================================================ PLOT AIR TEMPERATURE =====
        
    TEMPmin = -40
    TEMPscale = 20
    TEMPmax = 40
    
    ax4.axis([TIMEmin, TIMEmax, TEMPmax-TEMPscale*NZGrid, TEMPmax])    
    yticks_position = np.arange(TEMPmin, TEMPmax + TEMPscale, TEMPscale)
    
    ax4.set_xticks(xticks_position)
    ax4.xaxis.set_ticklabels([])
    ax4.tick_params(axis='x', length=0, direction='out')
    
    ax4.set_yticks(yticks_position)
    ax4.yaxis.set_ticks_position('left')
    ax4.tick_params(axis='y', direction='out', labelsize=10)
    ax4.yaxis.set_label_position('left')
    
    TIME2X = np.zeros(len(time)*2)
    Tmax2X = np.zeros(len(time)*2)
    
    n = 3.5
    TIME2X[0:2*len(time)-1:2] = time - n
    TIME2X[1:2*len(time):2] = time + n
    Tmax2X[0:2*len(time)-1:2] = Tmax
    Tmax2X[1:2*len(time):2] = Tmax
        
    #----------------------------------------------------------- PLOT DATA -----
        
    ax4.fill_between(TIME2X, 0.1, Tmax2X, color='red', alpha=0.25,
                     edgecolor='none')
    ax4.plot(TIME2X, Tmax2X, 'k')
    
    
    if fname_info:
        Temp_missing_time, Temp_missing_value = load_weather_log(
                               fname_info, 'Max Temp (deg C)',
                               time, Tmax)
        
        h1_ax4, = ax4.plot(Temp_missing_time, 
                          np.ones(len(Temp_missing_time)) * 35, '.')
        plt.setp(h1_ax4, markerfacecolor=(1, 0.25, 0.25),
                 markeredgecolor='none', markersize=5)
                 
    if GraphParamObj.isLegend == True:

        rec1 = plt.Rectangle((0, 0), 1, 1, fc=[0.65,0.65,0.65])
        rec2 = plt.Rectangle((0, 0), 1, 1, fc=[0, 0, 1])
        rec3 = plt.Rectangle((0, 0), 1, 1, fc=[1, 0.65, 0.65])
       
        labels = ['Snow', 'Rain', 'Air Temperature', 'Missing Data']
        ax4.legend([rec1, rec2, rec3, h1_ax4], labels, loc=[0.01, 0.45],
                   numpoints=1, fontsize=10)
                     
    #-------------------------------------------------------- FIGURE TITLE -----
        
    if isTitle == 1:
        
        xTitle = (TIMEmin + TIMEmax) / 2.

        dZGrid_inch = (fheight - bottom_margin - top_margin) / NZGrid
        
        print dZGrid_inch
        ytitle = NZGrid + (top_margin / 1.7 / dZGrid_inch)
        
        ax1.text(xTitle, ytitle, graph_title,
                 fontsize=18 * fheight / 8.5,
                 horizontalalignment='center', 
                 verticalalignment='center')
                     
    #------------------------------------------------------- xlabel (Time) -----
        
    i = 0
    for xlabel in xticks_labels : 
        ax1.text(xticks_labels_position[i], -0.15, xlabel, rotation=45, 
                 verticalalignment='top', horizontalalignment='right',
                 fontsize=10)
        i += 1
            
    #------------------------------------------------------------- ylabels -----
    
    if GraphParamObj.WLref == 0:       
        lab_ax2 = labelDB.mbgs % name_well
    elif GraphParamObj.WLref == 1:
        lab_ax2 = labelDB.masl % name_well
        
    ax2.set_ylabel(lab_ax2,rotation=90,
                   fontsize=label_font_size, verticalalignment='top',
                   horizontalalignment='center')
                   
    ax4.set_ylabel(labelDB.temperature, rotation=90,
                   fontsize=label_font_size, verticalalignment='top',
                   horizontalalignment='center')
                   
    # Get bounding box dimensions of yaxis ticklabels for ax2 and ax4
    renderer = fig.canvas.get_renderer()            
    bbox2_left, bbox2_right = ax2.yaxis.get_ticklabel_extents(renderer)
    bbox4_left, bbox4_right = ax4.yaxis.get_ticklabel_extents(renderer)
    
    # Transform coordinates in ax2 and ax4 coordinate system and
    # calculate the labels positions in x and y.
    bbox2_left = ax2.transAxes.inverted().transform(bbox2_left)
    bbox4_left = ax4.transAxes.inverted().transform(bbox4_left)
    
    ylabel2_xpos = - (bbox2_left[1, 0] - bbox2_left[0, 0])
    ylabel2_ypos = (bbox2_left[1, 1] + bbox2_left[0, 1]) / 2.
    
    ylabel4_xpos = - (bbox4_left[1, 0] - bbox4_left[0, 0])
    ylabel4_ypos = (bbox4_left[1, 1] + bbox4_left[0, 1]) / 2.
    
    # Take the position which is farthest from the left y axis in order
    # to have both labels on the left aligned.
    ylabel_xpos = min(ylabel2_xpos, ylabel4_xpos)
    
    ax2.yaxis.set_label_coords(ylabel_xpos - 0.04, ylabel2_ypos)
    ax4.yaxis.set_label_coords(ylabel_xpos - 0.04, ylabel4_ypos)

#            Old way I was doing it before. Position of the labels were
#            fixed, indepently of the ticks labels format.
        
#            ax4.yaxis.set_label_coords(-.07, (NZGrid - 2.) / NZGrid)

#===============================================================================
def generate_xticks_informations(TIMEmin, TIMEmax, n, datemode, month_names):
#===============================================================================

    i = 0
               
    xticks_labels = np.array([])  
    xticks_position = np.array([TIMEmin])
    xticks_labels_position = np.array([])
    
    xticks_labels_offset = 0.012 * (TIMEmax - TIMEmin + 1)    
    
    while xticks_position[i] < TIMEmax:
        year = xldate_as_tuple(xticks_position[i], datemode)[0]
        month = xldate_as_tuple(xticks_position[i], datemode)[1]
        
        month_range = monthrange(year, month)[1]    
        
        xticks_position = np.append(xticks_position, 
                                    xticks_position[i] + month_range )
        xticks_labels_position = np.append(xticks_labels_position, 
                  xticks_position[i] + 0.5 * month_range + xticks_labels_offset)
        if i % n == 0:    
            xticks_labels = np.append(
                                 xticks_labels, 
                                 month_names[month - 1] + " '" + str(year)[-2:])
        else:
            xticks_labels = np.append(xticks_labels, " ")
        i += 1
        
    return xticks_position, xticks_labels_position, xticks_labels

#===============================================================================
class GraphParameters():
# This class contains the saved graph layout for a well. It also
# contains methods to load and save a new graph layout from the
# config file <graph_layout.lst>.
#===============================================================================
      
    def __init__(self, parent=None):

        self.fmeteo = []
        self.finfo = []      
        self.WLmin = 0
        self.WLscale = 0
        self.TIMEmin = 36526
        self.TIMEmax = 36526
        self.ygrid_divnumber = 20 #Dundurn: 17 #26
        
        self.fheight = 8.5 # Figure height in inches
        self.fwidth = 11.0 # Figure width in inches
        
        self.title_state = 0
        self.title_text = 'Add A Title To The Figure Here'
        self.language = 'English'
        
        self.RAINscale = 20 # Dundurn: 10
        self.WLref = 0 # 0: mbgs 1: masl
        self.trend_line = 0
        
        self.isLegend = False
        
        self.header = [['Name Well', 'Station Meteo', 'Min. Waterlvl',
                        'Waterlvl Scale', 'Date Start', 'Date End',
                        'Fig. Title State', 'Fig. Title Text', 'Precip. Scale',
                        'Waterlvl Ref.', 'Trend Line']]
        
    def checkConfig(self, name_well): # old var. names: check, isConfigExist
        
        # Check first if a layout file is present in the folder.
        # If not, initiate the creation of a new one.
        if not path.exists('graph_layout.lst'):
            self.create_new_config_file()
                
        reader = open('graph_layout.lst', 'rb')
        reader = csv.reader(reader, delimiter='\t')
        reader = list(reader)
        reader = np.array(reader)
       
        # Check if config file is from an old version of Hydroprint
        # and if yes, convert it to the new version.
        nCONFG, nPARA = np.shape(reader)

        if nPARA < len(self.header[0]):
            
            nMissing = len(self.header[0]) - nPARA
            
            col2add = np.zeros((nCONFG, nMissing)).astype(int)
            col2add = col2add.astype(str)
            
            reader = np.hstack((reader, col2add))
            reader[0] = self.header[0]
            
            if nPARA < 8:
                reader[1:, 7] = 'Add A Title To The Figure Here'
            if nPARA < 9:
                reader[1:, 8] = 20
            if nPARA < 10:
                reader[1:, 9] = 0
            if nPARA < 11:
                reader[1:, 10] = 0
            
            with open('graph_layout.lst', 'wb') as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerows(reader)
             
            msg = ('The "graph_layout.lst" file is from an older version ' +
                   'of WHAT. The old file has been converted to the newer ' +
                   'version.') 
            print msg
        
        # Check if there is a layout stored for the current 
        # selected observation well.
        row = np.where(reader[:,0] == name_well)[0]
           
        if len(row) > 0:
            layoutExist = True
        else:
            layoutExist = False
           
        return layoutExist
        
    def create_new_config_file(self):

        print 'No "graph_layout.lst" file found. A new one has been created.'

        with open('graph_layout.lst', 'wb') as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerows(self.header)
        
    def load(self, name_well):
        # A <checkConfig> is supposed to have been carried before this method
        # is called. So it can be supposed at this point that everything is
        # fine with the graph layout for this well.
            
        reader = open('graph_layout.lst', 'rb')
        reader = csv.reader(reader, delimiter='\t')
        reader = list(reader)
        reader = np.array(reader)
     
        row = np.where(reader[:,0] == name_well)[0]
        
        reader = reader[row][0]
        
        self.fmeteo = reader[1]
        self.finfo = self.fmeteo[:-3] + 'log'
                          
        self.WLmin = reader[2].astype(float)
        self.WLscale = reader[3].astype(float)
            
        self.TIMEmin = reader[4].astype(float)
        self.TIMEmax = reader[5].astype(float)
        
        self.title_state = reader[6].astype(float)
        if self.title_state != 0:
            self.title_state = 1
        
        self.title_text = reader[7].astype(str)
        self.RAINscale = reader[8].astype(float)
        self.WLref = reader[9].astype(int)
        self.trend_line = reader[10].astype(int)
        
    def save(self, name_well):
            
        reader = open('graph_layout.lst', 'rb')
        reader = csv.reader(reader, delimiter='\t')
        reader = list(reader)
        reader = np.array(reader)
         
        rowx = np.where(reader[:,0] == name_well)[0]
        
        new = [name_well, self.fmeteo, self.WLmin, self.WLscale, 
               self.TIMEmin, self.TIMEmax,self.title_state, self.title_text,
               self.RAINscale, self.WLref, self.trend_line]
               
        if len(rowx) == 0:
            reader = np.vstack((reader, new))
        else:
            reader = np.delete(reader, rowx, 0)
            reader = np.vstack((reader, new))
        reader[0] = self.header[0]
            
        with open('graph_layout.lst', 'wb') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(reader)
            
    def best_fit_waterlvl(self, WL):

        WL = WL[~np.isnan(WL)]
        dWL = np.max(WL) - np.min(WL)
        ygrid = self.ygrid_divnumber - 10
        
        #----- WL Scale -----
        
        SCALE = np.hstack((np.arange(0.05, 0.30, 0.05), 
                           np.arange(0.3, 5.1, 0.1)))
        dSCALE = np.abs(SCALE - dWL / ygrid)
        indx = np.where(dSCALE == np.min(dSCALE))[0][0]
        
        self.WLscale = SCALE[indx]
        
        #-----WL Min Value-----
        
        if self.WLref == 0:
            N = np.ceil(np.max(WL) / self.WLscale)
        elif self.WLref == 1:
            N = np.floor(np.min(WL) / self.WLscale)
        
        self.WLmin = self.WLscale * N
        
        return self.WLscale, self.WLmin
    
    def best_fit_time(self, TIME):
        
        # ----- Data Start -----
        
        date0 = xldate_as_tuple(TIME[0], 0)
        date0 = (date0[0], date0[1], 1)
        
        self.TIMEmin = xldate_from_date_tuple(date0, 0)
        
        # ----- Date End -----
        
        date1 = xldate_as_tuple(TIME[-1], 0)
        
        year =  date1[0]
        month = date1[1] + 1
        if month > 12:
            month = 1
            year += 1
        
        date1 = (year, month, 1)
        
        self.TIMEmax = xldate_from_date_tuple(date1, 0)
        
        return date0, date1
        
#===============================================================================             
class WaterlvlData():
#===============================================================================

    def __init__(self):
        
        self.time = []
        self.lvl = []
        self.name_well = []
        self.well_info = []
        
        self.WLmes = []
        self.TIMEmes = []
        
        self.LAT = []
        self.LON = []
        self.ALT = []
        
    def load(self, fname):
        
        reader = open_workbook(fname)
            
        self.time = reader.sheet_by_index(0).col_values(0, start_rowx=11,
                                                           end_rowx=None) 
        self.time = np.array(self.time)
        
        self.lvl = reader.sheet_by_index(0).col_values(1, start_rowx=11, 
                                                          end_rowx=None) 
        self.lvl = np.array(self.lvl).astype('float')
        
        header = reader.sheet_by_index(0).col_values(1, start_rowx=0, 
                                                        end_rowx=5)
        self.name_well = header[0]
        self.LAT = header[1]
        self.LON = header[2]
        self.ALT = header[3]

    #----------------------------------------------------------- WELL INFO ----- 
        
        FIELDS = ['Well Name', 'Latitude', 'Longitude', 'Altitude',
                  'Municipality']
                  
        well_info = '''
                    <table border="0" cellpadding="2" cellspacing="0" 
                    align="left">
                    '''
        
        for i in range(len(FIELDS)):
            
             try:                 
                 VAL = '%0.2f' % float(header[i])
             except:
                 VAL = header[i]
                 
             well_info += '''
                          <tr>
                            <td width=10></td>
                            <td align="left">%s</td>
                            <td align="left" width=20>:</td>
                            <td align="left">%s</td>
                          </tr>
                          ''' % (FIELDS[i], VAL)
        well_info += '</table>'
        
        self.well_info = well_info
        
    def load_waterlvl_measures(self, fname, name_well):
        print name_well
        
        WLmes = []
        TIMEmes = []
            
        if path.exists(fname):
            
            #---- Import Data ----
            
            reader = open_workbook(fname)
            
            NAME = reader.sheet_by_index(0).col_values(0, start_rowx=1,
                                                       end_rowx=None)
                                                                   
            TIME = reader.sheet_by_index(0).col_values(1, start_rowx=1,
                                                       end_rowx=None)
            
            OBS = reader.sheet_by_index(0).col_values(2, start_rowx=1,
                                                      end_rowx=None)
            #---- Convert to Numpy ----
                                                      
            NAME = np.array(NAME).astype('str')
            TIME = np.array(TIME).astype('float')
            OBS = np.array(OBS).astype('float')
                       
            if len(NAME) > 1:
                rowx = np.where(NAME == name_well)[0]
            
                if len(rowx) > 0:
                    WLmes = OBS[rowx]
                    TIMEmes = TIME[rowx]
            
        self.TIMEmes = TIMEmes
        self.WLmes = WLmes
                
        return TIMEmes, WLmes
        
#===============================================================================      
def load_weather_log(fname, variable_name, time_week, value_week):
#===============================================================================

    reader = open(fname, 'rb')
    reader = csv.reader(reader, delimiter='\t')
    reader = list(reader)[36:]
    
    variable = np.zeros(len(reader)).astype('str') 
    time = np.zeros(len(reader))
    for i in range(len(reader)):
        variable[i] = reader[i][0]
        year = int(float(reader[i][1]))
        month = int(float(reader[i][2]))
        day = int(float(reader[i][3]))
        time[i] = xldate_from_date_tuple((year, month, day), 0)
    
    time = time[np.where(variable == variable_name)[0]]
    
    time2 = np.array([])
    missing_value = np.array([])
    for i in time:
        if i >= time_week[0] and i <= time_week[-1]+7:
            search = np.abs(time_week - i)
            hit = np.where(search == min(search))[0]
            time2 = np.append(time2, time_week[hit])
            missing_value = np.append(missing_value, value_week[hit])
    time2, indices = np.unique(time2, return_index=True)
    missing_value = missing_value[indices]
    
    return time2, missing_value
    
#===============================================================================    
def filt_data(time, waterlvl, period):
    """
    period is in days
    """
#===============================================================================
    
    #------------- RESAMPLING 6H BASIS AND NAN ESTIMATION BY INTERPOLATION -----
    
    time6h_0 = np.floor(time[0]) + 1/24
    time6h_end = np.floor(time[-1]) + 1/24
    
    time6h = np.arange(time6h_0, time6h_end + 6/24., 6/24.)     

    # Remove times with nan values    
    index_nonan = np.where(~np.isnan(waterlvl))[0]
    
    # Resample data and interpolate missing values
    waterlvl = np.interp(time6h, time[index_nonan], waterlvl[index_nonan])
    
    #----------------------------------------------------------- FILT DATA -----
#    cuttoff_freq = 1. / period
#    samp_rate = 1. / (time[1] - time[0])
#    Wn = cuttoff_freq / (samp_rate / 2)
#    N = 3
#    
#    (b, a) = signal.butter(N, Wn, btype='low')
#    wlfilt = signal.lfilter(b, a, waterlvl)
    
    win = 4 * period
    
    wlfilt = np.zeros(len(waterlvl) - win)
    tfilt = time6h[win/2:-win/2]
    
    # Centered Moving Average Window        
    for i in range(len(wlfilt)):
        wlfilt[i] = np.mean(waterlvl[i:i+win+1])
    
    return tfilt, wlfilt

#===============================================================================
def LatLong2Dist(LAT1, LON1, LAT2, LON2):
    """
    Computes the horizontal distance in km between 2 points from geographic 
    coordinates given in decimal degrees.
 
    ---- INPUT ----
    
    LAT1 = latitute coordinate of first point
    LON1 = longitude coordinate of first point
    LAT2 = latitude coordinate of second point
    LON2 = longitude coordinate of second point
    
    ---- OUTPUT ----
    
    DIST = horizontal distance between the two points in km

    ---- SOURCE ----
    
    www.stackoverflow.com/questions/19412462 (last accessed on 17/01/2014)
    """
#===============================================================================    
  
    R = 6373.0 # R = Earth radius in km

    # Convert decimal degrees to radians.
    LAT1 = radians(LAT1)
    LON1 = radians(LON1)
    LAT2 = radians(LAT2)
    LON2 = radians(LON2)
    
    # Compute the horizontal distance between the two points in km.
    dLON = LON2 - LON1
    dLAT = LAT2 - LAT1
    a = (sin(dLAT/2))**2 + cos(LAT1) * cos(LAT2) * (sin(dLON/2))**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))    
    
    DIST = R * c 
    
    return DIST
    
if __name__ == '__main__':
    
    from meteo import MeteoObj
    
    plt.close('all')
    
    fmeteo = 'Files4testing/AUTEUIL_2000-2013.out'
    fwaterlvl = 'Files4testing/PO16A.xls'
    
    import os
    import datetime
    import time
    
    t = os.path.getmtime(fmeteo)
    t = time.gmtime(t)
    
    print t[:3]
    
    waterLvlObj = WaterlvlData()
    waterLvlObj.load(fwaterlvl)
    
    fname = 'Files4testing/waterlvl_manual_measurements.xls'
    waterLvlObj.load_waterlvl_measures(fname, 'PO16A')
    
    meteoObj = MeteoObj()
    meteoObj.load(fmeteo)
    
    graphParamObj = GraphParameters()
    if graphParamObj.WLref == 0:
        WL = waterLvlObj.lvl
    elif graphParamObj.WLref == 1:
        WL = waterLvlObj.ALT - waterLvlObj.lvl
    
    graphParamObj.title_state = 1 # 1 -> title ; 0 -> no title
    graphParamObj.title_text = "Title of the Graph"
    
    _, _ = graphParamObj.best_fit_waterlvl(WL)
    _, _ = graphParamObj.best_fit_time(waterLvlObj.time)
    graphParamObj.finfo = 'Files4testing/AUTEUIL_2000-2013.log'
    
#    fig = plt.figure(figsize=(11, 8.5))
#    fig.set_size_inches(11, 8.5)
#    generate_hydrograph(fig, waterLvlObj, meteoObj, graphParamObj)
    
    hydrograph2display = Hydrograph()
    hydrograph2display.generare_hydrograph(waterLvlObj, meteoObj, graphParamObj)
    