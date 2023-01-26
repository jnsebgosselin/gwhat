# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from gwhat.hydrocalc.axeswidgets import WLCalcAxesWidget


# ---- Standard library imports
import io
import os.path as osp
import datetime

# ---- Third party imports
import numpy as np
from qtpy.QtGui import QImage
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSlot as QSlot
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtWidgets import (
    QGridLayout, QTabWidget, QApplication, QWidget, QMainWindow,
    QToolBar, QFrame, QMessageBox)

import matplotlib as mpl
from matplotlib.figure import Figure as MplFigure
from matplotlib.patches import Rectangle
from matplotlib.transforms import ScaledTranslation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

from xlrd import xldate_as_tuple
from xlrd.xldate import xldate_from_date_tuple

# ---- Local imports
from gwhat.hydrocalc.recession.recession_tool import MasterRecessionCalcTool
from gwhat.brf_mod import BRFManager
from gwhat.config.gui import FRAME_SYLE
from gwhat.config.main import CONF
from gwhat.gwrecharge.gwrecharge_gui import RechgEvalWidget
from gwhat.utils.qthelpers import create_toolbutton
from gwhat.utils import icons
from gwhat.utils.icons import QToolButtonNormal, get_iconsize
from gwhat.widgets.buttons import OnOffToolButton, OnOffPushButton
from gwhat.widgets.layout import VSep
from gwhat.widgets.fileio import SaveFileMixin


