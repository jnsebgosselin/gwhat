# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Standard library imports

import os
import os.path as osp

# ---- Third party imports

import numpy as np
import pytest

# ---- Local library imports

from gwhat.meteo.weather_reader import WXDataFrame, read_cweeds_file


def test_read_weather_data():
    fmeteo = osp.join(osp.dirname(__file__), "sample_weather_datafile.csv")
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


# ---- Test read_cweeds_file

def test_read_cweeds_wy2_file():
    filename = osp.join(osp.dirname(__file__), "cweed_sample.WY2")
    daily_wy2 = read_cweeds_file(filename, format_to_daily=True)
    for key in ['Years', 'Months', 'Days', 'Hours', 'Irradiance']:
        assert len(daily_wy2[key]) == 1096

    # Assert the Years, Months, and Days arrays :

    expected_result = np.array([1996, 1997, 1998])
    assert np.array_equal(np.unique(daily_wy2['Years']), expected_result)
    expected_result = np.arange(1, 13)
    assert np.array_equal(np.unique(daily_wy2['Months']), expected_result)
    expected_result = np.arange(1, 32)
    assert np.array_equal(np.unique(daily_wy2['Days']), expected_result)
    expected_result = np.arange(35065, 36161)
    assert np.array_equal(np.unique(daily_wy2['Time']), expected_result)

    # Assert the beginning of the Irradiance daily data series :

    expected_result = np.array([7.384, 5.460, 3.008, 7.244, 7.524])
    for i in range(len(expected_result)):
        assert np.round(daily_wy2['Irradiance'][i], 3) == expected_result[i]

    # Assert the end of the Irradiance daily data series :

    expected_result = np.array([5.511, 4.248, 3.773, 4.821, 7.074])
    for i in range(1, len(expected_result)+1):
        assert np.round(daily_wy2['Irradiance'][-i], 3) == expected_result[-i]


def test_read_cweeds_wy3_file():
    filename = osp.join(osp.dirname(__file__), "cweed_sample.WY3")
    daily_wy3 = read_cweeds_file(filename, format_to_daily=True)
    for key in ['Years', 'Months', 'Days', 'Hours', 'Time', 'Irradiance']:
        assert len(daily_wy3[key]) == 1096

    # Assert header values :

    assert daily_wy3['HORZ version'] == 'CWEEDS2011'
    assert daily_wy3['Location'] == 'MONTREAL INTL A'
    assert daily_wy3['Province'] == 'QC'
    assert daily_wy3['Country'] == 'CAN'
    assert daily_wy3['Station ID'] == '7025251'
    assert daily_wy3['Latitude'] == 45.47
    assert daily_wy3['Longitude'] == -73.74
    assert daily_wy3['Time Zone'] == -5.0
    assert daily_wy3['Elevation'] == 36.0

    # Assert the Years, Months, and Days arrays :

    expected_result = np.array([1998, 1999, 2000])
    assert np.array_equal(np.unique(daily_wy3['Years']), expected_result)
    expected_result = np.arange(1, 13)
    assert np.array_equal(np.unique(daily_wy3['Months']), expected_result)
    expected_result = np.arange(1, 32)
    assert np.array_equal(np.unique(daily_wy3['Days']), expected_result)
    expected_result = np.arange(35796, 36892)
    assert np.array_equal(np.unique(daily_wy3['Time']), expected_result)

    # Assert the beginning of the Irradiance daily data series :

    expected_result = np.array([4.425, 4.982, 4.798, 6.174, 3.059])
    for i in range(len(expected_result)):
        assert np.round(daily_wy3['Irradiance'][i], 3) == expected_result[i]

    # Assert the end of the Irradiance daily data series :

    expected_result = np.array([4.709, 5.337, 4.737, 3.746, 3.028])
    for i in range(1, len(expected_result)+1):
        assert np.round(daily_wy3['Irradiance'][-i], 3) == expected_result[-i]


if __name__ == "__main__":
    pytest.main([os.path.basename(__file__)])
    # pytest.main()
