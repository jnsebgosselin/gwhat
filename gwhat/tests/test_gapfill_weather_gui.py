# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
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
from gwhat.meteo.gapfill_weather_gui import (GapFillWeatherGUI, QFileDialog,
                                             QMessageBox)
from gwhat.common.utils import delete_folder_recursively
from gwhat.meteo.weather_reader import read_weather_datafile


# Qt Test Fixtures
# --------------------------------


working_dir = os.path.join(os.getcwd(), "@ new-prô'jèt!")
output_dir = os.path.join(working_dir, "Meteo", "Output")
input_dir = os.path.join(working_dir, "Meteo", "Input")


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
        assert os.path.exists(os.path.join(input_dir, file))

    # Select the datasets one by one by their filenames and delete them.
    for file in files:
        fnames = gapfiller.gapfill_worker.WEATHER.fnames.tolist()
        index = fnames.index(file)
        gapfiller.target_station.setCurrentIndex(index)
        qtbot.mouseClick(gapfiller.btn_delete_data, Qt.LeftButton)

        # Wait and asses that the file was correctly deleted.
        filepath = os.path.join(input_dir, file)
        qtbot.waitUntil(lambda: not os.path.exists(filepath))

    # Assert that the dataset were effectively removed from the list.
    expected_results = ["IBERVILLE", "L'ACADIE", "MARIEVILLE"]
    results = []
    for i in range(gapfiller.target_station.count()):
        results.append(gapfiller.target_station.itemText(i))
    assert expected_results == results


@pytest.mark.run(order=5)
def test_fill_data(gapfill_weather_bot, mocker):
    """
    Fill the data for the first dataset.
    """
    delete_folder_recursively(output_dir)

    gapfiller, qtbot = gapfill_weather_bot
    gapfiller.show()
    qtbot.mouseClick(gapfiller.btn_refresh_staList, Qt.LeftButton)

    # Click button "Fill Data" while no station is selected.
    mocker.patch.object(QMessageBox, 'warning', return_value=QMessageBox.Ok)
    qtbot.mouseClick(gapfiller.btn_fill, Qt.LeftButton)

    # Select first dataset and gapfill the data.
    gapfiller.target_station.setCurrentIndex(0)
    qtbot.mouseClick(gapfiller.btn_fill, Qt.LeftButton)
    qtbot.waitUntil(lambda: not gapfiller.gapfill_thread.isRunning(),
                    timeout=100000)

    # Assert that all the ouput files were generated correctly.
    basenames = ["IBERVILLE (7023270)_2000-2015.out",
                 "IBERVILLE (7023270)_2000-2015.log",
                 "weather_normals.pdf"]
    for basename in basenames:
        fname = os.path.join(output_dir, "IBERVILLE (7023270)", basename)
        assert os.path.exists(fname)

    # Assert that ETP was NOT added to the output file.
    filename = os.path.join(output_dir, "IBERVILLE (7023270)", basenames[0])
    wxdf = read_weather_datafile(filename)
    assert wxdf['PET'] is None


@pytest.mark.run(order=5)
def test_add_ETP(gapfill_weather_bot, mocker):
    gapfiller, qtbot = gapfill_weather_bot
    gapfiller.show()
    qtbot.mouseClick(gapfiller.btn_refresh_staList, Qt.LeftButton)

    # Mock the QFileDialog to return the path of the file.
    filename = os.path.join(output_dir, "IBERVILLE (7023270)",
                            "IBERVILLE (7023270)_2000-2015.out")
    mocker.patch.object(QFileDialog, 'getOpenFileName',
                        return_value=(filename, '*.out'))

    # Add ETP to file to the output weather data file.
    qtbot.mouseClick(gapfiller.btn_add_PET, Qt.LeftButton)

    # Assert that ETP was added to the output file.
    wxdf = read_weather_datafile(filename)
    assert len(wxdf['PET']) == len(wxdf['Time'])


@pytest.mark.run(order=5)
def test_gapfill_all_data(gapfill_weather_bot):
    """
    Fill the data in each dataset one by one with the default values for
    the parameters.
    """
    delete_folder_recursively(output_dir)

    gapfiller, qtbot = gapfill_weather_bot
    gapfiller.show()
    qtbot.mouseClick(gapfiller.btn_refresh_staList, Qt.LeftButton)

    # Check the option "Add PET to datafile" in the "Advanced Settings".
    gapfiller.add_PET_ckckbox.setCheckState(Qt.Checked)

    # Gapfill the data for each dataset in batch
    qtbot.mouseClick(gapfiller.btn_fill_all, Qt.LeftButton)
    qtbot.waitUntil(lambda: not gapfiller.isFillAll_inProgress, timeout=100000)

    # Assert that all the ouput files were generated correctly.
    files = [os.path.join(output_dir, "IBERVILLE (7023270)",
                          "IBERVILLE (7023270)_2000-2015.out"),
             os.path.join(output_dir, "IBERVILLE (7023270)",
                          "IBERVILLE (7023270)_2000-2015.log"),
             os.path.join(output_dir, "IBERVILLE (7023270)",
                          "weather_normals.pdf"),
             os.path.join(output_dir, "L'ACADIE (702LED4)",
                          "L'ACADIE (702LED4)_2000-2015.out"),
             os.path.join(output_dir, "L'ACADIE (702LED4)",
                          "L'ACADIE (702LED4)_2000-2015.log"),
             os.path.join(output_dir, "L'ACADIE (702LED4)",
                          "weather_normals.pdf"),
             os.path.join(output_dir, "MARIEVILLE (7024627)",
                          "MARIEVILLE (7024627)_2000-2015.out"),
             os.path.join(output_dir, "MARIEVILLE (7024627)",
                          "MARIEVILLE (7024627)_2000-2015.log"),
             os.path.join(output_dir, "MARIEVILLE (7024627)",
                          "weather_normals.pdf")
             ]
    for file in files:
        assert os.path.exists(file)

    # Assert that ETP was added to the output file.
    filenames = [files[i] for i in [0, 3, 6]]
    for filename in filenames:
        wxdf = read_weather_datafile(filename)
        assert len(wxdf['PET']) == len(wxdf['Time'])


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
    # pytest.main()
