# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------
from __future__ import annotations

# ---- Standard library imports
import os.path as osp

# ---- Third party imports
import numpy as np
import pandas as pd
from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import (
    QWidget, QSizePolicy, QPushButton, QGridLayout,
    QLabel, QApplication, QFileDialog, QMessageBox)

# ---- Local imports
from gwhat.hydrocalc.recession.recession_calc import calculate_mrc
from gwhat.hydrocalc.axeswidgets import (
    WLCalcVSpanSelector, WLCalcVSpanHighlighter, WLCalcAxesWidget)
from gwhat.hydrocalc.api import WLCalcTool, wlcalcmethod
from gwhat.utils.dates import (
    xldates_to_datetimeindex, datetimeindex_to_xldates)
from gwhat.utils.qthelpers import create_toolbutton
from gwhat.utils.icons import get_iconsize
from gwhat.widgets.buttons import (
    OnOffToolButton, ToolBarWidget, OnOffPushButton)
from gwhat.widgets.fileio import SaveFileMixin


class FeaturePointPlotter(WLCalcAxesWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._feature_artists = {
            'high_spring': self.ax.plot(
                [], [], marker='v', color='green', ls='none')[0],
            'high_fall': self.ax.plot(
                [], [], marker='v', color='red', ls='none')[0],
            }

        for artist in self._feature_artists.values():
            self.register_artist(artist)

    def set_feature_points(self, feature_points: dict):
        """Set and draw the seasonal pattern feature points."""
        for key, series in feature_points.items():
            if series.empty:
                self._feature_artists[key].set_data([], [])
            else:
                xldates = datetimeindex_to_xldates(series.index)
                self._feature_artists[key].set_data(xldates, series.values)

    def onactive(self, *args, **kwargs):
        self._update()

    def onmove(self, *args, **kwargs):
        self._update()

    def onpress(self, *args, **kwargs):
        self._update()

    def onrelease(self, *args, **kwargs):
        self._update()


class SeasonPatternsCalcTool(WLCalcTool, SaveFileMixin):
    __toolname__ = 'patterns'
    __tooltitle__ = 'Patterns'
    __tooltip__ = ("A tool to pick seasonal patterns on the hydrograph.")

    sig_new_mrc = Signal()

    def __init__(self, parent=None):
        WLCalcTool.__init__(self, parent)
        SaveFileMixin.__init__(self)

        # Whether it is the first time showEvent is called.
        self._first_show_event = True

        # The water level dataset currently registered to this tool.
        self.wldset = None

        # A dict to hold the picked seasonal pattern feature points.
        self._feature_points = {
            'high_fall': pd.Series(),
            'high_spring': pd.Series()
            }

        self.setup()

    def setup(self):
        # self.btn_save_mrc = create_toolbutton(
        #     parent=self,
        #     icon='save',
        #     iconsize=get_iconsize('normal'),
        #     tip='Save calculated MRC to file.',
        #     triggered=lambda: self.save_mrc_tofile())

        self._select_high_spring_btn = OnOffPushButton(
            '  Select High Spring', icon='select_range')
        self._select_high_spring_btn.setToolTip(
            'Select periods when maximum water levels were '
            'reached in the spring.')
        self._select_high_spring_btn.setCheckable(True)
        self._select_high_spring_btn.setFocusPolicy(Qt.NoFocus)
        self._select_high_spring_btn.sig_value_changed.connect(
            lambda: self._btn_select_high_spring_isclicked())

        self._select_high_fall_btn = OnOffPushButton(
            '  Select High Fall', icon='select_range')
        self._select_high_fall_btn.setToolTip(
            'Select periods when maximum water levels were '
            'reached in the fall.')
        self._select_high_fall_btn.setCheckable(True)
        self._select_high_fall_btn.setFocusPolicy(Qt.NoFocus)
        self._select_high_fall_btn.sig_value_changed.connect(
            lambda: self._btn_select_high_fall_isclicked())

        # Setup the Layout.
        layout = QGridLayout(self)

        layout.addWidget(self._select_high_spring_btn, 0, 0)
        layout.addWidget(self._select_high_fall_btn, 1, 0)
        layout.setRowMinimumHeight(2, 5)
        layout.setRowStretch(2, 100)

    # ---- WLCalc integration
    @wlcalcmethod
    def _btn_select_high_spring_isclicked(self):
        """Handle when the button to select high spring periods is clicked."""
        if self._select_high_spring_btn.value():
            self.wlcalc.toggle_navig_and_select_tools(
                self._select_high_spring_btn)
        self.high_spring_selector.set_active(
            self._select_high_spring_btn.value())

    @wlcalcmethod
    def _btn_select_high_fall_isclicked(self):
        """Handle when the button to select high fall periods is clicked."""
        if self._select_high_fall_btn.value():
            self.wlcalc.toggle_navig_and_select_tools(
                self._select_high_fall_btn)
        self.high_fall_selector.set_active(
            self._select_high_fall_btn.value())

    @wlcalcmethod
    def _on_daterange_selected(self, xdata):
        """
        Handle when a new period of high spring or hign fall water levels is
        selected by the user.

        Parameters
        ----------
        xdata : 2-tuple
            A 2-tuple of floats containing the time, in numerical Excel format,
            of the new selected recession period.
        """
        if self._select_high_spring_btn.value():
            key = 'high_spring'
        elif self._select_high_fall_btn.value():
            key = 'high_fall'

        date_times = xldates_to_datetimeindex(xdata)
        date_min = date_times.min()
        date_max = date_times.max()

        # Check and remove previously picked high springor high fall feature
        # points that are within the selected period.
        mask = ((self._feature_points[key].index < date_min) |
                (self._feature_points[key].index > date_max))
        self._feature_points[key] = self._feature_points[key][mask]

        # Find and add the new high spring or high fall feature point within
        # the selected period.
        data = self.wlcalc.wldset.data
        mask = ((data.index >= date_min) &
                (data.index <= date_max))
        argmin = np.argmin(data['WL'][mask])

        self._feature_points[key][
            data.index[mask][argmin]
            ] = data['WL'][mask][argmin]

        self.feature_points_plotter.set_feature_points(self._feature_points)
        self.wlcalc.update_axeswidgets()

    # @wlcalcmethod
    # def _draw_mrc(self):
    #     """
    #     Draw the periods during which water levels recedes and draw the
    #     water levels that were predicted with the MRC.
    #     """
    #     self._draw_mrc_wl()
    #     self._draw_mrc_periods()
    #     self.wlcalc.draw()

    # @wlcalcmethod
    # def _draw_mrc_wl(self):
    #     """Draw the water levels that were predicted with the MRC."""
    #     if (self.wldset is not None and
    #             self.btn_show_mrc.value() and
    #             self.wldset.mrc_exists()):
    #         self._mrc_plt.set_visible(True)
    #         mrc_data = self.wldset.get_mrc()

    #         x = mrc_data['time'] + self.wlcalc.dt4xls2mpl * self.wlcalc.dformat
    #         y = mrc_data['recess']
    #         self._mrc_plt.set_data(x, y)
    #     else:
    #         self._mrc_plt.set_visible(False)

    # @wlcalcmethod
    # def _btn_del_period_isclicked(self):
    #     """Handle when the button btn_del_period is clicked."""
    #     if self.btn_del_period.value():
    #         self.wlcalc.toggle_navig_and_select_tools(self.btn_del_period)
    #         self.btn_show_mrc.setValue(True)
    #     self.mrc_remover.set_active(self.btn_del_period.value())
    #     self.wlcalc.draw()

    @wlcalcmethod
    def _draw_patterns_feature_points(self):
        pass
    #     """Draw the periods that will be used to compute the MRC."""
    #     self.btn_undo.setEnabled(len(self._mrc_period_memory) > 1)
    #     for axvspan in self._mrc_period_axvspans:
    #         axvspan.set_visible(False)
    #     if self.wldset is not None and self.btn_show_mrc.value():
    #         for i, xdata in enumerate(self._mrc_period_xdata):
    #             xmin = xdata[0] + (
    #                 self.wlcalc.dt4xls2mpl * self.wlcalc.dformat)
    #             xmax = xdata[1] + (
    #                 self.wlcalc.dt4xls2mpl * self.wlcalc.dformat)
    #             try:
    #                 axvspan = self._mrc_period_axvspans[i]
    #                 axvspan.set_visible(True)
    #                 axvspan.xy = [[xmin, 1], [xmin, 0],
    #                               [xmax, 0], [xmax, 1]]
    #             except IndexError:
    #                 axvspan = self.wlcalc.fig.axes[0].axvspan(
    #                     xmin, xmax, visible=True, color='red', linewidth=1,
    #                     ls='-', alpha=0.1)
    #                 self._mrc_period_axvspans.append(axvspan)

    # def btn_show_mrc_isclicked(self):
    #     """Handle when the button to draw of hide the mrc is clicked."""
    #     if self.btn_show_mrc.value() is False:
    #         self.btn_add_period.setValue(False)
    #         self.btn_del_period.setValue(False)
    #     self._draw_mrc()

    # ---- WLCalcTool API
    def is_registered(self):
        return self.wlcalc is not None

    def register_tool(self, wlcalc: QWidget):
        # Setup wlcalc.
        self.wlcalc = wlcalc

        index = wlcalc.tools_tabwidget.addTab(self, self.title())
        wlcalc.tools_tabwidget.setTabToolTip(index, self.tooltip())
        # wlcalc.sig_date_format_changed.connect(self._draw_mrc)

        # Setup the axes widget to select high water level periods.
        wlcalc.register_navig_and_select_tool(self._select_high_spring_btn)
        wlcalc.register_navig_and_select_tool(self._select_high_fall_btn)

        # Setup the selectors for the periods of high spring and high fall
        # water levels.
        self.high_spring_selector = WLCalcVSpanSelector(
            self.wlcalc.fig.axes[0], wlcalc,
            onselected=self._on_daterange_selected,
            axvspan_color='green', axvline_color='green')
        wlcalc.install_axeswidget(self.high_spring_selector)

        self.high_fall_selector = WLCalcVSpanSelector(
            self.wlcalc.fig.axes[0], wlcalc,
            onselected=self._on_daterange_selected,
            axvspan_color='orange', axvline_color='orange')
        wlcalc.install_axeswidget(self.high_fall_selector)

        # Setup the seasonal pattern feature points plotter.
        self.feature_points_plotter = FeaturePointPlotter(
            self.wlcalc.fig.axes[0], wlcalc)
        self.wlcalc.install_axeswidget(
            self.feature_points_plotter, active=True)

        # Init matplotlib artists.
        self._high_spring_plt, = self.wlcalc.fig.axes[0].plot(
            [], [], color='green', clip_on=True,
            zorder=15, marker='v', linestyle='none')
        self._high_fall_plt, = self.wlcalc.fig.axes[0].plot(
            [], [], color='orange', clip_on=True,
            zorder=15, marker='v', linestyle='none')

        # self.load_mrc_from_wldset()
        self._draw_patterns_feature_points()

    def close_tool(self):
        super().close()

    def set_wldset(self, wldset):
        self.wldset = wldset

    def set_wxdset(self, wxdset):
        pass
