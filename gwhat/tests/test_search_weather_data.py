# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 01:50:50 2017
@author: jsgosselin
"""

import pytest

import sys
import os
from PyQt5.QtCore import Qt
import numpy as np

# Local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from gwhat.meteo.search_weather_data import WeatherStationBrowser      # nopep8
from gwhat.meteo.search_weather_data import QFileDialog                # nopep8


# ---- Qt Test Fixtures


@pytest.fixture
def station_finder_bot(qtbot):
    station_browser = WeatherStationBrowser()
    station_browser.set_yearmin(1960)
    station_browser.set_yearmax(2015)
    station_browser.set_yearnbr(10)
    station_browser.set_lat(45)
    station_browser.set_lon(60)

    qtbot.addWidget(station_browser)

    return station_browser, qtbot


# ---- Expected Results


expected_results = [
        ["L'ACADIE", "10843", "1994", "2018", "QC", "702LED4",
         '45.29', '-73.35', '43.8'],
        ["STE MADELEINE", "5501", "1979", "2016", "QC", "7027517",
         '45.62', '-73.13', '30.0'],
        ["MONTREAL/ST-HUBERT A", "5490", "1928", "2015", "QC", "7027320",
         '45.52', '-73.42', '27.4'],
        ["SABREVOIS", "5444", "1975", "2017", "QC", "7026734",
         '45.22', '-73.2', '38.1'],
        ["ROUGEMONT", "5442", "1956", "1985", "QC", "7026700",
         '45.43', '-73.1', '39.9'],
        ["MONT ST HILAIRE", "5423", "1960", "1969", "QC", "7025330",
         '45.55', '-73.08', '173.7'],
        ["MARIEVILLE", "5406", "1960", "2017", "QC", "7024627",
         '45.4', '-73.13', '38.0'],
        ["LAPRAIRIE", "5389", "1963", "2017", "QC", "7024100",
         '45.38', '-73.43', '30.0'],
        ["IBERVILLE", "5376", "1963", "2016", "QC", "7023270",
         '45.33', '-73.25', '30.5'],
        ["FARNHAM", "5358", "1917", "2017", "QC", "7022320",
         '45.3', '-72.9', '68.0']
        ]


# ---- Tests


@pytest.mark.run(order=2)
def test_search_weather_station(station_finder_bot, mocker):
    station_browser, qtbot = station_finder_bot
    station_browser.show()
    assert station_browser

    # Search for stations and assert that lat and lon are 0.
    station_browser.prox_grpbox.setChecked(True)
    assert station_browser.lat_spinBox.value() == 45.0
    assert station_browser.lon_spinBox.value() == 60.0

    # Changed the values of the lat and lon and assert that the proximity
    # values are shown correctly.
    station_browser.lon_spinBox.setValue(73.15)
    station_browser.lat_spinBox.setValue(45.40)
    prox_data = station_browser.station_table.get_prox_data()
    assert np.max(prox_data) <= 25

    # Assert that the search returns the expected results.
    results = station_browser.stationlist
    assert results == expected_results

    # Mock the dialog window and answer to specify the file name and type.
    fname = os.path.join(os.getcwd(), "@ new-prô'jèt!",
                         "weather_station_list.lst")
    mocker.patch.object(QFileDialog, 'getSaveFileName',
                        return_value=(fname, '*.csv'))

    # Delete file if it exists.
    if os.path.exists(fname):
        os.remove(fname)

    # Save the file and assert it was created correctly.
    station_browser.btn_save_isClicked()
    assert os.path.exists(fname)


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
