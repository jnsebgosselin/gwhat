.. _chap_plot_hydrographs:

Plotting the Hydrographs
===============================================

This document shows how to produce publication quality figures of well hydrographs
in GWHAT using the tools available under the tab :guilabel:`Plot Hydrograph` shown
in :numref:`scs_plot_hydrograph`.

.. _scs_plot_hydrograph:
.. figure:: img/demo/demo_plot_hydrograph.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center

    Presentation of the tool to plot hydrographs in GWHAT under the
    :guilabel:`Plot Hydrograph` tab.

The tab :guilabel:`Plot Hydrograph` consists mainly of an editor to produce a
graph showing the ground-water level time series in relation to weather
conditions. As shown in :numref:`fig_plot_hydrograph_annoted`, the editor
consists of a toolbar, the panel :guilabel:`Input data`, the panel
:guilabel:`Axes settings`, and a canvas where the hydrograph figure is shown.

A figure of the hydrograph is produced as soon as a water level and weather
dataset have been selected in the :guilabel:`Input data` panel.
It is possible to zoom the figure canvas in or out by pressing the
|icon_zoom_in| or |icon_zoom_out| icon or by rotating the mouse wheel while
holdind the :kbd:`Ctrl` key.

Various parameters are available to customize the layout of the hydrograph:

- Several options are available to customize the size and visibility of 
  the components of the hydrograph in the :guilabel:`Page and Figure Setup`
  window, which is accessible by clicking on the |icon_page_setup| icon.
  This is covered in more details in :numref:`subsec_page_and_fig_settings`.
  
- The color of most of the elements that are plotted in the hydrograph
  can be configured in the :guilabel:`Colors Palette Setup` window, which is
  accessible by clicking on the |icon_color_picker| icon.
  This is covered in more details in :numref:`subsec_color_settings`.
  
- The axis of the graph can be configured in the :guilabel:`Axes settings` panel.
  This is covered in more details in :numref:`subsec_axis_settings`.
  In addition, the |icon_fit_x| and |icon_fit_y| icons can be clicked at any time 
  to, respectively, fit the time and water level axis automatically to the data.

- The |icon_meteo| icon is used to access the :guilabel:`Weather Averages` window
  where are displayed the yearly and monthly normals of the weather dataset.
  This is covered in more details in :numref:`chap_weather_normals_viewer`.


The layout for the currently selected water level dataset can be saved by
clicking on the |icon_save_config| icon. The previously saved layout can be
loaded back for the currently selected water level dataset by clicking on the
|icon_load_config| icon. Finally, the hydrograph can be saved in a pdf or
svg format by clicking on the |icon_save| icon.


.. _fig_plot_hydrograph_annoted:
.. figure:: img/scs/plot_hydrograph_annoted.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center

    Presentation of the editor to produce publication quality figures of
    well hydrographs that is available in the tab :guilabel:`Plot Hydrograph`
    of GWHAT.

Components of the Hydrograph
-----------------------------------------------

.. _fig_hydrograph_components:
.. figure:: img/scs/hydrograph_components.*
    :align: center
    :width: 100%
    :alt: hydrograph_components.svg
    :figclass: align-center

    Identification of the components of the hydrograph.

.. _subsec_water_level_component:

Ground-water level
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ground-water levels are plotted on the bottom part of the hydrograph. By default,
the ground-water data are plotted as a continuous line that relies all the available
data. 

It is possible to force the line to break over an extended period of time for
which data is missing by adding a nan value between the period for which data is
available in the water level datafile before importing it.
For example, in :numref:`fig_missing_water_level`, water level data
were missing for the whole of 2012. A ``nan`` was thus added in the datafile 
at one time during this period to avoid a line to be plotted between the
31/12/2011 and the 01/01/2013.

It is also possible to show the trend of the water level data with the option
:guilabel:`Water Level Trend` that is available in the :guilabel:`Page and Figure Setup`
window (see :numref:`subsec_page_and_fig_settings`). The actual data will then be
plotted below the trend line as a scatter plot as shown in the hydrograph of 
:numref:`fig_hydrograph_components`. The trend line is computed using a
moving average window of 30 days.

