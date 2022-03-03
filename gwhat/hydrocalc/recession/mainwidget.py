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

