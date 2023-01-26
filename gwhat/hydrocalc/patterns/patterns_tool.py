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
from matplotlib.transforms import ScaledTranslation

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

        offset = ScaledTranslation(0, 6/72, self.ax.figure.dpi_scale_trans)
        self._feature_artists = {
            'high_spring': self.ax.plot(
                [], [], marker='v', color='green', ls='none',
                transform=self.ax.transData + offset
                )[0],
            'high_fall': self.ax.plot(
                [], [], marker='v', color='red', ls='none',
                transform=self.ax.transData + offset
                )[0],
            }

        for artist in self._feature_artists.values():
            self.register_artist(artist)

    def set_feature_points(self, feature_points: dict):
        """Set and draw the seasonal pattern feature points."""
        for key, series in feature_points.items():
            if not series.empty and self.wlcalc.dformat == 1:
                self._feature_artists[key].set_data(
                    series.index, series.values)
            elif not series.empty and self.wlcalc.dformat == 0:
                xldates = datetimeindex_to_xldates(series.index)
                self._feature_artists[key].set_data(
                    xldates, series.values)
            else:
                self._feature_artists[key].set_data([], [])

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

        self._select_highs_btn = OnOffPushButton(
            '  Select Highs', icon='select_range')
        self._select_highs_btn.setToolTip(
            'Select periods when maximum water levels were '
            'reached in the spring or in the fall.')
        self._select_highs_btn.setCheckable(True)
        self._select_highs_btn.setFocusPolicy(Qt.NoFocus)
        self._select_highs_btn.sig_value_changed.connect(
            lambda: self._btn_select_highs_isclicked())

        # Setup the Layout.
        layout = QGridLayout(self)

        layout.addWidget(self._select_highs_btn, 0, 0)
        layout.setRowMinimumHeight(2, 5)
        layout.setRowStretch(2, 100)

    # ---- WLCalc integration
    @wlcalcmethod
    def _btn_select_highs_isclicked(self):
        """Handle when the button to select high spring periods is clicked."""
        if self._select_highs_btn.value():
            self.wlcalc.toggle_navig_and_select_tools(self._select_highs_btn)
        self.highs_selector.set_active(self._select_highs_btn.value())

    @wlcalcmethod
    def _on_daterange_selected(self, xldates, button):
        """
        Handle when a new period of high spring or hign fall water levels is
        selected by the user.

        Parameters
        ----------
        xldates : 2-tuple
            A 2-tuple of floats containing the time, in numerical Excel format,
            of the new selected recession period.
        """
        dtmin, dtmax = xldates_to_datetimeindex(xldates)

        # Check and remove previously picked high spring or high fall feature
        # points that are within the selected period.
        for high_type in ['high_spring', 'high_fall']:
            mask = ((self._feature_points[high_type].index < dtmin) |
                    (self._feature_points[high_type].index > dtmax))
            self._feature_points[high_type] = (
                self._feature_points[high_type][mask])

        # Make sure there is not two feature point of the same type

        # Find and add the new high spring or high fall feature point within
        # the selected period.
        if button == 1:
            high_type = 'high_spring'
        elif button == 3:
            high_type = 'high_fall'

        data = self.wlcalc.wldset.data
        mask = (data.index >= dtmin) & (data.index <= dtmax)
        if mask.sum() > 0:
            argmin = np.argmin(data['WL'][mask])
            self._feature_points[high_type][
                data.index[mask][argmin]
                ] = data['WL'][mask][argmin]

        self._draw_patterns_feature_points()

    @wlcalcmethod
    def _draw_patterns_feature_points(self):
        self.feature_points_plotter.set_feature_points(self._feature_points)
        self.wlcalc.update_axeswidgets()

    # ---- WLCalcTool API
    def is_registered(self):
        return self.wlcalc is not None

    def register_tool(self, wlcalc: QWidget):
        # Setup wlcalc.
        self.wlcalc = wlcalc

        index = wlcalc.tools_tabwidget.addTab(self, self.title())
        wlcalc.tools_tabwidget.setTabToolTip(index, self.tooltip())

        # Setup the axes widget to select high water level periods.
        wlcalc.register_navig_and_select_tool(self._select_highs_btn)

        # Setup the selectors for the periods of high spring and high fall
        # water levels.
        self.highs_selector = WLCalcVSpanSelector(
            self.wlcalc.fig.axes[0], wlcalc,
            onselected=self._on_daterange_selected,
            axvspan_colors=['green', 'orange'],
            allowed_buttons=[1, 3])
        wlcalc.install_axeswidget(self.highs_selector)

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
