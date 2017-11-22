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

Creating a list of climate stations
-----------------------------------------------

Before any weather data can be downloaded with GWHAT, a list of stations 
must first be added to the table displayed in the ``Download Weather`` tab. 
This is done either by opening an existing list of stations from a file by
clicking on the |open_file| icon or by using the 
`climate stations browser`_ that can be opened by clicking on the
|magnifying_glass| icon (see :numref:`cdcd_browser`).

Climate stations can be removed from the current list of stations by 
selecting them and clicking on the toolbar |eraser| icon. Also, the list of
stations can be exported to a csv file by clicking on the |save| icon
This list can then be directly loaded in successive session of GWHAT as
explained in :ref:`Searching for weather stations`

Searching for weather stations
-----------------------------------------------

The climate station browser shown in :numref:`cdcd_browser` provides a
graphical interface to the CDCD_, which contains daily data for air temperature
and precipitation dating back to 1840 to the present for more than 8000
stations distributed across Canada. The list of stations can be filtered in
the browser by proximity, province, or/and the number and the range of years
for which data are available at each station. For example,
:numref:`cdcd_browser` shows all stations with at least
10 years of data available between 1960 and 2017 that are located less than
25 km kilometres away from the specified lat/lon coordinates

.. _cdcd_browser:
.. figure:: img/stations_browser.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
    
    Presentation of the climate stations browser.
    
Stations can be added to the table displayed in the ``Download Weather`` tab by
selecting them in the browser and clicking on the button |add_to_list|. 
Alternatively, the selected stations can also be exported from the browser
to an Excel or `comma-separated values`_ (csv) file by clicking on the
button |save|.

Downloading the weather data
-----------------------------------------------

Once one or more stations have been added to the ``Download Weather`` table, 
daily weather data can be downloaded by selecting the desired stations and
clicking on the |downward_arrow| icon on the toolbar 
(see :numref:`dwnld_weather_annoted`).

.. _dwnld_weather_annoted:
.. figure:: img/dwnld_weather_annoted.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
    
    Tool to download and format daily weather data from the online
    CDCD_ (Canadian Daily Climate Database).
    
Daily weather data will be downloaded between the ``From Year`` and ``To Year``
values specified for each selected station and the results will be saved
automatically as a csv file in the Raw folder of 
the current project. The downloading process can be stopped at any time by
clicking on the ``stop`` button that appears in the toolbar as soon a
downloading task is started. Weather data for a given station will not be
downloaded for the years for which a data file already exist in the Raw folder. 
Finally, the ``From Year`` and ``To Year`` values can be set individually
for each station or for all stations at once as shown in
:numref:`set_all_fromyear_toyear`.

.. _set_all_fromyear_toyear:
.. figure:: img/set_fromyear_toyear_annoted.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
    
    Set the ``From Year`` and ``To Year`` values for all stations at once.

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

.. _comma-separated values: https://en.wikipedia.org/wiki/Comma-separated_values
.. _Canadian Daily Climate Database: www.climate.weather.gc.ca
.. _CDCD: _Canadian Daily Climate Database

.. |add_to_list| image:: img/icon_add_to_list.*
                      :width: 1em
                      :height: 1em
                      :alt: Add

.. |downward_arrow| image:: img/icon_download.*
                    :width: 1em
                    :height: 1em
                    :alt: downward arrow

.. |eraser| image:: img/icon_erase.*
                      :width: 1em
                      :height: 1em
                      :alt: eraser

.. |magnifying_glass| image:: img/icon_search.*
                      :width: 1em
                      :height: 1em
                      :alt: magnifying glass

.. |open_file| image:: img/icon_open_file.*
                      :width: 1em
                      :height: 1em
                      :alt: open file

.. |save| image:: img/icon_save.*
                      :width: 1em
                      :height: 1em
                      :alt: save
