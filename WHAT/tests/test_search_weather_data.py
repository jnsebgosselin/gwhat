# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 01:50:50 2017
@author: jsgosselin
"""

import pytest

import sys
import os.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

# Local imports
from meteo.search_weather_data import Search4Stations

# Qt Test Fixtures
# --------------------------------


@pytest.fixture
def station_finder_bot(qtbot):
    station_finder_widget = Search4Stations()
    station_finder_widget.lat_spinBox.setValue(45.40)
    station_finder_widget.lon_spinBox.setValue(73.13)

    qtbot.addWidget(station_finder_widget)

    return station_finder_widget, qtbot

# Tests
# -------------------------------


def test_station_finder(station_finder_bot):
    station_finder_widget, qtbot = station_finder_bot
    assert station_finder_widget


if __name__ == "__main__":
    pytest.main()
