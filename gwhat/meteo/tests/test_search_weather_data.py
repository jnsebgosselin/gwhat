# -*- coding: utf-8 -*-

# Copyright © GWHAT Project Contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.

import pytest
from flaky import flaky

import os
import os.path as osp
from PyQt5.QtCore import Qt
import numpy as np

# Local imports
from gwhat.meteo.search_weather_data import WeatherStationBrowser
from gwhat.meteo.search_weather_data import QFileDialog
import gwhat.meteo.weather_station_finder
from gwhat.meteo.weather_station_finder import WeatherStationFinder


# ---- Pytest fixtures
@pytest.fixture(scope="module")
def database_filepath(tmp_path_factory):
    # Create a project and add add the wldset to it.
    basetemp = tmp_path_factory.getbasetemp()
    database_filepath = osp.join(basetemp, 'climate_station_database.npy')

    # Mock the path of the database resource file.
    gwhat.meteo.weather_station_finder.DATABASE_FILEPATH = database_filepath

    return database_filepath


@pytest.fixture
def station_browser(qtbot):
    station_browser = WeatherStationBrowser()
    station_browser.set_yearmin(1960)
    station_browser.set_yearmax(2015)
    station_browser.set_yearnbr(10)
    station_browser.set_lat(45)
    station_browser.set_lon(60)

    qtbot.addWidget(station_browser)

    return station_browser


# ---- Expected Results
NOWYEAR = "2018"
EXPECTED_RESULTS = [
    ["L'ACADIE", "10843", "1994", NOWYEAR, "QC", "702LED4",
     '45.29', '-73.35', '43.8'],
    ["STE MADELEINE", "5501", "1979", "2016", "QC", "7027517",
     '45.62', '-73.13', '30.0'],
    ["MONTREAL/ST-HUBERT A", "5490", "1928", "2015", "QC", "7027320",
     '45.52', '-73.42', '27.4'],
    ["SABREVOIS", "5444", "1975", NOWYEAR, "QC", "7026734",
     '45.22', '-73.2', '38.1'],
    ["ROUGEMONT", "5442", "1956", "1985", "QC", "7026700",
     '45.43', '-73.1', '39.9'],
    ["MONT ST HILAIRE", "5423", "1960", "1969", "QC", "7025330",
     '45.55', '-73.08', '173.7'],
    ["MARIEVILLE", "5406", "1960", NOWYEAR, "QC", "7024627",
     '45.4', '-73.13', '38.0'],
    ["LAPRAIRIE", "5389", "1963", NOWYEAR, "QC", "7024100",
     '45.38', '-73.43', '30.0'],
    ["IBERVILLE", "5376", "1963", "2016", "QC", "7023270",
     '45.33', '-73.25', '30.5'],
    ["FARNHAM", "5358", "1917", NOWYEAR, "QC", "7022320",
     '45.3', '-72.9', '68.0']
    ]


# ---- Tests
@flaky(max_runs=3)
def test_load_database(database_filepath, qtbot):
    """
    Test that is is possible to fetch the database from the server and
    save it on disk.
    """
    station_finder = WeatherStationFinder()

    assert not os.path.exists(database_filepath)
    assert station_finder.data is None

    # Load the climate station database from ECCC server.
    station_finder.load_database()
    qtbot.waitUntil(lambda: os.path.exists(database_filepath))
    assert station_finder.data is not None


def test_failed_fetch_database(database_filepath, qtbot, mocker):
    """
    Test that the weather station finder works as expected when fetching the
    database from the server fails.
    """
    station_finder = WeatherStationFinder()
    station_finder.load_database()
    assert station_finder.data is not None

    # Test loading the database when the fetching fails.
    mocker.patch(
        'gwhat.meteo.weather_station_finder.read_stationlist_from_tor',
        return_value=None)
    station_finder.fetch_database()
    qtbot.waitSignal(station_finder.sig_load_database_finished)
    assert station_finder.data is None
    assert os.path.exists(database_filepath)


def test_search_weather_station(database_filepath, station_browser,
                                qtbot, mocker):
    """
    Test that searching for weather station with various criteria
    works as expected.
    """
    station_browser.show()

    qtbot.waitSignal(station_browser.stn_finder_thread.started)
    qtbot.waitSignal(
        station_browser.stn_finder_worker.sig_load_database_finished)
    qtbot.waitSignal(station_browser.stn_finder_thread.finished)
    qtbot.waitUntil(lambda: not station_browser.stn_finder_thread.isRunning(),
                    timeout=60*1000)
    assert station_browser.stn_finder_worker._data is not None

    # Search for stations and assert that lat and lon are 0.
    station_browser.prox_grpbox.setChecked(True)
    assert station_browser.lat_spinBox.value() == 45.0
    assert station_browser.lon_spinBox.value() == 60.0

    # Changed the values of the lat and lon and assert that the proximity
    # values are shown correctly.
    station_browser.set_lat(45.40)
    station_browser.set_lon(73.15)
    prox_data = station_browser.station_table.get_prox_data()
    assert np.max(prox_data) <= 25

    # Assert that the search returned the expected results.
    results = station_browser.stationlist
    for data, expected_data in zip(results, EXPECTED_RESULTS):
        # Assert station info.
        for i in (0, 1, 4, 5):
            assert data[i] == expected_data[i]
        # Assert start and end date.
        assert int(data[2]) == int(expected_data[2])
        assert int(data[3]) >= int(expected_data[3])
        # Assert lat, lon, and elevation.
        for i in (6, 7, 8):
            assert float(data[i]) == float(expected_data[i])

    # Save the results in a csv file.
    fname = os.path.join(
        osp.dirname(database_filepath), "weather_station_list.lst")
    mocker.patch.object(
        QFileDialog, 'getSaveFileName', return_value=(fname, '*.csv'))

    # Save the file and assert it was created correctly.
    station_browser.btn_save_isClicked()
    assert os.path.exists(fname)


def test_refreshes_database_and_fails(station_browser, qtbot, mocker):
    """Test refreshing the database when the fetching fails."""
    station_browser.show()

    qtbot.waitSignal(station_browser.stn_finder_thread.started)
    qtbot.waitSignal(
        station_browser.stn_finder_worker.sig_load_database_finished)
    qtbot.waitSignal(station_browser.stn_finder_thread.finished)
    qtbot.waitUntil(lambda: not station_browser.stn_finder_thread.isRunning(),
                    timeout=60*1000)

    assert station_browser.stn_finder_worker._data is not None

    # Patch the function to fetch the database so that it fails.
    mocker.patch(
        'gwhat.meteo.weather_station_finder.read_stationlist_from_tor',
        return_value=None)

    # Force an update of the database from the GUI.
    qtbot.mouseClick(station_browser.btn_fetch, Qt.LeftButton)

    qtbot.waitSignal(station_browser.stn_finder_thread.started)
    qtbot.waitSignal(
        station_browser.stn_finder_worker.sig_load_database_finished)
    qtbot.waitSignal(station_browser.stn_finder_thread.finished)
    qtbot.waitUntil(lambda: not station_browser.stn_finder_thread.isRunning(),
                    timeout=60*1000)

    assert station_browser.stn_finder_worker._data is None
    assert station_browser.stationlist == []


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
