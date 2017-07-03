# -*- coding: utf-8 -*-
"""
Copyright 2014-2017 Jean-Sebastien Gosselin
email: jean-sebastien.gosselin@ete.inrs.ca

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

# Standard library imports :

from time import clock, sleep
import csv
import os
import datetime

# Third party imports :

import numpy as np
from PySide import QtGui, QtCore

import matplotlib as mpl
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT
import matplotlib.pyplot as plt

from xlrd import xldate_as_tuple
from xlrd.xldate import xldate_from_date_tuple
import xlsxwriter

# Local imports :

from gwrecharge_calc2 import SynthHydrograph
from gwrecharge_post import plot_rechg_GLUE

import common.database as db
import common.widgets as myqt
from common import IconDB, StyleDB, QToolButtonNormal
import brf_mod as bm

mpl.use('Qt4Agg')
mpl.rcParams['backend.qt4'] = 'PySide'
mpl.rc('font', **{'family': 'sans-serif', 'sans-serif': ['Arial']})


# =============================================================================


class WLCalc(myqt.DialogWindow):
    """
    This is the interface where are plotted the water level time series. It is
    possible to dynamically zoom and span the data, change the display,
    i.e. display the data as a continuous line or individual dot, perform a
    MRC and ultimately estimate groundwater recharge.
    """

    def __init__(self, datamanager, parent=None):
        super(WLCalc, self).__init__(parent, maximize=True)

        self.dmngr = datamanager
        self.dmngr.wldsetChanged.connect(self.set_wldset)
        self.dmngr.wxdsetChanged.connect(self.set_wxdset)

        self.isGraphExists = False
        self.__figbckground = None  # figure background
        self.__addPeakVisible = True

        # Water Level Time series :

        self.time = []
        self.txls = []  # time in Excel format
        self.tmpl = []  # time in matplotlib format
        self.water_lvl = []

        # Date System :

        t1 = xldate_from_date_tuple((2000, 1, 1), 0)  # time in Excel
        t2 = mpl.dates.date2num(datetime.datetime(2000, 1, 1))  # Time in
        self.dt4xls2mpl = t2-t1  # Delta between the datum of both date system

        # Date format: can either be 0 for Excel format or 1 for Matplotlib
        # format.

        self.dformat = 1

        # Recession Curve Parameters :

        self.A = None
        self.B = None
        self.RMSE = None
        self.hrecess = []

        self.peak_indx = np.array([]).astype(int)
        self.peak_memory = [np.array([]).astype(int)]

        # Barometric Response Function :

        self.brfperiod = [None, None]
        self.__brfcount = 0
        # self.config_brf = ConfigBRF()
        self.config_brf = bm.BRFManager(parent=self)

        # Soil Profiles :

        self.soilFilename = []
        self.SOILPROFIL = SoilProfil()

        # Recharge :

        self.rechg_setup_win = RechgSetupWin(self)

        self.synth_hydro_widg = SynthHydroWidg()
        self.synth_hydro_widg.hide()
        self.synth_hydro_widg.newHydroParaSent.connect(self.plot_synth_hydro)

        self.synth_hydrograph = SynthHydrograph()

        # INIT UI :

        self.__initFig__()
        self.__initUI__()
        self.setup_ax_margins(None)

    def __initFig__(self):  # =================================================

        # ----------------------------------------------------------- CANVAS --

        # Create a Qt figure canvas :

        self.fig = mpl.figure.Figure(facecolor='white')
        self.canvas = FigureCanvasQTAgg(self.fig)

        self.canvas.mpl_connect('button_press_event', self.onclick)
        self.canvas.mpl_connect('button_release_event', self.onrelease)
        self.canvas.mpl_connect('resize_event', self.setup_ax_margins)
        self.canvas.mpl_connect('motion_notify_event', self.mouse_vguide)
        self.canvas.mpl_connect('figure_leave_event', self.on_fig_leave)

        # ------------------------------------------------------------ FRAME --

        # Put figure canvas in a QFrame widget.

        self.fig_frame_widget = myqt.QFrameLayout()
        self.fig_frame_widget.addWidget(self.canvas, 0, 0)

        self.fig_frame_widget.setFrameStyle(StyleDB().frame)
        self.fig_frame_widget.setLineWidth(2)
        self.fig_frame_widget.setMidLineWidth(1)

        # ------------------------------------------------------------- AXES --

        # Water Level (Host) :
        ax0 = self.fig.add_axes([0, 0, 1, 1], zorder=100)
        ax0.patch.set_visible(False)
        ax0.invert_yaxis()

        # Precipitation :
        ax1 = ax0.twinx()
        ax1.patch.set_visible(False)
        ax1.set_zorder(50)
        ax1.set_navigate(False)
        ax1.invert_yaxis()
        ax1.axis(ymin=250, ymax=0)

        # --------------------------------------------------------- XTICKS ----

        ax0.xaxis.set_ticks_position('bottom')
        ax0.tick_params(axis='x', direction='out')

        # --------------------------------------------------------- YTICKS ----

        ax0.yaxis.set_ticks_position('left')
        ax0.tick_params(axis='y', direction='out')

        ax1.yaxis.set_ticks_position('right')
        ax1.tick_params(axis='y', direction='out')

        # --------------------------------------------------------- LABELS ----

        ax0.set_ylabel('Water level (mbgs)', fontsize=14, labelpad=25,
                       va='top', color='black')
        ax0.set_xlabel('Time (days)', fontsize=14, labelpad=25,
                       va='bottom', color='black')
        ax1.set_ylabel('Precipitation (mm)', fontsize=14, labelpad=25,
                       va='top', color='black', rotation=270)

        # ------------------------------------------------ Setup Gridlines ----

#        ax0.grid(axis='x', color=[0.35, 0.35, 0.35], ls='--')
#        ax0.set_axisbelow(True)

        # -------------------------------------------------------- ARTISTS ----

        # Water level :
        self.h1_ax0, = ax0.plot([], [], color='blue', clip_on=True, ls='-',
                                zorder=10, marker='None')

        # Recession :
        self.h3_ax0, = ax0.plot([], [], color='red', clip_on=True,
                                zorder=15, marker='None', linestyle='--')

        # Rain :
        self.h_rain, = ax1.plot([], [])

        # Ptot :
        self.h_ptot, = ax1.plot([], [])

        # ETP :
        self.h_etp, = ax1.plot([], [], color='#FF6666', lw=1.5, zorder=500)

        # BRF :
        self.h_brf1 = ax0.axvline(0, color='orange')
        self.h_brf2 = ax0.axvline(0, color='orange')

        # Vertical guide line under cursor :
        self.vguide = ax0.axvline(-1, color='red', zorder=40)
        self.vguide.set_visible(False)

        offset = mpl.transforms.ScaledTranslation(-5/72, 5/72,
                                                  self.fig.dpi_scale_trans)
        self.xcoord = ax0.text(1, 0, '', ha='right',
                               transform=ax0.transAxes + offset)
        self.xcoord.set_visible(False)

        # Peaks :
        self.h2_ax0, = ax0.plot([], [], color='white', clip_on=True,
                                zorder=30, marker='o', linestyle='None',
                                mec='red', mew=1.5)

        # Cross Remove Peaks :
        self.xcross, = ax0.plot(1, 0, color='red', clip_on=True,
                                zorder=20, marker='x', linestyle='None',
                                markersize=15, markeredgewidth=3)

    # =========================================================================

    def __initUI__(self):

        self.setWindowTitle('Hydrograph Analysis')

        # -------------------------------------------------------- TOOLBAR ----

        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.toolbar.hide()

        # Toolbar Buttons :

        self.btn_clearPeak = QToolButtonNormal(IconDB().clear_search)
        self.btn_clearPeak.setToolTip('Clear all extremum from the graph')
        self.btn_clearPeak.clicked.connect(self.clear_all_peaks)

        self.btn_home = QToolButtonNormal(IconDB().home)
        self.btn_home.setToolTip('Reset original view.')
        self.btn_home.clicked.connect(self.aToolbarBtn_isClicked)

        # self.btn_pan = QToolButtonNormal(IconDB().pan)
        # self.btn_pan.setToolTip('Pan axes with left mouse, zoom with right')
        # self.btn_pan.clicked.connect(self.aToolbarBtn_isClicked)

        self.btn_strati = QToolButtonNormal(IconDB().stratigraphy)
        self.btn_strati.setToolTip('Toggle on and off the display of the soil'
                                   ' stratigraphic layers')
        self.btn_strati.clicked.connect(self.btn_strati_isClicked)

        self.btn_Waterlvl_lineStyle = QToolButtonNormal(IconDB().showDataDots)
        self.btn_Waterlvl_lineStyle.setToolTip(
            '<p>Show water lvl data as dots instead of a continuous line</p>')
        self.btn_Waterlvl_lineStyle.clicked.connect(self.aToolbarBtn_isClicked)

        self.btn_dateFormat = QToolButtonNormal(IconDB().calendar)
        self.btn_dateFormat.setAutoRaise(1-self.dformat)
        self.btn_dateFormat.setToolTip('x axis label time format: '
                                       'date or MS Excel numeric')
        self.btn_dateFormat.clicked.connect(self.aToolbarBtn_isClicked)
        # dformat: 0 -> Excel Numeric Date Format
        #          1 -> Matplotlib Date Format

        # ---- recharge ----

        # self.btn_recharge = QToolButtonNormal(IconDB().recharge)
        # self.btn_recharge.setToolTip('Show window for recharge estimation')
        # self.btn_recharge.clicked.connect(self.rechg_setup_win.show)
        # self.btn_recharge.hide()

#        self.btn_synthHydro = QToolButtonNormal(IconDB().page_setup)
#        self.btn_synthHydro.setToolTip('Show synthetic hydrograph')
#        self.btn_synthHydro.clicked.connect(self.synth_hydro_widg.toggleOnOff)
#        self.btn_synthHydro.hide()

        # ---- BRF ----

#        self.btn_selBRF = QToolButtonNormal(IconDB().add_point)
#        self.btn_selBRF.clicked.connect(self.aToolbarBtn_isClicked)
#
#        self.btn_setBRF = QToolButtonNormal(IconDB().setup)
#        self.btn_setBRF.clicked.connect(self.config_brf.show)

#        self.btn_findPeak = toolBarBtn(iconDB.findPeak2, ttipDB.find_peak)
#        self.btn_findPeak.clicked.connect(self.find_peak)
#        self.btn_mrc2rechg = toolBarBtn(iconDB.mrc2rechg, ttipDB.mrc2rechg)
#        self.btn_mrc2rechg.clicked.connect(self.btn_mrc2rechg_isClicked)

        # Grid Layout :

        btn_list = [self.btn_home,
                    self.btn_Waterlvl_lineStyle,
                    self.btn_dateFormat]

        subgrid_toolbar = QtGui.QGridLayout()
        toolbar_widget = QtGui.QWidget()

        for col, btn in enumerate(btn_list):
            subgrid_toolbar.addWidget(btn, 0, col)
        subgrid_toolbar.setColumnStretch(col+1, 500)

        subgrid_toolbar.setSpacing(5)
        subgrid_toolbar.setContentsMargins(0, 0, 0, 0)

        toolbar_widget.setLayout(subgrid_toolbar)

        # ------------------------------------------------- MRC PARAMETERS ----

        self.MRC_type = QtGui.QComboBox()
        self.MRC_type.addItems(['Linear', 'Exponential'])
        self.MRC_type.setCurrentIndex(1)

        self.MRC_ObjFnType = QtGui.QComboBox()
        self.MRC_ObjFnType.addItems(['RMSE', 'MAE'])
        self.MRC_ObjFnType.setCurrentIndex(0)

        self.MRC_results = QtGui.QTextEdit()
        self.MRC_results.setReadOnly(True)
        self.MRC_results.setMinimumHeight(100)
        self.MRC_results.setMinimumWidth(100)

        sp = QtGui.QSizePolicy(QtGui.QSizePolicy.Ignored,
                               QtGui.QSizePolicy.MinimumExpanding)

        self.MRC_results.setSizePolicy(sp)

        # ---- MRC Toolbar ----

        self.btn_undo = QToolButtonNormal(IconDB().undo)
        self.btn_undo.setToolTip('Undo')
        self.btn_undo.setEnabled(False)
        self.btn_undo.clicked.connect(self.undo)

        self.btn_editPeak = QToolButtonNormal(IconDB().add_point)
        self.btn_editPeak.clicked.connect(self.aToolbarBtn_isClicked)
        self.btn_editPeak.setToolTip('<p>Toggle edit mode to manually'
                                     ' add extremums to the graph</p>')

        self.btn_delPeak = QToolButtonNormal(IconDB().erase)
        self.btn_delPeak.clicked.connect(self.aToolbarBtn_isClicked)
        self.btn_delPeak.setToolTip('<p>Toggle edit mode to manually remove '
                                    'extremums from the graph</p>')

        self.btn_save_interp = QToolButtonNormal(IconDB().save)
        self.btn_save_interp.setToolTip('Save Calculated MRC to file.')
        self.btn_save_interp.clicked.connect(self.aToolbarBtn_isClicked)

        self.btn_MRCalc = QtGui.QPushButton('Compute MRC')
        self.btn_MRCalc.clicked.connect(self.aToolbarBtn_isClicked)
        self.btn_MRCalc.setToolTip('<p>Calculate the Master Recession Curve'
                                   ' (MRC) for the selected time periods.</p>')

        mrc_tb = myqt.QFrameLayout()
        mrc_tb.addWidget(self.btn_undo, 0, 0)
        mrc_tb.addWidget(self.btn_clearPeak, 0, 1)
        mrc_tb.addWidget(self.btn_editPeak, 0, 2)
        mrc_tb.addWidget(self.btn_delPeak, 0, 3)
        mrc_tb.addWidget(self.btn_save_interp, 0, 4)
        mrc_tb.setColumnStretch(mrc_tb.columnCount(), 100)

        # ---- MRC Layout ----

        self.widget_MRCparam = myqt.QFrameLayout()
        self.widget_MRCparam.setContentsMargins(10, 10, 10, 10)

        row = 0
        self.widget_MRCparam.addWidget(QtGui.QLabel('MRC Type :'), row, 0)
        self.widget_MRCparam.addWidget(self.MRC_type, row, 1)
        row += 1
        self.widget_MRCparam.addWidget(self.MRC_results, row, 0, 1, 3)
        row += 1
        self.widget_MRCparam.addWidget(mrc_tb, row, 0, 1, 3)
        row += 1
        self.widget_MRCparam.setRowMinimumHeight(row, 15)
        self.widget_MRCparam.setRowStretch(row, 500)
        row += 1
        self.widget_MRCparam.addWidget(self.btn_MRCalc, row, 0, 1, 3)

        self.widget_MRCparam.setSpacing(5)
        self.widget_MRCparam.setColumnStretch(2, 500)

        # -------------------------------------------------- Tool Tab Area ----

        tooltab = QtGui.QTabWidget()
        tooltab.setIconSize(QtCore.QSize(28, 28))
        tooltab.setTabPosition(tooltab.North)

        tooltab.addTab(self.widget_MRCparam, IconDB().MRCalc, '')
        tooltab.addTab(self.rechg_setup_win, IconDB().recharge, '')
        tooltab.addTab(self.config_brf, IconDB().setup, '')

        # ---------------------------------------------------- Right Panel ----

        right_pan = myqt.QFrameLayout()

        row = 0
        right_pan.addWidget(self.dmngr, row, 0)
        row += 1
        right_pan.addWidget(tooltab, row, 0)
        row += 1
        right_pan.setRowStretch(row, 100)

        right_pan.setSpacing(15)

        # -------------------------------------------------------- MAIN GRID --

        mainGrid = QtGui.QGridLayout(self)

        mainGrid.addWidget(toolbar_widget, 0, 0)
        mainGrid.addWidget(self.fig_frame_widget, 1, 0)

        mainGrid.addWidget(myqt.VSep(), 0, 1, 2, 1)

        mainGrid.addWidget(right_pan, 0, 2, 2, 1)

        # items = [toolbar_widget, self.fig_frame_widget,
        #          self.synth_hydro_widg]
        # for row, item in enumerate(items):
        #     mainGrid.addWidget(item, row, 0)

        mainGrid.setContentsMargins(10, 10, 10, 10)  # (L, T, R, B)
        mainGrid.setHorizontalSpacing(15)
        mainGrid.setRowStretch(1, 500)
        mainGrid.setColumnStretch(0, 500)
        mainGrid.setColumnMinimumWidth(2, 250)

    # =========================================================================

    @property
    def wldset(self):
        return self.dmngr.get_current_wldset()

    @property
    def wxdset(self):
        return self.dmngr.get_current_wxdset()

    def set_wldset(self, wldset):
        self.config_brf.set_wldset(wldset)

        # Load Water Level Data :

        self.water_lvl = wldset['WL']
        self.time = wldset['Time']
        # self.soilFilename = self.waterLvl_data.soilFilename

        self.init_hydrograph()
        self.load_MRC_interp()

        # Reset UI :

        self.btn_Waterlvl_lineStyle.setAutoRaise(True)

    def set_wxdset(self, wxdset):
        self.plot_weather_data()

    # =========================================================================

    def plot_weather_data(self):
        if self.wxdset is None:
            return

        time = self.wxdset['Time'] + self.dt4xls2mpl*self.dformat
        ptot = self.wxdset['Ptot']
        rain = self.wxdset['Rain']
        etp = self.wxdset['PET']

        # ----------------------------------------------- Bin the Data ----

        bw = 7
        n = bw/2
        f = 0.65  # Space between individual bar.

        nbin = int(np.floor(len(time)/bw))

        time_bin = time[:nbin*bw].reshape(nbin, bw)
        time_bin = np.sum(time_bin, axis=1)/bw

        rain_bin = rain[:nbin*bw].reshape(nbin, bw)
        rain_bin = np.sum(rain_bin, axis=1)

        ptot_bin = ptot[:nbin*bw].reshape(nbin, bw)
        ptot_bin = np.sum(ptot_bin, axis=1)

        etp_bin = etp[:nbin*bw].reshape(nbin, bw)
        etp_bin = np.sum(etp_bin, axis=1)

        # --------------------------------------------- Generate Shape ----

        time_bar = np.zeros(len(time_bin) * 4)
        rain_bar = np.zeros(len(rain_bin) * 4)
        ptot_bar = np.zeros(len(ptot_bin) * 4)
        etp_bar = np.zeros(len(ptot_bin) * 3)
        time_bar2 = np.zeros(len(time_bin) * 3)

        time_bar[0::4] = time_bin - (n * f)
        time_bar[1::4] = time_bin - (n * f)
        time_bar[2::4] = time_bin + (n * f)
        time_bar[3::4] = time_bin + (n * f)

        rain_bar[0::4] = 0
        rain_bar[1::4] = rain_bin
        rain_bar[2::4] = rain_bin
        rain_bar[3::4] = 0

        ptot_bar[0::4] = 0
        ptot_bar[1::4] = ptot_bin
        ptot_bar[2::4] = ptot_bin
        ptot_bar[3::4] = 0

        time_bar2[0::3] = time_bin
        time_bar2[1::3] = time_bin
        time_bar2[2::3] = np.nan

        etp_bar[0::3] = 0
        etp_bar[1::3] = etp_bin
        etp_bar[2::3] = np.nan

        # -------------------------------------------------- Plot data ----

        ax = self.fig.axes[1]

        self.h_rain.remove()
        self.h_ptot.remove()

        self.h_rain = ax.fill_between(time_bar, 0., rain_bar,
                                      color='0.65', lw=0, zorder=100)

        self.h_ptot = ax.fill_between(time_bar, 0., ptot_bar,
                                      color='0.85', lw=0, zorder=50)

        self.h_etp.set_data(time_bar2, etp_bar)

        self.draw()

    # =========================================================================

    def aToolbarBtn_isClicked(self):
        # slot that redirects all clicked actions from the toolbar buttons

        if self.wldset is None:
            msg = 'Please import a valid water level dataset first.'
            self.emit_warning(msg)
            return

        sender = self.sender()
        if sender == self.btn_MRCalc:
            self.btn_MRCalc_isClicked()
        elif sender == self.btn_Waterlvl_lineStyle:
            self.change_waterlvl_lineStyle()
        elif sender == self.btn_home:
            self.home()
        elif sender == self.btn_save_interp:
            self.save_mrc_tofile()
        elif sender == self.btn_editPeak:
            self.add_peak()
        elif sender == self.btn_delPeak:
            self.delete_peak()
        elif sender == self.btn_dateFormat:
            self.switch_date_format()
        elif sender == self.btn_selBRF:
            self.select_BRF()

    # ================================================================ MRC ====

    def btn_MRCalc_isClicked(self):

        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

        A, B, hp, RMSE = mrc_calc(self.time, self.water_lvl, self.peak_indx,
                                  self.MRC_type.currentIndex())

        print('MRC Parameters: A=%f, B=%f' % (A, B))
        if A is None:
            QtGui.QApplication.restoreOverrideCursor()
            return

        # Display result :

        txt = '∂h/∂t (mm/d) = -%0.2f h + %0.2f' % (A*1000, B*1000)
        self.MRC_results.setText(txt)
        txt = '%s = %f m' % (self.MRC_ObjFnType.currentText(), RMSE)
        self.MRC_results.append(txt)
        self.MRC_results.append('\nwhere h is the depth to water '
                                'table in mbgs and ∂h/∂t is the recession '
                                'rate in mm/d.')

        # Store results in class attributes :

        self.A = A
        self.B = B
        self.RMSE = RMSE
        self.hrecess = hp

        # Store results in wldset :

        print('Saving MRC interpretation in dataset...')
        self.wldset.set_mrc(A, B, self.peak_indx, self.time, hp)

        # Plot result :

        self.draw_MRC()

        QtGui.QApplication.restoreOverrideCursor()

    # -------------------------------------------------------------------------

    def draw_MRC(self):
        tr = self.wldset['mrc/time']
        hr = self.wldset['mrc/recess']
        self.h3_ax0.set_ydata(hr)
        self.h3_ax0.set_xdata(tr + self.dt4xls2mpl * self.dformat)
        self.draw()

    # -------------------------------------------------------------------------

    def load_MRC_interp(self):
        if self.wldset.mrc_exists() is False:
            return

        self.peak_indx = self.wldset['mrc/peak_indx'].astype(int)
        self.peak_memory[0] = self.wldset['mrc/peak_indx'].astype(int)

        self.A, self.B = self.wldset['mrc/params']
        self.hrecess = self.wldset['mrc/recess']

        err = (self.wldset['mrc/recess']-self.water_lvl)**2
        self.RMSE = np.mean(err[~np.isnan(err)])**0.5

        # ---- Recalculate and Plot Results ----

        self.peak_memory[0] = self.peak_indx
        self.plot_peak()
        self.draw_MRC()

    # -------------------------------------------------------------------------

    def save_mrc_tofile(self):
        filename = self.wldset['Well'] + '.xlsx'

        # ---- get filename ----

        dialog = QtGui.QFileDialog()
        dialog.setConfirmOverwrite(True)
        filename, ftype = dialog.getSaveFileName(
            caption="Save Results Summary", dir=filename, filter=('*.xlsx'))

        if not filename:
            return

        root, ext = os.path.splitext(filename)
        if ext not in ['.xlsx', '.xls']:
            filename += '.xlsx'

        # ---- save MRC to file ----

        with xlsxwriter.Workbook(filename) as wb:
            ws = wb.add_worksheet()

            ws.set_column('A:A', 35)
            ws.set_column('B:B', 35)
            ws.set_column('C:C', 35)

            ws.write(0, 0, 'Well Name : %s' % self.wldset['Well'])
            ws.write(1, 0, 'Latitude : %f' % self.wldset['Latitude'])
            ws.write(2, 0, 'Longitude : %f' % self.wldset['Longitude'])
            ws.write(3, 0, 'Altitude : %f' % self.wldset['Elevation'])
            ws.write(4, 0, 'Municipality : %s' % self.wldset['Municipality'])

            A, B = self.wldset['mrc/params']

            ws.write(6, 0, 'dh/dt(mm/d) = -%f*h(mbgs) + %f' % (self.A, self.B))
            ws.write(7, 0, 'A (1/d)')
            ws.write(7, 1, self.A)
            ws.write(8, 0, 'B (m/d)')
            ws.write(8, 1, self.B)
            ws.write(9, 0, 'RMSE (m)')
            ws.write(9, 1, self.RMSE)

            ws.write(11, 0, 'Observed and Predicted Water Level')
            ws.write_row(12, 0, ['Time', 'hrecess(mbgs)', 'hobs(mbgs)'])
            print(len(self.time), len(self.hrecess), len(self.water_lvl))
            for i in range(len(self.time)):
                if np.isnan(self.hrecess[i]):
                    row = [self.time[i], 'nan', self.water_lvl[i]]
                else:
                    row = [self.time[i], self.hrecess[i], self.water_lvl[i]]
                ws.write_row(i+13, 0, row)

        print('MRC info saved sucessfully to file.')

    def btn_mrc2rechg_isClicked(self):
        if not self.A and not self.B:
            print('Need to calculate MRC equation first.')
            return

        if not os.path.exists(self.soilFilename):
            print('A ".sol" file is needed for the calculation of' +
                  ' groundwater recharge from the MRC')
            return

        self.SOILPROFIL.load_info(self.soilFilename)
        mrc2rechg(self.time, self.water_lvl, self.A, self.B,
                  self.SOILPROFIL.zlayer, self.SOILPROFIL.Sy)

    # =========================================================================

    def plot_BRFperiod(self):
        if self.brfperiod[0]:
            x = self.brfperiod[0] + self.dt4xls2mpl*self.dformat
            self.h_brf1.set_xdata(x)
            self.h_brf1.set_visible(True)
        else:
            self.h_brf1.set_visible(False)

        if self.brfperiod[1]:
            x = self.brfperiod[1] + self.dt4xls2mpl*self.dformat
            self.h_brf2.set_xdata(x)
            self.h_brf2.set_visible(True)
        else:
            self.h_brf2.set_visible(False)

        self.draw()

    def select_BRF(self):
        # slot connected when the button to select a period to compute the
        # BRF is clicked
        if self.btn_selBRF.autoRaise():
            self.btn_selBRF.setAutoRaise(False)
            self.brfperiod = [None, None]
            self.plot_BRFperiod()

            self.btn_pan.setAutoRaise(True)
            if self.toolbar._active == "PAN":
                self.toolbar.pan()

            self.btn_editPeak.setAutoRaise(True)
            self.btn_delPeak.setAutoRaise(True)
        else:
            self.btn_selBRF.setAutoRaise(True)

    # =========================================================================

    def plot_peak(self):
        if len(self.peak_memory) == 1:
            self.btn_undo.setEnabled(False)
        else:
            self.btn_undo.setEnabled(True)

        if self.isGraphExists is True:
            x = self.time[self.peak_indx] + (self.dt4xls2mpl * self.dformat)
            y = self.water_lvl[self.peak_indx]
            self.h2_ax0.set_data(x, y)

            # Take a screenshot of the background :
            self.draw()

    def find_peak(self):

        n_j, n_add = local_extrema(self.water_lvl, 4 * 5)

        # Removing first and last point if necessary to always start with a
        # maximum and end with a minimum.

        # WARNING: y axis is inverted. Consequently, the logic needs to be
        #          inverted also

        if n_j[0] > 0:
            n_j = np.delete(n_j, 0)

        if n_j[-1] < 0:
            n_j = np.delete(n_j, -1)

        self.peak_indx = np.abs(n_j).astype(int)
        self.peak_memory.append(self.peak_indx)

        self.plot_peak()

    def add_peak(self):
        # slot connected when the button to add new peaks is clicked.
        if self.isGraphExists is False:
            print('Graph is empty')
            self.emit_warning(
              'Please select a valid Water Level Data File first.')
            return

        if self.btn_editPeak.autoRaise():
            # Activate <add_peak>
            self.btn_editPeak.setAutoRaise(False)

            # Deactivate <delete_peak>
            self.btn_delPeak.setAutoRaise(True)
        else:
            # Deactivate <add_peak>
            self.btn_editPeak.setAutoRaise(True)

        # Draw to save background :
        self.draw()

    def delete_peak(self):
        if self.btn_delPeak.autoRaise():
            # Activate <delete_peak>
            self.btn_delPeak.setAutoRaise(False)

            # Deactivate <add_peak>
            self.btn_editPeak.setAutoRaise(True)
        else:
            # Deactivate <delete_peak>
            self.btn_delPeak.setAutoRaise(True)

        # Draw to save background :
        self.draw()

    def clear_all_peaks(self):
        if self.isGraphExists is False:
            print('Graph is empty')
            return

        self.peak_indx = np.array([]).astype(int)
        self.peak_memory.append(self.peak_indx)

        self.h3_ax0.set_data([], [])

        self.plot_peak()

    # =========================================================================

    def home(self):
        if self.isGraphExists is False:
            print('Graph is empty')
            return

        self.toolbar.home()
        self.draw()

    def undo(self):
        if self.isGraphExists is False:
            print('Graph is empty')
            return

        if len(self.peak_memory) > 1:
            self.peak_indx = self.peak_memory[-2]
            del self.peak_memory[-1]

            self.plot_peak()

            print('undo')
        else:
            pass

    # =========================================================================

    def setup_ax_margins(self, event):

        # Update axes :

        fheight = self.fig.get_figheight()
        fwidth = self.fig.get_figwidth()

        left_margin = 1. / fwidth
        right_margin = 1. / fwidth
        bottom_margin = 0.75 / fheight
        top_margin = 0.25 / fheight

        x0 = left_margin
        y0 = bottom_margin
        w = 1 - (left_margin + right_margin)
        h = 1 - (bottom_margin + top_margin)

        for axe in self.fig.axes:
            axe.set_position([x0, y0, w, h])

        self.draw()

    def switch_date_format(self):

        ax0 = self.fig.axes[0]

        # Change UI and System Variable State :

        if self.dformat == 0:    # 0 for Excel numeric date format
            self.btn_dateFormat.setAutoRaise(False)
            self.dformat = 1     # 1 for Matplotlib format
            print('switching to matplotlib date format')
        elif self.dformat == 1:  # 1 for Matplotlib format
            self.btn_dateFormat.setAutoRaise(True)
            self.dformat = 0     # 0 for Excel numeric date format
            print('switching to Excel numeric date format')

        # Change xtick Labels Date Format :

        if self.dformat == 1:
            xloc = mpl.dates.AutoDateLocator()
            ax0.xaxis.set_major_locator(xloc)
            xfmt = mpl.dates.AutoDateFormatter(xloc)
            ax0.xaxis.set_major_formatter(xfmt)
        elif self.dformat == 0:
            xfmt = mpl.ticker.ScalarFormatter()
            ax0.xaxis.set_major_formatter(xfmt)
            ax0.get_xaxis().get_major_formatter().set_useOffset(False)

        # Adjust Axis Range :

        xlim = ax0.get_xlim()
        if self.dformat == 1:
            ax0.set_xlim(xlim[0] + self.dt4xls2mpl, xlim[1] + self.dt4xls2mpl)
        elif self.dformat == 0:
            ax0.set_xlim(xlim[0] - self.dt4xls2mpl, xlim[1] - self.dt4xls2mpl)

        # Adjust Water Levels, Peak, MRC ant weather time frame :

        t = self.time + self.dt4xls2mpl * self.dformat
        self.h1_ax0.set_xdata(t)  # Water Levels

        if len(self.hrecess) > 0:  # MRC
            self.h3_ax0.set_xdata(t)

        if len(self.peak_indx) > 0:  # Peaks
            self.h2_ax0.set_xdata(self.time[self.peak_indx] +
                                  self.dt4xls2mpl * self.dformat)

        self.plot_weather_data()
        self.draw()

    # =========================================================================

    def init_hydrograph(self):

        ax0 = self.fig.axes[0]

        # ---- Reset UI ----

        self.peak_indx = np.array([]).astype(int)
        self.peak_memory = [np.array([]).astype(int)]
        self.btn_undo.setEnabled(False)

        # ---- PLot Data ----

        # Water Levels :

        y = self.water_lvl
        t = self.time + self.dt4xls2mpl * self.dformat

        self.h1_ax0.set_data(t, y)

        self.plt_wlpre, = ax0.plot([], [], color='red', clip_on=True,
                                   ls='-', zorder=10, marker='None')

        # Strati :

        if not self.btn_strati.autoRaise():
            self.display_soil_layer()

        # Setup Axis Range :

        y = self.water_lvl
        t = self.time + self.dt4xls2mpl * self.dformat

        delta = 0.05
        Xmin0 = np.min(t) - (np.max(t) - np.min(t)) * delta
        Xmax0 = np.max(t) + (np.max(t) - np.min(t)) * delta

        indx = np.where(~np.isnan(y))[0]
        Ymin0 = np.min(y[indx]) - (np.max(y[indx]) - np.min(y[indx])) * delta
        Ymax0 = np.max(y[indx]) + (np.max(y[indx]) - np.min(y[indx])) * delta

        ax0.axis([Xmin0, Xmax0, Ymax0, Ymin0])

        # Setup xtick Labels Date Format :

        if self.dformat == 1:  # matplotlib format
            xloc = mpl.dates.AutoDateLocator()
            ax0.xaxis.set_major_locator(xloc)
            xfmt = mpl.dates.AutoDateFormatter(xloc)
            ax0.xaxis.set_major_formatter(xfmt)
        elif self.dformat == 0:  # excel format
            xfmt = mpl.ticker.ScalarFormatter()
            ax0.xaxis.set_major_formatter(xfmt)
            ax0.get_xaxis().get_major_formatter().set_useOffset(False)

        # Draw the Graph :

        self.isGraphExists = True
        self.draw()

    # =========================================================================

    def plot_synth_hydro(self, parameters):
        print(parameters)
        Cro = parameters['Cro']
        RASmax = parameters['RASmax']
        Sy = parameters['Sy']
#        parameters['jack']

        # ----------------------------------------------- compute recharge ----

        rechg, _, _, _, _ = \
            self.synth_hydrograph.surf_water_budget(Cro, RASmax)

        # ------------------------------------------- compute water levels ----

        tweatr = self.wxdset['Time'] + 0  # Here we introduce the time lag
        twlvl = self.time

        ts = np.where(twlvl[0] == tweatr)[0][0]
        te = np.where(twlvl[-1] == tweatr)[0][0]

        WLpre = self.synth_hydrograph.calc_hydrograph(rechg[ts:te], Sy)

        # ---------------------------------------------- plot water levels ----

        self.plt_wlpre.set_data(self.synth_hydrograph.DATE, WLpre/1000.)

        self.draw()

    # =========================================================================

    def btn_strati_isClicked(self):

        # Checks :

        if self.isGraphExists is False:
            print('Graph is empty.')
            self.btn_strati.setAutoRaise(True)
            return

        # Attribute Action :

        if self.btn_strati.autoRaise():
            self.btn_strati.setAutoRaise(False)
            self.display_soil_layer()
        else:
            self.btn_strati.setAutoRaise(True)
            self.hide_soil_layer()

    def hide_soil_layer(self):

        for i in range(len(self.zlayer)):
            self.layers[i].remove()
            self.stratLines[i].remove()
        self.stratLines[i+1].remove()

        self.draw()

    def display_soil_layer(self):

        # Check :

        if not os.path.exists(self.soilFilename):
            print('No ".sol" file found for this well.')
            self.btn_strati.setAutoRaise(True)
            return

        # Load soil column info :

        with open(self.soilFilename, 'r') as f:
            reader = list(csv.reader(f, delimiter="\t"))

        NLayer = len(reader)

        self.zlayer = np.empty(NLayer).astype(float)
        self.soilName = np.empty(NLayer).astype(str)
        self.Sy = np.empty(NLayer).astype(float)
        self.soilColor = np.empty(NLayer).astype(str)

        for i in range(NLayer):
            self.zlayer[i] = reader[i][0]
            self.soilName[i] = reader[i][1]
            self.Sy[i] = reader[i][2]
            try:
                self.soilColor[i] = reader[i][3]
                print(reader[i][3])
            except:
                self.soilColor[i] = '#FFFFFF'

        print(self.soilColor)

        # Plot layers and lines :

        self.layers = [0] * len(self.zlayer)
        self.stratLines = [0] * (len(self.zlayer)+1)

        up = 0
        self.stratLines[0], = self.ax0.plot([0, 99999], [up, up],
                                            color="black",
                                            linewidth=1)
        for i in range(len(self.zlayer)):

            down = self.zlayer[i]

            self.stratLines[i+1], = self.ax0.plot([0, 99999], [down, down],
                                                  color="black",
                                                  linewidth=1)
            try:
                self.layers[i] = self.ax0.fill_between(
                    [0, 99999], up, down, color=self.soilColor[i], zorder=0)
            except:
                self.layers[i] = self.ax0.fill_between(
                    [0, 99999], up, down, color='#FFFFFF', zorder=0)

            up = down

        self.draw()

    # ============================================== Water Level Linestyle ====

    def change_waterlvl_lineStyle(self):
        if self.btn_Waterlvl_lineStyle.autoRaise():
            self.btn_Waterlvl_lineStyle.setAutoRaise(False)

            self.h1_ax0.set_linestyle('None')
            self.h1_ax0.set_marker('.')
            self.h1_ax0.set_markerfacecolor('blue')
            self.h1_ax0.set_markeredgewidth(1.5)
            self.h1_ax0.set_markeredgecolor('blue')
            self.h1_ax0.set_markersize(5)
        else:
            self.btn_Waterlvl_lineStyle.setAutoRaise(True)
            self.h1_ax0.set_linestyle('-')
            self.h1_ax0.set_marker('None')
        self.draw()

    # ======================================================== Mouse Event ====

    def draw(self):
        self.vguide.set_visible(False)
        self.xcoord.set_visible(False)
        self.xcross.set_visible(False)

        self.canvas.draw()
        self.__figbckground = self.fig.canvas.copy_from_bbox(self.fig.bbox)

    # -------------------------------------------------------------------------

    def on_fig_leave(self, event):
        self.draw()

    # -------------------------------------------------------------------------

    def mouse_vguide(self, event):
        if self.isGraphExists is False:
            return

        # if not self.btn_pan.autoRaise():
        #    return

        if self.toolbar._active == "PAN":
            return

        ax0 = self.fig.axes[0]
        fig = self.fig

        # Restore background:

        fig.canvas.restore_region(self.__figbckground)

        # ----- Draw vertical guide ----

        # Trace a red vertical guide (line) that folows the mouse marker :

        x = event.xdata
        if x:
            self.vguide.set_visible(True)
            self.vguide.set_xdata(x)
            ax0.draw_artist(self.vguide)

            self.xcoord.set_visible(True)
            if self.dformat == 0:
                self.xcoord.set_text('%d' % x)
            else:
                date = xldate_as_tuple(x-self.dt4xls2mpl, 0)
                yyyy = date[0]
                mm = date[1]
                dd = date[2]
                self.xcoord.set_text('%02d/%02d/%d' % (dd, mm, yyyy))
            ax0.draw_artist(self.xcoord)
        else:
            self.vguide.set_visible(False)
            self.xcoord.set_visible(False)

        # ---- Remove Peak Cursor ----

        if not self.btn_delPeak.autoRaise() and len(self.peak_indx) > 0:

            # For deleting peak in the graph. Will put a cross on top of the
            # peak to delete if some proximity conditions are met.

            x = event.x
            y = event.y

            xpeak = self.time[self.peak_indx] + self.dt4xls2mpl * self.dformat
            ypeak = self.water_lvl[self.peak_indx]

            xt = np.empty(len(xpeak))
            yt = np.empty(len(ypeak))

            for i, (xp, yp) in enumerate(zip(xpeak, ypeak)):
                xt[i], yt[i] = ax0.transData.transform((xp, yp))

            d = ((xt - x)**2 + (yt - y)**2)**0.5
            if np.min(d) < 15:  # put the cross over the nearest peak
                indx = np.argmin(d)
                self.xcross.set_xdata(xpeak[indx])
                self.xcross.set_ydata(ypeak[indx])
                self.xcross.set_visible(True)
            else:
                self.xcross.set_visible(False)
        else:
            self.xcross.set_visible(False)

        ax0.draw_artist(self.xcross)

        # ---- Update Canvas ----

        self.fig.canvas.blit()

    # -------------------------------------------------------------------------

    def onrelease(self, event):
        if self.btn_delPeak.autoRaise() and self.btn_editPeak.autoRaise():
            if self.toolbar._active == 'PAN':
                self.toolbar.pan()
                self.draw()
                QtGui.QApplication.restoreOverrideCursor()
                self.mouse_vguide(event)
            return

        if event.button != 1:
            return

        self.__addPeakVisible = True
        self.plot_peak()

    # -------------------------------------------------------------------------

    def onclick(self, event):
        x, y = event.x, event.y
        if x is None or y is None:
            return

        ax0 = self.fig.axes[0]

        # www.github.com/eliben/code-for-blog/blob/master/2009/qt_mpl_bars.py

        if not self.btn_delPeak.autoRaise():
            if len(self.peak_indx) == 0:
                return

            xt = np.empty(len(self.peak_indx))
            yt = np.empty(len(self.peak_indx))
            xpeak = self.time[self.peak_indx] + self.dt4xls2mpl * self.dformat
            ypeak = self.water_lvl[self.peak_indx]

            for i in range(len(self.peak_indx)):
                xt[i], yt[i] = ax0.transData.transform((xpeak[i], ypeak[i]))

            r = ((xt - x)**2 + (yt - y)**2)**0.5
            if np.min(r) < 15:
                indx = np.argmin(r)

                # Update the plot :
                self.xcross.set_xdata(xpeak[indx])
                self.xcross.set_ydata(ypeak[indx])

                # Remove peak from peak index sequence :
                self.peak_indx = np.delete(self.peak_indx, indx)
                self.peak_memory.append(self.peak_indx)

                xpeak = np.delete(xpeak, indx)
                ypeak = np.delete(ypeak, indx)

                # hide the cross outside of the plotting area :
                self.xcross.set_visible(False)
                self.plot_peak()

        elif not self.btn_editPeak.autoRaise():
            xclic = event.xdata
            if xclic is None:
                return

            # http://matplotlib.org/examples/pylab_examples/cursor_demo.html

            x = self.time + self.dt4xls2mpl * self.dformat
            y = self.water_lvl

            d = np.abs(xclic - x)
            indx = np.argmin(d)

            if len(self.peak_indx) > 0:
                if indx in self.peak_indx:
                    print('There is already a peak at this time.')
                    return

                if np.min(np.abs(x[self.peak_indx] - x[indx])) < 1:
                    print('There is a peak at less than 1 days.')
                    return

            self.peak_indx = np.append(self.peak_indx, indx)
            self.peak_memory.append(self.peak_indx)

            self.__addPeakVisible = False
            self.draw()
        else:
            if self.toolbar._active is None:
                self.toolbar.pan()
                self.draw()
                QtGui.QApplication.setOverrideCursor(QtCore.Qt.SizeAllCursor)
                self.toolbar.press_pan(event)

            # ------- Select BRF period ----

#        elif not self.btn_selBRF.autoRaise():
#            xclic = event.xdata
#            if xclic is None:
#                return
#            x = self.time + self.dt4xls2mpl * self.dformat
#            y = self.water_lvl
#
#            d = np.abs(xclic - x)
#            indx = np.argmin(d)
#            if len(self.peak_indx) > 0:
#                if indx in self.peak_indx:
#                    print('There is already a peak at this time.')
#                    return
#
#                if np.min(np.abs(x[self.peak_indx] - x[indx])) < 3:
#                    print('There is a peak at less than 3 days.')
#                    return
#
#            self.brfperiod[self.__brfcount] = self.time[indx]
#            if self.__brfcount == 0:
#                self.__brfcount += 1
#                self.plot_BRFperiod()
#            elif self.__brfcount == 1:
#                self.__brfcount = 0
#                self.select_BRF()
#                self.plot_BRFperiod()
#            else:
#                raise ValueError('Something is wrong in the code')
#
#            print(self.brfperiod)

# =============================================================================


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

    N = len(x)

    ni = 0
    nf = N - 1

    # ------------------------------------------------------------ PLATEAU ----

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
        print('At least 1 plateau has been detected in the data')
        for i in range(N-1):
            if x[i+1] == x[i]:
                n1[i+1] = n1[i]
                n2[n1[i+1]:i+1] = i+1

    # ------------------------------------------------------ MAIN FUNCTION ----

    # the iterative algorithm presented in Appendix E of [ATE]

    # Time step up to which the time series has been analyzed ([ATE] p. 127)
    nc = 0

    Jest = 0  # number of local extrema of the partition of scale DeltaN
    iadd = 0  # number of additional local extrema
    flagante = 0

    # order number of the additional local extrema between all the local
    # extrema
    kadd = []

    n_j = []   # positions of the local extrema of a partition of scale Deltan

    while nc < nf:

        # the next extremum is searched within the interval [nc, nlim]

        nlim = min(nc + Deltan, nf)

        # ------------------------------------------------- SEARCH FOR MIN ----

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

        # --------------------------------------------------- SEARCH FOR MAX --

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
            flagmax = 0

        # ------------------------------------------------------- MIN or MAX --

        # The extremum closest to nc is kept for analysis
        if flagmin == 1 and flagmax == 1:
            if nmin < nmax:
                flagmax = 0
            else:
                flagmin = 0

        # ---------------------------------------------- ANTERIOR EXTREMUM ----

        if flagante == 0:  # No ANTERIOR extremum

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

            else:  # No extremum

                nc = nc + Deltan

        elif flagante == -1:  # ANTERIOR extremum is an MINIMUM

            tminante = np.abs(n_j[-1])
            xminante = x[tminante]

            if flagmax == 1:  # CURRENT extremum is a MAXIMUM

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
                    n_j = np.append(n_j, np.floor((n1[nmaxx] + n2[nmaxx])/2))
                    Jest += 1

                    kadd = np.append(kadd, Jest-1)
                    iadd += 1

            elif flagmin == 1:
                # CURRENT extremum is also a MINIMUM an additional maximum
                # is added ([ATE] p. 82)

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

        else:  # ANTERIOR extremum is a MAXIMUM

            tmaxante = np.abs(n_j[-1])
            xmaxante = x[tmaxante]

            if flagmin == 1:  # CURRENT extremum is a MINIMUM

                if xmaxante > xmin:

                    nc = n1[nmin] + 1
                    flagante = -1

                    n_j = np.append(n_j, -np.floor((n1[nmin] + n2[nmin])/2))
                    Jest += 1

                else:
                    # CURRENT MINIMUM is larger than the ANTERIOR MAXIMUM:
                    # an additional minimum is added ([ATE] p. 82 and 83)

                    xminn = np.min(x[tmaxante:nmin+1])
                    nminn = np.where(x[tmaxante:nmin+1] == xminn)[0][0]
                    nminn += tmaxante

                    nc = n1[nminn] + 1
                    flagante = -1

                    n_j = np.append(n_j, -np.floor((n1[nminn] + n2[nminn])/2))
                    Jest = Jest + 1

                    kadd = np.append(kadd, Jest-1)
                    iadd += 1

            elif flagmax == 1:
                # CURRENT extremum is also an MAXIMUM:
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
#        if n1[nj1] > ni:
    # the boundary ni is not included in the plateau
    # containing the first local extremum at n_j[1] and it
    # is added as an additional local extremum ([ATE] p. 83)
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


# =============================================================================


def mrc_calc(t, h, ipeak, MRCTYPE=1):
    """
    Calculate the equation parameters of the Master Recession Curve (MRC) of
    the aquifer from the water level time series using a modified Gauss-Newton
    optimization method.

    INPUTS
    ------
    h : water level time series in mbgs
    t : time in days
    ipeak: sequence of indices where the maxima and minima are located in h

    MRCTYPE: MRC equation type
             MODE = 0 -> linear (dh/dt = b)
             MODE = 1 -> exponential (dh/dt = -a*h + b)

    """

    A, B, hp, RMSE = None, None, None, None

    # ------------------------------------------------------- Check MinMax ----

    if len(ipeak) == 0:
        print('No extremum selected')
        return A, B, hp, RMSE

    ipeak = np.sort(ipeak)
    maxpeak = ipeak[:-1:2]
    minpeak = ipeak[1::2]
    dpeak = (h[maxpeak] - h[minpeak]) * -1  # WARNING: Don't forget it is mbgs

    if np.any(dpeak < 0):
        print('There is a problem with the pair-ditribution of min-max')
        return A, B, hp, RMSE

    # ------------------------------------------------------- Optimization ----

    print('\n---- MRC calculation started ----\n')
    print('MRCTYPE = %s' % (['Linear', 'Exponential'][MRCTYPE]))

    tstart = clock()

    # If MRCTYPE is 0, then the parameter A is kept to a value of 0 throughout
    # the entire optimization process and only paramter B is optimized.

    dt = np.diff(t)
    tolmax = 0.001

    A = 0.
    B = np.mean((h[maxpeak]-h[minpeak]) / (t[maxpeak]-t[minpeak]))

    hp = calc_synth_hydrograph(A, B, h, dt, ipeak)
    tindx = np.where(~np.isnan(hp*h))
    # indexes where there is a valid data inside a recession period

    RMSE = np.sqrt(np.mean((h[tindx]-hp[tindx])**2))
    print('A = %0.3f ; B= %0.3f; RMSE = %f' % (A, B, RMSE))

    # NP: number of parameters
    if MRCTYPE == 0:
        NP = 1
    elif MRCTYPE == 1:
        NP = 2

    while 1:
        # Calculating Jacobian (X) Numerically :

        hdB = calc_synth_hydrograph(A, B + tolmax, h, dt, ipeak)
        XB = (hdB[tindx] - hp[tindx]) / tolmax

        if MRCTYPE == 1:
            hdA = calc_synth_hydrograph(A + tolmax, B, h, dt, ipeak)
            XA = (hdA[tindx] - hp[tindx]) / tolmax
            Xt = np.vstack((XA, XB))
        elif MRCTYPE == 0:
            Xt = XB

        X = Xt.transpose()

        # Solving Linear System :

        dh = h[tindx] - hp[tindx]
        XtX = np.dot(Xt, X)
        Xtdh = np.dot(Xt, dh)

        # Scaling :

        C = np.dot(Xt, X) * np.identity(NP)
        for j in range(NP):
            C[j, j] = C[j, j] ** -0.5

        Ct = C.transpose()
        Cinv = np.linalg.inv(C)

        # Constructing right hand side :

        CtXtdh = np.dot(Ct, Xtdh)

        # Constructing left hand side :

        CtXtX = np.dot(Ct, XtX)
        CtXtXC = np.dot(CtXtX, C)

        m = 0
        while 1:  # loop for the Marquardt parameter (m)

            # Constructing left hand side (continued) :

            CtXtXCImr = CtXtXC + np.identity(NP) * m
            CtXtXCImrCinv = np.dot(CtXtXCImr, Cinv)

            # Calculating parameter change vector :

            dr = np.linalg.tensorsolve(CtXtXCImrCinv, CtXtdh, axes=None)

            # Checking Marquardt condition :

            NUM = np.dot(dr.transpose(), CtXtdh)
            DEN1 = np.dot(dr.transpose(), dr)
            DEN2 = np.dot(CtXtdh.transpose(), CtXtdh)

            cos = NUM / (DEN1 * DEN2)**0.5
            if np.abs(cos) < 0.08:
                m = 1.5 * m + 0.001
            else:
                break

        # Storing old parameter values :

        Aold = np.copy(A)
        Bold = np.copy(B)
        RMSEold = np.copy(RMSE)

        while 1:  # Loop for Damping (to prevent overshoot)

            # Calculating new parameter values :

            if MRCTYPE == 1:
                A = Aold + dr[0]
                B = Bold + dr[1]
            elif MRCTYPE == 0:
                B = Bold + dr[0, 0]

            # Applying parameter bound-constraints :

            A = np.max((A, 0))  # lower bound

            # Solving for new parameter values :

            hp = calc_synth_hydrograph(A, B, h, dt, ipeak)
            RMSE = np.sqrt(np.mean((h[tindx]-hp[tindx])**2))

            # Checking overshoot :

            if (RMSE - RMSEold) > 0.001:
                dr = dr * 0.5
            else:
                break

        # Checking tolerance :

        tolA = np.abs(A - Aold)
        tolB = np.abs(B - Bold)
        tol = np.max((tolA, tolB))
        if tol < tolmax:
            break

    tend = clock()
    print('TIME = %0.3f sec' % (tend-tstart))
    print('\n---- FIN ----\n')

    return A, B, hp, RMSE


def calc_synth_hydrograph(A, B, h, dt, ipeak):
    """
    Compute synthetic hydrograph with a time-forward implicit numerical scheme
    during periods where the water level recedes identified by the "ipeak"
    pointers.

    This is documented in logbook#10 p.79-80, 106.
    """

    # Time indexes delimiting periods where water level recedes :

    maxpeak = ipeak[:-1:2]
    minpeak = ipeak[1::2]
    nsegmnt = len(minpeak)

    hp = np.ones(len(h)) * np.nan
    for i in range(nsegmnt):
        hp[maxpeak[i]] = h[maxpeak[i]]
        for j in range(minpeak[i] - maxpeak[i]):
            imax = maxpeak[i]

            LUMP1 = (1 - A*dt[imax+j]/2)
            LUMP2 = B*dt[imax+j]
            LUMP3 = (1 + A*dt[imax+j]/2)**-1

            hp[imax+j+1] = (LUMP1 * hp[imax+j] + LUMP2) * LUMP3

    return hp


# =============================================================================


class SoilProfil():
    """
    zlayer = Position of the layer boundaries in mbgs where 0 is the ground
             surface. There is one more element in zlayer than the total number
             of layer.

    soilName = Soil texture description.

    Sy = Soil specific yield.
    """

    def __init__(self):

        self.zlayer = []
        self.soilName = []
        self.Sy = []
        self.color = []

    def load_info(self, filename):

        # ---- load soil column info ----

        with open(filename, 'r') as f:
            reader = list(csv.reader(f, delimiter="\t"))

        NLayer = len(reader)

        self.zlayer = np.empty(NLayer+1).astype(float)
        self.soilName = np.empty(NLayer).astype(str)
        self.Sy = np.empty(NLayer).astype(float)
        self.color = np.empty(NLayer).astype(str)

        self.zlayer[0] = 0
        for i in range(NLayer):
            self.zlayer[i+1] = reader[i][0]
            self.soilName[i] = reader[i][1]
            self.Sy[i] = reader[i][2]
            try:
                self.color[i] = reader[i][3]
            except:
                self.color[i] = '#FFFFFF'


# =============================================================================


def mrc2rechg(t, ho, A, B, z, Sy):
    """
    Calculate groundwater recharge from the Master Recession Curve (MRC)
    equation defined by the parameters A and B, the water level time series
    in mbgs (t and ho) and the soil column description (z and Sy), using
    the water-level fluctuation principle.

    INPUTS
    ------
    {1D array} t : Time in days
    {1D array} ho = Observed water level in mbgs
    {float}    A = Model parameter of the MRC
    {float}    B = Model parameter of the MRC
    {1D array} z = Depth of the soil layer limits
    {1D array} Sy = Specific yield for each soil layer
    {1D array} indx = Time index defining the periods over which recharge
                      is to be computed. Odd index numbers are for the
                      beginning of periods while even index numbers are for
                      the end of periods.

    OUTPUTS
    -------
    {1D array} RECHG = Groundwater recharge time series in m

    Note: This is documented in logbook #11, p.23.
    """

    print(z)
    print(Sy)

    # ---- Check Data Integrity ----

    if np.min(ho) < 0:
        print('Water level rise above ground surface. Please check your data.')
        return

    dz = np.diff(z)  # Tickness of soil layer
    print(dz)

    dt = np.diff(t)
    RECHG = np.zeros(len(dt))

    # !Do not forget it is mbgs. Everything is upside down!

    for i in range(len(dt)):

        # Calculate projected water level at i+1

        LUMP1 = 1 - A * dt[i] / 2
        LUMP2 = B * dt[i]
        LUMP3 = (1 + A * dt[i] / 2) ** -1

        hp = (LUMP1 * ho[i] + LUMP2) * LUMP3

        # Calculate resulting recharge over dt (See logbook #11, p.23)

        hup = min(hp, ho[i+1])
        hlo = max(hp, ho[i+1])

        iup = np.where(hup >= z)[0][-1]
        ilo = np.where(hlo >= z)[0][-1]

        RECHG[i] = np.sum(dz[iup:ilo+1] * Sy[iup:ilo+1])
        RECHG[i] -= (z[ilo+1] - hlo) * Sy[ilo]
        RECHG[i] -= (hup - z[iup]) * Sy[iup]

        RECHG[i] *= np.sign(hp - ho[i+1])

        # RECHG[i] will be positive in most cases. In theory, it should always
        # be positive, but error in the MRC and noise in the data can cause hp
        # to be above ho in some cases.

    print("Recharge = %0.2f m" % np.sum(RECHG))

    return RECHG


# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


class SynthHydroWidg(QtGui.QWidget):

    newHydroParaSent = QtCore.Signal(dict)

    def __init__(self, parent=None):
        super(SynthHydroWidg, self).__init__(parent)

        self.__initUI__()

    def __initUI__(self):

        class HSep(QtGui.QFrame):  # horizontal separators for the toolbar
            def __init__(self, parent=None):
                super(HSep, self).__init__(parent)
                self.setFrameStyle(db.styleUI().HLine)

        class MyQDSpin(QtGui.QDoubleSpinBox):
            def __init__(self, step, min, max, dec, val,
                         suffix=None, parent=None):
                super(MyQDSpin, self).__init__(parent)

                self.setSingleStep(step)
                self.setMinimum(min)
                self.setMaximum(max)
                self.setDecimals(dec)
                self.setValue(val)
                self.setAlignment(QtCore.Qt.AlignCenter)
                if suffix:
                    self.setSuffix(' %s' % suffix)
                if parent:
                    self.valueChanged.connect(parent.param_changed)

        self.QSy = MyQDSpin(0.001, 0.005, 0.95, 3, 0.2, parent=self)
        self.QRAS = MyQDSpin(1, 0, 1000, 0, 100, 'mm', parent=self)
        self.CRO = MyQDSpin(0.001, 0, 1, 3, 0.3, parent=self)

        self.Tcrit = MyQDSpin(0.1, -25, 25, 1, 0, '°C', parent=self)
        self.Tmelt = MyQDSpin(0.1, -25, 25, 1, 0, '°C', parent=self)
        self.CM = MyQDSpin(0.1, 0, 100, 1, 2.7, 'mm/°C', parent=self)

        main_grid = QtGui.QGridLayout()

        items = [QtGui.QLabel('Sy:'), self.QSy,
                 QtGui.QLabel('Rasmax:'), self.QRAS,
                 QtGui.QLabel('Cro:'), self.CRO,
                 QtGui.QLabel('Tcrit:'), self.Tcrit,
                 QtGui.QLabel('Tmelt:'), self.Tmelt,
                 QtGui.QLabel('CM:'), self.CM]

        for col, item in enumerate(items):
            main_grid.addWidget(item, 1, col)
#        main_grid.addWidget(HSep(), 0, 0, 1, col+1)

        main_grid.setColumnStretch(col+1, 100)
        main_grid.setContentsMargins(0, 0, 0, 0)

        self.setLayout(main_grid)

    # =========================================================================

    def get_parameters(self):
        parameters = {'Sy': self.QSy.value(),
                      'RASmax': self.QRAS.value(),
                      'Cro': self.CRO.value()}

        return parameters

    def param_changed(self):
        self.newHydroParaSent.emit(self.get_parameters())

    # =========================================================================

    def toggleOnOff(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.newHydroParaSent.emit(self.get_parameters())


# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


class RechgSetupWin(myqt.DialogWindow):

    def __init__(self, parent):
        super(RechgSetupWin, self).__init__(parent)

        self.setWindowTitle('Recharge Calibration Setup')
        self.setWindowFlags(QtCore.Qt.Window)

        self.__initUI__()

    def __initUI__(self):

        class QRowLayout(QtGui.QWidget):
            def __init__(self, items, parent=None):
                super(QRowLayout, self).__init__(parent)

                layout = QtGui.QGridLayout()
                for col, item in enumerate(items):
                    layout.addWidget(item, 0, col)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setColumnStretch(0, 100)
                self.setLayout(layout)

        # ---------------------------------------------------------- Toolbar --

        toolbar_widget = QtGui.QWidget()

        btn_calib = QtGui.QPushButton('Compute Recharge')
        btn_calib.clicked.connect(self.btn_calibrate_isClicked)

        # btn_cancel = QtGui.QPushButton('Cancel')
        # btn_cancel.clicked.connect(self.close)

        toolbar_layout = QtGui.QGridLayout()

        toolbar_layout.addWidget(btn_calib, 0, 0)

        # toolbar_layout.setColumnStretch(2, 100)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)  # (L, T, R, B)

        toolbar_widget.setLayout(toolbar_layout)

        # ------------------------------------------------------- Parameters --

        # Specific yield (Sy) :

        self.QSy_min = myqt.QDoubleSpinBox(0.2, 3)
        self.QSy_min.setRange(0.001, 1)

        self.QSy_max = myqt.QDoubleSpinBox(0.3, 3)
        self.QSy_max.setRange(0.001, 1)

        # Maximum readily available water (RASmax) :

        # units=' mm'

        self.QRAS_min = myqt.QDoubleSpinBox(40)
        self.QRAS_min.setRange(0, 999)

        self.QRAS_max = myqt.QDoubleSpinBox(120)
        self.QRAS_max.setRange(0, 999)
        self.QRAS_max.setValue(120)

        # Runoff coefficient (Cro) :

        self.CRO_min = myqt.QDoubleSpinBox(0.2, 3)
        self.CRO_min.setRange(0, 1)

        self.CRO_max = myqt.QDoubleSpinBox(0.4, 3)
        self.CRO_max.setRange(0, 1)

        # Snowmelt parameters :

        # units=' °C'

        self._Tcrit = myqt.QDoubleSpinBox(0, 1, )
        self._Tcrit.setRange(-25, 25)

        self._Tmelt = myqt.QDoubleSpinBox(0, 1)
        self._Tmelt.setRange(-25, 25)

        # units=' mm/°C'

        self._CM = myqt.QDoubleSpinBox(4, 1, 0.1, )
        self._CM.setRange(0.1, 100)

        # units=' days'

        self._deltaT = myqt.QDoubleSpinBox(0, 0, )
        self._deltaT.setRange(0, 999)

        qtitle = QtGui.QLabel('Range')
        qtitle.setAlignment(QtCore.Qt.AlignCenter)

        class QLabelCentered(QtGui.QLabel):
            def __init__(self, text):
                super(QLabelCentered, self).__init__(text)
                self.setAlignment(QtCore.Qt.AlignCenter)

        # ---- Layout ----

        mainLayout = QtGui.QGridLayout(self)

        row = 0
        mainLayout.addWidget(qtitle, row, 1, 1, 3)
        row += 1
        mainLayout.addWidget(myqt.HSep(), row, 0, 1, 5)
        row += 1
        mainLayout.addWidget(QtGui.QLabel('Sy :'), row, 0)
        mainLayout.addWidget(self.QSy_min, row, 1)
        mainLayout.addWidget(QLabelCentered('to'), row, 2)
        mainLayout.addWidget(self.QSy_max, row, 3)
        row += 1
        mainLayout.addWidget(QtGui.QLabel('RAS<sub>max</sub> :'), row, 0)
        mainLayout.addWidget(self.QRAS_min, row, 1)
        mainLayout.addWidget(QLabelCentered('to'), row, 2)
        mainLayout.addWidget(self.QRAS_max, row, 3)
        mainLayout.addWidget(QtGui.QLabel('mm'), row, 4)
        row += 1
        mainLayout.addWidget(QtGui.QLabel('Cro :'), row, 0)
        mainLayout.addWidget(self.CRO_min, row, 1)
        mainLayout.addWidget(QLabelCentered('to'), row, 2)
        mainLayout.addWidget(self.CRO_max, row, 3)
        row += 1
        mainLayout.addWidget(myqt.HSep(), row, 0, 1, 5)
        row += 1
        mainLayout.addWidget(QtGui.QLabel('Tcrit :'), row, 0)
        mainLayout.addWidget(self._Tcrit, row, 1)
        mainLayout.addWidget(QtGui.QLabel('°C'), row, 2, 1, 3)
        row += 1
        mainLayout.addWidget(QtGui.QLabel('Tmelt :'), row, 0)
        mainLayout.addWidget(self._Tmelt, row, 1)
        mainLayout.addWidget(QtGui.QLabel('°C'), row, 2, 1, 3)
        row += 1
        mainLayout.addWidget(QtGui.QLabel('CM :'), row, 0)
        mainLayout.addWidget(self._CM, row, 1)
        mainLayout.addWidget(QtGui.QLabel('mm/°C'), row, 2, 1, 3)
        row += 1
        mainLayout.addWidget(QtGui.QLabel('deltaT :'), row, 0)
        mainLayout.addWidget(self._deltaT, row, 1)
        mainLayout.addWidget(QtGui.QLabel('days'), row, 2, 1, 3)
        row += 1
        mainLayout.setRowStretch(row, 100)
        row += 1
        mainLayout.addWidget(toolbar_widget, row, 0, 1, 5)

        mainLayout.setColumnStretch(5, 100)

    # =========================================================================

    def get_Range(self, name):
        if name == 'Sy':
            return [self.QSy_min.value(), self.QSy_max.value()]
        elif name == 'RASmax':
            return [self.QRAS_min.value(), self.QRAS_max.value()]
        elif name == 'Cro':
            return [self.CRO_min.value(), self.CRO_max.value()]
        else:
            raise ValueError('Name must be either Sy, Rasmax or Cro.')

    @property
    def Tmelt(self):
        return self._Tmelt.value()

    @property
    def Tcrit(self):
        return self._Tcrit.value()

    @property
    def CM(self):
        return self._CM.value()

    @property
    def deltaT(self):
        return self._deltaT.value()

    # =========================================================================

    def closeEvent(self, event):
        super(RechgSetupWin, self).closeEvent(event)
        print('Closing Window')

    def btn_calibrate_isClicked(self):
        print('Calibration started')

        plt.close('all')

        sh = SynthHydrograph()

        # ---- Parameter ranges ----

        Sy = self.get_Range('Sy')
        RASmax = self.get_Range('RASmax')
        Cro = self.get_Range('Cro')

        sh.TMELT = self.Tmelt
        sh.CM = self.CM
        sh.deltat = self.deltaT

        print(self.parent().A, self.parent().B)

        # ---- Calculations ----

        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

        sh.load_data(self.parent().wxdset, self.parent().wldset)
        sh.GLUE(Sy, RASmax, Cro, res='rough')

        QtGui.QApplication.restoreOverrideCursor()

        sh.calc_recharge()
        sh.initPlot()
        sh.plot_prediction()
        plot_rechg_GLUE('English')

        plt.show()


if __name__ == '__main__':
    import sys
    from projet.manager_data import DataManager
    from projet.reader_projet import ProjetReader
    app = QtGui.QApplication(sys.argv)

    ft = app.font()
    ft.setFamily('Segoe UI')
    ft.setPointSize(11)
    app.setFont(ft)

    pf = ('C:/Users/jsgosselin/OneDrive/Research/'
          'PostDoc - MDDELCC/Outils/BRF MontEst/'
          'BRF MontEst.what')
    pr = ProjetReader(pf)
    dm = DataManager()

    hydrocalc = WLCalc(dm)
    hydrocalc.show()

    dm.set_projet(pr)

    sys.exit(app.exec_())

#    import sys
#    plt.rc('font', family='Arial')
#
#    app = QtGui.QApplication(sys.argv)
#
#    ft = app.font()
#    ft.setFamily('Segoe UI')
#    ft.setPointSize(11)
#    app.setFont(ft)
#
#    # Create and show widgets :
#
#    w = WLCalc()
#    w.show()
#    w.widget_MRCparam.show()
#
#    # ---- Pont Rouge ----
#
#    dirname = os.path.join(
#        os.path.dirname(os.getcwd()), 'Projects', 'Pont-Rouge')
#    fmeteo = os.path.join(
#        dirname, 'Meteo', 'Output', 'STE CHRISTINE (7017000)_1960-2015.out')
#    fwaterlvl = os.path.join(dirname, 'Water Levels', '5080001.xls')
#
#    # ---- IDM ----
#
#    dirname = os.path.dirname(os.getcwd())
#    dirname = os.path.join(dirname, 'Projects', 'IDM')
#    fmeteo = os.path.join(dirname, 'Meteo', 'Output', 'IDM (JSG2017)',
#                          'IDM (JSG2017)_1960-2016.out')
#    fwaterlvl = os.path.join(dirname, 'Water Levels', 'Boisville.xls')
#
#    # ---- Testing ----
#
#    dirname = os.path.dirname(os.getcwd())
#    dirname = os.path.join(dirname, 'Projects', 'Project4Testing')
#    fwaterlvl = os.path.join(dirname, 'Water Levels', 'F1.xlsx')
#
#    # ---- Valcartier ----
#
#    dirname = '../Projects/Valcartier'
#    fmeteo = os.path.join(dirname, 'Meteo', 'Output', 'Valcartier (9999999)',
#                          'Valcartier (9999999)_1994-2015.out')
#    fwaterlvl = os.path.join(dirname, 'Water Levels', 'valcartier2.xls')
#
#    # Load and plot data :
#
#    w.load_waterLvl_data(fwaterlvl)
#    w.load_weather_data(fmeteo)
#
#    # Calcul recharge :
#
##    w.synth_hydrograph.load_data(fmeteo, fwaterlvl)
#
#    sys.exit(app.exec_())
