.. _chap_importing_data:

Data Management in GWHAT
===============================================

Importing Data
-----------------------------------------------

Before groundwater well hydrographs can be plotted or analyzed in GWHAT, time
series of groundwater level and weather data must be imported into the currently
opened project. This is done for water level and weather datasets by clicking
on their corresponding |icon_open_project| icon located in the right side panel
of the main window, under the tab :guilabel:`Plot Hydrograph` or :guilabel:`Analyze Hydrograph`.

Clicking on either of the |icon_open_project| icons opens a dialog window 
where a valid water level or weather datafile can be selected by clicking on
the |icon_folder| icon (see :numref:`scs_new_water_level_dataset_dialog`).

After a valid file has been selected, the information relative to the climate
or piezometric station will be displayed in the dialog and a name for the dataset
will be proposed next to
the :guilabel:`Dataset name` label. Once the information relative to the
station and dataset name are correct, the dataset can be imported in the
project by clicking on the button :guilabel:`Ok`

.. _scs_new_water_level_dataset_dialog:
.. figure:: img/scs/new_water_level_dataset_dialog.*
    :align: center
    :width: 50%
    :alt: alternate text
    :figclass: align-center
    
    Presentation of the dialog window to import water level data files.

The tools for downloading and filling the gaps in daily weather records
(see in :numref:`chap_dwnld_weather` and :numref:`chap_gapfilling_weather_data`)
work directly from csv files to load and save the input and output data. This
is practical because it allowed using GWHAT more easily to generate gapless
daily weather datasets for any projects, even those not implying the
assessment of groundwater recharge.





Input data files format
-----------------------------------------------

Weather data files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The format of the weather data files must be coma-separated values text files
as described in :numref:`sec_weather_datafiles_format` with either a :file:`.out` or
:file:`.csv` extension. Files with a :file:`.out` extension are gapfilled weather
dataset produced with the gapfilling tool in tab :guilabel:`Gapfill Weather`
presented in :numref:`chap_gapfilling_weather_data`.

.. note:: Preferably, the gaps in the daily weather records must have been 
          filled before importing them. Otherwise, a value of 0 is assumed 
          for days where precipitation are missing and the missing values for 
          air temperature are evaluated by linear interpolation.

Water level data files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
          
The water level datafiles can be either in the :file:`xls` or :file:`xlsx` format. 
An exemple of correctly formatted water level datafile is presented in
:numref:`water_level_datafile_example`. The information contained in the header
will be loaded into the dialog window presented in :numref:`importing_data_inproject`.
The information can then be modified within this window before the data are imported into
the project. The first column of the data must contained the time in excel numeric
format. The second column must contain the water level, given in meters below the
ground surface. The third and fourth columns correspond, respectively, to the
barometric pressure and the Earth tides. This will be discussed in more details
in another section.

.. _water_level_datafile_example:
.. figure:: img/files/water_level_datafile.*
    :align: center
    :width: 85%
    :alt: water_level_datafile.png
    :figclass: align-center
    
    Formatted weather datafile example.
    
.. important:: Water levels must be entered in meters below the ground surface.

.. |icon_open_project| image:: img/icon/open_project.*
                      :width: 1em
                      :height: 1em
                      :alt: folder