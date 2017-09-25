# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 01:50:50 2017
@author: jsgosselin
"""

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
from meteo.dwnld_weather_data import ConcatenatedDataFrame
from meteo.merge_weather_data import WXDataMerger
from meteo.weather_reader import read_weather_datafile


# Qt Test Fixtures
# --------------------------------


#@pytest.fixture
#def downloader_bot(qtbot):
#    wxdata_downloader = RawDataDownloader()
#    wxdata_merger = WXDataMerger()
#
#    return wxdata_downloader, wxdata_merger, qtbot


# Test RawDataDownloader
# -------------------------------

working_dir = os.path.join(os.getcwd(), "@ new-prô'jèt!", "Meteo", "Input")

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


@pytest.mark.run(order=4)
def test_merge_data():
    # Generate synthetic input weather data files.
    files = [os.path.join(working_dir, "Station 1 (7020561)_1960-1974.csv"),
             os.path.join(working_dir, "Station 2 (7020562)_1974-1990.csv")]
    file1.save_to_csv(files[0])
    file2.save_to_csv(files[1])

    # Combine the two input weather data files and assert the resulting
    # combined dataset is as expected.
    wxdata_merger = WXDataMerger(files)

    np.testing.assert_equal(wxdata_merger['Combined Dataset'], expected_result)

    # Assert that the proposed filename is as expected.
    file12_expected_name = "Station 1 (7020561)_1960-1990.csv"
    assert wxdata_merger.get_proposed_saved_filename() == file12_expected_name

    # Save the resulting combined dataset to file.
    file12_path = os.path.join(working_dir, file12_expected_name)
    wxdata_merger.setDeleteInputFiles(True)
    wxdata_merger.save_to_csv(file12_path)

    # Assert that the original input weather datafile were deleted.
    for file in files:
        assert not os.path.exists(file)

    # Assert that the content of the combined dataset file is as expected.
    df12 = read_weather_datafile(file12_path)
    keys = ['Time', 'Year', 'Month', 'Day', 'Tmax', 'Tmin', 'Tavg', 'Ptot']
    for key in keys:
        np.testing.assert_equal(wxdata_merger[key], df12[key])


if __name__ == "__main__":                                   # pragma: no cover
    pytest.main([os.path.basename(__file__)])
    # pytest.main()
