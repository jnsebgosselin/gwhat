# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Standard library imports
import os
import os.path as osp
import csv

# ---- Third party imports
import pytest
import numpy as np

# ---- Local library imports
from gwhat.common.utils import save_content_to_excel, save_content_to_csv
from gwhat.projet.reader_waterlvl import (
    load_waterlvl_measures, init_waterlvl_measures, WLDataset)

DATA = [['Well name = ', "êi!@':i*"],
        ['well id : ', '1234ABC'],
        ['Province', 'Qc'],
        ['latitude   ', 45.36],
        ['Longitude=', -72.4234665345],
        ['Elevation:', 123],
        [],
        [],
        ['Date', 'WL(mbgs)', 'BP(m)', 'ET'],
        [41241.69792, 3.667377006, 10.33327435, 383.9680352],
        [41241.70833, 3.665777025, 10.33127437, 387.7404819],
        [41241.71875, 3.665277031, 10.33097437, 396.9950643]
        ]

WLMEAS = [['Well_ID', 'Time (days)', 'Obs. (mbgs)'],
          ['Test', 40623.54167, 1.43],
          ['Test', 40842.54167, 1.6],
          ['Test', 41065.54167, 1.57],
          ['test', 41065.54167, 1.57],
          ["é@#^'", 41240.8125, 3.75],
          ['test2', 41402.34375, 3.56],
          ]


# =============================================================================
# ---- Fixtures
# =============================================================================
@pytest.fixture
def datatmpdir(tmp_path):
    """Create a set of water level datafile in various format."""
    save_content_to_csv(
        osp.join(tmp_path, 'water_level_datafile.csv'), DATA)
    save_content_to_excel(
        osp.join(tmp_path, 'water_level_datafile.xls'), DATA)
    save_content_to_excel(
        osp.join(tmp_path, 'water_level_datafile.xlsx'), DATA)

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
@pytest.mark.parametrize("ext", ['.csv', '.xls', '.xlsx'])
def test_reading_waterlvl(datatmpdir, ext):
    df = WLDataset(osp.join(datatmpdir, 'water_level_datafile' + ext))

    expected_results = {
        'Well': "êi!@':i*",
        'Well ID': '1234ABC',
        'Province': 'Qc',
        'Latitude': 45.36,
        'Longitude': -72.4234665345,
        'Elevation': 123,
        'Municipality': '',
        'Time': np.array([41241.69792, 41241.70833, 41241.71875]),
        'WL': np.array([3.667377006, 3.665777025, 3.665277031]),
        'BP': np.array([10.33327435, 10.33127437, 10.33097437]),
        'ET': np.array([383.9680352, 387.7404819, 396.9950643])}

    keys = ['Well', 'Well ID', 'Province', 'Latitude', 'Longitude',
            'Elevation', 'Municipality']
    for key in keys:
        assert df[key] == expected_results[key]

    for key in ['WL', 'BP', 'ET']:
        assert np.abs(np.min(df[key] - expected_results[key])) < 10e-6
    assert np.abs(np.min(df.xldates - expected_results['Time'])) < 10e-6


def test_init_waterlvl_measures(tmp_path):
    """
    Assert that the water_level_measurement file is initialized correctly.
    """
    filename = os.path.join(tmp_path, 'waterlvl_manual_measurements.csv')
    assert not osp.exists(filename)

    time, wl = load_waterlvl_measures(filename, 'Test')
    assert len(time) == 0 and isinstance(time, np.ndarray)
    assert len(wl) == 0 and isinstance(wl, np.ndarray)

    init_waterlvl_measures(tmp_path)
    assert osp.exists(filename)

    time, wl = load_waterlvl_measures(filename, 'Test')
    assert len(time) == 0 and isinstance(time, np.ndarray)
    assert len(wl) == 0 and isinstance(wl, np.ndarray)

    # Assert that the format of the file is correct.
    expected_result = ['Well_ID', 'Time (days)', 'Obs. (mbgs)']
    with open(filename, 'r') as f:
        reader = list(csv.reader(f, delimiter=','))
    assert len(reader) == 1
    assert reader[0] == expected_result


@pytest.mark.parametrize("ext", ['.csv', '.xls', '.xlsx'])
def test_load_waterlvl_measurements(datatmpdir, ext):
    filename = osp.join(datatmpdir, "waterlvl_manual_measurements" + ext)

    # Test that init_waterlvl_measures does not everride an existing file.
    init_waterlvl_measures(datatmpdir)

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
