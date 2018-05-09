# -*- coding: utf-8 -*-

# Copyright © 2014-2018 GWHAT Project contributors
# https://github.com/jnsebgosselin/gwhat
#
# This file is part of GWHAT (Ground-Water Hydrograph Analysis Toolbox).
# Licensed under the terms of the GNU General Public License.


# ---- Standard library imports

import os
from datetime import datetime
import time

# ---- Third party imports

import pytest
from PyQt5.QtCore import Qt

# ---- Local imports

from gwhat.meteo.dwnld_weather_data import (
        DwnldWeatherWidget, RawDataDownloader, QFileDialog, QMessageBox)


# ---- Qt Test Fixtures


@pytest.fixture
def raw_downloader_bot(qtbot):
    dwnld_worker = RawDataDownloader()
    return dwnld_worker, qtbot


@pytest.fixture
def downloader_bot(qtbot):
    wxdata_downloader = DwnldWeatherWidget()
    qtbot.addWidget(wxdata_downloader)
    return wxdata_downloader, qtbot


# ---- Test RawDataDownloader


@pytest.mark.run(order=3)
def test_download_raw_data(raw_downloader_bot):
    dwnld_worker, qtbot = raw_downloader_bot
    now = datetime.now()

    # Set attributes of the data downloader.
    projetpath = os.path.join(os.getcwd(), "@ new-prô'jèt!")
    dwnld_worker.dirname = os.path.join(projetpath, 'Meteo', 'Raw')
    dwnld_worker.StaName = "MARIEVILLE"
    dwnld_worker.stationID = "5406"
    dwnld_worker.yr_start = str(now.year-5)
    dwnld_worker.yr_end = str(now.year)
    dwnld_worker.climateID = "7024627"

    # Download data for station Marieville
    dwnld_worker.download_data()

    # Download data again to test when raw data files are already present
    dwnld_worker.download_data()

    # Assert the stopping of the downloading process
    dwnld_worker.stop_download()
    dwnld_worker.download_data()


# ---- Test DwnldWeatherWidget


@pytest.mark.run(order=3)
def test_load_tabsep_stationlist(downloader_bot):
    wxdata_downloader, qtbot = downloader_bot
    assert wxdata_downloader

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
    fname = os.path.join(dirname, "stationlist_tabsep.lst")
    station_list = wxdata_downloader.load_stationList(fname)
    assert station_list == expected_results

    # Assert that the data are stored correctly in the widget table.
    list_from_table = wxdata_downloader.station_table.get_stationlist()
    assert list_from_table == expected_results


@pytest.mark.run(order=3)
def test_load_stationlist(downloader_bot, mocker):
    wxdata_downloader, qtbot = downloader_bot
    assert wxdata_downloader

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
    dirname = os.path.join(os.getcwd(), "@ new-prô'jèt!")
    fname = os.path.join(dirname, "weather_station_list.lst")
    mocker.patch.object(QFileDialog, 'getOpenFileName',
                        return_value=(fname, '*.lst'))

    # Assert that coma-separated-value station list loads correctly. The
    # weather station list was created during "test_dwnld_weather_data.py".
    wxdata_downloader.btn_browse_staList_isClicked()

    # Assert that the data are stored correctly in the widget table.
    station_list = wxdata_downloader.station_table.get_stationlist()
    assert expected_results == station_list

    # Test that the station list formating to html works without any error.
    station_list.format_list_in_html()

    # Try to open a station list when the file does not exist.
    wxdata_downloader.load_stationList("dummy.lst")
    assert [] == wxdata_downloader.station_table.get_stationlist()


@pytest.mark.run(order=3)
def test_delete_add_stations(downloader_bot, mocker):
    wxdata_downloader, qtbot = downloader_bot
    station_table = wxdata_downloader.station_table

    dirname = os.path.join(os.getcwd(), "@ new-prô'jèt!")
    fname = os.path.join(dirname, "weather_station_list.lst")

    # Load a station list from file.
    original_list = wxdata_downloader.load_stationList(fname)

    # Try to delete stations when no station are selected.
    wxdata_downloader.btn_delSta_isClicked()

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
    wxdata_downloader.btn_delSta_isClicked()
    assert expected_results == station_table.get_stationlist()

    # Save station list.
    fname = os.path.join(dirname, "cleaned_station_list.lst")
    mocker.patch.object(QFileDialog, 'getSaveFileName',
                        return_value=(fname, "*.lst"))
    wxdata_downloader.btn_saveAs_staList_isClicked()
    wxdata_downloader.btn_save_staList_isClicked()

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

    wxdata_downloader.add_stations2list(original_list)
    assert expected_results == station_table.get_stationlist()

    # Clear completely the station list.
    station_table.chkbox_header.setCheckState(Qt.CheckState(True))
    assert len(station_table.get_checked_rows()) == len(expected_results)

    wxdata_downloader.btn_delSta_isClicked()
    assert [] == station_table.get_stationlist()

    # Add back the stations that were deleted.
    wxdata_downloader.add_stations2list(original_list)
    assert original_list == station_table.get_stationlist()