class WLCalc(QWidget, SaveFileMixin):
    """
    This is the interface where are plotted the water level time series. It is
    possible to dynamically zoom and span the data, change the display,
    i.e. display the data as a continuous line or individual dot, perform a
    MRC and ultimately estimate groundwater recharge.
    """
    sig_date_format_changed = QSignal()

    def __init__(self, datamanager, parent=None):
        QWidget.__init__(self, parent)
        SaveFileMixin.__init__(self)

        self.tools = {}
        self._navig_and_select_tools = []
        self._wldset = None

        self.dmngr = datamanager
        self.dmngr.wldsetChanged.connect(self.set_wldset)
        self.dmngr.wxdsetChanged.connect(self.set_wxdset)

        # Setup recharge calculation tool.
        self.rechg_eval_widget = RechgEvalWidget(parent=self)
        self.rechg_eval_widget.sig_new_gluedf.connect(self.draw_glue_wl)

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

        # Setup wlcalc tools.
        self.brf_eval_widget = BRFManager(parent=self)
        self.install_tool(self.brf_eval_widget)

        self.mrc_eval_widget = MasterRecessionCalcTool(parent=self)
        self.install_tool(self.mrc_eval_widget)

        index = self.tools_tabwidget.addTab(self.rechg_eval_widget, 'Recharge')
        self.tools_tabwidget.setTabToolTip(
            index,
            ("A tool to evaluate groundwater recharge and its "
             "uncertainty from observed water levels and daily "
             "weather data."))

        self.tools_tabwidget.setCurrentIndex(
            CONF.get('hydrocalc', 'current_tool_index'))

        # Setup water levels and weather datasets.
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

        # Rain.
        self.h_rain, = ax1.plot([], [])

        # Precipitation.
        self.h_ptot, = ax1.plot([], [])

        # Evapotranspiration.
        self.h_etp, = ax1.plot([], [], color='#FF6666', lw=1.5, zorder=500,
                               ls='-')

        # Predicted GLUE water levels
        self.glue_plt, = ax0.plot([], [])

        # Rectangular selection box.
        self._rect_selection = [(None, None), (None, None)]
        self._rect_selector = Rectangle(
            (0, 0), 0, 0, edgecolor='black', facecolor='red', linestyle=':',
            fill=True, alpha=0.15, visible=False)
        ax0.add_patch(self._rect_selector)

        # x and y coorrdinate labels displayed at the right-bottom corner
        # of the graph
        offset = ScaledTranslation(-5/72, 5/72, self.fig.dpi_scale_trans)
        self.xycoord = ax0.text(
            1, 0, '', ha='right', transform=ax0.transAxes + offset)
        self.xycoord.set_visible(False)

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
        self._navig_toolbar = NavigationToolbar2QT(self.canvas, parent=self)
        self._navig_toolbar.hide()

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
                    self.btn_show_meas_wl, None,
                    self.btn_rect_select, self.btn_clear_select,
                    self.btn_del_select, self.btn_undo_changes,
                    self.btn_clear_changes, self.btn_commit_changes]:
            if btn is None:
                toolbar.addSeparator()
            else:
                toolbar.addWidget(btn)
        return toolbar

    def __initUI__(self):
        # Setup the left widget.
        left_widget = QMainWindow()

        self.toolbar = self._setup_toolbar()
        self.toolbar.setStyleSheet("QToolBar {border: 0px; spacing:1px;}")
        self.toolbar.setFloatable(False)
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(get_iconsize('normal'))
        left_widget.addToolBar(Qt.TopToolBarArea, self.toolbar)
        left_widget.setCentralWidget(self.fig_frame_widget)

        # Setup the tools tab area.
        self.tools_tabwidget = QTabWidget()

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

    def install_tool(self, tool):
        """Install the provided tool in WLCalc."""
        if tool.name() in self.tools:
            print(
                "WARNING: There is already a tool named '{}' installed "
                "in WLCalc.".format(tool.name()))
            return
        tool.register_tool(self)
        self.tools[tool.name()] = tool

    def install_axeswidget(self, axes_widget: WLCalcAxesWidget,
                           active: bool = False):
        """Install the provided axes widget."""
        self._axes_widgets.append(axes_widget)
        axes_widget.set_active(active)

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

        # Setup BRF widget.
        for tool in self.tools.values():
            tool.set_wldset(wldset)

        self.setup_hydrograph()
        self._navig_toolbar.update()

    def set_wxdset(self, wxdset):
        """Set the weather dataset."""
        self.rechg_eval_widget.set_wxdset(wxdset)
        self.draw_weather()

    def close(self):
        """Close this groundwater level calc window."""
        CONF.set('hydrocalc', 'current_tool_index',
                 self.tools_tabwidget.currentIndex())
        CONF.set('hydrocalc', 'show_weather', self.btn_show_weather.value())
        CONF.set('hydrocalc', 'show_glue', self.btn_show_glue.value())
        CONF.set('hydrocalc', 'show_meas_wl', self.btn_show_meas_wl.value())

        for tool in self.tools.values():
            tool.close_tool()

        super().close()

    def copy_to_clipboard(self):
        """Put a copy of the figure on the clipboard."""
        buf = io.BytesIO()
        self.fig.savefig(buf, dpi=300)
        QApplication.clipboard().setImage(QImage.fromData(buf.getvalue()))
        buf.close()

    # ---- Navigation and selection tools
    def register_navig_and_select_tool(self, tool):
        """
        Add the tool to the list of tools that are available to interactively
        navigate and select the data.
        """
        if not isinstance(tool, (OnOffToolButton, OnOffPushButton)):
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
            if self._navig_toolbar.mode.name == 'NONE':
                self._navig_toolbar.zoom()
        else:
            if self._navig_toolbar.mode.name == 'ZOOM':
                self._navig_toolbar.zoom()

    @property
    def pan_is_active(self):
        """Return whether the panning of the graph is active or not."""
        return self.btn_pan.value()

    @QSlot(bool)
    def pan_is_active_changed(self, pan_is_active):
        """Handle when the state of the button to pan the graph changes."""
        if self.pan_is_active:
            self.toggle_navig_and_select_tools(self.btn_pan)
            if self._navig_toolbar.mode.name == 'NONE':
                self._navig_toolbar.pan()
        else:
            if self._navig_toolbar.mode.name == 'PAN':
                self._navig_toolbar.pan()

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

    def zoom_axis(self, which: str, how: str):
        """
        Zoom in or out the specified axis.

        Parameters
        ----------
        which : str
            The axis to zoom in or out. Valid values are 'x' or 'y'.
        how : str
            Whether to zoom in or zoom out. Valid values are 'out' or 'in'.
        """
        ax = self.fig.axes[0]
        if which == 'x':
            xmin, xmax = ax.get_xlim()
            xoffset = 0.1 * abs(xmax - xmin)
            if how == 'in':
                xoffset *= -1
            ax.set_xlim(xmin=xmin - xoffset, xmax=xmax + xoffset)
        elif which == 'y':
            ymin, ymax = ax.get_ylim()
            yoffset = 0.025 * abs(ymax - ymin)
            if how == 'in':
                yoffset *= -1
            ax.set_ylim(ymin=ymin - yoffset, ymax=ymax + yoffset)
        self.draw()

    def move_axis_range(self, direction: str):
        """
        Move axis in the specified direction.

        Parameters
        ----------
        direction : str
            The direction in which to move the axis. Valid values are
            'left', 'right', 'up', and 'down'.
        """
        ax = self.fig.axes[0]
        if direction in ('left', 'right'):
            xmin, xmax = ax.get_xlim()
            xoffset = 0.1 * abs(xmax - xmin)
            if direction == 'right':
                xoffset *= -1
            ax.set_xlim(xmin=xmin + xoffset, xmax=xmax + xoffset)
        elif direction in ('up', 'down'):
            ymin, ymax = ax.get_ylim()
            yoffset = 0.025 * abs(ymax - ymin)
            if direction == 'down':
                yoffset *= -1
            ax.set_ylim(ymin=ymin + yoffset, ymax=ymax + yoffset)
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
        # TODO: reimplement this as tight_layout. See Seismate implementation.
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
        self.draw_weather()
        self.draw_glue_wl()
        self.sig_date_format_changed.emit()
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
        xycoord_is_visible = self.xycoord.get_visible()
        self.xycoord.set_visible(False)
        for widget in self._axes_widgets:
            widget.clear()

        self.canvas.draw()
        self._figbckground = self.fig.canvas.copy_from_bbox(self.fig.bbox)

        self.xycoord.set_visible(xycoord_is_visible)
        self.fig.axes[0].draw_artist(self.xycoord)
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

    # ----- Mouse Event Handlers
    def on_fig_leave(self, event):
        """Handle when the mouse cursor leaves the graph."""
        self.draw()

    def on_axes_enter(self, event):
        """Handle when the mouse cursor enters a new axe."""
        if self.rect_select_is_active:
            self._navig_toolbar.set_cursor(2)

    def on_axes_leave(self, event):
        """Handle when the mouse cursor leaves an axe."""
        self._navig_toolbar.set_cursor(1)

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

        # Disconnect the pan and zoom callback before drawing the canvas again.
        if self.pan_is_active:
            self._navig_toolbar.release_pan(event)
        if self.zoom_is_active:
            self._navig_toolbar.release_zoom(event)
        if self.rect_select_is_active:
            self._rect_selection[1] = (event.xdata, event.ydata)
            self._rect_selector.set_visible(False)
            self.on_rect_select()

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
        if self.rect_select_is_active:
            self._rect_selection[0] = (event.xdata, event.ydata)

        # Update all axes widget.
        for widget in self._axes_widgets:
            if widget.get_active():
                widget.onpress(event)
        self.draw()

    def update_axeswidgets(self):
        """"Update all active axes widgets."""
        if self._figbckground is None:
            return
        self.canvas.restore_region(self._figbckground)

        # Update all axes widget.
        for widget in self._axes_widgets:
            if widget.get_active():
                widget._update()

        self.canvas.blit()


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
