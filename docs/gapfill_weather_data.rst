Gapfilling Daily Weather Data
===============================================

GWHAT provides an automated, robust, and efficient method to fill the gaps in
daily weather data records. In addition, uncertainties of the estimated 
missing values can be automatically assessed with a cross-validation resampling technique.
This document shows how to fill the gaps in daily weather
records using the gapfilling weather data tool of GWHAT available under the tab
:guilabel:`Gapfill Weather` shown in :numref:`gapfill_weather_demo`.

.. _gapfill_weather_demo:
.. figure:: img/gapfill_weather_demo.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
    
    Presentation of the `gapfill weather data` tool of GWHAT available under
    the tab :guilabel:`Gapfill Weather`.

.. _sec_loading_weather_data:

Loading the weather data files
-----------------------------------------------

When starting GWHAT or when a new project is selected, the content of the
:term:`Input folder` is automatically scanned for valid weather data files that
respect the format described in :numref:`sec_weather_datafiles_format`.

The restuls are displayed in a list located under :guilabel:`Fill data for weather station` 
section as as shown in :numref:`scs_gapfill_weather_annoted`.
The list of weather datasets can be refreshed at any times by clicking on the 
|icon_refresh| icon. This needs to be done if new datafiles are added or deleted manually
from the :file:`Input` folder, outside of GWHAT.
Datasets can be removed from the list by selecting them and clicking on the |icon_clear| icon.
Doing so also removes the corresponding data file from the :file:`Input` folder.

A summary of the number of days with missing data for each dataset is also
produced and displayed under :guilabel:`Missing Data Overview` tab of the display area.

.. _scs_gapfill_weather_annoted:
.. figure:: img/scs_gapfill_weather_annoted.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
    
    Presentation of the `gapfill weather data` tool of GWHAT available under
    the tab :guilabel:`Gapfill Weather`.


Merging two weather data files
-----------------------------------------------

Sometimes, more than one daily weather dataset is available at a same location.
Often, this happens when a new climate station is installed in a location
where a station was operating in the past, but was later removed (due to
governmental budget cuts for example). This results in two datasets for which
the data are mutually exclusive in time. In that case, it is beneficial to
merge these two mutually exclusive datasets into a single dataset that spans over
a longer period of time. This can be done mannually by manipulating the files
located in the :file:`Input` folder or by using the tool available in GWHAT by clicking
on the |icon_merge_data| icon (see :numref:`merge_weather`).

.. _merge_weather:
.. figure:: img/scs_merge_weather_data_annoted.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
    
    Presentation of the tool to merge two daily weather records together.
    
.. note:: Datasets that are mutually exclusive in time can results in problems when filling the gaps
          in daily weather records. So it is always a good practice to reduce the occurence
          of the situation described above in the input weather datafiles before trying to
          fill the gaps in the data.
    
    
Filling the gaps in the data
-----------------------------------------------
    
The automated procedure to fill the gaps in the dataset of the selected weather
station can be started by clicking the button button |icon_fill_data| `Fill`.
It is also possible to fill the gaps of all the datasets of the 
:guilabel:`Fill data for weather station` dropdown list in batch by clicking
on the button |icon_fill_all_data| `Fill All Stations`. The parameters used in the
gapfilling procedure will stay the same for all the stations.

Once the process is completed for a station, the resulting gapless daily weather
dataset is automatically saved in a :abbr:csv (coma-separated values) file with
a :file:`.out` extension in the :file:`Output` folder. The :file:`.out` file is
named after the weather station name, climate ID, and first and last year of
the dataset. For example, the resulting output file for the station *FARNHAM*
in :numref:`scs_gapfill_weather_annoted` would be
:file:`FARNHAM (7022320)_1980-2017.out`.

In addition, detailed information on the values estimated
for filling the gaps in the data are saved in a file with the same name as the 
:file:`.out` file, but with a :file:`.log` extension. Information includes, 
the names of the neighboring stations, the values of the data used for
the estimations, as well as the expected uncertainty of the estimates.

Setting the parameters
-----------------------------------------------




.. |icon_clear| image:: img/icon_clear.*
                      :width: 1em
                      :height: 1em
                      :alt: stop
                      
.. |icon_fill_data| image:: img/icon_fill_data.*
                      :width: 1em
                      :height: 1em
                      :alt: fill data
                      
.. |icon_fill_all_data| image:: img/icon_fill_all_data.*
                      :width: 1em
                      :height: 1em
                      :alt: fill all data
                      
.. |icon_merge_data| image:: img/icon_merge_data.*
                      :width: 1em
                      :height: 1em
                      :alt: merge dataset
                      
                      
.. |icon_refresh| image:: img/icon_refresh.*
                      :width: 1em
                      :height: 1em
                      :alt: stop