.. _fig_missing_water_level:
.. figure:: img/scs/hydrograph_missing_period.*
    :align: center
    :width: 100%
    :alt: hydrograph_missing_period.png
    :figclass: align-center

    Example of an hydrogaph with an extended period of time for which data is
    missing.

.. _subsec_weather_data_component:

Weather data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Mean air temperature is plotted in the top part of the graph. The area
between 0ºC and the observed temperature is colored by default to highlight the
periods when air temperature is below the freezing point of water. Mean air
temperature can be plotted on a daily, weekly, or monthly basis. This can be changed
from the :guilabel:`Axes settings` panel as discussed in :numref:`subsec_axis_settings`. 

Cumulative precipitation, as rain and snow, are plotted in the bottom part of the
hydrograph along with the water level data. For a given day, precipitation is
assumed to fall as snow if the mean air temperature for that day is below 0ºC and
as rain otherwise. As for air temperature, cumulative precipitation can be plotted on
a daily, weekly, or monthly basis. 

Missing weather data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``Missing data`` component is used to mark where daily air temperature and
precipitation were estimated due to missing data in the dataset. These information
are read when importing a dataset in GWHAT (see :numref:`sec_importing_data`) from
the :file:`.log` file that is produced automatically when gapfilling daily
weather records with the tool presented in :numref:`chap_gapfilling_weather_data`.

.. note:: If no :file:`.log` exists when importing a daily weather datafile in 
          GWHAT, ``Missing data`` markers won't be plotted on the hydrograph,
          even if data are missing in the daily weather dataset.


Water level manual measurements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Water level measured manually during field visits can also be plotted on the hydrograph.
This provides a quick and easy way to visually validate the automated measurements
acquired with a water level datalogger.

To do so, the manual measurements must be saved in a csv or xls/xlsx file
named :file:`water_level_measurements` in the :file:`Water Levels` folder
(see :numref:`sec_desc_project_folders`).
An example is shown in :numref:`fig_water_level_measurements` below. The first column corresponds
to the name of the observation wells (see :numref:`sec_importing_data`), the second column is the
dates entered in :term:`Excel numeric date format`, and the last column corresponds to
the manual measurements, in meters below the ground surface.

.. _fig_water_level_measurements:
.. figure:: img/files/water_level_measurements.*
    :align: center
    :width: 50%
    :alt: water_level_measurements.png
    :figclass: align-center

    Example of a :file:`water_level_measurements` file.

.. note:: A :file:`water_level_measurements` file is created in a csv format
          by default by GWHAT the first time a project is created. If desired,
          this file can be converted to a xsl or xslx format. Note that if more
          than one file named :file:`water_level_measurements` exists in the folder
          :file:`Water Levels`, but with different extension, GWHAT will always
          read the data from the csv file by default.

.. _subsec_page_and_fig_settings:

Page and figure settings
-----------------------------------------------

Several options are available to customize the size and visibility of various
components of the hydrograph in the :guilabel:`Page and Figure Setup` window,
which is accessible by clicking on the |icon_page_setup| icon
(see :numref:`fig_plot_hydrograph_annoted`).
The :guilabel:`Page and Figure Setup` window is shown in
:numref:`fig_hydroprint_page_settings`, as well as the components of the
hydrograph for which the size or the visibility can be configured.

.. _fig_hydroprint_page_settings:
.. figure:: img/scs/hydroprint_page_setting.*
    :align: center
    :width: 100%
    :alt: hydroprint_page_setting.svg
    :figclass: align-center

    Presentation of the components of the hydrograph for which the size or the
    visibility can be configured in the `Page and Figure Setup` window.


.. _subsec_axis_settings:

Axis settings
-----------------------------------------------

The scale and range of the axes for time, water level, and weather data can be
configured from the :guilabel:`Axes settings` panel, located on the right side
of the hydrograph editor. The options that are available for each axis are
presented in :numref:`fig_hydroprint_axis_settings`. The hydrograph is updated
automatically when a value is changed in the :guilabel:`Axes settings` panel.

.. _fig_hydroprint_axis_settings:
.. figure:: img/scs/axis_parameters_annoted.*
    :align: center
    :width: 100%
    :alt: axis_setup_annoted.svg
    :figclass: align-center

