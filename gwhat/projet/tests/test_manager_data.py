# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------


# ---- Standard Libraries Imports
import os
import os.path as osp

# ---- Third Party Libraries Imports
import pytest
from PyQt5.QtCore import Qt


# ---- Local Libraries Imports
from gwhat.meteo.weather_reader import WXDataFrame
from gwhat.projet.reader_waterlvl import WLDataset
from gwhat.projet.reader_projet import ProjetReader
from gwhat.projet.manager_data import (DataManager, QFileDialog, QMessageBox,
                                       QCheckBox)

DATADIR = osp.join(osp.dirname(osp.realpath(__file__)), 'data')
WXFILENAME = osp.join(DATADIR, 'sample_weather_datafile.csv')
WLFILENAME = osp.join(DATADIR, 'sample_water_level_datafile.csv')
WLFILENAME2 = osp.join(DATADIR, 'sample_water_level_datafile2.csv')
WLFILENAME3 = osp.join(DATADIR, 'sample_water_level_datafile3.csv')


# ---- Pytest Fixtures
@pytest.fixture
def projectpath(tmpdir):
    return osp.join(str(tmpdir), "data_manager_test.gwt")


@pytest.fixture
def project(projectpath):
    return ProjetReader(projectpath)


@pytest.fixture
def datamanager(project, qtbot):
    datamanager = DataManager(projet=project, pytesting=True)
    qtbot.addWidget(datamanager)
    qtbot.addWidget(datamanager.new_waterlvl_win)
    qtbot.addWidget(datamanager.new_weather_win)
    datamanager.show()

    return datamanager


# ---- Tests Weather Dataset
def test_import_weather_data(datamanager, mocker, qtbot):
    """
    Test that importing data in gwhat projects is working as
    expected.
    """
    datamanager.new_weather_win.setModal(False)
    new_weather_dialog = datamanager.new_weather_win

    # Mock the file dialog to return the path of the weather datafile.
    mocker.patch.object(
        QFileDialog, 'exec_', return_value=True)
    mocker.patch.object(
        QFileDialog, 'selectedFiles', return_value=[WXFILENAME])

    # Open the dialog window and select a weather dataset.
    with qtbot.waitSignal(new_weather_dialog.sig_new_dataset_loaded):
        qtbot.mouseClick(datamanager.btn_load_meteo, Qt.LeftButton)

    assert new_weather_dialog.name == "IBERVILLE (7023270)"
    assert new_weather_dialog.station_name == "IBERVILLE"
    assert new_weather_dialog.station_id == "7023270"
    assert new_weather_dialog.province == "QUEBEC"
    assert new_weather_dialog.latitude == 45.33
    assert new_weather_dialog.longitude == -73.25
    assert new_weather_dialog.altitude == 30.5

    # Import the weather dataset into the project.
    with qtbot.waitSignal(new_weather_dialog.sig_new_dataset_imported):
        qtbot.mouseClick(new_weather_dialog.btn_ok, Qt.LeftButton)
    assert datamanager.wxdataset_count() == 1
    assert datamanager.wxdsets_cbox.currentText() == "IBERVILLE (7023270)"
    assert datamanager.get_current_wxdset().name == "IBERVILLE (7023270)"


def test_delete_weather_data(datamanager, mocker, qtbot):
    """
    Test that deleting weather datasets from gwhat projects is working
    as expected.
    """
    datamanager.add_new_wxdset('wxdset1', WXDataFrame(WXFILENAME))
    datamanager.add_new_wxdset('wxdset2', WXDataFrame(WXFILENAME))
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


