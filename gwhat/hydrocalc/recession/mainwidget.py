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

# ---- Third party imports
import pandas as pd
from PyQt5.QtWidgets import (
    QWidget, QComboBox, QTextEdit, QSizePolicy, QPushButton, QGridLayout,
    QLabel)

# ---- Local imports
from gwhat.hydrocalc.axeswidgets import WLCalcVSpanSelector
from gwhat.hydrocalc.api import WLCalcTool, wlcalcmethod
from gwhat.utils.qthelpers import create_toolbutton
from gwhat.utils.icons import QToolButtonNormal, get_iconsize
from gwhat.widgets.buttons import OnOffToolButton, ToolBarWidget


class MasterRecessionCalcTool(WLCalcTool):
    __toolname__ = 'mrc'
    __tooltitle__ = 'MRC'
    __tooltip__ = ("A tool to evaluate the barometric "
                   "response function of wells.")

    # Whether it is the first time showEvent is called.
    _first_show_event = True

    # The WLCalc instance to which this tool is registered.
    wlcalc = None

    _mrc_period_xdata = []
    _mrc_period_axvspans = []
    _mrc_period_memory = [[], ]

    def setup(self):
        # Setup MRC parameter widgets.
        self.MRC_type = QComboBox()
        self.MRC_type.addItems(['Linear', 'Exponential'])
        self.MRC_type.setCurrentIndex(1)

        self.MRC_results = QTextEdit()
        self.MRC_results.setReadOnly(True)
        self.MRC_results.setMinimumHeight(25)
        self.MRC_results.setMinimumWidth(100)
        self.MRC_results.setSizePolicy(
            QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred))

        # Setup the toolbar.
        self.btn_undo = create_toolbutton(
            parent=self,
            icon='undo',
            iconsize=get_iconsize('normal'),
            tip='Undo',
            triggered=self.undo_mrc_period)
        self.btn_undo.setEnabled(False)

        self.btn_clearPeak = create_toolbutton(
            parent=self,
            icon='clear_changes',
            iconsize=get_iconsize('normal'),
            tip='Clear all recession periods.',
            triggered=self.clear_all_mrcperiods)

        self.btn_addpeak = OnOffToolButton('pencil_add', size='normal')
        self.btn_addpeak.sig_value_changed.connect(self.btn_addpeak_isclicked)
        self.btn_addpeak.setToolTip(
            "Left-click on the graph to add new recession periods.")

        self.btn_delpeak = OnOffToolButton('pencil_del', size='normal')
        self.btn_delpeak.clicked.connect(self.btn_delpeak_isclicked)
        self.btn_delpeak.setToolTip(
            "Left-click on a recession period to remove it.")

        self.btn_save_mrc = create_toolbutton(
            parent=self,
            icon='save',
            iconsize=get_iconsize('normal'),
            tip='Save calculated MRC to file.',
            triggered=lambda: self.save_mrc_tofile())

        self.btn_MRCalc = QPushButton('Compute MRC')
        self.btn_MRCalc.clicked.connect(self.btn_MRCalc_isClicked)
        self.btn_MRCalc.setToolTip(
            'Calculate the Master Recession Curve (MRC).')

        mrc_tb = ToolBarWidget()
        for btn in [self.btn_undo, self.btn_clearPeak, self.btn_addpeak,
                    self.btn_delpeak, self.btn_save_mrc]:
            mrc_tb.addWidget(btn)

        # Setup the MRC Layout.
        layout = QGridLayout(self)

        row = 0
        layout.addWidget(QLabel('MRC Type :'), row, 0)
        layout.addWidget(self.MRC_type, row, 1)
        row += 1
        layout.addWidget(self.MRC_results, row, 0, 1, 3)
        row += 1
        layout.addWidget(mrc_tb, row, 0, 1, 3)
        row += 1
        layout.setRowMinimumHeight(row, 5)
        layout.setRowStretch(row, 100)
        row += 1
        layout.addWidget(self.btn_MRCalc, row, 0, 1, 3)
        layout.setColumnStretch(2, 500)

    # ---- WLCalc integration
    @property
    def wldset(self):
        return None if self.wlcalc is None else self.wlcalc.wldset

    @wlcalcmethod
    def _on_wldset_changed(self):
        self.load_mrc_from_wldset()
        self._draw_mrc()

    @wlcalcmethod
    def _on_period_selected(self, xdata):
        """
        Handle when a new period is selected for the MRC calculations.

        Parameters
        ----------
        xdata : 2-tuple
            A 2-tuple of floats containing the time, in numerical Excel format,
            of the new selected recession period.
        """
        self.add_mrcperiod(xdata)
        self.wlcalc._draw_mrc()

    @wlcalcmethod
    def _draw_mrc(self):
        """
        Draw the periods during which water levels recedes and draw the
        water levels that were predicted with the MRC.
        """
        self._draw_mrc_wl()
        self._draw_mrc_periods()
        self.wlcalc.draw()

    @wlcalcmethod
    def _draw_mrc_wl(self):
        """Draw the water levels that were predicted with the MRC."""
        if (self.wldset is not None and
                self.wlcalc.btn_show_mrc.value() and
                self.wldset.mrc_exists()):
            self._mrc_plt.set_visible(True)
            mrc_data = self.wldset.get_mrc()

            x = mrc_data['time'] + self.wlcalc.dt4xls2mpl * self.wlcalc.dformat
            y = mrc_data['recess']
            self._mrc_plt.set_data(x, y)
        else:
            self._mrc_plt.set_visible(False)

    @wlcalcmethod
    def _draw_mrc_periods(self):
        """Draw the periods that will be used to compute the MRC."""
        self.btn_undo.setEnabled(len(self._mrc_period_memory) > 1)
        for axvspan in self._mrc_period_axvspans:
            axvspan.set_visible(False)
        if self.wldset is not None and self.btn_show_mrc.value():
            for i, xdata in enumerate(self._mrc_period_xdata):
                xmin = xdata[0] + (
                    self.wlcalc.dt4xls2mpl * self.wlcalc.dformat)
                xmax = xdata[1] + (
                    self.wlcalc.dt4xls2mpl * self.wlcalc.dformat)
                try:
                    axvspan = self._mrc_period_axvspans[i]
                    axvspan.set_visible(True)
                    axvspan.xy = [[xmin, 1], [xmin, 0],
                                  [xmax, 0], [xmax, 1]]
                except IndexError:
                    axvspan = self.wlcalc.fig.axes[0].axvspan(
                        xmin, xmax, visible=True, color='red', linewidth=1,
                        ls='-', alpha=0.1)
                    self._mrc_period_axvspans.append(axvspan)

    # ---- WLCalcTool API
    def is_registered(self):
        return self.wlcalc is not None

    def register_tool(self, wlcalc: QWidget):
        self.wlcalc = wlcalc
        wlcalc.register_navig_and_select_tool(self.btn_addpeak)
        wlcalc.register_navig_and_select_tool(self.btn_delpeak)

        wlcalc.sig_wldset_changed.connect(self._on_wldset_changed)


        # Init matplotlib artists.
        self._mrc_plt, = self.wlcalc.fig.axes[0].plot(
            [], [], color='red', clip_on=True,
            zorder=15, marker='None', linestyle='--')
    # ---- MRC Tool Interface
    def add_mrcperiod(self, xdata):
        """
        Add a a new mrc period using the provided xdata.
        """
        try:
            xmin = min(xdata)
            xmax = max(xdata)
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
