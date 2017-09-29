# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 01:50:50 2017
@author: jsgosselin
"""

# ---- Standard library imports

import os
from datetime import datetime
import time

# ---- Third party imports

import pytest
from PyQt5.QtCore import Qt

# ---- Local imports

from WHAT.meteo.dwnld_weather_data import (
        DwnldWeatherWidget, RawDataDownloader, ConcatenatedDataFrame,
        QFileDialog, QMessageBox)


# Qt Test Fixtures
# --------------------------------

@pytest.fixture
def raw_downloader_bot(qtbot):
    dwnld_worker = RawDataDownloader()
    return dwnld_worker, qtbot


@pytest.fixture
def downloader_bot(qtbot):
    wxdata_downloader = DwnldWeatherWidget()
    qtbot.addWidget(wxdata_downloader)
    return wxdata_downloader, qtbot


# Test RawDataDownloader
# -------------------------------

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


# Test DwnldWeatherWidget
# -------------------------------

@pytest.mark.run(order=3)
def test_load_old_stationlist(downloader_bot):
    wxdata_downloader, qtbot = downloader_bot
    assert wxdata_downloader

    dirname = os.path.dirname(os.path.realpath(__file__))
    expected_result = [["ABERCORN", "5308", "1950", "1985",
                        "QC", "7020040", "1.25"],
                       ["AIGREMONT", "5886", "1973", "1982",
                        "QC", "7060070", "3.45"],
                       ["ALBANEL", "5887", "1922", "1991",
                        "QC", "7060080", "2.23"]]

    # Assert that tab-separated-value station list loads correctly.
    fname = os.path.join(dirname, "stationlist_tab.lst")
    station_list = wxdata_downloader.load_stationList(fname)
    assert station_list == expected_result

    # Assert that the data are stored correctly in the widget table.
    list_from_table = wxdata_downloader.station_table.get_stationlist()
    assert list_from_table == expected_result


@pytest.mark.run(order=3)
def test_load_stationlist(downloader_bot, mocker):
    wxdata_downloader, qtbot = downloader_bot
    assert wxdata_downloader

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
         "24.85"]]

    # Mock the dialog window and answer to specify the file name and type.
    dirname = os.path.join(os.getcwd(), "@ new-prô'jèt!")
    fname = os.path.join(dirname, "weather_station_list.lst")
    mocker.patch.object(QFileDialog, 'getOpenFileName',
                        return_value=(fname, '*.lst'))

    # Assert that coma-separated-value station list loads correctly. The
    # weather station list was created during "test_dwnld_weather_data.py".
    wxdata_downloader.btn_browse_staList_isClicked()

    # Assert that the data are stored correctly in the widget table.
    assert expected_result == wxdata_downloader.station_table.get_stationlist()

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

    # Select some stations in the list and delete them.
    expected_result = [
        ["MARIEVILLE", "5406", "1960", "2017", "QC", "7024627", "1.32"],
        ["IBERVILLE", "5376", "1963", "2016", "QC", "7023270", "10.86"],
        ["L'ACADIE", "10843", "1994", "2017", "QC", "702LED4", "19.73"],
        ["SABREVOIS", "5444", "1975", "2017", "QC", "7026734", "20.76"],
        ["LAPRAIRIE", "5389", "1963", "2017", "QC", "7024100", "22.57"],
        ["FARNHAM", "5358", "1917", "2017", "QC", "7022320", "22.73"],
        ["STE MADELEINE", "5501", "1979", "2016", "QC", "7027517", "24.12"]]

    for row in [1, 3, 9]:
        item = station_table.cellWidget(row, 0).layout().itemAtPosition(1, 1)
        widget = item.widget()
        qtbot.mouseClick(widget, Qt.LeftButton)
    wxdata_downloader.btn_delSta_isClicked()
    assert expected_result == station_table.get_stationlist()

    # Save station list.
    fname = os.path.join(dirname, "cleaned_station_list.lst")
    mocker.patch.object(QFileDialog, 'getSaveFileName',
                        return_value=(fname, "*.lst"))
    wxdata_downloader.btn_saveAs_staList_isClicked()
    wxdata_downloader.btn_save_staList_isClicked()

    # Add back the stations that were deleted.
    expected_result = [
        ["MARIEVILLE", "5406", "1960", "2017", "QC", "7024627", "1.32"],
        ["IBERVILLE", "5376", "1963", "2016", "QC", "7023270", "10.86"],
        ["L'ACADIE", "10843", "1994", "2017", "QC", "702LED4", "19.73"],
        ["SABREVOIS", "5444", "1975", "2017", "QC", "7026734", "20.76"],
        ["LAPRAIRIE", "5389", "1963", "2017", "QC", "7024100", "22.57"],
        ["FARNHAM", "5358", "1917", "2017", "QC", "7022320", "22.73"],
        ["STE MADELEINE", "5501", "1979", "2016", "QC", "7027517", "24.12"],
        ["ROUGEMONT", "5442", "1956", "1985", "QC", "7026700", "5.43"],
        ["MONT ST HILAIRE", "5423", "1960", "1969", "QC", "7025330", "17.49"],
        ["MONTREAL/ST-HUBERT A", "5490", "1928", "2015", "QC", "7027320",
         "24.85"]]
    wxdata_downloader.add_stations2list(original_list)
    assert expected_result == station_table.get_stationlist()

    # Clear completely the station list.
    station_table.chkbox_header.setCheckState(Qt.CheckState(True))
    assert len(station_table.get_checked_rows()) == len(expected_result)

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
    expected_result = [
        ["MARIEVILLE", "5406", "1960", "2017", "QC", "7024627", "1.32"],
        ["IBERVILLE", "5376", "1963", "2016", "QC", "7023270", "10.86"],
        ["L'ACADIE", "10843", "1994", "2017", "QC", "702LED4", "19.73"],
        ["SABREVOIS", "5444", "1975", "2017", "QC", "7026734", "20.76"],
        ["LAPRAIRIE", "5389", "1963", "2017", "QC", "7024100", "22.57"],
        ["FARNHAM", "5358", "1917", "2017", "QC", "7022320", "22.73"],
        ["STE MADELEINE", "5501", "1979", "2016", "QC", "7027517", "24.12"]]

    station_list = wxdata_downloader.load_stationList(
            os.path.join(projetpath, "cleaned_station_list.lst"))
    assert station_list == expected_result

    # Set "to year" and "from year" for all stations.
    station_table.set_fromyear(2000)
    station_table.set_toyear(2010)

    # Try starting the downloading process before selecting any station.
    mocker.patch.object(QMessageBox, 'warning', return_value=QMessageBox.Ok)
    qtbot.mouseClick(wxdata_downloader.btn_get, Qt.LeftButton)

    # Check stations "Marieville", "IBERVILLE", "L'ACADIE", "SABREVOIS",
    # "LAPRAIRIE", "FARNHAM", "STE MADELEINE".
    rows = [0, 1, 2]
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
    files = ["MARIEVILLE (7024627)_2000-2010.csv",
             "IBERVILLE (7023270)_2000-2010.csv",
             "L'ACADIE (702LED4)_2000-2010.csv"]
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


if __name__ == "__main__":                                   # pragma: no cover
    pytest.main([os.path.basename(__file__), '-v', '-rw', '--cov=WHAT'])
    # pytest.main()
