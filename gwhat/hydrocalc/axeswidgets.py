# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

# ---- Standard library imports
from typing import Any, Callable

# ---- Third party imports
import numpy as np

from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtWidgets import QWidget

from matplotlib.axes import Axes
from matplotlib.widgets import AxesWidget


class WLCalcVSpanHighlighter(AxesWidget, QObject):
    sig_span_clicked = QSignal(float)

    def __init__(self, ax: Axes, wlcalc: QWidget, tracked_axvspans: list,
                 useblit: bool = True, onclicked: Callable = None,
                 axvspan_color: str = 'red', axvline_color: str = 'black',
                 ):
        AxesWidget.__init__(self, ax)
        QObject.__init__(self)
        self.visible = True
        self.useblit = useblit and self.canvas.supports_blit
        self.wlcalc = wlcalc
        self.tracked_axvspans = tracked_axvspans

        if onclicked is not None:
            self.sig_span_clicked.connect(onclicked)

        # Axes span highlight.
        self.axvspan_highlight = ax.axvspan(
            0, 1, visible=False, color='red', linewidth=1,
            ls='-', alpha=0.3)

    def set_active(self, active):
        """
        Set whether the selector is active.
        """
        self.axvspan_highlight.xy = [
            [np.inf, 1], [np.inf, 0], [np.inf, 0], [np.inf, 1]]
        self.axvspan_highlight.set_visible(active)
        super().set_active(active)
        self.wlcalc.draw()

    def clear(self):
        """
        Clear the selector.

        This method must be called by the canvas BEFORE making a copy of
        the canvas background.
        """
        self.__axvspan_highlight_visible = self.axvspan_highlight.get_visible()
        self.axvspan_highlight.set_visible(False)

    def restore(self):
        """
        Restore the selector.

        This method must be called by the canvas AFTER a copy has been made
        of the canvas background.
        """
        self.axvspan_highlight.set_visible(self.__axvspan_highlight_visible)
        self.ax.draw_artist(self.axvspan_highlight)

    def onmove(self, event):
        """Handler to draw the selector when the mouse cursor moves."""
        if self.ignore(event):
            return
        if not self.canvas.widgetlock.available(self):
            return
        if not self.visible:
            return

        if event.xdata is None:
            self.axvspan_highlight.set_visible(False)
            self._update()
            return

        for axvspan in self.tracked_axvspans:
            if not axvspan.get_visible():
                continue

            xy_data = axvspan.xy
            x_data = [xy[0] for xy in xy_data]
            xdata_min = min(x_data)
            xdata_max = max(x_data)
            if event.xdata >= xdata_min and event.xdata <= xdata_max:
                self.axvspan_highlight.set_visible(True)
                self.axvspan_highlight.xy = [[xdata_min, 1],
                                             [xdata_min, 0],
                                             [xdata_max, 0],
                                             [xdata_max, 1]]
                break
        else:
            self.axvspan_highlight.set_visible(False)
        self._update()

    def onpress(self, event):
        """Handler for the button_press_event event."""
        if event.button != 1 or not event.xdata:
            return
        self.sig_span_clicked.emit(
            event.xdata - self.wlcalc.dt4xls2mpl * self.wlcalc.dformat)
        self.onmove(event)

    def onrelease(self, event):
        pass

    def _update(self):
        self.ax.draw_artist(self.axvspan_highlight)
        return False


class WLCalcVSpanSelector(AxesWidget, QObject):
    sig_span_selected = QSignal(tuple)

    def __init__(self, ax: Axes, wlcalc: QWidget,
                 useblit: bool = True, onselected: Callable = None,
                 axvspan_color: str = 'red', axvline_color: str = 'black'):
        AxesWidget.__init__(self, ax)
        QObject.__init__(self)
        self.visible = True
        self.useblit = useblit and self.canvas.supports_blit
        self.wlcalc = wlcalc

        if onselected is not None:
            self.sig_span_selected.connect(onselected)

        self.axvspan = ax.axvspan(
            ax.get_xbound()[0], ax.get_xbound()[0], visible=False,
            color=axvspan_color, linewidth=1, ls='-', animated=self.useblit,
            alpha=0.1)

        self.axvline = ax.axvline(
            ax.get_ybound()[0], visible=False, color=axvline_color,
            linewidth=1, ls='--', animated=self.useblit)

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

        self.axvline.set_xdata((np.inf, np.inf))
        self.axvline.set_visible(active)

        self.axvspan.xy = [[np.inf, 1],
                           [np.inf, 0],
                           [np.inf, 0],
                           [np.inf, 1]]
        self.axvspan.set_visible(active)

        super().set_active(active)
        self.wlcalc.draw()

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

                onrelease_xdata = tuple((
                    min(self._onrelease_xdata) -
                    self.wlcalc.dt4xls2mpl * self.wlcalc.dformat,
                    max(self._onrelease_xdata) -
                    self.wlcalc.dt4xls2mpl * self.wlcalc.dformat
                    ))
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
