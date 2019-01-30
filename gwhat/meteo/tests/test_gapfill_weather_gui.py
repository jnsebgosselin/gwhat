# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Standard library imports
import os
import os.path as osp
from shutil import copyfile

# ---- Third party imports
import pytest
from PyQt5.QtCore import Qt

# Local imports
from gwhat.meteo.gapfill_weather_gui import (GapFillWeatherGUI, QFileDialog,
                                             QMessageBox)
from gwhat.common.utils import delete_folder_recursively
from gwhat.meteo.weather_reader import read_weather_datafile


# ---- Pytest Fixtures
DATADIR = os.path.join(osp.dirname(osp.realpath(__file__)), "data")
INPUTFILES = ["IBERVILLE (7023270)_2000-2015.csv",
              "L'ACADIE (702LED4)_2000-2015.csv",
              "MARIEVILLE (7024627)_2000-2015.csv"]


@pytest.fixture(scope="module")
def workdir(tmp_path_factory):
    basetemp = tmp_path_factory.getbasetemp()
    workdir = osp.join(basetemp, "@ tèst-fïl! 'dätèt!")

    # Copy the input data files into the temp input directory.
    inputdir = osp.join(workdir, "Meteo", "Input")
    os.makedirs(inputdir, exist_ok=True)
    for file in INPUTFILES:
        copyfile(osp.join(DATADIR, file), osp.join(inputdir, file))

    return workdir


@pytest.fixture
def gapfiller_widget(workdir, qtbot):
    gapfiller_widget = GapFillWeatherGUI()
    gapfiller_widget.set_workdir(workdir)
    qtbot.addWidget(gapfiller_widget)
    qtbot.addWidget(gapfiller_widget.pbar)

    return gapfiller_widget


# ---- Tests
def test_refresh_data(gapfiller_widget, qtbot):
    """Test that refreshing the data loads correctly the data."""
    gapfiller_widget.show()

    # Load the input weather datafiles and assert that the list is loaded and
    # displayed as expected.
    qtbot.mouseClick(gapfiller_widget.btn_refresh_staList, Qt.LeftButton)

    # Assert the list of station displayed in the dropdown menu of the widget.
    expected_results = ["IBERVILLE", "L'ACADIE", "MARIEVILLE"]
    assert expected_results == gapfiller_widget.get_dataset_names()


def test_delete_data(gapfiller_widget, qtbot, mocker, workdir):
    """Test the button to delete inpu weather data."""
    gapfiller_widget.show()

    # Add a copy of the Marieville dataset.
    inputdir = osp.join(workdir, "Meteo", "Input")
    file_copy = osp.join(inputdir, 'a_copy_of_' + INPUTFILES[-1])
    copyfile(osp.join(DATADIR, INPUTFILES[-1]), file_copy)

    # Load the input weather datafiles.
    qtbot.mouseClick(gapfiller_widget.btn_refresh_staList, Qt.LeftButton)
    expected_results = [
        "IBERVILLE", "L'ACADIE", "MARIEVILLE", "MARIEVILLE (1)"]
    assert expected_results == gapfiller_widget.get_dataset_names()

    # Select the copy of the Marieville dataset.
    fnames = gapfiller_widget.gapfill_worker.WEATHER.fnames.tolist()
    index = fnames.index(osp.basename(file_copy))
    gapfiller_widget.target_station.setCurrentIndex(index)

    # Delete the copy of the Marieville dataset.
    qtbot.mouseClick(gapfiller_widget.btn_delete_data, Qt.LeftButton)
    qtbot.waitUntil(lambda: not osp.exists(file_copy))

    # Assert that the dataset were effectively removed from the list.
    expected_results = ["IBERVILLE", "L'ACADIE", "MARIEVILLE"]
    assert expected_results == gapfiller_widget.get_dataset_names()