@pytest.mark.run(order=3)
def test_download_data(downloader_bot, mocker):
    wxdata_downloader, qtbot = downloader_bot
    station_table = wxdata_downloader.station_table
    wxdata_downloader.show()

    # Set the path of the working directory.
    projetpath = os.path.join(os.getcwd(), "@ new-prô'jèt!")
    wxdata_downloader.set_workdir(projetpath)

    # Load the weather station list.
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

    station_list = wxdata_downloader.load_stationList(
            os.path.join(projetpath, "cleaned_station_list.lst"))
    assert station_list == expected_results

    # Set "to year" and "from year" for all stations.
    station_table.set_fromyear(2000)
    station_table.set_toyear(2015)

    # Try starting the downloading process before selecting any station.
    mocker.patch.object(QMessageBox, 'warning', return_value=QMessageBox.Ok)
    qtbot.mouseClick(wxdata_downloader.btn_get, Qt.LeftButton)

    # Check stations "Marieville", "IBERVILLE", "L'ACADIE", "SABREVOIS",
    # "LAPRAIRIE", "FARNHAM", "STE MADELEINE".
    rows = [3, 5, 0]
    for row in rows:
        item = station_table.cellWidget(row, 0).layout().itemAtPosition(1, 1)
        widget = item.widget()
        qtbot.mouseClick(widget, Qt.LeftButton)

    # Download the data for the selected stations.
    process_finished = wxdata_downloader.sig_download_process_ended
    with qtbot.waitSignal(process_finished, raising=True, timeout=100000):
        qtbot.mouseClick(wxdata_downloader.btn_get, Qt.LeftButton)

    # Assert that data before 2000 were not downloaded
    dirname = os.path.join(os.getcwd(), "@ new-prô'jèt!", "Meteo", "Raw")
    stanames = ["MARIEVILLE (7024627)", "IBERVILLE (7023270)",
                "L'ACADIE (702LED4)"]
    filename = "eng-daily-01011999-12311999.csv"
    for station in stanames:
        path = os.path.join(dirname, station, filename)
        assert not os.path.exists(path)

    # Assert that the concatenated datafiles were created.
    dirname = os.path.join(os.getcwd(), "@ new-prô'jèt!", "Meteo", "Input")
    files = ["MARIEVILLE (7024627)_2000-2015.csv",
             "IBERVILLE (7023270)_2000-2015.csv",
             "L'ACADIE (702LED4)_2000-2015.csv"]
    for file in files:
        assert os.path.exists(os.path.join(dirname, file))


