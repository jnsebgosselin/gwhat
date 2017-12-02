# -*- coding: utf-8 -*-

# Copyright © 2014-2017 GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (GroundWater Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

# Standard library imports
import sys
import os
import csv

# Third party imports
import pytest
import numpy as np
import xlsxwriter

# Local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from gwhat.common.utils import save_content_to_csv, delete_file
from gwhat.projet.reader_waterlvl import (load_waterlvl_measures,
                                          init_waterlvl_measures)

WLMEAS = [['Well_ID', 'Time (days)', 'Obs. (mbgs)'],
          ['Test', 40623.54167, 1.43],
          ['Test', 40842.54167, 1.6],
          ['Test', 41065.54167, 1.57],
          ['test', 41065.54167, 1.57],
          ["é@#^'", 41240.8125, 3.75],
          ['test2', 41402.34375, 3.56],
          ]


# Test water_level_measurements.*
# -------------------------------


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
