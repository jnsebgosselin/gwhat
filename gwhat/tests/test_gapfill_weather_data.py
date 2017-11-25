# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 01:50:50 2017
@author: jsgosselin
"""

# Standard library imports
import sys
import os

# Third party imports
import numpy as np
from numpy import nan
import pytest
from PyQt5.QtCore import Qt

# Local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from gwhat.meteo.gapfill_weather_gui import GapFillWeatherGUI


# Qt Test Fixtures
# --------------------------------


working_dir = os.path.join(os.getcwd(), "@ new-prô'jèt!")


@pytest.fixture
def gapfill_weather_bot(qtbot):
    gapfiller = GapFillWeatherGUI()
    gapfiller.set_workdir(working_dir)
    qtbot.addWidget(gapfiller)

    return gapfiller, qtbot


# Test RawDataDownloader
# -------------------------------

expected_results = ["IBERVILLE", "IBERVILLE (1)",
                    "L'ACADIE", "L'ACADIE (1)",
                    "MARIEVILLE", "MARIEVILLE (1)",
                    "Station 1", "Station 1 (1)"]


@pytest.mark.run(order=5)
def test_refresh_data(gapfill_weather_bot, mocker):
    gapfiller, qtbot = gapfill_weather_bot
    gapfiller.show()

    # Load the input weather datafiles and assert that the list is loaded and
    # displayed as expected.
    qtbot.mouseClick(gapfiller.btn_refresh_staList, Qt.LeftButton)

    results = []
    for i in range(gapfiller.target_station.count()):
        results.append(gapfiller.target_station.itemText(i))

    assert expected_results == results


@pytest.mark.run(order=5)
def test_delete_data(gapfill_weather_bot, mocker):
    gapfiller, qtbot = gapfill_weather_bot
    gapfiller.show()

    # Load the input weather datafiles and select the last one in the list.
    qtbot.mouseClick(gapfiller.btn_refresh_staList, Qt.LeftButton)
    last_index = gapfiller.target_station.count()-1
    gapfiller.target_station.setCurrentIndex(last_index)
    assert gapfiller.target_station.currentText() == expected_results[-1]

    # Delete the currently selected dataset.
    qtbot.mouseClick(gapfiller.btn_delete_data, Qt.LeftButton)

    results = []
    for i in range(gapfiller.target_station.count()):
        results.append(gapfiller.target_station.itemText(i))

    assert expected_results[:-1] == results


if __name__ == "__main__":
    pytest.main([os.path.basename(__file__)])
    # pytest.main()
