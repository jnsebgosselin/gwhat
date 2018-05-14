.. _chap_importing_data:

Data Management in GWHAT
===============================================

.. _sec_importing_data:

Importing Data
-----------------------------------------------

Time series of water level and weather data must first be imported in GWHAT
before groundwater hydrographs can be plotted or analyzed.
The format in which the data must be saved, so that they can be imported
successfully, is described in :numref:`input_datafile_format`.

Importing water level and weather datasets in GWHAT is done by clicking on one of
the |icon_open_project| icons that are located in the :guilabel:`Water Level Dataset` 
or in the :guilabel:`Weather Dataset` section of the tabs :guilabel:`Plot Hydrograph` 
or :guilabel:`Analyze Hydrograph` (see :numref:`scs_datamanager_panel`).
This opens a window named :guilabel:`Import Dataset` (shown in :numref:`scs_import_data_dialog_windows`),
where a valid water level or weather data file can be imported.

.. _scs_datamanager_panel:
.. figure:: img/scs/datamanager_panel.*
    :align: center
    :width: 100%
    :alt: datamanager panel screenshot
    :figclass: align-center

    Presentation of the panel to manage water levels and weather datasets.

Selecting a water levels or weather data file from the :guilabel:`Import Dataset` window
(shown in :numref:`scs_import_data_dialog_windows`) is done by clicking on the |icon_open_file| icon.
After a valid data file has been selected, the information relative to the climate 
or piezometric station is displayed in the section :guilabel:`Dataset info` of
the :guilabel:`Import Dataset` window.
This information is read from the header of the selected data file. Missing or
wrong info can be entered or corrected from :guilabel:`Import Dataset` window
before importing the dataset by clicking on the button :guilabel:`Import`. 
The dataset is then added to the :term:`project file` and is
referenced in the list of imported water level or weather datasets
(see :numref:`scs_datamanager_panel`) by the name that was entered in the
field :guilabel:`Dataset name`.

.. _scs_import_data_dialog_windows:
.. figure:: img/scs/import_data_dialog_windows.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center

    Presentation of the :guilabel:`Import Dataset` windows to import
    water levels (to the left) and weather (to the right) data files.
    
.. important:: A valid dataset name is at least one charater long and
    can't contain any of the following special characters:
    |_| |_| \\ |_| \/ |_| \: |_| \* |_| \? |_| \" |_| \< |_| \> |_| \|

.. _input_datafile_format:

Input data files format
-----------------------------------------------

This section describes the format in which daily weather and water level datasets
must be saved so that they can be imported in GWHAT as described in
:numref:`sec_importing_data`.
GWHAT includes a tool to download and automatically save daily weather
data from the `Canadian Daily Climate Database`_ [#url_cddc]_ in the
appropriate format (see :numref:`chap_dwnld_weather`). Moreover,
GWHAT provides an automated, robust, and efficient tool to fill the gaps in
daily weather data records that is presented in :numref:`chap_gapfilling_weather_data`.
There is currently no tool in GWHAT to automatically download and format
groundwater levels time series. However, these data can be downloaded
free of charge for the province of Quebec from the `Groundwater Monitoring Network
of Quebec`_ [#url_rsesq]_  and for several Canadian provinces from the
`Groundwater Information Network (GIN)`_ [#url_gin]_.

.. _daily_weather_datafile_format:

Weather data files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

GWHAT can read weather data saved in comma-separated values (:file:`csv`) or
tab-separated values (:file:`tsv`) text files with UTF-8 encoding. An example
of correctly formatted data file is presented in :numref:`weather_datafile_example`.

The file header contains information about the station name, province, latitude, longitude,
elevation and climate identifier. The dataset is composed of daily maximum, minimum,
and mean air temperature in °C and total precipitation in mm.
:abbr:`nan (not a number)` values must be entered where data are missing.
Data must also be in chronological order, but do not need to be continuous over time.
That is, missing blocks of data (e.g., several days, months or years) can be completely
omitted in the time series.

.. _weather_datafile_example:
.. figure:: img/files/weather_datafile_example.*
    :align: center
    :width: 85%
    :alt: weather_datafile_example.png
    :figclass: align-center

    Example of a correctly formatted weather data file.

.. note:: Preferably, the gaps in the daily weather records must have been
          filled before importing them. Otherwise, a value of 0 is assumed
          for days where precipitation is missing and the missing values for
          air temperature are evaluated by linear interpolation. GWHAT provides
          an automated, robust, and efficient tool to fill the gaps in
          daily weather data records that is presented in :numref:`chap_gapfilling_weather_data`.

Water level data files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

GWHAT can read water level data from either coma-separated text files (:file:`csv`)
encoded in UTF-8 or from an Excel spreadsheet (:file:`xls` or :file:`xlsx`).
An example of correctly formatted water level data file is presented in
:numref:`water_level_datafile_example`. This file is also available in the
folder of the project example that is distributed with GWHAT 
(see :numref:`sec_installing_on_windows`).

The file header contains information about the well name, identifier, province,
latitude, longitude, and elevation. The data must be saved in chronological order.
The first column of the data must contain the time in excel numeric format. 
The second column must contain the water level, given in metres below the 
ground surface. The third and fourth columns correspond, respectively, to the 
barometric pressure and the Earth tides.
The use of barometric pressure and the Earth tides data will be discussed in
more details in :numref:`chap_computing_the_brf`.


.. _water_level_datafile_example:
.. figure:: img/files/water_level_datafile.*
    :align: center
    :width: 85%
    :alt: water_level_datafile.png
    :figclass: align-center

    Example of a correctly formatted water level data file. This file is
    available in the folder of the project example that is distributed with
    GWHAT.

.. important:: Water levels must be in metres below the ground surface.
    The name of the labels of the header and of the data columns 
    (e.g., Well Name, Well ID, Date) must be respected for the program
    to read the content of the file correctly.

.. _sec_exporting_data:

Exporting Data
-----------------------------------------------

It is possible to export the currently selected weather dataset to a coma-separated 
text file (with UTF-8 encoding) or an Excel spreadsheet (:file:`xls` or :file:`xlsx`)
by clicking on the |icon_export_data| icon as shown in :numref:`export_weather_data`.
The dataset can be exported in a daily, monthly or yearly format. Note that 
the export of water level datasets is currently not available in GWHAT.

.. _export_weather_data:
.. figure:: img/scs/export_weather_data.*
    :align: center
    :width: 100%
    :alt: export_weather_data.png
    :figclass: align-center

    Tool to export weather datasets in a daily, monthly, or yearly format to
    a :file:`csv`, :file:`xls`, or :file:`xlsx` file.


.. |icon_export_data| image:: img/icon/export-data.*
                      :width: 1em
                      :height: 1em
                      :alt: export-data

.. |icon_open_project| image:: img/icon/open_project.*
                      :width: 1em
                      :height: 1em
                      :alt: folder

.. |icon_open_file| image:: img/icon/icon_open_file.*
                      :width: 1em
                      :height: 1em
                      :alt: folder

.. _Canadian Daily Climate Database: www.climate.weather.gc.ca
.. _Groundwater Monitoring Network of Quebec: http://www.mddelcc.gouv.qc.ca/eau/piezo/
.. _Groundwater Information Network (GIN): http://gin.gw-info.net/service/api_ngwds:gin2/en/gin.html

.. rubric:: Footnotes
.. [#url_cddc] http://climate.weather.gc.ca/
.. [#url_rsesq] http://www.mddelcc.gouv.qc.ca/eau/piezo/
.. [#url_gin] http://gin.gw-info.net/service/api_ngwds:gin2/en/gin.html

.. |_| unicode:: 0020
