# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 01:50:50 2017
@author: jsgosselin
"""

import pytest

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

# Local imports
from meteo.search_weather_data import Search4Stations
from meteo.search_weather_data import QFileDialog

# Qt Test Fixtures
# --------------------------------


@pytest.fixture
def station_finder_bot(qtbot):
    station_finder_widget = Search4Stations()
    station_finder_widget.lat_spinBox.setValue(45.40)
    station_finder_widget.lon_spinBox.setValue(73.15)
    station_finder_widget.minYear.setValue(1960)
    station_finder_widget.maxYear.setValue(2015)
    station_finder_widget.nbrYear.setValue(10)

    qtbot.addWidget(station_finder_widget)

    return station_finder_widget, qtbot

# Tests
# -------------------------------


def test_station_finder(station_finder_bot):
    station_finder_widget, qtbot = station_finder_bot
    assert station_finder_widget


def test_search_weather_station(station_finder_bot, mocker):
    station_finder_widget, qtbot = station_finder_bot
    station_finder_widget.show()

    expected_results = [
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

    # Search for stations and assert the results.
    searchFinished = station_finder_widget.finder.searchFinished
    with qtbot.waitSignal(searchFinished, raising=True, timeout=60000):
        station_finder_widget.btn_search_isClicked()
    results = station_finder_widget.finder.stationlist

    assert results == expected_results

    # Assert that the results are displayed correctly in the UI
    assert (station_finder_widget.station_table.get_staList() ==
            station_finder_widget.finder.stationlist)

    # Mock the dialog window and answer to specify the file name and type
    fname = os.path.join(os.getcwd(), 'weather_station_list.lst')
    ftype = '*.csv'
    mocker.patch.object(QFileDialog, 'getSaveFileName',
                        return_value=(fname, ftype))

    # Delete file if it exists
    if os.path.exists(fname):
        os.remove(fname)

    # Save the file
    station_finder_widget.btn_save_isClicked()


def test_stop_search(station_finder_bot):
    station_finder_widget, qtbot = station_finder_bot
    station_finder_widget.show()

    expected_results = [
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

    # Start the search.
    newStationFound = station_finder_widget.finder.newStationFound
    with qtbot.waitSignal(newStationFound, raising=True, timeout=60000):
        station_finder_widget.btn_search_isClicked()

    # Stop the search as soon as we received a result and assert the results.
    searchFinished = station_finder_widget.finder.searchFinished
    with qtbot.waitSignal(searchFinished, raising=True, timeout=60000):
        station_finder_widget.btn_search_isClicked()
    results = station_finder_widget.finder.stationlist

    assert len(results) < len(expected_results)
    assert results == expected_results[:len(results)]

    # Assert that the results are displayed correctly in the UI
    assert (station_finder_widget.station_table.get_staList() ==
            station_finder_widget.finder.stationlist)

    # Restart the search and let it fihish completely and assert the results.
    searchFinished = station_finder_widget.finder.searchFinished
    with qtbot.waitSignal(searchFinished, raising=True, timeout=60000):
        station_finder_widget.btn_search_isClicked()
    results = station_finder_widget.finder.stationlist

    assert results == expected_results

    # Assert that the results are displayed correctly in the UI
    assert (station_finder_widget.station_table.get_staList() ==
            station_finder_widget.finder.stationlist)


if __name__ == "__main__":
    pytest.main([os.path.basename(__file__)])
