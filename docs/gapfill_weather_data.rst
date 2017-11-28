Gapfilling Daily Weather Data
===============================================

GWHAT provides an automated, robust, and efficient method to fill the gaps in
daily weather data records. In addition, uncertainties of the estimated 
missing values can be automatically assessed with a cross-validation resampling technique.
This document shows how to fill the gaps in daily weather
records using the gapfilling weather data tool of GWHAT available under the tab
:guilabel:`Gapfill Weather` shown in :numref:`gapfill_weather_demo`.

.. _gapfill_weather_demo:
.. figure:: img/demo/gapfill_weather_demo.*
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

The method used to estimate the missing data for the selected weather station consists in the generation
of a multiple linear regression (MLR) model, using synchronous data from selected neighboring
stations from the list. The neighboring stations are selected mainly on the basis of the correlation coefficients
computed between their data and those of the selected weather station. The values of these
coefficients are automatically displayed in the table located in the right side of the interface when a new
weather station is selected from the list. Moreover, among the selected neighboring stations, the ones
with the highest correlation coefficients have more weight in the model than those with weak correlation
coefficients. For this reason, correlation coefficients that fall below a value of 0.7 are shown in red in the
table, as a guidance for the user. There are several settings that can be used to control the selection of the
neighboring stations, the generation of the MLR model, and the outputs of the gapfilling procedure. An
overview of these settings is presented below.

Selected Station and Period
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The first step is to select the dataset for which missing values need to be filled.
This is done from the drop-down list located under the :guilabel:`Fill data for station section` 
shown in :numref:`fig_fill_data_for_station`.
Under this list are displayed information about the currently selected weather station. 

It is also possible to define the period for which the data of the selected
station will be filled by editing the date fields located next to the 
:guilabel:`From` and ::`To` labels. By default, dates are set as the first and
the last date for which data are available for any of the stations of the list.

.. _fig_fill_data_for_station:
.. figure:: img/scs_gapfill_data_for_station.*
    :align: center
    :width: 50%
    :alt: alternate text
    :figclass: align-center
    
    Presentation of the :guilabel:`Fill data for weather station` section
    located under the :guilabel:`Gapfill Weather` tab.

Stations Selection Criteria
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A MLR model is generated for each day for which a data is missing in the
dataset of the selected station. This is done because the number of neighboring stations with available
data can vary in time. Therefore, for a given date with missing data in the dataset of the selected station,
the neighboring stations are selected in decreasing order of their correlation coefficients. Neighboring
stations that also have a missing data at this particular date are excluded from the selection process. The
maximum number of station that are selected for the generation of the MLR model can be specified in
the Nbr. of stations field, located in the Stations Selection Criteria menu shown in Fig. 3.5. The number
of neighboring station that is selected by default is 4. If for a given date, all the neighboring stations have
missing data synchronously with the selected station, a NaN value is kept in the dataset at this particular
date.
Moreover, the correlation between the data of two stations will, in general, decreases as the distance
and the altitude difference between them increase. Therefore, the fields Max. Distance and Max. Elevation
Diff. allow to specify thresholds for the distance and altitude difference. Neighboring stations
exceeding either one of these thresholds will not be used to fill the gaps in the dataset of the selected station.
The default values for the distance and altitude difference are set to 100 km and 350 m, respectively,
based on a literature review (Simolo et al., 2010; Tronci et al., 1986; Xia et al., 1999). The horizontal
distances and elevation differences calculated between the selected station and its neighbors are shown
in the table to the right, alongside the correlation coefficients. The values that exceed their corresponding
threshold are shown in red.

.. _fig_gapfill_station_selection_criteri:
.. figure:: img/scs_gapfill_station_selection_criteria.*
    :align: center
    :width: 50%
    :alt: alternate text
    :figclass: align-center

Regression Model
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
It is possible to select whether the MLR model is generated using a Ordinary Least
Squares (OLS) or a Least Absolute Deviations (LAD) criteria from the Regression Model menu shown
in Fig. 3.6. A regression based on a LAD is more robust to outliers than a regression based on a OLS, but
is more expensive in computation time.

.. _fig_gapfill_regression_model:
.. figure:: img/scs_gapfill_regression_model.*
    :align: center
    :width: 50%
    :alt: alternate text
    :figclass: align-center

Advanced Settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is possible to automatically estimate and add the daily Potential Evapotranspiration
(ETP) to the output data file produced at the end of the gapfilling procedure of the selected station.
This option is enabled by checking the Add ETP to data file option in the menu Advanced Settings shown
in Fig. 3.7. The daily ETP is estimated with a method adapted from Thornthwaite (1948), using the daily
mean air temperature time series of the selected station. Alternatively, it is possible to add manually the
ETP to an existing weather data file by clicking on the open file icon located next to the Add ETP to
data file option.

The Full Error Analysis option can be checked to perform a cross-validation resampling analysis
during the gapfilling procedure. The results from this analysis can be used afterward to estimate the
accuracy of the method. This option is discussed in more details in Section 3.2.5.

Uncertainty Assessment
-----------------------------------------------
By default, each time a new MLR model is generated to estimate a missing value in the dataset of the
selected station, the model is also used to predict the values in the dataset that are not missing. The
accuracy of the MLR model is then approximated by computing a Root-Mean-Square Error (RMSE)
between the values estimated with the model and the respective non-missing observations in the dataset
of the selected station. The RMSE thus calculated is saved, along with the estimated value, in the “.log”
file.

When the Full Error Analysis option in the Advanced Settings menu is enabled, WHAT will also
perform a cross-validation resampling procedure to estimate the accuracy of the model, in addition to fill
the gaps in the dataset. More specifically, the procedure consists in estimating alternately a weather data
value for each day of the selected station’s dataset, even for days for which data are not missing. Before
estimating a value for a given day, the corresponding measured data in the dataset of the selected station
is temporarily discarded to avoid self-influence of this observation on the generation of the MLR model.
The model is then generated and used to estimate a value on this given day and the corresponding observed
data is put back in the dataset of the selected station. When a value for every day of the dataset has
thus been estimated, the estimated values are saved in a tsv (tabular-separated values) file in the Output
folder with the extension “.err”, along with the “.log” and “.out” files described in Section 3.2.4. The accuracy
of the method can then be estimated by computing the RMSE between the estimated weather data
and the respective non-missing observations in the original dataset of the selected station. Activating this
feature will significantly increase the computation time of the gap filling procedure, especially if the least
absolute deviation regression model is selected, but can provide interesting insights on the performance
of the procedure for the specific datasets used for a project.

.. _fig_gapfill_advanced_setting:
.. figure:: img/scs_gapfill_advanced_setting.*
    :align: center
    :width: 50%
    :alt: alternate text
    :figclass: align-center


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
