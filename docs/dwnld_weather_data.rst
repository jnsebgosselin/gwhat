Downloading Daily Weather Data
==============================

This document shows how to search, download, and format daily climate data from the `Canadian Daily Climate Database`_ (CDCD) using the download weather data tool of GWHAT available under the tab ``Download Weather`` shown in :numref:`gif_dwnld_weather`.

.. _gif_dwnld_weather:
.. figure:: img/download_weather.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
    
    Presentation of the download weather data tool of GWHAT available under the tab ``Download Weather``.

Downloading weather data
-----------------------------------------------

Daily weather data can be downloaded automatically for one or more stations at a time simply by selecting them in the table shown in :numref:`dwnld_weather_annoted` and by clicking on the |downward_arrow| icon in the toolbar.

Climate stations can be added to the table either by selecting an existing list of stations from a file by clicking on the |open_file| icon or by using the `climate stations browser`_ by clicking on the |magnifying_glass| icon (see :numref:`cdcd_browser`). Climate stations can be removed from the table by selecting them and clicking on the |eraser| icon. The list of stations can be exported to a `comma-separated values`_ (csv) file by clicking on the |save| icon, so that it can be directly loaded in successive sessions of GWHAT.

.. _dwnld_weather_annoted:
.. figure:: img/dwnld_weather_annoted.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
    
    Tool to download and format daily weather data from the online
    CDCD_ (Canadian Daily Climate Database).

When clicking on the |downward_arrow| icon, daily weather data are downloaded between the ``From Year`` and ``To Year`` values specified for each selected station and the results are saved as a csv files in the Raw folder of the current project. The downloading process can be stopped at any time by clicking on the |stop| icon that appears in the toolbar as soon as a downloading task is started. Weather data for a given station will not be downloaded for the years for which a data file already exist in the Raw folder. Finally, the ``From Year`` and ``To Year`` values can be set individually
for each station or for all stations at once as shown in :numref:`set_all_fromyear_toyear`.

.. _set_all_fromyear_toyear:
.. figure:: img/set_fromyear_toyear_annoted.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
    
    Set the ``From Year`` and ``To Year`` values for all stations at once.

.. _climate stations browser: `Searching for weather data`_

Searching for weather data
-----------------------------------------------

The climate station browser shown in :numref:`cdcd_browser` provides a graphical interface to the CDCD_, which contains daily data for air temperature and precipitation dating back to 1840 to the present for more than 8000 stations distributed across Canada. The list of stations can be filtered in the browser by proximity, province, or/and the number and the range of years for which data are available at each station. For example, :numref:`cdcd_browser` shows all stations with at least 10 years of data available between 1960 and 2017 that are located less than 25 km kilometres away from the specified lat/lon coordinates.

Stations can be added to the table displayed in the ``Download Weather`` tab by selecting them in the browser and clicking on the button |add_to_list|. Alternatively, the selected stations can also be exported from the browser to an Excel or csv file by clicking on the button |save|.

.. _cdcd_browser:
.. figure:: img/stations_browser.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
    
    Presentation of the climate stations browser.

Concatenating the weather datafiles
----------------------------------------------------------
By default, GWHAT automatically formats and save the data in a csv file as soon as they have been successfully downloaded for a given station. Only the data related to air temperature (mean, max and min) and total precipitation are kept and days with missing data in the dataset are filled with a NaN (not a number) value.

The automatic saving of the formatted data series can be disabled by unchecking the Automatically save concatenated data option. From the right side-panel, it is then possible to navigate through the datasets that were formatted over the course of a given session using the
left-right arrows and save any dataset manually by clicking on the save button.




Finally,
information on the number of days with missing data for each meteorological variable are displayed in the right side-panel. Alternatively, it is possible to open and format previously downloaded weather data files by clicking on the Load button in the right side-panel and selecting the desired files from the dialog window that will open. By default, WHAT will automatically save the formatted data in a single csv file in the Input folder (see section 2.4).






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

.. |stop| image:: img/icon_stop.*
                      :width: 1em
                      :height: 1em
                      :alt: stop
