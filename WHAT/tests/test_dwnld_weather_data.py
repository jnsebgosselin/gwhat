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


@pytest.mark.run(order=2)
def test_load_old_stationlist(downloader_bot):
    downloader_bot, qtbot = downloader_bot
    assert downloader_bot

    dirname = os.path.dirname(os.path.realpath(__file__))
    expected_result = [["ABERCORN", "5308", "1950", "1985",
                        "QC", "7020040", "1.25"],
                       ["AIGREMONT", "5886", "1973", "1982",
                        "QC", "7060070", "3.45"],
                       ["ALBANEL", "5887", "1922", "1991",
                        "QC", "7060080", "2.23"]]

    # Assert that tab-separated-value station list loads correctly
    fname = os.path.join(dirname, "stationlist_tab.lst")
    station_list = downloader_bot.load_stationList(fname)
    assert station_list == expected_result

    # Assert that the data are stored correctly in the widget table
    list_from_table = downloader_bot.station_table.get_staList()
    assert list_from_table == expected_result


@pytest.mark.run(order=2)
def test_load_stationlist(downloader_bot):
    downloader_bot, qtbot = downloader_bot
    assert downloader_bot

    expected_result = [
        ["MARIEVILLE", "5406", "1960", "2017", "QC", "7024627", "1.32"],
        ["ROUGEMONT", "5442", "1956", "1985", "QC", "7026700", "5.43"],
        ["IBERVILLE", "5376", "1963", "2016", "QC", "7023270", "10.86"],
        ["MONT ST HILAIRE", "5423", "1960", "1969", "QC", "7025330", "17.49"],
        ["L'ACADIE", "10843", "1994", "2017", "QC", "702LED4", "19.73"],
        ["SABREVOIS", "5444", "1975", "2017", "QC", "7026734", "20.76"],
        ["LAPRAIRIE", "5389", "1963", "2017", "QC", "7024100", "22.57"],
        ["FARNHAM", "5358", "1917", "2017", "QC", "7022320", "22.73"],
        ["STE MADELEINE", "5501", "1979", "2016", "QC", "7027517", "24.12"],
        ["MONTREAL/ST-HUBERT A", "5490", "1928", "2015", "QC", "7027320",
         "24.85"]
        ]

    # Assert that coma-separated-value station list loads correctly
    fname = os.path.join(os.getcwd(), 'weather_station_list.lst')
    station_list = downloader_bot.load_stationList(fname)
    assert station_list == expected_result

    # Assert that the data are stored correctly in the widget table
    list_from_table = downloader_bot.station_table.get_staList()
    assert list_from_table == expected_result


if __name__ == "__main__":
    pytest.main()
