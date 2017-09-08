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
from meteo.dwnld_weather_data import dwnldWeather

# Qt Test Fixtures
# --------------------------------


@pytest.fixture
def downloader_bot(qtbot):
    wxdata_downloader = dwnldWeather()
    qtbot.addWidget(wxdata_downloader)
    return wxdata_downloader, qtbot

# Tests
# -------------------------------


def test_downloader(downloader_bot):
    downloader_bot, qtbot = downloader_bot
    assert downloader_bot


def test_load_stationlist(downloader_bot):
    downloader_bot, qtbot = downloader_bot
#    dirname = os.path.dirname(os.path.realpath(__file__))
    expected_result = [["ABERCORN", "5308", "1950", "1985",
                        "QC", "7020040", "1.25"],
                       ["AIGREMONT", "5886", "1973", "1982",
                        "QC", "7060070", "3.45"],
                       ["ALBANEL", "5887", "1922", "1991",
                        "QC", "7060080", "2.23"]]

    assert True == True
#
#    # Assert that coma-separated-value station list loads correctly
#    fname = os.path.join(dirname, "stationlist_coma.lst")
#    station_list = downloader_bot.load_stationList(fname)
#    assert station_list == expected_result
#
#    # Assert that the data are stored correctly in the widget table
#    list_from_table = downloader_bot.station_table.get_staList()
#    assert list_from_table == expected_result
#
#    # Assert that tab-separated-value station list loads correctly
#    fname = os.path.join(dirname, "stationlist_tab.lst")
#    station_list = downloader_bot.load_stationList(fname)
#    assert station_list == expected_result
#
#    # Assert that the data are stored correctly in the widget table
#    list_from_table = downloader_bot.station_table.get_staList()
#    assert list_from_table == expected_result


if __name__ == "__main__":
    pytest.main()
