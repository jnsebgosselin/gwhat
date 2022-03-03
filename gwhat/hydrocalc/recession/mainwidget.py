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
    QWidget, QComboBox, QTextEdit, QSizePolicy)

# ---- Local imports
from gwhat.hydrocalc.axeswidgets import WLCalcVSpanSelector
from gwhat.hydrocalc.api import WLCalcTool, wlcalcmethod
from gwhat.utils.qthelpers import create_toolbutton
from gwhat.utils.icons import QToolButtonNormal, get_iconsize
from gwhat.widgets.buttons import OnOffToolButton


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

