# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.


# ---- Standard library imports
import os
import os.path as osp
from urllib.parse import urljoin
from urllib.request import pathname2url


# ---- Third party imports
import pytest
from PyQt5.QtCore import Qt

# ---- Local imports
import gwhat.meteo.search_weather_data
from gwhat.meteo.dwnld_weather_data import (
        DwnldWeatherWidget, RawDataDownloader, QFileDialog, QMessageBox)

STARTYEAR = 2000
ENDYEAR = 2003
DATADIR = os.path.join(osp.dirname(osp.realpath(__file__)), "data")
STATIONDB = os.path.join(DATADIR, "Station Inventory EN.csv")
STATIONLIST = os.path.join(DATADIR, "weather_station_list.lst")

gwhat.meteo.weather_station_finder.URL_TOR = urljoin(
    'file:', pathname2url(STATIONDB))


# ---- Pytest Fixtures
@pytest.fixture(scope="module")
def workdir(tmp_path_factory):
    basetemp = tmp_path_factory.getbasetemp()
    return osp.join(basetemp, "@ tèst-dôwn'loaddätèt!")


@pytest.fixture
def dwnld_weather_widget(qtbot, workdir):
    dwnld_weather_widget = DwnldWeatherWidget()
    dwnld_weather_widget.set_workdir(workdir)
    qtbot.addWidget(dwnld_weather_widget)

    return dwnld_weather_widget


# ---- Test RawDataDownloader
def test_download_raw_data(workdir):
    """Test downloading raw datafiles from the Environnement Canada server."""
    dwnld_worker = RawDataDownloader()

    # Set attributes of the data downloader.
    dwnld_worker.dirname = os.path.join(workdir, 'Meteo', 'Raw')
    dwnld_worker.StaName = "MARIEVILLE"
    dwnld_worker.stationID = "5406"
    dwnld_worker.yr_start = str(STARTYEAR)
    dwnld_worker.yr_end = str(ENDYEAR)
    dwnld_worker.climateID = "7024627"

    # Download data for station Marieville
    dwnld_worker.download_data()

    # Download data again to test when raw data files are already present
    dwnld_worker.download_data()

    # Test the stopping of the downloading process
    dwnld_worker.stop_download()
    dwnld_worker.download_data()

    # Assert that the raw data files were downloaded.
    expected_files = ["eng-daily-0101{}-1231{}.csv".format(year, year) for
                      year in range(STARTYEAR, ENDYEAR+1)]
    subfolder = "{} ({})".format(dwnld_worker.StaName, dwnld_worker.climateID)
    for file in expected_files:
        assert osp.exists(os.path.join(
            dwnld_worker.dirname, subfolder, file))


# ---- Test DwnldWeatherWidget
def test_load_tabsep_stationlist(dwnld_weather_widget, qtbot):
    """
    Test that the station list is loaded correctly when the data are
    separated by tabs.
    """
    dirname = os.path.dirname(os.path.realpath(__file__))
    expected_results = [
        ["MARIEVILLE", "5406", "1960", "2017", "QC", "7024627",
         '45.400', '73.133', '38.0'],
        ["ROUGEMONT", "5442", "1956", "1985", "QC", "7026700",
         '45.433', '73.100', '39.9'],
        ["IBERVILLE", "5376", "1963", "2016", "QC", "7023270",
         '45.333', '73.250', '30.5']
        ]

    # Assert that tab-separated-value station list loads correctly.
    fname = os.path.join(dirname, "data", "stationlist_tabsep.lst")
    station_list = dwnld_weather_widget.load_stationList(fname)
    assert station_list == expected_results

    # Assert that the data are stored correctly in the widget table.
    list_from_table = dwnld_weather_widget.station_table.get_stationlist()
    assert list_from_table == expected_results


