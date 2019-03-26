# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Standard library imports
from time import clock
import csv
import os
import os.path as osp
import datetime


# ---- Third party imports
import numpy as np
from matplotlib.patches import Rectangle
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSlot as QSlot
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtWidgets import (
    QGridLayout, QComboBox, QTextEdit, QSizePolicy, QPushButton, QLabel,
    QTabWidget, QApplication, QWidget)

import matplotlib as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

from xlrd import xldate_as_tuple
from xlrd.xldate import xldate_from_date_tuple


# ---- Local imports
from gwhat.gwrecharge.gwrecharge_gui import RechgEvalWidget
import gwhat.common.widgets as myqt
from gwhat.common.widgets import DialogWindow
from gwhat.common import StyleDB
from gwhat.utils import icons
from gwhat.utils.icons import QToolButtonNormal
from gwhat.widgets.buttons import ToolBarWidget
from gwhat.brf_mod import BRFManager
from gwhat.widgets.buttons import OnOffToolButton
from gwhat.widgets.layout import VSep
from gwhat.widgets.fileio import SaveFileMixin


class WLCalc(DialogWindow, SaveFileMixin):
    """
    This is the interface where are plotted the water level time series. It is
    possible to dynamically zoom and span the data, change the display,
    i.e. display the data as a continuous line or individual dot, perform a
    MRC and ultimately estimate groundwater recharge.
    """
    sig_new_mrc = QSignal()

    def __init__(self, datamanager, parent=None):
        DialogWindow.__init__(self, parent, maximize=True)
        SaveFileMixin.__init__(self)

        self._navig_and_select_tools = []
        self._wldset = None

        self.dmngr = datamanager
        self.dmngr.wldsetChanged.connect(self.set_wldset)
        self.dmngr.wxdsetChanged.connect(self.set_wxdset)
        self.dmngr.sig_workdir_changed.connect(self.set_dialog_dir)

        # Setup recharge calculation tool.
        self.rechg_eval_widget = RechgEvalWidget(parent=self)
        self.rechg_eval_widget.sig_new_gluedf.connect(self.draw_glue_wl)

        # Setup BRF calculation tool.
        self.brf_eval_widget = BRFManager(parent=self)
        self.brf_eval_widget.sig_brfperiod_changed.connect(self.plot_brfperiod)
        self.brf_eval_widget.btn_seldata.sig_value_changed.connect(
            lambda: self.toggle_brfperiod_selection(
                self.brf_eval_widget.btn_seldata.value())
            )
        self.register_navig_and_select_tool(self.brf_eval_widget.btn_seldata)

        self.__figbckground = None
        self.__addPeakVisible = True
        self.__mouse_btn_is_pressed = False

        # Calcul the delta between the datum of Excel and Maplotlib numeric
        # date system.
        t_xls = xldate_from_date_tuple((2000, 1, 1), 0)
        t_mpl = mpl.dates.date2num(datetime.datetime(2000, 1, 1))
        self.dt4xls2mpl = t_mpl - t_xls

        # The date format can either be 0 for Excel format or 1 for Matplotlib
        # format.
        self.dformat = 1

        # Recession Curve Parameters :
        self.peak_indx = np.array([]).astype(int)
        self.peak_memory = [np.array([]).astype(int)]

        # Selected water level data.
        self.wl_selected_i = []

        # Soil Profiles :
        self.soilFilename = []
        self.SOILPROFIL = SoilProfil()

        # Initialize the GUI
        self.precip_bwidth = 7
        self._setup_mpl_canvas()
        self.__initUI__()
        self.btn_pan.setValue(True)
        self.setup_ax_margins(None)
        self.set_wldset(self.dmngr.get_current_wldset())
        self.set_wxdset(self.dmngr.get_current_wxdset())

    def _setup_mpl_canvas(self):

        # ---- Setup the canvas

        self.fig = mpl.figure.Figure(facecolor='white')
        self.canvas = FigureCanvasQTAgg(self.fig)

        self.canvas.mpl_connect('button_press_event', self.onclick)
        self.canvas.mpl_connect('button_release_event', self.onrelease)
        self.canvas.mpl_connect('resize_event', self.setup_ax_margins)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas.mpl_connect('figure_leave_event', self.on_fig_leave)
        self.canvas.mpl_connect('axes_enter_event', self.on_axes_enter)
        self.canvas.mpl_connect('axes_leave_event', self.on_axes_leave)

        # ---- Setup the canvas frame

        # Put figure canvas in a QFrame widget.

        self.fig_frame_widget = myqt.QFrameLayout()
        self.fig_frame_widget.addWidget(self.canvas, 0, 0)

        self.fig_frame_widget.setFrameStyle(StyleDB().frame)
        self.fig_frame_widget.setLineWidth(2)
        self.fig_frame_widget.setMidLineWidth(1)

        # ----- Setup the axes

        # Water Level (Host) :
        ax0 = self.fig.add_axes([0, 0, 1, 1], zorder=100)
        ax0.patch.set_visible(False)
        ax0.invert_yaxis()

        # Precipitation :
        ax1 = ax0.twinx()
        ax1.patch.set_visible(False)
        ax1.set_zorder(50)
        ax1.set_navigate(False)

        # ---- Setup ticks

        ax0.xaxis.set_ticks_position('bottom')
        ax0.tick_params(axis='x', direction='out')

        ax0.yaxis.set_ticks_position('left')
        ax0.tick_params(axis='y', direction='out')

        ax1.yaxis.set_ticks_position('right')
        ax1.tick_params(axis='y', direction='out')

        # ---- Setup axis labels

        ax0.set_ylabel('Water level (mbgs)', fontsize=14, labelpad=25,
                       va='top', color='black')
        ax0.set_xlabel('Time (days)', fontsize=14, labelpad=25,
                       va='bottom', color='black')
        ax1.set_ylabel('Precipitation (mm)', fontsize=14, labelpad=25,
                       va='top', color='black', rotation=270)

        # ---- Setup gridlines

        # ax0.grid(axis='x', color=[0.35, 0.35, 0.35], ls='--')
        # ax0.set_axisbelow(True)

        # ---- Setup the artists

        # Water level data.
        self._obs_wl_plt, = ax0.plot(
            [], [], color='blue', clip_on=True, ls='-', zorder=10,
            marker='None')

        self._select_wl_plt, = ax0.plot(
            [], [], color='orange', clip_on=True, ls='None', zorder=10,
            marker='.', mfc='orange', mec='orange', ms=5, mew=1.5)

        # Water levels measured manually.
        self._meas_wl_plt, = ax0.plot(
            [], [], clip_on=True, ls='none', zorder=10, marker='+', ms=8,
            mec='red', mew=2, mfc='red')

        # Predicted water levels.
        self.plt_wlpre, = ax0.plot([], [], color='red', clip_on=True,
                                   ls='-', zorder=10, marker='None')

        # Recession.
        self._mrc_plt, = ax0.plot([], [], color='red', clip_on=True,
                                  zorder=15, marker='None', linestyle='--')

        # Rain.
        self.h_rain, = ax1.plot([], [])

        # Precipitation.
        self.h_ptot, = ax1.plot([], [])

        # Evapotranspiration.
        self.h_etp, = ax1.plot([], [], color='#FF6666', lw=1.5, zorder=500,
                               ls='-')

        # Barometric response function (BRF).
        self.h_brf1 = ax0.axvline(0, color='red', lw=1)
        self.h_brf2 = ax0.axvline(0, color='red', lw=1)

        self._selected_brfperiod = [None, None]
        self._brf_selector = ax0.axvspan(
            0, 0, edgecolor='black', facecolor='red', linestyle=':',
            fill=True, alpha=0.15, visible=False)

        # Predicted GLUE water levels
        self.glue_plt, = ax0.plot([], [])

        # Rectangular selection box.
        self._rect_selection = [(None, None), (None, None)]
        self._rect_selector = Rectangle(
            (0, 0), 0, 0, edgecolor='black', facecolor='red', linestyle=':',
            fill=True, alpha=0.15, visible=False)
        ax0.add_patch(self._rect_selector)

        # Vertical guide line under cursor.
        self.vguide = ax0.axvline(
            -1, color='black', zorder=40,  linestyle='--', lw=1, visible=False)

        # x and y coorrdinate labels displayed at the right-bottom corner
        # of the graph
        offset = mpl.transforms.ScaledTranslation(
            -5/72, 5/72, self.fig.dpi_scale_trans)
        self.xycoord = ax0.text(
            1, 0, '', ha='right', transform=ax0.transAxes + offset)
        self.xycoord.set_visible(False)

        # Peaks :
        self._peaks_plt, = ax0.plot(
            [], [], color='white', clip_on=True, zorder=30, marker='o',
            linestyle='None', mec='red', mew=1.5)

        # Cross Remove Peaks :
        self.xcross, = ax0.plot(1, 0, color='red', clip_on=True,
                                zorder=20, marker='x', linestyle='None',
                                markersize=15, markeredgewidth=3)

    def _setup_toolbar(self):
        """Setup the main toolbar of the water level calc tool."""

        # ---- Navigate data.
        self.toolbar = NavigationToolbar2QT(self.canvas, parent=self)
        self.toolbar.hide()

        self.btn_home = QToolButtonNormal(icons.get_icon('home'))
        self.btn_home.setToolTip('Reset original view.')
        self.btn_home.clicked.connect(self.home)

        self.btn_fit_waterlevels = QToolButtonNormal('expand_all')
        self.btn_fit_waterlevels.setToolTip(
            "<p>Best fit the water level data along the x and y axis.</p>")
        self.btn_fit_waterlevels.clicked.connect(self.setup_axis_range)

        self.btn_pan = OnOffToolButton('pan', size='normal')
        self.btn_pan.setToolTip(
            'Pan axes with the left mouse button and zoom with the right')
        self.btn_pan.sig_value_changed.connect(self.pan_is_active_changed)
        self.register_navig_and_select_tool(self.btn_pan)

        self.btn_zoom_to_rect = OnOffToolButton('zoom_to_rect', size='normal')
        self.btn_zoom_to_rect.setToolTip(
            "Zoom into the rectangle with the left mouse button and zoom"
            " out with the right mouse button.")
        self.btn_zoom_to_rect.sig_value_changed.connect(
            self.zoom_is_active_changed)
        self.register_navig_and_select_tool(self.btn_zoom_to_rect)

        self.btn_wl_style = OnOffToolButton('showDataDots', size='normal')
        self.btn_wl_style.setToolTip(
            '<p>Show water lvl data as dots instead of a continuous line</p>')
        self.btn_wl_style.sig_value_changed.connect(self.setup_wl_style)

        self.btn_strati = QToolButtonNormal(icons.get_icon('stratigraphy'))
        self.btn_strati.setToolTip('Toggle on and off the display of the soil'
                                   ' stratigraphic layers')
        self.btn_strati.clicked.connect(self.btn_strati_isClicked)

        self.btn_dateFormat = QToolButtonNormal(icons.get_icon('calendar'))
        self.btn_dateFormat.setToolTip(
            'Show x-axis tick labels as Excel numeric format.')
        self.btn_dateFormat.clicked.connect(self.switch_date_format)
        self.btn_dateFormat.setAutoRaise(False)
        # dformat: False -> Excel Numeric Date Format
        #          True -> Matplotlib Date Format

        # ---- Show/Hide section
        self.btn_show_glue = OnOffToolButton('show_glue_wl', size='normal')
        self.btn_show_glue.setToolTip(
            "Show or hide GLUE water level 05/95 envelope.")
        self.btn_show_glue.sig_value_changed.connect(self.draw_glue_wl)
        self.btn_show_glue.setValue(True, silent=True)

        self.btn_show_weather = OnOffToolButton('show_meteo', size='normal')
        self.btn_show_weather.setToolTip("""Show or hide weather data.""")
        self.btn_show_weather.sig_value_changed.connect(self.draw_weather)
        self.btn_show_weather.setValue(True, silent=True)

        self.btn_show_mrc = OnOffToolButton('mrc_calc', size='normal')
        self.btn_show_mrc.setToolTip(
            "Show or hide water levels predicted with the MRC.")
        self.btn_show_mrc.sig_value_changed.connect(
            self.btn_show_mrc_isclicked)
        self.btn_show_mrc.setValue(True, silent=True)

        self.btn_show_meas_wl = OnOffToolButton(
            'manual_measures', size='normal')
        self.btn_show_meas_wl.setToolTip(
            "Show or hide water levels measured manually in the well.")
        self.btn_show_meas_wl.setValue(True, silent=True)
        self.btn_show_meas_wl.sig_value_changed.connect(self.draw_meas_wl)

        # ---- Select and transform data.
        self.btn_rect_select = OnOffToolButton('rect_select', size='normal')
        self.btn_rect_select.setToolTip(
            "Select water level data by clicking with the mouse and "
            "dragging the cursor over a rectangular region of the graph.")
        self.btn_rect_select.sig_value_changed.connect(
            self.rect_select_is_active_changed)
        self.register_navig_and_select_tool(self.btn_rect_select)

        self.btn_clear_select = QToolButtonNormal('rect_select_clear')
        self.btn_clear_select.setToolTip("Clear selected water levels.")
        self.btn_clear_select.clicked.connect(self.clear_selected_wl)

        self.btn_del_select = QToolButtonNormal('erase_data')
        self.btn_del_select.setToolTip(
            "Remove the selected water level data from the dataset.")
        self.btn_del_select.clicked.connect(self.delete_selected_wl)

        self.btn_undo_changes = QToolButtonNormal('undo_changes')
        self.btn_undo_changes.setToolTip(
            "Undo the last changes made to the water level data.")
        self.btn_undo_changes.setEnabled(False)
        self.btn_undo_changes.clicked.connect(self.undo_wl_changes)

        self.btn_clear_changes = QToolButtonNormal('clear_changes')
        self.btn_clear_changes.setToolTip(
            "Clear all changes made to the water level data since the last "
            "commit.")
        self.btn_clear_changes.clicked.connect(self.clear_all_changes)
        self.btn_clear_changes.setEnabled(False)

        self.btn_commit_changes = QToolButtonNormal('commit_changes')
        self.btn_commit_changes.clicked.connect(self.commit_wl_changes)
        self.btn_commit_changes.setEnabled(False)

        # Setup the layout.
        toolbar = ToolBarWidget()
        for btn in [self.btn_home, self.btn_fit_waterlevels, self.btn_pan,
                    self.btn_zoom_to_rect, None,
                    self.btn_wl_style, self.btn_dateFormat, None,
                    self.btn_show_glue, self.btn_show_weather,
                    self.btn_show_mrc, self.btn_show_meas_wl, None,
                    self.btn_rect_select, self.btn_clear_select,
                    self.btn_del_select, self.btn_undo_changes,
                    self.btn_clear_changes, self.btn_commit_changes]:
            toolbar.addWidget(btn)

        return toolbar

    def _setup_mrc_tool(self):
        """Setup the tool to evaluate the MRC."""

        # ---- MRC parameters

        self.MRC_type = QComboBox()
        self.MRC_type.addItems(['Linear', 'Exponential'])
        self.MRC_type.setCurrentIndex(1)

        self.MRC_ObjFnType = QComboBox()
        self.MRC_ObjFnType.addItems(['RMSE', 'MAE'])
        self.MRC_ObjFnType.setCurrentIndex(0)

        self.MRC_results = QTextEdit()
        self.MRC_results.setReadOnly(True)
        self.MRC_results.setMinimumHeight(25)
        self.MRC_results.setMinimumWidth(100)

        self.MRC_results.setSizePolicy(
            QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred))

        # ---- MRC toolbar

        self.btn_undo = QToolButtonNormal(icons.get_icon('undo'))
        self.btn_undo.setToolTip('Undo')
        self.btn_undo.setEnabled(False)
        self.btn_undo.clicked.connect(self.undo)

        self.btn_clearPeak = QToolButtonNormal(icons.get_icon('clear_search'))
        self.btn_clearPeak.setToolTip('Clear all extremum from the graph')
        self.btn_clearPeak.clicked.connect(self.clear_all_peaks)

        self.btn_addpeak = OnOffToolButton('add_point', size='normal')
        self.btn_addpeak.sig_value_changed.connect(self.btn_addpeak_isclicked)
        self.btn_addpeak.setToolTip(
            "<p>Toggle edit mode to manually add extremums to the graph</p>")
        self.register_navig_and_select_tool(self.btn_addpeak)

        self.btn_delpeak = OnOffToolButton('erase', size='normal')
        self.btn_delpeak.clicked.connect(self.btn_delpeak_isclicked)
        self.btn_delpeak.setToolTip(
            "<p>Toggle edit mode to manually remove extremums"
            " from the graph</p>")
        self.register_navig_and_select_tool(self.btn_delpeak)

        self.btn_save_mrc = QToolButtonNormal(icons.get_icon('save'))
        self.btn_save_mrc.setToolTip('Save calculated MRC to file.')
        self.btn_save_mrc.clicked.connect(self.save_mrc_tofile)

        self.btn_MRCalc = QPushButton('Compute MRC')
        self.btn_MRCalc.clicked.connect(self.btn_MRCalc_isClicked)
        self.btn_MRCalc.setToolTip('<p>Calculate the Master Recession Curve'
                                   ' (MRC) for the selected time periods.</p>')

        mrc_tb = ToolBarWidget()
        for btn in [self.btn_undo, self.btn_clearPeak, self.btn_addpeak,
                    self.btn_delpeak, self.btn_save_mrc]:
            mrc_tb.addWidget(btn)

        # ---- MRC Layout ----

        self.mrc_eval_widget = QWidget()
        mrc_lay = QGridLayout(self.mrc_eval_widget)

        row = 0
        mrc_lay.addWidget(QLabel('MRC Type :'), row, 0)
        mrc_lay.addWidget(self.MRC_type, row, 1)
        row += 1
        mrc_lay.addWidget(self.MRC_results, row, 0, 1, 3)
        row += 1
        mrc_lay.addWidget(mrc_tb, row, 0, 1, 3)
        row += 1
        mrc_lay.setRowMinimumHeight(row, 5)
        mrc_lay.setRowStretch(row, 100)
        row += 1
        mrc_lay.addWidget(self.btn_MRCalc, row, 0, 1, 3)

        mrc_lay.setContentsMargins(10, 10, 10, 10)
        mrc_lay.setSpacing(5)
        mrc_lay.setColumnStretch(2, 500)

        return self.mrc_eval_widget

    def __initUI__(self):
        self.setWindowTitle('Hydrograph Analysis')
        toolbar = self._setup_toolbar()
        self.mrc_eval_widget = self._setup_mrc_tool()

        # ---- Tool Tab Area

        tooltab = QTabWidget()
        tooltab.addTab(self.mrc_eval_widget, 'MRC')
        tooltab.setTabToolTip(
            0, ("<p>A tool to evaluate the master recession curve"
                " of the hydrograph.</p>"))
        tooltab.addTab(self.rechg_eval_widget, 'Recharge')
        tooltab.setTabToolTip(
            1, ("<p>A tool to evaluate groundwater recharge and its"
                " uncertainty from observed water levels and daily "
                " weather data.</p>"))
        tooltab.addTab(self.brf_eval_widget, 'BRF')
        tooltab.setTabToolTip(
            2, ("<p>A tool to evaluate the barometric response function of"
                " the well.</p>"))

        tooltab.currentChanged.connect(
            lambda: self.toggle_brfperiod_selection(False))

        # ---- Right Panel

        self.right_panel = myqt.QFrameLayout()

        row = 0
        self.right_panel.addWidget(self.dmngr, row, 0)
        row += 1
        self.right_panel.addWidget(tooltab, row, 0)
        row += 1
        self.right_panel.setRowStretch(row, 100)

        self.right_panel.setSpacing(15)

        # ---- Setup the main layout

        mainGrid = QGridLayout(self)

        mainGrid.addWidget(toolbar, 0, 0)
        mainGrid.addWidget(self.fig_frame_widget, 1, 0, 2, 1)
        mainGrid.addWidget(VSep(), 0, 1, 3, 1)
        mainGrid.addWidget(self.right_panel, 0, 2, 2, 1)

        mainGrid.setContentsMargins(10, 10, 10, 10)  # (L, T, R, B)
        mainGrid.setHorizontalSpacing(15)
        mainGrid.setRowStretch(1, 100)
        # mainGrid.setRowStretch(2, 100)
        mainGrid.setColumnStretch(0, 100)
        mainGrid.setColumnMinimumWidth(2, 250)

    @property
    def water_lvl(self):
        return np.array([]) if self.wldset is None else self.wldset.waterlevels

    @property
    def time(self):
        return np.array([]) if self.wldset is None else self.wldset.datetimes

    @property
    def wldset(self):
        return self._wldset

    @property
    def wxdset(self):
        return self.dmngr.get_current_wxdset()

    def set_wldset(self, wldset):
        """Set the namespace for the water level dataset."""
        self._wldset = wldset
        self.rechg_eval_widget.set_wldset(wldset)
        self.mrc_eval_widget.setEnabled(self.wldset is not None)

        # Setup BRF widget.
        self.brf_eval_widget.set_wldset(wldset)
        self.plot_brfperiod()

        self.setup_hydrograph()
        self.toolbar.update()
        self.load_mrc_from_wldset()

    def set_wxdset(self, wxdset):
        """Set the weather dataset."""
        self.rechg_eval_widget.set_wxdset(wxdset)
        self.draw_weather()

    # ---- MRC handlers

    def btn_show_mrc_isclicked(self):
        """Handle when the button to draw of hide the mrc is clicked."""
        if self.btn_show_mrc.value() is False:
            self.btn_addpeak.setValue(False)
            self.btn_delpeak.setValue(False)
        self.draw_mrc()

    def btn_MRCalc_isClicked(self):
        if self.wldset is None:
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)

        A, B, hp, RMSE = mrc_calc(self.time, self.water_lvl, self.peak_indx,
                                  self.MRC_type.currentIndex())

        print('MRC Parameters: A=%f, B=%f' % (A, B))
        if A is None:
            QApplication.restoreOverrideCursor()
            return

        # Display result :

        txt = '∂h/∂t (mm/d) = -%0.2f h + %0.2f' % (A*1000, B*1000)
        self.MRC_results.setText(txt)
        txt = '%s = %f m' % (self.MRC_ObjFnType.currentText(), RMSE)
        self.MRC_results.append(txt)
        self.MRC_results.append('\nwhere h is the depth to water '
                                'table in mbgs and ∂h/∂t is the recession '
                                'rate in mm/d.')

        # Store and plot the results.
        print('Saving MRC interpretation in dataset...')
        self.wldset.set_mrc(A, B, self.peak_indx, self.time, hp)
        self.btn_save_mrc.setEnabled(True)
        self.draw_mrc()
        self.sig_new_mrc.emit()

        QApplication.restoreOverrideCursor()

    def load_mrc_from_wldset(self):
        """Load saved MRC results from the project hdf5 file."""
        if self.wldset is not None and self.wldset.mrc_exists():
            self.peak_indx = self.wldset['mrc/peak_indx'].astype(int)
            self.peak_memory[0] = self.wldset['mrc/peak_indx'].astype(int)
            self.btn_save_mrc.setEnabled(True)
        else:
            self.peak_indx = np.array([]).astype(int)
            self.peak_memory = []
            self.btn_save_mrc.setEnabled(False)
        self.draw_mrc()

    def save_mrc_tofile(self, savefilename=None):
        """Save the master recession curve results to a file."""
        if savefilename is None:
            savefilename = osp.join(
                self.dialog_dir,
                "Well_%s_mrc_results.xlsx" % self.wldset['Well'])

        savefilename = self.select_savefilename(
            "Save MRC results", savefilename, "*.xlsx;;*.xls;;*.csv")

        if savefilename:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            QApplication.processEvents()
            try:
                self.wldset.save_mrc_tofile(savefilename)
            except PermissionError:
                self.show_permission_error()
                self.save_mrc_tofile(savefilename)
            QApplication.restoreOverrideCursor()

    def btn_mrc2rechg_isClicked(self):
        if not self.wldset.mrc_exists():
            print('Need to calculate MRC equation first.')
            return
        A, B = self.wldset['mrc/params']
        if not os.path.exists(self.soilFilename):
            print('A ".sol" file is needed for the calculation of' +
                  ' groundwater recharge from the MRC')
            return

        self.SOILPROFIL.load_info(self.soilFilename)
        mrc2rechg(self.time, self.water_lvl, A, B,
                  self.SOILPROFIL.zlayer, self.SOILPROFIL.Sy)

    # ---- BRF handlers
    def plot_brfperiod(self):
        """
        Plot on the graph the vertical lines that are used to define the period
        over which the BRF is evaluated.
        """
        if (self.brf_eval_widget.btn_seldata.value() is False and
                self.brf_eval_widget.isVisible()):
            brfperiod = self.brf_eval_widget.get_brfperiod()
        else:
            brfperiod = [None, None]
        for x, vline in zip(brfperiod, [self.h_brf1, self.h_brf2]):
            vline.set_visible(x is not None)
            if x is not None:
                x = x + self.dt4xls2mpl*self.dformat
                vline.set_xdata(x)
        self.draw()

    def toggle_brfperiod_selection(self, value):
        """
        Toggle on or off the option to select the BRF calculation period on
        the graph.
        """
        if self.wldset is None:
            self.brf_eval_widget.btn_seldata.setValue(False, silent=True)
            if value is True:
                self.emit_warning("Please import a valid water "
                                  "level dataset first.")
            return

        self.brf_eval_widget.btn_seldata.setValue(value, silent=True)
        if value is True:
            self.toggle_navig_and_select_tools(
                self.brf_eval_widget.btn_seldata)
        self.plot_brfperiod()

    # ---- Peaks handlers
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
        self.draw_mrc()

    def btn_addpeak_isclicked(self):
        """Handle when the button add_peak is clicked."""
        if self.btn_addpeak.value():
            self.toggle_navig_and_select_tools(self.btn_addpeak)
            self.btn_show_mrc.setValue(True)
        self.draw()

    def btn_delpeak_isclicked(self):
        """Handle when the button btn_delpeak is clicked."""
        if self.btn_delpeak.value():
            self.toggle_navig_and_select_tools(self.btn_delpeak)
            self.btn_show_mrc.setValue(True)
        self.draw()

    def clear_all_peaks(self):
        """Clear all peaks from the graph."""
        if len(self.peak_indx) > 0:
            self.peak_indx = np.array([]).astype(int)
            self.peak_memory.append(self.peak_indx)
            self.draw_mrc()

    # ---- Navig and selec tools

    def register_navig_and_select_tool(self, tool):
        """
        Add the tool to the list of tools that are available to interactively
        navigate and select the data.
        """
        if not isinstance(tool, OnOffToolButton):
            raise TypeError

        if tool not in self._navig_and_select_tools:
            self._navig_and_select_tools.append(tool)

    def toggle_navig_and_select_tools(self, keep_toggled=None):
        """
        Toggle off all navigation and selection tool, but the ones listed
        in the keep_toggled.
        """
        try:
            iter(keep_toggled)
        except TypeError:
            keep_toggled = [keep_toggled]

        for tool in self._navig_and_select_tools:
            if tool not in keep_toggled:
                tool.setValue(False)

    @property
    def zoom_is_active(self):
        """Return whether the zooming to rectangle tool is active or not."""
        return self.btn_zoom_to_rect.value()

    @QSlot(bool)
    def zoom_is_active_changed(self, zoom_is_active):
        """Handle when the state of the button to zoom to rectangle changes."""
        if self.zoom_is_active:
            self.toggle_navig_and_select_tools(self.btn_zoom_to_rect)
            if self.toolbar._active is None:
                self.toolbar.zoom()
        else:
            if self.toolbar._active == 'ZOOM':
                self.toolbar.zoom()

    @property
    def pan_is_active(self):
        """Return whether the panning of the graph is active or not."""
        return self.btn_pan.value()

    @QSlot(bool)
    def pan_is_active_changed(self, pan_is_active):
        """Handle when the state of the button to pan the graph changes."""
        if self.pan_is_active:
            self.toggle_navig_and_select_tools(self.btn_pan)
            if self.toolbar._active is None:
                self.toolbar.pan()
        else:
            if self.toolbar._active == 'PAN':
                self.toolbar.pan()

    @property
    def rect_select_is_active(self):
        """
        Return whether the rectangle selection of water level data is
        active or not.
        """
        return self.btn_rect_select.value()

    @QSlot(bool)
    def rect_select_is_active_changed(self, value):
        """Handle the rectangular selection tool is toggled on or off."""
        if self.rect_select_is_active:
            self.toggle_navig_and_select_tools(self.btn_rect_select)

    def clear_selected_wl(self, draw=True):
        """Clear the selecte water level data."""
        self.wl_selected_i = []
        self.draw_select_wl(draw)

    def home(self):
        """Reset the orgininal view of the figure."""
        self.toolbar.home()
        if self.dformat == 0:
            ax0 = self.fig.axes[0]
            xfmt = mpl.ticker.ScalarFormatter()
            ax0.xaxis.set_major_formatter(xfmt)
            ax0.get_xaxis().get_major_formatter().set_useOffset(False)

            xlim = ax0.get_xlim()
            ax0.set_xlim(xlim[0] - self.dt4xls2mpl, xlim[1] - self.dt4xls2mpl)
        self.setup_ax_margins()

    def undo(self):
        if len(self.peak_memory) > 1:
            self.peak_indx = self.peak_memory[-2]
            del self.peak_memory[-1]
            self.draw_mrc()

    # ---- Water level edit tools
    def delete_selected_wl(self):
        """Delete the selecte water level data."""
        if len(self.wl_selected_i) and self.wldset is not None:
            self.wldset.delete_waterlevels_at(self.wl_selected_i)
            self._draw_obs_wl()
            self._update_edit_toolbar_state()

    def undo_wl_changes(self):
        """Undo the last changes made to the water level data."""
        if self.wldset is not None:
            self.wldset.undo()
            self._draw_obs_wl()
            self._update_edit_toolbar_state()

    def clear_all_changes(self):
        """Clear all changes that were made to the wldset."""
        if self.wldset is not None:
            self.wldset.clear_all_changes()
            self._draw_obs_wl()
            self._update_edit_toolbar_state()

    def commit_wl_changes(self):
        """Commit the changes made to the water level data to the project."""
        if self.wldset is not None:
            self.wldset.commit()
            self._update_edit_toolbar_state()

    def _update_edit_toolbar_state(self):
        """Update the state of the edit toolbar."""
        buttons = [self.btn_commit_changes,
                   self.btn_clear_changes,
                   self.btn_undo_changes]
        for btn in buttons:
            btn.setEnabled(False if self.wldset is None else
                           self.wldset.has_uncommited_changes)

    # ---- Drawing methods
    def setup_hydrograph(self):
        """Setup the hydrograph after a new wldset has been set."""
        self.peak_indx = np.array([]).astype(int)
        self.peak_memory = [np.array([]).astype(int)]
        self.btn_undo.setEnabled(False)

        self.clear_selected_wl()
        self._update_edit_toolbar_state()

        # Plot observed and predicted water levels
        self._draw_obs_wl()
        self.plt_wlpre.set_data([], [])

        self.draw_meas_wl()
        self.draw_glue_wl()
        self.draw_weather()
        if not self.btn_strati.autoRaise():
            # Plot stratigraphy.
            self.display_soil_layer()

        self.setup_axis_range()
        self.setup_xticklabels_format()
        self.draw()

    def setup_axis_range(self, event=None):
        """Setup the range of the x- and y-axis."""
        if self.wldset is not None:
            y = self.water_lvl
            t = self.time + self.dt4xls2mpl * self.dformat
        elif self.wxdset is not None:
            y = [-1, 1]
            t = self.wxdset['Time'] + self.dt4xls2mpl * self.dformat
        else:
            y = [-1, 1]
            t = np.array(
                [xldate_from_date_tuple((1980, 1, 1), 0),
                 xldate_from_date_tuple((2018, 1, 1), 0)]
                ) + self.dt4xls2mpl * self.dformat

        Xmin0 = np.min(t) - (np.max(t) - np.min(t)) * 0.05
        Xmax0 = np.max(t) + (np.max(t) - np.min(t)) * 0.05
        Ymin0 = np.nanmin(y) - (np.nanmax(y) - np.nanmin(y)) * 0.25
        Ymax0 = np.nanmax(y) + (np.nanmax(y) - np.nanmin(y)) * 0.25
        self.fig.axes[0].axis([Xmin0, Xmax0, Ymax0, Ymin0])

        # Setup the yaxis range for the weather.
        self.fig.axes[1].axis(ymin=500, ymax=0)
        self.draw()

    def setup_ax_margins(self, event=None):
        """Setup the margins width of the axes in inches."""
        fheight = self.fig.get_figheight()
        fwidth = self.fig.get_figwidth()

        left_margin = 1 / fwidth
        right_margin = 1 / fwidth
        bottom_margin = 0.75 / fheight
        top_margin = 0.2 / fheight

        x0 = left_margin
        y0 = bottom_margin
        w = 1 - (left_margin + right_margin)
        h = 1 - (bottom_margin + top_margin)

        for axe in self.fig.axes:
            axe.set_position([x0, y0, w, h])
        self.draw()

    def setup_xticklabels_format(self):
        """Setup the format of the xticklabels."""
        ax0 = self.fig.axes[0]
        if self.dformat == 1:
            xloc = mpl.dates.AutoDateLocator()
            ax0.xaxis.set_major_locator(xloc)
            xfmt = mpl.dates.AutoDateFormatter(xloc)
            ax0.xaxis.set_major_formatter(xfmt)
        elif self.dformat == 0:
            xfmt = mpl.ticker.ScalarFormatter()
            ax0.xaxis.set_major_formatter(xfmt)
            ax0.get_xaxis().get_major_formatter().set_useOffset(False)

    def switch_date_format(self):
        """
        Change the format of the xticklabels.
        - 0 is for Excel numeric date format.
        - 1 is for Matplotlib text format.
        """
        ax0 = self.fig.axes[0]
        if self.dformat == 0:
            # Switch to matplotlib date format
            self.btn_dateFormat.setAutoRaise(False)
            self.btn_dateFormat.setToolTip(
                'Show x-axis tick labels as Excel numeric format')
            self.dformat = 1
        elif self.dformat == 1:
            # Switch to Excel numeric date format
            self.btn_dateFormat.setAutoRaise(True)
            self.btn_dateFormat.setToolTip(
                'Show x-axis tick labels as date')
            self.dformat = 0
        self.setup_xticklabels_format()

        # Adjust the range of the x-axis.
        xlim = ax0.get_xlim()
        if self.dformat == 1:
            ax0.set_xlim(xlim[0] + self.dt4xls2mpl, xlim[1] + self.dt4xls2mpl)
        elif self.dformat == 0:
            ax0.set_xlim(xlim[0] - self.dt4xls2mpl, xlim[1] - self.dt4xls2mpl)

        # Adjust the water levels, peak, MRC ant weather time frame.
        if len(self.peak_indx) > 0:  # Peaks
            self._peaks_plt.set_xdata(
                self.time[self.peak_indx] + self.dt4xls2mpl * self.dformat)

        self._draw_obs_wl()
        self.draw_meas_wl()
        self.draw_mrc()
        self.draw_weather()
        self.draw_glue_wl()
        self.draw()

    def plot_synth_hydro(self, parameters):
        print(parameters)
        Cro = parameters['Cro']
        RASmax = parameters['RASmax']
        Sy = parameters['Sy']

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

    def btn_strati_isClicked(self):

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
            reader = list(csv.reader(f, delimiter=','))

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
            except Exception:
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
            except Exception:
                self.layers[i] = self.ax0.fill_between(
                    [0, 99999], up, down, color='#FFFFFF', zorder=0)

            up = down

        self.draw()

    def setup_wl_style(self):
        """
        Setup the line and marker style of the obeserved water level data.
        """
        if self.btn_wl_style.value():
            self._obs_wl_plt.set_linestyle('None')
            self._obs_wl_plt.set_marker('.')
            self._obs_wl_plt.set_markerfacecolor('blue')
            self._obs_wl_plt.set_markeredgecolor('blue')
            self._obs_wl_plt.set_markeredgewidth(1.5)
            self._obs_wl_plt.set_markersize(5)
        else:
            self._obs_wl_plt.set_linestyle('-')
            self._obs_wl_plt.set_marker('None')
        self.draw()

    def draw(self):
        """Draw the canvas and save a snapshot of the background figure."""
        self.vguide.set_visible(False)
        self.xycoord.set_visible(False)
        self.xcross.set_visible(False)
        self.canvas.draw()
        self.__figbckground = self.fig.canvas.copy_from_bbox(self.fig.bbox)

    def draw_meas_wl(self):
        """Draw the water level measured manually in the well."""
        if self.wldset is not None and self.btn_show_meas_wl.value():
            time_wl_meas, wl_meas = self.wldset.get_wlmeas()
            if len(wl_meas) > 0:
                self._meas_wl_plt.set_visible(True)
                self._meas_wl_plt.set_data(
                    time_wl_meas + self.dt4xls2mpl * self.dformat, wl_meas)
            else:
                self._meas_wl_plt.set_visible(False)
        else:
            self._meas_wl_plt.set_visible(False)
        self.draw()

    def draw_select_wl(self, draw=True):
        """Draw the selected water level data points."""
        if self.wldset is not None:
            self._select_wl_plt.set_data(
                self.time[self.wl_selected_i] +
                (self.dt4xls2mpl * self.dformat),
                self.water_lvl[self.wl_selected_i]
                )
        if draw:
            self.draw()

    def draw_glue_wl(self):
        """Draw or hide the water level envelope estimated with GLUE."""
        if self.wldset is not None and self.btn_show_glue.value():
            gluedf = self.wldset.get_glue_at(-1)
            if gluedf is not None:
                self.glue_plt.set_visible(True)
                xlstime = (gluedf['water levels']['time'] +
                           self.dt4xls2mpl * self.dformat)
                wl05 = gluedf['water levels']['predicted'][:, 0]/1000
                wl95 = gluedf['water levels']['predicted'][:, 2]/1000

                self.glue_plt.remove()
                self.glue_plt = self.fig.axes[0].fill_between(
                    xlstime, wl95, wl05, facecolor='0.85', lw=1,
                    edgecolor='0.65', zorder=0)
            else:
                self.glue_plt.set_visible(False)
        else:
            self.glue_plt.set_visible(False)
        self.draw()

    def draw_weather(self):
        """Plot the weather data."""
        ax = self.fig.axes[1]
        if self.wxdset is None or self.btn_show_weather.value() is False:
            ax.set_visible(False)
        else:
            ax.set_visible(True)

            time = self.wxdset['Time'] + self.dt4xls2mpl*self.dformat
            ptot = self.wxdset['Ptot']
            rain = self.wxdset['Rain']
            etp = self.wxdset['PET']

            # Calculate the bins

            bw = self.precip_bwidth
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

            # Generate the shapes for the fill_between

            time_bar = np.zeros(len(time_bin) * 4)
            rain_bar = np.zeros(len(rain_bin) * 4)
            ptot_bar = np.zeros(len(ptot_bin) * 4)

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

            # Plot the data

            self.h_rain.remove()
            self.h_ptot.remove()

            self.h_rain = ax.fill_between(
                time_bar, 0, rain_bar, color=[23/255, 52/255, 88/255],
                zorder=100, linestyle='None', alpha=0.65, lw=0)
            self.h_ptot = ax.fill_between(
                time_bar, 0, ptot_bar, color=[165/255, 165/255, 165/255],
                zorder=50, linestyle='None', alpha=0.65, lw=0)
            self.h_etp.set_data(time_bin, etp_bin)
        self.draw()

    def draw_mrc(self):
        """
        Draw the periods during which water levels recedes and draw the
        water levels that were predicted with the MRC.
        """
        self._draw_mrc_wl()
        self._draw_mrc_peaks()
        self.draw()

    def _draw_obs_wl(self, draw=True):
        """Draw the observed water level data on the graph."""
        self.clear_selected_wl(draw=False)
        if self.wldset is not None:
            self._obs_wl_plt.set_data(
                self.wldset.datetimes + (self.dt4xls2mpl * self.dformat),
                self.wldset.waterlevels)
        self._obs_wl_plt.set_visible(self.wldset is not None)
        if draw:
            self.draw()

    def _draw_mrc_wl(self):
        """Draw the water levels that were predicted with the MRC."""
        if (self.wldset is not None and self.btn_show_mrc.value() and
                self.wldset.mrc_exists()):
            self._mrc_plt.set_visible(True)
            self._mrc_plt.set_data(
                self.wldset['mrc/time'] + self.dt4xls2mpl * self.dformat,
                self.wldset['mrc/recess'])
        else:
            self._mrc_plt.set_visible(False)

    def _draw_mrc_peaks(self):
        """Draw the periods that will be used to compute the MRC."""
        self.btn_undo.setEnabled(len(self.peak_memory) > 1)
        if self.wldset is not None and self.btn_show_mrc.value():
            self._peaks_plt.set_visible(True)
            self._peaks_plt.set_data(
                self.time[self.peak_indx] + (self.dt4xls2mpl * self.dformat),
                self.water_lvl[self.peak_indx])
        else:
            self._peaks_plt.set_visible(False)

    def _draw_rect_selection(self, x2, y2):
        """Draw the rectangle of the rectangular selection tool."""
        x1, y1 = self._rect_selection[0]
        if not all((x1, y1, x2, y2)):
            self._rect_selector.set_visible(False)
        else:
            self._rect_selector.set_xy((min(x1, x2), min(y1, y2)))
            self._rect_selector.set_height(abs(y1 - y2))
            self._rect_selector.set_width(abs(x1 - x2))
            self._rect_selector.set_visible(True)

            self.fig.axes[0].draw_artist(self._rect_selector)

    def _draw_brf_selection(self, x2):
        """Draw the period of the BRF selection tool."""
        x1 = self._selected_brfperiod[0]
        if not all((x1, x2)):
            self._brf_selector.set_visible(False)
        else:
            self._brf_selector.set_xy([[min(x1, x2), 0],
                                       [min(x1, x2), 1],
                                       [max(x1, x2), 1],
                                       [max(x1, x2), 0],
                                       [min(x1, x2), 0]])
            self._brf_selector.set_visible(True)
            self.fig.axes[0].draw_artist(self._brf_selector)

    def _draw_mouse_cursor(self, x, y):
        """Draw a vertical and horizontal line at the specified xy position."""
        if not all((x, y)):
            self.vguide.set_visible(False)
        elif (self.pan_is_active or self.zoom_is_active or
              self.rect_select_is_active):
            self.vguide.set_visible(False)
        else:
            self.vguide.set_visible(True)
            self.vguide.set_xdata(x)
            self.fig.axes[0].draw_artist(self.vguide)

    # ----- Handlers: Mouse events
    def is_all_btn_raised(self):
        """
        Return whether all of the tool buttons that can block the panning and
        zooming of the graph are raised.
        """
        return(self.btn_delpeak.autoRaise() and
               self.btn_addpeak.autoRaise() and
               self.brf_eval_widget.btn_seldata.autoRaise())

    def on_fig_leave(self, event):
        """Handle when the mouse cursor leaves the graph."""
        self.draw()

    def on_axes_enter(self, event):
        """Handle when the mouse cursor enters a new axe."""
        if self.rect_select_is_active:
            self.toolbar.set_cursor(2)

    def on_axes_leave(self, event):
        """Handle when the mouse cursor leaves an axe."""
        self.toolbar.set_cursor(1)

    def on_brf_select(self):
        """
        Handle when a period has been selected for the BRF calculation.
        """
        if all(self._selected_brfperiod):
            brfperiod = [None, None]
            for i in range(2):
                x = self._selected_brfperiod[i] - (
                        self.dt4xls2mpl * self.dformat)
                brfperiod[i] = self.time[np.argmin(np.abs(x - self.time))]
            self.brf_eval_widget.set_brfperiod(brfperiod)
        self.toggle_brfperiod_selection(False)

    def on_rect_select(self):
        """
        Handle when a rectangular area to select water level data has been
        selected.
        """
        xy_click, xy_release = self._rect_selection
        if not all(xy_click + xy_release):
            # The selection area is not valid.
            return
        else:
            x_click, y_click = xy_click
            x_click = x_click - (self.dt4xls2mpl * self.dformat)

            x_rel, y_rel = xy_release
            x_rel = x_rel - (self.dt4xls2mpl * self.dformat)

            self.wl_selected_i += np.where(
                (self.time >= min(x_click, x_rel)) &
                (self.time <= max(x_click, x_rel)) &
                (self.water_lvl >= min(y_click, y_rel)) &
                (self.water_lvl <= max(y_click, y_rel))
                )[0].tolist()
            self.draw_select_wl()

    def on_mouse_move(self, event):
        """
        Draw the vertical mouse guideline and the x and y coordinates of the
        mouse cursor on the graph.
        """
        if ((self.pan_is_active or self.zoom_is_active) and
                self.__mouse_btn_is_pressed):
            return

        ax0 = self.fig.axes[0]
        fig = self.fig
        fig.canvas.restore_region(self.__figbckground)

        # ---- Draw the cursor guide and the xy coordinates on the graph.

        # Trace a red vertical guide (line) that folows the mouse marker :

        x, y = event.xdata, event.ydata
        self._draw_mouse_cursor(x, y)
        if all((x, y)):
            self.xycoord.set_visible(True)
            if self.dformat == 0:
                self.xycoord.set_text(
                    '{:0.3f} mbgs\n{:0.1f} days'.format(y, x))
            else:
                date = xldate_as_tuple(x-self.dt4xls2mpl, 0)
                self.xycoord.set_text('{:0.3f} mbgs\n{}/{}/{}'.format(
                    y, date[2], date[1], date[0]))
            ax0.draw_artist(self.xycoord)
        else:
            self.vguide.set_visible(False)
            self.xycoord.set_visible(False)

        if self.rect_select_is_active and self.__mouse_btn_is_pressed:
            self._draw_rect_selection(x, y)
        if (self.brf_eval_widget.btn_seldata.value() and
                self.__mouse_btn_is_pressed):
            self._draw_brf_selection(x)

        # ---- Remove Peak Cursor
        if self.btn_delpeak.value() and len(self.peak_indx) > 0:
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
            if np.min(d) < 15:
                # Put the cross over the nearest peak.
                indx = np.argmin(d)
                self.xcross.set_xdata(xpeak[indx])
                self.xcross.set_ydata(ypeak[indx])
                self.xcross.set_visible(True)
            else:
                self.xcross.set_visible(False)
        else:
            self.xcross.set_visible(False)

        ax0.draw_artist(self.xcross)

        # Update the canvas
        self.fig.canvas.blit()

    def onrelease(self, event):
        """
        Handle when a button of the mouse is released after the graph has
        been clicked.
        """
        self.__mouse_btn_is_pressed = False
        # Disconnect the pan and zoom callback before drawing the canvas again.
        if self.pan_is_active:
            self.toolbar.release_pan(event)
        if self.zoom_is_active:
            self.toolbar.release_zoom(event)
        if self.rect_select_is_active:
            self._rect_selection[1] = (event.xdata, event.ydata)
            self._rect_selector.set_visible(False)
            self.on_rect_select()
        if self.brf_eval_widget.btn_seldata.value() is True:
            self._selected_brfperiod[1] = event.xdata
            self._brf_selector.set_visible(False)
            self.on_brf_select()

        if self.is_all_btn_raised():
            self.draw()
        else:
            if event.button != 1:
                return
            self.__addPeakVisible = True
            self.draw_mrc()
        self.on_mouse_move(event)

    def onclick(self, event):
        """Handle when the graph is clicked with the mouse."""
        self.__mouse_btn_is_pressed = True
        x, y = event.x, event.y
        if x is None or y is None or self.wldset is None:
            return

        if self.btn_delpeak.value():
            if len(self.peak_indx) == 0:
                return

            xt = np.empty(len(self.peak_indx))
            yt = np.empty(len(self.peak_indx))
            xpeak = self.time[self.peak_indx] + self.dt4xls2mpl * self.dformat
            ypeak = self.water_lvl[self.peak_indx]

            ax = self.fig.axes[0]
            for i in range(len(self.peak_indx)):
                xt[i], yt[i] = ax.transData.transform((xpeak[i], ypeak[i]))

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
                self.draw_mrc()
        elif not self.btn_addpeak.autoRaise():
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
        elif self.brf_eval_widget.btn_seldata.value() is True:
            self._selected_brfperiod[0] = event.xdata
        elif self.rect_select_is_active:
            self._rect_selection[0] = (event.xdata, event.ydata)
        else:
            self.draw()


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

    # ---- Check Min/Max

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

    # ---- Optimization

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
            reader = list(csv.reader(f, delimiter=','))

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
            except Exception:
                self.color[i] = '#FFFFFF'


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


# %% if __name__ == '__main__'

if __name__ == '__main__':
    import sys
    from projet.manager_data import DataManager
    from projet.reader_projet import ProjetReader
    from gwhat import __rootdir__

    app = QApplication(sys.argv)

    ft = app.font()
    ft.setFamily('Segoe UI')
    ft.setPointSize(11)
    app.setFont(ft)

    pf = osp.join(__rootdir__, '../Projects/Example/Example.gwt')
    pr = ProjetReader(pf)
    dm = DataManager()

    hydrocalc = WLCalc(dm)
    hydrocalc.show()

    dm.set_projet(pr)

    sys.exit(app.exec_())