# ---- Tests Weather Dataset
def test_import_waterlevel_data(datamanager, mocker, qtbot):
    """
    Test that importing a water level dataset in a gwhat project is
    working as expected.

    Regression test for jnsebgosselin/gwhat#416
    """
    datamanager.new_waterlvl_win.setModal(False)
    new_waterlvl_dialog = datamanager.new_waterlvl_win

    # Mock the file dialog to return the path of the weather datafiles.
    mocker.patch.object(
        QFileDialog, 'exec_', return_value=True)
    mocker.patch.object(
        QFileDialog, 'selectedFiles',
        return_value=[WLFILENAME, WLFILENAME2, WLFILENAME3])

    with qtbot.waitSignal(new_waterlvl_dialog.sig_new_dataset_loaded):
        qtbot.mouseClick(datamanager.btn_load_wl, Qt.LeftButton)

    assert new_waterlvl_dialog.directory.text() == WLFILENAME
    assert new_waterlvl_dialog.name == "PO01 - Calixa-Lavallée (3040002)"
    assert new_waterlvl_dialog.station_name == "PO01 - Calixa-Lavallée"
    assert new_waterlvl_dialog.station_id == "3040002"
    assert new_waterlvl_dialog.province == "QC"
    assert new_waterlvl_dialog.latitude == 45.74581
    assert new_waterlvl_dialog.longitude == -73.28024
    assert new_waterlvl_dialog.altitude == 19.51

    # Change dataset info in the UI.
    new_waterlvl_dialog._dset_name.setText("test_dataset_name")
    new_waterlvl_dialog._stn_name.setText("test_well_name")
    new_waterlvl_dialog._sid.setText("test_well_id")
    new_waterlvl_dialog._lat.setValue(45.678)
    new_waterlvl_dialog._lon.setValue(-76.543)
    new_waterlvl_dialog._alt.setValue(123.23)
    new_waterlvl_dialog._prov.setText("test_prov")

    assert new_waterlvl_dialog.name == "test_dataset_name"
    assert new_waterlvl_dialog.station_name == "test_well_name"
    assert new_waterlvl_dialog.station_id == "test_well_id"
    assert new_waterlvl_dialog.province == "test_prov"
    assert new_waterlvl_dialog.latitude == 45.678
    assert new_waterlvl_dialog.longitude == -76.543
    assert new_waterlvl_dialog.altitude == 123.23

    # Import the water level dataset into the project.
    with qtbot.waitSignal(new_waterlvl_dialog.sig_new_dataset_imported):
        qtbot.mouseClick(new_waterlvl_dialog.btn_ok, Qt.LeftButton)

    wldset = datamanager.get_current_wldset()
    assert wldset.name == "test_dataset_name"
    assert wldset['Well'] == "test_well_name"
    assert wldset['Well ID'] == "test_well_id"
    assert wldset['Province'] == "test_prov"
    assert wldset['Latitude'] == 45.678
    assert wldset['Longitude'] == -76.543
    assert wldset['Elevation'] == 123.23


