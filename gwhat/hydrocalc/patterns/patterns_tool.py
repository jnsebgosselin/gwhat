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
    from gwhat.HydroCalc2 import WLCalc
    from matplotlib.axes import Axes

# ---- Standard library imports
import io
import sys
from datetime import datetime, timedelta

# ---- Third party imports
import numpy as np
import pandas as pd
from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import QWidget, QGridLayout, QPushButton
from matplotlib.transforms import ScaledTranslation

# ---- Local imports
from gwhat.hydrocalc.axeswidgets import WLCalcVSpanSelector, WLCalcAxesWidget
from gwhat.hydrocalc.api import WLCalcTool, wlcalcmethod
from gwhat.utils.dates import xldates_to_datetimeindex
from gwhat.utils.icons import get_icon
from gwhat.widgets.buttons import OnOffPushButton
from gwhat.widgets.fileio import SaveFileMixin


EVENT_TYPES = [
    'low_winter',
    'high_spring',
    'recess_summer',
    'low_summer',
    'high_fall'
    ]
COLORS = {
    'high_spring': 'green',
    'high_fall': 'red',
    'recess_summer': 'purple',
    'low_summer': 'orange',
    'low_winter': 'cyan',
    }
MARKERS = {
    'high_spring': 'v',
    'high_fall': 'v',
    'recess_summer': 'o',
    'low_summer': '^',
    'low_winter': '^',
    }
MARKER_VOFFSETS = {
    'high_spring': 8/72,
    'high_fall': 8/72,
    'recess_summer': 0,
    'low_summer': -8/72,
    'low_winter': -8/72,
    }

DATE_FORMAT = '%Y-%m-%d'


class HydroCycleEventsSelector(WLCalcVSpanSelector):
    def __init__(self, ax, wlcalc, onselected):
        super().__init__(
            ax, wlcalc, onselected, allowed_buttons=[1, 3],
            )

    def onpress(self, event):
        if event.button == 2 and event.xdata:
            self._onpress_button = event.button
            self._onpress_keyboard_modifiers = event.guiEvent.modifiers()
            self._onpress_xdata = [event.xdata]
            self.axvline.set_visible(False)
            self._update()
        else:
            super().onpress(event)

    def onrelease(self, event):
        if event.button == 2 and self._onpress_button == 2:
            onrelease_xdata = tuple(
                [self._onpress_xdata[0] -
                 self.wlcalc.dt4xls2mpl * self.wlcalc.dformat] * 2
                )

            self.axvline.set_visible(True)
            if event.xdata:
                self.axvline.set_xdata((event.xdata, event.xdata))

            self.sig_span_selected.emit(
                onrelease_xdata,
                self._onpress_button,
                self._onpress_keyboard_modifiers)

            self._onpress_button = None
            self._onpress_xdata = []
            self._onrelease_xdata = []
            self._onpress_keyboard_modifiers = None
            self._update()
        else:
            super().onrelease(event)

    def get_onpress_axvspan_color(self, event):
        ctrl = bool(self._onpress_keyboard_modifiers & Qt.ControlModifier)
        if event.button == 1:
            return COLORS['high_fall'] if ctrl else COLORS['high_spring']
        elif event.button == 3:
            return COLORS['low_winter'] if ctrl else COLORS['low_summer']
        else:
            return super().get_axvline_color(event)


