# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.
# -----------------------------------------------------------------------------

# ---- Standard library imports
from datetime import datetime
import os
import os.path as osp

# ---- Third party imports
import pytest
import numpy as np
import pandas as pd

# ---- Local library imports
from gwhat import __rootdir__
from gwhat.common.utils import save_content_to_excel, save_content_to_csv
from gwhat.projet.reader_waterlvl import (
    load_waterlvl_measures, WLDataset)

WLMEAS = [['Well_ID', 'Time (days)', 'Obs. (mbgs)'],
          ['Test', 40623.54167, 1.43],
          ['Test', 40842.54167, 1.6],
          ['Test', 41065.54167, 1.57],
          ['test', 41065.54167, 1.57],
          ["é@#^'", 41240.8125, 3.75],
          ['test2', 41402.34375, 3.56],
          ]

DATADIR = osp.join(__rootdir__, 'projet', 'tests', 'data')


# =============================================================================
# ---- Fixtures
# =============================================================================
@pytest.fixture
def datatmpdir(tmp_path):
    """Create a set of water level datafile in various format."""
    save_content_to_csv(
        osp.join(tmp_path, 'waterlvl_manual_measurements.csv'), WLMEAS)
    save_content_to_excel(
        osp.join(tmp_path, 'waterlvl_manual_measurements.xls'), WLMEAS)
    save_content_to_excel(
        osp.join(tmp_path, 'waterlvl_manual_measurements.xlsx'), WLMEAS)

    return tmp_path


# =============================================================================
# ---- Tests
# =============================================================================
@pytest.mark.parametrize("ext", ['.csv', '.xls', '.xlsx', '_xldates.csv',
                                 '_strfmt.xls', '_strfmt.xlsx'])
def test_read_waterlvl(ext):
    """
    Test that reading water level input data files is working as expected.
    """
    filename = osp.join(DATADIR, 'water_level_datafile' + ext)
    dataset = WLDataset(filename)

    expected_results = {
        'Well': "êi!@':i*",
        'Well ID': '1234ABC',
        'Province': 'Qc',
        'Latitude': 45.36,
        'Longitude': -72.4234665345,
        'Elevation': 123,
        'Municipality': ''}
    keys = ['Well', 'Well ID', 'Province', 'Latitude', 'Longitude',
            'Elevation', 'Municipality']
    for key in keys:
        assert dataset[key] == expected_results[key]

    # Check barometric pressure.
    expected_results = np.array([10.33327435, 10.33127437, 10.33097437])
    assert np.min(np.abs(dataset['BP'] - expected_results)) < 10e-6

    # Ckeck water levels.
    expected_results = np.array([3.667377006, 3.665777025, 3.665277031])
    assert np.min(np.abs(dataset['WL'] - expected_results)) < 10e-6

    # Check earth tides.
    expected_results = np.array([383.9680352, 387.7404819, 396.9950643])
    assert np.min(np.abs(dataset['ET'] - expected_results)) < 10e-6

    # Check Excel numeric dates.
    expected_results = np.array([41241.69792, 41241.70833, 41241.71875])
    assert np.min(np.abs(dataset.xldates - expected_results)) < 10e-6

    # Checks datetimes.
    expected_results = pd.to_datetime([
        datetime(2012, 11, 28, 16, 45, 0),
        datetime(2012, 11, 28, 17, 0, 0),
        datetime(2012, 11, 28, 17, 15, 0)])
    assert (dataset.dates == expected_results.values).all()

    # Check times.
    expected_results = [
        '2012-11-28T16:45:00', '2012-11-28T17:00:00', '2012-11-28T17:15:00']
    assert list(dataset['Time']) == expected_results


def test_set_waterlvl_dataset():
    """
    Test that modifying water level datasets is working as expected.
    """
    filename = osp.join(DATADIR, 'water_level_datafile.csv')
    dataset = WLDataset(filename)

    expected_results = {
        'Well': "test_well_name",
        'Well ID': "test_well_id",
        'Province': 'test_prov',
        'Latitude': 45.678,
        'Longitude': -76.543,
        'Elevation': 123.23,
        'Municipality': 'test_municipality'}

    for key, value in expected_results.items():
        dataset[key] = value
        assert dataset[key] == expected_results[key]


@pytest.mark.parametrize("ext", ['.csv', '.xls', '.xlsx'])
def test_load_waterlvl_measurements(datatmpdir, ext):
    filename = osp.join(datatmpdir, "waterlvl_manual_measurements" + ext)

    # Assert that it loads the right data.
    time, wl = load_waterlvl_measures(filename, 'Dummy')
    assert len(time) == 0 and isinstance(time, np.ndarray)
    assert len(wl) == 0 and isinstance(wl, np.ndarray)

    time, wl = load_waterlvl_measures(filename, 'Test')
    assert np.all(time == np.array([40623.54167, 40842.54167, 41065.54167]))
    assert np.all(wl == np.array([1.43, 1.6, 1.57]))

    time, wl = load_waterlvl_measures(filename, "é@#^'")
    assert np.all(time == np.array([41240.8125]))
    assert np.all(wl == np.array([3.75]))


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
