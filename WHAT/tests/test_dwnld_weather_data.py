# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 01:50:50 2017
@author: jsgosselin
"""

# Standard library imports
import sys
import os
from datetime import datetime

# Third party imports
import pytest
from PyQt5.QtCore import Qt

# Local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from meteo.dwnld_weather_data import DwnldWeatherWidget, RawDataDownloader


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

    # Download data for station Marieville
    projetpath = os.path.join(os.getcwd(), "@ new-prô'jèt!")
    dwnld_worker.dirname = os.path.join(projetpath, 'Meteo', 'Raw')
    dwnld_worker.StaName = "MARIEVILLE"
    dwnld_worker.stationID = "5406"
    dwnld_worker.yr_start = str(now.year-5)
    dwnld_worker.yr_end = str(now.year)
    dwnld_worker.climateID = "7024627"

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
    list_from_table = wxdata_downloader.station_table.get_staList()
    assert list_from_table == expected_result


@pytest.mark.run(order=3)
def test_load_stationlist(downloader_bot):
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
         "24.85"]
        ]

    # Assert that coma-separated-value station list loads correctly. The
    # weather station list was created during "test_dwnld_weather_data.py".
    fname = os.path.join(os.getcwd(), "@ new-prô'jèt!",
                         "weather_station_list.lst")
    station_list = wxdata_downloader.load_stationList(fname)
    assert station_list == expected_result

    # Assert that the data are stored correctly in the widget table.
    list_from_table = wxdata_downloader.station_table.get_staList()
    assert list_from_table == expected_result


@pytest.mark.run(order=3)
def test_download_data(downloader_bot):
    wxdata_downloader, qtbot = downloader_bot
    table_widget = wxdata_downloader.station_table
    wxdata_downloader.show()
    assert wxdata_downloader

    # Set the path of the working directory.
    projetpath = os.path.join(os.getcwd(), "@ new-prô'jèt!")
    wxdata_downloader.set_workdir(projetpath)

    # Load the weather station list.
    wxdata_downloader.load_stationList(
            os.path.join(projetpath, "weather_station_list.lst"))

    # Set "to year" and "from year" for all stations.
    table_widget.set_fromyear(2000)
    table_widget.set_toyear(2017)

    # Check stations "Marieville", "IBERVILLE", "L'ACADIE", "SABREVOIS",
    # "LAPRAIRIE", "FARNHAM", "STE MADELEINE".

    rows = [0, 2]  # [0, 2, 4, 5, 6, 7, 8]
    for row in rows:
        item = table_widget.cellWidget(row, 0).layout().itemAtPosition(1, 1)
        widget = item.widget()
        qtbot.mouseClick(widget, Qt.LeftButton)

    # Download the data for the selected stations.
    process_finished = wxdata_downloader.sig_download_process_ended
    with qtbot.waitSignal(process_finished, raising=True, timeout=100000):
        qtbot.mouseClick(wxdata_downloader.btn_get, Qt.LeftButton)


if __name__ == "__main__":                                   # pragma: no cover
    pytest.main([os.path.basename(__file__)])
    # pytest.main()