def test_load_stationlist(dwnld_weather_widget, mocker):
    """Test loading a valid station list with coma separated values."""
    expected_results = [
        ["L'ACADIE", "10843", "1994", "2018", "QC", "702LED4",
         '45.29', '-73.35', '43.8'],
        ["STE MADELEINE", "5501", "1979", "2016", "QC", "7027517",
         '45.62', '-73.13', '30.0'],
        ["MONTREAL/ST-HUBERT A", "5490", "1928", "2015", "QC", "7027320",
         '45.52', '-73.42', '27.4'],
        ["SABREVOIS", "5444", "1975", "2018", "QC", "7026734",
         '45.22', '-73.2', '38.1'],
        ["ROUGEMONT", "5442", "1956", "1985", "QC", "7026700",
         '45.43', '-73.1', '39.9'],
        ["MONT ST HILAIRE", "5423", "1960", "1969", "QC", "7025330",
         '45.55', '-73.08', '173.7'],
        ["MARIEVILLE", "5406", "1960", "2018", "QC", "7024627",
         '45.4', '-73.13', '38.0'],
        ["LAPRAIRIE", "5389", "1963", "2018", "QC", "7024100",
         '45.38', '-73.43', '30.0'],
        ["IBERVILLE", "5376", "1963", "2016", "QC", "7023270",
         '45.33', '-73.25', '30.5'],
        ["FARNHAM", "5358", "1917", "2018", "QC", "7022320",
         '45.3', '-72.9', '68.0']
        ]

    # Mock the dialog window and answer to specify the file name and type.
    mocker.patch.object(QFileDialog, 'getOpenFileName',
                        return_value=(STATIONLIST, '*.lst'))

    # Assert that coma-separated-value station list loads correctly.
    dwnld_weather_widget.btn_browse_staList_isClicked()

    # Assert that the data are stored correctly in the widget table.
    station_list = dwnld_weather_widget.station_table.get_stationlist()
    assert expected_results == station_list

    # Test that the station list formating to html works without any error.
    station_list.format_list_in_html()

    # Try to open a station list when the file does not exist.
    dwnld_weather_widget.load_stationList("dummy.lst")
    assert [] == dwnld_weather_widget.station_table.get_stationlist()


