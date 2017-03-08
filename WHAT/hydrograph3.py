# -*- coding: utf-8 -*-
"""
Copyright 2014-2016 Jean-Sebastien Gosselin
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

from __future__ import division, unicode_literals

# STANDARD LIBRARY IMPORTS :

from calendar import monthrange
import csv
import os
from math import sin, cos, sqrt, atan2, radians
from time import clock

# THIRD PARTY IMPORTS :

import h5py
import numpy as np
import matplotlib as mpl
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.pyplot as plt
from PySide import QtGui

from xlrd.xldate import xldate_from_date_tuple
from xlrd import xldate_as_tuple

# PERSONAL IMPORTS :

import database as db
from waterlvldata import WaterlvlData
import meteo
from colors import Colors

mpl.use('Qt4Agg')
mpl.rcParams['backend.qt4'] = 'PySide'


# =============================================================================


class LabelDatabase():

    def __init__(self, language):  # ------------------------------- English --

        self.temperature = u'Temperature (°C)'
        self.mbgs = 'Water Level (mbgs)'
        self.masl = 'Water Level (masl)'
        self.precip = 'Precipitation (%s)'
        self.precip_units = ['mm/day', 'mm/week', 'mm/month', 'mm/year']
        self.title = 'Well %s'
        self.station_meteo = ('Weather Station %s\n' +
                              '(located %0.1f km from the well)')
        self.month_names = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                            "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

        self.legend = ['Snow', 'Rain', 'Air temperature', 'Missing data',
                       'Water level (trend)', 'Water level',
                       'Water level (data)', 'Manual measures',
                       'Estimated recession']

        if language.lower() == 'french':  # ------------------------- French --

            self.mbgs = "Niveau d'eau (m sous la surface)"
            self.masl = "Niveau d'eau (masl)"
            self.precip = 'Précipitations (%s)'
            self.precip_units = ['mm/jour', 'mm/sem.', 'mm/mois', 'mm/an']
            self.temperature = 'Température (°C)'
            self.title = 'Puits %s'
            self.station_meteo = ('Station météo %s\n' +
                                  '(située à %0.1f km du puits)')
            self.month_names = ["JAN", "FÉV", "MAR", "AVR", "MAI", "JUN",
                                "JUL", "AOÛ", "SEP", "OCT", "NOV", "DÉC"]

            self.legend = ['Neige', 'Pluie', "Température de l'air",
                           'Données manquantes',
                           "Niveau d'eau (tendance)", "Niveaux d'eau observés",
                           "Niveau d'eau (données)", 'Mesures manuelles',
                           'Récession simulée']


###############################################################################


class HydrographBase(mpl.figure.Figure):                     # HydrographBase #

    def __init__(self, *args, **kargs):
        super(HydrographBase, self).__init__(*args, **kargs)

        # set canvas and renderer :

        self.set_canvas(FigureCanvas(self))
        self.canvas.get_renderer()

        self.__meteo_on = True
        self.__language = 'english'

    @property
    def meteo_on(self):
        return self.__meteo_on

    @meteo_on.setter
    def meteo_on(self, x):
        if type(x) is bool:
            self.__meteo_on = x
        else:
            print('WARNING: "meteo_on" must be either True or False. '
                  'Previous value of "meteo_on" is kept.')

    @property
    def language(self):
        return self.__language

    @language.setter
    def language(self, x):
        if x.lower() in ['english', 'french']:
            self.__language = x
        else:
            print('WARNING: Language not supported. '
                  'Setting language to "english".')
            self.__language = 'english'


###############################################################################


class Hydrograph(HydrographBase):                             # Hydrograph #

    def __init__(self, *args, **kargs):
        super(Hydrograph, self).__init__(*args, **kargs)

        self.__isHydrographExists = False

        # Fig Init :

        self.fwidth = 11.0
        self.fheight = 8.5
        self.patch.set_facecolor('white')
        self.NZGrid = 8  # Number of interval in the grid of the bottom part

        # Vertical height ratio between the top part  and the bottom part
        self.va_ratio = 0.18

        # Graph labels language :
        self.language = 'english'

        # Database :

        self.header = db.FileHeaders().graph_layout
        self.colorsDB = Colors()
        self.colorsDB.load_colors_db()

        # Scales :

        self.WLmin = 0
        self.WLscale = 0

        self.RAINscale = 20

        self.TIMEmin = 36526
        self.TIMEmax = 36526

        # Legend  and Title :

        self.isLegend = 1
        self.isGraphTitle = 1

        # Layout Options :

        self.WLdatum = 0  # 0: mbgs;  1: masl
        self.trend_line = 0
        self.meteo_on = True  # controls wether meteo data are plotted or not
        self.gridLines = 2  # 0 -> None, 1 -> "-" 2 -> ":"
        self.datemode = 'Month'  # 'month' or 'year'
        self.label_font_size = 14
        self.date_labels_display_pattern = 2

        # plot or not the estimated recession segment that
        # were used to estimate the MRC
        self.isMRC = False
        self.isGLUE = False

        # Waterlvl & Meteo Obj :

        self.WaterLvlObj = WaterlvlData()
        self.meteo_obj = meteo.MeteoObj()

        # Daily Weather :

        self.fmeteo = []  # path to the weather data file (.out)
        self.finfo = []  # path the the .log file associated with the .out file

        self.TIMEmeteo = np.array([])
        self.TMAX = np.array([])
        self.PTOT = np.array([])
        self.RAIN = np.array([])

        # Bin Redistributed Weather :

        self.bTIME = np.array([])
        self.bTMAX = np.array([])
        self.bPTOT = np.array([])
        self.bRAIN = np.array([])

        self.bwidth_indx = 1
        #   0: 1 day;
        #   1: 1 week;
        #   2: 1 month;
        #   3: 1 year;

        self.NMissPtot = []

    @property
    def isHydrographExists(self):
        return self.__isHydrographExists

    def set_waterLvlObj(self, WaterLvlObj):  # ================================
        self.WaterLvlObj = WaterLvlObj

    def set_MeteoObj(self, meteo_obj):  # =====================================
        self.meteo_obj = meteo_obj

    def generate_hydrograph(self, meteo_obj=None, WaterLvlObj=None):  # =======

        if meteo_obj:
            self.meteo_obj = meteo_obj
        else:
            meteo_obj = self.meteo_obj

        if WaterLvlObj:
            self.WaterLvlObj = WaterLvlObj
        else:
            WaterLvlObj = self.WaterLvlObj

        # --- Reinit Figure --- #

        self.clf()

        fheight = self.fheight  # Figure height in inches
        fwidth = self.fwidth  # Figure width in inches

        self.set_size_inches(fwidth, fheight, forward=True)

        # Update Variables :

        WaterLvlObj = self.WaterLvlObj

        # Assign Weather Data :

        self.name_meteo = meteo_obj.STA

        DATA = meteo_obj.DATA
        # DATA = [YEAR, MONTH, DAY, TMAX, TMIN, TMEAN, PTOT, ETP, RAIN]

        self.TIMEmeteo = meteo_obj.TIME  # Time in numeric format (days)
        self.TMAX = DATA[:, 3]  # Daily maximum temperature (deg C)
        self.PTOT = DATA[:, 6]  # Daily total precipitation (mm)
        self.RAIN = DATA[:, -1]

        # --- Resample Data in Bins --- #

        self.resample_bin()

        # -------------------------------------------------- AXES CREATION ----

        # http://stackoverflow.com/questions/15303284/
        # multiple-y-scales-but-only-one-enabled-for-pan-and-zoom

        # http://matplotlib.1069221.n5.nabble.com/Control-twinx-series-zorder-
        # ax2-series-behind-ax1-series-or-place-ax2-on-left-ax1
        # -on-right-td12994.html

        # --- Time (host) --- #

        # Also holds the gridlines.

        self.ax1 = self.add_axes([0, 0, 1, 1], frameon=False)
        self.ax1.set_zorder(100)

        # --- Frame --- #

        # Only used to display the frame so it is always on top.

        self.ax0 = self.add_axes(self.ax1.get_position(), frameon=True)
        self.ax0.patch.set_visible(False)
        self.ax0.set_zorder(self.ax1.get_zorder() + 200)
        self.ax0.tick_params(bottom='off', top='off', left='off', right='off',
                             labelbottom='off', labelleft='off')

        # --- Water Levels --- #

        self.ax2 = self.ax1.twinx()
        self.ax2.set_zorder(self.ax1.get_zorder() + 100)
        self.ax2.yaxis.set_ticks_position('left')
        self.ax2.yaxis.set_label_position('left')
        self.ax2.tick_params(axis='y', direction='out', labelsize=10)

        # --- Precipitation --- #

        self.ax3 = self.ax1.twinx()
        self.ax3.set_zorder(self.ax1.get_zorder() + 150)
        self.ax3.set_navigate(False)

        # --- Air Temperature --- #

        self.ax4 = self.ax1.twinx()
        self.ax4.set_zorder(self.ax1.get_zorder() + 150)
        self.ax4.set_navigate(False)
        self.ax4.set_axisbelow(True)

        if self.meteo_on is False:
            self.ax3.set_visible(False)
            self.ax4.set_visible(False)

        # --- Bottom Graph Grid --- #

        self.axLow = self.ax1.twinx()
        self.axLow.patch.set_visible(False)
        self.axLow.set_zorder(self.ax2.get_zorder() - 50)
        self.axLow.tick_params(bottom='off', top='off', left='off',
                               right='off', labelbottom='off', labelleft='off')

        self.update_waterlvl_scale()

        # ---------------------------------------------------- Remove Spines --

        for axe in self.axes[2:]:
            for loc in axe.spines:
                axe.spines[loc].set_visible(False)

        # --------------------------------------------------- Update margins --

        self.bottom_margin = 0.75
        self.set_margins()  # set margins for all the axes

        # ----------------------------------------------------- FIGURE TITLE --

        # ---- Weather Station ----

        # Calculate horizontal distance between weather station and
        # observation well.

        LAT1 = float(WaterLvlObj.LAT)
        LON1 = float(WaterLvlObj.LON)
        LAT2 = float(meteo_obj.LAT)
        LON2 = float(meteo_obj.LON)

        self.dist = LatLong2Dist(LAT1, LON1, LAT2, LON2)

        # display text on figure

        offset = mpl.transforms.ScaledTranslation(0., 7/72.,
                                                  self.dpi_scale_trans)
        transform = self.ax0.transAxes + offset

        self.text1 = self.ax0.text(0, 1, '',
                                   rotation=0, verticalalignment='bottom',
                                   horizontalalignment='left', fontsize=10,
                                   transform=transform)

        # ---- Well Name ----

        offset = mpl.transforms.ScaledTranslation(0., 30/72.,
                                                  self.dpi_scale_trans)
        transform = self.ax0.transAxes + offset

        self.figTitle = self.ax0.text(0, 1, '', fontsize=18,
                                      ha='left', va='bottom',
                                      transform=transform)

        self.draw_figure_title()

        # ------------------------------------------------------------- TIME --

        self.xlabels = []  # Initiate variable
        self.set_time_scale()

        self.ax1.xaxis.set_ticklabels([])
        self.ax1.xaxis.set_ticks_position('bottom')
        self.ax1.tick_params(axis='x', direction='out')
        self.ax1.patch.set_facecolor('none')
        self.ax1.tick_params(top='off', left='off', right='off',
                             labeltop='off', labelleft='off', labelright='off')

        self.set_gridLines()

        # ------------------------------------------------------ WATER LEVEL --

        # --- Continuous Line Datalogger --- #

#        self.l1_ax2, = self.ax2.plot([], [], '.', zorder=10, linewidth=1,
#                                     color='blue', ms=3)

        self.l1_ax2, = self.ax2.plot([], [], '-', zorder=10, linewidth=1,
                                     color=self.colorsDB.rgb[3])

        # --- Data Point Datalogger --- #

        self.l2_ax2, = self.ax2.plot([], [], '.',
                                     color=self.colorsDB.rgb[4],
                                     markersize=5)

        # --- Manual Mesures --- #

        self.h_WLmes, = self.ax2.plot([], [], 'o', zorder=15,
                                      label='Manual measures')

        plt.setp(self.h_WLmes, markerfacecolor='none', markersize=5,
                 markeredgecolor=self.colorsDB.rgb[5], markeredgewidth=1.5)

        # --- Predicted Recession Curves --- #

        self.plot_recess, = self.ax2.plot([], [], color='red', lw=1.5,
                                          dashes=[5, 3], zorder=100,
                                          alpha=0.85)

        self.draw_waterlvl()

        # ---------------------------------------------------------- WEATHER --

        # ---- PRECIPITATION ----

        self.ax3.yaxis.set_ticks_position('right')
        self.ax3.yaxis.set_label_position('right')
        self.ax3.tick_params(axis='y', direction='out', labelsize=10)

        self.PTOT_bar, = self.ax3.plot([], [])
        self.RAIN_bar, = self.ax3.plot([], [])
        self.baseline, = self.ax3.plot([self.TIMEmin, self.TIMEmax],
                                       [0, 0], 'k')

        # ---- AIR TEMPERATURE ----

        TEMPmin = -40
        TEMPscale = 20
        TEMPmax = 40

        self.ax4.axis(ymin=TEMPmin, ymax=TEMPmax)

        yticks_position = np.array([TEMPmin, 0, TEMPmax])
        yticks_position = np.arange(TEMPmin, TEMPmax + TEMPscale/2,
                                    TEMPscale)
        self.ax4.set_yticks(yticks_position)
        self.ax4.yaxis.set_ticks_position('left')
        self.ax4.tick_params(axis='y', direction='out', labelsize=10)
        self.ax4.yaxis.set_label_position('left')

        self.ax4.set_yticks([-20, 20], minor=True)
        self.ax4.tick_params(axis='y', which='minor', length=0)
        self.ax4.xaxis.set_ticklabels([], minor=True)

        self.l1_ax4, = self.ax4.plot([], [])                 # fill shape
        self.l2_ax4, = self.ax4.plot([], [], color='black')  # contour line

        # ---- MISSING VALUES MARKERS ----

        if self.finfo:

            # ---- Precipitation (v2) ----

            # vertical shift of 3 points upward
            vshift = 5/72.
            offset = mpl.transforms.ScaledTranslation(0., vshift,
                                                      self.dpi_scale_trans)
            transform = self.ax4.transData + offset

            t = load_weather_log(self.finfo, 'Total Precip (mm)')
            y = np.ones(len(t)) * self.ax4.get_ylim()[0]
            self.ax4.plot(t, y, ls='-', solid_capstyle='projecting',
                          lw=1., c='red', transform=transform)

            # ---- Air Temperature (v2) ----

            # vertical shift of 3 points downward
            offset = mpl.transforms.ScaledTranslation(0., -vshift,
                                                      self.dpi_scale_trans)
            transform = self.ax4.transData + offset

            t = load_weather_log(self.finfo, 'Max Temp (deg C)')
            y = np.ones(len(t)) * self.ax4.get_ylim()[1]
            self.ax4.plot(t, y, ls='-', solid_capstyle='projecting',
                          lw=1., c='red', transform=transform)

        self.draw_weather()

        # ----------------------------------------------------- DRAW YLABELS --

        self.draw_ylabels()

        # ----------------------------------------------------------- LEGEND --

        self.set_legend()

        # ------------------------------------------------------ UPDATE FLAG --

        self.__isHydrographExists = True

    def set_legend(self):  # ==================================================

        if self.isLegend == 1:

            # ---- Entry ------------------------------------------------------

            labelDB = LabelDatabase(self.language).legend

            lg_handles = []
            lg_labels = []

            if self.meteo_on:

                # ---- Snow ---- #

                rec1 = plt.Rectangle((0, 0), 1, 1, fc=self.colorsDB.rgb[2],
                                     ec=self.colorsDB.rgb[2])

                lg_handles.append(rec1)
                lg_labels.append(labelDB[0])
                # Rain

                rec2 = plt.Rectangle((0, 0), 1, 1, fc=self.colorsDB.rgb[1],
                                     ec=self.colorsDB.rgb[1])

                lg_handles.append(rec2)
                lg_labels.append(labelDB[1])

                # ---- Air Temperature ---- #

                rec3 = plt.Rectangle((0, 0), 1, 1, fc=self.colorsDB.rgb[0],
                                     ec='black')

                lg_handles.append(rec3)
                lg_labels.append(labelDB[2])

                # ---- Missing Data Markers ---- #

                lin1, = plt.plot([], [], ls='-', solid_capstyle='projecting',
                                 lw=1., c='red')

                lg_handles.append(lin1)
                lg_labels.append(labelDB[3])

            # ---- Water Levels (continuous line) ---- #

            # ---- Continuous Line Datalogger ---- #

            lin2, = plt.plot([], [], '-', zorder=10, linewidth=1,
                             color=self.colorsDB.rgb[3], ms=15)
            lg_handles.append(self.l1_ax2)
            if self.trend_line == 1:
                lg_labels.append(labelDB[4])
            else:
                lg_labels.append(labelDB[5])

            # ---- Water Levels (data points) ----

            if self.trend_line == 1:
                lin3, = self.ax2.plot([], [], '.', ms=10, alpha=0.5,
                                      color=self.colorsDB.rgb[4])
                lg_handles.append(lin3)
                lg_labels.append(labelDB[6])

            # ---- Manual Measures ----

            if len(self.WaterLvlObj.WLmes) > 1:
                lg_handles.append(self.h_WLmes)
                lg_labels.append(labelDB[7])

            if self.isMRC:
                lg_labels.append(labelDB[8])
                lg_handles.append(self.plot_recess)

            if self.isGLUE:
                dum1 = plt.Rectangle((0, 0), 1, 1, fc='0.65', ec='0.65')

                lg_labels.append('GLUE 5/95')
                lg_handles.append(dum1)

            # ---- Position ---------------------------------------------------

            # ---- Draw -------------------------------------------------------

#            LOCS = ['right', 'center left', 'upper right', 'lower right',
#                    'center', 'lower left', 'center right', 'upper left',
#                    'upper center', 'lower center']
            # ncol = int(np.ceil(len(lg_handles)/2.))
            self.ax0.legend(lg_handles, lg_labels, bbox_to_anchor=[1., 1.],
                            loc='lower right', ncol=3,
                            numpoints=1, fontsize=10, frameon=False)
            self.ax0.get_legend().set_zorder(100)
        else:
            if self.ax0.get_legend():
                self.ax0.get_legend().set_visible(False)

    def update_colors(self):  # ===============================================
        self.colorsDB.load_colors_db()

        if not self.__isHydrographExists:
            return

        plt.setp(self.l1_ax2, color=self.colorsDB.rgb[3])
        plt.setp(self.l2_ax2, color=self.colorsDB.rgb[4])
        plt.setp(self.h_WLmes, markeredgecolor=self.colorsDB.rgb[5])
        self.draw_weather()

        self.set_legend()

    def update_fig_size(self):  # =============================================

        self.set_size_inches(self.fwidth, self.fheight)
        self.set_margins()
        self.draw_ylabels()
        self.set_time_scale()

        self.canvas.draw()

    def set_margins(self):  # =================================================

        print('Setting up graph margins')

        fheight = self.fheight

        # --- MARGINS (Inches / Fig. Dimension) --- #

        left_margin = 0.85 / self.fwidth

        if self.meteo_on is False:
            right_margin = 0.15 / self.fwidth
        else:
            right_margin = 0.85 / self.fwidth

        bottom_margin = 0.6 / self.fheight

        top_margin = 0.25 / self.fheight
        if self.isGraphTitle == 1 or self.isLegend == 1:
            if self.meteo_on is False:
                top_margin += 0.2 / fheight
            else:
                top_margin += 0.45 / fheight

        # --- MARGINS (% of figure) --- #

        if self.meteo_on:
            va_ratio = self.va_ratio
        else:
            va_ratio = 0

        htot = 1 - (bottom_margin + top_margin)
        htop = htot * va_ratio
        hlow = htot * (1-va_ratio)
        wtot = 1 - (left_margin + right_margin)

        # Host, Frame, Water Levels, Precipitation, Air Temperature

        for i, axe in enumerate(self.axes):
            if i == 4:  # Air Temperature
                axe.set_position([left_margin, bottom_margin + hlow,
                                  wtot, htop])
            elif i in [0, 1]:  # Time, Frame
                axe.set_position([left_margin, bottom_margin, wtot, htot])

            else:
                axe.set_position([left_margin, bottom_margin, wtot, hlow])

    def draw_ylabels(self):  # ================================================

        labelDB = LabelDatabase(self.language)

        # ------------------------------------------- Calculate LabelPadding --

        left_margin = 0.85
        right_margin = 0.85
        if self.meteo_on is False:
            right_margin = 0.35

        axwidth = (self.fwidth - left_margin - right_margin)

        labPad = 0.3 / 2.54  # in Inches
        labPad /= axwidth   # relative coord.

        # -------------------------------- YLABELS LEFT (Temp. & Waterlvl) ----

        if self.WLdatum == 0:
            lab_ax2 = labelDB.mbgs
        elif self.WLdatum == 1:
            lab_ax2 = labelDB.masl

        # ---- Water Level ---- #

        self.ax2.set_ylabel(lab_ax2, rotation=90,
                            fontsize=self.label_font_size,
                            va='bottom', ha='center')

        # Get bounding box dimensions of yaxis ticklabels for ax2
        renderer = self.canvas.get_renderer()
        self.canvas.draw()

        bbox2_left, _ = self.ax2.yaxis.get_ticklabel_extents(renderer)

        # bbox are structured in the the following way:   [[ Left , Bottom ],
        #                                                  [ Right, Top    ]]

        # Transform coordinates in ax2 coordinate system.
        bbox2_left = self.ax2.transAxes.inverted().transform(bbox2_left)

        # Calculate the labels positions in x and y.
        ylabel2_xpos = bbox2_left[0, 0] - labPad
        ylabel2_ypos = (bbox2_left[1, 1] + bbox2_left[0, 1]) / 2.

        if self.meteo_on is False:
            self.ax2.yaxis.set_label_coords(ylabel2_xpos, ylabel2_ypos)
            return

        # ---- Temperature ---- #

        self.ax4.set_ylabel(labelDB.temperature, rotation=90, va='bottom',
                            ha='center', fontsize=self.label_font_size)

        # Get bounding box dimensions of yaxis ticklabels for ax4
        bbox4_left, _ = self.ax4.yaxis.get_ticklabel_extents(renderer)

        # Transform coordinates in ax4 coordinate system.
        bbox4_left = self.ax4.transAxes.inverted().transform(bbox4_left)

        # Calculate the labels positions in x and y.
        ylabel4_xpos = bbox4_left[0, 0] - labPad
        ylabel4_ypos = (bbox4_left[1, 1] + bbox4_left[0, 1]) / 2.

        # Take the position which is farthest from the left y axis in order
        # to have both labels on the left aligned.
        ylabel_xpos = min(ylabel2_xpos, ylabel4_xpos)

        self.ax2.yaxis.set_label_coords(ylabel_xpos, ylabel2_ypos)
        self.ax4.yaxis.set_label_coords(ylabel_xpos, ylabel4_ypos)

        # -------------------------------------------------- Precipitation ----

        label = labelDB.precip % labelDB.precip_units[self.bwidth_indx]
        self.ax3.set_ylabel(label, rotation=270, va='bottom',
                            ha='center', fontsize=self.label_font_size)

        # Get bounding box dimensions of yaxis ticklabels for ax3
        _, bbox = self.ax3.yaxis.get_ticklabel_extents(renderer)

        # Transform coordinates in ax3 coordinate system and
        # calculate the labels positions in x and y.
        bbox = self.ax3.transAxes.inverted().transform(bbox)

        ylabel3_xpos = bbox[1, 0] + labPad
        ylabel3_ypos = (bbox[1, 1] + bbox[0, 1]) / 2.

        self.ax3.yaxis.set_label_coords(ylabel3_xpos, ylabel3_ypos)

        # --------------------------------------------------- Figure Title ----

        self.draw_figure_title()

    def checkLayout(self, name_well, filename):  # ============================

        # Check if there is a layout stored for the current
        # selected observation well.

        with open(filename, 'r') as f:
            reader = list(csv.reader(f, delimiter='\t'))

        for line in reader:
            if line[0] == name_well:
                return True

        return False

    def save_layout(self, name_well, filename):  # ============================

        # ---- load file ----

        with open(filename, 'r') as f:
            reader = list(csv.reader(f, delimiter='\t'))

        # ---- update content ----

        # this is necessary for Windows when there is an accented character
        # in the path of the meteo data file, in the name of the well, or in
        # the title of the graph.

        fmeteo = self.fmeteo

        colorStack = ''
        for color in self.colorsDB.RGB:
            for code in color:
                colorStack = colorStack + str(code) + ','
            colorStack = colorStack[:-1] + ';'
        colorStack = colorStack[:-1]

        new = [name_well, fmeteo, self.WLmin, self.WLscale,
               self.TIMEmin, self.TIMEmax, self.isGraphTitle, self.isLegend,
               self.RAINscale, self.WLdatum, self.trend_line, self.fwidth,
               self.fheight, colorStack, self.language, self.datemode,
               self.date_labels_display_pattern, self.bwidth_indx,
               self.va_ratio, self.NZGrid]

        for row in range(len(reader)):
            if reader[row][0] == name_well:
                del reader[row]
                break
            else:
                row += 1

        reader.append(new)
        reader[0] = self.header[0]

        # ---- save file ----

        with open(filename, 'w') as f:
            writer = csv.writer(f, delimiter='\t',  lineterminator='\n')
            writer.writerows(reader)

    def load_layout(self, name_well, filename):  # ============================

        # A <checkConfig> is supposed to have been carried before this method
        # is called. So it can be supposed at this point that everything is
        # fine with the graph layout for this well and that it does exist.

        with open(filename, 'r') as f:
            reader = list(csv.reader(f, delimiter='\t'))

        # ---- Find row for Well ----

        for row in range(len(reader)):
            if reader[row][0] == name_well:
                break
            else:
                row += 1

        reader = reader[row]

        # ---- Fetch Info ----

        self.fmeteo = reader[1]
        self.finfo = self.fmeteo[:-3] + 'log'

        self.WLmin = float(reader[2])
        self.WLscale = float(reader[3])

        self.TIMEmin = float(reader[4])
        self.TIMEmax = float(reader[5])

        try:
            self.isGraphTitle = min(abs(int(reader[6])), 1)
        except:
            self.isGraphTitle = 1

        try:
            self.isLegend = min(abs(int(reader[7])), 1)
        except:
            self.isLegend = 1

        try:
            self.RAINscale = abs(int(reader[8]))
        except:
            self.RAINscale = 20

        try:
            self.WLdatum = min(abs(int(reader[9])), 1)
        except:
            self.WLdatum = 1

        try:
            self.trend_line = min(abs(int(reader[10])), 1)
        except:
            self.trend_line = 1

        try:
            self.fwidth = abs(float(reader[11]))
        except:
            self.fwidth = 11.

        try:
            self.fheight = abs(float(reader[12]))
        except:
            self.fheight = 8.5

        try:
            colorStack = reader[13]
            colors = colorStack.rsplit(';')
            for i, color in enumerate(colors):
                color = color.rsplit(',')
                for j in range(3):
                    self.colorsDB.RGB[i][j] = int(color[j])
                    self.colorsDB.rgb[i][j] = int(color[j])/255.
            print('Color Palette loaded from layout.')
            self.colorsDB.save_colors_db()
        except:
            print('!Color Palette is wrong. Keeping defaults.!')

        try:
            self.language = reader[14]
        except:
            self.language = 'English'

        try:
            if reader[15].lower() in ['month', 'year']:
                self.datemode = reader[15]
            else:
                self.datemode = 'month'
        except:
            self.datemode = 'month'

        try:
            self.date_labels_display_pattern = int(reader[16])
        except:
            self.date_labels_display_pattern = 2

        try:
            if int(reader[17]) in [0, 1, 2]:
                self.bwidth_indx = int(reader[17])
            else:
                self.bwidth_indx = 1
        except:
            self.bwidth_indx = 1

        try:
            self.va_ratio = abs(float(reader[18]))
            if self.va_ratio > 0.95:
                self.va_ratio = 0.95
            if self.va_ratio < 0.05:
                self.va_ratio = 0.05
        except:
            self.va_ratio = 0.15

        try:
            self.NZGrid = int(reader[19])
        except:
            self.NZGrid = 8

    def best_fit_waterlvl(self):  # ===========================================

        WL = self.WaterLvlObj.lvl
        if self.WLdatum == 1:  # masl
            WL = self.WaterLvlObj.ALT - WL

        WL = WL[~np.isnan(WL)]
        dWL = np.max(WL) - np.min(WL)
        ygrid = self.NZGrid - 5

        # --- WL Scale --- #

        SCALE = np.hstack((np.arange(0.05, 0.30, 0.05),
                           np.arange(0.3, 5.1, 0.1)))
        dSCALE = np.abs(SCALE - dWL / ygrid)
        indx = np.where(dSCALE == np.min(dSCALE))[0][0]

        self.WLscale = SCALE[indx]

        # ---- WL Min Value --- #

        if self.WLdatum == 0:  # mbgs
            N = np.ceil(np.max(WL) / self.WLscale)
        elif self.WLdatum == 1:  # masl
            # WL = self.WaterLvlObj.ALT - WL
            N = np.floor(np.min(WL) / self.WLscale)

        self.WLmin = self.WLscale * N

        return self.WLscale, self.WLmin

    def best_fit_time(self, TIME):  # =========================================

        # ----- Data Start -----

        date0 = xldate_as_tuple(TIME[0], 0)
        date0 = (date0[0], date0[1], 1)

        self.TIMEmin = xldate_from_date_tuple(date0, 0)

        # ----- Date End -----

        date1 = xldate_as_tuple(TIME[-1], 0)

        year = date1[0]
        month = date1[1] + 1
        if month > 12:
            month = 1
            year += 1

        date1 = (year, month, 1)

        self.TIMEmax = xldate_from_date_tuple(date1, 0)

        return date0, date1

    def resample_bin(self):  # ================================================

        # day; week; month; year
        self.bwidth = [1., 7., 30., 365.][self.bwidth_indx]
        bwidth = self.bwidth

        if self.bwidth_indx == 0:  # daily

            self.bTIME = np.copy(self.TIMEmeteo)
            self.bTMAX = np.copy(self.TMAX)
            self.bPTOT = np.copy(self.PTOT)
            self.bRAIN = np.copy(self.RAIN)
        else:
            self.bTIME = self.bin_sum(self.TIMEmeteo, bwidth) / bwidth
            self.bTMAX = self.bin_sum(self.TMAX, bwidth) / bwidth
            self.bPTOT = self.bin_sum(self.PTOT, bwidth)
            self.bRAIN = self.bin_sum(self.RAIN, bwidth)

#        elif self.bwidth_indx == 4 : # monthly
#            print('option not yet available, kept default of 1 day')
#
#        elif self.bwidth_indx == 5 : # yearly
#            print('option not yet available, kept default of 1 day')

    def bin_sum(self, x, bwidth):  # ==========================================
        """
        Sum data x over bins of width "bwidth" starting at indice 0 of x.
        If there is residual data at the end because of the last bin being not
        complete, data are rejected and removed from the reshaped series.
        """

        bwidth = int(bwidth)
        nbin = int(np.floor(len(x) / bwidth))

        bheight = x[:nbin*bwidth].reshape(nbin, bwidth)
        bheight = np.sum(bheight, axis=1)

        return bheight

    def draw_GLUE(self):  # ===================================================

        fname = 'GLUE.h5'
        with h5py.File(fname, 'r') as hf:
            data = hf.get('hydrograph')
            hydrograph = np.array(data)

            data = hf.get('Time')
            tweatr = np.array(data)

            data = hf.get('RMSE')
            RMSE = np.array(data)

            data = hf.get('twlvl')
            twlvl = np.array(data)

        ts = np.where(twlvl[0] == tweatr)[0]
        te = np.where(twlvl[-1] == tweatr)[0]
        time = tweatr[ts:te+1]

        RMSE = RMSE / np.sum(RMSE)

        hGLUE = []

        for i in range(len(time)):
            isort = np.argsort(hydrograph[:, i])
            CDF = np.cumsum(RMSE[isort])
            hGLUE.append(
                np.interp([0.05, 0.5, 0.95], CDF, hydrograph[isort, i]))

        hGLUE = np.array(hGLUE)
        min_wlvl = hGLUE[:, 0] / 1000.
        max_wlvl = hGLUE[:, 2] / 1000.

        self.ax2.fill_between(time, min_wlvl, max_wlvl, edgecolor='0.65',
                              color='0.65', zorder=0)

        self.isGLUE = True
        self.set_legend()

    def draw_recession(self):  # ==============================================
        t = self.WaterLvlObj.trecess
        wl = self.WaterLvlObj.hrecess
        self.plot_recess.set_data(t, wl)

        self.isMRC = True
        self.set_legend()

    def draw_waterlvl(self):  # ===============================================
        """
        This method is called the first time the graph is plotted and each
        time water level datum is changed.
        """

        # -------------------------------------------------- Logger Measures --

        time = self.WaterLvlObj.time

        if self.WLdatum == 1:  # masl
            water_lvl = self.WaterLvlObj.ALT - self.WaterLvlObj.lvl
        else:  # mbgs -> yaxis is inverted
            water_lvl = self.WaterLvlObj.lvl

        if self.trend_line == 1:
            tfilt, wlfilt = filt_data(time, water_lvl, 7)

            self.l1_ax2.set_data(tfilt, wlfilt)
            self.l2_ax2.set_data(time, water_lvl)

        else:
            self.l1_ax2.set_data(time, water_lvl)
            self.l2_ax2.set_data([], [])

        # -------------------------------------------------- Manual Measures --

        TIMEmes = self.WaterLvlObj.TIMEmes
        WLmes = self.WaterLvlObj.WLmes

        if len(WLmes) > 1:
            if self.WLdatum == 1:   # masl
                WLmes = self.WaterLvlObj.ALT - WLmes

            self.h_WLmes.set_data(TIMEmes, WLmes)

    def draw_weather(self):  # ================================================
        """
        This method is called the first time the graph is plotted and each
        time the time scale is changed.
        """

        if self.meteo_on is False:
            return

        # --------------------------------------------------- SUBSAMPLE DATA --

        # For performance purposes, only the data that fit within the limits
        # of the x axis limits are plotted.

        istart = np.where(self.bTIME > self.TIMEmin)[0]
        if len(istart) == 0:
            istart = 0
        else:
            istart = istart[0]
            if istart > 0:
                istart += -1

        iend = np.where(self.bTIME < self.TIMEmax)[0]
        if len(iend) == 0:
            iend = 0
        else:
            iend = iend[-1]
            if iend < len(self.bTIME):
                iend += 1

        time = self.bTIME[istart:iend]
        Tmax = self.bTMAX[istart:iend]
        Ptot = self.bPTOT[istart:iend]
        Rain = self.bRAIN[istart:iend]

        # ------------------------------------------------------ PLOT PRECIP --

        TIME2X = np.zeros(len(time) * 4)
        Ptot2X = np.zeros(len(time) * 4)
        Rain2X = np.zeros(len(time) * 4)

        n = self.bwidth / 2.
        f = 0.85  # Space between individual bar.

        TIME2X[0::4] = time - n * f
        TIME2X[1::4] = time - n * f
        TIME2X[2::4] = time + n * f
        TIME2X[3::4] = time + n * f

        Ptot2X[0::4] = 0
        Ptot2X[1::4] = Ptot
        Ptot2X[2::4] = Ptot
        Ptot2X[3::4] = 0

        Rain2X[0::4] = 0
        Rain2X[1::4] = Rain
        Rain2X[2::4] = Rain
        Rain2X[3::4] = 0

        self.PTOT_bar.remove()
        self.RAIN_bar.remove()

        self.PTOT_bar = self.ax3.fill_between(TIME2X, 0., Ptot2X,
                                              color=self.colorsDB.rgb[2],
                                              linewidth=0.0)

        self.RAIN_bar = self.ax3.fill_between(TIME2X, 0., Rain2X,
                                              color=self.colorsDB.rgb[1],
                                              linewidth=0.0)

        self.baseline.set_data([self.TIMEmin, self.TIMEmax], [0, 0])

        # ---------------------------------------------------- PLOT AIR TEMP --

        TIME2X = np.zeros(len(time)*2)
        Tmax2X = np.zeros(len(time)*2)

        n = self.bwidth / 2.
        TIME2X[0:2*len(time)-1:2] = time - n
        TIME2X[1:2*len(time):2] = time + n
        Tmax2X[0:2*len(time)-1:2] = Tmax
        Tmax2X[1:2*len(time):2] = Tmax

        self.l1_ax4.remove()
        self.l1_ax4 = self.ax4.fill_between(TIME2X, 0., Tmax2X,
                                            color=self.colorsDB.rgb[0],
                                            edgecolor='None')

        self.l2_ax4.set_xdata(TIME2X)
        self.l2_ax4.set_ydata(Tmax2X)

        self.update_precip_scale()

    def set_time_scale(self):  # ==============================================

        # ------------------------------------------------- time min and max --

        if self.datemode.lower() == 'year':

            year = xldate_as_tuple(self.TIMEmin, 0)[0]
            self.TIMEmin = xldate_from_date_tuple((year, 1, 1), 0)

            last_month = xldate_as_tuple(self.TIMEmax, 0)[1] == 1
            last_day = xldate_as_tuple(self.TIMEmax, 0)[2] == 1

            if last_month and last_day:
                pass
            else:
                year = xldate_as_tuple(self.TIMEmax, 0)[0] + 1
                self.TIMEmax = xldate_from_date_tuple((year, 1, 1), 0)

        # ---------------------------------------------- xticks and labels ----

        # ---- compute parameters ---- #

        xticks_info = self.make_xticks_info()

        # ---- major ---- #

        self.ax1.set_xticks(xticks_info[0])

        # -------------------------------------------------------- xlabels ----

        # labels are set using the minor ticks.

        # labels are placed manually instead. This is around 25% faster than
        # using the minor ticks.

#        self.ax1.set_xticks(xticks_info[1], minor=True)
#        self.ax1.tick_params(which='minor', length=0)
#        self.ax1.xaxis.set_ticklabels(xticks_info[2], minor=True, rotation=45,
#                                      va='top', ha='right', fontsize=10)

        # ---- Remove labels ---- #

        for i in range(len(self.xlabels)):
            self.xlabels[i].remove()

        # ---- Redraw labels ---- #

        padding = mpl.transforms.ScaledTranslation(0, -5/72.,
                                                   self.dpi_scale_trans)
        transform = self.ax1.transData + padding

        self.xlabels = []
        for i in range(len(xticks_info[1])):
            new_label = self.ax1.text(xticks_info[1][i], 0,
                                      xticks_info[2][i], rotation=45,
                                      va='top', ha='right', fontsize=10.,
                                      transform=transform)

            self.xlabels.append(new_label)

        # ---------------------------------------------------- axis limits ----

        self.ax1.axis([self.TIMEmin, self.TIMEmax, 0, self.NZGrid])

    def draw_xlabels(self):  # ================================================

        # Called when there is a change in language of the labels
        # of the graph

        _, _, xticks_labels = self.make_xticks_info()
        self.ax1.xaxis.set_ticklabels([])

        # ---- using minor ticks ---- #

#        self.ax1.xaxis.set_ticklabels(xticks_labels, minor=True, rotation=45,
#                                      va='top', ha='right', fontsize=10)

        # ---- ploting manually the xlabels instead ---- #

        for i in range(len(self.xlabels)):
            self.xlabels[i].set_text(xticks_labels[i])

    def draw_figure_title(self):  # ===========================================

        labelDB = LabelDatabase(self.language)

        if self.isGraphTitle == 1:
            self.text1.set_text(labelDB.station_meteo % (self.name_meteo,
                                                         self.dist))

            self.figTitle.set_text(labelDB.title % self.WaterLvlObj.name_well)
        else:
            self.text1.set_text('')
            self.figTitle.set_text('')

    def update_waterlvl_scale(self):  # =======================================

        if self.meteo_on:
            NZGrid = self.NZGrid
        else:
            NZGrid = self.NZGrid - 2

        self.axLow.set_yticks(np.arange(1, self.NZGrid))
        self.axLow.axis(ymin=0, ymax=NZGrid)
        self.axLow.yaxis.set_ticklabels([])

        if self.WLdatum == 1:   # masl
            WLmin = self.WLmin
            WLscale = self.WLscale
            WLmax = WLmin + (NZGrid * WLscale)

            if self.meteo_on:
                self.ax2.set_yticks(np.arange(WLmin, WLmax - 1.9*WLscale,
                                              WLscale))
            else:
                self.ax2.set_yticks(np.arange(WLmin, WLmax + 0.1*WLscale,
                                              WLscale))

            self.ax2.axis(ymin=WLmin, ymax=WLmax)

        else:  # mbgs: Y axis is inverted
            WLmax = self.WLmin
            WLscale = self.WLscale
            WLmin = WLmax - (NZGrid * WLscale)

            if self.meteo_on:
                self.ax2.set_yticks(np.arange(WLmax, WLmin + 1.9*WLscale,
                                              -WLscale))
            else:
                self.ax2.set_yticks(np.arange(WLmax, WLmin - 0.1*WLscale,
                                              -WLscale))

            self.ax2.axis(ymin=WLmin, ymax=WLmax)
            self.ax2.invert_yaxis()

    def update_precip_scale(self):  # =========================================

        if self.meteo_on is False:
            return

        ymax = self.NZGrid * self.RAINscale

        try:
            p = self.PTOT_bar.get_paths()[0]
            v = p.vertices
            y = v[:, 1]

            ymax = self.NZGrid * self.RAINscale

            yticksmax = 0
            while 1:
                if yticksmax > max(y):
                    break
                yticksmax += self.RAINscale
            yticksmax = min(ymax, yticksmax) + self.RAINscale/2.

        except:
            yticksmax = 3.9 * self.RAINscale

        self.ax3.axis(ymin=0, ymax=ymax)
        self.ax3.set_yticks(np.arange(0, yticksmax, self.RAINscale))
        self.ax3.invert_yaxis()

    def set_gridLines(self):  # ===============================================

        # 0 -> None, 1 -> "-" 2 -> ":"

        if self.gridLines == 0:
            for ax in self.axes:
                ax._gridOn = False

        elif self.gridLines == 1:
            self.ax4.grid(axis='y', color=[0.35, 0.35, 0.35], linestyle='-',
                          linewidth=0.5, which='minor')
            self.axLow.grid(axis='y', color=[0.35, 0.35, 0.35], linestyle='-',
                            linewidth=0.5)
            self.ax1.grid(axis='x', color=[0.35, 0.35, 0.35], linestyle='-',
                          linewidth=0.5)

        else:
            self.ax4.grid(axis='y', color=[0.35, 0.35, 0.35], linestyle=':',
                          linewidth=0.5, dashes=[0.5, 5], which='minor')
            self.axLow.grid(axis='y', color=[0.35, 0.35, 0.35], linestyle=':',
                            linewidth=0.5, dashes=[0.5, 5])
            self.ax1.grid(axis='x', color=[0.35, 0.35, 0.35], linestyle=':',
                          linewidth=0.5, dashes=[0.5, 5])

    def make_xticks_info(self):  # ============================================

        # ---------------------------------------- horizontal text alignment --

        # The strategy here is to:
        # 1. render some random text ;
        # 2. get the height of its bounding box ;
        # 3. get the horizontal translation of the top-right corner after a
        #    rotation of the bbox of 45 degrees ;
        # 4. sclale the length calculated in step 3 to the height to width
        #    ratio of the axe ;
        # 5. convert the lenght calculated in axes coord. to the data coord.
        #    system ;
        # 6. remove the random text from the figure.

        # Random text bbox height :

        dummytxt = self.ax1.text(0.5, 0.5, 'some_dummy_text', fontsize=10,
                                 ha='right', va='top',
                                 transform=self.ax1.transAxes)

        renderer = self.canvas.get_renderer()

        bbox = dummytxt.get_window_extent(renderer)
        bbox = bbox.transformed(self.ax1.transAxes.inverted())

        # Horiz. trans. of bbox top-right corner :

        dx = bbox.height * np.sin(np.radians(45))

        # Scale dx to axe dimension :

        bbox = self.ax1.get_window_extent(renderer)  # in pixels
        bbox = bbox.transformed(self.dpi_scale_trans.inverted())  # in inches

        sdx = dx * bbox.height / bbox.width
        sdx *= (self.TIMEmax - self.TIMEmin + 1)

        dummytxt.remove()

        # Transform to data coord :

        n = self.date_labels_display_pattern
        month_names = LabelDatabase(self.language).month_names

        xticks_labels_offset = sdx

        xticks_labels = []
        xticks_position = [self.TIMEmin]
        xticks_labels_position = []

        if self.datemode.lower() == 'month':

            i = 0
            while xticks_position[i] < self.TIMEmax:

                year = xldate_as_tuple(xticks_position[i], 0)[0]
                month = xldate_as_tuple(xticks_position[i], 0)[1]

                month_range = monthrange(year, month)[1]

                xticks_position.append(xticks_position[i] + month_range)

                if i % n == 0:

                    xticks_labels_position.append(xticks_position[i] +
                                                  0.5 * month_range +
                                                  xticks_labels_offset)

                    xticks_labels.append("%s '%s" % (month_names[month - 1],
                                                     str(year)[-2:]))

                i += 1

        elif self.datemode.lower() == 'year':

            i = 0
            year = xldate_as_tuple(xticks_position[i], 0)[0]
            while xticks_position[i] < self.TIMEmax:

                xticks_position.append(
                                     xldate_from_date_tuple((year+1, 1, 1), 0))
                year_range = xticks_position[i+1] - xticks_position[i]

                if i % n == 0:

                    xticks_labels_position.append(xticks_position[i] +
                                                  0.5 * year_range +
                                                  xticks_labels_offset)

                    xticks_labels.append("%d" % year)

                year += 1
                i += 1


        return xticks_position, xticks_labels_position, xticks_labels


#==============================================================================
def  load_weather_log(fname, varname):
#==============================================================================

    print('loading info for missing weather data')

    #---- load Data ----

    with open(fname, 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        reader = list(reader)[36:]

    #---- load data and convert time ----

    time = []
    tseg = [np.nan, np.nan, np.nan]
    for i in range(len(reader)):
        if reader[i][0] == varname:
            year = int(float(reader[i][1]))
            month = int(float(reader[i][2]))
            day = int(float(reader[i][3]))
            xldate = xldate_from_date_tuple((year, month, day), 0)

            if np.isnan(tseg[1]):
                tseg[1] = xldate
                tseg[2] = xldate + 1
            elif tseg[2] == xldate:
                tseg[2] += 1
            else:
                time.extend(tseg)
                tseg[1] = xldate
                tseg[2] = xldate + 1
    time.append(np.nan)
    time = np.array(time)

#    time = []
#    for i in range(len(reader)):
#        if reader[i][0] == varname:
#            year = int(float(reader[i][1]))
#            month = int(float(reader[i][2]))
#            day = int(float(reader[i][3]))
#            newt = xldate_from_date_tuple((year, month, day), 0)
#            time.append(newt)
#            time.append(newt+1)
#            time.append(np.nan)
#    time = np.array(time)

    return time

#==============================================================================
def filt_data(time, waterlvl, period):
    """
    period is in days
    """
#==============================================================================

    #------------- RESAMPLING 6H BASIS AND NAN ESTIMATION BY INTERPOLATION ----

    time6h_0 = np.floor(time[0]) + 1/24
    time6h_end = np.floor(time[-1]) + 1/24

    time6h = np.arange(time6h_0, time6h_end + 6/24., 6/24.)

    # Remove times with nan values
    index_nonan = np.where(~np.isnan(waterlvl))[0]

    # Resample data and interpolate missing values
    waterlvl = np.interp(time6h, time[index_nonan], waterlvl[index_nonan])

    #----------------------------------------------------------- FILT DATA ----
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


# =============================================================================

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

    R = 6373.0  # R = Earth radius in km

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


if __name__ == '__main__':  # =================================================

    import sys
    from mplFigViewer3 import ImageViewer
    plt.ioff()

    app = QtGui.QApplication(sys.argv)

    # ------------------------------------------------------------ load data --

#    fmeteo = 'Files4testing/AUTEUIL_2000-2013.out'
#    fwaterlvl = 'Files4testing/PO16A.xls'

    # ---- Pont Rouge ----

    dirname = '../Projects/Pont-Rouge'
    fmeteo = dirname + '/Meteo/Output/STE CHRISTINE (7017000)_1960-2015.out'
    finfo = dirname + '/Meteo/Output/STE CHRISTINE (7017000)_1960-2015.log'
    fwaterlvl = dirname + '/Water Levels/5080001.xls'

    # ---- Cap-aux-Meules ----
    dirname = '../Projects/IDM/'
    fmeteo = os.path.join(dirname, 'Meteo', 'Output', 'IDM (JSG2017)',
                          'IDM (JSG2017)_1960-2016.out')
    finfo = os.path.join(dirname, 'Meteo', 'Output', 'IDM (JSG2017)',
                         'IDM (JSG2017)_1960-2016.log')
    fwaterlvl = os.path.join(dirname, 'Water Levels', 'Cap-aux-Meules.xls')

    # ---- Valcartier ----

#    dirname = '../Projects/Valcartier'
#    fmeteo = dirname + '/Meteo/Output/Valcartier (9999999)/Valcartier (9999999)_1994-2015.out'
#    fwaterlvl = dirname + '/Water Levels/valcartier2.xls'
#    finfo = (dirname + '/Meteo/Output/Valcartier (9999999)/Valcartier (9999999)_1994-2015.log')

    # ---- Dundurn ----

#    dirname = '/home/jnsebgosselin/Dropbox/WHAT/Projects/Dundurn'
#    fmeteo = dirname + "/Meteo/Output/SASKATOON DIEFENBAKER INT'L A (4057120)/SASKATOON DIEFENBAKER INT'L A (4057120)_1950-2015.out"
#    fwaterlvl = dirname + '/Water Levels/P19 2013-2014.xls'
#    fwaterlvl = dirname + '/Water Levels/P22 2014-2015.xls'
#    finfo = dirname + "/Meteo/Output/SASKATOON DIEFENBAKER INT'L A (4057120)/SASKATOON DIEFENBAKER INT'L A (4057120)_1950-2015.log"

    waterLvlObj = WaterlvlData()
    waterLvlObj.load(fwaterlvl)

#    fname = 'Files4testing/waterlvl_manual_measurements.xls'
#    waterLvlObj.load_waterlvl_measures(fname, 'PO16A')

    meteo_obj = meteo.MeteoObj()
    meteo_obj.load_and_format(fmeteo)

    # ---------------------------------------------------- set up hydrograph --

    hg = Hydrograph()
    hg.set_waterLvlObj(waterLvlObj)
    hg.set_MeteoObj(meteo_obj)
    hg.finfo = finfo
    hg.language = 'french'

    what = ['normal', 'MRC', 'GLUE'][2]

    if what == 'normal':
        hg.fwidth = 11.  # Width of the figure in inches
        hg.fheight = 8.5

        hg.WLdatum = 0  # 0 -> mbgs ; 1 -> masl
        hg.trend_line = False
        hg.gridLines = 2  # Gridlines Style
        hg.isGraphTitle = 1  # 1 -> title ; 0 -> no title
        hg.isLegend = 1

        hg.meteo_on = True  # True or False
        hg.datemode = 'year'  # 'month' or 'year'
        hg.date_labels_display_pattern = 1
        hg.bwidth_indx = 2  # Meteo Bin Width
        # 0: daily | 1: weekly | 2: monthly | 3: yearly
        hg.RAINscale = 100

        hg.best_fit_time(waterLvlObj.time)
        hg.best_fit_waterlvl()
        hg.generate_hydrograph()

    elif what == 'MRC':

        hg.fheight = 5.
        hg.isGraphTitle = 0

        hg.NZGrid = 11
        hg.WLmin = 10.75
        hg.WLscale = 0.25

        hg.best_fit_time(waterLvlObj.time)
        hg.generate_hydrograph(meteo_obj)

        hg.draw_recession()
        hg.savefig(dirname + '/MRC_hydrograph.pdf')

        hg.isMRC = False

    elif what == 'GLUE':

        hg.fwidth = 11
        hg.fheight = 4

        hg.NZGrid = 8
        hg.WLmin = 5
        hg.WLscale = 0.5

        hg.isGraphTitle = 0 # 1 -> title ; 0 -> no title
        hg.isLegend = 1
        hg.meteo_on = False
        hg.datemode = 'year' # 'month' or 'year'
        hg.date_labels_display_pattern = 3

        hg.best_fit_time(waterLvlObj.time)
        hg.generate_hydrograph(meteo_obj)

        plt.setp(hg.l1_ax2, zorder=10, linewidth=1, color='blue', ms=2,
                 linestyle='none', marker='.')

        # plot a hydrograph friend
#        wl2 = WaterlvlData()
#        wl2.load(dirname + '/Water Levels/5080001.xls')
#        ax2 = hydrograph.ax2
#        ax2.plot(wl2.time, wl2.lvl, color='green')

        hg.draw_GLUE()
        hg.draw_recession()
        hg.savefig(dirname + '/GLUE_hydrograph.pdf')

    # ------------------------------------------------ show figure on-screen --

    imgview = ImageViewer()
    imgview.sfmax = 10
    imgview.load_mpl_figure(hg)
    imgview.show()

    sys.exit(app.exec_())
