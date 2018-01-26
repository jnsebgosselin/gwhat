# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# Standard library imports
import os

# Third party imports
import numpy as np
import pytest

# Local imports
from gwhat.meteo.weather_reader import WXDataFrame


def test_read_weather_data():
    fmeteo = "sample_weather_datafile.csv"
    wxdset = WXDataFrame(fmeteo)

    # Assert that the dataset was loaded correctly and that the 3 lines that
    # were removed manually from the dataset were added back. The lines were
    # removed for december 18, 19, and 20 of 2017.

    assert len(wxdset['Time']) == 2188 + 3
    assert np.all(np.diff(wxdset['Time']) == 1)

    expected_times = np.arange(40179, 42369+1)
    assert np.array_equal(wxdset['Time'], expected_times)

    expected_years = np.arange(2010, 2015+1)
    assert np.array_equal(np.unique(wxdset['Year']), expected_years)

    expected_months = np.arange(1, 13)
    assert np.array_equal(np.unique(wxdset['Month']), expected_months)

    # Assert the data for a sample of the dataset.

    expected_results = np.array([14, 0, 0, 0, 8.5])
    assert np.array_equal(wxdset['Ptot'][-15:-10], expected_results)
    expected_results = np.array([14, 0, 0, 0, 0])
    assert np.array_equal(wxdset['Rain'][-15:-10], expected_results)
    expected_results = np.array([0, 0, 0, 0, 8.5])
    assert np.array_equal(wxdset['Snow'][-15:-10], expected_results)

    expected_results = np.array([4.300, 3.100, 1.900, 0.700, -0.500])
    assert np.array_equal(np.round(wxdset['Tavg'][-15:-10], 3),
                          expected_results)
    expected_results = np.array([9.000, 7.750, 6.500, 5.250, 4.000])
    assert np.array_equal(np.round(wxdset['Tmax'][-15:-10], 3),
                          expected_results)
    expected_results = np.array([-0.500, -1.125, -1.750, -2.375, -3.00])
    assert np.array_equal(np.round(wxdset['Tmin'][-15:-10], 3),
                          expected_results)


if __name__ == "__main__":
    pytest.main([os.path.basename(__file__)])
    # pytest.main()
