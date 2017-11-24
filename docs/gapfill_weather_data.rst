Gapfilling Daily Weather Data
==============================

This document shows how to quickly and easily fill the gaps in daily weather
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
daily weather data records. In addition, GWHAT validate and assess the uncertainty
of the estimated missing values with a cross-validation resampling technique.

Loading the weather data files
-----------------------------------------------

When starting GWHAT or when a new project is selected, the content of the
*Meteo/Input* folder located in the *project folder* is automatically scanned
for weather data files. The results are displayed in a list of weather stations,
located under the label Fill data for weather station shown in Fig. 3.4.
A summary of the number of days with missing data for each dataset is also
produced and displayed in the tab Missing Data Overview of the display area, to the right.
The icon with the circular arrows , located next to the list of stations, can be
clicked to re-scan the Input folder for new weather data files to update the list
of stations and the summary.

It is also possible to fill the gaps in weather datasets from files that were not produced with WHAT, provided that the data
are formatted in the right format (see Appendix B).
