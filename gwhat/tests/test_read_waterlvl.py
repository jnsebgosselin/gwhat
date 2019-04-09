# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# ---- Standard library imports
import sys
import os
import os.path as osp
import csv

# ---- Third party imports
import pytest
import numpy as np
import xlsxwriter

# ---- Local library imports
from gwhat.common.utils import (save_content_to_excel, save_content_to_csv,
                                delete_file)
from gwhat.projet.reader_waterlvl import (
        load_waterlvl_measures, init_waterlvl_measures, WLDataFrame)

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
FILENAME = "water_level_datafile"


# ---- Pytest Fixtures
@pytest.fixture
def datatmpdir(tmpdir):
    """Create a set of water level datafile in various format."""
    save_content_to_csv(
        osp.join(str(tmpdir), FILENAME + '.csv'), DATA)
    save_content_to_excel(
        osp.join(str(tmpdir), FILENAME + '.xls'), DATA)
    save_content_to_excel(
        osp.join(str(tmpdir), FILENAME + '.xlsx'), DATA)

    return str(tmpdir)


# ---- Test reading water level datafiles
@pytest.mark.parametrize("ext", ['.csv', '.xls', '.xlsx'])
def test_reading_waterlvl(datatmpdir, ext):
    df = WLDataFrame(osp.join(datatmpdir, FILENAME + ext))

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


# Test water_level_measurements.
# -------------------------------

delete_file("waterlvl_manual_measurements.csv")
delete_file("waterlvl_manual_measurements.xls")
delete_file("waterlvl_manual_measurements.xlsx")

WLMEAS = [['Well_ID', 'Time (days)', 'Obs. (mbgs)'],
          ['Test', 40623.54167, 1.43],
          ['Test', 40842.54167, 1.6],
          ['Test', 41065.54167, 1.57],
          ['test', 41065.54167, 1.57],
          ["é@#^'", 41240.8125, 3.75],
          ['test2', 41402.34375, 3.56],
          ]


def test_init_waterlvl_measures():
    # Assert that the water_level_measurement file is initialized correctly.
    filename = os.path.join(os.getcwd(), "waterlvl_manual_measurements")
    assert not os.path.exists(filename+'.csv')
    time, wl = load_waterlvl_measures(filename, 'Test')
    assert os.path.exists(filename+'.csv')
    assert len(time) == 0 and isinstance(time, np.ndarray)
    assert len(wl) == 0 and isinstance(wl, np.ndarray)

    # Assert that the format of the file is correct.
    expected_result = ['Well_ID', 'Time (days)', 'Obs. (mbgs)']
    with open(filename+'.csv', 'r') as f:
        reader = list(csv.reader(f, delimiter=','))
    assert len(reader) == 1
    assert reader[0] == expected_result


def test_load_waterlvl_measures_withcsv():
    filename = os.path.join(os.getcwd(), "waterlvl_manual_measurements.csv")
    save_content_to_csv(filename, WLMEAS)

    # Test init_waterlvl_measures to be sure the file is not overriden.
    init_waterlvl_measures(os.getcwd())

    # Assert that it loads the right data.
    filename = os.path.join(os.getcwd(), "waterlvl_manual_measurements")
    time, wl = load_waterlvl_measures(filename, 'Dummy')
    assert len(time) == 0 and isinstance(time, np.ndarray)
    assert len(wl) == 0 and isinstance(wl, np.ndarray)

    time, wl = load_waterlvl_measures(filename, 'Test')
    assert np.all(time == np.array([40623.54167, 40842.54167, 41065.54167]))
    assert np.all(wl == np.array([1.43, 1.6, 1.57]))

    time, wl = load_waterlvl_measures(filename, "é@#^'")
    assert np.all(time == np.array([41240.8125]))
    assert np.all(wl == np.array([3.75]))


def test_load_waterlvl_measures_withxls():
    filename = os.path.join(os.getcwd(), "waterlvl_manual_measurements.csv")
    delete_file(filename)
    assert not os.path.exists(filename)

    filename = os.path.join(os.getcwd(), "waterlvl_manual_measurements.xlsx")
    with xlsxwriter.Workbook(filename) as wb:
        ws = wb.add_worksheet()
        for i, line in enumerate(WLMEAS):
            ws.write_row(i, 0, line)

    # Test init_waterlvl_measures to be sure the file is not overriden.
    init_waterlvl_measures(os.getcwd())

    # Assert that it loads the right data.
    filename = os.path.join(os.getcwd(), "waterlvl_manual_measurements")
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
    # pytest.main()
