Downloading Daily Weather Data
==============================

This document will show you how to search and download daily climate data
from the CDCD_ (Canadian Daily Climate Database) using GWHAT.

.. _CDCD: www.climate.weather.gc.ca

Searching for weather stations
-----------------------------------------------

Before you can download daily climate data, you need first to select the
relevant climate stations on the CDCD_ and add it to the table in the
`Download Weather` tab.

To do this, click on the magnifying glass icon located on the toolbar of the
`Download Weather` to open a browser to the online CDCD_
(:numref:`cdcd_browser`). The CDCD_ contains daily data for air temperature
and precipitation dating back to 1840 to the present for about 8450 stations
distributed across Canada. 

.. _cdcd_browser:
.. figure:: img/scs_search_weather_stations.png
    :width: 600px
    :align: center
    :alt: alternate text
    :figclass: align-center
    Browser to the online CDCD_ (Canadian Daily Climate Database).

The left panel of the browser allow you to filter the list of available
climate stations by proximity, province, or/and the number and the range of
years for which data are available.

Click on the button ``Save`` to export the list of visible station in the table
to a Excel or CSV file.

Select the stations for which you want to download climate data by clicking on
their respective checkbox and click on the button ``Add``. This will append the
selected stations to the table of the `Download Weather` tab, where the data
for each station can be downloaded automatically.

Downloading the weather data
-----------------------------------------------

GWHAT allows to search for stations interactively using location coordinates, download the available data for the selected weather stations, and automatically organize the data in a format compatible with GWHAT. These features are available in the Download Data tab shown in Fig. 3.1. This tab consists of a toolbar located at the top of the interface, an area where are displayed the current list of weather stations for which data can be downloaded, and a side-panel to the right where can be manage the formatting of the weather data files that were downloaded for each year individually.


.. figure:: img/scs_download_weather.png
    :width: 300px
    :align: center
    :alt: alternate text
    :figclass: align-center

Concatenating the weather datafiles
----------------------------------------------------------
By default, when raw datafiles are downloaded from the CDCD_
