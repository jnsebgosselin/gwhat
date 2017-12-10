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
from PyQt5.QtWidgets import QGridLayout, QApplication

# ---- Imports: local

from gwhat.gwrecharge.gwrecharge_calc2 import calcul_glue
from gwhat.gwrecharge.gwrecharge_calc2 import calcul_glue_yearly_rechg
from gwhat.common.widgets import DialogWindow
from gwhat.common import IconDB


class NavigationToolbar(NavigationToolbar2QT):
    # only display the buttons we need
    toolitems = [t for t in NavigationToolbar2QT.toolitems if
                 t[0] in ('Home', 'Pan', 'Zoom', 'Save')]

    def __init__(self, *args, **kwargs):
        icondb = IconDB()
        self.icons = {'home.png': IconDB().home,
                      'move.png': IconDB().pan,
                      'zoom_to_rect.png': IconDB().search,
                      'filesave.png': IconDB().save}
        super(NavigationToolbar, self).__init__(*args, **kwargs)
    #     self.layout().takeAt(1)  #or more than 1 if you have more buttons

    def _icon(self, name):
        """Matplotlib method override."""
        icondb = IconDB()
        self.icons = {'home.png': IconDB().home,
                      'move.png': IconDB().pan,
                      'zoom_to_rect.png': IconDB().search,
                      'filesave.png': IconDB().save}
        if name in list(self.icons.keys()):
            return self.icons[name]
        else:
            return super(NavigationToolbar, self)._icon(name)


class ViewerWaterLevelGLUE(DialogWindow):
    def __init__(self, language='English', parent=None):
        super(ViewerWaterLevelGLUE, self).__init__(parent)
        self.setFixedSize(900, 500)

        self.figure = FigWaterLevelGLUE()
        self.toolbar = NavigationToolbar(self.figure, parent=self)

        layout = QGridLayout(self)
        layout.addWidget(self.toolbar, 0, 0)
        layout.addWidget(self.figure, 1, 0)

    def plot_prediction(self, glue_data):
        self.figure.plot_prediction(glue_data)


class FigResultsBase(FigureCanvasQTAgg):
    """
    This is the base figure format to plot GLUE results.
    """
    colors = {'dark grey': '0.65',
              'light grey': '0.85'}

    def __init__(self, language='English'):
        super(FigResultsBase, self).__init__(mpl.figure.Figure())
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.language = language

        fwidth, fheight = 8.5, 5
        self.figure.set_size_inches(fwidth, fheight)
        self.figure.patch.set_facecolor('white')

        lmarg = 0.85/fwidth
        rmarg = 0.25/fwidth
        tmarg = 0.5/fheight
        bmarg = 0.65/fheight

        axwidth = 1 - (lmarg + rmarg)
        axheight = 1 - (bmarg + tmarg)

        self.ax0 = self.figure.add_axes([lmarg, bmarg, axwidth, axheight])


class FigWaterLevelGLUE(FigResultsBase):
    """
    This is a graph that shows observed ground-water levels and GLUE 5/95
    predicted water levels.
    """

    def __init__(self, *args, **kargs):
        super(FigWaterLevelGLUE, self).__init__(*args, **kargs)
        fig = self.figure
        ax = self.ax0

        # ---- Axes labels

        if self.language == 'French':
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

    def plot_prediction(self, glue_data):
        glue_dly = calcul_glue(glue_data, [0.05, 0.95], varname='hydrograph')

        dates, wlobs = glue_data['wl_date'], glue_data['wl_obs']
        ax = self.figure.axes[0]
        self.plot_wlobs.set_xdata(dates)
        self.plot_wlobs.set_ydata(wlobs)
        ax.fill_between(dates, glue_dly[:, -1]/1000, glue_dly[:, 0]/1000,
                        facecolor='0.85', lw=1, edgecolor='0.65', zorder=0)


