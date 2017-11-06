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
from WHAT.meteo.search_weather_data import Search4Stations             # nopep8
from WHAT.meteo.search_weather_data import QFileDialog                 # nopep8


# ---- Qt Test Fixtures


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


# ---- Expected Results


expected_results = [
        ["MARIEVILLE", "5406", "1960", "2017", "QC", "7024627",
         '45.400', '73.133', '38.0'],
        ["ROUGEMONT", "5442", "1956", "1985", "QC", "7026700",
         '45.433', '73.100', '39.9'],
        ["IBERVILLE", "5376", "1963", "2016", "QC", "7023270",
         '45.333', '73.250', '30.5'],
        ["MONT ST HILAIRE", "5423", "1960", "1969", "QC", "7025330",
         '45.550', '73.083', '173.7'],
        ["L'ACADIE", "10843", "1994", "2017", "QC", "702LED4",
         '45.294', '73.349', '43.8'],
        ["SABREVOIS", "5444", "1975", "2017", "QC", "7026734",
         '45.217', '73.200', '38.1'],
        ["LAPRAIRIE", "5389", "1963", "2017", "QC", "7024100",
         '45.383', '73.433', '30.0'],
        ["FARNHAM", "5358", "1917", "2017", "QC", "7022320",
         '45.300', '72.900', '68.0'],
        ["STE MADELEINE", "5501", "1979", "2016", "QC", "7027517",
         '45.617', '73.133', '30.0'],
        ["MONTREAL/ST-HUBERT A", "5490", "1928", "2015", "QC", "7027320",
         '45.517', '73.417', '27.4']
        ]


# ---- Tests


@pytest.mark.run(order=2)
def test_search_weather_station(station_finder_bot, mocker):
    station_finder_widget, qtbot = station_finder_bot
    station_finder_widget.show()
    assert station_finder_widget

    # Search for stations and assert the results.
    searchFinished = station_finder_widget.finder.searchFinished
    with qtbot.waitSignal(searchFinished, raising=True, timeout=60000):
        station_finder_widget.btn_search_isClicked()
    results = station_finder_widget.finder.stationlist

    assert results == expected_results

    # Assert that the results are displayed correctly in the UI.
    assert (station_finder_widget.station_table.get_stationlist() ==
            station_finder_widget.finder.stationlist)

    # Mock the dialog window and answer to specify the file name and type.
    fname = os.path.join(os.getcwd(), "@ new-prô'jèt!",
                         "weather_station_list.lst")
    ftype = '*.csv'
    mocker.patch.object(QFileDialog, 'getSaveFileName',
                        return_value=(fname, ftype))

    # Delete file if it exists.
    if os.path.exists(fname):
        os.remove(fname)

    # Save the file.
    station_finder_widget.btn_save_isClicked()


@pytest.mark.run(order=2)
def test_stop_search(station_finder_bot):
    station_finder_widget, qtbot = station_finder_bot
    station_finder_widget.show()
    assert station_finder_widget

    # Start the search.
    sig_newstation_found = station_finder_widget.finder.sig_newstation_found
    with qtbot.waitSignal(sig_newstation_found, raising=True, timeout=60000):
        station_finder_widget.btn_search_isClicked()

    # Stop the search as soon as we received a result and assert the results.
    searchFinished = station_finder_widget.finder.searchFinished
    with qtbot.waitSignal(searchFinished, raising=True, timeout=60000):
        station_finder_widget.btn_search_isClicked()
    results = station_finder_widget.finder.stationlist

    assert len(results) < len(expected_results)
    assert results == expected_results[:len(results)]

    # Assert that the results are displayed correctly in the UI
    assert (station_finder_widget.station_table.get_stationlist() ==
            station_finder_widget.finder.stationlist)

    # Restart the search and let it fihish completely and assert the results.
    searchFinished = station_finder_widget.finder.searchFinished
    with qtbot.waitSignal(searchFinished, raising=True, timeout=60000):
        station_finder_widget.btn_search_isClicked()
    results = station_finder_widget.finder.stationlist

    assert results == expected_results

    # Assert that the results are displayed correctly in the UI
    assert (station_finder_widget.station_table.get_stationlist() ==
            station_finder_widget.finder.stationlist)


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