def test_import_multiple_waterlevel_data(datamanager, mocker, qtbot):
    """
    Test that importing multiple water level datasets in a gwhat project is
    working as expected.
    """
    datamanager.new_waterlvl_win.setModal(False)
    new_waterlvl_dialog = datamanager.new_waterlvl_win

    # Mock the file dialog to return the path of the weather datafiles.
    mocker.patch.object(
        QFileDialog, 'exec_', return_value=True)
    mocker.patch.object(
        QFileDialog, 'selectedFiles',
        return_value=[WLFILENAME, WLFILENAME2, WLFILENAME3])

    with qtbot.waitSignal(new_waterlvl_dialog.sig_new_dataset_loaded):
        qtbot.mouseClick(datamanager.btn_load_wl, Qt.LeftButton)

    assert new_waterlvl_dialog.directory.text() == WLFILENAME
    assert new_waterlvl_dialog.name == "PO01 - Calixa-Lavallée (3040002)"
    assert new_waterlvl_dialog.station_name == "PO01 - Calixa-Lavallée"
    assert new_waterlvl_dialog.station_id == "3040002"
    assert new_waterlvl_dialog.province == "QC"
    assert new_waterlvl_dialog.latitude == 45.74581
    assert new_waterlvl_dialog.longitude == -73.28024
    assert new_waterlvl_dialog.altitude == 19.51

    assert new_waterlvl_dialog.isVisible()
    assert new_waterlvl_dialog.btn_skip.isEnabled()
    assert new_waterlvl_dialog._queued_filenames == [WLFILENAME2, WLFILENAME3]
    assert new_waterlvl_dialog._import_progress == 1
    assert new_waterlvl_dialog._len_filenames == 3

    # Import the water level dataset into the project.
    with qtbot.waitSignal(new_waterlvl_dialog.sig_new_dataset_imported):
        qtbot.mouseClick(new_waterlvl_dialog.btn_ok, Qt.LeftButton)

    assert datamanager.wldataset_count() == 1
    assert (datamanager.wldsets_cbox.currentText() ==
            "PO01 - Calixa-Lavallée (3040002)")
    assert (datamanager.get_current_wldset().name ==
            "PO01 - Calixa-Lavallée (3040002)")

    # Assert that the dataset from the second input data file was loaded
    # as expected.
    assert new_waterlvl_dialog.directory.text() == WLFILENAME2
    assert new_waterlvl_dialog.name == "test_well_02 (3040002)"
    assert new_waterlvl_dialog.station_name == "test_well_02"
    assert new_waterlvl_dialog.station_id == "3040002"
    assert new_waterlvl_dialog.province == "QC"
    assert new_waterlvl_dialog.latitude == 42.02
    assert new_waterlvl_dialog.longitude == -72.02
    assert new_waterlvl_dialog.altitude == 22.02

    assert new_waterlvl_dialog.isVisible()
    assert new_waterlvl_dialog.btn_skip.isEnabled()
    assert new_waterlvl_dialog._queued_filenames == [WLFILENAME3]
    assert new_waterlvl_dialog._import_progress == 2

    # Skip the import of this dataset.
    with qtbot.waitSignal(new_waterlvl_dialog.sig_new_dataset_loaded):
        qtbot.mouseClick(new_waterlvl_dialog.btn_skip, Qt.LeftButton)

    assert datamanager.wldataset_count() == 1
    assert (datamanager.wldsets_cbox.currentText() ==
            "PO01 - Calixa-Lavallée (3040002)")
    assert (datamanager.get_current_wldset().name ==
            "PO01 - Calixa-Lavallée (3040002)")

    # Assert that the dataset from the second input data file was loaded
    # as expected.
    assert new_waterlvl_dialog.directory.text() == WLFILENAME3
    assert new_waterlvl_dialog.name == "test_well_03 (3040003)"
    assert new_waterlvl_dialog.station_name == "test_well_03"
    assert new_waterlvl_dialog.station_id == "3040003"
    assert new_waterlvl_dialog.province == "QC"
    assert new_waterlvl_dialog.latitude == 43.03
    assert new_waterlvl_dialog.longitude == -73.03
    assert new_waterlvl_dialog.altitude == 33.03

    assert new_waterlvl_dialog.isVisible()
    assert not new_waterlvl_dialog.btn_skip.isEnabled()
    assert new_waterlvl_dialog._queued_filenames == []
    assert new_waterlvl_dialog._import_progress == 3

    # Import the water level dataset into the project.
    with qtbot.waitSignal(new_waterlvl_dialog.sig_new_dataset_imported):
        qtbot.mouseClick(new_waterlvl_dialog.btn_ok, Qt.LeftButton)

    assert datamanager.wldataset_count() == 2
    assert datamanager.wldsets_cbox.currentText() == "test_well_03 (3040003)"
    assert datamanager.get_current_wldset().name == "test_well_03 (3040003)"

    assert not new_waterlvl_dialog.isVisible()


def test_delete_waterlevel_data(datamanager, mocker, qtbot):
    """
    Test deleting water level datasets from the project.
    """
    datamanager.add_new_wldset('wldset1', WLDataset(WLFILENAME))
    datamanager.add_new_wldset('wldset2', WLDataset(WLFILENAME))
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
        datamanager.add_new_wldset(name, WLDataset(WLFILENAME))
    assert datamanager.get_current_wldset().name == 'wldset3'

    # Add some weather dataset.
    for name in ['wxdset1', 'wxdset2', 'wxdset3']:
        datamanager.add_new_wxdset(name, WXDataFrame(WXFILENAME))
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
    datamanager.add_new_wxdset(wxdset.metadata['Station Name'], wxdset)

    for ftype in ['xlsx', 'csv', 'xls']:
        for time_frame in ['daily', 'monthly', 'yearly']:
            filename = osp.join(
                tmp_path, "export_{}_weather.{}".format(time_frame, ftype))
            mocker.patch.object(
                QFileDialog,
                'getSaveFileName',
                return_value=(filename, '*.' + ftype))
            datamanager.btn_export_weather.select_export_file(time_frame)
            assert osp.exists(filename)


if __name__ == "__main__":
    pytest.main(['-x', __file__, '-v', '-rw', '-s'])
