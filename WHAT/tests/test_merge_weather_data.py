# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 01:50:50 2017
@author: jsgosselin
"""

# Standard library imports
import sys
import os
from datetime import datetime

# Third party imports
import numpy as np
from numpy import nan
import pytest
from PyQt5.QtCore import Qt

# Local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from meteo.dwnld_weather_data import ConcatenatedDataFrame
from meteo.merge_weather_data import WXDataMerger


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
file1['Climate Identifier'] = '7020560'
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
file1.save_to_csv(
        os.path.join(working_dir, file1.get_proposed_saved_filename()))

file2 = ConcatenatedDataFrame()
file2['Station Name'] = 'Station 2'
file2['Province'] = 'QUEBEC'
file2['Latitude'] = 47
file2['Longitude'] = -75
file2['Elevation'] = 174
file2['Climate Identifier'] = '7020560'
file2['Maximum Year'] = 1974
file2['Minimum Year'] = 1990
file2['Concatenated Dataset'] = np.array([
        [1974, 1, 2, 6.1, nan, 6.1, 6.1],
        [1974, 1, 3, 6.1, 6.1, nan, nan],
        [1974, 1, 4, 6.1, 6.1, 6.1, 6.1],
        [1974, 1, 5, 6.1, 6.1, 6.1, nan],
        [1990, 1, 3, 6.5, 6.5, 6.5, 6.5],
        [1990, 1, 4, 6.5, 6.5, 6.5, 6.5],
        [1990, 1, 5, 6.5, 6.5, 6.5, 6.5]])
file2.save_to_csv(
        os.path.join(working_dir, file2.get_proposed_saved_filename()))


@pytest.mark.run(order=3)
def test_merge_data():
    files = [os.path.join(working_dir, "Station 1 (7020560)_1960-1974.csv"),
             os.path.join(working_dir, "Station 2 (7020560)_1990-1974.csv")]

    wxdata_merger = WXDataMerger()
    wxdata_merger.load_and_format_data(files)


if __name__ == "__main__":                                   # pragma: no cover
    pytest.main([os.path.basename(__file__)])
    # pytest.main()
