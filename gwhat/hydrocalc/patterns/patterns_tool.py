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
import sys
from datetime import datetime, timedelta

# ---- Third party imports
import numpy as np
import pandas as pd
from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import (QWidget, QGridLayout, QApplication, QPushButton)
from matplotlib.transforms import ScaledTranslation

# ---- Local imports
from gwhat.hydrocalc.axeswidgets import WLCalcVSpanSelector, WLCalcAxesWidget
from gwhat.hydrocalc.api import WLCalcTool, wlcalcmethod
from gwhat.utils.dates import (
    xldates_to_datetimeindex, datetimeindex_to_xldates)
from gwhat.utils.icons import get_icon
from gwhat.widgets.buttons import OnOffPushButton
from gwhat.widgets.fileio import SaveFileMixin


COLORS = {
    'high_spring': 'green',
    'high_fall': 'red',
    'low_summer': 'orange',
    'low_winter': 'cyan'}


class FeaturePointSelector(WLCalcVSpanSelector):
    def __init__(self, ax, wlcalc, onselected):
        super().__init__(
            ax, wlcalc, onselected, allowed_buttons=[1, 3],
            )

    def get_onpress_axvspan_color(self, event):
        ctrl = bool(self._onpress_keyboard_modifiers & Qt.ControlModifier)
        if event.button == 1:
            return COLORS['high_fall'] if ctrl else COLORS['high_spring']
        elif event.button == 3:
            return COLORS['low_winter'] if ctrl else COLORS['low_summer']
        else:
            return super().get_axvline_color(event)


