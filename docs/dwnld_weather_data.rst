Downloading Daily Weather Data
==============================

This document shows how to search, download, and format daily climate data
from the `Canadian Daily Climate Database`_ (CDCD) using the `download weather 
data` tool of GWHAT available under the tab ``Download Weather`` shown in 
:numref:`gif_dwnld_weather`.

.. _gif_dwnld_weather:
.. figure:: img/download_weather.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
    
    Presentation of the `download weather data` tool of GWHAT available under
    the tab in GWHAT to search 
    and download daily climate data from the CDCD_ (Canadian Daily Climate
    Database).

.. _Canadian Daily Climate Database: www.climate.weather.gc.ca
.. _CDCD: _Canadian Daily Climate Database

Searching for weather stations
-----------------------------------------------

Before any weather data can be downloaded with GWHAT, a list of stations 
must first be added to the table displayed in the ``Download Weather`` tab. 
This is done either by opening an existing list of stations from a file by
clicking on the ``open document`` icon or by using the 
`climate stations browser`_ that is opened by clicking on the
``magnifying glass`` icon (see :numref:`cdcd_browser`).

.. _cdcd_browser:
.. figure:: img/stations_browser.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
    
    Presentation of the climate stations browser.

The climate station browser provides a graphical interface to the CDCD_, which
contains daily data for air temperature and precipitation dating back to 
1840 to the present for more than 8000 stations distributed across Canada.
The list of stations can be filtered in the browser by proximity, province,
or/and the number and the range of years for which data are available at each
station. For example, :numref:`cdcd_browser` shows all stations with at least
10 years of data available between 1960 and 2017 that are located less than
25 km kilometres away from the specified lat/lon coordinates

Stations can be added to the table displayed in the ``Download Weather`` tab by
selecting them in the browser and clicking on the button ``Add``.

Alternatively, the selected stations can also be exported to an Excel or CSV
file by clicking on the button ``Save``.

Downloading the weather data
-----------------------------------------------



It is possible to remove any weather station from the current list by 
selecting them and clicking on the toolbar `eraser` icon.

The station list can be saved by clicking on the toolbar floppy disk icon.

Daily weather data can be downloaded from the online CDCD by selecting the desired stations from the
list displayed in the Download Data tab and clicking on the toolbar icon with the encircled downward
arrow . Data will be downloaded for the years specified for each selected station and the results will be
saved automatically as a csv (comma-separated values) file in the Raw folder (see section 2.4). Weather
data for a given station won’t be downloaded for the years for which a data file already exist in the Raw
folder. Detailed information about the downloading process are printed in the console area located at the
bottom of the interface (see section 1.4). The downloading process can be stopped at any time by clicking
on the stop icon that appears in the toolbar as soon a downloading task is started.

Daily climate data can be downloaded automatically for all the selected weather
stations by clicking on the ``downward arrow`` button in the toolbar of the
`download weather data` tool (see :numref:`dwnld_weather_annoted`).

.. _dwnld_weather_annoted:
.. figure:: img/dwnld_weather_annoted.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
    
    Tool to download and format daily weather data from the online
    CDCD_ (Canadian Daily Climate Database).


.. _climate stations browser: `Searching for weather stations`_

Concatenating the weather datafiles
----------------------------------------------------------
By default, when raw datafiles are downloaded from the CDCD_

WHAT automatically formats the data as soon as they have been successfully downloaded for a given
weather station. To do this, data from each annual file are put together end to end in chronological
order. Only the data related to air temperature (mean, max and min) and total precipitation are kept.
In addition, days with missing data in the dataset are filled with a NaN (not a number) value. Finally,
information on the number of days with missing data for each meteorological variable are displayed in
the right side-panel. Alternatively, it is possible to open and format previously downloaded weather data
files by clicking on the Load button in the right side-panel and selecting the desired files from the
dialog window that will open.
By default, WHAT will automatically save the formatted data in a single tsv (tabular-separated values)
file in the Input folder (see section 2.4). The automatic saving of the formatted data series can be disabled
by unchecking the Automatically save concatenated data option. From the right side-panel, it is then
possible to navigate through the datasets that were formatted over the course of a given session using the
left-right arrows and save any dataset manually by clicking on the save button.
