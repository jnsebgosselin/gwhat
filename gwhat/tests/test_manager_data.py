# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

import pytest

import sys
import os.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

# ---- Third party imports

import pytest
from PyQt5.QtCore import Qt

# Local imports
from gwhat.projet.reader_projet import ProjetReader
from gwhat.projet.manager_data import DataManager, QFileDialog, QMessageBox

projetpath = os.path.join(os.getcwd(), "@ new-prô'jèt!", "@ new-prô'jèt!.gwt")


# Qt Test Fixtures
# --------------------------------

@pytest.fixture
def data_manager_bot(qtbot):
    data_manager = DataManager(projet=ProjetReader(projetpath),
                               pytesting=True)
    qtbot.addWidget(data_manager)
    qtbot.addWidget(data_manager.new_waterlvl_win)
    qtbot.addWidget(data_manager.new_weather_win)

    return data_manager, qtbot

# Tests
# -------------------------------


@pytest.mark.run(order=7)
def test_load_projet(data_manager_bot):
    data_manager, qtbot = data_manager_bot
    data_manager.show()
    assert data_manager


@pytest.mark.run(order=7)
def test_import_weather_data(data_manager_bot, mocker):
    data_manager, qtbot = data_manager_bot
    data_manager.new_weather_win.setModal(False)
    data_manager.show()

    # Assert that the weather datafile exists.
    output_dir = os.path.join(os.getcwd(), "@ new-prô'jèt!", "Meteo", "Output")
    filename = os.path.join(output_dir, "IBERVILLE (7023270)",
                            "IBERVILLE (7023270)_2000-2010.out")
    assert os.path.exists(filename)

    # Mock the QFileDialog to return the path of the file.
    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes)
    mocker.patch.object(QFileDialog, 'getOpenFileName',
                        return_value=(filename, '*.out'))

    # Open the dialog window and select a weather dataset.
    qtbot.mouseClick(data_manager.btn_load_meteo, Qt.LeftButton)
    qtbot.mouseClick(data_manager.new_weather_win.btn_browse, Qt.LeftButton)

    assert data_manager.new_weather_win.name == "IBERVILLE"
    assert data_manager.new_weather_win.station_name == "IBERVILLE"
    assert data_manager.new_weather_win.station_id == "7023270"
    assert data_manager.new_weather_win.province == "QUEBEC"
    assert data_manager.new_weather_win.latitude == 45.33
    assert data_manager.new_weather_win.longitude == -73.25
    assert data_manager.new_weather_win.altitude == 30.5

    # Import the weather dataset.
    qtbot.mouseClick(data_manager.new_weather_win.btn_ok, Qt.LeftButton)

    # Assert that a weather dataset was added to the project and is currently
    # selected.
    assert data_manager.wxdataset_count() == 1
    assert data_manager.wxdsets_cbox.currentText() == "IBERVILLE"


@pytest.mark.run(order=7)
def test_delete_weather_data(data_manager_bot, mocker):
    data_manager, qtbot = data_manager_bot
    data_manager.show()

    # Mock the QMessageBox to return Yes, delete the weather dataset, and
    # assert that it was removed from the project.
    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes)
    qtbot.mouseClick(data_manager.btn_del_wxdset, Qt.LeftButton)
    assert data_manager.wxdataset_count() == 0


@pytest.mark.run(order=7)
def test_import_waterlevel_data(data_manager_bot, mocker):
    data_manager, qtbot = data_manager_bot
    data_manager.new_weather_win.setModal(False)
    data_manager.show()

    # Assert that the water level datafile exists.
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "sample_water_level_datafile.xlsx")
    assert os.path.exists(filename)

    # Mock the QFileDialog to return the path of the file.
    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes)
    mocker.patch.object(QFileDialog, 'getOpenFileName',
                        return_value=(filename, '*.xlsx'))

    # Open the dialog window and select a waterlevel dataset.
    qtbot.mouseClick(data_manager.btn_load_wl, Qt.LeftButton)
    qtbot.mouseClick(data_manager.new_waterlvl_win.btn_browse, Qt.LeftButton)

    assert data_manager.new_waterlvl_win.name == "PO01 - Calixa-Lavallée"
    assert data_manager.new_waterlvl_win.station_name == "PO01 - Calixa-Lavallée"
    assert data_manager.new_waterlvl_win.station_id == "3040002"
    assert data_manager.new_waterlvl_win.province == "QC"
    assert data_manager.new_waterlvl_win.latitude == 45.74581
    assert data_manager.new_waterlvl_win.longitude == -73.28024
    assert data_manager.new_waterlvl_win.altitude == 19.51

    # Import the waterlevel dataset.
    qtbot.mouseClick(data_manager.new_waterlvl_win.btn_ok, Qt.LeftButton)

    # Assert that a weather dataset was added to the project and is currently
    # selected.
    assert data_manager.wldataset_count() == 1
    assert data_manager.wldsets_cbox.currentText() == "PO01 - Calixa-Lavallée"


@pytest.mark.run(order=7)
def test_delete_waterlevel_data(data_manager_bot, mocker):
    data_manager, qtbot = data_manager_bot
    data_manager.show()

    # Mock the QMessageBox to return Yes, delete the waterlevel dataset, and
    # assert that it was removed from the project.
    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes)
    qtbot.mouseClick(data_manager.btn_del_wldset, Qt.LeftButton)
    assert data_manager.wldataset_count() == 0

    # Import the water level again since we will need it for another test.
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "sample_water_level_datafile.xlsx")
    data_manager.new_waterlvl_win.load_dataset(filename)
    data_manager.new_waterlvl_win.accept_dataset()
    assert data_manager.wldataset_count() == 1


@pytest.mark.run(order=7)
def test_import_back_alldata(data_manager_bot):
    data_manager, qtbot = data_manager_bot
    data_manager.show()

    # Import the weather data again since we will need it for another test.
    output_dir = os.path.join(os.getcwd(), "@ new-prô'jèt!", "Meteo", "Output")
    filenames = [os.path.join(output_dir, "IBERVILLE (7023270)",
                              "IBERVILLE (7023270)_2000-2010.out"),
                 os.path.join(output_dir, "L'ACADIE (702LED4)",
                              "L'ACADIE (702LED4)_2000-2010.out"),
                 os.path.join(output_dir, "MARIEVILLE (7024627)",
                              "MARIEVILLE (7024627)_2000-2010.out")
                 ]
    for filename in filenames:
        data_manager.new_weather_win.load_dataset(filename)
        data_manager.new_waterlvl_win.accept_dataset()
    assert data_manager.wxdataset_count() == 3

    # Import the water level again since we will need it for another test.
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "sample_water_level_datafile.xlsx")
    data_manager.new_waterlvl_win.load_dataset(filename)
    data_manager.new_waterlvl_win.accept_dataset()
    assert data_manager.wldataset_count() == 1


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
    # pytest.main()
