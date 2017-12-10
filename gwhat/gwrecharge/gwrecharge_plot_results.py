# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Standard library imports

# from datetime import date
import csv

# ---- Imports: third parties

import numpy as np
import matplotlib as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
# from xlrd.xldate import xldate_from_date_tuple

from PyQt5.QtCore import Qt

# ---- Imports: local


class FigWaterLevelGLUE(FigureCanvasQTAgg):
    """
    This is a graph that shows observed ground-water levels and GLUE 5/95
    predicted water levels.
    """
    colors = {'dark grey': '0.65',
              'light grey': '0.85'}

    def __init__(self, language='English'):

        self.language = language

        # ---- Prepare Figure and Axe

        fwidth, fheight = 8.5, 5
        fig = mpl.figure.Figure(figsize=(fwidth, fheight), facecolor='white')
        super(FigWaterLevelGLUE, self).__init__(fig)
        self.setAttribute(Qt.WA_DeleteOnClose)

        lmarg = 0.85/fwidth
        rmarg = 0.25/fwidth
        tmarg = 0.5/fheight
        bmarg = 0.65/fheight

        axwidth = 1 - (lmarg + rmarg)
        axheight = 1 - (bmarg + tmarg)

        ax = fig.add_axes([lmarg, bmarg, axwidth, axheight])

        # ---- Axes labels

        if language == 'French':
            label = "Niveau d'eau (m sous la surface)"
        else:
            label = 'Water Level (mbgs)'

        ax.set_ylabel(label, fontsize=16)

        # ---- Grids

        ax.grid(axis='x', color='0.35', ls=':', lw=1, zorder=200)
        ax.grid(axis='y', color='0.35', ls=':', lw=1, zorder=200)
        ax.invert_yaxis()

        # ----- Plot Observation

        self.plot_wlobs, = ax.plot([], [], color='b', ls='None',
                                   marker='.', ms=3, zorder=100)
        fig.canvas.draw()

        # ---- Yticks format

        ax.yaxis.set_ticks_position('left')
        ax.tick_params(axis='y', direction='out', labelsize=12)

        # ---- Xticks format

        ax.xaxis.set_ticks_position('bottom')
        ax.tick_params(axis='x', direction='out')
        fig.autofmt_xdate()

        # ---- Legend

        dum1 = mpl.patches.Rectangle((0, 0), 1, 1, fc='0.85', ec='0.65')
        dum2, = ax.plot([], [], color='b', ls='None', marker='.', ms=10)

        lg_handles = [dum2, dum1]
        lg_labels = ['Observations', 'GLUE 5/95']

        ax.legend(lg_handles, lg_labels, ncol=2, fontsize=12, frameon=False,
                  numpoints=1)

    def plot_prediction(self, dates, wlobs, glue_data):
        hydrograph = np.array(glue_data['hydrograph'])
        rmse = np.array(glue_data['RMSE'])
        rmse = rmse/np.sum(rmse)

        hGLUE = []
        conf = [0.05, 0.5, 0.95]
        for i in range(len(hydrograph[0, :])):
            isort = np.argsort(hydrograph[:, i])
            CDF = np.cumsum(rmse[isort])
            hGLUE.append(np.interp(conf, CDF, hydrograph[isort, i]))
        hGLUE = np.array(hGLUE)

        # ---- Plot the data
        ax = self.figure.axes[0]
        self.plot_wlobs.set_xdata(dates)
        self.plot_wlobs.set_ydata(wlobs)
        ax.fill_between(dates,  hGLUE[:, -1]/1000,  hGLUE[:, 0]/1000,
                        facecolor='0.85', lw=1, edgecolor='0.65', zorder=0)
        self.show()


class FigYearlyRechgGLUE(FigureCanvasQTAgg):
    """
    This is a graph that shows annual ground-water recharge and its
    uncertainty.
    """

    def __init__(self, Ymin0=None, Ymax0=None, yrs_range=None,
                 language='English'):
        self.language = language

        # ---- Prepare Figure and Axe

        fwidth, fheight = 8.5, 5
        fig = mpl.figure.Figure(figsize=(fwidth, fheight), facecolor='white')
        super(FigWaterLevelGLUE, self).__init__(fig)
        self.setAttribute(Qt.WA_DeleteOnClose)