class HydroCycleEventsPlotter(WLCalcAxesWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._picked_event_artists = {}
        for event_type in EVENT_TYPES:
            scaled_trans = ScaledTranslation(
                0, MARKER_VOFFSETS[event_type], self.ax.figure.dpi_scale_trans)
            artist = self.ax.plot(
                [], [],
                marker=MARKERS[event_type],
                color=COLORS[event_type],
                ls='none',
                transform=self.ax.transData + scaled_trans
                )[0]
            self.register_artist(artist)
            self._picked_event_artists[event_type] = artist

    def set_events_data(self, events_data: pd.DataFrame):
        """Set and draw the hydrological cycle picked events."""
        for event_type in EVENT_TYPES:
            xydata = events_data[event_type].dropna()
            if not xydata.empty:
                self._picked_event_artists[event_type].set_data(
                    xydata.date, xydata.value)
            else:
                self._picked_event_artists[event_type].set_data([], [])

    def onactive(self, *args, **kwargs):
        self._update()

    def onmove(self, *args, **kwargs):
        self._update()

    def onpress(self, *args, **kwargs):
        self._update()

    def onrelease(self, *args, **kwargs):
        self._update()


class YearlyVGridPlotter(object):

    def __init__(self, ax: Axes, wlcalc: WLCalc):
        self.ax = ax
        self.wlcalc = wlcalc
        self._vgrid_artists = []
        self._active = False

    def set_active(self, active: bool):
        self._active = active
        for artist in self._vgrid_artists:
            artist.set_visible(active)
        self.wlcalc.draw()

    def set_grid_xdata(self, xdata: list):
        """Set the position of the yearly vertical grid lines."""
        for artist in self._vgrid_artists:
            artist.set_visible(False)
        for i, value in enumerate(xdata):
            try:
                artist = self._vgrid_artists[i]
                artist.set_xdata(value)
            except IndexError:
                artist = self.ax.axvline(value, ls=':', color='0.85', zorder=1)
                self._vgrid_artists.append(artist)
            artist.set_visible(self._active)
        self.wlcalc.draw()


class HydroCycleCalcTool(WLCalcTool, SaveFileMixin):
    __toolname__ = 'cycle'
    __tooltitle__ = 'Cycle'
    __tooltip__ = ("<p>A tool to pick hydrological cycle events "
                   "on the hydrograph.</p>")

    sig_new_mrc = Signal()

    def __init__(self, parent=None):
        WLCalcTool.__init__(self, parent)
        SaveFileMixin.__init__(self)

        # Whether it is the first time showEvent is called.
        self._first_show_event = True

        # A pandas dataframe to hold the data of the picked
        # hydrological cycle events.
        tuples = []
        for event_type in EVENT_TYPES:
            tuples.append((event_type, 'date'))
            tuples.append((event_type, 'value'))
        self._events_data = pd.DataFrame(
            columns=pd.MultiIndex.from_tuples(tuples)
            )

        self.setup()

    def setup(self):
        key_modif = 'COMMAND' if sys.platform == 'darwin' else 'CONTROL'
        self._select_events_btn = OnOffPushButton(
            label='  Select Events',
            icon='select_range',
            tooltip=(
                '<b>Select Events</b>'
                '<p>Select periods on the hydrograph corresponding to '
                'an event of the hydrological cycle :'
                '<ul>'
                '<li>Use Left click to select a spring maximum;</li>'
                '<li>Use {key_modif} + Left click to select a '
                'fall maximum;</li>'
                '<li>Use Right click to select a summer minimum;</li>'
                '<li>Use {key_modif} + Right click to select a '
                'winter minimum.</li>'
                '</ul>'
                ).format(key_modif=key_modif),
            on_value_changed=self._btn_select_events_isclicked
            )

        self._erase_events_btn = OnOffPushButton(
            label='  Erase Events',
            icon='erase_data',
            tooltip=(
                '<b>Erase Events</b>'
                '<p>Use Left click of the mouse to select a period '
                'where to erase all picked events.</p>'),
            on_value_changed=self._btn_erase_events_isclicked
            )

        self._clear_events_btn = QPushButton('  Clear Events')
        self._clear_events_btn.setIcon(get_icon('close'))
        self._clear_events_btn.setToolTip(
            '<b>Clear Events</b>'
            '<p>Clear all picked events from the hydrograph.</p>')
        self._clear_events_btn.clicked.connect(
            self._btn_clear_events_isclicked)

        self._copy_events_btn = QPushButton('  Copy Events')
        self._copy_events_btn.setIcon(get_icon('copy_clipboard'))
        self._copy_events_btn.setToolTip(
            '<b>Copy Events</b>'
            '<p>Place a copy of the hydrological cycle events '
            'data on the clipboard.</p>'
            )
        self._copy_events_btn.clicked.connect(lambda: self.copy_to_clipboard())

        self._save_events_btn = QPushButton('  Save Events')
        self._save_events_btn.setIcon(get_icon('save'))
        self._save_events_btn.setToolTip(
            '<b>Save Events</b>'
            '<p>Save picked hydrological cycle events in the '
            'GWHAT project.</p>')
        self._save_events_btn.clicked.connect(lambda: self.save_events_data())
        self._save_events_btn.setEnabled(False)

        # Setup the Layout.
        layout = QGridLayout(self)

        layout.addWidget(self._select_events_btn, 0, 0)
        layout.addWidget(self._erase_events_btn, 1, 0)
        layout.addWidget(self._clear_events_btn, 2, 0)
        layout.addWidget(self._copy_events_btn, 3, 0)
        layout.addWidget(self._save_events_btn, 4, 0)
        layout.setRowStretch(5, 100)

    # ---- Public interface.
    @wlcalcmethod
    def read_events_data(self):
        """
        Read previously picked hydological cycle events from the GWHAT project.
        """
        wldset = self.wlcalc.wldset
        if wldset is None:
            return

        try:
            out = wldset.dset.attrs['hydro_cycle_picked_event_data']
        except KeyError:
            return

        self._events_data = pd.read_csv(
            io.StringIO(out.tobytes().decode('utf-8')),
            header=[0, 1], index_col=0)
        for column in self._events_data.columns.to_flat_index():
            if column[1] == 'value':
                self._events_data[column] = (
                    self._events_data[column].astype(float))
            elif column[1] == 'date':
                self._events_data[column] = pd.to_datetime(
                    self._events_data[column], format=DATE_FORMAT)

    @wlcalcmethod
    def save_events_data(self):
        """
        Save events data in the GWHAT project.
        """
        events_data = self._events_data.dropna(how='all').copy()

        binary_blob = events_data.to_csv(
            index=True, na_rep='', date_format='%Y-%m-%d', encoding='utf-8'
            ).encode('utf-8')
        self.wlcalc.wldset.dset.attrs[
            'hydro_cycle_picked_event_data'
            ] = np.void(binary_blob)
        self.wlcalc.wldset.dset.file.flush()
        self._save_events_btn.setEnabled(False)

    def clear_all_events(self):
        """
        Clear all picked events.
        """
        tuples = []
        for event_type in EVENT_TYPES:
            tuples.append((event_type, 'date'))
            tuples.append((event_type, 'value'))
        self._events_data = pd.DataFrame(
            columns=pd.MultiIndex.from_tuples(tuples)
            )

    def add_new_event(self, picked_date: datetime, picked_value: float,
                      event_type: str):
        """
        Add new picked event.

        Parameters
        ----------
        picked_date : datetime
            The datetime of the picked event point.
        picked_value : float
            The water level value (in mbgs) of the picked event point.
        event_type : str
            The type of event. Valide values are 'low_winter', 'high_spring',
            'low_summer', 'high_fall', and 'recess_summer'.
        """
        cycle_year = picked_date.year
        if event_type == 'low_winter' and picked_date.month >= 12:
            # This means the low winter event occured early at the end
            # of the previous year.
            cycle_year = cycle_year + 1
        elif event_type == 'high_fall' and picked_date.month < 6:
            # This means the high fall event occured late during
            # the winter of the next year.
            cycle_year = cycle_year - 1

        self._events_data.loc[
            cycle_year, (event_type, 'date')] = picked_date
        self._events_data.loc[
            cycle_year, (event_type, 'value')] = picked_value
        if cycle_year + 1 not in self._events_data.index:
            self._events_data.loc[cycle_year + 1] = np.nan
        if cycle_year - 1 not in self._events_data.index:
            self._events_data.loc[cycle_year - 1] = np.nan

        # Cleanup conflicting events.
        if event_type == 'low_summer':
            # The low winter and high spring events must happen
            # before the low summer event.
            for other_type in ['low_winter', 'high_spring']:
                other_date = self._events_data.loc[
                    cycle_year, (other_type, 'date')]
                if not pd.isnull(other_date) and other_date >= picked_date:
                    self._events_data.loc[
                        cycle_year, (other_type, 'date')] = np.nan
                    self._events_data.loc[
                        cycle_year, (other_type, 'value')] = np.nan
            # The high fall event must happen after the low summer event.
            for other_type in ['high_fall']:
                other_date = self._events_data.loc[
                    cycle_year, (other_type, 'date')]
                if not pd.isnull(other_date) and other_date <= picked_date:
                    self._events_data.loc[
                        cycle_year, (other_type, 'date')] = np.nan
                    self._events_data.loc[
                        cycle_year, (other_type, 'value')] = np.nan
        elif event_type == 'low_winter':
            # The high spring, low summer, and high fall events must happen
            # after the low winter event.
            for other_type in ['high_spring', 'low_summer', 'high_fall']:
                other_date = self._events_data.loc[
                    cycle_year, (other_type, 'date')]
                if not pd.isnull(other_date) and other_date <= picked_date:
                    self._events_data.loc[
                        cycle_year, (other_type, 'date')] = np.nan
                    self._events_data.loc[
                        cycle_year, (other_type, 'value')] = np.nan
            # The high spring, low summer, and high fall events of the
            # previous year must happen before the low winter event.
            for other_type in ['high_spring', 'low_summer', 'high_fall']:
                other_date = self._events_data.loc[
                    cycle_year - 1, (other_type, 'date')]
                if not pd.isnull(other_date) and other_date >= picked_date:
                    self._events_data.loc[
                        cycle_year - 1, (other_type, 'date')] = np.nan
                    self._events_data.loc[
                        cycle_year - 1, (other_type, 'value')] = np.nan
        elif event_type == 'high_spring':
            # The low winter event must happen before the high spring event.
            for other_type in ['low_winter']:
                other_date = self._events_data.loc[
                    cycle_year, (other_type, 'date')]
                if not pd.isnull(other_date) and other_date >= picked_date:
                    self._events_data.loc[
                        cycle_year, (other_type, 'date')] = np.nan
                    self._events_data.loc[
                        cycle_year, (other_type, 'value')] = np.nan
            # The low summer and high fall events must happen
            # after the high spring event.
            for other_type in ['low_summer', 'high_fall']:
                other_date = self._events_data.loc[
                    cycle_year, (other_type, 'date')]
                if not pd.isnull(other_date) and other_date <= picked_date:
                    self._events_data.loc[
                        cycle_year, (other_type, 'date')] = np.nan
                    self._events_data.loc[
                        cycle_year, (other_type, 'value')] = np.nan
            # The high fall event of the previous year must happen
            # before this high spring event.
            for other_type in ['high_fall']:
                other_date = self._events_data.loc[
                    cycle_year - 1, (other_type, 'date')]
                if not pd.isnull(other_date) and other_date >= picked_date:
                    self._events_data.loc[
                        cycle_year - 1, (other_type, 'date')] = np.nan
                    self._events_data.loc[
                        cycle_year - 1, (other_type, 'value')] = np.nan
        elif event_type == 'high_fall':
            # The low winter, high spring, and low summer events must happen
            # before this high fall event.
            for other_type in ['low_winter', 'high_spring', 'low_summer']:
                other_date = self._events_data.loc[
                    cycle_year, (other_type, 'date')]
                if not pd.isnull(other_date) and other_date >= picked_date:
                    self._events_data.loc[
                        cycle_year, (other_type, 'date')] = np.nan
                    self._events_data.loc[
                        cycle_year, (other_type, 'value')] = np.nan

            # The low winter, high spring, and low summer events of the
            # following year must happen after this high fall event.
            for other_type in ['low_winter', 'high_spring', 'low_summer']:
                other_date = self._events_data.loc[
                    cycle_year + 1, (other_type, 'date')]
                if not pd.isnull(other_date) and other_date <= picked_date:
                    self._events_data.loc[
                        cycle_year + 1, (other_type, 'date')] = np.nan
                    self._events_data.loc[
                        cycle_year + 1, (other_type, 'value')] = np.nan
        self._events_data = self._events_data.sort_index()
        self._save_events_btn.setEnabled(True)

    def copy_to_clipboard(self):
        """
        Put the picked hydrological events data on the clipboard.
        """
        events_data = self._events_data.dropna(how='all').copy()

        # Format the datetime data.
        for event_type in EVENT_TYPES:
            events_data.loc[:, (event_type, 'date')] = (
                pd.to_datetime(events_data[event_type]['date']).dt.date
                )

        events_data.to_clipboard(
            excel=True, index=True, na_rep='', date_format='%Y-%m-%d')

    # ---- WLCalc integration
    @wlcalcmethod
    def _btn_clear_events_isclicked(self, *args, **kwargs):
        """
        Handle when the button to clear all hydrological ëvents from the
        well hydrograph is clicked.
        """
        self.clear_all_events()
        self._draw_event_points()

    @wlcalcmethod
    def _btn_erase_events_isclicked(self, *args, **kwargs):
        """
        Handle when the button to erase hydrological cycle events is clicked.
        """
        if self._erase_events_btn.value():
            self.wlcalc.toggle_navig_and_select_tools(self._erase_events_btn)
        self.events_erasor.set_active(self._erase_events_btn.value())

    @wlcalcmethod
    def _btn_select_events_isclicked(self, *args, **kwargs):
        """
        Handle when the button to select hydrological cycle events is clicked.
        """
        if self._select_events_btn.value():
            self.wlcalc.toggle_navig_and_select_tools(self._select_events_btn)
        self.events_selector.set_active(self._select_events_btn.value())

    @wlcalcmethod
    def _on_daterange_selected(self, xldates, button, modifiers):
        """
        Handle when a new hydrological cycle event is selected by the user.

        Parameters
        ----------
        xldates : 2-tuple
            A 2-tuple of floats containing the time, in numerical Excel format,
            where to add a new hydrological cycle event.
        """
        ctrl = bool(modifiers & Qt.ControlModifier)
        dtmin, dtmax = xldates_to_datetimeindex(xldates)
        data = self.wlcalc.wldset.data

        # Find the point of the new event within the selected period or the
        # closest point if it is a single date.
        if button in [1, 3]:
            mask = (data.index >= dtmin) & (data.index <= dtmax)
            if mask.sum() == 0:
                return

            if button == 1:
                event_type = 'high_spring' if not ctrl else 'high_fall'
                index = np.argmin(data['WL'][mask])
            elif button == 3:
                event_type = 'low_summer' if not ctrl else 'low_winter'
                index = np.argmax(data['WL'][mask])

            picked_date = data.index[mask][index]
            picked_value = data['WL'][mask][index]
        elif button == 2:
            # When button 2 is pressed, dtmin and dtmax are the same.
            event_type = 'recess_summer'
            index = np.argmin(np.abs(data.index - dtmin))

            picked_date = data.index[index]
            picked_value = data['WL'][index]

        # Add the new picked event and redraw picked events.
        self.add_new_event(picked_date, picked_value, event_type)
        self._draw_event_points()

    @wlcalcmethod
    def _on_daterange_erased(self, xldates, button, modifiers):
        """
        Handle when a period is selected to erase all picked hydrological
        cycle events.

        Parameters
        ----------
        xldates : 2-tuple
            A 2-tuple of floats containing the time, in numerical Excel format,
            of the period where to erase all picked hydrological cycle events.
        """
        dtmin, dtmax = xldates_to_datetimeindex(xldates)
        for event_type in EVENT_TYPES:
            mask = ((self._events_data[event_type]['date'] >= dtmin) &
                    (self._events_data[event_type]['date'] <= dtmax))
            self._events_data.loc[mask, (event_type, 'date')] = np.nan
            self._events_data.loc[mask, (event_type, 'value')] = np.nan
        self._draw_event_points()

    @wlcalcmethod
    def _draw_event_points(self):
        self.events_plotter.set_events_data(self._events_data)
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
        wlcalc.register_navig_and_select_tool(self._select_events_btn)
        wlcalc.register_navig_and_select_tool(self._erase_events_btn)

        # Setup the hydrological cycle events selector and erasor.
        self.events_selector = HydroCycleEventsSelector(
            self.wlcalc.figure.axes[0], wlcalc,
            onselected=self._on_daterange_selected)
        wlcalc.install_axeswidget(self.events_selector)

        self.events_erasor = WLCalcVSpanSelector(
            self.wlcalc.figure.axes[0], wlcalc,
            onselected=self._on_daterange_erased,
            axvspan_color='0.6')
        wlcalc.install_axeswidget(self.events_erasor)

        # Setup the hydrological cycle events plotter.
        self.events_plotter = HydroCycleEventsPlotter(
            self.wlcalc.figure.axes[0], wlcalc)
        self.wlcalc.install_axeswidget(self.events_plotter, active=True)

        # Setup the yearly vertical grid plotter.
        self.vgrid_plotter = YearlyVGridPlotter(
            self.wlcalc.figure.axes[1], wlcalc)
        self.vgrid_plotter.set_active(True)

        # Init matplotlib artists.
        self._high_spring_plt, = self.wlcalc.figure.axes[0].plot(
            [], [], color='green', clip_on=True,
            zorder=15, marker='v', linestyle='none')
        self._high_fall_plt, = self.wlcalc.figure.axes[0].plot(
            [], [], color='orange', clip_on=True,
            zorder=15, marker='v', linestyle='none')

        # self.load_mrc_from_wldset()
        self._draw_event_points()

    def close_tool(self):
        super().close()

    def on_wldset_changed(self):
        self.clear_all_events()
        if self.wlcalc.wldset is not None:
            min_year = self.wlcalc.wldset.data.index.year.min()
            max_year = self.wlcalc.wldset.data.index.year.max()
            self.vgrid_plotter.set_grid_xdata(
                [datetime(y, 1, 1) for y in range(min_year, max_year + 1)])
            self.read_events_data()
        self._draw_event_points()

    def set_wldset(self, wldset):
        pass

    def set_wxdset(self, wxdset):
        pass
