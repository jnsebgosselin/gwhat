# -*- coding: utf-8 -*-

# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# Standard library imports
import os
import os.path as osp

# Third party imports
import numpy as np
from numpy import nan
import pytest
from PyQt5.QtCore import Qt

# Local imports
from gwhat.meteo.dwnld_weather_data import ConcatenatedDataFrame
from gwhat.meteo.weather_reader import read_weather_datafile
from gwhat.meteo.merge_weather_data import (WXDataMerger, WXDataMergerWidget,
                                            QFileDialog)


# ---- Tests data
file1 = ConcatenatedDataFrame()
file1['Station Name'] = 'Station 1'
file1['Province'] = 'QUEBEC'
file1['Latitude'] = 45
file1['Longitude'] = -77
file1['Elevation'] = 160
file1['Climate Identifier'] = '7020561'
file1['Minimum Year'] = 1960
file1['Maximum Year'] = 1974
file1['Concatenated Dataset'] = np.array([
        [1960, 1, 1, nan, 2.4, 2.4, nan],
        [1960, 1, 2, 2.4, 2.4, nan, 2.4],
        [1960, 1, 3, nan, nan, nan, nan],
        [1960, 1, 4, 2.4, 2.4, 2.4, 2.4],
        [1974, 1, 1, 4.1, 4.1, 4.1, 4.1],
        [1974, 1, 2, nan, 4.1, nan, 4.1],
        [1974, 1, 3, 4.1, 4.1, 4.1, 4.1]])


file2 = ConcatenatedDataFrame()
file2['Station Name'] = 'Station 2'
file2['Province'] = 'QUEBEC'
file2['Latitude'] = 47
file2['Longitude'] = -75
file2['Elevation'] = 174
file2['Climate Identifier'] = '7020562'
file2['Maximum Year'] = 1974
file2['Minimum Year'] = 1990
file2['Concatenated Dataset'] = np.array([
        [1974, 1, 2, 6.1, nan, 6.1, 6.1],
        [1974, 1, 3, 6.1, 6.1, nan, nan],
        [1974, 1, 4, 6.1, 6.1, 6.1, 6.1],
        [1974, 1, 5, 6.1, 6.1, 6.1, nan],
        [1990, 1, 3, 6.5, 6.5, 6.5, 6.5],
        [1990, 1, 4, 6.5, 6.5, 6.5, 6.5],
        [1990, 1, 5, 6.5, 6.5, 6.5, 6.5]
        ])

expected_result = np.array([
        [1960, 1, 1, nan, 2.4, 2.4, nan],
        [1960, 1, 2, 2.4, 2.4, nan, 2.4],
        [1960, 1, 3, nan, nan, nan, nan],
        [1960, 1, 4, 2.4, 2.4, 2.4, 2.4],
        [1974, 1, 1, 4.1, 4.1, 4.1, 4.1],
        [1974, 1, 2, 6.1, 4.1, 6.1, 4.1],
        [1974, 1, 3, 4.1, 4.1, 4.1, 4.1],
        [1974, 1, 4, 6.1, 6.1, 6.1, 6.1],
        [1974, 1, 5, 6.1, 6.1, 6.1, nan],
        [1990, 1, 3, 6.5, 6.5, 6.5, 6.5],
        [1990, 1, 4, 6.5, 6.5, 6.5, 6.5],
        [1990, 1, 5, 6.5, 6.5, 6.5, 6.5]
        ])


# ---- Pytest Fixtures
@pytest.fixture(scope="module")
def workdir(tmp_path_factory):
    # Create a project and add add the wldset to it.
    basetemp = tmp_path_factory.getbasetemp()
    return osp.join(basetemp, "@ new-prô'jèt!")


@pytest.fixture(scope="module")
def datafiles(workdir):
    """
    Fixture that generates synthetic input weather data files and returns a
    list of paths to these files.
    """
    files = [osp.join(workdir, "Station 1 (7020561)_1960-1974.csv"),
             osp.join(workdir, "Station 2 (7020562)_1974-1990.csv")]
    file1.save_to_csv(files[0])
    file2.save_to_csv(files[1])

    return files


@pytest.fixture
def wxdata_merger(qtbot):
    wxdata_merger = WXDataMergerWidget()
    qtbot.addWidget(wxdata_merger)
    return wxdata_merger


# ---- Tests
def test_merge_data(workdir, datafiles):
    """
    Combine the two input weather data files and assert the resulting
    combined dataset is as expected.
    """
    wxdata_merger = WXDataMerger(datafiles)

    np.testing.assert_equal(wxdata_merger['Combined Dataset'], expected_result)

    # Assert that the proposed filename is as expected.
    file12_expected_name = "Station 1 (7020561)_1960-1990.csv"
    assert wxdata_merger.get_proposed_saved_filename() == file12_expected_name

    # Save the resulting combined dataset to file.
    file12_path = os.path.join(workdir, file12_expected_name)
    wxdata_merger.setDeleteInputFiles(False)
    wxdata_merger.save_to_csv(file12_path)

    # Assert that the original input weather datafile were not deleted.
    for file in datafiles:
        assert osp.exists(file)

    # Assert that the content of the combined dataset file is as expected.
    df12 = read_weather_datafile(file12_path)
    keys = ['Time', 'Year', 'Month', 'Day', 'Tmax', 'Tmin', 'Tavg', 'Ptot']
    for key in keys:
        np.testing.assert_equal(wxdata_merger[key], df12[key])


def test_merge_data_widget(wxdata_merger, workdir, datafiles, qtbot, mocker):
    """
    Test the GUI to merge datasets.
    """
    wxdata_merger.show()
    wxdata_merger.set_workdir(workdir)
    fname1, fname2 = datafiles

    # Select and load the first input file.
    mocker.patch.object(QFileDialog, 'getOpenFileName',
                        return_value=(fname1, '*.csv'))

    qtbot.mouseClick(wxdata_merger.btn_get_file1, Qt.LeftButton)

    # Select and load the second input file.
    mocker.patch.object(QFileDialog, 'getOpenFileName',
                        return_value=(fname2, '*.csv'))

    qtbot.mouseClick(wxdata_merger.btn_get_file2, Qt.LeftButton)

    # Check the "Delete both original input datafiles after merging" option.
    wxdata_merger._del_input_files_ckbox.setChecked(True)

    # Save the combined dataset to file.
    fname12 = os.path.join(workdir, "Station 12 (7020562)_1960-1990.csv")
    mocker.patch.object(QFileDialog, 'getSaveFileName',
                        return_value=(fname12, '*.csv'))

    qtbot.mouseClick(wxdata_merger.btn_saveas, Qt.LeftButton)

    # Assert that the original input weather datafile were deleted and that
    # the file for the combined dataset was created.
    assert not os.path.exists(fname1)
    assert not os.path.exists(fname2)
    assert os.path.exists(fname12)

    # Recreate file2, set file1 for file12 and save combined results.
    file2.save_to_csv(fname2)
    wxdata_merger.set_first_filepath(fname12)
    qtbot.mouseClick(wxdata_merger.btn_saveas, Qt.LeftButton)

    # Assert that file2 has been deleted, but not file12. This is to test that
    # if the output file has the same name as one of the input file, it is
    # not aftward deleted in the process.
    assert not os.path.exists(fname2)
    assert os.path.exists(fname12)


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
