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
from gwhat.HydroPrint2 import HydroprintGUI
from gwhat.projet.manager_data import DataManager
from gwhat.projet.reader_projet import ProjetReader


# Qt Test Fixtures
# --------------------------------


working_dir = os.path.join(os.getcwd(), "@ new-prô'jèt!")
output_dir = os.path.join(working_dir, "Water Levels")


@pytest.fixture
def hydroprint_bot(qtbot):
    pf = os.path.join(working_dir, "@ new-prô'jèt!.gwt")
    pr = ProjetReader(pf)

    dm = DataManager()
    dm.set_projet(pr)

    hydroprint = HydroprintGUI(dm)
    qtbot.addWidget(hydroprint)

    return hydroprint, qtbot


# Test HydroprintGUI
# -------------------------------


@pytest.mark.run(order=8)
def test_hydroprint_init(hydroprint_bot, mocker):
    hydroprint, qtbot = hydroprint_bot
    hydroprint.show()
    assert hydroprint

    # Assert that the water_level_measurement file was initialize correctly.
    filename = os.path.join(output_dir, "waterlvl_manual_measurements.csv")
    assert os.path.exists(filename)


@pytest.mark.run(order=8)
def test_autoplot_hydroprint(hydroprint_bot):
    hydroprint, qtbot = hydroprint_bot
    hydroprint.show()

    # Forces a refresh of the graph and check that the automatic values
    # set for the axis is correct.

    hydroprint.wldset_changed()

    assert hydroprint.waterlvl_scale.value() == 0.25
    assert hydroprint.waterlvl_max.value() == 3.75
    assert hydroprint.NZGridWL_spinBox.value() == 8
    assert hydroprint.datum_widget.currentText() == 'Ground Surface'


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
    # pytest.main()
