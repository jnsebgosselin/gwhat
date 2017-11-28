# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

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
    qtbot.addWidget(gapfiller.pbar)

    return gapfiller, qtbot


# Test RawDataDownloader
# -------------------------------


@pytest.mark.run(order=5)
def test_refresh_data(gapfill_weather_bot, mocker):

    expected_results = ["IBERVILLE", "IBERVILLE (1)",
                        "L'ACADIE", "L'ACADIE (1)",
                        "MARIEVILLE", "MARIEVILLE (1)",
                        "Station 1", "Station 1 (1)"]

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
    dirname = os.path.join(os.getcwd(), "@ new-prô'jèt!", "Meteo", "Input")

    gapfiller, qtbot = gapfill_weather_bot
    gapfiller.show()

    # Load the input weather datafiles.
    qtbot.mouseClick(gapfiller.btn_refresh_staList, Qt.LeftButton)

    # Assert that the files that need to be deleted exists.
    files = ["IBERVILLE (7023270)_2000-2002.csv",
             "L'ACADIE (702LED4)_2000-2002.csv",
             "MARIEVILLE (7024627)_2000-2002.csv",
             "Station 1 (7020561)_1960-1990.csv",
             "Station 12 (7020562)_1960-1990.csv"]
    for file in files:
        assert os.path.exists(os.path.join(dirname, file))

    # Select the datasets one by one by their filenames and delete them.
    for file in files:
        index = gapfiller.gapfill_worker.WEATHER.fnames.index(file)
        gapfiller.target_station.setCurrentIndex(index)
        qtbot.mouseClick(gapfiller.btn_delete_data, Qt.LeftButton)

    # Assert that the dataset were effectively removed from the list.
    expected_results = ["IBERVILLE", "L'ACADIE", "MARIEVILLE"]
    results = []
    for i in range(gapfiller.target_station.count()):
        results.append(gapfiller.target_station.itemText(i))
    assert expected_results == results

    # Assert that the files were removed from the disk.
    for file in files:
        assert not os.path.exists(os.path.join(dirname, file))


@pytest.mark.run(order=5)
def test_gapfill_data(gapfill_weather_bot, mocker):
    """
    Fill the data in each dataset one by one with the default values for
    the parameters.
    """
    gapfiller, qtbot = gapfill_weather_bot
    gapfiller.show()
    qtbot.mouseClick(gapfiller.btn_refresh_staList, Qt.LeftButton)

    # Gapfill the data for each dataset in batch
    qtbot.mouseClick(gapfiller.btn_fill_all, Qt.LeftButton)
    qtbot.waitUntil(lambda: not gapfiller.isFillAll_inProgress, timeout=100000)

    assert gapfiller.isFillAll_inProgress is False


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
    # pytest.main()