def test_delete_add_stations(dwnld_weather_widget, qtbot, mocker, workdir):
    """Test deleting and adding new stations to the list."""
    station_table = dwnld_weather_widget.station_table

    # Load a station list from file.
    original_list = dwnld_weather_widget.load_stationList(STATIONLIST)

    # Try to delete stations when no station are selected.
    dwnld_weather_widget.btn_delSta_isClicked()

    # Select stations MONT ST HILAIRE, MONTREAL/ST-HUBERT A, and ROUGEMONT
    # in the list and delete them.
    expected_results = [
        ["L'ACADIE", "10843", "1994", "2018", "QC", "702LED4",
         '45.29', '-73.35', '43.8'],
        ["STE MADELEINE", "5501", "1979", "2016", "QC", "7027517",
         '45.62', '-73.13', '30.0'],
        ["SABREVOIS", "5444", "1975", "2018", "QC", "7026734",
         '45.22', '-73.2', '38.1'],
        ["MARIEVILLE", "5406", "1960", "2018", "QC", "7024627",
         '45.4', '-73.13', '38.0'],
        ["LAPRAIRIE", "5389", "1963", "2018", "QC", "7024100",
         '45.38', '-73.43', '30.0'],
        ["IBERVILLE", "5376", "1963", "2016", "QC", "7023270",
         '45.33', '-73.25', '30.5'],
        ["FARNHAM", "5358", "1917", "2018", "QC", "7022320",
         '45.3', '-72.9', '68.0']
        ]

    for row in [2, 4, 5]:
        item = station_table.cellWidget(row, 0).layout().itemAtPosition(1, 1)
        widget = item.widget()
        qtbot.mouseClick(widget, Qt.LeftButton)
    dwnld_weather_widget.btn_delSta_isClicked()
    assert expected_results == station_table.get_stationlist()

    # Save station list.
    fname = os.path.join(workdir, "cleaned_station_list.lst")
    mocker.patch.object(QFileDialog, 'getSaveFileName',
                        return_value=(fname, "*.lst"))
    dwnld_weather_widget.btn_saveAs_staList_isClicked()
    dwnld_weather_widget.btn_save_staList_isClicked()

    # Add back the stations that were deleted.
    expected_results = [
        ["L'ACADIE", "10843", "1994", "2018", "QC", "702LED4",
         '45.29', '-73.35', '43.8'],
        ["STE MADELEINE", "5501", "1979", "2016", "QC", "7027517",
         '45.62', '-73.13', '30.0'],
        ["SABREVOIS", "5444", "1975", "2018", "QC", "7026734",
         '45.22', '-73.2', '38.1'],
        ["MARIEVILLE", "5406", "1960", "2018", "QC", "7024627",
         '45.4', '-73.13', '38.0'],
        ["LAPRAIRIE", "5389", "1963", "2018", "QC", "7024100",
         '45.38', '-73.43', '30.0'],
        ["IBERVILLE", "5376", "1963", "2016", "QC", "7023270",
         '45.33', '-73.25', '30.5'],
        ["FARNHAM", "5358", "1917", "2018", "QC", "7022320",
         '45.3', '-72.9', '68.0'],
        ["MONTREAL/ST-HUBERT A", "5490", "1928", "2015", "QC", "7027320",
         '45.52', '-73.42', '27.4'],
        ["ROUGEMONT", "5442", "1956", "1985", "QC", "7026700",
         '45.43', '-73.1', '39.9'],
        ["MONT ST HILAIRE", "5423", "1960", "1969", "QC", "7025330",
         '45.55', '-73.08', '173.7']
        ]

    dwnld_weather_widget.add_stations2list(original_list)
    assert expected_results == station_table.get_stationlist()

    # Clear completely the station list.
    station_table.chkbox_header.setCheckState(Qt.CheckState(True))
    assert len(station_table.get_checked_rows()) == len(expected_results)

    dwnld_weather_widget.btn_delSta_isClicked()
    assert [] == station_table.get_stationlist()

    # Add back the stations that were deleted.
    dwnld_weather_widget.add_stations2list(original_list)
    assert original_list == station_table.get_stationlist()


def test_download_data(dwnld_weather_widget, qtbot, mocker, workdir):
    """Test downloading data."""
    station_table = dwnld_weather_widget.station_table
    dwnld_weather_widget.show()
    dwnld_weather_widget.load_stationList(STATIONLIST)

    # Set "to year" and "from year" for all stations.
    station_table.set_fromyear(STARTYEAR)
    station_table.set_toyear(ENDYEAR)

    # Try starting the downloading process before selecting any station.
    mocker.patch.object(QMessageBox, 'warning', return_value=QMessageBox.Ok)
    qtbot.mouseClick(dwnld_weather_widget.btn_get, Qt.LeftButton)

    # Check stations "Marieville", "IBERVILLE" and "L'ACADIE".
    for row in [0, 6, 8]:
        item = station_table.cellWidget(row, 0).layout().itemAtPosition(1, 1)
        widget = item.widget()
        qtbot.mouseClick(widget, Qt.LeftButton)

    # Download the data for the selected stations.
    process_finished = dwnld_weather_widget.sig_download_process_ended
    with qtbot.waitSignal(process_finished, raising=True, timeout=300000):
        qtbot.mouseClick(dwnld_weather_widget.btn_get, Qt.LeftButton)

    stanames = [
        "MARIEVILLE (7024627)", "IBERVILLE (7023270)", "L'ACADIE (702LED4)"]
    for station in stanames:
        # Assert that data before STARTYEAR were not downloaded.
        file = "eng-daily-0101{}-1231{}.csv".format(STARTYEAR-1, STARTYEAR-1)
        assert not osp.exists(osp.join(workdir, "Meteo", "Raw", station, file))

        # Assert that data after ENDYEAR were not downloaded.
        file = "eng-daily-0101{}-1231{}.csv".format(ENDYEAR+1, ENDYEAR+1)
        assert not osp.exists(osp.join(workdir, "Meteo", "Raw", station, file))

        # Assert that the concatenated datafiles were created.
        file = "{}_{}-{}.csv".format(station, STARTYEAR, ENDYEAR)
        assert osp.exists(osp.join(workdir, "Meteo", "Input", file))


