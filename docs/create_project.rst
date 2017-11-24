Project Management in GWHAT
===============================================

This document shows how to create and open existing project in GWHAT from the
`project toolbar` that is located in the upper right corner of the GWHAT window
as shown in :numref:`demo_create_project`.

.. _demo_create_project:
.. figure:: img/demo_create_project.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
    
    Presentation of the interface to create a new project in GWHAT.

Open an existing project
-----------------------------------------------

Data are managed in GWHAT by project. This means that all input and output files
relative to a particular project are stored in a common folder, hereafter referred to as
the *project folder*.This file management system allows to easily backup or copy the
data related to a particular project since all the files are saved at the same
location.

Only one project at a time can be opened per instance of GWHAT. The title of the 
currently opened project is displayed on a button located inthe project toolbar as
shown in :numref:`project_toolbar`. The project named *Example* is opened by
default the first time GWHAT is started. This project includes samples of
files to easily and quickly test the different features of GWHAT.

It is possible to open an existing project by clicking on the button where is
displayed the name of the currently opened project in GWHAT. This will open a
new dialog window, from which an existing project file (*.gwt) can be selected
and opened. 

The path to the project folder is stored in a relative format. This means that
if the location of the project folder is changed relative the executable of
the software (“WHAT.exe”), WHAT will need to be redirected to the new location
of the project by repeating the procedure described in the paragraph above.


Create a new project
-----------------------------------------------


The creation of a new project is started by clicking on the |new_project| icon
located in the project toolbar as shown in .

This will open a new dialog window (Fig. 2.1) where information about the project can
be entered such as its title, author, and location coordinates. Clicking on the button Save will create a
new project folder named after the project’s title. Moreover, information related to the project are saved
in a file with an extension “.what”. It is possible to change the directory where the project is saved by
clicking the folder icon located next to the Save in Folder directory path.
For example, information related to the project My New Project by John Doe, in Fig. 2.1, would be
saved in the file named “My New Project.what”, in the folder named “My New Project”, located in the
directory “...nWHATnProjects”.

.. _project_toolbar:
.. figure:: img/scs_project_toolbar_annoted.*
    :align: center
    :width: 100%
    :alt: alternate text
    :figclass: align-center
    
    Presentation of the project toolbar in GWHAT.
    





.. |new_project| image:: img/icon_new_project.*
                      :width: 1em
                      :height: 1em
                      :alt: stop