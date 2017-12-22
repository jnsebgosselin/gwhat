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

    assert hydroprint.dmngr.wldsets_cbox.currentText() == "PO01 - Calixa-Lavallée"
    assert hydroprint.dmngr.wxdsets_cbox.currentText() == "IBERVILLE"

    # Forces a refresh of the graph and check that the automatic values
    # set for the axis is correct.

    hydroprint.wldset_changed()
    assert hydroprint.dmngr.wxdsets_cbox.currentText() == "MARIEVILLE"
    assert hydroprint.waterlvl_scale.value() == 0.25
    assert hydroprint.waterlvl_max.value() == 3.75
    assert hydroprint.NZGridWL_spinBox.value() == 8
    assert hydroprint.datum_widget.currentText() == 'Ground Surface'
    data_start = hydroprint.date_start_widget.date()
    assert data_start.day() == 1
    assert data_start.month() == 11
    assert data_start.year() == 2012
    data_end = hydroprint.date_end_widget.date()
    assert data_end.day() == 1
    assert data_end.month() == 12
    assert data_end.year() == 2013
    assert hydroprint.time_scale_label.currentText() == "Month"


@pytest.mark.run(order=8)
def test_zoomin_zoomout(hydroprint_bot):
    hydroprint, qtbot = hydroprint_bot
    hydroprint.show()
    hydroprint.wldset_changed()

    expected_values = [100, 120, 144, 172, 172]
    for expected_value in expected_values:
        assert hydroprint.zoom_disp.value() == expected_value
        hydroprint.zoom_in()
    expected_values = [172, 144, 120, 100, 83, 69, 57, 57]
    for expected_value in expected_values:
        assert hydroprint.zoom_disp.value() == expected_value
        hydroprint.zoom_out()


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
    # pytest.main()
