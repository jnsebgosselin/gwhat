# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

# ---- Standard library imports
import io
from time import perf_counter
import csv
import os
import os.path as osp
import datetime

# ---- Third party imports
import numpy as np
import pandas as pd
from qtpy.QtGui import QImage
from PyQt5.QtCore import Qt, QObject
from PyQt5.QtCore import pyqtSlot as QSlot
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtWidgets import (
    QGridLayout, QComboBox, QTextEdit, QSizePolicy, QPushButton, QLabel,
    QTabWidget, QApplication, QWidget, QMainWindow, QToolBar, QFrame,
    QMessageBox, QFileDialog)

import matplotlib as mpl
from matplotlib.widgets import AxesWidget
import matplotlib.dates as mdates
from matplotlib.figure import Figure as MplFigure
from matplotlib.patches import Rectangle
from matplotlib.transforms import ScaledTranslation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

from xlrd import xldate_as_tuple
from xlrd.xldate import xldate_from_date_tuple

# ---- Local imports
from gwhat.recession.recession_calc import calculate_mrc
from gwhat.brf_mod import BRFManager
from gwhat.config.gui import FRAME_SYLE
from gwhat.config.main import CONF
from gwhat.gwrecharge.gwrecharge_gui import RechgEvalWidget
from gwhat.utils import icons
from gwhat.utils.icons import QToolButtonNormal, get_iconsize
from gwhat.utils.qthelpers import create_toolbutton
from gwhat.widgets.buttons import ToolBarWidget
from gwhat.widgets.buttons import OnOffToolButton
from gwhat.widgets.layout import VSep
from gwhat.widgets.fileio import SaveFileMixin


