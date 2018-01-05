.. _chap_dwnld_weather:

Downloading Daily Weather Data
===============================================

This document shows how to search, download, and format daily climate data
from the `Canadian Daily Climate Database`_ (CDCD) [#url_cddc]_ using the download
weather data tool of GWHAT available under the tab :guilabel:`Download Weather`
shown in :numref:`gif_dwnld_weather`.

.. _gif_dwnld_weather:
.. figure:: img/download_weather.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center

    Presentation of the download weather data tool of GWHAT available under
    the :guilabel:`Download Weather` tab.

.. _sec_download_weather_data:

Downloading weather data
-----------------------------------------------

Daily weather data can be downloaded automatically for one or more stations at
a time simply by selecting them in the table shown in :numref:`dwnld_weather_annoted`
and by clicking on the |downward_arrow| icon in the toolbar.

Climate stations can be added to the table either by selecting an existing list
of stations from a file by clicking on the |open_file| icon or by using the
:guilabel:`Weather Stations Browser` (see :numref:`cdcd_browser`) that is
accessible by clicking on the |magnifying_glass| icon.
Climate stations can be removed from the table by selecting them and clicking
on the |eraser| icon. The list of stations can be exported to a :abbr:`csv (comma-separated values)`
file by clicking on the |save| icon, so that it can be directly loaded in successive sessions of GWHAT.

When clicking on the |downward_arrow| icon, daily weather data are downloaded
between the :guilabel:`From Year` and :guilabel:`To Year` values specified for each selected
station and the results are saved as csv files in the Raw folder of the current
project. The downloading process can be stopped at any time by clicking on the |stop|
icon that appears in the toolbar as soon as a downloading task is started.
Weather data for a given station will not be downloaded for the years for which
a data file already exist in the Raw folder. Finally, the :guilabel:`From Year` and
:guilabel:`To Year` values can be set individually for each station or for all stations
at once using the |set_fromyear| and |set_toyear| icons as shown in
:numref:`set_all_fromyear_toyear`.

.. _dwnld_weather_annoted:
.. figure:: img/dwnld_weather_annoted.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center

    Tool to download and format daily weather data from the online
    CDCD_ (Canadian Daily Climate Database).

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

The :guilabel:Weather Stations Browser shown in :numref:`cdcd_browser` provides a graphical
interface to the CDCD_, which contains daily data for air temperature and precipitation
dating back to 1840 to the present for more than 8000 stations distributed across Canada.
The list of stations can be filtered in the browser by proximity, province, or/and the
number and the range of years for which data are available at each station.
For example, :numref:`cdcd_browser` shows all stations with at least 10 years
of available data between 1960 and 2017 that are located less than 25 kilometres
away from the specified lat/lon coordinates.

Stations can be added to the table displayed in the :guilabel:`Download Weather` tab
by selecting them in the browser and clicking on the button |add_to_list| `Add`.
Alternatively, the selected stations can also be exported from the browser to an
Excel or :abbr:`csv (comma-separated values)` file by clicking on the button |save| `Save`.

.. _cdcd_browser:
.. figure:: img/scs_stations_browser_annoted.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center

    Presentation of the :guilabel:Weather Stations Browser.

.. _sec_weather_datafiles_format:

Formatting the weather datafiles
----------------------------------------------------------

After all data have been successfully downloaded for a given weather station,
GWHAT automatically displays information about the number
and the proportion of days with missing data in the the right-side panel of
the :guilabel:`Download Weather` tab (see :numref:`format_weather_panel`).
It is possible to navigate through the information of all the datasets that were
downloaded over the course of a given session by using the left-right arrows located
at the bottom of the panel.

By default, GWHAT saves the formatted data automatically in a single
csv (comma-separated values) file in the :file:`Input` folder of the current project folder.
Details about the format of the csv files in which the data are saved are provided
in :numref:`daily_weather_datafile_format`.
It is possible to prevent GWHAT from automatically saving the formatted data
by unchecking the :guilabel:`Automatically save formatted weather data` option
located at the bottom of the formating tool. The formatted data can be manually
saved afterwards by clicking on the button |save| `Save`.

Moreover, previously downloaded raw weather data files, which are saved automatically
in the :file:`Raw` folder, can be opened and formated at any times by
clicking on the button |open_file| `Select` at the top of the panel. The formatted
data can then be saved manually by clicking on the button |save| `Save` or automatically
if the :guilabel:`Automatically save formatted weather data` option is checked.


.. _format_weather_panel:
.. figure:: img/scs/annotations_concatenate_panel.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center

    Presentation of the tool to format raw weather datafiles located in the right
    panel of the :guilabel:`Download Weather` tab.


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

.. |open_file| image:: img/icon/icon_open_file.*
                      :width: 1em
                      :height: 1em
                      :alt: open file

.. |save| image:: img/icon_save.*
                      :width: 1em
                      :height: 1em
                      :alt: save

.. |set_fromyear| image:: img/icon_set_fromyear.*
                      :width: 1em
                      :height: 1em
                      :alt: set From Year

.. |set_toyear| image:: img/icon_set_toyear.*
                      :width: 1em
                      :height: 1em
                      :alt: set To Year


.. |stop| image:: img/icon_stop.*
                      :width: 1em
                      :height: 1em
                      :alt: stop


.. rubric:: Footnotes
.. [#url_cddc] http://climate.weather.gc.ca/
