Downloading Daily Weather Data
==============================

This document will show you how to search and download daily climate data
from the CDCD_ (Canadian Daily Climate Database) using the ``Download Weather``
tool of GWHAT as shown in :numref:`gif_dwnld_weather`.

.. _gif_dwnld_weather:
.. figure:: img/download_weather.*
    :width: 650px
    :align: center
    :alt: alternate text
    :figclass: align-center
    
    
.. _CDCD: www.climate.weather.gc.ca

Searching for weather stations
-----------------------------------------------

Before data can be downloaded from the CDCD_, climate stations must be 
added to the table of the `Download Weather` tool. To do so, click on the 
``magnifying glass`` icon located on the toolbar to open a browser of the 
online CDCD_ (:numref:`cdcd_browser`). The CDCD_ contains daily data for air
temperature and precipitation for about 8450 stations distributed across Canada.

.. _cdcd_browser:
.. figure:: img/scs_search_weather_stations.png
    :width: 600px
    :align: center
    :alt: alternate text
    :figclass: align-center
    
    Online CDCD_ (Canadian Daily Climate Database) browser.

The left panel of the browser allow you to filter the list of climate stations
by proximity, province, or/and the number and the range of
years for which data are available. For example, :numref:`cdcd_browser` shows
all stations less than 25 km kilometres away from the specified location 
with at least 3 years of data available between 1980 and 2017.

Select the stations for which you want to download climate data by clicking on
their respective checkbox and click on the button ``Add`` to add them to the
table of the `Download Weather` tab.

You can also export the list of selected stations to an Excel or CSV file by clicking
on the button ``Save``.

Downloading the weather data
-----------------------------------------------

GWHAT allows to search for stations interactively using location coordinates, download the available data for the selected weather stations, and automatically organize the data in a format compatible with GWHAT. These features are available in the Download Data tab shown in Fig. 3.1. This tab consists of a toolbar located at the top of the interface, an area where are displayed the current list of weather stations for which data can be downloaded, and a side-panel to the right where can be manage the formatting of the weather data files that were downloaded for each year individually.



Concatenating the weather datafiles
----------------------------------------------------------
By default, when raw datafiles are downloaded from the CDCD_
