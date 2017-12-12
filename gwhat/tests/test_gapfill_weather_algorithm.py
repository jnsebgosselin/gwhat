# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# Standard library imports
import sys
import os
from itertools import product

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
    delete_folder_recursively(output_dir)

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

    gapfiller.set_target_station(1)
    gapfiller.limitDist = -1
    gapfiller.limitAlt = -1
    gapfiller.fill_data()

    gapfiller.set_target_station(2)
    gapfiller.regression_mode = 1
    gapfiller.fill_data()

    # Assert that all the ouput files were generated correctly.
    files = [("IBERVILLE (7023270)", "IBERVILLE (7023270)_2000-2010.out"),
             ("IBERVILLE (7023270)", "IBERVILLE (7023270)_2000-2010.log"),
             ("IBERVILLE (7023270)", "IBERVILLE (7023270)_2000-2010.err"),
             ("L'ACADIE (702LED4)", "L'ACADIE (702LED4)_2000-2010.out"),
             ("L'ACADIE (702LED4)", "L'ACADIE (702LED4)_2000-2010.log"),
             ("L'ACADIE (702LED4)", "L'ACADIE (702LED4)_2000-2010.err"),
             ("MARIEVILLE (7024627)", "MARIEVILLE (7024627)_2000-2010.out"),
             ("MARIEVILLE (7024627)", "MARIEVILLE (7024627)_2000-2010.log"),
             ("MARIEVILLE (7024627)", "MARIEVILLE (7024627)_2000-2010.err")
             ]
    for dirname, basename in files:
        assert os.path.exists(os.path.join(output_dir, dirname, basename))

    dirnames = ["IBERVILLE (7023270)",
                "L'ACADIE (702LED4)",
                "MARIEVILLE (7024627)"]
    fignames = ["weather_normals.pdf", "max_temp_deg_c.pdf",
                "mean_temp_deg_c.pdf", "min_temp_deg_c.pdf",
                "precip_PDF.pdf", "total_precip_mm.pdf"]
    for dirname, figname in product(dirnames, fignames):
        assert os.path.join(output_dir, dirname, figname)


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
    # pytest.main()
