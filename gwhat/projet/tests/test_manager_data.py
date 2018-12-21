# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.


# ---- Standard Libraries Imports
import os
import os.path as osp

# ---- Third Party Libraries Imports
import pytest
from PyQt5.QtCore import Qt


# ---- Local Libraries Imports
from gwhat.meteo.weather_reader import WXDataFrame
from gwhat.projet.reader_projet import ProjetReader
from gwhat.projet.manager_data import DataManager, QFileDialog, QMessageBox

DATADIR = osp.dirname(osp.realpath(__file__))
WXFILENAME = osp.join(DATADIR, 'data', 'sample_weather_datafile.out')
WLFILENAME = osp.join(DATADIR, 'data', 'sample_water_level_datafile.csv')


# ---- Pytest Fixtures
@pytest.fixture(scope="module")
def project(tmp_path_factory):
    # Create a project and add add the wldset to it.
    basetemp = tmp_path_factory.getbasetemp()
    return ProjetReader(osp.join(basetemp, "data_manager_test.gwt"))


@pytest.fixture
def datamanager(project, qtbot):
    datamanager = DataManager(projet=project, pytesting=True)
    qtbot.addWidget(datamanager)
    qtbot.addWidget(datamanager.new_waterlvl_win)
    qtbot.addWidget(datamanager.new_weather_win)

    return datamanager


# ---- Tests DataManager
def test_import_weather_data(datamanager, mocker, qtbot):
    """Test importing and saving weather data to the project."""
    datamanager.new_weather_win.setModal(False)
    datamanager.show()

    # Mock the file dialog to return the path of the weather datafile.
    mocker.patch.object(
        QFileDialog, 'getOpenFileName', return_value=(WXFILENAME, '*.out'))

    # Open the dialog window and select a weather dataset.
    qtbot.mouseClick(datamanager.btn_load_meteo, Qt.LeftButton)
    qtbot.mouseClick(datamanager.new_weather_win.btn_browse, Qt.LeftButton)

    assert datamanager.new_weather_win.name == "IBERVILLE"
    assert datamanager.new_weather_win.station_name == "IBERVILLE"
    assert datamanager.new_weather_win.station_id == "7023270"
    assert datamanager.new_weather_win.province == "QUEBEC"
    assert datamanager.new_weather_win.latitude == 45.33
    assert datamanager.new_weather_win.longitude == -73.25
    assert datamanager.new_weather_win.altitude == 30.5

    # Import the weather dataset into the project.
    qtbot.mouseClick(datamanager.new_weather_win.btn_ok, Qt.LeftButton)
    assert datamanager.wxdataset_count() == 1
    assert datamanager.wxdsets_cbox.currentText() == "IBERVILLE"
    assert datamanager.get_current_wxdset().name == "IBERVILLE"


def test_delete_weather_data(datamanager, mocker, qtbot):
    """Test deleting weather datasets from the project."""
    datamanager.show()

    # Click on the button to delete the weather dataset from the project, but
    # answer no.
    assert datamanager.wxdataset_count() == 1
    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.No)
    qtbot.mouseClick(datamanager.btn_del_wxdset, Qt.LeftButton)
    assert datamanager.wxdataset_count() == 1

    # Click on the button to delete the weather dataset from the project and
    # answer yes.
    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes)
    qtbot.mouseClick(datamanager.btn_del_wxdset, Qt.LeftButton)
    assert datamanager.wxdataset_count() == 0


def test_import_waterlevel_data(datamanager, mocker, qtbot):
    """Test importing and saving water level data to the project."""
    datamanager.new_weather_win.setModal(False)
    datamanager.show()

    # Mock the file dialog to return the path of the weather datafile.
    mocker.patch.object(
        QFileDialog, 'getOpenFileName', return_value=(WLFILENAME, '*.out'))

    # Open the dialog window and select a water level dataset.
    qtbot.mouseClick(datamanager.btn_load_wl, Qt.LeftButton)
    qtbot.mouseClick(datamanager.new_waterlvl_win.btn_browse, Qt.LeftButton)

    new_waterlvl_win = datamanager.new_waterlvl_win
    assert new_waterlvl_win.name == "PO01 - Calixa-Lavallée"
    assert new_waterlvl_win.station_name == "PO01 - Calixa-Lavallée"
    assert new_waterlvl_win.station_id == "3040002"
    assert new_waterlvl_win.province == "QC"
    assert new_waterlvl_win.latitude == 45.74581
    assert new_waterlvl_win.longitude == -73.28024
    assert new_waterlvl_win.altitude == 19.51

    # Import the water level dataset into the project.
    qtbot.mouseClick(new_waterlvl_win.btn_ok, Qt.LeftButton)
    assert datamanager.wldataset_count() == 1
    assert datamanager.wldsets_cbox.currentText() == "PO01 - Calixa-Lavallée"
    assert datamanager.get_current_wldset().name == "PO01 - Calixa-Lavallée"


def test_delete_waterlevel_data(datamanager, mocker, qtbot):
    """Test deleting water level datasets from the project."""
    datamanager.show()

    # Click on the button to delete the water level dataset from the project,
    # but answer no.
    assert datamanager.wldataset_count() == 1
    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.No)
    qtbot.mouseClick(datamanager.btn_del_wldset, Qt.LeftButton)
    assert datamanager.wldataset_count() == 1

    # Click on the button to delete the water level dataset from the project
    # and answer yes.
    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes)
    qtbot.mouseClick(datamanager.btn_del_wldset, Qt.LeftButton)
    assert datamanager.wldataset_count() == 0


# ---- Tests ExportWeatherButton
def test_export_yearly_monthly_daily(datamanager, mocker, qtbot, tmp_path):
    """
    Test exporting a weather dataset to various file format and time frame.
    """
    datamanager.show()
    wxdset = WXDataFrame(WXFILENAME)
    datamanager.new_wxdset_imported(wxdset['Station Name'], wxdset)

    for ftype in ['xlsx', 'csv', 'xls']:
        for time_frame in ['daily', 'monthly', 'yearly']:
            filename = osp.join(
                tmp_path, "export_{}_weather.{}".format(time_frame, ftype))
            mocker.patch.object(
                QFileDialog,
                'getSaveFileName',
                return_value=(filename, '*.'+ftype))
            datamanager.btn_export_weather.select_export_file(time_frame)
            assert osp.exists(filename)


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
    # pytest.main()