class WLCalc(QWidget, SaveFileMixin):
    """
    This is the interface where are plotted the water level time series. It is
    possible to dynamically zoom and span the data, change the display,
    i.e. display the data as a continuous line or individual dot, perform a
    MRC and ultimately estimate groundwater recharge.
    """
    sig_new_mrc = QSignal()

    def __init__(self, datamanager, parent=None):
        QWidget.__init__(self, parent)
        SaveFileMixin.__init__(self)

        self._navig_and_select_tools = []
        self._last_toggled_navig_and_select_tool = None
        self._wldset = None

        self.dmngr = datamanager
        self.dmngr.wldsetChanged.connect(self.set_wldset)
        self.dmngr.wxdsetChanged.connect(self.set_wxdset)

        # Setup recharge calculation tool.
        self.rechg_eval_widget = RechgEvalWidget(parent=self)
        self.rechg_eval_widget.sig_new_gluedf.connect(self.draw_glue_wl)

        # Setup BRF calculation tool.
        self.brf_eval_widget = BRFManager(parent=self)
        self.brf_eval_widget.sig_brfperiod_changed.connect(self.plot_brfperiod)
        self.brf_eval_widget.sig_select_brfperiod_requested.connect(
            self.toggle_brfperiod_selection)

        self._figbckground = None
        self._axes_widgets = []
        self.__mouse_btn_is_pressed = False

        # Calcul the delta between the datum of Excel and Maplotlib numeric
        # date system.
        t_xls = xldate_from_date_tuple((2000, 1, 1), 0)
        t_mpl = mpl.dates.date2num(datetime.datetime(2000, 1, 1))
        self.dt4xls2mpl = t_mpl - t_xls

        # The date format can either be 0 for Excel format or 1 for Matplotlib
        # format.
        self.dformat = 1

        # Selected water level data.
        self.wl_selected_i = []

        # Soil Profiles :
        self.soilFilename = []

        # Initialize the GUI
        self.precip_bwidth = 7
        self._setup_mpl_canvas()
        self.__initUI__()
        self.btn_pan.setValue(True)
        self.setup_ax_margins(None)
        self.set_wldset(self.dmngr.get_current_wldset())
        self.set_wxdset(self.dmngr.get_current_wxdset())

    def _setup_mpl_canvas(self):

        # Setup the figure canvas.
        self.fig = MplFigure(facecolor='white')
        self.canvas = FigureCanvasQTAgg(self.fig)

        self.canvas.mpl_connect('button_press_event', self.onpress)
        self.canvas.mpl_connect('button_release_event', self.onrelease)
        self.canvas.mpl_connect('resize_event', self.setup_ax_margins)
        self.canvas.mpl_connect('motion_notify_event', self.onmove)
        self.canvas.mpl_connect('figure_leave_event', self.on_fig_leave)
        self.canvas.mpl_connect('axes_enter_event', self.on_axes_enter)
        self.canvas.mpl_connect('axes_leave_event', self.on_axes_leave)

        # Put figure canvas in a QFrame widget so that it has a frame.
        self.fig_frame_widget = QFrame()
        self.fig_frame_widget.setMinimumSize(200, 200)
        self.fig_frame_widget.setFrameStyle(FRAME_SYLE)
        self.fig_frame_widget.setLineWidth(2)
        self.fig_frame_widget.setMidLineWidth(1)
        fig_frame_layout = QGridLayout(self.fig_frame_widget)
        fig_frame_layout.setContentsMargins(0, 0, 0, 0)
        fig_frame_layout.addWidget(self.canvas, 0, 0)

        # Setup the Water Level (Host) axe.
        ax0 = self.fig.add_axes([0, 0, 1, 1], zorder=100)
        ax0.patch.set_visible(False)
        ax0.invert_yaxis()

        # Setup the Precipitation axe.
        ax1 = ax0.twinx()
        ax1.patch.set_visible(False)
        ax1.set_zorder(50)
        ax1.set_navigate(False)

        # Setup the ticks
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
            -1, color='black', zorder=40, linestyle='--', lw=1, visible=False)

        # x and y coorrdinate labels displayed at the right-bottom corner
        # of the graph
        offset = ScaledTranslation(-5/72, 5/72, self.fig.dpi_scale_trans)
        self.xycoord = ax0.text(
            1, 0, '', ha='right', transform=ax0.transAxes + offset)
        self.xycoord.set_visible(False)

        # Axes span highlight.
        self.axvspan_highlight = self.fig.axes[0].axvspan(
            0, 1, visible=False, color='red', linewidth=1,
            ls='-', alpha=0.3)

    def _setup_toolbar(self):
        """Setup the main toolbar of the water level calc tool."""

        # Save and copy.
        self.btn_copy_to_clipboard = create_toolbutton(
            self, icon='copy_clipboard',
            text="Copy",
            tip="Put a copy of the figure on the Clipboard.",
            triggered=self.copy_to_clipboard,
            shortcut='Ctrl+C')

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
        self.btn_show_glue.setValue(
            CONF.get('hydrocalc', 'show_glue', True), silent=True)

        self.btn_show_weather = OnOffToolButton('show_meteo', size='normal')
        self.btn_show_weather.setToolTip("""Show or hide weather data.""")
        self.btn_show_weather.sig_value_changed.connect(self.draw_weather)
        self.btn_show_weather.setValue(
            CONF.get('hydrocalc', 'show_weather', True), silent=True)

        self.btn_show_mrc = OnOffToolButton('mrc_calc', size='normal')
        self.btn_show_mrc.setToolTip(
            "Show or hide water levels predicted with the MRC.")
        self.btn_show_mrc.sig_value_changed.connect(
            self.btn_show_mrc_isclicked)
        self.btn_show_mrc.setValue(
            CONF.get('hydrocalc', 'show_mrc', True), silent=True)

        self.btn_show_meas_wl = OnOffToolButton(
            'manual_measures', size='normal')
        self.btn_show_meas_wl.setToolTip(
            "Show or hide water levels measured manually in the well.")
        self.btn_show_meas_wl.sig_value_changed.connect(self.draw_meas_wl)
        self.btn_show_meas_wl.setValue(
            CONF.get('hydrocalc', 'show_meas_wl', True), silent=True)

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
        self.btn_clear_select.clicked.connect(
            lambda: self.clear_selected_wl(draw=True))

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
        toolbar = QToolBar()
        for btn in [self.btn_copy_to_clipboard, None,
                    self.btn_home, self.btn_fit_waterlevels, self.btn_pan,
                    self.btn_zoom_to_rect, None,
                    self.btn_wl_style, self.btn_dateFormat, None,
                    self.btn_show_glue, self.btn_show_weather,
                    self.btn_show_mrc, self.btn_show_meas_wl, None,
                    self.btn_rect_select, self.btn_clear_select,
                    self.btn_del_select, self.btn_undo_changes,
                    self.btn_clear_changes, self.btn_commit_changes]:
            if btn is None:
                toolbar.addSeparator()
            else:
                toolbar.addWidget(btn)
        return toolbar

    def _setup_mrc_tool(self):
        """Setup the tool to evaluate the MRC."""

        # Setup the mrc period selector.
        self.mrc_selector = WLCalcVSpanSelector(self.fig.axes[0])
        self.install_axeswidget(self.mrc_selector)
        self.mrc_selector.sig_span_selected.connect(self.add_mrcperiod)
        self._mrc_period_xdata = []
        self._mrc_period_axvspans = []
        self._mrc_period_memory = [[], ]

        # ---- MRC parameters
        self.MRC_type = QComboBox()
        self.MRC_type.addItems(['Linear', 'Exponential'])
        self.MRC_type.setCurrentIndex(1)

        self.MRC_results = QTextEdit()
        self.MRC_results.setReadOnly(True)
        self.MRC_results.setMinimumHeight(25)
        self.MRC_results.setMinimumWidth(100)

        self.MRC_results.setSizePolicy(
            QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred))

        # Setup the MRC toolbar
        self.btn_undo = create_toolbutton(
            parent=self,
            icon='undo',
            iconsize=get_iconsize('normal'),
            tip='Undo',
            triggered=self.undo_mrc_period)
        self.btn_undo.setEnabled(False)

        self.btn_clearPeak = create_toolbutton(
            parent=self,
            icon='clear_search',
            iconsize=get_iconsize('normal'),
            tip='Clear all extremum from the graph',
            triggered=self.clear_all_mrcperiods)

        self.btn_addpeak = OnOffToolButton('mrc_add', size='normal')
        self.btn_addpeak.sig_value_changed.connect(self.btn_addpeak_isclicked)
        self.btn_addpeak.setToolTip(
            "Left-click on the graph to select the recession periods "
            "to use for the MRC assessment.")
        self.register_navig_and_select_tool(self.btn_addpeak)

        self.btn_delpeak = OnOffToolButton('erase', size='normal')
        self.btn_delpeak.clicked.connect(self.btn_delpeak_isclicked)
        self.btn_delpeak.setToolTip(
            "Left-click on a selected recession period to remove it.")
        self.register_navig_and_select_tool(self.btn_delpeak)

        self.btn_save_mrc = create_toolbutton(
            parent=self,
            icon='save',
            iconsize=get_iconsize('normal'),
            tip='Save calculated MRC to file.',
            triggered=lambda: self.save_mrc_tofile())

        self.btn_MRCalc = QPushButton('Compute MRC')
        self.btn_MRCalc.clicked.connect(self.btn_MRCalc_isClicked)
        self.btn_MRCalc.setToolTip('<p>Calculate the Master Recession Curve'
                                   ' (MRC) for the selected time periods.</p>')

        mrc_tb = ToolBarWidget()
        for btn in [self.btn_undo, self.btn_clearPeak, self.btn_addpeak,
                    self.btn_delpeak, self.btn_save_mrc]:
            mrc_tb.addWidget(btn)

        # Setup the MRC Layout.
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
        mrc_lay.setColumnStretch(2, 500)

        return self.mrc_eval_widget

    def __initUI__(self):
        # Setup the left widget.
        left_widget = QMainWindow()

        toolbar = self._setup_toolbar()
        toolbar.setStyleSheet("QToolBar {border: 0px; spacing:1px;}")
        toolbar.setFloatable(False)
        toolbar.setMovable(False)
        toolbar.setIconSize(get_iconsize('normal'))
        left_widget.addToolBar(Qt.TopToolBarArea, toolbar)
        left_widget.setCentralWidget(self.fig_frame_widget)

        # Setup the tools tab area.
        self.tools_tabwidget = QTabWidget()
        self.mrc_eval_widget = self._setup_mrc_tool()
        self.tools_tabwidget.addTab(self.mrc_eval_widget, 'MRC')
        self.tools_tabwidget.setTabToolTip(
            0, ("<p>A tool to evaluate the master recession curve"
                " of the hydrograph.</p>"))
        self.tools_tabwidget.addTab(self.rechg_eval_widget, 'Recharge')
        self.tools_tabwidget.setTabToolTip(
            1, ("<p>A tool to evaluate groundwater recharge and its"
                " uncertainty from observed water levels and daily "
                " weather data.</p>"))
        self.tools_tabwidget.addTab(self.brf_eval_widget, 'BRF')
        self.tools_tabwidget.setTabToolTip(
            2, ("<p>A tool to evaluate the barometric response function of"
                " the well.</p>"))
        self.tools_tabwidget.currentChanged.connect(
            lambda: self.toggle_brfperiod_selection(False))
        self.tools_tabwidget.setCurrentIndex(
            CONF.get('hydrocalc', 'current_tool_index'))

        # Setup the right panel.
        self.right_panel = QFrame()
        right_panel_layout = QGridLayout(self.right_panel)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        right_panel_layout.addWidget(self.dmngr, 0, 0)
        right_panel_layout.addWidget(self.tools_tabwidget, 1, 0)
        right_panel_layout.setRowStretch(2, 100)
        right_panel_layout.setSpacing(15)

        # ---- Setup the main layout
        main_layout = QGridLayout(self)

        main_layout.addWidget(left_widget, 0, 0)
        main_layout.addWidget(VSep(), 0, 1)
        main_layout.addWidget(self.right_panel, 0, 2)

        main_layout.setHorizontalSpacing(15)
        main_layout.setColumnStretch(0, 100)

    def install_axeswidget(self, axes_widget):
        """
        Install the provided axes widget in the WLCalc.
        """
        self._axes_widgets.append(axes_widget)

    def emit_warning(self, message, title='Warning'):
        QMessageBox.warning(self, title, message, QMessageBox.Ok)

    @property
    def water_lvl(self):
        return np.array([]) if self.wldset is None else self.wldset.waterlevels

    @property
    def time(self):
        return np.array([]) if self.wldset is None else self.wldset.xldates

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

    def close(self):
        """Close this groundwater level calc window."""
        CONF.set('hydrocalc', 'current_tool_index',
                 self.tools_tabwidget.currentIndex())

        CONF.set('hydrocalc', 'show_mrc', self.btn_show_mrc.value())
        CONF.set('hydrocalc', 'show_weather', self.btn_show_weather.value())
        CONF.set('hydrocalc', 'show_glue', self.btn_show_glue.value())
        CONF.set('hydrocalc', 'show_meas_wl', self.btn_show_meas_wl.value())

        self.brf_eval_widget.close()
        super().close()

    def showEvent(self, event):
        """Extend Qt method"""
        # This is required to make sure the BRF is plotted correctly on
        # restart.
        self.plot_brfperiod()
        super().showEvent(event)

    def copy_to_clipboard(self):
        """Put a copy of the figure on the clipboard."""
        buf = io.BytesIO()
        self.fig.savefig(buf, dpi=300)
        QApplication.clipboard().setImage(QImage.fromData(buf.getvalue()))
        buf.close()

    # ---- MRC handlers
    def add_mrcperiod(self, xdata):
        """
        Add a a new mrc period using the provided xdata.
        """
        try:
            xmin = min(xdata) - self.dt4xls2mpl * self.dformat
            xmax = max(xdata) - self.dt4xls2mpl * self.dformat
        except TypeError:
            return

        for i in reversed(range(len(self._mrc_period_xdata))):
            period_xdata = self._mrc_period_xdata[i]
            if xmin >= period_xdata[0] and xmax <= period_xdata[1]:
                # This means this mrc period is fully enclosed within
                # another period previously selected by the user,
                # so we discard it completely.
                return

            if period_xdata[0] >= xmin and period_xdata[0] <= xmax:
                xmax = max(period_xdata[1], xmax)
                del self._mrc_period_xdata[i]
            elif period_xdata[1] >= xmin and period_xdata[1] <= xmax:
                xmin = min(period_xdata[0], xmin)
                del self._mrc_period_xdata[i]

        self._mrc_period_xdata.append((xmin, xmax))
        self._mrc_period_memory.append(self._mrc_period_xdata.copy())
        self.draw_mrc()

    def remove_mrcperiod(self, xdata):
        """
        Remove the mrc period at xdata if any.
        """
        for i, period_xdata in enumerate(self._mrc_period_xdata):
            period_xmin = period_xdata[0] + (self.dt4xls2mpl * self.dformat)
            period_xmax = period_xdata[1] + (self.dt4xls2mpl * self.dformat)
            if xdata >= period_xmin and xdata <= period_xmax:
                del self._mrc_period_xdata[i]
                self._mrc_period_memory.append(self._mrc_period_xdata.copy())
                self.draw_mrc()
                break

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

        coeffs, hp, std_err, r_squared, rmse = calculate_mrc(
            self.time, self.water_lvl, self._mrc_period_xdata,
            self.MRC_type.currentIndex())
        A = coeffs.A
        B = coeffs.B
        print('MRC Parameters: A={}, B={}'.format(
            'None' if pd.isnull(A) else '{:0.3f}'.format(coeffs.A),
            'None' if pd.isnull(B) else '{:0.3f}'.format(coeffs.B)))

        # Store and plot the results.
        print('Saving MRC interpretation in dataset...')
        self.wldset.set_mrc(
            A, B, self._mrc_period_xdata,
            self.time, hp,
            std_err, r_squared, rmse)

        self.show_mrc_results()
        self.btn_save_mrc.setEnabled(True)
        self.draw_mrc()
        self.sig_new_mrc.emit()

        QApplication.restoreOverrideCursor()

    def show_mrc_results(self):
        """Show MRC results if any."""
        if self.wldset is None:
            self.MRC_results.setHtml('')
            return

        mrc_data = self.wldset.get_mrc()

        coeffs = mrc_data['params']
        if pd.isnull(coeffs.A):
            text = ''
        else:
            text = (
                "∂h/∂t = -A · h + B<br>"
                "A = {:0.5f} day<sup>-1</sup><br>"
                "B = {:0.5f} m/day<br><br>"
                "were ∂h/∂t is the recession rate in m/day, "
                "h is the depth to water table in mbgs, "
                "and A and B are the coefficients of the MRC.<br><br>"
                "Goodness-of-fit statistics :<br>"
                ).format(coeffs.A, coeffs.B)

            fit_stats = {
                'rmse': "RMSE = {} m<br>",
                'r_squared': "r² = {}<br>",
                'std_err': "S = {} m"}
            for key, label in fit_stats.items():
                value = mrc_data[key]
                if value is None:
                    text += label.format('N/A')
                else:
                    text += label.format('{:0.5f}'.format(value))
        self.MRC_results.setHtml(text)

    def load_mrc_from_wldset(self):
        """Load saved MRC results from the project hdf5 file."""
        if self.wldset is not None:
            self._mrc_period_xdata = self.wldset.get_mrc()['peak_indx']
            self._mrc_period_memory[0] = self._mrc_period_xdata.copy()
            self.btn_save_mrc.setEnabled(True)
        else:
            self._mrc_period_xdata = []
            self._mrc_period_memory = [[], ]
            self.btn_save_mrc.setEnabled(False)
        self.show_mrc_results()
        self.draw_mrc()

    def save_mrc_tofile(self, filename=None):
        """Save the master recession curve results to a file."""
        if filename is None:
            filename = osp.join(
                self.dialog_dir,
                "Well_{}_mrc_results.csv".format(self.wldset['Well']))

        filename, filetype = QFileDialog.getSaveFileName(
            self, "Save MRC results", filename, 'Text CSV (*.csv)')

        if filename:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            QApplication.processEvents()
            try:
                self.wldset.save_mrc_tofile(filename)
            except PermissionError:
                self.show_permission_error()
                self.save_mrc_tofile(filename)
            QApplication.restoreOverrideCursor()

    def undo_mrc_period(self):
        """
        Undo the last operation performed by the user on the selection
        of mrc periods.
        """
        if len(self._mrc_period_memory) > 1:
            self._mrc_period_xdata = self._mrc_period_memory[-2].copy()
            del self._mrc_period_memory[-1]
            self.draw_mrc()

    def clear_all_mrcperiods(self):
        """Clear all mrc periods from the graph."""
        if len(self._mrc_period_xdata) > 0:
            self._mrc_period_xdata = []
            self._mrc_period_memory.append([])
        self.draw_mrc()

    # ---- BRF selection
    def plot_brfperiod(self):
        """
        Plot on the graph the vertical lines that are used to define the period
        over which the BRF is evaluated.
        """
        if (not self.brf_eval_widget.is_brfperiod_selection_toggled() and
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
            self.brf_eval_widget.toggle_brfperiod_selection(False)
            if value is True:
                self.emit_warning(
                    "Please import a valid water level dataset first.")
            return

        if value is True:
            self._last_toggled_navig_and_select_tool = None
            for tool in self._navig_and_select_tools:
                if tool.value() is True:
                    self._last_toggled_navig_and_select_tool = tool
                    tool.setValue(False)
                    break
        else:
            self.brf_eval_widget.toggle_brfperiod_selection(False)
            if self._last_toggled_navig_and_select_tool is not None:
                self._last_toggled_navig_and_select_tool.setValue(True)
        self.plot_brfperiod()

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

    # ---- Peaks handlers
    def btn_addpeak_isclicked(self):
        """Handle when the button add_peak is clicked."""
        if self.btn_addpeak.value():
            self.toggle_navig_and_select_tools(self.btn_addpeak)
            self.btn_show_mrc.setValue(True)
        self.mrc_selector.set_active(self.btn_addpeak.value())
        self.draw()

    def btn_delpeak_isclicked(self):
        """Handle when the button btn_delpeak is clicked."""
        if self.btn_delpeak.value():
            self.toggle_navig_and_select_tools(self.btn_delpeak)
            self.btn_show_mrc.setValue(True)
        self.draw()

    # ---- Navigation and selection tools
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

        # Reset BRF selection.
        self.brf_eval_widget.toggle_brfperiod_selection(False)
        self.plot_brfperiod()

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
        self._mrc_period_xdata = []
        self._mrc_period_memory = [[], ]
        self.btn_undo.setEnabled(False)

        self.clear_selected_wl()
        self._update_edit_toolbar_state()

        # Plot observed and predicted water levels
        self._draw_obs_wl()
        self.draw_meas_wl()
        self.draw_glue_wl()
        self.draw_weather()

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
            t = self.wxdset.get_xldates() + self.dt4xls2mpl * self.dformat
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
        right_margin = (
            1 / fwidth if self.btn_show_weather.value() else 0.2 / fwidth)
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

        self._draw_obs_wl()
        self.draw_meas_wl()
        self.draw_mrc()
        self.draw_weather()
        self.draw_glue_wl()
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
        self.axvspan_highlight.set_visible(False)
        for widget in self._axes_widgets:
            widget.clear()

        self.canvas.draw()
        self._figbckground = self.fig.canvas.copy_from_bbox(self.fig.bbox)

        for widget in self._axes_widgets:
            widget.restore()

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

            time = self.wxdset.get_xldates() + self.dt4xls2mpl * self.dformat
            ptot = self.wxdset.data['Ptot'].values
            rain = self.wxdset.data['Rain'].values
            etp = self.wxdset.data['PET'].values

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
        self.setup_ax_margins()

    def draw_mrc(self):
        """
        Draw the periods during which water levels recedes and draw the
        water levels that were predicted with the MRC.
        """
        self._draw_mrc_wl()
        self._draw_mrc_periods()
        self.draw()

    def _draw_obs_wl(self, draw=True):
        """Draw the observed water level data on the graph."""
        self.clear_selected_wl(draw=False)
        if self.wldset is not None:
            self._obs_wl_plt.set_data(
                self.time + (self.dt4xls2mpl * self.dformat),
                self.water_lvl)
        self._obs_wl_plt.set_visible(self.wldset is not None)
        if draw:
            self.draw()

    def _draw_mrc_wl(self):
        """Draw the water levels that were predicted with the MRC."""
        if (self.wldset is not None and self.btn_show_mrc.value() and
                self.wldset.mrc_exists()):
            self._mrc_plt.set_visible(True)
            mrc_data = self.wldset.get_mrc()
            self._mrc_plt.set_data(
                mrc_data['time'] + self.dt4xls2mpl * self.dformat,
                mrc_data['recess'])
        else:
            self._mrc_plt.set_visible(False)

    def _draw_mrc_periods(self):
        """Draw the periods that will be used to compute the MRC."""
        self.btn_undo.setEnabled(len(self._mrc_period_memory) > 1)
        for axvspan in self._mrc_period_axvspans:
            axvspan.set_visible(False)
        if self.wldset is not None and self.btn_show_mrc.value():
            for i, xdata in enumerate(self._mrc_period_xdata):
                xmin = xdata[0] + (self.dt4xls2mpl * self.dformat)
                xmax = xdata[1] + (self.dt4xls2mpl * self.dformat)
                try:
                    axvspan = self._mrc_period_axvspans[i]
                    axvspan.set_visible(True)
                    axvspan.xy = [[xmin, 1], [xmin, 0],
                                  [xmax, 0], [xmax, 1]]
                except IndexError:
                    axvspan = self.fig.axes[0].axvspan(
                        xmin, xmax, visible=True, color='red', linewidth=1,
                        ls='-', alpha=0.1)
                    self._mrc_period_axvspans.append(axvspan)

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
        elif self.brf_eval_widget.is_brfperiod_selection_toggled():
            self.vguide.set_visible(True)
            self.vguide.set_xdata(x)
            self.fig.axes[0].draw_artist(self.vguide)
        else:
            self.vguide.set_visible(False)

    # ----- Mouse Event Handlers
    def is_all_btn_raised(self):
        """
        Return whether all of the tool buttons that can block the panning and
        zooming of the graph are raised.
        """
        return(self.btn_delpeak.autoRaise() and
               self.btn_addpeak.autoRaise() and
               not self.brf_eval_widget.is_brfperiod_selection_toggled())

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

    def onmove(self, event):
        """
        Draw the vertical mouse guideline and the x and y coordinates of the
        mouse cursor on the graph.
        """
        if ((self.pan_is_active or self.zoom_is_active) and
                self.__mouse_btn_is_pressed):
            return

        ax0 = self.fig.axes[0]
        self.canvas.restore_region(self._figbckground)

        # Draw the vertical cursor guide.
        x, y = event.xdata, event.ydata
        self._draw_mouse_cursor(x, y)

        # Draw the xy coordinates on the graph.
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
            self.xycoord.set_visible(False)

        if self.rect_select_is_active and self.__mouse_btn_is_pressed:
            self._draw_rect_selection(x, y)
        if (self.brf_eval_widget.is_brfperiod_selection_toggled() and
                self.__mouse_btn_is_pressed):
            self._draw_brf_selection(x)

        # Draw mrc period highlight.
        if self.btn_delpeak.value() and len(self._mrc_period_axvspans) > 0:
            if event.xdata:
                for xdata in self._mrc_period_xdata:
                    xdata_min = xdata[0] + (self.dt4xls2mpl * self.dformat)
                    xdata_max = xdata[1] + (self.dt4xls2mpl * self.dformat)
                    if event.xdata >= xdata_min and event.xdata <= xdata_max:
                        self.axvspan_highlight.set_visible(True)
                        self.axvspan_highlight.xy = [[xdata_min, 1],
                                                     [xdata_min, 0],
                                                     [xdata_max, 0],
                                                     [xdata_max, 1]]
                        break
                else:
                    self.axvspan_highlight.set_visible(False)
            else:
                self.axvspan_highlight.set_visible(False)
            ax0.draw_artist(self.axvspan_highlight)

        # Update all axes widget.
        for widget in self._axes_widgets:
            if widget.get_active():
                widget.onmove(event)

        # Update the canvas
        self.canvas.blit()

    def onrelease(self, event):
        """
        Handle when a button of the mouse is released after the graph has
        been clicked.
        """
        self.__mouse_btn_is_pressed = False
        self.vguide.set_color('black')

        # Disconnect the pan and zoom callback before drawing the canvas again.
        if self.pan_is_active:
            self.toolbar.release_pan(event)
        if self.zoom_is_active:
            self.toolbar.release_zoom(event)
        if self.rect_select_is_active:
            self._rect_selection[1] = (event.xdata, event.ydata)
            self._rect_selector.set_visible(False)
            self.on_rect_select()
        if self.brf_eval_widget.is_brfperiod_selection_toggled():
            self._selected_brfperiod[1] = event.xdata
            self._brf_selector.set_visible(False)
            self.on_brf_select()

        # Update all axes widget.
        for widget in self._axes_widgets:
            if widget.get_active():
                widget.onrelease(event)

        self.draw()

    def onpress(self, event):
        """Handle when the graph is clicked with the mouse."""
        self.__mouse_btn_is_pressed = True
        if event.x is None or event.y is None or self.wldset is None:
            return

        # Remove mrc period.
        if self.btn_delpeak.value() and len(self._mrc_period_xdata) > 0:
            self.axvspan_highlight.set_visible(False)
            self.remove_mrcperiod(event.xdata)
        elif self.brf_eval_widget.is_brfperiod_selection_toggled():
            self._selected_brfperiod[0] = event.xdata
            self.vguide.set_color('red')
            self.draw()
            self.onmove(event)
        elif self.rect_select_is_active:
            self._rect_selection[0] = (event.xdata, event.ydata)

        # Update all axes widget.
        for widget in self._axes_widgets:
            if widget.get_active():
                widget.onpress(event)

        self.draw()


class WLCalcVSpanSelector(AxesWidget, QObject):
    sig_span_selected = QSignal(tuple)

    def __init__(self, ax, useblit=True):
        AxesWidget.__init__(self, ax)
        QObject.__init__(self)
        self.visible = True
        self.useblit = useblit and self.canvas.supports_blit

        self.axvspan = ax.axvspan(
            ax.get_xbound()[0], ax.get_xbound()[0], visible=False,
            color='red', linewidth=1, ls='-', animated=self.useblit,
            alpha=0.1)

        self.axvline = ax.axvline(
            ax.get_ybound()[0], visible=False, color='black', linewidth=1,
            ls='--', animated=self.useblit)

        self._onpress_xdata = []
        self._onpress_button = None
        self._onrelease_xdata = []
        super().set_active(False)

    def set_active(self, active):
        """
        Set whether the selector is active.
        """
        self._onpress_xdata = []
        self._onpress_button = None
        self._onrelease_xdata = []
        super().set_active(active)

    def clear(self):
        """
        Clear the selector.

        This method must be called by the canvas BEFORE making a copy of
        the canvas background.
        """
        self.__axvspan_visible = self.axvspan.get_visible()
        self.__axvline_visible = self.axvline.get_visible()
        self.axvspan.set_visible(False)
        self.axvline.set_visible(False)

    def restore(self):
        """
        Restore the selector.

        This method must be called by the canvas AFTER a copy has been made
        of the canvas background.
        """
        self.axvspan.set_visible(self.__axvspan_visible)
        self.ax.draw_artist(self.axvspan)

        self.axvline.set_visible(self.__axvline_visible)
        self.ax.draw_artist(self.axvline)

    def onpress(self, event):
        """Handler for the button_press_event event."""
        if event.button == 1 and event.xdata:
            if self._onpress_button in [None, event.button]:
                self._onpress_button = event.button
                self._onpress_xdata.append(event.xdata)
                self.axvline.set_visible(False)
                self.axvspan.set_visible(True)
                if len(self._onpress_xdata) == 1:
                    self.axvspan.xy = [[self._onpress_xdata[0], 1],
                                       [self._onpress_xdata[0], 0],
                                       [self._onpress_xdata[0], 0],
                                       [self._onpress_xdata[0], 1]]
                elif len(self._onpress_xdata) == 2:
                    self.axvspan.xy = [[self._onpress_xdata[0], 1],
                                       [self._onpress_xdata[0], 0],
                                       [self._onpress_xdata[1], 0],
                                       [self._onpress_xdata[1], 1]]
        self._update()

    def onrelease(self, event):
        if event.button == self._onpress_button:
            self._onrelease_xdata = self._onpress_xdata.copy()
            if len(self._onrelease_xdata) == 1:
                self.axvline.set_visible(True)
                self.axvspan.set_visible(True)
                if event.xdata:
                    self.axvline.set_xdata((event.xdata, event.xdata))
                    self.axvspan.xy = [[self._onrelease_xdata[0], 1],
                                       [self._onrelease_xdata[0], 0],
                                       [event.xdata, 0],
                                       [event.xdata, 1]]
            elif len(self._onrelease_xdata) == 2:
                self.axvline.set_visible(True)
                self.axvspan.set_visible(False)
                if event.xdata:
                    self.axvline.set_xdata((event.xdata, event.xdata))

                onrelease_xdata = tuple(self._onrelease_xdata)
                self._onpress_button = None
                self._onpress_xdata = []
                self._onrelease_xdata = []
                self.sig_span_selected.emit(onrelease_xdata)
        self._update()

    def onmove(self, event):
        """Handler to draw the selector when the mouse cursor moves."""
        if self.ignore(event):
            return
        if not self.canvas.widgetlock.available(self):
            return
        if not self.visible:
            return

        if event.xdata is None:
            self.axvline.set_visible(False)
            self.axvspan.set_visible(False)
        elif len(self._onpress_xdata) == 0 and len(self._onrelease_xdata) == 0:
            self.axvline.set_visible(True)
            self.axvline.set_xdata((event.xdata, event.xdata))
            self.axvspan.set_visible(False)
        elif len(self._onpress_xdata) == 1 and len(self._onrelease_xdata) == 0:
            self.axvline.set_visible(False)
            self.axvspan.set_visible(True)
        elif len(self._onpress_xdata) == 1 and len(self._onrelease_xdata) == 1:
            self.axvline.set_visible(True)
            self.axvline.set_xdata((event.xdata, event.xdata))
            self.axvspan.set_visible(True)
            self.axvspan.xy = [[self._onrelease_xdata[0], 1],
                               [self._onrelease_xdata[0], 0],
                               [event.xdata, 0],
                               [event.xdata, 1]]
        elif len(self._onpress_xdata) == 2 and len(self._onrelease_xdata) == 1:
            self.axvline.set_visible(False)
            self.axvspan.set_visible(True)
        elif len(self._onpress_xdata) == 2 and len(self._onrelease_xdata) == 2:
            self.axvline.set_visible(False)
            self.axvspan.set_visible(False)
        self._update()

    def _update(self):
        self.ax.draw_artist(self.axvline)
        self.ax.draw_artist(self.axvspan)
        return False


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


if __name__ == '__main__':
    import sys
    from projet.manager_data import DataManager
    from projet.reader_projet import ProjetReader
    from gwhat import __rootdir__
    from gwhat.utils.qthelpers import create_qapplication

    app = create_qapplication()

    pf = osp.join(__rootdir__, '../Projects/Example/Example.gwt')
    pr = ProjetReader(pf)
    dm = DataManager()

    hydrocalc = WLCalc(dm)
    hydrocalc.show()

    dm.set_projet(pr)

    sys.exit(app.exec_())
