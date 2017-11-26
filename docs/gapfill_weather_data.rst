Gapfilling Daily Weather Data
===============================================

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

GWHAT provides an automated, robust, and efficient method to fill the gaps in
daily weather data records. In addition, GWHAT automatically validates and assess
the uncertainties of the estimated missing values with a cross-validation resampling technique.

Loading the weather data files
-----------------------------------------------

When starting GWHAT or when a new project is selected, the content of the
*Input* folder is automatically scanned for valid weather data files that respect
the format described in :ref:`Formatting the weather datafiles`.

The restuls are displayed in a list located under the label `Fill data for weather station`
as shown in :numref:`scs_gapfill_weather_annoted`.
The list of weather datasets can be refreshed at any times by clicking on the 
|refresh| icon. This needs to be done if new datafiles were added or deleted manually
from the *Input* folder outside of GWHAT. Dataset can be removed from the list
by selecting them and clicking on the |clear| icon. Doing so also remove the
corresponding data file from the *Input* folder.

A summary of the number of days with missing data for each dataset is also
produced and displayed under `Missing Data Overview` tab of the display area.


.. _scs_gapfill_weather_annoted:
.. figure:: img/scs_gapfill_weather_annoted.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
    
    Presentation of the `gapfill weather data` tool of GWHAT available under


Merging two weather data files
-----------------------------------------------

.. _merge_weather:
.. figure:: img/scs_merge_weather_data.*
    :align: center
    :width: 50%
    :alt: alternate text
    :figclass: align-center
    
    Presentation of the tool to merge two daily weather records together.
    
    
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