# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

# ---- Standard library imports
import datetime as dt
import os.path as osp
from datetime import datetime

# ---- Third party imports
import numpy as np
import pandas as pd
import pytest

# ---- Local library imports
from gwhat.meteo.weather_reader import WXDataFrame, read_weather_datafile


@pytest.mark.parametrize(
    "filename",
    ['basic_weather_datafile.xlsx',
     'basic_weather_datafile.xls',
     'basic_weather_datafile.csv'])
def test_read_weather_datafile(filename):
    """
    Test that the basic function to read weather data input file is
    working as expected.
    """
    filename = osp.join(osp.dirname(__file__), filename)
    metadata, data = read_weather_datafile(filename)

    # Assert metadata.
    assert metadata['filename'] == filename
    assert metadata['Station Name'] == 'MARIEVILLE'
    assert metadata['Station ID'] == '7024627'
    assert metadata['Location'] == 'QUEBEC'
    assert metadata['Latitude'] == 45.4
    assert metadata['Longitude'] == -73.13
    assert metadata['Elevation'] == 38

    # Assert dataset columns.
    expected_columns = ['Tmax', 'Tmin', 'Tavg', 'Ptot']
    assert data.columns.values.tolist() == expected_columns

    # Assert dataset times.
    expected_datetimes = [
        '2000-01-01 00:00', '2000-01-02 00:00', '2000-01-03 00:00',
        '2000-01-04 00:00', '2000-01-05 00:00']
    assert (data.index.strftime("%Y-%m-%d %H:%M").values.tolist() ==
            expected_datetimes)

    # We need to compare the values as strings because comparing two nan
    # values always yield False.
    expected_values = np.array(
        [['2.0', '-12.8', '-4.9', '0.0'],
         ['nan', '-6.0', '1.5', '6.8'],
         ['nan', '-3.5', '-0.5', '6.0'],
         ['nan', 'nan', 'nan', 'nan'],
         ['nan', 'nan', 'nan', 'nan']
         ])
    assert np.array_equal(expected_values, data.astype(str).values)


def test_init_wxdataframe_from_input_file():
    """
    Test that the WXDataFrame can be initiated properly from an input
    weather datafile.
    """
    fmeteo = osp.join(osp.dirname(__file__), "sample_weather_datafile.xlsx")
    wxdset = WXDataFrame(fmeteo)

    assert len(wxdset) == 366 + 365 + 365

    # Assert time was read correctly.
    assert np.all(np.diff(wxdset.data.index) == np.timedelta64(1, 'D'))
    assert wxdset.get_data_period() == (2000, 2002)
    assert np.array_equal(
        wxdset.get_xldates(),
        np.arange(36526, 36526 + 366 + 365 + 365))
    assert np.array_equal(
        wxdset.data.index,
        pd.date_range(start=dt.datetime(2000, 1, 1),
                      end=dt.datetime(2002, 12, 31),
                      freq='D'))

    # Assert the data for a sample of the dataset.

    # Note that the data for the 04/01/2000 are missing from the dataset
    # completely and the first data for the average temperature is missing.
    assert np.array_equal(
        wxdset.data['Tmax'][:5],
        np.array([2, 9, 2.5, 0.5 * (2.5 + -8), -8]))
    assert np.array_equal(
        wxdset.data['Tmin'][:5],
        np.array([-12.8, -6, -3.5, 0.5 * (-3.5 + -10.5), -10.5]))
    assert np.array_equal(
        wxdset.data['Tavg'][:5],
        np.array([0, 1.5, -0.5, 0.5 * (-0.5 + -9.3), -9.3]))
    assert np.array_equal(
        wxdset.data['Ptot'][:5], np.array([0, 6.8, 6, 0, 0]))


def test_wxdata_monthly_yearly_values():
    """
    Test that monthly and yearly values are calculated as expected from the
    daily values.
    """
    wxdset = WXDataFrame(
        osp.join(osp.dirname(__file__), "sample_weather_datafile.xlsx"))

    # Assert monthly values.
    monthly = wxdset.get_monthly_values()

    assert round(monthly.loc[(2001, 1), 'Ptot'], 1) == 82.6
    assert round(monthly.loc[(2001, 1), 'Rain'], 1) == 30.6
    assert round(monthly.loc[(2001, 1), 'Snow'], 1) == 52.0
    assert round(monthly.loc[(2001, 1), 'PET'], 1) == 1.0
    assert round(monthly.loc[(2001, 1), 'Tmax'], 1) == -5.3
    assert round(monthly.loc[(2001, 1), 'Tavg'], 1) == -9.7
    assert round(monthly.loc[(2001, 1), 'Tmin'], 1) == -14.1

    assert round(monthly.loc[(2001, 6), 'Ptot'], 1) == 103.1
    assert round(monthly.loc[(2001, 6), 'Rain'], 1) == 103.1
    assert round(monthly.loc[(2001, 6), 'Snow'], 1) == 0.0
    assert round(monthly.loc[(2001, 6), 'PET'], 1) == 111.1
    assert round(monthly.loc[(2001, 6), 'Tmax'], 1) == 22.1
    assert round(monthly.loc[(2001, 6), 'Tavg'], 1) == 17.1
    assert round(monthly.loc[(2001, 6), 'Tmin'], 1) == 12.2

    # Assert yearly values.
    yearly = wxdset.get_yearly_values()

    assert round(yearly.loc[2001, 'Ptot'], 1) == 1145.5
    assert round(yearly.loc[2001, 'Rain'], 1) == 865.6
    assert round(yearly.loc[2001, 'Snow'], 1) == 279.9
    assert round(yearly.loc[2001, 'PET'], 1) == 613.4
    assert round(yearly.loc[2001, 'Tmax'], 1) == 10.9
    assert round(yearly.loc[2001, 'Tavg'], 1) == 6.3
    assert round(yearly.loc[2001, 'Tmin'], 1) == 1.7


if __name__ == "__main__":
    pytest.main(['-x', __file__, '-v', '-rw'])
