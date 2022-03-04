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
import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtWidgets import (
    QWidget, QComboBox, QTextEdit, QSizePolicy, QPushButton, QGridLayout,
    QLabel, QApplication, QFileDialog)

# ---- Local imports
from gwhat.hydrocalc.recession.recession_calc import calculate_mrc
from gwhat.hydrocalc.axeswidgets import (
    WLCalcVSpanSelector, WLCalcVSpanHighlighter)
from gwhat.hydrocalc.api import WLCalcTool, wlcalcmethod
from gwhat.utils.qthelpers import create_toolbutton
from gwhat.utils.icons import get_iconsize
from gwhat.widgets.buttons import OnOffToolButton, ToolBarWidget
from gwhat.widgets.fileio import SaveFileMixin


class MasterRecessionCalcTool(WLCalcTool, SaveFileMixin):
    __toolname__ = 'mrc'
    __tooltitle__ = 'MRC'
    __tooltip__ = ("A tool to evaluate the master recession curve "
                   "of the hydrograph.")

    # Whether it is the first time showEvent is called.
    _first_show_event = True

    # The WLCalc instance to which this tool is registered.
    wlcalc = None

    _mrc_period_xdata = []
    _mrc_period_axvspans = []
    _mrc_period_memory = [[], ]

    sig_new_mrc = QSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        WLCalcTool.__init__(self, parent)
        SaveFileMixin.__init__(self)
        self.setup()

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

        self.btn_add_period = OnOffToolButton('pencil_add', size='normal')
        self.btn_add_period.sig_value_changed.connect(
            lambda: self._btn_add_period_isclicked())
        self.btn_add_period.setToolTip(
            "Left-click on the graph to add new recession periods.")

        self.btn_del_period = OnOffToolButton('pencil_del', size='normal')
        self.btn_del_period.sig_value_changed.connect(
            lambda: self._btn_del_period_isclicked())
        self.btn_del_period.setToolTip(
            "Left-click on a recession period to remove it.")

        self.btn_save_mrc = create_toolbutton(
            parent=self,
            icon='save',
            iconsize=get_iconsize('normal'),
            tip='Save calculated MRC to file.',
            triggered=lambda: self.save_mrc_tofile())

        self.btn_calc_mrc = QPushButton('Compute MRC')
        self.btn_calc_mrc.clicked.connect(self.calculate_mrc)
        self.btn_calc_mrc.setToolTip(
            'Calculate the Master Recession Curve (MRC).')

        mrc_tb = ToolBarWidget()
        for btn in [self.btn_undo, self.btn_clearPeak, self.btn_add_period,
                    self.btn_del_period, self.btn_save_mrc]:
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
        layout.addWidget(self.btn_calc_mrc, row, 0, 1, 3)
        layout.setColumnStretch(2, 500)

        # This button needs to be added to WCalc toolbar.
        self.btn_show_mrc = OnOffToolButton('mrc_calc', size='normal')
        self.btn_show_mrc.setToolTip(
            "Show or hide water levels predicted with the MRC.")
        self.btn_show_mrc.sig_value_changed.connect(
            self.btn_show_mrc_isclicked)
        self.btn_show_mrc.setValue(
            self.get_option('show_mrc', True), silent=True)

    # ---- WLCalc integration
    @property
    def wldset(self):
        return None if self.wlcalc is None else self.wlcalc.wldset

    @wlcalcmethod
    def _on_wldset_changed(self):
        self._mrc_period_xdata = []
        self._mrc_period_memory = [[], ]
        self.btn_undo.setEnabled(False)
        self.setEnabled(self.wldset is not None)
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
                self.btn_show_mrc.value() and
                self.wldset.mrc_exists()):
            self._mrc_plt.set_visible(True)
            mrc_data = self.wldset.get_mrc()

            x = mrc_data['time'] + self.wlcalc.dt4xls2mpl * self.wlcalc.dformat
            y = mrc_data['recess']
            self._mrc_plt.set_data(x, y)
        else:
            self._mrc_plt.set_visible(False)

    @wlcalcmethod
    def _btn_add_period_isclicked(self):
        """Handle when the button add_peak is clicked."""
        if self.btn_add_period.value():
            self.wlcalc.toggle_navig_and_select_tools(self.btn_add_period)
            self.btn_show_mrc.setValue(True)
        self.mrc_selector.set_active(self.btn_add_period.value())

    @wlcalcmethod
    def _btn_del_period_isclicked(self):
        """Handle when the button btn_del_period is clicked."""
        if self.btn_del_period.value():
            self.wlcalc.toggle_navig_and_select_tools(self.btn_del_period)
            self.btn_show_mrc.setValue(True)
        self.mrc_remover.set_active(self.btn_del_period.value())
        self.wlcalc.draw()

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

    def btn_show_mrc_isclicked(self):
        """Handle when the button to draw of hide the mrc is clicked."""
        if self.btn_show_mrc.value() is False:
            self.btn_add_period.setValue(False)
            self.btn_del_period.setValue(False)
        self._draw_mrc()

    # ---- WLCalcTool API
    def is_registered(self):
        return self.wlcalc is not None

    def register_tool(self, wlcalc: QWidget):
        # Setup wlcalc.
        self.wlcalc = wlcalc
        index = wlcalc.tools_tabwidget.addTab(self, self.title())
        wlcalc.tools_tabwidget.setTabToolTip(index, self.tooltip())
        # wlcalc.tools_tabwidget.currentChanged.connect(
        #     lambda: self.toggle_brfperiod_selection(False))
        wlcalc.sig_wldset_changed.connect(self._on_wldset_changed)
        wlcalc.sig_date_format_changed.connect(self._draw_mrc)
        wlcalc.sig_new_mrc = self.sig_new_mrc

        # Add "Show MRC" button to WLCalc toolbar.
        before_widget = wlcalc.btn_show_meas_wl
        for action in wlcalc.toolbar.actions():
            if wlcalc.toolbar.widgetForAction(action) == before_widget:
                wlcalc.toolbar.insertWidget(
                    action, self.btn_show_mrc)

        # Setup the axes widget to add and remove recession periods.
        wlcalc.register_navig_and_select_tool(self.btn_add_period)
        wlcalc.register_navig_and_select_tool(self.btn_del_period)

        self.mrc_selector = WLCalcVSpanSelector(
            self.wlcalc.fig.axes[0], wlcalc,
            onselected=self._on_period_selected)
        wlcalc.install_axeswidget(self.mrc_selector)

        self.mrc_remover = WLCalcVSpanHighlighter(
            self.wlcalc.fig.axes[0], wlcalc, self._mrc_period_axvspans,
            onclicked=self.remove_mrcperiod)
        wlcalc.install_axeswidget(self.mrc_remover)

        # Init matplotlib artists.
        self._mrc_plt, = self.wlcalc.fig.axes[0].plot(
            [], [], color='red', clip_on=True,
            zorder=15, marker='None', linestyle='--')

        self.load_mrc_from_wldset()
        self._draw_mrc()

    def close_tool(self):
        self.set_option('show_mrc', self.btn_show_mrc.value())
        super().close()

    def set_wldset(self, wldset):
        pass

    def set_wxdset(self, wxdset):
        pass

    # ---- MRC Tool Public Interface
    def calculate_mrc(self):
        if self.wldset is None:
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)

        coeffs, hp, std_err, r_squared, rmse = calculate_mrc(
            self.wldset.xldates,
            self.wldset.waterlevels,
            self._mrc_period_xdata,
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
            self.wldset.xldates, hp,
            std_err, r_squared, rmse)

        self.show_mrc_results()
        self.btn_save_mrc.setEnabled(True)
        self._draw_mrc()
        self.sig_new_mrc.emit()

        QApplication.restoreOverrideCursor()

    def save_mrc_tofile(self, filename=None):
        """Save the master recession curve results to a file."""
        if self.wldset is None:
            return

        if filename is None:
            filename = osp.join(
                self.dialog_dir,
                "mrc_results ({}).csv".format(self.wldset['Well']))

        filename, filetype = QFileDialog.getSaveFileName(
            self.parent() or self,
            "Save MRC results",
            filename,
            'Text CSV (*.csv)')

        if filename:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            QApplication.processEvents()
            try:
                self.wldset.save_mrc_tofile(filename)
            except PermissionError:
                self.show_permission_error(widget=self.parent())
                self.save_mrc_tofile(filename)
            QApplication.restoreOverrideCursor()

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
        self._draw_mrc()

    def undo_mrc_period(self):
        """
        Undo the last operation performed by the user on the selection
        of mrc periods.
        """
        if len(self._mrc_period_memory) > 1:
            self._mrc_period_xdata = self._mrc_period_memory[-2].copy()
            del self._mrc_period_memory[-1]
            self._draw_mrc()

    def clear_all_mrcperiods(self):
        """Clear all mrc periods from the graph."""
        if len(self._mrc_period_xdata) > 0:
            self._mrc_period_xdata = []
            self._mrc_period_memory.append([])
        self._draw_mrc()

    def remove_mrcperiod(self, xdata):
        """
        Remove the mrc period at xdata if any.
        """
        for i, period_xdata in enumerate(self._mrc_period_xdata):
            period_xmin = period_xdata[0]
            period_xmax = period_xdata[1]
            if xdata >= period_xmin and xdata <= period_xmax:
                del self._mrc_period_xdata[i]
                self._mrc_period_memory.append(self._mrc_period_xdata.copy())
                self._draw_mrc()
                break

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