def test_merge_widget(dwnld_weather_widget, qtbot, mocker, workdir):
    """
    Test the widget that merge the raw weather data files.
    """
    dwnld_weather_widget.show()
    qtbot.waitActive(dwnld_weather_widget, timeout=3000)

    dirname = os.path.join(workdir, "Meteo", "Raw")
    stations = ["MARIEVILLE (7024627)",
                "IBERVILLE (7023270)",
                "L'ACADIE (702LED4)"]
    filenames = ["eng-daily-01012000-12312000.csv",
                 "eng-daily-01012001-12312001.csv",
                 "eng-daily-01012002-12312002.csv"]

    # Disable 'auto save merged data' option.
    dwnld_weather_widget.saveAuto_checkbox.setChecked(False)

    # Opens raw data files for each station.
    for station in stations:
        paths = []
        for file in filenames:
            filepath = os.path.join(dirname, station, file)
            assert os.path.exists(filepath)
            paths.append(filepath)

        mocker.patch.object(QFileDialog, 'getOpenFileNames',
                            return_value=(paths, '*.csv'))
        qtbot.mouseClick(dwnld_weather_widget.btn_selectRaw, Qt.LeftButton)

    # Assert that the concatenated files were not saved.
    dirname = os.path.join(workdir, "Meteo", "Input")
    filenames = ["{}_2000-2002.csv".format(s) for s in stations]
    filepaths = [osp.join(dirname, f) for f in filenames]
    for path in filepaths:
        assert not os.path.exists(path)

    # Navigate to the first concatedated dataset and assert that
    # the navigation buttons are enabled/disabled as expected.
    qtbot.mouseClick(dwnld_weather_widget.btn_goFirst, Qt.LeftButton)
    qtbot.waitUntil(lambda: not dwnld_weather_widget.btn_goFirst.isEnabled())
    qtbot.waitUntil(
        lambda: not dwnld_weather_widget.btn_goPrevious.isEnabled())
    qtbot.waitUntil(lambda: dwnld_weather_widget.btn_goLast.isEnabled())
    qtbot.waitUntil(lambda: dwnld_weather_widget.btn_goNext.isEnabled())

    # Save the file and assert that it was created as expected
    mocker.patch.object(QFileDialog, 'getSaveFileName',
                        return_value=(filepaths[0], '*.csv'))
    qtbot.mouseClick(dwnld_weather_widget.btn_saveMerge, Qt.LeftButton)
    qtbot.waitUntil(lambda: osp.exists(filepaths[0]))

    # Navigate to the last concatedated dataset and assert that
    # the navigation buttons are enabled/disabled as expected.
    qtbot.mouseClick(dwnld_weather_widget.btn_goLast, Qt.LeftButton)
    qtbot.waitUntil(lambda: dwnld_weather_widget.btn_goFirst.isEnabled())
    qtbot.waitUntil(lambda: dwnld_weather_widget.btn_goPrevious.isEnabled())
    qtbot.waitUntil(lambda: not dwnld_weather_widget.btn_goLast.isEnabled())
    qtbot.waitUntil(lambda: not dwnld_weather_widget.btn_goNext.isEnabled())

    # Save the file and assert that it was created as expected
    mocker.patch.object(QFileDialog, 'getSaveFileName',
                        return_value=(filepaths[-1], '*.csv'))
    qtbot.mouseClick(dwnld_weather_widget.btn_saveMerge, Qt.LeftButton)
    qtbot.waitUntil(lambda: os.path.exists(filepaths[-1]))

    # Navigate to the previous concatedated dataset and assert that
    # the navigation buttons are enabled/disabled as expected.
    qtbot.mouseClick(dwnld_weather_widget.btn_goPrevious, Qt.LeftButton)
    qtbot.waitUntil(lambda: dwnld_weather_widget.btn_goFirst.isEnabled())
    qtbot.waitUntil(lambda: dwnld_weather_widget.btn_goPrevious.isEnabled())
    qtbot.waitUntil(lambda: dwnld_weather_widget.btn_goLast.isEnabled())
    qtbot.waitUntil(lambda: dwnld_weather_widget.btn_goNext.isEnabled())

    # Save the file and assert that it was created as expected
    mocker.patch.object(QFileDialog, 'getSaveFileName',
                        return_value=(filepaths[-2], '*.csv'))
    qtbot.mouseClick(dwnld_weather_widget.btn_saveMerge, Qt.LeftButton)
    qtbot.waitUntil(lambda: osp.exists(filepaths[-2]))

    # Navigate to the next concatedated dataset and assert that
    # the navigation buttons are enabled/disabled as expected.
    qtbot.mouseClick(dwnld_weather_widget.btn_goNext, Qt.LeftButton)
    qtbot.waitUntil(lambda: dwnld_weather_widget.btn_goFirst.isEnabled())
    qtbot.waitUntil(lambda: dwnld_weather_widget.btn_goPrevious.isEnabled())
    qtbot.waitUntil(lambda: not dwnld_weather_widget.btn_goLast.isEnabled())
    qtbot.waitUntil(lambda: not dwnld_weather_widget.btn_goNext.isEnabled())


