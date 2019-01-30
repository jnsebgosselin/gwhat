# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Standard library imports
import os
import os.path as osp
from itertools import product
from shutil import copyfile

# Third party imports
import pytest

# Local imports
from gwhat.meteo.gapfill_weather_algorithm2 import GapFillWeather


# ---- Pytest Fixtures
DATADIR = os.path.join(osp.dirname(osp.realpath(__file__)), "data")
INPUTFILES = ["IBERVILLE (7023270)_2000-2015.csv",
              "L'ACADIE (702LED4)_2000-2015.csv",
              "MARIEVILLE (7024627)_2000-2015.csv"]


@pytest.fixture(scope="module")
def workdir(tmp_path_factory):
    basetemp = tmp_path_factory.getbasetemp()
    return osp.join(basetemp, "@ tèst-fïl! 'dätèt!")


@pytest.fixture(scope="module")
def inputdir(workdir):
    inputdir = osp.join(workdir, "Meteo", "Input")

    # Copy the input data files into the temp input directory.
    os.makedirs(inputdir, exist_ok=True)

    for file in INPUTFILES:
        copyfile(osp.join(DATADIR, file), osp.join(inputdir, file))
    return inputdir


@pytest.fixture(scope="module")
def outputdir(workdir):
    return osp.join(workdir, "Meteo", "Output")


@pytest.fixture
def gapfiller(inputdir, outputdir):
    gapfiller = GapFillWeather()
    gapfiller.inputDir = inputdir
    gapfiller.outputDir = outputdir
    return gapfiller


# ---- Test GapFillWeather
def test_load_data(gapfiller):
    """Test loading input data automatically from the inpu directory."""

    # Load input weather datafiles and assert the results.
    expected_results = ["IBERVILLE", "L'ACADIE", "MARIEVILLE"]
    stanames = gapfiller.load_data()
    for name in stanames:
        assert name in expected_results


@pytest.mark.run(order=6)
def test_fill_data(gapfiller, outputdir):
    """Test filling missing data."""
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
    files = [("IBERVILLE (7023270)", "IBERVILLE (7023270)_2000-2015.out"),
             ("IBERVILLE (7023270)", "IBERVILLE (7023270)_2000-2015.log"),
             ("IBERVILLE (7023270)", "IBERVILLE (7023270)_2000-2015.err"),
             ("L'ACADIE (702LED4)", "L'ACADIE (702LED4)_2000-2015.out"),
             ("L'ACADIE (702LED4)", "L'ACADIE (702LED4)_2000-2015.log"),
             ("L'ACADIE (702LED4)", "L'ACADIE (702LED4)_2000-2015.err"),
             ("MARIEVILLE (7024627)", "MARIEVILLE (7024627)_2000-2015.out"),
             ("MARIEVILLE (7024627)", "MARIEVILLE (7024627)_2000-2015.log"),
             ("MARIEVILLE (7024627)", "MARIEVILLE (7024627)_2000-2015.err")
             ]
    for dirname, basename in files:
        assert osp.exists(osp.join(outputdir, dirname, basename))

    dirnames = ["IBERVILLE (7023270)",
                "L'ACADIE (702LED4)",
                "MARIEVILLE (7024627)"]
    fignames = ["weather_normals.pdf", "max_temp_deg_c.pdf",
                "mean_temp_deg_c.pdf", "min_temp_deg_c.pdf",
                "precip_PDF.pdf", "total_precip_mm.pdf"]
    for dirname, figname in product(dirnames, fignames):
        assert os.path.join(outputdir, dirname, figname)


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