@pytest.mark.run(order=3)
def test_merge_widget(downloader_bot, mocker):
    wxdata_downloader, qtbot = downloader_bot
    wxdata_downloader.show()

    qtbot.waitActive(wxdata_downloader, timeout=3000)

    projetpath = os.path.join(os.getcwd(), "@ new-prô'jèt!")
    wxdata_downloader.set_workdir(projetpath)

    dirname = os.path.join(projetpath, "Meteo", "Raw")
    stations = ["MARIEVILLE (7024627)", "IBERVILLE (7023270)",
                "L'ACADIE (702LED4)"]
    filenames = ["eng-daily-01012000-12312000.csv",
                 "eng-daily-01012001-12312001.csv",
                 "eng-daily-01012002-12312002.csv"]

    # Disable 'auto save merged data' option.
    wxdata_downloader.saveAuto_checkbox.setChecked(False)

    # Opens raw data files for each station.
    for station in stations:
        paths = []
        for file in filenames:
            filepath = os.path.join(dirname, station, file)
            assert os.path.exists(filepath)
            paths.append(filepath)

        mocker.patch.object(QFileDialog, 'getOpenFileNames',
                            return_value=(paths, '*.csv'))
        qtbot.mouseClick(wxdata_downloader.btn_selectRaw, Qt.LeftButton)

    # Assert that the concatenated files were not saved.
    dirname = os.path.join(os.getcwd(), "@ new-prô'jèt!", "Meteo", "Input")
    filenames = ["MARIEVILLE (7024627)_2000-2002.csv",
                 "IBERVILLE (7023270)_2000-2002.csv",
                 "L'ACADIE (702LED4)_2000-2002.csv"]

    filepaths = [os.path.join(dirname, f) for f in filenames]
    for path in filepaths:
        assert not os.path.exists(path)

    # Navigate to the first concatedated dataset and assert that
    # the navigation buttons are enabled/disabled as expected.
    qtbot.mouseClick(wxdata_downloader.btn_goFirst, Qt.LeftButton)
    qtbot.waitUntil(lambda: not wxdata_downloader.btn_goFirst.isEnabled())
    qtbot.waitUntil(lambda: not wxdata_downloader.btn_goPrevious.isEnabled())
    qtbot.waitUntil(lambda: wxdata_downloader.btn_goLast.isEnabled())
    qtbot.waitUntil(lambda: wxdata_downloader.btn_goNext.isEnabled())

    # Save the file and assert that it was created as expected
    mocker.patch.object(QFileDialog, 'getSaveFileName',
                        return_value=(filepaths[0], '*.csv'))
    qtbot.mouseClick(wxdata_downloader.btn_saveMerge, Qt.LeftButton)
    qtbot.waitUntil(lambda: os.path.exists(filepaths[0]))

    # Navigate to the last concatedated dataset and assert that
    # the navigation buttons are enabled/disabled as expected.
    qtbot.mouseClick(wxdata_downloader.btn_goLast, Qt.LeftButton)
    qtbot.waitUntil(lambda: wxdata_downloader.btn_goFirst.isEnabled())
    qtbot.waitUntil(lambda: wxdata_downloader.btn_goPrevious.isEnabled())
    qtbot.waitUntil(lambda: not wxdata_downloader.btn_goLast.isEnabled())
    qtbot.waitUntil(lambda: not wxdata_downloader.btn_goNext.isEnabled())

    # Save the file and assert that it was created as expected
    mocker.patch.object(QFileDialog, 'getSaveFileName',
                        return_value=(filepaths[-1], '*.csv'))
    qtbot.mouseClick(wxdata_downloader.btn_saveMerge, Qt.LeftButton)
    qtbot.waitUntil(lambda: os.path.exists(filepaths[-1]))

    # Navigate to the previous concatedated dataset and assert that
    # the navigation buttons are enabled/disabled as expected.
    qtbot.mouseClick(wxdata_downloader.btn_goPrevious, Qt.LeftButton)
    qtbot.waitUntil(lambda: wxdata_downloader.btn_goFirst.isEnabled())
    qtbot.waitUntil(lambda: wxdata_downloader.btn_goPrevious.isEnabled())
    qtbot.waitUntil(lambda: wxdata_downloader.btn_goLast.isEnabled())
    qtbot.waitUntil(lambda: wxdata_downloader.btn_goNext.isEnabled())

    # Save the file and assert that it was created as expected
    mocker.patch.object(QFileDialog, 'getSaveFileName',
                        return_value=(filepaths[-2], '*.csv'))
    qtbot.mouseClick(wxdata_downloader.btn_saveMerge, Qt.LeftButton)
    qtbot.waitUntil(lambda: os.path.exists(filepaths[-2]))

    # Navigate to the next concatedated dataset and assert that
    # the navigation buttons are enabled/disabled as expected.
    qtbot.mouseClick(wxdata_downloader.btn_goNext, Qt.LeftButton)
    qtbot.waitUntil(lambda: wxdata_downloader.btn_goFirst.isEnabled())
    qtbot.waitUntil(lambda: wxdata_downloader.btn_goPrevious.isEnabled())
    qtbot.waitUntil(lambda: not wxdata_downloader.btn_goLast.isEnabled())
    qtbot.waitUntil(lambda: not wxdata_downloader.btn_goNext.isEnabled())


# ---- Test WeatherStationFinder

@pytest.mark.run(order=3)
def test_search_weather_data(downloader_bot, mocker):
    """
    Test that the Climate Station Browser is initialise correctly from
    the Weather Data Downloader widget and that the stations from the
    browser are added correctly to the table of the downloader.
    """
    wxdata_downloader, qtbot = downloader_bot
    assert wxdata_downloader.station_browser is None
    wxdata_downloader.set_station_browser_latlon((45.40, 73.15))

    # Open the Climate station browser.
    wxdata_downloader.btn_search4station_isclicked()
    assert wxdata_downloader.station_browser is not None
    assert wxdata_downloader.station_browser.lat == 45.40
    assert wxdata_downloader.station_browser.lon == 73.15

    # Assert that the database was loaded correctly in the browser.
    station_browser = wxdata_downloader.station_browser
    qtbot.addWidget(station_browser)

    qtbot.waitSignal(station_browser.stn_finder_thread.started)
    qtbot.waitSignal(station_browser.stn_finder_worker.sig_load_database_finished)
    qtbot.waitSignal(station_browser.stn_finder_thread.finished)
    qtbot.waitUntil(lambda: not station_browser.stn_finder_thread.isRunning(),
                    timeout=60*1000)
    assert station_browser.stn_finder_worker._data is not None

    # Add no station to the download table and assert the result.
    assert wxdata_downloader.station_table.get_stationlist() == []
    qtbot.mouseClick(wxdata_downloader.station_browser.btn_addSta, Qt.LeftButton)
    assert wxdata_downloader.station_table.get_stationlist() == []

    # Check and Add one station to the download table and assert the result.
    station_tbl = wxdata_downloader.station_browser.station_table
    model = station_tbl.model()
    model._checks[0] = 1
    model.dataChanged.emit(model.index(0, 0),
                           model.index(model.rowCount(0), 0))

    checked_rows = station_tbl.get_checked_rows()
    assert checked_rows == [0]
    checked_sta = station_tbl.get_content4rows(checked_rows)
    assert len(checked_sta) == 1

    qtbot.mouseClick(wxdata_downloader.station_browser.btn_addSta, Qt.LeftButton)
    assert wxdata_downloader.station_table.get_stationlist() == checked_sta


if __name__ == "__main__":
    pytest.main([os.path.basename(__file__), '-v', '-rw'])
