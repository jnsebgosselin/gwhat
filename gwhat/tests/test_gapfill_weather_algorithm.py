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
from gwhat.meteo.gapfill_weather_algorithm2 import GapFillWeather
from gwhat.common.utils import delete_folder_recursively


# Qt Test Fixtures
# --------------------------------


working_dir = os.path.join(os.getcwd(), "@ new-prô'jèt!")
input_dir = os.path.join(working_dir, "Meteo", "Input")
output_dir = os.path.join(working_dir, "Meteo", "Output")
delete_folder_recursively(output_dir)


@pytest.fixture
def gapfill_weather_bot(qtbot):
    gapfiller = GapFillWeather()
    return gapfiller, qtbot


# Test RawDataDownloader
# -------------------------------


@pytest.mark.run(order=6)
def test_load_data(gapfill_weather_bot):
    gapfiller, qtbot = gapfill_weather_bot
    gapfiller.inputDir = input_dir
    gapfiller.outputDir = output_dir

    # Load input weather datafiles and assert the results.
    expected_results = ["IBERVILLE", "L'ACADIE", "MARIEVILLE"]
    stanames = gapfiller.load_data()
    for name in stanames:
        assert name in expected_results


@pytest.mark.run(order=6)
def test_fill_data(gapfill_weather_bot):
    gapfiller, qtbot = gapfill_weather_bot
    gapfiller.inputDir = input_dir
    gapfiller.outputDir = output_dir
    gapfiller.load_data()

    # Set the parameters value of the gapfilling routine.
    gapfiller.time_start = gapfiller.WEATHER.TIME[0]
    gapfiller.time_end = gapfiller.WEATHER.TIME[-1]

    gapfiller.NSTAmax = 4
    gapfiller.limitDist = 100
    gapfiller.limitAlt = 350
    gapfiller.regression_mode = 0
    gapfiller.full_error_analysis = True
    gapfiller.add_ETP = True

    gapfiller.set_target_station(0)
    gapfiller.fill_data()

    gapfiller.regression_mode = 1
    gapfiller.set_target_station(1)
    gapfiller.fill_data()




if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
    # pytest.main()
