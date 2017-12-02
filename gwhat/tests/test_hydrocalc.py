# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# Standard library imports
import sys
import os

# Third party imports
import pytest
from PyQt5.QtCore import Qt

# Local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from gwhat.HydroCalc2 import WLCalc
from gwhat.projet.manager_data import DataManager
from gwhat.projet.reader_projet import ProjetReader


# Qt Test Fixtures
# --------------------------------


working_dir = os.path.join(os.getcwd(), "@ new-prô'jèt!")
output_dir = os.path.join(working_dir, "Water Levels")


@pytest.fixture
def hydrocalc_bot(qtbot):
    pf = os.path.join(working_dir, "@ new-prô'jèt!.gwt")
    pr = ProjetReader(pf)

    dm = DataManager()
    dm.set_projet(pr)

    hydrocalc = WLCalc(dm)
    qtbot.addWidget(hydrocalc)

    return hydrocalc, qtbot


# Test WLCalc
# -------------------------------


@pytest.mark.run(order=9)
def test_hydrocalc_init(hydrocalc_bot, mocker):
    hydrocalc, qtbot = hydrocalc_bot
    hydrocalc.show()
    assert hydrocalc


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
    # pytest.main()