Time axis
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The range of the time axis can be changed by setting the :guilabel:`From` and 
:guilabel:`To` dates. The :guilabel:`Scale` of the time axis can be set to
`monthly` or `yearly`. The :guilabel:`Date Disp. Pattern` setting allow to define
the interval with which the tick labels of the time axis are plotted. Four different
cases with different values of the :guilabel:`Scale` and The :guilabel:`Date Disp. Pattern`
settings are presented in :numref:`fig_hydroprint_axis_settings`.

Water level axis
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :guilabel:`Minimum` setting of corresponds to the value at the bottom of
the water level axis. The :guilabel:`Grid Divisions` value corresponds to the 
number of intervals in which the water level axis is divided as shown on
:numref:`fig_hydroprint_axis_settings`. The :guilabel:`Datum` of reference of
the water level axis can be set to either ``Ground Surface`` or ``See Level``.

The value at the top of the water level axis is calculated from the values
specified in :guilabel:`Minimum`, :guilabel:`Scale`, and :guilabel:`Grid Divisions`.
The equation that is used in the calculation, which depends on the :guilabel:`Datum` that
is selected, is presented at the bottom of :numref:`fig_hydroprint_axis_settings`.

Weather axis
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Only the scale of the axis for the precipitation is configurable through the
:guilabel:`Precip. Scale` setting. The minimum value for precipitation is always
set to 0 and the range of the axis depends on the value specified for the setting
:guilabel:`Precip. Scale` and :guilabel:`Grid Divisions` in the water level axis
settings.

As discussed in :numref:`subsec_weather_data_component`, the :guilabel:`Resampling` setting is used to set the time scale on which mean
air temperature and cumulative precipitation are plotted on the graph.


.. _subsec_color_settings:

Color Settings
-----------------------------------------------

The color of several components of the hydrograph can be changed from the
:guilabel:`Colors Palette Setup` window, which is accessible by clicking
on the |icon_color_picker| icon (see :numref:`fig_plot_hydrograph_annoted`). The
:guilabel:`Colors Palette Setup` window and the components of the hydrograph for which
the color can be changed are both shown in :numref:`fig_hydroprint_color_settings`.
A new color can be selected for a given component of the hydrograph by clicking
on its corresponding colored square in the :guilabel:`Colors Palette Setup`
window and by clicking on the :guilabel:`OK` or :guilabel:`Apply` button.

.. _fig_hydroprint_color_settings:
.. figure:: img/scs/hydroprint_color_settings.*
    :align: center
    :width: 100%
    :alt: hydroprint_color_settings.svg
    :figclass: align-center

    Presentation of the :guilabel:`Colors Palette Setup` and identification on
    the hydrograph of the components for which the color can be changed.

.. |icon_save| image:: img/icon_save.*
                      :width: 1em
                      :height: 1em
                      :alt: folder
.. |icon_folder| image:: img/icon/icon_folder.*
                      :width: 1em
                      :height: 1em
                      :alt: folder

.. |icon_meteo| image:: img/icon/meteo.*
                      :width: 1em
                      :height: 1em
                      :alt: folder

.. |icon_color_picker| image:: img/icon/color_picker.*
                      :width: 1em
                      :height: 1em
                      :alt: color picker

.. |icon_page_setup| image:: img/icon/page_setup.*
                      :width: 1em
                      :height: 1em
                      :alt: page setup

.. |icon_zoom_in| image:: img/icon/icon_zoom_in.*
                      :width: 1em
                      :height: 1em
                      :alt: zoom in

.. |icon_zoom_out| image:: img/icon/icon_zoom_out.*
                      :width: 1em
                      :height: 1em
                      :alt: zoom in
                      
.. |icon_fit_x| image:: img/icon/icon_fit_x.*
                      :width: 1em
                      :height: 1em
                      :alt: best-fit x-axis
                                            
.. |icon_fit_y| image:: img/icon/icon_fit_y.*
                      :width: 1em
                      :height: 1em
                      :alt: best-fit y-axis
                      
.. |icon_save_config| image:: img/icon/icon_save_config.*
                      :width: 1em
                      :height: 1em
                      :alt: save layout
                                            
.. |icon_load_config| image:: img/icon/icon_load_config.*
                      :width: 1em
                      :height: 1em
                      :alt: load layout
                      