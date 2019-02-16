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
from gwhat.projet.reader_waterlvl import WLDataFrame
from gwhat.projet.reader_projet import ProjetReader
from gwhat.projet.manager_data import (DataManager, QFileDialog, QMessageBox,
                                       QCheckBox)

DATADIR = osp.join(osp.dirname(osp.realpath(__file__)), 'data')
WXFILENAME = osp.join(DATADIR, 'sample_weather_datafile.out')
WLFILENAME = osp.join(DATADIR, 'sample_water_level_datafile.csv')


# ---- Pytest Fixtures
@pytest.fixture
def projectpath(tmpdir):
    return osp.join(str(tmpdir), "data_manager_test.gwt")


@pytest.fixture
def project(projectpath):
    # Create a project and add add the wldset to it.
    return ProjetReader(projectpath)


@pytest.fixture
def datamanager(project, qtbot):
    datamanager = DataManager(projet=project, pytesting=True)
    qtbot.addWidget(datamanager)
    qtbot.addWidget(datamanager.new_waterlvl_win)
    qtbot.addWidget(datamanager.new_weather_win)
    datamanager.show()

    return datamanager


# ---- Tests DataManager
def test_import_weather_data(datamanager, mocker, qtbot):
    """Test importing and saving weather data to the project."""
    datamanager.new_weather_win.setModal(False)

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
    """
    Test deleting weather datasets from the project.
    """
    datamanager.new_wxdset_imported('wxdset1', WXDataFrame(WXFILENAME))
    datamanager.new_wxdset_imported('wxdset2', WXDataFrame(WXFILENAME))
    assert datamanager.wxdataset_count() == 2

    # Click to delete the current weather dataset, but cancel.
    mock_exec_ = mocker.patch.object(
        QMessageBox, 'exec_', return_value=QMessageBox.Cancel)
    qtbot.mouseClick(datamanager.btn_del_wxdset, Qt.LeftButton)
    assert datamanager.wxdataset_count() == 2
    assert datamanager._confirm_before_deleting_dset is True
    assert mock_exec_.call_count == 1

    # Click to delete the current weather dataset, check the
    # 'Don't show this message again' option and answer Yes.
    mock_exec_.return_value = QMessageBox.Yes
    mocker.patch.object(QCheckBox, 'isChecked', return_value=True)
    with qtbot.waitSignal(datamanager.sig_new_console_msg, raising=True):
        qtbot.mouseClick(datamanager.btn_del_wxdset, Qt.LeftButton)
    assert datamanager.wxdataset_count() == 1
    assert datamanager._confirm_before_deleting_dset is False
    assert mock_exec_.call_count == 2

    # Click to delete the current weather dataset.
    with qtbot.waitSignal(datamanager.sig_new_console_msg, raising=True):
        qtbot.mouseClick(datamanager.btn_del_wxdset, Qt.LeftButton)
    assert datamanager.wxdataset_count() == 0
    assert datamanager._confirm_before_deleting_dset is False
    assert mock_exec_.call_count == 2


def test_import_waterlevel_data(datamanager, mocker, qtbot):
    """Test importing and saving water level data to the project."""
    datamanager.new_weather_win.setModal(False)

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
    """
    Test deleting water level datasets from the project.
    """
    datamanager.new_wldset_imported('wldset1', WLDataFrame(WLFILENAME))
    datamanager.new_wldset_imported('wldset2', WLDataFrame(WLFILENAME))
    assert datamanager.wldataset_count() == 2

    # Click to delete the current water level dataset, but cancel.
    mock_exec_ = mocker.patch.object(
        QMessageBox, 'exec_', return_value=QMessageBox.Cancel)
    qtbot.mouseClick(datamanager.btn_del_wldset, Qt.LeftButton)
    assert datamanager.wldataset_count() == 2
    assert datamanager._confirm_before_deleting_dset is True
    assert mock_exec_.call_count == 1

    # Click to delete the current water level dataset, check the
    # 'Don't show this message again' option and answer Yes.
    mock_exec_.return_value = QMessageBox.Yes
    mocker.patch.object(QCheckBox, 'isChecked', return_value=True)
    with qtbot.waitSignal(datamanager.sig_new_console_msg, raising=True):
        qtbot.mouseClick(datamanager.btn_del_wldset, Qt.LeftButton)
    assert datamanager.wldataset_count() == 1
    assert datamanager._confirm_before_deleting_dset is False
    assert mock_exec_.call_count == 2

    # Click to delete the current weather dataset.
    with qtbot.waitSignal(datamanager.sig_new_console_msg, raising=True):
        qtbot.mouseClick(datamanager.btn_del_wldset, Qt.LeftButton)
    assert datamanager.wldataset_count() == 0
    assert datamanager._confirm_before_deleting_dset is False
    assert mock_exec_.call_count == 2


def test_last_opened_datasets(qtbot, projectpath):
    """
    Test that the data manager recall correctly the water level and weather
    datasets that were last opened when opening a new project.

    Cover the new feature added in PR #267.
    """
    datamanager = DataManager(projet=ProjetReader(projectpath))
    qtbot.addWidget(datamanager)
    datamanager.show()

    # Add some water level dataset.
    for name in ['wldset1', 'wldset2', 'wldset3']:
        datamanager.new_wldset_imported(name, WLDataFrame(WLFILENAME))
    assert datamanager.get_current_wldset().name == 'wldset3'

    # Add some weather dataset.
    for name in ['wxdset1', 'wxdset2', 'wxdset3']:
        datamanager.new_wxdset_imported(name, WXDataFrame(WXFILENAME))
    assert datamanager.get_current_wxdset().name == 'wxdset3'

    # Change the current water level and weather datasets.
    datamanager.set_current_wldset('wldset2')
    assert datamanager.get_current_wldset().name == 'wldset2'
    datamanager.set_current_wxdset('wxdset2')
    assert datamanager.get_current_wxdset().name == 'wxdset2'

    # Close the datamanager and its project.
    datamanager.projet.close()
    datamanager.close()

    # Create a new datamanager and assert that the last opened water level
    # and weather datasets are remembered correctly.
    datamanager2 = DataManager(projet=ProjetReader(projectpath))
    qtbot.addWidget(datamanager2)
    datamanager2.show()

    assert datamanager2.get_current_wldset().name == 'wldset2'
    assert datamanager2.get_current_wxdset().name == 'wxdset2'


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