class FeaturePointPlotter(WLCalcAxesWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        offset_highs = ScaledTranslation(
            0, 6/72, self.ax.figure.dpi_scale_trans)
        offset_lows = ScaledTranslation(
            0, -6/72, self.ax.figure.dpi_scale_trans)

        self._feature_artists = {
            'high_spring': self.ax.plot(
                [], [], marker='v', color=COLORS['high_spring'], ls='none',
                transform=self.ax.transData + offset_highs
                )[0],
            'high_fall': self.ax.plot(
                [], [], marker='v', color=COLORS['high_fall'], ls='none',
                transform=self.ax.transData + offset_highs
                )[0],
            'low_summer': self.ax.plot(
                [], [], marker='^', color=COLORS['low_summer'], ls='none',
                transform=self.ax.transData + offset_lows
                )[0],
            'low_winter': self.ax.plot(
                [], [], marker='^', color=COLORS['low_winter'], ls='none',
                transform=self.ax.transData + offset_lows
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

        # A dict to hold the picked seasonal pattern feature points.
        self._feature_points = {
            'high_fall': pd.Series(),
            'high_spring': pd.Series(),
            'low_summer': pd.Series(),
            'low_winter': pd.Series(),
            }

        self.setup()

    def setup(self):
        mod_str = 'COMMAND' if sys.platform == 'darwin' else 'CONTROL'
        self._select_feature_points_btn = OnOffPushButton(
            label='  Select Feature Points',
            icon='select_range',
            tooltip=(
                '<b>Select Feature Points</b>'
                '<p>Select periods corresponding to seasonal maximum '
                'or minimum water levels.</p>'
                '<p>Use Left click to select a spring maximum and '
                f'{mod_str} + Left click to select a fall maximum.</p>'
                '<p>Use Right click to select a summer minimum and '
                f'{mod_str} + Right click to select a winter minimum.</p>'),
            on_value_changed=self._btn_select_feature_points_isclicked
            )

        self._erase_feature_points_btn = OnOffPushButton(
            label='  Erase Feature Points',
            icon='erase_data',
            tooltip=(
                '<b>Erase Feature Points</b>'
                '<p>Use the left click of the mouse to select a period '
                'within which to erase all feature points.</p>'),
            on_value_changed=self._btn_erase_feature_points_isclicked
            )

        self._clear_feature_points_btn = QPushButton('  Clear Feature Points')
        self._clear_feature_points_btn.setIcon(get_icon('close'))
        self._clear_feature_points_btn.setToolTip(
            '<b>Clear Feature Points</b>'
            '<p>Clear all feature points from the current well '
            'hydrograph.</p>')
        self._clear_feature_points_btn.clicked.connect(
            self._btn_clear_feature_points_isclicked)


        # Setup the Layout.
        layout = QGridLayout(self)

        layout.addWidget(self._select_feature_points_btn, 0, 0)
        layout.addWidget(self._erase_feature_points_btn, 1, 0)
        layout.addWidget(self._clear_feature_points_btn, 2, 0)
        layout.setRowStretch(4, 100)

    # ---- WLCalc integration

    @wlcalcmethod
    def _btn_clear_feature_points_isclicked(self, *args, **kwargs):
        """
        Handle when the button to clear all feature points from the current
        well hydrograph is clicked.
        """
        self._feature_points = {
            'high_fall': pd.Series(),
            'high_spring': pd.Series(),
            'low_summer': pd.Series(),
            'low_winter': pd.Series(),
            }
        self._draw_patterns_feature_points()

    @wlcalcmethod
    def _btn_erase_feature_points_isclicked(self, *args, **kwargs):
        """
        Handle when the button to erase seasonal feature points is clicked.
        """
        if self._erase_feature_points_btn.value():
            self.wlcalc.toggle_navig_and_select_tools(
                self._erase_feature_points_btn)
        self.feature_points_erasor.set_active(
            self._erase_feature_points_btn.value())

    @wlcalcmethod
    def _btn_select_feature_points_isclicked(self, *args, **kwargs):
        """
        Handle when the button to select seasonal feature points is clicked.
        """
        if self._select_feature_points_btn.value():
            self.wlcalc.toggle_navig_and_select_tools(
                self._select_feature_points_btn)
        self.feature_points_selector.set_active(
            self._select_feature_points_btn.value())

    @wlcalcmethod
    def _on_daterange_selected(self, xldates, button, modifiers):
        """
        Handle when a new period of high spring or hign fall water levels is
        selected by the user.

        Parameters
        ----------
        xldates : 2-tuple
            A 2-tuple of floats containing the time, in numerical Excel format,
            where to add a new seasonal feature point.
        """
        dtmin, dtmax = xldates_to_datetimeindex(xldates)

        # Check and remove previously picked high spring or high fall feature
        # points that are within the selected period.
        if button == 1:
            feature_types = ['high_spring', 'high_fall']
        elif button == 3:
            feature_types = ['low_summer', 'low_winter']

        for key in feature_types:
            mask = ((self._feature_points[key].index < dtmin) |
                    (self._feature_points[key].index > dtmax))
            self._feature_points[key] = self._feature_points[key][mask]

        # Find and add the new high spring or high fall feature point within
        # the selected period.
        data = self.wlcalc.wldset.data
        mask = (data.index >= dtmin) & (data.index <= dtmax)
        if mask.sum() == 0:
            return

        ctrl = bool(modifiers & Qt.ControlModifier)
        if button == 1:
            feature_type = 'high_spring' if not ctrl else 'high_fall'
            index = np.argmin(data['WL'][mask])
        elif button == 3:
            feature_type = 'low_summer' if not ctrl else 'low_winter'
            index = np.argmax(data['WL'][mask])

        self._feature_points[feature_type][
            data.index[mask][index]
            ] = data['WL'][mask][index]
    @wlcalcmethod
    def _on_daterange_erased(self, xldates, button, modifiers):
        """
        Handle when a period is selected to erase all selected seasonal
        feature points.

        Parameters
        ----------
        xldates : 2-tuple
            A 2-tuple of floats containing the time, in numerical Excel format,
            of the period where to erase all picked seasonal feature points.
        """
        dtmin, dtmax = xldates_to_datetimeindex(xldates)
        for key in self._feature_points.keys():
            mask = ((self._feature_points[key].index < dtmin) |
                    (self._feature_points[key].index > dtmax))
            self._feature_points[key] = self._feature_points[key][mask]
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
        wlcalc.register_navig_and_select_tool(self._select_feature_points_btn)
        wlcalc.register_navig_and_select_tool(self._erase_feature_points_btn)

        # Setup the seasonal feature points selectorand erasor.
        self.feature_points_selector = FeaturePointSelector(
            self.wlcalc.fig.axes[0], wlcalc,
            onselected=self._on_daterange_selected)
        wlcalc.install_axeswidget(self.feature_points_selector)

        self.feature_points_erasor = WLCalcVSpanSelector(
            self.wlcalc.fig.axes[0], wlcalc,
            onselected=self._on_daterange_erased,
            axvspan_color='0.6')
        wlcalc.install_axeswidget(self.feature_points_erasor)

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

    def on_wldset_changed(self):
        self._feature_points = {
            'high_fall': pd.Series(),
            'high_spring': pd.Series(),
            'low_summer': pd.Series(),
            'low_winter': pd.Series(),
            }
        self.wlcalc.update_axeswidgets()

    def set_wldset(self, wldset):
        pass

    def set_wxdset(self, wxdset):
        pass