class FigYearlyRechgGLUE(FigResultsBase):
    """
    This is a graph that shows annual ground-water recharge and its
    uncertainty.
    """

    def __init__(self, *args, **kargs):
        super(FigYearlyRechgGLUE, self).__init__(*args, **kargs)
        fig = self.figure
        ax0 = self.ax0

        # ---- Modify ax0

        ax0.patch.set_visible(False)
        for axis in ['top', 'bottom', 'left', 'right']:
            ax0.spines[axis].set_linewidth(0.5)
        ax0.set_axisbelow(True)

        # ---- Prepare data

    def plot_recharge(self, data, Ymin0=None, Ymax0=None, yrs_range=None):
        fig = self.figure
        ax0 = self.ax0

        p = [0.05, 0.25, 0.5, 0.75, 0.95]
        year_labels, glue_rechg_yr = calcul_glue_yearly_rechg(
                data, p, yrs_range)

        max_rechg_yrly = glue_rechg_yr[:, -1]
        min_rechg_yrly = glue_rechg_yr[:, 0]
        prob_rechg_yrly = glue_rechg_yr[:, 2]
        glue25_yr = glue_rechg_yr[:, 1]
        glue75_yr = glue_rechg_yr[:, -2]

        # ---- Axis range

        if yrs_range:
            yrs2plot = np.arange(yrs_range[0], yrs_range[1]).astype('int')
        else:
            years = np.array(data['Year']).astype(int)
            yrs2plot = np.arange(np.min(years), np.max(years)).astype('int')

        Xmin0 = min(yrs2plot)-1
        Xmax0 = max(yrs2plot)+1

        if Ymax0 is None:
            Ymax0 = np.max(max_rechg_yrly) + 50
        if Ymin0 is None:
            Ymin0 = 0

        # ---- Xticks format

        ax0.xaxis.set_ticks_position('bottom')
        ax0.tick_params(axis='x', direction='out', pad=1)
        ax0.set_xticks(yrs2plot)
        ax0.xaxis.set_ticklabels(year_labels, rotation=45, ha='right')

        # ----- ticks format

        if np.max(max_rechg_yrly) < 250:
            yticks = np.arange(0, Ymax0+1, 25)
        else:
            yticks = np.arange(0, Ymax0+1, 100)

        ax0.yaxis.set_ticks_position('left')
        ax0.set_yticks(yticks)
        ax0.tick_params(axis='y', direction='out', gridOn=True, labelsize=12)
        ax0.grid(axis='y', color=[0.35, 0.35, 0.35], linestyle=':',
                 linewidth=0.5, dashes=[0.5, 5])

        ax0.set_yticks(np.arange(0, Ymax0, 25), minor=True)
        ax0.tick_params(axis='y', direction='out', which='minor', gridOn=False)

        # ---- Axis range

        ax0.axis([Xmin0, Xmax0, Ymin0, Ymax0])

        # ---- Plot results

        ax0.plot(yrs2plot, prob_rechg_yrly, ls='--', color='0.35', zorder=100)

        yerr = [prob_rechg_yrly-min_rechg_yrly, max_rechg_yrly-prob_rechg_yrly]
        herr = ax0.errorbar(yrs2plot, prob_rechg_yrly, yerr=yerr,
                            fmt='o', capthick=1, capsize=4, ecolor='0',
                            elinewidth=1, mfc='White', mec='0', ms=5,
                            markeredgewidth=1, zorder=200)

        h25 = ax0.plot(yrs2plot, glue25_yr, color='red',
                       dashes=[3, 5], alpha=0.65)
        ax0.plot(yrs2plot, glue75_yr, color='red', dashes=[3, 5], alpha=0.65)

        # ----- Legend

        lg_handles = [herr[0], herr[1], h25[0]]
        lg_labels = ['Recharge (GLUE 50)', 'Recharge (GLUE 5/95)',
                     'Recharge (GLUE 25/75)']

        ax0.legend(lg_handles, lg_labels, ncol=3, fontsize=12, frameon=False,
                   numpoints=1, loc='upper left')


# ---- if __name__ == '__main__'

if __name__ == '__main__':
    from gwhat.gwrecharge.gwrecharge_calc2 import RechgEvalWorker
    import sys
    import time

    app = QApplication(sys.argv)

    rechg_worker = RechgEvalWorker()
    data = rechg_worker.load_glue_from_npy("..\GLUE.npy")

    tic = time.clock()
    glue_wl_viewer = ViewerWaterLevelGLUE()
    glue_wl_viewer.plot_prediction(data)
    glue_wl_viewer.show()
    print(time.clock()-tic)

    sys.exit(app.exec_())
