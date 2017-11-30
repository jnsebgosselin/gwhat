.. _chap_plot_hydrographs:

Plotting the hydrographs
===============================================

This document shows how to produce publication quality figure of well hydrographs
in GWHAT using the tools availble under the tab :guilabel:`Plot Hydrograph` shown
in :numref:`scs_plot_hydrograph`.

.. _scs_plot_hydrograph:
.. figure:: img/scs/plot_hydrograph.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
    
    Presentation of the tool to plot hydrographs in GWHAT under the ``Plot Hydrograph`` tab.
 
    
Importing Data
-----------------------------------------------

The tools for downloading and filling the gaps in daily weather records
(see in :numref:chap_dwnld_weather and :numref:chap_gapfilling_weather_data)
work directly from the csv file to load and save the input and output data. This
is practical because it allowed using GWHAT more easily to generate gapless
daily weather datasets for any projects, even those not implying the
assessment of groundwater recharge.

The tools to plot and analyze groundwater well hydrograph, however, requires to
import the water level and weather data into the project. This is done for 
water level and weather datasets by clicking on the corresponding  
|icon_open_project| icon located in the right side panel of the tab 
:guilabel:`Plot Hydrograph`.

This opens a dialog window that allow to select a valid water level or weather
data file as shown in :numref:`scs_new_water_level_dataset_dialog`.

.. _scs_new_water_level_dataset_dialog:
.. figure:: img/scs/new_water_level_dataset_dialog.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
    
    Presentation of the dialog window to import water level data files.

Weather Normals Viewer
-----------------------------------------------


.. |icon_folder| image:: img/icon/icon_folder.*
                      :width: 1em
                      :height: 1em
                      :alt: folder
                      
.. |icon_open_project| image:: img/icon/open_project.*
                      :width: 1em
                      :height: 1em
                      :alt: folder