Project Management in GWHAT
===============================================

This document shows how to create, open and manage existing projects in GWHAT.
Data are managed in GWHAT by project. This means that all input and output files
relative to a particular project are stored in a common folder, hereafter referred
to as the :term:`project folder`. This file management system allows to easily backup
or copy the data related to a particular project since all the files are saved
at the same location.

Only one project at a time can be opened per instance of GWHAT. The title of the 
currently opened project is displayed on a button located in the :guilabel:`project toolbar`
as shown in :numref:`project_toolbar`. The project named *Example* is opened by
default the first time GWHAT is started. This project includes samples of
files to test the different features of GWHAT.

.. _project_toolbar:
.. figure:: img/scs_project_toolbar_annoted.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
    
    Presentation of the project toolbar in GWHAT.

Creating a new project
-----------------------------------------------

New projects are created by clicking on the |icon_new_project| icon located on the
:guilabel:`project toolbar` (see :numref:`project_toolbar`). This opens a dialog window 
(see :numref:`create_new_project`) where information about the project can 
be entered such as its title, author, and location coordinates.

.. _create_new_project:
.. figure:: img/scs_new_project_annoted.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center

Clicking on the button :guilabel:`Save` will create a new project folder (named after
the project’s title) and a file with a :file:`gwt` extension where the information
related to the project are saved. 
The directory where the :file:`project folder` is created can be changed by
clicking the |icon_folder| icon.
The content and format of the project folder 
and project file (:file:`*.gwt`) are described in more details, respectively, in 
:numref:`sec_desc_project_folders` and :numref:`sec_gwt_structure_overview`.

Opening an existing project
-----------------------------------------------

Clicking on the button where is displayed the currently opened project title on
the project toolbar (see :numref:`project_toolbar`) opens a dialog window where
an existing project file (:file:`.gwt`) can be selected and opened.

The path to the project folder is stored in a relative format in GWHAT. This means
that if the location of the project folder is changed relative the executable of
the software (:program:`gwhat.exe`), GWHAT will need to be redirected to the new location
of the project by repeating the procedure described above.

.. _sec_desc_project_folders:

Project Folders
-----------------------------------------------

This section describes in details the content of project folders, where are
stored all input and output files relative to a particular project.
An example of a project folder files organization is presented in
:numref:`file_and_folder_architecture`.

.. _file_and_folder_architecture:
.. figure:: img/file_and_folder_architecture.*
    :align: center
    :width: 75%
    :alt: alternate text
    :figclass: align-center
    
    Example of a project folder files organization.

The file with the :file:`gwt` extension is a binary file where are saved the metadata
related to the project (e.g. project title, author, creation date, etc.). It is also
where are saved all the input and output data related to the plotting and interpretation of
hydrographs, including the estimation of recharge. The format and structure of these
files are described in more details in :numref:`sec_gwt_structure_overview`.

The file with the :file:`lst` extension is a csv file containing a list of
weather stations from the Canadian Daily Climate Database (CDCD). These files
can be created with the tools presented in :numref:`chap_dwnld_weather`.
An exemple of weather station list is presented in :numref:`weather_stationlist_example`.

.. _weather_stationlist_example:
.. figure:: img/file_climate_station_list.*
    :align: center
    :width: 85%
    :alt: file_climate_station_list.png
    :figclass: align-center
    
    Example of a :file:`.lst` file containing a list of climate stations.

The file :file:`waterlvl_manual_measurements.xls` contains the manual
water-level measurements from field visits that are used when plotting the
hydrophraph as explained in :numref:`chap_plot_hydrographs`.

The folder :file:`Meteo` contains all input and output data relative to the
downloading, formatting, and the creation of gapless daily weather records. It
contains three sub-folders named respectively :file:`Raw`, :file:`Input`, 
and :file:`Output`.

The folder :file:`Raw` is where are saved the daily weather data files once they
have been downloaded from the CDCD as described in :numref:`sec_download_weather_data`.
All the files downloaded for a same station are saved within a common folder,
named after the name of the station and its climate ID. For example,
in :numref:`file_and_folder_architecture`, the data file
:file:`eng-daily-01011980-12311980.csv`, which contains weather data from the station *Marieville*
for the year 1980, is saved in a folder named :file:`MARIEVILLE (7024627)`, where the number in
parentheses is the climate ID of the station.

The folder :file:`Input` is where are saved by default the formatted weather
data files generated from the raw data files. The csv files are named by 
default after the name of the station, its climate ID, and the first and last year of the data record.
This folder is also the default location used by the tool to fill the gaps in 
daily weather data records to look for input weather data files as described in 
:numref:`sec_loading_weather_data`.

The folder :file:`Output` is where the gapless weather time-series are saved in
csv files with the extension :file:`.out`. The files with the extension :file:`.log`
are csv files that contain detailed information about the missing
daily weather values that were estimated to fill the gaps in the weather datasets.
The files with the extension :file:`.err` contains a time-series of estimated weather
values that were produced with a crossvalidation re-sampling technique.
These estimated values can be used to evaluate the accuracy of the method.
The file :file:`weather_datasets_summary.log` is a csv file that contains a summary
of all the weather data files that are saved in the :file:`Input` folder.

The folder :file:`Water Levels` is the preferred location where the water level
datasets related to a same project should be stored. These files can be either
in a csv, xls or xlsx file format.

.. _sec_gwt_structure_overview:

Project Files
-----------------------------------------------

.. figure:: img/Work-in-progress.*
    :align: center
    :width: 50%
    :alt: http://breakingbad.wikia.com/wiki/File:Work-in-progress-1024x603.png.
    :figclass: align-center


.. |icon_folder| image:: img/icon_folder.*
                      :width: 1em
                      :height: 1em
                      :alt: folder



.. |icon_new_project| image:: img/icon_new_project.*
                      :width: 1em
                      :height: 1em
                      :alt: stop