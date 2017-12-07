.. _chap_plot_hydrographs:

Plotting the hydrographs
===============================================

This document shows how to produce publication quality figure of well hydrographs
in GWHAT using the tools availble under the tab :guilabel:`Plot Hydrograph` shown
in :numref:`scs_plot_hydrograph`.

.. _scs_plot_hydrograph:
.. figure:: img/demo/demo_plot_hydrograph.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
    
    Presentation of the tool to plot hydrographs in GWHAT under the 
    :guilabel:`Plot Hydrograph` tab.
 

.. _importing_data_inproject:
  

Plotting the Hydrograph
-----------------------------------------------

.. _fig_plot_hydrograph_annoted:
.. figure:: img/scs/plot_hydrograph_annoted.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
 
Page and figure settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Several options are available to customize the size and visibility of the
various components of the hydrograph. These options are available in the
:guilabel:`Page and Figure Setup` window that is accessible by clicking on the
|icon_page_setup| icon (see :numref:`fig_plot_hydrograph_annoted`).
The :guilabel:`Page and Figure Setup` window is shown in
:numref:`fig_hydroprint_page_settings`, as well as the components of the
hydrograph for which the size or the visibility can be configured.

.. _fig_hydroprint_page_settings:
.. figure:: img/scs/hydroprint_page_setting.*
    :align: center
    :width: 100%
    :alt: hydroprint_page_setting.svg
    :figclass: align-center
   
Water level manual measurements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Water level measured manually during field visits can be plotted on the hydrograph.
This provides a quick and easy way to validate visually the automated measurements acquired
with a water level datalogger.

To do so, the manual measurements must be saved in a csv or xls/xlsx file
named :file:`water_level_measurements` in the :file:`Water Levels` folder 
(see :numref:`sec_desc_project_folders`).
An example is shown in :numref:`fig_water_level_measurements` below. The first column corresponds
to the name of the observation wells, as specified when importing the data into
the project (see :numref:`importing_data_inproject`), the second column is the
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


Axes settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _fig_hydroprint_axis_settings:
.. figure:: img/scs/axis_setup_annoted.*
    :align: center
    :width: 100%
    :alt: axis_setup_annoted.svg
    :figclass: align-center

The axis can be configured from the 

Color Settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The color of several components of the hydrograph can be changed from the
:guilabel:`Colors Palette Setup` window that is accessible by clicking
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

 
Weather Normals Viewer
-----------------------------------------------

.. _fig_weather_normal_viewer:
.. figure:: img/scs/weather_normal_viewer.*
    :align: center
    :width: 85%
    :alt: water_level_datafile.png
    :figclass: align-center
    
    Presentation of the weather normals viewer.
    


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