# ---- Test WeatherStationFinder
def test_search_weather_data(dwnld_weather_widget, qtbot, mocker):
    """
    Test that the Climate Station Browser is initialise correctly from
    the Weather Data Downloader widget and that the stations from the
    browser are added correctly to the table of the downloader.
    """
    assert dwnld_weather_widget.station_browser is None
    dwnld_weather_widget.set_station_browser_latlon((45.40, 73.15))

    # Open the Climate station browser.
    dwnld_weather_widget.btn_search4station_isclicked()
    assert dwnld_weather_widget.station_browser is not None
    assert dwnld_weather_widget.station_browser.lat == 45.40
    assert dwnld_weather_widget.station_browser.lon == 73.15

    # Assert that the database was loaded correctly in the browser.
    station_browser = dwnld_weather_widget.station_browser
    qtbot.addWidget(station_browser)

    qtbot.waitSignal(station_browser.stn_finder_thread.started)
    qtbot.waitSignal(
        station_browser.stn_finder_worker.sig_load_database_finished)
    qtbot.waitSignal(station_browser.stn_finder_thread.finished)
    qtbot.waitUntil(lambda: not station_browser.stn_finder_thread.isRunning(),
                    timeout=60*1000)
    assert station_browser.stn_finder_worker._data is not None

    # Add no station to the download table and assert the result.
    assert dwnld_weather_widget.station_table.get_stationlist() == []
    qtbot.mouseClick(
        dwnld_weather_widget.station_browser.btn_addSta, Qt.LeftButton)
    assert dwnld_weather_widget.station_table.get_stationlist() == []

    # Check and Add one station to the download table and assert the result.
    station_tbl = dwnld_weather_widget.station_browser.station_table
    model = station_tbl.model()
    model._checks[0] = 1
    model.dataChanged.emit(
        model.index(0, 0), model.index(model.rowCount(0), 0))

    checked_rows = station_tbl.get_checked_rows()
    assert checked_rows == [0]
    checked_sta = station_tbl.get_content4rows(checked_rows)
    assert len(checked_sta) == 1

    qtbot.mouseClick(
        dwnld_weather_widget.station_browser.btn_addSta, Qt.LeftButton)
    assert dwnld_weather_widget.station_table.get_stationlist() == checked_sta


if __name__ == "__main__":
    pytest.main([os.path.basename(__file__), '-v', '-rw'])