def test_fill_data(gapfiller_widget, qtbot, mocker, workdir):
    """
    Fill the data for the first dataset.
    """
    gapfiller_widget.show()
    qtbot.mouseClick(gapfiller_widget.btn_refresh_staList, Qt.LeftButton)

    # Click button "Fill Data" while no station is selected.
    mocker.patch.object(QMessageBox, 'warning', return_value=QMessageBox.Ok)
    qtbot.mouseClick(gapfiller_widget.btn_fill, Qt.LeftButton)

    # Select first dataset and gapfill the data.
    gapfiller_widget.target_station.setCurrentIndex(0)
    qtbot.mouseClick(gapfiller_widget.btn_fill, Qt.LeftButton)
    qtbot.waitUntil(lambda: not gapfiller_widget.gapfill_thread.isRunning(),
                    timeout=100000)

    # Assert that all the ouput files were generated correctly.
    basenames = ["IBERVILLE (7023270)_2000-2015.out",
                 "IBERVILLE (7023270)_2000-2015.log",
                 "weather_normals.pdf"]
    outputdir = osp.join(workdir, "Meteo", "Output")
    for basename in basenames:
        fname = osp.join(outputdir, "IBERVILLE (7023270)", basename)
        assert os.path.exists(fname)

    # Assert that ETP was NOT added to the output file.
    filename = osp.join(outputdir, "IBERVILLE (7023270)", basenames[0])
    wxdf = read_weather_datafile(filename)
    assert wxdf['PET'] is None


def test_add_ETP(gapfiller_widget, qtbot, mocker, workdir):
    """
    Test adding the estimated potential evapotranspiration to an
    output file.
    """
    gapfiller_widget.show()
    qtbot.mouseClick(gapfiller_widget.btn_refresh_staList, Qt.LeftButton)

    # Mock the QFileDialog to return the path of the file.
    outputdir = osp.join(workdir, "Meteo", "Output")
    filename = os.path.join(
        outputdir, "IBERVILLE (7023270)", "IBERVILLE (7023270)_2000-2015.out")
    mocker.patch.object(QFileDialog, 'getOpenFileName',
                        return_value=(filename, '*.out'))

    # Add ETP to file to the output weather data file.
    qtbot.mouseClick(gapfiller_widget.btn_add_PET, Qt.LeftButton)

    # Assert that ETP was added to the output file.
    wxdf = read_weather_datafile(filename)
    assert len(wxdf['PET']) == len(wxdf['Time'])


def test_gapfill_all_data(gapfiller_widget, qtbot, mocker, workdir):
    """
    Fill the data in each dataset one by one with the default values for
    the parameters.
    """
    outputdir = osp.join(workdir, "Meteo", "Output")
    delete_folder_recursively(outputdir)

    gapfiller_widget.show()
    qtbot.mouseClick(gapfiller_widget.btn_refresh_staList, Qt.LeftButton)

    # Check the option "Add PET to datafile" in the "Advanced Settings".
    gapfiller_widget.add_PET_ckckbox.setCheckState(Qt.Checked)

    # Gapfill the data for each dataset in batch
    qtbot.mouseClick(gapfiller_widget.btn_fill_all, Qt.LeftButton)
    qtbot.waitUntil(
        lambda: not gapfiller_widget.isFillAll_inProgress, timeout=100000)

    # Assert that all the ouput files were generated correctly.
    files = [osp.join(outputdir, "IBERVILLE (7023270)",
                      "IBERVILLE (7023270)_2000-2015.out"),
             osp.join(outputdir, "IBERVILLE (7023270)",
                      "IBERVILLE (7023270)_2000-2015.log"),
             osp.join(outputdir, "IBERVILLE (7023270)",
                      "weather_normals.pdf"),
             osp.join(outputdir, "L'ACADIE (702LED4)",
                      "L'ACADIE (702LED4)_2000-2015.out"),
             osp.join(outputdir, "L'ACADIE (702LED4)",
                      "L'ACADIE (702LED4)_2000-2015.log"),
             osp.join(outputdir, "L'ACADIE (702LED4)",
                      "weather_normals.pdf"),
             osp.join(outputdir, "MARIEVILLE (7024627)",
                      "MARIEVILLE (7024627)_2000-2015.out"),
             osp.join(outputdir, "MARIEVILLE (7024627)",
                      "MARIEVILLE (7024627)_2000-2015.log"),
             osp.join(outputdir, "MARIEVILLE (7024627)",
                      "weather_normals.pdf")]
    for file in files:
        assert os.path.exists(file)

    # Assert that ETP was added to the output file.
    filenames = [files[i] for i in [0, 3, 6]]
    for filename in filenames:
        wxdf = read_weather_datafile(filename)
        assert len(wxdf['PET']) == len(wxdf['Time'])


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
