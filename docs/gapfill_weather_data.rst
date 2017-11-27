Gapfilling Daily Weather Data
===============================================

GWHAT provides an automated, robust, and efficient method to fill the gaps in
daily weather data records. In addition, GWHAT automatically validates and assess
the uncertainties of the estimated missing values with a cross-validation resampling technique.

This document shows how to fill the gaps in daily weather
records using the gapfilling weather data tool of GWHAT available under the tab
``Gapfill Weather`` shown in :numref:`gapfill_weather_demo`.

.. _gapfill_weather_demo:
.. figure:: img/gapfill_weather_demo.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
    
    Presentation of the `gapfill weather data` tool of GWHAT available under
    the tab ``Gapfill Weather``.


Loading the weather data files
-----------------------------------------------

When starting GWHAT or when a new project is selected, the content of the
:ref:`Input <def_meteo_input_folder>` folder is automatically scanned for valid weather data files that respect
the format described in :ref:`Formatting the weather datafiles`.

The restuls are displayed in a list located under :guilabel:`Fill data for weather station` 
section as as shown in :numref:`scs_gapfill_weather_annoted`.
The list of weather datasets can be refreshed at any times by clicking on the 
|refresh| icon. This needs to be done if new datafiles are added or deleted manually
from the :file:`Input` folder, outside of GWHAT. Datasets can be removed from the list
by selecting them and clicking on the |clear| icon. Doing so also remove the
corresponding data file from the :file:`Input` folder.

A summary of the number of days with missing data for each dataset is also
produced and displayed under :guilabel:`Missing Data Overview` tab of the display area.

.. _scs_gapfill_weather_annoted:
.. figure:: img/scs_gapfill_weather_annoted.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
    
    Presentation of the `gapfill weather data` tool of GWHAT available under


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
on the |merge_data| icon (see :numref:`merge_weather`).



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
    
    
.. |clear| image:: img/icon_clear.*
                      :width: 1em
                      :height: 1em
                      :alt: stop

.. |merge_data| image:: img/icon_merge_data.*
                      :width: 1em
                      :height: 1em
                      :alt: merge dataset

.. |refresh| image:: img/icon_refresh.*
                      :width: 1em
                      :height: 1em
                      :alt: stop